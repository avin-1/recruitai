from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId
import requests
import json
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=False)
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    logger.error("Error: MONGODB_URI not found in environment!")
else:
    # Masked URI for logs
    masked_uri = MONGO_URI.replace(MONGO_URI.split('@')[0], 'mongodb+srv://****:****') if '@' in MONGO_URI else '****'
    logger.info(f"Connecting to MongoDB: {masked_uri}")
    
# MongoDB setup
DB_NAME = "profiles"
COLLECTION_NAME = "json_files"
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
applications_col = db.get_collection("applications")

try:
    applications_col.create_index([("job_id", 1), ("email", 1)], unique=True)
except Exception:
    pass

# Microservice URLs
NOTIFICATION_SERVICE_URL = "http://localhost:5005"
ML_SERVICE_URL = "http://localhost:5004"
INTERVIEW_SERVICE_URL = "http://localhost:5002"

# Flask app
app = Flask(__name__)
# Allow CORS
CORS(app)

# Set upload folder relative to backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: In microservices, local file storage shared between services is tricky. 
# For now, we assume services run on same machine or have shared volume.
# Ideally, use S3/Cloud Storage. 
# We'll use a local 'uploads' dir in this service.
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
RESUMES_FOLDER = os.path.join(BASE_DIR, "resumes")
os.makedirs(RESUMES_FOLDER, exist_ok=True)

# ---------------- Root Endpoint (Health Check) ----------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "online",
        "message": "REDAI Core API (Microservice) is running",
        "services": ["upload", "core"]
    }), 200

# ---------------- Mock Fetch Candidates (LinkedIn/Naukri) ----------------
@app.route('/fetch_candidates', methods=['POST'])
def fetch_candidates():
    """
    Mock endpoint to fetch candidates from external sources (LinkedIn, Naukri).
    """
    try:
        data = request.json
        job_id = data.get('job_id')
        source = data.get('source')
        
        if not job_id or not source:
            return jsonify({"error": "Missing job_id or source"}), 400
            
        logger.info(f"Fetching candidates for Job {job_id} from {source}")
        
        # Mock Logic
        import time
        time.sleep(1.5) # Simulate network delay
        
        return jsonify({
            "status": "success",
            "message": f"Sync initiated with {source.title()}. 0 new candidates found (Mock).",
            "count": 0
        }), 200
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- File Upload Endpoint ----------------
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(filepath)

    return jsonify({"message": f"File uploaded successfully: {file.filename}"}), 200

# ---------------- Retrieve Job Profiles ----------------
@app.route("/profiles", methods=["GET"])
def get_profiles():
    try:
        profiles_cursor = collection.find({})
        profiles = []
        for profile in profiles_cursor:
            profile["_id"] = str(profile["_id"])
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
            doc["_id"] = str(doc["_id"])
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
        doc["_id"] = str(doc["_id"])
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

