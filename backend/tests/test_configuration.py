"""
配置测试模块

测试基本配置功能，包括:
1. 环境配置
2. 必要配置项
"""
import pytest
import os
from backend.app.config import Config, DevelopmentConfig, TestingConfig, ProductionConfig

class TestEnvironmentConfig:
    """测试环境配置"""

    def test_development_config(self):
        """测试开发环境配置"""
        config = DevelopmentConfig()
        assert config.DEBUG is True
        assert config.TESTING is False
        assert config.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///')

    def test_testing_config(self):
        """测试测试环境配置"""
        config = TestingConfig()
        assert config.DEBUG is False
        assert config.TESTING is True
        assert config.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///')

    def test_production_config(self):
        """测试生产环境配置"""
        config = ProductionConfig()
        assert config.DEBUG is False
        assert config.TESTING is False
        assert config.SQLALCHEMY_DATABASE_URI.startswith('postgresql://')

class TestRequiredConfig:
    """测试必要配置项"""

    def test_required_config_values(self):
        """测试必需配置值"""
        config = Config()

        # 验证必需配置项
        assert hasattr(config, 'SECRET_KEY')
        assert hasattr(config, 'SQLALCHEMY_DATABASE_URI')
        assert hasattr(config, 'MAIL_SERVER')
        assert hasattr(config, 'MAIL_PORT')

        # 验证配置值不为空
        assert config.SECRET_KEY is not None
        assert config.SQLALCHEMY_DATABASE_URI is not None
        assert config.MAIL_SERVER is not None
        assert config.MAIL_PORT is not None
