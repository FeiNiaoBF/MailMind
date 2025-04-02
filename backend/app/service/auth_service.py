"""
认证服务模块
处理用户认证和授权
"""
from typing import Dict, Any, Optional, List
from flask import current_app, session
from ..utils.logger import get_logger
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from ..models import User
from ..db.database import db
from datetime import datetime
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
        logger.debug("开始初始化认证服务")
        # 配置OAuth作用域
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',  # Gmail 只读权限
            'https://www.googleapis.com/auth/userinfo.email',  # 邮箱信息权限
            'https://www.googleapis.com/auth/userinfo.profile',  # 用户资料权限
            'openid'  # OpenID 认证
        ]
        logger.debug(f"配置的OAuth作用域: {self.scopes}")

        # 验证必要的环境变量
        required_vars = [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI"
        ]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.debug("环境变量验证通过")

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
        logger.debug("客户端配置创建完成")

        logger.info("OAuth2配置初始化成功")

    def get_auth_url(self, state: str) -> str:
        """获取Google认证URL"""
        logger.debug(f"开始生成认证URL，state: {state}")
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
                'prompt': 'consent select_account'  # 添加 select_account 以确保每次都显示账号选择
            }
            logger.debug(f"构建的URL参数: {params}")

            # 生成授权URL
            authorization_url = f"{self.client_config['web']['auth_uri']}?{urlencode(params)}"
            logger.debug(f"生成的认证URL: {authorization_url}")
            return authorization_url

        except Exception as e:
            logger.error(f"生成认证URL失败: {str(e)}")
            raise

    def handle_callback(self, authorization_response: str) -> Optional[Dict[str, Any]]:
        """处理OAuth回调"""
        logger.debug(f"开始处理OAuth回调，URL: {authorization_response}")
        try:
            # 解析回调URL
            parsed_url = urlparse(authorization_response)
            query_params = parse_qs(parsed_url.query)
            logger.debug(f"解析的回调参数: {query_params}")

            # 获取授权码
            code = query_params.get('code', [None])[0]
            if not code:
                logger.error("未收到Gmail授权码")
                raise ValueError("Authorization code not found")

            logger.debug(f"收到授权码: {code[:10]}...")  # 只记录前10个字符

            # 创建新的 Flow 实例
            logger.debug("创建新的Flow实例")
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")
            )

            # 获取令牌
            logger.debug("开始获取令牌")
            flow.fetch_token(code=code)
            credentials = flow.credentials
            logger.debug("令牌获取成功")

            # 验证ID令牌
            logger.debug("开始验证ID令牌")
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                self.client_config['web']['client_id']
            )
            logger.debug(f"ID令牌验证成功，用户邮箱: {id_info.get('email')}")

            # 构建用户信息
            user_info = {
                'email': id_info.get('email'),
                'name': id_info.get('name', ''),
                'picture': id_info.get('picture', ''),
                'provider_id': id_info.get('sub'),
                'auth_provider': 'google'
            }
            logger.debug(f"构建的用户信息: {user_info}")

            # 保存凭据到会话
            session['credentials'] = credentials_to_dict(credentials)
            session['user'] = user_info
            logger.debug("凭据和用户信息已保存到会话")

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
        logger.debug("开始撤销访问令牌")
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

    def get_or_create_user(self, user_info: Dict[str, Any], credentials: Dict[str, Any]) -> Optional[User]:
        """获取或创建用户"""
        logger.debug(f"开始获取或创建用户，邮箱: {user_info.get('email')}")
        try:
            user = User.query.filter_by(email=user_info['email']).first()
            logger.debug(f"数据库查询结果: {'用户存在' if user else '用户不存在'}")

            if not user:
                logger.info(f"创建新用户: {user_info['email']}")
                user = User(
                    email=user_info['email'],
                    provider_id=user_info['provider_id'],
                    auth_provider='google',
                    access_token=credentials['token'],
                    refresh_token=credentials['refresh_token']
                )
                db.session.add(user)
                logger.debug("新用户已添加到会话")
            else:
                logger.info(f"更新现有用户: {user_info['email']}")
                user.access_token = credentials['token']
                user.refresh_token = credentials['refresh_token']
                user.last_login = datetime.now()
                logger.debug("用户信息已更新")

            try:
                db.session.commit()
                logger.info("数据库更改已提交")
                logger.debug(f"用户操作完成，用户ID: {user.id}")
                return user
            except Exception as e:
                logger.error(f"数据库提交失败: {str(e)}")
                db.session.rollback()
                return None

        except Exception as e:
            logger.error(f"获取或创建用户失败: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        logger.debug(f"开始根据邮箱查询用户: {email}")
        try:
            user = User.query.filter_by(email=email).first()
            logger.debug(f"查询结果: {'找到用户' if user else '未找到用户'}")
            return user
        except Exception as e:
            logger.error(f"根据邮箱获取用户失败: {str(e)}")
            return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """获取所有用户数据"""
        logger.debug("开始获取所有用户数据")
        try:
            users = User.query.all()
            logger.debug(f"数据库查询到 {len(users)} 个用户")

            user_list = []
            for user in users:
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'auth_provider': user.auth_provider,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'has_access_token': bool(user.access_token),
                    'has_refresh_token': bool(user.refresh_token)
                }
                user_list.append(user_data)
                logger.debug(f"处理用户数据: {user_data}")

            logger.debug(f"成功获取 {len(user_list)} 个用户数据")
            return user_list
        except Exception as e:
            logger.error(f"获取所有用户数据失败: {str(e)}")
            return []
