"""
خدمة إدارة المهام والتكليفات
Task Management Service
"""
from app import db
from k9.models.models_handler_daily import Task, TaskStatus, TaskPriority, NotificationType
from k9.models.models import User
from k9.services.handler_service import NotificationService
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy import or_, and_


class TaskService:
    """خدمة إدارة المهام"""
    
    @staticmethod
    def create_task(
        title: str,
        assigned_to_user_id: str,
        created_by_user_id: str,
        description: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None,
        project_id: Optional[str] = None
    ) -> tuple:
        """إنشاء مهمة جديدة"""
        try:
            # Validate assigned user exists and is HANDLER
            assigned_user = User.query.get(assigned_to_user_id)
            if not assigned_user:
                return None, "المستخدم المحدد غير موجود"
            
            # Create task
            task = Task(
                title=title,
                description=description,
                priority=priority,
                status=TaskStatus.PENDING,
                assigned_to_user_id=assigned_to_user_id,
                created_by_user_id=created_by_user_id,
                due_date=due_date,
                project_id=project_id
            )
            
            db.session.add(task)
            db.session.commit()
            
            # Send notification to assigned handler
            creator = User.query.get(created_by_user_id)
            NotificationService.create_notification(
                user_id=assigned_to_user_id,
                notification_type=NotificationType.TASK_ASSIGNED,
                title=f"مهمة جديدة: {title}",
                message=f"تم تكليفك بمهمة جديدة من قبل {creator.full_name if creator else 'المشرف'}",
                related_id=str(task.id),
                related_type='Task'
            )
            
            return task, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"خطأ في إنشاء المهمة: {str(e)}"
    
    @staticmethod
    def update_task(
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        due_date: Optional[datetime] = None,
        status: Optional[TaskStatus] = None
    ) -> tuple:
        """تحديث مهمة"""
        try:
            task = Task.query.get(task_id)
            if not task:
                return None, "المهمة غير موجودة"
            
            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if priority is not None:
                task.priority = priority
            if due_date is not None:
                task.due_date = due_date
            if status is not None:
                old_status = task.status
                task.status = status
                
                # If status changed to COMPLETED, set completed_at
                if status == TaskStatus.COMPLETED and old_status != TaskStatus.COMPLETED:
                    task.completed_at = datetime.utcnow()
            
            db.session.commit()
            return task, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"خطأ في تحديث المهمة: {str(e)}"
    
    @staticmethod
    def complete_task(task_id: str, user_id: str) -> tuple:
        """إكمال مهمة"""
        try:
            task = Task.query.get(task_id)
            if not task:
                return None, "المهمة غير موجودة"
            
            # Check if user is assigned to this task
            if str(task.assigned_to_user_id) != str(user_id):
                return None, "غير مصرح لك بإكمال هذه المهمة"
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            # Notify task creator
            NotificationService.create_notification(
                user_id=str(task.created_by_user_id),
                notification_type=NotificationType.TASK_ASSIGNED,
                title=f"تم إكمال المهمة: {task.title}",
                message=f"تم إكمال المهمة من قبل {task.assigned_to.full_name}",
                related_id=str(task.id),
                related_type='Task'
            )
            
            return task, None
        
        except Exception as e:
            db.session.rollback()
            return None, f"خطأ في إكمال المهمة: {str(e)}"
    
    @staticmethod
    def delete_task(task_id: str) -> tuple:
        """حذف مهمة"""
        try:
            task = Task.query.get(task_id)
            if not task:
                return False, "المهمة غير موجودة"
            
            db.session.delete(task)
            db.session.commit()
            
            return True, None
        
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في حذف المهمة: {str(e)}"
    
    @staticmethod
    def get_task(task_id: str) -> Optional[Task]:
        """الحصول على مهمة"""
        return Task.query.get(task_id)
    
    @staticmethod
    def get_user_tasks(
        user_id: str,
        status: Optional[TaskStatus] = None,
        include_created: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """الحصول على مهام المستخدم"""
        try:
            # Build query
            if include_created:
                # Include tasks created by user (for admins/PMs)
                query = Task.query.filter(
                    or_(
                        Task.assigned_to_user_id == user_id,
                        Task.created_by_user_id == user_id
                    )
                )
            else:
                # Only tasks assigned to user (for handlers)
                query = Task.query.filter_by(assigned_to_user_id=user_id)
            
            # Filter by status if provided
            if status:
                query = query.filter_by(status=status)
            
            # Order by priority and due date
            query = query.order_by(
                Task.status.asc(),  # Pending first
                Task.priority.desc(),  # High priority first
                Task.due_date.asc()  # Earliest due date first
            )
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            tasks = query.limit(limit).offset(offset).all()
            
            return {
                'tasks': tasks,
                'total_count': total_count,
                'has_more': (offset + limit) < total_count
            }
        
        except Exception as e:
            return {
                'tasks': [],
                'total_count': 0,
                'has_more': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_project_tasks(
        project_id: str,
        status: Optional[TaskStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """الحصول على مهام المشروع"""
        try:
            query = Task.query.filter_by(project_id=project_id)
            
            if status:
                query = query.filter_by(status=status)
            
            query = query.order_by(Task.due_date.asc())
            
            total_count = query.count()
            tasks = query.limit(limit).offset(offset).all()
            
            return {
                'tasks': tasks,
                'total_count': total_count,
                'has_more': (offset + limit) < total_count
            }
        
        except Exception as e:
            return {
                'tasks': [],
                'total_count': 0,
                'has_more': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_task_statistics(user_id: str, include_created: bool = False) -> Dict:
        """إحصائيات المهام"""
        try:
            if include_created:
                base_query = Task.query.filter(
                    or_(
                        Task.assigned_to_user_id == user_id,
                        Task.created_by_user_id == user_id
                    )
                )
            else:
                base_query = Task.query.filter_by(assigned_to_user_id=user_id)
            
            total = base_query.count()
            pending = base_query.filter_by(status=TaskStatus.PENDING).count()
            in_progress = base_query.filter_by(status=TaskStatus.IN_PROGRESS).count()
            completed = base_query.filter_by(status=TaskStatus.COMPLETED).count()
            
            # Overdue tasks (pending/in_progress with due_date in past)
            overdue = base_query.filter(
                and_(
                    or_(
                        Task.status == TaskStatus.PENDING,
                        Task.status == TaskStatus.IN_PROGRESS
                    ),
                    Task.due_date < datetime.utcnow()
                )
            ).count()
            
            return {
                'total': total,
                'pending': pending,
                'in_progress': in_progress,
                'completed': completed,
                'overdue': overdue
            }
        
        except Exception as e:
            return {
                'total': 0,
                'pending': 0,
                'in_progress': 0,
                'completed': 0,
                'overdue': 0,
                'error': str(e)
            }
