# agents/closure.py

def validate_closure(feedback, system_logs):
    if "issue fixed" in feedback.lower() or "working fine" in feedback.lower():
        return "✅ Issue validated via feedback."
    elif "no errors" in system_logs.lower():
        return "✅ Issue validated via system logs."
    else:
        return "❌ Unable to confirm resolution. Needs re-check."
