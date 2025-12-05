# Backend Study Guide (Deep Dive)

## 1. Tech Stack Narrative

Our backend is the powerhouse of the application, built using **Python** and **Flask**. We chose Python because it is the "Lingua Franca" of Artificial Intelligence. Since our system relies heavily on AI/ML libraries like PyTorch and Transformers, using Python for the API ensures that our web layer and our logic layer speak the same language, avoiding the complexity of a "Polyglot" system.

**Flask** was chosen over Django for its simplicity. Django is a "Battery-included" framework that forces a specific structure and comes with a heavy ORM. Flask, being a "Micro-framework," stays out of our way. It allows us to structure our Agents and Services exactly how we want, making it perfect for our custom Hybrid Architecture. For the database, we use **MongoDB** (via PyMongo). This choice is crucial because recruitment data is highly unstructured—one candidate might have a Github link, another a Portfolio, another a list of Patents. A rigid SQL schema would be a nightmare to maintain here, whereas MongoDB's flexible documents adapt naturally to this variance.

## 2. The Story of an API Request (`upload_api.py`)

Let's look at what happens when a user hits the `/upload` endpoint. This isn't just a simple file save; it's a carefully orchestrated sequence.

1.  **Validation:** First, the endpoint checks if the request actually contains a file. It uses `secure_filename` to sanitize the input name, preventing malicious users from trying to overwrite critical system files by naming their upload `../../system.conf`.
2.  **Storage:** The file is saved to a specific "Input" folder watched by our agents.
3.  **Trigger:** By saving the file, we implicitly trigger the **Job Description Agent**, which is watching that folder. This is an "Event-Driven" pattern—the API doesn't call the Agent; the data change *is* the call.

This same pattern repeats throughout the system. The API handles the "User Input/Output" (Synchronous), and the Agents handle the "Thinking" (Asynchronous), linked together by the Data.

## 3. Core Services Deep Dive

### The Email Service
The `EmailService` is a dedicated module for communication. It doesn't just "fire and forget" emails; it maintains a local **SQLite** database to track the state of every message. When we select candidates for an interview, the service iterates through them, constructs a personalized email using an HTML template, sends it via SMTP, and *then* records the success. This ensures that if the server crashes halfway through, we know exactly who got the email and who didn't.

### The Social Media Service
Our `Social Media Service` allows HR to act as marketers. When a Job Profile is approved, this service can push a beautifully formatted post to **Instagram**. It uses the **Facebook Graph API**. The flow is two-step: first, we create a "Media Container" hosting the image, and then we "Publish" that container. It uses the `httpx` library, which is modern and supports async operations, future-proofing the service for high-volume posting.

## 4. Security & Authentication

Currently, our prototype uses a trusted internal model. However, in a production environment, this would be a major vulnerability. We would implement **JWT (JSON Web Tokens)**. The flow would be: User Logs In -> Server generates a signed Token -> User sends this Token in the Header of every request. The Backend would then Decode and Verify this token before allowing any action, ensuring that only specialized "HR Admin" accounts could approve jobs or schedule interviews.

## 5. Technology Trade-offs (Why we chose X vs Y)

### Flask vs. Django
- **Why Flask?** Django comes with a heavy ORM, Admin Panel, and strict directory structure. It's great for blogs, but bloat for an AI API.
- **Benefit:** Flask is "Micro". It gets out of the way. We can structure our agents however we want without fighting the framework.

### MongoDB vs. SQL (PostgreSQL)
- **Why NoSQL?** Job Descriptions and Resumes are highly variable. One resume has "Github", another has "Portfolio", another has "Patents".
- **Benefit:** In SQL, we'd need a table with 50 columns mostly NULL. In MongoDB, we just store the JSON document as-is. It matches our data naturally.

### Python vs. Node.js (for Backend)
- **Why Python?** Logic. If the AI/ML libraries (PyTorch, Transformers, LangChain) are in Python, the API should be too.
- **Benefit:** Avoids the complexity of a "Polyglot" repo (e.g., Node.js Backend calling Python scripts via shell commands). Everything runs in the same process/language.

## 6. Exam Q&A Preparation

**Q: What is the purpose of `wsgi.py` or Waitress?**
**A:** Flask's `app.run()` is single-threaded and not secure for the internet. A WSGI server (like Waitress or Gunicorn) sits between Nginx and Flask to handle concurrency and buffering.

**Q: Explain Vector Database (ChromaDB) usage.**
**A:** Standard databases search for **KEYWORDS** (e.g., "Python"). Vector databases search for **MEANING**. "I know coding" ≈ "I am a developer" (High semantic similarity). A keyword search would miss this. A Vector DB catches it by converting text into high-dimensional geometric vectors (embeddings).
