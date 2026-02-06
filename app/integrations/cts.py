from google.cloud import talent_v4
from google.api_core.exceptions import GoogleAPIError, AlreadyExists, NotFound, DeadlineExceeded, ServiceUnavailable, InternalServerError
from typing import Dict, Any, Optional, List
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings
import hashlib

logger = logging.getLogger(__name__)
settings = get_settings()


class CTSError(Exception):
    """Custom exception for CTS errors"""
    pass


class CTSClient:
    """Client for Google Cloud Talent Solution integration"""
    
    def __init__(self):
        self.project_id = settings.GCP_PROJECT_ID
        self.parent = settings.parent_path  # Uses DEFAULT tenant: projects/{PROJECT_ID}
        self.company_name = settings.CTS_COMPANY_NAME
        self._tenant_parent = None  # Will be set when first company is created
        
        # Initialize CTS clients
        self.job_service_client = talent_v4.JobServiceClient()
        self.company_service_client = talent_v4.CompanyServiceClient()
    
    def _extract_tenant_parent(self, company_name: str) -> str:
        """Extract tenant parent from company name (includes auto-generated tenant)"""
        if not company_name:
            return self.parent
        # company_name format: projects/{project}/tenants/{tenant}/companies/{company}
        parts = company_name.split('/companies/')
        if len(parts) == 2:
            return parts[0]  # Returns: projects/{project}/tenants/{tenant}
        return self.parent  # Fallback to project-level parent
    
    def generate_requisition_id(self, adzuna_id: str) -> str:
        """
        Generate a globally unique requisition ID from Adzuna ID
        CTS requires requisition_id to be unique across the tenant
        """
        # Use hash to ensure uniqueness and consistent length
        hash_suffix = hashlib.md5(str(adzuna_id).encode()).hexdigest()[:8]
        return f"adzuna-{adzuna_id}-{hash_suffix}"
    
    def generate_job_name(self, requisition_id: str) -> str:
        """Generate CTS job name (full path) - uses tenant parent if available"""
        parent_for_job = self._tenant_parent if self._tenant_parent else self.parent
        return f"{parent_for_job}/jobs/{requisition_id}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((DeadlineExceeded, ServiceUnavailable, InternalServerError))
    )
    def create_company_if_not_exists(
        self, 
        display_name: str,
        external_id: Optional[str] = None
    ) -> str:
        """
        Create a company in CTS if it doesn't exist
        
        Returns:
            Company name (full path)
        """
        try:
            # Try to create company
            company = talent_v4.Company(
                display_name=display_name,
                external_id=external_id or f"company-{display_name.lower().replace(' ', '-')}"
            )
            
            request = talent_v4.CreateCompanyRequest(
                parent=self.parent,
                company=company
            )
            
            response = self.company_service_client.create_company(request=request)
            logger.info(f"Created company: {response.name}")
            
            # Extract tenant parent if not already set
            if not self._tenant_parent and hasattr(response, 'name') and response.name:
                self._tenant_parent = self._extract_tenant_parent(response.name)
            
            return response.name if hasattr(response, 'name') else None
            
        except AlreadyExists:
            # Company already exists, list and find it
            logger.info(f"Company {display_name} already exists")
            companies = self.list_companies()
            for company in companies:
                if hasattr(company, 'display_name') and company.display_name == display_name:
                    # Extract tenant parent if not already set
                    if not self._tenant_parent and hasattr(company, 'name') and company.name:
                        self._tenant_parent = self._extract_tenant_parent(company.name)
                    return company.name if hasattr(company, 'name') else self.company_name
            # Fallback to configured company
            return self.company_name
        except GoogleAPIError as e:
            logger.error(f"Error creating company: {str(e)}")
            return self.company_name
    
    def list_companies(self) -> List[talent_v4.Company]:
        """List all companies in the tenant"""
        try:
            request = talent_v4.ListCompaniesRequest(parent=self.parent)
            companies = self.company_service_client.list_companies(request=request)
            return list(companies)
        except GoogleAPIError as e:
            logger.error(f"Error listing companies: {str(e)}")
            return []
    
    def _build_cts_job(
        self,
        job_data: Dict[str, Any],
        requisition_id: str,
        company_name: str
    ) -> talent_v4.Job:
        """Build CTS Job object from job data"""
        
        # Build addresses
        addresses = []
        if job_data.get("location"):
            addresses.append(job_data["location"])
        
        # Build application info
        application_info = talent_v4.Job.ApplicationInfo()
        if job_data.get("redirect_url"):
            application_info.uris = [job_data["redirect_url"]]
        
        # Build compensation info
        compensation_info = None
        if job_data.get("salary_min") or job_data.get("salary_max"):
            compensation_entry = talent_v4.CompensationInfo.CompensationEntry()
            compensation_entry.type_ = talent_v4.CompensationInfo.CompensationType.BASE
            compensation_entry.unit = talent_v4.CompensationInfo.CompensationUnit.ANNUALIZED
            
            if job_data.get("salary_min") and job_data.get("salary_max"):
                compensation_entry.range_ = talent_v4.CompensationInfo.CompensationRange(
                    max_compensation=talent_v4.Money(
                        currency_code=job_data.get("salary_currency", "USD"),
                        units=int(job_data["salary_max"])
                    ),
                    min_compensation=talent_v4.Money(
                        currency_code=job_data.get("salary_currency", "USD"),
                        units=int(job_data["salary_min"])
                    )
                )
            elif job_data.get("salary_min"):
                compensation_entry.amount = talent_v4.Money(
                    currency_code=job_data.get("salary_currency", "USD"),
                    units=int(job_data["salary_min"])
                )
            
            compensation_info = talent_v4.CompensationInfo(
                entries=[compensation_entry]
            )
        
        # Map employment types
        employment_types = []
        emp_type = job_data.get("employment_type", "FULL_TIME")
        employment_type_map = {
            "FULL_TIME": talent_v4.EmploymentType.FULL_TIME,
            "PART_TIME": talent_v4.EmploymentType.PART_TIME,
            "CONTRACTOR": talent_v4.EmploymentType.CONTRACTOR,
            "INTERNSHIP": talent_v4.EmploymentType.INTERN,
        }
        if emp_type in employment_type_map:
            employment_types.append(employment_type_map[emp_type])
        
        # Map job level (use correct CTS enum values)
        job_level_map = {
            "ENTRY_LEVEL": talent_v4.JobLevel.ENTRY_LEVEL,
            "MID_LEVEL": talent_v4.JobLevel.EXPERIENCED,  # MID_LEVEL → EXPERIENCED
            "SENIOR_LEVEL": talent_v4.JobLevel.MANAGER,   # SENIOR_LEVEL → MANAGER
            "MANAGER": talent_v4.JobLevel.MANAGER,
            "DIRECTOR": talent_v4.JobLevel.DIRECTOR,
            "EXECUTIVE": talent_v4.JobLevel.EXECUTIVE,
        }
        job_level = job_level_map.get(job_data.get("job_level", "MID_LEVEL"), None)
        
        # Build the job
        job = talent_v4.Job(
            company=company_name,
            requisition_id=requisition_id,
            title=job_data["title"],
            description=job_data["description"],
            addresses=addresses,
            application_info=application_info,
            employment_types=employment_types,
            language_code="en-US"
        )
        
        if compensation_info:
            job.compensation_info = compensation_info
        
        if job_level:
            job.job_level = job_level
        
        return job
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((DeadlineExceeded, ServiceUnavailable, InternalServerError))
    )
    def create_job(self, job_data: Dict[str, Any]) -> str:
        """
        Create a job in CTS
        
        Args:
            job_data: Normalized job data dictionary
            
        Returns:
            CTS job name (full path)
        """
        try:
            # Generate requisition ID
            requisition_id = self.generate_requisition_id(job_data["adzuna_id"])
            
            # Get or create company
            company_name = self.company_name
            if job_data.get("company_display_name"):
                try:
                    company_name = self.create_company_if_not_exists(
                        display_name=job_data["company_display_name"]
                    )
                except Exception as e:
                    logger.warning(f"Failed to create company, using default: {str(e)}")
            
            # Extract tenant parent from company name (CTS auto-generates DEFAULT tenant)
            if not self._tenant_parent and company_name:
                self._tenant_parent = self._extract_tenant_parent(company_name)
            
            # Build CTS job
            job = self._build_cts_job(job_data, requisition_id, company_name)
            
            # Create job using tenant parent (not project parent)
            parent_for_job = self._tenant_parent if self._tenant_parent else self.parent
            request = talent_v4.CreateJobRequest(
                parent=parent_for_job,
                job=job
            )
            
            response = self.job_service_client.create_job(request=request)
            
            # Guard against missing attributes in response
            if not hasattr(response, 'name') or not response.name:
                raise CTSError("CTS returned response without job name")
            
            logger.info(f"Created CTS job: {response.name}")
            return response.name
            
        except AlreadyExists:
            logger.warning(f"Job {requisition_id} already exists in CTS")
            return self.generate_job_name(requisition_id)
        except GoogleAPIError as e:
            logger.error(f"Error creating CTS job: {str(e)}")
            raise CTSError(f"Failed to create job in CTS: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((DeadlineExceeded, ServiceUnavailable, InternalServerError))
    )
    def update_job(self, cts_job_name: str, job_data: Dict[str, Any]) -> str:
        """
        Update an existing job in CTS
        
        Args:
            cts_job_name: Full CTS job name (path)
            job_data: Updated job data
            
        Returns:
            CTS job name
        """
        try:
            # Extract requisition ID from name
            requisition_id = cts_job_name.split("/")[-1]
            
            # Get company
            company_name = self.company_name
            if job_data.get("company_display_name"):
                try:
                    company_name = self.create_company_if_not_exists(
                        display_name=job_data["company_display_name"]
                    )
                except Exception:
                    pass
            
            # Build updated job
            job = self._build_cts_job(job_data, requisition_id, company_name)
            job.name = cts_job_name
            
            # Update job
            request = talent_v4.UpdateJobRequest(job=job)
            response = self.job_service_client.update_job(request=request)
            
            logger.info(f"Updated CTS job: {response.name}")
            return response.name
            
        except NotFound:
            logger.warning(f"Job {cts_job_name} not found in CTS, creating new")
            return self.create_job(job_data)
        except GoogleAPIError as e:
            logger.error(f"Error updating CTS job: {str(e)}")
            raise CTSError(f"Failed to update job in CTS: {str(e)}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((DeadlineExceeded, ServiceUnavailable, InternalServerError))
    )
    def delete_job(self, cts_job_name: str) -> bool:
        """
        Delete a job from CTS
        
        Args:
            cts_job_name: Full CTS job name (path)
            
        Returns:
            True if deleted successfully
        """
        try:
            request = talent_v4.DeleteJobRequest(name=cts_job_name)
            self.job_service_client.delete_job(request=request)
            logger.info(f"Deleted CTS job: {cts_job_name}")
            return True
        except NotFound:
            logger.warning(f"Job {cts_job_name} not found in CTS")
            return False
        except GoogleAPIError as e:
            logger.error(f"Error deleting CTS job: {str(e)}")
            return False
    
    def search_jobs_with_resume(
        self,
        resume_text: str,
        job_query: Optional[str] = None,
        location_filters: Optional[List[str]] = None,
        employment_types: Optional[List[str]] = None,
        job_categories: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for jobs using resume text (profile-based search)
        
        Returns:
            List of matching jobs with relevance scores
        """
        try:
            # Build search request
            request_metadata = talent_v4.RequestMetadata(
                user_id="resume-matcher",
                session_id="resume-search",
                domain="jobmatch.ai"
            )
            
            # Build job query
            query = talent_v4.JobQuery()
            if job_query:
                query.query = job_query
            
            if employment_types:
                emp_type_map = {
                    "FULL_TIME": talent_v4.EmploymentType.FULL_TIME,
                    "PART_TIME": talent_v4.EmploymentType.PART_TIME,
                    "CONTRACTOR": talent_v4.EmploymentType.CONTRACTOR,
                    "INTERNSHIP": talent_v4.EmploymentType.INTERN,
                }
                query.employment_types = [
                    emp_type_map[et] for et in employment_types if et in emp_type_map
                ]
            
            if location_filters:
                query.location_filters = [
                    talent_v4.LocationFilter(address=loc) for loc in location_filters
                ]
            
            if job_categories:
                query.job_categories = job_categories
            
            # Build search request with profile
            search_request = talent_v4.SearchJobsRequest(
                parent=self.parent,
                request_metadata=request_metadata,
                job_query=query,
                job_view=talent_v4.JobView.JOB_VIEW_FULL,
                offset=0,
                max_page_size=max_results,
                order_by="relevance desc"
            )
            
            # Add custom ranking with resume text
            if resume_text:
                search_request.custom_ranking_info = talent_v4.SearchJobsRequest.CustomRankingInfo(
                    importance_level=talent_v4.SearchJobsRequest.CustomRankingInfo.ImportanceLevel.EXTREME,
                    ranking_expression=f"(textSimilarity(resume, \"{self._escape_query(resume_text[:5000])}\"))"
                )
            
            # Execute search
            response = self.job_service_client.search_jobs(request=search_request)
            
            results = []
            for matching_job in response.matching_jobs:
                job = matching_job.job
                results.append({
                    "cts_job_name": job.name,
                    "requisition_id": job.requisition_id,
                    "title": job.title,
                    "company": job.company,
                    "description": job.description,
                    "relevance_score": matching_job.job_title_snippet or 0.0,
                    "application_urls": list(job.application_info.uris) if job.application_info else []
                })
            
            logger.info(f"CTS resume search returned {len(results)} results")
            return results
            
        except GoogleAPIError as e:
            logger.error(f"Error searching CTS jobs: {str(e)}")
            return []
    
    def search_jobs_with_jd(
        self,
        job_description: str,
        location_filters: Optional[List[str]] = None,
        employment_types: Optional[List[str]] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for similar jobs using job description
        
        Returns:
            List of similar jobs
        """
        # Extract key terms from JD for query
        query_text = job_description[:500]  # Use first 500 chars as query
        
        return self.search_jobs_with_resume(
            resume_text=job_description,
            job_query=query_text,
            location_filters=location_filters,
            employment_types=employment_types,
            max_results=max_results
        )
    
    def _escape_query(self, text: str) -> str:
        """Escape special characters in query text"""
        return text.replace('"', '\\"').replace('\n', ' ').replace('\r', ' ')
