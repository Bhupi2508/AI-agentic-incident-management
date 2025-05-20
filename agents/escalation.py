import os
from dotenv import load_dotenv

load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID")

import json

def escalate(severity):
    severity = severity.lower()
    if severity == "blocker":
        return "🚨 Escalated to Platform Commander + Alert all stakeholders", True
    elif severity == "critical":
        return "🚨 Escalated to SME (Subject Matter Expert)", True
    elif severity == "high":
        return "⚠️ Escalated to Level 3 Support", True
    elif severity == "medium":
        return "📧 Escalated to Level 2 Support", False
    elif severity == "low":
        return "✅ Handled by automation", False
    else:
        return "⚠️ Unknown severity – fallback to automation", False

def extract_severity_and_respond(diagnosis_result):
    severity = diagnosis_result.get("severity", "medium")
    escalation_action, should_escalate_based_on_severity = escalate(severity)

    # Decide if escalation is needed based on severity or human intervention
    needs_intervention = diagnosis_result.get("needs_human_intervention", should_escalate_based_on_severity)
    should_escalate = needs_intervention or severity.lower() in ["blocker", "critical", "high"]

    return {
        "severity": severity,
        "escalation_action": escalation_action,
        "should_escalate": should_escalate
    }
