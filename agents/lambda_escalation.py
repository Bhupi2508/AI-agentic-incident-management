import json

def escalate(severity):
    severity = severity.lower()
    if severity == "blocker":
        return "🚨 Escalated to Platform Commander + Alert all stakeholders", True
    elif severity == "critical":
        return "🚨 Escalated to SME (Subject Matter Expert)", True
    elif severity == "high":
        return "⚠️ Escalated to Level 3 Support", True
    elif severity == "medium":
        return "📧 Escalated to Level 2 Support", False
    elif severity == "low":
        return "✅ Handled by automation", False
    else:
        return "⚠️ Unknown severity – fallback to automation", False

def lambda_handler(event, context):
    # event expected to be a dict with keys: 'severity', 'needs_human_intervention'
    severity = event.get('severity', '')
    needs_human_intervention = event.get('needs_human_intervention', False)

    escalation_action, should_escalate_based_on_severity = escalate(severity)

    should_escalate = needs_human_intervention or severity.lower() in ["blocker", "critical", "high"]

    response = {
        "severity": severity,
        "escalation_action": escalation_action,
        "should_escalate": should_escalate
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
