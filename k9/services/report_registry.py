"""
Centralized Report Registry Service
Single source of truth for all report definitions including:
- Column definitions (key, header, width, arabic flag)
- Filter configurations
- Report titles (Arabic)
- Data fetching logic

This ensures 100% parity between HTML preview and PDF export.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional
from enum import Enum
from datetime import datetime, date, timedelta
import logging

logger = logging.getLogger(__name__)


class FilterType(Enum):
    """Types of filters available for reports"""
    SELECT = 'select'
    MULTI_SELECT = 'multi_select'
    DATE_RANGE = 'date_range'
    TEXT_SEARCH = 'text_search'
    NUMBER_RANGE = 'number_range'


@dataclass
class ColumnDefinition:
    """Definition for a single report column"""
    key: str
    header: str
    width_mm: int = 25
    is_arabic: bool = True
    formatter: Optional[Callable] = None
    
    def format_value(self, value: Any) -> str:
        """Format a value using the column's formatter or default conversion"""
        if value is None:
            return ''
        if self.formatter:
            return self.formatter(value)
        return str(value)


@dataclass
class FilterDefinition:
    """Definition for a report filter"""
    key: str
    label: str
    filter_type: FilterType
    options: List[Dict[str, str]] = field(default_factory=list)
    default_value: Any = None
    

@dataclass
class ReportDefinition:
    """Complete definition for a report type"""
    report_type: str
    title_ar: str
    title_en: str
    icon: str
    color: str
    columns: List[ColumnDefinition]
    filters: List[FilterDefinition] = field(default_factory=list)
    description_ar: str = ''
    description_en: str = ''
    

