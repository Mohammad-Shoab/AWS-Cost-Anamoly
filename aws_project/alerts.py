import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from dateutil.relativedelta import relativedelta

# Configure the database host
DATABASE_HOST = os.getenv("DATABASE_HOST")

# Connect to the MongoDB databases
client = MongoClient(f"mongodb://{DATABASE_HOST}/?authSource=admin")
db = client["usage"]
db_service = client["service"]

# Function to get latest date range
def get_latest_date_range():
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

    return max_date

# Function for daily usagetype level alert
def daily_usagetype_alert():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Get the latest date as datetime object
    end_date = get_latest_date_range()
    start_date = end_date - timedelta(days=2)

    # Query the database for latest_date's data
    for service in services:
        # Get the collection object
        collection = db[service]

        for usage_type_doc in collection.find():
            usage_type = usage_type_doc["UsageTypes"]

            # Initialize variables to track costs for the three dates
            costs = {start_date + timedelta(days=i): 0 for i in range(3)}

            # Iterate over each day's data to find the latest
            for year, months in usage_type_doc.items():
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

                                # Check if current date is within the date range
                                if start_date <= current_date <= end_date:
                                    costs[current_date] += cost

            cost1 = costs[start_date]
            cost2 = costs[start_date + timedelta(days=1)]
            cost3 = costs[end_date]

            # Fetch the corresponding document in service2
            collection_service2 = db_service[service]
            service_entry = collection_service2.find_one({"UsageTypes.UsageType": usage_type})

            if service_entry:
                # Fetch the daily threshold value
                usage_types = service_entry.get("UsageTypes", [])
                for usage_type_info in usage_types:
                    if usage_type_info.get("UsageType") == usage_type:
                        daily_alert = usage_type_info.get("Daily-Alert", "false")
                        daily_threshold_value = float(usage_type_info.get("Daily-Threshold-Value", 0))
                        daily_threshold_percentage = float(usage_type_info.get("Daily-Threshold-Percentage", 0))

                        if daily_alert.lower == "true":
                            # Compare cost3 with threshold value
                            if cost3 > daily_threshold_value:
                                increase_amount = cost3 - daily_threshold_value
                                print(f"Daily Alert: {service} : {usage_type} - exceeded threshold by {increase_amount:.2f} on {end_date}")

                            # Percentage comparison with past day
                            if cost3 is not None and cost1 is not None and cost1 != 0:
                                percentage_increase_past_day = (cost3 - cost1) / cost1 * 100
                                if percentage_increase_past_day > daily_threshold_percentage:
                                    print(f"Daily Alert: {service} : {usage_type} increased by {percentage_increase_past_day:.2f}% on {end_date} from {end_date - timedelta(days=2)}")

                            # Percentage comparison with past two days
                            if cost3 is not None and cost2 is not None and cost2 != 0:
                                percentage_increase_past_two_days = (cost3 - cost2) / cost2 * 100
                                if percentage_increase_past_two_days > daily_threshold_percentage:
                                    print(f"Daily Alert: {service} : {usage_type} increased by {percentage_increase_past_two_days:.2f}% on {end_date} from {end_date - timedelta(days=1)}")

