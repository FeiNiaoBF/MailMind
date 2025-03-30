"""
邮件模型模块
"""
from datetime import datetime
from ..db.database import db


class Email(db.Model):
    """邮件模型"""
    __tablename__ = 'emails'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(255), unique=True, nullable=False)
    subject = db.Column(db.String(255))
    sender = db.Column(db.String(255))
    recipient = db.Column(db.String(255))
    body = db.Column(db.Text)
    html_body = db.Column(db.Text)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'message_id': self.message_id,
            'subject': self.subject,
            'sender': self.sender,
            'recipient': self.recipient,
            'body': self.body,
            'html_body': self.html_body,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<Email {self.message_id}>'
