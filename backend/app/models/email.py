"""
邮箱模型模块
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.app.db.models import Base

class Email(Base):
    """邮箱模型"""

    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    email_address = Column(String(255), nullable=False)
    provider = Column(String(50), nullable=False)  # gmail, mailtrap等
    access_token = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    user = relationship('User', back_populates='emails')

    def __repr__(self):
        return f'<Email {self.email_address}>'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_address': self.email_address,
            'provider': self.provider,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
