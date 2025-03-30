"""
AI 服务工厂模块
用于创建和管理 AI 服务实例
"""
from typing import Dict, Any, Type, Optional
from .base_ai_service import BaseAIService, AIServiceError
from .deepseek_service import DeepSeekService
from ...utils.logger import get_logger

logger = get_logger(__name__)

class AIServiceFactory:
    """AI 服务工厂类"""

    # 支持的服务提供商
    PROVIDERS: Dict[str, Type[BaseAIService]] = {
        'deepseek': DeepSeekService,
    }

    # 单例实例
    _instance: Optional[BaseAIService] = None
    _current_provider: Optional[str] = None
    _current_api_key: Optional[str] = None
    _current_model: Optional[str] = None

    @classmethod
    def create_service(cls, provider: str, **kwargs) -> BaseAIService:
        """创建或获取 AI 服务实例

        Args:
            provider: 服务提供商名称
            **kwargs: 服务配置参数，必须包含 api_key 和 model

        Returns:
            BaseAIService: AI 服务实例

        Raises:
            AIServiceError: 服务创建失败时抛出
        """
        try:
            provider = provider.lower()
            if provider not in cls.PROVIDERS:
                raise AIServiceError(f"不支持的 AI 服务提供商: {provider}")

            # 检查必要参数
            api_key = kwargs.get('api_key')
            model = kwargs.get('model')
            if not api_key or not model:
                raise AIServiceError("缺少必要参数：api_key 和 model")

            # 如果实例已存在且配置相同，直接返回
            if (cls._instance and
                cls._current_provider == provider and
                cls._current_api_key == api_key and
                cls._current_model == model):
                logger.info("使用现有的 AI 服务实例")
                return cls._instance

            # 创建新实例
            service_class = cls.PROVIDERS[provider]
            service = service_class(**kwargs)

            # 验证配置
            if not service.validate_config({'api_key': api_key, 'model': model}):
                raise AIServiceError("API 配置验证失败")

            # 更新实例信息
            cls._instance = service
            cls._current_provider = provider
            cls._current_api_key = api_key
            cls._current_model = model

            logger.info(f"成功创建新的 {provider} AI 服务实例")
            return service

        except Exception as e:
            logger.error(f"创建 AI 服务失败: {str(e)}")
            raise AIServiceError(f"创建 AI 服务失败: {str(e)}")

    @classmethod
    def get_service_config(cls, provider: str) -> Dict[str, Any]:
        """获取服务配置信息

        Args:
            provider: 服务提供商名称

        Returns:
            Dict[str, Any]: 服务配置信息

        Raises:
            AIServiceError: 获取配置失败时抛出
        """
        try:
            provider = provider.lower()
            if provider not in cls.PROVIDERS:
                raise AIServiceError(f"不支持的 AI 服务提供商: {provider}")

            if provider == "deepseek":
                return {
                    "name": "DeepSeek",
                    "models": [
                        {
                            "id": "deepseek-chat",
                            "name": "DeepSeek-V3",
                            "description": "通用对话模型，支持多种任务",
                            "max_tokens": 8192,
                            "temperature_range": [0, 2]
                        }
                    ]
                }
            else:
                raise AIServiceError(f"暂未实现 {provider} 的配置信息")

        except Exception as e:
            logger.error(f"获取 AI 服务配置失败: {str(e)}")
            raise AIServiceError(f"获取 AI 服务配置失败: {str(e)}")

    @classmethod
    def get_instance(cls) -> Optional[BaseAIService]:
        """获取当前的 AI 服务实例

        Returns:
            Optional[BaseAIService]: AI 服务实例，如果未创建则返回 None
        """
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置 AI 服务实例"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
            cls._current_provider = None
            cls._current_api_key = None
            cls._current_model = None
            logger.info("AI 服务实例已重置")
