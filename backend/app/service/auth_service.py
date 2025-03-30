"""
认证服务模块
处理用户认证和授权
"""
from typing import Dict, Any, Optional
from flask import current_app, session
from ..utils.logger import get_logger
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
from urllib.parse import urlencode, parse_qs, urlparse
from dotenv import load_dotenv

logger = get_logger(__name__)

# 加载环境变量
load_dotenv()

def credentials_to_dict(credentials: Credentials) -> dict:
    """将凭据转换为字典格式"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

class AuthService:
    """认证服务类"""

    def __init__(self):
        """初始化认证服务"""
        # 配置OAuth作用域
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid'
        ]

        # 验证必要的环境变量
        required_vars = [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")

        # 创建客户端配置
        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "project_id": os.getenv("GOOGLE_PROJECT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")]
            }
        }

        logger.info("OAuth配置初始化成功")

    def get_auth_url(self, state: str) -> str:
        """获取Google认证URL"""
        try:
            # 构建授权URL参数
            params = {
                'client_id': self.client_config['web']['client_id'],
                'redirect_uri': os.getenv("GOOGLE_REDIRECT_URI"),
                'scope': ' '.join(self.scopes),
                'response_type': 'code',
                'access_type': 'offline',
                'include_granted_scopes': 'true',
                'state': state,
                'prompt': 'consent'
            }

            # 生成授权URL
            authorization_url = f"{self.client_config['web']['auth_uri']}?{urlencode(params)}"

            logger.info(f"生成认证URL: {authorization_url}")
            return authorization_url

        except Exception as e:
            logger.error(f"生成认证URL失败: {str(e)}")
            raise

    def handle_callback(self, authorization_response: str) -> Optional[Dict[str, Any]]:
        """处理OAuth回调"""
        try:
            # 解析回调URL
            parsed_url = urlparse(authorization_response)
            query_params = parse_qs(parsed_url.query)

            # 获取授权码
            code = query_params.get('code', [None])[0]
            if not code:
                logger.error("未收到授权码")
                raise ValueError("Authorization code not found")

            logger.info(f"收到授权码: {code[:10]}...")  # 只记录前10个字符

            # 创建新的 Flow 实例
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
            )

            # 获取令牌
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # 验证ID令牌
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                self.client_config['web']['client_id']
            )

            logger.info(f"成功获取用户信息: {id_info.get('email')}")

            # 构建用户信息
            user_info = {
                'email': id_info.get('email'),
                'name': id_info.get('name', ''),
                'picture': id_info.get('picture', ''),
                'provider_id': id_info.get('sub'),
                'auth_provider': 'google'
            }

            # 保存凭据到会话
            session['credentials'] = credentials_to_dict(credentials)
            session['user'] = user_info

            return {
                'user': user_info
            }

        except ValueError as e:
            logger.error(f"验证失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"处理回调失败: {str(e)}")
            raise

    def revoke_token(self, token: str) -> bool:
        """撤销访问令牌"""
        try:
            import requests
            response = requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': token},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )
            success = response.status_code == 200
            if success:
                logger.info("令牌撤销成功")
            else:
                logger.error(f"令牌撤销失败: {response.text}")
            return success
        except Exception as e:
            logger.error(f"撤销令牌失败: {str(e)}")
            return False
