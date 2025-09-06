"""
Trainer daily report data provider services
"""

from datetime import date, datetime, time
from typing import Dict, List, Optional, Any
from uuid import UUID
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_
from k9.models.models import TrainingSession, Employee, Dog, Project, TrainingCategory
from app import db

from k9.utils.dates_ar import get_arabic_day_name
from k9.utils.trainer_daily_constants import CATEGORY_LABELS_AR


def get_trainer_daily(
    project_id: Optional[str], 
    date_filter: date, 
    trainer_id: Optional[str], 
    dog_id: Optional[str], 
    category: Optional[str], 
    user
) -> Dict[str, Any]:
    """
    Get trainer daily report data
    
    Args:
        project_id: Project UUID (required for PROJECT_MANAGER)
        date_filter: Date for the report
        trainer_id: Optional trainer filter
        dog_id: Optional dog filter  
        category: Optional category filter
        user: Current user for permissions
        
    Returns:
        Dictionary with sessions, summary, and KPIs
    """
    # Validate permissions and scope
    if user.role.value == "PROJECT_MANAGER":
        if not project_id:
            raise ValueError("Project ID is required for PROJECT_MANAGER")
        # TODO: Add check that project_id is in user.assigned_project_ids()
    
    # Build query for training sessions
    query = db.session.query(TrainingSession).options(
        joinedload(TrainingSession.trainer),
        joinedload(TrainingSession.dog), 
        joinedload(TrainingSession.project)
    )
    
    # Filter by date range (start of day to end of day)
    start_datetime = datetime.combine(date_filter, time.min)
    end_datetime = datetime.combine(date_filter, time.max)
    query = query.filter(
        and_(
            TrainingSession.session_date >= start_datetime,
            TrainingSession.session_date <= end_datetime
        )
    )
    
    # Apply filters
    if project_id:
        query = query.filter(TrainingSession.project_id == project_id)
    if trainer_id:
        query = query.filter(TrainingSession.trainer_id == trainer_id)  
    if dog_id:
        query = query.filter(TrainingSession.dog_id == dog_id)
    if category:
        query = query.filter(TrainingSession.category == TrainingCategory(category))
    
    # Execute query and order by time
    sessions = query.order_by(TrainingSession.session_date).all()
    
    # Build sessions list
    sessions_data = []
    for session in sessions:
        equipment_list = session.equipment_used if session.equipment_used else []
        equipment_str = ", ".join(equipment_list) if isinstance(equipment_list, list) else str(equipment_list)
        
        sessions_data.append({
            "time": session.session_date.strftime("%H:%M"),
            "trainer_name": session.trainer.name if session.trainer else "",
            "dog_name": session.dog.name if session.dog else "",
            "category_ar": CATEGORY_LABELS_AR.get(session.category.value, session.category.value),
            "subject": session.subject,
            "duration_min": session.duration,
            "success_rating": session.success_rating, 
            "location": session.location or "",
            "weather": session.weather_conditions or "",
            "equipment": equipment_str,
            "notes": session.notes or ""
        })
    
    # Build summary by dog
    dog_summary = {}
    for session in sessions:
        dog_name = session.dog.name if session.dog else "Unknown"
        if dog_name not in dog_summary:
            dog_summary[dog_name] = {
                "sessions_count": 0,
                "total_duration_min": 0,
                "ratings": [],
                "categories": {}
            }
        
        dog_summary[dog_name]["sessions_count"] += 1
        dog_summary[dog_name]["total_duration_min"] += session.duration
        dog_summary[dog_name]["ratings"].append(session.success_rating)
        
        category_ar = CATEGORY_LABELS_AR.get(session.category.value, session.category.value)
        dog_summary[dog_name]["categories"][category_ar] = dog_summary[dog_name]["categories"].get(category_ar, 0) + 1
    
    # Convert to final format
    summary_by_dog = []
    for dog_name, data in dog_summary.items():
        avg_rating = sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else 0
        
        # Ensure all categories are represented
        categories_breakdown = {}
        for category_en, category_ar in CATEGORY_LABELS_AR.items():
            categories_breakdown[category_ar] = data["categories"].get(category_ar, 0)
        
        summary_by_dog.append({
            "dog_name": dog_name,
            "sessions_count": data["sessions_count"],
            "total_duration_min": data["total_duration_min"],
            "avg_success_rating": round(avg_rating, 1),
            "categories_breakdown": categories_breakdown
        })
    
    # Calculate KPIs
    unique_dogs = len(set(session.dog_id for session in sessions))
    unique_trainers = len(set(session.trainer_id for session in sessions))
    total_duration = sum(session.duration for session in sessions)
    avg_rating = sum(session.success_rating for session in sessions) / len(sessions) if sessions else 0
    
    # Get project info for display
    project_name = ""
    if project_id:
        project = Project.query.get(project_id)
        project_name = project.name if project else f"Project {project_id}"
    
    return {
        "project_id": project_id,
        "date": date_filter.strftime("%Y-%m-%d"),
        "day_name_ar": get_arabic_day_name(date_filter),
        "project_name": project_name,
        "filters_applied": {
            "project_id": project_id,
            "date": date_filter.strftime("%Y-%m-%d"),
            "trainer_id": trainer_id,
            "dog_id": dog_id,
            "category": category
        },
        "sessions": sessions_data,
        "summary_by_dog": summary_by_dog,
        "kpis": {
            "total_sessions": len(sessions),
            "unique_dogs": unique_dogs,
            "unique_trainers": unique_trainers,
            "total_duration_min": total_duration,
            "avg_success_rating": round(avg_rating, 1)
        }
    }