# Function for daily service level alert
def daily_service_alert():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Get the latest date as datetime object
    end_date = get_latest_date_range()
    start_date = end_date - timedelta(days=2)

    # Query the database for date's data
    for service in services:
        data = list(db[service].find())
        service_data = []
        for i in range((end_date - start_date).days + 1):
            date = start_date + timedelta(days=i)  # Removed .date() from start_date
            total_cost = 0
            for doc in data:
                year_data = doc.get(str(date.year), {})
                month_data = year_data.get(str(date.month).zfill(2), {})
                day_cost = month_data.get(str(date.day).zfill(2), 0)
                total_cost += day_cost
            
            service_data.append(total_cost)

        cost1 = service_data[0]
        cost2 = service_data[1]
        cost3 = service_data[2]
            
        # # Print the total cost for the service
        # print(f"Total cost for {service} on {end_date} is {sum(service_data)}")

        # Fetch the corresponding document in service2
        collection_service2 = db_service[service]
        service_entry = collection_service2.find_one()  # Use find_one() instead of find()

        if service_entry:
            # Fetch the daily threshold value and percentage from Service-Alert-Threshold
            daily_service_alert = service_entry.get("Service-Alert-Threshold", {}).get("Daily-Alert", "false")
            daily_threshold_value = float(service_entry.get("Service-Alert-Threshold", {}).get("Daily-Threshold-Value", 0))
            daily_threshold_percentage = float(service_entry.get("Service-Alert-Threshold", {}).get("Daily-Threshold-Percentage", 0))

            if daily_service_alert.lower() == "true":
                # Compare total cost with daily threshold value
                if cost3 > daily_threshold_value:
                    increase_amount = cost3 - daily_threshold_value
                    print(f"Daily Alert: {service} exceeded threshold by {increase_amount} on {end_date}")

                # Percentage comparison with past day
                if cost3 is not None and cost1 is not None and cost1 != 0:
                    percentage_increase_past_day = (cost3 - cost1) / cost1 * 100
                    if percentage_increase_past_day > daily_threshold_percentage:
                        print(f"Daily Alert: {service} increased by {percentage_increase_past_day:.2f}% on {end_date} from {end_date - timedelta(days=2)}")

                # Percentage comparison with past two days
                if cost3 is not None and cost2 is not None and cost2 != 0:
                    percentage_increase_past_two_days = (cost3 - cost2) / cost2 * 100
                    if percentage_increase_past_two_days > daily_threshold_percentage:
                        print(f"Daily Alert: {service} increased by {percentage_increase_past_two_days:.2f}% on {end_date} from {end_date - timedelta(days=1)}")

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

    # Calculate the last Sunday from max_date
    last_sunday = max_date - timedelta(days=(max_date.weekday() + 1) % 7)

    # Calculate the Monday of the same week
    last_monday = last_sunday - timedelta(days=6)

    return last_monday, last_sunday

# Function for weekly usage type level alert
def weekly_usagetype_alert():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Get the latest complete week date range
    start_date_current, end_date_current = get_latest_complete_week()

    # Calculate start and end dates for the past 2 weeks
    start_date_last_week = start_date_current - timedelta(days=7)
    end_date_last_week = end_date_current - timedelta(days=7)
    start_date_two_weeks_ago = start_date_current - timedelta(days=14)
    end_date_two_weeks_ago = end_date_current - timedelta(days=14)

    # Query the database for usage type data within each date range
    for service in services:
        # Get the collection object
        collection = db[service]

        for usage_type_doc in collection.find():
            usage_type = usage_type_doc["UsageTypes"]

            # Fetch the corresponding document in service2
            collection_service2 = db_service[service]
            service_entry = collection_service2.find_one({"UsageTypes.UsageType": usage_type})

            if service_entry:
                # Fetch the weekly threshold value and percentage
                usage_types = service_entry.get("UsageTypes", [])
                for usage_type_info in usage_types:
                    if usage_type_info.get("UsageType") == usage_type:
                        weekly_alert = usage_type_info.get("Weekly-Alert", "false")
                        weekly_threshold_value = float(usage_type_info.get("Weekly-Threshold-Value", 0))
                        weekly_threshold_percentage = float(usage_type_info.get("Weekly-Threshold-Percentage", 0))

                        if weekly_alert.lower() == "true":
                            # Fetch the data for current week
                            weekly_cost_current_week = calculate_weekly_cost1(service, usage_type, start_date_current, end_date_current)

                            # Compare current week cost with threshold value
                            if weekly_cost_current_week > weekly_threshold_value:
                                increase_amount = weekly_cost_current_week - weekly_threshold_value
                                print(f"Weekly Alert: {service} : {usage_type} - exceeded threshold by {increase_amount:.2f} for week starting {start_date_current.strftime('%Y-%m-%d')} to {end_date_current.strftime('%Y-%m-%d')}")

                            # Fetch the data for last week
                            weekly_cost_last_week = calculate_weekly_cost1(service, usage_type, start_date_last_week, end_date_last_week)

                            # Percentage comparison with last week
                            if weekly_cost_last_week != 0:
                                percentage_increase_last_week = (weekly_cost_current_week - weekly_cost_last_week) / weekly_cost_last_week * 100
                                if percentage_increase_last_week > weekly_threshold_percentage:
                                    print(f"Weekly Alert: {service} : {usage_type} - increased by {percentage_increase_last_week:.2f}% for week starting {start_date_current.strftime('%Y-%m-%d')} to {end_date_current.strftime('%Y-%m-%d')} from {start_date_last_week.strftime('%Y-%m-%d')} to {end_date_last_week.strftime('%Y-%m-%d')}")

                            # Fetch the data for two weeks ago
                            weekly_cost_two_weeks_ago = calculate_weekly_cost1(service, usage_type, start_date_two_weeks_ago, end_date_two_weeks_ago)

                            # Percentage comparison with two weeks ago
                            if weekly_cost_two_weeks_ago != 0:
                                percentage_increase_two_weeks_ago = (weekly_cost_current_week - weekly_cost_two_weeks_ago) / weekly_cost_two_weeks_ago * 100
                                if percentage_increase_two_weeks_ago > weekly_threshold_percentage:
                                    print(f"Weekly Alert: {service} : {usage_type} - increased by {percentage_increase_two_weeks_ago:.2f}% for week starting {start_date_current.strftime('%Y-%m-%d')} to {end_date_current.strftime('%Y-%m-%d')} from {start_date_two_weeks_ago.strftime('%Y-%m-%d')} to {end_date_two_weeks_ago.strftime('%Y-%m-%d')}")

