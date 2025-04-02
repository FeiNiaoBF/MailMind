"""
装饰器工具模块
"""
from functools import wraps
from flask import session, jsonify
from ..models import User
from ..db.database import db

def login_required(f):
    """用户登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'error': '用户未登录'}), 401

        user = User.query.filter_by(email=session['user']['email']).first()
        if not user:
            return jsonify({'error': '用户不存在'}), 404

        # 将用户对象添加到 kwargs
        kwargs['user'] = user
        return f(*args, **kwargs)
    return decorated_function
