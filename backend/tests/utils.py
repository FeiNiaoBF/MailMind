"""
测试工具函数
"""
from datetime import datetime, UTC
from typing import Dict, Any, List
from backend.app.models import User, Email
from backend.app.config.config import Config

def create_test_user() -> User:
    """创建测试用户"""
    return User(
        username="test_user",
        email="test@example.com",
        google_id="test_google_id",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=datetime.now(UTC)
    )

def create_test_email(user_id: int) -> Email:
    """创建测试邮件"""
    return Email(
        user_id=user_id,
        uid="test123",
        message_id="test123",
        from_header="sender@example.com",
        to_header="recipient@example.com",
        subject="Test Email",
        body="Test plain text content",
        html_body="<p>Test HTML content</p>",
        received_at=datetime.now(UTC),
        raw_headers={
            "From": "sender@example.com",
            "To": "recipient@example.com",
            "Subject": "Test Email",
            "Date": "2024-03-25T10:00:00Z"
        },
        size=1000,
        labels=["INBOX", "UNREAD"]
    )

def mock_gmail_service_response() -> Dict[str, Any]:
    """模拟Gmail服务响应"""
    return {
        "messages": [
            {
                "id": "msg1",
                "threadId": "thread1",
                "labelIds": ["INBOX", "UNREAD"],
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Test Subject"},
                        {"name": "From", "value": "sender@example.com"},
                        {"name": "To", "value": "recipient@example.com"},
                        {"name": "Date", "value": "2024-03-25T10:00:00Z"}
                    ],
                    "parts": [
                        {
                            "mimeType": "text/plain",
                            "body": {"data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQ=="}  # "This is a test message"
                        },
                        {
                            "mimeType": "text/html",
                            "body": {"data": "PGgxPlRoaXMgaXMgYSB0ZXN0IG1lc3NhZ2U8L2gxPg=="}  # "<h1>This is a test message</h1>"
                        }
                    ]
                }
            }
        ],
        "nextPageToken": "next_page_token"
    }

def mock_gmail_profile_response() -> Dict[str, Any]:
    """模拟Gmail个人资料响应"""
    return {
        "emailAddress": "test@example.com",
        "messagesTotal": 100,
        "threadsTotal": 50,
        "historyId": "12345"
    }
