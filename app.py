from flask import Flask, render_template, request, jsonify
from agents.diagnosis import diagnose_with_bedrock
from agents.escalation import escalate, extract_severity_and_respond
from agents.resolution import resolve_issue
from agents.communication import send_test_email
from agents.closure import validate_closure
from agents.postmortem import generate_postmortem
from datetime import datetime, timezone
from utils.logger import log
from utils.dynamodb import fetch_dynamodb_item, update_incident_in_dynamodb
import boto3
import os
import ast

app = Flask(__name__, template_folder='.')

# Environment variables for email recipient and DynamoDB table names
EMAIL_RECIPIENT = os.getenv("EMAIL_SEND_TO")
TABLE_NAME = os.getenv("TABLE_NAME")
LATEST_TABLE_NAME = os.getenv("LATEST_TABLE_NAME")

# Initialize boto3 DynamoDB resource using AWS region from environment variables
dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_DEFAULT_REGION"))
table = dynamodb.Table(LATEST_TABLE_NAME)  # Reference to the DynamoDB table


@app.route("/")
def index():
    # Render the main HTML page when user visits root URL
    return render_template("index.html")


@app.route("/run_agents", methods=["POST"])
def run_agents():
    data = request.get_json()
    incident_id = data.get("incidentId", "")
    incident_desc = data.get("incidentDesc", "")

    print("incident_id :::: ", incident_id)
    print("incident_desc :::: ", incident_desc)

    if not incident_id:
        return jsonify({"error": "incidentId is required"}), 400

    item = fetch_dynamodb_item(table, incident_id)

    results1 = {}
    if item and item.get("status") == "POSTMORTEM":
        print("If status is POSTMORTEM ....", item)
        results1["description"] = item.get("description", "")
        results1["status"] = item.get("status", "")
        results1["created_at"] = item.get("created_at", "")
        results1["priority"] = item.get("priority", "")
        results1["resolution"] = item.get("resolution", "")
        results1["communication"] = item.get("communication", "")
        results1["communication"] = item.get("communication", "")
        results1["escalation"] = item.get("escalation", "")
        results1["diagnosis"] = item.get("diagnosis", "")
        return results1

    # Define the sequence of incident handling stages (agents)
    status_order = [
        "DIAGNOSIS",
        "ESCALATION",
        "RESOLUTION",
        "COMMUNICATION",
        "CLOSURE",
        "POSTMORTEM",
    ]

    # Determine current status from the fetched item (if exists)
    current_status = None
    if item and "status" in item:
        current_status = item["status"].upper()

    # Determine start index of agents to run
    if current_status and current_status in status_order:
        start_index = status_order.index(current_status)
    else:
        start_index = 0  # start from DIAGNOSIS if no status found

    results = {}
    update_attrs = {
        "incidentId": incident_id,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "priority": item.get("priority")
        if item
        else "normal",  # you can adjust priority logic
    }

    # DIAGNOSIS agent
    try:
        if start_index <= 0:
            log(
                "Running Diagnosis Agent Start #################################################"
            )
            diagnosis = diagnose_with_bedrock(incident_desc)
            print("+++++++++++++++ Diagnosis data :::::::: ", diagnosis)
            results["diagnosis"] = diagnosis["diagnosis"]
            results["severity"] = diagnosis["severity"]
            results["needs_human_intervention"] = diagnosis["needs_human_intervention"]
            results["status"] = "DIAGNOSIS"
            update_attrs["diagnosis"] = diagnosis
            update_attrs["status"] = "DIAGNOSIS"
            update_attrs["updated_at"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            log(
                "Running Diagnosis Agent End #################################################"
            )
        else:
            results["diagnosis"] = item.get("diagnosis") if item else ""
            results["status"] = "DIAGNOSIS"
    except Exception as e:
        results["diagnosis"] = f"Diagnosis failed: {str(e)}"

    # ESCALATION agent
    try:
        if start_index <= 1:
            log(
                "Running Escalation Agent Start #################################################"
            )
            escalation_input = (
                results.get("severity", "")
                or results.get("severity", "")
                or (item.get("diagnosis") if item else "")
            )
            needs_human_intervention_input = (
                results.get("needs_human_intervention", "")
                or results.get("needs_human_intervention", "")
                or ""
            )
            escalation = extract_severity_and_respond(
                escalation_input, needs_human_intervention_input
            )
            print("+++++++++++++++ Escalation data :::::::: ", escalation)
            results["escalation"] = escalation
            results["status"] = "ESCALATION"
            update_attrs["escalation"] = escalation
            update_attrs["status"] = "ESCALATION"
            update_attrs["updated_at"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            log(
                "Running Escalation Agent End #################################################"
            )
        else:
            results["escalation"] = item.get("escalation") if item else ""
            results["status"] = "ESCALATION"
    except Exception as e:
        results["escalation"] = f"Escalation failed: {str(e)}"

    # RESOLUTION agent
    try:
        if start_index <= 2:
            log(
                "Running Resolution Agent Start #################################################"
            )
            resolution_input = results.get("diagnosis", "") or (
                item.get("diagnosis") if item else ""
            )
            resolution = resolve_issue(resolution_input)
            print("+++++++++++++++ resolution data :::::::: ", resolution)
            results["resolution"] = resolution
            results["status"] = "RESOLUTION"
            update_attrs["resolution"] = resolution
            update_attrs["status"] = "RESOLUTION"
            update_attrs["updated_at"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            log(
                "Running Resolution Agent End #################################################"
            )
        else:
            results["resolution"] = item.get("resolution") if item else ""
            results["status"] = "RESOLUTION"
    except Exception as e:
        results["resolution"] = f"Resolution failed: {str(e)}"

    # COMMUNICATION agent
    try:
        if start_index <= 3:
            log(
                "Running Communication Agent Start #################################################"
            )
            diagnosis = results.get("diagnosis", "") or (
                item.get("diagnosis") if item else ""
            )
            escalation = results.get("escalation", "") or (
                item.get("escalation") if item else ""
            )
            resolution = results.get("resolution", "") or (
                item.get("resolution") if item else ""
            )
            data = send_test_email(
                incident_desc,
                escalation,
                results.get("resolution", ""),
                incident_id,
                EMAIL_RECIPIENT,
            )
            print("+++++++++++++++ COMMUNICATION data :::::::: ", data)
            results["communication"] = "Email sent successfully."
            results["status"] = "COMMUNICATION"
            update_attrs["communication"] = results["communication"]
            update_attrs["status"] = "COMMUNICATION"
            update_attrs["updated_at"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            log(
                "Running Communication Agent End #################################################"
            )
        else:
            results["communication"] = item.get("communication") if item else ""
            results["status"] = "COMMUNICATION"
    except Exception as e:
        results["communication"] = f"Communication Error: {str(e)}"

    # CLOSURE agent
    try:
        if start_index <= 4:
            log(
                "Running Closure Agent Start #################################################"
            )

            # user_feedback/system_logs not yet provided
            closure_status = validate_closure({"userFeedback": "", "systemLogs": ""})
            print("+++++++++++++++ CLOSURE data :::::::: ", closure_status)
            results["closure"] = closure_status
            results["status"] = "CLOSURE"
            update_attrs["closure"] = closure_status
            update_attrs["status"] = "CLOSURE"
            update_attrs["updated_at"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            log(
                "Running Closure Agent End #################################################"
            )
        else:
            results["closure"] = item.get("closure") if item else ""
            results["status"] = "CLOSURE"
    except Exception as e:
        results["closure"] = f"Closure validation failed: {str(e)}"

    # POSTMORTEM agent
    try:
        if start_index <= 5:
            log(
                "Running Post-Mortem Start #################################################"
            )
            diagnosis = results.get("diagnosis", "") or (
                item.get("diagnosis") if item else ""
            )
            escalation = results.get("escalation", "") or (
                item.get("escalation") if item else ""
            )
            resolution = results.get("resolution", "") or (
                item.get("resolution") if item else ""
            )

            postmortem = generate_postmortem(
                item.get("description") if item else "",
                results.get("diagnosis", diagnosis),
                results.get("resolution", resolution),
                escalation,
            )
            print("+++++++++++++++ Post-Mortem :::::::: ", postmortem)
            results["status"] = "POSTMORTEM"
            update_attrs["postmortem"] = postmortem
            update_attrs["status"] = "POSTMORTEM"
            update_attrs["updated_at"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )
            log(
                "Running Post-Mortem End #################################################"
            )
        else:
            results["status"] = "CLOSURE"

        update_attrs["description"] = (
            incident_desc
            if incident_desc is not None
            else (item.get("description") if item else "")
        )
        update_attrs["created_at"] = results.get("created_at", "") or (
            item.get("created_at")
            if item
            else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        )
        try:
            update_incident_in_dynamodb(incident_id, update_attrs, LATEST_TABLE_NAME)
            log(
                f"Incident {incident_id} updated with status {update_attrs.get('status')} in DynamoDB"
            )
            results["diagnosis"] = str(results["diagnosis"])
            results["escalation"] = str(results["escalation"])

        except Exception as e:
            log(f"❌ Error while pushing incident data to DynamoDB: {str(e)}")

            del results["needs_human_intervention"]
            del results["severity"]
        return jsonify(results)
    except Exception as e:
        results["postmortem"] = f"Post-Mortem Generation failed: {str(e)}"


@app.route("/check_incident", methods=["POST"])
def check_incident():
    try:
        data = request.get_json()
        if not data or "incidentId" not in data:
            return jsonify({"error": "incidentId is required in the request body"}), 400

        incident_id = data["incidentId"]

        response = table.get_item(Key={"incidentId": incident_id})

        if "Item" in response:
            return jsonify({"exists": True})
        else:
            return jsonify({"exists": False})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)