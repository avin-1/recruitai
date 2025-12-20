from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure we can import utils
sys.path.append(os.path.dirname(__file__))

# Lazy load Matcher
_matcher = None

def get_matcher():
    global _matcher
    if _matcher is None:
        logger.info("Loading Embeddings Model (Heavy)...")
        from utils.matcher import semantic_match
        _matcher = semantic_match
    return _matcher

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ML Matching Service Online"}), 200

@app.route("/score", methods=["POST"])
def score_text():
    """
    Expects JSON: { "resume_text": "...", "job_description": "..." }
    """
    try:
        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_description = data.get('job_description', '')
        
        if not resume_text: # Allow empty JD, but need resume text
             return jsonify({"error": "No resume_text provided"}), 400

        matcher = get_matcher()
        # "all-MiniLM-L6-v2" is standard
        score = matcher(resume_text, job_description, "all-MiniLM-L6-v2")
        
        score_percent = float(score * 100)
        
        return jsonify({
            "score": score_percent
        }), 200
                
    except Exception as e:
        logger.error(f"Error in matching: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Port 5004 for ML (Matching) Service
    port = int(os.environ.get("PORT", 5004))
    app.run(host="0.0.0.0", port=port)
