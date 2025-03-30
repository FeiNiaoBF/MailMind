"""
Flask应用初始化
"""
from flask import Flask
from .config import config
from .routes.views import views
from .routes.chat_routes import chat_bp
from .routes.ai_routes import ai_bp
from .routes.auth_routes import auth_bp
from .utils.logger import init_logger

def create_app(config_name='dev'):
    """创建Flask应用"""
    app = Flask(__name__, template_folder='../templates')

    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # 初始化日志
    init_logger(app)
    app.logger.info('MailMind startup')

    # 注册蓝图
    app.register_blueprint(views)
    app.register_blueprint(chat_bp)
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    return app
