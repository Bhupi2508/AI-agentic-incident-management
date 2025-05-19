# main.py
from agents.diagnosis import diagnose_with_bedrock
from agents.escalation import escalate
from agents.resolution import resolve_issue
from agents.communication import send_update
from utils.logger import log

incident = "Login service timing out for multiple users since 2 AM."

log("🔍 Running Diagnosis Agent...")
diagnosis = diagnose_with_bedrock(incident)
print("Diagnosis:", diagnosis)

log("⚠️ Running Escalation Agent...")
escalation = escalate(diagnosis)
print("Escalation:", escalation)

log("🛠️ Running Resolution Agent...")
resolution = resolve_issue(diagnosis)
print("Resolution:", resolution)

log("📣 Running Communication Agent...")
send_update(incident, resolution)

# Simulated data
user_feedback = "The issue fixed after service restart."
system_logs = "No errors reported in last 30 minutes."

# 🧪 Closure Validation
log("✅ Running Closure Agent...")
closure_status = validate_closure(user_feedback, system_logs)
print("Closure:", closure_status)

# 🧾 Post-Mortem Generation
log("📜 Running Post-Mortem Agent...")
postmortem = generate_postmortem(incident, diagnosis, resolution)
print("Post-Mortem Summary:\n", postmortem)
