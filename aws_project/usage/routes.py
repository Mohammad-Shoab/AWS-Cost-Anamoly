from flask import Blueprint, render_template, request
from flask_pymongo import PyMongo
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from . import usage_bp

from flask_caching import Cache
from hashlib import md5

def make_cache_key():
    return md5(request.path.encode('utf-8')).hexdigest()

cache = Cache()

# Initialize cache with default settings
def init_cache(app):
    cache.init_app(app)

usage_bp = Blueprint('usage', __name__, template_folder='templates')

# Use the usage MongoDB instance
mongo_usage = PyMongo()

@usage_bp.record_once
def on_load(state):
    global mongo_usage
    mongo_usage.init_app(state.app, uri=state.app.config["MONGO_URI_USAGE"])

# Function to get date range
def get_date_range():
    min_date = datetime.utcnow().date()
    max_date = datetime(1970, 1, 1).date()  # start with a very old date

    for collection in mongo_usage.db.list_collection_names():
        data = list(mongo_usage.db[collection].find())
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


def get_usage_data(service):
    # Query the database for the specified service
    data = list(mongo_usage.db[service].find())

    # Initialize an empty dictionary to store the usage data
    usage_data = {}

    # Loop through the data and populate the usage_data dictionary
    for doc in data:
        for year, months in doc.items():
            if not year.isdigit():
                continue
            for month, days in months.items():
                for day, cost in days.items():
                    date = f"{year}-{month}-{day}"
                    usage_type = doc.get('UsageTypes')
                    if usage_type not in usage_data:
                        usage_data[usage_type] = {}
                    usage_data[usage_type][date] = float(cost)

    return usage_data


# Function to calculate weekly usage data
@cache.cached(timeout=86400, key_prefix=make_cache_key)  # Cache for 24 hours (adjust timeout as needed)
def calculate_weekly_data(service):
    # Query the database for the specified service
    data = list(mongo_usage.db[service].find())

    # Initialize weekly data dictionary
    weekly_data = {}

    min_date, max_date = get_date_range()
    # Calculate start and end dates for the past 8 weeks (including the current week)
    # end_date = max_date
    end_date = max_date - timedelta(days=(max_date.weekday() + 1) % 7)
    start_date = end_date - relativedelta(weeks=7)

    # Find the Monday of the start_date week
    start_date -= timedelta(days=start_date.weekday())

    # Iterate over each week within the selected date range
    current_date = start_date
    while current_date <= end_date:
        for doc in data:
            usage_type = doc.get('UsageTypes')
            if usage_type not in weekly_data:
                weekly_data[usage_type] = {}
            weekly_data[usage_type][current_date] = 0
            for year, months in doc.items():
                if not year.isdigit():
                    continue
                for month, days in months.items():
                    for day, cost in days.items():
                        date = datetime(int(year), int(month), int(day)).date()
                        if current_date <= date < current_date + timedelta(days=7):
                            weekly_data[usage_type][current_date] += cost
        # Move to next week
        current_date += timedelta(days=7)

    return weekly_data


# Function to calculate monthly usage data
@cache.cached(timeout=86400)  # Cache for 24 hours (adjust timeout as needed)
def calculate_monthly_data(service):
    # Query the database for the specified service
    data = list(mongo_usage.db[service].find())

    # Initialize monthly data dictionary
    monthly_data = {}

    # Fetch the date range
    min_date, max_date = get_date_range()

    # Calculate start and end dates for the past 8 months (including the current month)
    # end_date = max_date.replace(day=1)
    end_date = max_date.replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1) - relativedelta(months=7)

    # Iterate over each month within the selected date range
    current_date = start_date.replace(day=1)
    while current_date.replace(day=1) <= end_date.replace(day=1):
        for doc in data:
            usage_type = doc.get('UsageTypes')
            if usage_type not in monthly_data:
                monthly_data[usage_type] = {}
            monthly_data[usage_type][current_date.strftime('%B-%Y')] = 0
            for year, months in doc.items():
                if not year.isdigit():
                    continue
                for month, days in months.items():
                    for day, cost in days.items():
                        date = datetime(int(year), int(month), int(day)).date()
                        if current_date.replace(day=1) <= date <= (current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1):
                            monthly_data[usage_type][current_date.strftime('%B-%Y')] += cost
        # Move to next month
        current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

    return monthly_data


