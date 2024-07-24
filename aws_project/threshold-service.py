from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pymongo import MongoClient
import os

# Configure the database host
DATABASE_HOST = os.getenv("DATABASE_HOST")

# Connect to the MongoDB databases
client = MongoClient(f"mongodb://{DATABASE_HOST}/?authSource=admin")
db = client["usage"]
db_service = client["service"]

idle_percentage = float(os.getenv("IDLE_PERCENTAGE", 2))    # Idle percentage for threshold calculation

# Function to get date range
def get_date_range():
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

# Function to calculate daily cost data
def daily():
    min_date, max_date = get_date_range()

    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Set the end date to the last day of the previous month
    end_date = max_date.replace(day=1) - timedelta(days=1)

    # Set the start date to the second day of the previous month
    start_date = end_date.replace(day=2)

    # Convert dates to datetime objects
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Query the database for the previous month's data
    service_data = {}
    for service in services:
        data = list(db[service].find())
        service_data[service] = []
        for i in range((end_date - start_date).days + 1):
            date = start_date.date() + timedelta(days=i)
            total_cost = 0
            for doc in data:
                year_data = doc.get(str(date.year), {})
                month_data = year_data.get(str(date.month).zfill(2), {})
                day_cost = month_data.get(str(date.day).zfill(2), 0)
                total_cost += day_cost
            service_data[service].append(total_cost)

        # Count of data for each service
        count = len(service_data[service])

        # Total cost for each service
        total_daily_cost = sum(service_data[service])

        # Average cost (total cost / count )
        daily_average_cost = total_daily_cost / count if count > 0 else 0

        # Daily percentage changes
        percentage_changes = []
        for i in range(1, count):
            if service_data[service][i-1] != 0:
                denominator = service_data[service][i-1] if service_data[service][i-1] >= 1 else 1
                percentage_change = ((service_data[service][i] - service_data[service][i-1]) / denominator) * 100
                if -100 < percentage_change < 100:
                    percentage_changes.append(percentage_change)

        # Calculate average percentage change
        average_percentage_change = max(0, sum(percentage_changes) / len(percentage_changes) if percentage_changes else 0)
        daily_threshold_percentage = average_percentage_change + idle_percentage
        daily_threshold_percentage = round(daily_threshold_percentage)

        # Calculate daily threshold value
        daily_threshold_value = daily_average_cost + (idle_percentage / 100 * daily_average_cost)
        daily_threshold_value = round(daily_threshold_value, 2)

        # Update the corresponding document in service2
        collection_service2 = db_service[service]
        collection_service2.update_one(
            {"Service-Alert-Threshold": {"$exists": True}},
            {
                "$set": {
                    "Service-Alert-Threshold.Daily-Threshold-Percentage": daily_threshold_percentage,
                    "Service-Alert-Threshold.Daily-Threshold-Value": daily_threshold_value
                }
            }
        )

    return service_data

# Function to get the latest date range for complete weeks
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

# Function for weekly service level alert
def weekly():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Get the latest complete week date range
    start_date_current, end_date_current = get_latest_complete_week()

    # Calculate the date ranges for the last 8 weeks
    date_ranges = []
    for i in range(8):
        start_date = start_date_current - timedelta(weeks=i)
        end_date = end_date_current - timedelta(weeks=i)
        date_ranges.append((start_date, end_date))

    # Query the database for service level data within each date range
    for service in services:
        # Fetch the corresponding document in service2
        collection_service2 = db_service[service]
        weekly_costs = []
        
        for start_date, end_date in date_ranges:
            # Fetch the data for the current week
            weekly_cost = calculate_weekly_cost(service, start_date, end_date)
            weekly_costs.append(weekly_cost)

        # Reverse the list to get the latest week first
        weekly_costs.reverse()

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

        # Update the corresponding document in service2
        collection_service2 = db_service[service]
        collection_service2.update_one(
            {"Service-Alert-Threshold": {"$exists": True}},
            {
                "$set": {
                    "Service-Alert-Threshold.Weekly-Threshold-Percentage": weekly_threshold_percentage,
                    "Service-Alert-Threshold.Weekly-Threshold-Value": weekly_threshold_value
                }
            }
        )

        # # Print the weekly costs
        # print(f"Service: {service} - Weekly Costs: {weekly_costs}")
        # # Print the percentage changes
        # print(f"Percentage Changes: {percentage_changes}")
        # # Print the average percentage change
        # print(f"Average Percentage Change: {average_percentage_change}")
        # # Print the weekly threshold percentage
        # print(f"Weekly Threshold Percentage: {weekly_threshold_percentage}")
        # # Print the average cost
        # print(f"Average Cost: {average_cost}")
        # # Print the weekly threshold value
        # print(f"Weekly Threshold Value: {weekly_threshold_value}")

