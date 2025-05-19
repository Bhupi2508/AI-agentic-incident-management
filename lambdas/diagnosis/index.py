def handler(event, context):
    print("Diagnosing incident:", event)
    return {"status": "diagnosed", "incidentId": event["incidentId"]}