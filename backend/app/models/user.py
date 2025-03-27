"""
用户模型
"""
from datetime import datetime, UTC
from typing import Optional, Dict, Any
from backend.app.db.database import db, BaseModel

class User(BaseModel):
    """用户模型类"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, comment='用户邮箱')
    name = db.Column(db.String(255), comment='用户名')
    is_active = db.Column(db.Boolean, default=True, comment='用户是否激活')
    last_login = db.Column(db.DateTime, comment='最后登录时间')
    oauth_provider = db.Column(db.String(20), comment='OAuth提供商(gmail/mailtrap)')
    oauth_uid = db.Column(db.String(255), unique=True, comment='第三方唯一ID')
    oauth_token = db.Column(db.JSON, comment='OAuth令牌信息')
    google_id = db.Column(db.String(120), unique=True, nullable=True, comment='Google用户ID')

    # 关联关系
    emails = db.relationship('Email', backref='user', lazy=True)
    tasks = db.relationship('Task', backref='user', lazy=True)

    def __init__(self, email: str, oauth_uid: Optional[str] = None,
                 oauth_token: Optional[dict] = None, oauth_provider: Optional[str] = None,
                 google_id: Optional[str] = None):
        """初始化用户"""
        super().__init__()
        self.email = email
        self.oauth_uid = oauth_uid
        self.oauth_token = oauth_token
        self.oauth_provider = oauth_provider
        self.google_id = google_id
        self.last_login = datetime.now(UTC)

    def update_oauth_token(self, token: dict) -> None:
        """更新OAuth令牌"""
        self.oauth_token = token
        self.last_login = datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        # 格式化日期时间
        if base_dict['last_login']:
            base_dict['last_login'] = base_dict['last_login'].isoformat()
        if base_dict['created_at']:
            base_dict['created_at'] = base_dict['created_at'].isoformat()
        if base_dict['updated_at']:
            base_dict['updated_at'] = base_dict['updated_at'].isoformat()
        return base_dict
