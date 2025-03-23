import os
import logging
from logging.handlers import RotatingFileHandler
from flask import current_app


def _create_handler(log_file: str, max_bytes: int, backup_count: int,
                    log_level: str, log_format: str) -> RotatingFileHandler:
    """创建日志处理程序
    :param log_file: 日志文件路径
    :param max_bytes: 日志文件大小
    :param backup_count: 日志备份数量
    :param log_level: 日志级别
    :param log_format: 日志格式
    :return: RotatingFileHandler
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(str(log_file))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建处理程序
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )

    # 设置格式
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    # 设置日志级别
    handler.setLevel(getattr(logging, log_level.upper()))

    return handler


def setup_logger(app):
    """初始化应用主日志系统"""
    # 创建文件处理程序
    log_file = os.path.join(app.config['LOG_DIR'], app.config['LOG_FILE'])
    file_handler = _create_handler(
        log_file=log_file,
        max_bytes=app.config['LOG_MAX_BYTES'],
        backup_count=app.config['LOG_BACKUP_COUNT'],
        log_level=app.config['LOG_LEVEL'],
        log_format=app.config['LOG_FORMAT']
    )
    # 添加到应用日志器
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL'].upper()))
    # 记录应用启动
    app.logger.info('Application startup complete')


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器
    :param name: 日志记录器名称
    :return: 日志记录器
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        # 获取配置
        if current_app:
            log_level = current_app.config['LOG_LEVEL'].upper()
            log_format = current_app.config['LOG_FORMAT']
        else:
            log_level = 'INFO'
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        # 创建控制台处理程序
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        console_handler.setLevel(getattr(logging, log_level))

        logger.addHandler(console_handler)
        logger.setLevel(getattr(logging, log_level))

    return logger
