from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from bson.objectid import ObjectId
import math
from email_service import EmailService
try:
    # Optional advanced scoring imports
    from agents.resumeandmatching.utils.resume_parser import parse_resume as _parse_resume
    from agents.resumeandmatching.utils.matcher import semantic_match as _semantic_match
    from agents.resumeandmatching.utils.llm_scorer import compute_score as _llm_score
    _ADVANCED_SCORING = True
except Exception:
    _ADVANCED_SCORING = False
    _parse_resume = None
    _semantic_match = None
    _llm_score = None
import fitz  # PyMuPDF (fallback text extraction)

# Load .env explicitly
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)
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
# Ensure unique (job_id, email) to prevent duplicate applications per job
try:
    applications_col.create_index([("job_id", 1), ("email", 1)], unique=True)
except Exception:
    pass

# Flask app
app = Flask(__name__)
CORS(app)  # enable CORS for all routes

# Initialize email service
email_service = EmailService()

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
        # Return all applications for this job; sort by score desc (missing/null last), then created_at desc
        query = {"job_id": ObjectId(job_id)}
        # Prefer score desc if available, then created_at desc
        sort_spec = [("score", -1), ("created_at", -1)]
        cursor = applications_col.find(query).sort(sort_spec)
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
                "score": a.get("score"),
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
        stored_path = os.path.abspath(os.path.join(RESUMES_FOLDER, stored_name))
        resume.save(stored_path)

        # Compute score for ranking (best-effort)
        try:
            # Extract JD text
            jd_text = job.get("responsibilities") or job.get("summary") or job.get("description") or ""
            # Extract resume text
            if _parse_resume is not None:
                resume_text = _parse_resume(stored_path) or ""
            else:
                try:
                    d = fitz.open(stored_path)
                    resume_text = "".join(p.get_text() for p in d)
                    d.close()
                except Exception:
                    resume_text = ""

            score_val = 0.0
            if resume_text and jd_text:
                if _ADVANCED_SCORING and _semantic_match is not None and _llm_score is not None:
                    sem = _semantic_match(resume_text, jd_text, "all-MiniLM-L6-v2")  # 0..1
                    llm = _llm_score(resume_text, jd_text, "openai/gpt-oss-20b:fireworks-ai")  # 0..100 (fallback inside if no token)
                    score_val = 0.5 * (sem * 100.0) + 0.5 * llm
                else:
                    # Lightweight heuristic fallback
                    r_set = set(resume_text.lower().split())
                    j_set = set(jd_text.lower().split())
                    overlap = len(r_set & j_set)
                    base = len(j_set) or 1
                    score_val = 100.0 * overlap / base
            score_val = float(max(0.0, min(100.0, score_val)))
        except Exception:
            score_val = 0.0

        # Upsert application (unique per job_id + email); update score and latest resume metadata
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

        # Return id when inserted; for updates, fetch existing id
        if result.upserted_id is not None:
            app_id = str(result.upserted_id)
        else:
            existing = applications_col.find_one(filter_doc, {"_id": 1})
            app_id = str(existing["_id"]) if existing else None
        return jsonify({"message": "Application received", "application_id": app_id}), 201
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

# ---------------- Serve Static Files ----------------
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
            # Get Job Details
            job = collection.find_one({"_id": ObjectId(profile_id)})
            
            # Handle Image
            image_url = None
            if "image" in request.files and request.files["image"].filename:
                # Save uploaded image
                img_file = request.files["image"]
                filename = secure_filename(f"{profile_id}_{img_file.filename}")
                save_path = os.path.join(BASE_DIR, "static", "social_images", filename)
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                img_file.save(save_path)
                
                # Construct URL
                # NOTE: Instagram API requires a PUBLICLY ACCESSIBLE URL.
                host_url = request.host_url
                if "localhost" in host_url or "127.0.0.1" in host_url:
                    # Use a stable public placeholder for testing
                    image_url = "https://images.unsplash.com/photo-1575936123452-b67c3203c357?ixlib=rb-4.0.3&w=1000&q=80"
                    import logging
                    logging.warning(f"Localhost detected ({host_url}). Using public placeholder image for Instagram: {image_url}")
                else:
                    image_url = f"{host_url}static/social_images/{filename}".replace("http://", "https://")
            else:
                # Use default JDImage.jpg
                # Check if it exists in root and copy to static if needed
                root_img_path = os.path.join(BASE_DIR, "..", "JDImage.jpg")
                if os.path.exists(root_img_path):
                    filename = "JDImage.jpg"
                    static_img_path = os.path.join(BASE_DIR, "static", "social_images", filename)
                    os.makedirs(os.path.dirname(static_img_path), exist_ok=True)
                    if not os.path.exists(static_img_path):
                        import shutil
                        shutil.copy(root_img_path, static_img_path)
                    
                    # Construct URL
                    host_url = request.host_url
                    if "localhost" in host_url or "127.0.0.1" in host_url:
                        # Use a stable public placeholder for testing
                        image_url = "https://images.unsplash.com/photo-1575936123452-b67c3203c357?ixlib=rb-4.0.3&w=1000&q=80"
                        import logging
                        logging.warning(f"Localhost detected ({host_url}). Using public placeholder image for Instagram: {image_url}")
                    else:
                        image_url = f"{host_url}static/social_images/{filename}".replace("http://", "https://")

            if image_url:
                from social_media_service import SocialMediaService
                sms = SocialMediaService()
                post_results = sms.post_job(job, image_url, post_to)
                return jsonify({
                    "message": "Profile approved successfully", 
                    "social_media_results": post_results
                }), 200
            else:
                 return jsonify({
                    "message": "Profile approved, but could not resolve image for social media posting.",
                }), 200

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

