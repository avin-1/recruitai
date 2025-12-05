from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class JobProvider(ABC):
    """Abstract base class for job posting providers"""
    
    @abstractmethod
    def post_job(self, job_details: dict) -> dict:
        """
        Post a job to the platform.
        
        Args:
            job_details (dict): Dictionary containing job info.
            
        Returns:
            dict: Result dictionary with 'status' ('success', 'failed', 'skipped') and 'id' or 'error'.
        """
        pass
