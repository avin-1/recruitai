import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from langgraph.graph import StateGraph, START, END

# Robust import so this file can be run as a module or script
try:
    from .jdParsing import parse_job_description  # type: ignore
except Exception:
    try:
        from agents.jobdescription.jdParsing import parse_job_description  # type: ignore
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        import jdParsing as _jd  # type: ignore
        parse_job_description = _jd.parse_job_description  # type: ignore


# Load environment variables
load_dotenv()


# --- MongoDB setup ---
MONGO_URI = os.getenv("MONGODB_URI")
if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in environment")

DB_NAME = "profiles"
PROFILES_COLLECTION = "json_files"
ACTIONS_COLLECTION = "profile_actions"  # used by HR UI to send actions

mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[DB_NAME]
profiles_col = mongo_db[PROFILES_COLLECTION]
actions_col = mongo_db[ACTIONS_COLLECTION]


# ---------- Agent State ----------
@dataclass
class AgentState:
    """LangGraph state for the JD parsing and approval flow."""
    processed_files: list = field(default_factory=list)  # paths consumed from input/
    current_jd_path: str = ""
    profile: Dict = field(default_factory=dict)
    profile_id: Optional[str] = None  # Mongo _id as string
    approval_action: Optional[str] = None  # approve | modify | disapprove
    modified_profile: Optional[Dict] = None  # populated when action == modify


def latest_file(folder: str, exclude_list: list) -> Optional[str]:
    """Return the newest file path in folder not present in exclude_list."""
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)
    files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    new_files = [f for f in files if f not in exclude_list]
    return max(new_files, key=os.path.getctime) if new_files else None


# ---------- Node functions ----------
def watch_input_folder_node(state: AgentState) -> AgentState:
    """WatchInputFolderNode – monitors input/ for new JD files."""
    print("Node: Watching 'input/' for new JD PDFs...")
    while True:
        new_jd_file = latest_file("input", state.processed_files)
        if new_jd_file:
            print(f"Found new JD file: {new_jd_file}")
            state.processed_files.append(new_jd_file)
            state.current_jd_path = new_jd_file
            state.profile = {}
            state.profile_id = None
            state.approval_action = None
            state.modified_profile = None
            return state
        time.sleep(2)


def parse_jd_node(state: AgentState) -> AgentState:
    """ParseJDNode – calls parse_job_description to build profile dict."""
    print("Node: Parsing JD...")
    try:
        profile = parse_job_description(state.current_jd_path)
        # ensure an approved flag exists and is False until HR action
        profile.setdefault("approved", False)
        state.profile = profile
        print("Parsed profile keys:", list(profile.keys()))
    except Exception as exc:
        print(f"Parse error: {exc}")
        state.profile = {}
    return state


def insert_mongo_node(state: AgentState) -> AgentState:
    """InsertMongoNode – inserts profile into MongoDB."""
    print("Node: Inserting profile into Mongo...")
    if not state.profile:
        print("No profile to insert; skipping.")
        return state
    try:
        res = profiles_col.insert_one({**state.profile, "approved": False})
        state.profile_id = str(res.inserted_id)
        print(f"Inserted profile _id={state.profile_id}")
    except Exception as exc:
        print(f"Mongo insert failed: {exc}")
    return state


def approval_node(state: AgentState) -> AgentState:
    """ApprovalNode – aligns with existing Flask endpoints and blocks until approve.

    Backend behavior today:
      - /approve sets approved=True on the profile document
      - /delete removes the profile document
      - /modify updates fields and sets approved=False

    This node watches the profile document directly and infers action:
      - If approved=True -> approve (return)
      - If doc deleted -> disapprove (return and stop further steps)
      - If fields differ (excluding _id/approved) with approved=False -> keep waiting (do not proceed)
    """
    if not state.profile_id:
        return state
    print("Node: Waiting for HR approval action...")
    oid = ObjectId(state.profile_id)
    baseline = {k: v for k, v in state.profile.items() if k not in {"_id", "approved"}}
    while True:
        try:
            doc = profiles_col.find_one({"_id": oid})
            if not doc:
                state.approval_action = "disapprove"
                state.modified_profile = None
                print("Detected deletion -> disapprove (stopping flow)")
                return state

            current = {k: v for k, v in doc.items() if k not in {"_id", "approved"}}
            if doc.get("approved") is True:
                state.approval_action = "approve"
                state.modified_profile = {k: v for k, v in doc.items() if k != "_id"}
                print("Detected approved=True -> approve")
                return state
            # If modified but not approved yet, keep waiting instead of proceeding
            if current != baseline:
                print("Detected profile field changes -> waiting for approval...")
        except Exception as exc:
            print(f"Approval polling error: {exc}")
        time.sleep(2)


def update_mongo_node(state: AgentState) -> AgentState:
    """UpdateMongoNode – no-op because backend already applied changes.

    We log the final action for observability. If needed, you can
    re-enable writes here to enforce idempotency.
    """
    print(f"Final HR action: {state.approval_action}")
    return state


# ---------- Build Graph ----------
workflow = StateGraph(AgentState)
workflow.add_node("watch_input", watch_input_folder_node)
workflow.add_node("parse_jd", parse_jd_node)
workflow.add_node("insert_mongo", insert_mongo_node)
workflow.add_node("approval", approval_node)
workflow.add_node("update_mongo", update_mongo_node)

# Graph edges (simple LangGraph API)
workflow.add_edge(START, "watch_input")
workflow.add_edge("watch_input", "parse_jd")
workflow.add_edge("parse_jd", "insert_mongo")
workflow.add_edge("insert_mongo", "approval")
workflow.add_edge("approval", "update_mongo")
workflow.add_edge("update_mongo", END)

graph = workflow.compile()


if __name__ == "__main__":
    print("Starting RecruitAI JD parsing + approval service...")
    state = AgentState()
    while True:
        final_state = graph.invoke(state)
        state = final_state
        print("Cycle complete. Waiting for next JD...")
