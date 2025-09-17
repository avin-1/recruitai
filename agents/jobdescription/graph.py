# This file will contain the LangGraph orchestration logic.
import os
import json
import fitz  # PyMuPDF
from pymongo import MongoClient
from openai import OpenAI
from dotenv import load_dotenv
from typing import TypedDict, List

# Load environment variables
load_dotenv()

# --- Configuration ---
MONGO_URI = os.getenv("MONGODB_URI")
HF_TOKEN = os.getenv("HF_TOKEN")
LLM_MODEL = "openai/gpt-oss-20b:fireworks-ai"

# --- Error Handling ---
if not MONGO_URI:
    raise ValueError("MONGODB_URI not found in .env")
if not HF_TOKEN:
    print("ERROR: HF_TOKEN environment variable not set.")
    # In a real app, you might want to exit or handle this more gracefully
    # For now, we'll let it proceed but expect errors later.

# --- MongoDB Setup ---
profiles_client = MongoClient(MONGO_URI)
profiles_db = profiles_client["profiles"]
profiles_collection = profiles_db["json_files"]

prompts_client = MongoClient(MONGO_URI)
prompts_db = prompts_client["prompt_db"]
prompts_collection = prompts_db["prompts"]

# --- OpenAI Client for Hugging Face ---
llm_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
    timeout=60.0
)

# --- Core Functions (adapted from existing scripts) ---

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a given PDF file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    try:
        document = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in document)
        document.close()
        print(f"✅ Successfully extracted text from {os.path.basename(pdf_path)}.")
        return text
    except Exception as e:
        print(f"❌ Error extracting text from PDF {pdf_path}: {e}")
        raise

def get_prompt_from_db(prompt_id: str = "job_parser_v1") -> str:
    """Retrieves a prompt content from the MongoDB prompts collection."""
    try:
        prompt_doc = prompts_collection.find_one({"id": prompt_id})
        if prompt_doc and "content" in prompt_doc:
            print(f"✅ Successfully retrieved prompt '{prompt_id}' from MongoDB.")
            return prompt_doc["content"]
        else:
            raise ValueError(f"Prompt with id '{prompt_id}' not found or has no content.")
    except Exception as e:
        print(f"❌ Error retrieving prompt from MongoDB: {e}")
        raise

def parse_job_description_with_llm(job_text: str, prompt_template: str) -> dict:
    """Parses job description text using an LLM and a prompt template."""
    if not job_text or not prompt_template:
        raise ValueError("Job text and prompt template cannot be empty.")

    prompt = prompt_template.format(job_description_text=job_text)

    try:
        print("🤖 Sending job description to LLM for parsing...")
        chat_completion = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        response_content = chat_completion.choices[0].message.content
        print("✅ Successfully received response from LLM.")
        return json.loads(response_content)
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON from LLM response: {e}")
        print(f"LLM Response was: {response_content}")
        raise
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        raise

def store_profile_in_db(profile_data: dict) -> dict:
    """Stores the parsed job profile JSON into the MongoDB profiles collection."""
    if not profile_data:
        raise ValueError("Profile data cannot be empty.")

    try:
        # Add the 'approved' field, defaulting to False
        profile_data['approved'] = False
        result = profiles_collection.insert_one(profile_data)
        print(f"✅ Successfully stored profile in MongoDB with ID: {result.inserted_id}")
        # Return the original data, perhaps with the new ID for logging
        profile_data['_id'] = str(result.inserted_id)
        return profile_data
    except Exception as e:
        print(f"❌ Error storing profile in MongoDB: {e}")
        raise

# --- LangGraph State Definition ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        filepath: The path to the PDF file.
        job_text: The extracted text from the PDF.
        prompt: The prompt template fetched from the database.
        json_profile: The parsed JSON profile from the LLM.
        db_id: The ID of the document inserted into the database.
    """
    filepath: str
    job_text: str
    prompt: str
    json_profile: dict
    db_id: str

# --- LangGraph Node Functions ---

def node_extract_text(state: GraphState) -> GraphState:
    """Node to extract text from the PDF."""
    print("--- Starting Node: Extract Text ---")
    filepath = state['filepath']
    job_text = extract_text_from_pdf(filepath)
    return {"job_text": job_text}

def node_get_prompt(state: GraphState) -> GraphState:
    """Node to get the prompt from the database."""
    print("--- Starting Node: Get Prompt ---")
    prompt = get_prompt_from_db()
    return {"prompt": prompt}

def node_parse_profile(state: GraphState) -> GraphState:
    """Node to parse the job description using the LLM."""
    print("--- Starting Node: Parse Profile ---")
    job_text = state['job_text']
    prompt = state['prompt']
    json_profile = parse_job_description_with_llm(job_text, prompt)
    return {"json_profile": json_profile}

def node_store_profile(state: GraphState) -> GraphState:
    """Node to store the parsed profile in the database."""
    print("--- Starting Node: Store Profile ---")
    json_profile = state['json_profile']
    stored_profile = store_profile_in_db(json_profile)
    return {"db_id": stored_profile['_id']}

# --- LangGraph Workflow Definition ---
from langgraph.graph import StateGraph, END

# Create a new graph
workflow = StateGraph(GraphState)

# Add nodes to the graph
workflow.add_node("extract_text", node_extract_text)
workflow.add_node("get_prompt", node_get_prompt)
workflow.add_node("parse_profile", node_parse_profile)
workflow.add_node("store_profile", node_store_profile)

# Set the entry point
workflow.set_entry_point("extract_text")

# Add edges to define the flow
workflow.add_edge("extract_text", "get_prompt")
workflow.add_edge("get_prompt", "parse_profile")
workflow.add_edge("parse_profile", "store_profile")
workflow.add_edge("store_profile", END)

# Compile the graph into a runnable app
app = workflow.compile()

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    # This is for testing the graph directly.
    # You would need a sample file in the correct input directory.
    # Construct path relative to the script's location
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INPUT_DIR = os.path.join(BASE_DIR, "input")
    sample_file = "Sample-Full-Time-Job-Description.pdf" # Make sure this file exists
    sample_filepath = os.path.join(INPUT_DIR, sample_file)

    if os.path.exists(sample_filepath):
        print(f"🚀 Starting graph execution with sample file: {sample_file} 🚀")
        # The input to the graph is a dictionary with the key matching the attribute in the state
        initial_input = {"filepath": sample_filepath}

        # Run the graph
        final_state = app.invoke(initial_input)

        print("\n--- 🏁 Graph Execution Finished ---")
        print(f"Final State: {final_state}")
        print(f"Profile for '{os.path.basename(sample_filepath)}' processed and stored with DB ID: {final_state.get('db_id')}")
    else:
        print(f"⚠️  Test file not found: {sample_filepath}")
        print("Please place a sample PDF in the 'agents/jobdescription/input/' directory to run this test.")
