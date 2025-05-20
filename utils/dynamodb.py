import boto3
import os
import uuid
from datetime import datetime, timezone
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

import boto3
import uuid
import os

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
        'createdAt': timestamp,
        'updatedAt': timestamp,
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


def update_incident_in_dynamodb(incident_id, update_fields, TABLE_NAME):
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv("AWS_DEFAULT_REGION"))
    table = dynamodb.Table(TABLE_NAME)

    update_expression = "SET "
    expression_attribute_values = {}
    for i, (key, value) in enumerate(update_fields.items()):
        print(":!1111111111111111111, ", key)
        update_expression += f"{key} = :val{i}, "
        expression_attribute_values[f":val{i}"] = value

    # Add updatedAt field
    update_expression += "updatedAt = :updated"
    expression_attribute_values[":updated"] = datetime.now(timezone.utc).isoformat()

    try:
        table.update_item(
            Key={'incidentId': incident_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        print(f"✅ Incident {incident_id} updated successfully.")
    except Exception as e:
        print(f"❌ Failed to update incident {incident_id}:", e)



def fetch_dynamodb_items(table_name):
    dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
    table = dynamodb.Table(table_name)

    try:
        response = table.scan()
        print(f"DynamoDB RESPONSE::::::::::::::::: {response}")
        return response.get('Items', [])
    except Exception as e:
        print(f"Error fetching data from DynamoDB: {e}")
        return []