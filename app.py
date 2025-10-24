"""
Web UI for Azure Document Translation
Flask application for uploading PDFs and running translation scripts
"""

import os
import json
import logging
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Import our translation modules
from single_document_translation import SingleDocumentTranslator
from batch_translation import BatchDocumentTranslator
from ocr_translation_pipeline import OCRTranslationPipeline

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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {
    # PDF
    'pdf',
    # Microsoft Office
    'doc', 'docx',
    'xls', 'xlsx',
    'ppt', 'pptx',
    # OpenDocument
    'odt', 'ods', 'odp',
    # Text and Markup
    'rtf', 'txt',
    'html', 'htm', 'mhtml', 'mht',
    'md', 'markdown', 'mkdn', 'mdown', 'mdwn',
    # Email and Localization
    'msg',
    'xlf', 'xliff',
    # Data Files
    'csv', 'tsv', 'tab'
}

# Authentication configuration
# Set USE_MANAGED_IDENTITY=true in .env to use Azure Managed Identity (for Azure-hosted environments)
# Otherwise, uses key-based authentication (for local development)
USE_MANAGED_IDENTITY = os.getenv('USE_MANAGED_IDENTITY', 'false').lower() == 'true'

logger.info(f"Flask app starting - Managed Identity: {USE_MANAGED_IDENTITY}")
logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
logger.info(f"Output folder: {app.config['OUTPUT_FOLDER']}")

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store job status
jobs = {}


def sanitize_container_name(name):
    """
    Sanitize a name to be valid for Azure Blob Storage containers.
    Container names must:
    - Be 3-63 characters long
    - Contain only lowercase letters, numbers, and hyphens
    - Start and end with a letter or number
    - Not contain consecutive hyphens
    """
    # Convert to lowercase and replace underscores with hyphens
    sanitized = name.lower().replace('_', '-')
    # Remove any characters that aren't alphanumeric or hyphen
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '-')
    # Remove consecutive hyphens
    while '--' in sanitized:
        sanitized = sanitized.replace('--', '-')
    # Remove leading/trailing hyphens
    sanitized = sanitized.strip('-')
    # Ensure it starts with alphanumeric
    if sanitized and not sanitized[0].isalnum():
        sanitized = 'c' + sanitized
    # Truncate to 63 characters if needed
    if len(sanitized) > 63:
        sanitized = sanitized[:63].rstrip('-')
    # Ensure minimum 3 characters
    if len(sanitized) < 3:
        sanitized = sanitized + 'xyz'
    return sanitized


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


