import re

def resolve_issue(diagnosis_result):
    root_cause = diagnosis_result.get("diagnosis", {}).get("root_cause", "").lower()
    next_steps = diagnosis_result.get("diagnosis", {}).get("next_steps", "").lower()
    combined_text = root_cause + " " + next_steps

    resolution_map = {
        "restart": "Auto-resolved by restarting the service.",
        "config": "Suggested configuration changes have been applied.",
        "scale out": "Auto-scaled the service to handle increased load.",
        "rollback": "Rolled back to the previous stable version.",
        "database": "Database performance issues addressed.",
        "network": "Network connectivity issues resolved.",
        "resource": "Resource constraints mitigated by adding more capacity.",
        "bug": "Bug fix deployed to resolve the issue.",
        "timeout": "Timeout parameters adjusted to improve service responsiveness.",
        "cache": "Cache cleared or caching mechanism optimized.",
        "failover": "Failover mechanisms triggered to maintain availability."
    }

    for keyword, resolution_msg in resolution_map.items():
        # Regex pattern for exact whole word matching, case insensitive
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, combined_text):
            return resolution_msg

    return "No automated resolution found. Manual intervention required."