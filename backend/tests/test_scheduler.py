"""
定时任务服务测试模块

测试 SchedulerService 的核心功能，包括:
1. 调度器基础功能
2. 任务管理功能
3. 任务执行功能
4. 并发处理
5. 错误处理
"""
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch, AsyncMock
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.app.service.scheduler_service import SchedulerService
from backend.app.models import User, Email, Analysis
from backend.app.exceptions import SchedulerError
import asyncio

# =============== Fixtures ===============

@pytest.fixture
def scheduler_service():
    """创建调度器服务实例"""
    service = SchedulerService()
    # 使用测试专用的调度器
    service.scheduler = AsyncIOScheduler()
    return service

@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        email="test@example.com",
        oauth_provider="gmail",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def test_emails(db_session, test_user):
    """创建测试邮件数据"""
    emails = []
    for i in range(5):
        email = Email(
            user_id=test_user.id,
            subject=f"Test Subject {i}",
            sender="sender@example.com",
            recipient="recipient@example.com",
            body=f"Test Body {i}",
            date=datetime.now(UTC) - timedelta(days=i),
            is_analyzed=False
        )
        db_session.add(email)
        emails.append(email)
    db_session.commit()
    return emails

# =============== 调度器基础功能测试 ===============

class TestSchedulerBasic:
    """测试调度器基础功能"""

    def test_scheduler_initialization(self, scheduler_service):
        """测试调度器初始化"""
        assert scheduler_service.scheduler is not None
        assert scheduler_service.sync_service is not None
        assert scheduler_service.ai_service is not None
        assert scheduler_service.sender_service is not None
        assert isinstance(scheduler_service.jobs, dict)

    async def test_scheduler_start_stop(self, scheduler_service):
        """测试调度器启动和停止"""
        # 启动调度器
        scheduler_service.start()
        assert scheduler_service.scheduler.running is True

        # 停止调度器
        scheduler_service.stop()
        assert scheduler_service.scheduler.running is False

        # 重复停止应该不会报错
        scheduler_service.stop()
        assert scheduler_service.scheduler.running is False

# =============== 任务管理测试 ===============

class TestJobManagement:
    """测试任务管理功能"""

    async def test_add_sync_job(self, scheduler_service, test_user):
        """测试添加同步任务"""
        # 添加同步任务
        scheduler_service.add_sync_job(test_user, interval_hours=24)

        # 验证任务是否添加
        job_id = f"sync_{test_user.id}"
        assert job_id in scheduler_service.jobs

        # 验证任务是否在调度器中
        job = scheduler_service.scheduler.get_job(scheduler_service.jobs[job_id])
        assert job is not None
        assert job.args[0] == test_user.id

        # 验证重复添加会更新现有任务
        scheduler_service.add_sync_job(test_user, interval_hours=12)
        job = scheduler_service.scheduler.get_job(scheduler_service.jobs[job_id])
        assert job is not None
        assert job.trigger.interval.total_seconds() == 12 * 3600

    async def test_add_analysis_job(self, scheduler_service, test_user):
        """测试添加分析任务"""
        # 添加分析任务
        scheduler_service.add_analysis_job(test_user, cron_expression="0 0 * * *")

        # 验证任务是否添加
        job_id = f"analysis_{test_user.id}"
        assert job_id in scheduler_service.jobs

        # 验证任务是否在调度器中
        job = scheduler_service.scheduler.get_job(scheduler_service.jobs[job_id])
        assert job is not None
        assert job.args[0] == test_user.id

    async def test_add_cleanup_job(self, scheduler_service, test_user):
        """测试添加清理任务"""
        # 添加清理任务
        scheduler_service.add_cleanup_job(test_user, days=30)

        # 验证任务是否添加
        job_id = f"cleanup_{test_user.id}"
        assert job_id in scheduler_service.jobs

        # 验证任务是否在调度器中
        job = scheduler_service.scheduler.get_job(scheduler_service.jobs[job_id])
        assert job is not None
        assert job.args[0] == test_user.id
        assert job.args[1] == 30

    async def test_remove_job(self, scheduler_service, test_user):
        """测试移除任务"""
        # 添加任务
        scheduler_service.add_sync_job(test_user)
        job_id = f"sync_{test_user.id}"

        # 验证任务已添加
        assert job_id in scheduler_service.jobs

        # 移除任务
        scheduler_service.remove_job(job_id)

        # 验证任务已移除
        assert job_id not in scheduler_service.jobs
        assert scheduler_service.scheduler.get_job(scheduler_service.jobs.get(job_id)) is None

        # 移除不存在的任务应该不会报错
        scheduler_service.remove_job("non_existent_job")

