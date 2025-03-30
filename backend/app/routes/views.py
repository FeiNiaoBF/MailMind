"""
视图路由模块
"""
from flask import Blueprint, render_template

views = Blueprint('views', __name__)

@views.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@views.route('/chat')
def chat():
    """渲染聊天页面"""
    return render_template('chat.html')

@views.route('/emails')
def emails():
    """渲染邮件分析页面"""
    return render_template('emails.html')
