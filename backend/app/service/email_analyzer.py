"""
邮件预处理器
用于：
1. 清理 HTML 内容
2. 提取纯文本
3. 格式化元数据
"""
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailPreprocessor:
    """邮件预处理器"""

    def __init__(self):
        """初始化邮件预处理器"""
        super().__init__()

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
    """邮件分析服务"""

    def __init__(self):
        self.db = db

    async def analyze_email(self, email: Email) -> Analysis:
        """分析邮件

        Args:
            email: 邮件对象

        Returns:
            分析结果
        """
        try:
            # 检查是否已分析
            existing_analysis = Analysis.query.filter_by(email_id=email.id).first()
            if existing_analysis:
                return existing_analysis

            # 获取邮件内容
            content = self._prepare_content(email)

            # 调用AI服务进行分析
            result = await self._analyze_with_ai(content)

            # 保存分析结果
            analysis = Analysis(
                email_id=email.id,
                user_id=email.user_id,
                summary=result['summary'],
                keywords=result['keywords'],
                sentiment=result['sentiment'],
                model_used='deepseek'  # 默认使用deepseek模型
            )

            self.db.session.add(analysis)

            # 更新邮件状态
            email.is_analyzed = True
            email.analysis_status = 'completed'
            email.last_analysis = datetime.utcnow()

            # 提交事务
            self.db.session.commit()

            return analysis

        except Exception as e:
            self.db.session.rollback()
            # 更新邮件状态
            email.analysis_status = 'failed'
            email.analysis_error = str(e)
            self.db.session.commit()
            raise AnalysisError(f"Failed to analyze email: {str(e)}")

    def _prepare_content(self, email: Email) -> str:
        """准备邮件内容

        Args:
            email: 邮件对象

        Returns:
            处理后的邮件内容
        """
        # 优先使用纯文本内容
        content = email.body or email.html_body or ''

        # 移除HTML标签
        if email.html_body:
            # TODO: 实现HTML标签移除
            pass

        return content

    async def _analyze_with_ai(self, content: str) -> Dict[str, Any]:
        """使用AI服务分析内容

        Args:
            content: 邮件内容

        Returns:
            分析结果
        """
        # TODO: 实现AI分析逻辑
        return {
            'summary': '邮件摘要',
            'keywords': ['关键词1', '关键词2'],
            'sentiment': 'positive'
        }
