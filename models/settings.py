from .base import db
from datetime import datetime
import uuid

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.String(16), primary_key=True, default=lambda: str(uuid.uuid4()).replace('-', '')[:16])
    user_id = db.Column(db.String(16), db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    language = db.Column(db.String(20), default='zh')
    font_size = db.Column(db.Integer, default=14)
    theme = db.Column(db.String(20), default='system')
    notifications_enabled = db.Column(db.Boolean, default=True)
    sound_enabled = db.Column(db.Boolean, default=True)
    vibration_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = db.Column(db.String(19), default=lambda: datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

    def __init__(self, user_id):
        self.id = str(uuid.uuid4()).replace('-', '')[:16]
        self.user_id = user_id

    def to_dict(self):
        return {
            'language': self.language,
            'font_size': self.font_size,
            'theme': self.theme,
            'notifications_enabled': self.notifications_enabled,
            'sound_enabled': self.sound_enabled,
            'vibration_enabled': self.vibration_enabled
        }
