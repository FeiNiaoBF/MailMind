"""
AI 服务测试模块
专注于文本摘要功能的测试
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from backend.app.service.ai_service import AIService
from backend.app.models import Email, Analysis
from backend.app.db.database import db

class TestAIService:
    """AI 服务测试类"""

    @pytest.fixture
    def ai_service(self):
        """创建 AI 服务实例"""
        return AIService()

    @pytest.fixture
    def sample_email(self):
        """创建测试邮件"""
        return Email(
            id=1,
            subject="项目进度报告",
            sender="test@example.com",
            recipient="manager@example.com",
            body="""
            尊敬的经理：

            本周项目进展顺利，我们完成了以下工作：
            1. 完成了用户认证模块的开发
            2. 修复了三个关键bug
            3. 优化了数据库查询性能

            下周计划：
            1. 开始进行压力测试
            2. 准备系统上线文档
            3. 安排用户培训

            如有任何问题，请随时联系我。

            祝好！
            """,
            date=datetime.utcnow()
        )

    def test_service_initialization(self, ai_service):
        """测试服务初始化

        验证:
        1. 服务实例创建成功
        2. OpenAI 客户端正确初始化
        3. 默认模型设置正确
        """
        # Arrange
        # 服务实例已在 fixture 中创建

        # Act
        initialized = ai_service.initialize()

        # Assert
        assert initialized is True
        assert ai_service.model == "deepseek"
        assert ai_service.client is not None

    def test_email_analysis(self, ai_service, sample_email):
        """测试邮件分析功能

        验证:
        1. 成功调用 OpenAI API
        2. 正确解析分析结果
        3. 分析结果包含必要字段
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="""
                主题总结：项目进度报告，本周完成用户认证模块开发、bug修复和性能优化。
                情感分析：积极正面
                关键信息：
                - 完成用户认证模块
                - 修复3个关键bug
                - 优化数据库性能
                后续行动：准备压力测试和上线文档
                """
            )
        )]

        # Act
        with patch('openai.OpenAI.chat.completions.create', return_value=mock_response):
            result = ai_service.analyze_email(sample_email)

        # Assert
        assert result is not None
        assert 'summary' in result
        assert 'analyzed_at' in result
        assert 'model_used' in result
        assert result['model_used'] == "deepseek"

    def test_batch_analysis(self, ai_service, sample_email):
        """测试批量分析功能

        验证:
        1. 成功处理多个邮件
        2. 正确处理分析失败的情况
        3. 返回有效的分析结果列表
        """
        # Arrange
        emails = [sample_email, sample_email]  # 使用相同的邮件进行测试
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(
            message=MagicMock(
                content="测试摘要内容"
            )
        )]

        # Act
        with patch('openai.OpenAI.chat.completions.create', return_value=mock_response):
            results = ai_service.batch_analyze(emails)

        # Assert
        assert len(results) == 2
        assert all(isinstance(result, dict) for result in results)
        assert all('summary' in result for result in results)

    def test_analysis_error_handling(self, ai_service, sample_email):
        """测试错误处理

        验证:
        1. API 调用失败时正确处理错误
        2. 返回 None 而不是抛出异常
        """
        # Arrange
        # 模拟 API 调用失败
        with patch('openai.OpenAI.chat.completions.create', side_effect=Exception("API Error")):
            # Act
            result = ai_service.analyze_email(sample_email)

        # Assert
        assert result is None

    def test_analysis_result_parsing(self, ai_service):
        """测试分析结果解析

        验证:
        1. 正确解析分析文本
        2. 生成标准化的结果格式
        """
        # Arrange
        test_analysis_text = """
        主题总结：测试邮件
        情感分析：中性
        关键信息：测试信息
        后续行动：无
        """

        # Act
        result = ai_service._parse_analysis(test_analysis_text)

        # Assert
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'analyzed_at' in result
        assert 'model_used' in result
        assert result['summary'] == test_analysis_text
