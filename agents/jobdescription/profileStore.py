import os
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
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

# Folder to watch
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCH_FOLDER = os.path.join(BASE_DIR, "output")
os.makedirs(WATCH_FOLDER, exist_ok=True)

class JsonHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".json"):
            try:
                with open(event.src_path, "r") as f:
                    data = json.load(f)
                # add approved flag
                collection.insert_one({**data, "approved": False})
                print(f"Inserted {os.path.basename(event.src_path)} into MongoDB with approved=False")
            except Exception as e:
                print(f"Failed to insert {os.path.basename(event.src_path)}: {e}")


if __name__ == "__main__":
    event_handler = JsonHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()
    print(f"Watching folder: {WATCH_FOLDER} for new JSON files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
