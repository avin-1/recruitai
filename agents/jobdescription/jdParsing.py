import os
import json
import time
import fitz  # PyMuPDF
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI, RateLimitError
import re
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
PROMPT_FILE = os.path.join("promptsDB", "prompt.txt")
LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai"

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("ERROR: HF_TOKEN environment variable not set. Please set it before running the script.")
    exit(1)

# Initialize OpenAI client for Hugging Face router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
    timeout=60.0
)

# --- Setup Directories ---
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
print(f"Watching for new PDF job descriptions in: '{INPUT_FOLDER}/'")
print(f"Output JSON profiles will be saved to: '{OUTPUT_FOLDER}/'")

# --- Helper Functions ---
def sanitize_filename(filename):
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^\w\-]', '', filename)
    return filename[:100]

def wait_for_file_completion(filepath, timeout=10, interval=0.5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(filepath, 'rb') as f:
                f.seek(0, os.SEEK_END)
            return True
        except IOError:
            time.sleep(interval)
        except Exception as e:
            print(f"Unexpected error while waiting for file {filepath}: {e}")
            return False
    print(f"Timeout reached while waiting for file {filepath} to be written.")
    return False

def extract_text_from_pdf(pdf_path):
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
    """Reads the parsing prompt from prompt.txt"""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading prompt file {PROMPT_FILE}: {e}")
        return None

def parse_job_description_with_llm(job_description_text, parsing_prompt, max_retries=5, initial_delay=1):
    if not job_description_text or not parsing_prompt:
        return None

    # Insert job text inside prompt
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

# --- Watchdog Event Handler ---
class JobDescriptionHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".pdf"):
            print(f"New PDF detected: {event.src_path}")
            time.sleep(0.1)
            process_job_description(event.src_path)
        else:
            print(f"Ignored non-PDF file: {event.src_path}")

def process_job_description(pdf_path):
    print(f"Waiting for file {pdf_path} to be fully written...")
    if not wait_for_file_completion(pdf_path):
        print(f"Skipping {pdf_path} as it could not be accessed after waiting.")
        return

    print(f"Extracting text from {pdf_path}...")
    job_text = extract_text_from_pdf(pdf_path)
    if not job_text:
        print(f"Could not extract text from {pdf_path}. Skipping.")
        return

    print("Loading parsing prompt...")
    parsing_prompt = load_prompt()
    if not parsing_prompt:
        print("No parsing prompt available. Skipping.")
        return

    print("Sending text to LLM for parsing...")
    structured_profile = parse_job_description_with_llm(job_text, parsing_prompt)

    if structured_profile:
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_filename = os.path.join(OUTPUT_FOLDER, f"{base_name}.json")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(structured_profile, f, indent=4, ensure_ascii=False)
            print(f"✅ Successfully created structured job profile: {output_filename}")
        except Exception as e:
            print(f"Error saving JSON file {output_filename}: {e}")
    else:
        print(f"❌ Failed to get structured profile from LLM for {pdf_path}.")

# --- Main Execution ---
if __name__ == "__main__":
    event_handler = JobDescriptionHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Job parsing agent stopped.")
    observer.join()
