# escalation.py
import json
import boto3
import os
from dotenv import load_dotenv

try:
    from utils.logger import log
except ImportError:
    def log(*args, **kwargs):
        print(*args)

load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID")

def diagnose_with_bedrock(incident_description):
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_DEFAULT_REGION)

    prompt_text = f"""
Incident Description: {incident_description}

Step 1: Identify the root cause of the incident.
Step 2: Suggest next steps.
Step 3: Based on the content, assign a severity level from: Blocker, Critical, High, Medium, Low

Format:
Root Cause: <your analysis>
Next Steps: <your suggestions>
Severity: <Blocker/Critical/High/Medium/Low>
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.7,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt_text
                    }
                ]
            }
        ]
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    response_body = json.loads(response['body'].read().decode('utf-8'))
    return response_body['content'][0]['text']

def escalate(severity):
    severity = severity.lower()
    if severity == "blocker":
        return "🚨 Escalated to Platform Commander + Alert all stakeholders"
    elif severity == "critical":
        return "🚨 Escalated to SME (Subject Matter Expert)"
    elif severity == "high":
        return "⚠️ Escalated to Level 3 Support"
    elif severity == "medium":
        return "📧 Escalated to Level 2 Support"
    elif severity == "low":
        return "✅ Handled by automation"
    else:
        return "⚠️ Unknown severity – fallback to automation"

def extract_severity_and_respond(diagnosis_result):
    print("111111111111111111111", diagnosis_result)
    lines = diagnosis_result.strip().splitlines()
    print("22222222222222222222", lines)
    severity_line = next((line for line in lines if line.lower().startswith("severity:")), None)
    print("33333333333333333333333", severity_line)

    if severity_line:
        severity = severity_line.split(":", 1)[1].strip()
        escalation_action = escalate(severity)
        return {
            "diagnosis_result": diagnosis_result,
            "severity": severity,
            "escalation_action": escalation_action
        }
    else:
        return {
            "diagnosis_result": diagnosis_result,
            "severity": "Not found",
            "escalation_action": "⚠️ No escalation - fallback to automation"
        }