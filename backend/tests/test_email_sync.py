"""
邮件同步服务测试
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, UTC
import httplib2
from backend.app.service.email.sync import EmailSyncService
from backend.app.db.models import User, Email
from backend.app.config.config import Config
from googleapiclient.errors import HttpError


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


@pytest.fixture(autouse=True)
def mock_http():
    """模拟 HTTP 请求"""
    with patch('httplib2.Http') as mock_http_class:
        # 创建一个真实的 httplib2.Http 实例
        http = httplib2.Http()

        # 创建一个模拟的响应对象
        class MockResponse:
            def __init__(self, status, headers, content):
                self.status = status
                self.headers = headers
                self.content = content

        # 模拟 request 方法
        def mock_request(uri, method="GET", body=None, headers=None, **kwargs):
            return (
                MockResponse(
                    status=200,
                    headers={'content-type': 'application/json'},
                    content=b'{"messages": [{"id": "msg1"}, {"id": "msg2"}]}'
                ),
                b'{"messages": [{"id": "msg1"}, {"id": "msg2"}]}'
            )

        http.request = mock_request
        mock_http_class.return_value = http
        yield http


@pytest.fixture
def mock_gmail_service():
    mock_service = Mock()

    # 模拟用户服务
    mock_users = Mock()
    mock_service.users = Mock(return_value=mock_users)

    # 模拟消息服务
    mock_messages = Mock()
    mock_users.messages = Mock(return_value=mock_messages)

    # 模拟列表响应
    mock_list = Mock()
    mock_messages.list = Mock(return_value=mock_list)
    mock_list.execute = Mock(return_value={
        'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
    })

    # 模拟获取邮件响应
    mock_get = Mock()
    mock_messages.get = Mock(return_value=mock_get)

    def get_message_response(msg_id='msg1'):
        """获取消息响应
        from: https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages?hl=zh-cn#Message
        {
          "id": string,
          "threadId": string,
          "labelIds": [
            string
          ],
          "snippet": string,
          "historyId": string,
          "internalDate": string,
          "payload": {
            object (MessagePart)
          },
          "sizeEstimate": integer,
          "raw": string
        }
        """
        return {
            'id': msg_id,
            'threadId': f'thread_{msg_id}',
            'labelIds': ['INBOX', 'UNREAD'],
            'snippet': 'Email snippet...',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'},
                    {'name': 'To', 'value': 'recipient@example.com'},
                    {'name': 'Date', 'value': '2024-01-01T12:00:00Z'}
                ],
                'parts': [
                    {
                        'mimeType': 'text/plain',
                        'body': {'data': 'Test email body'}
                    },
                    {
                        'mimeType': 'text/html',
                        'body': {'data': '<html>Test email body</html>'}
                    }
                ]
            }
        }

    mock_get.execute = Mock(side_effect=lambda: get_message_response())

    # 模拟修改标签响应
    mock_modify = Mock()
    mock_messages.modify = Mock(return_value=mock_modify)
    mock_modify.execute = Mock(return_value={
        'id': 'msg1',
        'labelIds': ['IMPORTANT']
    })

    # 创建错误版本的消息服务
    mock_messages_error = Mock()
    mock_messages_error.list = Mock()
    mock_messages_error.list.return_value = Mock()
    mock_messages_error.list.return_value.execute = Mock(
        side_effect=HttpError(resp=Mock(status=500), content=b'API Error')
    )
    mock_messages_error.get = Mock()
    mock_messages_error.get.return_value = Mock()
    mock_messages_error.get.return_value.execute = Mock(
        side_effect=HttpError(resp=Mock(status=404), content=b'Not found')
    )
    mock_messages_error.modify = Mock()
    mock_messages_error.modify.return_value = Mock()
    mock_messages_error.modify.return_value.execute = Mock(
        side_effect=HttpError(resp=Mock(status=400), content=b'Invalid request')
    )

    mock_service._messages_error = mock_messages_error

    return mock_service


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
def sync_service(mock_gmail_service):
    """创建邮件同步服务"""
    service = EmailSyncService()
    service.service = mock_gmail_service
    service.user = User(
        id=1,
        email='test@example.com',
        oauth_token={
            'access_token': 'test_token',
            'refresh_token': 'test_refresh_token'
        }
    )
    return service


def test_service_initialization():
    """测试服务初始化"""
    service = EmailSyncService()
    assert service.service is None
    assert service.user is None


def test_sync_emails(sync_service, mock_gmail_service):
    """测试同步邮件"""
    emails = sync_service.sync_emails(max_results=2)

    assert len(emails) == 2
    assert all(isinstance(email, Email) for email in emails)
    assert emails[0].subject == 'Test Subject'
    assert emails[0].from_header == 'sender@example.com'
    assert emails[0].to_header == 'recipient@example.com'


def test_get_email(sync_service, mock_gmail_service):
    """测试获取单个邮件"""
    email = sync_service.get_email('msg1')

    assert isinstance(email, Email)
    assert email.subject == 'Test Subject'
    assert email.from_header == 'sender@example.com'
    assert email.to_header == 'recipient@example.com'


def test_update_email_labels(sync_service, mock_gmail_service):
    """测试更新邮件标签"""
    sync_service.update_email_labels('msg1', add_labels=['IMPORTANT'], remove_labels=['INBOX'])

    # 验证 modify 方法被调用
    mock_modify = mock_gmail_service.users().messages().modify
    mock_modify.assert_called_once_with(
        userId='me',
        id='msg1',
        body={
            'addLabelIds': ['IMPORTANT'],
            'removeLabelIds': ['INBOX']
        }
    )

    # 验证 execute 方法被调用
    mock_modify().execute.assert_called_once()


def test_sync_emails_error(sync_service, mock_gmail_service):
    """测试同步邮件错误"""
    mock_gmail_service.users().messages = Mock(return_value=mock_gmail_service._messages_error)

    with pytest.raises(Exception) as exc_info:
        sync_service.sync_emails()
    assert 'API Error' in str(exc_info.value)


def test_get_email_error(sync_service, mock_gmail_service):
    """测试获取邮件错误"""
    # 替换为错误版本的 messages
    mock_messages_error = mock_gmail_service._messages_error
    mock_gmail_service.users().messages = Mock(return_value=mock_messages_error)

    # 设置错误响应
    mock_messages_error.get.return_value.execute = Mock(
        side_effect=HttpError(
            resp=Mock(status=500),  # 使用 500 错误而不是 404
            content=b'API Error'
        )
    )

    # 验证异常
    with pytest.raises(Exception) as exc_info:
        sync_service.get_email('not_exist')
    assert 'Failed to get email' in str(exc_info.value)


def test_update_email_labels_error(sync_service, mock_gmail_service):
    """测试更新标签错误"""
    mock_gmail_service.users().messages = Mock(return_value=mock_gmail_service._messages_error)

    with pytest.raises(Exception) as exc_info:
        sync_service.update_email_labels('msg1', add_labels=['INVALID'], remove_labels=[])
    assert 'Invalid request' in str(exc_info.value)


def test_email_sync_service_sync_emails_with_invalid_base64(sync_service, mock_gmail_service):
    """测试处理无效的base64编码"""
    # 模拟邮件列表响应
    mock_gmail_service.users().messages().list().execute.return_value = {
        'messages': [{'id': 'msg1', 'threadId': 'thread1'}],
        'nextPageToken': None
    }

    # 模拟邮件详情响应
    mock_gmail_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Invalid Base64'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'recipient@example.com'}
            ],
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {'data': 'Invalid base64 data'}
                }
            ]
        }
    }

    emails = sync_service.sync_emails(max_results=1)
    assert len(emails) == 1
    assert emails[0].body == ''  # 应该返回空字符串而不是抛出异常


def test_email_sync_service_sync_emails_with_missing_data(sync_service, mock_gmail_service):
    """测试处理缺失的data字段"""
    # 模拟邮件列表响应
    mock_gmail_service.users().messages().list().execute.return_value = {
        'messages': [{'id': 'msg1', 'threadId': 'thread1'}],
        'nextPageToken': None
    }

    # 模拟邮件详情响应
    mock_gmail_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Missing Data'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'recipient@example.com'}
            ],
            'parts': [
                {
                    'mimeType': 'text/plain',
                    'body': {}  # 没有data字段
                }
            ]
        }
    }

    emails = sync_service.sync_emails(max_results=1)
    assert len(emails) == 1
    assert emails[0].body == ''  # 应该返回空字符串而不是抛出异常


def test_email_sync_service_sync_emails_with_empty_parts(sync_service, mock_gmail_service):
    """测试处理空的parts数组"""
    # 模拟邮件列表响应
    mock_gmail_service.users().messages().list().execute.return_value = {
        'messages': [{'id': 'msg1', 'threadId': 'thread1'}],
        'nextPageToken': None
    }

    # 模拟邮件详情响应
    mock_gmail_service.users().messages().get().execute.return_value = {
        'id': 'msg1',
        'threadId': 'thread1',
        'labelIds': ['INBOX'],
        'payload': {
            'headers': [
                {'name': 'Subject', 'value': 'Test Empty Parts'},
                {'name': 'From', 'value': 'sender@example.com'},
                {'name': 'To', 'value': 'recipient@example.com'}
            ],
            'parts': []  # 空的parts数组
        }
    }

    emails = sync_service.sync_emails(max_results=1)
    assert len(emails) == 1
    assert emails[0].body == ''  # 应该返回空字符串而不是抛出异常
