import boto3
import os
from botocore.exceptions import ClientError
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

#####################################################################################
# python setup_dynamodb_table.py  ::: Run Script to create the table with a mock data
#####################################################################################

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
LATEST_TABLE_NAME = os.getenv("LATEST_TABLE_NAME")

def table_exists(dynamodb_client, table_name):
    try:
        dynamodb_client.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return False
        else:
            raise

def create_table(dynamodb_client, table_name):
    print(f"Creating table '{table_name}'...")
    dynamodb_client.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'incidentId', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'incidentId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    waiter = dynamodb_client.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    print(f"✅ Table '{table_name}' created and ready.")

def add_incident_entry(
    incidentId,
    description=None,
    status=None,
    priority=None,
    assigned_to=None,
    created_at=None,
    updated_at=None,
    diagnosis=None,
    escalation=None,
    resolution=None,
    postmortem=None,
    closure=None,
    freefield1=None,
    freefield2=None,
    freefield3=None
):
    allowed_statuses = {
        "DIAGNOSIS",
        "ESCALATION",
        "RESOLUTION",
        "COMMUNICATION",
        "POSTMORTEM",
        "CLOSURE"
    }

    if status is None or status.upper() not in allowed_statuses:
        print(f"Invalid or missing status '{status}'. Allowed statuses are: {allowed_statuses}")
        return

    print(f"Using AWS Region: {AWS_DEFAULT_REGION}")
    print(f"Using DynamoDB Table: {LATEST_TABLE_NAME}")

    dynamodb_resource = boto3.resource('dynamodb', region_name=AWS_DEFAULT_REGION)
    dynamodb_client = boto3.client('dynamodb', region_name=AWS_DEFAULT_REGION)

    if not table_exists(dynamodb_client, LATEST_TABLE_NAME):
        create_table(dynamodb_client, LATEST_TABLE_NAME)

    table = dynamodb_resource.Table(LATEST_TABLE_NAME)

    now_iso = datetime.now(timezone.utc).isoformat()
    created_at = created_at or now_iso
    updated_at = updated_at or now_iso

    item = {
        'incidentId': incidentId,
        'description': description,
        'status': status.upper(),
        'priority': priority,
        'assignedTo': assigned_to,
        'createdAt': created_at,
        'updatedAt': updated_at,
        'diagnosis': diagnosis,
        'escalation': escalation,
        'resolution': resolution,
        'postmortem': postmortem,
        'closure': closure,
        'freefield1': freefield1,
        'freefield2': freefield2,
        'freefield3': freefield3
    }

    item = {k: v for k, v in item.items() if v is not None}

    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(incidentId)'
        )
        print(f"Incident '{incidentId}' added successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"Incident with ID '{incidentId}' already exists!")
        else:
            print(f"Error adding incident: {e.response['Error']['Message']}")

if __name__ == "__main__":
    add_incident_entry(
        incidentId="INC01",
        description="Javascript heap memory issue",
        status="DIAGNOSIS",
        priority="High",
        assigned_to="John Doe",
        diagnosis="Memory leak in server",
        escalation="Escalated to infra team",
        resolution="Increased heap memory limit",
        postmortem="Added memory monitoring",
        closure="Ticket closed after fix",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        freefield1="",
        freefield2="",
        freefield3=""
    )