def calculate_weekly_cost(service, start_date, end_date):
    data = list(db[service].find())
    weekly_cost = 0

    # Iterate over each document in the data
    for doc in data:
        for year, months in doc.items():
            if not year.isdigit():
                continue
            for month, days in months.items():
                if not month.isdigit():
                    continue
                for day, cost in days.items():
                    if not day.isdigit():
                        continue
                    date = datetime(int(year), int(month), int(day)).date()
                    # Check if the current day is within the specified week range
                    if start_date <= date <= end_date:
                        weekly_cost += cost

    return weekly_cost

# Function to calculate monthly cost data
def monthly():
    # Fetch the date range
    min_date, max_date = get_date_range()

    # Initialize an empty dictionary to store monthly data for each service
    monthly_data = {}

    # Calculate start and end dates for the past 4 months
    # Set the end date to the last day of the previous month
    end_date = max_date.replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1) - relativedelta(months=3)

    # Get the list of services
    services = sorted(db.list_collection_names())

    # Iterate over each service
    for service in services:
        # Initialize an empty list to store monthly costs for the current service
        monthly_data[service] = []

        # Query the database for the current service
        data = list(db[service].find())

        # Iterate over each month within the selected date range
        current_date = start_date.replace(day=1)
        while current_date.replace(day=1) <= end_date.replace(day=1):
            # Initialize the monthly usage for the current service and month to 0
            monthly_cost = 0

            # Iterate over each document in the data
            for doc in data:
                # Iterate over the years in the document
                for year, months in doc.items():
                    # Skip if the year is not numeric
                    if not year.isdigit():
                        continue
                    # Iterate over the months in the year
                    for month, days in months.items():
                        # Iterate over the days in the month
                        for day, cost in days.items():
                            # Convert the date to a datetime object
                            date = datetime(int(year), int(month), int(day)).date()
                            # Check if the date falls within the current month
                            if current_date.replace(day=1) <= date <= (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1):
                                # Add the cost to the monthly usage for the current service and month
                                monthly_cost += cost

            # Append the monthly cost to the list for the current service
            monthly_data[service].append(monthly_cost)

            # Count of data for each service
            count = len(monthly_data[service])

            # Service total cost by adding all cost of each service
            total_monthly_cost = sum(monthly_data[service])

            # Average cost (total cost / count )
            monthly_average_cost = total_monthly_cost / count if count > 0 else 0

            # Monthly percentage changes
            percentage_changes = []
            for i in range(1, count):
                if monthly_data[service][i-1] != 0:
                    denominator = monthly_data[service][i-1] if monthly_data[service][i-1] >= 1 else 1
                    percentage_change = ((monthly_data[service][i] - monthly_data[service][i-1]) / denominator) * 100
                    if -100 < percentage_change < 100:
                        percentage_changes.append(percentage_change)

            # Calculate average percentage change
            average_percentage_change = max(0, sum(percentage_changes) / len(percentage_changes) if percentage_changes else 0)
            monthly_threshold_percentage = average_percentage_change + idle_percentage
            monthly_threshold_percentage = round(monthly_threshold_percentage)

            # Calculate monthly threshold value
            monthly_threshold_value = monthly_average_cost + (idle_percentage / 100 * monthly_average_cost)
            monthly_threshold_value = round(monthly_threshold_value, 2)

            # Update the corresponding document in service2
            collection_service2 = db_service[service]
            collection_service2.update_one(
                {"Service-Alert-Threshold": {"$exists": True}},
                {
                    "$set": {
                        "Service-Alert-Threshold.Monthly-Threshold-Percentage": monthly_threshold_percentage,
                        "Service-Alert-Threshold.Monthly-Threshold-Value": monthly_threshold_value
                    }
                }
            )

            # Move to the next month
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

    return monthly_data

# Execute all three functions
daily_data = daily()
weekly_data = weekly()
monthly_data = monthly()
