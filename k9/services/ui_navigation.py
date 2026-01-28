"""
UI Navigation Registry - Single Source of Truth for Navigation Authorization
============================================================================

This module defines all navigation items with their permission requirements.
All templates must use this registry to render navigation consistently.

Key Concepts:
- Each menu item has required permissions (any or all)
- Parent menus only show if at least one child is visible
- Final destination permissions ensure users can access the target page
- Uses effective_permissions (role baseline + grants - revokes)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable
from flask import url_for, request
from flask_login import current_user


@dataclass
class NavItem:
    """Single navigation item with permission requirements"""
    id: str
    label: str
    icon: str
    endpoint: str = ""
    endpoint_args: dict = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    permission_mode: str = "any"
    children: List['NavItem'] = field(default_factory=list)
    divider_before: bool = False
    header: str = ""
    badge_func: Optional[Callable] = None
    role_scope: Optional[str] = None
    
    def get_url(self):
        """Get the URL for this nav item"""
        if self.endpoint:
            try:
                return url_for(self.endpoint, **self.endpoint_args)
            except:
                return "#"
        return "#"
    
    def is_active(self):
        """Check if this nav item or any child is active"""
        if self.endpoint and request.endpoint == self.endpoint:
            return True
        for child in self.children:
            if child.is_active():
                return True
        return False


class UINavigationRegistry:
    """
    Centralized registry for all navigation items.
    Provides permission-filtered navigation for templates.
    """
    
    @staticmethod
    def get_main_navigation():
        """
        Main navigation items for base.html (desktop and mobile)
        Returns list of NavItem with children
        """
        return [
            NavItem(
                id="dashboard",
                label="الرئيسية",
                icon="fas fa-home",
                endpoint="main.dashboard",
                permissions=[]
            ),
            NavItem(
                id="resources",
                label="الموارد",
                icon="fas fa-users",
                permissions=["dogs.view", "dogs.create", "dogs.edit", "employees.view", "employees.create", "employees.edit"],
                permission_mode="any",
                children=[
                    NavItem(
                        id="dogs_header",
                        label="الكلاب",
                        icon="",
                        header="الكلاب",
                        permissions=["dogs.view", "dogs.create", "dogs.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="dogs_list",
                        label="قائمة الكلاب",
                        icon="fas fa-dog",
                        endpoint="main.dogs_list",
                        permissions=["dogs.view", "dogs.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="dogs_add",
                        label="إضافة كلب",
                        icon="fas fa-plus",
                        endpoint="main.dogs_add",
                        permissions=["dogs.create"]
                    ),
                    NavItem(
                        id="employees_header",
                        label="الموظفين",
                        icon="",
                        header="الموظفين",
                        permissions=["employees.view", "employees.create", "employees.edit"],
                        permission_mode="any",
                        divider_before=True
                    ),
                    NavItem(
                        id="employees_list",
                        label="قائمة الموظفين",
                        icon="fas fa-users",
                        endpoint="main.employees_list",
                        permissions=["employees.view", "employees.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="employees_add",
                        label="إضافة موظف",
                        icon="fas fa-user-plus",
                        endpoint="main.employees_add",
                        permissions=["employees.create"]
                    ),
                ]
            ),
            NavItem(
                id="breeding",
                label="التربية",
                icon="fas fa-leaf",
                permissions=["training.view", "training.create", "training.edit", "training.delete", "breeding.view", "breeding.create", "breeding.edit"],
                permission_mode="any",
                children=[
                    NavItem(
                        id="training_header",
                        label="التدريب",
                        icon="",
                        header="التدريب",
                        permissions=["training.view", "training.create", "training.edit", "training.delete"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="training_list",
                        label="جلسات التدريب",
                        icon="fas fa-clipboard",
                        endpoint="main.training_list",
                        permissions=["training.view", "training.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="training_add",
                        label="إضافة جلسة",
                        icon="fas fa-plus",
                        endpoint="main.training_add",
                        permissions=["training.create"],
                        divider_before=True
                    ),
                    NavItem(
                        id="breeding_header",
                        label="الرعاية اليومية",
                        icon="",
                        header="الرعاية اليومية",
                        permissions=["breeding.view"],
                        divider_before=True
                    ),
                    NavItem(
                        id="breeding_feeding",
                        label="التغذية",
                        icon="fas fa-utensils",
                        endpoint="main.breeding_feeding",
                        permissions=["breeding.view"]
                    ),
                    NavItem(
                        id="breeding_checkup",
                        label="الفحص الظاهري",
                        icon="fas fa-stethoscope",
                        endpoint="main.breeding_checkup",
                        permissions=["breeding.view"]
                    ),
                    NavItem(
                        id="breeding_excretion",
                        label="البراز / البول / القيء",
                        icon="fas fa-tint",
                        endpoint="main.breeding_excretion",
                        permissions=["breeding.view"]
                    ),
                    NavItem(
                        id="breeding_care_header",
                        label="الرعاية والتدريب",
                        icon="",
                        header="الرعاية والتدريب",
                        permissions=["breeding.view"],
                        divider_before=True
                    ),
                    NavItem(
                        id="breeding_grooming",
                        label="العناية (الاستحمام والصيانة)",
                        icon="fas fa-cut",
                        endpoint="main.breeding_grooming",
                        permissions=["breeding.view"]
                    ),
                    NavItem(
                        id="breeding_deworming",
                        label="جرعة الديدان",
                        icon="fas fa-capsules",
                        endpoint="main.breeding_deworming",
                        permissions=["breeding.view"]
                    ),
                    NavItem(
                        id="breeding_cleaning",
                        label="النظافة (البيئة/القفص)",
                        icon="fas fa-broom",
                        endpoint="main.breeding_cleaning",
                        permissions=["breeding.view"]
                    ),
                ]
            ),
            NavItem(
                id="veterinary",
                label="الطبابة",
                icon="fas fa-stethoscope",
                permissions=["veterinary.view", "veterinary.create", "veterinary.edit"],
                permission_mode="any",
                children=[
                    NavItem(
                        id="veterinary_list",
                        label="الزيارات البيطرية",
                        icon="fas fa-notes-medical",
                        endpoint="main.veterinary_list",
                        permissions=["veterinary.view"]
                    ),
                    NavItem(
                        id="veterinary_add",
                        label="إضافة زيارة",
                        icon="fas fa-plus-square",
                        endpoint="main.veterinary_add",
                        permissions=["veterinary.create"]
                    ),
                ]
            ),
            NavItem(
                id="production",
                label="الإنتاج",
                icon="fas fa-heart",
                permissions=["production.view", "production.create", "production.edit"],
                permission_mode="any",
                children=[
                    NavItem(
                        id="production_header",
                        label="إدارة الإنتاج",
                        icon="",
                        header="إدارة الإنتاج",
                        permissions=["production.view", "production.create", "production.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="production_list",
                        label="لوحة الإنتاج",
                        icon="fas fa-tachometer-alt",
                        endpoint="main.production_list",
                        permissions=["production.view", "production.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="lifecycle_header",
                        label="دورة الحياة",
                        icon="",
                        header="دورة الحياة",
                        permissions=["production.view"],
                        divider_before=True
                    ),
                    NavItem(
                        id="maturity_list",
                        label="البلوغ",
                        icon="fas fa-seedling",
                        endpoint="main.maturity_list",
                        permissions=["production.view"]
                    ),
                    NavItem(
                        id="heat_cycles_list",
                        label="الدورة",
                        icon="fas fa-calendar-alt",
                        endpoint="main.heat_cycles_list",
                        permissions=["production.view"]
                    ),
                    NavItem(
                        id="mating_list",
                        label="التزاوج",
                        icon="fas fa-heart",
                        endpoint="main.mating_list",
                        permissions=["production.view"]
                    ),
                    NavItem(
                        id="pregnancy_list",
                        label="الحمل",
                        icon="fas fa-baby",
                        endpoint="main.pregnancy_list",
                        permissions=["production.view"]
                    ),
                    NavItem(
                        id="delivery_list",
                        label="الولادة",
                        icon="fas fa-baby-carriage",
                        endpoint="main.delivery_list",
                        permissions=["production.view"]
                    ),
                    NavItem(
                        id="puppies_header",
                        label="الجراء",
                        icon="",
                        header="الجراء",
                        permissions=["production.view"],
                        divider_before=True
                    ),
                    NavItem(
                        id="puppies_list",
                        label="الجراء",
                        icon="fas fa-paw",
                        endpoint="main.puppies_list",
                        permissions=["production.view"]
                    ),
                    NavItem(
                        id="puppy_training_list",
                        label="تدريب الجراء",
                        icon="fas fa-graduation-cap",
                        endpoint="main.puppy_training_list",
                        permissions=["production.view"]
                    ),
                ]
            ),
            NavItem(
                id="projects",
                label="المشاريع",
                icon="fas fa-project-diagram",
                permissions=["projects.view", "projects.create", "projects.edit", "incidents.view", "incidents.create", "suspicions.view", "suspicions.create"],
                permission_mode="any",
                children=[
                    NavItem(
                        id="projects_header",
                        label="إدارة المشاريع",
                        icon="",
                        header="إدارة المشاريع",
                        permissions=["projects.view", "projects.create", "projects.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="projects_list",
                        label="قائمة المشاريع",
                        icon="fas fa-folder",
                        endpoint="main.projects",
                        permissions=["projects.view", "projects.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="project_add",
                        label="إضافة مشروع",
                        icon="fas fa-plus-circle",
                        endpoint="main.project_add",
                        permissions=["projects.create"]
                    ),
                    NavItem(
                        id="incidents_header",
                        label="الحوادث",
                        icon="",
                        header="الحوادث",
                        permissions=["incidents.view", "incidents.create", "incidents.edit"],
                        permission_mode="any",
                        divider_before=True
                    ),
                    NavItem(
                        id="incidents_list",
                        label="قائمة الحوادث",
                        icon="fas fa-exclamation-triangle",
                        endpoint="main.incidents",
                        permissions=["incidents.view", "incidents.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="incident_add",
                        label="إضافة حادثة",
                        icon="fas fa-plus",
                        endpoint="main.incident_add",
                        permissions=["incidents.create"]
                    ),
                    NavItem(
                        id="suspicions_header",
                        label="الاشتباهات",
                        icon="",
                        header="الاشتباهات",
                        permissions=["suspicions.view", "suspicions.create", "suspicions.edit"],
                        permission_mode="any",
                        divider_before=True
                    ),
                    NavItem(
                        id="suspicions_list",
                        label="قائمة الاشتباهات",
                        icon="fas fa-search",
                        endpoint="main.suspicions",
                        permissions=["suspicions.view", "suspicions.edit"],
                        permission_mode="any"
                    ),
                    NavItem(
                        id="suspicion_add",
                        label="إضافة اشتباه",
                        icon="fas fa-plus",
                        endpoint="main.suspicion_add",
                        permissions=["suspicions.create"]
                    ),
                ]
            ),
            NavItem(
                id="reports",
                label="التقارير",
                icon="fas fa-file-alt",
                permissions=["reports.view"],
                children=[
                    NavItem(
                        id="reports_hub",
                        label="مركز التقارير",
                        icon="fas fa-chart-bar",
                        endpoint="main.reports_hub",
                        permissions=["reports.view"]
                    ),
                ]
            ),
        ]
    
    @staticmethod
    def get_handler_navigation():
        """
        Handler-specific navigation items
        Only visible to handlers (non-admin, non-PM roles)
        """
        return NavItem(
            id="handler_daily",
            label="التقرير اليومي",
            icon="fas fa-clipboard-check",
            permissions=["handler_daily.view", "handler_daily.reports.view", "handler_daily.reports.create", "tasks.my_tasks.view", "notifications.view"],
            permission_mode="any",
            role_scope="handler",
            children=[
                NavItem(
                    id="handler_dashboard",
                    label="لوحة التحكم",
                    icon="fas fa-tachometer-alt",
                    endpoint="handler.dashboard",
                    permissions=["handler_daily.reports.view"]
                ),
                NavItem(
                    id="handler_my_reports",
                    label="تقاريري",
                    icon="fas fa-file-alt",
                    endpoint="handler.my_reports",
                    permissions=["handler_daily.reports.view"]
                ),
                NavItem(
                    id="handler_new_report",
                    label="تقرير جديد",
                    icon="fas fa-plus",
                    endpoint="handler.new_report",
                    permissions=["handler_daily.reports.create"]
                ),
                NavItem(
                    id="handler_tasks",
                    label="المهام المكلف بها",
                    icon="fas fa-tasks",
                    endpoint="tasks.handler_index",
                    permissions=["tasks.my_tasks.view"]
                ),
                NavItem(
                    id="handler_notifications",
                    label="الإشعارات",
                    icon="fas fa-bell",
                    endpoint="handler.notifications",
                    permissions=["notifications.view"],
                    divider_before=True
                ),
                NavItem(
                    id="handler_profile",
                    label="الملف الشخصي",
                    icon="fas fa-user",
                    endpoint="handler.profile",
                    permissions=["handler_daily.view"]
                ),
            ]
        )
    
    @staticmethod
    def get_pm_navigation():
        """
        Project Manager specific navigation items
        """
        return NavItem(
            id="pm_management",
            label="إدارة المشروع",
            icon="fas fa-project-diagram",
            permissions=["pm.dashboard.view", "pm.reports.review", "pm.schedules.view", "pm.attendance.view"],
            permission_mode="any",
            role_scope="project_manager",
            children=[
                NavItem(
                    id="pm_dashboard",
                    label="لوحة التحكم",
                    icon="fas fa-tachometer-alt",
                    endpoint="pm.dashboard",
                    permissions=["pm.dashboard.view"]
                ),
                NavItem(
                    id="pm_approvals",
                    label="طلبات الموافقة",
                    icon="fas fa-check-circle",
                    endpoint="pm.approvals",
                    permissions=["pm.reports.review"]
                ),
                NavItem(
                    id="pm_schedules",
                    label="إدارة الجداول",
                    icon="fas fa-calendar-alt",
                    endpoint="pm.schedules",
                    permissions=["pm.schedules.view"]
                ),
                NavItem(
                    id="pm_attendance",
                    label="الحضور والغياب",
                    icon="fas fa-user-clock",
                    endpoint="pm.attendance",
                    permissions=["pm.attendance.view"]
                ),
                NavItem(
                    id="pm_team",
                    label="فريق العمل",
                    icon="fas fa-users",
                    endpoint="pm.team",
                    permissions=["pm.team.view"]
                ),
            ]
        )
    
    @staticmethod
    def get_admin_navigation():
        """
        Admin/supervisor navigation items
        """
        return NavItem(
            id="admin",
            label="الإدارة",
            icon="fas fa-cog",
            permissions=[
                "admin.permissions.view", "admin.tasks.send", 
                "supervisor.reports.view", "supervisor.schedules.view",
                "admin.notifications.view", "admin.backup.manage",
                "account_management.view", "shifts.view"
            ],
            permission_mode="any",
            children=[
                NavItem(
                    id="admin_users_header",
                    label="المستخدمين",
                    icon="",
                    header="المستخدمين",
                    permissions=["admin.permissions.view", "account_management.view"],
                    permission_mode="any"
                ),
                NavItem(
                    id="admin_permissions",
                    label="صلاحيات المستخدمين",
                    icon="fas fa-user-shield",
                    endpoint="permissions.admin_permissions_v2",
                    permissions=["admin.permissions.view"]
                ),
                NavItem(
                    id="admin_account_management",
                    label="إدارة حسابات الموظفين",
                    icon="fas fa-users-cog",
                    endpoint="account_management.index",
                    permissions=["account_management.view"]
                ),
                NavItem(
                    id="admin_tasks_header",
                    label="المهام",
                    icon="",
                    header="المهام",
                    permissions=["admin.tasks.send"],
                    divider_before=True
                ),
                NavItem(
                    id="admin_tasks",
                    label="إدارة المهام",
                    icon="fas fa-tasks",
                    endpoint="tasks.admin_index",
                    permissions=["admin.tasks.send"]
                ),
                NavItem(
                    id="admin_supervisor_header",
                    label="الإشراف",
                    icon="",
                    header="الإشراف",
                    permissions=["supervisor.reports.view", "supervisor.schedules.view"],
                    permission_mode="any",
                    divider_before=True
                ),
                NavItem(
                    id="supervisor_reports",
                    label="تقارير المتابعة",
                    icon="fas fa-file-signature",
                    endpoint="supervisor.reports_index",
                    permissions=["supervisor.reports.view"]
                ),
                NavItem(
                    id="supervisor_schedules",
                    label="جداول المهام",
                    icon="fas fa-calendar-week",
                    endpoint="supervisor.schedules_index",
                    permissions=["supervisor.schedules.view"]
                ),
                NavItem(
                    id="admin_shifts",
                    label="إدارة الورديات",
                    icon="fas fa-clock",
                    endpoint="shifts.index",
                    permissions=["shifts.view"]
                ),
                NavItem(
                    id="admin_system_header",
                    label="النظام",
                    icon="",
                    header="النظام",
                    permissions=["admin.notifications.view", "admin.backup.manage"],
                    permission_mode="any",
                    divider_before=True
                ),
                NavItem(
                    id="admin_notifications",
                    label="إدارة الإشعارات",
                    icon="fas fa-bell",
                    endpoint="admin.admin_notifications",
                    permissions=["admin.notifications.view"]
                ),
                NavItem(
                    id="admin_backup",
                    label="النسخ الاحتياطي",
                    icon="fas fa-database",
                    endpoint="admin.backup_dashboard",
                    permissions=["admin.backup.manage"]
                ),
            ]
        )
    
    @staticmethod
    def get_pm_quick_nav():
        """
        PM quick navigation buttons (shown in PM header)
        """
        return [
            NavItem(
                id="pm_quick_dashboard",
                label="لوحة التحكم",
                icon="fas fa-tachometer-alt",
                endpoint="pm.dashboard",
                permissions=["pm.dashboard.view"]
            ),
            NavItem(
                id="pm_quick_approvals",
                label="طلبات الموافقة",
                icon="fas fa-check-circle",
                endpoint="pm.approvals",
                permissions=["pm.reports.review"]
            ),
            NavItem(
                id="pm_quick_schedules",
                label="إدارة الجداول",
                icon="fas fa-calendar-alt",
                endpoint="pm.schedules",
                permissions=["pm.schedules.view"]
            ),
            NavItem(
                id="pm_quick_attendance",
                label="الحضور والغياب",
                icon="fas fa-user-clock",
                endpoint="pm.attendance",
                permissions=["pm.attendance.view"]
            ),
            NavItem(
                id="pm_quick_team",
                label="فريق العمل",
                icon="fas fa-users",
                endpoint="pm.team",
                permissions=["pm.team.view"]
            ),
            NavItem(
                id="pm_quick_reports",
                label="التقارير",
                icon="fas fa-file-alt",
                endpoint="pm.reports",
                permissions=["pm.reports.view"]
            ),
        ]


class NavigationFilter:
    """
    Filters navigation items based on user permissions.
    Implements parent menu gating rule.
    """
    
    def __init__(self, has_permission_func, is_admin_func=None):
        """
        Initialize with permission checking function.
        
        Args:
            has_permission_func: Function that takes permission_key and returns bool
            is_admin_func: Optional function that returns True if user is admin
        """
        self.has_permission = has_permission_func
        self.is_admin = is_admin_func or (lambda: False)
    
    def check_permission(self, permissions: List[str], mode: str = "any") -> bool:
        """
        Check if user has required permissions.
        
        Args:
            permissions: List of permission keys
            mode: "any" = user needs at least one, "all" = user needs all
        
        Returns:
            True if permission check passes
        """
        if not permissions:
            return True
        
        if self.is_admin():
            return True
        
        if mode == "all":
            return all(self.has_permission(p) for p in permissions)
        else:
            return any(self.has_permission(p) for p in permissions)
    
    def filter_nav_item(self, item: NavItem) -> Optional[NavItem]:
        """
        Filter a nav item and its children based on permissions.
        Returns None if item should not be visible.
        Implements parent menu gating rule.
        
        Args:
            item: NavItem to filter
        
        Returns:
            Filtered NavItem or None if not visible
        """
        if not self.check_permission(item.permissions, item.permission_mode):
            return None
        
        if item.children:
            filtered_children = []
            for child in item.children:
                filtered_child = self.filter_nav_item(child)
                if filtered_child:
                    filtered_children.append(filtered_child)
            
            if not filtered_children:
                return None
            
            return NavItem(
                id=item.id,
                label=item.label,
                icon=item.icon,
                endpoint=item.endpoint,
                endpoint_args=item.endpoint_args,
                permissions=item.permissions,
                permission_mode=item.permission_mode,
                children=filtered_children,
                divider_before=item.divider_before,
                header=item.header,
                badge_func=item.badge_func,
                role_scope=item.role_scope
            )
        
        return item
    
    def filter_navigation(self, nav_items: List[NavItem]) -> List[NavItem]:
        """
        Filter a list of nav items.
        
        Args:
            nav_items: List of NavItem to filter
        
        Returns:
            Filtered list with only visible items
        """
        filtered = []
        for item in nav_items:
            filtered_item = self.filter_nav_item(item)
            if filtered_item:
                filtered.append(filtered_item)
        return filtered
