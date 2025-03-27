"""
认证相关路由
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from backend.app.models import User
from backend.app.service.email.providers.gmail import GmailProvider
from backend.app.config.config import Config
from backend.app.db.database import db
from backend.app.utils.logger import get_logger

# 创建蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = get_logger(__name__)


@auth_bp.route('/login/gmail', methods=['GET'])
def gmail_login():
    """Gmail登录"""
    try:
        # 创建Gmail提供商实例
        provider = GmailProvider()

        # 获取授权URL
        auth_url = provider.get_authorization_url()

        return jsonify({
            'status': 'success',
            'auth_url': auth_url
        })
    except Exception as e:
        logger.error(f"Gmail登录失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@auth_bp.route('/callback/gmail', methods=['GET'])
def gmail_callback():
    """Gmail回调"""
    try:
        # 获取授权码
        code = request.args.get('code')
        if not code:
            return jsonify({
                'status': 'error',
                'message': '未提供授权码'
            }), 400

        # 创建Gmail提供商实例
        provider = GmailProvider()

        # 获取用户信息
        user_info = provider.get_user_info(code)

        # 查找或创建用户
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                email=user_info['email'],
                name=user_info['name'],
                google_id=user_info['google_id']
            )
            db.session.add(user)
            db.session.commit()

        # 创建访问令牌
        access_token = create_access_token(identity=user.id)

        return jsonify({
            'status': 'success',
            'access_token': access_token,
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"Gmail回调失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    try:
        # 获取用户ID
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': '无效的令牌'
            }), 401

        # 查询用户
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404

        return jsonify(user.to_dict())
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
