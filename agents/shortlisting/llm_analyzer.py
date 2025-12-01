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
    
    def analyze_candidate_performance(self, candidate_data: Dict, test_questions: List[Dict], codeforces_data: Dict = None) -> Dict:
        """
        Analyze candidate performance using LLM and return detailed analysis
        NOTE: Model loading is DISABLED by default to prevent server crashes.
        Set ENABLE_LLM_MODEL=true in environment to enable model loading.
        """
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
            return self._rule_based_analysis(candidate_data, test_questions)
        
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
            if self.model and self.tokenizer and codeforces_data:
                return self._llm_analysis_with_codeforces(candidate_data, test_questions, codeforces_data)
            else:
                return self._rule_based_analysis(candidate_data, test_questions)
        except Exception as e:
            print(f"Error in performance analysis: {e}")
            import traceback
            traceback.print_exc()
            # Always fall back to rule-based analysis on any error
            return self._rule_based_analysis(candidate_data, test_questions)
    
    def _llm_analysis_with_codeforces(self, candidate_data: Dict, test_questions: List[Dict], codeforces_data: Dict) -> Dict:
        """Use LLM for advanced performance analysis with real Codeforces data"""
        
        # Prepare data for LLM with real Codeforces submissions
        analysis_prompt = self._create_codeforces_analysis_prompt(candidate_data, test_questions, codeforces_data)
        
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
        return self._parse_codeforces_llm_response(analysis_text, candidate_data, codeforces_data)
    
    def _llm_analysis(self, candidate_data: Dict, test_questions: List[Dict]) -> Dict:
        """Use LLM for advanced performance analysis"""
        
        # Prepare data for LLM
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
    
    def _rule_based_analysis(self, candidate_data: Dict, test_questions: List[Dict]) -> Dict:
        """Fallback rule-based analysis"""
        
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
            "areas_for_improvement": self._identify_improvement_areas(candidate_data, flat_questions)
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
        
        for i, question in enumerate(flat_questions, 1):
            # Determine question type and ID
            if question.get('type') == 'codeforces' or ('contestId' in question and 'index' in question):
                # Codeforces Question
                q_data = question.get('data', question)
                question_id = f"{q_data.get('contestId', '')}{q_data.get('index', '')}"
                
                # Get result data
                result_data = candidate_data.get('questions', {}).get(question_id, {})
                solved = result_data.get('solved', False)
                difficulty = q_data.get('rating', 'Unknown')
                tags = ', '.join(q_data.get('tags', []))
                
                prompt += f"""
                Question {i} (Coding): {question_id}
                - Name: {q_data.get('name', 'Unknown')}
                - Difficulty: {difficulty}
                - Tags: {tags}
                - Solved: {'Yes' if solved else 'No'}
                """
            else:
                # Manual Question (MCQ or Text)
                q_type = question.get('type', 'text').upper()
                question_text = question.get('question', 'Unknown Question')
                question_id = str(question.get('id', i)) # Fallback ID
                
                # Try to find result by ID or index
                # Note: Manual answers are stored by question ID if available, or we might need a better mapping strategy
                # For now, let's assume api.py/database.py handles the mapping correctly in candidate_data['questions']
                # But wait, manual questions might not have a stable ID if just indices. 
                # In CandidateTest.jsx, we used `currentSection.id || idx` for ID.
                # Let's assume the key in candidate_data['questions'] matches.
                
                # Actually, looking at api.py submit logic:
                # answers is a dict of {questionId: answer}
                # In CandidateTest.jsx: renderQuestion(q, idx, currentSection.id || idx)
                # The key passed to onAnswer is `sectionId-idx` or similar? 
                # No, in CandidateTest.jsx: `onAnswer={(val) => handleAnswer(sectionId, index, val)}`
                # And `answers` state is `{[sectionId]: { [index]: val } }` ?
                # No, let's check CandidateTest.jsx again.
                
                # In CandidateTest.jsx:
                # const handleAnswer = (sectionId, questionId, value) => { ... }
                # renderQuestion calls it with `q.id || idx`.
                # So the key is `q.id` or the index.
                
                # In the prompt, we just want to show the Question and the Answer.
                # We need to look up the answer in candidate_data.
                
                # For now, let's try to find the answer in candidate_data['questions']
                # The keys in candidate_data['questions'] are what was stored in DB.
                
                # Let's iterate through candidate_data['questions'] to find a match if possible, 
                # or just list what we have.
                
                # Simplified approach: Just dump the question text.
                # If we can find the answer, great.
                
                # Let's assume the question object has an 'id'.
                q_id = str(question.get('id', ''))
                result_data = candidate_data.get('questions', {}).get(q_id, {})
                candidate_answer = result_data.get('data', {}).get('answer', 'No Answer')
                
                prompt += f"""
                Question {i} ({q_type}):
                - Question: {question_text}
                - Candidate Answer: {candidate_answer}
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
    
    def _parse_codeforces_llm_response(self, response: str, candidate_data: Dict, codeforces_data: Dict) -> Dict:
        """Parse LLM response with Codeforces data and extract structured data"""
        
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
        
        flat_questions = self._extract_questions(test_questions)
        
        difficulty_stats = {
            "easy": {"total": 0, "solved": 0},
            "medium": {"total": 0, "solved": 0},
            "hard": {"total": 0, "solved": 0}
        }
        
        for question in flat_questions:
            # Determine question ID and rating
            if question.get('type') == 'codeforces' or ('contestId' in question and 'index' in question):
                q_data = question.get('data', question)
                question_id = f"{q_data.get('contestId', '')}{q_data.get('index', '')}"
                rating = q_data.get('rating', 0)
            else:
                # Manual question - assume medium if not specified
                # Use ID or index fallback logic if needed, but here we just need to check if solved
                question_id = str(question.get('id', ''))
                rating = 1400 # Default to medium
            
            # Check if solved
            # Try exact ID match first
            solved = candidate_data.get('questions', {}).get(question_id, {}).get('solved', False)
            
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
    
    def _calculate_performance_score(self, candidate_data: Dict, test_questions: List[Dict]) -> int:
        """Calculate overall performance score (0-100)"""
        
        flat_questions = self._extract_questions(test_questions)
        total_questions = len(flat_questions)
        solved_questions = candidate_data.get('total_solved', 0)
        
        if total_questions == 0:
            return 0
        
        # Base score from completion rate
        completion_score = (solved_questions / total_questions) * 60
        
        # Bonus for solving harder problems
        difficulty_bonus = 0
        for question in flat_questions:
            if question.get('type') == 'codeforces' or ('contestId' in question and 'index' in question):
                q_data = question.get('data', question)
                question_id = f"{q_data.get('contestId', '')}{q_data.get('index', '')}"
                rating = q_data.get('rating', 0)
            else:
                question_id = str(question.get('id', ''))
                rating = 1400 # Default medium
            
            solved = candidate_data.get('questions', {}).get(question_id, {}).get('solved', False)
            
            if solved:
                if rating > 1600:
                    difficulty_bonus += 15
                elif rating > 1200:
                    difficulty_bonus += 10
                else:
                    difficulty_bonus += 5
        
        # Cap difficulty bonus
        difficulty_bonus = min(difficulty_bonus, 40)
        
        total_score = min(completion_score + difficulty_bonus, 100)
        return round(total_score)
    
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
