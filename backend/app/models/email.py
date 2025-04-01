"""
邮件模型
"""
from datetime import datetime
from ..db.database import db, BaseModel

class Email(BaseModel):
    """邮件模型"""
    __tablename__ = 'emails'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message_id = db.Column(db.String(255), unique=True, nullable=True)
    subject = db.Column(db.String(255))
    from_email = db.Column(db.String(255))
    to_email = db.Column(db.String(255))
    body = db.Column(db.Text)
    html_body = db.Column(db.Text)
    received_at = db.Column(db.DateTime, default=datetime.now)
    attachments = db.Column(db.JSON)

    # 关系
    user = db.relationship('User', backref=db.backref('emails', lazy=True))

    def __repr__(self):
        return f'<Email {self.subject}>'

    def to_dict(self):
        """转换为字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            'user_id': self.user_id,
            'message_id': self.message_id,
            'subject': self.subject,
            'from_email': self.from_email,
            'to_email': self.to_email,
            'body': self.body,
            'html_body': self.html_body,
            'received_at': self.received_at.isoformat() if self.received_at else None,
            'attachments': self.attachments
        })
        return base_dict
