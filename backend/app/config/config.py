import os
from datetime import timedelta


class BaseConfig:
    """基础配置类"""

    # Flask config
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    FLASK_APP = 'run.py'

    # Logging config
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    LOG_DIR = 'logs'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 10

    # API config
    API_PREFIX = '/api'

    # JWT config
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # CORS config
    CORS_ORIGINS = ['*']

    # Database config (placeholder for future use)
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///app.db')


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
