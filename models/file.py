from .base import db
from datetime import datetime
import uuid

class SharedFile(db.Model):
    """共享文件模型"""
    __tablename__ = 'shared_files'
    
    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False, index=True)
    group_id = db.Column(db.String(16), db.ForeignKey('project_groups.id'), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50))  # image, video, audio, document, other
    file_size = db.Column(db.Integer)  # 文件大小（字节）
    mime_type = db.Column(db.String(100))
    thumbnail_path = db.Column(db.String(500))  # 缩略图路径（用于图片/视频预览）
    created_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    is_deleted = db.Column(db.Boolean, default=False)
    
    def __init__(self, user_id, filename, file_path, group_id=None, file_type=None, 
                 file_size=None, mime_type=None, thumbnail_path=None):
        """初始化共享文件对象"""
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.user_id = user_id
        self.group_id = group_id
        self.filename = filename
        self.file_path = file_path
        self.file_type = file_type
        self.file_size = file_size
        self.mime_type = mime_type
        self.thumbnail_path = thumbnail_path
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'thumbnail_path': self.thumbnail_path,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'is_deleted': self.is_deleted
        }
    
    def __repr__(self):
        return f'<SharedFile {self.filename}>'

