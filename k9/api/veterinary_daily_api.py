"""
Veterinary daily report API endpoints
"""
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, date
import os

from k9.utils.permission_decorators import admin_required
from k9.services.veterinary_daily_services import get_vet_daily, get_available_vets, get_available_dogs
from k9.utils.veterinary_daily_exporters import export_vet_daily_pdf

bp = Blueprint('veterinary_daily_api', __name__)


@bp.route('/run/daily', methods=['POST'])
@login_required
@admin_required
def run_daily_report():
    """
    Generate veterinary daily report data
    """
        
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'project_id' not in data or 'date' not in data:
            return jsonify({"error": "project_id and date are required"}), 400
        
        project_id = data['project_id']
        date_str = data['date']
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Extract optional filters
        vet_id = data.get('vet_id')
        dog_id = data.get('dog_id') 
        visit_type = data.get('visit_type')
        
        # Get report data
        report_data = get_vet_daily(
            project_id=project_id,
            target_date=target_date,
            vet_id=vet_id,
            dog_id=dog_id,
            visit_type=visit_type,
            user=current_user
        )
        
        return jsonify(report_data)
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500


@bp.route('/export/pdf/daily', methods=['POST'])
@login_required
def export_daily_pdf():
    """
    Export veterinary daily report as PDF
    """
    # Check permission
    if not has_permission(current_user, "reports:veterinary:daily:export"):
        return jsonify({"error": "Access denied"}), 403
        
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'project_id' not in data or 'date' not in data:
            return jsonify({"error": "project_id and date are required"}), 400
        
        project_id = data['project_id']
        date_str = data['date']
        
        # Parse date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Extract optional filters
        vet_id = data.get('vet_id')
        dog_id = data.get('dog_id')
        visit_type = data.get('visit_type')
        
        # Get report data
        report_data = get_vet_daily(
            project_id=project_id,
            target_date=target_date,
            vet_id=vet_id,
            dog_id=dog_id,
            visit_type=visit_type,
            user=current_user
        )
        
        # Generate PDF
        pdf_result = export_vet_daily_pdf(report_data)
        
        # Return file
        if os.path.exists(pdf_result['path']):
            return send_file(
                pdf_result['path'],
                as_attachment=True,
                download_name=pdf_result['filename'],
                mimetype='application/pdf'
            )
        else:
            return jsonify({"error": "Failed to generate PDF file"}), 500
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        return jsonify({"error": f"Failed to export PDF: {str(e)}"}), 500


@bp.route('/data/vets', methods=['GET'])
@login_required
@admin_required
def get_vets():
    """Get available veterinarians"""
        
    try:
        project_id = request.args.get('project_id')
        vets = get_available_vets(project_id)
        return jsonify(vets)
    except Exception as e:
        return jsonify({"error": f"Failed to get vets: {str(e)}"}), 500


@bp.route('/data/dogs', methods=['GET'])
@login_required
@admin_required
def get_dogs():
    """Get available dogs"""
        
    try:
        project_id = request.args.get('project_id')
        dogs = get_available_dogs(project_id)
        return jsonify(dogs)
    except Exception as e:
        return jsonify({"error": f"Failed to get dogs: {str(e)}"}), 500