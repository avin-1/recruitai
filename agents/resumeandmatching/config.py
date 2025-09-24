import os


# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESUMES_DIR = os.path.join(BASE_DIR, "resumes")
UTILS_DIR = os.path.join(BASE_DIR, "utils")

# Ensure folders exist
os.makedirs(RESUMES_DIR, exist_ok=True)


# Databases
SQLITE_PATH = os.path.join(BASE_DIR, "database.db")
SQLALCHEMY_URL = f"sqlite:///{SQLITE_PATH}"

# Models / Providers
SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai"

# External services
MONGODB_URI_ENV = "MONGODB_URI"
HF_TOKEN_ENV = "HF_TOKEN"

# Matching / thresholds
REJECTION_THRESHOLD = 70.0  # out of 100

# ChromaDB (optional)
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, ".chroma")

CONFIG = {
    "paths": {
        "base": BASE_DIR,
        "resumes": RESUMES_DIR,
        "sqlite": SQLITE_PATH,
        "chroma": CHROMA_PERSIST_DIR,
    },
    "db": {
        "sqlalchemy_url": SQLALCHEMY_URL,
    },
    "models": {
        "sbert": SENTENCE_TRANSFORMER_MODEL,
        "llm": LLM_MODEL,
    },
    "env": {
        "mongodb_uri_env": MONGODB_URI_ENV,
        "hf_token_env": HF_TOKEN_ENV,
    },
    "thresholds": {
        "rejection": REJECTION_THRESHOLD,
    },
}


