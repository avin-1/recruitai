# System Architecture Study Guide (Deep Dive)

## 1. High-Level Overview

**Architecture Style:** Hybrid Monolith + Microservices

Our system adopts a **Hybrid Architecture** that blends the simplicity of a Monolith with the scalability of Microservices. At its core, we have a centralized **Flask Backend** (running on port 8080) that handles all user-facing interactions, such as file uploads, authentication placeholders, and data retrieval. This ensures that the core business logic remains tightly coupled and easy to debug.

Surrounding this core are specialized **Microservices** (Agents) running on separate ports (5001, 5002). These agents are responsible for computationally intensive or long-running tasks, such as conducting AI interviews or analyzing code complexity. By offloading these tasks, we ensure that the main user interface remains snappy and responsive, even when the system is under heavy load processing complex AI reasoning.

### Why this architecture?
We chose this "Hybrid" approach to balance **Speed of Development** with **Scalability**. A pure monolith would have been easier to start with, but it would have struggled as we added more complex AI features. A pure microservices architecture would have introduced too much complexity (service discovery, distributed tracing) for a team of our size. This middle ground gives us the best of both worlds: the ease of a single codebase for the main app, and the freedom to write specialized, independent agents for the AI logic.

## 2. The Life of a Candidate (Data Flow Narrative)

To understand how the system works, let's follow the journey of a single piece of data—a Candidate Application—through the entire system.

### Step 1: The Job Description (The Spark)
Everything begins when a Recruiter uploads a Job Description (JD) PDF via the Frontend. This file is sent to the **Upload API**, which saves it to a watched folder (`agents/jobdescription/input`). The **Job Description Agent**, running efficiently in the background, detects this new file. It wakes up, uses an LLM to "read" the PDF, and extracts structured data like "Job Title," "Required Skills," and "Company Name." This structured JSON is then written to our **MongoDB** database, making the job "live" and searchable.

### Step 2: The Application (The Match)
A candidate visits the Job Portal and uploads their resume. The Frontend pushes this file to the Backend. Instantly, the **Resume & Matching Agent** (embedded in the backend for speed) is triggered. It doesn't just look for keywords; it performs a **Semantic Search** using vector embeddings to understand the *meaning* of the resume. Simultaneously, sends the resume to an LLM to get a qualitative score (0-100). If the score crosses our threshold (e.g., 50%), the application is accepted and saved to the database. This happens in milliseconds, giving the user instant feedback.

### Step 3: The Shortlist (The Decision)
Accepted candidates are invited to take a technical test. When they complete it, the **Shortlisting Agent** (:5001) swings into action. It queries the **Codeforces API** to verify their coding performance, ensuring they didn't just guess the answers. It combines this hard data with an LLM analysis of their code style. If the candidate proves their competence, the agent updates their status to `SHORTLISTED` in the database.

### Step 4: The Interview (The Closing)
Finally, the **Interview Scheduler Agent** (:5002) polls the database for these shortlisted candidates. It acts like a human assistant, checking the HR manager's **Google Calendar** for free slots. It uses an optimization algorithm to find times that maximize availability. once a slot is found, it automatically sends an email invite with a generated **Google Meet** link and creates a calendar event.

## 3. System Diagram (Conceptual)

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

## 4. Integration Points & Communication

- **Frontend <-> Backend:** All communication happens via **REST APIs** using JSON. The Frontend uses **Axios** to send asynchronous requests, meaning the UI never freezes while waiting for the server. **Nginx** acts as the traffic cop, routing requests starting with `/api` to the backend and serving the React app for everything else.

- **Backend <-> Database:** **MongoDB** is our single source of truth. We use the "Shared Database" pattern, where multiple services (Core, Interview, Shortlist) all talk to the same DB. While purists might argue for "Database per Service," our shared approach drastically simplifies reporting and data consistency for this scale of project.

## 5. Technology Trade-offs (Why we chose X vs Y)

### Hybrid vs. Pure Microservices
- **The Choice:** We have separate processes but a **Shared Database**.
- **Alternative:** "Database per Service" (Pure Microservices).
- **Why Hybrid?** Managing Distributed Transactions (e.g., "Rollback the Application if the Interview fails") is extremely hard in pure microservices. With a shared Mongo, we get the speed of microservices but the data simplicity of a monolith.

### Polling vs. WebSockets (for Notifications)
- **The Choice:** Frontend polls `/api/notifications` every X seconds.
- **Alternative:** WebSockets (Socket.io).
- **Why Polling?** WebSockets require a persistent stateful connection server, which is hard to scale and deploy on some serverless platforms. Polling is "dumb but robust" and easier to implement for a prototype.

### Docker Compose vs. Kubernetes
- **The Choice:** Docker Compose.
- **Why?** Kubernetes is an orchestration beast intended for Google-scale. For a team project with <10 services, Docker Compose provides 80% of the value (Containerization, Networking) with 10% of the complexity.

## 6. Exam Q&A Preparation

**Q: Why use MongoDB instead of SQL (PostgreSQL)?**
**A:** Recruitment data is highly unstructured. Resumes come in different formats, and job descriptions vary wildly. A NoSQL document store (JSON-like) allows us to store arbitrary data without complex migrations every time we add a field like "Github URL" or "Portfolio".

**Q: What is the role of Nginx?**
**A:** It acts as a **Reverse Proxy**. It sits in front of all our python services. It serves the static frontend files (React build) and routes API requests to the correct backend port. It handles CORS, SSL termination (in production), and load balancing.

**Q: Why separate the Interview Agent into its own service?**
**A:** The Interview agent might need to hold long-running connections or perform complex scheduling logic (simulated "thinking"). If this ran in the main Flask app, it could slow down simple requests like "Main Page Load". Separating it ensures the UI stays snappy.
