"""
邮件同步服务测试
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
from backend.app.service.email.sync import EmailSyncService
from backend.app.db.models import User, Email
from backend.app.config.config import Config

@pytest.fixture(autouse=True)
def mock_config():
    """模拟配置"""
    with patch('backend.app.service.email.sync.Config') as mock_config:
        mock_config.GMAIL_CLIENT_CONFIG = {
            'web': {
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'token_uri': 'https://oauth2.googleapis.com/token'
            }
        }
        yield mock_config

@pytest.fixture
def mock_gmail_service():
    """创建模拟的 Gmail 服务"""
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_service = Mock()
        mock_build.return_value = mock_service
        yield mock_service

@pytest.fixture
def test_user():
    """创建测试用户"""
    return User(
        id=1,
        email='test@example.com',
        oauth_token={
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token'
        }
    )

@pytest.fixture
def sync_service(mock_gmail_service, test_user):
    """创建同步服务实例"""
    service = EmailSyncService()
    service.initialize(test_user)
    return service

def test_service_initialization(sync_service, test_user):
    """测试服务初始化"""
    assert sync_service.user == test_user
    assert sync_service.service is not None

def test_sync_emails(sync_service, mock_gmail_service):
    """测试同步邮件"""
    emails = sync_service.sync_emails(max_results=2)

    assert len(emails) == 2
    assert all(isinstance(email, Email) for email in emails)
    assert emails[0].subject == 'Test Subject'
    assert emails[0].from_header == 'sender@example.com'
    assert emails[0].to_header == 'receiver@example.com'
    assert emails[0].body == 'Test body'
    assert emails[0].html_body == '<p>Test body</p>'
    assert emails[0].labels == ['INBOX']

def test_get_email(sync_service, mock_gmail_service):
    """测试获取单个邮件"""
    email = sync_service.get_email('msg1')

    assert isinstance(email, Email)
    assert email.subject == 'Test Subject'
    assert email.from_header == 'sender@example.com'
    assert email.to_header == 'receiver@example.com'
    assert email.body == 'Test body'
    assert email.labels == ['INBOX']

def test_update_email_labels(sync_service, mock_gmail_service):
    """测试更新邮件标签"""
    sync_service.update_email_labels(
        'msg1',
        add_labels=['IMPORTANT'],
        remove_labels=['INBOX']
    )

    mock_gmail_service.users().messages().modify.assert_called_once_with(
        userId='me',
        id='msg1',
        body={
            'addLabelIds': ['IMPORTANT'],
            'removeLabelIds': ['INBOX']
        }
    )

def test_sync_emails_error(sync_service, mock_gmail_service):
    """测试同步邮件错误"""
    mock_gmail_service.users().messages().list().execute.side_effect = Exception('API Error')

    with pytest.raises(Exception) as exc_info:
        sync_service.sync_emails()

    assert 'Failed to sync emails' in str(exc_info.value)

def test_get_email_error(sync_service, mock_gmail_service):
    """测试获取邮件错误"""
    mock_gmail_service.users().messages().get().execute.side_effect = Exception('API Error')

    with pytest.raises(Exception) as exc_info:
        sync_service.get_email('msg1')

    assert 'Failed to get email' in str(exc_info.value)

def test_update_email_labels_error(sync_service, mock_gmail_service):
    """测试更新标签错误"""
    mock_gmail_service.users().messages().modify().execute.side_effect = Exception('API Error')

    with pytest.raises(Exception) as exc_info:
        sync_service.update_email_labels('msg1', add_labels=['IMPORTANT'])

    assert 'Failed to update email labels' in str(exc_info.value)
