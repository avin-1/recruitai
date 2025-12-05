# System Architecture Study Guide

## 1. High-Level Overview

**Architecture Style:** Hybrid Monolith + Microservices
The system isn't a pure monolith or a pure microservice architecture. It uses a **main backend** (Flask) that handles the core business logic (Uploads, Auth, DB access) and orchestrates **specialized microservices** (Agents) for heavy lifting.

### Why this architecture?
- **Speed of Development:** Flask allows rapid prototyping for the core CRUD features.
- **Scalability of Agents:** Heavy AI tasks (Resume Matching, Interview Scheduling) are separated into their own services (ports 5001, 5002) so they don't block the main API.
- **Flexibility:** Different agents can use different libraries or even languages (though all are Python here) without affecting the main backend.

## 2. System Diagram (Conceptual)

```mermaid
graph TD
    User[User / Frontend] -->|HTTP/REST| Nginx[Nginx Reverse Proxy]
    Nginx -->|/api| Core[Core Backend (Flask :8080)]
    Nginx -->|/interview| Interview[Interview Agent (:5002)]
    Nginx -->|/shortlist| Shortlist[Shortlisting Agent (:5001)]
    
    Core -->|Read/Write| Mongo[(MongoDB)]
    Core -->|Vector Search| Chroma[(ChromaDB)]
    
    JobWorker[Job Description Worker] -->|Polls| Folder[Input Folder]
    JobWorker -->|Updates| Mongo
    
    Interview -->|Read| Mongo
    Shortlist -->|Read/Write| Mongo
```

## 3. Integration Points

- **Frontend <-> Backend:**
  - Communication happens via **REST APIs** (JSON).
  - **Axios** is the HTTP client used in React.
  - **Nginx** handles routing, so the frontend just calls `/api/...` and Nginx knows where to send it.

- **Backend <-> Database:**
  - **MongoDB** is the primary source of truth (User profiles, Jobs, Applications).
  - **ChromaDB** (if active) is used for semantic search (finding resumes that "mean" the same as the job description, not just keyword matching).

- **Agents <-> Core:**
  - Agents often run as standalone APIs. The Core might call them via HTTP, or they might share the Database.
  - In this system, they largely **share the MongoDB** database. One writes, the other reads. This is the "Shared Database" pattern.

## 4. Exam Q&A Preparation

**Q: Why use MongoDB instead of SQL (PostgreSQL)?**
**A:** Recruitment data is highly unstructured. Resumes come in different formats, and job descriptions vary wildly. A NoSQL document store (JSON-like) allows us to store arbitrary data without complex migrations every time we add a field like "Github URL" or "Portfolio".

**Q: What is the role of Nginx?**
**A:** It acts as a **Reverse Proxy**. It sits in front of all our python services. It serves the static frontend files (React build) and routes API requests to the correct backend port. It handles CORS, SSL termination (in production), and load balancing.

**Q: Why separate the Interview Agent into its own service?**
**A:** The Interview agent might need to hold long-running connections or perform complex scheduling logic (simulated "thinking"). If this ran in the main Flask app, it could slow down simple requests like "Main Page Load". Separating it ensures the UI stays snappy.

**Q: What is "Agentic" about this system?**
**A:** Unlike a standard CRUD app, this system has components that "reason". The Orchestrator doesn't just run a script; it uses an LLM (Language Model) to look at data, make a decision (Accept/Reject), and **explain its reasoning** to the user. It has autonomy.
