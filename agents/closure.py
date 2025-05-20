import re

def validate_closure(feedback: str, system_logs: str) -> str:
    feedback = (feedback or "").lower().strip()
    system_logs = (system_logs or "").lower().strip()

    positive_feedback_patterns = [
        r"issue\s+(is\s+)?(fixed|resolved)",
        r"working\s+(fine|properly|normally)",
        r"service\s+(is\s+)?(fine|okay|ok|up)",
        r"(problem|error|bug)\s+(is\s+)?(gone|resolved|not\s+seen)",
        r"no\s+(issues|errors|problems)\s+now",
        r"(functionality|app)\s+is\s+(restored|normal)"
    ]

    positive_logs_patterns = [
        r"no\s+errors",
        r"logs?\s+(are\s+)?clean",
        r"running\s+(smoothly|fine|normally)",
        r"system\s+(is\s+)?stable",
        r"no\s+exceptions",
        r"service\s+healthy",
        r"uptime\s+confirmed"
    ]

    negative_feedback_patterns = [
        r"still\s+(facing|getting|seeing)",
        r"not\s+(fixed|resolved)",
        r"intermittent\s+(issue|problem)",
        r"(again|yet)\s+not\s+working",
        r"same\s+(error|issue)\s+exists"
    ]

    negative_logs_patterns = [
        r"(error|exception|fail(ed|ure))",
        r"stacktrace",
        r"retry\s+attempt",
        r"crash\s+detected",
        r"connection\s+timeout",
        r"unexpected\s+behavior"
    ]

    def matches_any(patterns, text):
        return any(re.search(pattern, text) for pattern in patterns)

    # Check for positive indicators
    if matches_any(positive_feedback_patterns, feedback):
        return "✅ Closure validated based on user feedback."

    if matches_any(positive_logs_patterns, system_logs):
        return "✅ Closure validated based on clean system logs."

    # Check for negative indicators
    if matches_any(negative_feedback_patterns, feedback):
        return "❌ Feedback suggests the issue may still persist."

    if matches_any(negative_logs_patterns, system_logs):
        return "❌ System logs indicate unresolved or recurring issues."

    # Default
    return "⚠️ Unable to confirm resolution. Further investigation needed."
