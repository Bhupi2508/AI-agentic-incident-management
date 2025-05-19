def handler(event, context):
    print("Resolving incident:", event)
    return {"status": "resolved", "incidentId": event["incidentId"]}