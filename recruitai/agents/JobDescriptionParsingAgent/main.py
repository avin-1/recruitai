import os
import json
import time
import fitz # PyMuPDF
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from openai import OpenAI, RateLimitError # Import RateLimitError
import re # For sanitizing filenames
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai" # Example LLM model for Hugging Face router
# Ensure your Hugging Face token is set as an environment variable
# export HF_TOKEN="your_huggingface_token_here"
HF_TOKEN = os.environ.get("HF_TOKEN")

if not HF_TOKEN:
    print("ERROR: HF_TOKEN environment variable not set. Please set it before running the script.")
    exit(1)

# Initialize the OpenAI client for the Hugging Face router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
    timeout=60.0 # Add a timeout for API calls to prevent indefinite waits
)

# --- Setup Directories ---
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
print(f"Watching for new PDF job descriptions in: '{INPUT_FOLDER}/'")
print(f"Output JSON profiles will be saved to: '{OUTPUT_FOLDER}/'")

# --- Helper Functions ---
def sanitize_filename(filename):
    """
    Sanitizes a string to be used as a filename by removing invalid characters.
    """
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Remove any characters that are not alphanumeric, underscores, or hyphens
    filename = re.sub(r'[^\w\-]', '', filename)
    # Trim to a reasonable length to avoid OS limits
    return filename[:100]

def wait_for_file_completion(filepath, timeout=10, interval=0.5):
    """
    Waits for a file to be completely written by repeatedly trying to open it.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(filepath, 'rb') as f:
                # If we can open it, seek to end, and it doesn't raise an error,
                # it's likely complete enough to read.
                f.seek(0, os.SEEK_END)
            return True
        except IOError:
            # File is still being written or is locked
            time.sleep(interval)
        except Exception as e:
            print(f"Unexpected error while waiting for file {filepath}: {e}")
            return False
    print(f"Timeout reached while waiting for file {filepath} to be written.")
    return False

def extract_text_from_pdf(pdf_path):
    """
    Extracts text content from a PDF file using PyMuPDF.
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

def parse_job_description_with_llm(job_description_text, max_retries=5, initial_delay=1):
    """
    Sends the job description text to the LLM to extract structured information,
    with exponential backoff for rate limit errors.
    """
    if not job_description_text:
        return None

    prompt = f"""
    You are an expert job parsing agent. Your task is to extract key information from the following job description and return it as a structured JSON object.

    Extract the following fields:
    - **job_title**: The official title of the job.
    - **company**: The name of the hiring company.
    - **location**: The primary location of the job (e.g., city, country).
    - **responsibilities**: A list of key responsibilities.
    - **required_skills**: A list of essential skills or technologies.
    - **experience_level**: The required years of experience or a general level (e.g., "5+ years", "Entry-level").
    - **educational_requirements**: The minimum educational qualifications (e.g., "Bachelor's degree in Computer Science").

    If a field is not explicitly found, use `null` for its value.
    The output MUST be a valid JSON object.

    ---
    Job Description:
    {job_description_text}
    ---

    JSON Output:
    """

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
            delay *= 2 # Exponential increase
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
        if event.src_path.lower().endswith(".pdf"): # Case-insensitive check
            print(f"New PDF detected: {event.src_path}")
            # Add a small initial delay to allow the file system to settle
            time.sleep(0.1)
            process_job_description(event.src_path)
        else:
            print(f"Ignored non-PDF file: {event.src_path}")

def process_job_description(pdf_path):
    """
    Handles the end-to-end processing of a new job description PDF.
    """
    # Wait for the file to be fully written before processing
    print(f"Waiting for file {pdf_path} to be fully written...")
    if not wait_for_file_completion(pdf_path):
        print(f"Skipping {pdf_path} as it could not be accessed after waiting.")
        return

    # 1. Extract text from PDF
    print(f"Extracting text from {pdf_path}...")
    job_text = extract_text_from_pdf(pdf_path)
    if not job_text:
        print(f"Could not extract text from {pdf_path}. Skipping.")
        return

    # 2. Parse with LLM
    print(f"Sending text to LLM for parsing...")
    structured_profile = parse_job_description_with_llm(job_text)

    if structured_profile:
        # 3. Determine output filename based on job title or original filename
        output_base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        if 'job_title' in structured_profile and structured_profile['job_title']:
            sanitized_job_title = sanitize_filename(structured_profile['job_title'])
            final_filename = f"{sanitized_job_title}.json"
        else:
            print(f"Job title not found in LLM output for {pdf_path}. Using original filename base.")
            final_filename = f"{output_base_name}_profile.json"

        output_filename = os.path.join(
            OUTPUT_FOLDER,
            final_filename
        )
        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(structured_profile, f, indent=4, ensure_ascii=False)
            print(f"Successfully created structured job profile: {output_filename}")
        except Exception as e:
            print(f"Error saving JSON file {output_filename}: {e}")
    else:
        print(f"Failed to get structured profile from LLM for {pdf_path}.")

# --- Main Execution ---
if __name__ == "__main__":
    event_handler = JobDescriptionHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1) # Keep the observer running
    except KeyboardInterrupt:
        observer.stop()
        print("Job parsing agent stopped.")
    observer.join()
