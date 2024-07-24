from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os
from pymongo import MongoClient

# Configure the database host
DATABASE_HOST = os.getenv("DATABASE_HOST")

# Connect to the usage database
client = MongoClient(f"mongodb://{DATABASE_HOST}/?authSource=admin")
db = client["usage"]

# Connect to the service database
db_service = client["service"]

idle_percentage = float(os.getenv("IDLE_PERCENTAGE", 2)) # Idle percentage for threshold calculation

# This is for daily threshold
# Function to get the latest date range
def get_latest_date_range():
    min_date = datetime.utcnow().date()
    max_date = datetime(1970, 1, 1).date()  # start with a very old date

    for collection in db.list_collection_names():
        data = list(db[collection].find())
        for document in data:
            for year, months in document.items():
                if not year.isdigit():
                    continue
                for month, days in months.items():
                    for day in days.keys():
                        date = datetime(int(year), int(month), int(day)).date()
                        min_date = min(min_date, date)
                        max_date = max(max_date, date)

    return min_date, max_date

# Function for daily usage type level alert
def daily_usagetype_alert():
    min_date, max_date = get_latest_date_range()

    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Set the end date to the last day of the previous month
    end_date = max_date.replace(day=1) - timedelta(days=1)

    # Set the start date to the second day of the previous month
    start_date = end_date.replace(day=2)

    # Generate a list of all dates between start_date and end_date
    all_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

    # Query the database for latest_date's data
    for service in services:
        # Get the collection object
        collection = db[service]

        for usage_type_doc in collection.find():
            # Initialize costs dictionary with all dates set to 0
            costs_dict = {date: 0 for date in all_dates}
            usage_type = usage_type_doc["UsageTypes"]

            # Iterate over each day's data to find the latest
            for year, months in usage_type_doc.items():
                if year.isdigit():
                    for month, days in months.items():
                        if month.isdigit():
                            for day, cost in days.items():
                                try:
                                    # Attempt to convert day to integer
                                    day_int = int(day)
                                    current_date = datetime(int(year), int(month), day_int).date()
                                    if current_date in costs_dict:
                                        costs_dict[current_date] = cost
                                except ValueError:
                                    continue  # Skip if day is not a valid integer

            # Convert costs_dict to a list of costs
            costs = list(costs_dict.values())

            # # Debugging output
            # print(f"Service: {service}, Usage Type: {usage_type}")
            # print(f"Costs: {costs}")

            total_cost = sum(costs)
            count = len(costs)
            daily_average_cost = total_cost / count if count > 0 else 0

            # Daily percentage changes
            percentage_changes = []
            for i in range(1, count):
                if costs[i-1] != 0:
                    percentage_change = ((costs[i] - costs[i-1]) / costs[i-1]) * 100
                    if -100 < percentage_change < 100:
                        percentage_changes.append(percentage_change)

            # # Debugging output
            # print(f"Percentage Changes: {percentage_changes}")

            average_percentage_change = sum(percentage_changes) / len(percentage_changes) if percentage_changes else 0
            if average_percentage_change < 0:
                average_percentage_change = 0
            daily_threshold_percentage = round(average_percentage_change + idle_percentage)
            daily_threshold_value = round(daily_average_cost + (idle_percentage / 100 * daily_average_cost), 2)

            # # Debugging output
            # print(f"Daily Average Cost: {daily_average_cost}")
            # print(f"Daily Threshold Percentage: {daily_threshold_percentage}")
            # print(f"Daily Threshold Value: {daily_threshold_value}")

            # Update the corresponding document in service2
            collection_service2 = db_service[service]
            collection_service2.update_one(
                {
                    "UsageTypes.UsageType": usage_type
                },
                {
                    "$set": {
                        "UsageTypes.$.Daily-Threshold-Percentage": daily_threshold_percentage,
                        "UsageTypes.$.Daily-Threshold-Value": daily_threshold_value
                    }
                }
            )

# This is for weekly threshold
# Function to get latest date range for complete weeks
def get_latest_complete_week():
    max_date = datetime(1970, 1, 1).date()  # start with a very old date

    # Iterate over each collection
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        # Find the document with the latest date
        latest_entry = collection.find_one(sort=[('_id', -1)])
        if latest_entry:
            for year, months in latest_entry.items():
                if not year.isdigit():
                    continue
                for month, days in months.items():
                    for day in days.keys():
                        date = datetime(int(year), int(month), int(day)).date()
                        max_date = max(max_date, date)

    # Set max_date to the last day of last month
    max_date = max_date.replace(day=1) - timedelta(days=1)

    # Calculate the last Sunday from max_date
    last_sunday = max_date - timedelta(days=(max_date.weekday() + 1) % 7)

    # Calculate the Monday of the same week
    last_monday = last_sunday - timedelta(days=6)

    return last_monday, last_sunday

