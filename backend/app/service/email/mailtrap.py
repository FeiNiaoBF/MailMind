from typing import List
import requests
from .interface import EmailServiceInterface, EmailMessage, EmailAttachment
from backend.app.config import Config


class MailtrapEmailService(EmailServiceInterface):
    """Mailtrap邮件服务实现（用于开发环境）"""

    def __init__(self):
        self.api_token = Config.MAILTRAP_API_TOKEN
        self.inbox_id = Config.MAILTRAP_INBOX_ID
        self.base_url = "https://api.mailtrap.io/api/v1"
        self.headers = {
            "Api-Token": self.api_token,
            "Content-Type": "application/json"
        }

    def send_email(self, message: EmailMessage) -> bool:
        """发送邮件到Mailtrap
        :param message: 邮件消息对象
        :return: 发送结果
        """
        try:
            payload = {
                "from": {"email": message.from_email or Config.DEFAULT_FROM_EMAIL},
                "to": [{"email": email} for email in message.to_emails],
                "subject": message.subject,
                "text": message.body,
                "html": message.html_body,
                "cc": [{"email": email} for email in (message.cc_emails or [])],
                "bcc": [{"email": email} for email in (message.bcc_emails or [])],
                "reply_to": message.reply_to
            }

            if message.attachments:
                payload["attachments"] = [
                    {
                        "content": attachment.data.decode('base64'),
                        "filename": attachment.filename,
                        "type": attachment.content_type
                    }
                    for attachment in message.attachments
                ]

            response = requests.post(
                f"{self.base_url}/inboxes/{self.inbox_id}/messages",
                headers=self.headers,
                json=payload
            )

            return response.status_code == 201

        except Exception as e:
            print(f"Error sending email via Mailtrap: {str(e)}")
            return False

    def send_bulk_emails(self, messages: List[EmailMessage]) -> List[bool]:
        """批量发送邮件
        :param messages: 邮件消息对象列表
        :return: 发送结果列表
        """
        return [self.send_email(message) for message in messages]

    def get_delivery_status(self, message_id: str) -> dict:
        """获取邮件投递状态
        :param message_id: 邮件ID
        :return: 邮件投递状态
        """
        try:
            response = requests.get(
                f"{self.base_url}/messages/{message_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "message": "Failed to get delivery status"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def validate_email(self, email: str) -> bool:
        """验证邮箱地址
        :param email: 邮箱地址
        :return: 是否有效
        """
        # 简单的邮箱格式验证
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
