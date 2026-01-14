"""
نماذج نظام التقارير الموحد
Unified Reporting Models Layer

This module provides a unified model layer for all report types in the K9 Operations system.
Supports: Generate Once → Preview → Export pattern with caching, approval workflows, and export tracking.
"""
from app import db
from datetime import datetime
from enum import Enum
from k9.models.model_utils import get_uuid_column, default_uuid
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Text, Index


# ============================================================================
# Unified Enums - أنواع التقارير والحالات الموحدة
# ============================================================================

class UnifiedReportType(Enum):
    """
    نوع التقرير الموحد
    Unified report type covering all report categories in the system
    """
    HANDLER = "HANDLER"              # تقرير السائس اليومي
    SHIFT = "SHIFT"                  # تقرير الوردية
    TRAINER = "TRAINER"              # تقرير المدرب
    VET = "VET"                      # تقرير الطبيب البيطري
    CARETAKER = "CARETAKER"          # تقرير المربي اليومي
    ATTENDANCE = "ATTENDANCE"        # تقرير الحضور
    INCIDENT = "INCIDENT"            # تقرير الحوادث
    FEEDING = "FEEDING"              # تقرير التغذية
    CHECKUP = "CHECKUP"              # تقرير الفحص الصحي
    GROOMING = "GROOMING"            # تقرير العناية
    DEWORMING = "DEWORMING"          # تقرير مكافحة الديدان
    PRODUCTION = "PRODUCTION"        # تقرير الإنتاج
    EVALUATION = "EVALUATION"        # تقرير التقييم
    CUSTOM = "CUSTOM"                # تقرير مخصص


class UnifiedReportStatus(Enum):
    """
    حالة التقرير الموحدة - سير العمل الكامل
    Unified report status covering the complete approval workflow
    """
    DRAFT = "DRAFT"                          # مسودة - قيد الإعداد
    SUBMITTED = "SUBMITTED"                  # تم الإرسال - بانتظار المراجعة
    PM_REVIEWED = "PM_REVIEWED"              # تمت المراجعة من مدير المشروع
    PM_APPROVED = "PM_APPROVED"              # معتمد من مدير المشروع
    PM_REJECTED = "PM_REJECTED"              # مرفوض من مدير المشروع
    FORWARDED_TO_ADMIN = "FORWARDED_TO_ADMIN"  # تم تحويله للإدارة العامة
    APPROVED = "APPROVED"                    # معتمد نهائياً
    REJECTED = "REJECTED"                    # مرفوض نهائياً
    ARCHIVED = "ARCHIVED"                    # مؤرشف


class ExportFormat(Enum):
    """
    صيغة التصدير
    Export format options
    """
    PDF = "PDF"
    EXCEL = "EXCEL"
    CSV = "CSV"
    JSON = "JSON"


class ReportPriority(Enum):
    """
    أولوية التقرير
    Report priority levels
    """
    LOW = "LOW"              # منخفضة
    NORMAL = "NORMAL"        # عادية
    HIGH = "HIGH"            # عالية
    URGENT = "URGENT"        # عاجلة


# ============================================================================
# Report Definition - تعريف نوع التقرير
# ============================================================================