# =============== 任务执行测试 ===============

class TestJobExecution:
    """测试任务执行功能"""

    @patch('backend.app.service.scheduler_service.SyncService')
    async def test_sync_emails_success(self, mock_sync_service, scheduler_service, test_user):
        """测试同步邮件成功"""
        # 模拟同步服务
        mock_sync = AsyncMock()
        mock_sync.sync_emails.return_value = [Mock() for _ in range(3)]
        scheduler_service.sync_service = mock_sync

        # 执行同步
        await scheduler_service._sync_emails(test_user.id)

        # 验证调用
        mock_sync.sync_emails.assert_called_once_with(test_user, days=7)

    @patch('backend.app.service.scheduler_service.SyncService')
    async def test_sync_emails_failure(self, mock_sync_service, scheduler_service, test_user):
        """测试同步邮件失败"""
        # 模拟同步服务抛出异常
        mock_sync = AsyncMock()
        mock_sync.sync_emails.side_effect = Exception("Sync failed")
        scheduler_service.sync_service = mock_sync

        # 验证异常处理
        with pytest.raises(SchedulerError) as exc_info:
            await scheduler_service._sync_emails(test_user.id)
        assert "Failed to sync emails" in str(exc_info.value)

    @patch('backend.app.service.scheduler_service.AIService')
    async def test_analyze_emails_success(self, mock_ai_service, scheduler_service, test_user, test_emails):
        """测试分析邮件成功"""
        # 模拟 AI 服务
        mock_ai = AsyncMock()
        mock_ai.batch_analyze.return_value = [{'summary': f'Summary {i}'} for i in range(3)]
        scheduler_service.ai_service = mock_ai

        # 执行分析
        await scheduler_service._analyze_emails(test_user.id)

        # 验证调用
        mock_ai.batch_analyze.assert_called_once()

    @patch('backend.app.service.scheduler_service.AIService')
    async def test_analyze_emails_failure(self, mock_ai_service, scheduler_service, test_user):
        """测试分析邮件失败"""
        # 模拟 AI 服务抛出异常
        mock_ai = AsyncMock()
        mock_ai.batch_analyze.side_effect = Exception("Analysis failed")
        scheduler_service.ai_service = mock_ai

        # 验证异常处理
        with pytest.raises(SchedulerError) as exc_info:
            await scheduler_service._analyze_emails(test_user.id)
        assert "Failed to analyze emails" in str(exc_info.value)

    async def test_cleanup_emails_success(self, scheduler_service, test_user, test_emails):
        """测试清理邮件成功"""
        # 执行清理
        await scheduler_service._cleanup_emails(test_user.id, days=2)

        # 验证结果
        remaining_emails = Email.query.filter_by(user_id=test_user.id).all()
        assert len(remaining_emails) <= 2  # 只保留最近2天的邮件

    async def test_cleanup_emails_failure(self, scheduler_service, test_user):
        """测试清理邮件失败"""
        # 模拟数据库操作失败
        with patch('backend.app.models.Email.query.filter_by') as mock_query:
            mock_query.side_effect = Exception("Database error")

            # 验证异常处理
            with pytest.raises(SchedulerError) as exc_info:
                await scheduler_service._cleanup_emails(test_user.id, days=2)
            assert "Failed to cleanup emails" in str(exc_info.value)

# =============== 并发测试 ===============

class TestConcurrency:
    """测试并发情况"""

    async def test_concurrent_job_execution(self, scheduler_service, test_user):
        """测试并发任务执行"""
        # 添加多个任务
        scheduler_service.add_sync_job(test_user)
        scheduler_service.add_analysis_job(test_user)
        scheduler_service.add_cleanup_job(test_user)

        # 模拟任务执行
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync, \
             patch('backend.app.service.scheduler_service.SchedulerService._analyze_emails') as mock_analyze, \
             patch('backend.app.service.scheduler_service.SchedulerService._cleanup_emails') as mock_cleanup:

            # 启动调度器
            scheduler_service.start()

            # 等待一段时间让任务执行
            await asyncio.sleep(1)

            # 验证任务是否都被执行
            assert mock_sync.called
            assert mock_analyze.called
            assert mock_cleanup.called

    async def test_job_cancellation(self, scheduler_service, test_user):
        """测试任务取消"""
        # 添加任务
        scheduler_service.add_sync_job(test_user)
        job_id = f"sync_{test_user.id}"

        # 启动调度器
        scheduler_service.start()

        # 取消任务
        scheduler_service.remove_job(job_id)

        # 等待一段时间
        await asyncio.sleep(1)

        # 验证任务已被取消
        assert job_id not in scheduler_service.jobs
        assert scheduler_service.scheduler.get_job(scheduler_service.jobs.get(job_id)) is None

