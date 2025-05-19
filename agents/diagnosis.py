import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]
MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

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
    return response_body['content'][0]['text']