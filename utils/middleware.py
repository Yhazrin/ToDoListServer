"""
中间件模块
提供请求日志、响应时间等中间件功能
"""
from flask import request, g
from datetime import datetime
import time

def setup_request_logging(app, access_logger):
    """
    设置请求日志中间件
    
    Args:
        app: Flask应用实例
        access_logger: 访问日志记录器
    """
    @app.before_request
    def log_request_info():
        """记录请求信息"""
        g.start_time = time.time()
        g.request_id = str(time.time()).replace('.', '')[:16]
        
        # 记录请求日志
        access_logger.info(
            f'[{g.request_id}] {request.method} {request.path} - '
            f'IP: {request.remote_addr} - '
            f'User-Agent: {request.headers.get("User-Agent", "Unknown")}'
        )
    
    @app.after_request
    def log_response_info(response):
        """记录响应信息"""
        # 计算请求处理时间
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
        else:
            duration = 0
        
        # 记录响应日志
        request_id = getattr(g, 'request_id', 'unknown')
        status_code = response.status_code
        
        access_logger.info(
            f'[{request_id}] Response: {status_code} - '
            f'Duration: {duration:.3f}s - '
            f'Size: {response.content_length or 0} bytes'
        )
        
        # 添加响应头
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Response-Time'] = f'{duration:.3f}'
        
        return response