# =============== 错误处理测试 ===============

class TestErrorHandling:
    """测试错误处理"""

    async def test_invalid_cron_expression(self, scheduler_service, test_user):
        """测试无效的 cron 表达式"""
        with pytest.raises(ValueError):
            scheduler_service.add_analysis_job(test_user, cron_expression="invalid")

    async def test_invalid_interval(self, scheduler_service, test_user):
        """测试无效的时间间隔"""
        with pytest.raises(ValueError):
            scheduler_service.add_sync_job(test_user, interval_hours=-1)

    async def test_invalid_cleanup_days(self, scheduler_service, test_user):
        """测试无效的清理天数"""
        with pytest.raises(ValueError):
            scheduler_service.add_cleanup_job(test_user, days=-1)

    async def test_duplicate_job_handling(self, scheduler_service, test_user):
        """测试重复任务处理"""
        # 添加同步任务
        scheduler_service.add_sync_job(test_user)

        # 验证重复添加不会报错，而是更新现有任务
        scheduler_service.add_sync_job(test_user, interval_hours=12)
        job_id = f"sync_{test_user.id}"
        job = scheduler_service.scheduler.get_job(scheduler_service.jobs[job_id])
        assert job is not None
        assert job.trigger.interval.total_seconds() == 12 * 3600

# =============== 任务监控测试 ===============

class TestTaskMonitoring:
    """测试任务执行监控功能"""

    async def test_task_execution_time(self, scheduler_service, test_user):
        """测试任务执行时间统计"""
        # 添加同步任务
        scheduler_service.add_sync_job(test_user)

        # 模拟任务执行
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync:
            start_time = datetime.now(UTC)
            mock_sync.side_effect = lambda *args: asyncio.sleep(0.1)  # 模拟耗时操作

            # 执行任务
            await scheduler_service._sync_emails(test_user.id)

            # 验证执行时间记录
            execution_time = datetime.now(UTC) - start_time
            assert execution_time.total_seconds() >= 0.1

    async def test_task_execution_count(self, scheduler_service, test_user):
        """测试任务执行次数统计"""
        # 添加同步任务
        scheduler_service.add_sync_job(test_user)

        # 模拟多次执行
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync:
            for _ in range(3):
                await scheduler_service._sync_emails(test_user.id)

            # 验证执行次数
            assert mock_sync.call_count == 3

    async def test_task_status_recording(self, scheduler_service, test_user):
        """测试任务状态记录"""
        # 添加同步任务
        scheduler_service.add_sync_job(test_user)

        # 模拟任务执行
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync:
            mock_sync.side_effect = Exception("Task failed")

            # 执行任务并验证状态记录
            with pytest.raises(SchedulerError):
                await scheduler_service._sync_emails(test_user.id)

            # 验证任务状态
            job_id = f"sync_{test_user.id}"
            assert scheduler_service.get_job_status(job_id) == "failed"

# =============== 任务优先级测试 ===============

class TestTaskPriority:
    """测试任务优先级功能"""

    async def test_high_priority_execution(self, scheduler_service, test_user):
        """测试高优先级任务优先执行"""
        # 添加不同优先级的任务
        scheduler_service.add_sync_job(test_user, priority=1)
        scheduler_service.add_analysis_job(test_user, priority=2)

        # 模拟任务执行
        execution_order = []
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync, \
             patch('backend.app.service.scheduler_service.SchedulerService._analyze_emails') as mock_analyze:

            mock_sync.side_effect = lambda *args: execution_order.append("sync")
            mock_analyze.side_effect = lambda *args: execution_order.append("analyze")

            # 启动调度器
            scheduler_service.start()
            await asyncio.sleep(0.1)

            # 验证执行顺序
            assert execution_order[0] == "analyze"  # 高优先级任务先执行

    async def test_priority_dynamic_adjustment(self, scheduler_service, test_user):
        """测试任务优先级动态调整"""
        # 添加任务
        scheduler_service.add_sync_job(test_user, priority=1)
        job_id = f"sync_{test_user.id}"

        # 调整优先级
        scheduler_service.adjust_job_priority(job_id, new_priority=2)

        # 验证优先级更新
        job = scheduler_service.scheduler.get_job(scheduler_service.jobs[job_id])
        assert job.priority == 2

