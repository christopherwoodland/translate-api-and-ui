# Azure Document Translation

A complete solution for translating PDF documents using Azure Translator Service and Azure Document Intelligence, with both a **Web UI** and **Command-Line Scripts**.

## 🎯 Features

- **🌐 Web UI**: User-friendly interface for uploading PDFs and running translations
- **Single Document Translation**: Translate one PDF at a time with auto language detection
- **Batch Translation**: Process multiple PDFs simultaneously to multiple target languages
- **OCR + Translation Pipeline**: Convert scanned/image PDFs to searchable format before translation
- **Real-time Progress Tracking**: Monitor translation jobs with live status updates
- **Multiple Language Support**: Translate to 20+ popular languages (100+ total supported)

## Prerequisites

### Azure Resources Required

1. **Azure Translator Service**
   - Create a Translator resource in Azure Portal
   - Get the endpoint URL and API key
   - Documentation: https://learn.microsoft.com/azure/cognitive-services/translator/

2. **Azure Storage Account**
   - Required for document translation (service uses blob storage)
   - Create a storage account with blob service enabled
   - Get connection string, account name, and account key
   - Documentation: https://learn.microsoft.com/azure/storage/

3. **Azure Document Intelligence** (for OCR script only)
   - Create a Document Intelligence resource
   - Get the endpoint URL and API key
   - Documentation: https://learn.microsoft.com/azure/ai-services/document-intelligence/

### Python Requirements

- Python 3.8 or higher
- pip (Python package installer)

## Installation

### 1. Clone or Download the Scripts

```powershell
cd c:\Users\cwoodland\dev\translate-api-and-ui
```

### 2. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

This will install:
- `azure-ai-translation-document` - Azure Translator SDK
- `azure-ai-formrecognizer` - Azure Document Intelligence SDK
- `azure-storage-blob` - Azure Blob Storage SDK
- `azure-identity` - Azure authentication
- `python-dotenv` - Environment variable management

### 3. Configure Azure Credentials

Copy the template file and add your credentials:

```powershell
Copy-Item .env.template .env
```

Edit `.env` file and fill in your Azure credentials:

```env
AZURE_TRANSLATOR_ENDPOINT=https://your-translator-resource.cognitiveservices.azure.com/
AZURE_TRANSLATOR_KEY=your-translator-key-here

AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intelligence-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-doc-intelligence-key-here

AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your-account;AccountKey=your-key;EndpointSuffix=core.windows.net
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account-name
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key
```

**Important**: Never commit the `.env` file to source control!

## 🚀 Quick Start

### Option 1: Web UI (Recommended)

The easiest way to use the translation services:

1. **Start the web server:**
   ```powershell
   python app.py
   ```

2. **Open your browser:**
   Navigate to `http://localhost:5000`

3. **Use the interface:**
   - Select translation type (Single, Batch, or OCR)
   - Upload your PDF file(s)
   - Choose target language(s)
   - Click "Start Translation"
   - Download your translated files

**Web UI Features:**
- ✅ Drag-and-drop file upload
- ✅ Real-time progress tracking
- ✅ Support for all three translation types
- ✅ Easy language selection from 20+ languages
- ✅ One-click downloads of results
- ✅ Mobile-responsive design

### Option 2: Command-Line Scripts

For automation or advanced usage, use the Python scripts directly.

### Script 1: Single Document Translation

Translates one PDF document at a time with automatic language detection.

```powershell
python single_document_translation.py
```

