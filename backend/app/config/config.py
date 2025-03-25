"""
配置文件
"""
import os
from logging import DEBUG
from datetime import timedelta

from dotenv import load_dotenv
from ..utils.logger import get_logger

# 加载环境变量
load_dotenv()

# 创建配置文件的日志器
logger = get_logger(__name__)


class Config:
    """基础配置类"""
    # 基础配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    DEBUG = False
    TESTING = False

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/mailmind.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮件配置
    EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'mailtrap')
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'sandbox.smtp.mailtrap.io')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 2525))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'test@mailtrap.io')

    # Gmail OAuth2 配置
    GMAIL_CLIENT_CONFIG = {
        "web": {
            "client_id": os.getenv("GMAIL_CLIENT_ID"),
            "project_id": os.getenv("GMAIL_PROJECT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
            "redirect_uris": [os.getenv("GMAIL_REDIRECT_URI", "http://localhost:5000/auth/callback")]
        }
    }

    # Gmail API 配置
    GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI", "http://localhost:5000/auth/callback")

    # IMAP配置
    IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.getenv('IMAP_PORT', 993))

    # AI配置
    AI_MODEL_TYPE = os.getenv('AI_MODEL_TYPE', 'openai')
    AI_MODEL_KEY = os.getenv('AI_MODEL_KEY')

    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 5242880))
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    LOG_OUTPUT_MODE = os.getenv('LOG_OUTPUT_MODE', 'both')

    # 默认发件人邮箱
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@mailmind.com")


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/dev.db'
    EMAIL_PROVIDER = 'mailtrap'


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 使用内存数据库
    EMAIL_PROVIDER = 'mailtrap'

    # 测试用 Gmail API 配置
    GMAIL_CLIENT_ID = 'test_client_id'
    GMAIL_CLIENT_SECRET = 'test_client_secret'
    GMAIL_REDIRECT_URI = 'http://localhost:5000/api/auth/gmail/callback'

    # 测试用 JWT 配置
    JWT_SECRET_KEY = 'test_jwt_secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)

    # 测试用 AI 配置
    AI_MODEL_TYPE = 'test_model'
    AI_MODEL_KEY = 'test_key'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    EMAIL_PROVIDER = 'gmail'

    # 生产环境特定配置
    SQLALCHEMY_DATABASE_URI = os.getenv('PROD_DATABASE_URL')
    SECRET_KEY = os.getenv('PROD_SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('PROD_JWT_SECRET_KEY')


# 配置映射
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
