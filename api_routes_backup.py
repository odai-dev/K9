from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
from models import (
    db, Project, Employee, Dog
)
from utils import get_user_permissions
import uuid

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Keep this file minimal for now - only non-attendance related API endpoints would go here
# All attendance-related endpoints have been removed as requested

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'API is running'})