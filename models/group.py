from .base import db
from datetime import datetime, date
import uuid
import random
import string

# 用户和项目组的多对多关系表
user_groups = db.Table('user_groups',
    db.Column('user_id', db.String(16), db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.String(16), db.ForeignKey('project_groups.id'), primary_key=True),
    db.Column('joined_at', db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
)

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

