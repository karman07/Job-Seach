import httpx
from typing import List, Dict, Any, Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AdzunaAPIError(Exception):
    """Custom exception for Adzuna API errors"""
    pass


class AdzunaClient:
    """Client for Adzuna API integration"""
    
    BASE_URL = "https://api.adzuna.com/v1/api"
    
    def __init__(self):
        self.app_id = settings.ADZUNA_APP_ID
        self.app_key = settings.ADZUNA_APP_KEY
        self.country = settings.ADZUNA_COUNTRY
        self.results_per_page = settings.ADZUNA_RESULTS_PER_PAGE
        self.timeout = httpx.Timeout(30.0, connect=10.0)
    
    def _build_url(self, endpoint: str, country: Optional[str] = None) -> str:
        """Build full API URL"""
        target_country = country or self.country
        return f"{self.BASE_URL}/jobs/{target_country}/{endpoint}"
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = self._build_url(endpoint, country=country)
        
        # Add auth params - DON'T include content-type (not needed by Adzuna)
        request_params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": self.results_per_page
        }
        
        if params:
            request_params.update(params)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; JobMatchBot/1.0)"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Log the actual URL being called for debugging
                logger.info(f"Calling Adzuna API: {url} with params: {request_params}")
                response = await client.get(url, params=request_params, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Adzuna API error: {e.response.status_code}")
                logger.error(f"Request URL: {e.request.url}")
                logger.error(f"Response: {e.response.text[:500]}")
                raise AdzunaAPIError(f"API returned {e.response.status_code}")
            except Exception as e:
                logger.error(f"Adzuna request failed: {str(e)}")
                raise
    
    async def search_jobs(
        self,
        what: Optional[str] = None,
        page: int = 1,
        country: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for jobs on Adzuna (minimal params - filtering done after retrieval)
        
        Args:
            what: Keywords for job title/description
            page: Page number (1-indexed, included in URL path)
            country: Optional country code (defaults to settings.ADZUNA_COUNTRY)
        """
        endpoint = f"search/{page}"
        
        params = {}
        
        if what:
            params["what"] = what
        
        logger.info(f"Searching Adzuna ({country or self.country}): page={page}, what={what}")
        return await self._make_request(endpoint, params, country=country)
    
    async def fetch_all_jobs(
        self,
        max_pages: int = 5,  # Reduced from 20 to limit API calls
        what: Optional[str] = None,  # Default to None to fetch everything
        country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all available jobs up to max_pages (limited to avoid rate limits)
        Only using minimal params: app_id, app_key, results_per_page, what

        Filtering will be done after data retrieval
        
        Returns:
            List of job dictionaries
        """
        all_jobs = []
        page = 1
        
        logger.info(f"Starting job fetch (max {max_pages} pages, {self.results_per_page} per page, what='{what}')")
        
        while page <= max_pages:
            try:
                result = await self.search_jobs(page=page, what=what, country=country)
                
                jobs = result.get("results", [])
                if not jobs:
                    logger.info(f"No more jobs found at page {page}")
                    break
                
                all_jobs.extend(jobs)
                
                # Check if we've reached the end
                count = result.get("count", 0)
                total_fetched = page * self.results_per_page
                
                logger.info(f"Fetched page {page}/{max_pages}: {len(jobs)} jobs (total: {len(all_jobs)}/{count})")
                
                if total_fetched >= count:
                    logger.info(f"Reached end of results (total available: {count})")
                    break
                
                page += 1
                
            except AdzunaAPIError as e:
                logger.error(f"Failed to fetch page {page}: {str(e)}")
                # If we already have some jobs, return them instead of failing completely
                if all_jobs:
                    logger.info(f"Returning {len(all_jobs)} jobs fetched before error")
                break
            except Exception as e:
                logger.error(f"Unexpected error on page {page}: {str(e)}")
                if all_jobs:
                    logger.info(f"Returning {len(all_jobs)} jobs fetched before error")
                break
        
        logger.info(f"Total jobs fetched from Adzuna: {len(all_jobs)}")
        return all_jobs
    
    async def get_job_categories(self) -> List[Dict[str, Any]]:
        """Get available job categories"""
        endpoint = "categories"
        result = await self._make_request(endpoint)
        return result.get("results", [])
    
    def parse_job_data(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Adzuna job data into standardized format
        
        Returns:
            Normalized job dictionary
        """
        # Determine if it's an internship
        title_lower = job.get("title", "").lower()
        description_lower = job.get("description", "").lower()
        is_internship = any(keyword in title_lower or keyword in description_lower 
                           for keyword in ["intern", "internship", "co-op", "coop"])
        
        # Determine job level
        job_level = "MID_LEVEL"
        if is_internship or "entry" in title_lower or "junior" in title_lower:
            job_level = "ENTRY_LEVEL"
        elif any(keyword in title_lower for keyword in ["senior", "lead", "principal"]):
            job_level = "SENIOR_LEVEL"
        elif any(keyword in title_lower for keyword in ["director", "vp", "chief", "head of"]):
            job_level = "EXECUTIVE"
        
        # Determine employment type
        employment_type = "FULL_TIME"
        contract_type = job.get("contract_type", "").lower()
        contract_time = job.get("contract_time", "").lower()
        
        if is_internship:
            employment_type = "INTERNSHIP"
        elif "part" in contract_time or "part_time" in contract_type:
            employment_type = "PART_TIME"
        elif "contract" in contract_type or "temporary" in contract_type:
            employment_type = "CONTRACTOR"
        
        # Check if remote
        is_remote = any(keyword in title_lower or keyword in description_lower 
                       for keyword in ["remote", "work from home", "wfh", "telecommute"])
        
        location_data = job.get("location", {})
        
        area = location_data.get("area", [])
        country_name = area[0] if len(area) > 0 else None
        state_name = area[1] if len(area) > 1 else None
        city_name = area[-1] if len(area) > 2 else None
        
        return {
            "adzuna_id": job.get("id"),
            "title": job.get("title"),
            "description": job.get("description"),
            "company_display_name": job.get("company", {}).get("display_name"),
            "location": location_data.get("display_name"),
            "location_structured": {
                "city": city_name,
                "state": state_name,
                "country": country_name,
                "lat": location_data.get("latitude"),
                "lon": location_data.get("longitude")
            },
            "employment_type": employment_type,
            "job_level": job_level,
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "salary_currency": "USD",
            "category": job.get("category", {}).get("label"),
            "contract_time": job.get("contract_time"),
            "redirect_url": job.get("redirect_url"),
            "is_internship": is_internship,
            "is_remote": is_remote,
            "raw_data": job
        }
