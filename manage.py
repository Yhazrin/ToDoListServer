#!/usr/bin/env python3
"""
Flask CLI管理脚本
用于运行Flask命令，包括数据库迁移命令

使用方法:
    python manage.py db init          # 初始化迁移目录
    python manage.py db migrate       # 生成迁移脚本
    python manage.py db upgrade       # 执行迁移
    python manage.py db downgrade     # 回退迁移
    python manage.py run              # 运行开发服务器
"""

import os
from flask.cli import FlaskGroup
from app import create_app

# 设置环境变量（如果需要）
os.environ.setdefault('FLASK_APP', 'app:create_app()')
os.environ.setdefault('FLASK_ENV', 'development')

def create_cli_app():
    """创建CLI应用"""
    app = create_app()
    return app

# 创建Flask CLI组
cli = FlaskGroup(create_app=create_cli_app)

@cli.command()
def run():
    """运行开发服务器"""
    app = create_app()
    import sys
    
    # 获取端口设置
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    
    print("=" * 60)
    print("ToDoList服务器启动中...")
    print(f"监听地址: http://{host}:{port}")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    cli()

