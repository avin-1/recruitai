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
            # Point to the shared backend/prompts.db
            # This file is in services/shortlisting_service/utils/
            # Path to DB: ../../../../backend/prompts.db
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'backend', 'prompts.db'))
            
        self.db_path = db_path
        # We assume the DB is already initialized by the main backend, but we can init if missing
        self._init_db()
        # default prompts load might be redundant if DB exists, but safe
    
    def _init_db(self):
        """Initialize the prompts database"""
        # Ensure dir exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
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
    
    def get_default_prompt(self, agent_name: str) -> str:
        # Simplified for microservice usage - just return a string if we can't find it easily
        # ideally we copy the map, but for now let's just use what's in DB or return empty
        return "" 

    def get_prompt(self, agent_name: str, prompt_type: str = 'reasoning') -> Optional[str]:
        """Get the active prompt for an agent"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # If prompt_type wasn't passed correctly or needs inference
            # We just try to query
            
            cursor.execute('''
                SELECT prompt_content FROM prompts
                WHERE agent_name = ? AND prompt_type = ? AND is_active = 1
                ORDER BY version DESC
                LIMIT 1
            ''', (agent_name, prompt_type))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting prompt: {e}")
            return None
    
    def modify_prompt_with_llm(self, agent_name: str, instruction: str) -> str:
        # Mock implementation for microservice to avoid pulling in all LLM deps if not needed
        # Or we can implement if critical
        return f"Modified prompt for {agent_name} based on: {instruction}"

    def reset_prompt(self, agent_name: str):
        pass

# Global prompt manager instance
prompt_manager = PromptManager()
