import boto3
import json
import os

# You can set these as Lambda environment variables
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-west-2")
MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-v2")

def lambda_handler(event, context):
    try:
        # Extract data from event (assuming JSON input)
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        incident = body.get("incident", "")
        diagnosis = body.get("diagnosis", "")
        resolution = body.get("resolution", "")
        escalation = body.get("escalation", "")

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

        payload = {
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
            body=json.dumps(payload)
        )

        response_body = json.loads(response['body'].read().decode('utf-8'))
        generated_text = response_body['content'][0]['text'].strip()

        return {
            "statusCode": 200,
            "body": json.dumps({"postmortem": generated_text})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Post-mortem generation failed: {str(e)}"})
        }