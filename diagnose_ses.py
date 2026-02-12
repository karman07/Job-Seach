"""
AWS SES Diagnostic Script
Checks SES configuration, sender verification, and sending limits
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import boto3
from botocore.exceptions import ClientError
from app.config import get_settings

settings = get_settings()

print("=" * 70)
print("AWS SES DIAGNOSTIC REPORT")
print("=" * 70)

# Initialize SES client
try:
    ses_client = boto3.client(
        'ses',
        region_name=settings.AWS_SES_REGION,
        aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY
    )
    print("✅ SES Client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize SES client: {e}")
    sys.exit(1)

print(f"\n📍 Region: {settings.AWS_SES_REGION}")
print(f"📧 From Email: {settings.AWS_SES_FROM_EMAIL}")
print(f"🔑 Access Key: {settings.AWS_SES_ACCESS_KEY_ID[:10]}...")

# Check account sending status
print("\n" + "=" * 70)
print("ACCOUNT SENDING STATUS")
print("=" * 70)

try:
    account_info = ses_client.get_account_sending_enabled()
    if account_info.get('Enabled'):
        print("✅ Account sending is ENABLED")
    else:
        print("❌ Account sending is DISABLED")
except ClientError as e:
    print(f"❌ Error checking account status: {e.response['Error']['Message']}")

# Check sending quota
print("\n" + "=" * 70)
print("SENDING QUOTA & LIMITS")
print("=" * 70)

try:
    quota = ses_client.get_send_quota()
    print(f"📊 Max 24h send: {quota['Max24HourSend']}")
    print(f"📊 Max send rate: {quota['MaxSendRate']} emails/second")
    print(f"📊 Sent last 24h: {quota['SentLast24Hours']}")
    
    remaining = quota['Max24HourSend'] - quota['SentLast24Hours']
    print(f"📊 Remaining quota: {remaining}")
    
    if quota['Max24HourSend'] == 200:
        print("\n⚠️  WARNING: You are in SES SANDBOX mode")
        print("   - You can only send to verified email addresses")
        print("   - Limited to 200 emails per 24 hours")
        print("   - Request production access to remove restrictions")
except ClientError as e:
    print(f"❌ Error checking quota: {e.response['Error']['Message']}")

# Check verified email addresses
print("\n" + "=" * 70)
print("VERIFIED EMAIL IDENTITIES")
print("=" * 70)

try:
    identities = ses_client.list_identities(IdentityType='EmailAddress')
    verified_emails = identities.get('Identities', [])
    
    if verified_emails:
        print(f"✅ Found {len(verified_emails)} verified email(s):")
        for email in verified_emails:
            # Check verification status
            try:
                attrs = ses_client.get_identity_verification_attributes(Identities=[email])
                status = attrs['VerificationAttributes'].get(email, {}).get('VerificationStatus', 'Unknown')
                
                if status == 'Success':
                    print(f"   ✅ {email} - Verified")
                else:
                    print(f"   ⚠️  {email} - Status: {status}")
            except:
                print(f"   ❓ {email} - Status unknown")
        
        # Check if FROM email is verified
        if settings.AWS_SES_FROM_EMAIL in verified_emails:
            print(f"\n✅ Your FROM email ({settings.AWS_SES_FROM_EMAIL}) is verified!")
        else:
            print(f"\n❌ WARNING: Your FROM email ({settings.AWS_SES_FROM_EMAIL}) is NOT verified!")
            print("   You must verify this email before sending.")
            print(f"\n   To verify, run:")
            print(f"   aws ses verify-email-identity --email-address {settings.AWS_SES_FROM_EMAIL} --region {settings.AWS_SES_REGION}")
    else:
        print("❌ No verified email addresses found!")
        print(f"\n   To verify your FROM email, run:")
        print(f"   aws ses verify-email-identity --email-address {settings.AWS_SES_FROM_EMAIL} --region {settings.AWS_SES_REGION}")
        
except ClientError as e:
    print(f"❌ Error listing identities: {e.response['Error']['Message']}")

# Check verified domains
print("\n" + "=" * 70)
print("VERIFIED DOMAINS")
print("=" * 70)

try:
    domains = ses_client.list_identities(IdentityType='Domain')
    verified_domains = domains.get('Identities', [])
    
    if verified_domains:
        print(f"✅ Found {len(verified_domains)} verified domain(s):")
        for domain in verified_domains:
            print(f"   ✅ {domain}")
    else:
        print("ℹ️  No verified domains found (email verification is sufficient)")
        
except ClientError as e:
    print(f"❌ Error listing domains: {e.response['Error']['Message']}")

# Test email sending capability
print("\n" + "=" * 70)
print("EMAIL SENDING TEST")
print("=" * 70)

test_email = input("\nEnter a verified email address to test sending (or press Enter to skip): ").strip()

if test_email:
    print(f"\n📤 Attempting to send test email to: {test_email}")
    
    try:
        response = ses_client.send_email(
            Source=settings.AWS_SES_FROM_EMAIL,
            Destination={'ToAddresses': [test_email]},
            Message={
                'Subject': {'Data': '🧪 SES Diagnostic Test Email', 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {
                        'Data': '''
                        <html>
                        <body style='font-family: Arial, sans-serif;'>
                            <h2 style='color: #27ae60;'>✅ AWS SES is Working!</h2>
                            <p>This test email confirms that your AWS SES integration is configured correctly.</p>
                            <p><strong>Configuration Details:</strong></p>
                            <ul>
                                <li>Region: ''' + settings.AWS_SES_REGION + '''</li>
                                <li>From: ''' + settings.AWS_SES_FROM_EMAIL + '''</li>
                            </ul>
                            <hr>
                            <p style='font-size: 12px; color: #95a5a6;'>Job Matching API - SES Diagnostic Test</p>
                        </body>
                        </html>
                        ''',
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        
        message_id = response.get('MessageId')
        print(f"\n✅ SUCCESS! Email sent successfully")
        print(f"   Message ID: {message_id}")
        print(f"   Check {test_email} inbox (and spam folder)")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"\n❌ FAILED to send email")
        print(f"   Error Code: {error_code}")
        print(f"   Error Message: {error_message}")
        
        if error_code == 'MessageRejected':
            print("\n   💡 Common causes:")
            print("      - FROM email is not verified")
            print("      - TO email is not verified (in sandbox mode)")
            print("      - Email address format is invalid")
        elif error_code == 'AccessDenied':
            print("\n   💡 Your AWS credentials may not have SES permissions")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
else:
    print("\nℹ️  Skipping email send test")

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)

print("\n📋 NEXT STEPS:")
print("1. Ensure your FROM email is verified in SES")
print("2. If in sandbox mode, verify recipient emails OR request production access")
print("3. Check that your AWS credentials have ses:SendEmail permission")
print("4. Monitor CloudWatch logs for detailed error information")
print("\n")
