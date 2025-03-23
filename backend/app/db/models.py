from datetime import datetime, UTC
from sqlalchemy.dialects.sqlite import JSON

from backend.app import db


class BaseDB(db.Model):
    """数据库基类"""
    __abstract__ = True  # 关键声明，告诉SQLAlchemy不要创建这个表
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )


class User(BaseDB):
    """用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, comment='用户邮箱')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)

    # 关联关系
    emails = db.relationship('Email', backref='user', lazy=True)
    tasks = db.relationship('Task', backref='user', lazy=True)


class Email(BaseDB):
    """邮件模型"""
    __tablename__ = 'emails'
    # 索引和约束——用于优化
    __table_args__ = (
        db.UniqueConstraint('user_id', 'uid', name='uq_user_mail_uid'),  # 唯一约束
        db.Index('ix_user_received', 'user_id', 'received_at'),  # 复合索引
        db.Index('ix_message_id', 'message_id')  # 单独索引
    )
    # 主键改为自增ID
    id = db.Column(db.BigInteger, primary_key=True)

    # IMAP UID（与user_id构成唯一约束）
    uid = db.Column(db.BigInteger, nullable=False, comment='IMAP邮箱内的唯一UID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 邮件基础信息
    message_id = db.Column(db.String(500), nullable=False, comment='Message-ID头')
    from_header = db.Column(db.Text, nullable=False, comment='From头完整内容')
    to_header = db.Column(db.Text, nullable=False, comment='To头完整内容')
    subject = db.Column(db.Text, comment='邮件主题')
    body = db.Column(db.Text, comment='邮件正文')
    html_body = db.Column(db.Text, comment='邮件正文')
    received_at = db.Column(db.DateTime(timezone=True), nullable=False, comment='服务器接收时间')

    # 扩展信息
    raw_headers = db.Column(db.JSON, comment='原始头信息JSON存储')
    attachments = db.Column(db.JSON, comment='附件信息列表', default=list)
    labels = db.Column(db.JSON, comment='邮箱标签', default=list)
    size = db.Column(db.Integer, comment='邮件大小（字节）')

    # 同步元数据
    last_sync = db.Column(db.DateTime, comment='最后同步时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='软删除标记')


class Analysis(BaseDB):
    """邮件分析结果模型"""
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    email_uid = db.Column(db.BigInteger, db.ForeignKey('emails.uid'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)  # summary/keywords/action_items
    result = db.Column(JSON, nullable=False)  # 分析结果
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_used = db.Column(db.String(50), nullable=False)


class Task(BaseDB):
    """任务模型
    用于记录任务的执行状态和结果
    """
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mail_uid = db.Column(db.String(255), db.ForeignKey('emails.uid'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # fetch/analyze/send
    task_data = db.Column(JSON, nullable=False)  # 任务参数
    status = db.Column(db.String(50), nullable=False)  # pending/processing/completed/failed
    result = db.Column(JSON)  # 任务结果
    error = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    model_used = db.Column(db.String(50), nullable=False)


class VerificationCode(BaseDB):
    """验证码模型"""
    __tablename__ = 'verification_codes'

    email = db.Column(db.String(255), primary_key=True)
    code = db.Column(db.String(6), nullable=False)
    expire_time = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
