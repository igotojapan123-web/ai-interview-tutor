# constants.py
# 대기업 수준 상수 및 메시지 중앙 관리
# FlyReady Lab - Constants & Messages

from typing import Dict, List
from enum import Enum

# =============================================================================
# 앱 정보
# =============================================================================

APP_NAME = "FlyReady Lab"
APP_VERSION = "2.0.0"
APP_TAGLINE = "AI 승무원 면접 코칭"
APP_DESCRIPTION = "항공사 승무원 면접을 위한 AI 기반 종합 코칭 플랫폼"

# =============================================================================
# 페이지 설정
# =============================================================================

PAGE_CONFIG = {
    "page_title": APP_NAME,
    "page_icon": "✈️",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# 페이지 목록
PAGES = {
    "홈": {"name": "홈", "icon": "home", "desc": "대시보드"},
    "모의면접": {"name": "모의면접", "icon": "message-circle", "desc": "AI 면접관"},
    "롤플레잉": {"name": "롤플레잉", "icon": "users", "desc": "기내 상황"},
    "영어면접": {"name": "영어면접", "icon": "globe", "desc": "영어 답변"},
    "토론면접": {"name": "토론면접", "icon": "message-square", "desc": "그룹 토론"},
    "자소서첨삭": {"name": "자소서첨삭", "icon": "edit", "desc": "AI 피드백"},
    "실전연습": {"name": "실전연습", "icon": "play", "desc": "종합 분석"},
    "이미지메이킹": {"name": "이미지메이킹", "icon": "image", "desc": "복장 체크"},
    "기내방송연습": {"name": "기내방송연습", "icon": "mic", "desc": "스크립트"},
    "표정연습": {"name": "표정연습", "icon": "smile", "desc": "표정 분석"},
    "항공사퀴즈": {"name": "항공사퀴즈", "icon": "help-circle", "desc": "187문항"},
    "면접꿀팁": {"name": "면접꿀팁", "icon": "lightbulb", "desc": "핵심 팁"},
    "항공사가이드": {"name": "항공사가이드", "icon": "book", "desc": "각 사 정보"},
    "국민체력": {"name": "국민체력", "icon": "activity", "desc": "체력 기준"},
    "기업분석": {"name": "기업분석", "icon": "bar-chart", "desc": "기업 정보"},
    "진도관리": {"name": "진도관리", "icon": "check-square", "desc": "학습 현황"},
    "성장그래프": {"name": "성장그래프", "icon": "trending-up", "desc": "점수 추이"},
    "채용알림": {"name": "채용알림", "icon": "bell", "desc": "공고 소식"},
    "합격자DB": {"name": "합격자DB", "icon": "database", "desc": "합격 자료"},
    "D-Day캘린더": {"name": "D-Day캘린더", "icon": "calendar", "desc": "일정 관리"},
}

# =============================================================================
# 항공사 정보
# =============================================================================

class Airline(Enum):
    """항공사 코드"""
    KOREAN_AIR = "대한항공"
    ASIANA = "아시아나항공"
    JINAIR = "진에어"
    JEJU_AIR = "제주항공"
    TWAY = "티웨이항공"
    AIR_BUSAN = "에어부산"
    AIR_SEOUL = "에어서울"
    EASTAR = "이스타항공"


AIRLINES: Dict[str, Dict] = {
    "대한항공": {
        "code": "KE",
        "english": "Korean Air",
        "hub": "인천국제공항",
        "slogan": "Excellence in Flight",
        "color": "#0033A0"
    },
    "아시아나항공": {
        "code": "OZ",
        "english": "Asiana Airlines",
        "hub": "인천국제공항",
        "slogan": "Beautiful People, Asiana",
        "color": "#E31837"
    },
    "진에어": {
        "code": "LJ",
        "english": "Jin Air",
        "hub": "인천국제공항",
        "slogan": "Fly, Better Fly",
        "color": "#FF6B00"
    },
    "제주항공": {
        "code": "7C",
        "english": "Jeju Air",
        "hub": "김포국제공항",
        "slogan": "Refresh your life",
        "color": "#FF6B00"
    },
    "티웨이항공": {
        "code": "TW",
        "english": "T'way Air",
        "hub": "김포국제공항",
        "slogan": "Your way, T'way",
        "color": "#E31837"
    },
    "에어부산": {
        "code": "BX",
        "english": "Air Busan",
        "hub": "김해국제공항",
        "slogan": "Air Busan, Fly High!",
        "color": "#1E3A8A"
    },
    "에어서울": {
        "code": "RS",
        "english": "Air Seoul",
        "hub": "인천국제공항",
        "slogan": "Fly with Smile",
        "color": "#6366F1"
    },
    "이스타항공": {
        "code": "ZE",
        "english": "Eastar Jet",
        "hub": "인천국제공항",
        "slogan": "Easy & Smart Travel",
        "color": "#10B981"
    },
}

AIRLINE_NAMES = list(AIRLINES.keys())

# =============================================================================
# UI 메시지
# =============================================================================

class Messages:
    """UI 메시지 상수"""

    # 로딩 메시지
    LOADING_GENERAL = "처리 중입니다"
    LOADING_AI_ANALYSIS = "AI가 분석하고 있습니다"
    LOADING_VOICE = "음성을 처리하고 있습니다"
    LOADING_VIDEO = "영상을 처리하고 있습니다"
    LOADING_FILE = "파일을 처리하고 있습니다"
    LOADING_SAVE = "저장 중입니다"
    LOADING_NETWORK = "서버와 통신 중입니다"

    # 완료 메시지
    SUCCESS_GENERAL = "완료되었습니다"
    SUCCESS_SAVE = "저장되었습니다"
    SUCCESS_DELETE = "삭제되었습니다"
    SUCCESS_SUBMIT = "제출되었습니다"
    SUCCESS_COPY = "클립보드에 복사되었습니다"

    # 에러 메시지
    ERROR_GENERAL = "오류가 발생했습니다"
    ERROR_NETWORK = "네트워크 연결을 확인해 주세요"
    ERROR_API = "서비스에 연결할 수 없습니다"
    ERROR_TIMEOUT = "요청 시간이 초과되었습니다"
    ERROR_VALIDATION = "입력 내용을 확인해 주세요"
    ERROR_AUTH = "인증이 필요합니다"
    ERROR_PERMISSION = "접근 권한이 없습니다"
    ERROR_NOT_FOUND = "요청한 내용을 찾을 수 없습니다"
    ERROR_FILE = "파일을 처리할 수 없습니다"

    # 경고 메시지
    WARNING_UNSAVED = "저장되지 않은 변경사항이 있습니다"
    WARNING_CONFIRM = "이 작업을 진행하시겠습니까?"
    WARNING_DELETE = "삭제하면 복구할 수 없습니다"
    WARNING_LIMIT = "사용 한도에 도달했습니다"

    # 안내 메시지
    INFO_EMPTY = "표시할 내용이 없습니다"
    INFO_NO_DATA = "데이터가 없습니다"
    INFO_FIRST_TIME = "처음 방문하셨네요! 환영합니다"
    INFO_HINT = "도움이 필요하시면 안내를 확인하세요"

    # 입력 안내
    PLACEHOLDER_TEXT = "내용을 입력하세요"
    PLACEHOLDER_SEARCH = "검색어를 입력하세요"
    PLACEHOLDER_EMAIL = "example@email.com"
    PLACEHOLDER_PASSWORD = "비밀번호를 입력하세요"


# =============================================================================
# 버튼 레이블
# =============================================================================

class ButtonLabels:
    """버튼 레이블 상수"""

    # 기본 동작
    SUBMIT = "제출"
    SAVE = "저장"
    CANCEL = "취소"
    CLOSE = "닫기"
    CONFIRM = "확인"
    DELETE = "삭제"
    EDIT = "수정"
    ADD = "추가"
    COPY = "복사"

    # 네비게이션
    NEXT = "다음"
    PREV = "이전"
    FIRST = "처음"
    LAST = "마지막"
    BACK = "돌아가기"
    HOME = "홈으로"

    # 상태
    START = "시작"
    STOP = "중지"
    PAUSE = "일시정지"
    RESUME = "재개"
    RETRY = "다시 시도"
    RESET = "초기화"
    REFRESH = "새로고침"

    # 면접 관련
    START_INTERVIEW = "면접 시작"
    END_INTERVIEW = "면접 종료"
    NEXT_QUESTION = "다음 질문"
    GET_FEEDBACK = "피드백 받기"
    RECORD_ANSWER = "답변 녹음"
    SUBMIT_ANSWER = "답변 제출"
    VIEW_RESULT = "결과 보기"
    PRACTICE_MORE = "더 연습하기"


# =============================================================================
# 면접 관련 상수
# =============================================================================

class InterviewConfig:
    """면접 설정"""

    # 질문 수
    MIN_QUESTIONS = 3
    DEFAULT_QUESTIONS = 5
    MAX_QUESTIONS = 10

    # 답변 시간 (초)
    MIN_ANSWER_TIME = 30
    DEFAULT_ANSWER_TIME = 60
    MAX_ANSWER_TIME = 180

    # 답변 길이 (글자)
    MIN_ANSWER_LENGTH = 50
    MAX_ANSWER_LENGTH = 2000

    # 점수 범위
    MIN_SCORE = 0
    MAX_SCORE = 100
    PASSING_SCORE = 70


# 면접 유형
INTERVIEW_TYPES = {
    "인성면접": {
        "description": "지원자의 가치관, 태도, 인성을 평가하는 면접",
        "duration": "15-20분",
        "questions": 5
    },
    "직무면접": {
        "description": "직무 역량과 전문성을 평가하는 면접",
        "duration": "20-30분",
        "questions": 7
    },
    "영어면접": {
        "description": "영어 의사소통 능력을 평가하는 면접",
        "duration": "10-15분",
        "questions": 5
    },
    "토론면접": {
        "description": "그룹 토론을 통해 협업 능력을 평가하는 면접",
        "duration": "30-40분",
        "questions": 3
    },
    "상황면접": {
        "description": "가상의 상황에서의 대처 능력을 평가하는 면접",
        "duration": "15-20분",
        "questions": 5
    },
}

# 질문 카테고리
QUESTION_CATEGORIES = [
    "자기소개",
    "지원동기",
    "성격/강점",
    "경험/사례",
    "위기대처",
    "서비스마인드",
    "팀워크",
    "글로벌역량",
    "미래계획",
    "기업이해",
]

# =============================================================================
# 평가 관련 상수
# =============================================================================

class EvaluationCriteria:
    """평가 기준"""

    CRITERIA = {
        "내용": {
            "weight": 30,
            "description": "답변의 구체성, 적절성, 논리성"
        },
        "표현": {
            "weight": 25,
            "description": "발음, 어조, 속도, 명확성"
        },
        "태도": {
            "weight": 25,
            "description": "자신감, 성실함, 긍정적 태도"
        },
        "구조": {
            "weight": 20,
            "description": "답변의 구성, 시간 배분"
        }
    }


# 점수 등급
SCORE_GRADES = {
    "S": {"min": 90, "label": "최우수", "color": "#059669"},
    "A": {"min": 80, "label": "우수", "color": "#2563eb"},
    "B": {"min": 70, "label": "양호", "color": "#7c3aed"},
    "C": {"min": 60, "label": "보통", "color": "#d97706"},
    "D": {"min": 50, "label": "미흡", "color": "#dc2626"},
    "F": {"min": 0, "label": "부족", "color": "#6b7280"},
}


def get_score_grade(score: float) -> dict:
    """점수에 해당하는 등급 반환"""
    for grade, info in SCORE_GRADES.items():
        if score >= info["min"]:
            return {"grade": grade, **info}
    return {"grade": "F", **SCORE_GRADES["F"]}


# =============================================================================
# 제한 설정
# =============================================================================

class Limits:
    """시스템 제한"""

    # 파일 업로드
    MAX_FILE_SIZE_MB = 50
    MAX_IMAGE_SIZE_MB = 10
    MAX_VIDEO_SIZE_MB = 100
    MAX_AUDIO_SIZE_MB = 25

    # 허용 파일 형식
    ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "gif", "webp"]
    ALLOWED_VIDEO_TYPES = ["mp4", "webm", "mov", "avi"]
    ALLOWED_AUDIO_TYPES = ["mp3", "wav", "m4a", "ogg"]
    ALLOWED_DOC_TYPES = ["pdf", "doc", "docx", "txt"]

    # API 호출
    MAX_API_RETRIES = 3
    API_TIMEOUT_SECONDS = 60
    RATE_LIMIT_PER_MINUTE = 60

    # 텍스트 길이
    MAX_INPUT_LENGTH = 10000
    MAX_PROMPT_LENGTH = 4000
    MAX_RESPONSE_LENGTH = 8000

    # 세션
    SESSION_TIMEOUT_MINUTES = 30
    MAX_SESSION_DATA_MB = 50


