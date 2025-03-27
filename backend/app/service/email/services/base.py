"""
邮件服务基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from backend.app.models import Email, User
from backend.app.service.email.providers.base import EmailProvider
from backend.app.service.email.processors.base import EmailProcessor
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

class EmailService(ABC):
    """邮件服务基类"""

    def __init__(self, provider: EmailProvider, processor: EmailProcessor):
        """初始化邮件服务
        :param provider: 邮件服务提供商
        :param processor: 邮件处理器
        """
        self.provider = provider
        self.processor = processor

    @abstractmethod
    def initialize(self, user: User) -> bool:
        """初始化服务
        :param user: 用户对象
        :return: 是否成功
        """
        pass

    @abstractmethod
    def sync_emails(self, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Email]:
        """同步邮件
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 邮件列表
        """
        pass

    @abstractmethod
    def get_email(self, message_id: str) -> Optional[Email]:
        """获取单个邮件
        :param message_id: 邮件ID
        :return: 邮件对象
        """
        pass

    @abstractmethod
    def process_email(self, email: Email) -> Dict[str, Any]:
        """处理邮件
        :param email: 邮件对象
        :return: 处理结果
        """
        pass

    @abstractmethod
    def process_emails(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 处理结果列表
        """
        pass

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """标记邮件为已读
        :param message_id: 邮件ID
        :return: 是否成功
        """
        pass

    @abstractmethod
    def mark_as_unread(self, message_id: str) -> bool:
        """标记邮件为未读
        :param message_id: 邮件ID
        :return: 是否成功
        """
        pass

    @abstractmethod
    def move_to_folder(self, message_id: str, folder: str) -> bool:
        """移动邮件到指定文件夹
        :param message_id: 邮件ID
        :param folder: 目标文件夹
        :return: 是否成功
        """
        pass

    @abstractmethod
    def delete_email(self, message_id: str) -> bool:
        """删除邮件
        :param message_id: 邮件ID
        :return: 是否成功
        """
        pass
