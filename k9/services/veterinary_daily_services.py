"""
Veterinary daily report services
"""
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload

from k9.models.models import VeterinaryVisit, Dog, Employee, Project, EmployeeRole, VisitType
from app import db
from k9.utils.dates_ar import get_arabic_day_name
from k9.utils.utils_pdf_rtl import format_arabic_date
from k9.utils.veterinary_daily_constants import VISIT_TYPE_LABELS


def get_vet_daily(
    project_id: str,
    target_date: date,
    vet_id: Optional[str] = None,
    dog_id: Optional[str] = None,
    visit_type: Optional[str] = None,
    user=None
) -> Dict[str, Any]:
    """
    Get veterinary daily report data
    
    Args:
        project_id: Project ID to filter by
        target_date: Date for the report
        vet_id: Optional veterinarian ID filter
        dog_id: Optional dog ID filter
        visit_type: Optional visit type filter
        user: Current user for RBAC
        
    Returns:
        Dictionary containing report data
    """
    # Validate project access for PROJECT_MANAGER
    if user and user.role.value == "PROJECT_MANAGER":
        # Check if user has access to this project
        if not user.managed_projects or project_id not in [p.id for p in user.managed_projects]:
            raise ValueError("Access denied to this project")
    
    # Get project info
    project = Project.query.get(project_id)
    if not project:
        raise ValueError("Project not found")
    
    # Build query with joins for better performance
    query = VeterinaryVisit.query.join(
        VeterinaryVisit.dog
    ).join(
        VeterinaryVisit.vet
    ).join(
        VeterinaryVisit.project
    ).filter(
        and_(
            VeterinaryVisit.project_id == project_id,
            db.func.date(VeterinaryVisit.visit_date) == target_date
        )
    )
    
    # Apply filters
    if vet_id:
        query = query.filter(VeterinaryVisit.vet_id == vet_id)
    
    if dog_id:
        query = query.filter(VeterinaryVisit.dog_id == dog_id)
    
    if visit_type:
        query = query.filter(VeterinaryVisit.visit_type == VisitType(visit_type))
    
    # Execute query
    visits = query.order_by(VeterinaryVisit.visit_date.asc()).all()
    
    # Process visits data
    visits_data = []
    for visit in visits:
        # Format medications
        medications_str = ""
        if visit.medications:
            meds = []
            for med in visit.medications:
                name = med.get('name', '')
                dose = med.get('dose', '')
                frequency = med.get('frequency', '')
                if name:
                    med_str = f"{name}"
                    if dose:
                        med_str += f" ({dose}"
                        if frequency:
                            med_str += f"×{frequency}"
                        med_str += ")"
                    meds.append(med_str)
            medications_str = "؛ ".join(meds)
        
        # Format vital signs
        vital_signs_str = ""
        if visit.vital_signs:
            vs_parts = []
            temp = visit.vital_signs.get('temp') or visit.temperature
            hr = visit.vital_signs.get('hr') or visit.heart_rate
            resp = visit.vital_signs.get('resp')
            bp = visit.vital_signs.get('bp') or visit.blood_pressure
            
            if temp:
                vs_parts.append(f"الحرارة: {temp}°")
            if hr:
                vs_parts.append(f"النبض: {hr}")
            if resp:
                vs_parts.append(f"التنفس: {resp}")
            if bp:
                vs_parts.append(f"الضغط: {bp}")
                
            vital_signs_str = "، ".join(vs_parts)
        elif visit.temperature or visit.heart_rate or visit.blood_pressure:
            # Fallback to individual fields
            vs_parts = []
            if visit.temperature:
                vs_parts.append(f"الحرارة: {visit.temperature}°")
            if visit.heart_rate:
                vs_parts.append(f"النبض: {visit.heart_rate}")
            if visit.blood_pressure:
                vs_parts.append(f"الضغط: {visit.blood_pressure}")
            vital_signs_str = "، ".join(vs_parts)
        
        visits_data.append({
            "time": visit.visit_date.strftime("%H:%M"),
            "dog_name": visit.dog.name,
            "breed": visit.dog.breed or "",
            "vet_name": visit.vet.name,
            "visit_type_ar": VISIT_TYPE_LABELS.get(visit.visit_type.value, visit.visit_type.value),
            "diagnosis": visit.diagnosis or "",
            "treatment": visit.treatment or "",
            "medications": medications_str,
            "cost": visit.cost or 0.0,
            "location": visit.location or "",
            "weather": visit.weather or "",
            "vital_signs": vital_signs_str,
            "notes": visit.notes or ""
        })
    
    # Calculate KPIs
    total_visits = len(visits)
    unique_dogs = len(set(visit.dog_id for visit in visits))
    total_cost = sum(visit.cost or 0 for visit in visits)
    emergencies = len([v for v in visits if v.visit_type == VisitType.EMERGENCY])
    vaccinations = len([v for v in visits if v.visit_type == VisitType.VACCINATION])
    
    return {
        "project_id": project_id,
        "project_name": project.name,
        "date": target_date.strftime("%Y-%m-%d"),
        "date_ar": format_arabic_date(target_date),
        "day_name_ar": get_arabic_day_name(target_date),
        "filters_applied": {
            "project_id": project_id,
            "date": target_date.strftime("%Y-%m-%d"),
            "vet_id": vet_id,
            "dog_id": dog_id,
            "visit_type": visit_type
        },
        "visits": visits_data,
        "kpis": {
            "total_visits": total_visits,
            "unique_dogs": unique_dogs,
            "total_cost": round(total_cost, 2),
            "emergencies": emergencies,
            "vaccinations": vaccinations
        }
    }


def get_available_vets(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get list of available veterinarians"""
    query = Employee.query.filter(Employee.role == EmployeeRole.VET)
    
    if project_id:
        # Filter vets - simplified for now
        pass
    
    vets = query.all()
    return [{"id": vet.id, "name": vet.name} for vet in vets]


def get_available_dogs(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get list of available dogs"""
    query = Dog.query
    
    if project_id:
        # Filter dogs - simplified for now
        pass
    
    dogs = query.all()
    return [{"id": dog.id, "name": dog.name, "breed": dog.breed or ""} for dog in dogs]