"""
认证服务模块
处理用户认证和授权
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from flask import current_app, session, redirect, url_for
from flask_jwt_extended import create_access_token
from ..models import User
from ..db.database import db
from ..utils.logger import get_logger
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import socket
import httpx
from dotenv import load_dotenv

logger = get_logger(__name__)

# 加载环境变量
load_dotenv()

# 设置socket超时
socket.setdefaulttimeout(30)

# 代理配置
PROXY_HOST = os.getenv('PROXY_HOST', '127.0.0.1')
PROXY_PORT = os.getenv('PROXY_PORT', '7890')
PROXIES = {
    'http://': f'http://{PROXY_HOST}:{PROXY_PORT}',
    'https://': f'http://{PROXY_HOST}:{PROXY_PORT}'
}

def create_http_client(timeout: float = 60.0, retries: int = 3) -> httpx.Client:
    """创建带有重试机制的HTTP客户端"""
    transport = httpx.HTTPTransport(
        retries=retries,
        verify=False  # 禁用SSL验证
    )

    # 设置更细粒度的超时控制
    timeouts = httpx.Timeout(
        connect=5.0,       # 减少连接超时
        read=timeout,      # 读取超时
        write=5.0,        # 写入超时
        pool=5.0          # 连接池超时
    )

    try:
        client = httpx.Client(
            proxies=PROXIES,
            timeout=timeouts,
            verify=False,      # 如果有SSL证书问题，可以禁用验证
            follow_redirects=True,  # 允许重定向
            transport=transport,
            trust_env=True    # 信任环境变量中的代理设置
        )
        logger.info(f"HTTP客户端创建成功，代理配置: {PROXIES}")
        return client
    except Exception as e:
        logger.error(f"创建HTTP客户端失败: {str(e)}")
        raise

def check_google_connection(max_retries: int = 3) -> bool:
    """检查与Google服务的连接"""
    urls = [
        "https://www.google.com",  # 添加更基础的Google服务检查
        "https://accounts.google.com",
        "https://oauth2.googleapis.com/token",  # 修改为正确的OAuth端点
        "https://www.googleapis.com/oauth2/v2/certs"  # 添加证书端点
    ]

    for attempt in range(max_retries):
        try:
            with create_http_client(timeout=10.0) as client:
                # 首先测试代理连接
                try:
                    logger.info("测试代理服务器连接...")
                    proxy_test = client.get("http://www.google.com/generate_204")
                    logger.info(f"代理测试响应状态码: {proxy_test.status_code}")
                    if proxy_test.status_code in [204, 302]:
                        logger.info("代理服务器连接正常")
                    else:
                        logger.warning(f"代理服务器返回异常状态码: {proxy_test.status_code}")
                except Exception as e:
                    logger.error(f"代理服务器连接失败: {str(e)}")
                    continue

                # 测试Google服务
                success = False
                for url in urls:
                    try:
                        logger.info(f"尝试连接 {url}")
                        # 对于OAuth端点，使用POST方法
                        if 'token' in url:
                            response = client.post(url, data={'grant_type': 'client_credentials'})
                        else:
                            response = client.get(url)

                        status_code = response.status_code
                        logger.info(f"连接 {url} 状态码: {status_code}")

                        # 检查状态码，200、302和401都认为是成功（401表示未授权但服务可用）
                        if status_code in [200, 302, 401]:
                            logger.info(f"成功连接到 {url}")
                            success = True
                            continue

                        # 如果是其他3xx状态码，检查重定向URL
                        if 300 <= status_code < 400 and response.headers.get('location'):
                            redirect_url = response.headers['location']
                            logger.info(f"重定向到 {redirect_url}")
                            if 'google.com' in redirect_url or 'googleapis.com' in redirect_url:
                                success = True
                                continue

                    except httpx.TimeoutException as e:
                        logger.warning(f"连接 {url} 超时: {str(e)}")
                        continue
                    except httpx.ProxyError as e:
                        logger.error(f"代理服务器错误: {str(e)}")
                        raise ConnectionError(f"代理服务器错误: {str(e)}")
                    except Exception as e:
                        logger.warning(f"连接 {url} 失败: {str(e)}")
                        continue

                if success:
                    return True

            if attempt < max_retries - 1:
                logger.warning(f"连接失败，第{attempt + 1}次重试...")
                continue
            else:
                return False

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"连接出错，第{attempt + 1}次重试: {str(e)}")
                continue
            else:
                logger.error(f"检查Google连接时出错: {str(e)}")
                return False

    return False

class AuthService:
    """认证服务类"""

    def __init__(self):
        """初始化认证服务"""
        logger.info(f"初始化认证服务，代理配置: {PROXIES}")

        # 检查网络连接
        if not check_google_connection():
            logger.error("无法连接到Google服务，请检查网络连接和代理设置")
            raise ConnectionError("无法连接到Google服务，请检查网络连接和代理设置")

        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",  # 更新为v2版本
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:5000/api/auth/google/callback"],
                "javascript_origins": ["http://localhost:5000"],
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"  # 添加证书URL
            }
        }

        # 验证必要的环境变量
        if not all([
            self.client_config['web']['client_id'],
            self.client_config['web']['client_secret']
        ]):
            logger.error("缺少必要的Google OAuth配置")
            raise ValueError("缺少必要的Google OAuth配置，请检查环境变量")

        # 配置OAuth作用域
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]

        logger.info("OAuth配置初始化成功")

    def get_google_auth_url(self) -> str:
        """获取Google认证URL

        Returns:
            str: Google认证URL
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri=self.client_config['web']['redirect_uris'][0]
            )

            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                hd='gmail.com',
                login_hint=os.getenv('TEST_USER_EMAIL', '')
            )

            logger.info(f"生成认证URL: {auth_url}")
            return auth_url

        except Exception as e:
            logger.error(f"生成Google认证URL时出错: {str(e)}")
            raise

    def handle_google_callback(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """处理Google回调

        Args:
            auth_code: 授权码

        Returns:
            Optional[Dict[str, Any]]: 用户信息
        """
        max_retries = 3
        retry_delay = 1  # 重试延迟秒数
        last_error = None

        for attempt in range(max_retries):
            try:
                # 检查网络连接
                if not check_google_connection():
                    logger.warning(f"Google服务连接检查失败，第{attempt + 1}次尝试")
                    if attempt == max_retries - 1:
                        raise ConnectionError("无法连接到Google服务，请检查网络连接和代理设置")
                    continue

                # 使用带重试的HTTP客户端
                with create_http_client(timeout=60.0) as client:  # 增加超时时间到60秒
                    flow = Flow.from_client_config(
                        self.client_config,
                        scopes=self.scopes,
                        redirect_uri=self.client_config['web']['redirect_uris'][0]
                    )

                    # 配置flow的transport
                    flow._transport = client._transport
                    flow._timeout = client._timeout

                    # 使用授权码获取凭证
                    try:
                        flow.fetch_token(code=auth_code)
                    except Exception as e:
                        error_msg = str(e)
                        logger.error(f"获取访问令牌失败: {error_msg}")

                        # 如果是授权码过期，直接返回错误
                        if 'invalid_grant' in error_msg:
                            raise ValueError("授权码已过期，请重新登录")

                        # 其他错误继续重试
                        last_error = e
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay)
                            continue
                        raise ValueError("获取访问令牌失败，请重试")

                    credentials = flow.credentials

                    # 获取用户信息
                    try:
                        service = build('oauth2', 'v2',
                                    credentials=credentials,
                                    static_discovery=False)  # 禁用静态发现
                        user_info = service.userinfo().get().execute()
                    except HttpError as e:
                        logger.error(f"获取用户信息失败: {str(e)}")
                        last_error = e
                        if attempt < max_retries - 1:
                            continue
                        raise ValueError("获取用户信息失败，请重试")

                    # 验证用户是否是测试用户
                    test_users = os.getenv('TEST_USERS', '').split(',')
                    if not test_users or user_info['email'] not in test_users:
                        logger.error(f"用户 {user_info['email']} 不是测试用户")
                        raise ValueError("您不是授权的测试用户")

                    # 查找或创建用户
                    user = User.query.filter_by(email=user_info['email']).first()
                    if not user:
                        user = User(
                            email=user_info['email'],
                            provider_id=user_info['id'],
                            auth_provider='google'
                        )
                        db.session.add(user)
                        db.session.commit()

                    # 生成JWT令牌
                    access_token = create_access_token(identity=user.id)

                    logger.info(f"测试用户 {user.email} 登录成功")
                    return {
                        'access_token': access_token,
                        'user': {
                            'email': user.email,
                            'id': user.id
                        }
                    }

            except Exception as e:
                last_error = e
                logger.error(f"处理回调出错，第{attempt + 1}次尝试: {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                logger.error(f"处理Google回调时出错: {str(e)}")
                raise

        if last_error:
            raise last_error
        return None

    def _get_or_create_user(self, user_info: Dict[str, Any]) -> User:
        """获取或创建用户

        Args:
            user_info: 用户信息

        Returns:
            User: 用户对象
        """
        try:
            email = user_info.get('email')
            if not email:
                raise ValueError("Email not found in user info")

            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    name=user_info.get('name', ''),
                    provider_id=user_info.get('id'),
                    auth_provider='google'
                )
                db.session.add(user)
                db.session.commit()

            return user

        except Exception as e:
            logger.error(f"获取或创建用户失败: {str(e)}")
            db.session.rollback()
            raise
