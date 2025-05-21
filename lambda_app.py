import json
import boto3
import os
from datetime import datetime, timezone

lambda_client = boto3.client('lambda')

def log(message):
    print(f"[LOGGER] {datetime.now().isoformat()} :: {message}")

def invoke_lambda(function_name, payload_dict):
    log(f"Invoke Function Name ===>>>> {function_name}")
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload_dict),
    )
    response_payload = response['Payload'].read().decode('utf-8')
    result = json.loads(response_payload)
    body = result.get('body', None)
    if body:
        try:
            return json.loads(body)
        except Exception:
            return body
    return None


def lambda_handler(event, context):
    try:
        log("Handler started")
        log(f"incident_desc :: {event.get('incident_desc')}")
        event['action'] = 'add' if event.get('incident_desc') else 'update'

        results = event.get("results", {})  # cumulative results from previous runs
        item = event.get("item", None)      # existing incident data from DB
        update_attrs = event.get("update_attrs", {})
        start_index = event.get("start_index", 0)

        # Define the sequence of statuses
        status_order = [
            "DIAGNOSIS",
            "ESCALATION",
            "RESOLUTION",
            "COMMUNICATION",
            "CLOSURE",
            "POSTMORTEM",
        ]

        # Helper to get current status index if available
        if item:
            current_status = item.get("status", "").upper()
            if current_status in status_order:
                start_index = status_order.index(current_status)
            else:
                start_index = 0
        else:
            start_index = 0

        # 0. DIAGNOSIS
        if start_index <= 0:
            log("Calling diagnose_with_bedrock")
            diagnosis = invoke_lambda("diagnosisAgent", event)
            log(f" Diagnosis Result :: {diagnosis}")
            results["diagnosis"] = diagnosis.get("diagnosis", "") if isinstance(diagnosis, dict) else diagnosis
            results["severity"] = diagnosis.get("severity", "") if isinstance(diagnosis, dict) else ""
            results["needs_human_intervention"] = diagnosis.get("needs_human_intervention", False) if isinstance(diagnosis, dict) else False
            update_attrs["diagnosis"] = diagnosis
            update_attrs["status"] = "DIAGNOSIS"
            start_index = 1
        else:
            results["diagnosis"] = item.get("diagnosis", "")
            results["severity"] = item.get("severity", "")
            results["needs_human_intervention"] = item.get("needs_human_intervention", False)

        # 1. ESCALATION
        if start_index <= 1:
            log("Calling extract_severity_and_respond")
            escalation_input = results.get("severity", "") or results.get("diagnosis", "")
            needs_human_intervention_input = results.get("needs_human_intervention", False)
            event['severity'] = escalation_input
            event['needs_human_intervention'] = needs_human_intervention_input
            escalation = invoke_lambda("escalationAgent", event)
            results["escalation"] = escalation
            update_attrs["escalation"] = escalation
            update_attrs["status"] = "ESCALATION"
            start_index = 2
            del event['severity']
            del event['needs_human_intervention']
        else:
            results["escalation"] = item.get("escalation", "")

        # 2. RESOLUTION
        if start_index <= 2:
            log("Calling resolve_issue")
            data = results.get("diagnosis", "")
            resolution = invoke_lambda("resolutionAgent", {"body": json.dumps(data)})
            log(f" Resolution Data :: {resolution}")
            results["resolution"] = resolution
            update_attrs["resolution"] = resolution
            update_attrs["status"] = "RESOLUTION"
            start_index = 3
        else:
            results["resolution"] = item.get("resolution", "")

        # 3. COMMUNICATION
        if start_index <= 3:
            log("Calling send_test_email")
            log(f"event {event} ")
            log(f"results {results} ")

            email_payload = {
            "incident_summary_comm": event.get("incident_desc", ""),
            "escalation_message_comm": results.get("escalation", ""),
            "resolution_message_comm": results.get("resolution", ""),
            "incident_Id_comm": event.get("incidentId", ""),
            "email_recipient_comm": os.getenv("EMAIL_SEND_TO", "")
            }

            # Wrap the payload in a `body` key as a JSON string, to match the lambda handler's expectation
            lambda_event = {
                "body": json.dumps(email_payload)
            }
            email_status = invoke_lambda("communicationAgent", lambda_event)
            log(f" Email_status data :: {email_status}")
            results["communication"] = email_status or "Email sent successfully."
            update_attrs["communication"] = results["communication"]
            update_attrs["status"] = "COMMUNICATION"
            start_index = 4
        else:
            results["communication"] = item.get("communication", "")

        # 4. CLOSURE
        if start_index <= 4:
            log("Calling validate_closure")
            closure_valid = invoke_lambda("closureAgent", {"userFeedback": "", "systemLogs": ""})
            log(f" Closure data :: {closure_valid}")
            results["closure"] = closure_valid
            update_attrs["closure"] = closure_valid
            update_attrs["status"] = "CLOSURE"
            start_index = 5
        else:
            results["closure"] = item.get("closure", "")

        # 5. POSTMORTEM
        if start_index <= 5:
            log("Calling generate_postmortem")
            email_payload = {
            "incident_summary_comm": event.get("incident_desc", ""),
            "escalation_message_comm": results.get("escalation", ""),
            "resolution_message_comm": results.get("resolution", ""),
            "incident_Id_comm": results.get("diagnosis", ""),
            }
            # Wrap the payload in a `body` key as a JSON string, to match the lambda handler's expectation
            lambda_event = {
                "body": json.dumps(email_payload)
            }
            postmortem_report = invoke_lambda("postmortemAgent", lambda_event)
            log(f" postmortem_report data :: {postmortem_report}")
            results["postmortem"] = postmortem_report
            update_attrs["postmortem"] = postmortem_report
            update_attrs["status"] = "POSTMORTEM"
        else:
            results["postmortem"] = item.get("postmortem", "")

        # Update timestamps & description
        update_attrs["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        update_attrs["description"] = event.get("incident_desc", "") or (item.get("description") if item else "")

       # ✅ Final DynamoDB Lambda Invocation
        log("Calling update_dynamodb_lambda")
        log(f"update_attrs :::: {update_attrs}")
        event['update_attrs'] = update_attrs
        result = invoke_lambda("dynamoDBAgent", event)
        log(f"DB Result :: {result} ")
        # invoke_lambda(os.getenv("dynamoDBAgent"), update_attrs)

        log("Handler finished successfully") 
        return {
        "statusCode": 200,
        "body": {
            "incidentId": results.get("incidentId"),
            "status": results.get("status"),
            "description": results.get("description"),
            "diagnosis": results.get("diagnosis"),
            "severity": results.get("severity"),
            "needs_human_intervention": results.get("needs_human_intervention"),
            "confidence_score": results.get("confidence_score"),
            "escalation": results.get("escalation"),
            "resolution": results.get("resolution"),
            "communication": results.get("communication"),
            "closure": results.get("closure"),
            "postmortem": results.get("postmortem"),
            "updated_at": results.get("updated_at")
        }
    }

    except Exception as e:
        log(f"Error in handler: {str(e)}")
        return {
            "status": False,
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }