"""
调度器服务模块
处理定时任务相关的业务逻辑
"""
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """调度器服务类"""

    def __init__(self):
        """初始化调度器服务"""
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        logger.info("调度器服务初始化成功")

    def create_job(
            self,
            name: str,
            func: Callable,
            trigger: Union[str, Dict[str, Any]],
            args: Optional[List[Any]] = None,
            kwargs: Optional[Dict[str, Any]] = None,
            **options
    ) -> Dict[str, Any]:
        """创建定时任务
        Args:
            name: 任务名称
            func: 要执行的函数
            trigger: 触发器，可以是字符串或字典
            args: 函数的位置参数
            kwargs: 函数的关键字参数
            **options: 其他选项
        Returns:
            Dict[str, Any]: 任务信息
        """
        try:
            # 解析触发器
            if isinstance(trigger, str):
                if trigger.startswith('cron:'):
                    # cron表达式
                    cron_expr = trigger[6:]
                    trigger = CronTrigger.from_crontab(cron_expr)
                elif trigger.startswith('interval:'):
                    # 间隔时间（秒）
                    seconds = int(trigger[9:])
                    trigger = IntervalTrigger(seconds=seconds)
                elif trigger.startswith('date:'):
                    # 具体时间
                    date_str = trigger[5:]
                    trigger = DateTrigger(run_date=datetime.fromisoformat(date_str))
                else:
                    raise ValueError(f"不支持的触发器格式: {trigger}")

            # 创建任务
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                args=args or [],
                kwargs=kwargs or {},
                name=name,
                **options
            )

            logger.info(f"创建{name}定时任务成功")
            return {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
        except Exception as e:
            logger.error(f"创建定时任务失败: {str(e)}")
            raise

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息
        Args:
            job_id: 任务ID
        Returns:
            Optional[Dict[str, Any]]: 任务信息
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
            return None
        except Exception as e:
            logger.error(f"获取任务信息失败: {str(e)}")
            raise

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """获取所有任务
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        try:
            jobs = self.scheduler.get_jobs()
            return [{
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            } for job in jobs]
        except Exception as e:
            logger.error(f"获取任务列表失败: {str(e)}")
            raise

    def remove_job(self, job_id: str) -> bool:
        """删除任务
        Args:
            job_id: 任务ID
        Returns:
            bool: 是否删除成功
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"删除任务成功: {job_id}")
            return True
        except Exception as e:
            logger.error(f"删除任务失败: {str(e)}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """暂停任务
        Args:
            job_id: 任务ID
        Returns:
            bool: 是否暂停成功
        """
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"暂停任务成功: {job_id}")
            return True
        except Exception as e:
            logger.error(f"暂停任务失败: {str(e)}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """恢复任务
        Args:
            job_id: 任务ID
        Returns:
            bool: 是否恢复成功
        """
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"恢复任务成功: {job_id}")
            return True
        except Exception as e:
            logger.error(f"恢复任务失败: {str(e)}")
            return False

    def shutdown(self):
        """关闭调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("调度器已关闭")
        except Exception as e:
            logger.error(f"关闭调度器失败: {str(e)}")
            raise
