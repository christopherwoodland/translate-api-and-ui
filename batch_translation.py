"""
Batch Document Translation Script
Translates multiple documents using Azure Translator Service batch processing.
Supports: PDF, Office (Word/Excel/PowerPoint), OpenDocument, Text, HTML, Markdown, and more.
"""

import os
import time
import logging
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, generate_container_sas, BlobSasPermissions, ContainerSasPermissions, ContainerClient
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BatchDocumentTranslator:
    def __init__(self, use_managed_identity=None):
        """Initialize the batch translator with Azure credentials.
        
        Args:
            use_managed_identity: If True, use Managed Identity. If False, use keys.
                                 If None, auto-detect based on whether connection string is present.
        """
        self.translator_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
        self.translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
        self.storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        
        # Auto-detect authentication method if not specified
        if use_managed_identity is None:
            use_managed_identity = not bool(self.storage_connection_string)
        
        self.use_managed_identity = use_managed_identity
        
        # Validate required credentials
        if not all([self.translator_endpoint, self.translator_key, self.storage_account_name]):
            raise ValueError("Missing required Azure credentials. Please check your .env file.")
        
        # Initialize translation client (currently always uses key)
        self.translation_client = DocumentTranslationClient(
            self.translator_endpoint,
            AzureKeyCredential(self.translator_key)
        )
        
        # Initialize blob service client based on authentication method
        account_url = f"https://{self.storage_account_name}.blob.core.windows.net"
        
        if self.use_managed_identity:
            # Use Managed Identity (for Azure-hosted environments)
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=credential
            )
        else:
            # Use connection string or account key (for local development)
            if self.storage_connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.storage_connection_string
                )
            else:
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=AzureKeyCredential(self.storage_account_key)
                )
    
    def upload_documents_to_blob(self, file_paths, container_name):
        """
        Upload multiple documents to Azure Blob Storage.
        
        Args:
            file_paths: List of paths to document files
            container_name: Name of the blob container
            
        Returns:
            List of uploaded blob URLs
        """
        try:
            # Create container if it doesn't exist
            container_client = self.blob_service_client.get_container_client(container_name)
            try:
                # Create container without public access (SAS tokens will provide access)
                container_client.create_container()
                print(f"Created container: {container_name}")
            except Exception as e:
                # Container might already exist, which is fine
                if "ContainerAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    print(f"Container {container_name} already exists")
                else:
                    print(f"Container creation note: {e}")
            
            uploaded_urls = []
            
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    print(f"Warning: File not found: {file_path}")
                    continue
                
                # Upload the file
                blob_name = os.path.basename(file_path)
                blob_client = container_client.get_blob_client(blob_name)
                
                with open(file_path, "rb") as data:
                    blob_client.upload_blob(data, overwrite=True)
                    print(f"  Uploaded: {blob_name}")
                
                uploaded_urls.append(blob_client.url)
            
            print(f"Uploaded {len(uploaded_urls)} documents to container {container_name}")
            return uploaded_urls
            
        except Exception as e:
            print(f"Error uploading documents: {e}")
            raise
    
    def translate_batch(self, input_folder, target_languages, source_container="batch-source", target_container_prefix="batch-target", source_language=None):
        """
        Translate multiple documents in batch.
        
        Args:
            input_folder: Folder containing document files to translate
            target_languages: List of target language codes (e.g., ['es', 'fr', 'de'])
            source_container: Name of the source blob container
            target_container_prefix: Prefix for target blob container names
            source_language: Optional source language code (if not provided, auto-detect)
            
        Returns:
            Dictionary with translation results by language and detected source languages
        """
        try:
            print(f"Starting batch translation from folder: {input_folder}")
            print(f"Target languages: {', '.join(target_languages)}")
            
            # Find all supported document files in the input folder
            supported_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.odt', '.ods', '.odp', '.rtf', '.txt', '.html', '.htm',
                '.mhtml', '.mht', '.md', '.markdown', '.mkdn', '.mdown', '.mdwn',
                '.msg', '.xlf', '.xliff', '.csv', '.tsv', '.tab'
            ]
            
            document_files = []
            input_path = Path(input_folder)
            
            if input_path.is_file() and input_path.suffix.lower() in supported_extensions:
                document_files = [str(input_path)]
            elif input_path.is_dir():
                for ext in supported_extensions:
                    document_files.extend([str(f) for f in input_path.glob(f"*{ext}")])
            else:
                raise ValueError(f"Invalid input: {input_folder} is not a file or directory")
            
            if not document_files:
                print(f"No supported document files found in {input_folder}")
                return {}
            
            print(f"Found {len(document_files)} document file(s) to translate")
            
            # Upload all source documents
            print("\nUploading source documents...")
            self.upload_documents_to_blob(document_files, source_container)
            
            # Generate source container URL (with or without SAS token)
            if self.use_managed_identity:
                # With Managed Identity, no SAS token needed - Translator uses system identity
                source_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{source_container}"
            else:
                # Generate SAS token for source container using container-specific function
                source_sas_token = generate_container_sas(
                    account_name=self.storage_account_name,
                    container_name=source_container,
                    account_key=self.storage_account_key,
                    permission=ContainerSasPermissions(read=True, list=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                source_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{source_container}?{source_sas_token}"
            
            # Create translation targets for each language
            translation_targets = []
            
            for lang in target_languages:
                target_container_name = f"{target_container_prefix}-{lang}"
                
                # Log container name for debugging
                logger.info(f"Creating target container for language '{lang}': {target_container_name}")
                
                # Validate container name length (Azure requirement: 3-63 characters)
                if len(target_container_name) < 3:
                    error_msg = f"Container name too short for language '{lang}': {target_container_name} (length: {len(target_container_name)})"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # Create target container
                target_container_client = self.blob_service_client.get_container_client(target_container_name)
                try:
                    # Create container without public access (SAS tokens will provide access)
                    target_container_client.create_container()
                    print(f"Created target container: {target_container_name}")
                    logger.info(f"Successfully created container: {target_container_name}")
                except Exception as e:
                    # Container might already exist, which is fine
                    if "ContainerAlreadyExists" in str(e) or "already exists" in str(e).lower():
                        print(f"Target container {target_container_name} already exists")
                        # Clear existing blobs to avoid TargetFileAlreadyExists error
                        print(f"Clearing existing files from {target_container_name}...")
                        blobs = target_container_client.list_blobs()
                        for blob in blobs:
                            target_container_client.delete_blob(blob.name)
                            print(f"  Deleted: {blob.name}")
                    else:
                        print(f"Target container creation note: {e}")
                
                # Generate target container URL (with or without SAS token)
                if self.use_managed_identity:
                    # With Managed Identity, no SAS token needed
                    target_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container_name}"
                else:
                    # Generate SAS token for target container using container-specific function
                    target_sas_token = generate_container_sas(
                        account_name=self.storage_account_name,
                        container_name=target_container_name,
                        account_key=self.storage_account_key,
                        permission=ContainerSasPermissions(write=True, read=True, list=True),
                        expiry=datetime.utcnow() + timedelta(hours=24)
                    )
                    target_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container_name}?{target_sas_token}"
                
                translation_targets.append(
                    TranslationTarget(
                        target_url=target_container_url,
                        language=lang
                    )
                )
            
            # Set up batch translation
            print("\nStarting batch translation job...")
            # Build translation input with optional source language
            translation_kwargs = {
                'source_url': source_container_url,
                'targets': translation_targets
            }
            
            # Add source language if specified (otherwise Azure will auto-detect)
            if source_language:
                translation_kwargs['source_language'] = source_language
                print(f"Using specified source language: {source_language}")
            else:
                print("Using auto-detection for source language")
            
            translation_input = DocumentTranslationInput(**translation_kwargs)
            
            # Start translation
            poller = self.translation_client.begin_translation([translation_input])
            
            print("Batch translation job submitted. Waiting for completion...")
            print("This may take several minutes depending on the number and size of documents.\n")
            
            # Monitor progress
            while not poller.done():
                time.sleep(30)
                print("  Still processing...")
            
            result = poller.result()
            
            # Collect results
            results_by_language = {lang: [] for lang in target_languages}
            success_count = 0
            failure_count = 0
            detected_source_languages = {}  # Track detected language per document
            
            print("\n" + "="*70)
            print("BATCH TRANSLATION RESULTS")
            print("="*70)
            
            for document in result:
                if document.status == "Succeeded":
                    success_count += 1
                    source_file = os.path.basename(document.source_document_url.split('?')[0])
                    target_lang = document.translated_to
                    
                    # Note: Azure Document Translation API does not expose detected source language
                    # The API detects language internally but doesn't return it in the response
                    detected_lang = 'auto-detected'
                    
                    # Debug output (can be removed later)
                    # print(f"\n📋 Available document properties: {[attr for attr in dir(document) if not attr.startswith('_')]}")
                    
                    # Store detected language for this source file
                    if source_file not in detected_source_languages:
                        detected_source_languages[source_file] = detected_lang
                    
                    print(f"\n✓ {source_file} → {target_lang}")
                    print(f"  📝 Detected source language: {detected_lang}")
                    print(f"  Translated URL: {document.translated_document_url}")
                    
                    # Log detected language
                    logger.info(f"Translation complete: {source_file} | Source: {detected_lang} → Target: {target_lang}")
                    
                    results_by_language[target_lang].append({
                        'source': source_file,
                        'url': document.translated_document_url,
                        'status': 'success',
                        'detected_source_language': detected_lang
                    })
                    
                elif document.status == "Failed":
                    failure_count += 1
                    source_file = os.path.basename(document.source_document_url.split('?')[0])
                    target_lang = getattr(document, 'translated_to', 'unknown')
                    error_code = document.error.code if document.error else 'Unknown'
                    error_msg = document.error.message if document.error else 'Unknown error'
                    
                    print(f"\n✗ {source_file} → {target_lang} - FAILED")
                    print(f"  Error Code: {error_code}")
                    print(f"  Error Message: {error_msg}")
                    
                    # Log detailed error information
                    logger.error(f"Translation failed: {source_file} → {target_lang} | Error: {error_code} - {error_msg}")
                    
            print("\n" + "="*70)
            print(f"SUMMARY: {success_count} succeeded, {failure_count} failed")
            print("\n📝 Detected Source Languages:")
            for source_file, lang in detected_source_languages.items():
                print(f"  • {source_file}: {lang}")
            print("="*70)
            
            # Log summary
            logger.info(f"Batch translation summary: {success_count} succeeded, {failure_count} failed")
            logger.info(f"Detected source languages: {detected_source_languages}")
            
            return {
                'results': results_by_language,
                'detected_source_languages': detected_source_languages
            }
            
        except Exception as e:
            print(f"Error during batch translation: {e}")
            raise
    
    def download_translated_documents(self, container_name, output_folder):
        """
        Download all translated documents from a container.
        
        Args:
            container_name: Name of the container with translated documents
            output_folder: Local folder to save translated documents
        """
        try:
            os.makedirs(output_folder, exist_ok=True)
            
            container_client = self.blob_service_client.get_container_client(container_name)
            blobs = container_client.list_blobs()
            
            downloaded_count = 0
            for blob in blobs:
                blob_client = container_client.get_blob_client(blob.name)
                output_path = os.path.join(output_folder, blob.name)
                
                with open(output_path, "wb") as download_file:
                    download_file.write(blob_client.download_blob().readall())
                
                print(f"  Downloaded: {blob.name}")
                downloaded_count += 1
            
            print(f"Downloaded {downloaded_count} files to {output_folder}")
            
        except Exception as e:
            print(f"Error downloading documents: {e}")
            raise


def main():
    """Main function to demonstrate batch translation."""
    translator = BatchDocumentTranslator()
    
    # Configuration
    input_folder = "input_documents"  # Folder containing your document files
    target_languages = ["es", "fr", "de"]  # Spanish, French, German - modify as needed
    output_base_folder = "translated_output"
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' not found!")
        print("Please create the folder and add your document files, or update the 'input_folder' variable.")
        return
    
    # Translate all documents
    results = translator.translate_batch(
        input_folder=input_folder,
        target_languages=target_languages
    )
    
    # Download translated documents for each language
    print("\nDownloading translated documents...")
    for lang, documents in results.items():
        if documents:
            output_folder = os.path.join(output_base_folder, lang)
            container_name = f"batch-target-{lang}"
            
            print(f"\nDownloading {lang} translations...")
            translator.download_translated_documents(container_name, output_folder)
    
    print(f"\n✓ Batch translation complete! Check the '{output_base_folder}' folder for results.")


if __name__ == "__main__":
    main()
