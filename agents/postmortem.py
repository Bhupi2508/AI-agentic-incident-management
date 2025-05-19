# agents/postmortem.py
import boto3, json
import os
from dotenv import load_dotenv

load_dotenv()

def generate_postmortem(incident, diagnosis, resolution):
    bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

    prompt = (
        f"Incident: {incident}\n"
        f"Diagnosis: {diagnosis}\n"
        f"Resolution: {resolution}\n\n"
        f"Summarize the learnings, root cause, resolution path, and future prevention."
    )

    body = {
        "prompt": prompt,
        "max_tokens_to_sample": 300,
        "temperature": 0.6,
        "stop_sequences": ["\n"]
    }

    response = bedrock.invoke_model(
        modelId="anthropic.claude-v2",
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    response_body = json.loads(response['body'].read().decode('utf-8'))
    return response_body.get("completion", "No post-mortem generated.")
