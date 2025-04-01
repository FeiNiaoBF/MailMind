"""
路由包初始化模块
"""
from .auth_routes import auth_bp
from .ai_routes import ai_bp
from .email_routes import email_bp
from .views import views

__all__ = ['auth_bp', 'ai_bp', 'email_bp', 'views']
