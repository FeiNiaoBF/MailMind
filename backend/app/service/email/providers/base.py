"""
邮件服务提供商基础接口
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC
from backend.app.models import Email, User
from backend.app.service.email.processors.base import EmailProcessor

class EmailProvider(ABC):
    """邮件服务提供商接口"""

    @abstractmethod
    def authenticate(self) -> bool:
        """认证服务"""
        pass

    @abstractmethod
    def get_emails(self, start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """获取邮件列表"""
        pass

    @abstractmethod
    def get_email_content(self, message_id: str) -> Dict[str, Any]:
        """获取邮件内容"""
        pass

    @abstractmethod
    def get_email_attachments(self, message_id: str) -> List[Dict[str, Any]]:
        """获取邮件附件"""
        pass

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """标记邮件为已读"""
        pass

    @abstractmethod
    def mark_as_unread(self, message_id: str) -> bool:
        """标记邮件为未读"""
        pass

    # 暂时不知道需不需使用
    @abstractmethod
    def move_to_folder(self, message_id: str, folder: str) -> bool:
        """移动邮件到指定文件夹"""
        pass

    @abstractmethod
    def delete_email(self, message_id: str) -> bool:
        """删除邮件"""
        pass
