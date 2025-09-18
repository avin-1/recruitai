import os
import time
import json
import subprocess
from dataclasses import dataclass, field
from pymongo import MongoClient
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

# ---------- Agent State ----------
@dataclass
class AgentState:
    """Represents the state of our job application agent."""
    jobtitle: str = ""
    approved: bool = False
    # Added to store files that have already been processed
    processed_files: list = field(default_factory=list)
    # Temporary paths to pass between nodes within a single workflow run
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
    
    # Filter out files that have already been processed
    new_files = [os.path.join(folder, f) for f in files if os.path.join(folder, f) not in exclude_list]
    
    return max(new_files, key=os.path.getctime) if new_files else None

# ---------- Node functions ----------
def wait_for_input(state: AgentState) -> AgentState:
    """
    Waits for a new job description file to appear in the 'Input' folder.
    This node polls the directory and transitions only when a new file is found.
    """
    print("Node: Waiting for a new job description in 'Input' folder...")
    while True:
        # Check for new files, ignoring those already processed
        new_jd_file = latest_file("Input", state.processed_files)
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
    
    # Execute external script to parse JD
    try:
        # Pass the input file path to the external script
        subprocess.run(["python", "jdparsing.py", inp], check=True)
        with open(inp, "r") as f:
            data = json.load(f)
        state.jobtitle = data.get("title", "")
        print(f"Job title found: '{state.jobtitle}'")
        state.approved = False
    except subprocess.CalledProcessError as e:
        print(f"Error executing jdparsing.py: {e}")
    except FileNotFoundError:
        print(f"Error: jdparsing.py or the input file not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the input file '{inp}'.")
    return state

def wait_for_output(state: AgentState) -> AgentState:
    """
    Waits for a new output file to be created in the 'Output' folder.
    This node polls the directory and transitions only when a new file is found.
    """
    print("Node: Waiting for a new file in 'Output' folder...")
    while True:
        new_output_file = latest_file("Output", []) # Note: We don't exclude files here
        if new_output_file:
            print(f"New output file found: '{new_output_file}'")
            state.current_output_path = new_output_file
            return state

        print("No new output files found. Checking again in 5s...")
        time.sleep(5)

def store_profile(state: AgentState) -> AgentState:
    """Stores the parsed profile, including the job title, to the database."""
    print("Node: Storing Profile...")
    out = state.current_output_path
    if not out or not os.path.exists(out):
        print(f"Error: No output file path provided or file does not exist: {out}")
        return state
        
    # Execute external script to store profile
    try:
        subprocess.run(["python", "profileStore.py", out], check=True)
        print("Profile successfully stored.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing profileStore.py: {e}")
    except FileNotFoundError:
        print("Error: profileStore.py not found.")
    return state

# ---------- Conditional Logic ----------
def should_continue(state: AgentState) -> str:
    """
    Determines the next step based on the 'approved' state.
    Returns 'end' if approved, 'continue' otherwise.
    """
    print("Router: Checking approval status...")
    if state.approved:
        return "end" # Ends this specific job workflow
    else:
        return "continue"

# ---------- Build Graph ----------
workflow = StateGraph(AgentState)
workflow.add_node("wait_for_input", wait_for_input)
workflow.add_node("parse_jd", parse_jd)
workflow.add_node("wait_for_output", wait_for_output)
workflow.add_node("store_profile", store_profile)

# Define the graph flow
workflow.add_edge(START, "wait_for_input")
workflow.add_edge("wait_for_input", "parse_jd")
workflow.add_edge("parse_jd", "wait_for_output")
workflow.add_edge("wait_for_output", "store_profile")
workflow.add_edge("store_profile", END)

graph = workflow.compile()

# ---------- Run ----------
if __name__ == "__main__":
    print("Starting continuous agent workflow...")
    # The graph will handle the looping internally
    while True:
        print("\nReady for a new job. Waiting for input...")
        final_state = graph.invoke(AgentState())
        print("Workflow cycle finished.")