class ReportDefinition(db.Model):
    """
    تعريف نوع التقرير - يحدد خصائص ومتطلبات كل نوع تقرير
    Defines a report type with its properties, required permissions, and data fields.
    
    This model acts as a registry/catalog of available report types in the system.
    Each report type has defined permissions, required fields, and display metadata.
    """
    __tablename__ = 'report_definition'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Report type identification
    report_type = db.Column(db.Enum(UnifiedReportType), nullable=False, unique=True)
    code = db.Column(db.String(50), nullable=False, unique=True)  # Short code: HANDLER_DAILY, VET_VISIT
    
    # Display names (bilingual)
    name_ar = db.Column(db.String(200), nullable=False)   # الاسم بالعربية
    name_en = db.Column(db.String(200), nullable=False)   # الاسم بالإنجليزية
    description_ar = db.Column(Text, nullable=True)       # الوصف بالعربية
    description_en = db.Column(Text, nullable=True)       # الوصف بالإنجليزية
    
    # Permissions required - stored as JSON array of permission keys
    # e.g., ["reports.view", "reports.create", "handler_daily.view"]
    required_permissions = db.Column(JSON, nullable=False, default=list)
    
    # Data field definitions - JSON schema for the report's data structure
    # Defines which fields are required, optional, and their types
    data_fields = db.Column(JSON, nullable=False, default=dict)
    
    # Report configuration
    requires_project = db.Column(db.Boolean, default=True)       # هل يتطلب مشروع
    requires_dog = db.Column(db.Boolean, default=False)          # هل يتطلب كلب
    requires_employee = db.Column(db.Boolean, default=True)      # هل يتطلب موظف
    supports_attachments = db.Column(db.Boolean, default=True)   # يدعم المرفقات
    
    # Approval workflow configuration
    requires_pm_approval = db.Column(db.Boolean, default=True)   # يتطلب موافقة مدير المشروع
    requires_admin_approval = db.Column(db.Boolean, default=False)  # يتطلب موافقة الإدارة
    
    # Display and sorting
    icon = db.Column(db.String(50), nullable=True)      # FontAwesome icon class
    color = db.Column(db.String(20), nullable=True)     # Bootstrap color class
    sort_order = db.Column(db.Integer, default=0)       # ترتيب العرض
    is_active = db.Column(db.Boolean, default=True)     # مفعل
    
    # Audit fields
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contexts = db.relationship('ReportContext', backref='definition', lazy='dynamic')
    
    __table_args__ = (
        Index('idx_report_definition_type', 'report_type'),
        Index('idx_report_definition_code', 'code'),
        Index('idx_report_definition_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<ReportDefinition {self.code} - {self.name_en}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'report_type': self.report_type.value,
            'code': self.code,
            'name_ar': self.name_ar,
            'name_en': self.name_en,
            'description_ar': self.description_ar,
            'description_en': self.description_en,
            'required_permissions': self.required_permissions,
            'data_fields': self.data_fields,
            'requires_project': self.requires_project,
            'requires_dog': self.requires_dog,
            'requires_employee': self.requires_employee,
            'supports_attachments': self.supports_attachments,
            'requires_pm_approval': self.requires_pm_approval,
            'requires_admin_approval': self.requires_admin_approval,
            'icon': self.icon,
            'color': self.color,
            'is_active': self.is_active
        }


# ============================================================================
# Report Context - سياق التقرير المولد
# ============================================================================

class ReportContext(db.Model):
    """
    سياق التقرير - يحتفظ ببيانات التقرير المولد وحالته
    Holds generated report data, metadata, and workflow status.
    
    Supports the Generate Once → Preview → Export pattern by caching
    generated report data and tracking approval workflow state.
    """
    __tablename__ = 'report_context'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Link to report definition
    definition_id = db.Column(get_uuid_column(), db.ForeignKey('report_definition.id'), nullable=True)
    
    # Report type (duplicated for quick queries without join)
    report_type = db.Column(db.Enum(UnifiedReportType), nullable=False, index=True)
    
    # Reference to the source report (polymorphic link)
    # Links to HandlerReport, ShiftReport, VeterinaryVisit, etc.
    source_report_id = db.Column(get_uuid_column(), nullable=True, index=True)
    source_report_table = db.Column(db.String(100), nullable=True)  # Table name for polymorphic reference
    
    # Scoping
    project_id = db.Column(get_uuid_column(), db.ForeignKey('project.id'), nullable=True)
    dog_id = db.Column(get_uuid_column(), db.ForeignKey('dog.id'), nullable=True)
    
    # Date range for aggregated reports
    date_from = db.Column(db.Date, nullable=True)
    date_to = db.Column(db.Date, nullable=True)
    report_date = db.Column(db.Date, nullable=True, index=True)  # Single date for daily reports
    
    # Status and workflow
    status = db.Column(db.Enum(UnifiedReportStatus), nullable=False, default=UnifiedReportStatus.DRAFT)
    priority = db.Column(db.Enum(ReportPriority), nullable=False, default=ReportPriority.NORMAL)
    
    # Generated report data - cached JSON containing the complete report data
    # This allows Generate Once → Preview → Export without regenerating
    cached_data = db.Column(JSON, nullable=True)
    cached_at = db.Column(db.DateTime, nullable=True)
    cache_valid = db.Column(db.Boolean, default=False)  # Invalidate when source data changes
    
    # Report metadata
    title = db.Column(db.String(300), nullable=True)       # عنوان التقرير
    title_ar = db.Column(db.String(300), nullable=True)    # عنوان التقرير بالعربية
    summary = db.Column(Text, nullable=True)               # ملخص التقرير
    notes = db.Column(Text, nullable=True)                 # ملاحظات إضافية
    
    # Creator/Submitter
    created_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=True)
    
    # PM Review workflow
    pm_reviewed_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=True)
    pm_reviewed_at = db.Column(db.DateTime, nullable=True)
    pm_review_notes = db.Column(Text, nullable=True)
    pm_review_status = db.Column(db.String(50), nullable=True)  # 'approved', 'rejected', 'needs_revision'
    
    # Admin Review workflow (for reports forwarded to admin)
    admin_reviewed_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=True)
    admin_reviewed_at = db.Column(db.DateTime, nullable=True)
    admin_review_notes = db.Column(Text, nullable=True)
    admin_review_status = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = db.relationship('Project', backref='report_contexts', foreign_keys=[project_id])
    dog = db.relationship('Dog', backref='report_contexts', foreign_keys=[dog_id])
    created_by = db.relationship('User', foreign_keys=[created_by_user_id], backref='created_report_contexts')
    pm_reviewer = db.relationship('User', foreign_keys=[pm_reviewed_by_user_id], backref='pm_reviewed_contexts')
    admin_reviewer = db.relationship('User', foreign_keys=[admin_reviewed_by_user_id], backref='admin_reviewed_contexts')
    
    # Related export history
    exports = db.relationship('ReportExportHistory', backref='context', cascade='all, delete-orphan', lazy='dynamic')
    
    # Approval history
    approvals = db.relationship('ReportApprovalHistory', backref='context', cascade='all, delete-orphan', lazy='dynamic')
    
    __table_args__ = (
        Index('idx_report_context_type', 'report_type'),
        Index('idx_report_context_status', 'status'),
        Index('idx_report_context_project', 'project_id'),
        Index('idx_report_context_date', 'report_date'),
        Index('idx_report_context_source', 'source_report_id', 'source_report_table'),
        Index('idx_report_context_creator', 'created_by_user_id'),
    )
    
    def __repr__(self):
        return f'<ReportContext {self.report_type.value} - {self.status.value}>'
    
    def invalidate_cache(self):
        """Invalidate cached data when source data changes"""
        self.cache_valid = False
        self.updated_at = datetime.utcnow()
    
    def update_cache(self, data: dict):
        """Update cached report data"""
        self.cached_data = data
        self.cached_at = datetime.utcnow()
        self.cache_valid = True
        self.updated_at = datetime.utcnow()
    
    def submit(self):
        """Submit report for review"""
        self.status = UnifiedReportStatus.SUBMITTED
        self.submitted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_cached_data=False):
        """Convert to dictionary for API responses"""
        result = {
            'id': str(self.id),
            'definition_id': str(self.definition_id) if self.definition_id else None,
            'report_type': self.report_type.value,
            'source_report_id': str(self.source_report_id) if self.source_report_id else None,
            'source_report_table': self.source_report_table,
            'project_id': str(self.project_id) if self.project_id else None,
            'dog_id': str(self.dog_id) if self.dog_id else None,
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'date_to': self.date_to.isoformat() if self.date_to else None,
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'status': self.status.value,
            'priority': self.priority.value,
            'title': self.title,
            'title_ar': self.title_ar,
            'summary': self.summary,
            'notes': self.notes,
            'created_by_user_id': str(self.created_by_user_id),
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'pm_reviewed_by_user_id': str(self.pm_reviewed_by_user_id) if self.pm_reviewed_by_user_id else None,
            'pm_reviewed_at': self.pm_reviewed_at.isoformat() if self.pm_reviewed_at else None,
            'pm_review_status': self.pm_review_status,
            'admin_reviewed_by_user_id': str(self.admin_reviewed_by_user_id) if self.admin_reviewed_by_user_id else None,
            'admin_reviewed_at': self.admin_reviewed_at.isoformat() if self.admin_reviewed_at else None,
            'admin_review_status': self.admin_review_status,
            'cache_valid': self.cache_valid,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        if include_cached_data and self.cached_data:
            result['cached_data'] = self.cached_data
        return result


# ============================================================================
# Report Export History - سجل تصدير التقارير
# ============================================================================

class ReportExportHistory(db.Model):
    """
    سجل تصدير التقارير - يتتبع متى ومن وكيف تم تصدير التقرير
    Tracks when reports are exported, by whom, and in what format.
    """
    __tablename__ = 'report_export_history'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Link to report context
    context_id = db.Column(get_uuid_column(), db.ForeignKey('report_context.id', ondelete='CASCADE'), nullable=False)
    
    # Export details
    export_format = db.Column(db.Enum(ExportFormat), nullable=False)
    exported_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    exported_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # File information
    file_path = db.Column(db.String(500), nullable=True)    # المسار للملف المصدر
    file_name = db.Column(db.String(255), nullable=True)    # اسم الملف
    file_size = db.Column(db.Integer, nullable=True)        # حجم الملف بالبايت
    
    # Export parameters (filters, date range, etc.)
    export_params = db.Column(JSON, nullable=True)
    
    # Status
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(Text, nullable=True)
    
    # IP address for audit
    ip_address = db.Column(db.String(50), nullable=True)
    
    # Relationships
    exported_by = db.relationship('User', backref='report_exports')
    
    __table_args__ = (
        Index('idx_export_history_context', 'context_id'),
        Index('idx_export_history_user', 'exported_by_user_id'),
        Index('idx_export_history_date', 'exported_at'),
        Index('idx_export_history_format', 'export_format'),
    )
    
    def __repr__(self):
        return f'<ReportExportHistory {self.export_format.value} - {self.exported_at}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'context_id': str(self.context_id),
            'export_format': self.export_format.value,
            'exported_by_user_id': str(self.exported_by_user_id),
            'exported_at': self.exported_at.isoformat(),
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'export_params': self.export_params,
            'success': self.success,
            'error_message': self.error_message
        }


