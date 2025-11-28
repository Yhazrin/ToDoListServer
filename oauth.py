from flask import Blueprint, request, jsonify, redirect, url_for
from models import db, User, OAuthAccount
from auth import token_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import requests
import uuid

oauth_bp = Blueprint('oauth', __name__, url_prefix='/auth')

# OAuth配置（需要在实际部署时配置）
GOOGLE_CLIENT_ID = None  # 从环境变量或配置文件读取
GOOGLE_CLIENT_SECRET = None
GITHUB_CLIENT_ID = None
GITHUB_CLIENT_SECRET = None

@oauth_bp.route('/google/login', methods=['POST'])
def google_login():
    """Google OAuth登录/绑定接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        access_token = data.get('access_token')
        user_id = data.get('user_id')  # 可选，如果提供则绑定到现有账户
        
        if not access_token:
            return jsonify({
                'success': False,
                'message': 'Access token is required'
            }), 400
        
        # 通过access_token获取Google用户信息
        try:
            google_user_info = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            ).json()
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to get Google user info: {str(e)}'
            }), 400
        
        if 'error' in google_user_info:
            return jsonify({
                'success': False,
                'message': f'Google API error: {google_user_info["error"]}'
            }), 400
        
        google_user_id = google_user_info.get('id')
        email = google_user_info.get('email')
        
        if user_id:
            # 绑定到现有账户
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            # 检查是否已绑定
            existing_oauth = OAuthAccount.query.filter_by(
                user_id=user_id,
                provider='google'
            ).first()
            
            if existing_oauth:
                # 更新OAuth账户信息
                existing_oauth.provider_user_id = google_user_id
                existing_oauth.email = email
                existing_oauth.access_token = access_token
                existing_oauth.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 创建新的OAuth绑定
                oauth_account = OAuthAccount(
                    user_id=user_id,
                    provider='google',
                    provider_user_id=google_user_id,
                    email=email,
                    access_token=access_token
                )
                db.session.add(oauth_account)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Google account linked successfully',
                'user': user.to_dict(),
                'oauth_account': oauth_account.to_dict() if not existing_oauth else existing_oauth.to_dict()
            }), 200
        else:
            # 通过Google账户登录或创建新账户
            # 查找是否已有绑定的账户
            existing_oauth = OAuthAccount.query.filter_by(
                provider='google',
                provider_user_id=google_user_id
            ).first()
            
            if existing_oauth:
                # 使用已有账户登录
                user = User.query.filter_by(id=existing_oauth.user_id).first()
                if not user or not user.is_active:
                    return jsonify({
                        'success': False,
                        'message': 'Account disabled or not found'
                    }), 403
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': user.to_dict(),
                    'token': user.id
                }), 200
            else:
                # 创建新账户（使用邮箱或Google ID作为用户名）
                username = email.split('@')[0] if email else f'google_{google_user_id[:8]}'
                # 确保用户名唯一
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f'{base_username}{counter}'
                    counter += 1
                
                new_user = User(
                    username=username,
                    password=str(uuid.uuid4()),  # 随机密码
                    email=email
                )
                db.session.add(new_user)
                db.session.flush()  # 获取新用户ID
                
                # 创建OAuth绑定
                oauth_account = OAuthAccount(
                    user_id=new_user.id,
                    provider='google',
                    provider_user_id=google_user_id,
                    email=email,
                    access_token=access_token
                )
                db.session.add(oauth_account)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Account created and logged in successfully',
                    'user': new_user.to_dict(),
                    'token': new_user.id
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
            'message': f'Google login failed: {str(e)}'
        }), 500

@oauth_bp.route('/google/callback', methods=['POST'])
def google_callback():
    """Google OAuth回调接口（处理授权码）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        code = data.get('code')
        user_id = data.get('user_id')  # 可选
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'Authorization code is required'
            }), 400
        
        # 使用授权码交换access_token
        # 注意：这需要客户端配置，通常在前端完成，然后调用/login端点
        # 这里提供一个简化版本
        return jsonify({
            'success': False,
            'message': 'Please use /auth/google/login endpoint with access_token directly'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Google callback failed: {str(e)}'
        }), 500

