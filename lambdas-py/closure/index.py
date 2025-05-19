def handler(event, context):
    print("Closing incident:", event)
    return {"status": "closed", "incidentId": event["incidentId"]}