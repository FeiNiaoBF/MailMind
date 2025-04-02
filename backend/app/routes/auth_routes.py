"""
认证路由模块
处理用户认证相关的路由
"""
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, session, jsonify
from ..service.service_manager import ServiceManager
from ..models import User
from ..db.database import db
from ..utils.logger import get_logger
import secrets

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/google/login')
def google_login():
    """Google登录路由"""
    try:
        # 生成并保存state
        state = secrets.token_urlsafe(16)
        session['oauth2_state'] = state
        session.permanent = True

        # 获取认证URL
        auth_service = ServiceManager.get_auth_service()
        auth_url = auth_service.get_auth_url(state)
        logger.info(f"开始Google认证流程 - state: {state}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"启动认证流程失败: {str(e)}")
        return jsonify({'error': '认证失败，请稍后重试', 'details': str(e)}), 500

@auth_bp.route('/google/callback')
def google_callback():
    """Google认证回调路由"""
    try:
        # 验证state
        state = request.args.get('state')
        stored_state = session.get('oauth2_state')

        if not state:
            logger.error("未收到state参数")
            return jsonify({'error': '无效的认证请求：缺少state参数'}), 400

        if not stored_state:
            logger.error("session中未找到state")
            return jsonify({'error': '无效的认证请求：session已过期'}), 400

        if state != stored_state:
            logger.error(f"state不匹配: 收到 {state}, 期望 {stored_state}")
            return jsonify({'error': '无效的认证请求：state不匹配'}), 400

        # 处理回调
        auth_service = ServiceManager.get_auth_service()
        result = auth_service.handle_callback(request.url)
        if not result:
            logger.error("处理回调返回空结果")
            return jsonify({'error': '认证失败：未获取到用户信息'}), 401

        # 获取或创建用户
        user = auth_service.get_or_create_user(result['user'], session['credentials'])
        if not user:
            return jsonify({'error': '保存用户信息失败'}), 500

        # 初始化邮件服务并启动同步
        email_service = ServiceManager.get_email_service()
        if not email_service:
            logger.error("邮件服务初始化失败")
            session['sync_error'] = "邮件服务初始化失败"
        else:
            if not email_service.start_sync(user):
                logger.error(f"启动邮件同步服务失败: {email_service.sync_error}")
                session['sync_error'] = email_service.sync_error
            else:
                logger.info(f"已为用户 {user.email} 启动邮件同步服务")
                session['sync_status'] = email_service.sync_status.value

        # 清理state
        session.pop('oauth2_state', None)

        # 重定向到主页
        logger.info(f"用户 {result['user']['email']} 登录成功")
        return redirect('/')

    except ValueError as e:
        logger.error(f"验证失败: {str(e)}")
        return jsonify({'error': f'验证失败：{str(e)}'}), 400
    except Exception as e:
        logger.error(f"处理回调失败: {str(e)}")
        return jsonify({'error': '认证失败，请稍后重试', 'details': str(e)}), 500

@auth_bp.route('/google/logout')
def google_logout():
    """退出登录"""
    try:
        auth_service = ServiceManager.get_auth_service()
        credentials = session.get('credentials')
        if credentials and credentials.get('token'):
            # 撤销令牌
            if not auth_service.revoke_token(credentials['token']):
                logger.warning("令牌撤销失败，但继续执行登出流程")

            # 停止邮件同步
            if 'user' in session:
                email_service = ServiceManager.get_email_service()
                if email_service:
                    user = auth_service.get_user_by_email(session['user']['email'])
                    if user:
                        if not email_service.stop_sync(user):
                            logger.error(f"停止邮件同步服务失败: {email_service.sync_error}")
                        else:
                            logger.info(f"已停止用户 {user.email} 的邮件同步服务")

        # 清除session
        session.clear()
        logger.info("用户已退出登录")
        return redirect('/')
    except Exception as e:
        logger.error(f"退出登录失败: {str(e)}")
        return jsonify({'error': '退出失败，请稍后重试', 'details': str(e)}), 500

@auth_bp.route('/check_users')
def check_users():
    """检查用户数据（仅用于调试）"""
    try:
        auth_service = ServiceManager.get_auth_service()
        users = auth_service.get_all_users()
        return jsonify({
            'total_users': len(users),
            'users': users
        })
    except Exception as e:
        logger.error(f"检查用户数据失败: {str(e)}")
        return jsonify({'error': str(e)}), 500
