def handler(event, context):
    print("Post-incident review:", event)
    return {"status": "reviewed", "incidentId": event["incidentId"]}