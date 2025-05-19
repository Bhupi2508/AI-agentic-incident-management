import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

ses_client = boto3.client('ses', region_name=AWS_DEFAULT_REGION)

def send_update(incident, resolution, recipient_email):
    subject = "Incident Update"
    body_text = (f"Incident:\n{incident}\n\nResolution Summary:\n{resolution}")

    try:
        response = ses_client.send_email(
            Source="bhupsingh@deloitte.com",
            Destination={'ToAddresses': [recipient_email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")