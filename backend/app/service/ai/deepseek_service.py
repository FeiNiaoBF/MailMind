"""
DeepSeek AI 服务模块
实现 DeepSeek API 的调用
"""
import os
import httpx
from typing import Dict, Any
from .base_ai_service import BaseAIService, AIServiceError
from ...utils.logger import get_logger

logger = get_logger(__name__)

# 代理配置
PROXY_HOST = os.getenv('PROXY_HOST', '127.0.0.1')
PROXY_PORT = os.getenv('PROXY_PORT', '7890')
PROXIES = {
    'http://': f'http://{PROXY_HOST}:{PROXY_PORT}',
    'https://': f'http://{PROXY_HOST}:{PROXY_PORT}'
}

class DeepSeekService(BaseAIService):
    """DeepSeek AI 服务类"""

    BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """初始化 DeepSeek 服务

        Args:
            api_key: API 密钥
            model: 模型名称
        """
        super().__init__(api_key, model)

        # 设置超时
        timeout = httpx.Timeout(
            connect=5.0,    # 连接超时
            read=30.0,      # 读取超时
            write=5.0,      # 写入超时
            pool=5.0        # 连接池超时
        )

        # 设置重试
        transport = httpx.HTTPTransport(
            retries=3,
            verify=False  # 禁用SSL验证
        )

        # 创建客户端
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            proxies=PROXIES,
            timeout=timeout,
            transport=transport,
            follow_redirects=True
        )
        logger.info("DeepSeek 服务初始化完成")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """验证配置

        Args:
            config: 配置信息

        Returns:
            bool: 配置是否有效
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 测试 API 连接
                response = self.client.get("/models")
                if response.status_code == 200:
                    logger.info("DeepSeek API 验证成功")
                    return True
                logger.warning(f"API 验证失败，状态码: {response.status_code}")
                return False
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"API 验证失败，第 {attempt + 1} 次重试: {str(e)}")
                    continue
                logger.error(f"DeepSeek API 验证失败: {str(e)}")
                return False
        return False

    def chat(self, message: str, **kwargs) -> Dict[str, Any]:
        """发送对话请求

        Args:
            message: 用户消息
            **kwargs: 其他参数

        Returns:
            Dict[str, Any]: 响应结果

        Raises:
            AIServiceError: 请求失败时抛出
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 构建请求数据
                data = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": message}],
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 1000),
                    "stream": kwargs.get("stream", False)
                }

                # 发送请求
                response = self.client.post("/chat/completions", json=data)
                response.raise_for_status()

                # 解析响应
                result = response.json()
                return {
                    "response": result["choices"][0]["message"]["content"]
                }

            except httpx.TimeoutException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"请求超时，第 {attempt + 1} 次重试: {str(e)}")
                    continue
                logger.error(f"DeepSeek API 请求超时: {str(e)}")
                raise AIServiceError(f"API 请求超时: {str(e)}")
            except httpx.HTTPError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"HTTP 错误，第 {attempt + 1} 次重试: {str(e)}")
                    continue
                logger.error(f"DeepSeek API 请求失败: {str(e)}")
                raise AIServiceError(f"API 请求失败: {str(e)}")
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"请求失败，第 {attempt + 1} 次重试: {str(e)}")
                    continue
                logger.error(f"DeepSeek 服务处理失败: {str(e)}")
                raise AIServiceError(f"服务处理失败: {str(e)}")

    def close(self):
        """关闭服务"""
        if self.client:
            self.client.close()
            logger.info("DeepSeek 服务已关闭")
