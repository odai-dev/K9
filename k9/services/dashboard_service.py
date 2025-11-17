"""
Dashboard Statistics Service
Provides analytics and chart data for PM and Admin dashboards
"""
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
from k9.models.models import (
    Dog, DogStatus, Employee, EmployeeRole, Project, ProjectStatus,
    User, UserRole, TrainingSession, VeterinaryVisit
)
from k9.models.models_handler_daily import (
    HandlerReport, ReportStatus, DailySchedule, DailyScheduleItem,
    ScheduleItemStatus, ShiftReport
)
from typing import Dict, List, Optional
import calendar


class DashboardService:
    """Service for generating dashboard statistics and chart data"""
    
    @staticmethod
    def get_active_dogs_by_project() -> Dict:
        """Get count of active dogs grouped by project"""
        from k9.models.models import ProjectAssignment
        
        # Query active dog assignments grouped by project
        results = db.session.query(
            Project.name,
            Project.code,
            func.count(ProjectAssignment.id).label('count')
        ).join(
            ProjectAssignment,
            Project.id == ProjectAssignment.project_id
        ).filter(
            and_(
                ProjectAssignment.dog_id.isnot(None),
                ProjectAssignment.is_active == True
            )
        ).group_by(
            Project.id,
            Project.name,
            Project.code
        ).all()
        
        labels = [f"{r.name} ({r.code})" for r in results]
        data = [r.count for r in results]
        
        return {
            'labels': labels,
            'data': data,
            'total': sum(data)
        }
    
    @staticmethod
    def get_dogs_by_status() -> Dict:
        """Get count of dogs grouped by status"""
        results = db.session.query(
            Dog.current_status,
            func.count(Dog.id).label('count')
        ).group_by(
            Dog.current_status
        ).all()
        
        status_labels = {
            DogStatus.ACTIVE: 'نشط',
            DogStatus.TRAINING: 'في التدريب',
            DogStatus.RETIRED: 'متقاعد',
            DogStatus.DECEASED: 'متوفى'
        }
        
        labels = [status_labels.get(r.current_status, str(r.current_status)) for r in results]
        data = [r.count for r in results]
        
        return {
            'labels': labels,
            'data': data,
            'total': sum(data)
        }
    
    @staticmethod
    def get_handler_report_status_distribution(project_id: Optional[str] = None) -> Dict:
        """Get distribution of handler reports by status"""
        query = db.session.query(
            HandlerReport.status,
            func.count(HandlerReport.id).label('count')
        )
        
        if project_id:
            query = query.filter(HandlerReport.project_id == project_id)
        
        results = query.group_by(HandlerReport.status).all()
        
        status_labels = {
            ReportStatus.DRAFT: 'مسودة',
            ReportStatus.SUBMITTED: 'مقدم',
            ReportStatus.APPROVED: 'موافق عليه',
            ReportStatus.APPROVED_BY_PM: 'معتمد من PM',
            ReportStatus.FORWARDED_TO_ADMIN: 'محول للإدارة',
            ReportStatus.REJECTED: 'مرفوض',
            ReportStatus.REJECTED_BY_PM: 'مرفوض من PM',
            ReportStatus.APPROVED_BY_ADMIN: 'معتمد من الإدارة',
            ReportStatus.REJECTED_BY_ADMIN: 'مرفوض من الإدارة'
        }
        
        labels = [status_labels.get(r.status, str(r.status)) for r in results]
        data = [r.count for r in results]
        
        return {
            'labels': labels,
            'data': data,
            'total': sum(data)
        }
    
    @staticmethod
    def get_attendance_trends(project_id: Optional[str] = None, days: int = 30) -> Dict:
        """Get attendance trends over time (present/absent/replaced)"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = db.session.query(
            DailySchedule.date,
            DailyScheduleItem.status,
            func.count(DailyScheduleItem.id).label('count')
        ).join(
            DailyScheduleItem,
            DailySchedule.id == DailyScheduleItem.daily_schedule_id
        ).filter(
            DailySchedule.date.between(start_date, end_date)
        )
        
        if project_id:
            query = query.filter(DailySchedule.project_id == project_id)
        
        results = query.group_by(
            DailySchedule.date,
            DailyScheduleItem.status
        ).order_by(
            DailySchedule.date
        ).all()
        
        # Organize data by date
        dates_dict = {}
        for r in results:
            date_str = r.date.strftime('%Y-%m-%d')
            if date_str not in dates_dict:
                dates_dict[date_str] = {
                    'present': 0,
                    'absent': 0,
                    'replaced': 0
                }
            
            if r.status == ScheduleItemStatus.PRESENT:
                dates_dict[date_str]['present'] = r.count
            elif r.status == ScheduleItemStatus.ABSENT:
                dates_dict[date_str]['absent'] = r.count
            elif r.status == ScheduleItemStatus.REPLACED:
                dates_dict[date_str]['replaced'] = r.count
        
        # Fill in missing dates
        all_dates = []
        current = start_date
        while current <= end_date:
            all_dates.append(current)
            current += timedelta(days=1)
        
        labels = []
        present_data = []
        absent_data = []
        replaced_data = []
        
        for d in all_dates:
            date_str = d.strftime('%Y-%m-%d')
            labels.append(d.strftime('%m/%d'))
            
            if date_str in dates_dict:
                present_data.append(dates_dict[date_str]['present'])
                absent_data.append(dates_dict[date_str]['absent'])
                replaced_data.append(dates_dict[date_str]['replaced'])
            else:
                present_data.append(0)
                absent_data.append(0)
                replaced_data.append(0)
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'حاضر',
                    'data': present_data,
                    'borderColor': '#10b981',
                    'backgroundColor': '#10b98133'
                },
                {
                    'label': 'غائب',
                    'data': absent_data,
                    'borderColor': '#ef4444',
                    'backgroundColor': '#ef444433'
                },
                {
                    'label': 'مستبدل',
                    'data': replaced_data,
                    'borderColor': '#f59e0b',
                    'backgroundColor': '#f59e0b33'
                }
            ]
        }
    
    @staticmethod
    def get_dogs_worked_per_handler(project_id: Optional[str] = None, limit: int = 10) -> Dict:
        """Get number of dogs worked by each handler"""
        query = db.session.query(
            User.full_name,
            func.count(func.distinct(DailyScheduleItem.dog_id)).label('dog_count')
        ).join(
            DailyScheduleItem,
            User.id == DailyScheduleItem.handler_user_id
        ).join(
            DailySchedule,
            DailyScheduleItem.daily_schedule_id == DailySchedule.id
        ).filter(
            DailyScheduleItem.dog_id.isnot(None)
        )
        
        if project_id:
            query = query.filter(DailySchedule.project_id == project_id)
        
        results = query.group_by(
            User.id,
            User.full_name
        ).order_by(
            func.count(func.distinct(DailyScheduleItem.dog_id)).desc()
        ).limit(limit).all()
        
        labels = [r.full_name for r in results]
        data = [r.dog_count for r in results]
        
        return {
            'labels': labels,
            'data': data
        }
    
    @staticmethod
    def get_monthly_report_trends(project_id: Optional[str] = None, months: int = 6) -> Dict:
        """Get monthly report submission trends"""
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        query = db.session.query(
            func.date_trunc('month', HandlerReport.submitted_at).label('month'),
            func.count(HandlerReport.id).label('count')
        ).filter(
            and_(
                HandlerReport.submitted_at.isnot(None),
                HandlerReport.submitted_at >= start_date
            )
        )
        
        if project_id:
            query = query.filter(HandlerReport.project_id == project_id)
        
        results = query.group_by('month').order_by('month').all()
        
        # Format labels in Arabic
        month_names = [
            'يناير', 'فبراير', 'مارس', 'إبريل', 'مايو', 'يونيو',
            'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
        ]
        
        labels = []
        data = []
        
        for r in results:
            if r.month:
                month_num = r.month.month
                year = r.month.year
                labels.append(f"{month_names[month_num - 1]} {year}")
                data.append(r.count)
        
        return {
            'labels': labels,
            'data': data
        }
    
    @staticmethod
    def get_employee_distribution_by_role() -> Dict:
        """Get count of employees grouped by role"""
        results = db.session.query(
            Employee.role,
            func.count(Employee.id).label('count')
        ).filter(
            Employee.is_active == True
        ).group_by(
            Employee.role
        ).all()
        
        role_labels = {
            EmployeeRole.HANDLER: 'سائس',
            EmployeeRole.TRAINER: 'مدرب',
            EmployeeRole.BREEDER: 'مربي',
            EmployeeRole.VET: 'طبيب بيطري',
            EmployeeRole.PROJECT_MANAGER: 'مدير مشروع'
        }
        
        labels = [role_labels.get(r.role, str(r.role)) for r in results]
        data = [r.count for r in results]
        
        return {
            'labels': labels,
            'data': data,
            'total': sum(data)
        }
    
    @staticmethod
    def get_project_status_overview() -> Dict:
        """Get count of projects grouped by status"""
        results = db.session.query(
            Project.status,
            func.count(Project.id).label('count')
        ).group_by(
            Project.status
        ).all()
        
        status_labels = {
            ProjectStatus.PLANNED: 'مخطط',
            ProjectStatus.ACTIVE: 'نشط',
            ProjectStatus.COMPLETED: 'مكتمل',
            ProjectStatus.CANCELLED: 'ملغي'
        }
        
        labels = [status_labels.get(r.status, str(r.status)) for r in results]
        data = [r.count for r in results]
        
        return {
            'labels': labels,
            'data': data,
            'total': sum(data)
        }
    
    @staticmethod
    def get_training_activity_stats(project_id: Optional[str] = None, days: int = 30) -> Dict:
        """Get training session statistics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = db.session.query(
            func.count(TrainingSession.id).label('total_sessions'),
            func.count(func.distinct(TrainingSession.dog_id)).label('unique_dogs')
        ).filter(
            TrainingSession.created_at >= start_date
        )
        
        if project_id:
            query = query.filter(TrainingSession.project_id == project_id)
        
        result = query.first()
        
        return {
            'total_sessions': result.total_sessions if result else 0,
            'unique_dogs': result.unique_dogs if result else 0
        }
    
    @staticmethod
    def get_veterinary_visit_stats(project_id: Optional[str] = None, days: int = 30) -> Dict:
        """Get veterinary visit statistics"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        query = db.session.query(
            func.count(VeterinaryVisit.id).label('total_visits'),
            func.count(func.distinct(VeterinaryVisit.dog_id)).label('unique_dogs')
        ).filter(
            VeterinaryVisit.created_at >= start_date
        )
        
        if project_id:
            query = query.filter(VeterinaryVisit.project_id == project_id)
        
        result = query.first()
        
        return {
            'total_visits': result.total_visits if result else 0,
            'unique_dogs': result.unique_dogs if result else 0
        }
    
    @staticmethod
    def get_pm_dashboard_data(project_id: str) -> Dict:
        """Get comprehensive dashboard data for Project Manager"""
        return {
            'report_status': DashboardService.get_handler_report_status_distribution(project_id),
            'attendance_trends': DashboardService.get_attendance_trends(project_id, days=30),
            'handler_activity': DashboardService.get_dogs_worked_per_handler(project_id, limit=10),
            'monthly_trends': DashboardService.get_monthly_report_trends(project_id, months=6),
            'training_stats': DashboardService.get_training_activity_stats(project_id, days=30),
            'veterinary_stats': DashboardService.get_veterinary_visit_stats(project_id, days=30)
        }
    
    @staticmethod
    def get_admin_dashboard_data() -> Dict:
        """Get comprehensive dashboard data for General Admin"""
        return {
            'dogs_by_project': DashboardService.get_active_dogs_by_project(),
            'dogs_by_status': DashboardService.get_dogs_by_status(),
            'employee_by_role': DashboardService.get_employee_distribution_by_role(),
            'project_status': DashboardService.get_project_status_overview(),
            'system_reports': DashboardService.get_handler_report_status_distribution(),
            'system_attendance': DashboardService.get_attendance_trends(days=30),
            'training_stats': DashboardService.get_training_activity_stats(days=30),
            'veterinary_stats': DashboardService.get_veterinary_visit_stats(days=30)
        }
