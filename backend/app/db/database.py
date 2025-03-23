"""
建立数据库manage
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    # 创建表
    with app.app_context():
        db.create_all()
        db.session.commit()
