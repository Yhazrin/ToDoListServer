from flask import Blueprint, request, jsonify, send_file, send_from_directory
from models import db, User, ProjectGroup, SharedFile
from auth import token_required
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
import os
import mimetypes
from datetime import datetime

files_bp = Blueprint('files', __name__, url_prefix='/files')

# 文件上传配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 
                      'ppt', 'pptx', 'txt', 'mp4', 'avi', 'mov', 'mp3', 'wav', 'zip', 'rar'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    """根据文件名推断文件类型"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    image_exts = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    video_exts = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv'}
    audio_exts = {'mp3', 'wav', 'flac', 'aac', 'ogg'}
    
    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    elif ext in audio_exts:
        return 'audio'
    elif ext in {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'}:
        return 'document'
    else:
        return 'other'

@files_bp.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user):
    """上传文件接口"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'message': f'File size exceeds maximum limit of {MAX_FILE_SIZE / (1024*1024)}MB'
            }), 400
        
        # 验证文件扩展名
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': 'File type not allowed'
            }), 400
        
        # 获取可选参数
        group_id = request.form.get('group_id')
        if group_id:
            # 验证项目组存在且用户有权限
            project = ProjectGroup.query.filter_by(id=group_id).first()
            if not project:
                return jsonify({
                    'success': False,
                    'message': 'Project group not found'
                }), 404
            
            if current_user not in project.members and project.leader_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': 'Permission denied: Not a member of this project'
                }), 403
        
        # 安全化文件名并保存
        filename = secure_filename(file.filename)
        # 添加时间戳确保唯一性
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(file_path)
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # 创建文件记录
        new_file = SharedFile(
            user_id=current_user.id,
            filename=filename,
            file_path=unique_filename,  # 存储相对路径
            group_id=group_id,
            file_type=get_file_type(filename),
            file_size=file_size,
            mime_type=mime_type
        )
        
        db.session.add(new_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'file': new_file.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to upload file: {str(e)}'
        }), 500

@files_bp.route('/<file_id>', methods=['GET'])
@token_required
def get_file(current_user, file_id):
    """获取文件信息接口"""
    try:
        file = SharedFile.query.filter_by(id=file_id, is_deleted=False).first()
        if not file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # 检查权限
        if file.user_id != current_user.id:
            # 如果是项目文件，检查用户是否是项目组成员
            if file.group_id:
                project = ProjectGroup.query.filter_by(id=file.group_id).first()
                if not project or (current_user not in project.members and project.leader_id != current_user.id):
                    return jsonify({
                        'success': False,
                        'message': 'Permission denied'
                    }), 403
            else:
                return jsonify({
                    'success': False,
                    'message': 'Permission denied'
                }), 403
        
        return jsonify({
            'success': True,
            'message': 'File retrieved successfully',
            'file': file.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve file: {str(e)}'
        }), 500

@files_bp.route('/<file_id>', methods=['DELETE'])
@token_required
def delete_file(current_user, file_id):
    """删除文件接口（软删除）"""
    try:
        file = SharedFile.query.filter_by(id=file_id, is_deleted=False).first()
        if not file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # 检查权限：只有文件所有者可以删除
        if file.user_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied: Only file owner can delete'
            }), 403
        
        # 软删除：标记为已删除
        file.is_deleted = True
        file.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()
        
        # 可选：同时删除物理文件
        # file_path = os.path.join(UPLOAD_FOLDER, file.file_path)
        # if os.path.exists(file_path):
        #     os.remove(file_path)
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete file: {str(e)}'
        }), 500

@files_bp.route('/group/<group_id>', methods=['GET'])
@token_required
def get_group_files(current_user, group_id):
    """获取项目组的文件列表接口"""
    try:
        # 验证项目组存在且用户有权限
        project = ProjectGroup.query.filter_by(id=group_id).first()
        if not project:
            return jsonify({
                'success': False,
                'message': 'Project group not found'
            }), 404
        
        if current_user not in project.members and project.leader_id != current_user.id:
            return jsonify({
                'success': False,
                'message': 'Permission denied: Not a member of this project'
            }), 403
        
        # 获取项目组的所有文件
        files = SharedFile.query.filter_by(
            group_id=group_id,
            is_deleted=False
        ).order_by(SharedFile.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'message': 'Files retrieved successfully',
            'files': [file.to_dict() for file in files]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to retrieve files: {str(e)}'
        }), 500

@files_bp.route('/<file_id>/preview', methods=['GET'])
@token_required
def preview_file(current_user, file_id):
    """获取文件预览接口（下载文件）"""
    try:
        file = SharedFile.query.filter_by(id=file_id, is_deleted=False).first()
        if not file:
            return jsonify({
                'success': False,
                'message': 'File not found'
            }), 404
        
        # 检查权限
        if file.user_id != current_user.id:
            # 如果是项目文件，检查用户是否是项目组成员
            if file.group_id:
                project = ProjectGroup.query.filter_by(id=file.group_id).first()
                if not project or (current_user not in project.members and project.leader_id != current_user.id):
                    return jsonify({
                        'success': False,
                        'message': 'Permission denied'
                    }), 403
            else:
                return jsonify({
                    'success': False,
                    'message': 'Permission denied'
                }), 403
        
        # 获取文件路径
        file_path = os.path.join(UPLOAD_FOLDER, file.file_path)
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'message': 'File not found on server'
            }), 404
        
        # 返回文件
        return send_file(
            file_path,
            mimetype=file.mime_type or 'application/octet-stream',
            as_attachment=False,
            download_name=file.filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to preview file: {str(e)}'
        }), 500

