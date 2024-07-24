import time
import boto3  # type: ignore
import datetime
import os
import json
from pymongo import MongoClient  # type: ignore
from bson.objectid import ObjectId  # type: ignore

# Configure the database host
DATABASE_HOST = os.getenv("DATABASE_HOST")
MASTER_ACCOUNT_ID = os.getenv("MASTER_ACCOUNT_ID")

def get_aws_cost_data(start_date, end_date, master_account_id):
    # Initialize the Cost Explorer client
    ce_client = boto3.client('ce', region_name=os.environ.get('AWS_REGION'))

    # Specify the time period
    time_period = {
        'Start': start_date,
        'End': end_date
    }

    # Specify the granularity (DAILY)
    granularity = 'DAILY'

    # Specify the metrics and group by service and usage type
    metrics = ['UnblendedCost']
    group_by = [{'Type': 'DIMENSION', 'Key': 'SERVICE'}, {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}]

    # Specify the filter to include only the master account's costs
    filters = {
        'Dimensions': {
            'Key': 'LINKED_ACCOUNT',
            'Values': [master_account_id]
        }
    }

    # Get the cost data
    result = ce_client.get_cost_and_usage(
        TimePeriod=time_period,
        Granularity=granularity,
        Metrics=metrics,
        GroupBy=group_by,
        Filter=filters
    )

    return result

def save_to_mongodb(db, date_str, data):
    # Iterate over each service in the data
    for service_name, service_data in data.items():
        collection = db[service_name]  # Create a new collection for each service

        # Iterate over each usage type in the service data
        for usage_type, cost in service_data['UsageTypes'].items():
            # Check if a document with the same usage type exists
            existing_doc = collection.find_one({'UsageTypes': usage_type})

            if existing_doc:
                # Update the existing document with the new usage data
                if date_str[:4] not in existing_doc:
                    existing_doc[date_str[:4]] = {}
                if date_str[5:7] not in existing_doc[date_str[:4]]:
                    existing_doc[date_str[:4]][date_str[5:7]] = {}
                existing_doc[date_str[:4]][date_str[5:7]][date_str[8:]] = cost
                collection.replace_one({'_id': existing_doc['_id']}, existing_doc)
            else:
                # Create a new document with the initial usage data
                new_doc = {
                    'UsageTypes': usage_type,
                    date_str[:4]: {
                        date_str[5:7]: {
                            date_str[8:]: cost
                        }
                    }
                }
                collection.insert_one(new_doc)

def save_to_service_db(db, data):
    # Insert JSON data into MongoDB
    for service, data in data.items():
        collection = db[service]
        
        # Ensure all existing UsageTypes have an _id
        for document in collection.find():
            for usage_type_entry in document.get('UsageTypes', []):
                if '_id' not in usage_type_entry:
                    usage_type_entry['_id'] = ObjectId()
            collection.replace_one({'_id': document['_id']}, document)

        # Check if collection exists and if not, create it
        if collection.count_documents({}) == 0:
            # Create a new collection and insert data
            collection.insert_one({
                "Service-Alert-Threshold": {
                    "Daily-Alert": "false",
                    "Daily-Threshold-Percentage": "na",
                    "Daily-Threshold-Value": "na",
                    "Weekly-Alert": "false",
                    "Weekly-Threshold-Percentage": "na",
                    "Weekly-Threshold-Value": "na",
                    "Monthly-Alert": "false",
                    "Monthly-Threshold-Percentage": "na",
                    "Monthly-Threshold-Value": "na",
                },
                "UsageTypes": [
                    {
                        "_id": ObjectId(),
                        "UsageType": usage_type,
                        "Daily-Alert": "false",
                        "Daily-Threshold-Percentage": "na",
                        "Daily-Threshold-Value": "na",
                        "Weekly-Alert": "false",
                        "Weekly-Threshold-Percentage": "na",
                        "Weekly-Threshold-Value": "na",
                        "Monthly-Alert": "false",
                        "Monthly-Threshold-Percentage": "na",
                        "Monthly-Threshold-Value": "na",
                    } for usage_type in data["UsageTypes"]
                ]
            })
        else:
            # If collection exists, check if usage type already exists and add if not
            for usage_type, cost in data["UsageTypes"].items():
                if collection.count_documents({"UsageTypes.UsageType": usage_type}) == 0:
                    collection.update_one({}, {"$push": {"UsageTypes": {
                        "_id": ObjectId(),
                        "UsageType": usage_type,
                        "Daily-Alert": "false",
                        "Daily-Threshold-Percentage": "na",
                        "Daily-Threshold-Value": "na",
                        "Weekly-Alert": "false",
                        "Weekly-Threshold-Percentage": "na",
                        "Weekly-Threshold-Value": "na",
                        "Monthly-Alert": "false",
                        "Monthly-Threshold-Percentage": "na",
                        "Monthly-Threshold-Value": "na",
                    }}})

def calculate_date_range():
    today = datetime.datetime.today()
    total_days = 0
    month = today.month
    year = today.year

    # Add days in the current month
    total_days += (today - today.replace(day=1)).days + 1

    # Add days in the past four complete months
    for _ in range(4):
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        total_days += (today.replace(month=month, year=year) - today.replace(month=month-1 if month > 1 else 12, year=year if month > 1 else year-1)).days

    return total_days

def main():
    # Connect to MongoDB
    client = MongoClient(f'mongodb://{DATABASE_HOST}/?authSource=admin')

    # Save the service data to usage database
    usage_db = client.usage

    # Save the service data to service database
    service_db = client.service

    # Calculate the number of days in the current month and the past four complete months
    total_days = calculate_date_range()

    curr_date = datetime.datetime.now() - datetime.timedelta(days=1)

    for i in range(total_days):    
        end_date = (curr_date - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        start_date = (curr_date - datetime.timedelta(days=i+1)).strftime('%Y-%m-%d')

        master_account_id = MASTER_ACCOUNT_ID
        result = get_aws_cost_data(start_date, end_date, master_account_id)

        service_data = {}

        for time_data in result['ResultsByTime']:
            for group in time_data['Groups']:
                service_name = group['Keys'][0]
                usage_type = group['Keys'][1]
                cost_amount = round(float(group['Metrics']['UnblendedCost']['Amount']), 2)

                if service_name not in service_data:
                    service_data[service_name] = {'TotalCost': 0, 'UsageTypes': {}}

                if usage_type not in service_data[service_name]['UsageTypes']:
                    service_data[service_name]['UsageTypes'][usage_type] = 0

                service_data[service_name]['TotalCost'] = round(service_data[service_name]['TotalCost'] + cost_amount, 2)
                service_data[service_name]['UsageTypes'][usage_type] = round(service_data[service_name]['UsageTypes'][usage_type] + cost_amount, 2)
        
        save_to_mongodb(usage_db, start_date, service_data)

        save_to_service_db(service_db, service_data)

        # Wait for 2 second to avoid rate limiting
        time.sleep(2)

if __name__ == "__main__":
    main()
