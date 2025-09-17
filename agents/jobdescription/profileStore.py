import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv

# Load .env
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in .env")

# This file is now a utility module. The core logic has been moved to graph.py
# The watchdog and main execution logic has been removed.

# MongoDB setup
DB_NAME = "profiles"
COLLECTION_NAME = "json_files"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def store_profile(data: dict):
    """
    Stores a dictionary (JSON object) into MongoDB.
    Note: This function is now called from graph.py
    """
    try:
        # The 'approved' field is now added in the graph node
        # but we can keep it here as a fallback.
        if 'approved' not in data:
            data['approved'] = False
        collection.insert_one(data)
        print(f"Successfully inserted profile into MongoDB.")
    except Exception as e:
        print(f"Failed to insert profile into MongoDB: {e}")
        raise # Re-raise the exception to be caught by the graph
