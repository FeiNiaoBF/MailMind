"""
用户模型
"""
from datetime import datetime, timedelta
from ..db.database import BaseModel, db


class User(BaseModel):
    """用户模型"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, default=datetime.now)

    # OAuth 字段
    auth_provider = db.Column(db.String(50))  # 认证提供商（例如：google）
    provider_id = db.Column(db.String(255))  # 第三方用户唯一ID
    access_token = db.Column(db.String(512))  # 移除加密存储注释
    refresh_token = db.Column(db.String(512))
    token_expiry = db.Column(db.DateTime)  # token过期时间

    def __init__(self, email: str, **kwargs):
        """初始化用户"""
        self.email = email
        self.last_login = datetime.now()
        # 处理 OAuth 相关字段
        if kwargs.get('auth_provider') == 'google':
            self.auth_provider = 'google'
            self.provider_id = kwargs.get('provider_id')
            # 直接存储不加密
            self.access_token = kwargs.get('access_token')
            self.refresh_token = kwargs.get('refresh_token')
            self.token_expiry = datetime.now() + timedelta(
                seconds=kwargs.get('expires_in', 3600)
            )

    def to_dict(self):
        """转换为字典（移除敏感字段）"""
        base_dict = super().to_dict()
        base_dict.update({
            'email': self.email,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'auth_provider': self.auth_provider
        })
        return base_dict

    def __repr__(self):
        return f'<User {self.email}>'
