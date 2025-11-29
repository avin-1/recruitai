import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
from database import DatabaseManager
from codeforces_api import CodeforcesAPI

load_dotenv()

class TestService:
    def __init__(self):
        self.db = DatabaseManager()
        self.cf_api = CodeforcesAPI()
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
    
    def create_test(self, test_name: str, test_description: str, selected_questions: List[Dict]) -> int:
        """
        Create a new test with selected questions
        """
        questions_json = json.dumps(selected_questions)
        test_id = self.db.create_test(test_name, test_description, questions_json)
        return test_id
    
    def send_test_invitations(self, test_id: int, test_link: str = None) -> Dict:
        """
        Send test invitations to all selected candidates
        """
        if not self.sender_email or not self.sender_password:
            raise ValueError("Email credentials not configured. Please set SENDER_EMAIL and SENDER_PASSWORD in .env file")
        
        # Use default test link if not provided
        if not test_link:
            test_link = f"http://localhost:3000/test/{test_id}"
        
        candidates = self.db.send_test_notifications(test_id, test_link)
        
        results = {
            'success': [],
            'failed': [],
            'total_sent': 0
        }
        
        for candidate in candidates:
            try:
                success = self._send_test_email(
                    candidate['email'],
                    candidate['name'],
                    test_link
                )
                
                if success:
                    results['success'].append(candidate)
                else:
                    results['failed'].append(candidate)
                
                results['total_sent'] += 1
                
            except Exception as e:
                print(f"Error sending test email to {candidate['email']}: {str(e)}")
                results['failed'].append(candidate)
        
        return results
    
    def _send_test_email(self, candidate_email: str, candidate_name: str, test_link: str) -> bool:
        """
        Send test invitation email to a candidate
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = candidate_email
            msg['Subject'] = "Technical Test Invitation - Codeforces Assessment"
            
            body = f"""
Dear {candidate_name},

You have been invited to take a technical assessment test as part of our recruitment process.

Test Details:
- Platform: Codeforces
- Test Link: {test_link}
- Instructions: Please register with your Codeforces username to begin the test

Please click on the test link above to access your assessment. You will need to:
1. Enter your Codeforces username
2. Complete the assigned problems
3. Submit your solutions

The test will evaluate your problem-solving skills and coding abilities.

If you have any questions or technical issues, please contact our recruitment team.

Best regards,
The Recruitment Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, candidate_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending email to {candidate_email}: {str(e)}")
            return False
    
    def register_candidate(self, candidate_email: str, codeforces_username: str, test_id: int) -> int:
        """
        Register a candidate's Codeforces username for a test
        """
        # Verify the username exists on Codeforces
        user_info = self.cf_api.get_user_info(codeforces_username)
        if not user_info:
            raise ValueError(f"Codeforces username '{codeforces_username}' not found")
        
        userid_id = self.db.register_codeforces_user(candidate_email, codeforces_username, test_id)
        return userid_id
    
    def fetch_and_save_results(self, test_id: int) -> Dict:
        """
        Fetch results from Codeforces API and save to database
        """
        try:
            registered_users = self.db.get_registered_users(test_id)
            test_questions = self.db.get_test_questions(test_id)
            
            if not registered_users:
                return {
                    'total_users': 0,
                    'processed_users': 0,
                    'total_solved': 0,
                    'errors': ['No registered users found for this test']
                }
            
            if not test_questions:
                return {
                    'total_users': len(registered_users),
                    'processed_users': 0,
                    'total_solved': 0,
                    'errors': ['No test questions found for this test']
                }
            
            results_summary = {
                'total_users': len(registered_users),
                'processed_users': 0,
                'total_solved': 0,
                'errors': []
            }
            
            for user in registered_users:
                try:
                    user_results = {}
                    user_solved_count = 0
                    
                    for question in test_questions:
                        try:
                            problem_id = {
                                'contestId': question.get('contestId'),
                                'index': question.get('index')
                            }
                            
                            if not problem_id.get('contestId') or not problem_id.get('index'):
                                continue
                            
                            result = self.cf_api.check_problem_solved(user['username'], problem_id)
                            question_id = self.cf_api.format_problem_id(question)
                            user_results[question_id] = result
                            
                            if result.get('solved', False):
                                user_solved_count += 1
                        except Exception as q_err:
                            error_msg = f"Error checking question for user {user.get('username', 'unknown')}: {str(q_err)}"
                            results_summary['errors'].append(error_msg)
                            print(error_msg)
                            continue
                    
                    # Save results to database
                    if user_results:
                        self.db.save_test_results(user['id'], test_id, user_results)
                        results_summary['processed_users'] += 1
                        results_summary['total_solved'] += user_solved_count
                    
                except Exception as e:
                    error_msg = f"Error processing user {user.get('username', 'unknown')}: {str(e)}"
                    results_summary['errors'].append(error_msg)
                    print(error_msg)
                    import traceback
                    print(traceback.format_exc())
            
            return results_summary
            
        except Exception as e:
            import traceback
            error_msg = f"Error in fetch_and_save_results: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            raise Exception(error_msg)
    
    def get_test_results(self, test_id: int) -> List[Dict]:
        """
        Get formatted test results for display
        """
        raw_results = self.db.get_test_results(test_id)
        test_questions = self.db.get_test_questions(test_id)
        
        # Group results by user
        user_results = {}
        for row in raw_results:
            email, username, question_id, solved, result_data = row
            user_key = f"{email}_{username}"
            
            if user_key not in user_results:
                user_results[user_key] = {
                    'email': email,
                    'username': username,
                    'questions': {},
                    'total_solved': 0,
                    'total_questions': len(test_questions)
                }
            
            user_results[user_key]['questions'][question_id] = {
                'solved': solved,
                'data': result_data
            }
            
            if solved:
                user_results[user_key]['total_solved'] += 1
        
        return list(user_results.values())
    
    def get_available_problems(self, difficulty_min: int = None, difficulty_max: int = None, tags: List[str] = None) -> List[Dict]:
        """
        Get available problems from Codeforces for selection
        """
        return self.cf_api.get_problems(tags=tags, difficulty_min=difficulty_min, difficulty_max=difficulty_max)
