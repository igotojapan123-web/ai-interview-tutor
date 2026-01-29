# auth_system.py
# FlyReady Lab - 통합 인증 시스템 (Kakao, Google, Apple)
# Firebase Authentication 기반

import os
import json
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import requests
import hashlib
import secrets

from logging_config import get_logger
logger = get_logger(__name__)

# ============================================
# 환경 변수 설정
# ============================================
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID", "")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET", "")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8501/callback/kakao")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/callback/google")

APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID", "")
APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID", "")
APPLE_KEY_ID = os.getenv("APPLE_KEY_ID", "")
APPLE_REDIRECT_URI = os.getenv("APPLE_REDIRECT_URI", "http://localhost:8501/callback/apple")

# Firebase 설정 (선택적)
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

# ============================================
# 사용자 데이터 저장소
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(DATA_DIR, "sessions.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_users() -> Dict:
    """사용자 데이터 로드"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"사용자 데이터 로드 실패: {e}")
    return {}


def save_users(users: Dict):
    """사용자 데이터 저장"""
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"사용자 데이터 저장 실패: {e}")


def load_sessions() -> Dict:
    """세션 데이터 로드"""
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"세션 데이터 로드 실패: {e}")
    return {}


def save_sessions(sessions: Dict):
    """세션 데이터 저장"""
    try:
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"세션 데이터 저장 실패: {e}")


# ============================================
# 사용자 모델
# ============================================
class User:
    def __init__(self, data: Dict):
        self.user_id = data.get("user_id", "")
        self.email = data.get("email", "")
        self.name = data.get("name", "")
        self.profile_image = data.get("profile_image", "")
        self.provider = data.get("provider", "")  # kakao, google, apple
        self.provider_id = data.get("provider_id", "")

        # 구독 정보
        self.subscription_tier = data.get("subscription_tier", "free")  # free, standard, premium
        self.subscription_end = data.get("subscription_end")

        # 사용량
        self.daily_api_calls = data.get("daily_api_calls", 0)
        self.last_api_date = data.get("last_api_date", "")

        # 메타데이터
        self.created_at = data.get("created_at", "")
        self.last_login = data.get("last_login", "")
        self.is_active = data.get("is_active", True)

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "profile_image": self.profile_image,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "subscription_tier": self.subscription_tier,
            "subscription_end": self.subscription_end,
            "daily_api_calls": self.daily_api_calls,
            "last_api_date": self.last_api_date,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "is_active": self.is_active,
        }

    def is_premium(self) -> bool:
        """프리미엄 구독 여부 확인"""
        if self.subscription_tier == "free":
            return False
        if self.subscription_end:
            end_date = datetime.fromisoformat(self.subscription_end)
            return datetime.now() < end_date
        return False

    def get_daily_limit(self) -> int:
        """일일 API 호출 제한"""
        limits = {
            "free": 10,
            "standard": 50,
            "premium": 999999,
        }
        return limits.get(self.subscription_tier, 10)

    def can_use_api(self) -> bool:
        """API 사용 가능 여부"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_api_date != today:
            return True
        return self.daily_api_calls < self.get_daily_limit()

    def increment_api_usage(self):
        """API 사용량 증가"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.last_api_date != today:
            self.daily_api_calls = 1
            self.last_api_date = today
        else:
            self.daily_api_calls += 1


# ============================================
# 구독 티어 정의
# ============================================
SUBSCRIPTION_TIERS = {
    "free": {
        "name": "무료",
        "price_monthly": 0,
        "price_yearly": 0,
        "features": [
            "일일 AI 면접 연습 3회",
            "기본 피드백",
            "진도 관리",
            "항공사 퀴즈",
        ],
        "daily_limit": 10,
        "color": "#6b7280",
    },
    "standard": {
        "name": "스탠다드",
        "price_monthly": 19900,
        "price_yearly": 149000,
        "features": [
            "일일 AI 면접 연습 30회",
            "심층 AI 피드백",
            "자소서 첨삭 무제한",
            "음성 분석",
            "합격자 DB 열람",
            "우선 고객 지원",
        ],
        "daily_limit": 50,
        "color": "#3b82f6",
    },
    "premium": {
        "name": "프리미엄",
        "price_monthly": 39900,
        "price_yearly": 299000,
        "features": [
            "모든 기능 무제한",
            "1:1 멘토 매칭",
            "자소서 완전 첨삭",
            "영상 면접 분석",
            "표정/음성 종합 분석",
            "합격 보장 프로그램",
            "전담 매니저 배정",
        ],
        "daily_limit": 999999,
        "color": "#f59e0b",
    },
}


# ============================================
# 카카오 로그인
# ============================================
def get_kakao_auth_url() -> str:
    """카카오 로그인 URL 생성"""
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state"] = state

    params = {
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "response_type": "code",
        "state": state,
        "scope": "profile_nickname profile_image account_email",
    }

    query = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"https://kauth.kakao.com/oauth/authorize?{query}"


def process_kakao_callback(code: str, state: str) -> Optional[User]:
    """카카오 콜백 처리"""
    # State 검증
    if state != st.session_state.get("oauth_state"):
        logger.error("카카오 OAuth state 불일치")
        return None

    # Access Token 획득
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "client_secret": KAKAO_CLIENT_SECRET,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }

    try:
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            logger.error(f"카카오 토큰 획득 실패: {token_json}")
            return None

        # 사용자 정보 획득
        user_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(user_url, headers=headers)
        user_json = user_response.json()

        kakao_id = str(user_json.get("id", ""))
        kakao_account = user_json.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        # 사용자 생성 또는 업데이트
        user = find_or_create_user(
            provider="kakao",
            provider_id=kakao_id,
            email=kakao_account.get("email", ""),
            name=profile.get("nickname", ""),
            profile_image=profile.get("profile_image_url", ""),
        )

        return user

    except Exception as e:
        logger.error(f"카카오 로그인 처리 실패: {e}")
        return None


# ============================================
# 구글 로그인
# ============================================
def get_google_auth_url() -> str:
    """구글 로그인 URL 생성"""
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state"] = state

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "state": state,
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }

    query = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"


def process_google_callback(code: str, state: str) -> Optional[User]:
    """구글 콜백 처리"""
    if state != st.session_state.get("oauth_state"):
        logger.error("구글 OAuth state 불일치")
        return None

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "code": code,
    }

    try:
        token_response = requests.post(token_url, data=token_data)
        token_json = token_response.json()
        access_token = token_json.get("access_token")

        if not access_token:
            logger.error(f"구글 토큰 획득 실패: {token_json}")
            return None

        # 사용자 정보 획득
        user_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(user_url, headers=headers)
        user_json = user_response.json()

        google_id = user_json.get("id", "")

        user = find_or_create_user(
            provider="google",
            provider_id=google_id,
            email=user_json.get("email", ""),
            name=user_json.get("name", ""),
            profile_image=user_json.get("picture", ""),
        )

        return user

    except Exception as e:
        logger.error(f"구글 로그인 처리 실패: {e}")
        return None


# ============================================
# 애플 로그인
# ============================================
def get_apple_auth_url() -> str:
    """애플 로그인 URL 생성"""
    state = secrets.token_urlsafe(16)
    st.session_state["oauth_state"] = state

    params = {
        "client_id": APPLE_CLIENT_ID,
        "redirect_uri": APPLE_REDIRECT_URI,
        "response_type": "code id_token",
        "state": state,
        "scope": "name email",
        "response_mode": "form_post",
    }

    query = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"https://appleid.apple.com/auth/authorize?{query}"


def process_apple_callback(code: str, id_token: str, state: str) -> Optional[User]:
    """애플 콜백 처리"""
    if state != st.session_state.get("oauth_state"):
        logger.error("애플 OAuth state 불일치")
        return None

    try:
        # ID 토큰 디코딩 (JWT)
        import jwt

        # 실제 구현에서는 Apple의 공개키로 검증 필요
        decoded = jwt.decode(id_token, options={"verify_signature": False})

        apple_id = decoded.get("sub", "")
        email = decoded.get("email", "")

        user = find_or_create_user(
            provider="apple",
            provider_id=apple_id,
            email=email,
            name=email.split("@")[0] if email else "Apple User",
            profile_image="",
        )

        return user

    except Exception as e:
        logger.error(f"애플 로그인 처리 실패: {e}")
        return None


# ============================================
# 사용자 관리
# ============================================
def find_or_create_user(
    provider: str,
    provider_id: str,
    email: str,
    name: str,
    profile_image: str,
) -> User:
    """사용자 찾기 또는 생성"""
    users = load_users()

    # 기존 사용자 찾기
    user_key = f"{provider}_{provider_id}"

    if user_key in users:
        # 기존 사용자 업데이트
        user_data = users[user_key]
        user_data["last_login"] = datetime.now().isoformat()
        user_data["name"] = name or user_data.get("name", "")
        user_data["profile_image"] = profile_image or user_data.get("profile_image", "")
        users[user_key] = user_data
    else:
        # 새 사용자 생성
        user_data = {
            "user_id": user_key,
            "email": email,
            "name": name,
            "profile_image": profile_image,
            "provider": provider,
            "provider_id": provider_id,
            "subscription_tier": "free",
            "subscription_end": None,
            "daily_api_calls": 0,
            "last_api_date": "",
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
            "is_active": True,
        }
        users[user_key] = user_data

    save_users(users)
    return User(user_data)


def get_user_by_id(user_id: str) -> Optional[User]:
    """사용자 ID로 조회"""
    users = load_users()
    if user_id in users:
        return User(users[user_id])
    return None


def update_user(user: User):
    """사용자 정보 업데이트"""
    users = load_users()
    users[user.user_id] = user.to_dict()
    save_users(users)


def update_subscription(user_id: str, tier: str, months: int = 1):
    """구독 업데이트"""
    user = get_user_by_id(user_id)
    if user:
        user.subscription_tier = tier
        user.subscription_end = (datetime.now() + timedelta(days=30 * months)).isoformat()
        update_user(user)
        return True
    return False


# ============================================
# 세션 관리
# ============================================
def create_session(user: User) -> str:
    """세션 생성"""
    session_token = secrets.token_urlsafe(32)
    sessions = load_sessions()

    sessions[session_token] = {
        "user_id": user.user_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
    }

    save_sessions(sessions)
    return session_token


def validate_session(session_token: str) -> Optional[User]:
    """세션 검증"""
    sessions = load_sessions()

    if session_token not in sessions:
        return None

    session = sessions[session_token]
    expires_at = datetime.fromisoformat(session["expires_at"])

    if datetime.now() > expires_at:
        del sessions[session_token]
        save_sessions(sessions)
        return None

    return get_user_by_id(session["user_id"])


def destroy_session(session_token: str):
    """세션 삭제 (로그아웃)"""
    sessions = load_sessions()
    if session_token in sessions:
        del sessions[session_token]
        save_sessions(sessions)


# ============================================
# Streamlit 헬퍼 함수
# ============================================
def init_auth_state():
    """인증 상태 초기화"""
    if "user" not in st.session_state:
        st.session_state["user"] = None
    if "session_token" not in st.session_state:
        st.session_state["session_token"] = None


def get_current_user() -> Optional[User]:
    """현재 로그인된 사용자 반환"""
    init_auth_state()

    # 세션 토큰으로 사용자 조회
    session_token = st.session_state.get("session_token")
    if session_token:
        user = validate_session(session_token)
        if user:
            st.session_state["user"] = user
            return user
        else:
            st.session_state["session_token"] = None

    return st.session_state.get("user")


def login_user(user: User):
    """사용자 로그인 처리"""
    session_token = create_session(user)
    st.session_state["user"] = user
    st.session_state["session_token"] = session_token


def logout_user():
    """사용자 로그아웃 처리"""
    session_token = st.session_state.get("session_token")
    if session_token:
        destroy_session(session_token)
    st.session_state["user"] = None
    st.session_state["session_token"] = None


def require_login(func):
    """로그인 필수 데코레이터"""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            st.warning("로그인이 필요한 서비스입니다.")
            render_login_buttons()
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def require_premium(func):
    """프리미엄 구독 필수 데코레이터"""
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            st.warning("로그인이 필요한 서비스입니다.")
            render_login_buttons()
            st.stop()
        if not user.is_premium():
            st.warning("프리미엄 구독이 필요한 서비스입니다.")
            render_upgrade_prompt()
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def check_api_limit() -> bool:
    """API 사용량 체크"""
    user = get_current_user()
    if not user:
        return False

    if not user.can_use_api():
        remaining = user.get_daily_limit() - user.daily_api_calls
        st.error(f"오늘의 사용량을 모두 소진했습니다. (남은 횟수: {remaining}회)")
        st.info("더 많은 기능을 이용하려면 구독을 업그레이드하세요.")
        render_upgrade_prompt()
        return False

    return True


def use_api_call():
    """API 호출 사용 기록"""
    user = get_current_user()
    if user:
        user.increment_api_usage()
        update_user(user)


# ============================================
# UI 컴포넌트
# ============================================
def render_login_buttons():
    """로그인 버튼 렌더링"""
    st.markdown("""
    <style>
    .login-container {
        background: white;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-width: 400px;
        margin: 40px auto;
        text-align: center;
    }
    .login-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 8px;
    }
    .login-subtitle {
        font-size: 0.9rem;
        color: #64748b;
        margin-bottom: 24px;
    }
    .login-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        width: 100%;
        padding: 14px 20px;
        border-radius: 12px;
        font-size: 1rem;
        font-weight: 600;
        text-decoration: none;
        margin-bottom: 12px;
        transition: all 0.2s;
    }
    .login-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .btn-kakao {
        background: #FEE500;
        color: #000000;
    }
    .btn-google {
        background: #ffffff;
        color: #333333;
        border: 1px solid #dadce0;
    }
    .btn-apple {
        background: #000000;
        color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

    kakao_url = get_kakao_auth_url() if KAKAO_CLIENT_ID else "#"
    google_url = get_google_auth_url() if GOOGLE_CLIENT_ID else "#"
    apple_url = get_apple_auth_url() if APPLE_CLIENT_ID else "#"

    st.markdown(f"""
    <div class="login-container">
        <div class="login-title">FlyReady Lab 로그인</div>
        <div class="login-subtitle">소셜 계정으로 간편하게 시작하세요</div>

        <a href="{kakao_url}" class="login-btn btn-kakao">
            <svg width="20" height="20" viewBox="0 0 20 20"><path fill="#000" d="M10 0C4.477 0 0 3.582 0 8c0 2.867 1.886 5.382 4.73 6.812-.207.783-.75 2.84-.859 3.283-.136.553.203.546.427.398.176-.116 2.8-1.9 3.934-2.673.576.085 1.168.13 1.768.13 5.523 0 10-3.582 10-8S15.523 0 10 0z"/></svg>
            카카오로 시작하기
        </a>

        <a href="{google_url}" class="login-btn btn-google">
            <svg width="20" height="20" viewBox="0 0 20 20"><path fill="#4285F4" d="M19.6 10.2c0-.7-.1-1.3-.2-1.9H10v3.7h5.4c-.2 1.2-.9 2.2-1.9 2.9v2.4h3.1c1.8-1.7 2.9-4.1 2.9-7.1z"/><path fill="#34A853" d="M10 20c2.6 0 4.7-.9 6.3-2.3l-3.1-2.4c-.9.6-2 .9-3.2.9-2.5 0-4.6-1.7-5.3-3.9H1.5v2.5C3.1 17.8 6.3 20 10 20z"/><path fill="#FBBC05" d="M4.7 12.3c-.2-.6-.3-1.2-.3-1.9s.1-1.3.3-1.9V6H1.5C.8 7.3.4 8.6.4 10s.4 2.7 1.1 4l3.2-1.7z"/><path fill="#EA4335" d="M10 4c1.4 0 2.6.5 3.6 1.4l2.7-2.7C14.7 1 12.6 0 10 0 6.3 0 3.1 2.2 1.5 5.5l3.2 2.5c.7-2.2 2.8-4 5.3-4z"/></svg>
            Google로 시작하기
        </a>

        <a href="{apple_url}" class="login-btn btn-apple">
            <svg width="20" height="20" viewBox="0 0 20 20"><path fill="#fff" d="M15.5 10.2c0-2.4 2-3.6 2.1-3.6-.1-.2-1.2-1.7-3-1.7-1.3 0-2.3.7-3 .7-.7 0-1.7-.7-2.9-.7-1.5 0-2.9.9-3.6 2.2-1.5 2.7-.4 6.7 1.1 8.9.7 1.1 1.6 2.3 2.8 2.2 1.1 0 1.5-.7 2.9-.7 1.3 0 1.7.7 2.9.7 1.2 0 2-1.1 2.7-2.1.9-1.3 1.2-2.5 1.2-2.6-.1-.1-2.2-.8-2.2-3.3zm-2-6.1c.6-.7 1-1.7.9-2.7-1 0-2.1.7-2.7 1.4-.6.7-1.1 1.7-.9 2.7 1 .1 2.1-.5 2.7-1.4z"/></svg>
            Apple로 시작하기
        </a>
    </div>
    """, unsafe_allow_html=True)


def render_user_profile():
    """사용자 프로필 렌더링"""
    user = get_current_user()
    if not user:
        return

    tier_info = SUBSCRIPTION_TIERS.get(user.subscription_tier, SUBSCRIPTION_TIERS["free"])
    tier_color = tier_info["color"]

    st.markdown(f"""
    <style>
    .user-profile {{
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 20px;
    }}
    .user-avatar {{
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        overflow: hidden;
    }}
    .user-avatar img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}
    .user-info {{
        flex: 1;
    }}
    .user-name {{
        font-size: 1rem;
        font-weight: 700;
        color: #1e3a5f;
    }}
    .user-tier {{
        font-size: 0.75rem;
        padding: 2px 8px;
        border-radius: 10px;
        background: {tier_color}20;
        color: {tier_color};
        font-weight: 600;
        display: inline-block;
        margin-top: 4px;
    }}
    .user-usage {{
        font-size: 0.8rem;
        color: #64748b;
    }}
    </style>
    """, unsafe_allow_html=True)

    avatar_html = f'<img src="{user.profile_image}" alt="avatar">' if user.profile_image else user.name[0] if user.name else "U"
    remaining = user.get_daily_limit() - user.daily_api_calls

    st.markdown(f"""
    <div class="user-profile">
        <div class="user-avatar">{avatar_html}</div>
        <div class="user-info">
            <div class="user-name">{user.name}</div>
            <div class="user-tier">{tier_info['name']}</div>
        </div>
        <div class="user-usage">오늘 남은 횟수: {remaining}회</div>
    </div>
    """, unsafe_allow_html=True)


def render_upgrade_prompt():
    """구독 업그레이드 안내"""
    st.markdown("""
    <style>
    .upgrade-prompt {
        background: linear-gradient(135deg, #1e3a5f, #3b82f6);
        border-radius: 16px;
        padding: 24px;
        color: white;
        text-align: center;
        margin: 20px 0;
    }
    .upgrade-title {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .upgrade-desc {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-bottom: 16px;
    }
    .upgrade-btn {
        background: white;
        color: #1e3a5f;
        padding: 12px 32px;
        border-radius: 8px;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
    }
    </style>

    <div class="upgrade-prompt">
        <div class="upgrade-title">더 많은 기능을 원하시나요?</div>
        <div class="upgrade-desc">프리미엄으로 업그레이드하고 무제한으로 연습하세요!</div>
        <a href="/pricing" class="upgrade-btn">요금제 보기</a>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# 콜백 처리 (별도 페이지에서 호출)
# ============================================
def handle_oauth_callback():
    """OAuth 콜백 처리"""
    query_params = st.query_params

    code = query_params.get("code")
    state = query_params.get("state")

    if not code:
        return None

    # 현재 URL 경로로 provider 판단
    # 실제 구현에서는 callback URL을 분리하거나 state에 provider 포함

    # 임시: state에서 provider 추출하거나 별도 처리 필요
    # 여기서는 세션에 저장된 정보 사용

    provider = st.session_state.get("oauth_provider", "kakao")

    user = None
    if provider == "kakao":
        user = process_kakao_callback(code, state)
    elif provider == "google":
        user = process_google_callback(code, state)
    elif provider == "apple":
        id_token = query_params.get("id_token", "")
        user = process_apple_callback(code, id_token, state)

    if user:
        login_user(user)
        st.success(f"{user.name}님, 환영합니다!")
        # 쿼리 파라미터 제거
        st.query_params.clear()
        return user

    return None
