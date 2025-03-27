"""
邮件同步服务
用于：
1. 从邮件服务器同步邮件
2. 保存邮件到数据库
3. 管理邮件状态
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from flask import current_app
from sqlalchemy.orm import Session
from backend.app.models import Email, User
from backend.app.db.database import db
from backend.app.service.email.providers.base import EmailProvider
from backend.app.service.email.processors.base import EmailProcessor
from backend.app.utils.logger import get_logger
from .base import EmailService
from backend.app.service.email.providers.gmail import GmailProvider
from backend.app.config.config import Config

logger = get_logger(__name__)

class EmailSyncService(EmailService):
    """邮件同步服务"""

    def __init__(self, processor: Optional[EmailProcessor] = None):
        """初始化邮件同步服务
        :param processor: 邮件处理器
        """
        provider = GmailProvider(Config.GMAIL_CLIENT_CONFIG)
        super().__init__(provider, processor)
        self.user = None

    def initialize(self, user: User) -> bool:
        """初始化服务
        :param user: 用户对象
        :return: 是否成功
        """
        try:
            self.user = user
            return self.provider.authenticate()
        except Exception as e:
            logger.error(f"Error initializing sync service: {str(e)}")
            return False

    def sync_emails(self, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   max_results: Optional[int] = None) -> List[Email]:
        """同步邮件
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param max_results: 最大结果数
        :return: 邮件列表
        """
        if not self.user:
            raise ValueError("Service not initialized")

        try:
            # 从服务器获取邮件
            email_data_list = self.provider.get_emails(start_date, end_date, max_results)

            # 处理邮件
            emails = []
            for email_data in email_data_list:
                try:
                    # 检查邮件是否已存在
                    existing_email = Email.query.filter_by(
                        user_id=self.user.id,
                        uid=email_data['id']
                    ).first()

                    if existing_email:
                        # 更新现有邮件
                        self._update_email(existing_email, email_data)
                        emails.append(existing_email)
                    else:
                        # 创建新邮件
                        email = self._create_email(email_data)
                        emails.append(email)
                except Exception as e:
                    logger.error(f"Error processing email {email_data['id']}: {str(e)}")
                    continue

            # 提交更改
            db.session.commit()
            return emails

        except Exception as e:
            logger.error(f"Error syncing emails: {str(e)}")
            db.session.rollback()
            raise Exception(f"Failed to sync emails: {str(e)}")

    def get_email(self, message_id: str) -> Optional[Email]:
        """获取单个邮件
        :param message_id: 邮件ID
        :return: 邮件对象
        """
        if not self.user:
            raise ValueError("Service not initialized")

        try:
            # 从服务器获取邮件
            email_data = self.provider.get_email_content(message_id)
            if not email_data:
                return None

            # 检查邮件是否已存在
            existing_email = Email.query.filter_by(
                user_id=self.user.id,
                uid=message_id
            ).first()

            if existing_email:
                # 更新现有邮件
                self._update_email(existing_email, email_data)
            else:
                # 创建新邮件
                existing_email = self._create_email(email_data)

            # 提交更改
            db.session.commit()
            return existing_email

        except Exception as e:
            logger.error(f"Error getting email {message_id}: {str(e)}")
            db.session.rollback()
            raise Exception(f"Failed to get email: {str(e)}")

    def process_email(self, email: Email) -> Dict[str, Any]:
        """处理邮件
        :param email: 邮件对象
        :return: 处理结果
        """
        return self.processor.process(email)

    def process_emails(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 处理结果列表
        """
        return self.processor.batch_process(emails)

    def update_email_labels(self, message_id: str,
                          add_labels: Optional[List[str]] = None,
                          remove_labels: Optional[List[str]] = None) -> bool:
        """更新邮件标签
        :param message_id: 邮件ID
        :param add_labels: 要添加的标签
        :param remove_labels: 要移除的标签
        :return: 是否成功
        """
        if not self.user:
            raise ValueError("Service not initialized")

        try:
            return self.provider.update_labels(message_id, add_labels, remove_labels)
        except Exception as e:
            logger.error(f"Error updating email labels: {str(e)}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """标记邮件为已读
        :param message_id: 邮件ID
        :return: 是否成功
        """
        if not self.user:
            raise ValueError("Service not initialized")

        try:
            return self.provider.mark_as_read(message_id)
        except Exception as e:
            logger.error(f"Error marking email as read: {str(e)}")
            return False

    def mark_as_unread(self, message_id: str) -> bool:
        """标记邮件为未读
        :param message_id: 邮件ID
        :return: 是否成功
        """
        if not self.user:
            raise ValueError("Service not initialized")

        try:
            return self.provider.mark_as_unread(message_id)
        except Exception as e:
            logger.error(f"Error marking email as unread: {str(e)}")
            return False

    def move_to_folder(self, message_id: str, folder: str) -> bool:
        """移动邮件到指定文件夹
        :param message_id: 邮件ID
        :param folder: 目标文件夹
        :return: 是否成功
        """
        if not self.user:
            raise ValueError("Service not initialized")

        try:
            return self.provider.move_to_folder(message_id, folder)
        except Exception as e:
            logger.error(f"Error moving email to folder: {str(e)}")
            return False

    def delete_email(self, message_id: str) -> bool:
        """删除邮件
        :param message_id: 邮件ID
        :return: 是否成功
        """
        if not self.user:
            raise ValueError("Service not initialized")

        try:
            return self.provider.delete_email(message_id)
        except Exception as e:
            logger.error(f"Error deleting email: {str(e)}")
            return False

    def _create_email(self, email_data: Dict[str, Any]) -> Email:
        """创建邮件对象
        :param email_data: 邮件数据
        :return: 邮件对象
        """
        email = Email(
            user_id=self.user.id,
            uid=email_data['id'],
            message_id=email_data['id'],
            from_header=email_data['from'],
            to_header=email_data['to'],
            subject=email_data['subject'],
            body=email_data['body'],
            html_body=email_data['html_body'],
            received_at=email_data['date'],
            raw_headers=email_data.get('headers', {}),
            attachments=email_data.get('attachments', []),
            labels=email_data.get('labels', []),
            size=email_data.get('size', 0)
        )
        db.session.add(email)
        return email

    def _update_email(self, email: Email, email_data: Dict[str, Any]) -> None:
        """更新邮件对象
        :param email: 邮件对象
        :param email_data: 邮件数据
        """
        email.from_header = email_data['from']
        email.to_header = email_data['to']
        email.subject = email_data['subject']
        email.body = email_data['body']
        email.html_body = email_data['html_body']
        email.received_at = email_data['date']
        email.raw_headers = email_data.get('headers', email.raw_headers)
        email.attachments = email_data.get('attachments', email.attachments)
        email.labels = email_data.get('labels', email.labels)
        email.size = email_data.get('size', email.size)