# ---------------- Select Candidates ----------------
@app.route("/select_candidates", methods=["POST"])
def select_candidates():
    """Select specific candidates for a job and send them emails"""
    data = request.get_json()
    job_id = data.get("job_id")
    candidates = data.get("candidates", [])
    
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    
    if not candidates:
        return jsonify({"error": "No candidates provided"}), 400
    
    try:
        # Get job details
        job = collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Select candidates and send emails
        job_title = job.get("job_title") or job.get("title") or "Unknown Position"
        company = job.get("company") or "Our Company"
        
        results = email_service.select_candidates(
            str(job_id), 
            job_title, 
            company, 
            candidates
        )
        
        return jsonify({
            "message": f"Selection process completed",
            "total_selected": results["total_selected"],
            "successful_emails": len(results["success"]),
            "failed_emails": len(results["failed"]),
            "success": results["success"],
            "failed": results["failed"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- Get Selected Candidates ----------------
@app.route("/selected_candidates", methods=["GET"])
def get_selected_candidates():
    """Get list of selected candidates"""
    job_id = request.args.get("job_id")
    
    try:
        selected = email_service.get_selected_candidates(job_id)
        return jsonify({"selected_candidates": selected}), 200
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
        # Import the text-based parsing function
        import sys
        import os
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        jd_path = os.path.join(backend_dir, "..", "agents", "jobdescription")
        if jd_path not in sys.path:
            sys.path.insert(0, jd_path)
        
        from jdParsing import parse_job_description_from_text
        
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
        return jsonify({"error": str(e)}), 500

# ---------------- Agentic Chat Endpoint ----------------
@app.route("/chat", methods=["POST"])
def chat_agent():
    """Agentic chat endpoint for job profile management"""
    try:
        data = request.get_json()
        message = data.get("message", "").lower()
        context = data.get("context", {}) # e.g., current profile data
        
        response = {
            "success": True,
            "message": "I didn't understand that command.",
            "action": None,
            "data": None
        }

        # Intent: Update field
        # "Change title to Senior Engineer"
        # "Set location to New York"
        if "change" in message or "set" in message or "update" in message:
            import re
            # Try to extract field and value
            # Simple regex for "change X to Y"
            match = re.search(r'(?:change|set|update)\s+(.*?)\s+to\s+(.*)', message, re.IGNORECASE)
            if match:
                field_raw = match.group(1).strip().lower()
                value = match.group(2).strip()
                
                # Map common terms to field names
                field_map = {
                    "title": "job_title",
                    "role": "job_title",
                    "company": "company",
                    "location": "location",
                    "experience": "experience_level",
                    "education": "educational_requirements"
                }
                
                field = field_map.get(field_raw, field_raw)
                
                response["message"] = f"I've updated the {field_raw} to '{value}'. Please review the changes."
                response["action"] = "UPDATE_PROFILE_FIELD"
                response["data"] = {
                    "field": field,
                    "value": value
                }
            else:
                response["message"] = "I can update the profile. Try saying 'Change title to Senior Developer' or 'Set location to Remote'."
        
        # Intent: Create new
        elif "create" in message and "new" in message:
            response["message"] = "Sure, let's start a new profile. What's the job title?"
            response["action"] = "CREATE_NEW_PROFILE"
            
        # Intent: Approve
        elif "approve" in message:
            response["message"] = "Great! I'll approve this profile now."
            response["action"] = "APPROVE_PROFILE"
            
        else:
            # Fallback to general AI chat (mocked for now)
            # In a real system, this would call an LLM to generate a response
            if not context.get("profile"):
                response["message"] = "I can help you create a job profile. Describe the position you're hiring for, or upload a PDF."
            else:
                response["message"] = "I can help you modify this profile. You can ask me to change the title, location, or other details."
            
        return jsonify(response)

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- Run App ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
