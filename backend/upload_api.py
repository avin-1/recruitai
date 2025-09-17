from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import subprocess
import sys

# Load .env
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in .env")

# MongoDB setup
DB_NAME = "profiles"
COLLECTION_NAME = "json_files"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Flask app
app = Flask(__name__)
CORS(app)  # enable CORS for all routes

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "agents", "jobdescription", "input")
ORCHESTRATOR_SCRIPT = os.path.join(BASE_DIR, "..", "agents", "jobdescription", "main.py")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- File Upload Endpoint ----------------
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # Trigger the LangGraph orchestrator script in the background
    try:
        print(f"Triggering orchestrator for: {filepath}")
        # Use the same Python executable that is running the Flask app
        python_executable = sys.executable
        subprocess.Popen([python_executable, ORCHESTRATOR_SCRIPT, filepath])
        message = f"File '{file.filename}' uploaded successfully and processing has started."
        return jsonify({"message": message}), 200
    except Exception as e:
        print(f"Failed to trigger orchestrator: {e}")
        return jsonify({"error": "File uploaded, but failed to start processing."}), 500

# ---------------- Retrieve Job Profiles ----------------
@app.route("/profiles", methods=["GET"])
def get_profiles():
    try:
        profiles_cursor = collection.find({})
        profiles = []
        for profile in profiles_cursor:
            profile["_id"] = str(profile["_id"])  # Convert ObjectId to string
            profiles.append(profile)
        return jsonify({"profiles": profiles}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.route("/delete", methods=["POST"])
def delete_profile():
    data = request.get_json()
    job_title = data.get("job_title")
    if not job_title:
        return jsonify({"error": "No job_title provided"}), 400
    try:
        result = collection.delete_one({"job_title": job_title})
        if result.deleted_count == 0:
            return jsonify({"error": "Profile not found"}), 404
        return jsonify({"message": f'Profile "{job_title}" deleted successfully'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Retrieve Approved Jobs ----------------
@app.route("/jobs", methods=["GET"])
def get_jobs():
    try:
        # Find only profiles where 'approved' is true
        approved_jobs_cursor = collection.find({"approved": True})
        jobs = []
        for job in approved_jobs_cursor:
            job["_id"] = str(job["_id"])
            jobs.append(job)
        return jsonify({"jobs": jobs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Approve Job Profile ----------------
@app.route("/approve", methods=["POST"])
def approve_profile():
    data = request.get_json()
    job_title = data.get("job_title")
    if not job_title:
        return jsonify({"error": "No job_title provided"}), 400
    try:
        result = collection.update_one(
            {"job_title": job_title},
            {"$set": {"approved": True}}
        )
        if result.matched_count == 0:
            return jsonify({"error": "Profile not found"}), 404
        return jsonify({"message": f'Profile "{job_title}" approved successfully'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(port=5001, debug=True)
