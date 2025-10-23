"""
Web UI for Azure Document Translation
Flask application for uploading PDFs and running translation scripts
"""

import os
import json
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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store job status
jobs = {}


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


def run_single_translation(job_id, file_path, target_language):
    """Run single document translation in background."""
    job = jobs[job_id]
    try:
        job.update(status="running", progress=10, message="Initializing translator...")
        translator = SingleDocumentTranslator()
        
        job.update(progress=30, message="Uploading document to Azure...")
        translated_url = translator.translate_document(
            input_file_path=file_path,
            target_language=target_language
        )
        
        if translated_url:
            job.update(progress=80, message="Downloading translated document...")
            output_filename = f"translated_{target_language}_{os.path.basename(file_path)}"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            translator.download_translated_document(translated_url, output_path)
            
            job.update(
                status="completed",
                progress=100,
                message="Translation completed successfully",
                result={'output_file': output_filename, 'download_url': f'/download/{output_filename}'}
            )
        else:
            job.update(status="failed", message="Translation failed", error="No translated URL returned")
    
    except Exception as e:
        job.update(status="failed", message=f"Error: {str(e)}", error=str(e))


def run_batch_translation(job_id, file_paths, target_languages):
    """Run batch translation in background."""
    job = jobs[job_id]
    try:
        job.update(status="running", progress=10, message="Initializing batch translator...")
        translator = BatchDocumentTranslator()
        
        # Create a temporary batch folder
        batch_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"batch_{job_id}")
        os.makedirs(batch_folder, exist_ok=True)
        
        # Copy files to batch folder
        job.update(progress=20, message="Preparing batch files...")
        for file_path in file_paths:
            import shutil
            shutil.copy2(file_path, batch_folder)
        
        job.update(progress=40, message=f"Translating to {len(target_languages)} languages...")
        results = translator.translate_batch(
            input_folder=batch_folder,
            target_languages=target_languages,
            source_container=f"batch-source-{job_id}",
            target_container_prefix=f"batch-target-{job_id}"
        )
        
        # Download results
        job.update(progress=80, message="Downloading translated documents...")
        output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f"batch_{job_id}")
        
        download_urls = {}
        for lang, documents in results.items():
            if documents:
                lang_output = os.path.join(output_folder, lang)
                container_name = f"batch-target-{job_id}-{lang}"
                translator.download_translated_documents(container_name, lang_output)
                
                # Get list of files
                if os.path.exists(lang_output):
                    files = os.listdir(lang_output)
                    download_urls[lang] = [f'/download/batch_{job_id}/{lang}/{f}' for f in files]
        
        job.update(
            status="completed",
            progress=100,
            message=f"Batch translation completed for {len(target_languages)} languages",
            result={'output_folder': f"batch_{job_id}", 'download_urls': download_urls}
        )
    
    except Exception as e:
        job.update(status="failed", message=f"Error: {str(e)}", error=str(e))


def run_ocr_translation(job_id, file_path, target_language):
    """Run OCR + translation pipeline in background."""
    job = jobs[job_id]
    try:
        job.update(status="running", progress=10, message="Initializing OCR pipeline...")
        pipeline = OCRTranslationPipeline()
        
        output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f"ocr_{job_id}")
        os.makedirs(output_folder, exist_ok=True)
        
        job.update(progress=20, message="Running OCR analysis...")
        results = pipeline.process_document(
            input_pdf_path=file_path,
            target_language=target_language,
            output_folder=output_folder
        )
        
        if results:
            # Prepare download URLs
            download_urls = {
                'ocr_text': f'/download/ocr_{job_id}/{os.path.basename(results["ocr_text"])}',
                'searchable_pdf': f'/download/ocr_{job_id}/{os.path.basename(results["searchable_pdf"])}',
                'translated_pdf': f'/download/ocr_{job_id}/{os.path.basename(results["translated_pdf"])}'
            }
            
            job.update(
                status="completed",
                progress=100,
                message="OCR and translation completed successfully",
                result={'output_folder': f"ocr_{job_id}", 'download_urls': download_urls}
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
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
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
    try:
        data = request.json
        job_type = data.get('job_type')
        files = data.get('files', [])
        target_languages = data.get('target_languages', [])
        
        if not files or not target_languages:
            return jsonify({'error': 'Files and target languages are required'}), 400
        
        # Create job ID
        job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job = JobStatus(job_id, job_type)
        jobs[job_id] = job
        
        # Start appropriate translation job
        if job_type == 'single':
            if len(files) != 1 or len(target_languages) != 1:
                return jsonify({'error': 'Single translation requires exactly one file and one language'}), 400
            
            thread = threading.Thread(
                target=run_single_translation,
                args=(job_id, files[0]['filepath'], target_languages[0])
            )
            thread.daemon = True
            thread.start()
        
        elif job_type == 'batch':
            if len(target_languages) == 0:
                return jsonify({'error': 'Batch translation requires at least one target language'}), 400
            
            file_paths = [f['filepath'] for f in files]
            thread = threading.Thread(
                target=run_batch_translation,
                args=(job_id, file_paths, target_languages)
            )
            thread.daemon = True
            thread.start()
        
        elif job_type == 'ocr':
            if len(files) != 1 or len(target_languages) != 1:
                return jsonify({'error': 'OCR translation requires exactly one file and one language'}), 400
            
            thread = threading.Thread(
                target=run_ocr_translation,
                args=(job_id, files[0]['filepath'], target_languages[0])
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
        {'code': 'en', 'name': 'English'},
        {'code': 'es', 'name': 'Spanish'},
        {'code': 'fr', 'name': 'French'},
        {'code': 'de', 'name': 'German'},
        {'code': 'it', 'name': 'Italian'},
        {'code': 'pt', 'name': 'Portuguese'},
        {'code': 'ja', 'name': 'Japanese'},
        {'code': 'ko', 'name': 'Korean'},
        {'code': 'zh-Hans', 'name': 'Chinese (Simplified)'},
        {'code': 'zh-Hant', 'name': 'Chinese (Traditional)'},
        {'code': 'ar', 'name': 'Arabic'},
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
    app.run(debug=True, host='0.0.0.0', port=5000)
