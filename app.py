import os
import json
import logging
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.utils import secure_filename
import os.path
from pathlib import Path
from dotenv import load_dotenv

# Import our receipt analyzer
from content_analyzer import analyze_receipt

# Load environment variables
load_dotenv()

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['SAMPLE_RECEIPTS_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample-receipts')

# Register MIME types for PDF files
mimetypes.add_type('application/pdf', '.pdf')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif', 'bmp', 'tif', 'tiff'}

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_sample_receipts():
    """Get list of sample receipts in the sample folder"""
    sample_path = app.config['SAMPLE_RECEIPTS_FOLDER']
    if not os.path.exists(sample_path):
        return []
    
    # Get all valid sample receipts
    sample_files = [f for f in os.listdir(sample_path) 
                   if os.path.isfile(os.path.join(sample_path, f)) and allowed_file(f)]
    
    # Copy all samples to static folder for easier access
    static_samples = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'samples')
    os.makedirs(static_samples, exist_ok=True)
    
    for sample in sample_files:
        src_path = os.path.join(sample_path, sample)
        dst_path = os.path.join(static_samples, sample)
        if not os.path.exists(dst_path):
            try:
                # Use copy instead of symlink for better cross-platform compatibility
                import shutil
                shutil.copy2(src_path, dst_path)
            except Exception as e:
                logger.error(f"Error copying sample file {sample}: {str(e)}")
                
    return sample_files

def process_api_results(api_results):
    """Process API results to handle various response formats"""
    if not api_results:
        logger.info("No API results to process")
        return {}
        
    logger.info(f"Processing API results: {json.dumps(api_results)[:200]}...")
    
    # Initialize results
    results = {}
    
    # Case 1: Standard format with analyzerResult
    if "analyzerResult" in api_results:
        if "documents" in api_results["analyzerResult"] and len(api_results["analyzerResult"]["documents"]) > 0:
            # Get fields from the first document
            results = api_results["analyzerResult"]["documents"][0]
            logger.info("Found fields in analyzerResult.documents[0]")
        elif "contents" in api_results["analyzerResult"] and len(api_results["analyzerResult"]["contents"]) > 0:
            # Look for fields in contents
            for content in api_results["analyzerResult"]["contents"]:
                if "fields" in content:
                    results = content
                    logger.info("Found fields in analyzerResult.contents")
                    break
    
    # Case 2: Direct fields in the root
    elif "fields" in api_results:
        results = api_results
        logger.info("Found fields directly in root of API results")
    
    # Case 3: Structure with result.contents
    elif "result" in api_results:
        if isinstance(api_results["result"], dict) and "contents" in api_results["result"]:
            # Process the result.contents structure
            for content in api_results["result"]["contents"]:
                if isinstance(content, dict) and "fields" in content:
                    results = {"fields": content["fields"]}
                    logger.info("Found fields in result.contents[].fields")
                    break
        else:
            # Just use whatever is in result
            results = {"fields": api_results["result"]}
            logger.info("Using API result directly")
    
    # Case 4: Any other nested structure, we try to find fields
    if not results and isinstance(api_results, dict):
        # Recursively search for fields
        def find_fields(obj, path=""):
            if isinstance(obj, dict):
                if "fields" in obj and isinstance(obj["fields"], dict):
                    logger.info(f"Found fields at path: {path}.fields")
                    return {"fields": obj["fields"]}
                
                for key, value in obj.items():
                    result = find_fields(value, f"{path}.{key}" if path else key)
                    if result:
                        return result
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    result = find_fields(item, f"{path}[{i}]")
                    if result:
                        return result
            return None
            
        found_fields = find_fields(api_results)
        if found_fields:
            results = found_fields
    
    # If we still don't have structured results, just return the raw API results
    if not results:
        logger.warning("Could not find structured fields in API results, returning raw data")
        results = {"raw_data": api_results}
        
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    receipt_url = None
    results = None
    
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
            
        file = request.files['file']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                # Process the uploaded receipt
                api_results = analyze_receipt(file_path=file_path)
                
                # Process results for display using the new function
                results = process_api_results(api_results)
                
                # Ensure the static/uploads directory exists
                static_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
                os.makedirs(static_uploads, exist_ok=True)
                
                # Copy the file directly to static/uploads (more reliable than symlinks)
                static_file_path = os.path.join(static_uploads, filename)
                import shutil
                shutil.copy2(file_path, static_file_path)
                
                # Set the receipt URL
                receipt_url = url_for('static', filename=f'uploads/{filename}')
            except Exception as e:
                logger.error(f"Error processing receipt: {str(e)}")
                flash(f"Error processing receipt: {str(e)}")
                return redirect(request.url)
    
    # Get sample receipts
    sample_receipts = get_sample_receipts()
    
    return render_template('index.html', 
                          receipt_url=receipt_url, 
                          results=results, 
                          sample_receipts=sample_receipts)

