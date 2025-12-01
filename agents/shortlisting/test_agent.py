import sys
import os
import json
from typing import List, Dict

# Add backend to path to import AIAgent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from backend.agent_orchestrator import AIAgent

class TestGenerationAgent(AIAgent):
    """Autonomous agent for generating test questions"""
    
    def __init__(self):
        super().__init__(
            "Test Generation Agent",
            "autonomously generates technical and aptitude questions for tests"
        )
    
    def generate_questions(self, topic: str, count: int = 5, difficulty: str = "medium", type: str = "multiple_choice") -> List[Dict]:
        """Generate questions using LLM"""
        self.notify(
            f"🧠 Generating {count} {difficulty} {type} questions on '{topic}'...",
            'processing'
        )
        
        prompt = f"""User Request: "{topic}"
        
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
        
        try:
            if not self.client:
                # Fallback if no client
                return self._get_fallback_questions(topic, count)

            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:fireworks-ai", # Or any available model
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up potential markdown code blocks
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            questions = json.loads(content.strip())
            
            self.notify(
                f"✅ Generated {len(questions)} questions on '{topic}'",
                'success',
                reasoning=f"LLM successfully generated {len(questions)} questions"
            )
            
            return questions
            
        except Exception as e:
            self.notify(
                f"❌ Failed to generate questions: {str(e)}",
                'error'
            )
            print(f"Error generating questions: {e}")
            return self._get_fallback_questions(topic, count)

    def _get_fallback_questions(self, topic: str, count: int) -> List[Dict]:
        """Return dummy questions if LLM fails"""
        return [
            {
                "question": f"Sample question {i+1} about {topic}?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "Option A",
                "explanation": "This is a fallback question."
            }
            for i in range(count)
        ]
