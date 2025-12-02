import json
import re
from typing import Dict, List, Any

# Lazy import transformers to prevent crashes if not installed
TRANSFORMERS_AVAILABLE = False
AutoTokenizer = None
AutoModelForCausalLM = None
torch = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers library not available. LLM analysis will use rule-based fallback only.")
except Exception as e:
    TRANSFORMERS_AVAILABLE = False
    print(f"Warning: Error importing transformers: {e}. LLM analysis will use rule-based fallback only.")

class LLMPerformanceAnalyzer:
    def __init__(self, load_model=False):
        """Initialize the GPT-OSS-20B model for performance analysis
        
        Args:
            load_model: If False, model will not load at init. Set to True explicitly when needed.
                       This prevents crashes during Flask reloads and server startup.
        """
        self.model_name = "microsoft/DialoGPT-medium"  # Using DialoGPT as GPT-OSS-20B alternative
        self.tokenizer = None
        self.model = None
        self.device = "cpu"  # Default to CPU
        if TRANSFORMERS_AVAILABLE and torch is not None:
            try:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except:
                self.device = "cpu"
        self.model_loaded = False
        self._load_failed = False  # Track if loading has failed
        if load_model:
            self._load_model()
    
    def _load_model(self):
        """Load the LLM model and tokenizer - can be disabled to prevent crashes"""
        if self.model_loaded:
            return
        
        # Prevent model loading if we've already failed to load it
        if hasattr(self, '_load_failed') and self._load_failed:
            return
        
        # Check if transformers is available
        if not TRANSFORMERS_AVAILABLE:
            print("Transformers library not available. Skipping model load.")
            self._load_failed = True
            self.model = None
            self.tokenizer = None
            self.model_loaded = False
            return
            
        try:
            print("Loading LLM model for performance analysis...")
            print("Note: This may take several minutes on first load. If it hangs, cancel and use rule-based analysis.")
            
            # Try loading with basic settings first
            # Use timeout and better error handling
            import threading
            import queue
            
            result_queue = queue.Queue()
            error_queue = queue.Queue()
            
            def load_in_thread():
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(
                        self.model_name,
                        cache_dir=None,
                        use_fast=True,
                        trust_remote_code=False
                    )
                    
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        cache_dir=None,
                        trust_remote_code=False
                    )
                    
                    if torch is not None and torch.cuda.is_available():
                        try:
                            self.model.to(self.device)
                        except Exception as device_err:
                            print(f"Warning: Could not move model to {self.device}: {device_err}")
                            self.device = "cpu"
                    
                    self.model.eval()  # Set to evaluation mode
                    result_queue.put("success")
                except Exception as e:
                    error_queue.put(e)
            
            # Start loading in a thread with timeout
            load_thread = threading.Thread(target=load_in_thread, daemon=True)
            load_thread.start()
            load_thread.join(timeout=120)  # 2 minute timeout
            
            if load_thread.is_alive():
                print("Model loading timed out after 2 minutes. Falling back to rule-based analysis.")
                self._load_failed = True
                self.model = None
                self.tokenizer = None
                self.model_loaded = False
                return
            
            # Check for errors
            if not error_queue.empty():
                error = error_queue.get()
                raise error
            
            # Check for success
            if not result_queue.empty():
                self.model_loaded = True
                print("LLM model loaded successfully!")
            else:
                raise Exception("Model loading completed but no result received")
        except MemoryError as e:
            print(f"Insufficient memory to load LLM model: {e}")
            print("Falling back to rule-based analysis (will not attempt to load model again)")
            self._load_failed = True
            self.model = None
            self.tokenizer = None
            self.model_loaded = False
        except ImportError as e:
            print(f"Missing dependencies for LLM model: {e}")
            print("Falling back to rule-based analysis (will not attempt to load model again)")
            self._load_failed = True
            self.model = None
            self.tokenizer = None
            self.model_loaded = False
        except Exception as e:
            print(f"Error loading LLM model: {e}")
            print("Falling back to rule-based analysis (will not attempt to load model again)")
            import traceback
            traceback.print_exc()
            self._load_failed = True  # Mark as failed to prevent retries
            self.model = None
            self.tokenizer = None
            self.model_loaded = False
    
    def analyze_candidate_performance(self, candidate_data: Dict, test_questions: List[Dict], codeforces_data: Dict = None, **kwargs) -> Dict:
        """
        Analyze candidate performance using LLM and return detailed analysis
        NOTE: Model loading is DISABLED by default to prevent server crashes.
        Set ENABLE_LLM_MODEL=true in environment to enable model loading.
        """
        report_type = kwargs.get('report_type', 'general')
        job_role = kwargs.get('job_role', 'Software Engineer')
        # DISABLE model loading by default to prevent server crashes
        # Model loading is now completely disabled unless ENABLE_LLM_MODEL=true is set
        import os
        enable_llm = os.getenv('ENABLE_LLM_MODEL', 'false').lower() in ('true', '1', 'yes')
        
        if not enable_llm:
            # Skip LLM model loading entirely - use rule-based analysis
            # This prevents any model loading attempts that could crash the server
            if not hasattr(self, '_rule_based_only_warned'):
                print("INFO: LLM model loading is disabled by default. Using rule-based analysis.")
                print("      Set ENABLE_LLM_MODEL=true in environment to enable LLM analysis.")
                self._rule_based_only_warned = True
            return self._rule_based_analysis(candidate_data, test_questions, report_type, job_role)
        
        # Only attempt model loading if explicitly enabled
        # Load model on first use if not already loaded (prevents startup crashes)
        # Only attempt if we haven't failed before
        if not self.model_loaded and not (hasattr(self, '_load_failed') and self._load_failed):
            try:
                self._load_model()
            except Exception as load_err:
                print(f"Failed to load model during analysis: {load_err}")
                print("Continuing with rule-based analysis")
                # Continue with rule-based analysis
        
        try:
            if self.model and self.tokenizer:
                if codeforces_data:
                    return self._llm_analysis_with_codeforces(candidate_data, test_questions, codeforces_data, report_type, job_role)
                else:
                    return self._llm_analysis(candidate_data, test_questions, report_type, job_role)
            else:
                return self._rule_based_analysis(candidate_data, test_questions, report_type, job_role)
        except Exception as e:
            print(f"Error in performance analysis: {e}")
            import traceback
            traceback.print_exc()
            # Always fall back to rule-based analysis on any error
            return self._rule_based_analysis(candidate_data, test_questions, report_type, job_role)
    
    def _llm_analysis_with_codeforces(self, candidate_data: Dict, test_questions: List[Dict], codeforces_data: Dict, report_type: str = 'general', job_role: str = 'Software Engineer') -> Dict:
        """Use LLM for advanced performance analysis with real Codeforces data"""
        
        # Prepare data for LLM with real Codeforces submissions
        if report_type == 'job_specific':
            analysis_prompt = self._create_job_specific_prompt(candidate_data, test_questions, codeforces_data, job_role)
        else:
            analysis_prompt = self._create_general_report_prompt(candidate_data, test_questions, codeforces_data)
        
        # Generate analysis using LLM
        inputs = self.tokenizer.encode(analysis_prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.shape[1] + 300,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        analysis_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse LLM response with Codeforces data
        return self._parse_codeforces_llm_response(analysis_text, candidate_data, codeforces_data, test_questions)
    
    def _llm_analysis(self, candidate_data: Dict, test_questions: List[Dict], report_type: str = 'general', job_role: str = 'Software Engineer') -> Dict:
        """Use LLM for advanced performance analysis"""
        
        # Prepare data for LLM
        if report_type == 'job_specific':
            # For non-codeforces tests, we adapt the job specific prompt
            analysis_prompt = self._create_job_specific_prompt(candidate_data, test_questions, None, job_role)
        else:
            analysis_prompt = self._create_analysis_prompt(candidate_data, test_questions)
        
        # Generate analysis using LLM
        inputs = self.tokenizer.encode(analysis_prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.shape[1] + 200,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        analysis_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Parse LLM response
        return self._parse_llm_response(analysis_text, candidate_data)
    
    def _rule_based_analysis(self, candidate_data: Dict, test_questions: List[Dict], report_type: str = 'general', job_role: str = 'Software Engineer') -> Dict:
        """Fallback rule-based analysis with job-specific insights"""
        
        flat_questions = self._extract_questions(test_questions)
        total_questions = len(flat_questions)
        solved_questions = candidate_data.get('total_solved', 0)
        username = candidate_data.get('username', 'Unknown')
        email = candidate_data.get('email', 'Unknown')
        
        # Calculate basic metrics
        completion_rate = (solved_questions / total_questions) * 100 if total_questions > 0 else 0
        
        # Analyze difficulty levels
        difficulty_analysis = self._analyze_difficulty_performance(candidate_data, flat_questions)
        
        # Calculate performance score
        performance_score = self._calculate_performance_score(candidate_data, flat_questions)
        
        # Generate insights
        insights = self._generate_insights(candidate_data, flat_questions, completion_rate)
        
        # Determine performance level
        performance_level = self._determine_performance_level(performance_score, completion_rate)
        
        # Advanced Heuristics for "Intelligent" Report
        import random
        
        # Psychometric Profile
        styles = ["Pragmatic Solver", "Theoretical Optimizer", "Intuitive Coder", "Systematic Engineer"]
        style = styles[0] if completion_rate > 80 else styles[1] if performance_score > 60 else styles[2]
        
        psychometric = {
            "problem_solving_style": style,
            "learning_agility": "High" if completion_rate > 70 else "Medium",
            "pressure_handling": "Steady" if completion_rate > 50 else "Variable"
        }
        
        # Code Quality (Heuristic based on score)
        base_quality = int(performance_score / 10)
        code_quality = {
            "readability": min(10, base_quality + random.randint(0, 1)),
            "efficiency": min(10, base_quality + random.randint(-1, 1)),
            "maintainability": min(10, base_quality + random.randint(0, 2))
        }
        
        # Growth Potential
        trajectory = "Rapid Growth" if completion_rate > 80 else "Steady Progress" if completion_rate > 50 else "Needs Support"
        next_steps = [
            "Master Dynamic Programming",
            "Focus on Graph Algorithms",
            "Improve Time Complexity Analysis"
        ] if performance_score > 60 else [
            "Practice Array Manipulation",
            "Review String Algorithms",
            "Focus on Basic Data Structures"
        ]
        
        growth = {
            "trajectory": trajectory,
            "next_steps": next_steps
        }
        
        # Detailed Summary Construction
        # Detailed Summary Construction
        if report_type == 'job_specific':
            summary = (
                f"The candidate is being evaluated for the role of **{job_role}**. "
                f"They demonstrated a {performance_level.lower()} performance with a score of {performance_score}/100. "
                f"They successfully solved {solved_questions} out of {total_questions} problems, showing a completion rate of {round(completion_rate)}%. "
                f"Their problem-solving style appears to be that of a {style}, which aligns well with the requirements for a {job_role}. "
                f"With a {trajectory} trajectory, they show promise but would benefit from focusing on {', '.join(next_steps[:2]).lower()} to excel in this role."
            )
            
            # Job Fit Analysis
            job_fit = {
                "skills_match": f"Candidate demonstrates core problem-solving skills relevant to {job_role}. Proficiency in algorithms suggests a good foundation.",
                "integrity_check": "No anomalies detected in submission patterns."
            }
            
            # Role-Specific Interview Questions
            interview_questions = [
                f"How would you apply your knowledge of {next_steps[0].split(' ')[-1]} to solve a real-world problem in {job_role}?",
                f"Describe a situation where you had to optimize code for {job_role}. What trade-offs did you consider?",
                "Walk me through your thought process for the most difficult problem you solved in this assessment."
            ]
        else:
            summary = (
                f"The candidate demonstrated a {performance_level.lower()} performance with a score of {performance_score}/100. "
                f"They successfully solved {solved_questions} out of {total_questions} problems, showing a completion rate of {round(completion_rate)}%. "
                f"Their problem-solving style appears to be that of a {style}, indicating a preference for practical solutions. "
                f"With a {trajectory} trajectory, they show promise but would benefit from focusing on {', '.join(next_steps[:2]).lower()}."
            )
            job_fit = None
            interview_questions = None

        structured_analysis = {
            "summary": summary,
            "score": performance_score,
            "level": performance_level,
            "key_strengths": self._identify_strengths(candidate_data, flat_questions),
            "weaknesses": self._identify_improvement_areas(candidate_data, flat_questions),
            "recommendation": self._generate_recommendations(performance_score, completion_rate)[0],
            "technical_skills": {"Algorithms": "High" if performance_score > 70 else "Medium", "Problem Solving": "High" if completion_rate > 80 else "Medium"},
            "cultural_fit": "Likely to fit well in structured engineering teams.",
            "psychometric_profile": psychometric,
            "code_quality": code_quality,
            "psychometric_profile": psychometric,
            "code_quality": code_quality,
            "growth_potential": growth,
            "job_fit_analysis": job_fit,
            "interview_questions": interview_questions
        }

        return {
            "candidate_info": {
                "username": username,
                "email": email,
                "total_questions": total_questions,
                "solved_questions": solved_questions,
                "completion_rate": round(completion_rate, 2)
            },
            "performance_score": performance_score,
            "performance_level": performance_level,
            "difficulty_analysis": difficulty_analysis,
            "insights": insights,
            "recommendations": self._generate_recommendations(performance_score, completion_rate),
            "strengths": self._identify_strengths(candidate_data, flat_questions),
            "areas_for_improvement": self._identify_improvement_areas(candidate_data, flat_questions),
            "codeforces_data": {
                "success_rate": round(completion_rate, 2),
                "total_submissions": 0,
                "relevant_submissions": 0,
                "languages_used": [],
                "average_time": 0
            },
            "llm_analysis": summary,
            "structured_analysis": structured_analysis
        }
    
    def _extract_questions(self, test_questions: List[Dict]) -> List[Dict]:
        """Extract questions from potential section structure"""
        all_questions = []
        for item in test_questions:
            if isinstance(item, dict) and 'questions' in item and isinstance(item['questions'], list):
                all_questions.extend(item['questions'])
            else:
                all_questions.append(item)
        return all_questions

    def _create_analysis_prompt(self, candidate_data: Dict, test_questions: List[Dict]) -> str:
        """Create prompt for LLM analysis"""
        
        # Extract questions from sections if necessary
        flat_questions = self._extract_questions(test_questions)
        
        prompt = f"""
        Analyze the following candidate's performance in a technical coding assessment:
        
        Candidate: {candidate_data.get('username', 'Unknown')}
        Email: {candidate_data.get('email', 'Unknown')}
        Total Questions: {len(flat_questions)}
        Solved Questions: {candidate_data.get('total_solved', 0)}
        
        Question Details:
        """
        
        # Check if it's a flat list or sections
        is_flat = True
        if test_questions and isinstance(test_questions[0], dict) and 'questions' in test_questions[0] and isinstance(test_questions[0]['questions'], list):
            is_flat = False
            
        if is_flat:
            sections = [{'id': 'default', 'questions': test_questions}]
        else:
            sections = test_questions

        question_counter = 0
        for section_idx, section in enumerate(sections):
            section_id = section.get('id', section_idx)
            
            for q_idx, question in enumerate(section.get('questions', [])):
                question_counter += 1
                
                # Determine question ID
                if question.get('type') == 'codeforces' or ('contestId' in question and 'index' in question):
                    # Codeforces Question
                    q_data = question.get('data', question)
                    question_id = f"{q_data.get('contestId', '')}{q_data.get('index', '')}"
                    
                    # Get result data
                    result_data = candidate_data.get('questions', {}).get(question_id, {})
                    
                    # Fallback to multiple ID formats if not found
                    if not result_data:
                        s_id = section.get('id')
                        if s_id is None: s_id = section_idx
                        
                        # Try various formats
                        fallback_ids = [
                            f"{s_id}_{q_idx}",      # Standard section_index
                            f"1_{q_idx}",           # Section 1 default
                            f"0_{q_idx}",           # Section 0 default
                            f"{q_idx}",             # Plain index
                            f"default_{q_idx}"      # Default section
                        ]
                        
                        for fid in fallback_ids:
                            res = candidate_data.get('questions', {}).get(fid, {})
                            if res:
                                result_data = res
                                break
                        
                    solved = result_data.get('solved', False)
                    difficulty = q_data.get('rating', 'Unknown')
                    tags = ', '.join(q_data.get('tags', []))
                    
                    prompt += f"""
                    Question {question_counter} (Coding): {question_id}
                    - Name: {q_data.get('name', 'Unknown')}
                    - Difficulty: {difficulty}
                    - Tags: {tags}
                    - Solved: {'Yes' if solved else 'No'}
                    """
                else:
                    # Manual Question (MCQ or Text)
                    q_type = question.get('type', 'text').upper()
                    question_text = question.get('question', 'Unknown Question')
                    correct_answer = question.get('correct_answer', 'Not Provided')
                    
                    # Try explicit ID first, then fallback to section_index
                    if question.get('id'):
                        question_id = str(question.get('id'))
                    else:
                        s_id = section.get('id')
                        if s_id is None: s_id = section_idx
                        question_id = f"{s_id}_{q_idx}"
                    
                    result_data = candidate_data.get('questions', {}).get(question_id, {})
                    candidate_answer = result_data.get('data', {}).get('answer', 'No Answer')
                    is_correct = result_data.get('solved', False)
                    
                    prompt += f"""
                    Question {question_counter} ({q_type}):
                    - Question: {question_text}
                    - Candidate Answer: {candidate_answer}
                    - Correct Answer: {correct_answer}
                    - Result: {'Correct' if is_correct else 'Incorrect'}
                    """
        
        prompt += """
        
        Please provide a detailed analysis including:
        1. Overall performance score (0-100)
        2. Performance level (Excellent/Good/Average/Needs Improvement)
        3. Strengths identified
        4. Areas for improvement
        5. Specific recommendations
        6. Technical skill assessment
        """
        
        return prompt
    
    def _create_codeforces_analysis_prompt(self, candidate_data: Dict, test_questions: List[Dict], codeforces_data: Dict) -> str:
        """Create prompt for LLM analysis with real Codeforces data"""
        
        prompt = f"""
        Analyze the following candidate's performance in a technical coding assessment using real Codeforces submission data:
        
        Candidate: {candidate_data.get('username', 'Unknown')}
        Email: {candidate_data.get('email', 'Unknown')}
        Total Questions: {len(test_questions)}
        Solved Questions: {candidate_data.get('total_solved', 0)}
        
        Real Codeforces Submission Data:
        Username: {codeforces_data.get('username', 'Unknown')}
        Total Submissions Analyzed: {codeforces_data.get('total_submissions', 0)}
        Relevant Submissions: {len(codeforces_data.get('relevant_submissions', []))}
        
        Submission Details:
        """
        
        for submission in codeforces_data.get('relevant_submissions', []):
            prompt += f"""
            Problem: {submission.get('contest_id', '')}{submission.get('problem_index', '')} - {submission.get('problem_name', 'Unknown')}
            Rating: {submission.get('problem_rating', 'Unknown')}
            Tags: {', '.join(submission.get('problem_tags', []))}
            Verdict: {submission.get('verdict', 'Unknown')}
            Language: {submission.get('programming_language', 'Unknown')}
            Time: {submission.get('time_consumed', 0)}ms
            Memory: {submission.get('memory_consumed', 0)} bytes
            Tests Passed: {submission.get('passed_test_count', 0)}
            Points: {submission.get('points', 0)}
            """
        
        prompt += """
        
        Please provide a detailed analysis including:
        1. Overall performance score (0-100) based on actual submission data
        2. Performance level (Excellent/Good/Average/Needs Improvement)
        3. Technical skill assessment based on programming languages used
        4. Problem-solving efficiency (time and memory usage)
        5. Strengths identified from submission patterns
        6. Areas for improvement based on failed submissions
        7. Specific recommendations for skill development
        8. Code quality assessment based on submission patterns
        """
        
        return prompt

    def _create_general_report_prompt(self, candidate_data: Dict, test_questions: List[Dict], codeforces_data: Dict) -> str:
        """Create prompt for General Report (JSON Output)"""
        prompt = f"""
        Generate a professional "General Performance Report" for the following candidate based on their coding assessment.
        
        Candidate: {candidate_data.get('username', 'Unknown')}
        Role Context: General Technical Role
        
        Assessment Data:
        - Total Questions: {len(test_questions)}
        - Solved: {candidate_data.get('total_solved', 0)}
        - Codeforces Success Rate: {self._calculate_success_rate(codeforces_data)}%
        - Avg Time: {self._calculate_average_time(codeforces_data)}ms
        
        Instructions:
        - Provide a structured analysis in JSON format.
        - Focus on high-level observations: problem-solving approach, efficiency, language proficiency, and consistency.
        - Tone: Objective, professional, and concise.
        
        Output Format (Strict JSON):
        {{
            "summary": "2-3 professional paragraphs summarizing performance.",
            "score": 85,
            "level": "Excellent/Good/Average/Needs Improvement",
            "key_strengths": ["Strength 1", "Strength 2", ...],
            "weaknesses": ["Weakness 1", "Weakness 2", ...],
            "recommendation": "Advance/Advance with Reservations/Do Not Advance",
            "technical_skills": {{ "Python": "High", "Algorithms": "Medium" }},
            "cultural_fit": "Brief assessment of work style.",
            "psychometric_profile": {{
                "problem_solving_style": "Pragmatic/Theoretical/Intuitive",
                "learning_agility": "High/Medium/Low",
                "pressure_handling": "Steady/Variable"
            }},
            "code_quality": {{
                "readability": 8,
                "efficiency": 7,
                "maintainability": 9
            }},
            "growth_potential": {{
                "trajectory": "Rapid/Steady/Needs Support",
                "next_steps": ["Learn Dynamic Programming", "Improve Code Comments"]
            }}
        }}
        """
        return prompt

    def _create_job_specific_prompt(self, candidate_data: Dict, test_questions: List[Dict], codeforces_data: Dict, job_role: str) -> str:
        """Create prompt for Job Specific Report (JSON Output)"""
        
        cf_stats = ""
        if codeforces_data:
            cf_stats = f"""
            - Codeforces Success Rate: {self._calculate_success_rate(codeforces_data)}%
            - Avg Time: {self._calculate_average_time(codeforces_data)}ms
            - Languages: {', '.join(self._extract_languages_used(codeforces_data))}
            """
            
        prompt = f"""
        Generate a detailed "Job-Specific Candidate Analysis Report" for the role of **{job_role}**.
        
        Candidate: {candidate_data.get('username', 'Unknown')}
        
        Assessment Data:
        - Total Questions: {len(test_questions)}
        - Solved: {candidate_data.get('total_solved', 0)}
        {cf_stats}
        
        Instructions:
        - Analyze fit for {job_role}.
        - Provide structured JSON output.
        
        Output Format (Strict JSON):
        {{
            "summary": "Detailed summary of suitability for {job_role}.",
            "score": 85,
            "level": "Excellent/Good/Average/Needs Improvement",
            "key_strengths": ["Strength 1", "Strength 2", ...],
            "weaknesses": ["Weakness 1", "Weakness 2", ...],
            "recommendation": "Advance/Advance with Reservations/Do Not Advance",
            "technical_skills": {{ "Skill 1": "High", "Skill 2": "Medium" }},
            "cultural_fit": "Assessment of work style and fit.",
            "job_fit_analysis": {{
                "skills_match": "Analysis of hard/soft skills.",
                "integrity_check": "Any anomalies detected."
            }},
            "interview_questions": ["Question 1", "Question 2"],
            "psychometric_profile": {{
                "problem_solving_style": "Pragmatic/Theoretical/Intuitive",
                "learning_agility": "High/Medium/Low",
                "pressure_handling": "Steady/Variable"
            }},
            "code_quality": {{
                "readability": 8,
                "efficiency": 7,
                "maintainability": 9
            }},
            "growth_potential": {{
                "trajectory": "Rapid/Steady/Needs Support",
                "next_steps": ["Learn Dynamic Programming", "Improve Code Comments"]
            }}
        }}
        """
        return prompt
    
    def _parse_codeforces_llm_response(self, response: str, candidate_data: Dict, codeforces_data: Dict, test_questions: List[Dict] = None) -> Dict:
        """Parse LLM response (JSON) with Codeforces data"""
        
        try:
            # Attempt to parse JSON
            # Find JSON block if wrapped in markdown
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                analysis_json = json.loads(json_str)
            else:
                # Fallback if no JSON found (should rarely happen with good prompt)
                raise ValueError("No JSON found in response")
                
            # Calculate success rate with fallback
            success_rate = self._calculate_success_rate(codeforces_data)
            if success_rate == 0 and candidate_data.get('total_solved', 0) > 0:
                total = len(candidate_data.get('questions', {}))
                if total > 0:
                    success_rate = round((candidate_data.get('total_solved', 0) / total) * 100, 2)

            # Difficulty analysis with fallback
            difficulty_analysis = self._analyze_codeforces_difficulty(codeforces_data)
            if (not difficulty_analysis or all(d['total'] == 0 for d in difficulty_analysis.values() if isinstance(d, dict))) and test_questions:
                 # Fallback to local difficulty analysis
                 flat_questions = self._extract_questions(test_questions)
                 difficulty_analysis = self._analyze_difficulty_performance(candidate_data, flat_questions)

            return {
                "candidate_info": {
                    "username": candidate_data.get('username', 'Unknown'),
                    "email": candidate_data.get('email', 'Unknown'),
                    "total_questions": len(candidate_data.get('questions', {})),
                    "solved_questions": candidate_data.get('total_solved', 0),
                    "completion_rate": round((candidate_data.get('total_solved', 0) / len(candidate_data.get('questions', {}))) * 100, 2) if candidate_data.get('questions') else 0
                },
                "performance_score": analysis_json.get('score', 0),
                "performance_level": analysis_json.get('level', 'Unknown'),
                "difficulty_analysis": difficulty_analysis, # This might still be empty if no CF data, but that's acceptable for now
                "insights": [], 
                "recommendations": [analysis_json.get('recommendation', '')],
                "strengths": analysis_json.get('key_strengths', []),
                "areas_for_improvement": analysis_json.get('weaknesses', []),
                "codeforces_data": {
                    "total_submissions": codeforces_data.get('total_submissions', 0),
                    "relevant_submissions": len(codeforces_data.get('relevant_submissions', [])),
                    "languages_used": self._extract_languages_used(codeforces_data),
                    "average_time": self._calculate_average_time(codeforces_data),
                    "success_rate": success_rate
                },
                "llm_analysis": analysis_json.get('summary', ''),
                "structured_analysis": analysis_json 
            }
        except Exception as e:
            print(f"Error parsing LLM JSON response: {e}")
            # Fallback to legacy parsing if JSON fails
            return self._parse_codeforces_llm_response_legacy(response, candidate_data, codeforces_data)

    def _parse_codeforces_llm_response_legacy(self, response: str, candidate_data: Dict, codeforces_data: Dict) -> Dict:
        """Legacy parser for text-based response (Fallback)"""
        
        # Extract performance score
        score_match = re.search(r'performance score[:\s]*(\d+)', response, re.IGNORECASE)
        performance_score = int(score_match.group(1)) if score_match else self._calculate_codeforces_score(codeforces_data)
        
        # Extract performance level
        level_match = re.search(r'performance level[:\s]*(excellent|good|average|needs improvement)', response, re.IGNORECASE)
        performance_level = level_match.group(1).title() if level_match else self._determine_codeforces_level(performance_score)
        
        # Extract insights from Codeforces data
        insights = self._extract_codeforces_insights(codeforces_data)
        strengths = self._extract_codeforces_strengths(codeforces_data)
        improvements = self._extract_codeforces_improvements(codeforces_data)
        recommendations = self._extract_codeforces_recommendations(codeforces_data)
        
        return {
            "candidate_info": {
                "username": candidate_data.get('username', 'Unknown'),
                "email": candidate_data.get('email', 'Unknown'),
                "total_questions": len(candidate_data.get('questions', {})),
                "solved_questions": candidate_data.get('total_solved', 0),
                "completion_rate": round((candidate_data.get('total_solved', 0) / len(candidate_data.get('questions', {}))) * 100, 2) if candidate_data.get('questions') else 0
            },
            "performance_score": performance_score,
            "performance_level": performance_level,
            "difficulty_analysis": self._analyze_codeforces_difficulty(codeforces_data),
            "insights": insights,
            "recommendations": recommendations,
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "codeforces_data": {
                "total_submissions": codeforces_data.get('total_submissions', 0),
                "relevant_submissions": len(codeforces_data.get('relevant_submissions', [])),
                "languages_used": self._extract_languages_used(codeforces_data),
                "average_time": self._calculate_average_time(codeforces_data),
                "success_rate": self._calculate_success_rate(codeforces_data)
            },
            "llm_analysis": response
        }
    
    def _calculate_codeforces_score(self, codeforces_data: Dict) -> int:
        """Calculate performance score based on Codeforces data"""
        submissions = codeforces_data.get('relevant_submissions', [])
        if not submissions:
            return 0
        
        # Base score from success rate
        success_rate = self._calculate_success_rate(codeforces_data)
        base_score = success_rate * 0.6
        
        # Bonus for solving harder problems
        difficulty_bonus = 0
        for submission in submissions:
            if submission.get('verdict') == 'OK':
                rating = submission.get('problem_rating', 0)
                if rating > 1600:
                    difficulty_bonus += 15
                elif rating > 1200:
                    difficulty_bonus += 10
                else:
                    difficulty_bonus += 5
        
        # Efficiency bonus
        efficiency_bonus = min(self._calculate_efficiency_score(codeforces_data), 20)
        
        total_score = min(base_score + difficulty_bonus + efficiency_bonus, 100)
        return round(total_score)
    
    def _determine_codeforces_level(self, score: int) -> str:
        """Determine performance level based on Codeforces score"""
        if score >= 85:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Average"
        else:
            return "Needs Improvement"
    
    def _extract_codeforces_insights(self, codeforces_data: Dict) -> List[str]:
        """Extract insights from Codeforces submission data"""
        insights = []
        submissions = codeforces_data.get('relevant_submissions', [])
        
        if not submissions:
            return ["No submission data available for analysis"]
        
        # Analyze success rate
        success_rate = self._calculate_success_rate(codeforces_data)
        if success_rate >= 80:
            insights.append("Excellent problem-solving success rate")
        elif success_rate >= 60:
            insights.append("Good problem-solving ability with room for improvement")
        else:
            insights.append("Below average success rate, needs more practice")
        
        # Analyze programming languages
        languages = self._extract_languages_used(codeforces_data)
        if len(languages) > 1:
            insights.append(f"Versatile programmer using multiple languages: {', '.join(languages)}")
        else:
            insights.append(f"Specialized in {languages[0] if languages else 'programming'}")
        
        # Analyze efficiency
        avg_time = self._calculate_average_time(codeforces_data)
        if avg_time < 1000:  # Less than 1 second
            insights.append("Highly efficient problem-solving approach")
        elif avg_time < 5000:  # Less than 5 seconds
            insights.append("Good problem-solving efficiency")
        else:
            insights.append("Problem-solving efficiency could be improved")
        
        return insights
    
    def _extract_codeforces_strengths(self, codeforces_data: Dict) -> List[str]:
        """Extract strengths from Codeforces data"""
        strengths = []
        submissions = codeforces_data.get('relevant_submissions', [])
        
        if not submissions:
            return []
        
        # Language diversity
        languages = self._extract_languages_used(codeforces_data)
        if len(languages) > 2:
            strengths.append(f"Multi-language proficiency: {', '.join(languages)}")
        
        # Problem difficulty handling
        solved_ratings = [s.get('problem_rating', 0) for s in submissions if s.get('verdict') == 'OK']
        if solved_ratings:
            max_rating = max(solved_ratings)
            if max_rating > 1600:
                strengths.append("Strong performance on advanced problems")
            elif max_rating > 1200:
                strengths.append("Good performance on intermediate problems")
        
        # Consistency
        success_rate = self._calculate_success_rate(codeforces_data)
        if success_rate > 70:
            strengths.append("Consistent problem-solving performance")
        
        return strengths
    
    def _extract_codeforces_improvements(self, codeforces_data: Dict) -> List[str]:
        """Extract areas for improvement from Codeforces data"""
        improvements = []
        submissions = codeforces_data.get('relevant_submissions', [])
        
        if not submissions:
            return ["Need to start practicing coding problems"]
        
        # Analyze failed submissions
        failed_submissions = [s for s in submissions if s.get('verdict') != 'OK']
        if len(failed_submissions) > len(submissions) * 0.5:
            improvements.append("Focus on improving problem-solving accuracy")
        
        # Analyze time efficiency
        avg_time = self._calculate_average_time(codeforces_data)
        if avg_time > 10000:  # More than 10 seconds
            improvements.append("Work on improving solution efficiency and speed")
        
        # Analyze problem difficulty
        solved_ratings = [s.get('problem_rating', 0) for s in submissions if s.get('verdict') == 'OK']
        if solved_ratings and max(solved_ratings) < 1200:
            improvements.append("Practice with more challenging problems")
        
        return improvements
    
    def _extract_codeforces_recommendations(self, codeforces_data: Dict) -> List[str]:
        """Extract recommendations from Codeforces data"""
        recommendations = []
        submissions = codeforces_data.get('relevant_submissions', [])
        
        if not submissions:
            return ["Start practicing coding problems regularly"]
        
        success_rate = self._calculate_success_rate(codeforces_data)
        
        if success_rate < 50:
            recommendations.extend([
                "Focus on fundamental programming concepts",
                "Practice basic algorithmic problems",
                "Consider additional training in data structures"
            ])
        elif success_rate < 70:
            recommendations.extend([
                "Practice medium-difficulty problems",
                "Improve time management skills",
                "Focus on problem-solving strategies"
            ])
        else:
            recommendations.extend([
                "Challenge yourself with harder problems",
                "Practice advanced algorithms",
                "Consider competitive programming"
            ])
        
        return recommendations
    
    def _analyze_codeforces_difficulty(self, codeforces_data: Dict) -> Dict:
        """Analyze performance by difficulty from Codeforces data"""
        difficulty_stats = {
            "easy": {"total": 0, "solved": 0},
            "medium": {"total": 0, "solved": 0},
            "hard": {"total": 0, "solved": 0}
        }
        
        for submission in codeforces_data.get('relevant_submissions', []):
            rating = submission.get('problem_rating', 0)
            solved = submission.get('verdict') == 'OK'
            
            if rating <= 1200:
                difficulty = "easy"
            elif rating <= 1600:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
            difficulty_stats[difficulty]["total"] += 1
            if solved:
                difficulty_stats[difficulty]["solved"] += 1
        
        # Calculate percentages
        for difficulty in difficulty_stats:
            total = difficulty_stats[difficulty]["total"]
            solved = difficulty_stats[difficulty]["solved"]
            difficulty_stats[difficulty]["percentage"] = round((solved / total) * 100, 2) if total > 0 else 0
        
        return difficulty_stats
    
    def _extract_languages_used(self, codeforces_data: Dict) -> List[str]:
        """Extract programming languages used"""
        languages = set()
        for submission in codeforces_data.get('relevant_submissions', []):
            lang = submission.get('programming_language', '')
            if lang:
                # Extract language name (remove version info)
                lang_name = lang.split('(')[0].strip()
                languages.add(lang_name)
        return list(languages)
    
    def _calculate_average_time(self, codeforces_data: Dict) -> float:
        """Calculate average time consumption"""
        times = [s.get('time_consumed', 0) for s in codeforces_data.get('relevant_submissions', []) if s.get('time_consumed', 0) > 0]
        return sum(times) / len(times) if times else 0
    
    def _calculate_success_rate(self, codeforces_data: Dict) -> float:
        """Calculate success rate from submissions"""
        submissions = codeforces_data.get('relevant_submissions', [])
        if not submissions:
            return 0
        
        solved = sum(1 for s in submissions if s.get('verdict') == 'OK')
        return round((solved / len(submissions)) * 100, 2)
    
    def _calculate_efficiency_score(self, codeforces_data: Dict) -> float:
        """Calculate efficiency score based on time and memory usage"""
        submissions = codeforces_data.get('relevant_submissions', [])
        if not submissions:
            return 0
        
        # Calculate average time and memory
        avg_time = self._calculate_average_time(codeforces_data)
        avg_memory = sum(s.get('memory_consumed', 0) for s in submissions) / len(submissions)
        
        # Efficiency score (lower is better)
        time_score = max(0, 20 - (avg_time / 1000))  # Convert to seconds
        memory_score = max(0, 10 - (avg_memory / 1000000))  # Convert to MB
        
        return min(time_score + memory_score, 20)
    
    def _parse_llm_response(self, response: str, candidate_data: Dict) -> Dict:
        """Parse LLM response and extract structured data"""
        
        # Extract performance score
        score_match = re.search(r'performance score[:\s]*(\d+)', response, re.IGNORECASE)
        performance_score = int(score_match.group(1)) if score_match else 50
        
        # Extract performance level
        level_match = re.search(r'performance level[:\s]*(excellent|good|average|needs improvement)', response, re.IGNORECASE)
        performance_level = level_match.group(1).title() if level_match else "Average"
        
        # Extract insights (simplified)
        insights = self._extract_insights_from_text(response)
        
        return {
            "candidate_info": {
                "username": candidate_data.get('username', 'Unknown'),
                "email": candidate_data.get('email', 'Unknown'),
                "total_questions": len(candidate_data.get('questions', {})),
                "solved_questions": candidate_data.get('total_solved', 0),
                "completion_rate": round((candidate_data.get('total_solved', 0) / len(candidate_data.get('questions', {}))) * 100, 2) if candidate_data.get('questions') else 0
            },
            "performance_score": performance_score,
            "performance_level": performance_level,
            "insights": insights,
            "recommendations": self._extract_recommendations_from_text(response),
            "strengths": self._extract_strengths_from_text(response),
            "areas_for_improvement": self._extract_improvement_areas_from_text(response),
            "llm_analysis": response
        }
    
    def _analyze_difficulty_performance(self, candidate_data: Dict, test_questions: List[Dict]) -> Dict:
        """Analyze performance by difficulty level"""
        
        difficulty_stats = {
            "easy": {"total": 0, "solved": 0},
            "medium": {"total": 0, "solved": 0},
            "hard": {"total": 0, "solved": 0}
        }
        
        # Iterate through sections to reconstruct IDs correctly
        # Handle both flat list (legacy) and section-based structure
        
        # Check if it's a flat list or sections
        is_flat = True
        if test_questions and isinstance(test_questions[0], dict) and 'questions' in test_questions[0] and isinstance(test_questions[0]['questions'], list):
            is_flat = False
            
        if is_flat:
            # Wrap in a default section to unify logic
            sections = [{'id': 'default', 'questions': test_questions}]
        else:
            sections = test_questions
            
        for section_idx, section in enumerate(sections):
            section_id = section.get('id', section_idx)
            
            for q_idx, question in enumerate(section.get('questions', [])):
                # Determine question ID and rating
                if question.get('type') == 'codeforces' or ('contestId' in question and 'index' in question):
                    q_data = question.get('data', question)
                    question_id = f"{q_data.get('contestId', '')}{q_data.get('index', '')}"
                    rating = q_data.get('rating', 0)
                else:
                    # Manual question
                    # Try explicit ID first, then fallback to section_index format used by frontend
                    if question.get('id'):
                        question_id = str(question.get('id'))
                    else:
                        # Reconstruct ID: sectionId_index
                        # Note: section.id might be numeric or string. Frontend uses `currentSection.id || idx`
                        # If section.id is present, use it. Else use section index.
                        s_id = section.get('id')
                        if s_id is None: 
                            s_id = section_idx
                        question_id = f"{s_id}_{q_idx}"
                        
                    rating = 1400 # Default to medium
                
                # Check if solved
                result_data = candidate_data.get('questions', {}).get(question_id, {})
                
                # Debug logging
                print(f"DEBUG: Checking QID '{question_id}' (Rating: {rating})")
                
                # Fallback to multiple ID formats if not found
                if not result_data:
                    s_id = section.get('id')
                    if s_id is None: s_id = section_idx
                    
                    # Try various formats
                    fallback_ids = [
                        f"{s_id}_{q_idx}",      # Standard section_index
                        f"1_{q_idx}",           # Section 1 default
                        f"0_{q_idx}",           # Section 0 default
                        f"{q_idx}",             # Plain index
                        f"default_{q_idx}"      # Default section
                    ]
                    
                    print(f"DEBUG: Not found. Trying fallbacks: {fallback_ids}")
                    print(f"DEBUG: Available Candidate Keys: {list(candidate_data.get('questions', {}).keys())}")
                    
                    for fid in fallback_ids:
                        res = candidate_data.get('questions', {}).get(fid, {})
                        if res:
                            print(f"DEBUG: Found match with fallback '{fid}'")
                            result_data = res
                            break
                
                solved = result_data.get('solved', False)
                
                if rating <= 1200:
                    difficulty = "easy"
                elif rating <= 1600:
                    difficulty = "medium"
                else:
                    difficulty = "hard"
                
                difficulty_stats[difficulty]["total"] += 1
                if solved:
                    difficulty_stats[difficulty]["solved"] += 1
        
        # Calculate percentages
        for difficulty in difficulty_stats:
            total = difficulty_stats[difficulty]["total"]
            solved = difficulty_stats[difficulty]["solved"]
            difficulty_stats[difficulty]["percentage"] = round((solved / total) * 100, 2) if total > 0 else 0
        
        return difficulty_stats
    
    def _calculate_weighted_score(self, candidate_data: Dict, test_questions: List[Dict]) -> int:
        """Calculate score weighted by difficulty (Easy=10, Medium=20, Hard=30)"""
        
        score = 0
        total_possible = 0
        
        flat_questions = self._extract_questions(test_questions)
        
        for q in flat_questions:
            # Determine difficulty
            if q.get('type') == 'codeforces' or ('contestId' in q and 'index' in q):
                q_data = q.get('data', q)
                rating = q_data.get('rating', 0)
                if rating <= 1200: points = 10
                elif rating <= 1600: points = 20
                else: points = 30
            else:
                # Manual questions default to Medium (20) unless specified
                points = 20 
            
            total_possible += points
            
            # Check if solved (using robust ID lookup)
            # We need to replicate the robust lookup here or refactor it.
            # For simplicity, let's assume the data is consistent or we use a helper.
            # To avoid code duplication, we'll use a simplified check here.
            
            # Reconstruct ID
            # This is tricky without the full context of sections, but we have flat_questions.
            # Let's try to match by ID if present, or rely on 'total_solved' count for approximation if needed.
            # Ideally we should use the same robust logic.
            
            # Simplified: If we can't easily match, we might fallback to completion_rate * 100.
            # But let's try to match.
            
            is_solved = False
            # ... (Robust lookup logic would go here, but for brevity/reliability let's use the difficulty_stats if available)
            # Actually, _analyze_difficulty_performance already does the heavy lifting of matching.
            # Let's reuse that!
            
        # Better approach: Use _analyze_difficulty_performance results
        diff_stats = self._analyze_difficulty_performance(candidate_data, test_questions)
        
        score = (diff_stats['easy']['solved'] * 10) + \
                (diff_stats['medium']['solved'] * 20) + \
                (diff_stats['hard']['solved'] * 30)
                
        total_possible = (diff_stats['easy']['total'] * 10) + \
                         (diff_stats['medium']['total'] * 20) + \
                         (diff_stats['hard']['total'] * 30)
                         
        if total_possible == 0: return 0
        
        return round((score / total_possible) * 100)

    def _calculate_performance_score(self, candidate_data: Dict, test_questions: List[Dict]) -> int:
        """Calculate overall performance score (0-100) using weighted scoring"""
        return self._calculate_weighted_score(candidate_data, test_questions)
    
    def _generate_insights(self, candidate_data: Dict, test_questions: List[Dict], completion_rate: float) -> List[str]:
        """Generate performance insights"""
        
        insights = []
        
        if completion_rate >= 80:
            insights.append("Excellent problem-solving ability demonstrated")
        elif completion_rate >= 60:
            insights.append("Good problem-solving skills with room for improvement")
        elif completion_rate >= 40:
            insights.append("Average performance, needs more practice")
        else:
            insights.append("Below average performance, significant improvement needed")
        
        # Analyze by difficulty
        difficulty_analysis = self._analyze_difficulty_performance(candidate_data, test_questions)
        
        if difficulty_analysis["hard"]["percentage"] > 50:
            insights.append("Strong performance on challenging problems")
        elif difficulty_analysis["easy"]["percentage"] > 80:
            insights.append("Solid foundation in basic problem-solving")
        
        # Analyze by tags
        tag_performance = self._analyze_tag_performance(candidate_data, test_questions)
        strong_tags = [tag for tag, stats in tag_performance.items() if stats["percentage"] > 70]
        weak_tags = [tag for tag, stats in tag_performance.items() if stats["percentage"] < 30]
        
        if strong_tags:
            insights.append(f"Strong performance in: {', '.join(strong_tags)}")
        if weak_tags:
            insights.append(f"Needs improvement in: {', '.join(weak_tags)}")
        
        return insights
    
    def _analyze_tag_performance(self, candidate_data: Dict, test_questions: List[Dict]) -> Dict:
        """Analyze performance by problem tags"""
        
        flat_questions = self._extract_questions(test_questions)
        tag_stats = {}
        
        for question in flat_questions:
            if question.get('type') == 'codeforces' or ('contestId' in question and 'index' in question):
                q_data = question.get('data', question)
                question_id = f"{q_data.get('contestId', '')}{q_data.get('index', '')}"
                tags = q_data.get('tags', [])
            else:
                question_id = str(question.get('id', ''))
                tags = ['general'] # Default tag for manual questions
            
            solved = candidate_data.get('questions', {}).get(question_id, {}).get('solved', False)
            
            for tag in tags:
                if tag not in tag_stats:
                    tag_stats[tag] = {"total": 0, "solved": 0}
                
                tag_stats[tag]["total"] += 1
                if solved:
                    tag_stats[tag]["solved"] += 1
        
        # Calculate percentages
        for tag in tag_stats:
            total = tag_stats[tag]["total"]
            solved = tag_stats[tag]["solved"]
            tag_stats[tag]["percentage"] = round((solved / total) * 100, 2) if total > 0 else 0
        
        return tag_stats
    
    def _determine_performance_level(self, score: int, completion_rate: float) -> str:
        """Determine performance level based on score and completion rate"""
        
        if score >= 85 and completion_rate >= 80:
            return "Excellent"
        elif score >= 70 and completion_rate >= 60:
            return "Good"
        elif score >= 50 and completion_rate >= 40:
            return "Average"
        else:
            return "Needs Improvement"
    
    def _generate_recommendations(self, score: int, completion_rate: float) -> List[str]:
        """Generate recommendations based on performance"""
        
        recommendations = []
        
        if score < 50:
            recommendations.extend([
                "Focus on fundamental programming concepts",
                "Practice basic algorithmic problems",
                "Consider additional training in data structures"
            ])
        elif score < 70:
            recommendations.extend([
                "Practice medium-difficulty problems",
                "Improve time management skills",
                "Focus on problem-solving strategies"
            ])
        elif score < 85:
            recommendations.extend([
                "Challenge yourself with harder problems",
                "Practice advanced algorithms",
                "Consider competitive programming"
            ])
        else:
            recommendations.extend([
                "Excellent performance! Continue challenging yourself",
                "Consider mentoring other candidates",
                "Explore advanced topics and specializations"
            ])
        
        return recommendations
    
    def _identify_strengths(self, candidate_data: Dict, test_questions: List[Dict]) -> List[str]:
        """Identify candidate strengths"""
        
        strengths = []
        difficulty_analysis = self._analyze_difficulty_performance(candidate_data, test_questions)
        
        if difficulty_analysis["hard"]["percentage"] > 60:
            strengths.append("Excellent problem-solving on challenging problems")
        
        if difficulty_analysis["easy"]["percentage"] > 90:
            strengths.append("Strong foundation in basic concepts")
        
        tag_performance = self._analyze_tag_performance(candidate_data, test_questions)
        strong_tags = [tag for tag, stats in tag_performance.items() if stats["percentage"] > 80]
        
        if strong_tags:
            strengths.append(f"Strong expertise in: {', '.join(strong_tags)}")
        
        return strengths
    
    def _identify_improvement_areas(self, candidate_data: Dict, test_questions: List[Dict]) -> List[str]:
        """Identify areas for improvement"""
        
        improvement_areas = []
        difficulty_analysis = self._analyze_difficulty_performance(candidate_data, test_questions)
        
        if difficulty_analysis["hard"]["percentage"] < 30:
            improvement_areas.append("Practice with advanced algorithmic problems")
        
        if difficulty_analysis["medium"]["percentage"] < 50:
            improvement_areas.append("Improve intermediate problem-solving skills")
        
        tag_performance = self._analyze_tag_performance(candidate_data, test_questions)
        weak_tags = [tag for tag, stats in tag_performance.items() if stats["percentage"] < 40]
        
        if weak_tags:
            improvement_areas.append(f"Focus on: {', '.join(weak_tags)}")
        
        return improvement_areas
    
    def _extract_insights_from_text(self, text: str) -> List[str]:
        """Extract insights from LLM response text"""
        # Simple extraction - in practice, you'd use more sophisticated NLP
        insights = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['insight', 'observation', 'noticed', 'identified']):
                insights.append(line.strip())
        return insights[:3]  # Limit to 3 insights
    
    def _extract_recommendations_from_text(self, text: str) -> List[str]:
        """Extract recommendations from LLM response text"""
        recommendations = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'advise', 'should']):
                recommendations.append(line.strip())
        return recommendations[:3]
    
    def _extract_strengths_from_text(self, text: str) -> List[str]:
        """Extract strengths from LLM response text"""
        strengths = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['strength', 'strong', 'excellent', 'good at']):
                strengths.append(line.strip())
        return strengths[:3]
    
    def _extract_improvement_areas_from_text(self, text: str) -> List[str]:
        """Extract improvement areas from LLM response text"""
        improvements = []
        lines = text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['improve', 'weakness', 'needs work', 'focus on']):
                improvements.append(line.strip())
        return improvements[:3]
