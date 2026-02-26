"""
K9 Test Configuration — PostgreSQL App Factory

Fully isolated test environment:
  - PostgreSQL (TEST_DATABASE_URL or DATABASE_URL) — tables are dropped/recreated per session
  - WTF_CSRF_ENABLED=False → no CSRF tokens needed in tests
  - Tables truncated before each test function for clean isolation
"""
import os
import uuid
import pytest
from datetime import date, datetime, timedelta

# ── import after env is set ──────────────────────────────────────────────────
from sqlalchemy.pool import StaticPool  # kept for import compatibility
from app import app as flask_app, db as _db
from werkzeug.security import generate_password_hash


# ─────────────────────────────────────────────────
# App / DB session-level setup
# ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def app():
    """Create application configured for testing against a PostgreSQL test database."""
    test_db_url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not test_db_url:
        pytest.skip("No database URL set. Set TEST_DATABASE_URL or DATABASE_URL to run tests.")

    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=test_db_url,
        SQLALCHEMY_ENGINE_OPTIONS={
            "pool_recycle": 300,
            "pool_pre_ping": True,
        },
        WTF_CSRF_ENABLED=False,
        WTF_CSRF_CHECK_DEFAULT=False,
        SECRET_KEY="test-secret-key-not-for-production",
        SERVER_NAME=None,
    )
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Database bound to the session-scoped app."""
    return _db


@pytest.fixture(scope="function", autouse=True)
def clean_db(app, db):
    """
    Wipe all table data before each test, then yield, then commit nothing.
    This is simpler and more reliable than savepoint-rollback with SQLite.
    """
    # Delete in reverse dependency order to avoid FK violations
    _delete_all_data(db)
    
    # Clear PermissionService cache to avoid test isolation failures
    try:
        from k9.services.permission_service import PermissionService
        PermissionService._cache = {}
    except ImportError:
        pass
        
    yield
    _delete_all_data(db)


def _delete_all_data(db):
    """Truncate all tables in safe order using PostgreSQL syntax."""
    from sqlalchemy import text, inspect
    with db.engine.connect() as conn:
        conn.execute(text("SET session_replication_role = replica"))  # Disable FK checks
        inspector = inspect(db.engine)
        for table_name in reversed(inspector.get_table_names()):
            conn.execute(text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'))
        conn.execute(text("SET session_replication_role = DEFAULT"))  # Re-enable FK checks
        conn.commit()


@pytest.fixture(scope="function")
def db_session(app, clean_db):
    """Provide a database session for a single test."""
    yield _db.session
    _db.session.remove()


@pytest.fixture(scope="function")
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


# ─────────────────────────────────────────────────
# Authenticated client helpers
# ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def auth_client(client, admin_user, app):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user.id)
        sess["_fresh"] = True
        sess["admin_mode"] = "general_admin"
        sess["user_permissions"] = ["*"]  # Force all permissions in session cache
    return client


@pytest.fixture(scope="function")
def pm_client(client, pm_user, app):
    """HTTP client with an active PM session."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(pm_user.id)
        sess["_fresh"] = True
        sess["user_permissions"] = ["pm.*", "projects.*", "dogs.*", "reports.*"]
    return client


