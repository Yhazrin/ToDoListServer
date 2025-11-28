"""ToDoList服务器包

这是一个基于Flask的用户认证服务器，提供用户注册和登录功能。
主要特性：
- 用户注册和登录
- 密码加密存储（bcrypt）
- RESTful API设计
- SQLite数据库支持
- 跨域请求支持
"""

from .app import create_app
from .models import db, User
from .config import config

__version__ = '1.0.0'
__author__ = 'ToDoList Team'

# 导出主要组件
__all__ = ['create_app', 'db', 'User', 'config']