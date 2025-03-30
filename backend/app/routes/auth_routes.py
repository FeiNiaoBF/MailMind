"""
认证路由模块
处理用户认证相关的路由
"""
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, session, jsonify
from ..service.auth_service import AuthService
from ..service.email_sync import EmailSyncService
from ..models import User
from ..db.database import db
from ..utils.logger import get_logger
import secrets

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()
email_sync_service = EmailSyncService()

@auth_bp.route('/google/login')
def google_login():
    """Google登录路由"""
    try:
        # 生成并保存state
        state = secrets.token_urlsafe(16)
        session['oauth2_state'] = state
        session.permanent = True

        # 获取认证URL
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
        result = auth_service.handle_callback(request.url)
        if not result:
            logger.error("处理回调返回空结果")
            return jsonify({'error': '认证失败：未获取到用户信息'}), 401

        # 获取或创建用户
        user = User.query.filter_by(email=result['user']['email']).first()
        if not user:
            user = User(
                email=result['user']['email'],
                provider_id=result['user']['provider_id'],
                auth_provider='google',
                access_token=session['credentials']['token'],
                refresh_token=session['credentials']['refresh_token']
            )
            db.session.add(user)
        else:
            user.access_token = session['credentials']['token']
            user.refresh_token = session['credentials']['refresh_token']
            user.last_login = datetime.now()

        db.session.commit()

        # 启动定时同步任务
        email_sync_service.schedule_sync_for_user(user)
        logger.info(f"已为用户 {user.email} 启动定时同步任务")

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
        credentials = session.get('credentials')
        if credentials and credentials.get('token'):
            # 撤销令牌
            if not auth_service.revoke_token(credentials['token']):
                logger.warning("令牌撤销失败，但继续执行登出流程")

        # 清除session
        session.clear()
        logger.info("用户已退出登录")
        return redirect('/')
    except Exception as e:
        logger.error(f"退出登录失败: {str(e)}")
        return jsonify({'error': '退出失败，请稍后重试', 'details': str(e)}), 500
