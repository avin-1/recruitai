import os
import sys
import json
import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from backend.agent_orchestrator import AIAgent
except ImportError:
    # Fallback if running from different context
    class AIAgent:
        def __init__(self, name, description):
            self.name = name
            self.description = description
            self.client = None

class InterviewChatAgent(AIAgent):
    def __init__(self):
        super().__init__(
            name="InterviewChatAgent",
            description="An intelligent agent that helps schedule interviews by understanding natural language requests."
        )
        
    def process_chat(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a chat message using LLM to understand intent and extract entities.
        
        Args:
            message: The user's chat message
            context: Context dictionary containing 'client_time', 'hr_email', etc.
            
        Returns:
            Dict containing 'response_text' and 'slots' (if applicable)
        """
        # Default response if LLM fails or is unavailable
        default_response = {
            "response": "I'm having trouble connecting to my brain right now. Please try again later.",
            "slots": []
        }
        
        if not self.client:
            return {
                "response": "I am running in rule-based mode because I cannot access the LLM. Please check your API keys.",
                "slots": []
            }

        try:
            # Determine current reference time
            client_time_str = context.get('client_time')
            if client_time_str:
                try:
                    if client_time_str.endswith('Z'):
                        client_time_str = client_time_str[:-1]
                    current_dt = datetime.datetime.fromisoformat(client_time_str)
                except:
                    current_dt = datetime.datetime.utcnow()
            else:
                current_dt = datetime.datetime.utcnow()
                
            current_date_str = current_dt.strftime("%Y-%m-%d")
            current_day_name = current_dt.strftime("%A")
            current_time_str = current_dt.strftime("%H:%M")

            # Construct prompt for the LLM
            # Construct prompt for the LLM
            try:
                from prompt_manager import PromptManager
                prompt_manager = PromptManager()
                template = prompt_manager.get_prompt("Interview Chat Agent")
            except Exception as e:
                print(f"Error loading prompt: {e}")
                template = """You are an intelligent interview scheduling assistant.
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
}}
"""
            
            try:
                system_prompt = template.format(
                    current_date_str=current_date_str,
                    current_day_name=current_day_name,
                    current_time_str=current_time_str
                )
            except KeyError as e:
                print(f"Prompt formatting error: {e}")
                system_prompt = f"{template}\n\nCurrent Date: {current_date_str}, Time: {current_time_str}"
            
            user_prompt = f"User Message: {message}"

            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:fireworks-ai", # Or appropriate model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            llm_output = response.choices[0].message.content
            if not llm_output:
                raise ValueError("LLM returned empty response")
            
            llm_output = llm_output.strip()
            
            # Log raw output for debugging
            print(f"DEBUG: LLM Output: {llm_output}")
            
            # Parse JSON response
            try:
                parsed_output = json.loads(llm_output)
            except json.JSONDecodeError:
                # Fallback if LLM didn't return valid JSON
                # Try to extract JSON from text (handling markdown blocks)
                import re
                
                # Try finding json block
                json_block_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', llm_output)
                if json_block_match:
                    try:
                        parsed_output = json.loads(json_block_match.group(1))
                    except:
                        pass
                
                if 'parsed_output' not in locals():
                    # Try finding any brace-enclosed block
                    json_match = re.search(r'(\{[\s\S]*\})', llm_output)
                    if json_match:
                        try:
                            parsed_output = json.loads(json_match.group(1))
                        except:
                            raise ValueError(f"Could not parse extracted JSON: {json_match.group(1)}")
                    else:
                        raise ValueError(f"Could not parse LLM response: {llm_output}")

            intent = parsed_output.get("intent", "unknown")
            target_date_str = parsed_output.get("target_date")
            time_pref = parsed_output.get("time_preference")
            natural_response = parsed_output.get("natural_response", "Here are some slots based on your request.")
            
            slots = []
            
            if intent == "schedule":
                # Generate slots based on parsed info
                if target_date_str:
                    try:
                        target_date = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
                    except:
                        target_date = current_dt.date() + datetime.timedelta(days=1)
                else:
                    target_date = current_dt.date() + datetime.timedelta(days=1)
                
                # Determine start/end times for slot generation
                start_hour = 10
                end_hour = 17
                
                if time_pref:
                    try:
                        p_start = datetime.datetime.strptime(time_pref.get("start", "10:00"), "%H:%M")
                        p_end = datetime.datetime.strptime(time_pref.get("end", "17:00"), "%H:%M")
                        start_hour = p_start.hour
                        end_hour = p_end.hour
                    except:
                        pass
                
                # Generate 3 slots
                for i in range(3):
                    # Simple logic to space them out
                    hour = start_hour + (i * 2)
                    if hour >= end_hour:
                        hour = start_hour + i # Fallback to tighter spacing
                        
                    slot_start = datetime.datetime(target_date.year, target_date.month, target_date.day, hour, 0)
                    slot_end = slot_start + datetime.timedelta(minutes=30)
                    
                    slots.append({
                        'start': slot_start.isoformat() + 'Z',
                        'end': slot_end.isoformat() + 'Z'
                    })
            
            return {
                "response": natural_response,
                "slots": slots
            }

        except Exception as e:
            print(f"Error in InterviewChatAgent: {e}")
            return {
                "response": f"I encountered an error processing your request: {str(e)}. Showing default slots.",
                "slots": [] # Frontend handles empty slots or we could return default ones here
            }
