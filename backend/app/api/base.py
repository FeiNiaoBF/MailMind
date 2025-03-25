"""
基础API蓝图
"""
from flask import Blueprint, jsonify, current_app
from ..utils.logger import get_logger, debug_print

# Create base blueprint
bp = Blueprint('base', __name__)
logger = get_logger(__name__)

@bp.route('/')
def index():
    """首页端点"""
    logger.info("访问首页")
    return jsonify({
        'message': 'Welcome to MailMind API'
    })


@bp.route('/health')
def health_check():
    """健康检查端点"""
    logger.info('健康检查请求')
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running'
    })


@bp.route('/error-test')
def error_test():
    """测试错误处理"""
    logger.warning('触发测试错误')
    try:
        raise ValueError('测试错误')
    except ValueError as e:
        logger.error(f'捕获到错误: {str(e)}')
        raise

# 在视图函数中使用
@bp.route('/test')
def test():
    value = 123
    debug_print("测试值:", value)
    debug_print("多个值:", value, "字符串", True)
    debug_print("带格式:", f"值={value}")
    debug_print("带关键字参数:", name="test", value=value)
    return jsonify({"message": "success"})


# Error handlers
@bp.app_errorhandler(404)
def not_found_error(error):
    """处理404错误"""
    logger.warning(f'404错误: {error}')
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404


@bp.app_errorhandler(500)
def internal_error(error):
    """处理500错误"""
    logger.error(f'500错误: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'






    }), 500


@bp.app_errorhandler(Exception)
def handle_exception(error):
    """处理所有其他异常"""
    logger.exception(f'未处理的异常: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error)
    }), 500
