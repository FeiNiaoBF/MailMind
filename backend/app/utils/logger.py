"""
日志工具模块
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import current_app


def _create_handler(log_file: str, max_bytes: int, backup_count: int,
                    log_level: str, log_format: str, encoding: str = 'utf-8') -> RotatingFileHandler:
    """创建日志处理程序
    :param log_file: 日志文件路径
    :param max_bytes: 日志文件大小
    :param backup_count: 日志备份数量
    :param log_level: 日志级别
    :param log_format: 日志格式
    :param encoding: 文件编码
    :return: RotatingFileHandler
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(str(log_file))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建处理程序
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding
    )

    # 设置格式
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    # 设置日志级别
    if isinstance(log_level, str):
        handler.setLevel(getattr(logging, log_level.upper()))
    else:
        handler.setLevel(logging.INFO)

    return handler


def init_logger(app):
    """初始化日志配置
    :param app: Flask应用实例
    """
    # 设置日志级别
    log_level = getattr(logging, app.config['LOG_LEVEL'].upper())

    # 配置日志格式
    formatter = logging.Formatter(
        app.config['LOG_FORMAT'],
        datefmt=app.config['LOG_DATE_FORMAT']
    )

    # 配置控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # 配置文件日志
    log_file = os.path.join(app.config['LOG_DIR'], app.config['LOG_FILE'])
    file_handler = _create_handler(
        log_file=log_file,
        max_bytes=app.config['LOG_MAX_BYTES'],
        backup_count=app.config['LOG_BACKUP_COUNT'],
        log_level=app.config['LOG_LEVEL'],
        log_format=app.config['LOG_FORMAT'],
        encoding=app.config['LOG_ENCODING']
    )

    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有的处理器
    root_logger.handlers = []

    # 添加处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 设置Flask应用日志器
    app.logger.setLevel(log_level)
    app.logger.handlers = []  # 清除现有的处理器
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)


def get_logger(name):
    """获取日志记录器
    :param name: 日志记录器名称
    :return: 日志记录器实例
    """
    logger = logging.getLogger(name)
    # 确保日志器使用正确的编码
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
    return logger


def debug_print(*args):
    """调试打印函数
    仅在调试模式下打印信息
    """
    if current_app.debug:
        print(*args)
