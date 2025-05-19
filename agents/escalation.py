def escalate(diagnosis_result):
    # Split by lines and find the severity line
    lines = diagnosis_result.strip().splitlines()
    severity_line = next((line for line in lines if line.lower().startswith("severity:")), None)

    if severity_line:
        severity = severity_line.split(":", 1)[1].strip().lower()
        if severity == "high":
            return "Escalated to SME (Subject Matter Expert)"
        elif severity == "medium":
            return "Escalated to Level 2 Support"
        else:
            return "No escalation needed. Handled by automation."
    
    # If severity line not found, fallback safe option:
    return "No escalation needed. Handled by automation."