# Agents Study Guide (Overview)

## The "Brains" of the Operation

This system uses four distinct AI Agents to automate the recruitment lifecycle. We have broken down the deep technical details into separate study files for each agent.

Please review the following deep dive documents:

### 1. [The Resume & Matching Agent](agent_resume_matching.md)
* **Role:** The Analyst.
* **Key Concept:** **Hybrid Scoring**.
* **What to study:** How we combine Vector Math (Cosine Similarity) with LLM reasoning to get a fair score.
* **Why important:** This is the core "AI" feature that filters candidates.

### 2. [The Shortlisting Agent](agent_shortlisting.md)
* **Role:** The Verifier.
* **Key Concept:** **Proof of Work**.
* **What to study:** How we integrate with the **Codeforces API** to prove a candidate can actually code, rather than just trusting their resume.
* **Why important:** It demonstrates integration with external 3rd party APIs for validation.

### 3. [The Interview Scheduler Agent](agent_interview_scheduler.md)
* **Role:** The Assistant.
* **Key Concept:** **Constraint Satisfaction**.
* **What to study:** The algorithm that finds "Free Slots" in a calendar and how **Google OAuth** works.
* **Why important:** It shows how we handle "Real World" constraints like time and availability.

### 4. [The Job Description Parser](agent_job_description.md)
* **Role:** The Librarian.
* **Key Concept:** **Event-Driven Architecture**.
* **What to study:** How we use `watchdog` to monitor files and **Exponential Backoff** to handle API failures gracefully.
* **Why important:** It explains how data enters the system from the outside world.

---

## Common Architecture Patterns

While each agent is unique, they share a few patterns:

### A. The "Prompt Engineering" Standard
Every agent follows a strict prompting structure:
1.  **Persona:** "You are an expert X..."
2.  **Context:** "Here is the data..."
3.  **Constraint:** "Output JSON only."
*Why?* This ensures the LLM behaves like a function, not a chatbot.

### B. The "Fallback" Safety Net
All agents are designed to not crash the main app.
- If **OpenAI** fails, the Resume Agent falls back to Keyword matching.
- If **Codeforces** fails, the Shortlisting Agent reports a timeout error gracefully.
- If **Google Calendar** fails, the Interview Agent retries later.

*For the exam, focus on `agent_resume_matching.md` and `agent_system_architecture.md` first, as they are the most technically complex.*
