import boto3
import datetime
import os
import json

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

def main():
    end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    master_account_id = '286817589435'
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

    # Dump the service data to JSON
    print(json.dumps(service_data, indent=4))

if __name__ == "__main__":
    main()
import boto3
import datetime
import os
import json

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

def main():
    end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    master_account_id = '286817589435'
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

    # Dump the service data to JSON
    print(json.dumps(service_data, indent=4))

if __name__ == "__main__":
    main()
