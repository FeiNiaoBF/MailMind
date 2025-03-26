"""
Gmail 认证相关测试
"""
import pytest
from unittest.mock import Mock, patch
from flask import current_app

from app.utils import logger
from app.utils.logger import debug_print
from backend.app.service.email.auth import EmailAuthService
from backend.app.config.config import Config

# from: https://developers.google.com/workspace/gmail/api/auth/web-server?hl=zh-cn

logger.get_logger(__name__)


@pytest.fixture
def mock_flow():
    """创建模拟的 OAuth2 流程"""
    with patch('google_auth_oauthlib.flow.Flow') as mock:
        mock_flow = Mock()
        mock.from_client_config.return_value = mock_flow
        yield mock_flow


@pytest.fixture
def auth_service(mock_flow):
    """创建认证服务实例"""
    service = EmailAuthService()
    return service


def test_auth_service_initialization(auth_service):
    """测试认证服务初始化"""
    assert auth_service is not None
    assert len(auth_service.SCOPES) == 3
    assert 'gmail.readonly' in auth_service.SCOPES[0]
    assert 'gmail.send' in auth_service.SCOPES[1]
    assert 'gmail.modify' in auth_service.SCOPES[2]


def test_authenticate(auth_service, mock_flow, app):
    """测试获取认证URL"""
    mock_flow.authorization_url.return_value = (
        'https://accounts.google.com/o/oauth2/auth?response_type=code',
        'test_state'
    )

    # 在应用上下文中调用 authenticate 方法
    with app.app_context():
        result = auth_service.authenticate(user_id=1)

        # 使用 debug_print 打印调试信息
        debug_print(f'result: {result}\n'
                    f'result type: {type(result)}\n'
                    f'result keys: {result.keys()}')

        assert 'auth_url' in result
        assert 'state' in result
        assert result['user_id'] == 1
        assert 'accounts.google.com' in result['auth_url']


def test_handle_callback(auth_service, mock_flow, app):
    """测试处理认证回调"""
    # 设置 mock 凭证对象
    mock_credentials = Mock()
    mock_credentials.token = 'test_token'
    mock_credentials.refresh_token = 'test_refresh_token'
    mock_credentials.token_uri = 'https://oauth2.googleapis.com/token'
    mock_credentials.client_id = 'test_client_id'
    mock_credentials.client_secret = 'test_client_secret'
    mock_credentials.scopes = auth_service.SCOPES

    # 用于设置mock流程行为
    mock_flow.credentials = mock_credentials
    mock_flow.fetch_token = Mock()  # 直接替换 fetch_token 方法
    mock_flow.fetch_token.return_value = None

    # 设置 auth_service 的 flow 属性
    auth_service.flow = mock_flow
    # 调用 handle_callback 方法
    result = auth_service.handle_callback('test_code', 'test_state')

    with app.app_context():
        debug_print(f'result: {result}\n'
                    f'result type: {type(result)}\n')

    assert result == {
        'token': 'test_token',
        'refresh_token': 'test_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': auth_service.SCOPES
    }
    mock_flow.fetch_token.assert_called_once_with(code='test_code')


def test_refresh_token(auth_service):
    """测试刷新令牌"""
    credentials = {
        'token': 'expired_token',
        'refresh_token': 'valid_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': auth_service.SCOPES
    }

    # 创建一个真实的 Credentials 对象
    from google.oauth2.credentials import Credentials
    mock_creds = Credentials(
        token='expired_token',
        refresh_token='valid_refresh_token',
        token_uri='https://oauth2.googleapis.com/token',
        client_id='test_client_id',
        client_secret='test_client_secret',
        scopes=auth_service.SCOPES
    )

    with patch('google.oauth2.credentials.Credentials.from_authorized_user_info') as mock_from_auth:
        mock_from_auth.return_value = mock_creds
        with patch('google.auth.transport.requests.Request') as mock_request:
            result = auth_service.refresh_token(credentials)

            assert result == {
                'token': 'expired_token',
                'refresh_token': 'valid_refresh_token',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'scopes': auth_service.SCOPES
            }
            mock_from_auth.assert_called_once_with(credentials)


def test_get_provider_name(auth_service):
    """测试获取提供者名称"""
    assert auth_service.get_provider_name() == 'gmail'


def test_handle_callback_error(auth_service, mock_flow):
    """测试处理认证回调错误"""
    mock_flow.fetch_token.side_effect = Exception('Authentication failed')

    with pytest.raises(Exception) as exc_info:
        auth_service.handle_callback('test_code', 'test_state')

    assert 'Failed to handle callback' in str(exc_info.value)


def test_refresh_token_error(auth_service):
    """测试刷新令牌错误"""
    credentials = {
        'token': 'expired_token',
        'refresh_token': 'invalid_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': auth_service.SCOPES
    }

    with patch('google.oauth2.credentials.Credentials') as mock_creds:
        mock_creds.from_authorized_user_info.side_effect = Exception('Invalid credentials')

        with pytest.raises(Exception) as exc_info:
            auth_service.refresh_token(credentials)

        assert 'Failed to refresh token' in str(exc_info.value)