# ============================================================================
# Report Approval History - سجل موافقات التقارير
# ============================================================================

class ReportApprovalHistory(db.Model):
    """
    سجل موافقات التقارير - يتتبع كل خطوة في سير عمل الموافقة
    Tracks each step in the approval workflow history.
    """
    __tablename__ = 'report_approval_history'
    
    id = db.Column(get_uuid_column(), primary_key=True, default=default_uuid)
    
    # Link to report context
    context_id = db.Column(get_uuid_column(), db.ForeignKey('report_context.id', ondelete='CASCADE'), nullable=False)
    
    # Status transition
    from_status = db.Column(db.Enum(UnifiedReportStatus), nullable=True)
    to_status = db.Column(db.Enum(UnifiedReportStatus), nullable=False)
    
    # Action details
    action = db.Column(db.String(50), nullable=False)  # 'submit', 'approve', 'reject', 'forward', 'archive'
    action_by_user_id = db.Column(get_uuid_column(), db.ForeignKey('user.id'), nullable=False)
    action_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Notes and reason
    notes = db.Column(Text, nullable=True)
    rejection_reason = db.Column(Text, nullable=True)  # سبب الرفض
    
    # IP address for audit
    ip_address = db.Column(db.String(50), nullable=True)
    
    # Relationships
    action_by = db.relationship('User', backref='report_approval_actions')
    
    __table_args__ = (
        Index('idx_approval_history_context', 'context_id'),
        Index('idx_approval_history_user', 'action_by_user_id'),
        Index('idx_approval_history_date', 'action_at'),
        Index('idx_approval_history_action', 'action'),
    )
    
    def __repr__(self):
        return f'<ReportApprovalHistory {self.action} - {self.to_status.value}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': str(self.id),
            'context_id': str(self.context_id),
            'from_status': self.from_status.value if self.from_status else None,
            'to_status': self.to_status.value,
            'action': self.action,
            'action_by_user_id': str(self.action_by_user_id),
            'action_at': self.action_at.isoformat(),
            'notes': self.notes,
            'rejection_reason': self.rejection_reason
        }


