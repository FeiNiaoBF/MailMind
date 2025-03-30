"""
邮件存储测试
专注于邮件数据的存储和检索功能
"""
import pytest
from datetime import datetime, UTC
from backend.app.models import Email, Analysis
from backend.app.service.gmail.services import EmailAnalysisService

class TestEmailStorage:
    """邮件存储测试"""

    def test_save_analysis_result(self, mock_email_sync_service, mock_test_email, db_session):
        """测试保存分析结果

        验证结果:
            - 分析结果正确保存
            - 数据库记录完整
        """
        # Arrange
        analysis_type = 'summary'
        result = {
            'summary': 'Test summary',
            'keywords': ['test'],
            'sentiment': 'positive',
            'urgency': 3
        }

        # Act
        analysis = mock_email_sync_service._save_analysis_result(mock_test_email, analysis_type, result)
        db_session.add(analysis)
        db_session.commit()

        # Assert
        assert analysis.email_uid == mock_test_email.uid
        assert analysis.analysis_type == analysis_type
        assert analysis.result == result
        assert analysis.model_used == 'gpt-3.5-turbo'
        assert analysis.analyzed_at is not None

    def test_get_email_analysis(self, mock_email_sync_service, mock_test_email, db_session):
        """测试获取邮件分析结果

        验证结果:
            - 正确获取已保存的分析结果
            - 处理不存在的分析结果
        """
        # Arrange
        analysis_type = 'summary'
        result = {
            'summary': 'Test summary',
            'keywords': ['test'],
            'sentiment': 'positive',
            'urgency': 3
        }

        # 保存分析结果
        analysis = Analysis(
            email_uid=mock_test_email.uid,
            analysis_type=analysis_type,
            result=result,
            analyzed_at=datetime.now(UTC),
            model_used='gpt-3.5-turbo'
        )
        db_session.add(analysis)
        db_session.commit()

        # Act
        saved_analysis = mock_email_sync_service.get_email_analysis(mock_test_email, analysis_type)

        # Assert
        assert saved_analysis is not None
        assert saved_analysis.email_uid == mock_test_email.uid
        assert saved_analysis.analysis_type == analysis_type
        assert saved_analysis.result == result

    def test_get_nonexistent_analysis(self, mock_email_sync_service, mock_test_email):
        """测试获取不存在的分析结果

        验证结果:
            - 返回 None
        """
        # Act
        result = mock_email_sync_service.get_email_analysis(mock_test_email, 'nonexistent')

        # Assert
        assert result is None

    def test_update_analysis_result(self, mock_email_sync_service, mock_test_email, db_session):
        """测试更新分析结果

        验证结果:
            - 更新现有分析结果
            - 保持其他字段不变
        """
        # Arrange
        analysis_type = 'summary'
        initial_result = {
            'summary': 'Initial summary',
            'keywords': ['initial']
        }
        updated_result = {
            'summary': 'Updated summary',
            'keywords': ['updated']
        }

        # 保存初始结果
        analysis = Analysis(
            email_uid=mock_test_email.uid,
            analysis_type=analysis_type,
            result=initial_result,
            analyzed_at=datetime.now(UTC),
            model_used='gpt-3.5-turbo'
        )
        db_session.add(analysis)
        db_session.commit()

        # Act
        updated_analysis = mock_email_sync_service._save_analysis_result(
            mock_test_email,
            analysis_type,
            updated_result
        )
        db_session.add(updated_analysis)
        db_session.commit()

        # Assert
        assert updated_analysis.email_uid == mock_test_email.uid
        assert updated_analysis.analysis_type == analysis_type
        assert updated_analysis.result == updated_result
        assert updated_analysis.model_used == 'gpt-3.5-turbo'
        assert updated_analysis.analyzed_at is not None

    def test_delete_analysis_result(self, mock_email_sync_service, mock_test_email, db_session):
        """测试删除分析结果

        验证结果:
            - 正确删除分析结果
            - 数据库记录被移除
        """
        # Arrange
        analysis_type = 'summary'
        result = {
            'summary': 'Test summary',
            'keywords': ['test']
        }

        # 保存分析结果
        analysis = Analysis(
            email_uid=mock_test_email.uid,
            analysis_type=analysis_type,
            result=result,
            analyzed_at=datetime.now(UTC),
            model_used='gpt-3.5-turbo'
        )
        db_session.add(analysis)
        db_session.commit()

        # Act
        mock_email_sync_service.delete_analysis(mock_test_email, analysis_type)
        db_session.commit()

        # Assert
        deleted_analysis = mock_email_sync_service.get_email_analysis(mock_test_email, analysis_type)
        assert deleted_analysis is None
