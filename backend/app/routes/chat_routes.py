"""
聊天相关路由
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from ..service.ai.ai_service import AIServiceFactory
from ..utils.logger import get_logger

logger = get_logger(__name__)
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
def chat():
    """聊天页面"""
    return render_template('chat.html')

@chat_bp.route('/api/validate', methods=['POST'])
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

@chat_bp.route('/api/chat', methods=['POST'])
def chat_api():
    """处理聊天请求"""
    try:
        data = request.get_json()
        message = data.get('message')
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek-chat')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 8760))
        role = data.get('role', 'assistant')
        custom_prompt = data.get('custom_prompt')
        stream = data.get('stream', False)

        if not message:
            return jsonify({
                'error': '消息不能为空'
            }), 400

        # 创建服务实例
        service = AIServiceFactory.create_service(
            provider='deepseek',
            api_key=api_key,
            model=model
        )

        # 处理聊天请求
        response = service.chat(
            message=message,
            temperature=temperature,
            max_tokens=max_tokens,
            role=role,
            custom_prompt=custom_prompt,
            stream=stream
        )

        return jsonify(response)

    except Exception as e:
        logger.error(f"聊天请求失败: {str(e)}")
        return jsonify({
            'error': f'聊天请求失败: {str(e)}'
        }), 500

@chat_bp.route('/api/config', methods=['GET'])
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