@pytest.fixture(scope="function")
def handler_client(client, handler_user, app):
    """HTTP client with an active handler session."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(handler_user.id)
        sess["_fresh"] = True
        sess["user_permissions"] = ["handler_daily.*", "notifications.view", "profile.view"]
    return client


# ─────────────────────────────────────────────────
# Unique value helpers (avoid UNIQUE constraint failures)
# ─────────────────────────────────────────────────

def _uid():
    """Short unique suffix for phone numbers / IDs."""
    return uuid.uuid4().hex[:6]


# ─────────────────────────────────────────────────
# Core entity fixtures
# ─────────────────────────────────────────────────

@pytest.fixture(scope="function")
def admin_employee(db_session, app):
    from k9.models.models import Employee, EmployeeRole
    emp = Employee(
        name="مدير النظام",
        employee_id=f"EMP-ADMIN-{_uid()}",
        role=EmployeeRole.PROJECT_MANAGER,
        phone=f"711{_uid()}",
        email=f"admin_{_uid()}@k9test.com",
        hire_date=date(2020, 1, 1),
        is_active=True,
    )
    _db.session.add(emp)
    _db.session.commit()
    return emp


@pytest.fixture(scope="function")
def admin_user(db_session, admin_employee, app):
    from k9.models.models import User, UserRole
    from k9.models.permissions_v2 import Role, UserRoleAssignment, RoleType
    user = User(
        username=f"admin_{_uid()}",
        email=f"admin_{_uid()}@k9test.com",
        password_hash=generate_password_hash("Test1234!"),
        role=UserRole.GENERAL_ADMIN,
        full_name="مدير النظام",
        phone=f"799{_uid()}",
        active=True,
        employee_id=admin_employee.id,
    )
    _db.session.add(user)
    _db.session.commit()

    # Seed V2 role and assignment
    role = Role.query.filter_by(name=RoleType.GENERAL_ADMIN).first()
    if not role:
        role = Role(name=RoleType.GENERAL_ADMIN, name_ar="مشرف عام", is_system=True, is_active=True)
        _db.session.add(role)
        _db.session.commit()
    
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        is_active=True
    )
    _db.session.add(assignment)
    _db.session.commit()

    return user


@pytest.fixture(scope="function")
def pm_employee(db_session, app):
    from k9.models.models import Employee, EmployeeRole
    emp = Employee(
        name="مدير مشروع",
        employee_id=f"EMP-PM-{_uid()}",
        role=EmployeeRole.PROJECT_MANAGER,
        phone=f"712{_uid()}",
        email=f"pm_{_uid()}@k9test.com",
        hire_date=date(2020, 6, 1),
        is_active=True,
    )
    _db.session.add(emp)
    _db.session.commit()
    return emp


@pytest.fixture(scope="function")
def test_project(db_session, pm_employee, app):
    from k9.models.models import Project, ProjectStatus
    project = Project(
        name="مشروع الاختبار",
        code=f"TST-{_uid()}",
        description="مشروع مخصص للاختبارات",
        status=ProjectStatus.ACTIVE,
        start_date=date.today() - timedelta(days=60),
        project_manager_id=pm_employee.id,
    )
    _db.session.add(project)
    _db.session.commit()
    return project


@pytest.fixture(scope="function")
def pm_user(db_session, pm_employee, test_project, app):
    from k9.models.models import User, UserRole
    from k9.models.permissions_v2 import Role, UserRoleAssignment, RoleType
    user = User(
        username=f"pm_{_uid()}",
        email=f"pm_{_uid()}@k9test.com",
        password_hash=generate_password_hash("Test1234!"),
        role=UserRole.PROJECT_MANAGER,
        full_name="مدير مشروع",
        phone=f"713{_uid()}",
        active=True,
        employee_id=pm_employee.id,
        project_id=test_project.id,
    )
    _db.session.add(user)
    _db.session.commit()

    # Seed V2 role and assignment
    role = Role.query.filter_by(name=RoleType.PROJECT_MANAGER).first()
    if not role:
        role = Role(name=RoleType.PROJECT_MANAGER, name_ar="مدير مشروع", is_system=True, is_active=True)
        _db.session.add(role)
        _db.session.commit()
    
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        project_id=test_project.id,
        is_active=True
    )
    _db.session.add(assignment)
    _db.session.commit()

    return user


@pytest.fixture(scope="function")
def handler_employee(db_session, app):
    from k9.models.models import Employee, EmployeeRole
    emp = Employee(
        name="سائس الكلاب",
        employee_id=f"EMP-HDL-{_uid()}",
        role=EmployeeRole.HANDLER,
        phone=f"714{_uid()}",
        email=f"handler_{_uid()}@k9test.com",
        hire_date=date(2021, 3, 1),
        is_active=True,
    )
    _db.session.add(emp)
    _db.session.commit()
    return emp


@pytest.fixture(scope="function")
def test_dog(db_session, app):
    from k9.models.models import Dog, DogGender, DogStatus
    dog = Dog(
        name="ريكس",
        code=f"K9-{_uid()}",
        breed="جيرمن شيبرد",
        gender=DogGender.MALE,
        birth_date=date(2021, 5, 15),
        current_status=DogStatus.ACTIVE,
    )
    _db.session.add(dog)
    _db.session.commit()
    return dog


@pytest.fixture(scope="function")
def test_dog_female(db_session, app):
    from k9.models.models import Dog, DogGender, DogStatus
    dog = Dog(
        name="لونا",
        code=f"K9F-{_uid()}",
        breed="جيرمن شيبرد",
        gender=DogGender.FEMALE,
        birth_date=date(2020, 3, 10),
        current_status=DogStatus.ACTIVE,
    )
    _db.session.add(dog)
    _db.session.commit()
    return dog


@pytest.fixture(scope="function")
def handler_user(db_session, handler_employee, test_project, test_dog, app):
    from k9.models.models import User, UserRole
    from k9.models.permissions_v2 import Role, UserRoleAssignment, RoleType
    user = User(
        username=f"handler_{_uid()}",
        email=f"handler_{_uid()}@k9test.com",
        password_hash=generate_password_hash("Test1234!"),
        role=UserRole.HANDLER,
        full_name="سائس الكلاب",
        phone=f"715{_uid()}",
        active=True,
        employee_id=handler_employee.id,
        project_id=test_project.id,
        dog_id=test_dog.id,
    )
    _db.session.add(user)
    _db.session.commit()

    # Seed V2 role and assignment
    role = Role.query.filter_by(name=RoleType.HANDLER).first()
    if not role:
        role = Role(name=RoleType.HANDLER, name_ar="سائس", is_system=True, is_active=True)
        _db.session.add(role)
        _db.session.commit()
    
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=role.id,
        project_id=test_project.id,
        is_active=True
    )
    _db.session.add(assignment)
    _db.session.commit()

    return user


@pytest.fixture(scope="function")
def vet_employee(db_session, app):
    from k9.models.models import Employee, EmployeeRole
    emp = Employee(
        name="الطبيب البيطري",
        employee_id=f"EMP-VET-{_uid()}",
        role=EmployeeRole.VET,
        phone=f"716{_uid()}",
        email=f"vet_{_uid()}@k9test.com",
        hire_date=date(2019, 1, 1),
        is_active=True,
    )
    _db.session.add(emp)
    _db.session.commit()
    return emp


@pytest.fixture(scope="function")
def test_shift(db_session, app):
    from k9.models.models import Shift
    from datetime import time as t
    shift = Shift(
        name="الفترة الصباحية",
        start_time=t(6, 0),
        end_time=t(14, 0),
    )
    _db.session.add(shift)
    _db.session.commit()
    return shift


@pytest.fixture(scope="function")
def test_daily_schedule(db_session, test_project, admin_user, app):
    from k9.models.models_handler_daily import DailySchedule
    sched = DailySchedule(
        date=date.today(),
        project_id=test_project.id,
        created_by_user_id=admin_user.id,
        notes="جدول اختبار",
    )
    _db.session.add(sched)
    _db.session.commit()
    return sched


@pytest.fixture(scope="function")
def test_schedule_item(db_session, test_daily_schedule, handler_user, test_dog, test_shift, app):
    from k9.models.models_handler_daily import DailyScheduleItem, ScheduleItemStatus
    item = DailyScheduleItem(
        daily_schedule_id=test_daily_schedule.id,
        handler_user_id=handler_user.id,
        dog_id=test_dog.id,
        shift_id=test_shift.id,
        status=ScheduleItemStatus.PRESENT,
    )
    _db.session.add(item)
    _db.session.commit()
    return item


@pytest.fixture(scope="function")
def test_handler_report(db_session, handler_user, test_dog, test_project, test_schedule_item, app):
    from k9.models.models_handler_daily import (
        HandlerReport, HandlerReportHealth, HandlerReportCare,
        HandlerReportBehavior, ReportStatus,
    )
    report = HandlerReport(
        handler_user_id=handler_user.id,
        dog_id=test_dog.id,
        project_id=test_project.id,
        schedule_item_id=test_schedule_item.id,
        date=date.today(),
        status=ReportStatus.DRAFT,
        location="موقع الاختبار",
    )
    _db.session.add(report)
    _db.session.commit()

    health = HandlerReportHealth(report_id=report.id)
    _db.session.add(health)

    care = HandlerReportCare(report_id=report.id)
    _db.session.add(care)

    behavior = HandlerReportBehavior(report_id=report.id)
    _db.session.add(behavior)

    _db.session.commit()
    return report


@pytest.fixture(scope="function")
def test_submitted_report(db_session, test_handler_report, app):
    from k9.models.models_handler_daily import ReportStatus
    test_handler_report.status = ReportStatus.SUBMITTED
    test_handler_report.submitted_at = datetime.utcnow()
    _db.session.commit()
    return test_handler_report


@pytest.fixture(scope="function")
def test_vet_visit(db_session, test_dog, vet_employee, test_project, app):
    from k9.models.models import VeterinaryVisit, VisitType
    visit = VeterinaryVisit(
        dog_id=test_dog.id,
        vet_id=vet_employee.id,
        project_id=test_project.id,
        visit_type=VisitType.ROUTINE,
        visit_date=datetime.utcnow(),
        diagnosis="حالة صحية جيدة",
        treatment="لا يلزم علاج",
        status="PENDING_PM_REVIEW",
    )
    _db.session.add(visit)
    _db.session.commit()
    return visit


@pytest.fixture(scope="function")
def test_notification(db_session, handler_user, app):
    from k9.models.models_handler_daily import Notification, NotificationType
    notif = Notification(
        user_id=handler_user.id,
        type=NotificationType.REPORT_APPROVED,
        title="اختبار إشعار",
        message="هذا إشعار اختباري",
        read=False,
    )
    _db.session.add(notif)
    _db.session.commit()
    return notif