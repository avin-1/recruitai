"""
Agentic AI Orchestrator - Coordinates autonomous AI agents with reasoning and explainability
"""
import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, TypedDict, Any
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

class NotificationStore:
    """In-memory notification store (can be replaced with DB)"""
    def __init__(self):
        self.notifications = []
    
    def add(self, notification: Dict):
        notification['timestamp'] = datetime.now(timezone.utc).isoformat()
        notification['read'] = False
        self.notifications.insert(0, notification)
        # Keep last 100 notifications
        if len(self.notifications) > 100:
            self.notifications = self.notifications[:100]
        return notification
    
    def get_all(self) -> List[Dict]:
        return self.notifications
    
    def mark_read(self, index: int):
        if 0 <= index < len(self.notifications):
            self.notifications[index]['read'] = True
    
    def clear_all(self):
        self.notifications = []

# Global notification store
notification_store = NotificationStore()

class AIAgent:
    """Base class for autonomous AI agents"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.client = None
        try:
            token = os.environ.get('HF_TOKEN')
            if token:
                self.client = OpenAI(
                    base_url="https://router.huggingface.co/v1",
                    api_key=token,
                    timeout=60.0
                )
        except:
            pass
    
    def notify(self, message: str, type: str = 'info', reasoning: str = None, details: Dict = None):
        """Send notification with AI reasoning"""
        notification_store.add({
            'agent': self.name,
            'message': message,
            'type': type,
            'reasoning': reasoning,
            'details': details
        })
    
    def reason(self, context: str, task: str) -> str:
        """Generate AI reasoning for a decision"""
        if not self.client:
            return f"AI Agent '{self.name}' analyzed: {task}"
        
        try:
            # Try to get custom prompt from prompt manager
            try:
                from prompt_manager import prompt_manager
                custom_prompt = prompt_manager.get_prompt(self.name, 'reasoning')
            except ImportError:
                custom_prompt = None
            
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


# --- LangGraph States ---

class ResumeState(TypedDict):
    resume_text: str
    job_description: str
    job_id: str
    result: Dict

class ShortlistState(TypedDict):
    candidate_data: Dict
    test_questions: List[Dict]
    result: Dict

class SchedulingState(TypedDict):
    availability_slots: List[Dict]
    candidate_count: int
    result: List[Dict]

class JDState(TypedDict):
    file_path: str
    result: Dict


# --- Agents with LangGraph ---

class ResumeMatchingAgent(AIAgent):
    """Autonomous agent for resume-job matching"""
    
    def __init__(self):
        super().__init__(
            "Resume and Matching Agent",
            "automatically matches resumes to job descriptions using semantic analysis and LLM scoring"
        )
        # Initialize LangGraph
        builder = StateGraph(ResumeState)
        builder.add_node("analyze", self._analyze_node)
        builder.set_entry_point("analyze")
        builder.add_edge("analyze", END)
        self.graph = builder.compile()
    
    def _analyze_node(self, state: ResumeState) -> Dict:
        """LangGraph node for analysis"""
        resume_text = state['resume_text']
        job_description = state['job_description']
        job_id = state['job_id']
        
        self.notify(
            f"🔄 Analyzing resume against job {job_id}...",
            'processing'
        )
        
        # Simple scoring logic (enhance with actual LLM)
        resume_words = set(resume_text.lower().split())
        jd_words = set(job_description.lower().split())
        overlap = len(resume_words & jd_words)
        total_jd = len(jd_words) or 1
        score = min(100.0, (overlap / total_jd) * 100)
        
        # Generate reasoning
        reasoning = self.reason(
            f"Resume: {resume_text[:200]}... | Job: {job_description[:200]}...",
            f"Calculate match score between resume and job description"
        )
        
        threshold = 50.0
        decision = "ACCEPTED" if score >= threshold else "REJECTED"
        
        self.notify(
            f"✅ Resume matched: Score {score:.1f}/100 - {decision}",
            'decision',
            reasoning=reasoning,
            details={'score': score, 'threshold': threshold, 'job_id': job_id, 'decision': decision}
        )
        
        return {
            "result": {
                'score': score,
                'decision': decision,
                'reasoning': reasoning
            }
        }

    def match_resume(self, resume_text: str, job_description: str, job_id: str) -> Dict:
        """Autonomously match resume to job with reasoning"""
        inputs = {
            "resume_text": resume_text,
            "job_description": job_description,
            "job_id": job_id,
            "result": {}
        }
        output = self.graph.invoke(inputs)
        return output['result']


class ShortlistingAgent(AIAgent):
    """Autonomous agent for candidate shortlisting"""
    
    def __init__(self):
        super().__init__(
            "Shortlisting Agent",
            "autonomously evaluates candidate test performance and recommends shortlisting decisions"
        )
        # Initialize LangGraph
        builder = StateGraph(ShortlistState)
        builder.add_node("evaluate", self._evaluate_node)
        builder.set_entry_point("evaluate")
        builder.add_edge("evaluate", END)
        self.graph = builder.compile()
    
    def _evaluate_node(self, state: ShortlistState) -> Dict:
        """LangGraph node for evaluation"""
        candidate_data = state['candidate_data']
        test_questions = state['test_questions']
        
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
            "result": {
                'completion_rate': completion_rate,
                'decision': decision,
                'reasoning': reasoning
            }
        }

    def evaluate_candidate(self, candidate_data: Dict, test_questions: List[Dict]) -> Dict:
        """Autonomously evaluate candidate for shortlisting"""
        inputs = {
            "candidate_data": candidate_data,
            "test_questions": test_questions,
            "result": {}
        }
        output = self.graph.invoke(inputs)
        return output['result']


class InterviewSchedulingAgent(AIAgent):
    """Autonomous agent for interview scheduling"""
    
    def __init__(self):
        super().__init__(
            "Interview Scheduler Agent",
            "autonomously schedules interviews by analyzing HR calendar availability and optimizing time slots"
        )
        # Initialize LangGraph
        builder = StateGraph(SchedulingState)
        builder.add_node("schedule", self._schedule_node)
        builder.set_entry_point("schedule")
        builder.add_edge("schedule", END)
        self.graph = builder.compile()
    
    def _schedule_node(self, state: SchedulingState) -> Dict:
        """LangGraph node for scheduling"""
        availability_slots = state['availability_slots']
        candidate_count = state['candidate_count']
        
        self.notify(
            f"📅 Analyzing {len(availability_slots)} available slots for {candidate_count} candidates...",
            'processing'
        )
        
        # Simple logic: prefer morning slots, avoid conflicts
        sorted_slots = sorted(availability_slots, key=lambda x: x.get('start', ''))
        best_slots = sorted_slots[:min(5, len(sorted_slots))]
        
        reasoning = self.reason(
            f"Found {len(availability_slots)} slots, {candidate_count} candidates need scheduling",
            f"Select optimal interview time slots that minimize conflicts and maximize HR availability"
        )
        
        self.notify(
            f"🎯 Proposed {len(best_slots)} optimal interview slots",
            'decision',
            reasoning=reasoning,
            details={'slots': best_slots, 'candidate_count': candidate_count}
        )
        
        return {"result": best_slots}

    def propose_best_slots(self, availability_slots: List[Dict], candidate_count: int) -> List[Dict]:
        """Autonomously propose best interview slots"""
        inputs = {
            "availability_slots": availability_slots,
            "candidate_count": candidate_count,
            "result": []
        }
        output = self.graph.invoke(inputs)
        return output['result']


class JobDescriptionAgent(AIAgent):
    """Autonomous agent for job description parsing and management"""
    
    def __init__(self):
        super().__init__(
            "Job Description Agent",
            "automatically parses job descriptions from PDFs and extracts structured information"
        )
        # Initialize LangGraph
        builder = StateGraph(JDState)
        builder.add_node("parse", self._parse_node)
        builder.set_entry_point("parse")
        builder.add_edge("parse", END)
        self.graph = builder.compile()
    
    def _parse_node(self, state: JDState) -> Dict:
        """LangGraph node for parsing"""
        file_path = state['file_path']
        
        self.notify(
            f"📄 Parsing job description from {file_path}...",
            'processing'
        )
        
        try:
            # Import job description parsing function
            import sys
            import os
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            jd_path = os.path.join(backend_dir, 'agents', 'jobdescription')
            if jd_path not in sys.path:
                sys.path.insert(0, jd_path)
            
            from jdParsing import parse_job_description as parse_jd
            
            result = parse_jd(file_path)
            
            reasoning = self.reason(
                f"Parsed job description: {file_path}",
                f"Extract structured information from job description PDF"
            )
            
            self.notify(
                f"✅ Successfully parsed job description: {result.get('job_title', 'Unknown')}",
                'success',
                reasoning=reasoning,
                details={
                    'file_path': file_path,
                    'job_title': result.get('job_title'),
                    'company': result.get('company')
                }
            )
            
            return {
                "result": {
                    'success': True,
                    'result': result,
                    'reasoning': reasoning
                }
            }
        except Exception as e:
            error_msg = str(e)
            self.notify(
                f"❌ Failed to parse job description: {error_msg}",
                'error',
                reasoning=f"Error parsing job description: {error_msg}"
            )
            return {
                "result": {
                    'success': False,
                    'error': error_msg,
                    'reasoning': f"Error: {error_msg}"
                }
            }

    def parse_job_description(self, file_path: str) -> Dict:
        """Autonomously parse job description from PDF"""
        inputs = {
            "file_path": file_path,
            "result": {}
        }
        output = self.graph.invoke(inputs)
        return output['result']


# Global agents
resume_agent = ResumeMatchingAgent()
shortlisting_agent = ShortlistingAgent()
scheduling_agent = InterviewSchedulingAgent()
job_description_agent = JobDescriptionAgent()

def get_notifications():
    """Get all notifications"""
    return notification_store.get_all()

def mark_notification_read(index: int):
    """Mark notification as read"""
    notification_store.mark_read(index)

def clear_all_notifications():
    """Clear all notifications"""
    notification_store.clear_all()

