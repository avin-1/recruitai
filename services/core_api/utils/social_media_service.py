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
        # In microservice context, relying on main .env is safer, but we'll try to support self-conatined logic
        
        self.ig_user_id = os.getenv("IG_USER_ID")
        self.access_token = os.getenv("ACCESS_TOKEN")
        # Use Facebook Graph API base URL for Content Publishing
        self.base_url = "https://graph.facebook.com/v19.0"
        
        self.fb_page_id = os.getenv("FB_PAGE_ID")
        
        if not self.ig_user_id or not self.access_token:
            logger.warning("Instagram credentials (IG_USER_ID, ACCESS_TOKEN) not found in environment variables.")
        if not self.fb_page_id:
            logger.warning("Facebook Page ID (FB_PAGE_ID) not found in environment variables.")

    def post_to_instagram(self, caption, image_url):
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

        except Exception as e:
            logger.error(f"Error posting to Instagram: {e}")
            return None

    def post_to_facebook(self, caption, image_url):
        if not self.fb_page_id or not self.access_token:
            logger.error("Cannot post to Facebook: Missing credentials (FB_PAGE_ID or ACCESS_TOKEN).")
            return None

        try:
            # Step 1: Get Page Access Token
            # We need to exchange the User Token for a Page Token to post AS the page
            page_token_url = f"{self.base_url}/{self.fb_page_id}"
            token_params = {
                "fields": "access_token",
                "access_token": self.access_token
            }
            
            logger.info(f"Fetching Page Access Token for Page ID: {self.fb_page_id}")
            token_response = httpx.get(page_token_url, params=token_params, timeout=10.0)
            
            if token_response.status_code != 200:
                logger.error(f"Failed to get Page Token: {token_response.text}")
                # Fallback: Try using the user token directly (might fail with permission error)
                page_access_token = self.access_token
            else:
                page_access_token = token_response.json().get("access_token")

            # Step 2: Post Photo using Page Access Token
            url = f"{self.base_url}/{self.fb_page_id}/photos"
            
            params = {
                "access_token": page_access_token,
                "url": image_url,
                "message": caption,
                "published": "true"
            }
            
            logger.info(f"Posting to Facebook Page {self.fb_page_id} with image: {image_url}")
            response = httpx.post(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Successfully published to Facebook: {data.get('id')}")
            return data

        except Exception as e:
            logger.error(f"Error posting to Facebook: {e}")
            return None

    def post_job(self, job_details, image_url, platforms=["instagram"]):
        results = {}
        
        # Construct Caption
        title = job_details.get("job_title", "Job Opportunity")
        company = job_details.get("company", "Hiring")
        location = job_details.get("location", "")
        summary = job_details.get("summary", "")
        job_id = str(job_details.get("_id", ""))
        
        # Links
        # Ideally configured via env or constants
        portal_link = f"https://recruit-ai-autonomous-talent-intell.vercel.app/job/{job_id}"
        linkedin_link = "https://www.linkedin.com/jobs/view/3816594215"
        naukri_link = "https://www.naukri.com/job-listings-software-engineer-123456"
        
        caption = f"""🚀 WE ARE HIRING!

Role: {title}
Company: {company}
Location: {location}

{summary}

👇 APPLY HERE 👇
🏠 Our Portal: {portal_link}
🔗 LinkedIn: {linkedin_link}
💼 Naukri: {naukri_link}

#hiring #job #career #recruitment #jobsearch"""
        
        if "instagram" in platforms:
            res = self.post_to_instagram(caption, image_url)
            results["instagram"] = "success" if res else "failed"
            
        if "facebook" in platforms:
            res = self.post_to_facebook(caption, image_url)
            results["facebook"] = "success" if res else "failed"

        # New Platforms using Provider Pattern (Local internal import)
        if "linkedin" in platforms:
            try:
                from utils.platforms.linkedin_provider import LinkedInJobProvider
                provider = LinkedInJobProvider()
                res = provider.post_job(job_details)
                results["linkedin"] = res.get("status", "failed")
            except ImportError:
                 # Try relative import if module structure differs
                 try:
                     from .platforms.linkedin_provider import LinkedInJobProvider
                     provider = LinkedInJobProvider()
                     res = provider.post_job(job_details)
                     results["linkedin"] = res.get("status", "failed")
                 except Exception as e:
                     logger.error(f"Failed to load LinkedIn provider: {e}")
                     results["linkedin"] = "failed"
            except Exception as e:
                logger.error(f"Failed to load/run LinkedIn provider: {e}")
                results["linkedin"] = "failed"

        if "naukri" in platforms:
            try:
                from utils.platforms.naukri_provider import NaukriJobProvider
                provider = NaukriJobProvider()
                res = provider.post_job(job_details)
                results["naukri"] = res.get("status", "failed")
            except ImportError:
                 try:
                     from .platforms.naukri_provider import NaukriJobProvider
                     provider = NaukriJobProvider()
                     res = provider.post_job(job_details)
                     results["naukri"] = res.get("status", "failed")
                 except Exception as e:
                     logger.error(f"Failed to load Naukri provider: {e}")
                     results["naukri"] = "failed"
            except Exception as e:
                logger.error(f"Failed to load/run Naukri provider: {e}")
                results["naukri"] = "failed"
            
        return results
