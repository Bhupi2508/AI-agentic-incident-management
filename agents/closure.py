def validate_closure(data):
    user_feedback = data.get('userFeedback')
    system_logs = data.get('systemLogs')

    if not user_feedback or not system_logs:
        print("⏳ Waiting for user feedback and system logs before closure.")
        return "⌛ Closure pending"
    
    return "✅ Closure done"