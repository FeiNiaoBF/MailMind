# file: database.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

from app.config.timezone import china_tz

db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(china_tz)  # 使用中国时区
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(china_tz),
        onupdate=lambda: datetime.now(china_tz)
    )
