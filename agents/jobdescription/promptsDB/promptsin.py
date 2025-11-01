import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not set. Please define it in your environment or .env file.")

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

# Select database and collection
db = client["prompt_db"]
collection = db["prompts"]

# Define the prompt document
prompt_doc = {
    "id": "job_parser_v1",
    "name": "Job Description Parsing Prompt",
    "description": "Extracts structured job information (title, company, location, responsibilities, skills, experience, education) from raw job description text.",
    "content": """You are an expert job parsing agent. Your task is to extract key information from the following job description and return it as a structured JSON object.

Extract the following fields:
- **job_title**: The official title of the job.
- **company**: The name of the hiring company.
- **location**: The primary location of the job (e.g., city, country).
- **responsibilities**: A list of key responsibilities.
- **required_skills**: A list of essential skills or technologies.
- **experience_level**: The required years of experience or a general level (e.g., "5+ years", "Entry-level").
- **educational_requirements**: The minimum educational qualifications (e.g., "Bachelor's degree in Computer Science").

If a field is not explicitly found, use `null` for its value.
The output MUST be a valid JSON object.

---
Job Description:
{job_description_text}
---

JSON Output:"""
}

# Ensure "id" is unique (create an index if not exists)
collection.create_index("id", unique=True)

# Insert prompt into MongoDB (upsert to avoid duplicates)
result = collection.update_one(
    {"id": prompt_doc["id"]},  # Filter by ID
    {"$set": prompt_doc},      # Update fields
    upsert=True                # Insert if not exists
)

if result.upserted_id:
    print(f"✅ Prompt inserted with ObjectId: {result.upserted_id}")
else:
    print(f"🔄 Prompt with id '{prompt_doc['id']}' updated.")
