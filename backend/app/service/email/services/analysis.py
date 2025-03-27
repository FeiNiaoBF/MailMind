"""
邮件分析服务
用于：
1. 分析邮件内容
2. 生成分析报告
3. 管理分析结果
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, UTC, timedelta
from flask import current_app
from sqlalchemy.orm import Session
from backend.app.models import User, Email, Analysis
from backend.app.db.database import db
from backend.app.service.email.providers.base import EmailProvider
from backend.app.service.email.processors.analyzer import EmailAnalyzer
from backend.app.utils.logger import get_logger
from backend.app.service.email.services.base import EmailService
from backend.app.service.ai_service import AIService

logger = get_logger(__name__)

class EmailAnalysisService(EmailService):
    """邮件分析服务"""

    def __init__(self, provider: EmailProvider, processor: EmailAnalyzer):
        """初始化邮件分析服务
        :param provider: 邮件服务提供商
        :param processor: 邮件分析器
        """
        super().__init__(provider, processor)
        self.user = None

    def initialize(self, user: User) -> bool:
        """初始化服务
        :param user: 用户对象
        :return: 是否成功
        """
        try:
            self.user = user
            return self.provider.authenticate()
        except Exception as e:
            logger.error(f"Error initializing analysis service: {str(e)}")
            return False

    def sync_emails(self, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Email]:
        """同步邮件
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: 邮件列表
        """
        raise NotImplementedError("Analysis service does not support email syncing")

    def get_email(self, message_id: str) -> Optional[Email]:
        """获取单个邮件
        :param message_id: 邮件ID
        :return: 邮件对象
        """
        raise NotImplementedError("Analysis service does not support getting emails")

    def process_email(self, email: Email) -> Dict[str, Any]:
        """处理邮件
        :param email: 邮件对象
        :return: 处理结果
        """
        try:
            # 处理邮件
            result = self.processor.process(email)

            # 保存分析结果
            self._save_analysis_result(email, result)

            return result
        except Exception as e:
            logger.error(f"Error processing email {email.uid}: {str(e)}")
            return {
                'summary': '无法分析邮件内容',
                'keywords': [],
                'sentiment': 'neutral'
            }

    def process_emails(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 处理结果列表
        """
        try:
            # 处理邮件
            results = self.processor.batch_process(emails)

            # 保存分析结果
            for email, result in zip(emails, results):
                self._save_analysis_result(email, result)

            return results
        except Exception as e:
            logger.error(f"Error batch processing emails: {str(e)}")
            return [{
                'summary': '无法分析邮件内容',
                'keywords': [],
                'sentiment': 'neutral'
            } for _ in emails]

    def mark_as_read(self, message_id: str) -> bool:
        """标记邮件为已读
        :param message_id: 邮件ID
        :return: 是否成功
        """
        raise NotImplementedError("Analysis service does not support marking emails as read")

    def mark_as_unread(self, message_id: str) -> bool:
        """标记邮件为未读
        :param message_id: 邮件ID
        :return: 是否成功
        """
        raise NotImplementedError("Analysis service does not support marking emails as unread")

    def move_to_folder(self, message_id: str, folder: str) -> bool:
        """移动邮件到指定文件夹
        :param message_id: 邮件ID
        :param folder: 目标文件夹
        :return: 是否成功
        """
        raise NotImplementedError("Analysis service does not support moving emails")

    def delete_email(self, message_id: str) -> bool:
        """删除邮件
        :param message_id: 邮件ID
        :return: 是否成功
        """
        raise NotImplementedError("Analysis service does not support deleting emails")

    def _save_analysis_result(self, email: Email, result: Dict[str, Any]) -> None:
        """保存分析结果
        :param email: 邮件对象
        :param result: 分析结果
        """
        try:
            # 检查是否已存在分析结果
            analysis = Analysis.query.filter_by(
                email_uid=email.uid,
                analysis_type='summary'
            ).first()

            if analysis:
                # 更新现有分析结果
                analysis.result = result
                analysis.analyzed_at = datetime.now(UTC)
                analysis.model_used = self.processor.model
            else:
                # 创建新的分析结果
                analysis = Analysis(
                    email_uid=email.uid,
                    analysis_type='summary',
                    result=result,
                    analyzed_at=datetime.now(UTC),
                    model_used=self.processor.model
                )
                db.session.add(analysis)

            # 提交更改
            db.session.commit()
        except Exception as e:
            logger.error(f"Error saving analysis result for email {email.uid}: {str(e)}")
            db.session.rollback()
