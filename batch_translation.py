"""
Batch Document Translation Script
Translates multiple PDF documents using Azure Translator Service batch processing.
"""

import os
import time
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContainerClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


class BatchDocumentTranslator:
    def __init__(self):
        """Initialize the batch translator with Azure credentials."""
        self.translator_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
        self.translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
        self.storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        
        # Validate required credentials
        if not all([self.translator_endpoint, self.translator_key, self.storage_connection_string]):
            raise ValueError("Missing required Azure credentials. Please check your .env file.")
        
        self.translation_client = DocumentTranslationClient(
            self.translator_endpoint,
            AzureKeyCredential(self.translator_key)
        )
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.storage_connection_string
        )
    
    def upload_documents_to_blob(self, file_paths, container_name):
        """
        Upload multiple documents to Azure Blob Storage.
        
        Args:
            file_paths: List of paths to PDF files
            container_name: Name of the blob container
            
        Returns:
            List of uploaded blob URLs
        """
        try:
            # Create container if it doesn't exist
            container_client = self.blob_service_client.get_container_client(container_name)
            try:
                # Set public access to blob level for Azure Translator to access
                container_client.create_container(public_access='blob')
                print(f"Created container: {container_name}")
            except Exception as e:
                print(f"Container {container_name} already exists or creation failed: {e}")
            
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
    
    def translate_batch(self, input_folder, target_languages, source_container="batch-source", target_container_prefix="batch-target"):
        """
        Translate multiple PDF documents in batch.
        
        Args:
            input_folder: Folder containing PDF files to translate
            target_languages: List of target language codes (e.g., ['es', 'fr', 'de'])
            source_container: Name of the source blob container
            target_container_prefix: Prefix for target blob container names
            
        Returns:
            Dictionary of translation results by language
        """
        try:
            print(f"Starting batch translation from folder: {input_folder}")
            print(f"Target languages: {', '.join(target_languages)}")
            
            # Find all PDF files in the input folder
            pdf_files = []
            input_path = Path(input_folder)
            
            if input_path.is_file() and input_path.suffix.lower() == '.pdf':
                pdf_files = [str(input_path)]
            elif input_path.is_dir():
                pdf_files = [str(f) for f in input_path.glob("*.pdf")]
            else:
                raise ValueError(f"Invalid input: {input_folder} is not a file or directory")
            
            if not pdf_files:
                print(f"No PDF files found in {input_folder}")
                return {}
            
            print(f"Found {len(pdf_files)} PDF files to translate")
            
            # Upload all source documents
            print("\nUploading source documents...")
            self.upload_documents_to_blob(pdf_files, source_container)
            
            # Generate SAS token for source container
            source_sas_token = generate_blob_sas(
                account_name=self.storage_account_name,
                container_name=source_container,
                blob_name="",
                account_key=self.storage_account_key,
                permission=BlobSasPermissions(read=True, list=True),
                expiry=datetime.utcnow() + timedelta(hours=24)
            )
            
            source_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{source_container}?{source_sas_token}"
            
            # Create translation targets for each language
            translation_targets = []
            
            for lang in target_languages:
                target_container_name = f"{target_container_prefix}-{lang}"
                
                # Create target container
                target_container_client = self.blob_service_client.get_container_client(target_container_name)
                try:
                    # Set public access to blob level for Azure Translator to write results
                    target_container_client.create_container(public_access='blob')
                    print(f"Created target container: {target_container_name}")
                except Exception as e:
                    print(f"Target container {target_container_name} already exists or creation failed: {e}")
                
                # Generate SAS token for target container
                target_sas_token = generate_blob_sas(
                    account_name=self.storage_account_name,
                    container_name=target_container_name,
                    blob_name="",
                    account_key=self.storage_account_key,
                    permission=BlobSasPermissions(write=True, read=True, list=True),
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
            translation_input = DocumentTranslationInput(
                source_url=source_container_url,
                targets=translation_targets
            )
            
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
            
            print("\n" + "="*70)
            print("BATCH TRANSLATION RESULTS")
            print("="*70)
            
            for document in result:
                if document.status == "Succeeded":
                    success_count += 1
                    source_file = os.path.basename(document.source_document_url.split('?')[0])
                    target_lang = document.translated_to
                    
                    print(f"\n✓ {source_file} → {target_lang}")
                    print(f"  Translated URL: {document.translated_document_url}")
                    
                    results_by_language[target_lang].append({
                        'source': source_file,
                        'url': document.translated_document_url,
                        'status': 'success'
                    })
                    
                elif document.status == "Failed":
                    failure_count += 1
                    source_file = os.path.basename(document.source_document_url.split('?')[0])
                    
                    print(f"\n✗ {source_file} - FAILED")
                    print(f"  Error: {document.error.message if document.error else 'Unknown error'}")
                    
            print("\n" + "="*70)
            print(f"SUMMARY: {success_count} succeeded, {failure_count} failed")
            print("="*70)
            
            return results_by_language
            
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
    input_folder = "input_pdfs"  # Folder containing your PDF files
    target_languages = ["es", "fr", "de"]  # Spanish, French, German - modify as needed
    output_base_folder = "translated_output"
    
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' not found!")
        print("Please create the folder and add your PDF files, or update the 'input_folder' variable.")
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
