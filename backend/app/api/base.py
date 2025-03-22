"""
基础API蓝图
"""
from flask import Blueprint, jsonify
from ..utils.logger import get_logger

# Create base blueprint
bp = Blueprint('base', __name__)
logger = get_logger(__name__)


@bp.route('/')
def index():
    """首页端点"""
    return jsonify({
        'message': 'Welcome to MailMind API'
    })


@bp.route('/health')
def health_check():
    """健康检查端点"""
    logger.info('Health check requested')
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running'
    })


@bp.route('/error-test')
def error_test():
    """Test error handling."""
    logger.warning('Triggering test error')
    raise ValueError('Test error')


# Error handlers
@bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors."""
    logger.warning(f'404 error: {error}')
    return jsonify({
        'error': 'Not Found',
        'message': 'The requested resource was not found'
    }), 404


@bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f'500 error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


@bp.app_errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions."""
    logger.exception(f'Unhandled exception: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(error)
    }), 500
