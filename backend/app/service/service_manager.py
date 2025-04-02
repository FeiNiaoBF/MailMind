"""
服务管理器模块
用于管理各种服务的生命周期
"""
from flask import g, current_app, session
from typing import Optional, Dict, Any
from .email_service import EmailService
from .auth_service import AuthService
from .ai.ai_service import AIServiceFactory, BaseAIService
from ..db.database import db
from ..utils.logger import get_logger
from google.oauth2.credentials import Credentials
import traceback

logger = get_logger(__name__)

class ServiceManager:
    """服务管理器类"""

    @staticmethod
    def get_email_service() -> Optional[EmailService]:
        """获取邮件服务实例"""
        if not hasattr(g, 'email_service'):
            try:
                # 从会话中获取凭据
                credentials_dict = session.get('credentials')
                logger.debug(f"从会话获取凭据: {'成功' if credentials_dict else '失败'}")

                if not credentials_dict:
                    logger.warning("未找到用户凭据")
                    return None

                # 将字典转换为 Credentials 对象
                credentials = Credentials(
                    token=credentials_dict.get('token'),
                    refresh_token=credentials_dict.get('refresh_token'),
                    token_uri=credentials_dict.get('token_uri'),
                    client_id=credentials_dict.get('client_id'),
                    client_secret=credentials_dict.get('client_secret'),
                    scopes=credentials_dict.get('scopes')
                )
                logger.debug("凭据转换成功")

                # 创建邮件服务实例
                g.email_service = EmailService(db, credentials)
                logger.info("创建邮件服务实例成功")
            except Exception as e:
                logger.error(f"创建邮件服务实例失败: {str(e)}")
                return None
        return g.email_service

    @staticmethod
    def get_auth_service() -> Optional[AuthService]:
        """获取认证服务实例"""
        if not hasattr(g, 'auth_service'):
            try:
                g.auth_service = AuthService()
                logger.info("创建认证服务实例")
            except Exception as e:
                logger.error(f"创建认证服务实例失败: {str(e)}")
                return None
        return g.auth_service

    @staticmethod
    def get_ai_service(model_name: str = None) -> Optional[Any]:
        """获取AI服务实例"""
        service_key = f'ai_service_{model_name}' if model_name else 'ai_service'

        if not hasattr(g, service_key):
            try:
                # 创建新的服务实例
                service = AIServiceFactory.create_service(model_name)
                setattr(g, service_key, service)
                logger.debug(f"创建新的 {model_name} AI 服务实例")
            except Exception as e:
                logger.error(f"创建 AI 服务实例失败: {str(e)}")
                return None

        return getattr(g, service_key)

    @staticmethod
    def get_ai_service_config(provider: str = 'deepseek') -> Dict[str, Any]:
        """获取 AI 服务配置
        Args:
            provider: AI 服务提供商
        Returns:
            Dict[str, Any]: 服务配置信息
        """
        return AIServiceFactory.get_service_config(provider)

    @staticmethod
    def cleanup():
        """清理所有服务实例"""
        logger.info("开始清理服务实例")
        try:
            # 清理基础服务
            basic_services = ['auth_service', 'email_service']
            for service_name in basic_services:
                if hasattr(g, service_name):
                    service = getattr(g, service_name)
                    if hasattr(service, 'close'):
                        service.close()
                    delattr(g, service_name)
                    logger.debug(f"清理服务: {service_name}")

            # 清理AI服务
            # 获取所有g对象的属性
            all_attrs = [attr for attr in dir(g) if not attr.startswith('_')]
            ai_services = [attr for attr in all_attrs if attr.startswith('ai_service_')]

            for service_name in ai_services:
                service = getattr(g, service_name)
                if hasattr(service, 'close'):
                    service.close()
                delattr(g, service_name)
                logger.debug(f"清理AI服务: {service_name}")

            # 清理调度器服务
            if hasattr(g, 'scheduler'):
                scheduler = g.scheduler
                if hasattr(scheduler, 'shutdown'):
                    scheduler.shutdown()
                delattr(g, 'scheduler')
                logger.debug("清理调度器服务")

            logger.info("服务实例清理完成")
            return True

        except Exception as e:
            logger.error(f"清理服务实例失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")
            return False

    @staticmethod
    def get_scheduler():
        """获取调度器实例"""
        if not hasattr(g, 'scheduler'):
            from .scheduler import Scheduler
            g.scheduler = Scheduler()
        return g.scheduler
