"""
聊天模型
"""
from datetime import datetime
from ..db.database import BaseModel, db

class ChatHistory(BaseModel):
    """聊天历史模型"""
    __tablename__ = 'chat_histories'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 关系
    user = db.relationship('User', backref=db.backref('chat_histories', lazy=True))
    email = db.relationship('Email', backref=db.backref('chat_histories', lazy=True))

    def __repr__(self):
        return f'<ChatHistory {self.id}>'

    def to_dict(self):
        """转换为字典格式"""
        base_dict = super().to_dict()
        base_dict.update({
            'user_id': self.user_id,
            'email_id': self.email_id,
            'question': self.question,
            'answer': self.answer
        })
        return base_dict
