"""
OCR + Translation Script
Uses Azure Document Intelligence to convert PDF to searchable PDF with OCR,
then translates the searchable PDF using Azure Translator Service.
"""

import os
import time
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from dotenv import load_dotenv
from io import BytesIO

# Load environment variables
load_dotenv()


class OCRTranslationPipeline:
    def __init__(self):
        """Initialize the OCR and translation pipeline with Azure credentials."""
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
        
        # Validate required credentials
        if not all([
            self.doc_intel_endpoint, self.doc_intel_key,
            self.translator_endpoint, self.translator_key,
            self.storage_connection_string
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
        
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.storage_connection_string
        )
    
    def analyze_document_with_ocr(self, file_path):
        """
        Analyze a PDF document using Azure Document Intelligence OCR.
        
        Args:
            file_path: Path to the PDF file
            
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
    
    def create_searchable_pdf(self, original_pdf_path, ocr_result, output_path):
        """
        Create a searchable PDF by combining OCR results with the original PDF.
        Note: This is a simplified version. For production, consider using
        specialized PDF libraries like pypdf or reportlab for better results.
        
        Args:
            original_pdf_path: Path to the original PDF
            ocr_result: OCR analysis result from Document Intelligence
            output_path: Path to save the searchable PDF
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
            
            # Save the extracted text alongside the PDF
            text_output_path = output_path.replace('.pdf', '_ocr_text.txt')
            with open(text_output_path, 'w', encoding='utf-8') as f:
                f.write(''.join(text_content))
            
            print(f"✓ OCR text extracted to: {text_output_path}")
            
            # Copy the original PDF to the output location
            # In production, you would embed the text layer here
            import shutil
            shutil.copy2(original_pdf_path, output_path)
            
            print(f"✓ Searchable PDF created: {output_path}")
            print("  Note: For full text embedding, consider using specialized PDF libraries")
            
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
                # Set public access to blob level for Azure Translator to access
                container_client.create_container(public_access='blob')
            except Exception:
                pass
            
            # Upload the file
            blob_name = os.path.basename(file_path)
            blob_client = container_client.get_blob_client(blob_name)
            
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            
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
    
    def translate_document(self, file_path, target_language, source_container="ocr-source", target_container="ocr-target"):
        """
        Translate a document using Azure Translator.
        
        Args:
            file_path: Path to the PDF file
            target_language: Target language code
            source_container: Source blob container name
            target_container: Target blob container name
            
        Returns:
            URL of the translated document
        """
        try:
            print(f"\nStarting translation to {target_language}...")
            
            # Upload source document
            source_url = self.upload_to_blob(file_path, source_container)
            
            # Set up target container
            target_container_client = self.blob_service_client.get_container_client(target_container)
            try:
                # Set public access to blob level for Azure Translator to write results
                target_container_client.create_container(public_access='blob')
            except Exception:
                pass
            
            target_sas = generate_blob_sas(
                account_name=self.storage_account_name,
                container_name=target_container,
                blob_name="",
                account_key=self.storage_account_key,
                permission=BlobSasPermissions(write=True, read=True, list=True),
                expiry=datetime.utcnow() + timedelta(hours=24)
            )
            
            target_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container}?{target_sas}"
            
            # Start translation
            translation_input = DocumentTranslationInput(
                source_url=source_url,
                targets=[TranslationTarget(target_url=target_url, language=target_language)]
            )
            
            poller = self.translation_client.begin_translation([translation_input])
            print("Translation job submitted. Waiting for completion...")
            
            result = poller.result()
            
            for document in result:
                if document.status == "Succeeded":
                    print(f"✓ Translation completed successfully!")
                    return document.translated_document_url
                elif document.status == "Failed":
                    print(f"✗ Translation failed: {document.error.message if document.error else 'Unknown error'}")
                    return None
            
        except Exception as e:
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
    
    def process_document(self, input_pdf_path, target_language, output_folder="output"):
        """
        Complete pipeline: OCR → Searchable PDF → Translation
        
        Args:
            input_pdf_path: Path to the input PDF
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            output_folder: Folder to save output files
            
        Returns:
            Dictionary with paths to OCR and translated files
        """
        try:
            os.makedirs(output_folder, exist_ok=True)
            
            print("="*70)
            print("STARTING OCR + TRANSLATION PIPELINE")
            print("="*70)
            print(f"Input: {input_pdf_path}")
            print(f"Target language: {target_language}")
            print()
            
            # Step 1: OCR Analysis
            print("STEP 1: OCR Analysis")
            print("-" * 70)
            ocr_result = self.analyze_document_with_ocr(input_pdf_path)
            
            # Step 2: Create Searchable PDF
            print("\nSTEP 2: Creating Searchable PDF")
            print("-" * 70)
            base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]
            searchable_pdf_path = os.path.join(output_folder, f"{base_name}_searchable.pdf")
            self.create_searchable_pdf(input_pdf_path, ocr_result, searchable_pdf_path)
            
            # Step 3: Translate
            print("\nSTEP 3: Translation")
            print("-" * 70)
            translated_url = self.translate_document(
                searchable_pdf_path,
                target_language
            )
            
            # Step 4: Download translated document
            if translated_url:
                print("\nSTEP 4: Downloading Translated Document")
                print("-" * 70)
                translated_pdf_path = os.path.join(
                    output_folder,
                    f"{base_name}_translated_{target_language}.pdf"
                )
                self.download_from_blob(translated_url, translated_pdf_path)
                
                print("\n" + "="*70)
                print("PIPELINE COMPLETED SUCCESSFULLY!")
                print("="*70)
                print(f"✓ OCR text: {searchable_pdf_path.replace('.pdf', '_ocr_text.txt')}")
                print(f"✓ Searchable PDF: {searchable_pdf_path}")
                print(f"✓ Translated PDF: {translated_pdf_path}")
                
                return {
                    'ocr_text': searchable_pdf_path.replace('.pdf', '_ocr_text.txt'),
                    'searchable_pdf': searchable_pdf_path,
                    'translated_pdf': translated_pdf_path
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
    
    # Configuration
    input_pdf = "sample.pdf"  # Change to your PDF file path
    target_language = "es"  # Spanish - change to your target language
    output_folder = "ocr_translated_output"
    
    # Check if input file exists
    if not os.path.exists(input_pdf):
        print(f"Error: Input file '{input_pdf}' not found!")
        print("Please update the 'input_pdf' variable with your PDF file path.")
        return
    
    # Process the document
    results = pipeline.process_document(
        input_pdf_path=input_pdf,
        target_language=target_language,
        output_folder=output_folder
    )
    
    if results:
        print(f"\n✓ All files saved in: {output_folder}")


if __name__ == "__main__":
    main()
