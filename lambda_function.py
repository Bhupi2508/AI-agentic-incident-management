import json
from datetime import datetime, timezone
import boto3
import os

from agents.diagnosis import diagnose_with_bedrock
from agents.escalation import escalate, extract_severity_and_respond
from agents.resolution import resolve_issue
from agents.communication import send_test_email
from agents.closure import validate_closure
from agents.postmortem import generate_postmortem
from utils.logger import log
from utils.dynamodb import fetch_dynamodb_item, update_incident_in_dynamodb


# Env variables
EMAIL_RECIPIENT = os.getenv("EMAIL_SEND_TO")
TABLE_NAME = os.getenv("TABLE_NAME")
LATEST_TABLE_NAME = os.getenv("LATEST_TABLE_NAME")

dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_DEFAULT_REGION"))
table = dynamodb.Table(LATEST_TABLE_NAME)


def lambda_handler(event, context):
    path = event.get("path", "")
    http_method = event.get("httpMethod", "")
    body = event.get("body")
    if body and isinstance(body, str):
        body = json.loads(body)
    else:
        body = {}

    if path == "/" and http_method == "GET":
        # Return a simple message or static HTML (API Gateway + Lambda can't serve files directly)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html"},
            "body": "<html><body><h1>Welcome to Incident Handling API</h1></body></html>",
        }

    elif path == "/run_agents" and http_method == "POST":
        return handle_run_agents(body)

    elif path == "/check_incident" and http_method == "POST":
        return handle_check_incident(body)

    else:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Route not found"})
        }


def handle_run_agents(data):
    incident_id = data.get("incidentId", "")
    incident_desc = data.get("incidentDesc", "")

    if not incident_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "incidentId is required"})
        }

    item = fetch_dynamodb_item(table, incident_id)

    if item and item.get("status") == "POSTMORTEM":
        # Already postmortem done, just return details
        result = {
            "description": item.get("description", ""),
            "status": item.get("status", ""),
            "created_at": item.get("created_at", ""),
            "priority": item.get("priority", ""),
            "resolution": item.get("resolution", ""),
            "communication": item.get("communication", ""),
            "escalation": item.get("escalation", ""),
            "diagnosis": item.get("diagnosis", ""),
        }
        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }

    status_order = [
        "DIAGNOSIS",
        "ESCALATION",
        "RESOLUTION",
        "COMMUNICATION",
        "CLOSURE",
        "POSTMORTEM",
    ]

    current_status = item.get("status", "").upper() if item else None
    start_index = status_order.index(current_status) if current_status in status_order else 0

    results = {}
    update_attrs = {
        "incidentId": incident_id,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "priority": item.get("priority") if item else "normal",
    }

    # DIAGNOSIS
    try:
        if start_index <= 0:
            log("Running Diagnosis Agent Start")
            diagnosis = diagnose_with_bedrock(incident_desc)
            results["diagnosis"] = diagnosis["diagnosis"]
            results["severity"] = diagnosis["severity"]
            results["needs_human_intervention"] = diagnosis["needs_human_intervention"]
            results["status"] = "DIAGNOSIS"
            update_attrs["diagnosis"] = diagnosis
            update_attrs["status"] = "DIAGNOSIS"
            update_attrs["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            log("Running Diagnosis Agent End")
        else:
            results["diagnosis"] = item.get("diagnosis", "")
            results["status"] = "DIAGNOSIS"
    except Exception as e:
        results["diagnosis"] = f"Diagnosis failed: {str(e)}"

    # ESCALATION
    try:
        if start_index <= 1:
            log("Running Escalation Agent Start")
            escalation_input = results.get("severity", "") or (item.get("diagnosis") if item else "")
            needs_human_intervention_input = results.get("needs_human_intervention", "") or ""
            escalation = extract_severity_and_respond(escalation_input, needs_human_intervention_input)
            results["escalation"] = escalation
            results["status"] = "ESCALATION"
            update_attrs["escalation"] = escalation
            update_attrs["status"] = "ESCALATION"
            update_attrs["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            log("Running Escalation Agent End")
        else:
            results["escalation"] = item.get("escalation", "")
            results["status"] = "ESCALATION"
    except Exception as e:
        results["escalation"] = f"Escalation failed: {str(e)}"

    # RESOLUTION
    try:
        if start_index <= 2:
            log("Running Resolution Agent Start")
            resolution_input = results.get("diagnosis", "") or (item.get("diagnosis") if item else "")
            resolution = resolve_issue(resolution_input)
            results["resolution"] = resolution
            results["status"] = "RESOLUTION"
            update_attrs["resolution"] = resolution
            update_attrs["status"] = "RESOLUTION"
            update_attrs["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            log("Running Resolution Agent End")
        else:
            results["resolution"] = item.get("resolution", "")
            results["status"] = "RESOLUTION"
    except Exception as e:
        results["resolution"] = f"Resolution failed: {str(e)}"

    # COMMUNICATION
    try:
        if start_index <= 3:
            log("Running Communication Agent Start")
            escalation = results.get("escalation", "") or (item.get("escalation") if item else "")
            data_email = send_test_email(incident_desc, escalation, results.get("resolution", ""), incident_id, EMAIL_RECIPIENT)
            results["communication"] = "Email sent successfully."
            results["status"] = "COMMUNICATION"
            update_attrs["communication"] = results["communication"]
            update_attrs["status"] = "COMMUNICATION"
            update_attrs["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            log("Running Communication Agent End")
        else:
            results["communication"] = item.get("communication", "")
            results["status"] = "COMMUNICATION"
    except Exception as e:
        results["communication"] = f"Communication Error: {str(e)}"

    # CLOSURE
    try:
        if start_index <= 4:
            log("Running Closure Agent Start")
            closure_status = validate_closure({"userFeedback": "", "systemLogs": ""})
            results["closure"] = closure_status
            results["status"] = "CLOSURE"
            update_attrs["closure"] = closure_status
            update_attrs["status"] = "CLOSURE"
            update_attrs["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            log("Running Closure Agent End")
        else:
            results["closure"] = item.get("closure", "")
            results["status"] = "CLOSURE"
    except Exception as e:
        results["closure"] = f"Closure validation failed: {str(e)}"

    # POSTMORTEM
    try:
        if start_index <= 5:
            log("Running Post-Mortem Start")
            diagnosis = results.get("diagnosis", "") or (item.get("diagnosis") if item else "")
            escalation = results.get("escalation", "") or (item.get("escalation") if item else "")
            resolution = results.get("resolution", "") or (item.get("resolution") if item else "")

            postmortem = generate_postmortem(
                item.get("description", "") if item else "",
                diagnosis,
                resolution,
                escalation,
            )
            results["status"] = "POSTMORTEM"
            update_attrs["postmortem"] = postmortem
            update_attrs["status"] = "POSTMORTEM"
            update_attrs["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            log("Running Post-Mortem End")
        else:
            results["status"] = "CLOSURE"

        update_attrs["description"] = incident_desc or (item.get("description") if item else "")
        update_attrs["created_at"] = results.get("created_at", "") or (item.get("created_at") if item else "")
        update_incident_in_dynamodb(table, update_attrs)

    except Exception as e:
        results["postmortem"] = f"Postmortem generation failed: {str(e)}"

    return {
        "statusCode": 200,
        "body": json.dumps(results),
    }


def handle_check_incident(data):
    incident_id = data.get("incidentId", "")
    if not incident_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "incidentId is required"})
        }

    item = fetch_dynamodb_item(table, incident_id)

    if not item:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": "Incident not found"})
        }

    return {
        "statusCode": 200,
        "body": json.dumps(item),
    }