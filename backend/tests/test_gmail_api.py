"""
Gmail API 集成测试
"""
import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.app.service.email.gmail import GmailEmailService
from backend.app.service.email.sync import EmailSyncService
from backend.app.db.models import User
from backend.app.config.config import Config
from .utils import (
    create_test_user,
    create_test_email,
    mock_gmail_service_response,
    mock_gmail_profile_response
)

@pytest.fixture
def mock_gmail_service():
    """创建模拟的 Gmail 服务"""
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_service = Mock()
        mock_build.return_value = mock_service

        # 设置模拟响应
        mock_service.users().getProfile().execute.return_value = mock_gmail_profile_response()
        mock_service.users().messages().list().execute.return_value = mock_gmail_service_response()
        mock_service.users().messages().get().execute.return_value = mock_gmail_service_response()['messages'][0]

        yield mock_service

@pytest.fixture
def mock_credentials():
    """创建模拟的 Gmail 凭证"""
    with patch('google.oauth2.credentials.Credentials') as mock_creds:
        mock_creds.return_value = Mock(spec=Credentials)
        yield mock_creds

@pytest.fixture
def gmail_service(mock_gmail_service, mock_credentials):
    """创建 Gmail 服务实例"""
    service = GmailEmailService()
    return service

@pytest.fixture
def email_sync_service(mock_gmail_service, mock_credentials):
    """创建邮件同步服务实例"""
    service = EmailSyncService()
    return service

def test_gmail_service_initialization(gmail_service):
    """测试 Gmail 服务初始化"""
    assert gmail_service is not None
    assert gmail_service.service is not None
    assert gmail_service.credentials is not None

def test_gmail_service_authentication(mock_gmail_service):
    """测试 Gmail 服务认证"""
    service = GmailEmailService()
    profile = service.service.users().getProfile().execute()

    assert profile['emailAddress'] == 'test@example.com'
    assert profile['messagesTotal'] == 100
    assert profile['threadsTotal'] == 50
    assert profile['historyId'] == '12345'

def test_email_sync_service_initialization(email_sync_service, test_user):
    """测试邮件同步服务初始化"""
    email_sync_service.initialize(test_user)
    assert email_sync_service.service is not None
    assert email_sync_service.user == test_user

def test_email_sync_service_sync_emails(email_sync_service, test_user, mock_gmail_service):
    """测试邮件同步功能"""
    email_sync_service.initialize(test_user)
    emails = email_sync_service.sync_emails(max_results=2)

    assert len(emails) == 1  # 根据模拟响应，应该只有一封邮件
    email = emails[0]

    # 验证邮件属性
    assert email.uid == 'msg1'
    assert email.subject == 'Test Subject'
    assert email.from_header == 'sender@example.com'
    assert email.to_header == 'recipient@example.com'
    assert 'INBOX' in email.labels
    assert email.body == 'Test plain text'
    assert email.html_body == '<p>Test HTML content</p>'

def test_email_sync_service_error_handling(email_sync_service, test_user, mock_gmail_service):
    """测试邮件同步服务的错误处理"""
    # 模拟 API 错误
    mock_gmail_service.users().messages().list().execute.side_effect = Exception('API Error')

    email_sync_service.initialize(test_user)
    with pytest.raises(Exception) as exc_info:
        email_sync_service.sync_emails()

    assert 'Failed to sync emails' in str(exc_info.value)

def test_gmail_service_email_validation():
    """测试邮箱地址验证"""
    service = GmailEmailService()

    # 测试有效邮箱
    assert service.validate_email('test@example.com') is True
    assert service.validate_email('user.name@domain.co.uk') is True

    # 测试无效邮箱
    assert service.validate_email('invalid-email') is False
    assert service.validate_email('@domain.com') is False
    assert service.validate_email('user@') is False

def test_email_sync_service_get_email(email_sync_service, test_user, mock_gmail_service):
    """测试获取单个邮件"""
    email_sync_service.initialize(test_user)
    email = email_sync_service.get_email('msg1')

    assert email is not None
    assert email.uid == 'msg1'
    assert email.subject == 'Test Subject'
    assert email.from_header == 'sender@example.com'
    assert email.to_header == 'recipient@example.com'

def test_email_sync_service_update_labels(email_sync_service, test_user, mock_gmail_service):
    """测试更新邮件标签"""
    email_sync_service.initialize(test_user)

    # 模拟更新标签的响应
    mock_gmail_service.users().messages().modify().execute.return_value = {
        'id': 'msg1',
        'labelIds': ['INBOX', 'STARRED']
    }

    # 测试添加和移除标签
    email_sync_service.update_email_labels(
        'msg1',
        add_labels=['STARRED'],
        remove_labels=['UNREAD']
    )

    # 验证调用
    mock_gmail_service.users().messages().modify.assert_called_once_with(
        userId='me',
        id='msg1',
        body={
            'addLabelIds': ['STARRED'],
            'removeLabelIds': ['UNREAD']
        }
    )

