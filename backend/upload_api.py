from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
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
applications_col = db.get_collection("applications")

# Flask app
app = Flask(__name__)
CORS(app)  # enable CORS for all routes

# Set upload folder relative to backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend directory
UPLOAD_FOLDER = os.path.join(BASE_DIR, "..", "agents", "jobdescription", "input")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Resume storage folder (files on disk, metadata in Mongo)
RESUMES_FOLDER = os.path.join(BASE_DIR, "..", "agents", "resumeandmatching", "resumes")
os.makedirs(RESUMES_FOLDER, exist_ok=True)

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


# ---------------- List Approved Jobs ----------------
@app.route("/jobs", methods=["GET"])
def list_jobs():
    try:
        jobs = []
        for doc in collection.find({"approved": True}):
            doc["_id"] = str(doc["_id"])  # stringify id
            # Minimal card fields for portal; include more as needed
            jobs.append({
                "_id": doc["_id"],
                "job_title": doc.get("job_title") or doc.get("title") or "Untitled",
                "company": doc.get("company"),
                "location": doc.get("location"),
                "summary": doc.get("summary") or doc.get("responsibilities"),
            })
        return jsonify({"jobs": jobs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- Single Job Detail ----------------
@app.route("/job", methods=["GET"])
def get_job_detail():
    job_id = request.args.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    try:
        doc = collection.find_one({"_id": ObjectId(job_id)})
        if not doc:
            return jsonify({"error": "Job not found"}), 404
        doc["_id"] = str(doc["_id"])  # stringify id
        return jsonify({"job": doc}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Jobs with Applicant Counts ----------------
@app.route("/jobs_counts", methods=["GET"])
def jobs_with_counts():
    try:
        jobs = []
        for doc in collection.find({"approved": True}):
            count = applications_col.count_documents({"job_id": doc["_id"]})
            jobs.append({
                "_id": str(doc["_id"]),
                "job_title": doc.get("job_title") or doc.get("title") or "Untitled",
                "company": doc.get("company"),
                "location": doc.get("location"),
                "applicants_count": count,
            })
        return jsonify({"jobs": jobs}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- List Applications (optional limit) ----------------
@app.route("/applications", methods=["GET"])
def list_applications():
    job_id = request.args.get("job_id")
    limit = request.args.get("limit", type=int)
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    try:
        query = {"job_id": ObjectId(job_id)}
        cursor = applications_col.find(query).sort("created_at", -1)
        if limit and limit > 0:
            cursor = cursor.limit(limit)
        apps = []
        for a in cursor:
            a["_id"] = str(a["_id"])
            a["job_id"] = str(a["job_id"])
            # Only expose safe metadata
            apps.append({
                "_id": a["_id"],
                "name": a.get("name"),
                "email": a.get("email"),
                "resume_filename": a.get("resume_filename"),
                "created_at": a.get("created_at").isoformat() if a.get("created_at") else None,
            })
        return jsonify({"applications": apps}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Applicant Apply (multipart) ----------------
@app.route("/apply", methods=["POST"])
def apply_job():
    """Accepts multipart form: job_id, name, email, resume(file).

    Stores resume file on disk under agents/resumeandmatching/resumes and
    persists application document (without file bytes) in MongoDB.
    """
    job_id = request.form.get("job_id")
    name = request.form.get("name")
    email = request.form.get("email")
    resume = request.files.get("resume")

    if not job_id or not name or not email or not resume:
        return jsonify({"error": "Missing job_id, name, email, or resume"}), 400
    try:
        # Validate job exists and approved
        job = collection.find_one({"_id": ObjectId(job_id), "approved": True})
        if not job:
            return jsonify({"error": "Job not found or not approved"}), 404

        # Save resume to disk with safe unique filename
        base_name = secure_filename(resume.filename or "resume")
        timestamp = str(int(__import__("time").time()))
        stored_name = f"{job_id}_{timestamp}_{base_name}"
        stored_path = os.path.join(RESUMES_FOLDER, stored_name)
        resume.save(stored_path)

        # Create application document (no file bytes)
        app_doc = {
            "job_id": ObjectId(job_id),
            "name": name,
            "email": email,
            "resume_filename": resume.filename,
            "resume_path": stored_path,
            "created_at": __import__("datetime").datetime.utcnow(),
        }
        result = applications_col.insert_one(app_doc)

        return jsonify({"message": "Application received", "application_id": str(result.inserted_id)}), 201
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