class JobStatus:
    """Track job execution status."""
    def __init__(self, job_id, job_type):
        self.job_id = job_id
        self.job_type = job_type
        self.status = "pending"
        self.progress = 0
        self.message = "Job queued"
        self.result = None
        self.error = None
        self.started_at = datetime.now().isoformat()
        self.completed_at = None
    
    def update(self, status=None, progress=None, message=None, result=None, error=None):
        """Update job status."""
        if status:
            self.status = status
        if progress is not None:
            self.progress = progress
        if message:
            self.message = message
        if result:
            self.result = result
        if error:
            self.error = error
        if status in ["completed", "failed"]:
            self.completed_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert to dictionary for JSON response."""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'result': self.result,
            'error': self.error,
            'started_at': self.started_at,
            'completed_at': self.completed_at
        }


def run_single_translation(job_id, file_path, target_language, source_language=None):
    """Run single document translation in background."""
    logger.info(f"Starting single translation job {job_id}: {file_path} -> {target_language}")
    if source_language:
        logger.info(f"Job {job_id}: Source language specified as {source_language}")
    
    job = jobs[job_id]
    try:
        job.update(status="running", progress=10, message="Initializing translator...")
        logger.debug(f"Job {job_id}: Initializing SingleDocumentTranslator")
        translator = SingleDocumentTranslator(use_managed_identity=USE_MANAGED_IDENTITY)
        
        job.update(progress=30, message="Uploading document to Azure...")
        logger.info(f"Job {job_id}: Starting translation")
        translation_result = translator.translate_document(
            input_file_path=file_path,
            target_language=target_language,
            source_language=source_language
        )
        
        if translation_result:
            job.update(progress=80, message="Downloading translated document...")
            logger.info(f"Job {job_id}: Translation successful, downloading result")
            output_filename = f"translated_{target_language}_{os.path.basename(file_path)}"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            # Handle both old string format and new dict format
            if isinstance(translation_result, dict):
                translated_url = translation_result['url']
                detected_lang = translation_result.get('detected_source_language', 'unknown')
            else:
                translated_url = translation_result
                detected_lang = 'unknown'
            
            # Log detected language prominently
            logger.info(f"Job {job_id}: ✓ Source language detected: {detected_lang}")
            logger.info(f"Job {job_id}: → Target language: {target_language}")
            translator.download_translated_document(translated_url, output_path)
            
            logger.info(f"Job {job_id}: Completed successfully - Output: {output_filename}")
            job.update(
                status="completed",
                progress=100,
                message="Translation completed successfully",
                result={
                    'output_file': output_filename,
                    'download_url': f'/download/{output_filename}',
                    'detected_source_language': detected_lang,
                    'target_language': target_language
                }
            )
        else:
            logger.error(f"Job {job_id}: Translation failed - no URL returned")
            job.update(status="failed", message="Translation failed", error="No translated URL returned")
    
    except Exception as e:
        logger.error(f"Job {job_id}: Exception occurred - {str(e)}", exc_info=True)
        job.update(status="failed", message=f"Error: {str(e)}", error=str(e))


def run_batch_translation(job_id, file_paths, target_languages, source_language=None):
    """Run batch translation in background."""
    logger.info(f"Starting batch translation job {job_id}: {len(file_paths)} files -> {len(target_languages)} languages")
    logger.info(f"Job {job_id}: Target languages: {', '.join(target_languages)}")
    if source_language:
        logger.info(f"Job {job_id}: Source language specified as {source_language}")
    
    job = jobs[job_id]
    try:
        job.update(status="running", progress=10, message="Initializing batch translator...")
        logger.debug(f"Job {job_id}: Initializing BatchDocumentTranslator")
        translator = BatchDocumentTranslator(use_managed_identity=USE_MANAGED_IDENTITY)
        
        # Create a temporary batch folder
        batch_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"batch_{job_id}")
        os.makedirs(batch_folder, exist_ok=True)
        
        # Copy files to batch folder
        job.update(progress=20, message="Preparing batch files...")
        for file_path in file_paths:
            import shutil
            shutil.copy2(file_path, batch_folder)
        
        job.update(progress=40, message=f"Translating to {len(target_languages)} languages...")
        # Sanitize container names to comply with Azure naming rules
        source_container = sanitize_container_name(f"batch-source-{job_id}")
        target_container_prefix = sanitize_container_name(f"batch-target-{job_id}")
        
        batch_results = translator.translate_batch(
            input_folder=batch_folder,
            target_languages=target_languages,
            source_container=source_container,
            target_container_prefix=target_container_prefix,
            source_language=source_language
        )
        
        # Handle both old and new result format
        if isinstance(batch_results, dict) and 'results' in batch_results:
            results = batch_results['results']
            detected_langs = batch_results.get('detected_source_languages', {})
        else:
            results = batch_results
            detected_langs = {}
        
        # Log detected languages for each document
        if detected_langs:
            logger.info(f"Job {job_id}: ✓ Detected source languages:")
            for filename, lang_code in detected_langs.items():
                logger.info(f"Job {job_id}:   • {filename}: {lang_code}")
        else:
            logger.warning(f"Job {job_id}: No detected language information available")
        
        # Download results
        job.update(progress=80, message="Downloading translated documents...")
        output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f"batch_{job_id}")
        
        download_urls = {}
        for lang, documents in results.items():
            if documents:
                lang_output = os.path.join(output_folder, lang)
                # Use sanitized container name
                container_name = sanitize_container_name(f"batch-target-{job_id}-{lang}")
                translator.download_translated_documents(container_name, lang_output)
                
                # Get list of files
                if os.path.exists(lang_output):
                    files = os.listdir(lang_output)
                    download_urls[lang] = [f'/download/batch_{job_id}/{lang}/{f}' for f in files]
        
        job.update(
            status="completed",
            progress=100,
            message=f"Batch translation completed for {len(target_languages)} languages",
            result={
                'output_folder': f"batch_{job_id}",
                'download_urls': download_urls,
                'detected_source_languages': detected_langs,
                'target_languages': target_languages
            }
        )
    
    except Exception as e:
        job.update(status="failed", message=f"Error: {str(e)}", error=str(e))


def run_ocr_translation(job_id, file_path, target_language, source_language=None):
    """Run OCR + translation pipeline in background."""
    job = jobs[job_id]
    try:
        job.update(status="running", progress=10, message="Initializing OCR pipeline...")
        pipeline = OCRTranslationPipeline(use_managed_identity=USE_MANAGED_IDENTITY)
        
        output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f"ocr_{job_id}")
        os.makedirs(output_folder, exist_ok=True)
        
        job.update(progress=20, message="Running OCR analysis...")
        results = pipeline.process_document(
            input_file_path=file_path,
            target_language=target_language,
            output_folder=output_folder,
            source_language=source_language
        )
        
        if results:
            # Prepare download URLs - support both old (PDF) and new (all formats) keys
            searchable_key = 'searchable_document' if 'searchable_document' in results else 'searchable_pdf'
            translated_key = 'translated_document' if 'translated_document' in results else 'translated_pdf'
            
            download_urls = {
                'ocr_text': f'/download/ocr_{job_id}/{os.path.basename(results["ocr_text"])}',
                'searchable_pdf': f'/download/ocr_{job_id}/{os.path.basename(results[searchable_key])}',
                'translated_pdf': f'/download/ocr_{job_id}/{os.path.basename(results[translated_key])}'
            }
            
            detected_lang = results.get('detected_source_language', 'unknown')
            
            # Log detected language prominently
            logger.info(f"Job {job_id}: ✓ Source language detected: {detected_lang}")
            logger.info(f"Job {job_id}: → Target language: {target_language}")
            
            job.update(
                status="completed",
                progress=100,
                message="OCR and translation completed successfully",
                result={
                    'output_folder': f"ocr_{job_id}",
                    'download_urls': download_urls,
                    'detected_source_language': detected_lang,
                    'target_language': target_language
                }
            )
        else:
            job.update(status="failed", message="OCR translation failed", error="No results returned")
    
    except Exception as e:
        job.update(status="failed", message=f"Error: {str(e)}", error=str(e))


@app.route('/')
def index():
    """Serve the main UI page."""
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Handle file upload."""
    logger.info("Received file upload request")
    try:
        if 'files' not in request.files:
            logger.warning("Upload request missing files")
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            logger.warning("Upload request has empty file list")
            return jsonify({'error': 'No files selected'}), 400
        
        logger.info(f"Processing {len(files)} file(s) for upload")
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                logger.info(f"Uploaded file: {filename} ({os.path.getsize(filepath)} bytes)")
                uploaded_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size': os.path.getsize(filepath)
                })
        
        if not uploaded_files:
            return jsonify({'error': 'No valid PDF files uploaded'}), 400
        
        return jsonify({'files': uploaded_files}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate', methods=['POST'])
def start_translation():
    """Start a translation job."""
    logger.info("Received translation request")
    try:
        data = request.json
        job_type = data.get('job_type')
        files = data.get('files', [])
        target_languages = data.get('target_languages', [])
        source_language = data.get('source_language', None)  # Optional source language
        
        logger.info(f"Translation request - Type: {job_type}, Files: {len(files)}, Languages: {target_languages}")
        if source_language:
            logger.info(f"Source language specified: {source_language}")
        
        if not files or not target_languages:
            logger.warning("Translation request missing required parameters")
            return jsonify({'error': 'Files and target languages are required'}), 400
        
        # Create job ID
        job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Created job: {job_id}")
        job = JobStatus(job_id, job_type)
        jobs[job_id] = job
        
        # Start appropriate translation job
        if job_type == 'single':
            if len(files) != 1 or len(target_languages) != 1:
                logger.warning(f"Job {job_id}: Invalid parameters for single translation")
                return jsonify({'error': 'Single translation requires exactly one file and one language'}), 400
            
            logger.info(f"Job {job_id}: Starting single translation thread")
            thread = threading.Thread(
                target=run_single_translation,
                args=(job_id, files[0]['filepath'], target_languages[0], source_language)
            )
            thread.daemon = True
            thread.start()
        
        elif job_type == 'batch':
            if len(target_languages) == 0:
                logger.warning(f"Job {job_id}: No target languages specified for batch translation")
                return jsonify({'error': 'Batch translation requires at least one target language'}), 400
            
            logger.info(f"Job {job_id}: Starting batch translation thread")
            file_paths = [f['filepath'] for f in files]
            thread = threading.Thread(
                target=run_batch_translation,
                args=(job_id, file_paths, target_languages, source_language)
            )
            thread.daemon = True
            thread.start()
        
        elif job_type == 'ocr':
            if len(files) != 1 or len(target_languages) != 1:
                return jsonify({'error': 'OCR translation requires exactly one file and one language'}), 400
            
            thread = threading.Thread(
                target=run_ocr_translation,
                args=(job_id, files[0]['filepath'], target_languages[0], source_language)
            )
            thread.daemon = True
            thread.start()
        
        else:
            return jsonify({'error': 'Invalid job type'}), 400
        
        return jsonify({'job_id': job_id, 'status': job.to_dict()}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get status of a translation job."""
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict()), 200


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs."""
    return jsonify([job.to_dict() for job in jobs.values()]), 200


@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a translated file."""
    try:
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/languages', methods=['GET'])
def get_languages():
    """Get list of supported languages."""
    languages = [
        {'code': 'af', 'name': 'Afrikaans'},
        {'code': 'sq', 'name': 'Albanian'},
        {'code': 'am', 'name': 'Amharic'},
        {'code': 'ar', 'name': 'Arabic'},
        {'code': 'as', 'name': 'Assamese'},
        {'code': 'az', 'name': 'Azerbaijani'},
        {'code': 'bn', 'name': 'Bangla'},
        {'code': 'eu', 'name': 'Basque'},
        {'code': 'bs', 'name': 'Bosnian'},
        {'code': 'bg', 'name': 'Bulgarian'},
        {'code': 'yue', 'name': 'Cantonese'},
        {'code': 'ca', 'name': 'Catalan'},
        {'code': 'zh-Hans', 'name': 'Chinese (Simplified)'},
        {'code': 'zh-Hant', 'name': 'Chinese (Traditional)'},
        {'code': 'hr', 'name': 'Croatian'},
        {'code': 'cs', 'name': 'Czech'},
        {'code': 'da', 'name': 'Danish'},
        {'code': 'prs', 'name': 'Dari'},
        {'code': 'dv', 'name': 'Divehi'},
        {'code': 'nl', 'name': 'Dutch'},
        {'code': 'en', 'name': 'English'},
        {'code': 'et', 'name': 'Estonian'},
        {'code': 'fj', 'name': 'Fijian'},
        {'code': 'fil', 'name': 'Filipino'},
        {'code': 'fi', 'name': 'Finnish'},
        {'code': 'fr', 'name': 'French'},
        {'code': 'de', 'name': 'German'},
        {'code': 'el', 'name': 'Greek'},
        {'code': 'gu', 'name': 'Gujarati'},
        {'code': 'ht', 'name': 'Haitian Creole'},
        {'code': 'he', 'name': 'Hebrew'},
        {'code': 'hi', 'name': 'Hindi'},
        {'code': 'mww', 'name': 'Hmong Daw'},
        {'code': 'hu', 'name': 'Hungarian'},
        {'code': 'is', 'name': 'Icelandic'},
        {'code': 'id', 'name': 'Indonesian'},
        {'code': 'iu', 'name': 'Inuktitut'},
        {'code': 'ga', 'name': 'Irish'},
        {'code': 'it', 'name': 'Italian'},
        {'code': 'ja', 'name': 'Japanese'},
        {'code': 'kn', 'name': 'Kannada'},
        {'code': 'kk', 'name': 'Kazakh'},
        {'code': 'km', 'name': 'Khmer'},
        {'code': 'rw', 'name': 'Kinyarwanda'},
        {'code': 'tlh', 'name': 'Klingon'},
        {'code': 'ko', 'name': 'Korean'},
        {'code': 'ku', 'name': 'Kurdish'},
        {'code': 'lo', 'name': 'Lao'},
        {'code': 'lv', 'name': 'Latvian'},
        {'code': 'lt', 'name': 'Lithuanian'},
        {'code': 'mk', 'name': 'Macedonian'},
        {'code': 'mg', 'name': 'Malagasy'},
        {'code': 'ms', 'name': 'Malay'},
        {'code': 'ml', 'name': 'Malayalam'},
        {'code': 'mt', 'name': 'Maltese'},
        {'code': 'mi', 'name': 'Maori'},
        {'code': 'mr', 'name': 'Marathi'},
        {'code': 'mn', 'name': 'Mongolian'},
        {'code': 'my', 'name': 'Myanmar (Burmese)'},
        {'code': 'ne', 'name': 'Nepali'},
        {'code': 'nb', 'name': 'Norwegian'},
        {'code': 'or', 'name': 'Odia'},
        {'code': 'ps', 'name': 'Pashto'},
        {'code': 'fa', 'name': 'Persian'},
        {'code': 'pl', 'name': 'Polish'},
        {'code': 'pt', 'name': 'Portuguese'},
        {'code': 'pa', 'name': 'Punjabi'},
        {'code': 'otq', 'name': 'Queretaro Otomi'},
        {'code': 'ro', 'name': 'Romanian'},
        {'code': 'ru', 'name': 'Russian'},
        {'code': 'sm', 'name': 'Samoan'},
        {'code': 'sr', 'name': 'Serbian'},
        {'code': 'st', 'name': 'Sesotho'},
        {'code': 'si', 'name': 'Sinhala'},
        {'code': 'sk', 'name': 'Slovak'},
        {'code': 'sl', 'name': 'Slovenian'},
        {'code': 'es', 'name': 'Spanish'},
        {'code': 'sw', 'name': 'Swahili'},
        {'code': 'sv', 'name': 'Swedish'},
        {'code': 'ty', 'name': 'Tahitian'},
        {'code': 'ta', 'name': 'Tamil'},
        {'code': 'tt', 'name': 'Tatar'},
        {'code': 'te', 'name': 'Telugu'},
        {'code': 'th', 'name': 'Thai'},
        {'code': 'ti', 'name': 'Tigrinya'},
        {'code': 'tr', 'name': 'Turkish'},
        {'code': 'tk', 'name': 'Turkmen'},
        {'code': 'uk', 'name': 'Ukrainian'},
        {'code': 'ur', 'name': 'Urdu'},
        {'code': 'uz', 'name': 'Uzbek'},
        {'code': 'vi', 'name': 'Vietnamese'},
        {'code': 'cy', 'name': 'Welsh'},
        {'code': 'xh', 'name': 'Xhosa'},
        {'code': 'yi', 'name': 'Yiddish'},
        {'code': 'yo', 'name': 'Yoruba'},
        {'code': 'zu', 'name': 'Zulu'},
        {'code': 'ru', 'name': 'Russian'},
        {'code': 'hi', 'name': 'Hindi'},
        {'code': 'nl', 'name': 'Dutch'},
        {'code': 'pl', 'name': 'Polish'},
        {'code': 'sv', 'name': 'Swedish'},
        {'code': 'tr', 'name': 'Turkish'},
        {'code': 'vi', 'name': 'Vietnamese'},
        {'code': 'th', 'name': 'Thai'},
        {'code': 'id', 'name': 'Indonesian'},
    ]
    return jsonify(languages), 200


if __name__ == '__main__':
    print("="*70)
    print("Azure Document Translation Web UI")
    print("="*70)
    print("Starting server...")
    print("Access the UI at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("="*70)
    logger.info("="*70)
    logger.info("Starting Flask application")
    logger.info("Server accessible at: http://localhost:5000")
    logger.info("="*70)
    app.run(debug=True, host='0.0.0.0', port=5000)
