from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional, Set, Tuple
import hashlib
from datetime import datetime, timedelta
import logging
import re
from collections import Counter
import math
from app.integrations.cts import CTSClient
from app.models import ResumeSearchCache
from app.schemas import JobMatchResponse
from app.config import get_settings
from bson import ObjectId

logger = logging.getLogger(__name__)
settings = get_settings()


class LocalRAGMatcher:
    """
    Local Retrieval-Augmented Generation (RAG) matcher for job matching
    Uses semantic similarity, keyword matching, and TF-IDF scoring
    """
    
    # Common tech skills and keywords
    TECH_SKILLS = {
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node', 'nodejs', 'django', 'flask', 'fastapi', 'spring', 'sql', 'nosql',
        'mongodb', 'postgresql', 'mysql', 'redis', 'docker', 'kubernetes', 'aws',
        'azure', 'gcp', 'api', 'rest', 'graphql', 'microservices', 'agile', 'scrum',
        'git', 'ci/cd', 'devops', 'machine learning', 'ml', 'ai', 'data science',
        'tensorflow', 'pytorch', 'pandas', 'numpy', 'spark', 'hadoop', 'kafka',
        'android', 'ios', 'swift', 'kotlin', 'flutter', 'react native', 'html',
        'css', 'sass', 'webpack', 'redis', 'elasticsearch', 'rabbitmq', 'testing',
        'junit', 'pytest', 'selenium', 'cypress', 'c++', 'golang', 'rust', 'scala',
        'ruby', 'php', 'laravel', 'rails', '.net', 'c#', 'asp.net', 'blazor'
    }
    
    # Stop words to ignore
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has',
        'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was',
        'will', 'with', 'we', 'you', 'your', 'our', 'this', 'should', 'can',
        'may', 'must', 'have', 'had', 'but', 'or', 'not', 'been', 'which'
    }
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text"""
        # Convert to lowercase
        text = text.lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^a-z0-9\s\+\#\.\-]', ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text
    
    @staticmethod
    def _extract_keywords(text: str, top_n: int = 30) -> List[Tuple[str, float]]:
        """
        Extract important keywords using TF-IDF-like approach
        Returns list of (keyword, weight) tuples
        """
        cleaned_text = LocalRAGMatcher._clean_text(text)
        words = cleaned_text.split()
        
        # Count word frequencies
        word_freq = Counter()
        bigrams = []
        
        for i, word in enumerate(words):
            if len(word) < 2:
                continue
                
            # Skip stop words for unigrams
            if word not in LocalRAGMatcher.STOP_WORDS:
                word_freq[word] += 1
            
            # Extract bigrams (2-word phrases)
            if i < len(words) - 1:
                next_word = words[i + 1]
                if len(next_word) >= 2:
                    bigram = f"{word} {next_word}"
                    bigrams.append(bigram)
        
        # Add bigram frequencies
        for bigram in bigrams:
            word_freq[bigram] += 0.5  # Weight bigrams less than unigrams
        
        # Boost tech skills
        for word, count in list(word_freq.items()):
            if word in LocalRAGMatcher.TECH_SKILLS:
                word_freq[word] = count * 2.0
        
        # Get top keywords
        top_keywords = word_freq.most_common(top_n)
        
        # Normalize weights
        if top_keywords:
            max_freq = top_keywords[0][1]
            top_keywords = [(word, freq / max_freq) for word, freq in top_keywords]
        
        return top_keywords
    
    @staticmethod
    def _extract_skills(text: str) -> Set[str]:
        """Extract tech skills from text"""
        cleaned_text = LocalRAGMatcher._clean_text(text)
        found_skills = set()
        
        for skill in LocalRAGMatcher.TECH_SKILLS:
            if skill in cleaned_text:
                found_skills.add(skill)
        
        return found_skills
    
    @staticmethod
    def _calculate_keyword_match(
        resume_keywords: List[Tuple[str, float]],
        job_text: str
    ) -> float:
        """
        Calculate keyword match score between resume and job
        Returns score between 0 and 1
        """
        if not resume_keywords:
            return 0.0
        
        job_text_clean = LocalRAGMatcher._clean_text(job_text)
        total_weight = 0.0
        matched_weight = 0.0
        
        for keyword, weight in resume_keywords:
            total_weight += weight
            
            # Check if keyword exists in job text
            if keyword in job_text_clean:
                # Bonus if keyword appears near the beginning (job title/summary)
                position_bonus = 1.0
                keyword_pos = job_text_clean.find(keyword)
                if keyword_pos < 200:  # First 200 chars
                    position_bonus = 1.5
                elif keyword_pos < 500:  # First 500 chars
                    position_bonus = 1.2
                
                # Count occurrences (capped at 3 for diminishing returns)
                occurrences = min(job_text_clean.count(keyword), 3)
                matched_weight += weight * position_bonus * math.sqrt(occurrences)
        
        if total_weight == 0:
            return 0.0
        
        # Normalize to 0-1 range
        score = min(matched_weight / total_weight, 1.0)
        return score
    
    @staticmethod
    def _calculate_skill_match(resume_skills: Set[str], job_text: str) -> float:
        """
        Calculate skill match score
        Returns score between 0 and 1
        """
        if not resume_skills:
            return 0.0
        
        job_skills = LocalRAGMatcher._extract_skills(job_text)
        
        if not job_skills:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(resume_skills & job_skills)
        union = len(resume_skills | job_skills)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    @staticmethod
    def _calculate_text_similarity(text1: str, text2: str) -> float:
        """
        Calculate cosine-like similarity between two texts
        Returns score between 0 and 1
        """
        words1 = set(LocalRAGMatcher._clean_text(text1).split())
        words2 = set(LocalRAGMatcher._clean_text(text2).split())
        
        # Remove stop words
        words1 = words1 - LocalRAGMatcher.STOP_WORDS
        words2 = words2 - LocalRAGMatcher.STOP_WORDS
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    @staticmethod
    def match_resume_to_job(resume_text: str, job: Dict[str, Any]) -> float:
        """
        Match a resume to a single job using local RAG techniques
        
        Args:
            resume_text: Full resume text
            job: Job document from database
            
        Returns:
            Match score between 0 and 1
        """
        # Extract resume features
        resume_keywords = LocalRAGMatcher._extract_keywords(resume_text, top_n=40)
        resume_skills = LocalRAGMatcher._extract_skills(resume_text)
        
        # Combine job title and description for matching
        job_title = job.get("title", "")
        job_description = job.get("description", "")
        job_company = job.get("company_display_name", "")
        job_full_text = f"{job_title} {job_title} {job_description} {job_company}"
        
        # Calculate different match scores
        keyword_score = LocalRAGMatcher._calculate_keyword_match(
            resume_keywords, job_full_text
        )
        
        skill_score = LocalRAGMatcher._calculate_skill_match(
            resume_skills, job_full_text
        )
        
        text_sim_score = LocalRAGMatcher._calculate_text_similarity(
            resume_text[:1000],  # First 1000 chars of resume
            job_full_text[:1000]  # First 1000 chars of job
        )
        
        # Title match (very important)
        title_match = LocalRAGMatcher._calculate_keyword_match(
            resume_keywords[:10],  # Top 10 resume keywords
            job_title
        )
        
        # Weighted combination (tune these weights)
        final_score = (
            keyword_score * 0.35 +      # Keyword matching
            skill_score * 0.35 +         # Skills matching
            text_sim_score * 0.15 +      # Overall text similarity
            title_match * 0.15           # Title relevance
        )
        
        return min(final_score, 1.0)


class MatchingService:
    """Service for job matching using CTS with MongoDB"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.jobs_collection = db.jobs
        self.cache_collection = db.resume_search_cache
        self.cts_client = CTSClient()
        self.cache_expiry_hours = settings.CACHE_EXPIRY_HOURS
    
    def _generate_cache_key(
        self,
        resume_text: str,
        location: Optional[str] = None,
        internship_only: Optional[bool] = None,
        job_level: Optional[str] = None,
        stipend_min: Optional[float] = None
    ) -> str:
        """Generate cache key from search parameters"""
        cache_string = f"{resume_text}:{location}:{internship_only}:{job_level}:{stipend_min}"
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    async def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results if valid"""
        cache_entry = await self.cache_collection.find_one({
            "resume_hash": cache_key,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        if cache_entry:
            logger.info("Using cached search results")
            return cache_entry.get("matched_jobs", [])
        
        return None
    
    async def _cache_results(
        self,
        cache_key: str,
        results: List[Dict[str, Any]],
        location: Optional[str] = None,
        internship_only: Optional[bool] = None,
        job_level: Optional[str] = None,
        stipend_min: Optional[float] = None
    ):
        """Cache search results"""
        try:
            cache_entry = ResumeSearchCache(
                resume_hash=cache_key,
                location=location,
                internship_only=internship_only,
                job_level=job_level,
                stipend_min=stipend_min,
                matched_jobs=results,
                expires_at=datetime.utcnow() + timedelta(hours=self.cache_expiry_hours)
            )
            
            await self.cache_collection.insert_one(cache_entry.dict(by_alias=True))
            logger.info("Cached search results")
        except Exception as e:
            logger.error(f"Failed to cache results: {str(e)}")
    
    async def match_resume_to_jobs(
        self,
        resume_text: str,
        location: Optional[str] = None,
        internship_only: Optional[bool] = False,
        job_level: Optional[str] = None,
        stipend_min: Optional[float] = None,
        max_results: int = 50
    ) -> List[JobMatchResponse]:
        """
        Match resume to jobs using CTS
        
        Returns:
            List of matched jobs with relevance scores
        """
        # Check cache
        cache_key = self._generate_cache_key(
            resume_text, location, internship_only, job_level, stipend_min
        )
        
        cached_results = await self._get_cached_results(cache_key)
        if cached_results and len(cached_results) > 0:
            # Fetch jobs from DB
            job_ids = [ObjectId(r["job_id"]) for r in cached_results]
            cursor = self.jobs_collection.find({
                "_id": {"$in": job_ids},
                "status": "active"
            })
            jobs = await cursor.to_list(length=len(job_ids))
            
            # Map scores
            score_map = {str(r["job_id"]): r["score"] for r in cached_results}
            
            return self._build_match_responses(jobs, score_map)
        
        # Build CTS query parameters
        location_filters = [location] if location else None
        employment_types = None
        
        if internship_only:
            employment_types = ["INTERNSHIP"]
        
        # Try CTS search first, fall back to Local RAG matcher if it fails or returns empty
        jobs = []
        score_map = {}
        use_local_rag = False
        
        try:
            # Search CTS
            cts_results = self.cts_client.search_jobs_with_resume(
                resume_text=resume_text,
                location_filters=location_filters,
                employment_types=employment_types,
                max_results=max_results
            )
            
            # Check if CTS returned results
            if not cts_results or len(cts_results) == 0:
                logger.info("CTS returned empty results, using Local RAG matcher")
                use_local_rag = True
            else:
                # Map CTS results to DB jobs
                requisition_ids = [r["requisition_id"] for r in cts_results]
                cursor = self.jobs_collection.find({
                    "requisition_id": {"$in": requisition_ids},
                    "status": "active"
                })
                jobs = await cursor.to_list(length=len(requisition_ids))
                
                # Build score map from CTS results
                for cts_result in cts_results:
                    job = next(
                        (j for j in jobs if j["requisition_id"] == cts_result["requisition_id"]),
                        None
                    )
                    if job:
                        score_map[str(job["_id"])] = cts_result.get("relevance_score", 0.0)
        
        except Exception as e:
            logger.warning(f"CTS search failed, using Local RAG matcher: {str(e)}")
            use_local_rag = True
        
        # Use Local RAG matcher as fallback
        if use_local_rag:
            logger.info("🔍 Using Local RAG matcher for semantic job matching")
            
            # Build query filter
            query_filter = {"status": "active"}
            
            if location:
                query_filter["location"] = {"$regex": location, "$options": "i"}
            if internship_only:
                query_filter["is_internship"] = True
            
            # Fetch candidate jobs (fetch more for better matching)
            cursor = self.jobs_collection.find(query_filter).limit(max_results * 3)
            candidate_jobs = await cursor.to_list(length=max_results * 3)
            
            # Score each job using Local RAG matcher
            scored_jobs = []
            for job in candidate_jobs:
                relevance_score = LocalRAGMatcher.match_resume_to_job(resume_text, job)
                scored_jobs.append((job, relevance_score))
            
            # Sort by score and take top results
            scored_jobs.sort(key=lambda x: x[1], reverse=True)
            
            # Filter out low-scoring matches (threshold: 0.1)
            scored_jobs = [(job, score) for job, score in scored_jobs if score > 0.1]
            
            # Take top max_results
            scored_jobs = scored_jobs[:max_results]
            
            # Build jobs list and score map
            jobs = [job for job, score in scored_jobs]
            score_map = {str(job["_id"]): score for job, score in scored_jobs}
            
            top_score = scored_jobs[0][1] if scored_jobs else 0.0
            logger.info(f"Local RAG matcher found {len(jobs)} matches (top score: {top_score:.3f})")
        
        # Apply additional filters
        filtered_jobs = self._apply_filters(
            jobs, job_level, stipend_min, internship_only
        )
        
        # Cache results only if we found jobs
        if filtered_jobs:
            cache_data = [
                {"job_id": str(job["_id"]), "score": score_map.get(str(job["_id"]), 0.0)}
                for job in filtered_jobs
            ]
            await self._cache_results(
                cache_key, cache_data, location, internship_only, job_level, stipend_min
            )
        
        return self._build_match_responses(filtered_jobs, score_map)
    
    async def match_jd_to_jobs(
        self,
        job_description: str,
        location: Optional[str] = None,
        job_type: Optional[str] = None,
        max_results: int = 50
    ) -> List[JobMatchResponse]:
        """
        Find similar jobs based on job description
        
        Returns:
            List of similar jobs
        """
        # Build CTS query
        location_filters = [location] if location else None
        employment_types = [job_type] if job_type else None
        
        # Search CTS
        cts_results = self.cts_client.search_jobs_with_jd(
            job_description=job_description,
            location_filters=location_filters,
            employment_types=employment_types,
            max_results=max_results
        )
        
        # Map to DB jobs
        requisition_ids = [r["requisition_id"] for r in cts_results]
        cursor = self.jobs_collection.find({
            "requisition_id": {"$in": requisition_ids},
            "status": "active"
        })
        jobs = await cursor.to_list(length=len(requisition_ids))
        
        # Build score map
        score_map = {}
        for cts_result in cts_results:
            job = next(
                (j for j in jobs if j["requisition_id"] == cts_result["requisition_id"]),
                None
            )
            if job:
                score_map[str(job["_id"])] = cts_result.get("relevance_score", 0.0)
        
        return self._build_match_responses(jobs, score_map)
    
    def _apply_filters(
        self,
        jobs: List[Dict[str, Any]],
        job_level: Optional[str] = None,
        stipend_min: Optional[float] = None,
        internship_only: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Apply additional filters to job list"""
        filtered = jobs
        
        if job_level:
            filtered = [j for j in filtered if j.get("job_level") == job_level]
        
        if stipend_min is not None:
            filtered = [
                j for j in filtered
                if (j.get("salary_min") and j["salary_min"] >= stipend_min) or
                   (j.get("salary_max") and j["salary_max"] >= stipend_min)
            ]
        
        if internship_only:
            filtered = [j for j in filtered if j.get("is_internship")]
        
        return filtered
    
    def _build_match_responses(
        self,
        jobs: List[Dict[str, Any]],
        score_map: Dict[str, float]
    ) -> List[JobMatchResponse]:
        """Build JobMatchResponse objects from jobs and scores"""
        responses = []
        
        for job in jobs:
            job_id_str = str(job["_id"])
            description = job.get("description", "")
            truncated_desc = description[:500] + "..." if len(description) > 500 else description
            
            response = JobMatchResponse(
                job_id=job_id_str,
                adzuna_id=job["adzuna_id"],
                title=job["title"],
                company=job.get("company_display_name") or "Unknown",
                location=job.get("location"),
                employment_type=job.get("employment_type"),
                salary_min=job.get("salary_min"),
                salary_max=job.get("salary_max"),
                description=truncated_desc,
                redirect_url=job.get("redirect_url"),
                relevance_score=score_map.get(job_id_str, 0.0),
                is_internship=job.get("is_internship", False)
            )
            responses.append(response)
        
        # Sort by relevance score
        responses.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return responses
