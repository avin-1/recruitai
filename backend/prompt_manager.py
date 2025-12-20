"""
Prompt Management System - Stores and manages agent prompts with versioning
"""
import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

class PromptManager:
    """Manages agent prompts with versioning and modification history"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(backend_dir, 'prompts.db')
        self.db_path = db_path
        self._init_db()
        self._load_default_prompts()
    
    def _init_db(self):
        """Initialize the prompts database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prompts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                prompt_type TEXT NOT NULL,
                prompt_content TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(agent_name, prompt_type, version)
            )
        ''')
        
        # Feedback table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                feedback_text TEXT NOT NULL,
                hr_email TEXT,
                status TEXT DEFAULT 'pending',
                llm_suggestion TEXT,
                modified_prompt TEXT,
                applied BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_at TIMESTAMP
            )
        ''')
        
        # Prompt modification history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                prompt_type TEXT NOT NULL,
                old_version INTEGER,
                new_version INTEGER,
                change_reason TEXT,
                feedback_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feedback_id) REFERENCES feedback(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_default_prompts(self):
        """Load default prompts for all agents"""
        default_prompts = {
            'Resume and Matching Agent': {
                'reasoning': """You are an AI agent named 'Resume and Matching Agent' that automatically matches resumes to job descriptions using semantic analysis and LLM scoring.

Context: {context}
Task: {task}

Provide a brief, clear explanation (1-2 sentences) of your reasoning and decision:""",
                'matching': """Analyze the match between the resume and job description. Consider:
1. Skills alignment (technical and soft skills)
2. Experience relevance
3. Education requirements
4. Cultural fit indicators

Return a score (0-100) and brief reasoning."""
            },
            'Job Description Agent': {
                'reasoning': """You are an AI agent named 'Job Description Agent' that automatically parses job descriptions from PDFs and extracts structured information.

Context: {context}
Task: {task}

Provide a brief, clear explanation (1-2 sentences) of your reasoning and decision:""",
                'parsing': """Parse job description and extract:
1. Job title
2. Company name
3. Location
4. Key responsibilities
5. Required skills
6. Experience level
7. Educational requirements

Return structured JSON with all extracted information."""
            },
            'Shortlisting Agent': {
                'reasoning': """You are an AI agent named 'Shortlisting Agent' that autonomously evaluates candidate test performance and recommends shortlisting decisions.

Context: {context}
Task: {task}

Provide a brief, clear explanation (1-2 sentences) of your reasoning and decision:""",
                'evaluation': """Evaluate the candidate's test performance. Consider:
1. Problem-solving completion rate
2. Difficulty of problems solved
3. Time taken
4. Code quality indicators

Determine if candidate should be SHORTLIST or REJECT based on performance threshold."""
            },
            'Interview Scheduler Agent': {
                'reasoning': """You are an AI agent named 'Interview Scheduler Agent' that autonomously schedules interviews by analyzing HR calendar availability and optimizing time slots.

Context: {context}
Task: {task}

Provide a brief, clear explanation (1-2 sentences) of your reasoning and decision:""",
                'scheduling': """Propose optimal interview slots. Consider:
1. HR availability
2. Number of candidates
3. Time zone compatibility
4. Avoiding conflicts
5. Preferring morning slots when possible

Select best slots that minimize conflicts."""
            },
            'Test Generation Agent': {
                'generation': """User Request: "{topic}"

Task: Generate {count} {difficulty} {type} questions based on the request above.
- If the request is a topic (e.g. "Python"), generate questions about that topic.
- If the request is a specific instruction (e.g. "Give me questions about decorators"), follow that instruction.

Format the output as a JSON array of objects. Each object must have:
- "question": The question text
- "options": An array of 4 options (strings)
- "correct_answer": The correct option (string, must match one of the options exactly)
- "explanation": Brief explanation of the answer

Ensure the questions are high quality and relevant.
Output ONLY the JSON array. Do not add any markdown formatting or extra text."""
            },
            'Interview Chat Agent': {
                'reasoning': """You are an intelligent interview scheduling assistant.
Your goal is to help the user schedule an interview.
Current Date: {current_date_str} ({current_day_name})
Current Time: {current_time_str}

Extract the following information from the user's message:
1. Intent: "schedule" (if they want slots), "reject" (if they decline), "query" (general question), or "unknown".
2. Target Date: The specific date they want (YYYY-MM-DD). Calculate relative dates (tomorrow, next monday) based on Current Date.
3. Time Preference: "morning" (09:00-12:00), "afternoon" (12:00-17:00), "evening" (17:00-20:00), or specific time range if mentioned.
4. Negation: If they say "not tomorrow", "can't do monday", etc., identify the date they CANNOT do.

Output JSON ONLY:
{{
  "intent": "schedule|reject|query|unknown",
  "target_date": "YYYY-MM-DD" or null,
  "time_preference": {{"start": "HH:MM", "end": "HH:MM"}} or null,
  "natural_response": "A friendly, professional response confirming what you understood and what you are showing."
}}"""
            }
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for agent_name, prompts in default_prompts.items():
            for prompt_type, prompt_content in prompts.items():
                # Check if default prompt already exists
                cursor.execute('''
                    SELECT COUNT(*) FROM prompts 
                    WHERE agent_name = ? AND prompt_type = ? AND version = 1
                ''', (agent_name, prompt_type))
                
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO prompts (agent_name, prompt_type, prompt_content, version, is_active)
                        VALUES (?, ?, ?, 1, 1)
                    ''', (agent_name, prompt_type, prompt_content))
        
        conn.commit()
        conn.close()
    
    def get_prompt(self, agent_name: str, prompt_type: str) -> Optional[str]:
        """Get the active prompt for an agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT prompt_content FROM prompts
            WHERE agent_name = ? AND prompt_type = ? AND is_active = 1
            ORDER BY version DESC
            LIMIT 1
        ''', (agent_name, prompt_type))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def get_all_prompts(self, agent_name: str = None) -> List[Dict]:
        """Get all prompts, optionally filtered by agent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if agent_name:
            cursor.execute('''
                SELECT agent_name, prompt_type, prompt_content, version, is_active, modified_at
                FROM prompts
                WHERE agent_name = ?
                ORDER BY agent_name, prompt_type, version DESC
            ''', (agent_name,))
        else:
            cursor.execute('''
                SELECT agent_name, prompt_type, prompt_content, version, is_active, modified_at
                FROM prompts
                ORDER BY agent_name, prompt_type, version DESC
            ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'agent_name': row[0],
                'prompt_type': row[1],
                'prompt_content': row[2],
                'version': row[3],
                'is_active': bool(row[4]),
                'modified_at': row[5]
            })
        
        conn.close()
        return results
    
    def update_prompt(self, agent_name: str, prompt_type: str, new_prompt: str, change_reason: str = None, feedback_id: int = None) -> int:
        """Update a prompt with versioning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current version
        cursor.execute('''
            SELECT MAX(version) FROM prompts
            WHERE agent_name = ? AND prompt_type = ?
        ''', (agent_name, prompt_type))
        
        result = cursor.fetchone()
        old_version = result[0] if result[0] else 0
        new_version = old_version + 1
        
        # Deactivate old prompts
        cursor.execute('''
            UPDATE prompts SET is_active = 0
            WHERE agent_name = ? AND prompt_type = ?
        ''', (agent_name, prompt_type))
        
        # Insert new prompt version
        cursor.execute('''
            INSERT INTO prompts (agent_name, prompt_type, prompt_content, version, is_active, modified_at)
            VALUES (?, ?, ?, ?, 1, ?)
        ''', (agent_name, prompt_type, new_prompt, new_version, datetime.now(timezone.utc).isoformat()))
        
        # Record history
        cursor.execute('''
            INSERT INTO prompt_history (agent_name, prompt_type, old_version, new_version, change_reason, feedback_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (agent_name, prompt_type, old_version, new_version, change_reason, feedback_id))
        
        conn.commit()
        new_prompt_id = cursor.lastrowid
        conn.close()
        
        return new_version
    
    def submit_feedback(self, agent_name: str, feedback_text: str, hr_email: str = None) -> int:
        """Submit HR feedback"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feedback (agent_name, feedback_text, hr_email, status)
            VALUES (?, ?, ?, 'pending')
        ''', (agent_name, feedback_text, hr_email))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return feedback_id
    
    def get_feedback(self, feedback_id: int = None, agent_name: str = None) -> List[Dict]:
        """Get feedback entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if feedback_id:
            cursor.execute('''
                SELECT id, agent_name, feedback_text, hr_email, status, llm_suggestion, 
                       modified_prompt, applied, created_at, applied_at
                FROM feedback
                WHERE id = ?
            ''', (feedback_id,))
        elif agent_name:
            cursor.execute('''
                SELECT id, agent_name, feedback_text, hr_email, status, llm_suggestion,
                       modified_prompt, applied, created_at, applied_at
                FROM feedback
                WHERE agent_name = ?
                ORDER BY created_at DESC
            ''', (agent_name,))
        else:
            cursor.execute('''
                SELECT id, agent_name, feedback_text, hr_email, status, llm_suggestion,
                       modified_prompt, applied, created_at, applied_at
                FROM feedback
                ORDER BY created_at DESC
            ''')
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'agent_name': row[1],
                'feedback_text': row[2],
                'hr_email': row[3],
                'status': row[4],
                'llm_suggestion': row[5],
                'modified_prompt': row[6],
                'applied': bool(row[7]),
                'created_at': row[8],
                'applied_at': row[9]
            })
        
        conn.close()
        return results
    
    def update_feedback(self, feedback_id: int, llm_suggestion: str = None, modified_prompt: str = None, status: str = None, applied: bool = None):
        """Update feedback with LLM suggestions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if llm_suggestion is not None:
            updates.append('llm_suggestion = ?')
            params.append(llm_suggestion)
        
        if modified_prompt is not None:
            updates.append('modified_prompt = ?')
            params.append(modified_prompt)
        
        if status is not None:
            updates.append('status = ?')
            params.append(status)
        
        if applied is not None:
            updates.append('applied = ?')
            params.append(1 if applied else 0)
            if applied:
                updates.append('applied_at = ?')
                params.append(datetime.now(timezone.utc).isoformat())
        
        if updates:
            params.append(feedback_id)
            cursor.execute(f'''
                UPDATE feedback SET {', '.join(updates)}
                WHERE id = ?
            ''', params)
            
            conn.commit()
        
        conn.close()

# Global prompt manager instance
prompt_manager = PromptManager()

