import os
import json
import time
import fitz  # PyMuPDF
from openai import OpenAI, RateLimitError
import re
from dotenv import load_dotenv

load_dotenv()

# This file is now a utility module. The core logic has been moved to graph.py
# The watchdog and main execution logic has been removed.

# --- Configuration ---
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
PROMPT_FILE = os.path.join("promptsDB", "prompt.txt")
LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai"

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("ERROR: HF_TOKEN environment variable not set.")
    # This check is kept in case any function is tested standalone.

# Initialize OpenAI client for Hugging Face router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
    timeout=60.0
)

# --- Helper Functions (callable by other modules) ---
def sanitize_filename(filename):
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^\w\-]', '', filename)
    return filename[:100]

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    Note: This function is now called from graph.py
    """
    text = ""
    try:
        document = fitz.open(pdf_path)
        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text += page.get_text()
        document.close()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        return None

def load_prompt():
    """
    Reads the parsing prompt from prompt.txt
    Note: This function is now called from graph.py
    """
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading prompt file {PROMPT_FILE}: {e}")
        return None

def parse_job_description_with_llm(job_description_text, parsing_prompt, max_retries=5, initial_delay=1):
    """
    Parses a job description using an LLM.
    Note: This function is now called from graph.py
    """
    if not job_description_text or not parsing_prompt:
        return None

    prompt = f"""{parsing_prompt}

---
Job Description:
{job_description_text}
---

JSON Output:"""

    retries = 0
    delay = initial_delay
    while retries < max_retries:
        try:
            chat_completion = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            llm_response_content = chat_completion.choices[0].message.content
            return json.loads(llm_response_content)
        except RateLimitError:
            retries += 1
            print(f"Rate limit exceeded. Retrying in {delay} seconds (Attempt {retries}/{max_retries})...")
            time.sleep(delay)
            delay *= 2
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from LLM response: {e}")
            print(f"LLM Response was: {llm_response_content}")
            return None
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None
    print(f"Failed to get LLM response after {max_retries} retries due to rate limits.")
    return None
