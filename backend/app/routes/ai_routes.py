"""
AI 路由模块
处理 AI 相关的API路由
"""
from flask import Blueprint, jsonify, request
from ..service.service_manager import ServiceManager
from ..utils.logger import get_logger
from ..utils.decorators import login_required
from ..models import User

logger = get_logger(__name__)
ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_text(user: User):
    """分析文本内容"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400

        text = data.get('text')
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek-chat')
        analysis_type = data.get('analysis_type', 'general')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2000))

        if not text:
            return jsonify({'error': '文本内容不能为空'}), 400
        if not api_key:
            return jsonify({'error': 'API密钥不能为空'}), 400

        # 获取 AI 服务
        ai_service = ServiceManager.get_ai_service(
            provider='deepseek',
            api_key=api_key,
            model=model
        )
        if not ai_service:
            return jsonify({'error': 'AI服务初始化失败'}), 500

        # 分析文本
        result = ai_service.analyze_text(
            text=text,
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
        logger.error(f"文本分析失败: {str(e)}")
        return jsonify({'error': f'文本分析失败: {str(e)}'}), 500

@ai_bp.route('/validate', methods=['POST'])
def validate_api():
    """验证 API 配置"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek-chat')

        if not api_key:
            return jsonify({
                'valid': False,
                'message': 'API密钥不能为空'
            }), 400

        # 获取 AI 服务
        ai_service = ServiceManager.get_ai_service(
            provider='deepseek',
            api_key=api_key,
            model=model
        )
        if not ai_service:
            return jsonify({
                'valid': False,
                'message': 'AI服务初始化失败'
            }), 500

        result = ai_service.validate_api()
        return jsonify(result)

    except Exception as e:
        logger.error(f"API验证失败: {str(e)}")
        return jsonify({
            'valid': False,
            'message': f'API验证失败: {str(e)}'
        }), 500

@ai_bp.route('/config', methods=['GET'])
def get_config():
    """获取服务配置"""
    try:
        provider = request.args.get('provider', 'deepseek')
        config = ServiceManager.get_ai_service_config(provider)
        return jsonify(config)

    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({
            'error': f'获取配置失败: {str(e)}'
        }), 500
