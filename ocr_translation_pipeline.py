"""
OCR + Translation Script
Uses Azure Document Intelligence to OCR and extract text from documents,
then translates using Azure Translator Service.

Supports 25+ file formats:
- PDF: .pdf
- Microsoft Office: .doc, .docx, .xls, .xlsx, .ppt, .pptx
- OpenDocument: .odt, .ods, .odp
- Text: .txt, .rtf
- Markup: .html, .htm, .mhtml, .mht, .md, .markdown, .mkdn, .mdown, .mdwn
- Email: .msg
- Localization: .xlf, .xliff
- Data: .csv, .tsv, .tab
- Images: .jpg, .jpeg, .png, .bmp, .tiff, .tif
"""

import os
import time
import logging
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, generate_container_sas, BlobSasPermissions, ContainerSasPermissions
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from datetime import datetime, timedelta
from dotenv import load_dotenv
from io import BytesIO

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


class OCRTranslationPipeline:
    def __init__(self, use_managed_identity=None):
        """Initialize the OCR and translation pipeline with Azure credentials.
        
        Args:
            use_managed_identity: If True, use Managed Identity. If False, use keys.
                                 If None, auto-detect based on whether connection string is present.
        """
        # Document Intelligence credentials
        self.doc_intel_endpoint = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.doc_intel_key = os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")
        
        # Translator credentials
        self.translator_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
        self.translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
        
        # Storage credentials
        self.storage_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.storage_account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.storage_account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        
        # Auto-detect authentication method if not specified
        if use_managed_identity is None:
            use_managed_identity = not bool(self.storage_connection_string)
        
        self.use_managed_identity = use_managed_identity
        
        # Validate required credentials
        if not all([
            self.doc_intel_endpoint, self.doc_intel_key,
            self.translator_endpoint, self.translator_key,
            self.storage_account_name
        ]):
            raise ValueError("Missing required Azure credentials. Please check your .env file.")
        
        # Initialize clients
        self.doc_analysis_client = DocumentAnalysisClient(
            endpoint=self.doc_intel_endpoint,
            credential=AzureKeyCredential(self.doc_intel_key)
        )
        
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
    
    def analyze_document_with_ocr(self, file_path):
        """
        Analyze a document using Azure Document Intelligence OCR.
        Supports all document formats including PDF, Office files, images, and more.
        
        Args:
            file_path: Path to the document file (any supported format)
            
        Returns:
            Analysis result with extracted text and layout
        """
        try:
            print(f"Starting OCR analysis of: {file_path}")
            
            with open(file_path, "rb") as f:
                poller = self.doc_analysis_client.begin_analyze_document(
                    "prebuilt-read",  # Use the read model for OCR
                    document=f
                )
            
            print("OCR job submitted. Waiting for completion...")
            result = poller.result()
            
            print(f"✓ OCR completed successfully!")
            print(f"  Pages analyzed: {len(result.pages)}")
            print(f"  Paragraphs extracted: {len(result.paragraphs) if result.paragraphs else 0}")
            
            return result
            
        except Exception as e:
            print(f"Error during OCR analysis: {e}")
            raise
    
    def create_searchable_document(self, original_file_path, ocr_result, output_path):
        """
        Create a searchable document by extracting OCR text and preserving the original file.
        Extracts text content to a separate .txt file for reference.
        
        Args:
            original_file_path: Path to the original document (any format)
            ocr_result: OCR analysis result from Document Intelligence
            output_path: Path to save the searchable document
        """
        try:
            print("Creating searchable PDF with OCR data...")
            
            # For this example, we'll extract text and metadata
            # In a production scenario, you might want to embed the text layer into the PDF
            
            # Extract all text content
            text_content = []
            for page_num, page in enumerate(ocr_result.pages, start=1):
                text_content.append(f"=== Page {page_num} ===\n")
                if ocr_result.content:
                    # Get content for this page
                    page_text = ""
                    for paragraph in ocr_result.paragraphs:
                        if paragraph.bounding_regions:
                            for region in paragraph.bounding_regions:
                                if region.page_number == page_num:
                                    page_text += paragraph.content + "\n\n"
                    text_content.append(page_text)
            
            # Save the extracted text alongside the document
            # Preserve original file extension for output
            base_output = os.path.splitext(output_path)[0]
            original_ext = os.path.splitext(original_file_path)[1]
            text_output_path = f"{base_output}_ocr_text.txt"
            
            with open(text_output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(text_content))
            
            print(f"✓ OCR text extracted to: {text_output_path}")
            
            # Copy the original document to the output location with proper extension
            import shutil
            output_with_ext = f"{base_output}{original_ext}"
            shutil.copy2(original_file_path, output_with_ext)
            
            print(f"✓ Searchable document created: {output_with_ext}")
            print(f"  Original format: {original_ext}")
            
            return output_with_ext
            
            return output_path
            
        except Exception as e:
            print(f"Error creating searchable PDF: {e}")
            raise
    
    def upload_to_blob(self, file_path, container_name):
        """
        Upload a file to Azure Blob Storage.
        
        Args:
            file_path: Path to the file
            container_name: Name of the blob container
            
        Returns:
            URL with SAS token
        """
        try:
            # Create container if it doesn't exist
            container_client = self.blob_service_client.get_container_client(container_name)
            try:
                # Create container without public access (SAS tokens will provide access)
                container_client.create_container()
            except Exception as e:
                # Container might already exist, which is fine
                if "ContainerAlreadyExists" not in str(e) and "already exists" not in str(e).lower():
                    print(f"Container creation note: {e}")
            
            # Upload the file
            blob_name = os.path.basename(file_path)
            blob_client = container_client.get_blob_client(blob_name)
            
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
            # Return URL (with or without SAS token based on authentication method)
            if self.use_managed_identity:
                # With Managed Identity, return plain URL
                return blob_client.url
            else:
                # Generate SAS token with proper permissions
                sas_token = generate_blob_sas(
                    account_name=self.storage_account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    account_key=self.storage_account_key,
                    permission=BlobSasPermissions(read=True, list=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                return f"{blob_client.url}?{sas_token}"
            
        except Exception as e:
            print(f"Error uploading to blob: {e}")
            raise
    
    def translate_document(self, file_path, target_language, source_container="ocr-source", target_container="ocr-target", source_language=None):
        """
        Translate the document.
        
        Args:
            file_path: Path to the searchable PDF to translate
            target_language: Target language code
            source_container: Source blob container name
            target_container: Target blob container name
            source_language: Optional source language code (if not provided, auto-detect)
            
        Returns:
            URL of the translated document
        """
        try:
            print(f"\nStarting translation to {target_language}...")
            
            # Upload source document (this uploads the file but we need container URL)
            self.upload_to_blob(file_path, source_container)
            
            # Generate source container URL with SAS token
            # Note: Azure Translator needs container-level access, not individual blob URLs
            if self.use_managed_identity:
                # With Managed Identity, use container URL directly
                source_url = f"https://{self.storage_account_name}.blob.core.windows.net/{source_container}"
            else:
                # Generate SAS token for source container using container-specific function
                source_sas_token = generate_container_sas(
                    account_name=self.storage_account_name,
                    container_name=source_container,
                    account_key=self.storage_account_key,
                    permission=ContainerSasPermissions(read=True, list=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                source_url = f"https://{self.storage_account_name}.blob.core.windows.net/{source_container}?{source_sas_token}"
            
            # Set up target container
            target_container_client = self.blob_service_client.get_container_client(target_container)
            try:
                # Create container without public access (SAS tokens will provide access)
                target_container_client.create_container()
                print(f"Created target container: {target_container}")
            except Exception as e:
                # Container might already exist, which is fine
                if "ContainerAlreadyExists" in str(e) or "already exists" in str(e).lower():
                    print(f"Target container {target_container} already exists")
                    # Clear existing blobs to avoid TargetFileAlreadyExists error
                    print("Clearing existing files from target container...")
                    blobs = target_container_client.list_blobs()
                    for blob in blobs:
                        target_container_client.delete_blob(blob.name)
                        print(f"  Deleted: {blob.name}")
                else:
                    print(f"Target container creation note: {e}")
            
            # Generate target URL (with or without SAS token)
            if self.use_managed_identity:
                # With Managed Identity, no SAS token needed
                target_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container}"
            else:
                # Use container-specific SAS generation for proper permissions
                target_sas = generate_container_sas(
                    account_name=self.storage_account_name,
                    container_name=target_container,
                    account_key=self.storage_account_key,
                    permission=ContainerSasPermissions(write=True, read=True, list=True),
                    expiry=datetime.utcnow() + timedelta(hours=24)
                )
                target_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container}?{target_sas}"
            
            # Start translation
            # Build translation input with optional source language
            translation_kwargs = {
                'source_url': source_url,
                'targets': [TranslationTarget(target_url=target_url, language=target_language)]
            }
            
            # Add source language if specified (otherwise Azure will auto-detect)
            if source_language:
                translation_kwargs['source_language'] = source_language
                print(f"Using specified source language: {source_language}")
            else:
                print("Using auto-detection for source language")
            
            translation_input = DocumentTranslationInput(**translation_kwargs)
            
            poller = self.translation_client.begin_translation([translation_input])
            print("Translation job submitted. Waiting for completion...")
            
            result = poller.result()
            
            for document in result:
                if document.status == "Succeeded":
                    print(f"✓ Translation completed successfully!")
                    # Note: Azure Document Translation API does not expose detected source language
                    detected_lang = 'auto-detected'
                    print(f"  📝 Detected source language: {detected_lang}")
                    logger.info(f"✓ OCR Translation successful - Source: {detected_lang} → Target: {target_language}")
                    return {
                        'url': document.translated_document_url,
                        'detected_source_language': detected_lang
                    }
                elif document.status == "Failed":
                    error_code = document.error.code if document.error else 'Unknown'
                    error_msg = document.error.message if document.error else 'Unknown error'
                    logger.error(f"OCR Translation failed - Target: {target_language} | Code: {error_code}, Message: {error_msg}")
                    
                    print(f"✗ Translation failed!")
                    print(f"  Target language: {target_language}")
                    print(f"  Error code: {error_code}")
                    print(f"  Error message: {error_msg}")
                    return None
            
        except Exception as e:
            logger.error(f"Error during OCR translation: {e}", exc_info=True)
            print(f"Error during translation: {e}")
            raise
    
    def download_from_blob(self, blob_url, output_path):
        """
        Download a file from blob storage.
        
        Args:
            blob_url: URL of the blob
            output_path: Local path to save the file
        """
        try:
            url_parts = blob_url.split('?')[0].split('/')
            container_name = url_parts[-2]
            blob_name = url_parts[-1]
            
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name,
                blob=blob_name
            )
            
            with open(output_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
            
            print(f"Downloaded to: {output_path}")
            
        except Exception as e:
            print(f"Error downloading: {e}")
            raise
    
    def process_document(self, input_file_path, target_language, output_folder="output", source_language=None):
        """
        Complete pipeline: OCR → Extract Text → Translate Document
        Supports all 25+ file formats (PDF, Office, Images, etc.)
        
        Args:
            input_file_path: Path to the input document (any supported format)
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            output_folder: Folder to save output files
            source_language: Optional source language code (if not provided, auto-detect)
            
        Returns:
            Dictionary with paths to OCR text and translated files
        """
        try:
            os.makedirs(output_folder, exist_ok=True)
            
            # Get file extension and base name
            file_ext = os.path.splitext(input_file_path)[1]
            base_name = os.path.splitext(os.path.basename(input_file_path))[0]
            
            print("="*70)
            print("STARTING OCR + TRANSLATION PIPELINE")
            print("="*70)
            print(f"Input: {input_file_path}")
            print(f"Format: {file_ext}")
            print(f"Target language: {target_language}")
            print()
            
            # Step 1: OCR Analysis
            print("STEP 1: OCR Analysis")
            print("-" * 70)
            ocr_result = self.analyze_document_with_ocr(input_file_path)
            
            # Step 2: Create Searchable Document with OCR text
            print("\nSTEP 2: Extracting OCR Text")
            print("-" * 70)
            searchable_doc_path = os.path.join(output_folder, f"{base_name}_searchable{file_ext}")
            self.create_searchable_document(input_file_path, ocr_result, searchable_doc_path)
            
            # Step 3: Translate
            print("\nSTEP 3: Translation")
            print("-" * 70)
            translation_result = self.translate_document(
                searchable_doc_path,
                target_language,
                source_language=source_language
            )
            
            # Step 4: Download translated document
            if translation_result:
                print("\nSTEP 4: Downloading Translated Document")
                print("-" * 70)
                
                # Handle both old string format and new dict format
                if isinstance(translation_result, dict):
                    translated_url = translation_result['url']
                    detected_lang = translation_result.get('detected_source_language', 'unknown')
                else:
                    translated_url = translation_result
                    detected_lang = 'unknown'
                
                translated_doc_path = os.path.join(
                    output_folder,
                    f"{base_name}_translated_{target_language}{file_ext}"
                )
                self.download_from_blob(translated_url, translated_doc_path)
                
                # Get OCR text file path
                ocr_text_path = os.path.join(output_folder, f"{base_name}_searchable_ocr_text.txt")
                
                print("\n" + "="*70)
                print("PIPELINE COMPLETED SUCCESSFULLY!")
                print("="*70)
                print(f"✓ OCR text: {ocr_text_path}")
                print(f"✓ Searchable document: {searchable_doc_path}")
                print(f"✓ Translated document: {translated_doc_path}")
                print(f"📝 Detected source language: {detected_lang}")
                print(f"🎯 Target language: {target_language}")
                
                # Log completion with detected language
                logger.info(f"OCR Pipeline completed - Format: {file_ext} | Source: {detected_lang} → Target: {target_language}")
                
                return {
                    'ocr_text': ocr_text_path,
                    'searchable_document': searchable_doc_path,
                    'translated_document': translated_doc_path,
                    'detected_source_language': detected_lang
                }
            else:
                print("\n✗ Translation failed")
                return None
            
        except Exception as e:
            print(f"\n✗ Pipeline failed: {e}")
            raise


def main():
    """Main function to demonstrate the OCR + Translation pipeline."""
    pipeline = OCRTranslationPipeline()
    
    # Configuration - supports all file formats!
    input_file = "sample.pdf"  # Change to your file (PDF, DOCX, JPG, PNG, etc.)
    target_language = "es"  # Spanish - change to your target language
    output_folder = "ocr_translated_output"
    
    # Examples of supported formats:
    # input_file = "document.docx"  # Word document
    # input_file = "scan.jpg"       # Image file
    # input_file = "presentation.pptx"  # PowerPoint
    # input_file = "spreadsheet.xlsx"   # Excel
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        print("Please update the 'input_file' variable with your document file path.")
        print("Supported formats: PDF, Office (Word/Excel/PowerPoint), Images, and 25+ more!")
        return
    
    # Process the document
    results = pipeline.process_document(
        input_file_path=input_file,
        target_language=target_language,
        output_folder=output_folder
    )
    
    if results:
        print(f"\n✓ All files saved in: {output_folder}")


if __name__ == "__main__":
    main()
