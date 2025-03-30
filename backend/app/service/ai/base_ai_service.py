"""
AI 服务基类模块
定义 AI 服务的基本接口
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from ...utils.logger import get_logger

logger = get_logger(__name__)

class AIServiceError(Exception):
    """AI 服务错误"""
    pass

class BaseAIService(ABC):
    """AI 服务基类"""

    def __init__(self, api_key: str, model: str):
        """初始化 AI 服务

        Args:
            api_key: API 密钥
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model
        logger.info(f"初始化 AI 服务: {self.__class__.__name__}")

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置

        Args:
            config: 配置信息

        Returns:
            bool: 配置是否有效
        """
        pass

    @abstractmethod
    def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """发送对话请求

        Args:
            message: 用户消息
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 响应结果
        """
        pass

    def close(self):
        """关闭服务"""
        pass
