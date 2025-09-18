import os
import subprocess
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# --- Determine Virtual Environment Python Path ---
# Use the Python executable from the virtual environment
VENV_PYTHON = os.path.join(os.path.dirname(sys.executable), "python.exe")
if not os.path.exists(VENV_PYTHON):
    print(f"Error: Virtual environment Python executable not found at {VENV_PYTHON}")
    sys.exit(1)

# --- State ---
class State(TypedDict):
    processed_pdfs: set[str]
    processed_jsons: set[str]
    current_pdf_path: str
    current_json_path: str

# --- Watchdog Handler ---
class InputFolderHandler(FileSystemEventHandler):
    """Handles file system events for the input folder."""
    def __init__(self, state: State, callback):
        self.state = state
        self.callback = callback

    def on_created(self, event):
        """Called when a file is created in the input folder."""
        if event.is_directory:
            return
        file_path = event.src_path
        if file_path.endswith('.pdf') and file_path not in self.state["processed_pdfs"]:
            print(f"New PDF detected: {file_path}")
            self.state["processed_pdfs"].add(file_path)
            self.state["current_pdf_path"] = file_path  # Directly update state
            self.callback(self.state)  # Pass updated state to callback

# --- Node Functions ---
def wait_for_pdf(state: State) -> State:
    """Monitors the input folder for new PDF files using watchdog."""
    print("Node: Monitoring 'input' folder for new PDFs...")

    if not os.path.isdir("input"):
        print("Error: 'input' directory does not exist.")
        return state

    observer = Observer()
    def callback(updated_state: State):
        observer.stop()

    event_handler = InputFolderHandler(state, callback)
    observer.schedule(event_handler, path="input", recursive=False)
    observer.start()

    try:
        timeout = 300  # 5-minute timeout
        observer.join(timeout)
        if observer.is_alive():
            print("Timeout reached, no new PDFs detected.")
            observer.stop()
    finally:
        observer.stop()
        observer.join()

    print(f"State after wait_for_pdf: {state}")
    return state

def jd_parsing_node(state: State) -> State:
    """Runs jdParsing.py for the detected PDF."""
    print("[JD-PARSING] Running jdParsing.py...")
    pdf_path = state.get("current_pdf_path", "")
    
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"Error: No valid PDF path provided or file does not exist: {pdf_path}")
        return state

    try:
        result = subprocess.run(
            [VENV_PYTHON, "jdParsing.py", pdf_path],  # Use venv Python
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        output_file = result.stdout.strip()
        print(f"[JD-PARSING] jdParsing.py output: {output_file}")
        if output_file and os.path.exists(output_file):
            state["current_json_path"] = output_file
            print(f"[JD-PARSING] Successfully created: {output_file}")
        else:
            print(f"[JD-PARSING] Error: jdParsing.py did not return a valid file path: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"[JD-PARSING] Error executing jdParsing.py: {e}")
        print(f"[JD-PARSING] Stderr: {e.stderr}")
    except FileNotFoundError as e:
        print(f"[JD-PARSING] Error: jdParsing.py or PDF file not found: {e}")
    return state

def profile_store_node(state: State) -> State:
    """Runs profileStore.py for the generated JSON file."""
    print("[PROFILESTORE] Running profileStore.py...")
    json_path = state.get("current_json_path", "")

    if not json_path or not os.path.exists(json_path):
        print(f"[PROFILESTORE] Error: No valid JSON path provided or file does not exist: {json_path}")
        return state

    try:
        subprocess.run(
            [VENV_PYTHON, "profileStore.py", json_path],  # Use venv Python
            check=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        state["processed_jsons"].add(os.path.basename(json_path))
        print(f"[PROFILESTORE] Successfully stored profile for {json_path}")
    except subprocess.CalledProcessError as e:
        print(f"[PROFILESTORE] Error executing profileStore.py: {e}")
        print(f"[PROFILESTORE] Stderr: {e.stderr}")
    except FileNotFoundError as e:
        print(f"[PROFILESTORE] Error: profileStore.py or JSON file not found: {e}")
    return state

# --- Graph Setup ---
workflow = StateGraph(State)
workflow.add_node("wait_for_pdf", wait_for_pdf)
workflow.add_node("jd_parsing", jd_parsing_node)
workflow.add_node("profile_store", profile_store_node)

# Add edges
workflow.add_edge(START, "wait_for_pdf")
workflow.add_edge("wait_for_pdf", "jd_parsing")
workflow.add_edge("jd_parsing", "profile_store")
workflow.add_edge("profile_store", END)

graph = workflow.compile()

# --- Run Graph ---
if __name__ == "__main__":
    print("Starting job description processing workflow...")
    initial_state = State(processed_pdfs=set(), processed_jsons=set(), current_pdf_path="", current_json_path="")
    while True:
        print("\nReady for a new PDF. Waiting for input...")
        final_state = graph.invoke(initial_state)
        initial_state = final_state
        print("Workflow cycle finished.")