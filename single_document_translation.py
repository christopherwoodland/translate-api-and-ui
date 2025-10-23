"""
Single Document Translation Script
Translates a single PDF document using Azure Translator Service with auto language detection.
"""

import os
import time
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SingleDocumentTranslator:
    def __init__(self):
        """Initialize the translator with Azure credentials."""
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
    
    def upload_document_to_blob(self, file_path, container_name):
        """
        Upload a document to Azure Blob Storage.
        
        Args:
            file_path: Path to the local PDF file
            container_name: Name of the blob container
            
        Returns:
            URL of the uploaded blob with SAS token
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
            
            # Upload the file
            blob_name = os.path.basename(file_path)
            blob_client = container_client.get_blob_client(blob_name)
            
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                print(f"Uploaded {blob_name} to container {container_name}")
            
            # Generate SAS token for the blob with proper permissions
            sas_token = generate_blob_sas(
                account_name=self.storage_account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=self.storage_account_key,
                permission=BlobSasPermissions(read=True, list=True),
                expiry=datetime.utcnow() + timedelta(hours=24)
            )
            
            blob_url_with_sas = f"{blob_client.url}?{sas_token}"
            return blob_url_with_sas
            
        except Exception as e:
            print(f"Error uploading document: {e}")
            raise
    
    def translate_document(self, input_file_path, target_language, source_container="source", target_container="target"):
        """
        Translate a single PDF document.
        
        Args:
            input_file_path: Path to the input PDF file
            target_language: Target language code (e.g., 'es', 'fr', 'de')
            source_container: Name of the source blob container
            target_container: Name of the target blob container
            
        Returns:
            URL of the translated document
        """
        try:
            print(f"Starting translation of {input_file_path} to {target_language}")
            
            # Upload source document
            print("Uploading source document...")
            source_blob_url = self.upload_document_to_blob(input_file_path, source_container)
            
            # Get target container URL with SAS token
            target_container_client = self.blob_service_client.get_container_client(target_container)
            try:
                # Set public access to blob level for Azure Translator to write results
                target_container_client.create_container(public_access='blob')
                print(f"Created target container: {target_container}")
            except Exception as e:
                print(f"Target container {target_container} already exists or creation failed: {e}")
            
            target_sas_token = generate_blob_sas(
                account_name=self.storage_account_name,
                container_name=target_container,
                blob_name="",
                account_key=self.storage_account_key,
                permission=BlobSasPermissions(write=True, read=True, list=True),
                expiry=datetime.utcnow() + timedelta(hours=24)
            )
            
            target_container_url = f"https://{self.storage_account_name}.blob.core.windows.net/{target_container}?{target_sas_token}"
            
            # Set up translation
            print("Starting translation job...")
            translation_input = DocumentTranslationInput(
                source_url=source_blob_url,
                targets=[
                    TranslationTarget(
                        target_url=target_container_url,
                        language=target_language
                    )
                ]
            )
            
            # Start translation
            poller = self.translation_client.begin_translation([translation_input])
            
            print("Translation job submitted. Waiting for completion...")
            result = poller.result()
            
            # Check results
            for document in result:
                if document.status == "Succeeded":
                    print(f"✓ Translation completed successfully!")
                    print(f"  Source document: {document.source_document_url}")
                    print(f"  Translated document: {document.translated_document_url}")
                    print(f"  Detected source language: {document.source_language if hasattr(document, 'source_language') else 'auto-detected'}")
                    print(f"  Target language: {target_language}")
                    return document.translated_document_url
                elif document.status == "Failed":
                    print(f"✗ Translation failed!")
                    print(f"  Error code: {document.error.code if document.error else 'Unknown'}")
                    print(f"  Error message: {document.error.message if document.error else 'Unknown'}")
                    return None
                else:
                    print(f"  Status: {document.status}")
            
        except Exception as e:
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
    translated_url = translator.translate_document(
        input_file_path=input_pdf,
        target_language=target_language
    )
    
    if translated_url:
        # Download the translated document
        translator.download_translated_document(translated_url, output_pdf)
        print(f"\n✓ Translation complete! Output saved to: {output_pdf}")
    else:
        print("\n✗ Translation failed.")


if __name__ == "__main__":
    main()
