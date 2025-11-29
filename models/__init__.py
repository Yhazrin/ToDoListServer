"""
数据库模型模块

所有数据库模型按功能模块拆分到不同文件中，这里统一导出以保持向后兼容。
"""

from .base import db, bcrypt
from .user import User, OAuthAccount
from .group import ProjectGroup, user_groups
from .chat import GroupMessage, MessageReadStatus
from .task import Task, TaskFile, TaskAssignee
from .file import SharedFile
from .settings import UserSettings
from .calendar import CalendarEvent

__all__ = [
    # 数据库基础组件
    'db',
    'bcrypt',
    # 用户相关模型
    'User',
    'OAuthAccount',
    # 项目组相关模型
    'ProjectGroup',
    'user_groups',
    # 聊天相关模型
    'GroupMessage',
    'MessageReadStatus',
    # 任务相关模型
    'Task',
    'TaskFile',
    'TaskAssignee',
    # 文件相关模型
    'SharedFile',
    'UserSettings',
    # 日历相关模型
    'CalendarEvent',
]