**Configuration** (edit the script's `main()` function):
```python
input_pdf = "sample.pdf"  # Your PDF file path
target_language = "es"     # Target language code
```

**Supported Language Codes**:
- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ja` - Japanese
- `zh-Hans` - Chinese (Simplified)
- [See full list](https://learn.microsoft.com/azure/cognitive-services/translator/language-support)

**Output**: Creates `translated_{lang}_{filename}.pdf` in the current directory

### Script 2: Batch Translation

Translates multiple PDFs to multiple languages simultaneously.

```powershell
python batch_translation.py
```

**Configuration** (edit the script's `main()` function):
```python
input_folder = "input_pdfs"                  # Folder with PDF files
target_languages = ["es", "fr", "de"]        # List of target languages
output_base_folder = "translated_output"     # Output folder
```

**Setup**:
1. Create an `input_pdfs` folder
2. Place your PDF files in it
3. Run the script

**Output**: Creates `translated_output/{language}/` folders with translated PDFs

**Example**:
```
translated_output/
├── es/
│   ├── document1.pdf
│   └── document2.pdf
├── fr/
│   ├── document1.pdf
│   └── document2.pdf
└── de/
    ├── document1.pdf
    └── document2.pdf
```

### Script 3: OCR + Translation Pipeline

Converts scanned/image PDFs to searchable format using OCR, then translates.

```powershell
python ocr_translation_pipeline.py
```

**Configuration** (edit the script's `main()` function):
```python
input_pdf = "sample.pdf"                      # Your PDF file
target_language = "es"                        # Target language
output_folder = "ocr_translated_output"       # Output folder
```

**Pipeline Steps**:
1. ✓ Analyze PDF with Azure Document Intelligence OCR
2. ✓ Extract text and create searchable PDF
3. ✓ Translate the searchable PDF
4. ✓ Download the translated result

**Output**:
- `{filename}_ocr_text.txt` - Extracted text from OCR
- `{filename}_searchable.pdf` - Searchable PDF with OCR data
- `{filename}_translated_{lang}.pdf` - Final translated PDF

**Use Cases**:
- Scanned documents
- Image-based PDFs
- Documents with poor text recognition
- Historical documents

## Troubleshooting

### Common Issues

#### 1. Import Errors
```
ImportError: No module named 'azure.ai.translation.document'
```
**Solution**: Install dependencies
```powershell
pip install -r requirements.txt
```

#### 2. Authentication Errors
```
Error: Missing required Azure credentials
```
**Solution**: Check your `.env` file has all required values

#### 3. Storage Access Errors
```
Error: Failed to upload to blob storage
```
**Solution**: 
- Verify storage connection string is correct
- Ensure storage account has blob service enabled
- Check firewall settings allow your IP

#### 4. Translation Fails
```
Error: Translation failed
```
**Possible causes**:
- Invalid language code
- File too large (max 40MB per file)
- Unsupported file format
- Insufficient quota/credits

### Getting Azure Credentials

#### Translator Endpoint and Key:
1. Go to Azure Portal: https://portal.azure.com
2. Navigate to your Translator resource
3. Click "Keys and Endpoint" in the left menu
4. Copy KEY 1 and Endpoint

#### Storage Connection String:
1. Go to your Storage Account in Azure Portal
2. Click "Access keys" in the left menu
3. Copy "Connection string" from key1 or key2

#### Document Intelligence Endpoint and Key:
1. Go to your Document Intelligence resource
2. Click "Keys and Endpoint"
3. Copy KEY 1 and Endpoint

## Azure Cost Considerations

### Translator Service
- **Free Tier**: 2M characters/month
- **Standard Tier**: $10 per 1M characters
- Document translation may incur additional charges

### Storage Account
- **LRS (Locally Redundant)**: ~$0.02 per GB/month
- Transaction costs: Minimal for this use case

### Document Intelligence
- **Free Tier**: 500 pages/month
- **Standard Tier**: $1.50 per 1,000 pages

## Security Best Practices

1. **Never commit `.env` file** to version control
2. **Use Azure Key Vault** for production environments
3. **Rotate keys regularly** (every 90 days recommended)
4. **Use Managed Identity** when running in Azure
5. **Enable Storage Firewall** to restrict access
6. **Monitor usage** to detect anomalies

## Language Support

Azure Translator supports 100+ languages. Common codes:

| Language | Code | Language | Code |
|----------|------|----------|------|
| English | en | Spanish | es |
| French | fr | German | de |
| Italian | it | Portuguese | pt |
| Japanese | ja | Korean | ko |
| Chinese (Simplified) | zh-Hans | Chinese (Traditional) | zh-Hant |
| Arabic | ar | Russian | ru |
| Hindi | hi | Dutch | nl |

Full list: https://learn.microsoft.com/azure/cognitive-services/translator/language-support

## Advanced Configuration

### Custom Storage Containers

You can customize container names in each script:

```python
# Single document translation
translator.translate_document(
    input_file_path=input_pdf,
    target_language=target_language,
    source_container="my-source",      # Custom name
    target_container="my-target"       # Custom name
)
```

### Batch Processing Multiple Languages

```python
target_languages = [
    "es",      # Spanish
    "fr",      # French
    "de",      # German
    "it",      # Italian
    "pt",      # Portuguese
    "ja",      # Japanese
    "ko",      # Korean
    "zh-Hans"  # Chinese Simplified
]
```

### Error Handling

All scripts include comprehensive error handling. Check console output for detailed error messages.

## 📁 File Structure

```
translate-api-and-ui/
├── app.py                            # 🌐 Flask web application
├── templates/
│   └── index.html                    # Web UI interface
├── static/
│   ├── css/
│   │   └── style.css                 # UI styling
│   └── js/
│       └── app.js                    # UI interactivity
├── .env                              # Your credentials (DO NOT COMMIT)
├── .env.template                     # Template for credentials
├── requirements.txt                  # Python dependencies
├── single_document_translation.py    # Script 1: Single translation
├── batch_translation.py              # Script 2: Batch translation
├── ocr_translation_pipeline.py       # Script 3: OCR + Translation
├── README.md                         # This file
├── input_pdfs/                       # Input folder for batch processing
└── output folders/                   # Created automatically
```

## Support and Documentation

- **Azure Translator**: https://learn.microsoft.com/azure/cognitive-services/translator/
- **Azure Document Intelligence**: https://learn.microsoft.com/azure/ai-services/document-intelligence/
- **Azure Storage**: https://learn.microsoft.com/azure/storage/
- **Python SDK Docs**: https://learn.microsoft.com/python/api/overview/azure/

## License

These scripts are provided as-is for use with Azure services.

## Contributing

Feel free to enhance these scripts with additional features:
- Progress bars
- Email notifications
- Webhook integration
- Custom file naming
- Metadata preservation
- Format conversion

---

**Questions or Issues?**
Check the Azure Portal for service health and quotas, or review the troubleshooting section above.
