import subprocess
import os
import logging
from flask import Flask, jsonify, render_template, request
from flask_caching import Cache
from flask_pymongo import PyMongo
import datetime
from pymongo import MongoClient
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from usage.routes import usage_bp, init_cache  # type: ignore # assuming usage.routes is the module where your blueprint is defined
from alert.routes import alert_bp  # type: ignore # assuming alert.routes is the module where your blueprint is defined
import json
import re

# Create log directory if it doesn't exist
log_dir = "/var/log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler("/var/log/stdin.log"),
                        logging.FileHandler("/var/log/stdout.log"),
                        logging.FileHandler("/var/log/stderr.log"),
                        logging.StreamHandler()  # This will print to stdout
                    ])

logger = logging.getLogger(__name__)

# Example usage of logging
logger.info("Application is starting...")

app = Flask(__name__)

app.config["CACHE_TYPE"] = "simple"  # Example cache type; adjust as needed

# Initialize cache for usage module routes
init_cache(app)

# Initialize cache
cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# Configure the database host
DATABASE_HOST = os.getenv("DATABASE_HOST")

# Configure MongoDB URIs
app.config["MONGO_URI_ALERT"] = f"mongodb://{DATABASE_HOST}/service?authSource=admin"
app.config["MONGO_URI_USAGE"] = f"mongodb://{DATABASE_HOST}/usage?authSource=admin"
app.config["MONGO_URI_EDITLOG"] = f"mongodb://{DATABASE_HOST}/editlogdb?authSource=admin"

# Initialize PyMongo instances
mongo_alert = PyMongo(app, uri=app.config["MONGO_URI_ALERT"])
mongo_usage = PyMongo(app, uri=app.config["MONGO_URI_USAGE"])
mongo_editlog = PyMongo(app, uri=app.config["MONGO_URI_EDITLOG"])

# Register blueprints
app.register_blueprint(usage_bp, url_prefix='/usage')
app.register_blueprint(alert_bp, url_prefix='/alert')

# # Initialize cache for usage module routes
# AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

# # Initialize Boto3 session
# session = boto3.Session(
#     aws_access_key_id=AWS_ACCESS_KEY_ID,
#     aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
#     region_name='us-east-1'
# )

# # Get the AWS Account ID
# sts_client = session.client('sts')
# account_id = sts_client.get_caller_identity()["Account"]

# # Initialize variables
# AWS_ACCOUNT_ID = account_id

AWS_ACCOUNT_ID = '123456789012'

# Connect to the usage database
client = MongoClient(f"mongodb://{DATABASE_HOST}/?authSource=admin")
db = client["usage"]

# Check if usage database has any collections
if not db.list_collection_names():
    # If not, run db_setup.py, theshold-service.py and threshold.py
    subprocess.run(["python3", "db_setup.py"])
    subprocess.run(["python3", "threshold-service.py"])
    subprocess.run(["python3", "threshold.py"])

# Path to the cron status file
CRON_STATUS_FILE = 'cron_status.json'

def load_cron_status():
    try:
        with open(CRON_STATUS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'enabled': True}

def save_cron_status(status):
    with open(CRON_STATUS_FILE, 'w') as f:
        json.dump(status, f)

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

def home():
    min_date, max_date = get_date_range()

    # Fetch the list of services
    services = sorted(db.list_collection_names())

    # Query the database based on the selected date range and update service_data
    service_data = {}
    end_date = max_date
    start_date = end_date - timedelta(days=6)  # Define start_date here

    # Convert dates to datetime objects
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    for service in services:
        data = list(db[service].find())
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

    return service_data

def calculate_percentage_change(current, previous):
    if previous == 0:
        return 0
    change = ((current - previous) / previous) * 100
    return round(change, 2)

def top_10_services_with_percentage(service_data):
    sorted_services = sorted(service_data.items(), key=lambda x: x[1][-1], reverse=True)
    top_10_services = {service: [round(cost, 2) for cost in costs[-2:]] for service, costs in sorted_services[:10]}
    
    service_changes = {}
    for service, costs in top_10_services.items():
        current, previous = costs[-1], costs[-2]
        percentage_change = calculate_percentage_change(current, previous)
        direction = 'up' if percentage_change > 0 else 'down'
        service_changes[service] = (current, direction, abs(percentage_change))
    
    return service_changes

