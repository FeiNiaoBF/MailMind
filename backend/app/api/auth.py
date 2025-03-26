"""
认证路由
"""
from flask import Blueprint, request, jsonify, current_app, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from backend.app.service.email.auth import EmailAuthService
from backend.app.db.models import User
from backend.app.db.database import db
from datetime import datetime, UTC

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
email_auth_service = EmailAuthService()

@auth_bp.route('/gmail/url', methods=['GET'])
def get_gmail_auth_url():
    """获取Gmail认证URL"""
    try:
        auth_url, state = email_auth_service.get_auth_url()
        # 保存状态到会话中
        session['oauth_state'] = state
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'state': state
        })
    except Exception as e:
        current_app.logger.error(f"获取Gmail认证URL失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/gmail/callback', methods=['GET'])
def gmail_callback():
    """Gmail认证回调"""
    try:
        # 验证状态
        state = request.args.get('state')
        if not state or state != session.get('oauth_state'):
            return jsonify({
                'success': False,
                'error': '无效的状态参数'
            }), 400

        # 获取授权码
        code = request.args.get('code')
        if not code:
            return jsonify({
                'success': False,
                'error': '未提供授权码'
            }), 400

        # 获取访问令牌
        tokens = email_auth_service.get_tokens(code)

        # 获取用户信息
        user_info = email_auth_service.get_user_info(tokens['access_token'])
        email = user_info['emailAddress']

        # 验证邮箱格式
        if not email_auth_service.validate_email(email):
            return jsonify({
                'success': False,
                'error': '无效的邮箱地址'
            }), 400

        # 查找或创建用户
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                oauth_uid=user_info.get('id'),
                oauth_token=tokens,
                oauth_provider='gmail',
                is_active=True,
                oauth_token_expires_at=datetime.fromisoformat(tokens['expires_at'])
            )
            db.session.add(user)
        else:
            user.oauth_token = tokens
            user.oauth_provider = 'gmail'
            user.is_active = True
            user.last_login = datetime.now(UTC)
            user.oauth_token_expires_at = datetime.fromisoformat(tokens['expires_at'])

        db.session.commit()

        # 生成JWT令牌
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        # 清除会话中的状态
        session.pop('oauth_state', None)

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'oauth_provider': user.oauth_provider,
                'token_expires_at': user.oauth_token_expires_at.isoformat() if user.oauth_token_expires_at else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"Gmail认证回调处理失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """刷新访问令牌"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)

        if not user or not user.oauth_token:
            return jsonify({
                'success': False,
                'error': '用户未找到或未授权'
            }), 401

        # 检查令牌是否过期
        if user.oauth_token_expires_at and user.oauth_token_expires_at.replace(tzinfo=UTC) > datetime.now(UTC):
            return jsonify({
                'success': False,
                'error': '访问令牌尚未过期'
            }), 400

        # 刷新Gmail访问令牌
        new_tokens = email_auth_service.refresh_token(user.oauth_token['refresh_token'])

        # 更新用户令牌
        new_oauth_token = {
            **user.oauth_token,  # 保留原有的 refresh_token 等信息
            'access_token': new_tokens['access_token'],
            'expires_at': new_tokens['expires_at']
        }
        user.update_oauth_token(new_oauth_token)
        user.oauth_token_expires_at = datetime.fromisoformat(new_tokens['expires_at']).replace(tzinfo=UTC)
        user.last_login = datetime.now(UTC)
        db.session.commit()

        # 生成新的JWT令牌
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'success': True,
            'access_token': access_token,
            'token_expires_at': user.oauth_token_expires_at.isoformat()
        })

    except Exception as e:
        current_app.logger.error(f"刷新令牌失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    try:
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': '用户未找到'
            }), 404

        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'oauth_provider': user.oauth_provider,
                'token_expires_at': user.oauth_token_expires_at.isoformat() if user.oauth_token_expires_at else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
        })

    except Exception as e:
        current_app.logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
