"""
Flask应用初始化
"""
from flask import Flask, current_app
from flask_cors import CORS
from .config import config

from .routes import auth_bp, ai_bp, email_bp, views
from .utils.logger import init_logger, get_logger
from .db.database import init_db
from .service.service_manager import ServiceManager

logger = get_logger(__name__)

def create_app(config_name='dev'):
    """创建Flask应用"""
    app = Flask(__name__, template_folder='../templates')

    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化日志
    init_logger(app)
    app.logger.info('MailMind startup')

    # 初始化扩展
    CORS(app)  # 启用CORS

    # 初始化数据库
    try:
        init_db(app)
    except:
        raise RuntimeError('数据库初始化失败')

    # 注册蓝图
    app.register_blueprint(views)
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(email_bp, url_prefix='/api/email')

    return app
