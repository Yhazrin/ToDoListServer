from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, date
import uuid
import time

db = SQLAlchemy()
bcrypt = Bcrypt()

# 用户和项目组的多对多关系表
user_groups = db.Table('user_groups',
    db.Column('user_id', db.String(16), db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.String(16), db.ForeignKey('project_groups.id'), primary_key=True),
    db.Column('joined_at', db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
)

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
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
    
    # 定义与项目组的多对多关系
    project_groups = db.relationship('ProjectGroup', secondary=user_groups, backref=db.backref('members', lazy='dynamic'))
    
    def to_dict(self):
        """转换为字典格式（不包含密码）"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class ProjectGroup(db.Model):
    """项目组模型"""
    __tablename__ = 'project_groups'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    project_title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    leader_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.String(10))
    due_date = db.Column(db.String(10), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    contact_info = db.Column(db.String(200))
    invite_code = db.Column(db.String(8), unique=True, nullable=False, index=True)
    
    def __init__(self, name, project_title, leader_id, due_date, description=None, start_date=None, contact_info=None):
        """初始化项目组对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.name = name
        self.project_title = project_title
        self.leader_id = leader_id
        # 处理日期格式转换
        if isinstance(due_date, date):
            self.due_date = due_date.strftime('%Y-%m-%d')
        else:
            self.due_date = due_date
        self.description = description
        if isinstance(start_date, date):
            self.start_date = start_date.strftime('%Y-%m-%d')
        else:
            self.start_date = start_date
        self.contact_info = contact_info
        # 生成唯一邀请码
        self.invite_code = self._generate_invite_code()
    
    def _generate_invite_code(self):
        """生成唯一的8位邀请码"""
        import random
        import string
        
        while True:
            # 生成8位随机字符串，包含大小写字母和数字
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            # 检查是否已存在相同的邀请码
            existing = ProjectGroup.query.filter_by(invite_code=code).first()
            if not existing:
                return code
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'project_title': self.project_title,
            'description': self.description,
            'leader_id': self.leader_id,
            'start_date': self.start_date,
            'due_date': self.due_date,
            'is_active': self.is_active,
            'contact_info': self.contact_info,
            'invite_code': self.invite_code
        }
    
    def __repr__(self):
        return f'<ProjectGroup {self.name}>'


class GroupMessage(db.Model):
    """项目组聊天消息模型"""
    __tablename__ = 'group_messages'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    group_id = db.Column(db.String(16), db.ForeignKey('project_groups.id'), nullable=False)
    sender_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False)
    message_type = db.Column(db.String(10), default='text')
    content = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500))
    reply_to_id = db.Column(db.String(16), db.ForeignKey('group_messages.id'))
    sent_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_time = db.Column(db.Integer, default=lambda: int(time.time()))
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __init__(self, group_id, sender_id, content, message_type='text', file_url=None, reply_to_id=None):
        """初始化消息对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.group_id = group_id
        self.sender_id = sender_id
        self.content = content
        self.message_type = message_type
        self.file_url = file_url
        self.reply_to_id = reply_to_id
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'group_id': self.group_id,
            'sender_id': self.sender_id,
            'message_type': self.message_type,
            'content': self.content,
            'file_url': self.file_url,
            'reply_to_id': self.reply_to_id,
            'sent_at': self.sent_at,
            'updated_time': self.updated_time,
            'is_deleted': self.is_deleted
        }
    
    def __repr__(self):
        return f'<GroupMessage {self.id}>'


class MessageReadStatus(db.Model):
    """消息已读状态模型"""
    __tablename__ = 'message_read_status'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    message_id = db.Column(db.String(16), db.ForeignKey('group_messages.id'), nullable=False)
    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False)
    read_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_time = db.Column(db.Integer, default=lambda: int(time.time()))
    
    # 创建唯一约束
    __table_args__ = (db.UniqueConstraint('message_id', 'user_id', name='unique_user_message'),)
    
    def __init__(self, message_id, user_id):
        """初始化已读状态对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.message_id = message_id
        self.user_id = user_id
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'read_at': self.read_at,
            'updated_time': self.updated_time
        }
    
    def __repr__(self):
        return f'<MessageReadStatus {self.id}>'