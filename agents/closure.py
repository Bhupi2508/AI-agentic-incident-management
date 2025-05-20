def validate_closure(feedback: str, system_logs: str) -> str:
    feedback = feedback.lower().strip()
    system_logs = system_logs.lower().strip()

    if any(phrase in feedback for phrase in ["issue fixed", "working fine", "resolved", "service is fine now"]):
        return "Issue validated via feedback."
    elif any(phrase in system_logs for phrase in ["no errors", "logs clean", "running smoothly"]):
        return "Issue validated via system logs."
    else:
        return "Unable to confirm resolution. Needs re-check."