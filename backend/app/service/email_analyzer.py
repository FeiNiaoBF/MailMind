"""
邮件预处理器
用于：
1. 清理 HTML 内容
2. 提取纯文本
3. 格式化元数据
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from ..utils.logger import get_logger
from ..models import Email

logger = get_logger(__name__)


class EmailPreprocessor:
    """邮件预处理器"""

    def __init__(self):
        """初始化邮件预处理器"""
        pass

    def process(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个邮件
        :param email: 邮件数据
        :return: 处理结果
        """
        try:
            # 清理文本内容
            text = self._extract_text(email)
            clean_text = self._clean_text(text)

            # 清理 HTML 内容
            html = email.get('html_body', '')
            clean_html = self._clean_html(html) if html else ''

            # 格式化元数据
            metadata = self._extract_metadata(email)

            return {
                'id': email.get('id', ''),
                'subject': metadata['subject'],
                'from': metadata['sender'],
                'to': metadata['recipient'],
                'date': metadata['date'],
                'body': clean_text,
                'html_body': clean_html,
                'labels': metadata['labels']
            }

        except Exception as e:
            logger.error(f"Error preprocessing email: {str(e)}")
            return {}

    def batch_process(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 处理结果列表
        """
        results = []
        for email in emails:
            try:
                result = self.process(email)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error batch preprocessing email: {str(e)}")
                continue
        return results

    def _clean_text(self, text: str) -> str:
        """清理文本内容
        :param text: 原始文本
        :return: 清理后的文本
        """
        if not text:
            return ''

        # 移除多余的空白字符
        text = ' '.join(text.split())

        # 移除引用内容
        lines = text.split('\n')
        clean_lines = [line for line in lines if not line.startswith('>')]
        text = '\n'.join(clean_lines)

        return text

    def _clean_html(self, html: str) -> str:
        """清理 HTML 内容
        :param html: 原始 HTML
        :return: 清理后的 HTML
        """
        if not html:
            return ''

        try:
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(html, 'html.parser')

            # 移除脚本和样式标签
            for script in soup(['script', 'style']):
                script.decompose()

            # 移除注释
            for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
                comment.extract()

            # 获取纯文本内容
            text = soup.get_text()

            # 清理文本
            return self._clean_text(text)

        except Exception as e:
            logger.error(f"Error cleaning HTML: {str(e)}")
            return ''

    def _extract_text(self, email: Dict[str, Any]) -> str:
        """提取纯文本
        :param email: 邮件数据
        :return: 纯文本内容
        """
        try:
            return email.get('body', '')
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return ''

    def _extract_metadata(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """提取元数据
        :param email: 邮件数据
        :return: 提取的元数据
        """
        return {
            'subject': email.get('subject', ''),
            'sender': email.get('from', ''),
            'recipient': email.get('to', ''),
            'date': email.get('received_at', ''),
            'labels': email.get('labels', [])
        }


class EmailAnalyzer:
    """邮件分析器类"""

    def __init__(self):
        """初始化邮件分析器"""
        super().__init__()

    def process(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个邮件
        :param email: 邮件数据
        :return: 分析结果
        """
        pass

    def batch_process(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理邮件
        :param emails: 邮件列表
        :return: 分析结果列表
        """
        results = []
        for email in emails:
            try:
                result = self.process(email)
                results.append(result)
            except Exception as e:
                logger.error(f"Error batch analyzing email: {str(e)}")
                results.append({})
        return results


class EmailAnalysisService:
    """邮件分析服务类"""

    def __init__(self):
        """初始化邮件分析服务"""
        pass

    def analyze_email(self, email: Email) -> Dict[str, Any]:
        """分析邮件内容
        Args:
            email: 邮件对象
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            # TODO: 实现邮件分析逻辑
            return {
                "sentiment": "neutral",
                "keywords": [],
                "categories": [],
                "priority": "normal"
            }
        except Exception as e:
            logger.error(f"分析邮件失败: {str(e)}")
            raise

    def analyze_emails(self, emails: List[Email]) -> List[Dict[str, Any]]:
        """批量分析邮件
        Args:
            emails: 邮件列表
        Returns:
            List[Dict[str, Any]]: 分析结果列表
        """
        try:
            return [self.analyze_email(email) for email in emails]
        except Exception as e:
            logger.error(f"批量分析邮件失败: {str(e)}")
            raise
