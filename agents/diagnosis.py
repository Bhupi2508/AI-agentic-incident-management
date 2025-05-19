import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]
MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

def calculate_confidence(output_text):
    high_keywords = ["definitely", "confirmed", "clearly", "root cause is"]
    medium_keywords = ["likely", "possibly", "might be", "appears to be"]
    low_keywords = ["may be", "unsure", "unclear", "unknown", "cannot determine"]

    text = output_text.lower()

    if any(k in text for k in high_keywords):
        return 0.9
    elif any(k in text for k in medium_keywords):
        return 0.6
    elif any(k in text for k in low_keywords):
        return 0.3
    return 0.5  # Default neutral confidence

def needs_human_intervention(ai_output, confidence_score):
    # Check if all required parts exist
    required_parts = ["Root Cause:", "Next Steps:", "Severity:"]
    if not all(part in ai_output for part in required_parts):
        return True

    # Extract severity
    severity_line = [line for line in ai_output.split('\n') if line.startswith("Severity:")]
    severity = severity_line[0].split(":")[1].strip() if severity_line else ""

    # Decision logic
    if confidence_score < 0.6:
        return True
    if severity.lower() == "high":
        return True
    return False

def diagnose_with_bedrock(incident_description):
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_DEFAULT_REGION)

    prompt_text = f"""
You are an expert Incident Diagnosis AI Agent.

Your responsibilities:
1. Analyze the incident.
2. Identify the root cause.
3. Recommend immediate next steps.
4. Based on the following Severity Decision Table, assign a severity.

---

**Severity Decision Table**

- Blocker:
  - Entire system/platform is down
  - Login/authentication failure
  - Database outage
  - Affects all users
  - No workaround available

- Critical:
  - Payment or core business flow fails
  - Data loss/corruption
  - Major API or service is unresponsive
  - Affects large user group
  - No immediate workaround

- High:
  - Some services degraded or failing
  - Affects some users
  - Workaround exists (e.g., restart)

- Medium:
  - Internal tool issue
  - Performance slowness
  - Feature fails for niche case

- Low:
  - UI glitch
  - Cosmetic bugs
  - Logging issues
  - No business impact

---

Respond in **strict JSON format** like this:

{{
  "root_cause": "<your analysis>",
  "next_steps": "<your suggestions>",
  "severity": "<Blocker/Critical/High/Medium/Low>"
}}

Incident: {incident_description}
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.3,
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

    output_text = response_body['content'][0]['text']

    confidence_score = calculate_confidence(output_text)
    intervention_required = needs_human_intervention(output_text, confidence_score)

    return {
        "diagnosis": output_text,
        "confidence_score": round(confidence_score, 2),
        "needs_human_intervention": intervention_required
    }
