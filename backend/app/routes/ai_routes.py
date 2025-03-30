"""
AI 对话路由模块
处理与 AI 服务的对话请求
"""
from flask import Blueprint, request, jsonify
from ..service.ai.ai_service import AIServiceFactory
from ..utils.logger import get_logger

logger = get_logger(__name__)
ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/providers', methods=['GET'])
def get_providers():
    """获取可用的 AI 服务提供商列表"""
    try:
        providers = {}
        for provider in AIServiceFactory.PROVIDERS.keys():
            try:
                config = AIServiceFactory.get_service_config(provider)
                providers[provider] = config
            except Exception as e:
                logger.warning(f"获取 {provider} 配置失败: {str(e)}")
                continue

        return jsonify({
            'providers': providers
        })
    except Exception as e:
        logger.error(f"获取服务提供商列表失败: {str(e)}")
        return jsonify({
            'error': f'获取服务提供商列表失败: {str(e)}'
        }), 500

@ai_bp.route('/validate', methods=['POST'])
def validate_api():
    """验证 API 配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400

        provider = data.get('provider')
        api_key = data.get('api_key')
        model = data.get('model')

        if not all([provider, api_key, model]):
            return jsonify({'error': '缺少必要参数：provider、api_key、model'}), 400

        try:
            ai_service = AIServiceFactory.create_service(
                provider=provider,
                api_key=api_key,
                model=model
            )
            return jsonify({
                'valid': True,
                'message': 'API 验证成功'
            })
        except Exception as e:
            logger.error(f"API 验证失败: {str(e)}")
            return jsonify({
                'valid': False,
                'message': f'API 验证失败: {str(e)}'
            }), 400

    except Exception as e:
        logger.error(f"验证请求处理失败: {str(e)}")
        return jsonify({
            'error': f'验证请求处理失败: {str(e)}'
        }), 500

@ai_bp.route('/chat', methods=['POST'])
def chat():
    """处理对话请求"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '消息内容不能为空'}), 400

        message = data['message']
        provider = data.get('provider', 'deepseek')
        model = data.get('model', 'deepseek-chat')
        api_key = data.get('api_key')

        if not api_key:
            return jsonify({'error': 'API key 不能为空'}), 400

        try:
            ai_service = AIServiceFactory.create_service(
                provider=provider,
                api_key=api_key,
                model=model
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 400

        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 1000)
        stream = data.get('stream', False)

        try:
            response = ai_service.chat(
                message=message,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            logger.info(f"使用 {provider} 的 {model} 模型完成对话")
            return jsonify(response)
        except Exception as e:
            logger.error(f"对话请求失败: {str(e)}")
            return jsonify({'error': f'对话请求失败: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"对话请求处理失败: {str(e)}")
        return jsonify({
            'error': f'对话请求处理失败: {str(e)}'
        }), 500

@ai_bp.route('/analyze', methods=['POST'])
def analyze():
    """处理内容分析请求"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': '分析内容不能为空'}), 400

        content = data['content']
        provider = data.get('provider', 'deepseek')
        model = data.get('model', 'deepseek-chat')
        api_key = data.get('api_key')

        if not api_key:
            return jsonify({'error': 'API key 不能为空'}), 400

        try:
            ai_service = AIServiceFactory.create_service(
                provider=provider,
                api_key=api_key,
                model=model
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 400

        temperature = data.get('temperature', 0.7)
        max_tokens = data.get('max_tokens', 2000)

        try:
            response = ai_service.chat(
                message=f"请分析以下内容：\n\n{content}",
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"使用 {provider} 的 {model} 模型完成内容分析")
            return jsonify(response)
        except Exception as e:
            logger.error(f"内容分析请求失败: {str(e)}")
            return jsonify({'error': f'内容分析请求失败: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"内容分析请求处理失败: {str(e)}")
        return jsonify({
            'error': f'内容分析请求处理失败: {str(e)}'
        }), 500
