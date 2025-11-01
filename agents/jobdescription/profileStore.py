import os
import json
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

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

def store_profile(file_path):
    """
    Reads a JSON file and inserts its content into MongoDB.
    """
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        # add approved flag
        collection.insert_one({**data, "approved": False})
        print(f"Inserted {os.path.basename(file_path)} into MongoDB with approved=False")
        return True
    except Exception as e:
        print(f"Failed to insert {os.path.basename(file_path)}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python profileStore.py <path_to_json>")
        sys.exit(1)

    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"Error: File not found at {json_path}")
        sys.exit(1)

    if store_profile(json_path):
        sys.exit(0)
    else:
        sys.exit(1)
