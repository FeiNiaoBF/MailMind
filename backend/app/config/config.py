"""
配置文件
主要包含基础应用配置和日志配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    # 应用安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-for-development')

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/mailmind.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10
    LOG_ENCODING = 'utf-8'

    # 网络配置
    PROXY_HOST = os.getenv('PROXY_HOST', '127.0.0.1')
    PROXY_PORT = os.getenv('PROXY_PORT', '7890')

    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        # 确保日志目录存在
        if not os.path.exists(cls.LOG_DIR):
            os.makedirs(cls.LOG_DIR)

        # 设置日志文件路径
        cls.LOG_PATH = os.path.join(cls.LOG_DIR, cls.LOG_FILE)

        # 设置默认编码
        import sys
        if sys.stdout.encoding != 'utf-8':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    FLASK_ENV = 'dev'
    FLASK_DEBUG = 1
    FLASK_RUN_HOST = '127.0.0.1'
    FLASK_RUN_PORT = 5000


class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    FLASK_ENV = 'test'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    FLASK_ENV = 'prod'
    FLASK_DEBUG = 0


# 配置映射
config = {
    'dev': DevelopmentConfig,
    'test': TestingConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}
