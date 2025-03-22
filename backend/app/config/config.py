import os
from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """基础配置类"""

    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'

    # 邮箱配置
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_SERVER = os.getenv('EMAIL_SERVER')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '993'))

    # AI配置
    AI_API_KEY = os.getenv('AI_API_KEY')

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')

    @classmethod
    def init_app(cls, app):
        """初始化应用配置"""
        # 确保日志目录存在
        log_dir = os.path.dirname(cls.LOG_FILE)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 验证必要的配置
        required_vars = [
            'EMAIL_ADDRESS',
            'EMAIL_PASSWORD',
            'EMAIL_SERVER',
            'AI_API_KEY'
        ]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


class DevelopmentConfig(BaseConfig):
    """开发配置类"""

    DEBUG = True
    TESTING = False

    # Override logging config for development
    LOG_LEVEL = 'DEBUG'

    # Development specific settings
    FLASK_ENV = 'development'

    # Development database
    DATABASE_URI = 'sqlite:///dev.db'


class ProductionConfig(BaseConfig):
    """生产配置类"""

    DEBUG = False
    TESTING = False

    # Override logging config for production
    LOG_LEVEL = 'INFO'

    # Production specific settings
    FLASK_ENV = 'production'

    # Ensure all production configs are loaded from environment variables
    def __init__(self):
        super().__init__()
        self.SECRET_KEY = self._get_required_env('SECRET_KEY')
        self.JWT_SECRET_KEY = self._get_required_env('JWT_SECRET_KEY')
        self.DATABASE_URI = self._get_required_env('DATABASE_URI')

    @staticmethod
    def _get_required_env(key):
        """Get required environment variable or raise an error."""
        import os
        value = os.getenv(key)
        if value is None:
            raise ValueError(f'Environment variable {key} is required in production')
        return value


class TestConfig(BaseConfig):
    """测试配置类"""

    DEBUG = True
    TESTING = True

    # Override logging config for testing
    LOG_LEVEL = 'DEBUG'

    # Test database
    DATABASE_URI = 'sqlite:///test.db'