@app.route('/analyze-sample/<filename>')
def analyze_sample(filename):
    """Analyze a sample receipt"""
    # Validate filename to prevent directory traversal
    if not allowed_file(filename) or '/' in filename or '\\' in filename:
        flash("Invalid filename")
        return redirect(url_for('index'))
    
    # Construct the file path
    file_path = os.path.join(app.config['SAMPLE_RECEIPTS_FOLDER'], filename)
    
    if not os.path.exists(file_path):
        flash("Sample file not found")
        return redirect(url_for('index'))
    
    try:
        # Process the sample receipt
        api_results = analyze_receipt(file_path=file_path)
        
        # Process results for display using the new function
        results = process_api_results(api_results)
            
        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        os.makedirs(static_dir, exist_ok=True)
        
        # Create a directory for sample files in static
        static_samples = os.path.join(static_dir, 'samples')
        os.makedirs(static_samples, exist_ok=True)
        
        # Copy the file directly to static/samples (more reliable than symlinks)
        static_file_path = os.path.join(static_samples, filename)
        
        # Use copy instead of symlink for better compatibility
        import shutil
        if not os.path.exists(static_file_path):
            shutil.copy2(file_path, static_file_path)
        
        receipt_url = url_for('static', filename=f'samples/{filename}')
        
        # Get sample receipts for the dropdown
        sample_receipts = get_sample_receipts()
        
        return render_template('index.html', 
                              receipt_url=receipt_url, 
                              results=results, 
                              sample_receipts=sample_receipts)
    except Exception as e:
        logger.error(f"Error processing sample receipt: {str(e)}")
        flash(f"Error processing sample receipt: {str(e)}")
        return redirect(url_for('index'))

@app.route('/pdf/<path:filename>')
def serve_pdf(filename):
    """Serve PDF files directly with correct content type"""
    # Validate filename to prevent directory traversal
    if '/' in filename or '\\' in filename:
        return "Invalid filename", 400
    
    # First try uploads folder
    uploads_folder = app.config['UPLOAD_FOLDER']
    if os.path.exists(os.path.join(uploads_folder, filename)):
        return send_from_directory(uploads_folder, filename, mimetype='application/pdf')
    
    # Then try samples folder
    samples_folder = app.config['SAMPLE_RECEIPTS_FOLDER']
    if os.path.exists(os.path.join(samples_folder, filename)):
        return send_from_directory(samples_folder, filename, mimetype='application/pdf')
    
    return "File not found", 404

@app.template_filter('tojson')
def to_json_filter(obj, indent=None):
    """Convert object to pretty-printed JSON"""
    return json.dumps(obj, indent=indent)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('static/samples', exist_ok=True)
    
    # Create sample-receipts folder if it doesn't exist
    os.makedirs(app.config['SAMPLE_RECEIPTS_FOLDER'], exist_ok=True)
   
    app.run(debug=True, port=5001)  # Changed to port 5001 to avoid conflicts