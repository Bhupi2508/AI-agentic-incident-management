def escalate(diagnosis_result):
    try:
        # Parse string to JSON (if not already parsed)
        if isinstance(diagnosis_result, str):
            diagnosis_result = json.loads(diagnosis_result)

        severity = diagnosis_result.get("severity", "").strip().lower()

        if severity == "blocker":
            return "Escalated to Platform Incident Commander"
        elif severity == "critical":
            return "Escalated to SME (Subject Matter Expert)"
        elif severity == "high":
            return "Escalated to Level 3 Support"
        elif severity == "medium":
            return "Escalated to Level 2 Support"
        elif severity == "low":
            return "No escalation needed. Handled by automation."
        else:
            return "Unknown severity. Escalation not triggered."

    except Exception as e:
        return f"Error in escalation logic: {str(e)}"