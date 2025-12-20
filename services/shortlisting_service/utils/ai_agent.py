import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

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
            token = os.environ.get('HF_TOKEN') # Or OPENAI_API_KEY
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