def print_top_5_services(service_data):
    # Sort the list in descending order of cost of last date
    sorted_services = sorted(service_data.items(), key=lambda x: x[1][-1], reverse=True)

    # Create a dictionary for the top 5 services
    top_5_services = {service: costs for service, costs in sorted_services[:5]}

    return top_5_services

def calculate_weekly_data_index():
    min_date, max_date = get_date_range()

    weekly_data = {}

    # Calculate start and end dates for the past 5 weeks (including the current week)
    end_date = max_date - timedelta(days=(max_date.weekday() + 1) % 7)
    start_date = end_date - relativedelta(weeks=3)
    
    end_date = max_date

    # Find the Monday of the start date's week
    start_date -= timedelta(days=start_date.weekday())

    services = sorted(db.list_collection_names())
    for service in services:
        weekly_data[service] = {}

        # Initialize weekly data to 0 for each week in the range
        current_date = start_date
        while current_date <= end_date:
            weekly_data[service][current_date] = 0
            current_date += timedelta(days=7)

        data = list(db[service].find().sort("_id"))

        for doc in data:
            for year, months in doc.items():
                if not year.isdigit():
                    continue
                for month, days in months.items():
                    for day, cost in days.items():
                        date = datetime(int(year), int(month), int(day)).date()
                        week_start = date - timedelta(days=date.weekday())  # Find the Monday of the week
                        # Accumulate costs if the document date falls within the range
                        if start_date <= week_start <= end_date:
                            weekly_data[service][week_start] += cost

    return weekly_data

def calculate_monthly_data_index():
    # Fetch the date range
    min_date, max_date = get_date_range()

    # Initialize an empty dictionary to store monthly data for each service
    monthly_data = {}

    # Calculate start and end dates for the past 4 months (including the current month)
    end_date = max_date.replace(day=1) - timedelta(days=1)
    start_date = end_date.replace(day=1) - relativedelta(months=3)

    # Get the list of services
    services = sorted(db.list_collection_names())

    # Iterate over each service
    for service in services:
        # Initialize an empty dictionary to store monthly data for the current service
        monthly_data[service] = {}

        # Query the database for the current service
        data = list(db[service].find().sort("_id"))

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

def weekly_top_5_services(weekly_data):
    # Sort services based on the cost of the last available week
    sorted_services = sorted(weekly_data.items(), key=lambda x: list(x[1].values())[-2], reverse=True)

    # Create a dictionary for the top 5 services
    weekly_top_5_services = {service: list(costs.values()) for service, costs in sorted_services[:5]}

    return weekly_top_5_services

weekly_data = calculate_weekly_data_index()
#print(weekly_top_5_services(weekly_data))

def monthly_top_5_services(monthly_data):
    # Sort the list in descending order of cost of last date
    sorted_services = sorted(monthly_data.items(), key=lambda x: list(x[1].values())[-1], reverse=True)

    # Create a dictionary for the top 5 services
    monthly_top_5_services = {service: list(costs.values()) for service, costs in sorted_services[:5]}

    return monthly_top_5_services

monthly_data = calculate_monthly_data_index()
#print(monthly_top_5_services(monthly_data))

# Calculate total current and last month's cost
def total_last_two_month_cost(monthly_data):    
    # Sort the list in descending order of cost of last date
    sorted_services = monthly_data.items()

    # Create a dictionary for the for the current and last month costs
    last_two_month_cost = {}
    for service, costs in sorted_services:
        # Get the last two costs
        last_two_costs = list(costs.values())[-2:]
        
        # Check if the last two costs are the same
        if len(last_two_costs) == 2 and last_two_costs[0] == last_two_costs[1]:
            # If same, store both values
            last_two_month_cost[service] = last_two_costs
        else:
            # Otherwise, store only unique values
            last_two_month_cost[service] = list(dict.fromkeys(last_two_costs))

    # Calculate the total cost for the current and last month
    total_current_month_cost = 0
    total_last_month_cost = 0
    for service, costs in last_two_month_cost.items():
        total_current_month_cost += costs[-1]
        total_last_month_cost += costs[-2]

    return round(total_current_month_cost,2), round(total_last_month_cost,2)

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
                                current_date = datetime(int(year), int(month), int(day)).date()
                                if start_date <= current_date <= end_date:
                                    weekly_cost += cost
                            except ValueError:
                                continue
    return weekly_cost