class ReportRegistry:
    """
    Centralized registry for all report definitions.
    Provides a single source of truth for report structure.
    """
    
    _instance = None
    _reports: Dict[str, ReportDefinition] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_reports()
        return cls._instance
    
    def _initialize_reports(self):
        """Initialize all report definitions"""
        self._reports = {}
        
        # Dogs Report
        self._reports['dogs'] = ReportDefinition(
            report_type='dogs',
            title_ar='تقرير الكلاب',
            title_en='Dogs Report',
            icon='fa-dog',
            color='primary',
            description_ar='تقرير شامل بجميع معلومات الكلاب المسجلة في النظام',
            description_en='Comprehensive report of all registered dogs',
            columns=[
                ColumnDefinition(key='row_num', header='م', width_mm=10, is_arabic=False),
                ColumnDefinition(key='name', header='اسم الكلب', width_mm=25),
                ColumnDefinition(key='code', header='الكود', width_mm=20, is_arabic=False),
                ColumnDefinition(key='breed', header='السلالة', width_mm=25),
                ColumnDefinition(key='gender', header='الجنس', width_mm=15),
                ColumnDefinition(key='status', header='الحالة', width_mm=20),
                ColumnDefinition(key='location', header='الموقع', width_mm=25),
                ColumnDefinition(key='age', header='العمر', width_mm=15),
            ],
            filters=[
                FilterDefinition(
                    key='gender',
                    label='الجنس',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'MALE', 'label': 'ذكر'},
                        {'value': 'FEMALE', 'label': 'أنثى'}
                    ]
                ),
                FilterDefinition(
                    key='status',
                    label='الحالة',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'ACTIVE', 'label': 'نشط'},
                        {'value': 'RETIRED', 'label': 'متقاعد'},
                        {'value': 'DECEASED', 'label': 'متوفى'},
                        {'value': 'TRAINING', 'label': 'تدريب'}
                    ]
                ),
                FilterDefinition(
                    key='breed',
                    label='السلالة',
                    filter_type=FilterType.TEXT_SEARCH
                ),
                FilterDefinition(
                    key='keyword',
                    label='بحث',
                    filter_type=FilterType.TEXT_SEARCH
                )
            ]
        )
        
        # Employees Report
        self._reports['employees'] = ReportDefinition(
            report_type='employees',
            title_ar='تقرير الموظفين',
            title_en='Employees Report',
            icon='fa-users',
            color='success',
            description_ar='قائمة شاملة بجميع الموظفين ومعلوماتهم الوظيفية',
            description_en='Comprehensive list of all employees',
            columns=[
                ColumnDefinition(key='row_num', header='م', width_mm=10, is_arabic=False),
                ColumnDefinition(key='name', header='الاسم', width_mm=30),
                ColumnDefinition(key='employee_id', header='الرقم الوظيفي', width_mm=20, is_arabic=False),
                ColumnDefinition(key='role', header='الوظيفة', width_mm=25),
                ColumnDefinition(key='phone', header='الهاتف', width_mm=25, is_arabic=False),
                ColumnDefinition(key='status', header='الحالة', width_mm=15),
                ColumnDefinition(key='hire_date', header='تاريخ التعيين', width_mm=20, is_arabic=False),
            ],
            filters=[
                FilterDefinition(
                    key='role',
                    label='الوظيفة',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'HANDLER', 'label': 'مدرب'},
                        {'value': 'TRAINER', 'label': 'معالج'},
                        {'value': 'VET', 'label': 'طبيب بيطري'},
                        {'value': 'MANAGER', 'label': 'مدير'},
                        {'value': 'ADMIN', 'label': 'إداري'}
                    ]
                ),
                FilterDefinition(
                    key='status',
                    label='الحالة',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'ACTIVE', 'label': 'نشط'},
                        {'value': 'INACTIVE', 'label': 'غير نشط'}
                    ]
                ),
                FilterDefinition(
                    key='hire_date',
                    label='تاريخ التعيين',
                    filter_type=FilterType.DATE_RANGE
                )
            ]
        )
        
        # Training Report
        self._reports['training'] = ReportDefinition(
            report_type='training',
            title_ar='تقرير التدريب',
            title_en='Training Report',
            icon='fa-dumbbell',
            color='warning',
            description_ar='إحصائيات جلسات التدريب وتقييم الأداء',
            description_en='Training sessions statistics and performance evaluation',
            columns=[
                ColumnDefinition(key='row_num', header='م', width_mm=10, is_arabic=False),
                ColumnDefinition(key='dog_name', header='اسم الكلب', width_mm=25),
                ColumnDefinition(key='trainer_name', header='المدرب', width_mm=25),
                ColumnDefinition(key='category', header='الفئة', width_mm=20),
                ColumnDefinition(key='session_date', header='التاريخ', width_mm=20, is_arabic=False),
                ColumnDefinition(key='duration', header='المدة (دقيقة)', width_mm=15, is_arabic=False),
                ColumnDefinition(key='rating', header='التقييم', width_mm=15),
                ColumnDefinition(key='notes', header='ملاحظات', width_mm=30),
            ],
            filters=[
                FilterDefinition(
                    key='category',
                    label='فئة التدريب',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'OBEDIENCE', 'label': 'الطاعة'},
                        {'value': 'DETECTION', 'label': 'الكشف'},
                        {'value': 'PATROL', 'label': 'الدورية'},
                        {'value': 'TRACKING', 'label': 'التتبع'},
                        {'value': 'PROTECTION', 'label': 'الحماية'}
                    ]
                ),
                FilterDefinition(
                    key='date_range',
                    label='الفترة',
                    filter_type=FilterType.DATE_RANGE
                )
            ]
        )
        
        # Veterinary Report
        self._reports['veterinary'] = ReportDefinition(
            report_type='veterinary',
            title_ar='تقرير الطبابة',
            title_en='Veterinary Report',
            icon='fa-stethoscope',
            color='info',
            description_ar='سجلات الزيارات الطبية والفحوصات البيطرية',
            description_en='Medical visit records and veterinary examinations',
            columns=[
                ColumnDefinition(key='row_num', header='م', width_mm=10, is_arabic=False),
                ColumnDefinition(key='dog_name', header='اسم الكلب', width_mm=25),
                ColumnDefinition(key='visit_type', header='نوع الزيارة', width_mm=20),
                ColumnDefinition(key='visit_date', header='التاريخ', width_mm=20, is_arabic=False),
                ColumnDefinition(key='diagnosis', header='التشخيص', width_mm=30),
                ColumnDefinition(key='treatment', header='العلاج', width_mm=30),
                ColumnDefinition(key='vet_name', header='الطبيب', width_mm=25),
            ],
            filters=[
                FilterDefinition(
                    key='visit_type',
                    label='نوع الزيارة',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'ROUTINE', 'label': 'روتينية'},
                        {'value': 'EMERGENCY', 'label': 'طارئة'},
                        {'value': 'VACCINATION', 'label': 'تطعيم'},
                        {'value': 'SURGERY', 'label': 'جراحة'},
                        {'value': 'CHECKUP', 'label': 'فحص'}
                    ]
                ),
                FilterDefinition(
                    key='date_range',
                    label='الفترة',
                    filter_type=FilterType.DATE_RANGE
                )
            ]
        )
        
        # Breeding Report
        self._reports['breeding'] = ReportDefinition(
            report_type='breeding',
            title_ar='تقرير التكاثر',
            title_en='Breeding Report',
            icon='fa-paw',
            color='danger',
            description_ar='سجلات التكاثر والإنتاج للكلاب',
            description_en='Breeding and production records',
            columns=[
                ColumnDefinition(key='row_num', header='م', width_mm=10, is_arabic=False),
                ColumnDefinition(key='dog_name', header='اسم الكلب', width_mm=25),
                ColumnDefinition(key='cycle_type', header='نوع الدورة', width_mm=20),
                ColumnDefinition(key='start_date', header='تاريخ البدء', width_mm=20, is_arabic=False),
                ColumnDefinition(key='end_date', header='تاريخ الانتهاء', width_mm=20, is_arabic=False),
                ColumnDefinition(key='result', header='النتيجة', width_mm=20),
                ColumnDefinition(key='puppies_count', header='عدد الجراء', width_mm=15, is_arabic=False),
                ColumnDefinition(key='notes', header='ملاحظات', width_mm=30),
            ],
            filters=[
                FilterDefinition(
                    key='cycle_type',
                    label='نوع الدورة',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'MATING', 'label': 'تزاوج'},
                        {'value': 'PREGNANCY', 'label': 'حمل'},
                        {'value': 'DELIVERY', 'label': 'ولادة'},
                        {'value': 'WEANING', 'label': 'فطام'}
                    ]
                ),
                FilterDefinition(
                    key='date_range',
                    label='الفترة',
                    filter_type=FilterType.DATE_RANGE
                )
            ]
        )
        
        # Projects Report
        self._reports['projects'] = ReportDefinition(
            report_type='projects',
            title_ar='تقرير المشاريع',
            title_en='Projects Report',
            icon='fa-project-diagram',
            color='secondary',
            description_ar='تقرير بجميع المشاريع وحالاتها',
            description_en='Report of all projects and their status',
            columns=[
                ColumnDefinition(key='row_num', header='م', width_mm=10, is_arabic=False),
                ColumnDefinition(key='name', header='اسم المشروع', width_mm=30),
                ColumnDefinition(key='code', header='الكود', width_mm=20, is_arabic=False),
                ColumnDefinition(key='status', header='الحالة', width_mm=20),
                ColumnDefinition(key='start_date', header='تاريخ البدء', width_mm=20, is_arabic=False),
                ColumnDefinition(key='manager', header='المدير', width_mm=25),
                ColumnDefinition(key='dogs_count', header='عدد الكلاب', width_mm=15, is_arabic=False),
                ColumnDefinition(key='employees_count', header='عدد الموظفين', width_mm=15, is_arabic=False),
            ],
            filters=[
                FilterDefinition(
                    key='status',
                    label='الحالة',
                    filter_type=FilterType.MULTI_SELECT,
                    options=[
                        {'value': 'ACTIVE', 'label': 'نشط'},
                        {'value': 'COMPLETED', 'label': 'مكتمل'},
                        {'value': 'SUSPENDED', 'label': 'معلق'},
                        {'value': 'CANCELLED', 'label': 'ملغى'}
                    ]
                ),
                FilterDefinition(
                    key='date_range',
                    label='الفترة',
                    filter_type=FilterType.DATE_RANGE
                )
            ]
        )
        
        logger.info(f"ReportRegistry initialized with {len(self._reports)} report types")
    
    def get_report(self, report_type: str) -> Optional[ReportDefinition]:
        """Get a report definition by type"""
        return self._reports.get(report_type)
    
    def get_all_reports(self) -> Dict[str, ReportDefinition]:
        """Get all registered reports"""
        return self._reports.copy()
    
    def get_report_types(self) -> List[str]:
        """Get list of all registered report types"""
        return list(self._reports.keys())
    
    def get_columns(self, report_type: str) -> List[ColumnDefinition]:
        """Get column definitions for a report type"""
        report = self._reports.get(report_type)
        return report.columns if report else []
    
    def get_filters(self, report_type: str) -> List[FilterDefinition]:
        """Get filter definitions for a report type"""
        report = self._reports.get(report_type)
        return report.filters if report else []
    
    def get_headers(self, report_type: str) -> List[str]:
        """Get just the header names for a report type"""
        columns = self.get_columns(report_type)
        return [col.header for col in columns]
    
    def get_column_keys(self, report_type: str) -> List[str]:
        """Get just the column keys for a report type"""
        columns = self.get_columns(report_type)
        return [col.key for col in columns]


def get_report_registry() -> ReportRegistry:
    """Get the singleton ReportRegistry instance"""
    return ReportRegistry()
