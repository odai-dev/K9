"""
UI routes for trainer daily reports
"""

from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from k9.utils.permissions_new import admin_required, has_permission

bp = Blueprint('reports_training_trainer_daily_ui', __name__)


@bp.route('/trainer-daily')
@login_required
@admin_required
def trainer_daily():
    """
    Render trainer daily report page
    """
    if not has_permission("reports.training.trainer_daily.view"):
        return redirect("/unauthorized")
    
    # Get optional query parameters for prefilling
    project_id = request.args.get('project_id')
    date_param = request.args.get('date')
    trainer_id = request.args.get('trainer_id')
    dog_id = request.args.get('dog_id') 
    category = request.args.get('category')
    
    return render_template(
        'reports/training/trainer_daily.html',
        project_id=project_id,
        date=date_param,
        trainer_id=trainer_id,
        dog_id=dog_id,
        category=category
    )