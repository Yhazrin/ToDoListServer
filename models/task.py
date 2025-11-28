from .base import db
from datetime import datetime, date
import uuid

class Task(db.Model):
    """任务模型"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False, index=True)
    project_id = db.Column(db.String(16), db.ForeignKey('project_groups.id'), nullable=True, index=True)
    parent_task_id = db.Column(db.String(16), db.ForeignKey('tasks.id'), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    due_date = db.Column(db.String(10))  # YYYY-MM-DD格式
    created_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    completed_at = db.Column(db.String(19))
    is_deleted = db.Column(db.Boolean, default=False)
    position = db.Column(db.Integer, default=0)  # 用于排序
    
    # 自引用关系：子任务
    subtasks = db.relationship('Task', backref=db.backref('parent_task', remote_side=[id]), lazy='dynamic')
    
    def __init__(self, user_id, title, project_id=None, parent_task_id=None, description=None, 
                 status='pending', priority='medium', due_date=None):
        """初始化任务对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.user_id = user_id
        self.project_id = project_id
        self.parent_task_id = parent_task_id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        if due_date:
            if isinstance(due_date, date):
                self.due_date = due_date.strftime('%Y-%m-%d')
            else:
                self.due_date = due_date
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'parent_task_id': self.parent_task_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at,
            'is_deleted': self.is_deleted,
            'position': self.position
        }
    
    def __repr__(self):
        return f'<Task {self.title}>'


class TaskFile(db.Model):
    """任务附件关联模型"""
    __tablename__ = 'task_files'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    task_id = db.Column(db.String(16), db.ForeignKey('tasks.id'), nullable=False, index=True)
    file_id = db.Column(db.String(16), db.ForeignKey('shared_files.id'), nullable=False, index=True)
    created_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    
    # 创建唯一约束
    __table_args__ = (db.UniqueConstraint('task_id', 'file_id', name='unique_task_file'),)
    
    def __init__(self, task_id, file_id):
        """初始化任务文件关联对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.task_id = task_id
        self.file_id = file_id
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'file_id': self.file_id,
            'created_at': self.created_at
        }
    
    def __repr__(self):
        return f'<TaskFile {self.id}>'

