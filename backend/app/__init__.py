"""
应用工厂模块
"""
from flask import Flask
from flask_cors import CORS

from .config.config import BaseConfig


def create_app(config_class=BaseConfig):
    """创建Flask应用
    :param config_class: 配置类
    :return: Flask应用
    """
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(config_class)
    config_class.init_app(app)

    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册蓝图
    from .api.base import bp as api_bp
    app.register_blueprint(api_bp, url_prefix=app.config['API_PREFIX'])

    return app
