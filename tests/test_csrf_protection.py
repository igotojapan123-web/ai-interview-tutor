# tests/test_csrf_protection.py
# CSRF Protection 테스트

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from csrf_protection import CSRFProtection


class TestCSRFProtection:
    """CSRFProtection 클래스 테스트"""

    @pytest.fixture
    def csrf(self):
        """새 CSRF 인스턴스"""
        return CSRFProtection(expiry_minutes=60)

    def test_generate_token(self, csrf, sample_session_id):
        """토큰 생성 테스트"""
        token = csrf.generate_token(sample_session_id)

        assert token is not None
        assert len(token) > 20  # 충분히 긴 토큰

    def test_validate_valid_token(self, csrf, sample_session_id):
        """유효한 토큰 검증 테스트"""
        token = csrf.generate_token(sample_session_id)

        valid, message = csrf.validate_token(sample_session_id, token)

        assert valid is True
        assert message == "OK"

    def test_validate_invalid_token(self, csrf, sample_session_id):
        """무효한 토큰 검증 테스트"""
        csrf.generate_token(sample_session_id)

        valid, message = csrf.validate_token(sample_session_id, "invalid_token")

        assert valid is False
        assert "유효하지 않은 토큰" in message

    def test_token_consumed_after_validation(self, csrf, sample_session_id):
        """토큰 소비 테스트"""
        token = csrf.generate_token(sample_session_id)

        # 첫 검증 - 성공
        valid1, _ = csrf.validate_token(sample_session_id, token)
        assert valid1 is True

        # 두 번째 검증 - 실패 (이미 소비됨)
        valid2, message = csrf.validate_token(sample_session_id, token)
        assert valid2 is False

    def test_token_not_consumed_when_specified(self, csrf, sample_session_id):
        """토큰 비소비 옵션 테스트"""
        token = csrf.generate_token(sample_session_id)

        # consume=False로 검증
        valid1, _ = csrf.validate_token(sample_session_id, token, consume=False)
        assert valid1 is True

        # 재검증 가능
        valid2, _ = csrf.validate_token(sample_session_id, token, consume=False)
        assert valid2 is True

    def test_invalid_session(self, csrf):
        """잘못된 세션 테스트"""
        valid, message = csrf.validate_token("nonexistent_session", "any_token")

        assert valid is False
        assert "세션" in message

    def test_empty_token(self, csrf, sample_session_id):
        """빈 토큰 테스트"""
        csrf.generate_token(sample_session_id)

        valid, message = csrf.validate_token(sample_session_id, "")

        assert valid is False
        assert "토큰이 없습니다" in message

    def test_max_tokens_per_session(self, csrf, sample_session_id):
        """세션당 최대 토큰 수 테스트"""
        # 15개 토큰 생성 (기본 최대 10개)
        tokens = [csrf.generate_token(sample_session_id) for _ in range(15)]

        # 활성 토큰 수 확인
        count = csrf.get_session_token_count(sample_session_id)
        assert count <= 10  # 최대 10개 유지

    def test_cleanup_all(self, csrf):
        """전체 정리 테스트"""
        for i in range(5):
            csrf.generate_token(f"session_{i}")

        # 정리 (만료된 것만)
        cleaned = csrf.cleanup_all()

        # 아직 만료 안됨
        assert cleaned == 0
