import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.environ["AWS_DEFAULT_REGION"]
MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

SEVERITY_RULES = [{"conditions":["data loss","system crash","server down","complete failure","unrecoverable","permanent loss","database corruption","database down","security breach","payment failure","unable to login","authentication failed"],"severity":"Blocker"},{"conditions":["critical","production issue","prod down","latency spike","memory leak","cpu 100%","process killed","deadlock","high severity","infinite loop","timeout error"],"severity":"Critical"},{"conditions":["timeout","504","gateway timeout","system not responding","connection refused","failed dependency","retry limit reached","disk full","unavailable","service unavailable"],"severity":"High"},{"conditions":["minor","cosmetic","typo","spelling mistake","alignment issue","UI glitch","feedback","low impact","suggestion","warning only","non-blocking"],"severity":"Low"},{"conditions":["slow","latency","degraded","not loading properly","cache not working","delay in response","partial outage","memory warning","temporary error","inconsistent results","intermittent issue"],"severity":"Medium"}]


# This function sends the incident description to the AI model and processes the response to extract root cause, next steps, severity, and calculates confidence and human intervention need.
def diagnose_with_bedrock(incident_description):
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_DEFAULT_REGION)

    prompt_text = f"""
You are an expert Incident Diagnosis AI Agent.

Your responsibilities:
1. Analyze the incident.
2. Identify the root cause.
3. Recommend immediate next steps.
4. Provide a confidence score between 0 and 1 indicating how sure you are.
5. Assign a severity level for the incident (High, Medium, Low).
6. Indicate whether human intervention is needed based on severity and confidence.

Respond in **strict JSON format** like this:

{{
  "root_cause": "<your analysis>",
  "next_steps": "<your suggestions>",
  "confidence": <confidence_score_as_float>,
  "severity": "<severity_level>",
  "human_intervention_needed": <true_or_false>
}}

Incident: {incident_description}
"""

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt_text}]}
        ],
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )

    response_body = json.loads(response["body"].read().decode("utf-8"))
    output_text = response_body["content"][0]["text"]

    cleaned_output = output_text.strip()
    if cleaned_output.startswith("```json"):
        cleaned_output = cleaned_output[len("```json") :].strip()
    if cleaned_output.endswith("```"):
        cleaned_output = cleaned_output[:-3].strip()

    # Parse the JSON
    try:
        parsed_json = json.loads(output_text)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON from model: {e}"}

    # Get confidence
    confidence_score = calculate_confidence(output_text)

    # Get AI returned severity or fallback to rules-based severity
    severity = parsed_json.get("severity") or parsed_json.get("severity")
    final_severity = calculate_severity(incident_description, severity)
    print("final_severity ::::::::: ", final_severity)

    # Determine if human intervention is needed
    intervention_required = needs_human_intervention(confidence_score, final_severity)

    return {
        "diagnosis": parsed_json,
        "severity": final_severity,
        "confidence_score": round(confidence_score, 2),
        "needs_human_intervention": intervention_required,
    }


# Determines the severity level of the incident based on the incident description.
# Checks description against predefined severity rules (keywords/phrases).
# If no match is found, it returns the severity level provided by the AI.
def calculate_severity(description, severity):
    desc = description.lower()
    print("Description to check :::: ", desc)

    for rule in SEVERITY_RULES:
        for phrase in rule["conditions"]:
            if phrase in desc:
                print(f"Matched phrase :::: '{phrase}' for severity: {rule['severity']}")
                return rule["severity"]

    return severity


# Analyzes the AI output text to estimate how confident the AI is about the root cause.
# Uses keyword matching to assign a confidence score (high, medium, low).
# Returns a float between 0 and 1 indicating confidence level.
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
    ]

    text = output_text.lower()
    if any(k in text for k in high_keywords):
        return 0.9
    elif any(k in text for k in medium_keywords):
        return 0.6
    elif any(k in text for k in low_keywords):
        return 0.3
    return 0.5


# Decides if a human needs to review the incident based on confidence score and severity.
# Typically triggers human review if confidence is low or severity is high.
# Returns True if human intervention is required, else False.
def needs_human_intervention(confidence_score, severity):
    high_severity_levels = ["high", "blocker", "critical"]  # include all high-severity terms
    if confidence_score < 0.5 or severity.lower() in high_severity_levels:
        return True
    return False