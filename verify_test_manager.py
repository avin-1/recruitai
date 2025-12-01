import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agents', 'shortlisting')))

# Mock dependencies before importing api
sys.modules['backend.agent_orchestrator'] = MagicMock()
sys.modules['llm_analyzer'] = MagicMock()
sys.modules['test_service'] = MagicMock()
sys.modules['database'] = MagicMock()

from api import app

class TestManagerVerification(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('api.test_gen_agent')
    def test_generate_questions(self, mock_agent):
        """Test AI question generation endpoint"""
        mock_questions = [
            {
                "question": "What is Python?",
                "options": ["A snake", "A language", "A car", "A food"],
                "correct_answer": "A language",
                "explanation": "It is a programming language."
            }
        ]
        mock_agent.generate_questions.return_value = mock_questions
        
        response = self.app.post('/api/tests/generate-questions', json={
            'topic': 'Python',
            'count': 1,
            'difficulty': 'easy'
        })
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['questions']), 1)
        self.assertEqual(data['questions'][0]['question'], "What is Python?")
        print("\n✅ /api/tests/generate-questions verified")

    @patch('api.db_manager')
    def test_create_custom_test(self, mock_db):
        """Test creating a custom test with sections"""
        mock_db.create_test.return_value = 123
        
        sections = [
            {
                "id": 1, 
                "name": "Aptitude", 
                "questions": [{"question": "Q1", "options": ["A"], "correct_answer": "A"}]
            }
        ]
        
        response = self.app.post('/api/tests/create', json={
            'test_name': 'Custom Test',
            'test_description': 'Desc',
            'platform_type': 'custom',
            'custom_platform_name': 'MyPlatform',
            'questions': sections
        })
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['test_id'], 123)
        
        # Verify db call arguments
        mock_db.create_test.assert_called_once()
        args = mock_db.create_test.call_args[0]
        self.assertEqual(args[0], 'Custom Test')
        self.assertEqual(args[3], 'custom')
        self.assertEqual(args[4], 'MyPlatform')
        print("\n✅ /api/tests/create (Custom) verified")

    @patch('api.db_manager')
    def test_create_mixed_test(self, mock_db):
        """Test creating a custom test with mixed manual and Codeforces questions"""
        mock_db.create_test.return_value = 125
        
        sections = [
            {
                "id": 1, 
                "name": "Aptitude", 
                "questions": [{"type": "manual", "question": "Q1", "options": ["A"], "correct_answer": "A"}]
            },
            {
                "id": 2,
                "name": "Coding",
                "questions": [{
                    "type": "codeforces", 
                    "question": "[Codeforces 1A] Theatre Square",
                    "data": {"contestId": 1, "index": "A", "name": "Theatre Square"}
                }]
            }
        ]
        
        response = self.app.post('/api/tests/create', json={
            'test_name': 'Mixed Test',
            'test_description': 'Mixed Desc',
            'platform_type': 'custom',
            'custom_platform_name': 'MixedPlatform',
            'questions': sections
        })
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['test_id'], 125)
        
        # Verify db call
        mock_db.create_test.assert_called_once()
        args = mock_db.create_test.call_args[0]
        self.assertEqual(args[0], 'Mixed Test')
        saved_questions = json.loads(args[2])
        self.assertEqual(len(saved_questions), 2)
        self.assertEqual(saved_questions[1]['questions'][0]['type'], 'codeforces')
        print("\n✅ /api/tests/create (Mixed Content) verified")

    @patch('api.db_manager')
    def test_create_codeforces_test(self, mock_db):
        """Test creating a Codeforces test"""
        mock_db.create_test.return_value = 124
        
        problems = [{"contestId": 1, "index": "A"}]
        
        response = self.app.post('/api/tests/create', json={
            'test_name': 'CF Test',
            'platform_type': 'codeforces',
            'questions': problems
        })
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['test_id'], 124)
        print("\n✅ /api/tests/create (Codeforces) verified")

if __name__ == '__main__':
    unittest.main()