@usage_bp.route('/', methods=['GET', 'POST'])
def index():
    min_date, max_date = get_date_range()

    # Fetch the list of services
    services = sorted(mongo_usage.db.list_collection_names())

    if request.method == 'POST':
        # Retrieve selected end date
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()

        # Calculate the start date to ensure a continuous 7-day range
        start_date = end_date - timedelta(days=6)

        # Validate end date
        if end_date > datetime.utcnow().date() - timedelta(days=1):
            end_date = datetime.utcnow().date() - timedelta(days=1)

        # Convert dates to datetime objects
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())

        # Query the database based on the selected date range and update service_data
        service_data = {}
        for service in services:
            data = list(mongo_usage.db[service].find())
            service_data[service] = []
            for i in range(7):
                date = start_date.date() + timedelta(days=i)
                total_cost = 0
                for doc in data:
                    year_data = doc.get(str(date.year), {})
                    month_data = year_data.get(str(date.month).zfill(2), {})
                    day_cost = month_data.get(str(date.day).zfill(2), 0)
                    total_cost += day_cost
                service_data[service].append(total_cost)
    else:
        # Default to showing data for the last 7 days
        end_date = max_date
        start_date = end_date - timedelta(days=6)

        # Convert dates to datetime objects
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())

        # Query the database for the last 7 days' data
        service_data = {}
        for service in services:
            data = list(mongo_usage.db[service].find())
            service_data[service] = []
            for i in range(7):
                date = start_date.date() + timedelta(days=i)
                total_cost = 0
                for doc in data:
                    year_data = doc.get(str(date.year), {})
                    month_data = year_data.get(str(date.month).zfill(2), {})
                    day_cost = month_data.get(str(date.day).zfill(2), 0)
                    total_cost += day_cost
                service_data[service].append(total_cost)

    return render_template('usage.html', service_data=service_data, min_date=min_date, max_date=max_date, start_date=start_date, end_date=end_date, timedelta=timedelta)


@usage_bp.route('/usage-types/<service>', methods=['GET', 'POST'])
def usage(service):
    min_date, max_date = get_date_range()

    if request.method == 'POST':
        # Retrieve selected start and end dates
        # Retrieve selected end date
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()

        # Calculate the start date to ensure a continuous 7-day range
        start_date = end_date - timedelta(days=6)

        # Validate end date
        if end_date > datetime.utcnow().date() - timedelta(days=1):
            end_date = datetime.utcnow().date() - timedelta(days=1)

        # Convert dates to datetime objects
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())

    else:
        # Default to showing data for the last 7 days
        end_date = max_date
        start_date = end_date - timedelta(days=6)

        # Convert dates to datetime objects
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())

    # Get usage data for the specified service
    usage_data = get_usage_data(service)

    return render_template('usage-types.html', service_name=service, usage_data=usage_data, min_date=min_date, max_date=max_date, start_date=start_date, end_date=end_date, timedelta=timedelta)


@usage_bp.route('/weekly_monthly/<service>', methods=['GET'])
def weekly_monthly(service):
    data_type = request.args.get('data_type')

    # Fetch the date range
    min_date, max_date = get_date_range()

    # Set default end date to the latest date available in the database
    # end_date = max_date
    end_date = max_date - timedelta(days=(max_date.weekday() + 1) % 7)

    # Calculate the start date as the Monday of the week containing the end date
    start_date = end_date - timedelta(days=end_date.weekday())

    # Set start date to the beginning of the week
    start_date = start_date - timedelta(weeks=7)

    # Calculate the labels for the columns
    if data_type == 'weekly':
        # Calculate weekly labels from Monday to Sunday for each week
        labels = [(start_date + timedelta(days=i)).strftime('%y-%m-%d') + ' - ' + (start_date + timedelta(days=i+6)).strftime('%y-%m-%d') for i in range(0, 56, 7)]
        # Calculate weekly usage data
        usage_data = calculate_weekly_data(service)
    elif data_type == 'monthly':
        start_date = max_date.replace(day=1) - timedelta(days=1)
        start_date = start_date - relativedelta(months=7)
        labels = [(start_date.replace(day=1) + relativedelta(months=i)).strftime('%B %y') for i in range(8)]
        # Calculate monthly usage data
        usage_data = calculate_monthly_data(service)
    else:
        # Handle invalid data type
        return "Invalid data type", 400

    return render_template('weekly_monthly.html', service_name=service, usage_data=usage_data, data_type=data_type, min_date=min_date, max_date=max_date, start_date=start_date, end_date=end_date, labels=labels, timedelta=timedelta)

