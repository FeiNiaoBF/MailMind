"""
邮件服务接口
# TODO: 需要重构
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Union
from dataclasses import dataclass


@dataclass
class EmailAttachment:
    """邮件附件数据类
    :type filename: str: 附件文件名
    :type content_type: str: 附件类型
    :type data: bytes: 附件数据
    """
    filename: str
    content_type: str
    data: bytes


@dataclass
class EmailMessage:
    """邮件消息数据类
    :type uid: str: 邮件唯一标识符
    :type subject: str: 邮件主题
    :type body: str: 邮件正文
    :type html_body: Optional[str]: 邮件HTML正文
    :type from_header: str: 发件人邮箱
    :type to_header: str: 收件人邮箱
    :type date: str: 邮件日期
    :type labels: List[str]: 邮件标签
    :type attachments: List[EmailAttachment]: 附件列表
    """
    uid: str
    subject: str
    body: str
    html_body: Optional[str] = None
    from_header: str = ''
    to_header: str = ''
    date: str = ''
    labels: List[str] = None
    attachments: List[EmailAttachment] = None


class EmailAuthInterface(ABC):
    """邮件服务接口"""

    @abstractmethod
    def authenticate(self, user_id: int, **kwargs) -> Dict:
        """认证方法
        :param user_id: 用户ID
        :param kwargs: 认证参数
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供者名称
        :return: 提供者名称
        """
        pass


class EmailServiceInterface(ABC):
    """邮件服务接口"""

    @abstractmethod
    def send_email(self, message: EmailMessage) -> bool:
        """发送邮件
        :param message: 邮件消息对象
        :return: 发送结果
        """
        pass

    @abstractmethod
    def send_bulk_emails(self, messages: List[EmailMessage]) -> List[bool]:
        """批量发送邮件
        :param messages: 邮件消息对象列表
        :return: 发送结果列表
        """
        pass

    @abstractmethod
    def get_delivery_status(self, message_id: str) -> dict:
        """获取邮件投递状态
        :param message_id: 邮件ID
        :return: 投递状态信息
        """
        pass

    @abstractmethod
    def validate_email(self, email: str) -> bool:
        """验证邮箱地址
        :param email: 邮箱地址
        :return: 是否有效
        """
        pass

    @abstractmethod
    def initialize(self, **kwargs) -> None:
        """初始化服务
        :param kwargs: 配置参数
        :return: None
        """
        pass

    @abstractmethod
    def fetch_emails(self,
                     since: Optional[datetime] = None,
                     limit: Optional[int] = None) -> List[Dict]:
        """获取邮件
        :param since: 起始时间
        :param limit: 获取数量
        :return: 邮件列表
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """获取邮箱服务提供者名称"""
        pass
