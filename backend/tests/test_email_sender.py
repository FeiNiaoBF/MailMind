"""
测试邮件发送服务
专注于定时发送 AI 分析结果报告
"""
import pytest
from unittest.mock import patch
from datetime import datetime, UTC
from app.service.gmail.services import EmailSenderService
from backend.app.config import Config


@pytest.fixture
def sender_service(app):
    """创建邮件发送服务实例"""
    service = EmailSenderService()
    service.init_app(app)
    return service

@pytest.fixture
def mock_analysis_results():
    """创建模拟的分析结果数据"""
    return {
        'summary': {
            'total_emails': 10,
            'analyzed_emails': 8,
            'start_time': datetime(2024, 3, 28, 10, 0, tzinfo=UTC),
            'end_time': datetime(2024, 3, 28, 10, 5, tzinfo=UTC),
            'email_addresses': ['test1@example.com', 'test2@example.com'],
            'analysis_types': ['summary', 'sentiment', 'urgency']
        },
        'details': [
            {
                'email_id': 'msg1',
                'subject': 'Test Email 1',
                'from': 'sender1@example.com',
                'received_at': datetime(2024, 3, 28, 9, 0, tzinfo=UTC),
                'analysis': {
                    'summary': 'This is a test email about project updates.',
                    'sentiment': 'positive',
                    'urgency': 3
                }
            },
            {
                'email_id': 'msg2',
                'subject': 'Test Email 2',
                'from': 'sender2@example.com',
                'received_at': datetime(2024, 3, 28, 9, 30, tzinfo=UTC),
                'analysis': {
                    'summary': 'Meeting minutes and action items.',
                    'sentiment': 'neutral',
                    'urgency': 2
                }
            }
        ]
    }

def test_init_app(sender_service, app):
    """测试初始化Flask应用"""
    sender_service.init_app(app)
    assert sender_service.mail is not None

def test_send_email(sender_service):
    """测试发送普通邮件"""
    with patch('flask_mail.Mail.send') as mock_send:
        # 发送邮件
        success = sender_service.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            body='Test Body'
        )

        # 验证发送结果
        assert success is True
        mock_send.assert_called_once()

        # 验证邮件内容
        msg = mock_send.call_args[0][0]
        assert msg.recipients == ['test@example.com']
        assert msg.subject == 'Test Subject'
        assert msg.body == 'Test Body'
        assert msg.html is None
        assert len(msg.attachments) == 0

def test_send_email_with_html(sender_service):
    """测试发送HTML邮件"""
    with patch('flask_mail.Mail.send') as mock_send:
        # 发送HTML邮件
        success = sender_service.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            body='Test Body',
            html_body='<p>Test Body</p>'
        )

        # 验证发送结果
        assert success is True
        mock_send.assert_called_once()

        # 验证邮件内容
        msg = mock_send.call_args[0][0]
        assert msg.html == '<p>Test Body</p>'

def test_send_email_with_attachments(sender_service):
    """测试发送带附件的邮件"""
    with patch('flask_mail.Mail.send') as mock_send:
        # 准备附件
        attachments = [
            {
                'name': 'test.txt',
                'type': 'text/plain',
                'data': b'Test content'
            }
        ]

        # 发送带附件的邮件
        success = sender_service.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            body='Test Body',
            attachments=attachments
        )

        # 验证发送结果
        assert success is True
        mock_send.assert_called_once()

        # 验证附件
        msg = mock_send.call_args[0][0]
        assert len(msg.attachments) == 1
        assert msg.attachments[0].filename == 'test.txt'
        assert msg.attachments[0].content_type == 'text/plain'


def test_send_email_error(sender_service):
    """测试发送邮件失败的情况"""
    with patch('flask_mail.Mail.send', side_effect=Exception('Send error')):
        # 发送邮件
        success = sender_service.send_email(
            to_email='test@example.com',
            subject='Test Subject',
            body='Test Body'
        )

        # 验证发送失败
        assert success is False