@cache.cached(timeout=86400, key_prefix=make_cache_key)  # Cache for 24 hours (adjust timeout as needed)
def calculate_weekly_data_index():
    min_date, max_date = get_date_range()

    weekly_data = {}

    # Calculate start and end dates for the past 8 weeks (including the current week)
    # end_date = max_date
    end_date = max_date - timedelta(days=(max_date.weekday() + 1) % 7)
    start_date = end_date - relativedelta(weeks=7)

    # Find the Monday of the current week
    start_date -= timedelta(days=start_date.weekday())

    services = sorted(mongo_usage.db.list_collection_names())
    for service in services:
        weekly_data[service] = {}

        data = list(mongo_usage.db[service].find())

        current_date = start_date
        while current_date <= end_date:
            weekly_data[service][current_date] = 0
            for doc in data:
                for year, months in doc.items():
                    if not year.isdigit():
                        continue
                    for month, days in months.items():
                        for day, cost in days.items():
                            date = datetime(int(year), int(month), int(day)).date()
                            # Check if the current day is within the current week
                            if current_date <= date < current_date + timedelta(days=7):
                                weekly_data[service][current_date] += cost
            current_date += timedelta(days=7)

    return weekly_data

@cache.cached(timeout=86400)  # Cache for 24 hours (adjust timeout as needed)
def calculate_monthly_data_index():
    # Fetch the date range
    min_date, max_date = get_date_range()

    # Initialize an empty dictionary to store monthly data for each service
    monthly_data = {}

    # Calculate start and end dates for the past 8 months (including the current month)
    # end_date = max_date.replace(day=1)
    end_date = max_date.replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1) - relativedelta(months=7)

    # Get the list of services
    services = sorted(mongo_usage.db.list_collection_names())

    # Iterate over each service
    for service in services:
        # Initialize an empty dictionary to store monthly data for the current service
        monthly_data[service] = {}

        # Query the database for the current service
        data = list(mongo_usage.db[service].find())

        # Iterate over each month within the selected date range
        current_date = start_date.replace(day=1)
        while current_date.replace(day=1) <= end_date.replace(day=1):
            # Initialize the monthly usage for the current service and month to 0
            monthly_data[service][current_date.strftime('%B-%Y')] = 0

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
                                monthly_data[service][current_date.strftime('%B-%Y')] += cost
            # Move to the next month
            current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

    return monthly_data


@usage_bp.route('/weekly_monthly_index', methods=['GET'])
def weekly_monthly_index():
    data_type = request.args.get('data_type')

    min_date, max_date = get_date_range()

    # end_date = max_date
    end_date = max_date - timedelta(days=(max_date.weekday() + 1) % 7)

    start_date = end_date - timedelta(days=end_date.weekday())
    start_date = start_date - timedelta(weeks=7)
    
    if data_type == 'weekly':
        labels = [(start_date + timedelta(days=i)).strftime('%y-%m-%d') + ' - ' + (start_date + timedelta(days=i+6)).strftime('%y-%m-%d') for i in range(0, 56, 7)] 
        usage_data = calculate_weekly_data_index()
    elif data_type == 'monthly':
        start_date = max_date.replace(day=1) - timedelta(days=1)
        start_date = start_date - relativedelta(months=7)
        labels = [(start_date.replace(day=1) + relativedelta(months=i)).strftime('%B %y') for i in range(8)]
        usage_data = calculate_monthly_data_index()
    else:
        return "Invalid data type", 400

    return render_template('weekly_monthly_index.html', labels=labels, usage_data=usage_data, data_type=data_type, min_date=min_date, max_date=max_date, start_date=start_date, end_date=end_date, timedelta=timedelta)

# If you need to clear cache within usage/routes.py
@usage_bp.route('/clear_usage_cache')
def clear_usage_cache():
    cache.clear()
    return "Usage cache cleared!"