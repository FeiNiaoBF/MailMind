"""
Mailtrap 邮件服务提供商实现
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
import imaplib
import email
from email.header import decode_header
from backend.app.config.config import Config
from backend.app.utils.logger import get_logger
from .base import EmailProvider

logger = get_logger(__name__)

class MailtrapProvider(EmailProvider):
    """Mailtrap 邮件服务提供商"""

    def __init__(self, credentials: Dict[str, Any]):
        """初始化 Mailtrap 提供商
        :param credentials: 认证信息
        """
        self.credentials = credentials
        self.imap = None

    def authenticate(self) -> bool:
        """认证服务"""
        try:
            self.imap = imaplib.IMAP4_SSL(Config.MAIL_SERVER, Config.MAIL_PORT)
            self.imap.login(self.credentials['username'], self.credentials['password'])
            return True
        except Exception as e:
            logger.error(f"Mailtrap authentication failed: {str(e)}")
            return False

    def get_emails(self, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取邮件列表"""
        if not self.imap:
            raise ValueError("Service not initialized")

        try:
            self.imap.select('INBOX')

            # 构建搜索条件
            search_criteria = []
            if start_date:
                search_criteria.append(f'SINCE "{start_date.strftime("%d-%b-%Y")}"')
            if end_date:
                search_criteria.append(f'BEFORE "{end_date.strftime("%d-%b-%Y")}"')

            # 搜索邮件
            _, message_numbers = self.imap.search(None, *search_criteria)
            emails = []

            for num in message_numbers[0].split():
                email_data = self.get_email_content(num.decode())
                if email_data:
                    emails.append(email_data)

            return emails

        except Exception as e:
            logger.error(f"Error getting emails: {str(e)}")
            raise Exception(f"Failed to get emails: {str(e)}")

    def get_email_content(self, message_id: str) -> Dict[str, Any]:
        """获取邮件内容"""
        if not self.imap:
            raise ValueError("Service not initialized")

        try:
            _, msg_data = self.imap.fetch(message_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            # 解析邮件头
            subject = decode_header(email_message['subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            from_header = email_message['from']
            to_header = email_message['to']
            date = email_message['date']

            # 解析邮件内容
            body = ''
            html_body = ''
            attachments = []

            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue

                if part.get_content_type() == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode()
                    except Exception as e:
                        logger.error(f"Error decoding plain text: {str(e)}")
                        body = ''
                elif part.get_content_type() == 'text/html':
                    try:
                        html_body = part.get_payload(decode=True).decode()
                    except Exception as e:
                        logger.error(f"Error decoding HTML: {str(e)}")
                        html_body = ''
                elif part.get_filename():
                    attachments.append({
                        'filename': part.get_filename(),
                        'mime_type': part.get_content_type(),
                        'size': len(part.get_payload(decode=True))
                    })

            return {
                'id': message_id,
                'subject': subject,
                'from': from_header,
                'to': to_header,
                'date': datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z') if date else datetime.now(UTC),
                'body': body,
                'html_body': html_body,
                'attachments': attachments,
                'labels': []
            }

        except Exception as e:
            logger.error(f"Error getting email {message_id}: {str(e)}")
            return None

    def get_email_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """获取邮件附件"""
        email_content = self.get_email_content(message_id)
        return email_content.get('attachments', []) if email_content else []

    def mark_as_read(self, message_id: str) -> bool:
        """标记邮件为已读"""
        if not self.imap:
            raise ValueError("Service not initialized")

        try:
            self.imap.store(message_id, '+FLAGS', '(\Seen)')
            return True
        except Exception as e:
            logger.error(f"Error marking email as read: {str(e)}")
            return False

    def mark_as_unread(self, message_id: str) -> bool:
        """标记邮件为未读"""
        if not self.imap:
            raise ValueError("Service not initialized")

        try:
            self.imap.store(message_id, '-FLAGS', '(\Seen)')
            return True
        except Exception as e:
            logger.error(f"Error marking email as unread: {str(e)}")
            return False

    def move_to_folder(self, message_id: str, folder: str) -> bool:
        """移动邮件到指定文件夹"""
        if not self.imap:
            raise ValueError("Service not initialized")

        try:
            self.imap.copy(message_id, folder)
            self.imap.store(message_id, '+FLAGS', '(\Deleted)')
            return True
        except Exception as e:
            logger.error(f"Error moving email to folder: {str(e)}")
            return False

    def delete_email(self, message_id: str) -> bool:
        """删除邮件"""
        if not self.imap:
            raise ValueError("Service not initialized")

        try:
            self.imap.store(message_id, '+FLAGS', '(\Deleted)')
            return True
        except Exception as e:
            logger.error(f"Error deleting email: {str(e)}")
            return False
