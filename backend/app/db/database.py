"""
建立数据库manage
"""
import os
import sqlite3
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

class BaseDB(DeclarativeBase):
    """利用DeclarativeBase来做基类
    目的是为了在数据库表中添加时间戳
    """