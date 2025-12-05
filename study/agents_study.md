# Agents Study Guide

## 1. Overview of Agents
Unlike a standard app, our logic is distributed among "Agents". An agent is a piece of software that can:
1. **Perceive** (Read data/Events)
2. **Reason** (Decide what to do, often using LLM)
3. **Act** (Execute the decision)
4. **Explain** (Tell the user WHY)

## 2. Agent Breakdown

### A. Resume & Matching Agent
- **Location:** Embedded in Backend (`agents/resumeandmatching` library calls).
- **Trigger:** When a user uploads a resume.
- **Goal:** Assign a 0-100 score to the candidate.
- **Logic Flow:**
    1. **Parsing:** Extract text from PDF (using `PyMuPDF` or `fitz`).
    2. **Keyword Match:** Simple set intersection (Resume Words ∩ Job Words).
    3. **LLM Scoring (Advanced):** Sends both texts to an LLM (e.g., GPT/Llama) with a prompt: "Rate this candidate from 0-100 based on this JD."
    4. **Decision:** If Score > Threshold (e.g., 50%) -> ACCEPT, else REJECT.

### B. Shortlisting Agent
- **Location:** Microservice (Port 5001).
- **Trigger:** After a candidate completes a test (simulated).
- **Goal:** Decide if an accepted candidate should be interviewed.
- **Logic Flow:**
    1. Listen for "Test Completed" event.
    2. Analyze Codeforces/Test results.
    3. Calculate `completion_rate`.
    4. **Reasoning:** "Candidate solved 8/10 problems including the Hard one."
    5. Action: Update status to `SHORTLISTED`.

### C. Interview Scheduler Agent
- **Location:** Microservice (Port 5002).
- **Trigger:** When a candidate is Shortlisted.
- **Goal:** Find a time slot where both HR and Candidate are free.
- **Logic Flow:**
    1. Fetch HR Calendar (simulated availability).
    2. **Optimization:** Find slots that don't overlap with existing meetings.
    3. **Preference:** "Prefer Morning slots".
    4. Action: Create a "Tentative" calendar event.

### D. Job Description (JD) Agent
- **Location:** Background Worker (`agents/jobdescription`).
- **Trigger:** When a recruiter uploads a raw PDF JD.
- **Goal:** Convert "Messy PDF" -> "Structured JSON".
- **Logic Flow:**
    1. Watch input folder.
    2. Parse PDF.
    3. **Extraction:** Identify "Job Title", "Skills", "Company" from the blob of text.
    4. Save to MongoDB (`json_files` collection).

## 3. "Why This Approach?" (Exam Q&A)

**Q: Why are some agents Microservices and others embedded?**
**A:**
- **Resume Matching** is embedded because it needs to happen *immediately* when the user clicks upload. We want fast feedback.
- **Interview Scheduling** is a Microservice because it's a long, complex process that happens asynchronously. It doesn't need to block the user's screen.

**Q: How do Agents "Reason"?**
**A:** They use the `reason()` function (seen in `agent_orchestrator.py`).
- It constructs a prompt: *"Context: Candidate scored 80. Task: Shortlist? Response:"*
- The LLM replies with natural language: *"Yes, strong score."*
- We save this textual reasoning to the database so the UI can display it. This is **Explainable AI (XAI)**.

**Q: What is LangGraph?**
**A:** We use LangGraph (in `agent_orchestrator.py`) to define the agent's "Flowchart" as code.
- Nodes = Steps (Analyze, Decide, Act).
- Edges = Transitions.
- It makes the agent's behavior deterministic and visualizable, preventing it from looping forever.
