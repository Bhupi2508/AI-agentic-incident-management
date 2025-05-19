import boto3
import json
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

if not AWS_DEFAULT_REGION or not MODEL_ID:
    raise EnvironmentError("Missing AWS_DEFAULT_REGION or BEDROCK_MODEL_ID in .env")


import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "YOUR_MODEL_ID_HERE")

# Simple logger function

def log(*args):
    print("[BedrockDiagnosis]", *args)


def diagnose_with_bedrock(incident_description):
    """
    Diagnose incidents using Amazon Bedrock AI.

    Returns a dict with diagnosis JSON, confidence score, and a flag indicating if human intervention is needed.
    """
    # 1. Initialize client
    log("Initializing Bedrock client in region", AWS_DEFAULT_REGION)
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_DEFAULT_REGION)

    # 2. Build prompt
    prompt_text = f"""
                You are an expert Incident Diagnosis AI Agent.

                Your task is to:
                1. Analyze the incident.
                2. Identify the root cause.
                3. Recommend immediate next steps.
                4. Optionally, assign a severity level based on your understanding.

                Respond in strict JSON format:
                {
                    "root_cause": "<your analysis>",
                    "next_steps": "<your suggestions>",
                    "severity": "<Blocker/Critical/High/Medium/Low>"
                }

                Incident:
                {incident_description}
                """
    log("Prompt built:", prompt_text.replace(incident_description, "<incident_desc>"))

    # 3. Prepare payload
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
    }
    log("Payload prepared:", json.dumps(body, indent=2))

    try:
        # 4. Invoke model
        log("Invoking model... 🚀")
        response = bedrock.invoke_model(
            modelId=MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        log("Model invocation complete.")

        # 5. Parse response
        raw_body = response["body"]
        if isinstance(raw_body, bytes):
            raw_body = raw_body.decode("utf-8")
        resp_json = json.loads(raw_body)
        log("Raw response JSON:", json.dumps(resp_json, indent=2))

        output_text = resp_json["content"][0]["text"].strip()
        log("Model output:", output_text)

        # 6. Compute confidence and intervention
        confidence_score = calculate_confidence(output_text)
        intervention_required = needs_human_intervention(output_text, confidence_score)
        log("Confidence Score:", confidence_score)
        log("Needs Human Intervention:", intervention_required)

        # 7. Return structured result
        return {
            "diagnosis": output_text,
            "confidence_score": round(confidence_score, 2),
            "needs_human_intervention": intervention_required,
        }

    except Exception as e:
        log("Error during diagnosis:", str(e))
        raise


# Example usage
if __name__ == "__main__":
    test_incident = "Service X returned 500 errors intermittently under high load."
    result = diagnose_with_bedrock(test_incident)
    log("Final result:", result)




def calculate_confidence(output_text):
    high_keywords = ["definitely", "clearly", "confirmed", "root cause is", "100%"]
    medium_keywords = ["likely", "possibly", "might be", "appears to be", "could be"]
    low_keywords = [
        "may be",
        "unsure",
        "unclear",
        "unknown",
        "not sure",
        "cannot determine",
        "no idea",
        "Based on the limited information provided"
    ]

    text = output_text.lower()

    if any(k in text for k in high_keywords):
        return 0.9
    elif any(k in text for k in medium_keywords):
        return 0.6
    elif any(k in text for k in low_keywords):
        return 0.3
    return 0.5  # Neutral confidence


def needs_human_intervention(ai_output, confidence_score):
    required_parts = ["root_cause", "next_steps", "severity"]
    try:
        data = json.loads(ai_output)
        if not all(k in data for k in required_parts):
            return True
        severity = data.get("severity", "").lower()
        if confidence_score < 0.6 or severity in ["high", "critical", "blocker"]:
            return True
        return False
    except Exception:
        return True  # JSON parse failed — definitely needs review

