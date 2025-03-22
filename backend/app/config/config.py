import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class BaseConfig:
    """基础配置类"""
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    API_PREFIX = '/api'

    # SQLAlchemy 配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mailmind.db'

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
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')

    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        # 确保日志目录存在
        log_dir = os.path.dirname(cls.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 验证必要的配置
        required_vars = [
            'MAIL_USERNAME',
            'MAIL_PASSWORD',
            'AI_MODEL_KEY'
        ]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


class DevelopmentConfig(BaseConfig):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///mailmind-dev.db'


class TestingConfig(BaseConfig):
    """测试环境配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

    # 测试环境默认值
    MAIL_USERNAME = 'test@example.com'
    MAIL_PASSWORD = 'test-password'
    AI_MODEL_KEY = 'test-api-key'

    @classmethod
    def init_app(cls, app):
        """测试环境特定的初始化"""
        # 确保日志目录存在
        log_dir = os.path.dirname(cls.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # 测试环境不需要验证配置
        pass


class ProductionConfig(BaseConfig):
    """生产环境配置"""
    @classmethod
    def init_app(cls, app):
        """生产环境特定的初始化"""
        BaseConfig.init_app(app)

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
