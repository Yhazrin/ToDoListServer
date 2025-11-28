"""
错误处理模块
提供统一的错误响应格式和错误处理工具
"""
from flask import jsonify, request
import traceback
import uuid
try:
    from flask_limiter.errors import RateLimitExceeded
    LIMITER_AVAILABLE = True
except ImportError:
    LIMITER_AVAILABLE = False
    RateLimitExceeded = Exception

class APIError(Exception):
    """API错误基类"""
    def __init__(self, message, status_code=400, error_code=None, details=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f'ERR_{status_code}'
        self.details = details
        super().__init__(self.message)

def error_handler(app):
    """
    注册全局错误处理器
    
    Args:
        app: Flask应用实例
    """
    if LIMITER_AVAILABLE:
        @app.errorhandler(RateLimitExceeded)
        def handle_rate_limit_exceeded(e):
            """处理API限流错误"""
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ERR_429',
                    'message': '请求过于频繁，请稍后再试',
                    'details': {
                        'limit': str(e.description) if hasattr(e, 'description') else None,
                        'retry_after': e.retry_after if hasattr(e, 'retry_after') else None
                    }
                }
            }), 429
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """处理API错误"""
        response = {
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.message,
                'details': error.details
            }
        }
        return jsonify(response), error.status_code
    
    @app.errorhandler(404)
    def not_found(error):
        """处理404错误"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'ERR_404',
                'message': '请求的资源不存在',
                'path': request.path
            }
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """处理405错误"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'ERR_405',
                'message': '请求方法不被允许',
                'method': request.method,
                'path': request.path
            }
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        # 生成错误追踪ID
        error_id = str(uuid.uuid4())[:8]
        
        # 记录详细错误信息到日志
        app.logger.error(
            f'Internal Server Error [{error_id}]: {str(error)}\n'
            f'Traceback: {traceback.format_exc()}'
        )
        
        # 生产环境不返回详细错误信息
        details = None
        if app.config.get('DEBUG', False):
            details = {
                'traceback': traceback.format_exc(),
                'error_id': error_id
            }
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'ERR_500',
                'message': '服务器内部错误',
                'error_id': error_id,
                'details': details
            }
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """处理所有未捕获的异常"""
        # 生成错误追踪ID
        error_id = str(uuid.uuid4())[:8]
        
        # 记录详细错误信息
        app.logger.error(
            f'Unhandled Exception [{error_id}]: {str(error)}\n'
            f'Traceback: {traceback.format_exc()}'
        )
        
        # 生产环境不返回详细错误信息
        details = None
        if app.config.get('DEBUG', False):
            details = {
                'traceback': traceback.format_exc(),
                'error_id': error_id
            }
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'ERR_500',
                'message': '服务器内部错误',
                'error_id': error_id,
                'details': details
            }
        }), 500

