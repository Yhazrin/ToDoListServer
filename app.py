from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from config import config
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    Limiter = None
from models import db, bcrypt
from auth import auth_bp
from groups import groups_bp
from chat import chat_bp
from user import user_bp
from oauth import oauth_bp
from tasks import tasks_bp
from files import files_bp
from calendar_routes import calendar_bp
from projects import projects_bp
from notifications import notifications_bp
from widget import widget_bp
from utils.logger import setup_logger
from utils.errors import error_handler
from utils.middleware import setup_request_logging
import os

# Flask-Migrate
try:
    from flask_migrate import Migrate
    MIGRATE_AVAILABLE = True
except ImportError:
    MIGRATE_AVAILABLE = False
    Migrate = None

socketio = SocketIO()
import sockets  # 需要在 socketio 初始化后导入

# 全局限流器（稍后在create_app中初始化）
limiter = None
# 全局迁移对象（稍后在create_app中初始化）
migrate = None

def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # 初始化日志系统（需要在其他初始化之前）
    app_logger, access_logger = setup_logger(app)
    
    # 初始化扩展
    db.init_app(app)
    bcrypt.init_app(app)
    
    # 初始化Flask-Migrate
    global migrate
    if MIGRATE_AVAILABLE:
        try:
            migrate = Migrate(app, db)
            app.logger.info('数据库迁移系统已启用')
        except Exception as e:
            app.logger.warning(f'数据库迁移系统初始化失败: {str(e)}')
            migrate = None
    else:
        migrate = None
        app.logger.warning('Flask-Migrate未安装，数据库迁移功能不可用')
    
    # 初始化API限流
    global limiter
    if LIMITER_AVAILABLE and app.config.get('RATELIMIT_ENABLED', True):
        try:
            limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                default_limits=[app.config.get('RATELIMIT_DEFAULT', '200 per hour')],
                storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
            )
            app.logger.info('API限流已启用')
        except Exception as e:
            app.logger.warning(f'API限流初始化失败: {str(e)}，将禁用限流')
            limiter = None
    else:
        limiter = None
        if not LIMITER_AVAILABLE:
            app.logger.warning('Flask-Limiter未安装，API限流功能不可用')
        else:
            app.logger.info('API限流已禁用')
    
    socketio.init_app(app, cors_allowed_origins="*")
    CORS(app)  # 允许跨域请求
    
    # 设置请求日志中间件
    setup_request_logging(app, access_logger)
    
    # 注册错误处理器
    error_handler(app)
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(user_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(widget_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(notifications_bp)
    
    app.logger.info('所有蓝图已注册')
    
    # 根路由
    @app.route('/')
    def index():
        return jsonify({
            'success': True,
            'message': '欢迎使用ToDoList服务器',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health [GET]',
                'register': '/auth/register [POST]',
                'login': '/auth/login [POST]',
                'logout': '/auth/logout [POST]',
                'auth_status': '/auth/status [GET]',
                'create_group': '/groups/create [POST]',
                'join_group': '/groups/join [POST]',
                'join_by_code': '/groups/join-by-code [POST]',
                'list_groups': '/groups/list/<user_id> [GET]',
                'group_info': '/groups/info/<group_id> [GET]',
                'update_group': '/groups/update/<group_id> [PUT]',
                'delete_group': '/groups/delete/<group_id> [DELETE]',
                'chat_rooms': '/chat/rooms [GET]',
                'get_messages': '/chat/rooms/<room_id>/messages [GET]',
                'send_message': '/chat/rooms/<room_id>/messages [POST]'
            }
        })
    
    # 健康检查接口
    @app.route('/health')
    def health_check():
        """健康检查接口"""
        try:
            # 检查数据库连接
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            app.logger.error(f'数据库连接检查失败: {str(e)}')
            db_status = 'disconnected'
        
        health_status = 'healthy' if db_status == 'connected' else 'degraded'
        
        return jsonify({
            'success': True,
            'message': '服务运行正常',
            'status': health_status,
            'database': db_status,
            'version': '2.0.0'
        }), 200 if health_status == 'healthy' else 503
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        app.logger.info('数据库表检查完成')
        # 兼容旧版本数据库：确保 group_messages 表包含必要列
        try:
            from sqlalchemy import text
            uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'sqlite' in uri:
                rows = db.session.execute(text('PRAGMA table_info(group_messages)')).fetchall()
                # SQLite PRAGMA 返回 (cid, name, type, notnull, dflt_value, pk)
                names = {row[1] for row in rows}
                if 'file_url' not in names:
                    db.session.execute(text('ALTER TABLE group_messages ADD COLUMN file_url TEXT'))
                if 'task_id' not in names:
                    db.session.execute(text('ALTER TABLE group_messages ADD COLUMN task_id TEXT'))
                if 'updated_time' not in names:
                    db.session.execute(text('ALTER TABLE group_messages ADD COLUMN updated_time INTEGER'))
                db.session.commit()
                app.logger.info('group_messages 表结构已校正')

                # 兼容旧版本数据库：确保 users 表包含头像相关列
                user_rows = db.session.execute(text('PRAGMA table_info(users)')).fetchall()
                user_cols = {row[1] for row in user_rows}
                if 'avatar_url' not in user_cols:
                    db.session.execute(text('ALTER TABLE users ADD COLUMN avatar_url TEXT'))
                if 'avatar_file_id' not in user_cols:
                    db.session.execute(text('ALTER TABLE users ADD COLUMN avatar_file_id TEXT'))
                db.session.commit()
                app.logger.info('users 表头像列已校正')

                # 兼容旧版本数据库：确保 tasks 表包含新增列
                task_rows = db.session.execute(text('PRAGMA table_info(tasks)')).fetchall()
                task_cols = {row[1] for row in task_rows}
                if 'start_date' not in task_cols:
                    db.session.execute(text('ALTER TABLE tasks ADD COLUMN start_date TEXT'))
                if 'end_date' not in task_cols:
                    db.session.execute(text('ALTER TABLE tasks ADD COLUMN end_date TEXT'))
                if 'assigned_to' not in task_cols:
                    db.session.execute(text('ALTER TABLE tasks ADD COLUMN assigned_to TEXT'))
                db.session.commit()
                app.logger.info('tasks 表新增列已校正')

                # 兼容旧版本数据库：确保 oauth_accounts 唯一约束/索引
                oauth_rows = db.session.execute(text('PRAGMA table_info(oauth_accounts)')).fetchall()
                oauth_cols = {row[1] for row in oauth_rows}
                # 为 provider_user_id 添加索引（SQLite用普通索引）
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_oauth_provider_user ON oauth_accounts(provider, provider_user_id)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_oauth_user_provider ON oauth_accounts(user_id, provider)'))
                db.session.commit()
                app.logger.info('oauth_accounts 索引已校正')
        except Exception as e:
            app.logger.warning(f'group_messages 表结构校正失败: {str(e)}')
    
    app.logger.info('应用初始化完成')
    return app

if __name__ == '__main__':
    import sys
    app = create_app()
    
    # 获取端口设置，支持命令行参数和环境变量
    port = 5000
    host = '0.0.0.0'
    
    # 从命令行参数解析
    for i, arg in enumerate(sys.argv):
        if arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
        elif arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
    
    # 环境变量优先级更高
    port = int(os.getenv('PORT', port))
    host = os.getenv('HOST', host)
    
    print("ToDoList服务器启动中...")
    print(f"监听地址: http://{host}:{port}")
    print("可用接口:")
    print("- GET / - 服务信息")
    print("- GET /health - 健康检查")
    print("- POST /auth/register - 用户注册")
    print("- POST /auth/login - 用户登录")
    print("- POST /auth/logout - 用户登出")
    print("- GET /auth/status - 认证服务状态")
    print("- POST /groups/create - 创建项目组")
    print("- POST /groups/join - 加入项目组")
    print("- POST /groups/join-by-code - 通过邀请码加入项目组")
    print("- GET /groups/list/<user_id> - 获取用户项目组列表")
    print("- GET /groups/info/<group_id> - 获取项目组信息")
    print("- PUT /groups/update/<group_id> - 更新项目组信息")
    print("- DELETE /groups/delete/<group_id> - 删除项目组")
    print("- GET /chat/rooms - 获取聊天室列表")
    print("- GET /chat/rooms/<room_id>/messages - 获取聊天消息")
    print("- POST /chat/rooms/<room_id>/messages - 发送聊天消息")
    print("- WebSocket: subscribe/unsubscribe - 实时聊天功能")
    socketio.run(app, host=host, port=port, debug=True)
