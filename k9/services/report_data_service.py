"""
Unified Report Data Service
Single source of truth for fetching report data.
This ensures 100% parity between HTML preview and PDF export.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from flask import current_app
from flask_login import current_user

from app import db
from k9.services.report_registry import get_report_registry, ColumnDefinition

logger = logging.getLogger(__name__)


class ReportDataService:
    """
    Unified service for fetching and formatting report data.
    Ensures both preview and export use identical data.
    """
    
    def __init__(self):
        self.registry = get_report_registry()
    
    def fetch_report_data(
        self,
        report_type: str,
        filters: Dict[str, Any] = None,
        start_date: date = None,
        end_date: date = None,
        user = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch formatted report data for any report type.
        
        Args:
            report_type: Type of report to fetch
            filters: Dictionary of filter values
            start_date: Optional start date for date range
            end_date: Optional end date for date range
            user: User requesting the report (for permission scoping)
        
        Returns:
            List of formatted records ready for display/export
        """
        filters = filters or {}
        user = user or current_user
        
        # Get report definition
        report_def = self.registry.get_report(report_type)
        if not report_def:
            logger.warning(f"Unknown report type: {report_type}")
            return []
        
        # Fetch raw data based on report type
        fetcher_method = getattr(self, f'_fetch_{report_type}', None)
        if not fetcher_method:
            logger.warning(f"No fetcher method for report type: {report_type}")
            return []
        
        try:
            raw_data = fetcher_method(filters, start_date, end_date, user)
            
            # Format data according to column definitions
            formatted_data = self._format_records(raw_data, report_def.columns)
            
            return formatted_data
        except Exception as e:
            logger.error(f"Error fetching report data for {report_type}: {e}")
            return []
    
    def _format_records(
        self,
        raw_records: List[Dict[str, Any]],
        columns: List[ColumnDefinition]
    ) -> List[Dict[str, Any]]:
        """Format raw records according to column definitions"""
        formatted = []
        
        for idx, record in enumerate(raw_records, 1):
            formatted_record = {}
            for col in columns:
                if col.key == 'row_num':
                    formatted_record[col.header] = str(idx)
                else:
                    value = record.get(col.key, '')
                    formatted_record[col.header] = col.format_value(value)
            formatted.append(formatted_record)
        
        return formatted
    
    def _fetch_dogs(
        self,
        filters: Dict[str, Any],
        start_date: date,
        end_date: date,
        user
    ) -> List[Dict[str, Any]]:
        """Fetch dogs data with filters"""
        from k9.models.models import Dog, DogStatus, DogGender
        
        # Base query - scope based on user role
        if hasattr(user, 'role') and user.role.value == 'GENERAL_ADMIN':
            query = Dog.query
        else:
            query = Dog.query.filter_by(assigned_to_user_id=user.id)
        
        # Apply filters
        if filters.get('gender'):
            gender_values = filters['gender'] if isinstance(filters['gender'], list) else [filters['gender']]
            query = query.filter(Dog.gender.in_([DogGender[g] for g in gender_values if g in DogGender.__members__]))
        
        if filters.get('status'):
            status_values = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
            query = query.filter(Dog.current_status.in_([DogStatus[s] for s in status_values if s in DogStatus.__members__]))
        
        dogs = query.all()
        
        # Apply text filters in Python (more flexible)
        if filters.get('breed'):
            breed_filter = filters['breed'].lower()
            dogs = [d for d in dogs if breed_filter in (d.breed or '').lower()]
        
        if filters.get('keyword'):
            keyword = filters['keyword'].lower()
            dogs = [d for d in dogs if keyword in ' '.join([
                d.name or '', d.code or '', d.breed or '',
                d.location or '', d.microchip_id or '', d.notes or ''
            ]).lower()]
        
        # Gender translation
        gender_map = {'MALE': 'ذكر', 'FEMALE': 'أنثى'}
        # Status translation
        status_map = {'ACTIVE': 'نشط', 'RETIRED': 'متقاعد', 'DECEASED': 'متوفى', 'TRAINING': 'تدريب'}
        
        records = []
        for dog in dogs:
            age = ''
            if dog.birth_date:
                age_years = (datetime.now().date() - dog.birth_date).days // 365
                age = f'{age_years} سنة'
            
            records.append({
                'name': dog.name or '',
                'code': dog.code or '',
                'breed': dog.breed or '',
                'gender': gender_map.get(dog.gender.value, '') if dog.gender else '',
                'status': status_map.get(dog.current_status.value, '') if dog.current_status else '',
                'location': dog.location or '',
                'age': age
            })
        
        return records
    
    def _fetch_employees(
        self,
        filters: Dict[str, Any],
        start_date: date,
        end_date: date,
        user
    ) -> List[Dict[str, Any]]:
        """Fetch employees data with filters"""
        from k9.models.models import Employee, EmployeeRole
        
        query = Employee.query
        
        # Apply filters
        if filters.get('role'):
            role_values = filters['role'] if isinstance(filters['role'], list) else [filters['role']]
            query = query.filter(Employee.role.in_([EmployeeRole[r] for r in role_values if r in EmployeeRole.__members__]))
        
        if filters.get('status'):
            status_values = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
            is_active_list = ['ACTIVE' in status_values]
            if 'ACTIVE' in status_values and 'INACTIVE' not in status_values:
                query = query.filter(Employee.is_active == True)
            elif 'INACTIVE' in status_values and 'ACTIVE' not in status_values:
                query = query.filter(Employee.is_active == False)
        
        employees = query.all()
        
        # Apply date range filter
        if start_date:
            employees = [e for e in employees if e.hire_date and e.hire_date >= start_date]
        if end_date:
            employees = [e for e in employees if e.hire_date and e.hire_date <= end_date]
        
        # Role translation
        role_map = {
            'HANDLER': 'مدرب',
            'TRAINER': 'معالج',
            'VET': 'طبيب بيطري',
            'MANAGER': 'مدير',
            'ADMIN': 'إداري',
            'CARETAKER': 'راعي',
            'SECURITY': 'أمن'
        }
        
        records = []
        for emp in employees:
            records.append({
                'name': emp.name or '',
                'employee_id': emp.employee_id or '',
                'role': role_map.get(emp.role.value, emp.role.value) if emp.role else '',
                'phone': emp.phone or '',
                'status': 'نشط' if emp.is_active else 'غير نشط',
                'hire_date': emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else ''
            })
        
        return records
    
    def _fetch_training(
        self,
        filters: Dict[str, Any],
        start_date: date,
        end_date: date,
        user
    ) -> List[Dict[str, Any]]:
        """Fetch training sessions data with filters"""
        from k9.models.models import TrainingSession, TrainingCategory
        
        query = TrainingSession.query
        
        # Apply date range
        if start_date:
            query = query.filter(TrainingSession.session_date >= start_date)
        if end_date:
            query = query.filter(TrainingSession.session_date <= end_date)
        
        # Apply category filter
        if filters.get('category'):
            cat_values = filters['category'] if isinstance(filters['category'], list) else [filters['category']]
            query = query.filter(TrainingSession.category.in_([TrainingCategory[c] for c in cat_values if c in TrainingCategory.__members__]))
        
        sessions = query.order_by(TrainingSession.session_date.desc()).all()
        
        # Category translation
        category_map = {
            'OBEDIENCE': 'الطاعة',
            'DETECTION': 'الكشف',
            'PATROL': 'الدورية',
            'TRACKING': 'التتبع',
            'PROTECTION': 'الحماية',
            'AGILITY': 'الرشاقة',
            'SOCIALIZATION': 'التأهيل'
        }
        
        records = []
        for session in sessions:
            records.append({
                'dog_name': session.dog.name if session.dog else '',
                'trainer_name': session.trainer.name if session.trainer else '',
                'category': category_map.get(session.category.value, session.category.value) if session.category else '',
                'session_date': session.session_date.strftime('%Y-%m-%d') if session.session_date else '',
                'duration': str(session.duration_minutes) if session.duration_minutes else '',
                'rating': str(session.rating) if session.rating else '',
                'notes': session.notes or ''
            })
        
        return records
    
    def _fetch_veterinary(
        self,
        filters: Dict[str, Any],
        start_date: date,
        end_date: date,
        user
    ) -> List[Dict[str, Any]]:
        """Fetch veterinary visits data with filters"""
        from k9.models.models import VeterinaryVisit, VisitType
        
        query = VeterinaryVisit.query
        
        # Apply date range
        if start_date:
            query = query.filter(VeterinaryVisit.visit_date >= start_date)
        if end_date:
            query = query.filter(VeterinaryVisit.visit_date <= end_date)
        
        # Apply visit type filter
        if filters.get('visit_type'):
            type_values = filters['visit_type'] if isinstance(filters['visit_type'], list) else [filters['visit_type']]
            query = query.filter(VeterinaryVisit.visit_type.in_([VisitType[t] for t in type_values if t in VisitType.__members__]))
        
        visits = query.order_by(VeterinaryVisit.visit_date.desc()).all()
        
        # Visit type translation
        type_map = {
            'ROUTINE': 'روتينية',
            'EMERGENCY': 'طارئة',
            'VACCINATION': 'تطعيم',
            'SURGERY': 'جراحة',
            'CHECKUP': 'فحص',
            'FOLLOW_UP': 'متابعة'
        }
        
        records = []
        for visit in visits:
            records.append({
                'dog_name': visit.dog.name if visit.dog else '',
                'visit_type': type_map.get(visit.visit_type.value, visit.visit_type.value) if visit.visit_type else '',
                'visit_date': visit.visit_date.strftime('%Y-%m-%d') if visit.visit_date else '',
                'diagnosis': visit.diagnosis or '',
                'treatment': visit.treatment or '',
                'vet_name': visit.vet.name if visit.vet else ''
            })
        
        return records
    
    def _fetch_breeding(
        self,
        filters: Dict[str, Any],
        start_date: date,
        end_date: date,
        user
    ) -> List[Dict[str, Any]]:
        """Fetch breeding/production data with filters"""
        from k9.models.models import ProductionCycle, ProductionCycleType, ProductionResult
        
        query = ProductionCycle.query
        
        # Apply date range
        if start_date:
            query = query.filter(ProductionCycle.start_date >= start_date)
        if end_date:
            query = query.filter(ProductionCycle.start_date <= end_date)
        
        # Apply cycle type filter
        if filters.get('cycle_type'):
            type_values = filters['cycle_type'] if isinstance(filters['cycle_type'], list) else [filters['cycle_type']]
            query = query.filter(ProductionCycle.cycle_type.in_([ProductionCycleType[t] for t in type_values if t in ProductionCycleType.__members__]))
        
        cycles = query.order_by(ProductionCycle.start_date.desc()).all()
        
        # Cycle type translation
        type_map = {
            'MATING': 'تزاوج',
            'PREGNANCY': 'حمل',
            'DELIVERY': 'ولادة',
            'WEANING': 'فطام',
            'HEAT': 'حرارة'
        }
        
        # Result translation
        result_map = {
            'SUCCESS': 'نجاح',
            'FAILED': 'فشل',
            'PENDING': 'قيد الانتظار',
            'CANCELLED': 'ملغى'
        }
        
        records = []
        for cycle in cycles:
            records.append({
                'dog_name': cycle.dog.name if cycle.dog else '',
                'cycle_type': type_map.get(cycle.cycle_type.value, cycle.cycle_type.value) if cycle.cycle_type else '',
                'start_date': cycle.start_date.strftime('%Y-%m-%d') if cycle.start_date else '',
                'end_date': cycle.end_date.strftime('%Y-%m-%d') if cycle.end_date else '',
                'result': result_map.get(cycle.result.value, cycle.result.value) if cycle.result else '',
                'puppies_count': str(cycle.puppies_count) if cycle.puppies_count else '0',
                'notes': cycle.notes or ''
            })
        
        return records
    
    def _fetch_projects(
        self,
        filters: Dict[str, Any],
        start_date: date,
        end_date: date,
        user
    ) -> List[Dict[str, Any]]:
        """Fetch projects data with filters"""
        from k9.models.models import Project, ProjectStatus
        
        query = Project.query
        
        # Apply status filter
        if filters.get('status'):
            status_values = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
            query = query.filter(Project.status.in_([ProjectStatus[s] for s in status_values if s in ProjectStatus.__members__]))
        
        # Apply date range
        if start_date:
            query = query.filter(Project.start_date >= start_date)
        if end_date:
            query = query.filter(Project.start_date <= end_date)
        
        projects = query.order_by(Project.start_date.desc()).all()
        
        # Status translation
        status_map = {
            'ACTIVE': 'نشط',
            'COMPLETED': 'مكتمل',
            'SUSPENDED': 'معلق',
            'CANCELLED': 'ملغى',
            'PLANNING': 'تخطيط'
        }
        
        records = []
        for project in projects:
            # Count dogs and employees
            dogs_count = len(project.dogs) if hasattr(project, 'dogs') else 0
            employees_count = len(project.employees) if hasattr(project, 'employees') else 0
            
            records.append({
                'name': project.name or '',
                'code': project.code or '',
                'status': status_map.get(project.status.value, project.status.value) if project.status else '',
                'start_date': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
                'manager': project.manager.name if project.manager else '',
                'dogs_count': str(dogs_count),
                'employees_count': str(employees_count)
            })
        
        return records
    
    def get_report_metadata(self, report_type: str) -> Dict[str, Any]:
        """Get metadata for a report type"""
        report_def = self.registry.get_report(report_type)
        if not report_def:
            return {}
        
        return {
            'type': report_type,
            'title_ar': report_def.title_ar,
            'title_en': report_def.title_en,
            'icon': report_def.icon,
            'color': report_def.color,
            'description_ar': report_def.description_ar,
            'description_en': report_def.description_en,
            'columns': [{'key': c.key, 'header': c.header} for c in report_def.columns],
            'filters': [
                {
                    'key': f.key,
                    'label': f.label,
                    'type': f.filter_type.value,
                    'options': f.options
                } for f in report_def.filters
            ]
        }


def get_report_data_service() -> ReportDataService:
    """Get a ReportDataService instance"""
    return ReportDataService()
