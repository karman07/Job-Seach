"""
Test script to verify AWS SES email sending
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.email_service import EmailService
from app.config import get_settings

settings = get_settings()

print("=" * 60)
print("AWS SES Email Service Test")
print("=" * 60)
print(f"AWS Region: {settings.AWS_SES_REGION}")
print(f"From Email: {settings.AWS_SES_FROM_EMAIL}")
print(f"Access Key ID: {settings.AWS_SES_ACCESS_KEY_ID[:10]}...")
print("=" * 60)

# Test email
test_email = input("\nEnter test email address to send to: ").strip()

if not test_email:
    print("No email provided. Exiting.")
    sys.exit(1)

print(f"\nSending test email to: {test_email}")

body_html = """
<html>
<body style='font-family: Arial, sans-serif;'>
    <h2 style='color: #2c3e50;'>Test Email from Job Matching API</h2>
    <p>This is a test email to verify AWS SES integration.</p>
    <p>If you received this, your email service is working correctly! 🎉</p>
    <hr>
    <p style='font-size: 12px; color: #95a5a6;'>
        Sent from Job Matching API - AWS SES Test
    </p>
</body>
</html>
"""

try:
    result = EmailService.send_email(
        to_email=test_email,
        subject="🧪 Test Email - Job Matching API",
        body_html=body_html
    )
    
    if result:
        print("\n✅ SUCCESS! Email sent successfully.")
        print("Check your inbox (and spam folder) for the test email.")
    else:
        print("\n❌ FAILED! Email was not sent. Check logs above for errors.")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