# Function for weekly service level alert
def weekly_service_alert():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Get the latest complete week date range
    start_date_current, end_date_current = get_latest_complete_week()

    # Calculate start and end dates for the past 3 weeks
    start_date_last_week = start_date_current - timedelta(days=7)
    end_date_last_week = end_date_current - timedelta(days=7)
    start_date_two_weeks_ago = start_date_current - timedelta(days=14)
    end_date_two_weeks_ago = end_date_current - timedelta(days=14)

    # Query the database for service level data within each date range
    for service in services:
        # Fetch the corresponding document in service2
        collection_service2 = db_service[service]
        service_entry = collection_service2.find_one()

        if service_entry:
            # Fetch the weekly threshold value and percentage from Service-Alert-Threshold
            weekly_service_alert = service_entry.get("Service-Alert-Threshold", {}).get("Weekly-Alert", "false")
            weekly_threshold_value = float(service_entry.get("Service-Alert-Threshold", {}).get("Weekly-Threshold-Value", 0))
            weekly_threshold_percentage = float(service_entry.get("Service-Alert-Threshold", {}).get("Weekly-Threshold-Percentage", 0))

            if weekly_service_alert.lower() == "true":
                # Fetch the data for current week
                weekly_cost_current_week = calculate_weekly_cost(service, start_date_current, end_date_current)

                # Compare current week cost with threshold value
                if weekly_cost_current_week > weekly_threshold_value:
                    increase_amount = weekly_cost_current_week - weekly_threshold_value
                    print(f"Weekly Alert: {service} exceeded threshold by {increase_amount} for week starting {start_date_current.strftime('%Y-%m-%d')} to {end_date_current.strftime('%Y-%m-%d')}")

                # Fetch the data for last week
                weekly_cost_last_week = calculate_weekly_cost(service, start_date_last_week, end_date_last_week)

                # Percentage comparison with last week
                if weekly_cost_last_week != 0:
                    percentage_increase_last_week = (weekly_cost_current_week - weekly_cost_last_week) / weekly_cost_last_week * 100
                    if percentage_increase_last_week > weekly_threshold_percentage:
                        print(f"Weekly Alert: {service} increased by {percentage_increase_last_week:.2f}% for week starting {start_date_current.strftime('%Y-%m-%d')} to {end_date_current.strftime('%Y-%m-%d')} from {start_date_last_week.strftime('%Y-%m-%d')} to {end_date_last_week.strftime('%Y-%m-%m')}")

                # Fetch the data for two weeks ago
                weekly_cost_two_weeks_ago = calculate_weekly_cost(service, start_date_two_weeks_ago, end_date_two_weeks_ago)

                # Percentage comparison with two weeks ago
                if weekly_cost_two_weeks_ago != 0:
                    percentage_increase_two_weeks_ago = (weekly_cost_current_week - weekly_cost_two_weeks_ago) / weekly_cost_two_weeks_ago * 100
                    if percentage_increase_two_weeks_ago > weekly_threshold_percentage:
                        print(f"Weekly Alert: {service} increased by {percentage_increase_two_weeks_ago:.2f}% for week starting {start_date_current.strftime('%Y-%m-%d')} to {end_date_current.strftime('%Y-%m-%d')} from {start_date_two_weeks_ago.strftime('%Y-%m-%d')} to {end_date_two_weeks_ago.strftime('%Y-%m-%d')}")