@cache.cached(timeout=3600, key_prefix='regions_used')
def get_regions_used():
    min_date, max_date = get_date_range()
    end_date = max_date
    start_date = end_date - timedelta(days=(max_date.weekday() + 1) % 7)

    usage_types = []
    for service in db.list_collection_names():
        for usage_type_doc in db[service].find():
            usage_type = usage_type_doc["UsageTypes"]
            if calculate_weekly_cost(service, usage_type, start_date, end_date):
                usage_types.append(usage_type)

    region_pattern = re.compile(r'\b[A-Z]{2,4}\d{1,2}\b')
    regions = {match for usage_type in usage_types for match in region_pattern.findall(usage_type)}

    return sorted(regions)

@app.route('/')
def index():
    service_data = home()
    total_current_month_cost, total_last_month_cost = total_last_two_month_cost(monthly_data)
    top_services = top_10_services_with_percentage(service_data)
    num_services = len(db.list_collection_names())
    current_date = get_date_range()[1]
    aws_account_id = AWS_ACCOUNT_ID
    regions_used = ', '.join(get_regions_used())
    cron_status = load_cron_status()
    return render_template('index.html', num_services=num_services, top_services=top_services, total_current_month_cost=total_current_month_cost, total_last_month_cost=total_last_month_cost, current_date=current_date, aws_account_id=aws_account_id, regions_used=regions_used, cron_enabled=cron_status['enabled'])

def generate_daily_labels():
    min_date, max_date = get_date_range()
    end_date = max_date
    start_date = end_date - timedelta(days=6)
    labels = []
    current_date = start_date
    while current_date <= end_date:
        labels.append(current_date.strftime("%y-%m-%d"))
        current_date += timedelta(days=1)
    return labels

@app.route('/data')
@cache.cached(timeout=86400, key_prefix='daily_data')
def data():
    labels = generate_daily_labels()
    data = print_top_5_services(home())
    return jsonify(data=data, labels=labels)

def generate_weekly_labels():
    min_date, max_date = get_date_range()
    # Calculate start and end dates for the past 5 weeks (including the current week)
    end_date = max_date - timedelta(days=(max_date.weekday() + 1) % 7)
    start_date = end_date - relativedelta(weeks=3)
    end_date = max_date
    # Find the Monday of the start date's week
    start_date -= timedelta(days=start_date.weekday())
    labels = []
    current_date = start_date
    while current_date <= end_date:
        week_start = current_date
        week_end = week_start + timedelta(days=6)
        labels.append(f"{week_start.strftime('%Y-%m-%d')}- {week_end.strftime('%Y-%m-%d')}")
        current_date += timedelta(weeks=1)
    return labels[:4]

@app.route('/weekly')
@cache.cached(timeout=86400, key_prefix='weekly_data')
def weekly():
    labels = generate_weekly_labels()
    return jsonify(data=weekly_top_5_services(weekly_data), labels=labels)

def generate_monthly_labels():
    min_date, max_date = get_date_range()
    end_date = max_date
    start_date = end_date.replace(day=1)
    start_date = start_date - relativedelta(months=4)
    labels = []
    current_date = start_date
    while current_date <= end_date:
        labels.append(current_date.strftime('%B %y'))
        current_date += relativedelta(months=1)
    return labels[:4]

@app.route('/monthly')
@cache.cached(timeout=86400, key_prefix='monthly_data')
def monthly():
    labels = generate_monthly_labels()
    monthly_data_values = monthly_top_5_services(monthly_data)
    return jsonify(data=monthly_data_values, labels=labels)

def daily(service):
    min_date, max_date = get_date_range()

    # Query the database based on the selected date range and update service_data
    end_date = max_date
    start_date = end_date - timedelta(days=6)  # Define start_date here

    # Convert dates to datetime objects
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    service_data = {}
    data = list(db[service].find())
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

    return service_data

