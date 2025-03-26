"""
邮件预处理服务测试
"""
import pytest
from datetime import datetime, UTC
from backend.app.service.email.preprocessor import EmailPreprocessService
from backend.app.db.models import Email

@pytest.fixture
def preprocessor():
    """创建预处理服务实例"""
    return EmailPreprocessService()

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

@pytest.mark.parametrize("test_input,expected", [
    (
        "<p>Hello <b>World</b></p>",
        "Hello World"
    ),
    (
        "<div>Multi<br>line<br>text</div>",
        "Multi\nline\ntext"
    ),
    (
        '<a href="http://example.com">Link</a>',
        "Link"
    ),
    (
        "",  # 空字符串
        ""
    ),
    (
        None,  # None值
        ""
    ),
    (
        "<script>alert('xss')</script>",  # 包含脚本
        "alert('xss')"
    )
])
def test_clean_html(preprocessor, test_input, expected):
    """测试HTML清理功能"""
    result = preprocessor.clean_html(test_input)
    assert result.strip() == expected.strip()

def test_extract_text(preprocessor, sample_email):
    """测试文本提取功能"""
    result = preprocessor.extract_text(sample_email)

    # 验证提取的文本包含关键内容
    assert "Test Email" in result
    assert "formatted email" in result
    assert "HTML" in result
    assert "link" in result
    assert "Plain text content" in result

    # 验证HTML标签已被移除
    assert "<h1>" not in result
    assert "<p>" not in result
    assert "<b>" not in result
    assert "<a href" not in result

def test_format_metadata(preprocessor, sample_email):
    """测试元数据格式化功能"""
    result = preprocessor.format_metadata(sample_email)

    assert result["sender_name"] == "Sender Name"
    assert result["sender_email"] == "sender@example.com"
    assert result["recipient_name"] == "Recipient Name"
    assert result["recipient_email"] == "recipient@example.com"
    assert isinstance(result["received_at"], datetime)
    assert result["subject"] == "Test Email with HTML Content"
    assert "INBOX" in result["labels"]
    assert "IMPORTANT" in result["labels"]
    assert result["size"] == 1000
    assert result["message_id"] == "test123"

@pytest.mark.parametrize("header,expected_name,expected_email", [
    (
        "John Doe <john@example.com>",
        "John Doe",
        "john@example.com"
    ),
    (
        "john@example.com",
        "",
        "john@example.com"
    ),
    (
        "",
        "",
        ""
    ),
    (
        None,
        "",
        ""
    ),
    (
        "Invalid Format",
        "",
        "Invalid Format"
    )
])
def test_parse_email_header(preprocessor, header, expected_name, expected_email):
    """测试邮件头解析功能"""
    name, email = preprocessor._parse_email_header(header)
    assert name == expected_name
    assert email == expected_email

def test_process_email(preprocessor, sample_email):
    """测试完整的邮件处理流程"""
    result = preprocessor.process_email(sample_email)

    # 验证返回结果的结构
    assert "metadata" in result
    assert "content" in result
    assert "clean_text" in result

    # 验证内容
    assert result["content"]["text"] == sample_email.body
    assert result["content"]["html"] == sample_email.html_body
    assert len(result["clean_text"]) > 0

    # 验证元数据
    metadata = result["metadata"]
    assert metadata["sender_name"] == "Sender Name"
    assert metadata["sender_email"] == "sender@example.com"
    assert metadata["subject"] == "Test Email with HTML Content"

def test_process_empty_email(preprocessor, test_user):
    """测试处理空邮件"""
    empty_email = Email(
        user_id=test_user.id,
        uid="empty123",
        message_id="empty123",
        from_header="",
        to_header="",
        subject="",
        body="",
        html_body="",
        received_at=datetime.now(UTC),
        raw_headers={},
        size=0,
        labels=[]
    )

    result = preprocessor.process_email(empty_email)

    assert result["metadata"]["sender_name"] == ""
    assert result["metadata"]["sender_email"] == ""
    assert result["metadata"]["recipient_name"] == ""
    assert result["metadata"]["recipient_email"] == ""
    assert result["metadata"]["subject"] == ""
    assert result["content"]["text"] == ""
    assert result["content"]["html"] == ""
    assert result["clean_text"] == ""