# ---------------- List Applications ----------------
@app.route("/applications", methods=["GET"])
def list_applications():
    job_id = request.args.get("job_id")
    limit = request.args.get("limit", type=int)
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    try:
        query = {"job_id": ObjectId(job_id)}
        sort_spec = [("score", -1), ("created_at", -1)]
        cursor = applications_col.find(query).sort(sort_spec)
        if limit and limit > 0:
            cursor = cursor.limit(limit)
        apps = []
        for a in cursor:
            a["_id"] = str(a["_id"])
            a["job_id"] = str(a["job_id"])
            apps.append({
                "_id": a["_id"],
                "name": a.get("name"),
                "email": a.get("email"),
                "resume_filename": a.get("resume_filename"),
                "score": a.get("score"),
                "status": a.get("status", "selected"), 
                "created_at": a.get("created_at").isoformat() if a.get("created_at") else None,
            })
        return jsonify({"applications": apps}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Update Application Status ----------------
@app.route("/update_application_status", methods=["POST"])
def update_application_status():
    data = request.get_json()
    application_id = data.get("application_id")
    status = data.get("status")

    if not application_id or not status:
        return jsonify({"error": "Missing application_id or status"}), 400

    try:
        result = applications_col.update_one(
            {"_id": ObjectId(application_id)},
            {"$set": {"status": status}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Application not found"}), 404
            
        # Send rejection email if status is rejected
        if status == 'rejected':
            app_doc = applications_col.find_one({"_id": ObjectId(application_id)})
            if app_doc:
                job = collection.find_one({"_id": app_doc['job_id']})
                job_title = job.get("job_title") or job.get("title") or "Unknown Position"
                company = job.get("company") or "Our Company"
                
                # CALL NOTIFICATION SERVICE
                try:
                    payload = {
                        "candidate_email": app_doc.get('email'),
                        "candidate_name": app_doc.get('name'),
                        "job_title": job_title,
                        "company": company
                    }
                    requests.post(f"{NOTIFICATION_SERVICE_URL}/send/rejection", json=payload)
                except Exception as ex:
                    logger.error(f"Failed to call Notification Service: {ex}")
            
        return jsonify({"message": f"Status updated to {status}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Applicant Apply ----------------
@app.route("/apply", methods=["POST"])
def apply_job():
    job_id = request.form.get("job_id")
    name = request.form.get("name")
    email = request.form.get("email")
    resume = request.files.get("resume")

    if not job_id or not name or not email or not resume:
        return jsonify({"error": "Missing job_id, name, email, or resume"}), 400
    try:
        job = collection.find_one({"_id": ObjectId(job_id), "approved": True})
        if not job:
            return jsonify({"error": "Job not found or not approved"}), 404

        base_name = secure_filename(resume.filename or "resume")
        timestamp = str(int(__import__("time").time()))
        stored_name = f"{job_id}_{timestamp}_{base_name}"
        stored_path = os.path.abspath(os.path.join(RESUMES_FOLDER, stored_name))
        resume.save(stored_path)
        
        # Reset file pointer for reading
        resume.seek(0)
        
        # 1. PARSE RESUME (Call Parsing Service)
        resume_text = ""
        try:
            # Send file to parsing service
            files = {'resume': open(stored_path, 'rb')}
            PARSING_SERVICE_URL = "http://localhost:5006"
            resp_parse = requests.post(f"{PARSING_SERVICE_URL}/parse", files=files, timeout=10)
            
            # Reset file pointer if needed, but we opened a new handle
            
            if resp_parse.status_code == 200:
                resume_text = resp_parse.json().get('text', "")
            else:
                logger.warning(f"Parsing Service failed: {resp_parse.text}")
        except Exception as ex:
            logger.error(f"Failed to call Parsing Service: {ex}")

        # 2. SCORE RESUME (Call Matching Service)
        score_val = 0.0
        try:
            if resume_text:
                jd_text = job.get("responsibilities") or job.get("summary") or job.get("description") or ""
                payload = {
                    'resume_text': resume_text,
                    'job_description': jd_text
                }
                
                resp_match = requests.post(f"{ML_SERVICE_URL}/score", json=payload, timeout=10)
                if resp_match.status_code == 200:
                    score_val = resp_match.json().get('score', 0.0)
                else:
                    logger.warning(f"ML Matching Service returned {resp_match.status_code}")
        except Exception as ex:
            logger.error(f"Failed to call ML Service: {ex}")

        # Upsert application
        filter_doc = {"job_id": ObjectId(job_id), "email": email}
        update_doc = {
            "$set": {
                "name": name,
                "resume_filename": resume.filename,
                "resume_path": stored_path,
                "score": float(score_val),
            },
            "$setOnInsert": {
                "created_at": __import__("datetime").datetime.utcnow(),
            },
        }
        result = applications_col.update_one(filter_doc, update_doc, upsert=True)

        if result.upserted_id is not None:
            app_id = str(result.upserted_id)
        else:
            existing = applications_col.find_one(filter_doc, {"_id": 1})
            app_id = str(existing["_id"]) if existing else None
        return jsonify({"message": "Application received", "application_id": app_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Select Candidates ----------------
@app.route("/select_candidates", methods=["POST"])
def select_candidates():
    data = request.get_json()
    job_id = data.get("job_id")
    candidates = data.get("candidates", [])
    
    if not job_id or not candidates:
        return jsonify({"error": "job_id and candidates required"}), 400
    
    try:
        job = collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        job_title = job.get("job_title") or job.get("title") or "Unknown Position"
        company = job.get("company") or "Our Company"
        
        valid_candidates = []
        for cand in candidates:
            # Check status
            app = applications_col.find_one({"job_id": ObjectId(job_id), "email": cand['email']})
            if app and app.get('status') == 'rejected':
                continue
            valid_candidates.append(cand)

        if not valid_candidates:
             return jsonify({"error": "No eligible candidates selected."}), 400

        # CALL NOTIFICATION SERVICE
        payload = {
            "job_id": str(job_id),
            "job_title": job_title,
            "company": company,
            "candidates": valid_candidates
        }
        resp = requests.post(f"{NOTIFICATION_SERVICE_URL}/select-candidates", json=payload)
        
        if resp.status_code == 200:
            return jsonify(resp.json()), 200
        else:
            return jsonify({"error": "Notification service failed", "details": resp.text}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Get Selected Candidates ----------------
@app.route("/selected_candidates", methods=["GET"])
def get_selected_candidates():
    job_id = request.args.get("job_id")
    try:
        # CALL NOTIFICATION SERVICE
        params = {}
        if job_id: params['job_id'] = job_id
        resp = requests.get(f"{NOTIFICATION_SERVICE_URL}/selected-history", params=params)
        if resp.status_code == 200:
            return jsonify(resp.json()), 200
        else:
           return jsonify({"error": "Failed to fetch from notification service"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Run App ----------------
# ---------------- Delete Profile ----------------
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

# ---------------- Serve Static Files for Social Images ----------------
@app.route('/static/<path:path>')
def send_static(path):
    return __import__("flask").send_from_directory('static', path)

# ---------------- Approve Profile ----------------
@app.route("/approve", methods=["POST"])
def approve_profile():
    # Check if request is multipart (has file or form data)
    if request.content_type and "multipart/form-data" in request.content_type:
        profile_id = request.form.get("profile_id")
        post_to_json = request.form.get("post_to", "[]")
        import json
        try:
            post_to = json.loads(post_to_json)
        except:
            post_to = []
    else:
        # Fallback for JSON requests (legacy/simple approval)
        data = request.get_json() or {}
        profile_id = data.get("profile_id")
        post_to = []

    if not profile_id:
        return jsonify({"error": "No profile_id provided"}), 400

    try:
        # 1. Approve in DB
        result = collection.update_one({"_id": ObjectId(profile_id)}, {"$set": {"approved": True}})
        if result.matched_count == 0:
            return jsonify({"error": "Profile not found"}), 404
            
        # 2. Handle Social Media Posting
        if post_to:
            try:
                # Get Job Details
                job = collection.find_one({"_id": ObjectId(profile_id)})
                
                # Handle Image - simplified for microservice (no local file upload for images yet)
                # If image provided in multipart, save it.
                image_url = None
                
                if "image" in request.files and request.files["image"].filename:
                    img_file = request.files["image"]
                    filename = secure_filename(f"{profile_id}_{img_file.filename}")
                    save_path = os.path.join(BASE_DIR, "static", "social_images", filename)
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    img_file.save(save_path)
                    
                    host_url = request.host_url
                    if "localhost" in host_url or "127.0.0.1" in host_url:
                        # Use public placeholder for testing Instagram
                        image_url = "https://images.unsplash.com/photo-1575936123452-b67c3203c357?ixlib=rb-4.0.3&w=1000&q=80"
                    else:
                         # Ensure https
                        if not host_url.startswith("https"):
                            host_url = host_url.replace("http", "https", 1)
                        image_url = f"{host_url}static/social_images/{filename}"
                else: 
                     # Default image logic if needed (skipping copy from root for simplicity)
                     image_url = "https://images.unsplash.com/photo-1575936123452-b67c3203c357?ixlib=rb-4.0.3&w=1000&q=80"

                if image_url:
                    # Import our copied service
                    try:
                        from utils.social_media_service import SocialMediaService
                        sms = SocialMediaService()
                        post_results = sms.post_job(job, image_url, post_to)
                        return jsonify({
                            "message": "Profile approved successfully", 
                            "social_media_results": post_results
                        }), 200
                    except ImportError:
                        return jsonify({"message": "Privile approved but Social Media Service module missing."}), 200
            except Exception as sm_e:
                logger.error(f"Social Media Error: {sm_e}")
                # Don't fail the approval if social media fails
                return jsonify({"message": f"Profile approved, but social media posting failed: {str(sm_e)}"}), 200

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

        # Remove _id from the update data
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

# ---------------- Create Job Profile from Text ----------------
@app.route("/create-job-profile", methods=["POST"])
def create_job_profile_from_text():
    """Create a job profile from text input (job description prompt/details)"""
    data = request.get_json()
    job_description_text = data.get("job_description")
    
    if not job_description_text:
        return jsonify({"error": "job_description is required"}), 400
    
    try:
        # Import the text-based parsing function from our local utils
        from utils.jdParsing import parse_job_description_from_text
        
        # Parse the job description text into structured profile
        profile = parse_job_description_from_text(job_description_text)
        
        # Set approved to False by default (needs HR approval)
        profile["approved"] = False
        
        # Insert into MongoDB
        result = collection.insert_one(profile)
        profile["_id"] = str(result.inserted_id)
        
        return jsonify({
            "message": "Job profile created successfully",
            "profile": profile
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating job profile: {e}")
        return jsonify({"error": str(e)}), 500

# ---------------- Agentic Chat Endpoint ----------------
@app.route("/chat", methods=["POST"])
def chat_agent():
    """Agentic chat endpoint for job profile management"""
    try:
        data = request.get_json()
        message = data.get("message", "").lower()
        context = data.get("context", {}) 
        
        response = {
            "success": True,
            "message": "I didn't understand that command.",
            "action": None,
            "data": None
        }

        if "change" in message or "set" in message or "update" in message:
            import re
            match = re.search(r'(?:change|set|update)\s+(.*?)\s+to\s+(.*)', message, re.IGNORECASE)
            if match:
                field_raw = match.group(1).strip().lower()
                value = match.group(2).strip()
                field_map = {
                    "title": "job_title", "role": "job_title",
                    "company": "company", "location": "location",
                    "experience": "experience_level", "education": "educational_requirements"
                }
                field = field_map.get(field_raw, field_raw)
                response["message"] = f"I've updated the {field_raw} to '{value}'. Please review the changes."
                response["action"] = "UPDATE_PROFILE_FIELD"
                response["data"] = {"field": field, "value": value}
            else:
                response["message"] = "I can update the profile. Try saying 'Change title to Senior Developer'."
        
        elif "create" in message and "new" in message:
            response["message"] = "Sure, let's start a new profile. What's the job title?"
            response["action"] = "CREATE_NEW_PROFILE"
            
        elif "approve" in message:
            response["message"] = "Great! I'll approve this profile now."
            response["action"] = "APPROVE_PROFILE"
            
        else:
            if not context.get("profile"):
                response["message"] = "I can help you create a job profile. Describe the position you're hiring for."
            else:
                response["message"] = "I can help you modify this profile. You can ask me to change the title, location, or other details."
            
        return jsonify(response)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- Run App ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
