import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]
MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

# Load rules from external JSON file
current_dir = os.path.dirname(os.path.abspath(__file__))

# create full path to the JSON file inside the same folder as diagnosis.py
rules_path = os.path.join(current_dir, "severity_rules.json")

with open(rules_path, "r") as f:
    SEVERITY_RULES = json.load(f)

def diagnose_with_bedrock(incident_description):
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_DEFAULT_REGION)

    prompt_text = f"""
You are an expert Incident Diagnosis AI Agent.

Your responsibilities:
1. Analyze the incident.
2. Identify the root cause.
3. Recommend immediate next steps.

Respond in **strict JSON format** like this:

{{
  "root_cause": "<your analysis>",
  "next_steps": "<your suggestions>"
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

    cleaned_output = output_text.strip()
    if cleaned_output.startswith("```json"):
        cleaned_output = cleaned_output[len("```json"):].strip()
    if cleaned_output.endswith("```"):
        cleaned_output = cleaned_output[:-3].strip()

    try:
        parsed_json = json.loads(cleaned_output)
    except json.JSONDecodeError as e:
        return {
            "error": f"Invalid JSON from model: {e}"
        }

    confidence_score = calculate_confidence(cleaned_output)
    severity = calculate_severity(incident_description)
    intervention_required = needs_human_intervention(parsed_json, confidence_score, severity)

    return {
        "diagnosis": parsed_json,
        "severity": severity,
        "confidence_score": round(confidence_score, 2),
        "needs_human_intervention": intervention_required
    }

def calculate_confidence(output_text):
    high_keywords = ["definitely", "clearly", "confirmed", "root cause is", "100%"]
    medium_keywords = ["likely", "possibly", "might be", "appears to be", "could be"]
    low_keywords = ["may be", "unsure", "unclear", "unknown", "not sure", "cannot determine", "no idea"]

    text = output_text.lower()

    if any(k in text for k in high_keywords):
        return 0.9
    elif any(k in text for k in medium_keywords):
        return 0.6
    elif any(k in text for k in low_keywords):
        return 0.3
    return 0.5  # Default neutral confidence

def calculate_severity(description):
    desc = description.lower()
    for rule in SEVERITY_RULES:
        if any(phrase in desc for phrase in rule["conditions"]):
            return rule["severity"]
    return "Medium"  # Default

def needs_human_intervention(parsed_json, confidence_score, severity):
    required_parts = ["root_cause", "next_steps"]
    if not all(part in parsed_json for part in required_parts):
        return True

    if confidence_score < 0.6:
        return True
    if severity.lower() in ["high", "critical", "blocker"]:
        return True

    return False