# Azure Document Translation

A complete solution for translating **25+ document formats** using Azure Translator Service and Azure Document Intelligence, with both a **Web UI** and **Command-Line Scripts**.

## 🎯 Features

- **🌐 Web UI**: User-friendly interface for uploading documents and running translations
- **25+ File Format Support**: PDF, Microsoft Office (Word/Excel/PowerPoint), OpenDocument, text files, HTML, Markdown, email messages, localization files, CSV/TSV data, and images
- **Single Document Translation**: Translate one document at a time with auto language detection
- **Batch Translation**: Process multiple documents simultaneously to multiple target languages
- **OCR + Translation Pipeline**: Extract text from scanned/image documents (including JPG, PNG, TIFF), then translate - supports all 25+ file formats
- **Source Language Selection**: Choose from 100+ source languages or use auto-detect
- **Detected Language Display**: Shows detected source language for each document in results and logs
- **Real-time Progress Tracking**: Monitor translation jobs with live status updates
- **Multiple Language Support**: Translate to 100+ languages with easy language selection
- **Visual File Type Icons**: Dynamic icons for each supported format (📘 Word, 📗 Excel, 📙 PowerPoint, 🌐 HTML, 📷 Images, etc.)
- **Comprehensive Logging**: Detailed logs saved to `translation_app.log` for troubleshooting and monitoring
- **Managed Identity Support**: Optional Azure Managed Identity authentication for production environments
- **Smart Download Buttons**: Download buttons automatically show correct file type (not just "PDF")

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
   
   **Alternative**: Double-click `start_web_ui.bat` (Windows) which will:
   - Create virtual environment if needed
   - Install dependencies if needed
   - Check for .env file
   - Start the server automatically

2. **Open your browser:**
   Navigate to `http://localhost:5000`

3. **Use the interface:**
   
   **Step 1: Choose Translation Type**
   - **Single Translation**: One document → One language (quick translations)
   - **Batch Translation**: Multiple documents → Multiple languages (bulk processing)
   - **OCR + Translation**: Scanned/image documents → Extract text → Translate

   **Step 2: Upload Files**
   - Drag and drop files, or click "Browse Files"
   - Supports all 25+ formats (PDF, Office docs, images, text, HTML, etc.)
   - Max 100MB per file
   - Single/OCR: 1 file only | Batch: Multiple files

   **Step 3: Select Languages**
   - Source: Choose specific language or "Auto-detect" (recommended)
   - Target: Select one or more languages from 100+ options
   - Use search box to find languages quickly

   **Step 4: Start Translation**
   - Click "Start Translation"
   - Watch real-time progress with live updates
   - View detected source language in results (shown per document)
   - Download translated files when complete

**Web UI Features:**
- ✅ Drag-and-drop file upload for all 25+ formats
- ✅ Source language selection (100+ languages) or auto-detect
- ✅ Detected language display in results (per document for batch)
- ✅ Real-time progress tracking with detailed status
- ✅ Support for all three translation types (Single, Batch, OCR)
- ✅ Easy target language selection from 100+ languages with search
- ✅ Smart download buttons showing actual file type
- ✅ One-click downloads of results
- ✅ Mobile-responsive design
- ✅ Visual file type icons for uploaded documents

### Option 2: Command-Line Scripts

For automation or advanced usage, use the Python scripts directly.

### Script 1: Single Document Translation

Translates one document at a time with automatic language detection.

```powershell
python single_document_translation.py
```

