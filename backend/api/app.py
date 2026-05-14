"""
Flask backend API for InFynd Company Intelligence AI
Provides REST endpoints for chatbot and company data access
"""
import os
import json
import logging
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import sys

# Add parent directories to path
base_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(base_dir))

from backend.services.chatbot_service import ChatbotService
from backend.services.proofs_service import ProofsService
from backend.services.processing_service import start_processing, get_job_status

# Determine if we're in development or production mode
# In production, serve React build from frontend/dist
# In development, React dev server runs separately on port 3000
frontend_dist = base_dir / 'frontend' / 'dist'
is_production = frontend_dist.exists() and (frontend_dist / 'index.html').exists()

if is_production:
    # Production: serve React build
    app = Flask(__name__, static_folder=str(frontend_dist), static_url_path='')
else:
    # Development: serve templates (fallback)
    app = Flask(__name__, static_folder='../../frontend/static', template_folder='../../frontend/templates')

CORS(app)

# Increase file upload size limit (default is 16MB)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Error handler for file size limit
from werkzeug.exceptions import RequestEntityTooLarge

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    logger.error(f"File upload too large: {e}")
    return jsonify({"error": "File is too large. Maximum size is 100MB."}), 413

# Initialize services
chatbot_service = ChatbotService(base_dir)
proofs_service = ProofsService(base_dir)


@app.route('/')
def index():
    """Serve the main UI"""
    if is_production:
        # Serve React build
        return send_file(str(frontend_dist / 'index.html'))
    else:
        # Development fallback
        from flask import render_template
        return render_template('index.html')


