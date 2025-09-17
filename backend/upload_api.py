from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

# Add the parent directory of 'agents' to the Python path
# This is necessary so we can import from 'agents.jobdescription.graph'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.jobdescription.graph import app as langgraph_app

# Load .env
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in .env")

# MongoDB setup for retrieving profiles (the graph handles its own connections)
client = MongoClient(MONGO_URI)
db = client["profiles"]
collection = db["json_files"]

# Flask app
app = Flask(__name__)
CORS(app)  # enable CORS for all routes

# Set upload folder relative to backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "agents", "jobdescription", "input")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- File Upload and Processing Endpoint ----------------
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Save the file temporarily
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    print(f"File saved to: {filepath}")

    # --- Trigger the LangGraph Workflow ---
    try:
        print("Invoking LangGraph workflow...")
        # The input to the graph is a dictionary with keys matching the GraphState
        initial_input = {"filepath": filepath}

        # Run the graph
        final_state = langgraph_app.invoke(initial_input)

        print(f"LangGraph execution finished. Final state: {final_state}")
        db_id = final_state.get('db_id', 'N/A')

        # Return a success message to the frontend
        message = f"File '{file.filename}' processed successfully. Profile stored with ID: {db_id}."
        return jsonify({"message": message}), 200

    except Exception as e:
        # If the graph fails, return an error message
        print(f"Error during LangGraph execution: {e}")
        # It's good practice to also remove the temp file if processing fails
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": f"Failed to process file: {e}"}), 500

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
