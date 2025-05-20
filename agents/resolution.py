import re

def resolve_issue(diagnosis_result):
    root_cause = diagnosis_result.get("root_cause", "").lower()
    next_steps = diagnosis_result.get("next_steps", "").lower()
    combined_text = root_cause + " " + next_steps
    print("combined_text for resolution :::: ", combined_text)
 
    resolution_map = {
        "restart": "Recommended to restart the service based on diagnosis.",
        "config": "Configuration changes may help mitigate the issue.",
        "scale out": "Scaling out the service might reduce load pressure.",
        "rollback": "Rolling back to a stable version is suggested.",
        "database": "Database tuning or optimization required.",
        "network": "Network-level fixes or DNS checks may resolve the issue.",
        "resource": "Consider adding resources or freeing up memory/CPU.",
        "bug": "Possible bug found — escalate to dev team.",
        "timeout": "Timeout values can be increased as a temporary workaround.",
        "cache": "Review or clear cache for improved performance.",
        "failover": "Check failover configuration to maintain uptime."
    }

    for keyword, resolution_msg in resolution_map.items():
        # Regex pattern for exact whole word matching, case insensitive
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, combined_text):
            return resolution_msg

    return "No automated resolution found. Manual intervention required."