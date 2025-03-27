"""
分析结果模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from backend.app.db.database import db, BaseModel

class Analysis(BaseModel):
    """邮件分析结果模型"""
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_uid = db.Column(db.String(255), db.ForeignKey('emails.uid'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False, comment='分析类型(summary/keywords/action_items)')
    result = db.Column(db.JSON, nullable=False, comment='分析结果')
    analyzed_at = db.Column(db.DateTime, nullable=False, comment='分析时间')
    model_used = db.Column(db.String(50), nullable=False, comment='使用的模型')

    def __init__(self, user_id: int, email_uid: str, analysis_type: str,
                 result: dict, model_used: str,
                 analyzed_at: Optional[datetime] = None):
        """初始化分析结果"""
        super().__init__()
        self.user_id = user_id
        self.email_uid = email_uid
        self.analysis_type = analysis_type
        self.result = result
        self.model_used = model_used
        self.analyzed_at = analyzed_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        # 格式化日期时间
        if base_dict['analyzed_at']:
            base_dict['analyzed_at'] = base_dict['analyzed_at'].isoformat()
        return base_dict

    def __repr__(self):
        return f'<Analysis {self.analysis_type} for {self.email_uid}>'
