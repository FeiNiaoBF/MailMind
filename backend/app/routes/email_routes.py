"""
邮件路由模块
处理邮件相关的API路由
"""
from flask import Blueprint, jsonify, request, session
from ..service.service_manager import ServiceManager
from ..utils.logger import get_logger
from ..db.database import db
from ..models import User, Email
from ..utils.decorators import login_required
import traceback

logger = get_logger(__name__)
email_bp = Blueprint('email', __name__)

@email_bp.route('/sync', methods=['POST'])
@login_required
def sync_emails(user: User):
    """同步邮件"""
    try:
        email_service = ServiceManager.get_email_service()
        if not email_service:
            return jsonify({'error': '邮件服务初始化失败'}), 500

        # 开始同步邮件
        success = email_service.start_sync(user)
        if not success:
            return jsonify({
                'error': '同步失败',
                'details': email_service.sync_error
            }), 500

        return jsonify({
            'message': '同步已启动',
            'status': email_service.sync_status.value
        })

    except ValueError as e:
        logger.error(f"同步邮件失败: {str(e)}")
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        logger.error(f"同步邮件失败: {str(e)}")
        return jsonify({'error': '同步邮件失败'}), 500

@email_bp.route('/list', methods=['GET'])
@login_required
def list_emails(user: User):
    """获取邮件列表"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # 获取邮件服务
        email_service = ServiceManager.get_email_service()
        if not email_service:
            return jsonify({'error': '邮件服务初始化失败'}), 500

        # 获取邮件列表
        result = email_service.get_emails(
            user=user,
            page=page,
            per_page=per_page
        )
        logger.debug(f'获取邮件列表: {len(result)}')
        return jsonify(result)

    except Exception as e:
        logger.error(f"获取邮件列表失败: {str(e)}")
        return jsonify({'error': f'获取邮件列表失败: {str(e)}'}), 500

@email_bp.route('/<email_id>', methods=['GET'])
@login_required
def get_email(user: User, email_id: str):
    """获取单个邮件详情"""
    try:
        # 获取邮件服务
        email_service = ServiceManager.get_email_service()
        if not email_service:
            return jsonify({'error': '邮件服务初始化失败'}), 500

        # 获取邮件详情
        email = email_service.get_email_by_id(user, email_id)
        if not email:
            return jsonify({'error': '邮件不存在'}), 404

        return jsonify(email.to_dict())

    except Exception as e:
        logger.error(f"获取邮件详情失败: {str(e)}")
        return jsonify({'error': f'获取邮件详情失败: {str(e)}'}), 500

@email_bp.route('/<int:email_id>/analyze', methods=['POST'])
@login_required
def analyze_email(email_id: int, user: User):
    """分析邮件内容"""
    try:
        # 获取邮件服务
        email_service = ServiceManager.get_email_service()
        if not email_service:
            return jsonify({'error': '邮件服务初始化失败'}), 500

        # 获取 AI 服务配置
        data = request.get_json() or {}
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek-chat')

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

        # 获取邮件内容并分析
        email = email_service.get_email_by_id(user, email_id)
        if not email:
            return jsonify({'error': '邮件不存在'}), 404

        result = ai_service.analyze_email(email)
        return jsonify(result)

    except Exception as e:
        logger.error(f"分析邮件失败: {str(e)}")
        return jsonify({'error': '分析邮件失败'}), 500

@email_bp.route('/analyze', methods=['POST'])
def analyze_file():
    """分析文件内容"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'error': '文件名不能为空'}), 400

        # 检查文件类型
        if not file.filename.endswith(('.eml', '.txt')):
            return jsonify({'error': '不支持的文件类型，仅支持 .eml 和 .txt 文件'}), 400

        # 读取文件内容
        file_content = file.read().decode('utf-8')

        # 获取请求参数
        data = request.form
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek-chat')
        analysis_type = data.get('analysis_type', 'general')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2000))

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

        # 分析文件内容
        result = ai_service.analyze_file(
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
        return jsonify({'error': f'文件分析失败: {str(e)}'}), 500

@email_bp.route('/validate', methods=['POST'])
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

@email_bp.route('/config', methods=['GET'])
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

@email_bp.route('/send', methods=['POST'])
@login_required
def send_email(user: User):
    """发送邮件"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400

        # 获取邮件服务
        email_service = ServiceManager.get_email_service()
        if not email_service:
            return jsonify({'error': '邮件服务初始化失败'}), 500

        # 发送邮件
        result = email_service.send_email(user, data)
        return jsonify(result)

    except Exception as e:
        logger.error(f"发送邮件失败: {str(e)}")
        return jsonify({'error': f'发送邮件失败: {str(e)}'}), 500

@email_bp.route('/sync/status', methods=['GET'])
@login_required
def get_sync_status(user: User):
    """获取同步状态"""
    try:
        # 获取邮件服务
        email_service = ServiceManager.get_email_service()
        if not email_service:
            return jsonify({'error': '邮件服务初始化失败'}), 500

        # 获取同步状态
        status = email_service.sync_status

        # 获取最后同步时间
        last_email = Email.query.filter_by(user_id=user.id)\
            .order_by(Email.updated_at.desc())\
            .first()
        last_sync = last_email.updated_at if last_email else None

        return jsonify({
            'status': status.value,
            'last_sync': last_sync.isoformat() if last_sync else None
        })

    except Exception as e:
        logger.error(f"获取同步状态失败: {str(e)}")
        return jsonify({'error': f'获取同步状态失败: {str(e)}'}), 500

@email_bp.route('/sync/manual', methods=['POST'])
@login_required
def manual_sync(user: User):
    """手动触发邮件同步"""
    try:
        logger.debug(f"开始手动同步，用户: {user.email}")

        # 获取邮件服务
        email_service = ServiceManager.get_email_service()
        if not email_service:
            logger.error("邮件服务未初始化")
            return jsonify({'error': '邮件服务未初始化'}), 500

        # 检查Gmail服务状态
        if not email_service.service:
            logger.error("Gmail服务未初始化")
            return jsonify({'error': 'Gmail服务未初始化'}), 500

        logger.debug("Gmail服务状态: 已初始化")
        logger.debug(f"当前同步状态: {email_service.sync_status.value}")

        # 执行同步
        success = email_service.manual_sync(user, days=1)
        if not success:
            logger.error(f"同步失败: {email_service.sync_error}")
            return jsonify({'error': email_service.sync_error}), 500

        logger.debug("同步任务已启动")
        return jsonify({
            'status': 'success',
            'message': '同步任务已启动',
            'sync_status': email_service.sync_status.value
        })

    except Exception as e:
        logger.error(f"手动同步失败: {str(e)}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500
