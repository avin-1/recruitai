import requests
import json
from typing import List, Dict, Optional

class CodeforcesAPI:
    def __init__(self):
        self.base_url = "https://codeforces.com/api"
    
    def get_problems(self, tags: List[str] = None, difficulty_min: int = None, difficulty_max: int = None) -> List[Dict]:
        """
        Fetch problems from Codeforces API with optional filters
        """
        try:
            url = f"{self.base_url}/problemset.problems"
            params = {}
            
            if tags:
                params['tags'] = ';'.join(tags)
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] != 'OK':
                raise Exception(f"API Error: {data.get('comment', 'Unknown error')}")
            
            problems = data['result']['problems']
            
            # Filter by difficulty if specified
            if difficulty_min is not None or difficulty_max is not None:
                filtered_problems = []
                for problem in problems:
                    if 'rating' in problem:
                        rating = problem['rating']
                        if difficulty_min is not None and rating < difficulty_min:
                            continue
                        if difficulty_max is not None and rating > difficulty_max:
                            continue
                        filtered_problems.append(problem)
                problems = filtered_problems
            
            return problems
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching problems: {e}")
            return []
        except Exception as e:
            print(f"Error processing problems: {e}")
            return []
    
    def get_user_submissions(self, username: str, count: int = 1000) -> List[Dict]:
        """
        Get user's submission history
        """
        try:
            url = f"{self.base_url}/user.status"
            params = {
                'handle': username,
                'from': 1,
                'count': count
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] != 'OK':
                raise Exception(f"API Error: {data.get('comment', 'Unknown error')}")
            
            return data['result']
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching submissions for {username}: {e}")
            return []
        except Exception as e:
            print(f"Error processing submissions for {username}: {e}")
            return []
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """
        Get user information
        """
        try:
            url = f"{self.base_url}/user.info"
            params = {'handles': username}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] != 'OK':
                return None
            
            return data['result'][0] if data['result'] else None
            
        except Exception as e:
            print(f"Error fetching user info for {username}: {e}")
            return None
    
    def check_problem_solved(self, username: str, problem_id: Dict) -> Dict:
        """
        Check if a user has solved a specific problem
        """
        try:
            if not username or not problem_id:
                return {
                    'solved': False,
                    'submission_time': None,
                    'verdict': None,
                    'submission_id': None,
                    'error': 'Missing username or problem_id'
                }
            
            submissions = self.get_user_submissions(username)
            
            if not submissions:
                return {
                    'solved': False,
                    'submission_time': None,
                    'verdict': None,
                    'submission_id': None,
                    'error': f'No submissions found for user {username}'
                }
            
            for submission in submissions:
                problem = submission.get('problem', {})
                if (problem.get('contestId') == problem_id.get('contestId') and
                    problem.get('index') == problem_id.get('index')):
                    
                    return {
                        'solved': submission.get('verdict') == 'OK',
                        'submission_time': submission.get('creationTimeSeconds'),
                        'verdict': submission.get('verdict'),
                        'submission_id': submission.get('id')
                    }
            
            return {
                'solved': False,
                'submission_time': None,
                'verdict': None,
                'submission_id': None
            }
        except Exception as e:
            print(f"Error in check_problem_solved for {username}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {
                'solved': False,
                'submission_time': None,
                'verdict': None,
                'submission_id': None,
                'error': str(e)
            }
    
    def get_problems_by_difficulty(self, difficulty: int, count: int = 50) -> List[Dict]:
        """
        Get problems of a specific difficulty
        """
        problems = self.get_problems()
        filtered = [p for p in problems if p.get('rating') == difficulty]
        return filtered[:count]
    
    def get_problems_by_tags(self, tags: List[str], count: int = 50) -> List[Dict]:
        """
        Get problems with specific tags
        """
        return self.get_problems(tags=tags)[:count]
    
    def format_problem_id(self, problem: Dict) -> str:
        """
        Format problem ID for display
        """
        contest_id = problem.get('contestId', '')
        index = problem.get('index', '')
        return f"{contest_id}{index}"
    
    def get_problem_url(self, problem: Dict) -> str:
        """
        Get the URL for a problem
        """
        contest_id = problem.get('contestId', '')
        index = problem.get('index', '')
        return f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
    
    def get_user_submission_details(self, username: str, test_questions: List[Dict]) -> Dict:
        """
        Get detailed submission data for specific test questions
        """
        try:
            # Get last 10 submissions
            submissions = self.get_user_submissions(username, 10)
            
            if not submissions:
                return {'status': 'FAILED', 'comment': 'No submissions found'}
            
            # Create a mapping of problem IDs to test questions
            test_problem_ids = set()
            for question in test_questions:
                problem_id = f"{question.get('contestId', '')}{question.get('index', '')}"
                test_problem_ids.add(problem_id)
            
            # Filter submissions that match test questions
            relevant_submissions = []
            for submission in submissions:
                problem = submission.get('problem', {})
                problem_id = f"{problem.get('contestId', '')}{problem.get('index', '')}"
                
                if problem_id in test_problem_ids:
                    relevant_submissions.append({
                        'submission_id': submission.get('id'),
                        'contest_id': problem.get('contestId'),
                        'problem_index': problem.get('index'),
                        'problem_name': problem.get('name'),
                        'problem_rating': problem.get('rating'),
                        'problem_tags': problem.get('tags', []),
                        'verdict': submission.get('verdict'),
                        'programming_language': submission.get('programmingLanguage'),
                        'time_consumed': submission.get('timeConsumedMillis'),
                        'memory_consumed': submission.get('memoryConsumedBytes'),
                        'passed_test_count': submission.get('passedTestCount'),
                        'creation_time': submission.get('creationTimeSeconds'),
                        'points': problem.get('points', 0)
                    })
            
            return {
                'status': 'OK',
                'username': username,
                'total_submissions': len(submissions),
                'relevant_submissions': relevant_submissions,
                'test_problem_ids': list(test_problem_ids)
            }
            
        except Exception as e:
            return {'status': 'FAILED', 'comment': f'Error fetching submission details: {str(e)}'}
