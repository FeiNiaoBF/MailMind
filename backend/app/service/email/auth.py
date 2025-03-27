"""
邮件认证服务
"""
from typing import Dict, Any, Optional
from backend.app.models import User
from backend.app.service.email.providers.gmail import GmailProvider
from backend.app.config.config import Config
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

class EmailAuthService:
    """邮件认证服务"""

    def __init__(self):
        """初始化邮件认证服务"""
        self.provider = GmailProvider(Config.GMAIL_CLIENT_CONFIG)

    def get_authorization_url(self) -> str:
        """获取授权URL
        :return: 授权URL
        """
        try:
            return self.provider.get_authorization_url()
        except Exception as e:
            logger.error(f"获取授权URL失败: {str(e)}")
            raise Exception(f"获取授权URL失败: {str(e)}")

    def get_user_info(self, code: str) -> Dict[str, Any]:
        """获取用户信息
        :param code: 授权码
        :return: 用户信息
        """
        try:
            return self.provider.get_user_info(code)
        except Exception as e:
            logger.error(f"获取用户信息失败: {str(e)}")
            raise Exception(f"获取用户信息失败: {str(e)}")

    def get_access_token(self, code: str) -> str:
        """获取访问令牌
        :param code: 授权码
        :return: 访问令牌
        """
        try:
            return self.provider.get_access_token(code)
        except Exception as e:
            logger.error(f"获取访问令牌失败: {str(e)}")
            raise Exception(f"获取访问令牌失败: {str(e)}")

    def refresh_token(self, refresh_token: str) -> str:
        """刷新访问令牌
        :param refresh_token: 刷新令牌
        :return: 新的访问令牌
        """
        try:
            return self.provider.refresh_token(refresh_token)
        except Exception as e:
            logger.error(f"刷新访问令牌失败: {str(e)}")
            raise Exception(f"刷新访问令牌失败: {str(e)}")

    def revoke_token(self, token: str) -> bool:
        """撤销访问令牌
        :param token: 访问令牌
        :return: 是否成功
        """
        try:
            return self.provider.revoke_token(token)
        except Exception as e:
            logger.error(f"撤销访问令牌失败: {str(e)}")
            raise Exception(f"撤销访问令牌失败: {str(e)}")

    def validate_token(self, token: str) -> bool:
        """验证访问令牌
        :param token: 访问令牌
        :return: 是否有效
        """
        try:
            return self.provider.validate_token(token)
        except Exception as e:
            logger.error(f"验证访问令牌失败: {str(e)}")
            raise Exception(f"验证访问令牌失败: {str(e)}")
