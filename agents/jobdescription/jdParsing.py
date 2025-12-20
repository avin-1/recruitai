import os
import json
import time
import fitz  # PyMuPDF
from openai import OpenAI, RateLimitError
import re
from dotenv import load_dotenv
from typing import Optional, Dict

load_dotenv()

PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "promptsDB", "prompt.txt")
LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai"

# Add path to import PromptManager
# Add path to import PromptManager
import sys
try:
    # Add root directory to path to import backend
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from backend.prompt_manager import PromptManager
except ImportError as e:
    print(f"Failed to import PromptManager: {e}")
    PromptManager = None


# --- Helper Functions ---
def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    try:
        doc = fitz.open(pdf_path)
        text = "".join([page.get_text() for page in doc])
        doc.close()
        return text
    except Exception as exc:
        print(f"Error extracting text from {pdf_path}: {exc}")
        return None


def load_prompt() -> Optional[str]:
    """Load the prompt from PromptManager or file."""
    # Try PromptManager first
    if PromptManager:
        try:
            pm = PromptManager()
            # Fix: Add prompt_type argument
            prompt = pm.get_prompt("Job Description Agent", "parsing")
            if prompt:
                return prompt
        except Exception as e:
            print(f"Error loading from PromptManager: {e}")

    # Fallback to file
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            # If the file has metadata, extract only the prompt content part
            if "Prompt Content:" in content:
                # Extract content after "Prompt Content:"
                parts = content.split("Prompt Content:", 1)
                if len(parts) > 1:
                    return parts[1].strip()
            return content
    except Exception as exc:
        print(f"Error reading prompt file: {exc}")
        return None


def _get_openai_client() -> OpenAI:
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN environment variable not set")
    return OpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=hf_token,
        timeout=60.0,
    )


def _parse_with_llm(text: str, prompt: str, retries: int = 5) -> Optional[Dict]:
    if not text or not prompt:
        return None
    client = _get_openai_client()
    # Replace placeholder if it exists, otherwise append the text
    if "{job_description_text}" in prompt:
        full_prompt = prompt.replace("{job_description_text}", text)
    else:
        full_prompt = f"{prompt}\n\n---\nJob Description:\n{text}\n---\nJSON Output:"
    delay_seconds = 1
    for _ in range(retries):
        try:
            res = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": full_prompt},
                ],
                response_format={"type": "json_object"},
            )
            return json.loads(res.choices[0].message.content)
        except RateLimitError:
            time.sleep(delay_seconds)
            delay_seconds *= 2
        except Exception as exc:
            print(f"Error parsing LLM: {exc}")
            return None
    return None


def parse_job_description(file_path: str) -> Dict:
    """Return parsed job profile as dict ready to insert/update in MongoDB.

    This function performs PDF text extraction, loads the parsing prompt,
    calls the LLM, and returns the structured profile dictionary.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    job_text = extract_text_from_pdf(file_path)
    if not job_text:
        raise ValueError("Failed to extract text from PDF")

    parsing_prompt = load_prompt()
    if not parsing_prompt:
        raise RuntimeError("Parsing prompt not available")

    structured_profile = _parse_with_llm(job_text, parsing_prompt)
    if not structured_profile:
        raise RuntimeError("Failed to obtain structured profile from LLM")

    return structured_profile


def parse_job_description_from_text(job_description_text: str) -> Dict:
    """Return parsed job profile as dict from text input (not a file).
    
    This function loads the parsing prompt, calls the LLM with the provided text,
    and returns the structured profile dictionary.
    """
    if not job_description_text or not job_description_text.strip():
        raise ValueError("Job description text cannot be empty")

    parsing_prompt = load_prompt()
    if not parsing_prompt:
        raise RuntimeError("Parsing prompt not available")

    structured_profile = _parse_with_llm(job_description_text.strip(), parsing_prompt)
    if not structured_profile:
        raise RuntimeError("Failed to obtain structured profile from LLM")

    return structured_profile

