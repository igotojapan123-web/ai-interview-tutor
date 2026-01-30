# tests/test_rate_limiter.py
# Rate Limiter 테스트

import pytest
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rate_limiter import RateLimiter, RateLimitExceeded, rate_limit


class TestRateLimiter:
    """RateLimiter 클래스 테스트"""

    @pytest.fixture
    def limiter(self):
        """새 Rate Limiter 인스턴스"""
        return RateLimiter()

    def test_allow_under_limit(self, limiter, sample_user_id):
        """제한 내 요청 허용 테스트"""
        allowed, info = limiter.check_rate_limit(sample_user_id, "general")
        assert allowed is True
        assert "allowed" in info

    def test_block_over_limit(self, limiter, sample_user_id):
        """제한 초과 차단 테스트"""
        # 100번 요청 (general 한도)
        for _ in range(100):
            limiter.record_request(sample_user_id, "general")

        allowed, info = limiter.check_rate_limit(sample_user_id, "general")
        assert allowed is False
        assert "error" in info

    def test_different_users_independent(self, limiter):
        """사용자별 독립 제한 테스트"""
        user1 = "user1"
        user2 = "user2"

        # user1 제한 초과
        for _ in range(100):
            limiter.record_request(user1, "general")

        # user1 차단됨
        allowed1, _ = limiter.check_rate_limit(user1, "general")
        assert allowed1 is False

        # user2 허용됨
        allowed2, _ = limiter.check_rate_limit(user2, "general")
        assert allowed2 is True

    def test_get_user_stats(self, limiter, sample_user_id):
        """사용자 통계 조회 테스트"""
        limiter.record_request(sample_user_id, "openai")
        limiter.record_request(sample_user_id, "openai")

        stats = limiter.get_user_stats(sample_user_id)
        assert "openai" in stats
        assert stats["openai"]["current"] == 2

    def test_reset_user(self, limiter, sample_user_id):
        """사용자 제한 리셋 테스트"""
        # 요청 기록
        for _ in range(50):
            limiter.record_request(sample_user_id, "general")

        # 리셋
        limiter.reset_user(sample_user_id)

        # 통계 확인
        stats = limiter.get_user_stats(sample_user_id)
        assert len(stats) == 0


class TestRateLimitDecorator:
    """rate_limit 데코레이터 테스트"""

    def test_decorator_allows_request(self, sample_user_id):
        """데코레이터 요청 허용 테스트"""
        @rate_limit("general")
        def test_func(user_id):
            return "success"

        result = test_func(sample_user_id)
        assert result == "success"

    def test_decorator_blocks_excess(self, sample_user_id):
        """데코레이터 초과 차단 테스트"""
        @rate_limit("general", get_user_id=lambda uid: uid)
        def test_func(user_id):
            return "success"

        # 새 limiter로 테스트
        from rate_limiter import rate_limiter
        rate_limiter.reset_user(sample_user_id)

        # 100번 성공 후 차단
        for i in range(100):
            try:
                test_func(sample_user_id)
            except RateLimitExceeded:
                break

        # 101번째 차단됨
        with pytest.raises(RateLimitExceeded):
            test_func(sample_user_id)
