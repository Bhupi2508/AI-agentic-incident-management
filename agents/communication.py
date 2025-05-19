import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
EMAIL_SEND_TO = os.getenv("EMAIL_SEND_TO")

def send_test_email():
    ses_client = boto3.client('ses', region_name=AWS_DEFAULT_REGION)

    try:
        response = ses_client.send_email(
            Source=EMAIL_SEND_TO,
            Destination={'ToAddresses': [EMAIL_SEND_TO]},
            Message={
                'Subject': {'Data': 'Test Email from SES'},
                'Body': {'Text': {'Data': 'This is a test email'}}
            }
        )
        print("Email sent!", response)
    except ClientError as e:
        print("Error:", e.response['Error']['Message'])

send_test_email()