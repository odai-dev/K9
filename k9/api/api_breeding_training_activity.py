"""
API endpoints for breeding training activity management
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import joinedload
from datetime import datetime, date
from k9.models.models import (
    db, BreedingTrainingActivity, Project, Dog, Employee, UserRole, 
    TrainingCategory, SocializationType, BallWorkType
)
from k9.utils.permission_decorators import require_sub_permission
from k9.utils.utils import get_user_assigned_projects

bp = Blueprint('api_breeding_training_activity', __name__)

@bp.route('/api/breeding/training-activity', methods=['POST'])
@login_required
@require_sub_permission('Breeding', 'تدريب — أنشطة يومية', 'CREATE')
def create_training_activity():
    """Create new breeding training activity"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['session_date', 'dog_id', 'trainer_id', 'category', 'subject', 'duration', 'success_rating']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'الحقل المطلوب مفقود: {field}'}), 400
        
        # Handle optional project_id (allow entries without project assignment)
        project_id = data.get('project_id')
        if not project_id or project_id == '' or project_id == 'null':
            project_id = None
            data['project_id'] = None
        
        # Verify project access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if data.get('project_id'):  # Only check if project is assigned
                assigned_projects = get_user_assigned_projects(current_user)
                project_ids = [str(p.id) for p in assigned_projects]
                if str(data['project_id']) not in project_ids:
                    return jsonify({'error': 'غير مصرح بالوصول إلى هذا المشروع'}), 403
        
        # Verify entities exist
        if data.get('project_id'):
            try:
                project = Project.query.get(data['project_id'])
                if not project:
                    return jsonify({'error': 'المشروع المحدد غير موجود'}), 404
            except Exception as e:
                return jsonify({'error': 'معرف المشروع غير صالح'}), 400
        
        try:
            dog = Dog.query.get(data['dog_id'])
            if not dog:
                return jsonify({'error': 'الكلب المحدد غير موجود'}), 404
        except Exception as e:
            return jsonify({'error': 'معرف الكلب غير صالح'}), 400
            
        try:
            trainer = Employee.query.get(data['trainer_id'])
            if not trainer:
                return jsonify({'error': 'المدرب المحدد غير موجود'}), 404
        except Exception as e:
            return jsonify({'error': 'معرف المدرب غير صالح'}), 400
        
        # Parse and validate session_date
        try:
            if isinstance(data['session_date'], str):
                session_date = datetime.fromisoformat(data['session_date'].replace('Z', '+00:00'))
            else:
                session_date = data['session_date']
        except (ValueError, TypeError) as e:
            return jsonify({'error': 'تاريخ الجلسة غير صالح'}), 400
        
        # Validate session date is not in future
        if session_date.date() > date.today():
            return jsonify({'error': 'لا يمكن أن يكون تاريخ التدريب في المستقبل'}), 400
        
        # Validate category
        try:
            category = TrainingCategory(data['category'])
        except ValueError:
            return jsonify({'error': 'فئة التدريب غير صالحة'}), 400
        
        # Validate subtypes if provided
        subtype_socialization = None
        if data.get('subtype_socialization'):
            try:
                subtype_socialization = SocializationType(data['subtype_socialization'])
            except ValueError:
                return jsonify({'error': 'نوع التطبيع غير صالح'}), 400
        
        subtype_ball = None
        if data.get('subtype_ball'):
            try:
                subtype_ball = BallWorkType(data['subtype_ball'])
            except ValueError:
                return jsonify({'error': 'نوع تدريب الكرة غير صالح'}), 400
        
        # Validate duration (positive integer)
        try:
            duration = int(data['duration'])
            if duration <= 0:
                return jsonify({'error': 'مدة التدريب يجب أن تكون أكبر من صفر'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'مدة التدريب غير صالحة'}), 400
        
        # Validate duration_days (optional, positive integer)
        duration_days = None
        if data.get('duration_days'):
            try:
                duration_days = int(data['duration_days'])
                if duration_days <= 0:
                    return jsonify({'error': 'مدة التدريب بالأيام يجب أن تكون أكبر من صفر'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'مدة التدريب بالأيام غير صالحة'}), 400
        
        # Validate success rating (1-5)
        try:
            success_rating = int(data['success_rating'])
            if success_rating < 1 or success_rating > 5:
                return jsonify({'error': 'تقييم النجاح يجب أن يكون بين 1 و 5'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'تقييم النجاح غير صالح'}), 400
        
        # Create new training activity
        training_activity = BreedingTrainingActivity()
        training_activity.project_id = project_id
        training_activity.dog_id = data['dog_id']
        training_activity.trainer_id = data['trainer_id']
        training_activity.session_date = session_date
        training_activity.category = category
        training_activity.subtype_socialization = subtype_socialization
        training_activity.subtype_ball = subtype_ball
        training_activity.subject = data['subject']
        training_activity.duration = duration
        training_activity.duration_days = duration_days
        training_activity.success_rating = success_rating
        training_activity.location = data.get('location')
        training_activity.weather_conditions = data.get('weather_conditions')
        training_activity.equipment_used = data.get('equipment_used', [])
        training_activity.notes = data.get('notes')
        training_activity.created_by_user_id = current_user.id
        
        db.session.add(training_activity)
        db.session.commit()
        
        return jsonify({
            'message': 'تم إنشاء نشاط التدريب بنجاح',
            'id': str(training_activity.id)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f'Training activity creation error: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'حدث خطأ في النظام: {str(e)}'}), 500


@bp.route('/api/breeding/training-activity/list')
@login_required
@require_sub_permission('Breeding', 'تدريب — أنشطة يومية', 'VIEW')
def list_training_activities():
    """List training activities with filters and KPIs"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        project_id = request.args.get('project_id')
        dog_id = request.args.get('dog_id')
        trainer_id = request.args.get('trainer_id')
        category = request.args.get('category')
        subtype_socialization = request.args.get('subtype_socialization')
        subtype_ball = request.args.get('subtype_ball')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        duration_min = request.args.get('duration_min', type=int)
        duration_max = request.args.get('duration_max', type=int)
        
        # Base query with relationships
        query = BreedingTrainingActivity.query.options(
            joinedload(BreedingTrainingActivity.project),
            joinedload(BreedingTrainingActivity.dog),
            joinedload(BreedingTrainingActivity.trainer)
        )
        
        # Apply user access restrictions
        if current_user.role == UserRole.GENERAL_ADMIN:
            # Admin can see all activities
            pass
        else:
            # PROJECT_MANAGER can see activities from assigned projects + activities without projects
            assigned_projects = get_user_assigned_projects(current_user)
            if not assigned_projects:
                # If no assigned projects, only show activities without projects
                query = query.filter(BreedingTrainingActivity.project_id.is_(None))
            else:
                # Show activities from assigned projects OR activities without projects
                project_ids = [p.id for p in assigned_projects]
                query = query.filter(
                    or_(
                        BreedingTrainingActivity.project_id.in_(project_ids),
                        BreedingTrainingActivity.project_id.is_(None)
                    )
                )
        
        # Apply filters
        if project_id:
            if project_id == 'no_project':
                query = query.filter(BreedingTrainingActivity.project_id.is_(None))
            else:
                query = query.filter(BreedingTrainingActivity.project_id == project_id)
        
        if dog_id:
            query = query.filter(BreedingTrainingActivity.dog_id == dog_id)
            
        if trainer_id:
            query = query.filter(BreedingTrainingActivity.trainer_id == trainer_id)
            
        if category:
            query = query.filter(BreedingTrainingActivity.category == TrainingCategory(category))
            
        if subtype_socialization:
            query = query.filter(BreedingTrainingActivity.subtype_socialization == SocializationType(subtype_socialization))
            
        if subtype_ball:
            query = query.filter(BreedingTrainingActivity.subtype_ball == BallWorkType(subtype_ball))
        
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                query = query.filter(func.date(BreedingTrainingActivity.session_date) >= date_from_obj)
            except ValueError:
                return jsonify({'error': 'تاريخ البداية غير صالح'}), 400
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                query = query.filter(func.date(BreedingTrainingActivity.session_date) <= date_to_obj)
            except ValueError:
                return jsonify({'error': 'تاريخ النهاية غير صالح'}), 400
                
        if duration_min is not None:
            query = query.filter(BreedingTrainingActivity.duration >= duration_min)
            
        if duration_max is not None:
            query = query.filter(BreedingTrainingActivity.duration <= duration_max)
        
        # Execute query with pagination
        paginated_result = query.order_by(BreedingTrainingActivity.session_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        activities = paginated_result.items
        
        # Build activities list with Arabic labels
        activities_data = []
        for activity in activities:
            activity_data = {
                'id': str(activity.id),
                'session_date': activity.session_date.isoformat(),
                'dog_id': str(activity.dog_id),
                'dog_name': activity.dog.name if activity.dog else '',
                'trainer_id': str(activity.trainer_id),
                'trainer_name': activity.trainer.name if activity.trainer else '',
                'project_id': str(activity.project_id) if activity.project_id else None,
                'project_name': activity.project.name if activity.project else 'بدون مشروع',
                'category': activity.category.value,
                'subtype_socialization': activity.subtype_socialization.value if activity.subtype_socialization else None,
                'subtype_ball': activity.subtype_ball.value if activity.subtype_ball else None,
                'subject': activity.subject,
                'duration': activity.duration,
                'success_rating': activity.success_rating,
                'location': activity.location,
                'weather_conditions': activity.weather_conditions,
                'equipment_used': activity.equipment_used or [],
                'notes': activity.notes,
                'created_at': activity.created_at.isoformat()
            }
            activities_data.append(activity_data)
        
        # Calculate KPIs
        # Total activities
        total_activities = query.count()
        
        # Average success rating
        avg_rating_result = query.with_entities(func.avg(BreedingTrainingActivity.success_rating)).scalar()
        avg_rating = round(float(avg_rating_result), 1) if avg_rating_result else 0
        
        # Total duration
        total_duration_result = query.with_entities(func.sum(BreedingTrainingActivity.duration)).scalar()
        total_duration = int(total_duration_result) if total_duration_result else 0
        
        # Unique dogs trained
        unique_dogs = query.with_entities(func.count(func.distinct(BreedingTrainingActivity.dog_id))).scalar() or 0
        
        # Unique trainers
        unique_trainers = query.with_entities(func.count(func.distinct(BreedingTrainingActivity.trainer_id))).scalar() or 0
        
        # Category breakdown
        category_breakdown = {}
        category_results = db.session.query(
            BreedingTrainingActivity.category,
            func.count(BreedingTrainingActivity.id).label('count')
        ).filter(
            BreedingTrainingActivity.id.in_([activity.id for activity in activities])
        ).group_by(BreedingTrainingActivity.category).all()
        
        for category_result in category_results:
            category_breakdown[category_result.category.value] = category_result.count
        
        # Subtype breakdown
        subtype_socialization_breakdown = {}
        socialization_results = db.session.query(
            BreedingTrainingActivity.subtype_socialization,
            func.count(BreedingTrainingActivity.id).label('count')
        ).filter(
            and_(
                BreedingTrainingActivity.id.in_([activity.id for activity in activities]),
                BreedingTrainingActivity.subtype_socialization.is_not(None)
            )
        ).group_by(BreedingTrainingActivity.subtype_socialization).all()
        
        for subtype_result in socialization_results:
            subtype_socialization_breakdown[subtype_result.subtype_socialization.value] = subtype_result.count
        
        subtype_ball_breakdown = {}
        ball_results = db.session.query(
            BreedingTrainingActivity.subtype_ball,
            func.count(BreedingTrainingActivity.id).label('count')
        ).filter(
            and_(
                BreedingTrainingActivity.id.in_([activity.id for activity in activities]),
                BreedingTrainingActivity.subtype_ball.is_not(None)
            )
        ).group_by(BreedingTrainingActivity.subtype_ball).all()
        
        for subtype_result in ball_results:
            subtype_ball_breakdown[subtype_result.subtype_ball.value] = subtype_result.count
        
        return jsonify({
            'items': activities_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated_result.total,
                'pages': paginated_result.pages,
                'has_next': paginated_result.has_next,
                'has_prev': paginated_result.has_prev
            },
            'kpis': {
                'total_activities': total_activities,
                'unique_dogs': unique_dogs,
                'unique_trainers': unique_trainers,
                'total_duration_minutes': total_duration,
                'avg_success_rating': avg_rating,
                'category_breakdown': category_breakdown,
                'subtype_socialization_breakdown': subtype_socialization_breakdown,
                'subtype_ball_breakdown': subtype_ball_breakdown
            }
        })
        
    except Exception as e:
        print(f'Error listing training activities: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'حدث خطأ في تحميل البيانات: {str(e)}'}), 500


@bp.route('/api/breeding/training-activity/<activity_id>')
@login_required
@require_sub_permission('Breeding', 'تدريب — أنشطة يومية', 'VIEW')
def get_training_activity(activity_id):
    """Get single training activity by ID"""
    try:
        activity = BreedingTrainingActivity.query.options(
            joinedload(BreedingTrainingActivity.project),
            joinedload(BreedingTrainingActivity.dog),
            joinedload(BreedingTrainingActivity.trainer)
        ).get(activity_id)
        
        if not activity:
            return jsonify({'error': 'نشاط التدريب غير موجود'}), 404
        
        # Check access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if activity.project_id:
                assigned_projects = get_user_assigned_projects(current_user)
                project_ids = [str(p.id) for p in assigned_projects]
                if str(activity.project_id) not in project_ids:
                    return jsonify({'error': 'ليس لديك صلاحية للوصول إلى هذا النشاط'}), 403
        
        activity_data = {
            'id': str(activity.id),
            'session_date': activity.session_date.isoformat(),
            'dog_id': str(activity.dog_id),
            'dog_name': activity.dog.name if activity.dog else '',
            'trainer_id': str(activity.trainer_id),
            'trainer_name': activity.trainer.name if activity.trainer else '',
            'project_id': str(activity.project_id) if activity.project_id else None,
            'project_name': activity.project.name if activity.project else 'بدون مشروع',
            'category': activity.category.value,
            'subtype_socialization': activity.subtype_socialization.value if activity.subtype_socialization else None,
            'subtype_ball': activity.subtype_ball.value if activity.subtype_ball else None,
            'subject': activity.subject,
            'duration': activity.duration,
            'duration_days': activity.duration_days,
            'success_rating': activity.success_rating,
            'location': activity.location,
            'weather_conditions': activity.weather_conditions,
            'equipment_used': activity.equipment_used or [],
            'notes': activity.notes,
            'created_at': activity.created_at.isoformat(),
            'updated_at': activity.updated_at.isoformat()
        }
        
        return jsonify(activity_data)
        
    except Exception as e:
        print(f'Error getting training activity: {e}')
        return jsonify({'error': f'حدث خطأ في تحميل البيانات: {str(e)}'}), 500


@bp.route('/api/breeding/training-activity/<activity_id>', methods=['PUT'])
@login_required
@require_sub_permission('Breeding', 'تدريب — أنشطة يومية', 'EDIT')
def update_training_activity(activity_id):
    """Update existing training activity"""
    try:
        activity = BreedingTrainingActivity.query.get(activity_id)
        if not activity:
            return jsonify({'error': 'نشاط التدريب غير موجود'}), 404
        
        # Check access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if activity.project_id:
                assigned_projects = get_user_assigned_projects(current_user)
                project_ids = [str(p.id) for p in assigned_projects]
                if str(activity.project_id) not in project_ids:
                    return jsonify({'error': 'ليس لديك صلاحية لتعديل هذا النشاط'}), 403
        
        data = request.get_json()
        
        # Update fields if provided
        if 'subject' in data:
            activity.subject = data['subject']
            
        if 'duration' in data:
            try:
                duration = int(data['duration'])
                if duration <= 0:
                    return jsonify({'error': 'مدة التدريب يجب أن تكون أكبر من صفر'}), 400
                activity.duration = duration
            except (ValueError, TypeError):
                return jsonify({'error': 'مدة التدريب غير صالحة'}), 400
        
        if 'duration_days' in data:
            if data['duration_days']:
                try:
                    duration_days = int(data['duration_days'])
                    if duration_days <= 0:
                        return jsonify({'error': 'مدة التدريب بالأيام يجب أن تكون أكبر من صفر'}), 400
                    activity.duration_days = duration_days
                except (ValueError, TypeError):
                    return jsonify({'error': 'مدة التدريب بالأيام غير صالحة'}), 400
            else:
                activity.duration_days = None
        
        if 'success_rating' in data:
            try:
                success_rating = int(data['success_rating'])
                if success_rating < 1 or success_rating > 5:
                    return jsonify({'error': 'تقييم النجاح يجب أن يكون بين 1 و 5'}), 400
                activity.success_rating = success_rating
            except (ValueError, TypeError):
                return jsonify({'error': 'تقييم النجاح غير صالح'}), 400
        
        if 'category' in data:
            try:
                activity.category = TrainingCategory(data['category'])
            except ValueError:
                return jsonify({'error': 'فئة التدريب غير صالحة'}), 400
        
        if 'subtype_socialization' in data:
            if data['subtype_socialization']:
                try:
                    activity.subtype_socialization = SocializationType(data['subtype_socialization'])
                except ValueError:
                    return jsonify({'error': 'نوع التطبيع غير صالح'}), 400
            else:
                activity.subtype_socialization = None
        
        if 'subtype_ball' in data:
            if data['subtype_ball']:
                try:
                    activity.subtype_ball = BallWorkType(data['subtype_ball'])
                except ValueError:
                    return jsonify({'error': 'نوع تدريب الكرة غير صالح'}), 400
            else:
                activity.subtype_ball = None
        
        if 'location' in data:
            activity.location = data['location']
            
        if 'weather_conditions' in data:
            activity.weather_conditions = data['weather_conditions']
            
        if 'equipment_used' in data:
            activity.equipment_used = data['equipment_used']
            
        if 'notes' in data:
            activity.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({'message': 'تم تحديث نشاط التدريب بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        print(f'Training activity update error: {e}')
        return jsonify({'error': f'حدث خطأ في تحديث البيانات: {str(e)}'}), 500


@bp.route('/api/breeding/training-activity/<activity_id>', methods=['DELETE'])
@login_required
@require_sub_permission('Breeding', 'تدريب — أنشطة يومية', 'DELETE')
def delete_training_activity(activity_id):
    """Delete training activity"""
    try:
        activity = BreedingTrainingActivity.query.get(activity_id)
        if not activity:
            return jsonify({'error': 'نشاط التدريب غير موجود'}), 404
        
        # Check access for PROJECT_MANAGER
        if current_user.role == UserRole.PROJECT_MANAGER:
            if activity.project_id:
                assigned_projects = get_user_assigned_projects(current_user)
                project_ids = [str(p.id) for p in assigned_projects]
                if str(activity.project_id) not in project_ids:
                    return jsonify({'error': 'ليس لديك صلاحية لحذف هذا النشاط'}), 403
        
        db.session.delete(activity)
        db.session.commit()
        
        return jsonify({'message': 'تم حذف نشاط التدريب بنجاح'})
        
    except Exception as e:
        db.session.rollback()
        print(f'Training activity deletion error: {e}')
        return jsonify({'error': f'حدث خطأ في حذف البيانات: {str(e)}'}), 500