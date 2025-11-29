import os
import httpx
import logging

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env explicitly from the same directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)

class SocialMediaService:
    def __init__(self):
        # Reload .env to pick up any changes (e.g. updated tokens) without server restart
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        print(f"DEBUG: Loading .env from {env_path}")
        load_dotenv(env_path, override=True)
        
        self.ig_user_id = os.getenv("IG_USER_ID")
        self.access_token = os.getenv("ACCESS_TOKEN")
        # Use Facebook Graph API base URL for Content Publishing
        self.base_url = "https://graph.facebook.com/v19.0"
        
        print(f"DEBUG TOKEN: '{self.access_token}'")
        print(f"DEBUG IG_USER_ID: '{self.ig_user_id}'")
        
        if not self.ig_user_id or not self.access_token:
            logger.warning("Instagram credentials (IG_USER_ID, ACCESS_TOKEN) not found in environment variables.")

    def post_to_instagram(self, caption, image_url):
        """
        Post an image to Instagram Business account.
        
        Args:
            caption (str): The caption for the post.
            image_url (str): The PUBLIC URL of the image.
            
        Returns:
            dict: The response from the API (containing id on success) or None on failure.
        """
        if not self.ig_user_id or not self.access_token:
            logger.error("Cannot post to Instagram: Missing credentials.")
            return None

        try:
            # Step 1: Create Media Container
            create_url = f"{self.base_url}/{self.ig_user_id}/media"
            
            # Send access_token in query params to avoid parsing issues
            params = {"access_token": self.access_token}
            payload = {
                "image_url": image_url,
                "caption": caption
            }
            
            logger.info(f"Creating Instagram media container for image: {image_url}")
            response = httpx.post(create_url, params=params, json=payload, timeout=30.0)
            response.raise_for_status()
            container_data = response.json()
            creation_id = container_data.get("id")
            
            if not creation_id:
                logger.error(f"Failed to create media container. Response: {response.text}")
                return None
                
            logger.info(f"Media container created: {creation_id}")

            # Step 2: Publish Media Container
            publish_url = f"{self.base_url}/{self.ig_user_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id
            }
            
            logger.info(f"Publishing media container: {creation_id}")
            # Token is already in params from above if we reuse, but let's be explicit
            publish_response = httpx.post(publish_url, params=params, json=publish_payload, timeout=30.0)
            publish_response.raise_for_status()
            publish_data = publish_response.json()
            
            logger.info(f"Successfully published to Instagram: {publish_data.get('id')}")
            return publish_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error posting to Instagram: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error posting to Instagram: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def post_job(self, job_details, image_url, platforms=["instagram"]):
        """
        Post job details to specified platforms.
        
        Args:
            job_details (dict): Dictionary containing job info (title, company, location, etc.)
            image_url (str): Public URL of the image.
            platforms (list): List of platforms to post to (e.g., ["instagram", "facebook"]).
            
        Returns:
            dict: Results for each platform.
        """
        results = {}
        
        # Construct Caption
        title = job_details.get("job_title", "Job Opportunity")
        company = job_details.get("company", "Hiring")
        location = job_details.get("location", "")
        summary = job_details.get("summary", "")
        
        caption = f"🚀 WE ARE HIRING!\n\nRole: {title}\nCompany: {company}\nLocation: {location}\n\n{summary}\n\n#hiring #job #career #recruitment #jobsearch"
        
        if "instagram" in platforms:
            res = self.post_to_instagram(caption, image_url)
            results["instagram"] = "success" if res else "failed"
            
        # Placeholder for Facebook
        if "facebook" in platforms:
            # Facebook posting logic would go here
            # For now, we'll just log it
            logger.info("Facebook posting not yet implemented.")
            results["facebook"] = "skipped"
            
        return results
