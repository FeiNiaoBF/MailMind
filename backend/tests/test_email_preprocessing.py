"""
邮件预处理测试
专注于邮件数据的清洗和标准化
"""
import pytest
from datetime import datetime, UTC
from backend.app.models import Email
from backend.app.service.gmail.processors.preprocessor import EmailPreprocessor

@pytest.fixture
def preprocessor():
    """创建预处理器实例"""
    return EmailPreprocessor()

class TestEmailPreprocessing:
    """邮件预处理测试"""

    def test_clean_subject(self, preprocessor):
        """测试邮件主题清理

        验证结果:
            - 移除 Re: 前缀
            - 移除 Fwd: 前缀
            - 清理多余空白字符
        """
        # Arrange
        test_cases = [
            ('Re: Test Subject', 'Test Subject'),
            ('Fwd: Test Subject', 'Test Subject'),
            ('FW: Test Subject', 'Test Subject'),
            ('  Test   Subject  ', 'Test Subject')
        ]

        # Act & Assert
        for input_subject, expected in test_cases:
            result = preprocessor._clean_subject(input_subject)
            assert result == expected

    def test_parse_email_address(self, preprocessor):
        """测试邮件地址解析

        验证结果:
            - 正确解析带名字的地址
            - 正确解析纯邮箱地址
            - 处理空地址
        """
        # Arrange
        test_cases = [
            ('John Doe <john@example.com>', {'name': 'John Doe', 'email': 'john@example.com'}),
            ('john@example.com', {'name': '', 'email': 'john@example.com'}),
            ('', {'name': '', 'email': ''})
        ]

        # Act & Assert
        for input_address, expected in test_cases:
            result = preprocessor._parse_email_address(input_address)
            assert result == expected

    def test_parse_email_addresses(self, preprocessor):
        """测试多个邮件地址解析

        验证结果:
            - 正确解析多个地址
            - 处理空地址列表
        """
        # Arrange
        test_cases = [
            ('John Doe <john@example.com>, Jane Smith <jane@example.com>', [
                {'name': 'John Doe', 'email': 'john@example.com'},
                {'name': 'Jane Smith', 'email': 'jane@example.com'}
            ]),
            ('', [])
        ]

        # Act & Assert
        for input_addresses, expected in test_cases:
            result = preprocessor._parse_email_addresses(input_addresses)
            assert result == expected

    def test_clean_email_body(self, preprocessor):
        """测试邮件正文清理

        验证结果:
            - 移除引用内容
            - 移除签名
            - 清理多余空白字符
        """
        # Arrange
        test_cases = [
            ('> This is a quote\nThis is not a quote', 'This is not a quote'),
            ('Best regards\n--\nJohn Doe', 'Best regards'),
            ('This   is   a   test.\n\n\nAnother   line.', 'This is a test. Another line.')
        ]

        # Act & Assert
        for input_body, expected in test_cases:
            result = preprocessor._clean_email_body(input_body)
            assert result == expected

    def test_clean_html_body(self, preprocessor):
        """测试HTML邮件正文清理

        验证结果:
            - 移除脚本标签
            - 移除样式标签
            - 移除注释
            - 保留文本内容
        """
        # Arrange
        test_cases = [
            ('<p>This is a test.</p><script>alert("test")</script>', 'This is a test.'),
            ('<!-- comment --><p>This is a test.</p>', 'This is a test.'),
            ('<style>body { color: red; }</style><p>This is a test.</p>', 'This is a test.')
        ]

        # Act & Assert
        for input_html, expected in test_cases:
            result = preprocessor._clean_html_body(input_html)
            assert result == expected

    def test_process_attachments(self, preprocessor):
        """测试附件处理

        验证结果:
            - 正确解析附件信息
            - 处理空附件列表
        """
        # Arrange
        test_cases = [
            ([], []),
            ([
                {'name': 'test.txt', 'size': 100, 'type': 'text/plain'},
                {'name': 'test.pdf', 'size': 200, 'type': 'application/pdf'}
            ], [
                {'name': 'test.txt', 'size': 100},
                {'name': 'test.pdf', 'size': 200}
            ])
        ]

        # Act & Assert
        for input_attachments, expected in test_cases:
            result = preprocessor._process_attachments(input_attachments)
            assert result == expected

    def test_preprocess_email(self, preprocessor, mock_test_email):
        """测试完整的邮件预处理流程

        验证结果:
            - 所有字段都被正确处理
            - 清理后的数据格式正确
        """
        # Arrange
        email_data = {
            'message_id': mock_test_email.message_id,
            'subject': mock_test_email.subject,
            'from_header': mock_test_email.from_header,
            'to_header': mock_test_email.to_header,
            'body': mock_test_email.body,
            'html_body': mock_test_email.html_body,
            'attachments': mock_test_email.attachments,
            'labels': mock_test_email.labels,
            'received_at': mock_test_email.received_at,
            'raw_headers': mock_test_email.raw_headers
        }

        # Act
        processed = preprocessor.preprocess_email(email_data)

        # Assert
        # 验证基本字段
        assert processed['message_id'] == mock_test_email.message_id
        assert processed['subject'] == mock_test_email.subject
        assert processed['from_email'] == 'sender@example.com'
        assert processed['from_name'] == ''
        assert processed['to_emails'] == ['recipient@example.com']
        assert processed['to_names'] == ['']
        assert processed['labels'] == mock_test_email.labels

        # 验证清理后的内容
        assert processed['body'] == mock_test_email.body
        assert processed['html_body'] == mock_test_email.html_body

        # 验证附件处理
        assert len(processed['attachments']) == len(mock_test_email.attachments)
        if mock_test_email.attachments:
            assert processed['attachments'][0]['name'] == mock_test_email.attachments[0]['name']
