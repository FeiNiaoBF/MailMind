"""
邮件处理器基类
"""
from typing import Dict, Any, List
from abc import ABC, abstractmethod
from backend.app.models import Email

class EmailProcessor(ABC):
    """邮件处理器基类"""

    @abstractmethod
    def process(self, email: Email) -> Dict[str, Any]:
        """处理邮件
        :param email: 邮件对象
        :return: 处理结果
        """
        pass

    @abstractmethod
    def batch_process(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 处理结果列表
        """
        pass
