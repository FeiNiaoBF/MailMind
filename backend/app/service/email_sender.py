"""
邮件发送服务
用于:
1. 将分析的邮箱发送给自己的邮件
"""
from typing import Optional
from flask_mail import Mail
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailSenderService:
    """邮件发送服务"""

    def __init__(self):
        """初始化服务"""
        self.mail = Mail()

    def send_email_to_me(
            self,
            subject: str,
            body: str,
            html_body: Optional[str] = None,
    ) -> bool:
        """
        发送邮件
        :param subject: 邮件主题
        :param body: 邮件正文
        :param html_body: 邮件HTML正文
        :return: 是否成功
        """
        pass
