"""
مسارات إدارة المهام
Task Management Routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from k9.decorators import supervisor_required, handler_required
from k9.services.task_service import TaskService
from k9.models.models_handler_daily import Task, TaskStatus, TaskPriority
from k9.models.models import User, UserRole
from datetime import datetime

task_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


# ============================================================================
# Admin/PM Routes - Task Management
# ============================================================================

@task_bp.route('/admin')
@login_required
@supervisor_required
def admin_index():
    """قائمة المهام للمشرف"""
    # Get filter parameters
    status_filter = request.args.get('status')
    assigned_to_filter = request.args.get('assigned_to')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get tasks created by this user or all tasks (for admins)
    result = TaskService.get_user_tasks(
        user_id=str(current_user.id),
        status=TaskStatus[status_filter] if status_filter else None,
        include_created=True,  # Include tasks created by user
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    tasks = result.get('tasks', [])
    total_count = result.get('total_count', 0)
    
    # Get statistics
    stats = TaskService.get_task_statistics(
        user_id=str(current_user.id),
        include_created=True
    )
    
    # Get all handlers for filter dropdown
    handlers = User.query.filter_by(role=UserRole.HANDLER, active=True).all()
    
    return render_template('admin/tasks/index.html',
                         page_title='إدارة المهام',
                         tasks=tasks,
                         total_count=total_count,
                         stats=stats,
                         handlers=handlers,
                         current_page=page,
                         per_page=per_page,
                         TaskStatus=TaskStatus,
                         TaskPriority=TaskPriority)


@task_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
@supervisor_required
def admin_create():
    """إنشاء مهمة جديدة"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        assigned_to_user_id = request.form.get('assigned_to_user_id')
        priority = request.form.get('priority', 'MEDIUM')
        due_date_str = request.form.get('due_date')
        
        # Validate
        if not title or not assigned_to_user_id:
            flash('العنوان والمستخدم المحدد مطلوبان', 'danger')
            return redirect(request.url)
        
        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('تنسيق التاريخ غير صحيح', 'danger')
                return redirect(request.url)
        
        # Create task
        task, error = TaskService.create_task(
            title=title,
            description=description,
            assigned_to_user_id=assigned_to_user_id,
            created_by_user_id=str(current_user.id),
            priority=TaskPriority[priority],
            due_date=due_date
        )
        
        if error:
            flash(error, 'danger')
            return redirect(request.url)
        
        flash('تم إنشاء المهمة بنجاح وإرسال إشعار للسائس', 'success')
        return redirect(url_for('tasks.admin_index'))
    
    # GET - show form
    handlers = User.query.filter_by(role=UserRole.HANDLER, active=True).all()
    
    return render_template('admin/tasks/create.html',
                         page_title='إنشاء مهمة جديدة',
                         handlers=handlers,
                         TaskPriority=TaskPriority)


@task_bp.route('/admin/<task_id>')
@login_required
@supervisor_required
def admin_view(task_id):
    """عرض تفاصيل المهمة"""
    task = TaskService.get_task(task_id)
    if not task:
        flash('المهمة غير موجودة', 'danger')
        return redirect(url_for('tasks.admin_index'))
    
    return render_template('admin/tasks/view.html',
                         page_title=f'المهمة: {task.title}',
                         task=task,
                         TaskStatus=TaskStatus,
                         TaskPriority=TaskPriority)


