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

    should_escalate = escalation_message.get('should_escalate', False)

    # Check escalation flag before proceeding
    if not should_escalate:
        print(f"ℹ️ No escalation required for Incident #{incident_Id}. Email will not be sent.")
        return f"ℹ️ No escalation required for Incident #{incident_Id}. Email not sent."
    
    print("escalation_message, Whether should escalate :::: ", escalation_message['should_escalate'])
    ses_client = boto3.client('ses', region_name=AWS_DEFAULT_REGION)
    to_email = email_recipient or EMAIL_SEND_TO

    subject = f"[JIRA][AUTO-ALERT] 🚨 Incident #{incident_Id} – Escalation & Resolution Summary"
    escalation_message_data = escalation_message.get('severity', "Medium")
    escalation_message_action = escalation_message.get('escalation_action', "")

    body_html = f"""
<html>
<head>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #f4f5f7;
      color: #172b4d;
    }}
    .jira-box {{
      background-color: #ffffff;
      max-width: 700px;
      margin: auto;
      border: 1px solid #dfe1e6;
      border-radius: 5px;
      padding: 20px;
    }}
    .jira-header {{
      background-color: #0052cc;
      color: white;
      padding: 15px;
      font-size: 18px;
      border-radius: 5px 5px 0 0;
    }}
    .jira-section {{
      padding: 10px 0;
      border-bottom: 1px solid #dfe1e6;
    }}
    .jira-label {{
      font-weight: bold;
      color: #42526e;
      display: inline-block;
      min-width: 150px;
    }}
    .jira-footer {{
      padding-top: 20px;
      font-size: 12px;
      color: #5e6c84;
    }}
  </style>
</head>
<body>
  <div class="jira-box">
    <div class="jira-header">[JIRA][AUTO-ALERT] 🚨 Incident #{incident_Id} – Escalation & Resolution Summary</div>
    
    <div class="jira-section">
      <span class="jira-label">Incident ID:</span> {incident_Id}
    </div>

    <div class="jira-section">
      <span class="jira-label">Issue Type:</span> Bug / Incident
    </div>

    <div class="jira-section">
      <span class="jira-label">Priority:</span> {escalation_message_data}
    </div>

    <div class="jira-section">
      <span class="jira-label">Summary:</span> {incident_summary}
    </div>

    <div class="jira-section">
      <span class="jira-label">Escalation Notes:</span> {escalation_message_action}
    </div>

    <div class="jira-section">
      <span class="jira-label">Resolution:</span> {resolution_message}
    </div>

    <div class="jira-section">
      <span class="jira-label">Reported By:</span> Automation AI Bot 🤖
    </div>

    <div class="jira-footer">
      This is an automated alert generated by the monitoring system.<br/>
      Please do not reply to this email.
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
        return f"✅ Email sent successfully for Incident #{incident_Id}"
    except ClientError as e:
        error_msg = e.response['Error']['Message']
        print("❌ Email sending failed:", error_msg)
        return f"❌ Email sending failed: {error_msg}"