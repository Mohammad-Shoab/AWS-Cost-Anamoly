from flask import Blueprint

alert_bp = Blueprint('alert', __name__, template_folder='templates')

from . import routes
