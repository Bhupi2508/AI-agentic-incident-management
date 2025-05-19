# agents/resolution.py

def resolve_issue(diagnosis_result):
    if "restart" in diagnosis_result.lower():
        return "Auto-resolved by restarting the service."
    elif "config" in diagnosis_result.lower():
        return "Suggested config change applied."
    else:
        return "No automated resolution found. Manual intervention required."