def calculate_weekly_cost1(service, usage_type, start_date, end_date):
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

def calculate_weekly_cost(service, start_date, end_date):
    data = list(db[service].find())
    weekly_cost = 0

    # Iterate over each document in the data
    for doc in data:
        for year, months in doc.items():
            if not year.isdigit():
                continue
            for month, days in months.items():
                for day, cost in days.items():
                    date = datetime(int(year), int(month), int(day)).date()
                    # Check if the current day is within the specified week range
                    if start_date <= date <= end_date:
                        weekly_cost += cost

    return weekly_cost

# Function to get latest date range for complete months
def get_latest_complete_month():
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

    # Calculate the first day of the max_date month
    first_day_max_date_month = datetime(max_date.year, max_date.month, 1).date()

    # Calculate the first day of the previous month from the max_date month
    first_day_previous_month = first_day_max_date_month - relativedelta(months=1)

    # Calculate the first day of the month before the previous month
    first_day_two_months_ago = first_day_max_date_month - relativedelta(months=2)

    return first_day_two_months_ago, first_day_previous_month, first_day_max_date_month - timedelta(days=1)

# Function for monthly usage type level alert
def monthly_usagetype_alert():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Get the latest complete month date range
    start_date_two_months_ago, start_date_previous_month, end_date_previous_month = get_latest_complete_month()

    # Calculate end dates for the past two months
    end_date_two_months_ago = start_date_previous_month - timedelta(days=1)

    # Query the database for usage type data within the date range
    for service in services:
        # Get the collection object
        collection = db[service]

        for usage_type_doc in collection.find():
            usage_type = usage_type_doc["UsageTypes"]

            # Initialize variables to track monthly cost
            monthly_cost_two_months_ago = 0
            monthly_cost_previous_month = 0

            # Iterate over each day's data to aggregate monthly cost
            for year, months in usage_type_doc.items():
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

                                # Check if current date falls within the two-month-ago range
                                if start_date_two_months_ago <= current_date <= end_date_two_months_ago:
                                    monthly_cost_two_months_ago += cost
                                # Check if current date falls within the previous-month range
                                if start_date_previous_month <= current_date <= end_date_previous_month:
                                    monthly_cost_previous_month += cost

            # # Print the monthly data found for the current collection and usage type
            # if monthly_cost_two_months_ago is not None and monthly_cost_previous_month is not None:
            #     print(f"{service} : {usage_type} : {start_date_previous_month.strftime('%Y-%m')} : {monthly_cost_previous_month}")
            #     print(f"{service} : {usage_type} : {start_date_two_months_ago.strftime('%Y-%m')} : {monthly_cost_two_months_ago}")

            # Fetch the corresponding document in service2
            collection_service2 = db_service[service]
            service_entry = collection_service2.find_one({"UsageTypes.UsageType": usage_type})

            if service_entry:
                # Fetch the monthly threshold value and percentage
                usage_types = service_entry.get("UsageTypes", [])
                for usage_type_info in usage_types:
                    if usage_type_info.get("UsageType") == usage_type:
                        monthly_alert = usage_type_info.get("Monthly-Alert", "false")
                        monthly_threshold_value = float(usage_type_info.get("Monthly-Threshold-Value", 0))
                        monthly_threshold_percentage = float(usage_type_info.get("Monthly-Threshold-Percentage", 0))

                        if monthly_alert.lower() == "true":
                            # Compare monthly cost with threshold value
                            if monthly_cost_previous_month > monthly_threshold_value:
                                increase_amount = monthly_cost_previous_month - monthly_threshold_value
                                print(f"Monthly Alert: {service} : {usage_type} - exceeded threshold by {increase_amount:.2f} for {start_date_previous_month.strftime('%Y-%m')}")

                            # Percentage comparison with past month
                            if monthly_cost_previous_month is not None and monthly_cost_two_months_ago is not None and monthly_cost_two_months_ago != 0:
                                percentage_increase_past_month = (monthly_cost_previous_month - monthly_cost_two_months_ago) / monthly_cost_two_months_ago * 100
                                if percentage_increase_past_month > monthly_threshold_percentage:
                                    print(f"Monthly Alert: {service} : {usage_type} - increased by {percentage_increase_past_month:.2f}% for {start_date_previous_month.strftime('%Y-%m')} from {start_date_two_months_ago.strftime('%Y-%m')}")

