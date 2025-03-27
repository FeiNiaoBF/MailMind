"""
邮件提供商包
"""
from backend.app.models import Email, User
from .base import EmailProvider
from .gmail import GmailProvider

__all__ = ['EmailProvider', 'GmailProvider']
