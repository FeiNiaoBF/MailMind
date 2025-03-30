"""
认证路由模块
处理用户认证相关的路由
"""
from flask import Blueprint, request, redirect, url_for, jsonify, current_app
from ..service.auth_service import AuthService, check_google_connection, create_http_client
from ..utils.logger import get_logger

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/network-test')
def network_test():
    """测试与Google服务的连接"""
    try:
        # 测试基本连接
        if check_google_connection():
            # 测试OAuth端点
            with create_http_client(timeout=10.0) as client:
                oauth_test = client.get('https://oauth2.googleapis.com/token')
                cert_test = client.get('https://www.googleapis.com/oauth2/v1/certs')

                return jsonify({
                    'status': 'success',
                    'message': 'Google服务连接正常',
                    'details': {
                        'basic_connection': True,
                        'oauth_endpoint': oauth_test.status_code,
                        'cert_endpoint': cert_test.status_code
                    }
                })
        else:
            return jsonify({
                'status': 'error',
                'message': '无法连接到Google服务',
                'details': {
                    'basic_connection': False
                }
            }), 503
    except Exception as e:
        logger.error(f"网络测试失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'网络测试出错: {str(e)}',
            'details': None
        }), 500

@auth_bp.route('/google/login')
def google_login():
    """Google登录路由"""
    try:
        auth_url = auth_service.get_google_auth_url()
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Google登录失败: {str(e)}")
        return redirect(url_for('views.index', error='认证失败，请稍后重试'))

@auth_bp.route('/google/callback')
def google_callback():
    """Google回调路由"""
    try:
        auth_code = request.args.get('code')
        if not auth_code:
            logger.error("未收到授权码")
            return redirect(url_for('views.index', error='认证失败，请重试'))

        # 添加重试机制
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # 检查授权码是否已过期
                if 'invalid_grant' in str(last_error):
                    logger.error("授权码已过期，需要重新获取")
                    return redirect(url_for('auth.google_login'))

                result = auth_service.handle_google_callback(auth_code)
                if result:
                    # 重定向到前端，携带token
                    frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
                    return redirect(f"{frontend_url}/chat?token={result['access_token']}")
                else:
                    logger.error(f"处理回调失败，第{attempt + 1}次尝试")
                    if attempt == max_retries - 1:
                        return redirect(url_for('views.index', error='认证失败，请重试'))

            except ConnectionError as e:
                last_error = e
                logger.error(f"连接错误，第{attempt + 1}次尝试: {str(e)}")
                if attempt == max_retries - 1:
                    return redirect(url_for('views.index', error='网络连接失败，请检查网络设置'))

            except ValueError as e:
                last_error = e
                logger.error(f"验证错误: {str(e)}")
                if 'invalid_grant' in str(e):
                    # 如果是授权码过期，直接重新开始认证流程
                    logger.info("授权码已过期，重新开始认证流程")
                    return redirect(url_for('auth.google_login'))
                return redirect(url_for('views.index', error=str(e)))

            except Exception as e:
                last_error = e
                logger.error(f"处理回调出错，第{attempt + 1}次尝试: {str(e)}")
                if attempt == max_retries - 1:
                    if 'invalid_grant' in str(e):
                        return redirect(url_for('auth.google_login'))
                    return redirect(url_for('views.index', error='认证失败，请稍后重试'))

    except Exception as e:
        logger.error(f"处理Google回调时出错: {str(e)}")
        if 'invalid_grant' in str(e):
            return redirect(url_for('auth.google_login'))
        return redirect(url_for('views.index', error='认证失败，请稍后重试'))
