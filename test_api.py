"""
Quick test script to verify the MongoDB-based job matching API
"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_api():
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Job Matching API")
        print("=" * 50)
        
        # 1. Health Check
        print("\n1️⃣ Testing Health Check...")
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Check: {data['status']}")
                print(f"   MongoDB: {data['database']}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            print("   Make sure the server is running: uvicorn app.main:app --reload")
            return
        
        # 2. List Jobs
        print("\n2️⃣ Testing Job Listing...")
        try:
            response = await client.get(
                f"{BASE_URL}/jobs",
                params={"limit": 5, "skip": 0}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['total']} total jobs")
                print(f"   Showing {len(data['jobs'])} jobs")
                if data['jobs']:
                    job = data['jobs'][0]
                    print(f"   Example: {job['title']} at {job['company']}")
            else:
                print(f"⚠️ Job listing returned: {response.status_code}")
                print("   This is expected if no jobs synced yet")
        except Exception as e:
            print(f"❌ Job listing failed: {e}")
        
        # 3. Test Resume Matching
        print("\n3️⃣ Testing Resume Matching...")
        try:
            resume_data = {
                "resume_text": """
                Experienced Python developer with 5 years in backend development.
                Proficient in FastAPI, Django, and Flask.
                Strong experience with MongoDB, PostgreSQL, and Redis.
                Built scalable microservices on AWS and Google Cloud.
                Expert in RESTful API design and async programming.
                """,
                "location": "San Francisco, CA",
                "job_level": "MID_LEVEL",
                "stipend_min": 80000
            }
            
            response = await client.post(
                f"{BASE_URL}/match/resume",
                json=resume_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Resume matching successful")
                print(f"   Total matches: {data['total_matches']}")
                print(f"   Search time: {data['search_time_ms']:.2f}ms")
                
                if data['jobs']:
                    print(f"\n   Top 3 Matches:")
                    for i, job in enumerate(data['jobs'][:3], 1):
                        score = job.get('relevance_score', 0)
                        print(f"   {i}. {job['title']} at {job['company']}")
                        print(f"      Relevance: {score:.2f} | Location: {job.get('location', 'N/A')}")
            else:
                print(f"⚠️ Resume matching returned: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Resume matching failed: {e}")
        
        # 4. Test Job Description Matching
        print("\n4️⃣ Testing Job Description Matching...")
        try:
            jd_data = {
                "job_description": """
                We're looking for a talented backend engineer to join our team.
                Must have experience with Python, FastAPI, and cloud platforms.
                MongoDB or PostgreSQL experience required.
                """,
                "location": "Remote"
            }
            
            response = await client.post(
                f"{BASE_URL}/match/jd",
                json=jd_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ JD matching successful")
                print(f"   Total matches: {data['total_matches']}")
                print(f"   Search time: {data['search_time_ms']:.2f}ms")
                
                if data['jobs']:
                    print(f"\n   Top 3 Similar Jobs:")
                    for i, job in enumerate(data['jobs'][:3], 1):
                        score = job.get('relevance_score', 0)
                        print(f"   {i}. {job['title']} at {job['company']}")
                        print(f"      Score: {score:.2f}")
            else:
                print(f"⚠️ JD matching returned: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ JD matching failed: {e}")
        
        # 5. Test Filters
        print("\n5️⃣ Testing Filters (Internships)...")
        try:
            response = await client.get(
                f"{BASE_URL}/jobs",
                params={
                    "internship": True,
                    "remote": True,
                    "limit": 3
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Filter test successful")
                print(f"   Found {data['total']} remote internships")
                
                for job in data['jobs'][:3]:
                    print(f"   • {job['title']} at {job['company']}")
            else:
                print(f"⚠️ Filter test returned: {response.status_code}")
        except Exception as e:
            print(f"❌ Filter test failed: {e}")
        
        print("\n" + "=" * 50)
        print("✅ API Testing Complete!")
        print("\n💡 Next Steps:")
        print("   1. If no jobs found, trigger sync: curl -X POST http://localhost:8000/admin/refresh-jobs")
        print("   2. Visit API docs: http://localhost:8000/docs")
        print("   3. Check MongoDB for data using Atlas UI")

if __name__ == "__main__":
    asyncio.run(test_api())