# =============== 任务依赖测试 ===============

class TestTaskDependencies:
    """测试任务依赖关系"""

    async def test_dependent_task_execution(self, scheduler_service, test_user):
        """测试依赖任务执行顺序"""
        # 添加依赖任务
        scheduler_service.add_sync_job(test_user)
        scheduler_service.add_analysis_job(test_user, depends_on=f"sync_{test_user.id}")

        # 模拟任务执行
        execution_order = []
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync, \
             patch('backend.app.service.scheduler_service.SchedulerService._analyze_emails') as mock_analyze:

            mock_sync.side_effect = lambda *args: execution_order.append("sync")
            mock_analyze.side_effect = lambda *args: execution_order.append("analyze")

            # 启动调度器
            scheduler_service.start()
            await asyncio.sleep(0.1)

            # 验证执行顺序
            assert execution_order[0] == "sync"
            assert execution_order[1] == "analyze"

    async def test_dependency_failure_handling(self, scheduler_service, test_user):
        """测试依赖任务失败处理"""
        # 添加依赖任务
        scheduler_service.add_sync_job(test_user)
        scheduler_service.add_analysis_job(test_user, depends_on=f"sync_{test_user.id}")

        # 模拟同步任务失败
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync, \
             patch('backend.app.service.scheduler_service.SchedulerService._analyze_emails') as mock_analyze:

            mock_sync.side_effect = Exception("Sync failed")

            # 启动调度器
            scheduler_service.start()
            await asyncio.sleep(0.1)

            # 验证分析任务未执行
            assert not mock_analyze.called

# =============== 资源限制测试 ===============

class TestResourceLimits:
    """测试资源限制功能"""

    async def test_concurrent_task_limit(self, scheduler_service, test_user):
        """测试并发任务数量限制"""
        # 设置并发限制
        scheduler_service.max_concurrent_tasks = 2

        # 添加多个任务
        for i in range(3):
            scheduler_service.add_sync_job(test_user)

        # 模拟任务执行
        active_tasks = 0
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync:
            mock_sync.side_effect = lambda *args: asyncio.sleep(0.1)

            # 启动调度器
            scheduler_service.start()
            await asyncio.sleep(0.1)

            # 验证并发任务数不超过限制
            assert scheduler_service.get_active_task_count() <= 2

    async def test_memory_limit(self, scheduler_service, test_user):
        """测试内存使用限制"""
        # 设置内存限制
        scheduler_service.max_memory_usage = 100 * 1024 * 1024  # 100MB

        # 模拟大内存使用
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync:
            mock_sync.side_effect = lambda *args: [bytearray(200 * 1024 * 1024)]  # 200MB

            # 验证超出内存限制时抛出异常
            with pytest.raises(SchedulerError) as exc_info:
                await scheduler_service._sync_emails(test_user.id)
            assert "Memory limit exceeded" in str(exc_info.value)

# =============== 恢复机制测试 ===============

class TestRecoveryMechanism:
    """测试恢复机制"""

    async def test_service_restart_recovery(self, scheduler_service, test_user):
        """测试服务重启后任务恢复"""
        # 添加任务
        scheduler_service.add_sync_job(test_user)
        scheduler_service.add_analysis_job(test_user)

        # 模拟服务重启
        scheduler_service.stop()
        scheduler_service.start()

        # 验证任务是否恢复
        assert f"sync_{test_user.id}" in scheduler_service.jobs
        assert f"analysis_{test_user.id}" in scheduler_service.jobs

    async def test_task_interruption_recovery(self, scheduler_service, test_user):
        """测试任务执行中断恢复"""
        # 添加同步任务
        scheduler_service.add_sync_job(test_user)

        # 模拟任务中断
        with patch('backend.app.service.scheduler_service.SchedulerService._sync_emails') as mock_sync:
            mock_sync.side_effect = lambda *args: asyncio.sleep(0.1)

            # 启动任务
            task = asyncio.create_task(scheduler_service._sync_emails(test_user.id))

            # 中断任务
            await asyncio.sleep(0.05)
            task.cancel()

            # 验证任务状态
            job_id = f"sync_{test_user.id}"
            assert scheduler_service.get_job_status(job_id) == "interrupted"

            # 恢复任务
            await scheduler_service.recover_interrupted_task(job_id)
            assert scheduler_service.get_job_status(job_id) == "pending"

    async def test_database_connection_recovery(self, scheduler_service, test_user):
        """测试数据库连接中断恢复"""
        # 模拟数据库连接中断
        with patch('backend.app.models.Email.query.filter_by') as mock_query:
            mock_query.side_effect = Exception("Database connection lost")

            # 验证异常处理
            with pytest.raises(SchedulerError) as exc_info:
                await scheduler_service._cleanup_emails(test_user.id, days=2)
            assert "Database connection error" in str(exc_info.value)

            # 验证重试机制
            assert scheduler_service.get_connection_retry_count() > 0

