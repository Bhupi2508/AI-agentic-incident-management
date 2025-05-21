import json

def validate_closure(data):
    user_feedback = data.get('userFeedback')
    system_logs = data.get('systemLogs')

    if not user_feedback or not system_logs:
        print("⏳ Waiting for user feedback and system logs before closure.")
        return "⌛ Closure pending"
    
    return "✅ Closure done"

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        result = validate_closure(body)
        return {
            'statusCode': 200,
            'body': json.dumps({'closureStatus': result})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
