import boto3
import os
import uuid
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

def push_incident_to_dynamodb(incident, resolution, TABLE_NAME):
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
    table = dynamodb.Table(TABLE_NAME)

    # Prepare the data
    incident_data = {
        'incident_id': str(uuid.uuid4()),  # Primary key
        'incident': incident,
        'resolution': resolution
    }

    # Push the data to DynamoDB
    try:
        table.put_item(Item=incident_data)
        print("Incident data pushed successfully!")
    except Exception as e:
        print("Failed to push data to DynamoDB:", e)

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