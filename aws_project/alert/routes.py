from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_pymongo import PyMongo
from bson import ObjectId
import json

from . import alert_bp

alert_bp = Blueprint('alert', __name__, template_folder='templates')

# Use the alert MongoDB instance
mongo_alert = PyMongo()
mongo_editlog = PyMongo()

@alert_bp.record_once
def on_load(state):
    global mongo_alert
    mongo_alert.init_app(state.app, uri=state.app.config["MONGO_URI_ALERT"])
    mongo_editlog.init_app(state.app, uri=state.app.config["MONGO_URI_EDITLOG"])

# Function to log edit details
def log_edit(collection_name, document_id, previous_data, updated_data):
    current_date = datetime.utcnow().strftime("%Y-%m-%d")  # Get current date in YYYY-MM-DD format
    collection_name = f"{current_date}"  # Use a collection name like 'editlogs_2024-01-01'

    log_data = {
        "collection_name": collection_name,
        "document_id": str(document_id),
        "previous_data": json.dumps(previous_data, default=str),
        "updated_data": json.dumps(updated_data, default=str),
        "timestamp": datetime.utcnow(),
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get('User-Agent'),
        "session_id": request.cookies.get('session')
    }
    # current_app.config["MONGO_URI_EDITLOG"].db.editlogs.insert_one(log_data)
    # mongo_editlog.db.editlogs.insert_one(log_data)
    mongo_editlog.db[collection_name].insert_one(log_data)

# Function to check if a value is a positive integer
def is_positive_integer(value):
    try:
        int_value = int(value)
        return int_value > 0
    except ValueError:
        return False

# Function to sanitize input by removing extra spaces
def sanitize_input(value):
    return value.strip()

# Error handler for 404 - Page not found
@alert_bp.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_message="Page not found"), 404

# Error handler for 500 - Internal server error
@alert_bp.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_message="Internal server error"), 500

@alert_bp.route('/')
def index():
    collections = sorted(mongo_alert.db.list_collection_names())
    return render_template('service.html', collections=collections, mongo=mongo_alert)

# Route for editing service-level data of a specific service
@alert_bp.route('/edit-service/<collection_name>', methods=['GET', 'POST'])
def edit_service(collection_name):
    service_data = mongo_alert.db[collection_name].find_one()  # Retrieve service-level data from the specified collection
    if request.method == 'POST':
        updated_data = {}
        for field in request.form:
            if field != '_id':  # Exclude _id field from update
                value = request.form[field]
                if field in ['Daily-Threshold-Percentage', 'Weekly-Threshold-Percentage', 'Monthly-Threshold-Percentage', 'Daily-Threshold-Value', 'Weekly-Threshold-Value', 'Monthly-Threshold-Value']:
                    value = value.strip()
                    value = value.lower() if value.upper() == 'NA' else value
                updated_data[field] = sanitize_input(value)

        previous_data = service_data.get('Service-Alert-Threshold', {}) # Get the previous service-level data
        mongo_alert.db[collection_name].update_one({}, {'$set': {'Service-Alert-Threshold': updated_data}})  # Update the service-level data
        
        # Log the edit details
        log_edit(collection_name, "N/A", previous_data, updated_data)
        return redirect(url_for('alert.index'))
    else:
        return render_template('edit-service.html', collection_name=collection_name, service_data=service_data)

# Route for handling form submission to choose a collection
@alert_bp.route('/collection', methods=['POST'])
def show_collection_data():
    collection_name = request.form['collection']
    return redirect(url_for('alert.collection', collection_name=collection_name))

# Route for displaying data of a specific collection
@alert_bp.route('/collection/<collection_name>')
def collection(collection_name):
    collection_data = mongo_alert.db[collection_name].find_one()  # Retrieve data from the specified collection
    if collection_data:
        collection_data = collection_data.get('UsageTypes', [])
    return render_template('collection.html', collection_name=collection_name, collection_data=collection_data)

# Route for editing a document in a collection
@alert_bp.route('/edit/<collection_name>/<string:document_id>', methods=['GET', 'POST'])
def edit(collection_name, document_id):
    document_id = ObjectId(document_id)  # Convert document ID to ObjectId
    collection_data = mongo_alert.db[collection_name].find_one()  # Find the document by ID
    document = None
    if collection_data:
        for doc in collection_data.get('UsageTypes', []):
            if doc['_id'] == document_id:
                document = doc
                break
    if document is None:
        return 'Document not found', 404  # If document not found, return 404
    if request.method == 'POST':
        updated_data = {}
        for field in request.form:
            if field != '_id':  # Exclude _id field from update
                value = request.form[field]
                if field in ['Daily-Threshold-Percentage', 'Weekly-Threshold-Percentage', 'Monthly-Threshold-Percentage', 'Daily-Threshold-Value', 'Weekly-Threshold-Value', 'Monthly-Threshold-Value']:
                    value = value.strip()
                    value = value.lower() if value.upper() == 'NA' else value
                updated_data[field] = sanitize_input(value)

        previous_data = document.copy()  # Get the previous document data
        mongo_alert.db[collection_name].update_one({'UsageTypes._id': document_id}, {'$set': {f'UsageTypes.$.{field}': updated_data[field] for field in updated_data}})  # Update the document
        
        # Log the edit details
        log_edit(collection_name, document_id, previous_data, updated_data)
        
        return redirect(url_for('alert.collection', collection_name=collection_name))
    else:
        return render_template('edit.html', collection_name=collection_name, document=document)
