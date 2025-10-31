"""
Single Document Translation Script
Translates a single document using Azure Translator Service with auto language detection.
Supports: PDF, Office (Word/Excel/PowerPoint), OpenDocument, Text, HTML, Markdown, and more.
"""

import os
import time
import logging
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, generate_container_sas, BlobSasPermissions, ContainerSasPermissions
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get log level from environment variable (default to INFO)
log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Configure logging with Azure SDK HTTP logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('translation_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Enable Azure SDK HTTP request/response logging (DEBUG level shows full API details)
azure_logger = logging.getLogger('azure.core.pipeline.policies.http_logging_policy')
azure_logger.setLevel(log_level)
if log_level == logging.DEBUG:
    logger.info("API call logging enabled - HTTP requests, headers, and responses will be logged")
else:
    logger.info(f"Logging level: {log_level_str}")


class SingleDocumentTranslator:
    def __init__(self, use_managed_identity=None):
        """
        Initialize the translator with Azure credentials.
        
        Args:
            use_managed_identity: If True, use Managed Identity. If False, use keys.
                                 If None (default), auto-detect based on available credentials.
        """
        logger.info("Initializing SingleDocumentTranslator")
        
        self.translator_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
        self.translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
        self.storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        
        # Validate required credentials
        if not self.translator_endpoint or not self.storage_account_name:
            logger.error("Missing required credentials")
            raise ValueError("Missing required AZURE_TRANSLATOR_ENDPOINT or AZURE_STORAGE_ACCOUNT_NAME")
        
        # Auto-detect authentication method
        if use_managed_identity is None:
            # Use Managed Identity if connection string is not provided
            use_managed_identity = not bool(self.storage_connection_string)
        
        self.use_managed_identity = use_managed_identity
        
        # Initialize translation client
        if use_managed_identity:
            logger.info("Using Managed Identity for authentication")
            print("Using Managed Identity for authentication")
            credential = DefaultAzureCredential()
            self.translation_client = DocumentTranslationClient(
                self.translator_endpoint,
                credential
            )
            self.blob_service_client = BlobServiceClient(
                account_url=f"https://{self.storage_account_name}.blob.core.windows.net",
                credential=credential
            )
        else:
            logger.info("Using Key-based authentication")
            print("Using Key-based authentication")
            if not self.translator_key or not self.storage_connection_string:
                logger.error("Missing keys for key-based authentication")
                raise ValueError("Missing AZURE_TRANSLATOR_KEY or AZURE_STORAGE_CONNECTION_STRING for key-based auth")
            
            self.translation_client = DocumentTranslationClient(
                self.translator_endpoint,
                AzureKeyCredential(self.translator_key)
            )
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.storage_connection_string
            )
        
        logger.info("SingleDocumentTranslator initialized successfully")
    
    def upload_document_to_blob(self, file_path, container_name):
        """
        Upload a document to Azure Blob Storage.
        
        Args:
            file_path: Path to the local document file
            container_name: Name of the blob container
            
        Returns:
            URL of the uploaded blob with SAS token
        """
        logger.info(f"Starting upload: {file_path} to container {container_name}")
        try:
            # Create container if it doesn't exist
            container_client = self.blob_service_client.get_container_client(container_name)
            try:
                # Create container without public access (SAS tokens will provide access)
                container_client.create_container()
                logger.info(f"Created new container: {container_name}")
                print(f"Created container: {container_name}")
            except Exception as e:
                # Container might already exist, which is fine
                if "ContainerAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    logger.debug(f"Container {container_name} already exists")
                    print(f"Container {container_name} already exists")
                else:
                    logger.warning(f"Container creation note: {e}")
                    print(f"Container creation note: {e}")
            
            # Upload the file
            blob_name = os.path.basename(file_path)
            blob_client = container_client.get_blob_client(blob_name)
            
            logger.info(f"Uploading blob: {blob_name}")
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                logger.info(f"Successfully uploaded {blob_name} to {container_name}")
                print(f"Uploaded {blob_name} to container {container_name}")
            
            # Return URL based on authentication method
            if self.use_managed_identity:
                # With Managed Identity, return the blob URL directly
                # Azure Translator will use its own managed identity to access
                logger.debug(f"Returning blob URL (Managed Identity): {blob_client.url}")
                return blob_client.url
            else:
                # Generate SAS token for key-based authentication
                logger.debug("Generating SAS token for blob access")
                sas_token = generate_blob_sas(
                    account_name=self.storage_account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    account_key=self.storage_account_key,
                    permission=BlobSasPermissions(read=True, list=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                
                blob_url_with_sas = f"{blob_client.url}?{sas_token}"
                logger.debug("Returning blob URL with SAS token")
                return blob_url_with_sas
            
        except Exception as e:
            logger.error(f"Error uploading document: {e}", exc_info=True)
            print(f"Error uploading document: {e}")
            raise
    
    def translate_document(self, input_file_path, target_language, source_container="source", target_container="target", source_language=None):
        """
        Translate a single document.
        
        Args:
            input_file_path: Path to the input document file
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            source_container: Name of the source blob container
            target_container: Name of the target blob container
            source_language: Optional source language code (if not provided, auto-detect)
            
        Returns:
            Dictionary with URL of the translated document and detected source language
        """
        logger.info(f"Starting translation: {input_file_path} -> {target_language}")
        if source_language:
            logger.info(f"Source language specified: {source_language}")
        else:
            logger.info("Source language: auto-detect")
            
        try:
            print(f"Starting translation of {input_file_path} to {target_language}")
            
            # Upload source document
            logger.info("Uploading source document to blob storage")
            print("Uploading source document...")
            self.upload_document_to_blob(input_file_path, source_container)
            
            # Generate source container URL with SAS token
            # Note: Azure Translator needs container-level access, not individual blob URLs
            logger.info("Generating source container URL")
            if self.use_managed_identity:
                # With Managed Identity, use container URL directly
                source_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{source_container}"
                logger.debug(f"Source container URL (Managed Identity): {source_container_url}")
            else:
                # Generate SAS token for source container using container-specific function
                logger.debug("Generating SAS token for source container")
                source_sas_token = generate_container_sas(
                    account_name=self.storage_account_name,
                    container_name=source_container,
                    account_key=self.storage_account_key,
                    permission=ContainerSasPermissions(read=True, list=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                source_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{source_container}?{source_sas_token}"
                logger.debug("Source container SAS token generated")
            
            # Get target container URL with SAS token
            logger.info(f"Setting up target container: {target_container}")
            target_container_client = self.blob_service_client.get_container_client(target_container)
            try:
                # Create container without public access (SAS tokens will provide access)
                target_container_client.create_container()
                logger.info(f"Created target container: {target_container}")
                print(f"Created target container: {target_container}")
            except Exception as e:
                # Container might already exist, which is fine
                if "ContainerAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    logger.debug(f"Target container {target_container} already exists")
                    print(f"Target container {target_container} already exists")
                    # Clear existing blobs to avoid TargetFileAlreadyExists error
                    logger.info("Clearing existing files from target container")
                    print("Clearing existing files from target container...")
                    blobs = target_container_client.list_blobs()
                    for blob in blobs:
                        target_container_client.delete_blob(blob.name)
                        logger.debug(f"Deleted blob: {blob.name}")
                        print(f"  Deleted: {blob.name}")
                else:
                    logger.warning(f"Target container creation note: {e}")
                    print(f"Target container creation note: {e}")
            
            # Get target container URL based on authentication method
            logger.info("Generating target container URL")
            if self.use_managed_identity:
                # With Managed Identity, use container URL directly
                target_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container}"
                logger.debug(f"Target container URL (Managed Identity): {target_container_url}")
            else:
                # Generate SAS token for target container using container-specific function
                logger.debug("Generating SAS token for target container")
                target_sas_token = generate_container_sas(
                    account_name=self.storage_account_name,
                    container_name=target_container,
                    account_key=self.storage_account_key,
                    permission=ContainerSasPermissions(write=True, read=True, list=True, create=True, add=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                
                target_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container}?{target_sas_token}"
                logger.debug("Target container SAS token generated")
            
            # Set up translation
            logger.info("Configuring translation job")
            print("Starting translation job...")
            # Build translation input with optional source language
            translation_kwargs = {
                'source_url': source_container_url,  # Now using container URL, not blob URL
                'targets': [
                    TranslationTarget(
                        target_url=target_container_url,
                        language=target_language
                    )
                ]
            }
            
            # Add source language if specified (otherwise Azure will auto-detect)
            if source_language:
                # Check if source and target languages are the same
                if source_language.lower() == target_language.lower():
                    error_msg = f"Source language ({source_language}) and target language ({target_language}) are the same - no translation needed"
                    logger.error(error_msg)
                    print(f"Error: {error_msg}")
                    raise ValueError(error_msg)
                
                translation_kwargs['source_language'] = source_language
                logger.info(f"Using specified source language: {source_language}")
                print(f"Using specified source language: {source_language}")
            else:
                logger.info("Using auto-detection for source language")
                print("Using auto-detection for source language")
            
            translation_input = DocumentTranslationInput(**translation_kwargs)
            
            # Start translation
            logger.info("Submitting translation job to Azure")
            poller = self.translation_client.begin_translation([translation_input])
            
            logger.info("Translation job submitted, waiting for completion")
            print("Translation job submitted. Waiting for completion...")
            result = poller.result()
            logger.info("Translation job completed")
            
            # Check results
            logger.info("Processing translation results")
            for document in result:
                if document.status == "Succeeded":
                    logger.info(f"Translation succeeded for document")
                    logger.debug(f"Source URL: {document.source_document_url}")
                    logger.debug(f"Translated URL: {document.translated_document_url}")
                    
                    print(f"Translation completed successfully!")
                    print(f"  Source document: {document.source_document_url}")
                    print(f"  Translated document: {document.translated_document_url}")
                    
                    # Note: Azure Document Translation API does not expose detected source language
                    # The API detects language internally but doesn't return it in the response
                    detected_lang = 'auto-detected'
                    
                    # Warning: If auto-detection was used, we can't verify if source == target
                    # Azure will still process the translation even if languages match
                    if not source_language:
                        logger.warning(f"Source language was auto-detected - cannot verify if it matches target ({target_language})")
                        print(f"\n  WARNING: Source language was auto-detected")
                        print(f"  If the document is already in {target_language}, the translation may be unnecessary")
                    
                    logger.info(f"Translation successful - Source: {detected_lang} -> Target: {target_language}")
                    print(f"\n  Detected source language: {detected_lang}")
                    print(f"  Target language: {target_language}")
                    
                    # Return both URL and detected language
                    return {
                        'url': document.translated_document_url,
                        'detected_source_language': detected_lang
                    }
                elif document.status == "Failed":
                    error_code = document.error.code if document.error else 'Unknown'
                    error_msg = document.error.message if document.error else 'Unknown'
                    logger.error(f"Translation failed - Target: {target_language} | Code: {error_code}, Message: {error_msg}")
                    
                    print(f"Translation failed!")
                    print(f"  Target language: {target_language}")
                    print(f"  Error code: {error_code}")
                    print(f"  Error message: {error_msg}")
                    return None
                else:
                    logger.warning(f"Unexpected document status: {document.status}")
                    print(f"  Status: {document.status}")
            
        except Exception as e:
            logger.error(f"Error during translation: {e}", exc_info=True)
            print(f"Error during translation: {e}")
            raise
    
    def download_translated_document(self, blob_url, output_path):
        """
        Download the translated document from blob storage.
        
        Args:
            blob_url: URL of the translated blob
            output_path: Local path to save the translated document
        """
        try:
            # Extract container and blob name from URL
            url_parts = blob_url.split('?')[0].split('/')
            container_name = url_parts[-2]
            blob_name = url_parts[-1]
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            with open(output_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            print(f"Downloaded translated document to: {output_path}")
            
        except Exception as e:
            print(f"Error downloading document: {e}")
            raise


def main():
    """Main function to demonstrate single document translation."""
    # Example usage
    translator = SingleDocumentTranslator()
    
    # Configuration
    input_pdf = "sample.pdf"  # Change this to your PDF file path
    target_language = "es"  # Spanish - change to your target language (en, fr, de, etc.)
    output_pdf = f"translated_{target_language}_{os.path.basename(input_pdf)}"
    
    # Check if input file exists
    if not os.path.exists(input_pdf):
        print(f"Error: Input file '{input_pdf}' not found!")
        print("Please update the 'input_pdf' variable with your PDF file path.")
        return
    
    # Translate the document
    translation_result = translator.translate_document(
        input_file_path=input_pdf,
        target_language=target_language
    )
    
    if translation_result:
        # Handle dictionary return format
        if isinstance(translation_result, dict):
            translated_url = translation_result['url']
            detected_lang = translation_result.get('detected_source_language', 'unknown')
        else:
            translated_url = translation_result
            detected_lang = 'unknown'
        
        # Download the translated document
        translator.download_translated_document(translated_url, output_pdf)
        print(f"\nTranslation complete! Output saved to: {output_pdf}")
        print(f"  Detected source language: {detected_lang}")
        print(f"  Target language: {target_language}")
    else:
        print("\nTranslation failed.")


if __name__ == "__main__":
    main()