# Function for weekly usage type level alert
def weekly_usagetype_alert():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Calculate the date ranges for the last 8 weeks
    date_ranges = []
    for i in range(8):
        start_date = get_latest_complete_week()[0] - timedelta(weeks=i)
        end_date = get_latest_complete_week()[1] - timedelta(weeks=i)
        date_ranges.append((start_date, end_date))

    # Query the database for usage type data within each date range
    for service in services:
        # Get the collection object
        collection = db[service]

        for usage_type_doc in collection.find():
            usage_type = usage_type_doc["UsageTypes"]

            weekly_costs = []
            for start_date, end_date in date_ranges:
                weekly_cost = calculate_weekly_cost(service, usage_type, start_date, end_date)
                weekly_costs.append(weekly_cost)

            weekly_costs.reverse()  # Reverse the list to get the latest week first

            # Remove the first and fifth weeks from the list
            weekly_costs = weekly_costs[1:4] + weekly_costs[5:]

            # Calculate thresholds or perform other actions based on weekly_costs
            percentage_changes = []

            for i in range(1, len(weekly_costs)):
                if weekly_costs[i - 1] != 0:
                    percentage_change = (weekly_costs[i] - weekly_costs[i - 1]) / weekly_costs[i - 1] * 100
                else:
                    percentage_change = 0
                if -100 < percentage_change < 100:
                    percentage_changes.append(percentage_change)

            average_percentage_change = max(0, sum(percentage_changes) / len(percentage_changes) if percentage_changes else 0)
            weekly_threshold_percentage = round(average_percentage_change + idle_percentage)
            average_cost = sum(weekly_costs) / len(weekly_costs) if weekly_costs else 0
            weekly_threshold_value = round(average_cost + (idle_percentage / 100 * average_cost), 2)

            # # Print the costs
            # print(f"Service: {service}, Usage Type: {usage_type} - Weekly Costs: {weekly_costs}")
            # # Print the percentage changes
            # print(f"Percentage Changes: {percentage_changes}")
            # # Print the average percentage change
            # print(f"Average Percentage Change: {average_percentage_change}")
            # # Print the weekly threshold percentage
            # print(f"Weekly Threshold Percentage: {weekly_threshold_percentage}")
            # # Print the average cost
            # print(f"Average Cost: {average_cost}")
            
            # Update the corresponding document in service2
            collection_service2 = db_service[service]
            collection_service2.update_one(
                {
                    "UsageTypes.UsageType": usage_type
                },
                {
                    "$set": {
                        "UsageTypes.$.Weekly-Threshold-Percentage": weekly_threshold_percentage,
                        "UsageTypes.$.Weekly-Threshold-Value": weekly_threshold_value
                    }
                }
            )

def calculate_weekly_cost(service, usage_type, start_date, end_date):
    data = db[service].find_one({"UsageTypes": usage_type})
    weekly_cost = 0

    if data:
        for year, months in data.items():
            if year.isdigit():
                for month, days in months.items():
                    if month.isdigit():
                        for day, cost in days.items():
                            try:
                                # Attempt to convert day to integer
                                day_int = int(day)
                            except ValueError:
                                continue  # Skip if day is not a valid integer

                            # Convert date components to datetime object
                            current_date = datetime(int(year), int(month), day_int).date()

                            # Check if current date is within the specified week range
                            if start_date <= current_date <= end_date:
                                weekly_cost += cost

    return weekly_cost

# This is for monthly threshold
def get_max_date():
    max_date = datetime(1970, 1, 1).date()  # Start with a very old date
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        latest_entry = collection.find_one(sort=[('_id', -1)])
        if latest_entry:
            for year, months in latest_entry.items():
                if not year.isdigit():
                    continue
                for month, days in months.items():
                    for day in days.keys():
                        date = datetime(int(year), int(month), int(day)).date()
                        max_date = max(max_date, date)
    return max_date

def get_latest_complete_month():
    max_date = get_max_date()
    first_day_max_date_month = datetime(max_date.year, max_date.month, 1).date()
    return [
        first_day_max_date_month - relativedelta(months=i)
        for i in range(4, -1, -1)
    ]

def aggregate_monthly_cost(doc, date_ranges):
    costs = [0] * 4
    for year, months in doc.items():
        if year.isdigit():
            for month, days in months.items():
                if month.isdigit():
                    for day, cost in days.items():
                        try:
                            day_int = int(day)
                        except ValueError:
                            continue
                        current_date = datetime(int(year), int(month), day_int).date()
                        for i, (start, end) in enumerate(date_ranges):
                            if start <= current_date <= end:
                                costs[i] += cost
                                break
    return costs

def calculate_thresholds(costs):
    percentage_changes = [
        (costs[i] - costs[i-1]) / costs[i-1] * 100
        for i in range(1, len(costs))
        if costs[i-1] != 0 and -100 < (costs[i] - costs[i-1]) / costs[i-1] * 100 < 100
    ]
    avg_percentage_change = sum(percentage_changes) / len(percentage_changes) if percentage_changes else 0
    if avg_percentage_change < 0:
        avg_percentage_change = 0
    monthly_threshold_percentage = round(max(0, avg_percentage_change) + idle_percentage)
    avg_cost = sum(costs) / len(costs) if costs else 0
    monthly_threshold_value = round(avg_cost + (idle_percentage / 100 * avg_cost), 2)
    return monthly_threshold_percentage, monthly_threshold_value

def monthly_usagetype_alert():
    services = sorted(db.list_collection_names())
    date_ranges = get_latest_complete_month()
    date_ranges = [(date_ranges[i], date_ranges[i+1] - timedelta(days=1)) for i in range(4)]

    for service in services:
        collection = db[service]
        collection_service2 = db_service[service]

        for usage_type_doc in collection.find():
            usage_type = usage_type_doc["UsageTypes"]
            costs = aggregate_monthly_cost(usage_type_doc, date_ranges)
            monthly_threshold_percentage, monthly_threshold_value = calculate_thresholds(costs)

            collection_service2.update_one(
                {"UsageTypes.UsageType": usage_type},
                {"$set": {
                    "UsageTypes.$.Monthly-Threshold-Percentage": monthly_threshold_percentage,
                    "UsageTypes.$.Monthly-Threshold-Value": monthly_threshold_value
                }}
            )

if __name__ == "__main__":
    daily_usagetype_alert()
    weekly_usagetype_alert()
    monthly_usagetype_alert()