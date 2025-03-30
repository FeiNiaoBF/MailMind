"""
令牌生成工具
"""
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token, create_refresh_token
from backend.app.config.config import Config

def generate_access_token(identity: str) -> str:
    """
    生成访问令牌

    Args:
        identity: 用户标识

    Returns:
        str: 访问令牌
    """
    return create_access_token(
        identity=identity,
        expires_delta=Config.JWT_ACCESS_TOKEN_EXPIRES
    )

def generate_refresh_token(identity: str) -> str:
    """
    生成刷新令牌

    Args:
        identity: 用户标识

    Returns:
        str: 刷新令牌
    """
    return create_refresh_token(
        identity=identity,
        expires_delta=Config.JWT_REFRESH_TOKEN_EXPIRES
    )

def generate_tokens(identity: str) -> dict:
    """
    生成访问令牌和刷新令牌

    Args:
        identity: 用户标识

    Returns:
        dict: 包含访问令牌和刷新令牌的字典
    """
    return {
        'access_token': generate_access_token(identity),
        'refresh_token': generate_refresh_token(identity)
    }
