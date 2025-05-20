import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
EMAIL_SEND_TO = os.getenv("EMAIL_SEND_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")

def send_test_email(incident_summary, escalation_message, resolution_message, incident_Id, email_recipient=None):
    print(":::::: Print :::::: ", incident_summary, escalation_message, resolution_message, email_recipient, incident_Id)

    ses_client = boto3.client('ses', region_name=AWS_DEFAULT_REGION)
    to_email = EMAIL_SEND_TO or email_recipient
    subject = "🚨 Incident Report : Action Taken & Resolution Summary"

    body_html = f"""
    <html>
    <head>
      <style>
        body {{
          font-family: Arial, sans-serif;
          color: #333;
          line-height: 1.6;
        }}
        .container {{
          border: 1px solid #ccc;
          padding: 20px;
          border-radius: 8px;
          background-color: #f9f9f9;
        }}
        .header {{
          background-color: #f44336;
          color: white;
          padding: 10px;
          font-size: 18px;
          border-radius: 6px 6px 0 0;
        }}
        .section {{
          margin-top: 15px;
        }}
        .section-title {{
          font-weight: bold;
          color: #000;
        }}
        .footer {{
          margin-top: 30px;
          font-size: 14px;
          color: #666;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">🚨 Incident Report</div>
        
        <div class="section">
          <div class="section-title">🧾 Incident ID:</div>
          <div>{incident_Id}</div>
        </div>

        <div class="section">
          <div class="section-title">🧾 Incident Summary:</div>
          <div>{incident_summary}</div>
        </div>

        <div class="section">
          <div class="section-title">📣 Escalation Details:</div>
          <div>{escalation_message}</div>
        </div>

        <div class="section">
          <div class="section-title">✅ Resolution Applied:</div>
          <div>{resolution_message}</div>
        </div>

        <div class="footer">
          Regards,<br/>
          <strong>Automation System 🤖</strong>
        </div>
      </div>
    </body>
    </html>
    """

    try:
        response = ses_client.send_email(
            Source=EMAIL_FROM,
            Destination={'ToAddresses': [to_email]},
            Message={
                'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                'Body': {
                    'Html': {
                        'Data': body_html,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        print("✅ Email successfully sent!", response)
    except ClientError as e:
        print("❌ Email sending failed:", e.response['Error']['Message'])