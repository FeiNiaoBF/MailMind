"""
邮件同步服务模块
处理邮件同步相关的业务逻辑
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from googleapiclient.discovery import Resource
from ..models import Email, User
from ..utils.logger import get_logger
from .scheduler_service import SchedulerService
import json
import traceback
import pytz

logger = get_logger(__name__)


class EmailSyncService:
    """邮件同步服务类"""

    def __init__(self, db, gmail_service: Optional[Resource] = None):
        """初始化邮件同步服务
        Args:
            db: 数据库会话
            gmail_service: Gmail API 服务实例
        """
        self.db = db
        self.scheduler = SchedulerService()
        self.service = gmail_service
        logger.debug(f'Gmail 服务: {gmail_service}')
        if gmail_service:
            logger.info("Gmail 服务初始化成功")
        else:
            logger.warning("Gmail 服务未初始化，部分功能可能不可用")

    def start_sync(self, user: User, interval_hours: int = 6) -> bool:
        """启动邮件同步
        Args:
            user: 用户对象
            interval_hours: 同步间隔（小时）
        Returns:
            bool: 是否启动成功
        """
        try:
            if not self.service:
                raise ValueError("Gmail 服务未初始化")

            # 创建定时同步任务
            job = self.scheduler.create_job(
                name=f"email_sync_{user.id}",
                func=self._sync_emails_task,
                trigger=f"interval:{interval_hours * 3600}",
                args=[user.id]
            )

            logger.info(f"邮件同步任务启动成功: {job['id']}")
            return True
        except Exception as e:
            logger.error(f"启动邮件同步失败: {str(e)}")
            return False

    def stop_sync(self, user: User) -> bool:
        """停止邮件同步
        Args:
            user: 用户对象
        Returns:
            bool: 是否停止成功
        """
        try:
            # 查找并删除用户的同步任务
            jobs = self.scheduler.get_all_jobs()
            for job in jobs:
                if job['name'] == f"email_sync_{user.id}":
                    self.scheduler.remove_job(job['id'])
                    logger.info(f"停止邮件同步任务: {job['id']}")
                    return True
            return False
        except Exception as e:
            logger.error(f"停止邮件同步失败: {str(e)}")
            return False

    async def manual_sync(self, user: User, days: int = 1) -> bool:
        """手动触发同步
        Args:
            user: 用户对象
            days: 同步天数
        Returns:
            bool: 是否同步成功
        """
        try:
            if not self.service:
                raise ValueError("Gmail 服务未初始化")

            # 计算同步时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 执行同步
            await self._sync_emails(user, start_date, end_date)
            return True
        except Exception as e:
            logger.error(f"手动同步失败: {str(e)}")
            return False

    async def _sync_emails_task(self, user_id: int):
        """同步任务执行函数
        Args:
            user_id: 用户ID
        """
        try:
            user = User.query.get(user_id)
            if not user:
                logger.error(f"用户不存在: {user_id}")
                return

            # 获取上次同步时间
            last_sync = Email.query.filter_by(user_id=user_id) \
                .order_by(Email.received_at.desc()) \
                .first()

            start_date = last_sync.received_at if last_sync else datetime.now() - timedelta(days=1)
            end_date = datetime.now()

            await self._sync_emails(user, start_date, end_date)
        except Exception as e:
            logger.error(f"同步任务执行失败: {str(e)}")

    async def _sync_emails(self, user: User, start_date: datetime, end_date: datetime):
        """同步邮件
        Args:
            user: 用户对象
            start_date: 开始时间
            end_date: 结束时间
        """
        try:
            logger.info(f"开始同步邮件 - 用户: {user.email}, 开始时间: {start_date}, 结束时间: {end_date}")

            # 检查Gmail服务
            if not self.service:
                logger.error("Gmail服务未初始化")
                raise ValueError("Gmail服务未初始化")

            # 验证时间范围
            if start_date > end_date:
                logger.error("开始时间不能晚于结束时间")
                raise ValueError("开始时间不能晚于结束时间")

            # 构建查询条件
            query = f'after:{int(start_date.timestamp())} before:{int(end_date.timestamp())}'
            logger.debug(f"Gmail查询条件: {query}")

            # 获取邮件列表（支持分页）
            all_messages = []
            next_page_token = None

            while True:
                logger.debug("正在从Gmail获取邮件列表...")
                try:
                    results = self.service.users().messages().list(
                        userId='me',
                        q=query,
                        pageToken=next_page_token
                    ).execute(num_retries=3)  # 增加重试机制

                    messages = results.get('messages', [])
                    all_messages.extend(messages)
                    logger.debug(f"当前页获取到 {len(messages)} 封邮件")

                    next_page_token = results.get('nextPageToken')
                    if not next_page_token:
                        break
                except Exception as e:
                    logger.error(f"获取邮件列表失败: {str(e)}")
                    raise

            logger.debug(f"总共获取到 {len(all_messages)} 封邮件")

            if not all_messages:
                logger.info("没有新的邮件需要同步")
                return

            # 同步每封邮件
            success_count = 0
            error_count = 0
            for message in all_messages:
                try:
                    logger.debug(f"开始同步邮件 - ID: {message['id']}")
                    await self._sync_email(user, message['id'])
                    success_count += 1
                    logger.debug(f"邮件同步成功 - ID: {message['id']}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"同步单封邮件失败 - ID: {message['id']}, 错误: {str(e)}")
                    logger.error(f"错误详情: {traceback.format_exc()}")  # 记录完整堆栈

            logger.info(f"同步完成，成功: {success_count}/{len(all_messages)} 封邮件，失败: {error_count} 封")

        except Exception as e:
            logger.error(f"同步邮件失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")  # 记录完整堆栈
            raise

    async def _sync_email(self, user: User, message_id: str):
        """同步单封邮件
        Args:
            user: 用户对象
            message_id: 邮件ID
        """
        try:
            logger.debug(f"开始同步单封邮件 - 用户: {user.email}, 邮件ID: {message_id}")

            # 获取邮件详情
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            logger.debug(f"原始邮件数据: {json.dumps(message, indent=2)}")  # 记录完整响应

            # 解析邮件内容
            headers = message['payload']['headers']
            subject = self._get_header(headers, 'Subject')
            from_email = self._get_header(headers, 'From')
            to_email = self._get_header(headers, 'To')
            date = self._get_header(headers, 'Date')

            # 解析日期加强容错
            try:
                received_at = datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z')
            except ValueError as e:
                logger.warning(f"日期解析失败: {date}, 使用当前时间")
                received_at = datetime.now(pytz.UTC)

            logger.debug(f"解析邮件信息 - 主题: {subject}, 发件人: {from_email}, 收件人: {to_email}, 时间: {received_at}")

            # 获取邮件正文和附件
            body = self._get_email_body(message['payload'])
            html_body = self._get_email_html_body(message['payload'])
            attachments = self._get_email_attachments(message['payload'])

            logger.debug(f"获取邮件内容 - 文本长度: {len(body)}, HTML长度: {len(html_body)}, 附件数量: {len(attachments)}")

            # 检查邮件是否已存在
            existing_email = Email.query.filter_by(
                user_id=user.id,
                message_id=message_id
            ).first()

            if existing_email:
                logger.debug(f"更新现有邮件 - ID: {existing_email.id}")
                # 更新现有邮件
                existing_email.subject = subject
                existing_email.from_email = from_email
                existing_email.to_email = to_email
                existing_email.body = body
                existing_email.html_body = html_body
                existing_email.attachments = attachments
                existing_email.received_at = received_at
                existing_email.updated_at = datetime.now()
            else:
                logger.debug("创建新邮件")
                # 创建新邮件
                new_email = Email(
                    user_id=user.id,
                    message_id=message_id,
                    subject=subject,
                    from_email=from_email,
                    to_email=to_email,
                    body=body,
                    html_body=html_body,
                    attachments=attachments,
                    received_at=received_at
                )
                self.db.session.add(new_email)

            self.db.session.commit()
            logger.info(f"同步邮件成功: {subject}")

        except Exception as e:
            logger.error(f"同步邮件失败: {str(e)}")
            logger.error(f"错误详情: {traceback.format_exc()}")  # 记录完整堆栈
            self.db.session.rollback()
            raise

    def _get_header(self, headers: List[Dict[str, str]], name: str) -> str:
        """获取邮件头信息
        Args:
            headers: 邮件头列表
            name: 头信息名称
        Returns:
            str: 头信息值
        """
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ''

    def _get_email_body(self, payload: Dict[str, Any]) -> str:
        """获取邮件正文
        Args:
            payload: 邮件负载
        Returns:
            str: 邮件正文
        """
        if 'body' in payload and 'data' in payload['body']:
            return payload['body']['data']

        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    return part['body']['data']
                elif 'parts' in part:
                    return self._get_email_body(part)

        return ''

    def _get_email_html_body(self, payload: Dict[str, Any]) -> str:
        """获取HTML格式的邮件正文
        Args:
            payload: 邮件负载
        Returns:
            str: HTML格式的邮件正文
        """
        if 'body' in payload and 'data' in payload['body']:
            return payload['body']['data']

        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/html':
                    return part['body']['data']
                elif 'parts' in part:
                    return self._get_email_html_body(part)

        return ''

    def _get_email_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取邮件附件
        Args:
            payload: 邮件负载
        Returns:
            List[Dict[str, Any]]: 附件列表
        """
        attachments = []

        def process_part(part):
            if 'filename' in part:
                attachment = {
                    'filename': part['filename'],
                    'mime_type': part['mimeType'],
                    'size': part['body'].get('size', 0),
                    'attachment_id': part['body'].get('attachmentId')
                }
                attachments.append(attachment)

            if 'parts' in part:
                for subpart in part['parts']:
                    process_part(subpart)

        process_part(payload)
        return attachments
