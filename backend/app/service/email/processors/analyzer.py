"""
邮件分析器
用于：
1. 分析邮件内容
2. 提取关键信息
3. 生成分析报告
"""
from typing import Dict, Any, List
from datetime import datetime, UTC
from flask import current_app
from sqlalchemy.orm import Session
from backend.app.models import Email, Analysis
from backend.app.db.database import db
from backend.app.service.email.processors.base import EmailProcessor
from backend.app.service.ai_service import AIService
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailAnalyzer(EmailProcessor):
    """邮件分析器"""

    def __init__(self):
        """初始化邮件分析器"""
        self.ai_service = AIService()
        self.model = self.ai_service.model

    def process(self, email: Email) -> Dict[str, Any]:
        """处理单个邮件
        :param email: 邮件对象
        :return: 分析结果
        """
        try:
            # 获取邮件内容
            content = email.html_body if email.html_body else email.body
            if not content:
                return {
                    'summary': 'No content available',
                    'keywords': [],
                    'sentiment': 'neutral'
                }

            # 使用 AI 服务分析内容
            analysis_result = self.ai_service.analyze_content(content)

            return analysis_result
        except Exception as e:
            logger.error(f"Error analyzing email {email.uid}: {str(e)}")
            return {
                'summary': '无法分析邮件内容',
                'keywords': [],
                'sentiment': 'neutral'
            }

    def batch_process(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 分析结果列表
        """
        try:
            # 准备邮件内容
            contents = [
                email.html_body if email.html_body else email.body
                for email in emails
            ]

            # 使用 AI 服务批量分析
            analysis_results = self.ai_service.analyze_batch(contents)

            return analysis_results
        except Exception as e:
            logger.error(f"Error batch analyzing emails: {str(e)}")
            return [{
                'summary': '无法分析邮件内容',
                'keywords': [],
                'sentiment': 'neutral'
            } for _ in emails]

    def _save_analysis_result(self, email: Email, result: Dict[str, Any]) -> None:
        """保存分析结果
        :param email: 邮件对象
        :param result: 分析结果
        """
        try:
            analysis = Analysis(
                email_uid=email.uid,
                analysis_type='summary',
                result=result,
                analyzed_at=datetime.now(UTC),
                model_used=self.model
            )
            email.analyses.append(analysis)
        except Exception as e:
            logger.error(f"Error saving analysis result for email {email.uid}: {str(e)}")
