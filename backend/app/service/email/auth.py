"""
Gmail 认证服务
"""
from typing import Dict, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from .interface import EmailAuthInterface
from backend.app.config import Config

class EmailAuthService(EmailAuthInterface):
    """Gmail 认证服务实现"""

    def __init__(self):
        self.SCOPES = [
            # 查看自己的电子邮件及设置
            'https://www.googleapis.com/auth/gmail.readonly',
            # 以自己的身份发送电子邮件
            'https://www.googleapis.com/auth/gmail.send',
            # 在自己的 Gmail 帐号中阅读、撰写和发送电子邮件
            'https://www.googleapis.com/auth/gmail.modify'
        ]
        # 用于身份验证流程管理
        self.flow = Flow.from_client_config(
            Config.GMAIL_CLIENT_CONFIG,
            scopes=self.SCOPES,
            redirect_uri=Config.GMAIL_REDIRECT_URI
        )

    def authenticate(self, user_id: int, **kwargs) -> Dict:
        """获取认证URL和状态
        :param user_id: 用户ID
        :return: 认证URL和状态
        """
        auth_url, state = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )

        return {
            'auth_url': auth_url,
            'state': state,
            'user_id': user_id
        }

    def handle_callback(self, code: str, state: str) -> Dict:
        """处理认证回调
        :param code: 认证码
        :param state: 状态
        """
        try:
            self.flow.fetch_token(code=code)
            credentials = self.flow.credentials

            return {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
        except Exception as e:
            raise Exception(f"Failed to handle callback: {str(e)}")

    def refresh_token(self, credentials: Dict) -> Dict:
        """刷新认证令牌
        :param credentials: 令牌信息
        :return: 刷新后的令牌信息
        """
        try:
            creds = Credentials.from_authorized_user_info(credentials)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                return {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
            return credentials
        except Exception as e:
            raise Exception(f"Failed to refresh token: {str(e)}")

    def get_provider_name(self) -> str:
        """获取提供者名称"""
        return 'gmail'
