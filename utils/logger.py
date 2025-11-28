"""
日志系统配置模块
提供结构化日志和请求日志功能
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger(app):
    """
    设置应用日志系统
    
    Args:
        app: Flask应用实例
    """
    # 创建logs目录
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # 配置日志格式
    log_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 设置日志级别
    log_level = logging.DEBUG if app.config.get('DEBUG', False) else logging.INFO
    
    # 文件处理器 - 应用日志
    app_log_file = os.path.join(logs_dir, 'app.log')
    file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_format)
    
    # 文件处理器 - 错误日志
    error_log_file = os.path.join(logs_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    
    # 文件处理器 - 访问日志
    access_log_file = os.path.join(logs_dir, 'access.log')
    access_handler = RotatingFileHandler(
        access_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(log_format)
    
    # 获取Flask应用日志器
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    
    # 创建访问日志器
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_handler)
    access_logger.propagate = False
    
    # 禁用默认的handler避免重复日志
    app.logger.propagate = False
    
    # 如果是开发环境，也输出到控制台
    if app.config.get('DEBUG', False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(log_format)
        app.logger.addHandler(console_handler)
    
    app.logger.info('日志系统初始化完成')
    
    return app.logger, access_logger

