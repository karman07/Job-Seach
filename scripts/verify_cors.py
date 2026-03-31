import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8080"  # User running on port 8080

async def verify_cors():
    print("Startup verification script...")
    async with httpx.AsyncClient() as client:
        print(f"Connecting to {BASE_URL}...")
        try:
            # Check server is up first
            resp = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if resp.status_code != 200:
                print(f"⚠️ Server returned {resp.status_code} on /health")
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            print("Please ensure 'uvicorn app.main:app --reload --port 8080' is running.")
            return

        print("🧪 Testing CORS Configuration")
        print("=" * 50)
        
        # 1. Test Allowed Origin (React/Next.js)
        origin = "http://localhost:3000"
        print(f"\n1️⃣ Testing Allowed Origin: {origin}")
        try:
            response = await client.options(
                f"{BASE_URL}/health",
                headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
            )
            
            allow_origin = response.headers.get('access-control-allow-origin')
            allow_creds = response.headers.get('access-control-allow-credentials')
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Access-Control-Allow-Origin: {allow_origin}")
            print(f"   Access-Control-Allow-Credentials: {allow_creds}")
            
            if (response.status_code == 200 and 
                allow_origin == origin and
                allow_creds == 'true'):
                print("✅ CORS headers correct for allowed origin")
            else:
                print("❌ CORS headers INCORRECT for allowed origin")
        except Exception as e:
            print(f"❌ Request failed: {e}")

        # 2. Test Disallowed Origin
        origin = "http://evil-site.com"
        print(f"\n2️⃣ Testing Disallowed Origin: {origin}")
        try:
            response = await client.options(
                f"{BASE_URL}/health",
                headers={"Origin": origin, "Access-Control-Request-Method": "GET"}
            )
            
            allow_origin = response.headers.get('access-control-allow-origin')
            if not allow_origin or allow_origin != origin:
                print("✅ CORS headers correct (origin not allowed)")
            else:
                print(f"❌ Security Risk: Disallowed origin was allowed! ({allow_origin})")
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_cors())
