# agents/diagnosis.py
import boto3, json
import os
from dotenv import load_dotenv

load_dotenv()

def diagnose_with_bedrock(incident_description):
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

    prompt = f"Incident: {incident_description}\nGive root cause and suggest next steps."

    body = {
        "prompt": prompt,
        "max_tokens_to_sample": 300,
        "temperature": 0.7,
        "stop_sequences": ["\n"]
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    response_body = json.loads(response['body'].read().decode('utf-8'))
    return response_body.get("completion", "No result")
