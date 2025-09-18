import os
import json
import time
import fitz  # PyMuPDF
from openai import OpenAI, RateLimitError
import re
from dotenv import load_dotenv
import sys

load_dotenv()

INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"
PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "promptsDB", "prompt.txt")
LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai"

HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    print("ERROR: HF_TOKEN environment variable not set.", file=sys.stderr)
    sys.exit(1)

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
    timeout=60.0
)

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# --- Helper Functions ---
def sanitize_filename(filename):
    filename = filename.replace(" ", "_")
    filename = re.sub(r'[^\w\-]', '', filename)
    return filename[:100]


def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "".join([page.get_text() for page in doc])
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}", file=sys.stderr)
        return None

def load_prompt():
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading prompt file: {e}", file=sys.stderr)
        return None

def parse_job_description_with_llm(text, prompt, retries=5):
    if not text or not prompt:
        return None
    full_prompt = f"{prompt}\n\n---\nJob Description:\n{text}\n---\nJSON Output:"
    delay = 1
    for attempt in range(retries):
        try:
            res = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": full_prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)
        except RateLimitError:
            print(f"Rate limit exceeded. Retrying in {delay} seconds...", file=sys.stderr)
            time.sleep(delay)
            delay *= 2
        except Exception as e:
            print(f"Error parsing LLM: {e}", file=sys.stderr)
            return None
    return None

def process_job_description(pdf_path):
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

    structured_profile = parse_job_description_with_llm(job_text, parsing_prompt)

    if structured_profile:

        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        out_file = os.path.join(OUTPUT_FOLDER, f"{base_name}.json")
        try:

            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(structured_profile, f, indent=4, ensure_ascii=False)
            print(f"✅ Successfully created structured job profile: {output_filename}")
            return output_filename

        except Exception as e:
            print(f"Error saving JSON file {out_file}: {e}", file=sys.stderr)
            return None
    else:

        print(f"❌ Failed to get structured profile from LLM for {pdf_path}.")
    return None


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python jdParsing.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        sys.exit(1)

    output_file = process_job_description(pdf_path)
    if output_file:
        print(output_file)
        sys.exit(0)
    else:
        sys.exit(1)