# Function for monthly service level alert
def monthly_service_alert():
    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Get the latest complete month date range
    start_date_two_months_ago, start_date_previous_month, end_date_previous_month = get_latest_complete_month()

    # Calculate end dates for the past two months
    end_date_two_months_ago = start_date_previous_month - timedelta(days=1)

    # Query the database for service level data within the date range
    for service in services:
        monthly_data = []

        # Query the database for the current service
        data = list(db[service].find())

        # Initialize the monthly usage for the current service and month to 0
        monthly_cost_two_months_ago = 0
        monthly_cost_previous_month = 0

        # Iterate over each document in the data
        for doc in data:
            # Iterate over the years in the document
            for year, months in doc.items():
                # Skip if the year is not numeric
                if not year.isdigit():
                    continue
                # Iterate over the months in the year
                for month, days in months.items():
                    # Skip if the month is not numeric
                    if not month.isdigit():
                        continue
                    # Iterate over the days in the month
                    for day, cost in days.items():
                        # Convert the date to a datetime object
                        date = datetime(int(year), int(month), int(day)).date()
                        # Check if the date falls within the two-month-ago range
                        if start_date_two_months_ago <= date <= end_date_two_months_ago:
                            monthly_cost_two_months_ago += cost
                        # Check if the date falls within the previous-month range
                        if start_date_previous_month <= date <= end_date_previous_month:
                            monthly_cost_previous_month += cost

        monthly_data.append(monthly_cost_two_months_ago)
        monthly_data.append(monthly_cost_previous_month)

        # # Print the monthly data for the current service
        # print(f"Monthly data for {service}: {monthly_data}")

        cost1 = monthly_data[0]  # Two months ago
        cost2 = monthly_data[1]  # Previous month

        # Fetch the corresponding document in service2
        collection_service2 = db_service[service]
        service_entry = collection_service2.find_one()

        if service_entry:
            # Fetch the monthly threshold value and percentage from Service-Alert-Threshold
            monthly_service_alert = service_entry.get("Service-Alert-Threshold", {}).get("Monthly-Alert", "false")
            monthly_threshold_value = float(service_entry.get("Service-Alert-Threshold", {}).get("Monthly-Threshold-Value", 0))
            monthly_threshold_percentage = float(service_entry.get("Service-Alert-Threshold", {}).get("Monthly-Threshold-Percentage", 0))

            if monthly_service_alert.lower() == "true":
                # Compare total cost with monthly threshold value
                if cost2 > monthly_threshold_value:
                    increase_amount = cost2 - monthly_threshold_value
                    print(f"Monthly Alert: {service} exceeded threshold by {increase_amount:.2f} for {end_date_previous_month.strftime('%Y-%m')}")

                # Percentage comparison with past month
                if cost2 is not None and cost1 is not None and cost1 != 0:
                    percentage_increase_past_month = (cost2 - cost1) / cost1 * 100
                    if percentage_increase_past_month > monthly_threshold_percentage:
                        print(f"Monthly Alert: {service} increased by {percentage_increase_past_month:.2f}% for {end_date_previous_month.strftime('%Y-%m')} from {(start_date_two_months_ago).strftime('%Y-%m')}")

if __name__ == "__main__":
    latest_date = get_latest_date_range()
    if latest_date.day == 1:
        monthly_usagetype_alert()
        monthly_service_alert()
    else:
        daily_usagetype_alert()
        daily_service_alert()
    
    start_date, end_date = get_latest_complete_week()
    first_day_of_month = datetime(end_date.year, end_date.month, 1).date()
    if start_date <= first_day_of_month <= end_date:
        pass
    else:
        weekday = latest_date.weekday()
        if weekday == 0:
            weekly_usagetype_alert()
            weekly_service_alert()