@task_bp.route('/admin/<task_id>/edit', methods=['GET', 'POST'])
@login_required
@supervisor_required
def admin_edit(task_id):
    """تعديل مهمة"""
    task = TaskService.get_task(task_id)
    if not task:
        flash('المهمة غير موجودة', 'danger')
        return redirect(url_for('tasks.admin_index'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')
        status = request.form.get('status')
        due_date_str = request.form.get('due_date')
        
        # Parse due date
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('تنسيق التاريخ غير صحيح', 'danger')
                return redirect(request.url)
        
        # Update task
        _, error = TaskService.update_task(
            task_id=task_id,
            title=title,
            description=description,
            priority=TaskPriority[priority] if priority else None,
            status=TaskStatus[status] if status else None,
            due_date=due_date
        )
        
        if error:
            flash(error, 'danger')
            return redirect(request.url)
        
        flash('تم تحديث المهمة بنجاح', 'success')
        return redirect(url_for('tasks.admin_view', task_id=task_id))
    
    # GET - show form
    handlers = User.query.filter_by(role=UserRole.HANDLER, active=True).all()
    
    return render_template('admin/tasks/edit.html',
                         page_title=f'تعديل المهمة: {task.title}',
                         task=task,
                         handlers=handlers,
                         TaskStatus=TaskStatus,
                         TaskPriority=TaskPriority)


@task_bp.route('/admin/<task_id>/delete', methods=['POST'])
@login_required
@supervisor_required
def admin_delete(task_id):
    """حذف مهمة"""
    success, error = TaskService.delete_task(task_id)
    
    if error:
        flash(error, 'danger')
    else:
        flash('تم حذف المهمة بنجاح', 'success')
    
    return redirect(url_for('tasks.admin_index'))


# ============================================================================
# Handler Routes - My Tasks
# ============================================================================

@task_bp.route('/my-tasks')
@login_required
@handler_required
def handler_index():
    """قائمة مهام السائس"""
    # Get filter parameters
    status_filter = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get tasks assigned to this handler
    result = TaskService.get_user_tasks(
        user_id=str(current_user.id),
        status=TaskStatus[status_filter] if status_filter else None,
        include_created=False,  # Only assigned tasks
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    tasks = result.get('tasks', [])
    total_count = result.get('total_count', 0)
    
    # Get statistics
    stats = TaskService.get_task_statistics(
        user_id=str(current_user.id),
        include_created=False
    )
    
    return render_template('handler/tasks/index.html',
                         page_title='مهامي',
                         tasks=tasks,
                         total_count=total_count,
                         stats=stats,
                         current_page=page,
                         per_page=per_page,
                         TaskStatus=TaskStatus,
                         TaskPriority=TaskPriority)


@task_bp.route('/my-tasks/<task_id>')
@login_required
@handler_required
def handler_view(task_id):
    """عرض تفاصيل المهمة"""
    task = TaskService.get_task(task_id)
    if not task:
        flash('المهمة غير موجودة', 'danger')
        return redirect(url_for('tasks.handler_index'))
    
    # Check if this task is assigned to current user
    if str(task.assigned_to_user_id) != str(current_user.id):
        flash('غير مصرح لك بعرض هذه المهمة', 'danger')
        return redirect(url_for('tasks.handler_index'))
    
    return render_template('handler/tasks/view.html',
                         page_title=f'المهمة: {task.title}',
                         task=task,
                         TaskStatus=TaskStatus,
                         TaskPriority=TaskPriority)


@task_bp.route('/my-tasks/<task_id>/complete', methods=['POST'])
@login_required
@handler_required
def handler_complete(task_id):
    """إكمال مهمة"""
    _, error = TaskService.complete_task(
        task_id=task_id,
        user_id=str(current_user.id)
    )
    
    if error:
        flash(error, 'danger')
    else:
        flash('تم إكمال المهمة بنجاح', 'success')
    
    return redirect(url_for('tasks.handler_index'))


@task_bp.route('/my-tasks/<task_id>/start', methods=['POST'])
@login_required
@handler_required
def handler_start(task_id):
    """بدء العمل على مهمة"""
    task = TaskService.get_task(task_id)
    if not task:
        flash('المهمة غير موجودة', 'danger')
        return redirect(url_for('tasks.handler_index'))
    
    # Check if this task is assigned to current user
    if str(task.assigned_to_user_id) != str(current_user.id):
        flash('غير مصرح لك بتعديل هذه المهمة', 'danger')
        return redirect(url_for('tasks.handler_index'))
    
    _, error = TaskService.update_task(
        task_id=task_id,
        status=TaskStatus.IN_PROGRESS
    )
    
    if error:
        flash(error, 'danger')
    else:
        flash('تم بدء العمل على المهمة', 'success')
    
    return redirect(url_for('tasks.handler_view', task_id=task_id))
