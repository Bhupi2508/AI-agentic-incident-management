def resolve_issue(diagnosis_result):
    # Convert diagnosis text to lowercase for consistent checking
    text = diagnosis_result.lower()

    # Define common keywords and corresponding resolution messages
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

    # Check if any of the keywords exist in the diagnosis and return the first matched resolution
    for keyword, resolution_msg in resolution_map.items():
        if keyword in text:
            return resolution_msg

    return "No automated resolution found. Manual intervention required."