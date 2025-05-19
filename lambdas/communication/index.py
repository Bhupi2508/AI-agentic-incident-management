def handler(event, context):
    print("Communicating status:", event)
    return {"status": "communicated", "incidentId": event["incidentId"]}