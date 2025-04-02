# file: database.py
"""
数据库模块
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 创建数据库实例
db = SQLAlchemy()
migrate = Migrate()

class BaseModel(db.Model):
    """基础模型类"""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

def init_db(app):
    """初始化数据库"""
    try:
        # 初始化数据库扩展
        db.init_app(app)
        logger.info('数据库扩展初始化成功')

        # 初始化数据库迁移
        migrate.init_app(app, db)
        logger.info('数据库迁移初始化成功')

        # 在应用上下文中创建表
        with app.app_context():
            # 确保数据库连接可用
            db.engine.connect()
            logger.info('数据库连接成功')

            # 导入所有模型以确保它们被注册
            from ..models import User, Email, ChatHistory
            logger.info('模型导入成功')

            # 创建所有表
            db.create_all()
            logger.info('数据库表创建成功')

        return True
    except Exception as e:
        logger.error(f'数据库初始化失败: {str(e)}')
        return False

def get_db():
    """获取数据库实例"""
    return db
