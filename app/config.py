from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields like old GCP_TENANT_ID
    )
    # Adzuna API
    ADZUNA_APP_ID: str
    ADZUNA_APP_KEY: str
    ADZUNA_COUNTRY: str = "in"  # India as per working Postman request
    ADZUNA_RESULTS_PER_PAGE: int = 50  # Matches Postman
    
    # Google Cloud
    GCP_PROJECT_ID: str
    GOOGLE_APPLICATION_CREDENTIALS: str
    
    # CTS Configuration
    CTS_COMPANY_NAME: str
    CTS_JOB_LEVEL: str = "ENTRY_LEVEL,MID_LEVEL,SENIOR_LEVEL"
    CTS_EMPLOYMENT_TYPE: str = "FULL_TIME,PART_TIME,CONTRACTOR,INTERNSHIP"
    CTS_LOCATION_BIAS: str = "US"
    
    # MongoDB Database
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "jobmatch_db"
    
    # Job Refresh
    JOB_REFRESH_TIME: str = "03:00"
    JOB_EXPIRY_DAYS: int = 30
    
    # Cache settings
    CACHE_EXPIRY_HOURS: int = 24
    
    # Application
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # AWS SES Settings
    AWS_SES_ACCESS_KEY_ID: str = ""
    AWS_SES_SECRET_ACCESS_KEY: str = ""
    AWS_SES_FROM_EMAIL: str = "noreply@aiforjob.ai"
    AWS_SES_REGION: str = "us-east-1"
    
    @property
    def parent_path(self) -> str:
        """Full parent path for CTS (uses DEFAULT tenant)"""
        return f"projects/{self.GCP_PROJECT_ID}"
    
    @property
    def job_levels_list(self) -> List[str]:
        return [level.strip() for level in self.CTS_JOB_LEVEL.split(",")]
    
    @property
    def employment_types_list(self) -> List[str]:
        return [emp.strip() for emp in self.CTS_EMPLOYMENT_TYPE.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
