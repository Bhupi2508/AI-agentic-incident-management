import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]
MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

def diagnose_with_bedrock(incident_description):
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_DEFAULT_REGION)

    prompt_text = f"""Incident: {incident_description}

Give the root cause and suggest next steps.

Also, provide a severity level in one word at the end. (Options: Low, Medium, High)

Format the response exactly as:

Root Cause: <your analysis>
Next Steps: <your suggestions>
Severity: <Low/Medium/High>
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