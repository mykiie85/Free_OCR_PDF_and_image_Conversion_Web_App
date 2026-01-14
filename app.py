import os
import uuid
import logging
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
import threading
import time
from datetime import datetime
from collections import defaultdict
from functools import wraps
from dotenv import load_dotenv

from ocr.ocr_engine import OCREngine

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
app.config['OUTPUT_FOLDER'] = os.getenv('OUTPUT_FOLDER', 'outputs')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))
app.config['MAX_PAGES'] = int(os.getenv('MAX_PAGES', 50))
app.config['CLEANUP_INTERVAL'] = int(os.getenv('CLEANUP_INTERVAL', 3600))
app.config['FILE_RETENTION_TIME'] = int(os.getenv('FILE_RETENTION_TIME', 3600))

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
SUPPORTED_LANGUAGES = {
    'eng': 'English',
    'spa': 'Spanish',
    'fra': 'French',
    'deu': 'German',
    'ita': 'Italian',
    'por': 'Portuguese',
    'rus': 'Russian',
    'chi_sim': 'Chinese (Simplified)',
    'jpn': 'Japanese',
    'ara': 'Arabic',
    'hin': 'Hindi'
}

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize OCR Engine
tesseract_path = os.getenv('TESSERACT_PATH')
ocr_engine = OCREngine(tesseract_path=tesseract_path)

# Rate limiting storage
rate_limit_storage = defaultdict(list)


def rate_limit(max_per_minute=10, max_per_hour=100):
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if os.getenv('RATE_LIMIT_ENABLED', 'true').lower() != 'true':
                return f(*args, **kwargs)
            
            # Use IP address as identifier
            ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            rate_limit_storage[ip] = [
                timestamp for timestamp in rate_limit_storage[ip]
                if current_time - timestamp < 3600
            ]
            
            # Check limits
            recent_requests = [
                timestamp for timestamp in rate_limit_storage[ip]
                if current_time - timestamp < 60
            ]
            
            if len(recent_requests) >= max_per_minute:
                logger.warning(f"Rate limit exceeded for IP: {ip}")
                return jsonify({'error': 'Too many requests. Please wait a minute.'}), 429
            
            if len(rate_limit_storage[ip]) >= max_per_hour:
                logger.warning(f"Hourly rate limit exceeded for IP: {ip}")
                return jsonify({'error': 'Hourly limit reached. Please try again later.'}), 429
            
            # Add current request
            rate_limit_storage[ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def allowed_file(filename):
    
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files():
    
    while True:
        try:
            current_time = time.time()
            retention_time = app.config['FILE_RETENTION_TIME']
            
            for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
                for filename in os.listdir(folder):
                    filepath = os.path.join(folder, filename)
                    if os.path.isfile(filepath):
                        file_age = current_time - os.path.getmtime(filepath)
                        if file_age > retention_time:
                            os.remove(filepath)
                            logger.info(f"Cleaned up old file: {filepath}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        
        time.sleep(app.config['CLEANUP_INTERVAL'])


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()
logger.info("Cleanup thread started")


@app.route('/')
def index():
    
    return render_template('index.html', languages=SUPPORTED_LANGUAGES)


@app.route('/upload', methods=['POST'])
@rate_limit(max_per_minute=10, max_per_hour=100)
def upload_file():
    
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            logger.warning("Upload attempt with no files")
            return jsonify({'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        output_format = request.form.get('format', 'txt')
        language = request.form.get('language', 'eng')
        
        logger.info(f"Upload request: {len(files)} file(s), format={output_format}, language={language}")
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Validate output format
        if output_format not in ['txt', 'docx', 'xlsx']:
            return jsonify({'error': 'Invalid output format'}), 400
        
        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            language = 'eng'
        
        # Process files
        processed_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Generate unique filename
                original_filename = secure_filename(file.filename)
                unique_id = str(uuid.uuid4())[:8]
                filename = f"{unique_id}_{original_filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save uploaded file
                file.save(filepath)
                logger.info(f"Saved file: {filename}")
                
                processed_files.append({
                    'original': original_filename,
                    'path': filepath,
                    'id': unique_id
                })
            else:
                logger.warning(f"Invalid file type rejected: {file.filename}")
                return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
        
        if not processed_files:
            return jsonify({'error': 'No valid files to process'}), 400
        
        # Process all files
        results = []
        for file_info in processed_files:
            start_time = time.time()
            
            result = ocr_engine.process_document(
                input_path=file_info['path'],
                output_format=output_format,
                output_folder=app.config['OUTPUT_FOLDER'],
                file_id=file_info['id'],
                language=language
            )
            
            processing_time = time.time() - start_time
            
            if result['success']:
                logger.info(f"Successfully processed: {file_info['original']} in {processing_time:.2f}s")
                results.append({
                    'original_filename': file_info['original'],
                    'output_filename': os.path.basename(result['output_path']),
                    'pages': result['pages'],
                    'processing_time': round(processing_time, 2),
                    'success': True
                })
            else:
                logger.error(f"Processing failed: {file_info['original']} - {result['error']}")
                results.append({
                    'original_filename': file_info['original'],
                    'error': result['error'],
                    'success': False
                })
        
        # Check if any succeeded
        successful = [r for r in results if r['success']]
        if not successful:
            return jsonify({'error': 'All files failed to process', 'results': results}), 500
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f'Processed {len(successful)}/{len(results)} files successfully'
        })
    
    except Exception as e:
        logger.exception("Upload error occurred")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/download/<filename>')
def download_file(filename):
    
    try:
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], secure_filename(filename))
        
        if not os.path.exists(filepath):
            logger.warning(f"Download attempt for non-existent file: {filename}")
            return jsonify({'error': 'File not found'}), 404
        
        logger.info(f"File downloaded: {filename}")
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': f'Download error: {str(e)}'}), 500


@app.route('/health')
def health():
    
    tesseract_status = ocr_engine.check_tesseract()
    return jsonify({
        'status': 'healthy',
        'tesseract': tesseract_status,
        'uptime': time.time(),
        'environment': os.getenv('FLASK_ENV', 'production')
    })


@app.route('/languages')
def get_languages():
    
    return jsonify({
        'languages': SUPPORTED_LANGUAGES,
        'default': 'eng'
    })


@app.errorhandler(413)
def request_entity_too_large(error):
    
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413


@app.errorhandler(500)
def internal_error(error):
    
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error. Please try again later.'}), 500


if __name__ == '__main__':
    logger.info("Starting OCR Web Application")
    app.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000))
    )