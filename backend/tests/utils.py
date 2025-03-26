"""
测试工具模块
"""
from typing import Dict, Any
from datetime import datetime, UTC
from backend.app.db.models import User, Email

def create_test_user(
    email: str = 'test@example.com',
    oauth_token: Dict[str, Any] = None
) -> Dict[str, Any]:
    """创建测试用户数据

    Args:
        email: 用户邮箱
        oauth_token: OAuth令牌信息

    Returns:
        Dict[str, Any]: 用户数据
    """
    if oauth_token is None:
        oauth_token = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_at': datetime.now(UTC).isoformat()
        }

    return {
        'email': email,
        'oauth_uid': 'test_uid',
        'oauth_token': oauth_token,
        'oauth_provider': 'gmail',
        'is_active': True,
        'oauth_token_expires_at': datetime.now(UTC)
    }

def create_test_email(
    user_id: int,
    subject: str = 'Test Subject',
    body: str = 'Test Body'
) -> Dict[str, Any]:
    """创建测试邮件数据

    Args:
        user_id: 用户ID
        subject: 邮件主题
        body: 邮件正文

    Returns:
        Dict[str, Any]: 邮件数据
    """
    return {
        'user_id': user_id,
        'uid': 'test_uid',
        'message_id': 'test_message_id',
        'from_header': 'sender@example.com',
        'to_header': 'recipient@example.com',
        'subject': subject,
        'body': body,
        'html_body': f'<p>{body}</p>',
        'received_at': datetime.now(UTC),
        'raw_headers': {'header1': 'value1'},
        'labels': ['INBOX'],
        'size': 1000
    }

def mock_gmail_service_response():
    """模拟Gmail服务响应"""
    return {
        'messages': [
            {
                'id': 'msg1',
                'threadId': 'thread1',
                'labelIds': ['INBOX'],
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
                            'body': {'data': 'VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQ=='}  # "This is a test message"
                        },
                        {
                            'mimeType': 'text/html',
                            'body': {'data': 'PGgxPlRoaXMgaXMgYSB0ZXN0IG1lc3NhZ2U8L2gxPg=='}  # "<h1>This is a test message</h1>"
                        }
                    ]
                }
            }
        ],
        'nextPageToken': None  # 设置为None，表示没有更多邮件
    }

def mock_gmail_profile_response():
    """模拟Gmail用户信息响应"""
    return {
        'emailAddress': 'test@example.com',
        'messagesTotal': 1,  # 修改为1，表示只有一封邮件
        'threadsTotal': 1,
        'historyId': '12345'
    }
