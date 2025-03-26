"""
邮件预处理服务
用于：
1. 清理HTML内容，提取纯文本
2. 格式化邮件元数据
3. 提取邮件关键信息
"""
from typing import Dict, Any, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import re
from backend.app.db.models import Email
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

class EmailPreprocessService:
    """邮件预处理服务"""

    def clean_html(self, html_content: str) -> str:
        """清理HTML内容，保留纯文本

        Args:
            html_content: HTML格式的文本内容

        Returns:
            清理后的纯文本内容
        """
        if not html_content:
            return ""

        try:
            # 使用BeautifulSoup清理HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # 将<br>和<p>标签转换为换行
            for br in soup.find_all(['br', 'p']):
                br.replace_with('\n' + br.get_text())

            # 获取纯文本，保留换行符
            text = soup.get_text(separator='\n', strip=True)

            # 清理多余的空白字符，但保留换行符
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n', text)

            # 处理脚本标签
            for script in soup.find_all('script'):
                script_text = script.string
                if script_text:
                    text += '\n' + script_text

            return text.strip()
        except Exception as e:
            logger.error(f"清理HTML内容时发生错误: {str(e)}")
            return html_content

    def extract_text(self, email: Email) -> str:
        """提取邮件中的所有文本内容

        Args:
            email: 邮件对象

        Returns:
            提取的文本内容
        """
        try:
            text_parts = []

            # 添加纯文本内容
            if email.body:
                text_parts.append(email.body)

            # 处理HTML内容
            if email.html_body:
                clean_html = self.clean_html(email.html_body)
                if clean_html:
                    text_parts.append(clean_html)

            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"提取邮件文本时发生错误: {str(e)}")
            return ""

    def format_metadata(self, email: Email) -> Dict[str, Any]:
        """格式化邮件元数据

        Args:
            email: 邮件对象

        Returns:
            格式化后的元数据字典
        """
        try:
            # 解析发件人信息
            sender_name, sender_email = self._parse_email_header(email.from_header)

            # 解析收件人信息
            recipient_name, recipient_email = self._parse_email_header(email.to_header)

            return {
                "sender_name": sender_name,
                "sender_email": sender_email,
                "recipient_name": recipient_name,
                "recipient_email": recipient_email,
                "subject": email.subject,
                "received_at": email.received_at,
                "labels": email.labels,
                "size": email.size,
                "message_id": email.message_id
            }
        except Exception as e:
            logger.error(f"格式化邮件元数据时发生错误: {str(e)}")
            return {}

    def _parse_email_header(self, header: str) -> Tuple[str, str]:
        """解析邮件头中的名称和地址

        Args:
            header: 邮件头字符串

        Returns:
            (名称, 邮件地址)元组
        """
        if not header:
            return "", ""

        try:
            # 匹配 "Name <email@domain.com>" 格式
            match = re.match(r'^(.*?)\s*<(.+?)>$', header)
            if match:
                return match.group(1).strip(), match.group(2).strip()

            # 如果没有名称，直接返回邮件地址
            return "", header.strip()
        except Exception as e:
            logger.error(f"解析邮件头时发生错误: {str(e)}")
            return "", header

    def process_email(self, email: Email) -> Dict[str, Any]:
        """处理完整的邮件对象

        Args:
            email: 邮件对象

        Returns:
            处理后的邮件数据字典
        """
        try:
            metadata = self.format_metadata(email)
            clean_text = self.extract_text(email)

            return {
                "metadata": metadata,
                "content": {
                    "text": email.body,
                    "html": email.html_body
                },
                "clean_text": clean_text
            }
        except Exception as e:
            logger.error(f"处理邮件时发生错误: {str(e)}")
            raise
