from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import sys
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we can import utils
sys.path.append(os.path.dirname(__file__))

# Lazy load parser
_parser = None

def get_parser():
    global _parser
    if _parser is None:
        logger.info("Loading Resume Parser...")
        # Assuming resume_parser.py is in utils/ and has parse_resume function
        from utils.resume_parser import parse_resume
        _parser = parse_resume
    return _parser

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "Parsing Service Online"}), 200

@app.route("/parse", methods=["POST"])
def parse_resume_endpoint():
    try:
        if 'resume' not in request.files:
            return jsonify({"error": "No resume file provided"}), 400
        
        resume_file = request.files['resume']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            resume_file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            parser = get_parser()
            # resume_parser.parse_resume expects a file path
            resume_text = parser(tmp_path)
            
            if not resume_text:
                resume_text = ""
                
            return jsonify({
                "text": resume_text,
                "length": len(resume_text)
            }), 200
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        logger.error(f"Error in parsing: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Port 5006 for Parsing Service
    port = int(os.environ.get("PORT", 5006))
    app.run(host="0.0.0.0", port=port)