**Configuration** (edit the script's `main()` function):
```python
input_file = "sample.docx"  # Your document file path (any supported format)
source_language = None       # Optional: Specify source (e.g., "en") or None for auto-detect
target_language = "es"       # Target language code
```

**Supported File Formats**:
- **PDF**: .pdf
- **Microsoft Office**: .doc, .docx, .xls, .xlsx, .ppt, .pptx
- **OpenDocument**: .odt, .ods, .odp
- **Text**: .txt, .rtf
- **Markup**: .html, .htm, .mhtml, .mht, .md, .markdown, .mkdn, .mdown, .mdwn
- **Email**: .msg
- **Localization**: .xlf, .xliff
- **Data**: .csv, .tsv, .tab

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

**Output**: Creates `translated_{lang}_{filename}` with original extension in the current directory

### Script 2: Batch Translation

Translates multiple documents to multiple languages simultaneously. Supports all 25+ file formats.

```powershell
python batch_translation.py
```

**Configuration** (edit the script's `main()` function):
```python
input_folder = "input_documents"             # Folder with document files (any supported format)
source_language = None                       # Optional: Specify source (e.g., "en") or None for auto-detect
target_languages = ["es", "fr", "de"]        # List of target languages
output_base_folder = "translated_output"     # Output folder
```

**Setup**:
1. Create an `input_documents` folder
2. Place your document files in it (Word, Excel, PDF, text files, etc.)
3. Run the script

**Output**: Creates `translated_output/{language}/` folders with translated documents

**Example**:
```text
translated_output/
├── es/
│   ├── document1.docx
│   ├── spreadsheet.xlsx
│   └── report.pdf
├── fr/
│   ├── document1.docx
│   ├── spreadsheet.xlsx
│   └── report.pdf
└── de/
    ├── document1.docx
    ├── spreadsheet.xlsx
    └── report.pdf
```

### Script 3: OCR + Translation Pipeline

Extracts text from any document using OCR (Azure Document Intelligence), then translates. **Supports all 25+ file formats including images (.jpg, .png, .bmp, .tiff)**.

```powershell
python ocr_translation_pipeline.py
```

**Configuration** (edit the script's `main()` function):
```python
input_file = "scanned_doc.pdf"                # Any supported format
# Examples:
# input_file = "scan.jpg"                     # Image file
# input_file = "document.docx"                # Word with images
# input_file = "presentation.pptx"            # PowerPoint
source_language = None                        # Optional: Specify source or None for auto-detect
target_language = "es"                        # Target language
output_folder = "ocr_translated_output"       # Output folder
```

**Pipeline Steps**:
1. ✓ OCR analysis with Azure Document Intelligence (extracts text from any format)
2. ✓ Create text file with extracted OCR content
3. ✓ Translate the document with embedded OCR text
4. ✓ Download the translated result

**Output**:
- `{filename}_searchable_ocr_text.txt` - Extracted text from OCR
- `{filename}_searchable.{ext}` - Document with OCR data (preserves original format)
- `{filename}_translated_{lang}.{ext}` - Final translated document (same format as input)

**Supported Formats**:
- **Documents**: PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx), OpenDocument
- **Images**: JPG, PNG, BMP, TIFF (perfect for scanned documents)
- **Text**: TXT, RTF, HTML, Markdown
- **And 25+ more formats!**

**Use Cases**:
- Scanned documents (receipts, invoices, forms)
- Photos of documents (phone camera captures)
- Image-based PDFs
- Documents with poor text quality
- Historical documents
- Mixed text/image content
- Handwritten notes (with OCR capability)

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
- Verify container permissions allow blob access

#### 4. Translation Fails

```text
Error: Translation failed
```

**Possible causes**:
- Invalid language code
- File too large (max 40MB per file)
- Unsupported file format (check the supported list above)
- Insufficient quota/credits
- Document contains protected content or DRM

#### 5. Permission/Access Level Errors

```
InvalidDocumentAccessLevel: Azure Translator cannot access blob storage
```

**Solution**: This typically occurs when SAS tokens have insufficient permissions
- Container public access should be set to `blob` level
- SAS tokens need both `read` and `list` permissions
- This is automatically handled by the scripts
- If using custom storage setup, verify these settings

#### 6. OCR Translation Issues

**For scanned or image documents:**
- Use the "OCR + Translation" mode (not Single or Batch)
- Supported image formats: JPG, PNG, TIFF, BMP
- Ensure Azure Document Intelligence is configured in `.env`
- Check that document quality is sufficient for text recognition

#### 7. Web UI Not Starting

```
Error: Address already in use
```

**Solution**: Port 5000 is already in use
```powershell
# Find and stop the process using port 5000
netstat -ano | findstr :5000
taskkill /PID <process-id> /F
```

#### 8. File Download Issues

**Downloads not working or showing wrong file type:**
- Check browser console for JavaScript errors
- Verify files exist in `outputs/` folder
- Clear browser cache and try again
- Ensure file permissions allow reading from outputs folder

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

## 🔐 Managed Identity Support

The application supports **Azure Managed Identity** for secure authentication in Azure-hosted environments (Azure App Service, Azure Functions, Azure VMs).

**Benefits:**
- ✅ No credentials stored in code or configuration files
- ✅ Automatic credential rotation
- ✅ Enhanced security for production deployments
- ✅ Simplified credential management
- ✅ Better compliance and audit trail with Azure AD

### Authentication Methods

**Local Development (Key-Based):**
- Uses `AZURE_STORAGE_CONNECTION_STRING` or `AZURE_STORAGE_ACCOUNT_KEY`
- Generates SAS tokens for blob access
- Best for local development and testing

**Production (Managed Identity):**
- Uses Azure Managed Identity credentials
- No SAS tokens needed - direct authentication
- Best for Azure App Service, Container Apps, VMs
- No storage keys required

### Setup for Managed Identity (Production)

**Step 1: Enable System-Assigned Managed Identity**

For Azure App Service:
```bash
az webapp identity assign \
  --name <your-app-name> \
  --resource-group <your-resource-group>
```

For Azure Container Apps:
```bash
az containerapp identity assign \
  --name <your-app-name> \
  --resource-group <your-resource-group> \
  --system-assigned
```

Save the **Principal ID** from the output - you'll need it in Step 2.

**Step 2: Assign Storage Blob Data Contributor Role**

Via Azure Portal:
1. Navigate to your Storage Account
2. Click **Access Control (IAM)**
3. Click **+ Add** → **Add role assignment**
4. Select **Storage Blob Data Contributor** role
5. Select **Managed identity** and find your app
6. Click **Select** → **Review + assign**

Via Azure CLI:
```bash
# Get storage account resource ID
STORAGE_ID=$(az storage account show \
  --name <storage-account-name> \
  --resource-group <storage-resource-group> \
  --query id --output tsv)

# Assign role using Principal ID from Step 1
az role assignment create \
  --assignee <principal-id> \
  --role "Storage Blob Data Contributor" \
  --scope $STORAGE_ID
```

**Step 3: Configure Environment Variables**

In your Azure service, set these environment variables:

```bash
# Required
AZURE_TRANSLATOR_ENDPOINT=https://your-translator.cognitiveservices.azure.com/
AZURE_TRANSLATOR_KEY=your-key
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-doc-intel.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_KEY=your-key
AZURE_STORAGE_ACCOUNT_NAME=your-storage-name

# Enable Managed Identity
USE_MANAGED_IDENTITY=true

# NOT required with Managed Identity (omit these):
# AZURE_STORAGE_CONNECTION_STRING
# AZURE_STORAGE_ACCOUNT_KEY
```

**Step 4: Deploy and Test**

Deploy your application and verify authentication in logs:
```
Using Azure Managed Identity for authentication
```

### Auto-Detection

The application automatically chooses authentication method:
- If `AZURE_STORAGE_CONNECTION_STRING` is set → Uses key-based auth
- If `AZURE_STORAGE_CONNECTION_STRING` is NOT set → Uses Managed Identity
- Can override with `USE_MANAGED_IDENTITY=true/false`

### Migration from Key-Based to Managed Identity

**Current (Local Development):**
```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
USE_MANAGED_IDENTITY=false  # or omit
```

**New (Azure Production):**
```env
AZURE_STORAGE_ACCOUNT_NAME=your-storage-name
USE_MANAGED_IDENTITY=true
# Remove AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_ACCOUNT_KEY
```

### Troubleshooting Managed Identity

**"DefaultAzureCredential failed to retrieve a token"**
- Verify Managed Identity is enabled on your Azure resource
- Check role assignment (Storage Blob Data Contributor)
- Wait 5-10 minutes for role propagation

**"This request is not authorized"**
- Ensure role is **Storage Blob Data Contributor** (not just Reader)
- Verify role assigned to correct Managed Identity

**For Local Development:**
- Managed Identity only works in Azure environments
- Use `USE_MANAGED_IDENTITY=false` and connection string for local testing

## 📊 Logging and Monitoring

The application includes comprehensive logging for troubleshooting and monitoring:

**Log File:** `translation_app.log` (created automatically)

**What's Logged:**
- ✅ Translation job start/completion with job IDs
- ✅ Detected source language for each document
- ✅ Target languages selected
- ✅ File uploads and formats
- ✅ Container creation and blob operations
- ✅ Errors with detailed stack traces
- ✅ Processing times and progress updates

**Log Format:**
```
2025-10-23 14:30:45 - app - INFO - Job abc123: ✓ Source language detected: auto-detected
2025-10-23 14:30:45 - app - INFO - Job abc123: → Target language: es
2025-10-23 14:31:12 - app - INFO - Job abc123: Completed successfully
```

**Viewing Logs:**
- Console output shows real-time progress
- Check `translation_app.log` for detailed history
- Logs include emoji indicators (✓, →, ✗) for easy scanning

## Advanced Configuration

### Implementation Details

**Authentication Architecture:**

The application uses auto-detection to choose the authentication method:

```python
def __init__(self, use_managed_identity=None):
    # Auto-detect authentication method
    if use_managed_identity is None:
        use_managed_identity = not bool(self.storage_connection_string)
    
    self.use_managed_identity = use_managed_identity
```

**Key-Based Authentication Flow:**
1. `BlobServiceClient.from_connection_string()` uses storage keys
2. SAS tokens generated for source and target containers
3. URLs include SAS tokens: `https://account.blob.core.windows.net/container?sv=2021...`
4. Azure Translator accesses blobs using SAS token permissions

**Managed Identity Flow:**
1. `DefaultAzureCredential()` authenticates using Azure Managed Identity
2. `BlobServiceClient` uses credential directly (no keys)
3. No SAS tokens generated
4. Azure Translator accesses blobs using system identity
5. Plain URLs without SAS tokens: `https://account.blob.core.windows.net/container/blob`

**Environment Variable Precedence:**
- If `AZURE_STORAGE_CONNECTION_STRING` is set → Key-based authentication
- If `AZURE_STORAGE_CONNECTION_STRING` is NOT set → Managed Identity
- Can be overridden with explicit `USE_MANAGED_IDENTITY=true/false`

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

```text
translate-api-and-ui/
├── app.py                            # 🌐 Flask web application
├── templates/
│   └── index.html                    # Web UI interface
├── static/
│   ├── css/
│   │   └── style.css                 # UI styling
│   └── js/
│       └── app.js                    # UI interactivity (file type icons & validation)
├── .env                              # Your credentials (DO NOT COMMIT)
├── .env.template                     # Template for credentials
├── requirements.txt                  # Python dependencies
├── single_document_translation.py    # Script 1: Single translation (25+ formats)
├── batch_translation.py              # Script 2: Batch translation (25+ formats)
├── ocr_translation_pipeline.py       # Script 3: OCR + Translation
├── translation_app.log               # Application log file (auto-generated)
├── README.md                         # This file
├── input_documents/                  # Input folder for batch processing (any format)
└── output folders/                   # Created automatically
```

## Support and Documentation

- **Azure Translator**: https://learn.microsoft.com/azure/cognitive-services/translator/
- **Azure Document Intelligence**: https://learn.microsoft.com/azure/ai-services/document-intelligence/
- **Azure Storage**: https://learn.microsoft.com/azure/storage/
- **Python SDK Docs**: https://learn.microsoft.com/python/api/overview/azure/

## License

These scripts are provided as-is for use with Azure services.

## 🎨 File Type Support Details

The application uses visual icons to represent different file types:

- 📕 **PDF**: Standard PDF documents
- 📘 **Word**: .doc, .docx files
- 📗 **Excel**: .xls, .xlsx spreadsheets
- 📙 **PowerPoint**: .ppt, .pptx presentations
- 📓 **OpenDocument**: .odt, .ods, .odp files
- 📄 **Text**: .txt, .rtf files
- 🌐 **HTML**: .html, .htm, .mhtml, .mht files
- 📋 **Markdown**: .md, .markdown, .mkdn, .mdown, .mdwn files
- 📧 **Email**: .msg files
- 🌍 **Localization**: .xlf, .xliff files
- 📊 **Data**: .csv, .tsv, .tab files

All formats are natively supported by Azure Translator's Document Translation API with no conversion needed.

## Contributing

Feel free to enhance these scripts with additional features:

- Progress bars
- Email notifications
- Webhook integration
- Custom file naming
- Metadata preservation
- Format conversion
- Additional file format support

---

**Questions or Issues?**
Check the Azure Portal for service health and quotas, or review the troubleshooting section above.
