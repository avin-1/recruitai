# Backend Study Guide

## 1. Tech Stack Overview

- **Language:** Python
- **Framework:** Flask
- **Server:** Waitress (WSGI server for production)
- **Database:**
    - **MongoDB:** Primary transactional DB (NoSQL).
    - **ChromaDB:** Vector Database for AI embeddings.
- **ORM/ODM:** PyMongo (Direct driver, no heavy ORM like SQLAlchemy).
- **AI Integration:** OpenAI API / HuggingFace (via LangGraph/LangChain).

### Why this stack?
- **Flask:** Lightweight and explicit. Unlike Django, it doesn't force a structure on you. This is great for our "Hybrid" architecture where we need some custom microservice patterns.
- **Python:** The #1 language for AI. Since our system is AI-heavy, using Python for the backend keeps everything in one ecosystem.
- **MongoDB:** Flexible schema. Ideal for "Profiles" and "Job Descriptions" which change structure often.
- **Waitress:** Flask's built-in server is for development only. Waitress is a production-ready WSGI server that can handle multiple concurrent requests efficiently on Windows/Linux.

## 2. API Design & Database Schema

### Key API Endpoints (`upload_api.py`)
- `POST /upload`: Handles file uploads (resumes).
- `GET /jobs`: Lists available job openings.
- `POST /apply`: Submits an application (calculates match score instantly).
- `POST /approve`: "Human in the loop" step. HR approves a parsed profile.

### Database Schema (MongoDB)
We use a **Document-Oriented** model.
1. **collection `json_files` (Profiles/Jobs):**
    - Stores the parsed Job Descriptions.
    - Fields: `job_title`, `company`, `skills` (list), `approved` (boolean).
2. **collection `applications`:**
    - Stores candidate applications.
    - Fields: `job_id` (Link to Job), `email`, `score` (computed match), `resume_path`.
    - **Index:** Compound Unique Index on `(job_id, email)` prevents spamming the same job.

## 3. Security & Authentication

- **Current State:** Minimal/None.
- **Why?** It's a prototype/MVP. We focus on the AI features first.
- **Improvement for Exam:** "In a real production system, I would implement **JWT (JSON Web Tokens)**. Users would login -> get a token -> send token in Header -> Backend validates token before allowing access to `/approve`."

## 4. Exam Q&A Preparation

**Q: What is the purpose of `wsgi.py` or Waitress?**
**A:** Flask's `app.run()` is single-threaded and not secure for the internet. A WSGI server (like Waitress or Gunicorn) sits between Nginx and Flask to handle concurrency and buffering.

**Q: Explain Vector Database (ChromaDB) usage.**
**A:** Standard databases search for **KEYWORDS** (e.g., "Python"). Vector databases search for **MEANING**.
- "I know coding" ≈ "I am a developer" (High semantic similarity).
- A keyword search would miss this. A Vector DB catches it by converting text into high-dimensional geometric vectors (embeddings).

**Q: Why separate `upload_api.py` from `agent_orchestrator.py`?**
**A:** Separation of Concerns.
- `upload_api.py`: Synchronous. Fast. Handles User I/O.
- `agent_orchestrator.py`: Asynchronous. Slow. Handles "Thinking" and "Reasoning".
- This prevents the user from waiting 30 seconds for a page load while the AI thinks.
