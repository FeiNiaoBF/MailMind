"""
邮件服务包
"""
from backend.app.models import Email, User
from .services import (
    EmailService,
    EmailSyncService,
    EmailAnalysisService,
    GmailEmailService
)
from .providers import EmailProvider, GmailProvider
from .processors import EmailProcessor, EmailPreprocessor, EmailAnalyzer

__all__ = [
    'EmailService',
    'EmailSyncService',
    'EmailAnalysisService',
    'GmailEmailService',
    'EmailProvider',
    'GmailProvider',
    'EmailProcessor',
    'EmailPreprocessor',
    'EmailAnalyzer'
]
