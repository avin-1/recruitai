# Local import for microservice
try:
    from utils.ai_agent import AIAgent
except ImportError:
    # Fallback if running from different directory context
    import sys
    sys.path.append(os.path.dirname(__file__))
    from utils.ai_agent import AIAgent

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
        
        # Get dynamic prompt
        try:
            from prompt_manager import PromptManager
            prompt_manager = PromptManager()
            template = prompt_manager.get_prompt("Test Generation Agent")
        except Exception as e:
            print(f"Error loading prompt: {e}")
            # Fallback to hardcoded default if manager fails
            template = """User Request: "{topic}"
            
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

        # Format the template with current variables
        # Using .format() but handling potential missing keys safely
        try:
            prompt = template.format(
                topic=topic,
                count=count,
                difficulty=difficulty,
                type=type
            )
        except KeyError as e:
            print(f"Prompt formatting error (missing key {e}). Falling back to simple string.")
            prompt = f"{template}\n\nContext: {topic}, {count} questions, {difficulty}, {type}"
        
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
            content = self._clean_json_string(content)
            
            try:
                questions = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON Parse Error: {e}")
                print(f"Raw Content: {content}")
                # Try one more time with aggressive repair
                content = self._repair_json(content)
                questions = json.loads(content)
            
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

    def _clean_json_string(self, content: str) -> str:
        """Basic cleanup of markdown and whitespace"""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def _repair_json(self, content: str) -> str:
        """Aggressive JSON repair for common LLM errors"""
        import re
        # Fix invalid escape sequences (e.g. \s, \c, \e which are not valid JSON escapes)
        # JSON only allows \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
        # We want to escape backslashes that are NOT followed by these valid characters
        
        # This regex finds backslashes not followed by valid escape chars
        # and replaces them with double backslashes
        # Valid: " \ / b f n r t u
        
        # Replace \' with ' (valid in JS but not JSON)
        content = content.replace("\\'", "'")
        
        # Fix: replace single backslashes that are likely meant to be literal
        # This is hard to do perfectly with regex, but we can try to fix common ones
        # or just escape ALL backslashes that aren't part of a valid sequence.
        
        # Simple approach: If it fails, it's often because of things like "C:\Path" -> "C:\\Path"
        # or LaTeX like "\alpha" -> "\\alpha"
        
        # For now, let's try to fix the specific error "Invalid \escape"
        # This usually means a backslash followed by a char that isn't a valid escape.
        
        def replace_invalid_escape(match):
            return "\\\\" + match.group(1)
            
        # Find \ followed by anything that IS NOT " \ / b f n r t u
        content = re.sub(r'\\([^"\\/bfnrtu])', replace_invalid_escape, content)
        
        return content

    def _get_fallback_questions(self, topic: str, count: int) -> List[Dict]:
        """Return realistic dummy questions if LLM fails (Mock Mode)"""
        print(f"Generating fallback mock questions for: {topic}")
        
        # Simple keyword-based mock generation
        mock_questions = []
        topic_lower = topic.lower()
        
        for i in range(count):
            if "python" in topic_lower:
                q = {
                    "question": f"What is the output of print(2 ** {i+2}) in Python?",
                    "options": [str(2**(i+2)), str(2*(i+2)), str((i+2)**2), "Error"],
                    "correct_answer": str(2**(i+2)),
                    "explanation": "The ** operator performs exponentiation."
                }
            elif "react" in topic_lower:
                q = {
                    "question": f"Which hook is used for {['side effects', 'state', 'context', 'optimization'][i % 4]}?",
                    "options": ["useEffect", "useState", "useContext", "useMemo"],
                    "correct_answer": ["useEffect", "useState", "useContext", "useMemo"][i % 4],
                    "explanation": "Standard React hooks."
                }
            elif "math" in topic_lower:
                val = (i + 1) * 5
                q = {
                    "question": f"What is {val} + {val}?",
                    "options": [str(val*2), str(val+10), str(val*3), str(val)],
                    "correct_answer": str(val*2),
                    "explanation": "Basic addition."
                }
            else:
                 q = {
                    "question": f"Mock Question {i+1} about {topic}: What is the primary characteristic?",
                    "options": ["Efficiency", "Speed", "Complexity", "None of the above"],
                    "correct_answer": "Efficiency",
                    "explanation": "Generic fallback explanation."
                }
            mock_questions.append(q)
            
        return mock_questions