# ============================================================================
# Helper mappings for compatibility with existing models
# ============================================================================

# Map existing model tables to UnifiedReportType
SOURCE_TABLE_TO_TYPE = {
    'handler_report': UnifiedReportType.HANDLER,
    'shift_report': UnifiedReportType.SHIFT,
    'breeding_training_activity': UnifiedReportType.TRAINER,
    'veterinary_visit': UnifiedReportType.VET,
    'caretaker_daily_log': UnifiedReportType.CARETAKER,
    'project_incident': UnifiedReportType.INCIDENT,
    'feeding_log': UnifiedReportType.FEEDING,
    'daily_checkup': UnifiedReportType.CHECKUP,
    'grooming_record': UnifiedReportType.GROOMING,
    'deworming_log': UnifiedReportType.DEWORMING,
}

# Map UnifiedReportType to Arabic display names
REPORT_TYPE_NAMES_AR = {
    UnifiedReportType.HANDLER: 'تقرير السائس اليومي',
    UnifiedReportType.SHIFT: 'تقرير الوردية',
    UnifiedReportType.TRAINER: 'تقرير المدرب',
    UnifiedReportType.VET: 'تقرير الطبيب البيطري',
    UnifiedReportType.CARETAKER: 'تقرير المربي اليومي',
    UnifiedReportType.ATTENDANCE: 'تقرير الحضور',
    UnifiedReportType.INCIDENT: 'تقرير الحوادث',
    UnifiedReportType.FEEDING: 'تقرير التغذية',
    UnifiedReportType.CHECKUP: 'تقرير الفحص الصحي',
    UnifiedReportType.GROOMING: 'تقرير العناية',
    UnifiedReportType.DEWORMING: 'تقرير مكافحة الديدان',
    UnifiedReportType.PRODUCTION: 'تقرير الإنتاج',
    UnifiedReportType.EVALUATION: 'تقرير التقييم',
    UnifiedReportType.CUSTOM: 'تقرير مخصص',
}

# Map UnifiedReportStatus to Arabic display names
REPORT_STATUS_NAMES_AR = {
    UnifiedReportStatus.DRAFT: 'مسودة',
    UnifiedReportStatus.SUBMITTED: 'تم الإرسال',
    UnifiedReportStatus.PM_REVIEWED: 'تمت المراجعة',
    UnifiedReportStatus.PM_APPROVED: 'معتمد من مدير المشروع',
    UnifiedReportStatus.PM_REJECTED: 'مرفوض من مدير المشروع',
    UnifiedReportStatus.FORWARDED_TO_ADMIN: 'تم تحويله للإدارة',
    UnifiedReportStatus.APPROVED: 'معتمد',
    UnifiedReportStatus.REJECTED: 'مرفوض',
    UnifiedReportStatus.ARCHIVED: 'مؤرشف',
}

# Map ExportFormat to Arabic display names
EXPORT_FORMAT_NAMES_AR = {
    ExportFormat.PDF: 'ملف PDF',
    ExportFormat.EXCEL: 'ملف Excel',
    ExportFormat.CSV: 'ملف CSV',
    ExportFormat.JSON: 'ملف JSON',
}
