import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

BEDROCK_REGION = os.environ["BEDROCK_REGION"]
MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

def generate_postmortem(incident, diagnosis, resolution, escalation):
    try:
        bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

        prompt = (
            f"Create a detailed postmortem report based on the following incident details:\n\n"
            f"Incident Description:\n{incident}\n\n"
            f"Diagnosis Details:\n{diagnosis}\n\n"
            f"Escalation Steps Taken:\n{escalation}\n\n"
            f"Resolution Actions:\n{resolution}\n\n"
            "Format the postmortem with the following sections:\n"
            "1. Incident Summary (brief description and impact)\n"
            "2. Root Cause Analysis (what caused the issue)\n"
            "3. Resolution and Mitigation (how the issue was fixed)\n"
            "4. Timeline of Events (step-by-step timeline)\n"
            "5. Lessons Learned (what was learned to avoid future issues)\n"
            "6. Action Items (next steps, who is responsible, deadlines)\n\n"
            "Use clear, concise language. You can use bullet points if needed.\n"
            "Keep it professional and easy to understand."
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
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
        return response_body['content'][0]['text'].strip()

    except Exception as e:
        return f"Post-mortem generation failed: {str(e)}"