@app.route('/api/companies', methods=['GET'])
def get_companies():
    """Get list of all companies"""
    try:
        manifest_path = base_dir / "data" / "companies.json"
        if not manifest_path.exists():
            return jsonify({"error": "Manifest not found"}), 404
        
        with manifest_path.open('r', encoding='utf-8') as f:
            companies = json.load(f)
        
        return jsonify(companies)
    except Exception as e:
        logger.error(f"Error loading companies: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/companies/<domain>/profile', methods=['GET'])
def get_company_profile(domain):
    """Get company profile by domain"""
    try:
        profile_path = base_dir / "output" / domain / "profile.json"
        
        # If profile doesn't exist, try to generate a default one from chunks
        if not profile_path.exists():
            logger.warning(f"Profile not found for {domain}, generating default from chunks")
            default_profile = _generate_default_profile(domain, base_dir)
            if default_profile:
                return jsonify(default_profile)
            return jsonify({"error": "Profile not found and cannot generate default"}), 404
        
        # Load and validate profile
        with profile_path.open('r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                # Empty file, generate default
                logger.warning(f"Profile is empty for {domain}, generating default from chunks")
                default_profile = _generate_default_profile(domain, base_dir)
                if default_profile:
                    return jsonify(default_profile)
                return jsonify({"error": "Profile is empty and cannot generate default"}), 404
            
            try:
                profile = json.loads(content)
            except json.JSONDecodeError as e:
                # Invalid JSON, try to generate default
                logger.error(f"Invalid JSON in profile for {domain}: {e}, generating default")
                default_profile = _generate_default_profile(domain, base_dir)
                if default_profile:
                    return jsonify(default_profile)
                return jsonify({"error": f"Invalid JSON in profile: {str(e)}"}), 500
            
            # Validate profile structure
            if not isinstance(profile, dict) or "domain" not in profile:
                logger.warning(f"Invalid profile structure for {domain}, generating default")
                default_profile = _generate_default_profile(domain, base_dir)
                if default_profile:
                    return jsonify(default_profile)
                return jsonify({"error": "Invalid profile structure"}), 500
            
            # Normalize profile data before returning (fix data type issues)
            profile = _normalize_profile(profile)
        
        return jsonify(profile)
    except Exception as e:
        logger.error(f"Error loading profile for {domain}: {e}")
        # Try to return default profile as fallback
        try:
            default_profile = _generate_default_profile(domain, base_dir)
            if default_profile:
                return jsonify(default_profile)
        except:
            pass
        return jsonify({"error": str(e)}), 500


def _normalize_profile(profile: dict) -> dict:
    """
    Normalize profile data to ensure correct data types and fix common issues.
    """
    import re
    
    # Normalize contact.email - should be string, not array
    if "contact" in profile and isinstance(profile["contact"], dict):
        contact = profile["contact"]
        if "email" in contact:
            email_val = contact["email"]
            if isinstance(email_val, list):
                # Get first valid email from array
                valid_emails = [e for e in email_val if isinstance(e, str) and "@" in e]
                if valid_emails:
                    # Clean email - extract just email part
                    email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', valid_emails[0])
                    contact["email"] = email_match.group(1) if email_match else valid_emails[0]
                else:
                    contact["email"] = ""
            elif isinstance(email_val, str) and email_val.strip():
                # Clean email string if it has trailing text
                email_match = re.search(r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})', email_val)
                if email_match:
                    contact["email"] = email_match.group(1)
    
    # Ensure arrays are lists, not strings
    array_fields = ["services", "products", "certifications", "locations", "sectors", 
                    "leadership", "people", "technology_signals"]
    for field in array_fields:
        if field in profile:
            if isinstance(profile[field], str):
                profile[field] = []
            elif not isinstance(profile[field], list):
                profile[field] = []
    
    # Ensure contact.other_numbers is an array
    if "contact" in profile and isinstance(profile["contact"], dict):
        if "other_numbers" in profile["contact"]:
            if not isinstance(profile["contact"]["other_numbers"], list):
                profile["contact"]["other_numbers"] = []
    
    # Remove meta object if present
    if "meta" in profile:
        del profile["meta"]
    
    return profile


def _generate_default_profile(domain: str, base_dir: Path) -> dict:
    """
    Generate a default profile from available chunks when profile.json is missing or invalid.
    Returns a minimal profile with basic information extracted from chunks.
    """
    try:
        from services.llm_extractor import _default_profile_schema
        import json
        
        chunks_path = base_dir / "output" / domain / "chunks.json"
        profile = _default_profile_schema(domain)
        
        # Try to extract basic info from chunks if available
        if chunks_path.exists():
            try:
                with chunks_path.open('r', encoding='utf-8') as f:
                    chunks = json.load(f)
                    
                if chunks and isinstance(chunks, list) and len(chunks) > 0:
                    # Extract company name from first chunk's page title
                    for chunk in chunks[:5]:
                        page_title = chunk.get("page_title", "")
                        if page_title:
                            # Extract company name from title (usually before | or -)
                            name = page_title.split("|")[0].split("-")[0].strip()
                            if name and len(name) < 100:
                                profile["company_name"] = name
                                break
                        
                        # Extract description from meta_description
                        meta_desc = chunk.get("meta_description", "")
                        if meta_desc and not profile.get("description_long"):
                            profile["description_long"] = meta_desc[:500]
                            profile["description_short"] = meta_desc[:100]
                            break
                    
                    # Extract basic contact info from structured_data
                    for chunk in chunks[:20]:
                        structured = chunk.get("structured_data", {})
                        if structured:
                            # Emails
                            if structured.get("emails") and not profile.get("contact", {}).get("email"):
                                valid_emails = [e for e in structured["emails"] if isinstance(e, str) and "@" in e]
                                if valid_emails:
                                    profile["contact"]["email"] = valid_emails[0]
                            
                            # Phones
                            if structured.get("phones") and not profile.get("contact", {}).get("phone"):
                                valid_phones = [p for p in structured["phones"] if isinstance(p, str) and len(p) >= 10]
                                if valid_phones:
                                    profile["contact"]["phone"] = valid_phones[0]
                            
                            # Social links
                            social_links = structured.get("social_links", {})
                            if social_links:
                                profile["social"].update({
                                    k: v for k, v in social_links.items() 
                                    if k in profile["social"] and v
                                })
                            
                            # Addresses
                            if structured.get("addresses") and not profile.get("headquarters"):
                                profile["headquarters"] = structured["addresses"][0]
                                profile["contact"]["full_address"] = structured["addresses"][0]
                                
            except Exception as e:
                logger.warning(f"Could not extract info from chunks for {domain}: {e}")
        
        # Set domain status if we have chunks
        if chunks_path.exists():
            profile["domain_status"] = "Active"
        
        # Calculate extraction confidence (will be low since it's minimal)
        from services.llm_extractor import _calculate_extraction_confidence
        profile["extraction_confidence"] = _calculate_extraction_confidence(profile)
        
        return profile
        
    except Exception as e:
        logger.error(f"Error generating default profile for {domain}: {e}")
        return None


@app.route('/api/companies/<domain>/chunks', methods=['GET'])
def get_company_chunks(domain):
    """Get company chunks for proofs"""
    try:
        chunks_path = base_dir / "output" / domain / "chunks.json"
        if not chunks_path.exists():
            return jsonify({"error": "Chunks not found"}), 404
        
        with chunks_path.open('r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        return jsonify(chunks)
    except Exception as e:
        logger.error(f"Error loading chunks for {domain}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chatbot endpoint - answers questions about companies"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        domain = data.get('domain', '').strip()
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        if not domain:
            return jsonify({"error": "Domain is required"}), 400
        
        # Get response from chatbot service
        response = chatbot_service.get_response(domain, question)
        
        # Get proofs for the response
        proofs = proofs_service.get_proofs(domain, question, response)
        
        return jsonify({
            "response": response,
            "proofs": proofs
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/proofs/<domain>', methods=['GET'])
def get_proofs(domain):
    """Get proofs for a specific domain"""
    try:
        query = request.args.get('query', '')
        proofs = proofs_service.get_proofs(domain, query, "")
        return jsonify(proofs)
    except Exception as e:
        logger.error(f"Error getting proofs for {domain}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/output/<path:path>')
def serve_output(path):
    """Serve output files"""
    return send_from_directory(str(base_dir / "output"), path)


@app.route('/data/<path:path>')
def serve_data(path):
    """Serve data files"""
    return send_from_directory(str(base_dir / "data"), path)


@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Handle CSV file upload and start processing"""
    try:
        logger.info("CSV upload request received")
        
        if 'csv_file' not in request.files:
            logger.warning("No csv_file in request.files")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['csv_file']
        if file.filename == '':
            logger.warning("Empty filename in upload request")
            return jsonify({"error": "No file selected"}), 400
        
        logger.info(f"Uploading file: {file.filename}")
        
        if not file.filename.endswith('.csv'):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({"error": "File must be a CSV"}), 400
        
        # Save uploaded file
        uploads_dir = base_dir / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Uploads directory: {uploads_dir}")
        
        csv_path = uploads_dir / f"upload_{uuid.uuid4().hex[:8]}.csv"
        logger.info(f"Saving file to: {csv_path}")
        file.save(str(csv_path))
        
        if not csv_path.exists():
            raise Exception(f"Failed to save file to {csv_path}")
        
        logger.info(f"File saved successfully. Starting processing...")
        
        # Start processing
        job_id = start_processing(csv_path, base_dir)
        logger.info(f"Processing started with job_id: {job_id}")
        
        return jsonify({
            "job_id": job_id,
            "message": "CSV uploaded and processing started"
        })
    except Exception as e:
        logger.exception(f"Error uploading CSV: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/processing-status/<job_id>', methods=['GET'])
def processing_status(job_id):
    """Get processing status for a job"""
    try:
        status = get_job_status(job_id)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({"error": str(e)}), 500


# Serve React static assets in production
if is_production:
    @app.route('/assets/<path:path>')
    def serve_react_assets(path):
        """Serve React build assets"""
        return send_from_directory(str(frontend_dist / 'assets'), path)
    
    # Catch-all route for React Router (must be last)
    @app.route('/<path:path>')
    def serve_react_app(path):
        """Serve React app for client-side routing"""
        # Don't interfere with API routes
        if path.startswith('api/') or path.startswith('data/') or path.startswith('output/'):
            return jsonify({"error": "Not found"}), 404
        return send_file(str(frontend_dist / 'index.html'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

