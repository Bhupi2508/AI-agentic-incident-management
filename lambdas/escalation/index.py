def handler(event, context):
    print("Escalating incident:", event)
    return {"status": "escalated", "incidentId": event["incidentId"]}