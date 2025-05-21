import boto3
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

def log(message):
    print(f"[LOGGER] {datetime.now().isoformat()} : {message}")

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
TABLE_NAME = os.getenv("LATEST_TABLE_NAME", "YourTableName")  # Replace or set in Lambda env vars

dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    log(f" event :::  {event}")
    action = event.get("action")
    log(f" action :::  {action}")

    if action == "add":
        incident_id = event.get("incidentId")
        update_fields = event.get("update_attrs", {})
        incident_id = add_incident_to_dynamodb(incident_id, update_fields)
        return {
            "statusCode": 200 if incident_id else 500,
            "body": {"incidentId": incident_id} if incident_id else {"error": "Failed to add incident"}
        }

    elif action == "update":
        incident_id = event.get("incidentId")
        update_fields = event.get("update_attrs", {})
        log(f"update_fields ===>>> {update_fields}")
        if not incident_id:
            return {"statusCode": 400, "body": {"error": "incidentId is required"}}
        success = update_incident_in_dynamodb(incident_id, update_fields)
        if success:
            return {"statusCode": 200, "body": {"message": f"Incident {incident_id} updated"}}
        else:
            return {"statusCode": 500, "body": {"error": f"Failed to update incident {incident_id}"}}

    elif action == "fetch":
        incident_id = event.get("incidentId")
        if not incident_id:
            return {"statusCode": 400, "body": {"error": "incidentId is required"}}
        item = fetch_dynamodb_item(incident_id)
        return {"statusCode": 200, "body": item if item else {"error": "Incident not found"}}

    else:
        return {"statusCode": 400, "body": {"error": "Invalid or missing action"}}


def add_incident_to_dynamodb(incident_id, update_fields):
    log(f"Field Details ::: {update_fields}")

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    update_fields = convert_floats_to_decimal(update_fields)

    log(f"incidentId ::: {incident_id}")

    # Build the item from update_fields directly
    item = {
        'incidentId': incident_id,
        'incident': update_fields.get("incident_desc"),
        'resolution': update_fields.get("resolution"),
        'status': update_fields.get("status"),
        'created_at': timestamp,
        'updated_at': timestamp,
        'diagnosis': update_fields.get("diagnosis"),
        'escalation': update_fields.get("escalation"),
        'postmortem': update_fields.get("postmortem"),
        'closure': update_fields.get("closure"),
        'freefield1': None,
        'freefield2': None,
        'freefield3': None  # Reserved for future use
    }

    try:
        table.put_item(Item=item)
        log(f"✅ Incident added successfully with ID: {incident_id}")
        return incident_id, True
    except Exception as e:
        log(f"❌ Failed to add incident to DynamoDB: {e}")
        return None, False


def convert_floats_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    else:
        return obj


def update_incident_in_dynamodb(incident_id, update_fields):
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    # Convert floats to Decimal
    update_fields = convert_floats_to_decimal(update_fields)
    log(f"update_fields ++++  {update_fields}")

    # Set created_at if missing (should not update existing created_at)
    if "created_at" not in update_fields:
        update_fields["created_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Do not allow these fields to be updated
    for key in ["incidentId", "created_at"]:
        update_fields.pop(key, None)

    # DynamoDB reserved keywords list (partial example)
    reserved_keywords = {"status", "type", "date", "timestamp"}

    for i, (key, value) in enumerate(update_fields.items()):
        placeholder = f":val{i}"
        # Use ExpressionAttributeNames if key is reserved
        if key.lower() in reserved_keywords:
            name_placeholder = f"#key{i}"
            expression_attribute_names[name_placeholder] = key
            update_expression_parts.append(f"{name_placeholder} = {placeholder}")
        else:
            update_expression_parts.append(f"{key} = {placeholder}")

        expression_attribute_values[placeholder] = value

    # Always update updated_at timestamp
    update_expression_parts.append("updated_at = :updated_at")
    expression_attribute_values[":updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    update_expression = "SET " + ", ".join(update_expression_parts)

    log(f"update_expression::: {update_expression}")
    log(f"expression_attribute_values::: {expression_attribute_values}")
    log(f"expression_attribute_names::: {expression_attribute_names}")

    try:
        table.update_item(
            Key={'incidentId': incident_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None
        )
        log(f"✅ Incident {incident_id} updated successfully in DynamoDB")
        return True
    except Exception as e:
        log(f"❌ Failed to update incident {incident_id}: {e}")
        return False


def fetch_dynamodb_item(incident_id):
    try:
        response = table.get_item(Key={'incidentId': incident_id})
        return response.get('Item')
    except Exception as e:
        log(f"Error fetching data from DynamoDB: {e}")
        return None
