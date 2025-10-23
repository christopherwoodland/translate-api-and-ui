# 🚀 Quick Start Guide - Web UI

## Setup (First Time Only)

1. **Install Python packages:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **Configure Azure credentials:**
   - Open the `.env` file
   - Fill in your Azure credentials:
     - Translator endpoint and key
     - Document Intelligence endpoint and key
     - Storage account connection string, name, and key

## Running the Web UI

1. **Start the server:**
   ```powershell
   python app.py
   ```

2. **Open your browser:**
   - Navigate to: `http://localhost:5000`
   - The UI will load automatically

3. **Use the interface:**
   
   **Step 1: Choose Translation Type**
   - **Single Translation**: One PDF → One language
   - **Batch Translation**: Multiple PDFs → Multiple languages
   - **OCR + Translation**: Scanned PDF → Searchable → Translated

   **Step 2: Upload PDF Files**
   - Drag and drop PDF files, or click "Browse Files"
   - Max 100MB per file
   - Single/OCR: 1 file only
   - Batch: Multiple files allowed

   **Step 3: Select Target Language(s)**
   - Single/OCR: Select exactly 1 language
   - Batch: Select 1 or more languages
   - Use the search box to find languages quickly

   **Step 4: Start Translation**
   - Click "Start Translation"
   - Watch real-time progress
   - Download your files when complete!

## Common Languages

| Language | Code | Language | Code |
|----------|------|----------|------|
| English | en | Spanish | es |
| French | fr | German | de |
| Italian | it | Portuguese | pt |
| Japanese | ja | Korean | ko |
| Chinese (Simplified) | zh-Hans | Arabic | ar |

## Troubleshooting

**"Import errors" when starting:**
- Run: `pip install -r requirements.txt`

**"Missing credentials" error:**
- Check your `.env` file has all required values

**Translation fails:**
- Verify Azure credentials are correct
- Check you have sufficient quota in Azure
- Ensure file is a valid PDF (not scanned if using Single/Batch)

**For scanned/image PDFs:**
- Use the "OCR + Translation" option
- This requires Azure Document Intelligence to be configured

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Need Help?

Check the full README.md for detailed documentation, troubleshooting, and advanced configuration options.
