"""Autonomous Resume Matching Agent Integration"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from agent_orchestrator import resume_agent

def enhanced_match_resume(resume_text: str, job_description: str, job_id: str):
    """Enhanced resume matching with AI agent explainability"""
    result = resume_agent.match_resume(resume_text, job_description, job_id)
    return result

