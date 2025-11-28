from .base import db
from datetime import datetime
import uuid
import time

class GroupMessage(db.Model):
    """项目组聊天消息模型"""
    __tablename__ = 'group_messages'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    group_id = db.Column(db.String(16), db.ForeignKey('project_groups.id'), nullable=False)
    sender_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False)
    message_type = db.Column(db.String(10), default='text')  # text, image, video, audio, file, task
    content = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500))
    task_id = db.Column(db.String(16), db.ForeignKey('tasks.id'), nullable=True)  # 关联的任务ID（用于任务注入）
    reply_to_id = db.Column(db.String(16), db.ForeignKey('group_messages.id'))
    sent_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_time = db.Column(db.Integer, default=lambda: int(time.time()))
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __init__(self, group_id, sender_id, content, message_type='text', file_url=None, task_id=None, reply_to_id=None):
        """初始化消息对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.group_id = group_id
        self.sender_id = sender_id
        self.content = content
        self.message_type = message_type
        self.file_url = file_url
        self.task_id = task_id
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
            'task_id': self.task_id,
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

