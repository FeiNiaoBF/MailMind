"""
邮件预处理器
用于：
1. 清理 HTML 内容
2. 提取纯文本
3. 格式化元数据
"""
from typing import Dict, Any
from bs4 import BeautifulSoup
from backend.app.models import Email
from backend.app.utils.logger import get_logger
from .base import EmailProcessor

logger = get_logger(__name__)

class EmailPreprocessor(EmailProcessor):
    """邮件预处理器"""

    def process(self, email: Email) -> Dict[str, Any]:
        """处理单个邮件
        :param email: 邮件对象
        :return: 处理结果
        """
        try:
            # 清理 HTML 内容
            html_content = self._clean_html(email.html_body) if email.html_body else ''

            # 提取纯文本
            text_content = self._extract_text(html_content) if html_content else email.body

            # 格式化元数据
            metadata = self._format_metadata(email)

            return {
                'email_uid': email.uid,
                'cleaned_html': html_content,
                'text_content': text_content,
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error preprocessing email {email.uid}: {str(e)}")
            return {
                'email_uid': email.uid,
                'error': str(e)
            }

    def batch_process(self, emails: list[Email]) -> list[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 处理结果列表
        """
        return [self.process(email) for email in emails]

    def _clean_html(self, html_content: str) -> str:
        """清理 HTML 内容
        :param html_content: HTML 内容
        :return: 清理后的 HTML
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除脚本和样式标签
            for script in soup(['script', 'style']):
                script.decompose()

            # 移除注释
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                comment.extract()

            # 移除空白行
            for element in soup.find_all(text=True):
                if element.strip():
                    element.string = element.strip()

            return str(soup)
        except Exception as e:
            logger.error(f"Error cleaning HTML: {str(e)}")
            return html_content

    def _extract_text(self, html_content: str) -> str:
        """提取纯文本
        :param html_content: HTML 内容
        :return: 纯文本内容
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ''

    def _format_metadata(self, email: Email) -> Dict[str, Any]:
        """格式化元数据
        :param email: 邮件对象
        :return: 格式化后的元数据
        """
        return {
            'subject': email.subject,
            'from': email.from_header,
            'to': email.to_header,
            'received_at': email.received_at.isoformat(),
            'labels': email.labels,
            'attachments': email.attachments,
            'size': email.size
        }
