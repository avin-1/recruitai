import os
import sys
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
from langgraph.graph import StateGraph, START, END

# Robust imports so this file can be run as a module or script
try:
    from .config import CONFIG  # type: ignore
    from .utils.resume_parser import parse_resume  # type: ignore
    from .utils.matcher import semantic_match  # type: ignore
    from .utils.llm_scorer import compute_score  # type: ignore
    from .utils.database import get_session_factory, upsert_candidate  # type: ignore
except Exception:
    try:
        from agents.resumeandmatching.config import CONFIG  # type: ignore
        from agents.resumeandmatching.utils.resume_parser import parse_resume  # type: ignore
        from agents.resumeandmatching.utils.matcher import semantic_match  # type: ignore
        from agents.resumeandmatching.utils.llm_scorer import compute_score  # type: ignore
        from agents.resumeandmatching.utils.database import get_session_factory, upsert_candidate  # type: ignore
    except Exception:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        from config import CONFIG  # type: ignore
        from utils.resume_parser import parse_resume  # type: ignore
        from utils.matcher import semantic_match  # type: ignore
        from utils.llm_scorer import compute_score  # type: ignore
        from utils.database import get_session_factory, upsert_candidate  # type: ignore


load_dotenv()


# ----- State -----
@dataclass
class AgentState:
    resumes: List[str]
    jobs: List[Dict]
    current_resume_path: Optional[str] = None
    current_resume_text: Optional[str] = None
    shortlisted: List[Dict] = field(default_factory=list)
    rejected_count: int = 0


def fetch_jobs_node(state: AgentState) -> AgentState:
    uri = os.getenv(CONFIG["env"]["mongodb_uri_env"]) or ""
    jobs: List[Dict] = []
    if not uri:
        print("Warning: MONGODB_URI not set. Proceeding with no jobs.")
    else:
        try:
            client = MongoClient(uri)
            db = client["profiles"]
            col = db["json_files"]
            for doc in col.find({"approved": True}):
                jobs.append({
                    "_id": str(doc.get("_id")),
                    "title": doc.get("job_title") or doc.get("title"),
                    "description": doc.get("responsibilities") or doc.get("summary") or "",
                    "raw": doc,
                })
        except Exception as exc:
            print(f"Warning: Failed to fetch jobs from MongoDB: {exc}")
    state.jobs = jobs
    return state


def pick_next_resume_node(state: AgentState) -> AgentState:
    if not state.resumes:
        return state
    state.current_resume_path = os.path.abspath(state.resumes.pop(0))
    state.current_resume_text = parse_resume(state.current_resume_path) or ""
    return state


def score_against_jobs_node(state: AgentState) -> AgentState:
    if not state.current_resume_text:
        return state
    threshold = CONFIG["thresholds"]["rejection"]
    session_factory = get_session_factory(CONFIG["db"]["sqlalchemy_url"])
    session = session_factory()

    best_score = -1.0
    best_job_id = None
    if state.jobs:
        for job in state.jobs:
            jd_text = job.get("description", "")
            # combine semantic and llm
            sem = semantic_match(state.current_resume_text, jd_text, CONFIG["models"]["sbert"])  # 0..1
            llm = compute_score(state.current_resume_text, jd_text, CONFIG["models"]["llm"])  # 0..100
            score = 0.5 * (sem * 100.0) + 0.5 * llm
            if score > best_score:
                best_score = score
                best_job_id = job.get("_id")
    else:
        best_score = 0.0
        best_job_id = None

    email = os.path.basename(state.current_resume_path).split("_")[0] if state.current_resume_path else "unknown@example.com"

    if best_score >= threshold:
        upsert_candidate(session, email=email, resume_path=state.current_resume_path, score=best_score, job_id=best_job_id)
        # Also upsert into MongoDB for visibility in the main app
        try:
            mongo_uri = os.getenv(CONFIG["env"]["mongodb_uri_env"]) or ""
            if mongo_uri and state.current_resume_path:
                mclient = MongoClient(mongo_uri)
                mdb = mclient["profiles"]
                applications = mdb.get_collection("applications")
                # Update the original apply document by matching the stored resume path
                filter_doc = {"resume_path": state.current_resume_path}
                update_set = {
                    "score": float(max(0.0, min(100.0, best_score)))
                }
                # Optionally attach job_id if resolvable
                if best_job_id:
                    try:
                        update_set["job_id"] = ObjectId(best_job_id)
                    except Exception:
                        update_set["job_id"] = best_job_id
                applications.update_one(filter_doc, {"$set": update_set}, upsert=False)
        except Exception as _mongo_exc:
            # Non-fatal: keep processing even if Mongo write fails
            print(f"Warning: failed to upsert score into MongoDB: {_mongo_exc}")
        if state.shortlisted is None:
            state.shortlisted = []
        state.shortlisted.append({"email": email, "score": round(best_score, 2), "job_id": best_job_id})
    else:
        state.rejected_count += 1
        # simulate sending rejection email (log only)
        print(f"Rejection: {email} scored {best_score:.1f}")

    session.close()
    return state


def more_resumes_condition(state: AgentState) -> bool:
    return len(state.resumes) > 0


def run_agent():
    resumes_dir = CONFIG["paths"]["resumes"]
    # Watch mode: process new files continuously
    seen = set()
    while True:
        all_pdfs = [os.path.join(resumes_dir, f) for f in os.listdir(resumes_dir) if f.lower().endswith(".pdf")]
        new_pdfs = [p for p in all_pdfs if p not in seen]
        if not new_pdfs:
            time.sleep(2)
            continue
        for p in new_pdfs:
            seen.add(p)
        state = AgentState(resumes=new_pdfs, jobs=[], shortlisted=[], rejected_count=0)

        workflow = StateGraph(AgentState)
        workflow.add_node("fetch_jobs", fetch_jobs_node)
        workflow.add_node("pick_resume", pick_next_resume_node)
        workflow.add_node("score_resume", score_against_jobs_node)

        workflow.add_edge(START, "fetch_jobs")
        workflow.add_edge("fetch_jobs", "pick_resume")
        workflow.add_edge("pick_resume", "score_resume")
        # loop until resumes empty
        workflow.add_conditional_edges(
            "score_resume",
            lambda s: "more" if more_resumes_condition(s) else "done",
            {"more": "pick_resume", "done": END},
        )

        graph = workflow.compile()
        final = graph.invoke(state)

        # Summary log
        shortlisted = getattr(final, "shortlisted", None)
        if shortlisted is None and isinstance(final, dict):
            shortlisted = final.get("shortlisted", [])
        print("Shortlisted candidates (batch):")
        for c in shortlisted or []:
            print(f" - {c['email']}: {c['score']} (job {c['job_id']})")


if __name__ == "__main__":
    run_agent()


