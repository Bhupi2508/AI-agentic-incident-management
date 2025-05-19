from flask import Flask, request, jsonify, render_template
from agents.diagnosis import diagnose_with_bedrock
from agents.escalation import escalate
from agents.resolution import resolve_issue
from agents.communication import send_test_email
from agents.closure import validate_closure
from agents.postmortem import generate_postmortem
from utils.logger import log
import os

app = Flask(__name__)

EMAIL_RECIPIENT = os.getenv("EMAIL_SEND_TO")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_agents', methods=['POST'])
def run_agents():
    data = request.get_json()
    incident = data.get('incident', '')

    results = {}

    try:
        log("\n################  Running Diagnosis Agent  ################")
        diagnosis = diagnose_with_bedrock(incident)
        results['diagnosis'] = diagnosis
    except Exception as e:
        results['diagnosis'] = f"Diagnosis failed: {str(e)}"

    try:
        log("\n################  Running Escalation Agent  ################")
        escalation = escalate(results.get('diagnosis', ''))
        results['escalation'] = escalation
    except Exception as e:
        results['escalation'] = f"Escalation failed: {str(e)}"

    try:
        log("\n################  Running Resolution Agent  ################")
        resolution = resolve_issue(results.get('diagnosis', ''))
        results['resolution'] = resolution
    except Exception as e:
        results['resolution'] = f"Resolution failed: {str(e)}"

    try:
        log("\n################  Running Communication Agent  ################")
        send_test_email(incident, results.get('resolution', ''), EMAIL_RECIPIENT)
        results['communication'] = "Email sent successfully."
    except Exception as e:
        results['communication'] = f"Communication Error: {str(e)}"

    # Simulated closure data
    user_feedback = "The issue fixed after service restart."
    system_logs = "No errors reported in last 30 minutes."

    try:
        log("\n################  Running Closure Agent  ################")
        closure_status = validate_closure(user_feedback, system_logs)
        results['closure'] = closure_status
    except Exception as e:
        results['closure'] = f"Closure validation failed: {str(e)}"

    try:
        log("\n################  Running Post-Mortem Agent  ################")
        postmortem = generate_postmortem(incident, results.get('diagnosis', ''), results.get('resolution', ''))
        results['postmortem'] = postmortem
    except Exception as e:
        results['postmortem'] = f"Post-Mortem Generation failed: {str(e)}"

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)