def weekly(service):
    min_date, max_date = get_date_range()
    weekly_costs = []

    # Calculate start and end dates for the past 5 weeks (including the current week)
    end_date = max_date - timedelta(days=(max_date.weekday() + 1) % 7)
    start_date = end_date - relativedelta(weeks=4)  # Adjusted to get past 5 weeks including current week
    end_date = max_date

    # Find the Monday of the start date's week
    start_date -= timedelta(days=start_date.weekday())

    # Initialize weekly data to 0 for each week in the range
    weekly_data = {}
    current_date = start_date
    while current_date <= end_date:
        weekly_data[current_date] = 0
        current_date += timedelta(days=7)

    data = list(db[service].find().sort("_id"))

    for doc in data:
        for year, months in doc.items():
            if not year.isdigit():
                continue
            for month, days in months.items():
                for day, cost in days.items():
                    date = datetime(int(year), int(month), int(day)).date()
                    week_start = date - timedelta(days=date.weekday())  # Find the Monday of the week
                    # Accumulate costs if the document date falls within the range
                    if start_date <= week_start <= end_date:
                        weekly_data[week_start] += cost

    # Convert the weekly_data dictionary to a sorted list of costs
    for week_start in sorted(weekly_data.keys()):
        weekly_costs.append(weekly_data[week_start])

    return {service: weekly_costs}

def monthly(service):
    # Fetch the date range
    min_date, max_date = get_date_range()

    # Calculate start and end dates for the past 4 months (including the current month)
    end_date = max_date.replace(day=1)-timedelta(days=1)
    start_date = end_date.replace(day=1) - relativedelta(months=3)

    # Initialize a list to store monthly costs for the current service
    monthly_costs = []
    data = list(db[service].find().sort("_id"))
    current_date = start_date
    while current_date < end_date:
        monthly_total = 0
        for doc in data:
            for year, months in doc.items():
                if not year.isdigit():
                    continue
                for month, days in months.items():
                    for day, cost in days.items():
                        date = datetime(int(year), int(month), int(day)).date()
                        if current_date <= date < (current_date + relativedelta(months=1)):
                            monthly_total += cost
        monthly_costs.append(round(monthly_total, 2))
        # Move to the next month
        current_date += relativedelta(months=1)

    return {service: monthly_costs}

@app.route('/services/')
def get_services():
    # Replace this with the actual logic to fetch services
    services = sorted(db.list_collection_names())
    return jsonify(services=services)

@app.route('/daily_service/')
@cache.cached(timeout=86400, query_string=True)
def daily_service():
    services = sorted(db.list_collection_names())
    service1 = services[0]
    service = request.args.get('service', service1)
    graph_type = request.args.get('graph_type', 'bar')  # Default to 'bar' if not specified
    labels = generate_daily_labels()
    data = daily(service)
    return jsonify(data=data, labels=labels, graph_type=graph_type)

@app.route('/weekly_service/')
@cache.cached(timeout=86400, query_string=True)
def weekly_service():
    services = sorted(db.list_collection_names())
    service1 = services[0]
    service = request.args.get('service', service1)
    graph_type = request.args.get('graph_type', 'bar')  # Default to 'bar' if not specified
    labels = generate_weekly_labels()  # Ensure this matches weekly data
    data = weekly(service)
    return jsonify(data=data, labels=labels, graph_type=graph_type)

@app.route('/monthly_service/')
@cache.cached(timeout=86400, query_string=True)
def monthly_service():
    services = sorted(db.list_collection_names())
    service1 = services[0]
    service = request.args.get('service', service1)
    graph_type = request.args.get('graph_type', 'bar')  # Default to 'bar' if not specified
    labels = generate_monthly_labels()  # Ensure this matches monthly data
    data = monthly(service)
    return jsonify(data=data, labels=labels, graph_type=graph_type)

@app.route('/toggle-cron', methods=['POST'])
def toggle_cron():
    status = request.json.get('isChecked')
    cron_status = {'enabled': status}
    save_cron_status(cron_status)
    return jsonify(message='Cron status updated', status=cron_status['enabled'])

def run_cron_jobs():
    cron_status = load_cron_status()
    if datetime.now().hour == 23:
        if cron_status['enabled']:
            subprocess.run(["python3", "pythondb.py"])
        subprocess.run(["python3", "cache.py"])
        subprocess.run(["python3", "send_alerts.py"])

# Route to clear cache
@app.route('/clear_cache')
def clear_cache():
    cache.clear()
    return "Cache cleared!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)