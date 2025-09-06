"""
JSON API endpoints for trainer daily reports
"""

import os
from datetime import datetime, date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from k9.utils.permission_decorators import admin_required
from k9.services.trainer_daily_services import get_trainer_daily
from k9.utils.trainer_daily_exporters import export_trainer_daily_pdf

bp = Blueprint('reports_training_trainer_daily_api', __name__)


@bp.route('/run/trainer-daily', methods=['POST'])
@login_required
@admin_required
def run_trainer_daily():
    """
    Run trainer daily report and return JSON data
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        # Validate required date
        date_str = data.get('date')
        if not date_str:
            return jsonify({"error": "Date is required"}), 400
            
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Extract filters
        project_id = data.get('project_id')
        trainer_id = data.get('trainer_id')
        dog_id = data.get('dog_id')
        category = data.get('category')
        
        # Validate PROJECT_MANAGER has project_id
        if current_user.role.value == "PROJECT_MANAGER" and not project_id:
            return jsonify({"error": "Project ID is required for PROJECT_MANAGER"}), 400
        
        # Get report data
        result = get_trainer_daily(
            project_id=project_id,
            date_filter=report_date,
            trainer_id=trainer_id,
            dog_id=dog_id,
            category=category,
            user=current_user
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@bp.route('/export/pdf/trainer-daily', methods=['POST'])
@login_required
@admin_required
def export_pdf_trainer_daily():
    """
    Export trainer daily report as PDF
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        # Validate required date
        date_str = data.get('date')
        if not date_str:
            return jsonify({"error": "Date is required"}), 400
            
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Extract filters
        project_id = data.get('project_id')
        trainer_id = data.get('trainer_id')
        dog_id = data.get('dog_id')
        category = data.get('category')
        
        # Validate PROJECT_MANAGER has project_id
        if current_user.role.value == "PROJECT_MANAGER" and not project_id:
            return jsonify({"error": "Project ID is required for PROJECT_MANAGER"}), 400
        
        # Get report data first
        report_data = get_trainer_daily(
            project_id=project_id,
            date_filter=report_date,
            trainer_id=trainer_id,
            dog_id=dog_id,
            category=category,
            user=current_user
        )
        
        # Generate PDF
        pdf_path = export_trainer_daily_pdf(report_data)
        
        return jsonify({"path": pdf_path})
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500