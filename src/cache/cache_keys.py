"""
Cache Key Patterns.

Centralized cache key management for consistency and easy invalidation.
"""

from typing import Optional


class CacheKeys:
    """
    Cache key patterns for FlyReady Lab.

    Naming convention: {domain}:{entity}:{identifier}:{attribute}
    """

    # =========================================================================
    # User Cache Keys
    # =========================================================================

    @staticmethod
    def user(user_id: str) -> str:
        """User profile cache key."""
        return f"user:{user_id}"

    @staticmethod
    def user_profile(user_id: str) -> str:
        """User full profile with stats."""
        return f"user:{user_id}:profile"

    @staticmethod
    def user_sessions(user_id: str) -> str:
        """User's active sessions."""
        return f"user:{user_id}:sessions"

    @staticmethod
    def user_progress(user_id: str) -> str:
        """User learning progress."""
        return f"user:{user_id}:progress"

    @staticmethod
    def user_stats(user_id: str) -> str:
        """User statistics."""
        return f"user:{user_id}:stats"

    @staticmethod
    def user_subscription(user_id: str) -> str:
        """User subscription info."""
        return f"user:{user_id}:subscription"

    @staticmethod
    def user_pattern(user_id: str) -> str:
        """Pattern for all user cache keys."""
        return f"user:{user_id}:*"

    # =========================================================================
    # Interview Cache Keys
    # =========================================================================

    @staticmethod
    def interview_session(session_id: str) -> str:
        """Interview session data."""
        return f"interview:session:{session_id}"

    @staticmethod
    def interview_questions(interview_type: str) -> str:
        """Interview questions by type."""
        return f"interview:questions:{interview_type}"

    @staticmethod
    def interview_feedback(session_id: str, question_id: str) -> str:
        """Interview question feedback."""
        return f"interview:feedback:{session_id}:{question_id}"

    @staticmethod
    def interview_history(user_id: str) -> str:
        """User's interview history."""
        return f"interview:history:{user_id}"

    # =========================================================================
    # AI Cache Keys
    # =========================================================================

    @staticmethod
    def ai_response(prompt_hash: str) -> str:
        """Cached AI response."""
        return f"ai:response:{prompt_hash}"

    @staticmethod
    def ai_embedding(text_hash: str) -> str:
        """Cached text embedding."""
        return f"ai:embedding:{text_hash}"

    @staticmethod
    def ai_analysis(content_hash: str) -> str:
        """Cached AI analysis result."""
        return f"ai:analysis:{content_hash}"

    # =========================================================================
    # Mentor Cache Keys
    # =========================================================================

    @staticmethod
    def mentor(mentor_id: str) -> str:
        """Mentor profile."""
        return f"mentor:{mentor_id}"

    @staticmethod
    def mentor_list() -> str:
        """List of all mentors."""
        return "mentor:list"

    @staticmethod
    def mentor_availability(mentor_id: str, date: str) -> str:
        """Mentor availability for date."""
        return f"mentor:{mentor_id}:availability:{date}"

    @staticmethod
    def mentor_sessions(mentor_id: str) -> str:
        """Mentor's upcoming sessions."""
        return f"mentor:{mentor_id}:sessions"

    # =========================================================================
    # Job Cache Keys
    # =========================================================================

    @staticmethod
    def job_posting(job_id: str) -> str:
        """Job posting details."""
        return f"job:{job_id}"

    @staticmethod
    def job_list(airline: Optional[str] = None) -> str:
        """Job postings list."""
        if airline:
            return f"job:list:{airline}"
        return "job:list:all"

    @staticmethod
    def job_search(query_hash: str) -> str:
        """Job search results."""
        return f"job:search:{query_hash}"

    # =========================================================================
    # Analytics Cache Keys
    # =========================================================================

    @staticmethod
    def analytics_daily(date: str) -> str:
        """Daily analytics data."""
        return f"analytics:daily:{date}"

    @staticmethod
    def analytics_weekly(week: str) -> str:
        """Weekly analytics data."""
        return f"analytics:weekly:{week}"

    @staticmethod
    def analytics_monthly(month: str) -> str:
        """Monthly analytics data."""
        return f"analytics:monthly:{month}"

    @staticmethod
    def analytics_user(user_id: str) -> str:
        """User analytics data."""
        return f"analytics:user:{user_id}"

    @staticmethod
    def analytics_realtime() -> str:
        """Real-time analytics."""
        return "analytics:realtime"

    @staticmethod
    def analytics_leaderboard() -> str:
        """Leaderboard cache."""
        return "analytics:leaderboard"

    # =========================================================================
    # Rate Limiting Keys
    # =========================================================================

    @staticmethod
    def rate_limit(identifier: str, window: str) -> str:
        """Rate limit counter."""
        return f"ratelimit:{identifier}:{window}"

    @staticmethod
    def rate_limit_ip(ip: str) -> str:
        """IP-based rate limit."""
        return f"ratelimit:ip:{ip}"

    @staticmethod
    def rate_limit_user(user_id: str) -> str:
        """User-based rate limit."""
        return f"ratelimit:user:{user_id}"

    @staticmethod
    def rate_limit_api(user_id: str, endpoint: str) -> str:
        """API endpoint rate limit."""
        return f"ratelimit:api:{user_id}:{endpoint}"

    # =========================================================================
    # Session Keys
    # =========================================================================

    @staticmethod
    def session(session_id: str) -> str:
        """User session data."""
        return f"session:{session_id}"

    @staticmethod
    def session_token(token: str) -> str:
        """Token to session mapping."""
        return f"session:token:{token}"

    @staticmethod
    def active_sessions() -> str:
        """Set of active session IDs."""
        return "session:active"

    # =========================================================================
    # Temporary/Lock Keys
    # =========================================================================

    @staticmethod
    def lock(resource: str) -> str:
        """Distributed lock."""
        return f"lock:{resource}"

    @staticmethod
    def temp(identifier: str) -> str:
        """Temporary data."""
        return f"temp:{identifier}"

    @staticmethod
    def otp(user_id: str) -> str:
        """One-time password."""
        return f"otp:{user_id}"

    @staticmethod
    def verification(token: str) -> str:
        """Verification token."""
        return f"verify:{token}"

    # =========================================================================
    # Configuration Cache
    # =========================================================================

    @staticmethod
    def config(key: str) -> str:
        """Configuration value."""
        return f"config:{key}"

    @staticmethod
    def feature_flag(flag: str) -> str:
        """Feature flag value."""
        return f"feature:{flag}"

    # =========================================================================
    # TTL Constants
    # =========================================================================

    # Short TTL (for frequently changing data)
    TTL_SHORT = 60  # 1 minute
    TTL_REALTIME = 10  # 10 seconds

    # Medium TTL (for moderately changing data)
    TTL_MEDIUM = 300  # 5 minutes
    TTL_DEFAULT = 3600  # 1 hour

    # Long TTL (for rarely changing data)
    TTL_LONG = 86400  # 24 hours
    TTL_WEEK = 604800  # 1 week

    # Session TTL
    TTL_SESSION = 1800  # 30 minutes
    TTL_OTP = 300  # 5 minutes
    TTL_VERIFICATION = 86400  # 24 hours
