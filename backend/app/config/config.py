"""
配置文件
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置类"""
    # 应用安全
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-for-development')
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    # 数据库
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///data.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(os.path.dirname(__file__), '../logs')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # AI配置
    AI_API_KEY = os.getenv('AI_API_KEY', 'your-api-key-here')
    AI_MODEL = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '1000'))

    @classmethod
    def init_app(cls, app):
        """统一初始化方法"""
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置映射
config = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}