def test_gmail_service_fetch_emails(gmail_service, mock_gmail_service):
    """测试获取邮件列表"""
    # 模拟 Gmail API 响应
    mock_gmail_service.users().messages().list().execute.return_value = {
        'messages': [
            {'id': 'msg1', 'threadId': 'thread1'},
            {'id': 'msg2', 'threadId': 'thread2'}
        ],
        'nextPageToken': 'next_page_token'
    }

    # 模拟单个邮件详情
    mock_gmail_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX', 'UNREAD'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Subject'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'recipient@example.com'},
                {'name': 'Date', 'value': '2024-03-25T10:00:00Z'}
            ],
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {'data': 'VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQ=='}  # base64 encoded "This is a test message"
                }
            ]
        }
    }

    emails = gmail_service.fetch_emails(max_results=2)

    assert len(emails) == 2
    assert emails[0].uid == 'msg1'
    assert emails[0].subject == 'Test Subject'
    assert emails[0].from_header == 'sender@example.com'
    assert emails[0].to_header == 'recipient@example.com'
    assert 'INBOX' in emails[0].labels
    assert emails[0].body == 'This is a test message'

def test_gmail_service_fetch_emails_with_attachments(gmail_service, mock_gmail_service):
    """测试获取带附件的邮件"""
    mock_gmail_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Subject with Attachment'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'recipient@example.com'}
            ],
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {'data': 'VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQ=='}
                },
                {
                    'mimeType': 'application/pdf',
                    'filename': 'test.pdf',
                    'body': {'attachmentId': 'att1'}
                }
            ]
        }
    }

    # 模拟附件内容
    mock_gmail_service.users().messages().attachments().get().execute.return_value = {
        'data': 'JVBERi0...'  # base64 encoded PDF content
    }

    emails = gmail_service.fetch_emails(max_results=1)

    assert len(emails) == 1
    assert len(emails[0].attachments) == 1
    assert emails[0].attachments[0].filename == 'test.pdf'
    assert emails[0].attachments[0].mime_type == 'application/pdf'

def test_gmail_service_fetch_emails_with_pagination(gmail_service, mock_gmail_service):
    """测试邮件分页获取"""
    # 模拟第一页响应
    mock_gmail_service.users().messages().list().execute.side_effect = [
        {
            'messages': [{'id': 'msg1', 'threadId': 'thread1'}],
            'nextPageToken': 'next_page_token'
        },
        {
            'messages': [{'id': 'msg2', 'threadId': 'thread2'}],
            'nextPageToken': None
        }
    ]

    emails = gmail_service.fetch_emails(max_results=2)

    assert len(emails) == 2
    assert emails[0].uid == 'msg1'
    assert emails[1].uid == 'msg2'

def test_gmail_service_fetch_emails_error_handling(gmail_service, mock_gmail_service):
    """测试邮件获取错误处理"""
    mock_gmail_service.users().messages().list().execute.side_effect = Exception('API Error')

    with pytest.raises(Exception) as exc_info:
        gmail_service.fetch_emails()

    assert 'Failed to fetch emails' in str(exc_info.value)

def test_gmail_service_fetch_emails_with_nested_mime(gmail_service, mock_gmail_service):
    """测试获取嵌套MIME结构的邮件"""
    mock_gmail_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Nested MIME'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'recipient@example.com'}
            ],
            'parts': [
                {
                    'mimeType': 'multipart/mixed',
                    'parts': [
                        {
                            'mimeType': 'multipart/alternative',
                            'parts': [
                                {
                                    'mimeType': 'text/plain',
                                    'body': {'data': 'VGhpcyBpcyB0aGUgcGxhaW4gdGV4dA=='}  # "This is the plain text"
                                },
                                {
                                    'mimeType': 'text/html',
                                    'body': {'data': 'PGgxPlRoaXMgaXMgdGhlIEhUTUw8L2gxPg=='}  # "<h1>This is the HTML</h1>"
                                }
                            ]
                        },
                        {
                            'mimeType': 'application/pdf',
                            'filename': 'test.pdf',
                            'body': {'attachmentId': 'att1'}
                        }
                    ]
                }
            ]
        }
    }

    # 模拟附件内容
    mock_gmail_service.users().messages().attachments().get().execute.return_value = {
        'data': 'JVBERi0...'  # base64 encoded PDF content
    }

    emails = gmail_service.fetch_emails(max_results=1)

    assert len(emails) == 1
    assert emails[0].body == 'This is the plain text'
    assert emails[0].html_body == '<h1>This is the HTML</h1>'
    assert len(emails[0].attachments) == 1
    assert emails[0].attachments[0].filename == 'test.pdf'
    assert emails[0].attachments[0].mime_type == 'application/pdf'

def test_gmail_service_fetch_emails_with_multiple_attachments(gmail_service, mock_gmail_service):
    """测试获取多个附件的邮件"""
    mock_gmail_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Multiple Attachments'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'recipient@example.com'}
            ],
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {'data': 'VGhpcyBpcyB0aGUgZW1haWwgYm9keQ=='}  # "This is the email body"
                },
                {
                    'mimeType': 'application/pdf',
                    'filename': 'document1.pdf',
                    'body': {'attachmentId': 'att1'}
                },
                {
                    'mimeType': 'image/jpeg',
                    'filename': 'image1.jpg',
                    'body': {'attachmentId': 'att2'}
                }
            ]
        }
    }

    # 模拟附件内容
    mock_gmail_service.users().messages().attachments().get().execute.side_effect = [
        {'data': 'JVBERi0...'},  # PDF content
        {'data': '/9j/4AAQSkZJRg...'}  # JPEG content
    ]

    emails = gmail_service.fetch_emails(max_results=1)

    assert len(emails) == 1
    assert len(emails[0].attachments) == 2
    assert emails[0].attachments[0].filename == 'document1.pdf'
    assert emails[0].attachments[0].mime_type == 'application/pdf'
    assert emails[0].attachments[1].filename == 'image1.jpg'
    assert emails[0].attachments[1].mime_type == 'image/jpeg'
