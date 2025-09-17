from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId

# Load .env
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in .env")

# MongoDB setup
DB_NAME = "profiles"           # replace with your database name
COLLECTION_NAME = "json_files"   # replace with your collection name
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Flask app
app = Flask(__name__)
CORS(app)  # enable CORS for all routes

# Set upload folder relative to backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend directory
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "agents", "jobdescription", "input")
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

    return jsonify({"message": f"File uploaded successfully: {file.filename}"}), 200

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
    profile_id = data.get("profile_id")
    if not profile_id:
        return jsonify({"error": "No profile_id provided"}), 400
    try:
        result = collection.delete_one({"_id": ObjectId(profile_id)})
        if result.deleted_count == 0:
            return jsonify({"error": "Profile not found"}), 404
        return jsonify({"message": f'Profile deleted successfully'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Approve Profile ----------------
@app.route("/approve", methods=["POST"])
def approve_profile():
    data = request.get_json()
    profile_id = data.get("profile_id")
    if not profile_id:
        return jsonify({"error": "No profile_id provided"}), 400
    try:
        result = collection.update_one({"_id": ObjectId(profile_id)}, {"$set": {"approved": True}})
        if result.matched_count == 0:
            return jsonify({"error": "Profile not found"}), 404
        return jsonify({"message": f'Profile approved successfully'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Modify Profile ----------------
@app.route("/modify", methods=["POST"])
def modify_profile():
    data = request.get_json()
    profile_id = data.get("profile_id")
    new_profile_data = data.get("new_profile_data")

    if not profile_id or not new_profile_data:
        return jsonify({"error": "Missing profile_id or new_profile_data"}), 400

    try:
        # Ensure the 'approved' flag is set to False
        new_profile_data['approved'] = False

        # Remove _id from the update data, as it cannot be changed
        if '_id' in new_profile_data:
            del new_profile_data['_id']

        result = collection.update_one(
            {"_id": ObjectId(profile_id)},
            {"$set": new_profile_data}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Profile not found"}), 404

        return jsonify({"message": "Profile modified successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(port=8080, debug=True)
