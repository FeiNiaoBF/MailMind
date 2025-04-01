"""
邮件服务模块
处理邮件相关的业务逻辑
"""
from typing import Dict, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from .email_analyzer import EmailAnalysisService
from .email_sender import EmailSenderService
from .email_sync import EmailSyncService
from ..models import Email, User
from ..utils.logger import get_logger
from enum import Enum

logger = get_logger(__name__)


class SyncStatus(Enum):
    """同步状态枚举"""
    IDLE = "idle"  # 空闲状态
    RUNNING = "running"  # 正在同步
    ERROR = "error"  # 同步出错
    STOPPED = "stopped"  # 已停止


class EmailService:
    """邮件服务类"""

    def __init__(self, db, credentials: Optional[Credentials] = None):
        """初始化邮件服务
        Args:
            db: 数据库会话
            credentials: Gmail API凭据对象
        """
        self.db = db
        self.service = None
        self._sync_status = SyncStatus.IDLE
        self._sync_error = None

        logger.debug(f"初始化邮件服务 - 凭据: {'已提供' if credentials else '未提供'}")

        if credentials:
            try:
                # 确保凭据是有效的
                if not credentials.valid:
                    logger.info("凭据已过期，尝试刷新")
                    credentials.refresh()

                self.service = build('gmail', 'v1', credentials=credentials)
                logger.info("Gmail 服务初始化成功")
            except Exception as e:
                logger.error(f"Gmail 服务初始化失败: {str(e)}")
                raise
        else:
            logger.warning("Gmail 服务未初始化，部分功能可能不可用")

        # 初始化子服务
        self._sync_service = EmailSyncService(db, self.service)
        # TODO：完善其他服务
        self._analyze_service = EmailAnalysisService()
        self._sender_service = EmailSenderService()

    @property
    def sync_status(self) -> SyncStatus:
        """获取当前同步状态"""
        return self._sync_status

    @property
    def sync_error(self) -> Optional[str]:
        """获取同步错误信息"""
        return self._sync_error

    def start_sync(self, user: User, interval_hours: int = 6) -> bool:
        """启动同步服务
        Args:
            user: 用户对象
            interval_hours: 同步间隔（小时）
        Returns:
            bool: 是否启动成功
        """
        try:
            if not self.service:
                raise ValueError("Gmail 服务未初始化")

            if self._sync_status == SyncStatus.RUNNING:
                logger.warning("同步服务已在运行中")
                return True

            self._sync_status = SyncStatus.RUNNING
            self._sync_error = None

            # 启动同步服务
            success = self._sync_service.start_sync(user, interval_hours)
            if not success:
                self._sync_status = SyncStatus.ERROR
                self._sync_error = "启动同步服务失败"
                return False

            logger.info(f"已为用户 {user.email} 启动邮件同步服务")
            return True

        except Exception as e:
            self._sync_status = SyncStatus.ERROR
            self._sync_error = str(e)
            logger.error(f"启动同步服务失败: {str(e)}")
            return False

    def stop_sync(self, user: User) -> bool:
        """停止同步服务
        Args:
            user: 用户对象
        Returns:
            bool: 是否停止成功
        """
        try:
            if self._sync_status != SyncStatus.RUNNING:
                logger.warning("同步服务未在运行")
                return True

            success = self._sync_service.stop_sync(user)
            if success:
                self._sync_status = SyncStatus.STOPPED
                logger.info(f"已停止用户 {user.email} 的邮件同步服务")
            else:
                self._sync_status = SyncStatus.ERROR
                self._sync_error = "停止同步服务失败"

            return success

        except Exception as e:
            self._sync_status = SyncStatus.ERROR
            self._sync_error = str(e)
            logger.error(f"停止同步服务失败: {str(e)}")
            return False

    async def manual_sync(self, user: User, days: int = 1, interval_hours: int = 6) -> bool:
        """手动触发同步
        Args:
            user: 用户对象
            days: 同步天数
            interval_hours: 同步间隔（小时）
        Returns:
            bool: 是否同步成功
        """
        try:
            if not self.service:
                raise ValueError("Gmail 服务未初始化")

            if self._sync_status == SyncStatus.RUNNING:
                logger.warning("同步服务正在运行中，请等待完成")
                return False

            self._sync_status = SyncStatus.RUNNING
            self._sync_error = None

            # 执行同步
            success = await self._sync_service.manual_sync(user, days)
            if not success:
                self._sync_status = SyncStatus.ERROR
                self._sync_error = "手动同步失败"
                return False

            # 同步成功后，设置状态为空闲
            self._sync_status = SyncStatus.IDLE
            logger.info(f"用户 {user.email} 的手动同步完成")
            return True

        except Exception as e:
            self._sync_status = SyncStatus.ERROR
            self._sync_error = str(e)
            logger.error(f"手动同步失败: {str(e)}")
            return False

    def get_emails(self, user: User, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """获取邮件列表
        Args:
            user: 用户对象
            page: 页码
            per_page: 每页数量
        Returns:
            Dict[str, Any]: 邮件列表和分页信息
        """
        try:
            logger.debug(f"开始获取邮件列表 - 用户ID: {user.id}, 邮箱: {user.email}, 页码: {page}, 每页数量: {per_page}")

            # 检查用户ID
            if not user.id:
                logger.error("用户ID为空")
                raise ValueError("用户ID不能为空")

            # 构建查询
            query = Email.query.filter_by(user_id=user.id)
            logger.debug(f"构建查询条件: user_id={user.id}")

            # 获取总数
            total = query.count()
            logger.debug(f"查询到总邮件数: {total}")

            # 获取分页数据
            emails = query.order_by(Email.received_at.desc()) \
                .offset((page - 1) * per_page) \
                .limit(per_page) \
                .all()

            logger.debug(f"当前页邮件数: {len(emails)}")

            # 转换为字典并记录每封邮件的基本信息
            email_dicts = []
            for email in emails:
                try:
                    email_dict = email.to_dict()
                    logger.debug(f"邮件信息 - ID: {email_dict.get('id')}, 主题: {email_dict.get('subject')}, 发件人: {email_dict.get('from_email')}, 接收时间: {email_dict.get('received_at')}")
                    email_dicts.append(email_dict)
                except Exception as e:
                    logger.error(f"转换邮件数据失败 - ID: {email.id}, 错误: {str(e)}")
                    continue

            result = {
                "emails": email_dicts,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }

            logger.debug(f"返回数据: 邮件数={len(email_dicts)}, 总数={total}, 总页数={result['total_pages']}")
            return result

        except Exception as e:
            logger.error(f"获取邮件列表失败: {str(e)}")
            raise

    def get_email_by_id(self, user: User, email_id: int) -> Optional[Email]:
        """根据ID获取邮件
        Args:
            user: 用户对象
            email_id: 邮件ID
        Returns:
            Optional[Email]: 邮件对象
        """
        try:
            return Email.query.filter_by(
                user_id=user.id,
                id=email_id
            ).first()
        except Exception as e:
            logger.error(f"获取邮件详情失败: {str(e)}")
            raise

    async def send_email(self, user: User, email_data: Dict[str, Any]) -> bool:
        """发送邮件
        Args:
            user: 用户对象
            email_data: 邮件数据
        Returns:
            bool: 是否发送成功
        """
        try:
            if not self.service:
                raise ValueError("Gmail 服务未初始化")

            return await self._sender_service.send_email(
                service=self.service,
                user=user,
                email_data=email_data
            )
        except Exception as e:
            logger.error(f"发送邮件失败: {str(e)}")
            raise
