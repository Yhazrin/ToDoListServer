from .base import db
from datetime import datetime
import uuid

class CalendarEvent(db.Model):
    """日历事件模型"""
    __tablename__ = 'calendar_events'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False, index=True)
    task_id = db.Column(db.String(16), db.ForeignKey('tasks.id'), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.String(19), nullable=False)  # YYYY-MM-DD HH:MM:SS格式
    end_time = db.Column(db.String(19), nullable=False)  # YYYY-MM-DD HH:MM:SS格式
    location = db.Column(db.String(200))
    created_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __init__(self, user_id, title, start_time, end_time, task_id=None, description=None, location=None):
        """初始化日历事件对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.user_id = user_id
        self.task_id = task_id
        self.title = title
        self.description = description
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'location': self.location,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_deleted': self.is_deleted
        }
    
    def __repr__(self):
        return f'<CalendarEvent {self.title}>'

