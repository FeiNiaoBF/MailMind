"""
路由包初始化模块
"""
from .auth_routes import auth_bp
from .chat_routes import chat_bp

__all__ = ['auth_bp', 'chat_bp']
