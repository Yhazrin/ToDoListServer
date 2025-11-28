from flask import Blueprint, request, jsonify
from models import db, User, Task
from auth import token_required
from sqlalchemy.exc import IntegrityError

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户资料接口"""
    try:
        return jsonify({
            'success': True,
            'message': 'Profile retrieved successfully',
            'user': current_user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve profile: {str(e)}'
        }), 500

@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新当前用户资料接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        # 更新用户名（如果提供且不同）
        if 'username' in data:
            new_username = data['username'].strip()
            if new_username and new_username != current_user.username:
                # 检查新用户名是否已被使用
                existing_user = User.query.filter(User.username == new_username).first()
                if existing_user:
                    return jsonify({
                        'success': False,
                        'message': 'Username already exists'
                    }), 409
                current_user.username = new_username
        
        # 更新邮箱（如果提供且不同）
        if 'email' in data:
            new_email = data['email'].strip() if data['email'] else None
            if new_email != current_user.email:
                # 如果提供了新邮箱，检查是否已被使用
                if new_email:
                    existing_email = User.query.filter(User.email == new_email).first()
                    if existing_email:
                        return jsonify({
                            'success': False,
                            'message': 'Email already registered'
                        }), 409
                current_user.email = new_email
        
        # 更新密码（如果提供）
        if 'password' in data:
            new_password = data['password']
            if new_password:
                current_user.set_password(new_password)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Database constraint error'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500

@user_bp.route('/tasks', methods=['GET'])
@token_required
def get_my_tasks(current_user):
    try:
        status = request.args.get('status')
        priority = request.args.get('priority')
        due_start = request.args.get('dueStart')
        due_end = request.args.get('dueEnd')
        project_id = request.args.get('projectId')

        query = Task.query.filter(Task.is_deleted == False, Task.user_id == current_user.id)

        if status in ['pending', 'in_progress', 'completed', 'cancelled']:
            query = query.filter(Task.status == status)

        if priority in ['low', 'medium', 'high', 'urgent']:
            query = query.filter(Task.priority == priority)

        if project_id:
            query = query.filter(Task.project_id == project_id)

        if due_start:
            query = query.filter(Task.due_date >= due_start)
        if due_end:
            query = query.filter(Task.due_date <= due_end)

        tasks = query.order_by(Task.created_at.desc()).all()

        return jsonify({
            'success': True,
            'message': 'Tasks retrieved successfully',
            'tasks': [t.to_dict() for t in tasks]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve tasks: {str(e)}'
        }), 500
