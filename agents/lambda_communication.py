import boto3
from botocore.exceptions import ClientError
import os
import json
from datetime import datetime

# Environment variables
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
EMAIL_SEND_TO = os.getenv("EMAIL_SEND_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM")

# Logging utility
def log(message):
    print(f"[LOG] {datetime.now().isoformat()}: {message}")

# Email sender function
def send_test_email(incident_summary, escalation_message, resolution_message, incident_Id, email_recipient=None):
    log(f"incident_summary :: {incident_summary}")
    log(f"escalation_message :: {escalation_message}")
    log(f"resolution_message :: {resolution_message}")
    log(f"incident_Id :: {incident_Id}")
    log(f"email_recipient :: {email_recipient}")

    should_escalate = escalation_message.get('should_escalate', False)
    if not should_escalate:
        msg = f"ℹ️ No escalation required for Incident #{incident_Id}. Email not sent."
        log(msg)
        return msg

    # SES client
    ses_client = boto3.client('ses', region_name=AWS_DEFAULT_REGION)
    to_email = email_recipient or EMAIL_SEND_TO

    # Email content
    subject = f"[JIRA][AUTO-ALERT] 🚨 Incident #{incident_Id} – Escalation & Resolution Summary"
    priority = escalation_message.get('severity', "Medium")
    escalation_notes = escalation_message.get('escalation_action', "")

    body_html = f"""
    <html>
    <head><style>
        body {{ font-family: Arial; background-color: #f4f5f7; color: #172b4d; }}
        .jira-box {{ background: #fff; max-width: 700px; margin: auto; border: 1px solid #dfe1e6; border-radius: 5px; padding: 20px; }}
        .jira-header {{ background: #0052cc; color: white; padding: 15px; font-size: 18px; border-radius: 5px 5px 0 0; }}
        .jira-section {{ padding: 10px 0; border-bottom: 1px solid #dfe1e6; }}
        .jira-label {{ font-weight: bold; color: #42526e; display: inline-block; min-width: 150px; }}
        .jira-footer {{ padding-top: 20px; font-size: 12px; color: #5e6c84; }}
    </style></head>
    <body>
      <div class="jira-box">
        <div class="jira-header">[JIRA][AUTO-ALERT] 🚨 Incident #{incident_Id} – Escalation & Resolution Summary</div>
        <div class="jira-section"><span class="jira-label">Incident ID:</span> {incident_Id}</div>
        <div class="jira-section"><span class="jira-label">Issue Type:</span> Bug / Incident</div>
        <div class="jira-section"><span class="jira-label">Priority:</span> {priority}</div>
        <div class="jira-section"><span class="jira-label">Summary:</span> {incident_summary}</div>
        <div class="jira-section"><span class="jira-label">Escalation Notes:</span> {escalation_notes}</div>
        <div class="jira-section"><span class="jira-label">Resolution:</span> {resolution_message}</div>
        <div class="jira-section"><span class="jira-label">Reported By:</span> Automation AI Bot 🤖</div>
        <div class="jira-footer">This is an automated alert. Please do not reply to this email.</div>
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
                'Body': {'Html': {'Data': body_html, 'Charset': 'UTF-8'}}
            }
        )
        log(f"✅ Email sent. SES Response: {response}")
        return f"✅ Email sent successfully for Incident #{incident_Id}"
    except ClientError as e:
        error_msg = e.response['Error']['Message']
        log(f"❌ Email sending failed: {error_msg}")
        return f"❌ Email sending failed: {error_msg}"

# Lambda handler
def lambda_handler(event, context):
    try:
        body = event.get('body')
        if not body:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Missing body in request'})}

        # Parse body if it's a string (API Gateway format)
        if isinstance(body, str):
            body = json.loads(body)

        # Extract inputs
        incident_summary = body.get('incident_summary_comm')
        escalation_message = body.get('escalation_message_comm', {})
        resolution_message = body.get('resolution_message_comm')
        incident_Id = body.get('incident_Id_comm')
        email_recipient = body.get('email_recipient_comm')

        # Validate required fields
        missing_fields = [k for k, v in {
            "incident_summary": incident_summary,
            "escalation_message": escalation_message,
            "resolution_message": resolution_message,
            "incident_Id": incident_Id
        }.items() if not v]

        if missing_fields:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing fields: {", ".join(missing_fields)}'})
            }

        # Send the email
        result = send_test_email(
            incident_summary,
            escalation_message,
            resolution_message,
            incident_Id,
            email_recipient
        )

        return {'statusCode': 200, 'body': json.dumps({'message': result})}

    except Exception as e:
        log(f"❌ Exception in lambda_handler: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}