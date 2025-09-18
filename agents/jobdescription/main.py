import os
import time
import json
import subprocess
from dataclasses import dataclass, field
from pymongo import MongoClient
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# Load .env file
load_dotenv()

# ---------- Agent State ----------
@dataclass
class AgentState:
    """Represents the state of our job application agent."""
    jobtitle: str = ""
    approved: bool = False
    processed_files: list = field(default_factory=list)
    current_jd_path: str = ""
    current_output_path: str = ""


def latest_file(folder: str, exclude_list: list):
    """
    Finds the latest file in a given folder that is not in the exclude list.
    Returns the full path or None if the folder doesn't exist or is empty.
    """
    if not os.path.isdir(folder):
        print(f"Error: Directory '{folder}' does not exist.")
        return None
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    
    new_files = [os.path.join(folder, f) for f in files if os.path.join(folder, f) not in exclude_list]
    
    return max(new_files, key=os.path.getctime) if new_files else None

# ---------- Node functions ----------
def wait_for_input(state: AgentState) -> AgentState:
    """
    Waits for a new job description file to appear in the 'input' folder.
    This node polls the directory and transitions only when a new file is found.
    """
    print("Node: Waiting for a new job description in 'input' folder...")
    while True:
        new_jd_file = latest_file("input", state.processed_files)
        if new_jd_file:
            print(f"New job description found: '{new_jd_file}'")
            state.processed_files.append(new_jd_file)
            state.current_jd_path = new_jd_file
            return state
        
        print("No new files found. Checking again in 10s...")
        time.sleep(10)

def parse_jd(state: AgentState) -> AgentState:
    """Parses the latest job description file to extract the job title."""
    print("Node: Parsing Job Description...")
    inp = state.current_jd_path
    
    try:
        env = os.environ.copy()
        result = subprocess.run(["python", "jdParsing.py", inp], check=True, capture_output=True, text=True, env=env)
        output_file_path = result.stdout.strip()
        if output_file_path and os.path.exists(output_file_path):
            state.current_output_path = output_file_path
            with open(output_file_path, "r") as f:
                data = json.load(f)
            state.jobtitle = data.get("title", "")
            print(f"Job title found: '{state.jobtitle}'")
            state.approved = False
        else:
            print(f"Error: jdParsing.py did not return a valid file path.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing jdParsing.py: {e}")
        print(f"Stderr: {e.stderr}")
    except FileNotFoundError:
        print(f"Error: jdParsing.py or the input file not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the output file.")
    return state

def store_profile(state: AgentState) -> AgentState:
    """Stores the parsed profile, including the job title, to the database."""
    print("Node: Storing Profile...")
    out = state.current_output_path
    if not out or not os.path.exists(out):
        print(f"Error: No output file path provided or file does not exist: {out}")
        return state
        
    try:
        env = os.environ.copy()
        subprocess.run(["python", "profileStore.py", out], check=True, env=env)
        print("Profile successfully stored.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing profileStore.py: {e}")
    except FileNotFoundError:
        print("Error: profileStore.py not found.")
    return state

# ---------- Build Graph ----------
workflow = StateGraph(AgentState)
workflow.add_node("wait_for_input", wait_for_input)
workflow.add_node("parse_jd", parse_jd)
workflow.add_node("store_profile", store_profile)

# Define the graph flow
workflow.add_edge(START, "wait_for_input")
workflow.add_edge("wait_for_input", "parse_jd")
workflow.add_edge("parse_jd", "store_profile")
workflow.add_edge("store_profile", END)

graph = workflow.compile()

# ---------- Run ----------
if __name__ == "__main__":
    print("Starting continuous agent workflow...")
    # Instantiate the state once to persist processed_files across runs
    agent_state = AgentState()
    while True:
        print("\nReady for a new job. Waiting for input...")
        final_state = graph.invoke(agent_state)
        # The state is now managed by the graph, and the updated state is returned.
        # We can pass it to the next invocation if we want to maintain state across graph runs.
        agent_state = final_state
        print("Workflow cycle finished.")

