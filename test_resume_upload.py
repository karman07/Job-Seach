#!/usr/bin/env python3
"""
Test script for the resume upload and matching endpoint
"""
import requests
import sys
from pathlib import Path


def test_resume_upload(file_path: str, base_url: str = "http://localhost:8000"):
    """
    Test the resume upload endpoint
    
    Args:
        file_path: Path to the resume file (PDF, DOCX, or TXT)
        base_url: Base URL of the API (default: http://localhost:8000)
    """
    endpoint = f"{base_url}/match/resume/upload"
    
    # Check if file exists
    file = Path(file_path)
    if not file.exists():
        print(f"❌ Error: File not found: {file_path}")
        return False
    
    # Check file extension
    allowed_extensions = {'.pdf', '.docx', '.txt'}
    if file.suffix.lower() not in allowed_extensions:
        print(f"❌ Error: Invalid file format. Allowed: {', '.join(allowed_extensions)}")
        return False
    
    print(f"📄 Uploading resume: {file.name}")
    print(f"📍 Endpoint: {endpoint}")
    print(f"🔄 Processing...\n")
    
    try:
        # Upload file
        with open(file_path, 'rb') as f:
            files = {'file': f}
            
            # Optional: Add query parameters
            params = {
                'location': 'San Francisco, CA',  # Modify as needed
                'internship_only': False,
                # 'job_level': 'ENTRY_LEVEL',  # Uncomment to filter by level
                # 'stipend_min': 80000,  # Uncomment to set minimum salary
            }
            
            response = requests.post(endpoint, files=files, params=params)
        
        # Check response
        if response.status_code == 200:
            data = response.json()
            
            print("✅ SUCCESS!")
            print(f"📊 Total Matches: {data['total_matches']}")
            print(f"⏱️  Search Time: {data['search_time_ms']:.2f}ms")
            print(f"\n📋 Metadata:")
            for key, value in data['metadata'].items():
                print(f"   • {key}: {value}")
            
            if data['jobs']:
                print(f"\n🎯 Top 5 Matching Jobs:")
                print("-" * 80)
                
                for i, job in enumerate(data['jobs'][:5], 1):
                    print(f"\n{i}. {job['title']}")
                    print(f"   Company: {job['company']}")
                    print(f"   Location: {job['location']}")
                    print(f"   Type: {job['employment_type']}")
                    if job.get('salary_min') and job.get('salary_max'):
                        print(f"   Salary: ${job['salary_min']:,} - ${job['salary_max']:,}")
                    print(f"   Relevance Score: {job['relevance_score']:.2f}")
                    print(f"   Apply: {job['redirect_url']}")
            
            return True
        else:
            print(f"❌ Error {response.status_code}: {response.json().get('detail', 'Unknown error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to {base_url}")
        print("💡 Make sure the API is running (python quickstart.py or ./run.sh)")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_resume_upload.py <path_to_resume_file>")
        print("\nExample:")
        print("  python test_resume_upload.py ~/Documents/my_resume.pdf")
        print("  python test_resume_upload.py resume.docx")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # You can change the base URL if your API is running elsewhere
    base_url = "http://localhost:8000"
    
    success = test_resume_upload(file_path, base_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
