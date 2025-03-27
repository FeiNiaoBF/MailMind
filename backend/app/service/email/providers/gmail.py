"""
Gmail 邮件服务提供商实现
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from backend.app.config.config import Config
from backend.app.utils.logger import get_logger
from .base import EmailProvider
from backend.app.models import Email, User

logger = get_logger(__name__)

class GmailProvider(EmailProvider):
    """Gmail 邮件服务提供商"""

    def __init__(self, credentials: Dict[str, Any]):
        """初始化 Gmail 提供商
        :param credentials: 认证信息
        """
        self.credentials = credentials
        self.service = None

    def authenticate(self) -> bool:
        """认证服务"""
        try:
            creds = Credentials(
                token=self.credentials['access_token'],
                refresh_token=self.credentials['refresh_token'],
                token_uri=Config.GMAIL_CLIENT_CONFIG['web']['token_uri'],
                client_id=Config.GMAIL_CLIENT_CONFIG['web']['client_id'],
                client_secret=Config.GMAIL_CLIENT_CONFIG['web']['client_secret'],
                scopes=['https://www.googleapis.com/auth/gmail.readonly']
            )
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            return False

    def get_emails(self, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取邮件列表"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            query = []
            if start_date:
                query.append(f"after:{int(start_date.timestamp())}")
            if end_date:
                query.append(f"before:{int(end_date.timestamp())}")

            results = self.service.users().messages().list(
                userId='me',
                q=' '.join(query) if query else None
            ).execute()

            messages = results.get('messages', [])
            return [self.get_email_content(msg['id']) for msg in messages]

        except HttpError as e:
            logger.error(f"Error getting emails: {str(e)}")
            raise Exception(f"Failed to get emails: {str(e)}")

    def get_email_content(self, message_id: str) -> Dict[str, Any]:
        """获取邮件内容"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            payload = msg.get('payload', {})
            headers = payload.get('headers', [])

            # 解析邮件头
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # 解析邮件内容
            body = ''
            html_body = ''
            attachments = []

            def process_part(part: dict) -> None:
                """递归处理邮件部分"""
                nonlocal body, html_body, attachments

                if part.get('mimeType') == 'text/plain':
                    if 'data' in part.get('body', {}):
                        try:
                            data = part['body']['data']
                            padding = 4 - (len(data) % 4)
                            if padding != 4:
                                data += '=' * padding
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Error decoding plain text: {str(e)}")
                            body = ''
                elif part.get('mimeType') == 'text/html':
                    if 'data' in part.get('body', {}):
                        try:
                            data = part['body']['data']
                            padding = 4 - (len(data) % 4)
                            if padding != 4:
                                data += '=' * padding
                            html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Error decoding HTML: {str(e)}")
                            html_body = ''
                elif part.get('mimeType', '').startswith('multipart/'):
                    for subpart in part.get('parts', []):
                        process_part(subpart)
                elif part.get('filename'):
                    attachments.append({
                        'filename': part['filename'],
                        'mime_type': part['mimeType'],
                        'size': part['body'].get('size', 0)
                    })

            if 'parts' in payload:
                for part in payload['parts']:
                    process_part(part)
            elif 'body' in payload and 'data' in payload['body']:
                try:
                    data = payload['body']['data']
                    padding = 4 - (len(data) % 4)
                    if padding != 4:
                        data += '=' * padding
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                except Exception as e:
                    logger.error(f"Error decoding body: {str(e)}")
                    body = ''

            return {
                'id': message_id,
                'subject': subject,
                'from': from_header,
                'to': to_header,
                'date': datetime.fromisoformat(date.replace('Z', '+00:00')) if date else datetime.now(UTC),
                'body': body,
                'html_body': html_body,
                'attachments': attachments,
                'labels': msg.get('labelIds', [])
            }

        except HttpError as e:
            logger.error(f"Error getting email {message_id}: {str(e)}")
            if e.resp.status == 404:
                return None
            raise Exception(f"Failed to get email: {str(e)}")

    def get_email_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """获取邮件附件"""
        email_content = self.get_email_content(message_id)
        return email_content.get('attachments', [])

    def mark_as_read(self, message_id: str) -> bool:
        """标记邮件为已读"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Error marking email as read: {str(e)}")
            return False

    def mark_as_unread(self, message_id: str) -> bool:
        """标记邮件为未读"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Error marking email as unread: {str(e)}")
            return False

    def move_to_folder(self, message_id: str, folder: str) -> bool:
        """移动邮件到指定文件夹"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [folder]}
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Error moving email to folder: {str(e)}")
            return False

    def delete_email(self, message_id: str) -> bool:
        """删除邮件"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            self.service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()
            return True
        except HttpError as e:
            logger.error(f"Error deleting email: {str(e)}")
            return False
