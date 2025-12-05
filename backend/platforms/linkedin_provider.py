import os
import logging
import httpx
from .base_provider import JobProvider

logger = logging.getLogger(__name__)

class LinkedInJobProvider(JobProvider):
    """LinkedIn Job Posting Provider using /simpleJobPostings"""
    
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.base_url = "https://api.linkedin.com/v2"
        
        if not self.access_token:
            logger.warning("LinkedIn Access Token (LINKEDIN_ACCESS_TOKEN) not found in environment.")

    def post_job(self, job_details: dict) -> dict:
        if not self.access_token:
            return {"status": "failed", "error": "Missing LINKEDIN_ACCESS_TOKEN"}

        try:
            # Construct LinkedIn Job Schema
            # This is a simplified mapping based on the provided docs
            external_id = str(job_details.get("_id", ""))
            title = job_details.get("job_title", "Job Opening")
            description = job_details.get("summary") or job_details.get("description") or "See details."
            company_name = job_details.get("company", "Company")
            location_raw = job_details.get("location", "Remote")
            
            # Basic payload structure for /simpleJobPostings
            # Note: Real implementation requires mapping location to LinkedIn's standardized format
            # and handling company URNs. This is a best-effort implementation.
            
            payload = {
                "elements": [
                    {
                        "externalJobPostingId": external_id,
                        "jobPostingOperationType": "CREATE",
                        "title": title,
                        "description": description,
                        "companyName": company_name,
                        "location": location_raw,
                        # Add other required fields as per strict schema if needed
                    }
                ]
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "x-restli-method": "batch_create"
            }
            
            url = f"{self.base_url}/simpleJobPostings"
            
            logger.info(f"Posting job to LinkedIn: {title}")
            response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
            
            if response.status_code in [200, 201, 202]:
                data = response.json()
                # Parse response to get task ID or job ID
                return {"status": "success", "data": data}
            else:
                logger.error(f"LinkedIn API Error: {response.text}")
                return {"status": "failed", "error": response.text}

        except Exception as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            return {"status": "failed", "error": str(e)}
