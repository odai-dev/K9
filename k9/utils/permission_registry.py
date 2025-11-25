"""
Permission Registry - Comprehensive metadata for all system permissions
Maps permissions to actual pages, functions, and features in the K9 system
"""

from k9.models.models import PermissionType

# Comprehensive permission registry with Arabic descriptions
PERMISSION_REGISTRY = {
    "dogs": {
        "name_ar": "إدارة الكلاب",
        "name_en": "Dogs Management",
        "icon": "fa-dog",
        "permissions": {
            "view": {
                "name_ar": "عرض قائمة الكلاب",
                "name_en": "View dogs list",
                "routes": ["/dogs", "/dogs/list"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إضافة كلب جديد",
                "name_en": "Add new dog",
                "routes": ["/dogs/new", "/dogs/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل بيانات الكلب",
                "name_en": "Edit dog information",
                "routes": ["/dogs/<id>/edit", "/dogs/update"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف كلب",
                "name_en": "Delete dog",
                "routes": ["/dogs/<id>/delete"],
                "permission_type": PermissionType.DELETE
            },
            "assign": {
                "name_ar": "تعيين كلب لمشروع أو سائس",
                "name_en": "Assign dog to project or handler",
                "routes": ["/dogs/<id>/assign"],
                "permission_type": PermissionType.ASSIGN
            }
        }
    },
    
    "employees": {
        "name_ar": "إدارة الموظفين",
        "name_en": "Employee Management",
        "icon": "fa-users",
        "permissions": {
            "view": {
                "name_ar": "عرض قائمة الموظفين",
                "name_en": "View employees list",
                "routes": ["/employees", "/employees/list"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إضافة موظف جديد",
                "name_en": "Add new employee",
                "routes": ["/employees/new", "/employees/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل بيانات الموظف",
                "name_en": "Edit employee information",
                "routes": ["/employees/<id>/edit", "/employees/update"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف موظف",
                "name_en": "Delete employee",
                "routes": ["/employees/<id>/delete"],
                "permission_type": PermissionType.DELETE
            },
            "assign": {
                "name_ar": "تعيين موظف لمشروع",
                "name_en": "Assign employee to project",
                "routes": ["/employees/<id>/assign"],
                "permission_type": PermissionType.ASSIGN
            }
        }
    },
    
    "projects": {
        "name_ar": "إدارة المشاريع",
        "name_en": "Project Management",
        "icon": "fa-project-diagram",
        "permissions": {
            "view": {
                "name_ar": "عرض قائمة المشاريع",
                "name_en": "View projects list",
                "routes": ["/projects", "/projects/list", "/pm/dashboard"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إنشاء مشروع جديد",
                "name_en": "Create new project",
                "routes": ["/projects/new", "/projects/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل بيانات المشروع",
                "name_en": "Edit project information",
                "routes": ["/projects/<id>/edit", "/projects/update"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف مشروع",
                "name_en": "Delete project",
                "routes": ["/projects/<id>/delete"],
                "permission_type": PermissionType.DELETE
            }
        }
    },
    
    "attendance": {
        "name_ar": "الحضور والجداول اليومية",
        "name_en": "Attendance & Daily Schedules",
        "icon": "fa-calendar-check",
        "permissions": {
            "view": {
                "name_ar": "عرض الجداول اليومية والحضور",
                "name_en": "View daily schedules and attendance",
                "routes": ["/schedule", "/schedule/list", "/pm/schedules"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إنشاء جدول يومي جديد",
                "name_en": "Create new daily schedule",
                "routes": ["/schedule/new", "/schedule/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل الجدول اليومي",
                "name_en": "Edit daily schedule",
                "routes": ["/schedule/<id>/edit", "/schedule/update"],
                "permission_type": PermissionType.EDIT
            },
            "export": {
                "name_ar": "تصدير تقارير الحضور",
                "name_en": "Export attendance reports",
                "routes": ["/schedule/export", "/reports/attendance/export"],
                "permission_type": PermissionType.EXPORT
            }
        }
    },
    
    "training": {
        "name_ar": "التدريب",
        "name_en": "Training",
        "icon": "fa-dumbbell",
        "permissions": {
            "view": {
                "name_ar": "عرض سجلات التدريب",
                "name_en": "View training records",
                "routes": ["/training", "/training/list", "/pm/training"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إضافة سجل تدريب جديد",
                "name_en": "Add new training record",
                "routes": ["/training/new", "/training/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل سجل التدريب",
                "name_en": "Edit training record",
                "routes": ["/training/<id>/edit", "/training/update"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف سجل تدريب",
                "name_en": "Delete training record",
                "routes": ["/training/<id>/delete"],
                "permission_type": PermissionType.DELETE
            },
            "export": {
                "name_ar": "تصدير تقارير التدريب",
                "name_en": "Export training reports",
                "routes": ["/training/export", "/reports/training/export"],
                "permission_type": PermissionType.EXPORT
            }
        }
    },
    
    "veterinary": {
        "name_ar": "الرعاية الطبية",
        "name_en": "Veterinary Care",
        "icon": "fa-stethoscope",
        "permissions": {
            "view": {
                "name_ar": "عرض السجلات الطبية",
                "name_en": "View veterinary records",
                "routes": ["/veterinary", "/veterinary/list", "/pm/veterinary"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إضافة سجل طبي جديد",
                "name_en": "Add new veterinary record",
                "routes": ["/veterinary/new", "/veterinary/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل السجل الطبي",
                "name_en": "Edit veterinary record",
                "routes": ["/veterinary/<id>/edit", "/veterinary/update"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف سجل طبي",
                "name_en": "Delete veterinary record",
                "routes": ["/veterinary/<id>/delete"],
                "permission_type": PermissionType.DELETE
            },
            "export": {
                "name_ar": "تصدير التقارير الطبية",
                "name_en": "Export veterinary reports",
                "routes": ["/veterinary/export", "/reports/veterinary/export"],
                "permission_type": PermissionType.EXPORT
            }
        }
    },
    
    "breeding": {
        "name_ar": "التربية والإنتاج",
        "name_en": "Breeding & Production",
        "icon": "fa-paw",
        "permissions": {
            "view": {
                "name_ar": "عرض سجلات التربية",
                "name_en": "View breeding records",
                "routes": ["/breeding", "/breeding/list", "/pm/breeding"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إضافة سجل تربية جديد",
                "name_en": "Add new breeding record",
                "routes": ["/breeding/new", "/breeding/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل سجل التربية",
                "name_en": "Edit breeding record",
                "routes": ["/breeding/<id>/edit", "/breeding/update"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف سجل تربية",
                "name_en": "Delete breeding record",
                "routes": ["/breeding/<id>/delete"],
                "permission_type": PermissionType.DELETE
            },
            "export": {
                "name_ar": "تصدير تقارير التربية",
                "name_en": "Export breeding reports",
                "routes": ["/breeding/export", "/reports/breeding/export"],
                "permission_type": PermissionType.EXPORT
            }
        }
    },
    
    "handler_reports": {
        "name_ar": "تقارير السائسين",
        "name_en": "Handler Reports",
        "icon": "fa-file-alt",
        "permissions": {
            "view": {
                "name_ar": "عرض تقارير السائسين",
                "name_en": "View handler reports",
                "routes": ["/handler/reports", "/pm/handler-reports"],
                "permission_type": PermissionType.VIEW
            },
            "approve": {
                "name_ar": "مراجعة والموافقة على تقارير السائسين",
                "name_en": "Review and approve handler reports",
                "routes": ["/handler/reports/<id>/approve"],
                "permission_type": PermissionType.APPROVE
            },
            "export": {
                "name_ar": "تصدير تقارير السائسين",
                "name_en": "Export handler reports",
                "routes": ["/handler/reports/export"],
                "permission_type": PermissionType.EXPORT
            }
        }
    },
    
    "tasks": {
        "name_ar": "إدارة المهام",
        "name_en": "Task Management",
        "icon": "fa-tasks",
        "permissions": {
            "view": {
                "name_ar": "عرض المهام",
                "name_en": "View tasks",
                "routes": ["/tasks", "/pm/tasks"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إنشاء مهمة جديدة",
                "name_en": "Create new task",
                "routes": ["/tasks/new", "/tasks/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل المهام",
                "name_en": "Edit tasks",
                "routes": ["/tasks/<id>/edit"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف المهام",
                "name_en": "Delete tasks",
                "routes": ["/tasks/<id>/delete"],
                "permission_type": PermissionType.DELETE
            },
            "assign": {
                "name_ar": "تعيين مهمة لموظف",
                "name_en": "Assign task to employee",
                "routes": ["/tasks/<id>/assign"],
                "permission_type": PermissionType.ASSIGN
            },
            "approve": {
                "name_ar": "الموافقة على إنجاز المهام",
                "name_en": "Approve task completion",
                "routes": ["/tasks/<id>/approve"],
                "permission_type": PermissionType.APPROVE
            }
        }
    },
    
    "accounts": {
        "name_ar": "إدارة الحسابات",
        "name_en": "Account Management",
        "icon": "fa-user-cog",
        "permissions": {
            "view": {
                "name_ar": "عرض حسابات المستخدمين",
                "name_en": "View user accounts",
                "routes": ["/admin/accounts", "/admin/account-management"],
                "permission_type": PermissionType.VIEW
            },
            "create": {
                "name_ar": "إنشاء حساب مستخدم جديد",
                "name_en": "Create new user account",
                "routes": ["/admin/accounts/create"],
                "permission_type": PermissionType.CREATE
            },
            "edit": {
                "name_ar": "تعديل حساب المستخدم",
                "name_en": "Edit user account",
                "routes": ["/admin/accounts/<id>/edit"],
                "permission_type": PermissionType.EDIT
            },
            "delete": {
                "name_ar": "حذف حساب مستخدم",
                "name_en": "Delete user account",
                "routes": ["/admin/accounts/<id>/delete"],
                "permission_type": PermissionType.DELETE
            }
        }
    },
    
    "reports": {
        "name_ar": "التقارير والإحصائيات",
        "name_en": "Reports & Statistics",
        "icon": "fa-chart-bar",
        "subsections": {
            "attendance_reports": {
                "name_ar": "تقارير الحضور اليومية",
                "name_en": "Daily Attendance Reports",
                "permissions": {
                    "view": {
                        "name_ar": "عرض تقارير الحضور",
                        "name_en": "View attendance reports",
                        "routes": ["/reports/attendance/daily"],
                        "permission_type": PermissionType.VIEW
                    },
                    "export": {
                        "name_ar": "تصدير تقارير الحضور",
                        "name_en": "Export attendance reports",
                        "routes": ["/reports/attendance/export"],
                        "permission_type": PermissionType.EXPORT
                    }
                }
            },
            "training_reports": {
                "name_ar": "تقارير التدريب",
                "name_en": "Training Reports",
                "permissions": {
                    "view": {
                        "name_ar": "عرض تقارير التدريب اليومية",
                        "name_en": "View daily training reports",
                        "routes": ["/reports/training/daily"],
                        "permission_type": PermissionType.VIEW
                    },
                    "export": {
                        "name_ar": "تصدير تقارير التدريب",
                        "name_en": "Export training reports",
                        "routes": ["/reports/training/export"],
                        "permission_type": PermissionType.EXPORT
                    }
                }
            },
            "veterinary_reports": {
                "name_ar": "التقارير الطبية",
                "name_en": "Veterinary Reports",
                "permissions": {
                    "view": {
                        "name_ar": "عرض التقارير الطبية",
                        "name_en": "View veterinary reports",
                        "routes": ["/reports/veterinary/daily", "/reports/veterinary/unified"],
                        "permission_type": PermissionType.VIEW
                    },
                    "export": {
                        "name_ar": "تصدير التقارير الطبية",
                        "name_en": "Export veterinary reports",
                        "routes": ["/reports/veterinary/export"],
                        "permission_type": PermissionType.EXPORT
                    }
                }
            },
            "breeding_reports": {
                "name_ar": "تقارير التربية",
                "name_en": "Breeding Reports",
                "subsections": {
                    "feeding": {
                        "name_ar": "تقارير التغذية",
                        "name_en": "Feeding Reports",
                        "permissions": {
                            "view": {
                                "name_ar": "عرض تقارير التغذية",
                                "name_en": "View feeding reports",
                                "routes": ["/reports/breeding/feeding"],
                                "permission_type": PermissionType.VIEW
                            },
                            "export": {
                                "name_ar": "تصدير تقارير التغذية",
                                "name_en": "Export feeding reports",
                                "routes": ["/reports/breeding/feeding/export"],
                                "permission_type": PermissionType.EXPORT
                            }
                        }
                    },
                    "checkup": {
                        "name_ar": "تقارير الفحص اليومي",
                        "name_en": "Daily Checkup Reports",
                        "permissions": {
                            "view": {
                                "name_ar": "عرض تقارير الفحص",
                                "name_en": "View checkup reports",
                                "routes": ["/reports/breeding/checkup"],
                                "permission_type": PermissionType.VIEW
                            },
                            "export": {
                                "name_ar": "تصدير تقارير الفحص",
                                "name_en": "Export checkup reports",
                                "routes": ["/reports/breeding/checkup/export"],
                                "permission_type": PermissionType.EXPORT
                            }
                        }
                    },
                    "caretaker": {
                        "name_ar": "تقارير المربي اليومية",
                        "name_en": "Caretaker Daily Reports",
                        "permissions": {
                            "view": {
                                "name_ar": "عرض تقارير المربي",
                                "name_en": "View caretaker reports",
                                "routes": ["/reports/breeding/caretaker"],
                                "permission_type": PermissionType.VIEW
                            },
                            "export": {
                                "name_ar": "تصدير تقارير المربي",
                                "name_en": "Export caretaker reports",
                                "routes": ["/reports/breeding/caretaker/export"],
                                "permission_type": PermissionType.EXPORT
                            }
                        }
                    }
                }
            }
        }
    },
    
    "admin": {
        "name_ar": "لوحة التحكم الإدارية",
        "name_en": "Admin Dashboard",
        "icon": "fa-cogs",
        "permissions": {
            "view": {
                "name_ar": "الوصول إلى لوحة التحكم الإدارية",
                "name_en": "Access admin dashboard",
                "routes": ["/admin", "/admin/dashboard"],
                "permission_type": PermissionType.VIEW
            },
            "permissions": {
                "name_ar": "إدارة الصلاحيات",
                "name_en": "Manage permissions",
                "routes": ["/admin/permissions"],
                "permission_type": PermissionType.EDIT
            },
            "backup": {
                "name_ar": "إدارة النسخ الاحتياطي",
                "name_en": "Manage backups",
                "routes": ["/admin/backup"],
                "permission_type": PermissionType.VIEW
            }
        }
    }
}


def get_all_permissions_flat():
    """
    Get a flattened list of all permissions in the system
    Returns: List of dicts with section, subsection, permission_key, name_ar, name_en, permission_type
    """
    permissions_list = []
    
    def process_section(section_key, section_data, subsection_path=""):
        """
        Recursively process sections and their subsections
        
        Args:
            section_key: Top-level section name (e.g., 'reports', 'admin')
            section_data: Section configuration dictionary
            subsection_path: Accumulated path for nested subsections (e.g., 'breeding_reports.feeding')
        """
        if "permissions" in section_data:
            for perm_key, perm_data in section_data["permissions"].items():
                permissions_list.append({
                    "section": section_key,
                    "subsection": subsection_path,
                    "permission_key": perm_key,
                    "name_ar": perm_data["name_ar"],
                    "name_en": perm_data["name_en"],
                    "permission_type": perm_data["permission_type"],
                    "routes": perm_data.get("routes", [])
                })
        
        if "subsections" in section_data:
            for subsection_key, subsection_data in section_data["subsections"].items():
                # Build the full subsection path
                new_subsection_path = f"{subsection_path}.{subsection_key}" if subsection_path else subsection_key
                process_section(section_key, subsection_data, new_subsection_path)
    
    for section_key, section_data in PERMISSION_REGISTRY.items():
        process_section(section_key, section_data)
    
    return permissions_list


def get_sections_list():
    """
    Get a list of all main sections
    Returns: List of dicts with section_key, name_ar, name_en, icon
    """
    sections = []
    for key, data in PERMISSION_REGISTRY.items():
        sections.append({
            "section_key": key,
            "name_ar": data["name_ar"],
            "name_en": data["name_en"],
            "icon": data.get("icon", "fa-folder")
        })
    return sections


def get_section_permissions(section_key):
    """
    Get all permissions for a specific section
    """
    if section_key not in PERMISSION_REGISTRY:
        return []
    
    section_data = PERMISSION_REGISTRY[section_key]
    permissions = []
    
    def extract_permissions(data, parent_path=""):
        if "permissions" in data:
            for perm_key, perm_data in data["permissions"].items():
                permissions.append({
                    "permission_key": perm_key,
                    "subsection": parent_path,
                    "name_ar": perm_data["name_ar"],
                    "name_en": perm_data["name_en"],
                    "permission_type": perm_data["permission_type"],
                    "routes": perm_data.get("routes", [])
                })
        
        if "subsections" in data:
            for subsection_key, subsection_data in data["subsections"].items():
                new_path = f"{parent_path}.{subsection_key}" if parent_path else subsection_key
                extract_permissions(subsection_data, new_path)
    
    extract_permissions(section_data)
    return permissions
