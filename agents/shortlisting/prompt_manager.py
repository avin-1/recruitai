import os
import sys
from typing import Optional
import openai

# Add parent directory to path to import shortlisting_database as database
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from agents.shortlisting.shortlisting_database import DatabaseManager

# Default Prompts (Templates)
# Note: Using {variable} for python formatting. Literal braces must be escaped as {{ }}

DEFAULT_TEST_AGENT_PROMPT = """User Request: "{topic}"

Task: Generate {count} {difficulty} {type} questions based on the request above.
- If the request is a topic (e.g. "Python"), generate questions about that topic.
- If the request is a specific instruction (e.g. "Give me questions about decorators"), follow that instruction.

Format the output as a JSON array of objects. Each object must have:
- "question": The question text
- "options": An array of 4 options (strings)
- "correct_answer": The correct option (string, must match one of the options exactly)
- "explanation": Brief explanation of the answer

Ensure the questions are high quality and relevant.
Output ONLY the JSON array. Do not add any markdown formatting or extra text.
"""

DEFAULT_INTERVIEW_AGENT_PROMPT = """You are an intelligent interview scheduling assistant.
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

DEFAULT_JD_AGENT_PROMPT = """You are an expert job parsing agent. Your task is to extract key information from the following job description and return it as a structured JSON object.

Extract the following fields:
- **job_title**: The official title of the job.
- **company**: The name of the hiring company.
- **location**: The primary location of the job (e.g., city, country).
- **responsibilities**: A list of key responsibilities.
- **required_skills**: A list of essential skills or technologies.
- **experience_level**: The required years of experience or a general level (e.g., "5+ years", "Entry-level").
- **educational_requirements**: The minimum educational qualifications (e.g., "Bachelor's degree in Computer Science").

If a field is not explicitly found, use `null` for its value.
The output MUST be a valid JSON object.

---
Job Description:
{job_description_text}
---

JSON Output:
"""

class PromptManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.defaults = {
            "Test Generation Agent": DEFAULT_TEST_AGENT_PROMPT,
            "Interview Chat Agent": DEFAULT_INTERVIEW_AGENT_PROMPT,
            "Job Description Agent": DEFAULT_JD_AGENT_PROMPT
        }
        
        # Initialize OpenAI client for prompt modification
        # Using the same config as other agents
        self.client = None
        try:
            api_key = os.getenv("FIREWORKS_API_KEY")
            base_url = "https://api.fireworks.ai/inference/v1"
            if api_key:
                self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")

    def get_prompt(self, agent_name: str) -> str:
        """Get the effective prompt (custom or default)"""
        custom_prompt = self.db.get_agent_prompt(agent_name)
        if custom_prompt:
            return custom_prompt
        return self.defaults.get(agent_name, "")

    def get_default_prompt(self, agent_name: str) -> str:
        return self.defaults.get(agent_name, "")

    def reset_prompt(self, agent_name: str) -> None:
        self.db.reset_agent_prompt(agent_name)

    def modify_prompt_with_llm(self, agent_name: str, instruction: str) -> str:
        """Use LLM to rewrite the prompt based on instruction"""
        current_prompt = self.get_prompt(agent_name)
        
        if not self.client:
            raise Exception("LLM client not initialized. Cannot modify prompt.")

        meta_prompt = f"""You are an expert Prompt Engineer.
        
        Your task is to rewrite the following SYSTEM PROMPT based on the user's instruction.
        
        CRITICAL RULES:
        1. You MUST preserve all formatting placeholders (e.g. {{topic}}, {{count}}, {{current_date_str}}). Do NOT remove or change them.
        2. You MUST preserve the output format requirements (e.g. "Output JSON ONLY").
        3. You MUST preserve the core functionality of the prompt.
        4. Apply the user's instruction (style, tone, additional constraints) to the prompt text.
        
        CURRENT PROMPT:
        \"\"\"
        {current_prompt}
        \"\"\"
        
        USER INSTRUCTION:
        "{instruction}"
        
        Output ONLY the new prompt text. Do not add any explanations or markdown code blocks.
        """
        
        response = self.client.chat.completions.create(
            model="accounts/fireworks/models/llama-v3p1-70b-instruct", # Using a strong model for prompt engineering
            messages=[
                {"role": "user", "content": meta_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        new_prompt = response.choices[0].message.content.strip()
        
        # Cleanup
        if new_prompt.startswith("```"):
            lines = new_prompt.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            new_prompt = "\n".join(lines).strip()
            
        # Save the new prompt
        self.db.save_agent_prompt(agent_name, new_prompt)
        
        return new_prompt
