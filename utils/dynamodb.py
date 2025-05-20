import boto3
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

def add_incident_to_dynamodb(incident, resolution, status, TABLE_NAME):
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_DEFAULT_REGION"))
    table = dynamodb.Table(TABLE_NAME)

    incident_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    item = {
        'incidentId': incident_id,
        'incident': incident,
        'resolution': resolution,
        'status': status,
        'created_at': timestamp,
        'updated_at': timestamp,
        'diagnosis': None,
        'escalation': None,
        'resolution': None,
        'postmortem': None,
        'closure': None,
        'freefield1': None,
        'freefield2': None,
        'freefield3': None
    }

    try:
        table.put_item(Item=item)
        print(f"Incident added successfully with ID: {incident_id}")
        return incident_id
    except Exception as e:
        print("Failed to add incident to DynamoDB:", e)
        return None

# Converts floats to Decimals recursively
def convert_floats_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(i) for i in obj]
    else:
        return obj


def update_incident_in_dynamodb(incident_id, update_fields, TABLE_NAME):
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_DEFAULT_REGION"))
    table = dynamodb.Table(TABLE_NAME)

    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}

    # Convert specific dict fields to string
    for field in ['diagnosis', 'escalation']:
        if field in update_fields and isinstance(update_fields[field], dict):
            update_fields[field] = str(update_fields[field])

    # Convert floats to Decimal
    update_fields = convert_floats_to_decimal(update_fields)

    # Remove primary key from update fields
    update_fields.pop("incidentId", None)

    for i, (key, value) in enumerate(update_fields.items()):
        placeholder = f":val{i}"

        # Handle reserved keywords
        if key.lower() in {"status", "timestamp", "date", "type"}:
            name_placeholder = f"#key{i}"
            expression_attribute_names[name_placeholder] = key
            update_expression_parts.append(f"{name_placeholder} = {placeholder}")
        else:
            update_expression_parts.append(f"{key} = {placeholder}")

        expression_attribute_values[placeholder] = value

    # Add updatedAt timestamp
    if "updated_at" not in update_fields and not any("updated_at" in str(v) for v in update_fields.values()):
        update_expression_parts.append("updated_at = :updated_at")
        expression_attribute_values[":updated_at"] = datetime.now(timezone.utc).isoformat()


    update_expression = "SET " + ", ".join(update_expression_parts)

    try:
        table.update_item(
            Key={'incidentId': incident_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names if expression_attribute_names else None
        )
        print(f"[LOG] Incident {incident_id} updated successfully in DynamoDB")
    except Exception as e:
        print(f"❌ Failed to update incident {incident_id}:", e)


def fetch_dynamodb_item(table, incident_id):
    try:
        response = table.get_item(Key={'incidentId': incident_id})
        item = response.get('Item')
        return item
    except Exception as e:
        print(f"Error fetching data from DynamoDB: {e}")
        return None