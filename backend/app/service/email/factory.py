"""
邮箱 factory 模块
"""
from typing import Union, Dict, Type
from flask import current_app
from .interface import EmailServiceInterface
from .mailtrap import MailtrapEmailService
from .gmail import GmailEmailService
from .auth_providers import GmailAuthProvider, MailtrapAuthProvider
from backend.app.config import Config


class EmailFactory:
    """
    邮箱工厂类
    """

    @staticmethod
    def create_auth_provider() -> Union[GmailAuthProvider, MailtrapAuthProvider]:
        """
        创建认证提供者
        ：return: Union[GmailAuthProvider, MailtrapAuthProvider]
        """
        env = current_app.config.get('FLASK_ENV', 'development')
        # 根据环境配置返回对应的认证服务
        if env == 'production':
            return GmailAuthProvider(
                client_id=current_app.config['GMAIL_CLIENT_ID'],
                client_secret=current_app.config['GMAIL_CLIENT_SECRET'],
                redirect_uri=current_app.config['GMAIL_REDIRECT_URI']
            )
        else:
            return MailtrapAuthProvider(
                api_token=current_app.config['MAILTRAP_API_TOKEN'],
                inbox_id=current_app.config['MAILTRAP_INBOX_ID']
            )

    @staticmethod
    def create_email_provider(user_id: int) -> Union[GmailProvider, MailtrapProvider]:
        """
        创建邮件服务提供者
        :param user_id: 用户ID
        :return: Union[GmailProvider, MailtrapProvider]
        """
        from backend.app.db.models import EmailCredential

        env = current_app.config['FLASK_ENV']
        credential = EmailCredential.query.filter_by(
            user_id=user_id,
            is_active=True
        ).first()

        if not credential:
            raise ValueError("No active email credential found")

        if env == 'production':
            return GmailProvider(credentials={
                'token': credential.access_token,
                'refresh_token': credential.refresh_token,
                'token_expiry': credential.token_expiry,
                'client_id': current_app.config['GMAIL_CLIENT_ID'],
                'client_secret': current_app.config['GMAIL_CLIENT_SECRET']
            })
        else:
            return MailtrapProvider(
                api_token=credential.access_token,
                inbox_id=current_app.config['MAILTRAP_INBOX_ID']
            )


class EmailServiceFactory:
    """邮件服务工厂类"""

    _providers: Dict[str, Type[EmailServiceInterface]] = {
        'mailtrap': MailtrapEmailService,
        'gmail': GmailEmailService
    }

    @classmethod
    def create(cls, provider_name: str = None) -> EmailServiceInterface:
        """创建邮件服务实例

        Args:
            provider_name: 服务提供商名称，如果为None则从配置中读取

        Returns:
            EmailServiceInterface: 邮件服务实例

        Raises:
            ValueError: 当指定的服务提供商不存在时
        """
        if provider_name is None:
            provider_name = Config.EMAIL_PROVIDER

        if provider_name not in cls._providers:
            raise ValueError(f"Unsupported email provider: {provider_name}")

        provider_class = cls._providers[provider_name]
        return provider_class()

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[EmailServiceInterface]) -> None:
        """注册新的邮件服务提供商

        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        cls._providers[name] = provider_class
