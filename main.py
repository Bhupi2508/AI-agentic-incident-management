from agents.diagnosis import diagnose_with_bedrock
from agents.escalation import escalate
from agents.resolution import resolve_issue
from agents.communication import send_test_email
from agents.closure import validate_closure           # <-- import closure
from agents.postmortem import generate_postmortem    # <-- import post-mortem
from utils.logger import log
import os

# Load email recipient from environment or config
EMAIL_RECIPIENT = os.getenv("EMAIL_SEND_TO")

incident = "Login service timing out for multiple users since 2 AM."

print("Promt Ask :::::::::::::: ", incident, "\n")


try:
    log("\n################  Running Diagnosis Agent  ################")
    diagnosis = diagnose_with_bedrock(incident)
    print("Diagnosis:", diagnosis)
except Exception as e:
    print(">>>> Diagnosis Error <<<< ", e)
    diagnosis = "Diagnosis failed."

try:
    log("\n################  Running Escalation Agent  ################")
    escalation = escalate(diagnosis)
    print("Escalation:", escalation)
except Exception as e:
    print(">>>> Escalation Error  <<<< ", e)
    escalation = "Escalation failed."

try:
    log("\n################  Running Resolution Agent  ################")
    resolution = resolve_issue(diagnosis)
    print("Resolution:", resolution)
except Exception as e:
    print(">>>> Resolution Error  <<<< ", e)
    resolution = "Resolution failed."

try:
    log("\n################  Running Communication Agent  ################")
    send_test_email(incident, resolution, EMAIL_RECIPIENT)
except Exception as e:
    print(">>>> Communication Error  <<<< ", e)

# Simulated closure data
user_feedback = "The issue fixed after service restart."
system_logs = "No errors reported in last 30 minutes."

try:
    log("\n################  Running Closure Agent  ################")
    closure_status = validate_closure(user_feedback, system_logs)
    print(">>>> Closure:", closure_status)
except Exception as e:
    print("Closure Validation Error  <<<< ", e)
    closure_status = "Closure validation failed."

try:
    log("\n################  Running Post-Mortem Agent  ################")
    postmortem = generate_postmortem(incident, diagnosis, resolution)
    print(">>>> Post-Mortem Summary:\n", postmortem)
except Exception as e:
    print("Post-Mortem Generation Error  <<<< ", e)