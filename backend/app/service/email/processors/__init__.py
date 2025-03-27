"""
邮件处理器包
"""
from backend.app.models import Email
from .base import EmailProcessor
from .preprocessor import EmailPreprocessor
from .analyzer import EmailAnalyzer

__all__ = ['EmailProcessor', 'EmailPreprocessor', 'EmailAnalyzer']
