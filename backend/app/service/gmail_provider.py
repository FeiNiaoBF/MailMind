"""
Gmail服务提供者
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.exceptions import GmailProviderError

class GmailProvider:
    """Gmail服务提供者"""

    def __init__(self):
        """初始化Gmail服务"""
        self.service = None

    def initialize(self, credentials: Dict[str, Any]) -> bool:
        """初始化服务

        Args:
            credentials: OAuth凭证

        Returns:
            是否初始化成功
        """
        try:
            creds = Credentials.from_authorized_user_info(credentials)
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            raise GmailProviderError(f"Failed to initialize Gmail service: {str(e)}")

    def list_messages(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取邮件列表

        Args:
            days: 天数

        Returns:
            邮件列表
        """
        try:
            # 计算时间范围
            after_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y/%m/%d')

            # 获取邮件列表
            results = self.service.users().messages().list(
                userId='me',
                q=f'after:{after_date}'
            ).execute()

            messages = results.get('messages', [])
            if not messages:
                return []

            # 获取邮件详情
            email_list = []
            for message in messages:
                email = self.get_message(message['id'])
                if email:
                    email_list.append(email)

            return email_list

        except Exception as e:
            raise GmailProviderError(f"Failed to list messages: {str(e)}")

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """获取邮件详情

        Args:
            message_id: 邮件ID

        Returns:
            邮件详情
        """
        try:
            # 获取邮件详情
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # 解析邮件内容
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            recipient = next((h['value'] for h in headers if h['name'] == 'To'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            # 获取邮件正文
            body = self._get_message_body(message['payload'])

            return {
                'id': message_id,
                'uid': message_id,
                'message_id': message_id,
                'subject': subject,
                'from': sender,
                'to': recipient,
                'date': date,
                'body': body,
                'html_body': body,  # Gmail API返回的是HTML格式
                'headers': headers,
                'attachments': [],  # TODO: 实现附件处理
                'labels': message.get('labelIds', []),
                'size': len(str(message))
            }

        except Exception as e:
            raise GmailProviderError(f"Failed to get message: {str(e)}")

    def _get_message_body(self, payload: Dict[str, Any]) -> str:
        """获取邮件正文

        Args:
            payload: 邮件负载

        Returns:
            邮件正文
        """
        if 'body' in payload and 'data' in payload['body']:
            return payload['body']['data']

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return part['body']['data']
                elif part['mimeType'] == 'text/html':
                    return part['body']['data']

        return ''
