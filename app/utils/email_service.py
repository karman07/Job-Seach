import boto3
from botocore.exceptions import ClientError
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmailService:
    """Email service using AWS SES"""
    
    @staticmethod
    def send_email(to_email: str, subject: str, body_html: str):
        """Send email using AWS SES"""
        try:
            # Create SES client
            ses_client = boto3.client(
                'ses',
                region_name=settings.AWS_SES_REGION,
                aws_access_key_id=settings.AWS_SES_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SES_SECRET_ACCESS_KEY
            )
            
            # Send email
            response = ses_client.send_email(
                Source=settings.AWS_SES_FROM_EMAIL,
                Destination={
                    'ToAddresses': [to_email]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Html': {
                            'Data': body_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            logger.info(f"Email sent successfully to {to_email}. MessageId: {response['MessageId']}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to send email to {to_email}. Error: {error_code} - {error_message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
            return False
