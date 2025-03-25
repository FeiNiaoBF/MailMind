"""
邮件同步服务
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.app.db.models import Email, User
from backend.app.config.config import Config

class EmailSyncService:
    """邮件同步服务类"""

    def __init__(self):
        """初始化邮件同步服务"""
        self.service = None
        self.user = None

    def initialize(self, user: User) -> None:
        """初始化服务

        Args:
            user: 用户对象
        """
        self.user = user
        credentials = Credentials(
            token=user.oauth_token['access_token'],
            refresh_token=user.oauth_token['refresh_token'],
            token_uri=Config.GMAIL_CLIENT_CONFIG['web']['token_uri'],
            client_id=Config.GMAIL_CLIENT_CONFIG['web']['client_id'],
            client_secret=Config.GMAIL_CLIENT_CONFIG['web']['client_secret'],
            scopes=['https://www.googleapis.com/auth/gmail.readonly']
        )
        self.service = build('gmail', 'v1', credentials=credentials)

    def sync_emails(self, max_results: int = 100) -> List[Email]:
        """同步邮件

        Args:
            max_results: 最大同步数量

        Returns:
            同步的邮件列表
        """
        if not self.service or not self.user:
            raise ValueError("Service not initialized")

        try:
            # 获取邮件列表
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            if not messages:
                return []

            # 获取邮件详情
            emails = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                # 解析邮件头
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
                from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
                to_header = next((h['value'] for h in headers if h['name'] == 'To'), '')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

                # 解析邮件内容
                body = ''
                html_body = ''
                if 'parts' in msg['payload']:
                    for part in msg['payload']['parts']:
                        if part['mimeType'] == 'text/plain':
                            body = part['body']['data']
                        elif part['mimeType'] == 'text/html':
                            html_body = part['body']['data']
                elif 'body' in msg['payload']:
                    body = msg['payload']['body']['data']

                # 创建邮件对象
                email = Email(
                    user_id=self.user.id,
                    uid=message['id'],
                    message_id=message['id'],
                    from_header=from_header,
                    to_header=to_header,
                    subject=subject,
                    body=body,
                    html_body=html_body,
                    received_at=datetime.fromisoformat(date.replace('Z', '+00:00')),
                    raw_headers=dict(headers),
                    size=len(str(msg)),
                    labels=msg.get('labelIds', [])
                )
                emails.append(email)

            return emails

        except Exception as e:
            raise Exception(f"Failed to sync emails: {str(e)}")

    def get_email(self, message_id: str) -> Optional[Email]:
        """获取单个邮件

        Args:
            message_id: 邮件ID

        Returns:
            邮件对象，如果不存在则返回None
        """
        if not self.service or not self.user:
            raise ValueError("Service not initialized")

        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # 解析邮件头
            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
            to_header = next((h['value'] for h in headers if h['name'] == 'To'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            # 解析邮件内容
            body = ''
            html_body = ''
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = part['body']['data']
                    elif part['mimeType'] == 'text/html':
                        html_body = part['body']['data']
            elif 'body' in msg['payload']:
                body = msg['payload']['body']['data']

            # 创建邮件对象
            return Email(
                user_id=self.user.id,
                uid=message_id,
                message_id=message_id,
                from_header=from_header,
                to_header=to_header,
                subject=subject,
                body=body,
                html_body=html_body,
                received_at=datetime.fromisoformat(date.replace('Z', '+00:00')),
                raw_headers=dict(headers),
                size=len(str(msg)),
                labels=msg.get('labelIds', [])
            )

        except Exception as e:
            raise Exception(f"Failed to get email: {str(e)}")

    def update_email_labels(self, message_id: str, add_labels: List[str] = None, remove_labels: List[str] = None) -> None:
        """更新邮件标签

        Args:
            message_id: 邮件ID
            add_labels: 要添加的标签列表
            remove_labels: 要移除的标签列表
        """
        if not self.service or not self.user:
            raise ValueError("Service not initialized")

        try:
            body = {}
            if add_labels:
                body['addLabelIds'] = add_labels
            if remove_labels:
                body['removeLabelIds'] = remove_labels

            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body
            ).execute()

        except Exception as e:
            raise Exception(f"Failed to update email labels: {str(e)}")