@oauth_bp.route('/github/login', methods=['POST'])
def github_login():
    """GitHub OAuth登录/绑定接口"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        access_token = data.get('access_token')
        user_id = data.get('user_id')  # 可选，如果提供则绑定到现有账户
        
        if not access_token:
            return jsonify({
                'success': False,
                'message': 'Access token is required'
            }), 400
        
        # 通过access_token获取GitHub用户信息
        try:
            github_user_info = requests.get(
                'https://api.github.com/user',
                headers={'Authorization': f'token {access_token}'}
            ).json()
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Failed to get GitHub user info: {str(e)}'
            }), 400
        
        if 'error' in github_user_info or 'message' in github_user_info:
            return jsonify({
                'success': False,
                'message': f'GitHub API error: {github_user_info.get("message", "Unknown error")}'
            }), 400
        
        github_user_id = str(github_user_info.get('id'))
        email = github_user_info.get('email')
        username = github_user_info.get('login')
        
        if user_id:
            # 绑定到现有账户
            user = User.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 404
            
            # 检查是否已绑定
            existing_oauth = OAuthAccount.query.filter_by(
                user_id=user_id,
                provider='github'
            ).first()
            
            if existing_oauth:
                # 更新OAuth账户信息
                existing_oauth.provider_user_id = github_user_id
                existing_oauth.email = email
                existing_oauth.access_token = access_token
                existing_oauth.updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 创建新的OAuth绑定
                oauth_account = OAuthAccount(
                    user_id=user_id,
                    provider='github',
                    provider_user_id=github_user_id,
                    email=email,
                    access_token=access_token
                )
                db.session.add(oauth_account)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'GitHub account linked successfully',
                'user': user.to_dict(),
                'oauth_account': oauth_account.to_dict() if not existing_oauth else existing_oauth.to_dict()
            }), 200
        else:
            # 通过GitHub账户登录或创建新账户
            # 查找是否已有绑定的账户
            existing_oauth = OAuthAccount.query.filter_by(
                provider='github',
                provider_user_id=github_user_id
            ).first()
            
            if existing_oauth:
                # 使用已有账户登录
                user = User.query.filter_by(id=existing_oauth.user_id).first()
                if not user or not user.is_active:
                    return jsonify({
                        'success': False,
                        'message': 'Account disabled or not found'
                    }), 403
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': user.to_dict(),
                    'token': user.id
                }), 200
            else:
                # 创建新账户
                # 确保用户名唯一
                base_username = username or f'github_{github_user_id[:8]}'
                counter = 1
                while User.query.filter_by(username=base_username).first():
                    base_username = f'{username or "github"}{counter}'
                    counter += 1
                
                new_user = User(
                    username=base_username,
                    password=str(uuid.uuid4()),  # 随机密码
                    email=email
                )
                db.session.add(new_user)
                db.session.flush()  # 获取新用户ID
                
                # 创建OAuth绑定
                oauth_account = OAuthAccount(
                    user_id=new_user.id,
                    provider='github',
                    provider_user_id=github_user_id,
                    email=email,
                    access_token=access_token
                )
                db.session.add(oauth_account)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Account created and logged in successfully',
                    'user': new_user.to_dict(),
                    'token': new_user.id
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
            'message': f'GitHub login failed: {str(e)}'
        }), 500

@oauth_bp.route('/github/callback', methods=['POST'])
def github_callback():
    """GitHub OAuth回调接口（处理授权码）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Invalid request data'
            }), 400
        
        code = data.get('code')
        user_id = data.get('user_id')  # 可选
        
        if not code:
            return jsonify({
                'success': False,
                'message': 'Authorization code is required'
            }), 400
        
        # 使用授权码交换access_token
        # 注意：这需要客户端配置，通常在前端完成，然后调用/login端点
        # 这里提供一个简化版本
        return jsonify({
            'success': False,
            'message': 'Please use /auth/github/login endpoint with access_token directly'
        }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'GitHub callback failed: {str(e)}'
        }), 500

