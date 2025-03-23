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
    if log_dir:  # 只有当目录不为空时才创建
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # 创建处理程序
    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'  # 添加 UTF-8 编码支持
    )

    # 设置格式
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    # 设置日志级别
    handler.setLevel(getattr(logging, log_level.upper()))

    return handler


def setup_logger(app):
    """初始化应用主日志系统"""
    # 清除所有现有的处理程序
    app.logger.handlers = []

    # 获取日志输出模式
    output_mode = app.config.get('LOG_OUTPUT_MODE', 'both').lower()

    # 创建文件处理程序
    if output_mode in ['file', 'both']:
        log_file = app.config.get('LOG_FILE', os.path.join(app.config.get('LOG_DIR', 'logs'), 'app.log'))
        file_handler = _create_handler(
            log_file=log_file,
            max_bytes=app.config.get('LOG_MAX_BYTES', 5242880),
            backup_count=app.config.get('LOG_BACKUP_COUNT', 5),
            log_level=app.config.get('LOG_LEVEL', 'INFO'),
            log_format=app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        app.logger.addHandler(file_handler)

    # 创建控制台处理程序
    if output_mode in ['console', 'both']:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')))
        console_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper()))
        app.logger.addHandler(console_handler)

    # 设置日志级别
    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO').upper()))

    # 记录应用启动
    app.logger.info('日志系统初始化完成')


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器
    :param name: 日志记录器名称
    :return: 日志记录器
    """
    logger = logging.getLogger(name)

    # 如果已经有处理程序，直接返回
    if logger.handlers:
        return logger

    # 获取配置
    if current_app:
        log_level = current_app.config['LOG_LEVEL'].upper()
        log_format = current_app.config['LOG_FORMAT']
        log_file = current_app.config['LOG_FILE']
        output_mode = current_app.config.get('LOG_OUTPUT_MODE', 'both').lower()
    else:
        # 如果没有 current_app 上下文，根据环境变量决定日志文件
        log_level = 'INFO'
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        env = os.environ.get('FLASK_ENV', 'development')
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

        # 根据环境选择日志文件
        if env == 'testing':
            log_file = os.path.join(log_dir, 'test.log')
        elif env == 'development':
            log_file = os.path.join(log_dir, 'dev.log')
        else:
            log_file = os.path.join(log_dir, 'app.log')

        output_mode = 'both'

    # 创建文件处理程序
    if output_mode in ['file', 'both']:
        file_handler = _create_handler(
            log_file=log_file,
            max_bytes=10485760,  # 10MB
            backup_count=5,
            log_level=log_level,
            log_format=log_format
        )
        logger.addHandler(file_handler)

    # 创建控制台处理程序
    if output_mode in ['console', 'both']:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        console_handler.setLevel(getattr(logging, log_level))
        logger.addHandler(console_handler)

    logger.setLevel(getattr(logging, log_level))
    return logger


def debug_print(*args, **kwargs):
    """当APP_DEBUG为True时打印调试信息

    使用示例:
        debug_print("变量值:", value)
        debug_print("多个值:", value1, value2)
        debug_print("带格式:", f"值={value}")
        debug_print("带关键字参数:", name="test", value=123)
    """
    try:
        if current_app and current_app.config.get('DEBUG', False):
            # 获取调用者的文件名和行号
            import inspect
            frame = inspect.currentframe().f_back
            filename = os.path.basename(frame.f_code.co_filename)
            line_number = frame.f_lineno

            # 构建调试信息
            debug_info = []
            if args:
                debug_info.extend(str(arg) for arg in args)
            if kwargs:
                debug_info.extend(f"{k}={v}" for k, v in kwargs.items())

            # 使用应用日志器记录调试信息
            current_app.logger.debug(
                f"[{filename}:{line_number}] {' '.join(debug_info)}"
            )
    except Exception as e:
        # 如果出现任何错误，静默处理
        pass
