"""
测试是用验证码的邮箱登录
"""


class TestEmailAuth:
    def test_generate_code_format(self, app, email_auth_service, test_email):
        with app.app_context():
            code = email_auth_service.generate_code(test_email)
        assert isinstance(code, str)
        assert len(code) == 6
        assert code.isdigit()

    def test_generate_code_storage(self, app, auth_service, test_email):
        """测试验证码存储"""
        with app.app_context():
            code = auth_service.generate_code(test_email)

            # 检查数据库中的记录
            verification = VerificationCode.query.filter_by(email=test_email).first()
            assert verification is not None
            assert verification.code == code
            assert verification.email == test_email
            assert verification.is_used == False
            # 验证码应该在10分钟内有效
            assert verification.expire_time > datetime.utcnow()
            assert verification.expire_time < datetime.utcnow() + timedelta(minutes=11)

    def test_generate_code_update_existing(self, app, auth_service, test_email):
        """测试对同一邮箱重复生成验证码"""
        with app.app_context():
            code1 = auth_service.generate_code(test_email)
            code2 = auth_service.generate_code(test_email)

            # 两次生成的验证码应该不同
            assert code1 != code2
            # 数据库中应该只有一条记录
            count = VerificationCode.query.filter_by(email=test_email).count()
            assert count == 1

    def test_verify_code_success(self, app, auth_service, test_email):
        """测试验证码验证成功"""
        with app.app_context():
            code = auth_service.generate_code(test_email)
            result = auth_service.verify_code(test_email, code)

            assert result is True
            # 验证成功后，验证码应该被标记为已使用
            verification = VerificationCode.query.filter_by(email=test_email).first()
            assert verification.is_used == True
            # 验证成功后，应该创建用户记录
            user = User.query.filter_by(email=test_email).first()
            assert user is not None
            assert user.email == test_email
            assert user.is_active == True

    def test_verify_code_expired(self, app, auth_service, test_email):
        """测试过期验证码"""
        with app.app_context():
            code = auth_service.generate_code(test_email)
            # 手动设置验证码过期
            verification = VerificationCode.query.filter_by(email=test_email).first()
            verification.expire_time = datetime.utcnow() - timedelta(minutes=1)
            db.session.commit()

            result = auth_service.verify_code(test_email, code)
            assert result is False

    def test_verify_code_invalid(self, app, auth_service, test_email):
        """测试无效验证码"""
        with app.app_context():
            auth_service.generate_code(test_email)
            result = auth_service.verify_code(test_email, "000000")
            assert result is False

    def test_verify_code_used(self, app, auth_service, test_email):
        """测试已使用的验证码"""
        with app.app_context():
            code = auth_service.generate_code(test_email)
            # 第一次验证
            auth_service.verify_code(test_email, code)
            # 尝试重复使用
            result = auth_service.verify_code(test_email, code)
            assert result is False
