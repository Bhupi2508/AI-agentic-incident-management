# agents/escalation.py

def escalate(diagnosis_result):
    if "critical" in diagnosis_result.lower() or "outage" in diagnosis_result.lower():
        return "Escalated to SME (Subject Matter Expert)"
    return "No escalation needed. Handled by automation."
