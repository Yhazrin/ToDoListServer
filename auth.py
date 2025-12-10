from flask import Blueprint, request, jsonify
from models import db, User
from sqlalchemy.exc import IntegrityError
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# 移除了邮箱格式和密码强度验证函数

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip() if data.get('email') else None
        password = data.get('password', '')
        
        # 移除了用户名和密码为空的检测
        
        # 检查用户名是否已存在
        existing_user = User.query.filter(User.username == username).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Username already exists'
            }), 409
        
        # 如果提供了邮箱，检查邮箱是否已存在
        if email:
            existing_email = User.query.filter(User.email == email).first()
            if existing_email:
                return jsonify({
                    'success': False,
                    'message': 'Email already registered'
                }), 409
        
        # 创建新用户
        new_user = User(username=username, password=password, email=email)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': new_user.to_dict()
        }), 201
        
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
            'message': f'Registration failed: {str(e)}'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        username_or_email = data.get('username', '').strip()
        password = data.get('password', '')
        
        # 移除了用户名/邮箱和密码为空的检测
        
        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email.isnot(None) & (User.email == username_or_email))
        ).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # 检查用户是否激活
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'Account disabled'
            }), 403
        
        # 验证密码
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid password'
            }), 401
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user.to_dict(),
            'token': user.id  # 返回用户ID作为认证token
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Login failed: {str(e)}'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        username_or_email = data.get('username', '').strip()
        
        # 查找用户（支持用户名或邮箱登出）
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email.isnot(None) & (User.email == username_or_email))
        ).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
        
        # 检查用户是否激活
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': 'Account disabled'
            }), 403
        
        return jsonify({
            'success': True,
            'message': 'Logout successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout failed: {str(e)}'
        }), 500

@auth_bp.route('/status', methods=['GET'])
def status():
    """服务状态检查接口"""
    return jsonify({
        'success': True,
        'message': 'Auth service running',
        'service': 'ToDoList Auth Service'
    }), 200

# 简单的Token认证装饰器：Authorization: Bearer <token>
# token可为用户id、用户名或邮箱
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Missing or invalid Authorization header'}), 401
        token = auth_header.split('Bearer ', 1)[1].strip()
        if not token:
            return jsonify({'message': 'Token missing'}), 401
        user = User.query.filter(
            (User.id == token) | (User.username == token) | (User.email == token)
        ).first()
        if not user:
            return jsonify({'message': 'Invalid token'}), 401
        if not user.is_active:
            return jsonify({'message': 'Account disabled'}), 403
        return f(current_user=user, *args, **kwargs)
    return decorated

@auth_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    """修改密码接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
            
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
             return jsonify({
                'success': False,
                'message': 'Both old and new passwords are required'
            }), 400
            
        if not current_user.check_password(old_password):
            return jsonify({
                'success': False,
                'message': 'Invalid old password'
            }), 401
            
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Change password failed: {str(e)}'
        }), 500