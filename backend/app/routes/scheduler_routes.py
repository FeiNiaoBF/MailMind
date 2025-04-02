"""
调度器路由模块
处理定时任务相关的API路由
"""
from flask import Blueprint, jsonify, request
from ..service.scheduler_service import SchedulerService
from ..utils.logger import get_logger

logger = get_logger(__name__)
scheduler_bp = Blueprint('scheduler', __name__)

def get_scheduler_service():
    """获取调度器服务实例"""
    return SchedulerService()

@scheduler_bp.route('/jobs', methods=['GET'])
def list_jobs():
    """获取所有定时任务"""
    try:
        scheduler_service = get_scheduler_service()
        jobs = scheduler_service.get_all_jobs()
        return jsonify(jobs)
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {str(e)}")
        return jsonify({'error': '获取定时任务列表失败'}), 500

@scheduler_bp.route('/jobs', methods=['POST'])
def create_job():
    """创建定时任务"""
    try:
        data = request.get_json()
        scheduler_service = get_scheduler_service()
        job = scheduler_service.create_job(
            name=data.get('name'),
            func=data.get('func'),
            trigger=data.get('trigger'),
            args=data.get('args', []),
            kwargs=data.get('kwargs', {})
        )
        return jsonify(job)
    except Exception as e:
        logger.error(f"创建定时任务失败: {str(e)}")
        return jsonify({'error': '创建定时任务失败'}), 500

@scheduler_bp.route('/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """获取定时任务详情"""
    try:
        scheduler_service = get_scheduler_service()
        job = scheduler_service.get_job(job_id)
        if not job:
            return jsonify({'error': '定时任务不存在'}), 404
        return jsonify(job)
    except Exception as e:
        logger.error(f"获取定时任务详情失败: {str(e)}")
        return jsonify({'error': '获取定时任务详情失败'}), 500

@scheduler_bp.route('/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    """更新定时任务"""
    try:
        data = request.get_json()
        scheduler_service = get_scheduler_service()
        job = scheduler_service.update_job(
            job_id,
            name=data.get('name'),
            func=data.get('func'),
            trigger=data.get('trigger'),
            args=data.get('args', []),
            kwargs=data.get('kwargs', {})
        )
        if not job:
            return jsonify({'error': '定时任务不存在'}), 404
        return jsonify(job)
    except Exception as e:
        logger.error(f"更新定时任务失败: {str(e)}")
        return jsonify({'error': '更新定时任务失败'}), 500

@scheduler_bp.route('/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """删除定时任务"""
    try:
        scheduler_service = get_scheduler_service()
        if scheduler_service.delete_job(job_id):
            return jsonify({'message': '定时任务删除成功'})
        return jsonify({'error': '定时任务不存在'}), 404
    except Exception as e:
        logger.error(f"删除定时任务失败: {str(e)}")
        return jsonify({'error': '删除定时任务失败'}), 500

@scheduler_bp.route('/jobs/<job_id>/pause', methods=['POST'])
def pause_job(job_id):
    """暂停定时任务"""
    try:
        scheduler_service = get_scheduler_service()
        if scheduler_service.pause_job(job_id):
            return jsonify({'message': '定时任务暂停成功'})
        return jsonify({'error': '定时任务不存在'}), 404
    except Exception as e:
        logger.error(f"暂停定时任务失败: {str(e)}")
        return jsonify({'error': '暂停定时任务失败'}), 500

@scheduler_bp.route('/jobs/<job_id>/resume', methods=['POST'])
def resume_job(job_id):
    """恢复定时任务"""
    try:
        scheduler_service = get_scheduler_service()
        if scheduler_service.resume_job(job_id):
            return jsonify({'message': '定时任务恢复成功'})
        return jsonify({'error': '定时任务不存在'}), 404
    except Exception as e:
        logger.error(f"恢复定时任务失败: {str(e)}")
        return jsonify({'error': '恢复定时任务失败'}), 500