# =============================================================================
# 색상 팔레트
# =============================================================================

COLORS = {
    # 브랜드 색상
    "primary": "#2563eb",
    "secondary": "#64748b",
    "accent": "#f59e0b",

    # 상태 색상
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",

    # 텍스트 색상
    "text_primary": "#1e293b",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",

    # 배경 색상
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8fafc",
    "bg_tertiary": "#f1f5f9",

    # 테두리 색상
    "border": "#e2e8f0",
    "border_focus": "#2563eb",
}

# =============================================================================
# 키보드 단축키
# =============================================================================

KEYBOARD_SHORTCUTS = {
    "save": "Ctrl+S",
    "submit": "Ctrl+Enter",
    "cancel": "Escape",
    "next": "Ctrl+→",
    "prev": "Ctrl+←",
    "help": "F1",
    "search": "Ctrl+K",
}

# =============================================================================
# 정규식 패턴
# =============================================================================

REGEX_PATTERNS = {
    "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    "phone": r'^(0\d{1,2})-?(\d{3,4})-?(\d{4})$',
    "url": r'^https?://[^\s/$.?#].[^\s]*$',
    "korean": r'^[가-힣\s]+$',
    "english": r'^[a-zA-Z\s]+$',
    "alphanumeric": r'^[a-zA-Z0-9]+$',
}
