"""
邮件处理器测试
"""
import pytest
from datetime import datetime, UTC
from backend.app.models import Email
from backend.app.service.email.processors.base import EmailProcessor
from backend.app.service.email.processors.preprocessor import EmailPreprocessor
from backend.app.service.email.processors.analyzer import EmailAnalyzer

@pytest.fixture
def sample_email(test_user):
    """创建测试邮件样本"""
    return Email(
        user_id=test_user.id,
        uid="test123",
        message_id="test123",
        from_header="Sender Name <sender@example.com>",
        to_header="Recipient Name <recipient@example.com>",
        subject="Test Email with HTML Content",
        body="Plain text content",
        html_body="""
        <html>
            <body>
                <h1>Test Email</h1>
                <p>This is a <b>formatted</b> email with some <i>HTML</i> content.</p>
                <div>
                    Some additional content with a <a href="http://example.com">link</a>
                </div>
            </body>
        </html>
        """,
        received_at=datetime.now(UTC),
        raw_headers={
            "From": "Sender Name <sender@example.com>",
            "To": "Recipient Name <recipient@example.com>",
            "Date": "Thu, 1 Jan 2024 10:00:00 +0000",
            "Content-Type": "multipart/alternative"
        },
        size=1000,
        labels=["INBOX", "IMPORTANT"]
    )

@pytest.fixture
def preprocessor():
    """创建预处理器实例"""
    return EmailPreprocessor()

@pytest.fixture
def analyzer():
    """创建分析器实例"""
    return EmailAnalyzer()

def test_preprocessor_clean_html(preprocessor):
    """测试HTML清理功能"""
    html_content = """
    <html>
        <body>
            <h1>Test</h1>
            <p>This is a <b>test</b> paragraph.</p>
            <script>alert('xss')</script>
        </body>
    </html>
    """
    cleaned = preprocessor._clean_html(html_content)
    assert "Test" in cleaned
    assert "test" in cleaned
    assert "<script>" not in cleaned
    assert "<h1>" not in cleaned
    assert "<b>" not in cleaned

def test_preprocessor_extract_text(preprocessor, sample_email):
    """测试文本提取功能"""
    text = preprocessor._extract_text(sample_email)
    assert "Test Email" in text
    assert "formatted email" in text
    assert "HTML" in text
    assert "link" in text
    assert "Plain text content" in text

def test_preprocessor_format_metadata(preprocessor, sample_email):
    """测试元数据格式化功能"""
    metadata = preprocessor._format_metadata(sample_email)
    assert metadata["sender_name"] == "Sender Name"
    assert metadata["sender_email"] == "sender@example.com"
    assert metadata["recipient_name"] == "Recipient Name"
    assert metadata["recipient_email"] == "recipient@example.com"
    assert metadata["subject"] == "Test Email with HTML Content"
    assert "INBOX" in metadata["labels"]
    assert "IMPORTANT" in metadata["labels"]
    assert metadata["size"] == 1000

def test_preprocessor_process(preprocessor, sample_email):
    """测试预处理器完整处理流程"""
    result = preprocessor.process(sample_email)
    assert "metadata" in result
    assert "content" in result
    assert "clean_text" in result
    assert result["metadata"]["sender_email"] == "sender@example.com"
    assert result["content"]["text"] == "Plain text content"
    assert "Test Email" in result["clean_text"]

def test_analyzer_process(analyzer, sample_email):
    """测试分析器处理功能"""
    result = analyzer.process(sample_email)
    assert "summary" in result
    assert "keywords" in result
    assert "sentiment" in result
    assert isinstance(result["keywords"], list)
    assert result["sentiment"] in ["positive", "negative", "neutral"]

def test_analyzer_batch_process(analyzer, sample_email):
    """测试分析器批量处理功能"""
    emails = [sample_email]
    results = analyzer.batch_process(emails)
    assert len(results) == 1
    assert "summary" in results[0]
    assert "keywords" in results[0]
    assert "sentiment" in results[0]

def test_analyzer_empty_content(analyzer, test_user):
    """测试分析器处理空内容"""
    empty_email = Email(
        user_id=test_user.id,
        uid="empty123",
        message_id="empty123",
        from_header="",
        to_header="",
        subject="",
        body="",
        html_body="",
        received_at=datetime.now(UTC)
    )
    result = analyzer.process(empty_email)
    assert result["summary"] == "No content available"
    assert result["keywords"] == []
    assert result["sentiment"] == "neutral"

def test_analyzer_error_handling(analyzer, test_user):
    """测试分析器错误处理"""
    invalid_email = Email(
        user_id=test_user.id,
        uid="invalid123",
        message_id="invalid123",
        from_header="",
        to_header="",
        subject="",
        body=None,
        html_body=None,
        received_at=datetime.now(UTC)
    )
    result = analyzer.process(invalid_email)
    assert result["summary"] == "无法分析邮件内容"
    assert result["keywords"] == []
    assert result["sentiment"] == "neutral"
