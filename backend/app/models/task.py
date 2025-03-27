"""
任务模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from backend.app.db.database import db, BaseModel

class Task(BaseModel):
    """任务模型类"""
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mail_uid = db.Column(db.String(255), db.ForeignKey('emails.uid'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False, comment='任务类型(analyze/sync)')
    task_data = db.Column(db.JSON, nullable=False, comment='任务数据')
    status = db.Column(db.String(20), nullable=False, default='pending', comment='任务状态(pending/running/completed/failed)')
    result = db.Column(db.JSON, comment='任务结果')
    error = db.Column(db.Text, comment='错误信息')
    started_at = db.Column(db.DateTime, comment='开始时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    model_used = db.Column(db.String(50), comment='使用的模型')

    def __init__(self, user_id: int, mail_uid: str, task_type: str,
                 task_data: dict, model_used: Optional[str] = None):
        """初始化任务"""
        super().__init__()
        self.user_id = user_id
        self.mail_uid = mail_uid
        self.task_type = task_type
        self.task_data = task_data
        self.status = 'pending'
        self.model_used = model_used

    def start(self) -> None:
        """开始任务"""
        self.status = 'running'
        self.started_at = datetime.utcnow()

    def complete(self, result: dict) -> None:
        """完成任务"""
        self.status = 'completed'
        self.result = result
        self.completed_at = datetime.now()
    def fail(self, error: str) -> None:
        """任务失败"""
        self.status = 'failed'
        self.error = error
        self.completed_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        # 格式化日期时间
        if base_dict['started_at']:
            base_dict['started_at'] = base_dict['started_at'].isoformat()
        if base_dict['completed_at']:
            base_dict['completed_at'] = base_dict['completed_at'].isoformat()
        return base_dict