def test_run_sync_task_success(mock_test_user, mock_gmail_service, mock_ai_service, db_session):
    """测试同步任务成功"""
    # 准备测试数据
    service = SchedulerService()
    days = 7

    # 执行同步任务
    service.run_sync_task(mock_test_user, days)

    # 验证邮件同步
    emails = Email.query.filter_by(user_id=mock_test_user.id).all()
    assert len(emails) > 0

    # 验证邮件分析
    analyzed_emails = Email.query.filter_by(
        user_id=mock_test_user.id,
        is_analyzed=True
    ).all()
    assert len(analyzed_emails) > 0

def test_run_sync_task_error(mock_test_user, mock_gmail_service, mock_ai_service, db_session):
    """测试同步任务出错"""
    # 准备测试数据
    service = SchedulerService()
    days = 7

    # 模拟Gmail服务错误
    mock_gmail_service.users.return_value.messages.return_value.list.return_value.execute.side_effect = Exception("API Error")

    # 验证异常抛出
    with pytest.raises(SchedulerError):
        service.run_sync_task(mock_test_user, days)

def test_run_cleanup_task_success(mock_test_user, db_session):
    """测试清理任务成功"""
    # 准备测试数据
    service = SchedulerService()
    days = 30

    # 创建测试邮件和分析结果
    old_date = datetime.utcnow() - timedelta(days=days + 1)

    old_email = Email(
        user_id=mock_test_user.id,
        uid="old_uid",
        message_id="old_message_id",
        from_header="old_sender@example.com",
        to_header="old_recipient@example.com",
        subject="Old Subject",
        body="Old Body",
        received_at=old_date,
        created_at=old_date
    )
    db_session.add(old_email)
    db_session.commit()

    old_analysis = Analysis(
        email_id=old_email.id,
        user_id=mock_test_user.id,
        summary="Old Summary",
        keywords=["old"],
        sentiment="neutral",
        model_used="deepseek",
        created_at=old_date
    )
    db_session.add(old_analysis)
    db_session.commit()

    # 执行清理任务
    service.run_cleanup_task(days)

    # 验证清理结果
    assert Email.query.get(old_email.id) is None
    assert Analysis.query.get(old_analysis.id) is None

def test_run_cleanup_task_preserve_recent(mock_test_user, db_session):
    """测试清理任务保留最近数据"""
    # 准备测试数据
    service = SchedulerService()
    days = 30

    # 创建测试邮件和分析结果
    recent_date = datetime.utcnow() - timedelta(days=days - 1)

    recent_email = Email(
        user_id=mock_test_user.id,
        uid="recent_uid",
        message_id="recent_message_id",
        from_header="recent_sender@example.com",
        to_header="recent_recipient@example.com",
        subject="Recent Subject",
        body="Recent Body",
        received_at=recent_date,
        created_at=recent_date
    )
    db_session.add(recent_email)
    db_session.commit()

    recent_analysis = Analysis(
        email_id=recent_email.id,
        user_id=mock_test_user.id,
        summary="Recent Summary",
        keywords=["recent"],
        sentiment="positive",
        model_used="deepseek",
        created_at=recent_date
    )
    db_session.add(recent_analysis)
    db_session.commit()

    # 执行清理任务
    service.run_cleanup_task(days)

    # 验证保留结果
    assert Email.query.get(recent_email.id) is not None
    assert Analysis.query.get(recent_analysis.id) is not None

def test_run_cleanup_task_error(mock_test_user, db_session):
    """测试清理任务出错"""
    # 准备测试数据
    service = SchedulerService()
    days = 30

    # 模拟数据库错误
    with pytest.raises(SchedulerError):
        service.run_cleanup_task(days)
