from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)

# Use the exact database name where you inserted the prompt
db = client["prompt_db"]   # <-- match exactly as used during insert
prompts_collection = db["prompts"]

# ID of the prompt you want to fetch
PROMPT_ID = "job_parser_v1"

# Retrieve by custom id
retrieved = prompts_collection.find_one({"id": PROMPT_ID})

# Write retrieved prompt to prompt.txt
if retrieved:
    with open("prompt.txt", "w", encoding="utf-8") as f:
        f.write(f"ID: {retrieved.get('id')}\n")
        f.write(f"Name: {retrieved.get('name')}\n")
        f.write(f"Description: {retrieved.get('description')}\n\n")
        f.write("Prompt Content:\n")
        f.write(retrieved.get("content", ""))  # content instead of text
    print("✅ Prompt saved to prompt.txt")
else:
    print(f"No prompt found with id {PROMPT_ID}")
