from flask import Blueprint

usage_bp = Blueprint('usage', __name__, template_folder='templates')

from . import routes
