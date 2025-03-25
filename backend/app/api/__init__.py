"""
API package for MailMind.
"""
from flask import Blueprint
from backend.app.api.auth import auth_bp

api_bp = Blueprint('api', __name__)

def init_app(app):
    """初始化API蓝图"""
    app.register_blueprint(auth_bp)
