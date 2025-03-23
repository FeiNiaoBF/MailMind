import os
from logging import DEBUG

from dotenv import load_dotenv
from ..utils.logger import get_logger

# 加载环境变量
load_dotenv()

# 创建配置文件的日志器
logger = get_logger(__name__)


class BaseConfig:
    """基础配置类"""
    # Flask 配置
    API_PREFIX = '/api'
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', 'on', '1']
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'

    # SQLAlchemy 配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mailmind.db'
    logger.info(f"数据库URI: {SQLALCHEMY_DATABASE_URI}")

    # 邮件服务器配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # IMAP 配置（用于读取邮件）
    IMAP_SERVER = os.environ.get('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.environ.get('IMAP_PORT', '993'))

    # AI 模型配置
    AI_MODEL_TYPE = os.environ.get('AI_MODEL_TYPE', 'openai')
    AI_MODEL_KEY = os.environ.get('AI_MODEL_KEY')

    # 任务调度器配置
    SCHEDULER_API_ENABLED = True

    # 日志配置
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', '10485760'))
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '5'))
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_OUTPUT_MODE = os.environ.get('LOG_OUTPUT_MODE', 'both').lower()
    LOG_FILE = os.path.join(LOG_DIR, 'app.log')  # 默认日志文件
    logger.info(f"日志配置: 目录={LOG_DIR}, 文件={LOG_FILE}, 级别={LOG_LEVEL}")

    logger.info("配置文件加载完成")

    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        logger.info("开始初始化应用配置")
        # 确保日志目录存在
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)
            logger.info(f"创建日志目录: {cls.LOG_DIR}")

        # 验证必要的配置
        # required_vars = [
        #     'MAIL_USERNAME',
        #     'MAIL_PASSWORD',
        #     'AI_MODEL_KEY'
        # ]
        # missing_vars = [var for var in required_vars if not getattr(cls, var)]
        # if missing_vars:
        #     raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        logger.info("应用配置初始化完成")


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///dev/mailmind.db'
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = os.path.join(BaseConfig.LOG_DIR, 'dev.log')


class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    LOG_LEVEL = 'DEBUG'
    LOG_FILE = os.path.join(BaseConfig.LOG_DIR, 'test.log')

    @classmethod
    def init_app(cls, app):
        """测试环境特定的初始化"""
        # 确保日志目录存在
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)
        # 测试环境不需要验证配置
        pass


class ProductionConfig(BaseConfig):
    """生产环境配置"""

    @classmethod
    def init_app(cls, app):
        """生产环境特定的初始化"""
        BaseConfig.init_app(app)

        # 数据库配置
        if not app.config['SQLALCHEMY_DATABASE_URI']:
            raise ValueError('SQLALCHEMY_DATABASE_URI is not set')
        os.getenv('DATABASE_URL')
        # 日志配置
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            cls.LOG_FILE,
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(getattr(logging, cls.LOG_LEVEL))

        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, cls.LOG_LEVEL))
        app.logger.info('MailMind startup')


# 配置字典，用于选择不同环境的配置
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
