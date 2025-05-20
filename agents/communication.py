import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
EMAIL_SEND_TO = os.getenv("EMAIL_SEND_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")

def send_test_email(incident_summary, escalation_message, resolution_message, email_recipient=None):
    ses_client = boto3.client('ses', region_name=AWS_DEFAULT_REGION)
    
    to_email = email_recipient or EMAIL_SEND_TO

    subject = "🚨 Incident Report: Action Taken & Resolution Summary"
    
    body_text = f"""
🧾 Incident Summary:
{incident_summary}

📣 Escalation Details:
{escalation_message}

✅ Resolution Applied:
{resolution_message}

Regards,
Automation System 🤖
"""

    try:
        response = ses_client.send_email(
            Source=EMAIL_FROM,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {
                        'Data': body_text
                    }
                }
            }
        )
        print("✅ Email successfully sent!", response)
    except ClientError as e:
        print("❌ Email sending failed:", e.response['Error']['Message'])