from flask import Flask, request, jsonify, render_template
from agents.diagnosis import diagnose_with_bedrock
from agents.escalation import escalate, extract_severity_and_respond
from agents.resolution import resolve_issue
from agents.communication import send_test_email
from agents.closure import validate_closure
from agents.postmortem import generate_postmortem
from datetime import datetime, timezone
from utils.logger import log
from utils.dynamodb import update_incident_in_dynamodb
import boto3
import os
from datetime import datetime

app = Flask(__name__)

# Environment variables for email recipient and DynamoDB table names
EMAIL_RECIPIENT = os.getenv("EMAIL_SEND_TO")
TABLE_NAME = os.getenv("TABLE_NAME")
LATEST_TABLE_NAME = os.getenv("LATEST_TABLE_NAME")

# Initialize boto3 DynamoDB resource using AWS region from environment variables
dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_DEFAULT_REGION"))
table = dynamodb.Table(LATEST_TABLE_NAME)  # Reference to the DynamoDB table

@app.route('/')
def index():
    # Render the main HTML page when user visits root URL
    return render_template('index.html')

@app.route('/run_agents', methods=['POST'])
def run_agents():
    data = request.get_json()
    incident_id = data.get('incidentId', '')
    incident_desc = data.get('incidentDesc', '')

    if not incident_id:
        return jsonify({'error': 'incidentId is required'}), 400

    # Fetch incident data from DynamoDB to get current status and any saved info
    try:
        response = table.get_item(Key={'incidentId': incident_id})
        item = response.get('Item')
    except Exception as e:
        return jsonify({'error': f"Error fetching incident from DB: {str(e)}"}), 500

    # Define the sequence of incident handling stages (agents)
    status_order = [
        "DIAGNOSIS",
        "ESCALATION",
        "RESOLUTION",
        "COMMUNICATION",
        "CLOSURE",
        "POSTMORTEM"
    ]

    # Determine current status from the fetched item (if exists)
    current_status = None
    if item and 'status' in item:
        current_status = item['status'].upper()

    # Determine start index of agents to run
    if current_status and current_status in status_order:
        start_index = status_order.index(current_status)
    else:
        start_index = 0  # start from DIAGNOSIS if no status found

    results = {}
    update_attrs = {
        'incidentId': incident_id,
        'updateTime': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'priority': item.get('priority') if item else 'normal'  # you can adjust priority logic
    }

    # DIAGNOSIS agent
    try:
        if start_index <= 0:
            log("************ Running Diagnosis Agent ************")
            diagnosis = diagnose_with_bedrock(incident_desc)
            print("++++++ diagnosis final response :::::::: ", diagnosis)
            results['diagnosis'] = diagnosis
            update_attrs['diagnosis'] = diagnosis
            update_attrs['status'] = "DIAGNOSIS"
            update_attrs['updateTime'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        else:
            results['diagnosis'] = item.get('diagnosis') if item else ''
    except Exception as e:
        results['diagnosis'] = f"Diagnosis failed: {str(e)}"

    # ESCALATION agent
    try:
        if start_index <= 1:
            log("************ Running Escalation Agent ************")
            escalation_input = results.get('diagnosis', '') or (item.get('diagnosis') if item else '')
            escalation = extract_severity_and_respond(escalation_input)
            results['escalation'] = escalation
            update_attrs['escalation'] = escalation
            update_attrs['status'] = "ESCALATION"
            update_attrs['updateTime'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        else:
            results['escalation'] = item.get('escalation') if item else ''
    except Exception as e:
        results['escalation'] = f"Escalation failed: {str(e)}"

    # RESOLUTION agent
    try:
        if start_index <= 2:
            log("************ Running Resolution Agent ************")
            resolution_input = results.get('diagnosis', '') or (item.get('diagnosis') if item else '')
            resolution = resolve_issue(resolution_input)
            results['resolution'] = resolution
            update_attrs['resolution'] = resolution
            update_attrs['status'] = "RESOLUTION"
            update_attrs['updateTime'] = datetime.utcnow().isoformat()
        else:
            results['resolution'] = item.get('resolution') if item else ''
    except Exception as e:
        results['resolution'] = f"Resolution failed: {str(e)}"

    # COMMUNICATION agent
    try:
        if start_index <= 3:
            log("************ Running Communication Agent ************")
            send_test_email(incident_desc, escalation, results.get('resolution', ''), EMAIL_RECIPIENT)
            results['communication'] = "Email sent successfully."
            update_attrs['communication'] = results['communication']
            update_attrs['status'] = "COMMUNICATION"
            update_attrs['updateTime'] = datetime.utcnow().isoformat()
        else:
            results['communication'] = item.get('communication') if item else ''
    except Exception as e:
        results['communication'] = f"Communication Error: {str(e)}"


    # CLOSURE agent
    try:
        if start_index <= 4:
            log("************ Running Closure Agent ************")

            # Add dummy or fetched values if user_feedback/system_logs not provided
            user_feedback = data.get('userFeedback', 'Positive feedback received.')
            system_logs = data.get('systemLogs', 'No anomalies detected in logs.')

            closure_status = validate_closure(user_feedback, system_logs)
            results['closure'] = closure_status
            update_attrs['closure'] = closure_status
            update_attrs['status'] = "CLOSURE"
            update_attrs['updateTime'] = datetime.utcnow().isoformat()
        else:
            results['closure'] = item.get('closure') if item else ''
    except Exception as e:
        results['closure'] = f"Closure validation failed: {str(e)}"

    # POSTMORTEM agent
    try:
        if start_index <= 5:
            log("Running Post-Mortem Agent")
            postmortem = generate_postmortem(incident_desc, results.get('diagnosis', ''), results.get('resolution', ''), escalation)
            results['postmortem'] = postmortem
            update_attrs['postmortem'] = postmortem
            update_attrs['status'] = "POSTMORTEM"
            update_attrs['updateTime'] = datetime.utcnow().isoformat()
        else:
            results['postmortem'] = item.get('postmortem') if item else ''
    except Exception as e:
        results['postmortem'] = f"Post-Mortem Generation failed: {str(e)}"


    # Push all updates to DynamoDB at once
    try:
        # Note: update_attrs already contains incidentId, status, updateTime, and all agent outputs
        update_incident_in_dynamodb(incident_id, update_attrs, LATEST_TABLE_NAME)
        log(f"Incident {incident_id} updated with status {update_attrs.get('status')} in DynamoDB")
    except Exception as e:
        log(f"Error while pushing incident data to DynamoDB: {str(e)}")

    return jsonify(results)

@app.route('/check_incident', methods=['POST'])
def check_incident():
    try:
        data = request.get_json()
        if not data or 'incidentId' not in data:
            return jsonify({'error': 'incidentId is required in the request body'}), 400

        incident_id = data['incidentId']

        response = table.get_item(Key={'incidentId': incident_id})

        if 'Item' in response:
            return jsonify({'exists': True})
        else:
            return jsonify({'exists': False})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)