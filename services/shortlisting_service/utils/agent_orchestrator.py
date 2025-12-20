"""
Agentic AI Orchestrator - Local version for Shortlisting Microservice
"""
import os
import json
import time
from typing import Dict, List, Optional
from .ai_agent import AIAgent, NotificationStore, notification_store

# Import PromptManager from local utils
try:
    from .prompt_manager import prompt_manager
except ImportError:
    prompt_manager = None

# --- Agents ---

class ShortlistingAgent(AIAgent):
    """Autonomous agent for candidate shortlisting"""
    
    def __init__(self):
        super().__init__(
            "Shortlisting Agent",
            "autonomously evaluates candidate test performance and recommends shortlisting decisions"
        )
        # We skip LangGraph for simplicity in this migration if not strictly needed, 
        # or we implement a functional version directly. 
        # The original code used LangGraph. For stability, let's keep the core logic 
        # but simplify the execution flow if LangGraph is missing, or assume it's there.
        # Assuming LangChain/Graph dependencies are installed. (requirements.tx check needed)
    
    def reason(self, context: str, task: str) -> str:
        """Generate AI reasoning for a decision"""
        if not self.client:
            return f"AI Agent '{self.name}' analyzed: {task}"
        
        try:
            # Try to get custom prompt from prompt manager
            custom_prompt = None
            if prompt_manager:
                custom_prompt = prompt_manager.get_prompt(self.name, 'reasoning')
            
            # Use custom prompt if available, otherwise use default
            if custom_prompt:
                prompt = custom_prompt.format(context=context, task=task)
            else:
                prompt = f"""You are an AI agent named '{self.name}' that {self.description}.

Context: {context}
Task: {task}

Provide a brief, clear explanation (1-2 sentences) of your reasoning and decision:"""
            
            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:fireworks-ai",
                messages=[
                    {"role": "system", "content": "You are a helpful AI agent that explains its reasoning clearly and concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Analyzed {task} using internal logic. ({str(e)[:50]})"

    def evaluate_candidate(self, candidate_data: Dict, test_questions: List[Dict]) -> Dict:
        """Autonomously evaluate candidate for shortlisting"""
        
        email = candidate_data.get('email', 'Unknown')
        self.notify(
            f"🧠 Evaluating candidate {email} for shortlisting...",
            'processing'
        )
        
        total_questions = len(test_questions)
        solved = candidate_data.get('total_solved', 0)
        completion_rate = (solved / total_questions * 100) if total_questions > 0 else 0
        
        # Generate reasoning
        reasoning = self.reason(
            f"Candidate solved {solved}/{total_questions} questions ({completion_rate:.1f}% completion)",
            f"Determine if candidate should be shortlisted for interview based on performance"
        )
        
        threshold = 60.0
        decision = "SHORTLIST" if completion_rate >= threshold else "REJECT"
        
        self.notify(
            f"📊 Evaluation: {email} - {completion_rate:.1f}% completion → {decision}",
            'decision',
            reasoning=reasoning,
            details={
                'email': email,
                'completion_rate': completion_rate,
                'threshold': threshold,
                'decision': decision
            }
        )
        
        return {
            'completion_rate': completion_rate,
            'decision': decision,
            'reasoning': reasoning
        }

# Global agents
shortlisting_agent = ShortlistingAgent()

def get_notifications():
    """Get all notifications"""
    return notification_store.get_all()

def mark_notification_read(index: int):
    """Mark notification as read"""
    notification_store.mark_read(index)

def clear_all_notifications():
    """Clear all notifications"""
    notification_store.clear_all()
