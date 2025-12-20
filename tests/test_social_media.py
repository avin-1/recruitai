import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add backend and root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pymongo before importing upload_api
sys.modules['pymongo'] = MagicMock()
sys.modules['pymongo.MongoClient'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Set dummy env var
os.environ["MONGODB_URI"] = "mongodb://fake:27017"
os.environ["IG_USER_ID"] = "fake_user"
os.environ["ACCESS_TOKEN"] = "fake_token"

# Mock other potential imports that might cause issues
sys.modules['agents.resumeandmatching.utils.resume_parser'] = MagicMock()
sys.modules['agents.resumeandmatching.utils.matcher'] = MagicMock()
sys.modules['agents.resumeandmatching.utils.llm_scorer'] = MagicMock()

from social_media_service import SocialMediaService
# Now import app
from upload_api import app

class TestSocialMediaIntegration(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('social_media_service.httpx.post')
    def test_social_media_service_post(self, mock_post):
        # Mock responses
        mock_response_create = MagicMock()
        mock_response_create.json.return_value = {"id": "12345"}
        mock_response_create.raise_for_status.return_value = None
        
        mock_response_publish = MagicMock()
        mock_response_publish.json.return_value = {"id": "67890"}
        mock_response_publish.raise_for_status.return_value = None
        
        mock_post.side_effect = [mock_response_create, mock_response_publish]

        service = SocialMediaService()
        # Inject fake credentials
        service.ig_user_id = "fake_user_id"
        service.access_token = "fake_token"
        
        result = service.post_to_instagram("Test Caption", "https://example.com/image.jpg")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get("id"), "67890")
        self.assertEqual(mock_post.call_count, 2)

    @patch('upload_api.collection')
    @patch('social_media_service.SocialMediaService')
    def test_approve_endpoint_with_social(self, MockService, mock_collection):
        # Mock DB
        mock_collection.update_one.return_value.matched_count = 1
        mock_collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "job_title": "Software Engineer",
            "company": "Tech Corp",
            "location": "Remote"
        }
        
        # Mock Service
        mock_service_instance = MockService.return_value
        mock_service_instance.post_job.return_value = {"instagram": "success"}

        # Test Data
        data = {
            "profile_id": "507f1f77bcf86cd799439011",
            "post_to": json.dumps(["instagram"])
        }
        
        response = self.app.post('/approve', data=data, content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("social_media_results", response.json)
        self.assertEqual(response.json["social_media_results"]["instagram"], "success")

if __name__ == '__main__':
    unittest.main()
