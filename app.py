from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from config import config
from models import db, bcrypt
from auth import auth_bp
from groups import groups_bp
from chat import chat_bp
import os
import sockets

socketio = SocketIO()

def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    CORS(app)  # 允许跨域请求
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(chat_bp, url_prefix='/chat')
    
    # 全局错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': '请求的资源不存在'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': '请求方法不被允许'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500
    
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
        return jsonify({
            'success': True,
            'message': '服务运行正常',
            'status': 'healthy'
        })
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
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