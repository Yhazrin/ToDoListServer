from .base import db, bcrypt
from datetime import datetime
import uuid

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    avatar_url = db.Column(db.String(500))
    avatar_file_id = db.Column(db.String(16), db.ForeignKey('shared_files.id'), index=True)
    
    def __init__(self, username, password, email=None):
        """初始化用户对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.username = username
        self.email = email
        self.set_password(password)
    
    def set_password(self, password):
        """设置密码（加密存储）"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """验证密码"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    # 定义与项目组的多对多关系（使用字符串引用避免循环导入）
    project_groups = db.relationship('ProjectGroup', secondary='user_groups', backref=db.backref('members', lazy='dynamic'))
    
    # 定义与任务的关联关系
    tasks = db.relationship('Task', backref='user', lazy='dynamic', foreign_keys='Task.user_id')
    
    def to_dict(self):
        """转换为字典格式（不包含密码）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'avatar_url': self.avatar_url
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class OAuthAccount(db.Model):
    """OAuth账户绑定模型"""
    __tablename__ = 'oauth_accounts'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False, index=True)
    provider = db.Column(db.String(20), nullable=False)  # google, github
    provider_user_id = db.Column(db.String(100), nullable=False)  # OAuth提供商返回的用户ID
    email = db.Column(db.String(120))
    access_token = db.Column(db.Text)  # 访问令牌（加密存储）
    refresh_token = db.Column(db.Text)  # 刷新令牌（加密存储）
    token_expires_at = db.Column(db.String(19))
    created_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 创建唯一约束：一个用户在同一个提供商只能绑定一个账户
    __table_args__ = (db.UniqueConstraint('user_id', 'provider', name='unique_user_provider'),)
    
    def __init__(self, user_id, provider, provider_user_id, email=None, access_token=None, 
                 refresh_token=None, token_expires_at=None):
        """初始化OAuth账户对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.user_id = user_id
        self.provider = provider
        self.provider_user_id = provider_user_id
        self.email = email
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
    
    def to_dict(self):
        """转换为字典格式（不包含敏感信息）"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'provider': self.provider,
            'email': self.email,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def __repr__(self):
        return f'<OAuthAccount {self.provider}:{self.provider_user_id}>'
