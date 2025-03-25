"""
应用工厂模块
"""
from flask import Flask
from flask_cors import CORS

from .config.config import config
from .utils.logger import setup_logger
from .db.database import db
from .api.base import bp as base_bp


def create_app(config_name='default') -> Flask:
    """创建Flask应用
    :param config_name: 配置名称
    :return: Flask应用
    """
    app = Flask(__name__)

    # 加载配置
    cfg = config[config_name]
    app.config.from_object(cfg)
    cfg.init_app(app)

    # 初始化日志系统
    setup_logger(app)

    # 初始化数据库
    db.init_app(app)

    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册蓝图
    app.register_blueprint(base_bp, url_prefix=app.config['API_PREFIX'])

    return app
