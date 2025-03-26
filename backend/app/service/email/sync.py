"""
邮件同步服务
用于：
1. 从 Gmail 服务器获取用户的邮件数据
2. 将邮件数据保存到本地数据库
3. 支持邮件的增删改查操作
4. 支持邮件标签的管理（先不管）
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
import base64

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from backend.app.db.models import Email, User
from backend.app.config.config import Config
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailSyncService:
    """邮件同步服务类"""

    def __init__(self):
        """初始化邮件同步服务"""
        self.service = None
        self.user = None

    def initialize(self, user: User) -> None:
        """初始化服务
        :param user: 用户对象
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
        :param max_results: 最大结果数
        :return: 邮件列表
        """
        if not self.service or not self.user:
            logger.error('Service not initialized')
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
                try:
                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id'],
                        format='full'
                    ).execute()

                    # 使用 get 方法安全地访问嵌套字典
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

                    def process_part(part: dict) -> None:
                        """递归处理邮件部分

                        Args:
                            part: 邮件部分对象
                        """
                        nonlocal body, html_body

                        # 处理当前部分
                        if part.get('mimeType') == 'text/plain':
                            if 'data' in part.get('body', {}):
                                try:
                                    # 添加base64填充
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
                                    # 添加base64填充
                                    data = part['body']['data']
                                    padding = 4 - (len(data) % 4)
                                    if padding != 4:
                                        data += '=' * padding
                                    html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                                except Exception as e:
                                    logger.error(f"Error decoding HTML: {str(e)}")
                                    html_body = ''
                        elif part.get('mimeType', '').startswith('multipart/'):
                            # 递归处理多部分邮件
                            for subpart in part.get('parts', []):
                                process_part(subpart)

                    # 处理邮件内容
                    if 'parts' in payload:
                        for part in payload['parts']:
                            process_part(part)
                    elif 'body' in payload and 'data' in payload['body']:
                        try:
                            # 添加base64填充
                            data = payload['body']['data']
                            padding = 4 - (len(data) % 4)
                            if padding != 4:
                                data += '=' * padding
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Error decoding body: {str(e)}")
                            body = ''

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
                        received_at=datetime.fromisoformat(date.replace('Z', '+00:00')) if date else datetime.now(UTC),
                        raw_headers=dict(headers),
                        size=len(str(msg)),
                        labels=msg.get('labelIds', [])
                    )
                    emails.append(email)
                except HttpError as e:
                    logger.error(f"Error getting message {message['id']}: {str(e)}")
                    if e.resp.status != 404:  # 忽略 404 错误
                        raise Exception(f"Failed to get email: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing message {message['id']}: {str(e)}")
                    raise Exception(f"Failed to process email: {str(e)}")

            return emails

        except HttpError as e:
            logger.error(f"Error syncing emails: {str(e)}")
            raise Exception(f"Failed to sync emails: {str(e)}")
        except Exception as e:
            logger.error(f"Error syncing emails: {str(e)}")
            raise Exception(f"Failed to sync emails: {str(e)}")

    def get_email(self, message_id: str) -> Optional[Email]:
        """获取单个邮件
        :param message_id: 邮件ID
        :return: 邮件对象
        """
        if not self.service or not self.user:
            raise ValueError("Service not initialized")

        try:
            msg = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # 使用 get 方法安全地访问嵌套字典
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

            def process_part(part: dict) -> None:
                """递归处理邮件部分

                Args:
                    part: 邮件部分对象
                """
                nonlocal body, html_body

                # 处理当前部分
                if part.get('mimeType') == 'text/plain':
                    if 'data' in part.get('body', {}):
                        try:
                            # 添加base64填充
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
                            # 添加base64填充
                            data = part['body']['data']
                            padding = 4 - (len(data) % 4)
                            if padding != 4:
                                data += '=' * padding
                            html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Error decoding HTML: {str(e)}")
                            html_body = ''
                elif part.get('mimeType', '').startswith('multipart/'):
                    # 递归处理多部分邮件
                    for subpart in part.get('parts', []):
                        process_part(subpart)

            # 处理邮件内容
            if 'parts' in payload:
                for part in payload['parts']:
                    process_part(part)
            elif 'body' in payload and 'data' in payload['body']:
                try:
                    # 添加base64填充
                    data = payload['body']['data']
                    padding = 4 - (len(data) % 4)
                    if padding != 4:
                        data += '=' * padding
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                except Exception as e:
                    logger.error(f"Error decoding body: {str(e)}")
                    body = ''

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
                received_at=datetime.fromisoformat(date.replace('Z', '+00:00')) if date else datetime.now(UTC),
                raw_headers=dict(headers),
                size=len(str(msg)),
                labels=msg.get('labelIds', [])
            )

        except HttpError as e:
            logger.error(f"Error getting email {message_id}: {str(e)}")
            if e.resp.status == 404:
                return None
            raise Exception(f"Failed to get email: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting email {message_id}: {str(e)}")
            raise Exception(f"Failed to get email: {str(e)}")

    def update_email_labels(self, message_id: str, add_labels: List[str] = None,
                            remove_labels: List[str] = None) -> None:
        """更新邮件标签
        :param message_id: 邮件ID
        :param add_labels: 添加的标签
        :param remove_labels: 删除的标签
        """
        if not self.service or not self.user:
            raise ValueError("Service not initialized")

        try:
            body = {}
            if add_labels:
                body['addLabelIds'] = add_labels
            if remove_labels:
                body['removeLabelIds'] = remove_labels

            if not body:
                return

            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body
            ).execute()

        except HttpError as e:
            raise Exception(f"Failed to update email labels: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to update email labels: {str(e)}")
