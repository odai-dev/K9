"""
PM Report Review Service
Handles review workflow for all report types (Handler, Trainer, Vet, Caretaker)
"""
from app import db
from k9.models.models import User, Project, VeterinaryVisit, BreedingTrainingActivity, CaretakerDailyLog, ProjectManagerPermission
from k9.models.models_handler_daily import HandlerReport, Notification, ReportReview, NotificationType
from k9.models.models import UserRole
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import desc


class ReportReviewService:
    """Service for PM report review workflow"""
    
    # Report type to model mapping
    REPORT_TYPE_MODELS = {
        'HANDLER': HandlerReport,
        'TRAINER': BreedingTrainingActivity,
        'VET': VeterinaryVisit,
        'CARETAKER': CaretakerDailyLog
    }
    
    # Report type to display names (Arabic)
    REPORT_TYPE_NAMES = {
        'HANDLER': 'تقرير السائس اليومي',
        'TRAINER': 'تقرير التدريب',
        'VET': 'تقرير الطبيب البيطري',
        'CARETAKER': 'تقرير المربي اليومي'
    }
    
    @staticmethod
    def _get_submitter_id(report, report_type: str) -> str:
        """Get the submitter user ID from a report"""
        if report_type == 'HANDLER':
            return str(report.handler_user_id)
        else:
            # TRAINER, VET, CARETAKER all use created_by_user_id
            return str(report.created_by_user_id) if report.created_by_user_id else None
    
    @staticmethod
    def get_pm_project(user_id: str) -> Optional[Project]:
        """Get the ONE project assigned to a PM via ProjectManagerPermission"""
        user = User.query.get(user_id)
        if not user or user.role != UserRole.PROJECT_MANAGER:
            return None
        
        # PM project assignment is managed through ProjectManagerPermission
        # Get the first project the PM has permission for
        permission = ProjectManagerPermission.query.filter_by(user_id=user_id).first()
        
        if not permission:
            return None
        
        return permission.project
    
    @staticmethod
    def get_pending_reports(pm_user_id: str) -> Dict[str, List]:
        """Get all pending reports (status='SUBMITTED') for PM's project"""
        project = ReportReviewService.get_pm_project(pm_user_id)
        if not project:
            return {
                'HANDLER': [],
                'TRAINER': [],
                'VET': [],
                'CARETAKER': []
            }
        
        result = {}
        project_id = str(project.id)
        
        # Get HANDLER reports
        handler_reports = HandlerReport.query.filter_by(
            project_id=project_id,
            status='SUBMITTED'
        ).order_by(desc(HandlerReport.submitted_at)).all()
        result['HANDLER'] = [report for report in handler_reports]
        
        # Get TRAINER reports
        trainer_reports = BreedingTrainingActivity.query.filter_by(
            project_id=project_id,
            status='SUBMITTED'
        ).order_by(desc(BreedingTrainingActivity.submitted_at)).all()
        result['TRAINER'] = [report for report in trainer_reports]
        
        # Get VET reports
        vet_reports = VeterinaryVisit.query.filter_by(
            project_id=project_id,
            status='SUBMITTED'
        ).order_by(desc(VeterinaryVisit.submitted_at)).all()
        result['VET'] = [report for report in vet_reports]
        
        # Get CARETAKER reports
        caretaker_reports = CaretakerDailyLog.query.filter_by(
            project_id=project_id,
            status='SUBMITTED'
        ).order_by(desc(CaretakerDailyLog.submitted_at)).all()
        result['CARETAKER'] = [report for report in caretaker_reports]
        
        return result
    
    @staticmethod
    def get_pending_counts(pm_user_id: str) -> Dict[str, int]:
        """Get count of pending reports by type + TOTAL"""
        project = ReportReviewService.get_pm_project(pm_user_id)
        if not project:
            return {
                'HANDLER': 0,
                'TRAINER': 0,
                'VET': 0,
                'CARETAKER': 0,
                'TOTAL': 0
            }
        
        project_id = str(project.id)
        
        counts = {
            'HANDLER': HandlerReport.query.filter_by(project_id=project_id, status='SUBMITTED').count(),
            'TRAINER': BreedingTrainingActivity.query.filter_by(project_id=project_id, status='SUBMITTED').count(),
            'VET': VeterinaryVisit.query.filter_by(project_id=project_id, status='SUBMITTED').count(),
            'CARETAKER': CaretakerDailyLog.query.filter_by(project_id=project_id, status='SUBMITTED').count()
        }
        counts['TOTAL'] = sum(counts.values())
        
        return counts
    
    @staticmethod
    def get_report(report_type: str, report_id: str, pm_user_id: str) -> Optional[object]:
        """Fetch specific report with access check"""
        if report_type not in ReportReviewService.REPORT_TYPE_MODELS:
            return None
        
        project = ReportReviewService.get_pm_project(pm_user_id)
        if not project:
            return None
        
        Model = ReportReviewService.REPORT_TYPE_MODELS[report_type]
        report = Model.query.get(report_id)
        
        if not report:
            return None
        
        # Verify report belongs to PM's project
        if str(report.project_id) != str(project.id):
            return None
        
        return report
    
    @staticmethod
    def approve_and_forward(
        report_type: str,
        report_id: str,
        pm_user_id: str,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Approve report and forward to General Admin
        SUBMITTED → FORWARDED_TO_ADMIN
        """
        report = ReportReviewService.get_report(report_type, report_id, pm_user_id)
        
        if not report:
            return False, "تعذر العثور على التقرير أو ليس لديك صلاحية الوصول"
        
        if report.status != 'SUBMITTED':
            return False, f"التقرير في حالة {report.status} ولا يمكن اعتماده"
        
        # Prevent PM from reviewing their own reports
        submitter_id = ReportReviewService._get_submitter_id(report, report_type)
        if submitter_id and submitter_id == pm_user_id:
            return False, "لا يمكنك مراجعة تقريرك الخاص"
        
        try:
            # Update report status
            previous_status = report.status
            report.status = 'FORWARDED_TO_ADMIN'
            report.reviewed_by_user_id = pm_user_id
            report.reviewed_at = datetime.utcnow()
            if notes:
                report.review_notes = notes
            
            # Create audit log
            audit = ReportReview(
                report_type=report_type,
                report_id=str(report_id),
                action='APPROVE_AND_FORWARD',
                previous_status=previous_status,
                new_status='FORWARDED_TO_ADMIN',
                reviewed_by_user_id=pm_user_id,
                review_notes=notes,
                project_id=report.project_id
            )
            db.session.add(audit)
            
            # Notify all active General Admins
            ReportReviewService._notify_admin(
                report_type,
                report_id,
                pm_user_id,
                report.project_id
            )
            
            db.session.commit()
            return True, "تم اعتماد التقرير وإرساله للمسؤول العام بنجاح"
            
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في اعتماد التقرير: {str(e)}"
    
    @staticmethod
    def request_edits(
        report_type: str,
        report_id: str,
        pm_user_id: str,
        notes: str
    ) -> Tuple[bool, str]:
        """
        Request edits from submitter
        SUBMITTED → DRAFT (with notification)
        """
        if not notes or not notes.strip():
            return False, "يجب إدخال ملاحظات عند طلب التعديل"
        
        report = ReportReviewService.get_report(report_type, report_id, pm_user_id)
        
        if not report:
            return False, "تعذر العثور على التقرير أو ليس لديك صلاحية الوصول"
        
        if report.status != 'SUBMITTED':
            return False, f"التقرير في حالة {report.status} ولا يمكن طلب تعديله"
        
        # Prevent PM from reviewing their own reports
        submitter_id = ReportReviewService._get_submitter_id(report, report_type)
        if submitter_id and submitter_id == pm_user_id:
            return False, "لا يمكنك مراجعة تقريرك الخاص"
        
        try:
            # Update report status
            previous_status = report.status
            report.status = 'DRAFT'
            report.reviewed_by_user_id = pm_user_id
            report.reviewed_at = datetime.utcnow()
            report.review_notes = notes
            
            # Create audit log
            audit = ReportReview(
                report_type=report_type,
                report_id=str(report_id),
                action='REQUEST_EDITS',
                previous_status=previous_status,
                new_status='DRAFT',
                reviewed_by_user_id=pm_user_id,
                review_notes=notes,
                project_id=report.project_id
            )
            db.session.add(audit)
            
            # Notify submitter immediately
            if submitter_id:
                report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
                ReportReviewService._notify_submitter(
                    submitter_id,
                    report_type,
                    report_id,
                    pm_user_id,
                    f"طلب تعديل على {report_name}: {notes}",
                    'REQUEST_EDITS',
                    report.project_id
                )
            
            db.session.commit()
            return True, "تم إرسال طلب التعديل بنجاح"
            
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في طلب التعديل: {str(e)}"
    
    @staticmethod
    def reject_completely(
        report_type: str,
        report_id: str,
        pm_user_id: str,
        reason: str
    ) -> Tuple[bool, str]:
        """
        Reject report completely (final rejection)
        SUBMITTED → REJECTED_BY_PM
        """
        if not reason or not reason.strip():
            return False, "يجب إدخال سبب الرفض"
        
        report = ReportReviewService.get_report(report_type, report_id, pm_user_id)
        
        if not report:
            return False, "تعذر العثور على التقرير أو ليس لديك صلاحية الوصول"
        
        if report.status != 'SUBMITTED':
            return False, f"التقرير في حالة {report.status} ولا يمكن رفضه"
        
        # Prevent PM from reviewing their own reports
        submitter_id = ReportReviewService._get_submitter_id(report, report_type)
        if submitter_id and submitter_id == pm_user_id:
            return False, "لا يمكنك مراجعة تقريرك الخاص"
        
        try:
            # Update report status
            previous_status = report.status
            report.status = 'REJECTED_BY_PM'
            report.reviewed_by_user_id = pm_user_id
            report.reviewed_at = datetime.utcnow()
            report.review_notes = reason
            
            # Create audit log
            audit = ReportReview(
                report_type=report_type,
                report_id=str(report_id),
                action='REJECT',
                previous_status=previous_status,
                new_status='REJECTED_BY_PM',
                reviewed_by_user_id=pm_user_id,
                review_notes=reason,
                project_id=report.project_id
            )
            db.session.add(audit)
            
            # Notify submitter immediately
            if submitter_id:
                report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
                ReportReviewService._notify_submitter(
                    submitter_id,
                    report_type,
                    report_id,
                    pm_user_id,
                    f"تم رفض {report_name}: {reason}",
                    'REJECT',
                    report.project_id
                )
            
            db.session.commit()
            return True, "تم رفض التقرير بنجاح"
            
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في رفض التقرير: {str(e)}"
    
    @staticmethod
    def get_report_history(
        report_type: str,
        report_id: str,
        pm_user_id: str
    ) -> Optional[List[ReportReview]]:
        """Get audit trail for a specific report"""
        # Verify PM has access to this report
        report = ReportReviewService.get_report(report_type, report_id, pm_user_id)
        
        if not report:
            return None
        
        # Get all review actions for this report
        history = ReportReview.query.filter_by(
            report_type=report_type,
            report_id=str(report_id)
        ).order_by(ReportReview.created_at.desc()).all()
        
        return history
    
    @staticmethod
    def _notify_submitter(
        submitter_id: str,
        report_type: str,
        report_id: str,
        pm_user_id: str,
        message: str,
        action: str,
        project_id: str
    ):
        """Create immediate notification for report submitter"""
        pm_user = User.query.get(pm_user_id)
        pm_name = pm_user.username if pm_user else "مدير المشروع"
        report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
        
        if action == 'REQUEST_EDITS':
            notification_type = NotificationType.REPORT_EDITS_REQUESTED
            title = f"طلب تعديل - {report_name}"
        elif action == 'REJECT':
            notification_type = NotificationType.REPORT_REJECTED
            title = f"تم رفض - {report_name}"
        else:
            notification_type = NotificationType.REPORT_APPROVED
            title = f"تم الاعتماد - {report_name}"
        
        notification = Notification(
            user_id=submitter_id,
            type=notification_type,
            title=title,
            message=message,
            related_id=str(report_id),
            related_type=f'{report_type}_REPORT'
        )
        db.session.add(notification)
    
    @staticmethod
    def _notify_admin(
        report_type: str,
        report_id: str,
        pm_user_id: str,
        project_id: str
    ):
        """Notify all active General Admins about forwarded report"""
        # Get all active General Admin users
        admin_users = User.query.filter_by(
            role=UserRole.GENERAL_ADMIN,
            active=True
        ).all()
        
        pm_user = User.query.get(pm_user_id)
        pm_name = pm_user.username if pm_user else "مدير المشروع"
        report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
        
        # Create individual notification for each admin
        for admin in admin_users:
            notification = Notification(
                user_id=str(admin.id),
                type=NotificationType.REPORT_FORWARDED_TO_ADMIN,
                title=f"تقرير جديد للمراجعة - {report_name}",
                message=f"تم اعتماد {report_name} من قبل {pm_name} وإرساله للمراجعة النهائية",
                related_id=str(report_id),
                related_type=f'{report_type}_REPORT'
            )
            db.session.add(notification)
    
    @staticmethod
    def get_admin_report(report_type: str, report_id: str, admin_user_id: str) -> Optional[object]:
        """Fetch specific report for admin review (no project scope check)"""
        # Verify user is General Admin
        admin_user = User.query.get(admin_user_id)
        if not admin_user or admin_user.role != UserRole.GENERAL_ADMIN:
            return None
        
        if report_type not in ReportReviewService.REPORT_TYPE_MODELS:
            return None
        
        Model = ReportReviewService.REPORT_TYPE_MODELS[report_type]
        report = Model.query.get(report_id)
        
        return report
    
    @staticmethod
    def get_forwarded_reports(admin_user_id: str) -> Dict[str, List]:
        """Get all reports forwarded to admin (status='FORWARDED_TO_ADMIN')"""
        # Verify user is General Admin
        admin_user = User.query.get(admin_user_id)
        if not admin_user or admin_user.role != UserRole.GENERAL_ADMIN:
            return {
                'HANDLER': [],
                'TRAINER': [],
                'VET': [],
                'CARETAKER': []
            }
        
        result = {}
        
        # Get HANDLER reports
        handler_reports = HandlerReport.query.filter_by(
            status='FORWARDED_TO_ADMIN'
        ).order_by(desc(HandlerReport.reviewed_at)).all()
        result['HANDLER'] = [report for report in handler_reports]
        
        # Get TRAINER reports
        trainer_reports = BreedingTrainingActivity.query.filter_by(
            status='FORWARDED_TO_ADMIN'
        ).order_by(desc(BreedingTrainingActivity.reviewed_at)).all()
        result['TRAINER'] = [report for report in trainer_reports]
        
        # Get VET reports
        vet_reports = VeterinaryVisit.query.filter_by(
            status='FORWARDED_TO_ADMIN'
        ).order_by(desc(VeterinaryVisit.reviewed_at)).all()
        result['VET'] = [report for report in vet_reports]
        
        # Get CARETAKER reports
        caretaker_reports = CaretakerDailyLog.query.filter_by(
            status='FORWARDED_TO_ADMIN'
        ).order_by(desc(CaretakerDailyLog.reviewed_at)).all()
        result['CARETAKER'] = [report for report in caretaker_reports]
        
        return result
    
    @staticmethod
    def admin_approve(
        report_type: str,
        report_id: str,
        admin_user_id: str,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Admin final approval: FORWARDED_TO_ADMIN → APPROVED_BY_ADMIN
        Notifies both submitter and PM
        """
        report = ReportReviewService.get_admin_report(report_type, report_id, admin_user_id)
        
        if not report:
            return False, "تعذر العثور على التقرير أو ليس لديك صلاحية الوصول"
        
        if report.status != 'FORWARDED_TO_ADMIN':
            return False, f"التقرير في حالة {report.status} ولا يمكن اعتماده من الإدارة العامة"
        
        try:
            # Update report status
            previous_status = report.status
            report.status = 'APPROVED_BY_ADMIN'
            
            # Create audit log
            audit = ReportReview(
                report_type=report_type,
                report_id=str(report_id),
                action='ADMIN_APPROVE',
                previous_status=previous_status,
                new_status='APPROVED_BY_ADMIN',
                reviewed_by_user_id=admin_user_id,
                review_notes=notes,
                project_id=report.project_id
            )
            db.session.add(audit)
            
            # Notify submitter
            submitter_id = ReportReviewService._get_submitter_id(report, report_type)
            if submitter_id:
                report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
                admin_user = User.query.get(admin_user_id)
                admin_name = admin_user.username if admin_user else "الإدارة العامة"
                
                notification = Notification(
                    user_id=submitter_id,
                    type=NotificationType.REPORT_APPROVED,
                    title=f"تم اعتماد التقرير - {report_name}",
                    message=f"تم اعتماد {report_name} نهائياً من قبل {admin_name}",
                    related_id=str(report_id),
                    related_type=f'{report_type}_REPORT'
                )
                db.session.add(notification)
            
            # Notify PM
            if report.reviewed_by_user_id:
                report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
                admin_user = User.query.get(admin_user_id)
                admin_name = admin_user.username if admin_user else "الإدارة العامة"
                
                notification = Notification(
                    user_id=str(report.reviewed_by_user_id),
                    type=NotificationType.REPORT_APPROVED,
                    title=f"تم اعتماد التقرير - {report_name}",
                    message=f"تم اعتماد {report_name} نهائياً من قبل {admin_name}",
                    related_id=str(report_id),
                    related_type=f'{report_type}_REPORT'
                )
                db.session.add(notification)
            
            db.session.commit()
            return True, "تم اعتماد التقرير بنجاح"
            
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في اعتماد التقرير: {str(e)}"
    
    @staticmethod
    def admin_reject(
        report_type: str,
        report_id: str,
        admin_user_id: str,
        reason: str
    ) -> Tuple[bool, str]:
        """
        Admin final rejection: FORWARDED_TO_ADMIN → REJECTED_BY_ADMIN
        Notifies both submitter and PM with reason
        """
        if not reason or not reason.strip():
            return False, "يجب إدخال سبب الرفض"
        
        report = ReportReviewService.get_admin_report(report_type, report_id, admin_user_id)
        
        if not report:
            return False, "تعذر العثور على التقرير أو ليس لديك صلاحية الوصول"
        
        if report.status != 'FORWARDED_TO_ADMIN':
            return False, f"التقرير في حالة {report.status} ولا يمكن رفضه من الإدارة العامة"
        
        try:
            # Update report status
            previous_status = report.status
            report.status = 'REJECTED_BY_ADMIN'
            
            # Create audit log
            audit = ReportReview(
                report_type=report_type,
                report_id=str(report_id),
                action='ADMIN_REJECT',
                previous_status=previous_status,
                new_status='REJECTED_BY_ADMIN',
                reviewed_by_user_id=admin_user_id,
                review_notes=reason,
                project_id=report.project_id
            )
            db.session.add(audit)
            
            # Notify submitter
            submitter_id = ReportReviewService._get_submitter_id(report, report_type)
            if submitter_id:
                report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
                admin_user = User.query.get(admin_user_id)
                admin_name = admin_user.username if admin_user else "الإدارة العامة"
                
                notification = Notification(
                    user_id=submitter_id,
                    type=NotificationType.REPORT_REJECTED,
                    title=f"تم رفض التقرير - {report_name}",
                    message=f"تم رفض {report_name} من قبل {admin_name}: {reason}",
                    related_id=str(report_id),
                    related_type=f'{report_type}_REPORT'
                )
                db.session.add(notification)
            
            # Notify PM
            if report.reviewed_by_user_id:
                report_name = ReportReviewService.REPORT_TYPE_NAMES.get(report_type, 'التقرير')
                admin_user = User.query.get(admin_user_id)
                admin_name = admin_user.username if admin_user else "الإدارة العامة"
                
                notification = Notification(
                    user_id=str(report.reviewed_by_user_id),
                    type=NotificationType.REPORT_REJECTED,
                    title=f"تم رفض التقرير - {report_name}",
                    message=f"تم رفض {report_name} من قبل {admin_name}: {reason}",
                    related_id=str(report_id),
                    related_type=f'{report_type}_REPORT'
                )
                db.session.add(notification)
            
            db.session.commit()
            return True, "تم رفض التقرير بنجاح"
            
        except Exception as e:
            db.session.rollback()
            return False, f"خطأ في رفض التقرير: {str(e)}"
