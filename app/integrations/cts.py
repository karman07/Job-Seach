import logging
import uuid
import time
from typing import Dict, Any, Optional, List
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CTSClient:
    """
    Client for Google Cloud Talent Solution (CTS) integration.
    Handles job creation, updating, and deletion in CTS.
    """
    
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.parent = f"projects/{self.project_id}/tenants/default_tenant"
        self.enabled = False
        
        # Try to initialize CTS client
        try:
            from google.cloud import talent_v4beta1
            import google.auth
            
            # verify credentials exist
            _, project = google.auth.default()
            self.client = talent_v4beta1.JobServiceClient()
            self.enabled = True
            logger.info(f"CTS Client initialized for project: {self.project_id}")
            
        except ImportError:
            logger.warning("Google Cloud Talent Solution library not found. CTS integration disabled.")
        except Exception as e:
            logger.warning(f"Failed to initialize CTS Client: {str(e)}. CTS integration disabled.")
            
    def generate_requisition_id(self, adzuna_id: str) -> str:
        """Generate a unique requisition ID for CTS"""
        return f"req-{adzuna_id}-{uuid.uuid4().hex[:8]}"

    def create_job(self, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a job in CTS.
        
        Args:
            job_data: Normalized job data
            
        Returns:
            The created job name (resource path) or None if failed/disabled
        """
        if not self.enabled:
            logger.debug("CTS disabled, skipping job creation")
            return None
            
        try:
            from google.cloud import talent_v4beta1
            
            # Map simple fields
            job = {
                "requisition_id": job_data.get("requisition_id") or self.generate_requisition_id(job_data.get("adzuna_id")),
                "title": job_data.get("title", ""),
                "description": job_data.get("description", ""),
                "addresses": [job_data.get("location")] if job_data.get("location") else [],
                "application_info": {
                    "uris": [job_data.get("redirect_url")] if job_data.get("redirect_url") else []
                },
                "language_code": "en-US",
            }
            
            # Map structured compensation if available
            if job_data.get("salary_min") and job_data.get("salary_max"):
                job["compensation_info"] = {
                    "entries": [{
                        "type_": talent_v4beta1.CompensationInfo.CompensationType.BASE,
                        "unit": talent_v4beta1.CompensationInfo.CompensationUnit.YEARLY,
                        "amount": {
                            "currency_code": job_data.get("salary_currency", "USD"),
                            "units": int(job_data.get("salary_min", 0))
                        },
                        "range_": {
                            "min_compensation": {
                                "currency_code": job_data.get("salary_currency", "USD"),
                                "units": int(job_data.get("salary_min", 0))
                            },
                            "max_compensation": {
                                "currency_code": job_data.get("salary_currency", "USD"),
                                "units": int(job_data.get("salary_max", 0))
                            }
                        }
                    }]
                }
            
            # Map custom attributes
            custom_attributes = {}
            if job_data.get("is_remote"):
                custom_attributes["remote"] = talent_v4beta1.CustomAttribute(
                    string_values=["true"],
                    filterable=True
                )
            
            if job_data.get("job_level"):
                 custom_attributes["level"] = talent_v4beta1.CustomAttribute(
                    string_values=[job_data.get("job_level")],
                    filterable=True
                )
            
            if custom_attributes:
                job["custom_attributes"] = custom_attributes

            # Create the job
            response = self.client.create_job(
                parent=self.parent,
                job=job
            )
            
            logger.info(f"Created CTS job: {response.name}")
            return response.name

        except Exception as e:
            logger.error(f"Failed to create job in CTS: {str(e)}")
            return None

    def update_job(self, cts_job_name: str, job_data: Dict[str, Any]) -> Optional[str]:
        """
        Update a job in CTS.
        """
        if not self.enabled or not cts_job_name:
            return None
            
        try:
            from google.cloud import talent_v4beta1
            
            # Prepare update mask and job object
            # This is a simplified update for now
            job = {
                "name": cts_job_name,
                "title": job_data.get("title"),
                "description": job_data.get("description"),
            }
            
            # In a real implementation we would define the update_mask properly
            # For now we rely on the client to handle it or just do a partial update
            
            response = self.client.update_job(job=job)
            logger.info(f"Updated CTS job: {response.name}")
            return response.name
            
        except Exception as e:
            logger.error(f"Failed to update job in CTS: {str(e)}")
            return None

    def delete_job(self, cts_job_name: str):
        """Delete a job from CTS"""
        if not self.enabled or not cts_job_name:
            return
            
        try:
            self.client.delete_job(name=cts_job_name)
            logger.info(f"Deleted CTS job: {cts_job_name}")
        except Exception as e:
            logger.error(f"Failed to delete CTS job: {str(e)}")
