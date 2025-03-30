"""
邮件路由模块
处理邮件相关的API路由
"""
from flask import Blueprint, jsonify, request
from ..service.email_service import EmailService
from ..utils.logger import get_logger

logger = get_logger(__name__)
email_bp = Blueprint('email', __name__)

def get_email_service():
    """获取邮件服务实例"""
    return EmailService()

@email_bp.route('/sync', methods=['POST'])
def sync_emails():
    """同步邮件"""
    try:
        email_service = get_email_service()
        result = email_service.sync_emails()
        return jsonify(result)
    except Exception as e:
        logger.error(f"同步邮件失败: {str(e)}")
        return jsonify({'error': '同步邮件失败'}), 500

@email_bp.route('/list', methods=['GET'])
def list_emails():
    """获取邮件列表"""
    try:
        email_service = get_email_service()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        emails = email_service.get_emails(page=page, per_page=per_page)
        return jsonify(emails)
    except Exception as e:
        logger.error(f"获取邮件列表失败: {str(e)}")
        return jsonify({'error': '获取邮件列表失败'}), 500

@email_bp.route('/<int:email_id>', methods=['GET'])
def get_email(email_id):
    """获取邮件详情"""
    try:
        email_service = get_email_service()
        email = email_service.get_email_by_id(email_id)
        if not email:
            return jsonify({'error': '邮件不存在'}), 404
        return jsonify(email)
    except Exception as e:
        logger.error(f"获取邮件详情失败: {str(e)}")
        return jsonify({'error': '获取邮件详情失败'}), 500

@email_bp.route('/<int:email_id>/analyze', methods=['POST'])
def analyze_email(email_id):
    """分析邮件内容"""
    try:
        email_service = get_email_service()
        result = email_service.analyze_email(email_id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"分析邮件失败: {str(e)}")
        return jsonify({'error': '分析邮件失败'}), 500

"""
邮件分析相关路由
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from ..service.ai.ai_service import AIServiceFactory
from ..utils.logger import get_logger
import os

logger = get_logger(__name__)
email_bp = Blueprint('email', __name__)

@email_bp.route('/emails')
def emails():
    """邮件分析页面"""
    return render_template('emails.html')

@email_bp.route('/api/analyze', methods=['POST'])
def analyze_file():
    """分析文件内容"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'error': '未上传文件'
            }), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({
                'error': '文件名不能为空'
            }), 400

        # 检查文件类型
        if not file.filename.endswith(('.eml', '.txt')):
            return jsonify({
                'error': '不支持的文件类型，仅支持 .eml 和 .txt 文件'
            }), 400

        # 读取文件内容
        file_content = file.read().decode('utf-8')

        # 获取请求参数
        data = request.form
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek-reasoner')
        analysis_type = data.get('analysis_type', 'general')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2000))

        if not api_key:
            return jsonify({
                'error': 'API密钥不能为空'
            }), 400

        # 创建服务实例
        service = AIServiceFactory.create_service(
            provider='deepseek',
            api_key=api_key,
            model=model
        )

        # 分析文件内容
        result = service.analyze_file(
            file_content=file_content,
            analysis_type=analysis_type,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return jsonify({
            'analysis': result['analysis'],
            'model': result['model'],
            'timestamp': result['timestamp']
        })

    except Exception as e:
        logger.error(f"文件分析失败: {str(e)}")
        return jsonify({
            'error': f'文件分析失败: {str(e)}'
        }), 500

@email_bp.route('/api/validate', methods=['POST'])
def validate_api():
    """验证 API 配置"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek-reasoner')

        if not api_key:
            return jsonify({
                'valid': False,
                'message': 'API密钥不能为空'
            }), 400

        # 创建服务实例并验证
        service = AIServiceFactory.create_service(
            provider='deepseek',
            api_key=api_key,
            model=model
        )

        result = service.validate_api()
        return jsonify(result)

    except Exception as e:
        logger.error(f"API验证失败: {str(e)}")
        return jsonify({
            'valid': False,
            'message': f'API验证失败: {str(e)}'
        }), 500

@email_bp.route('/api/config', methods=['GET'])
def get_config():
    """获取服务配置"""
    try:
        provider = request.args.get('provider', 'deepseek')
        config = AIServiceFactory.get_service_config(provider)
        return jsonify(config)

    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({
            'error': f'获取配置失败: {str(e)}'
        }), 500
