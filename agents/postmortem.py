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
            f"Incident: {incident}\n"
            f"Diagnosis: {diagnosis}\n"
            f"Escalation: {escalation}\n\n"
            f"Resolution: {resolution}\n\n"
            "Give a short 5-line summary for:\n"
            "1. Root cause\n"
            "2. Resolution step\n"
            "3. Learning\n"
            "4. Prevention\n"
            "5. Final status"
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "temperature": 0.5,
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