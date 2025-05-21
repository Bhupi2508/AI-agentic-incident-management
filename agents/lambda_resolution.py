import json
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
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, combined_text):
            return resolution_msg

    return "No automated resolution found. Manual intervention required."


def lambda_handler(event, context):
    try:
        # Parse input JSON body from event
        body = event.get('body')
        if body is None:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing body in request'})
            }

        diagnosis_result = json.loads(body)

        # Call the resolve_issue function with parsed input
        resolution = resolve_issue(diagnosis_result)

        # Return response with resolution message
        return {
            'statusCode': 200,
            'body': json.dumps({'resolution': resolution})
        }

    except Exception as e:
        # Return error message in case of failure
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
