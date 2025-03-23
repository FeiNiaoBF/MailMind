from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Email(db.Model):
    """邮件模型"""
    __tablename__ = 'emails'
    uid = db.Column(db.String(255), primary_key=True)
    from_email = db.Column(db.String(255), nullable=False)
    to_email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(500))
    body = db.Column(db.Text)
    date_created = db.Column(db.DateTime, default=datetime.now)
    attachments = db.Column(JSON)
    labels = db.Column(JSON)

    analyses = db.relationship('Analysis', backref='mail', lazy=True)


class Analysis(db.Model):
    """邮件分析结果模型"""
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    mail_uid = db.Column(db.String(255), db.ForeignKey('mails.uid'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # summary/keywords/action_items
    result = db.Column(JSON, nullable=False)  # 分析结果
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_used = db.Column(db.String(50), nullable=False)


class Task(db.Model):
    """任务模型"""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(255), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # summary/keywords/action_items
    task_data = db.Column(JSON, nullable=False)  # 分析结果
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False)  # pending/processing/completed/failed
    result = db.Column(JSON)
    error = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    model_used = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(255), nullable=False)
    mail_uid = db.Column(db.String(255), db.ForeignKey('mails.uid'), nullable=False)

    mail = db.relationship('Email', backref='tasks', lazy=True)
