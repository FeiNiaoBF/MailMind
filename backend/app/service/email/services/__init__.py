"""
邮件服务包
"""
from backend.app.models import Email, User
from .base import EmailService
from .sync import EmailSyncService
from .analysis import EmailAnalysisService
from .gmail import GmailEmailService

__all__ = ['EmailService', 'EmailSyncService', 'EmailAnalysisService', 'GmailEmailService']
