import os
import sys
from typing import Optional

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.prompt_manager import prompt_manager as backend_prompt_manager

class PromptManager:
    """Wrapper around backend PromptManager for shortlisting agents"""
    
    def __init__(self):
        self.manager = backend_prompt_manager
        
    def get_prompt(self, agent_name: str) -> str:
        """Get the effective prompt (custom or default)"""
        # Map agent name to default prompt type if needed
        prompt_type = 'generation' if agent_name == 'Test Generation Agent' else 'reasoning'
        
        prompt = self.manager.get_prompt(agent_name, prompt_type)
        if prompt:
            return prompt
            
        # Fallback if not found in DB (should not happen if defaults loaded)
        return ""

    def get_default_prompt(self, agent_name: str) -> str:
        # Not easily accessible from backend manager without querying DB for version 1
        # But for now, we can just return empty or implement if strictly needed
        return ""

    def reset_prompt(self, agent_name: str) -> None:
        # Not implemented in wrapper, use Settings API
        pass

    def modify_prompt_with_llm(self, agent_name: str, instruction: str) -> str:
        # Not implemented in wrapper, use Settings API
        pass
