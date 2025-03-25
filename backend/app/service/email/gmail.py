from typing import List
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .interface import EmailServiceInterface, EmailMessage, EmailAttachment
from backend.app.config import Config

class GmailEmailService(EmailServiceInterface):
    """Gmail邮件服务实现（用于生产环境）"""

    def __init__(self):
        self.credentials = Credentials.from_authorized_user_info(Config.GMAIL_CREDENTIALS)
        self.service = build('gmail', 'v1', credentials=self.credentials)

    def _create_message(self, message: EmailMessage) -> dict:
        """创建Gmail消息格式

        Args:
            message: 邮件消息对象

        Returns:
            dict: Gmail消息格式
        """
        msg = MIMEMultipart('alternative')
        msg['Subject'] = message.subject
        msg['From'] = message.from_email or Config.DEFAULT_FROM_EMAIL
        msg['To'] = ', '.join(message.to_emails)

        if message.cc_emails:
            msg['Cc'] = ', '.join(message.cc_emails)
        if message.bcc_emails:
            msg['Bcc'] = ', '.join(message.bcc_emails)
        if message.reply_to:
            msg['Reply-To'] = message.reply_to

        # 添加纯文本内容
        msg.attach(MIMEText(message.body, 'plain'))

        # 如果有HTML内容，添加HTML版本
        if message.html_body:
            msg.attach(MIMEText(message.html_body, 'html'))

        # 添加附件
        if message.attachments:
            for attachment in message.attachments:
                part = MIMEApplication(attachment.data)
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=attachment.filename
                )
                msg.attach(part)

        return {'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')}

    def send_email(self, message: EmailMessage) -> bool:
        """发送邮件

        Args:
            message: 邮件消息对象

        Returns:
            bool: 发送是否成功
        """
        try:
            gmail_message = self._create_message(message)
            sent_message = self.service.users().messages().send(
                userId='me',
                body=gmail_message
            ).execute()

            return bool(sent_message.get('id'))

        except Exception as e:
            print(f"Error sending email via Gmail: {str(e)}")
            return False

    def send_bulk_emails(self, messages: List[EmailMessage]) -> List[bool]:
        """批量发送邮件

        Args:
            messages: 邮件消息对象列表

        Returns:
            List[bool]: 每个邮件发送的结果列表
        """
        return [self.send_email(message) for message in messages]

    def get_delivery_status(self, message_id: str) -> dict:
        """获取邮件投递状态

        Args:
            message_id: 邮件ID

        Returns:
            dict: 投递状态信息
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()

            return {
                "status": "success",
                "message_id": message_id,
                "thread_id": message.get('threadId'),
                "label_ids": message.get('labelIds', [])
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def validate_email(self, email: str) -> bool:
        """验证邮箱地址

        Args:
            email: 邮箱地址

        Returns:
            bool: 邮箱是否有效
        """
        # 简单的邮箱格式验证
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def fetch_emails(self, max_results: int = 10) -> List[EmailMessage]:
        """获取邮件列表

        Args:
            max_results: 最大获取数量

        Returns:
            List[EmailMessage]: 邮件列表

        Raises:
            Exception: 当API调用失败时抛出异常
        """
        try:
            emails = []
            next_page_token = None

            while len(emails) < max_results:
                # 获取邮件列表
                results = self.service.users().messages().list(
                    userId='me',
                    maxResults=min(max_results - len(emails), 100),
                    pageToken=next_page_token
                ).execute()

                messages = results.get('messages', [])
                if not messages:
                    break

                # 获取每封邮件的详细信息
                for message in messages:
                    if len(emails) >= max_results:
                        break

                    msg = self.service.users().messages().get(
                        userId='me',
                        id=message['id']
                    ).execute()

                    email = self._parse_email_message(msg)
                    if email:
                        emails.append(email)

                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break

            return emails

        except Exception as e:
            raise Exception(f"Failed to fetch emails: {str(e)}")

    def _parse_email_message(self, message: dict) -> EmailMessage:
        """解析Gmail邮件消息

        Args:
            message: Gmail API返回的邮件消息

        Returns:
            EmailMessage: 解析后的邮件消息对象
        """
        try:
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), '')
            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            to_header = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # 解析邮件内容
            body = ''
            html_body = ''
            attachments = []

            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif part['mimeType'] == 'text/html':
                        if 'data' in part['body']:
                            html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    elif 'filename' in part:
                        # 处理附件
                        attachment = self._get_attachment(message['id'], part['body']['attachmentId'])
                        if attachment:
                            attachments.append(attachment)
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                # 处理单部分邮件
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

            return EmailMessage(
                uid=message['id'],
                subject=subject,
                from_header=from_header,
                to_header=to_header,
                date=date,
                body=body,
                html_body=html_body,
                labels=message.get('labelIds', []),
                attachments=attachments
            )

        except Exception as e:
            print(f"Error parsing email message: {str(e)}")
            return None

    def _get_attachment(self, message_id: str, attachment_id: str) -> EmailAttachment:
        """获取邮件附件

        Args:
            message_id: 邮件ID
            attachment_id: 附件ID

        Returns:
            EmailAttachment: 附件对象
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()

            if 'data' in attachment:
                return EmailAttachment(
                    filename=attachment.get('filename', ''),
                    mime_type=attachment.get('mimeType', ''),
                    data=base64.urlsafe_b64decode(attachment['data'])
                )
            return None

        except Exception as e:
            print(f"Error getting attachment: {str(e)}")
            return None
