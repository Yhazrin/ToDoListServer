from flask import Blueprint, request, jsonify, current_app
from models import db, User, Task, SharedFile, UserSettings
from auth import token_required
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os
import mimetypes
from datetime import datetime

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

# 头像上传/删除配置
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_AVATAR_SIZE = 10 * 1024 * 1024  # 10MB

def _image_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

@user_bp.route('/avatar', methods=['POST'])
@token_required
def upload_avatar(current_user):
    try:
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'message': 'No avatar provided'}), 400

        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_AVATAR_SIZE:
            return jsonify({'success': False, 'message': f'Avatar size exceeds {MAX_AVATAR_SIZE // (1024*1024)}MB'}), 400

        # 验证扩展名
        if not _image_allowed(file.filename):
            return jsonify({'success': False, 'message': 'Image type not allowed'}), 400

        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        os.makedirs(upload_folder, exist_ok=True)

        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        unique_filename = f"avatar_{current_user.id}_{timestamp}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)

        file.save(file_path)

        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'

        # 创建/更新 SharedFile 记录
        new_file = SharedFile(
            user_id=current_user.id,
            filename=filename,
            file_path=unique_filename,
            group_id=None,
            file_type='image',
            file_size=file_size,
            mime_type=mime_type
        )

        db.session.add(new_file)
        db.session.flush()

        # 如果之前有头像，软删除旧文件
        if current_user.avatar_file_id:
            old = SharedFile.query.filter_by(id=current_user.avatar_file_id, is_deleted=False).first()
            if old:
                old.is_deleted = True
                old.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # 更新用户头像信息
        current_user.avatar_file_id = new_file.id
        current_user.avatar_url = f"/files/{new_file.id}/preview"

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Avatar uploaded successfully',
            'avatar_url': current_user.avatar_url
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to upload avatar: {str(e)}'}), 500

@user_bp.route('/avatar', methods=['DELETE'])
@token_required
def delete_avatar(current_user):
    try:
        if not current_user.avatar_file_id:
            # 没有头像也视为成功
            return jsonify({'success': True, 'message': 'No avatar to delete', 'avatar_url': None}), 200

        file_rec = SharedFile.query.filter_by(id=current_user.avatar_file_id, is_deleted=False).first()
        if file_rec:
            file_rec.is_deleted = True
            file_rec.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        current_user.avatar_file_id = None
        current_user.avatar_url = None
        db.session.commit()

        return jsonify({'success': True, 'message': 'Avatar deleted successfully', 'avatar_url': None}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to delete avatar: {str(e)}'}), 500

@user_bp.route('/settings', methods=['GET'])
@token_required
def get_settings(current_user):
    try:
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)
            db.session.commit()
        return jsonify({'success': True, 'message': '获取成功', 'settings': settings.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'获取用户设置失败: {str(e)}'}), 500

@user_bp.route('/settings', methods=['PUT'])
@token_required
def update_settings(current_user):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400

        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)

        # 仅更新前端允许的字段
        for key in ['language', 'font_size', 'theme', 'notifications_enabled', 'sound_enabled', 'vibration_enabled']:
            if key in data:
                setattr(settings, key, data[key])
        settings.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        db.session.commit()
        return jsonify({'success': True, 'message': '更新成功', 'settings': settings.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新用户设置失败: {str(e)}'}), 500