def test_send_batch_emails(sender_service):
    """测试批量发送邮件"""
    with patch('flask_mail.Mail.send') as mock_send:
        # 准备收件人列表
        to_emails = ['test1@example.com', 'test2@example.com']

        # 批量发送邮件
        results = sender_service.send_batch_emails(
            to_emails=to_emails,
            subject='Test Subject',
            body='Test Body'
        )

        # 验证发送结果
        assert len(results) == 2
        assert all(results.values())
        assert mock_send.call_count == 2

        # 验证每个邮件的内容
        calls = mock_send.call_args_list
        for i, call in enumerate(calls):
            msg = call[0][0]
            assert msg.recipients == [to_emails[i]]
            assert msg.subject == 'Test Subject'
            assert msg.body == 'Test Body'

def test_send_batch_emails_with_error(sender_service):
    """测试批量发送邮件时部分失败的情况"""
    with patch('flask_mail.Mail.send', side_effect=[True, Exception('Send error')]):
        # 准备收件人列表
        to_emails = ['test1@example.com', 'test2@example.com']

        # 批量发送邮件
        results = sender_service.send_batch_emails(
            to_emails=to_emails,
            subject='Test Subject',
            body='Test Body'
        )

        # 验证发送结果
        assert len(results) == 2
        assert results['test1@example.com'] is True
        assert results['test2@example.com'] is False

def test_send_scheduled_analysis_report(sender_service, mock_analysis_results):
    """测试定时发送分析报告

    验证结果:
        - 邮件主题包含分析时间范围
        - 邮件内容包含统计信息
        - 邮件内容包含详细分析结果
    """
    with patch('flask_mail.Mail.send') as mock_send:
        # 发送分析报告
        success = sender_service.send_scheduled_analysis_report(
            to_email='user@example.com',
            analysis_results=mock_analysis_results
        )

        # 验证发送结果
        assert success is True
        mock_send.assert_called_once()

        # 验证邮件内容
        msg = mock_send.call_args[0][0]
        assert msg.recipients == ['user@example.com']
        assert 'MailMind AI Analysis Report' in msg.subject
        assert '2024-03-28 10:00' in msg.subject
        assert '2024-03-28 10:05' in msg.subject

        # 验证邮件正文包含统计信息
        body = msg.body
        assert 'Total Emails: 10' in body
        assert 'Analyzed Emails: 8' in body
        assert 'Analysis Duration: 5 minutes' in body
        assert 'Analysis Types: summary, sentiment, urgency' in body

        # 验证邮件正文包含详细分析
        assert 'Test Email 1' in body
        assert 'Test Email 2' in body
        assert 'This is a test email about project updates' in body
        assert 'Meeting minutes and action items' in body

def test_send_scheduled_analysis_report_error(sender_service, mock_analysis_results):
    """测试定时发送分析报告失败的情况

    验证结果:
        - 发送失败时返回 False
        - 错误被正确处理
    """
    with patch('flask_mail.Mail.send', side_effect=Exception('Send error')):
        # 发送分析报告
        success = sender_service.send_scheduled_analysis_report(
            to_email='user@example.com',
            analysis_results=mock_analysis_results
        )

        # 验证发送失败
        assert success is False

def test_send_scheduled_analysis_report_empty_results(sender_service):
    """测试定时发送空分析结果的情况

    验证结果:
        - 处理空结果的情况
        - 发送适当的提示信息
    """
    with patch('flask_mail.Mail.send') as mock_send:
        # 发送空分析结果
        success = sender_service.send_scheduled_analysis_report(
            to_email='user@example.com',
            analysis_results={'summary': {'total_emails': 0}}
        )

        # 验证发送结果
        assert success is True
        mock_send.assert_called_once()

        # 验证邮件内容
        msg = mock_send.call_args[0][0]
        assert 'No emails analyzed' in msg.body
        assert 'Total Emails: 0' in msg.body
