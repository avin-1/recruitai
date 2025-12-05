# Agent Deep Dive: Shortlisting Agent

To understand the robustness of the system, we must examine the data it relies on. The Codeforces API returns a complex JSON array containing every submission a user has ever made.

**The API Response anatomy:**
The agent parses a payload where each object represents a submission event. Crucial fields include `creationTimeSeconds` (used for the time window check), `problem.name` (to match against the required test questions), and most importantly, `verdict`. The agent strictly requires the `verdict` to be `"OK"`. Any other status, such as `"WRONG_ANSWER"` or `"compilation error"`, is immediately discarded. This strict strictness is hard-coded into the logic to ensure fair standards.

**The Algorithm Trace:**
Imagine a candidate named Alice. The system defines a test window from 10:00 AM to 12:00 PM and requires her to solve "Two Sum" and "Graph BFS". The agent fetches her 50 most recent submissions. It discards 45 of them because their `creationTimeSeconds` timestamp is older than 10:00 AM. Of the remaining 5, it checks the problem names. It sees she attempted "Two Sum" twice: once failing, and once succeeding. It counts the success. It sees she solved "Graph BFS" on the first try. With 2 successful matches found, the logic evaluation `if solved >= required` evaluates to True, and Alice is automatically updated to `SHORTLISTED` status in the MongoDB database.

## 4. Engineering Reliability and Security

The Shortlisting Agent is designed with specific security considerations to protect the integrity of the recruitment process.

**API Rate Limiting:**
External APIs like Codeforces implement strict rate limits to prevent abuse. Our agent respects this by implementing a courtesy delay (`time.sleep(0.5)`) between requests. In a high-volume production environment, this synchronous delay would be replaced by a distributed queue with rate-limited workers to ensure we never get blocked by the provider.

**Remote Code Execution (RCE) mitigation:**
When analyzing raw code submitted by candidates, there is a risk of "Code Injection"—where a malicious user tries to execute system commands via the Python interpreter. We mitigate this risk by **never executing** the code. We treat the candidate's code strictly as text data, passing it only to the LLM for analysis. We do not run `exec()` or `eval()`, effectively neutralizing any attempt to harm the host system.

## 5. Advanced Topics and Defense Questions

**Identity Verification Risks:**
A common critique of remote testing is identity fraud: "Can't I just share my Codeforces account with a friend?" The honest engineering answer is "Yes, currently." Our system verifies that the *account* solved the problem, not who was typing. Solving this fully would require proctoring (webcam verification) or a "Challenge Question" phase during the interview. We mitigate it partially by requiring the solution to occur strictly during the short test window, making it harder to coordinate with a proxy.

**Dependency Risks:**
The system is tightly coupled to the Codeforces API structure. If Codeforces were to change their JSON schema (e.g., renaming `verdict` to `status`), our agent would fail. In software engineering terms, this is a **Rigid Coupling**. Ideally, we would implement an **Adapter Pattern**—a wrapper class that standardizes the external data into our internal format. This way, if the API changes, we only need to update the single Adapter file, rather than rewriting the core agent logic.
