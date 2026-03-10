# pages/4_모의면접.py
# 실전 모의면접 - AI 영상 면접관 + 음성 답변 + 음성/내용 평가

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import os
import time
import random
import base64
import json
import streamlit as st
import streamlit.components.v1 as components
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 안전한 API 호출 및 검증 유틸리티
try:
    from safe_api import (
        safe_api_call, get_audio_hash, is_audio_processed,
        validate_string, validate_int, validate_dict, validate_list,
        validate_api_response, safe_get, safe_execute,
        init_session_state, safe_session_get, escape_html
    )
    SAFE_API_AVAILABLE = True
except ImportError:
    SAFE_API_AVAILABLE = False

from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC, AIRLINES_WITH_RESUME, AIRLINE_TYPE
from env_config import OPENAI_API_KEY

# 음성/영상 유틸리티 import
try:
    from video_utils import (
        check_did_api_available,
        create_interviewer_video,
        get_video_html,
        get_fallback_avatar_html,
    )
    from voice_utils import (
        transcribe_audio,
        analyze_voice_quality,
        analyze_voice_complete,
        evaluate_answer_content,
        generate_tts_audio,
        get_audio_player_html,
        get_loud_audio_component,
        analyze_interview_emotion,  # Phase 1: 감정 분석 추가
        analyze_voice_advanced,  # 고도화된 음성 분석
    )
    from video_utils import get_enhanced_fallback_avatar_html  # Phase 1: 향상된 아바타
    VIDEO_UTILS_AVAILABLE = True
except ImportError:
    VIDEO_UTILS_AVAILABLE = False

# Phase D1: 음성 분석 고도화 모듈
try:
    from voice_analysis_enhancer import (
        analyze_voice_enhanced,
        get_speech_speed_graph_data,
        get_tone_graph_data,
        get_volume_graph_data,
        get_silence_analysis,
        SpeechSpeedLevel, VolumeLevel, TonePattern
    )
    VOICE_ENHANCER_AVAILABLE = True
except ImportError:
    VOICE_ENHANCER_AVAILABLE = False

# Phase D2: 감정 분석 고도화 모듈
try:
    from emotion_analysis_enhancer import (
        analyze_emotion_enhanced,
        get_confidence_timeline,
        get_stress_timeline,
        get_engagement_timeline,
        get_segment_analysis,
        ConfidenceLevel, StressLevel, EmotionType
    )
    EMOTION_ENHANCER_AVAILABLE = True
except ImportError:
    EMOTION_ENHANCER_AVAILABLE = False

# 점수 자동 저장 유틸리티
try:
    from score_utils import save_practice_score, parse_evaluation_score
    SCORE_UTILS_AVAILABLE = True
except ImportError:
    SCORE_UTILS_AVAILABLE = False

# Phase 3: 점수 집계 시스템
try:
    from score_aggregator import add_score as add_benchmark_score
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

# 면접 히스토리 저장
try:
    from interview_history_utils import save_interview_session
    HISTORY_UTILS_AVAILABLE = True
except ImportError:
    HISTORY_UTILS_AVAILABLE = False

# 비교 피드백 서비스
try:
    from comparison_feedback_service import (
        get_previous_feedback_context,
        generate_comparison_feedback,
        render_comparison_feedback_ui,
    )
    COMPARISON_FEEDBACK_AVAILABLE = True
except ImportError:
    COMPARISON_FEEDBACK_AVAILABLE = False

# 항공사별 맞춤 질문 import
try:
    from airline_questions import (
        get_airline_questions_fresh,  # 중복 방지 버전
        get_airline_questions,
        get_airline_values,
        get_airline_keywords,
        AIRLINE_VALUES,
    )
    AIRLINE_QUESTIONS_AVAILABLE = True
except ImportError:
    AIRLINE_QUESTIONS_AVAILABLE = False

# PDF 리포트 생성 import
try:
    from mock_interview_report import (
        generate_mock_interview_report,
        get_mock_interview_report_filename,
    )
    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

# Phase B1: 면접 강화 모듈 import
try:
    from interview_enhancer import (
        InterviewerType,
        INTERVIEWER_CHARACTERS,
        get_interviewer_character,
        get_interviewer_prompt,
        analyze_interview_answer,
        generate_follow_up_question,
        get_keyword_feedback,
        get_time_feedback,
        EnhancedInterviewEngine,
    )
    INTERVIEW_ENHANCER_AVAILABLE = True
except ImportError:
    INTERVIEW_ENHANCER_AVAILABLE = False

# Phase 2: 웹캠 분석 제거됨 (표정연습 페이지에서 별도 제공)
WEBCAM_AVAILABLE = False


# Use new layout system
from sidebar_common import init_page, end_page

# 공용 유틸리티 (Stage 2)
try:
    from shared_utils import get_api_key, load_json, save_json
except ImportError:
    pass

# Initialize page with new layout
init_page(
    title="AI 모의면접",
    current_page="모의면접",
    wide_layout=True
)



# 구글 번역 방지 + 복사/붙여넣기 허용 (캐싱)
@st.cache_resource
def get_interview_css():
    """모의면접 페이지 CSS (영구 캐시)"""
    return """
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<style>
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    translate: no !important;
}
.notranslate, [translate="no"] {
    translate: no !important;
}
textarea, input, [contenteditable="true"],
.stTextArea textarea, .stTextInput input,
[data-testid="stTextArea"] textarea,
[data-testid="stTextInput"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="input"] input {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
    -webkit-user-drag: none !important;
    pointer-events: auto !important;
}
html, body, div, span, p, h1, h2, h3, h4, h5, h6, label {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
button, .stButton, [role="button"] {
    -webkit-user-select: none !important;
    user-select: none !important;
}
</style>
"""

st.markdown(get_interview_css(), unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate" lang="ko">', unsafe_allow_html=True)

# ----------------------------
# 비밀번호 보호
# ----------------------------

# =====================
# 면접 질문 풀 (통합: 기본 + 실전연습 + STAR 기법)
# =====================

INTERVIEW_QUESTIONS = {
    "common": [
        "간단하게 자기소개 해주세요.",
        "왜 승무원이 되고 싶으신가요?",
        "저희 항공사에 왜 지원하셨나요?",
        "본인의 강점과 약점을 말씀해주세요.",
        "승무원에게 가장 중요한 자질은 무엇이라고 생각하시나요?",
        "지원 전 어떤 준비를 하셨나요?",
        "본인만의 서비스 철학이 있다면 말씀해주세요.",
        "이 직업을 통해 이루고 싶은 목표는 무엇인가요?",
    ],
    "experience": [
        "팀워크를 발휘했던 경험을 말씀해주세요.",
        "어려운 고객을 응대한 경험이 있나요?",
        "갈등을 해결했던 경험을 말씀해주세요.",
        "실패했던 경험과 그로부터 배운 점은 무엇인가요?",
        "리더십을 발휘한 경험을 말씀해주세요.",
        "서비스업에서 감동을 받았던 경험이 있나요?",
        "예상치 못한 상황에 대처한 경험을 말씀해주세요.",
        "다문화 환경에서 소통한 경험이 있나요?",
        "창의적으로 문제를 해결한 경험을 말씀해주세요.",
        "규정을 지키면서 고객을 만족시킨 경험이 있나요?",
    ],
    "situational": [
        "기내에서 승객이 쓰러지면 어떻게 하시겠습니까?",
        "승객이 무리한 요구를 하면 어떻게 대응하시겠습니까?",
        "동료와 의견 충돌이 생기면 어떻게 하시겠습니까?",
        "비행 중 공황 상태의 승객을 어떻게 도우시겠습니까?",
        "안전규정을 거부하는 승객을 어떻게 설득하시겠습니까?",
        "비행 중 난기류가 발생하면 어떻게 승객을 안심시키겠습니까?",
        "만취 승객이 다른 승객에게 불쾌감을 주면 어떻게 하시겠습니까?",
        "기내에서 승객 간 다툼이 발생하면 어떻게 중재하시겠습니까?",
        "갓난아이를 동반한 승객이 도움을 요청하면 어떻게 하시겠습니까?",
    ],
    "personality": [
        "스트레스를 어떻게 관리하시나요?",
        "주변에서 본인을 어떻게 평가하나요?",
        "10년 후 본인의 모습은 어떨 것 같나요?",
        "왜 다른 직업이 아닌 승무원인가요?",
        "이 직업의 어려운 점은 무엇이라고 생각하시나요?",
        "본인이 가장 소중하게 생각하는 가치는 무엇인가요?",
        "체력 관리는 어떻게 하고 계신가요?",
        "외국어 능력은 어느 정도이며, 어떻게 준비하셨나요?",
        "불규칙한 근무에 대해 어떻게 생각하시나요?",
    ],
}

# =====================
# STAR 기법 힌트 (연습모드용)
# PDF 기반 + 면접관 질문 의도 포함
# =====================
STAR_HINTS = {
    # 기본 질문
    "간단하게 자기소개 해주세요.": {
        "intent": "첫인상 + 핵심역량 파악",
        "star_focus": "S+T 40%, A 30%, R 30%",
        "tip": "30초 내로 핵심만! 이름-학력-경험-지원동기 순서",
        "example_star": "S: 서비스업 3년 경험 / T: 고객 만족 극대화 목표 / A: 매일 10명+ 응대 / R: 단골 50% 증가"
    },
    "왜 승무원이 되고 싶으신가요?": {
        "intent": "진정성 + 항공사 이해도",
        "star_focus": "S+T 40%, A 30%, R 30%",
        "tip": "구체적 경험 → 항공사 가치 연결",
        "example_star": "S: 해외여행 중 승무원 서비스에 감동 / T: 그 감동을 전하고 싶음 / A: 서비스 경험 쌓기 / R: 승무원 꿈 확신"
    },
    "저희 항공사에 왜 지원하셨나요?": {
        "intent": "회사 연구 + 지원 진정성",
        "star_focus": "S 30%, T 30%, A+R 40%",
        "tip": "해당 항공사만의 차별점 + 본인 가치관 연결",
        "example_star": "S: 항공사 서비스 직접 경험 / T: 그 가치에 공감 / A: 인재상 연구 / R: 나와 맞는 회사 확신"
    },
    # 팀워크 질문
    "팀워크를 발휘했던 경험을 말씀해주세요.": {
        "intent": "협업 능력 + 문제해결",
        "star_focus": "A (행동) 65%, R (결과) 25%",
        "tip": "갈등 해결 과정을 3단계로 쪼개서 설명",
        "example_star": "S: 5명 팀, 3개월 프로젝트 / T: 의견충돌로 2주 지체 / A: 강점분석→역할재분배→매일 30분 미팅 / R: A+ 학점, 최고 팀워크 평가"
    },
    # 고객응대 질문
    "어려운 고객을 응대한 경험이 있나요?": {
        "intent": "감정 조절 + 서비스 마인드",
        "star_focus": "A (행동) 60%, R (결과) 30%",
        "tip": "경청→공감→해결의 3단계",
        "example_star": "S: 카페 아르바이트, 주문 실수로 15분 지연 / T: 환불 요구 고객 진정 / A: 진심 사과→즉시 재제조→쿠폰 제공 / R: 5점 리뷰, 단골 됨"
    },
    # 실패 경험
    "실패했던 경험과 그로부터 배운 점은 무엇인가요?": {
        "intent": "자기 성찰 + 성장 가능성",
        "star_focus": "R (결과/배움) 50%, A 40%",
        "tip": "배운 점을 명확히 + 이후 적용 사례",
        "example_star": "S: 토익 목표 100점 미달 / T: 3개월 내 달성 필요 / A: 매일 2시간+약점 집중+스터디 / R: 2개월 만에 달성, 체계적 학습법 습득"
    },
    # 갈등 해결
    "갈등을 해결했던 경험을 말씀해주세요.": {
        "intent": "갈등 관리 + 소통 능력",
        "star_focus": "A (행동) 65%, R (결과) 25%",
        "tip": "1:1 대화 + 공통점 찾기 강조",
        "example_star": "S: 세대 다른 팀원 / T: 의견 차이 해소 / A: 1:1 대화→공통점 찾기 / R: 팀 화합, 프로젝트 성공"
    },
    # 리더십
    "리더십을 발휘한 경험을 말씀해주세요.": {
        "intent": "리더십 + 책임감",
        "star_focus": "A (행동) 60%, R (결과) 30%",
        "tip": "역할 분담과 동기 부여 과정 강조",
        "example_star": "S: 동아리 회장, 20명 관리 / T: 행사 한달 준비 / A: 역할분담+주2회 회의 / R: 참여율 95%, 성공적 행사"
    },
    # 상황대처 질문
    "기내에서 승객이 쓰러지면 어떻게 하시겠습니까?": {
        "intent": "위기 대처 + 안전 의식",
        "star_focus": "A (행동) 70%, T 20%",
        "tip": "안전 절차 + 팀 협력 + 침착함 강조",
        "example_star": "T: 승객 응급상황 / A: 1)상황 파악 2)기장 보고 3)응급처치 4)의료진 호출 / R: 침착한 대응으로 안전 확보"
    },
    "승객이 무리한 요구를 하면 어떻게 대응하시겠습니까?": {
        "intent": "원칙 vs 유연성 균형",
        "star_focus": "A (행동) 65%, R (결과) 25%",
        "tip": "공감 → 대안 제시 → 원칙 설명",
        "example_star": "S: 편의점 아르바이트, 신분증 없이 술 구매 요청 / T: 규정 준수 + 불편 최소화 / A: 정중히 규정 설명→대안 음료 추천 / R: 손님 이해, 감사 인사"
    },
    # 스트레스 관리
    "스트레스를 어떻게 관리하시나요?": {
        "intent": "자기 관리 능력",
        "star_focus": "A (행동) 60%, R (결과) 30%",
        "tip": "구체적인 루틴 + 실제 효과",
        "example_star": "S: 시험+아르바이트 병행 / T: 체력 한계 / A: 운동 루틴+수면시간 확보 / R: 스트레스 50% 감소"
    },
    # 강점/약점
    "본인의 강점과 약점을 말씀해주세요.": {
        "intent": "자기 인식 + 성장 가능성",
        "star_focus": "A (구체적 사례) 50%, R (개선 노력) 40%",
        "tip": "강점은 사례로 증명, 약점은 개선 노력과 함께 언급",
        "example_star": "S: 팀 프로젝트 경험 / T: 역할 분담 필요 / A: 소통으로 조율 (강점), 완벽주의→우선순위 정하기 (약점 개선) / R: 효율 30% 향상"
    },
    # 승무원 자질
    "승무원에게 가장 중요한 자질은 무엇이라고 생각하시나요?": {
        "intent": "직무 이해도 + 가치관",
        "star_focus": "T (자질 정의) 40%, A (본인 사례) 40%, R 20%",
        "tip": "안전/서비스/팀워크 중 하나 + 본인 경험 연결",
        "example_star": "T: 안전 의식이 가장 중요 / A: 카페 근무 중 위생 교육 철저 / R: 1년간 무사고"
    },
    # 서비스 철학
    "본인만의 서비스 철학이 있다면 말씀해주세요.": {
        "intent": "서비스 마인드 + 차별화",
        "star_focus": "T (철학) 30%, A (실천 사례) 50%, R 20%",
        "tip": "한 문장 철학 + 실제 적용 경험",
        "example_star": "T: '기대 이상의 한 걸음' / A: 손님 생일 기억→깜짝 서비스 / R: 5점 리뷰 + 단골 확보"
    },
    # 목표
    "이 직업을 통해 이루고 싶은 목표는 무엇인가요?": {
        "intent": "비전 + 성장 의지",
        "star_focus": "T (목표) 40%, A (준비 과정) 40%, R (기대 결과) 20%",
        "tip": "단기 목표(3년) + 장기 목표(10년) 구분",
        "example_star": "T: 3년 내 국제선 전문성, 10년 후 트레이너 / A: 영어 공부, 서비스 경험 / R: 후배 양성 기여"
    },
    # 서비스 감동 경험
    "서비스업에서 감동을 받았던 경험이 있나요?": {
        "intent": "서비스 감수성 + 적용 의지",
        "star_focus": "S (상황) 30%, A (인상 깊었던 점) 40%, R (본인 적용) 30%",
        "tip": "구체적 장면 묘사 + 왜 감동받았는지 + 본인 서비스에 적용 방법",
        "example_star": "S: 호텔 체크인 중 / A: 직원이 이름 기억하며 환영 / R: 나도 단골 손님 이름 외우기 실천"
    },
    # 예상치 못한 상황 대처
    "예상치 못한 상황에 대처한 경험을 말씀해주세요.": {
        "intent": "순발력 + 침착함",
        "star_focus": "A (행동) 60%, R (결과) 30%",
        "tip": "갑작스러운 상황 + 빠른 판단 + 대응 과정",
        "example_star": "S: 행사 당일 MC 불참 / T: 30분 내 대체 필요 / A: 직접 대본 숙지→진행 / R: 행사 성공, 칭찬"
    },
    # 다문화 환경
    "다문화 환경에서 소통한 경험이 있나요?": {
        "intent": "글로벌 역량 + 소통 능력",
        "star_focus": "S (상황) 30%, A (소통 방법) 50%, R 20%",
        "tip": "언어 장벽 극복 + 문화 이해 노력",
        "example_star": "S: 외국인 관광객 응대 / T: 언어 소통 어려움 / A: 번역앱+제스처+친절한 태도 / R: 감사 인사와 팁"
    },
    # 규정 vs 고객 만족
    "규정을 지키면서 고객을 만족시킨 경험이 있나요?": {
        "intent": "원칙 + 유연성 균형",
        "star_focus": "A (대처 방법) 60%, R (결과) 30%",
        "tip": "규정 설명 + 대안 제시로 만족 이끌어냄",
        "example_star": "S: 환불 규정 밖 요청 / T: 규정 지키며 만족 / A: 정중히 설명→포인트 적립 제안 / R: 고객 이해, 재방문"
    },
    # 10년 후
    "10년 후 본인의 모습은 어떨 것 같나요?": {
        "intent": "비전 + 회사 기여 의지",
        "star_focus": "T (목표) 40%, A (계획) 40%, R 20%",
        "tip": "단계별 목표 + 회사와 함께 성장 강조",
        "example_star": "T: 10년 후 선임 승무원으로 후배 양성 / A: 꾸준한 자기계발+리더십 경험 / R: 항공사 대표 서비스인"
    },
    # 직업의 어려움
    "이 직업의 어려운 점은 무엇이라고 생각하시나요?": {
        "intent": "현실 인식 + 극복 의지",
        "star_focus": "T (어려움 인식) 30%, A (대비 방법) 50%, R 20%",
        "tip": "솔직한 인정 + 구체적인 대비책",
        "example_star": "T: 불규칙한 생활 패턴 / A: 수면 관리 루틴+체력 운동 / R: 컨디션 유지 자신"
    },
    # 체력 관리
    "체력 관리는 어떻게 하고 계신가요?": {
        "intent": "자기 관리 능력",
        "star_focus": "A (관리 방법) 60%, R (효과) 30%",
        "tip": "구체적 운동 루틴 + 실제 효과",
        "example_star": "A: 주 3회 수영+매일 스트레칭 / R: 1년간 감기 없음, 활력 유지"
    },
    # 외국어
    "외국어 능력은 어느 정도이며, 어떻게 준비하셨나요?": {
        "intent": "글로벌 역량 + 자기계발",
        "star_focus": "S (현재 수준) 30%, A (학습 방법) 50%, R 20%",
        "tip": "객관적 수준 + 구체적 학습법 + 활용 계획",
        "example_star": "S: 토익 850, 회화 중급 / A: 매일 30분 쉐도잉+주 1회 화상영어 / R: 외국인 응대 자신감"
    },
    # 불규칙 근무
    "불규칙한 근무에 대해 어떻게 생각하시나요?": {
        "intent": "직무 이해 + 적응력",
        "star_focus": "T (인식) 30%, A (대비) 50%, R 20%",
        "tip": "현실 인정 + 적응 경험/계획",
        "example_star": "T: 가족과 일정 맞추기 어려움 인지 / A: 미리 가족과 소통+개인 루틴 유지 / R: 아르바이트 교대근무 성공 경험"
    },
    # 동료 의견 충돌
    "동료와 의견 충돌이 생기면 어떻게 하시겠습니까?": {
        "intent": "갈등 관리 + 협업",
        "star_focus": "A (대처 방법) 65%, R 25%",
        "tip": "경청 → 공통점 찾기 → 합의 도출",
        "example_star": "T: 발표 방식 의견 충돌 / A: 상대 의견 경청→장단점 비교→절충안 / R: 둘 다 만족, 좋은 결과"
    },
    # 기본 힌트 (매칭 안 되는 질문용)
    "_default": {
        "intent": "면접관은 구체성과 진정성을 평가합니다",
        "star_focus": "S 20%, T 20%, A 40%, R 20%",
        "tip": "구체적인 상황 + 본인의 행동 + 결과와 배움을 중심으로 답변",
        "example_star": "S: 구체적 상황(언제, 어디서) / T: 해결할 과제 / A: 본인이 취한 행동 / R: 결과와 배운 점"
    }
}

# STAR 기법 짧은 예시 (연습모드 참고용)
STAR_QUICK_EXAMPLES = [
    {"역량": "시간 관리", "hint": "S:시험 3과목 동시 준비 T:일주일 안에 A+ A:우선순위표+매일 6시간 R:전과목 A+"},
    {"역량": "서비스 마인드", "hint": "S:카페 단골 손님 T:취향 기억 A:주문 기록+맞춤 추천 R:단골 3배 증가"},
    {"역량": "융통성", "hint": "S:행사 당일 비 T:실외 불가 A:즉시 실내 확보+프로그램 수정 R:만족도 4.8/5"},
    {"역량": "위기 대처", "hint": "S:발표 당일 노트북 고장 T:10분 내 복구 불가 A:종이 자료+구두 발표 R:교수 칭찬, A+"},
    {"역량": "인내심", "hint": "S:클레임 고객 30분 응대 T:화 진정 A:경청+공감+해결책 R:사과 받음, 5점 리뷰"},
    {"역량": "적응력", "hint": "S:새 아르바이트 첫날 T:빠른 습득 A:메모+선배 질문+복습 R:1주일 만에 독립 근무"},
    {"역량": "책임감", "hint": "S:팀 프로젝트 리더 T:팀원 1명 중도 포기 A:업무 재분배+격려 R:기한 내 완료, A학점"},
]

QUESTION_CATEGORIES = {
    "common": "기본 질문",
    "experience": "경험 질문",
    "situational": "상황 대처",
    "personality": "인성 질문"
}

# 항공사별 핵심가치 요약 (UI 표시용)
AIRLINE_VALUE_SUMMARY = {
    "대한항공": "KE Way: Beyond Excellence, Journey Together, Better Tomorrow | 인재상: 진취성, 국제감각, 서비스정신, 성실, 팀워크",
    "아시아나항공": "Beautiful People | 핵심가치: 안전, 서비스, 지속가능성 | ESG: Better flight, Better tomorrow",
    "제주항공": "Fun & Fly | 7C 정신 | 핵심가치: 안전, 저비용, 신뢰, 팀워크, 도전",
    "진에어": "Fly, better fly | 4 Core Values: Safety, Practicality, Customer Service, Delight | 5 JINISM: JINIABLE, JINIFUL, JINIVELY, JINISH, JINIQUE",
    "티웨이항공": "I want T'way | 5S: Safety, Smart, Satisfaction, Sharing, Sustainability",
    "에어부산": "FLY SMART | 핵심가치: 안전운항, 산업안전, 정보보안 | 고객가치: 안전, 편리한 서비스, 실용적인 가격",
    "에어서울": "It's mint time | 최고안전, 행복서비스, 신뢰",
    "이스타항공": "Fly with EASTAR | 항공여행 대중화, 사회공익, 글로벌 국민항공사",
    "에어로케이": "새로운 하늘길 | 도전정신, 유연성, 성장지향",
    "에어프레미아": "Premium for all | HSC (Hybrid Service Carrier) | 프리미엄 서비스, 글로벌역량",
    "파라타항공": "Fly new | 핵심가치: 안전과 정시성, 투명함, 쾌적함, 고객가치 최우선 | 인재상: 신뢰 구축, 변화 적응력, 도전",
}

# =====================
# 세션 상태 초기화
# =====================

defaults = {
    "mock_started": False,
    "mock_questions": [],
    "mock_current_idx": 0,
    "mock_answers": [],
    "mock_transcriptions": [],
    "mock_times": [],
    "mock_voice_analyses": [],
    "mock_content_analyses": [],
    "mock_completed": False,
    "mock_airline": "",
    "mock_mode": "text",  # text / voice
    "mock_evaluation": None,
    "answer_start_time": None,
    "timer_running": False,
    "recorded_audio": None,
    "video_generated": False,
    "current_video_url": None,
    # 음성 분석용 추가 변수
    "mock_audio_bytes_list": [],  # 각 질문별 음성 데이터 저장
    "mock_combined_voice_analysis": None,  # 종합 음성 분석 결과
    "mock_processed_audio_hash": None,  # 오디오 중복 처리 방지
    "mock_response_times": [],  # 각 질문별 응답 시간
    # Phase 1: 감정 분석용 변수
    "mock_emotion_analyses": [],  # 각 질문별 감정 분석 결과
    "mock_combined_emotion": None,  # 종합 감정 분석
    "mock_confidence_timeline": [],  # 자신감 변화 추이
    # 고도화된 음성 분석 결과
    "mock_advanced_analyses": [],  # 각 질문별 고도화 음성 분석 결과
    "mock_stress_timeline": [],  # 스트레스 변화 추이
    # Phase B1: 면접 강화 기능
    "mock_interviewer_type": "neutral",  # 면접관 유형
    "mock_enhanced_analyses": [],  # 강화된 분석 결과 (키워드, 시간 관리)
    "mock_follow_up_questions": [],  # 꼬리질문 목록
    "mock_keyword_scores": [],  # 키워드 점수 목록
    # 통합: 연습모드 / 실전 시뮬레이션 모드
    "mock_interview_mode": "practice",  # practice / simulation
}

# 세션 상태 안전 초기화 (safe_api 사용 시)
if SAFE_API_AVAILABLE:
    init_session_state(st.session_state, defaults)
else:
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# 리스트 타입 세션 상태 None 체크 (안전성 강화)
list_keys = ["mock_questions", "mock_answers", "mock_transcriptions", "mock_times",
             "mock_voice_analyses", "mock_content_analyses", "mock_audio_bytes_list",
             "mock_response_times", "mock_emotion_analyses", "mock_confidence_timeline",
             "mock_advanced_analyses", "mock_stress_timeline"]
for key in list_keys:
    if st.session_state.get(key) is None:
        st.session_state[key] = []

# =====================
# 자소서 기반 질문 모드 처리
# =====================

# 자소서기반질문 페이지에서 넘어왔는지 확인
if st.session_state.get("from_resume_questions", False):
    resume_questions = st.session_state.get("resume_based_questions", [])
    resume_airline = st.session_state.get("resume_based_airline", "")

    if resume_questions and resume_airline:
        # 자소서 기반 질문 모드로 세션 설정
        st.session_state["resume_question_mode"] = True
        st.session_state["resume_question_list"] = resume_questions
        st.session_state["resume_question_airline"] = resume_airline

        # 플래그 초기화 (중복 방지)
        st.session_state["from_resume_questions"] = False
        st.session_state["resume_based_questions"] = []
        st.session_state["resume_based_airline"] = ""

        # 알림 표시
        st.toast(f"자소서 기반 {len(resume_questions)}개 질문으로 모의면접을 시작합니다!", icon="📝")

# 자소서 기반 질문 모드 초기화 (없으면)
if "resume_question_mode" not in st.session_state:
    st.session_state["resume_question_mode"] = False
if "resume_question_list" not in st.session_state:
    st.session_state["resume_question_list"] = []
if "resume_question_airline" not in st.session_state:
    st.session_state["resume_question_airline"] = ""


# =====================
# 헬퍼 함수
# =====================

def get_api_key():
    return os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or ""


def generate_questions(airline: str, count: int = 6) -> list:
    """면접 질문 생성 - 항공사별 맞춤 질문 사용"""
    # 항공사별 맞춤 질문 모듈이 있으면 사용
    if AIRLINE_QUESTIONS_AVAILABLE:
        return get_airline_questions_fresh(airline, count)

    # 폴백: 기존 공통 질문 사용
    questions = []

    if count <= 4:
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 1))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 1))
    elif count <= 6:
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 1))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["personality"], 1))
    else:
        questions.extend(random.sample(INTERVIEW_QUESTIONS["common"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["experience"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["situational"], 2))
        questions.extend(random.sample(INTERVIEW_QUESTIONS["personality"], 2))

    random.shuffle(questions)
    return questions[:count]


def evaluate_interview_combined(
    airline: str,
    questions: list,
    answers: list,
    times: list,
    voice_analyses: list,
    content_analyses: list,
) -> dict:
    """음성 + 내용 종합 평가"""
    api_key = get_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    # 각 질문별 점수 요약
    qa_summary = ""
    total_voice_score = 0
    total_content_score = 0

    for i, (q, a, t) in enumerate(zip(questions, answers, times), 1):
        voice = voice_analyses[i-1] if i-1 < len(voice_analyses) else {}
        content = content_analyses[i-1] if i-1 < len(content_analyses) else {}

        voice_score = voice.get("total_score", 0)
        content_score = content.get("total_score", 0)
        total_voice_score += voice_score
        total_content_score += content_score

        qa_summary += f"\n### 질문 {i}: {q}\n"
        qa_summary += f"- 답변 (소요시간: {t}초): {a[:200]}...\n" if len(a) > 200 else f"- 답변 (소요시간: {t}초): {a}\n"
        qa_summary += f"- 음성 점수: {voice_score}/100\n"
        qa_summary += f"- 내용 점수: {content_score}/100\n"

    avg_voice = total_voice_score // max(len(questions), 1)
    avg_content = total_content_score // max(len(questions), 1)

    # 항공사별 평가 기준 추가
    airline_criteria = ""
    if AIRLINE_QUESTIONS_AVAILABLE and airline in AIRLINE_VALUES:
        values = AIRLINE_VALUES[airline]
        인재상 = values.get("인재상", [])
        keywords = values.get("keywords", [])
        if 인재상:
            airline_criteria = f"\n\n이 항공사의 인재상: {', '.join(인재상)}"
        if keywords:
            airline_criteria += f"\n핵심 키워드: {', '.join(keywords)}"

    system_prompt = f"""당신은 엄격한 항공사 면접관입니다.
음성 평가와 내용 평가를 종합하여 최종 피드백을 제공하세요.
해당 항공사의 인재상과 핵심가치에 맞는지도 평가해주세요.{airline_criteria}
한국어로 상세하게 작성하세요."""

    user_prompt = f"""## 지원 항공사: {airline}

## 면접 내용 및 개별 평가
{qa_summary}

## 평균 점수
- 음성 평균: {avg_voice}/100
- 내용 평균: {avg_content}/100
- 종합 점수: {(avg_voice + avg_content) // 2}/100

## 종합 평가를 작성해주세요

### 출력 형식

#### 종합 점수: X/100

#### 음성 전달력 총평
(말 속도, 필러 단어, 발음 등)

#### 답변 내용 총평
(구체성, STAR 구조, 논리성 등)

#### 가장 잘한 점 (2-3개)
- ...

#### 반드시 개선해야 할 점 (3-4개)
- ...

#### {airline} 인재상 부합도
(해당 항공사의 인재상/핵심가치와 얼마나 맞는지 평가)

#### 합격 가능성
(솔직하게)

#### 다음 연습 때 집중할 것
(구체적인 액션 아이템)"""

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": LLM_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 1500,
        }

        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=60)

        # 401 오류 처리 (API 키 문제)
        if r.status_code == 401:
            return {
                "error": "API 인증 오류 (401): API 키를 확인해주세요.",
                "avg_voice": avg_voice,
                "avg_content": avg_content,
                "api_error": True
            }

        # 429 오류 처리 (Rate limit)
        if r.status_code == 429:
            return {
                "error": "API 요청 한도 초과 (429): 잠시 후 다시 시도해주세요.",
                "avg_voice": avg_voice,
                "avg_content": avg_content,
                "api_error": True
            }

        r.raise_for_status()
        resp = r.json()

        choices = resp.get("choices", [])
        if choices:
            return {
                "result": choices[0].get("message", {}).get("content", "").strip(),
                "avg_voice": avg_voice,
                "avg_content": avg_content,
            }
        return {"error": "평가 생성 실패", "avg_voice": avg_voice, "avg_content": avg_content}

    except requests.exceptions.Timeout:
        return {"error": "API 요청 시간 초과: 다시 시도해주세요.", "avg_voice": avg_voice, "avg_content": avg_content}
    except requests.exceptions.RequestException as e:
        return {"error": f"API 연결 오류: {str(e)}", "avg_voice": avg_voice, "avg_content": avg_content}
    except Exception as e:
        return {"error": str(e), "avg_voice": avg_voice, "avg_content": avg_content}


# =====================
# UI
# =====================

st.markdown("---")

# Page description already handled by init_page

# D-ID API 상태 확인
did_available = VIDEO_UTILS_AVAILABLE and check_did_api_available() if VIDEO_UTILS_AVAILABLE else False

if not st.session_state.mock_started:
    # =====================
    # 면접 설정 화면
    # =====================
    st.subheader("면접 설정")

    # 모드 선택 (연습 / 실전 시뮬레이션)
    st.markdown("**면접 모드 선택**")
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        practice_selected = st.button(
            "📚 연습 모드",
            use_container_width=True,
            type="primary" if st.session_state.get("_temp_mode", "practice") == "practice" else "secondary",
            help="STAR 기법 힌트와 답변 가이드가 함께 표시됩니다"
        )
        if practice_selected:
            st.session_state["_temp_mode"] = "practice"
    with mode_col2:
        simulation_selected = st.button(
            "🎯 실전 시뮬레이션",
            use_container_width=True,
            type="primary" if st.session_state.get("_temp_mode", "practice") == "simulation" else "secondary",
            help="실제 면접처럼 힌트 없이 진행됩니다"
        )
        if simulation_selected:
            st.session_state["_temp_mode"] = "simulation"

    # 선택된 모드 표시
    selected_mode = st.session_state.get("_temp_mode", "practice")
    if selected_mode == "practice":
        st.info("📚 **연습 모드**: STAR 기법 힌트, 면접관 질문 의도, 예시 답변 구조가 옆에 표시됩니다.")
    else:
        st.warning("🎯 **실전 시뮬레이션**: 실제 면접처럼 힌트 없이 진행됩니다. 긴장감을 갖고 연습하세요!")

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        airline = st.selectbox("지원 항공사", AIRLINES_WITH_RESUME)
        airline_type = AIRLINE_TYPE.get(airline, "LCC")

    with col2:
        question_count = st.slider("질문 개수", 4, 8, 6)

    with col3:
        answer_mode = st.radio(
            "답변 방식",
            ["음성 녹음 (추천)", "텍스트 입력"],
            index=0,  # 기본값: 음성 녹음
            help="실제 면접처럼 말로 연습하면 효과 2배!"
        )
        if answer_mode == "음성 녹음 (추천)":
            st.caption("실제 면접처럼 말하면서 연습해요!")

    # Phase B1: 면접관 캐릭터 선택
    if INTERVIEW_ENHANCER_AVAILABLE:
        st.markdown("---")
        st.markdown("**면접관 스타일 선택**")
        interviewer_options = {
            "warm": "온화한 면접관 (김민지 팀장) - 격려하고 장점을 찾아줌",
            "neutral": "정석 면접관 (박서연 부장) - 표준적인 면접 진행",
            "sharp": "분석 면접관 (이정훈 상무) - 답변을 깊이 분석",
            "pressure": "압박 면접관 (최현우 전무) - 한계를 테스트",
        }

        # 한국어 표시용 매핑 (뉘앙스 포함)
        interviewer_labels = {
            "warm": "온화형 - 격려하며 장점 발견",
            "neutral": "정석형 - 표준적인 면접 진행",
            "sharp": "분석형 - 답변을 깊이 분석",
            "pressure": "압박형 - 한계를 테스트",
        }

        col_int1, col_int2 = st.columns([1, 2])
        with col_int1:
            interviewer_type = st.selectbox(
                "면접관 유형",
                list(interviewer_options.keys()),
                format_func=lambda x: interviewer_labels.get(x, x),
                index=1,  # 기본: 중립
                help="면접관 스타일에 따라 꼬리질문 빈도와 피드백 스타일이 달라집니다"
            )
        with col_int2:
            selected_char = get_interviewer_character(interviewer_type)
            st.info(f"**{selected_char.name}** - {selected_char.personality}")
            st.caption(f"압박 수준: {'★' * selected_char.pressure_level}{'☆' * (10 - selected_char.pressure_level)} | 꼬리질문 빈도: {int(selected_char.follow_up_tendency * 100)}%")
    else:
        interviewer_type = "neutral"

    # Phase 2: 웹캠 분석 옵션
    # 항공사 핵심가치 표시
    if airline in AIRLINE_VALUE_SUMMARY:
        st.info(f"**{airline} 핵심가치**\n\n{AIRLINE_VALUE_SUMMARY[airline]}")

    st.divider()

    # 안내 박스
    if answer_mode == "음성 녹음 (추천)":
        st.info("""
        **음성 모의면접 안내**
        1. AI 면접관이 질문을 읽어줍니다
        2. 마이크로 답변을 녹음합니다
        3. 음성 분석: 말 속도, 필러 단어, 발음 등 평가
        4. 내용 분석: STAR 구조, 구체성, 논리성 평가
        5. 종합 피드백: 음성 + 내용 통합 평가
        """)
    else:
        st.info("""
        **텍스트 모의면접 안내**
        1. 질문을 읽고 답변을 작성하세요
        2. 내용 분석: STAR 구조, 구체성, 논리성 평가
        3. 답변을 완료하면 AI가 피드백을 제공합니다
        """)

    # 남은 사용량 표시

    # 자소서 기반 질문 모드 표시
    if st.session_state.get("resume_question_mode", False):
        resume_q_list = st.session_state.get("resume_question_list", [])
        resume_q_airline = st.session_state.get("resume_question_airline", "")

        st.success(f"📝 **자소서 기반 질문 모드** - {len(resume_q_list)}개 질문이 준비되었습니다!")

        with st.expander("자소서 기반 질문 목록 미리보기", expanded=False):
            for i, q in enumerate(resume_q_list, 1):
                q_text = q.get("question", "") if isinstance(q, dict) else q
                st.markdown(f"**{i}.** {q_text[:80]}...")

        # 항공사가 지정되어 있으면 자동 선택
        if resume_q_airline and resume_q_airline != airline:
            st.info(f"자소서 분석 시 선택한 항공사: **{resume_q_airline}** (위에서 변경 가능)")

        # 일반 모드로 전환 옵션
        if st.button("일반 모드로 전환 (자소서 질문 취소)", type="secondary"):
            st.session_state["resume_question_mode"] = False
            st.session_state["resume_question_list"] = []
            st.session_state["resume_question_airline"] = ""
            st.rerun()

    # 시작 버튼
    start_btn_label = "자소서 질문으로 모의면접 시작" if st.session_state.get("resume_question_mode") else "모의면접 시작"
    if st.button(start_btn_label, type="primary", use_container_width=True):
        # 사용량 체크

        st.session_state.mock_started = True

        # 자소서 기반 질문 모드인 경우
        if st.session_state.get("resume_question_mode", False):
            resume_q_list = st.session_state.get("resume_question_list", [])
            # 질문 텍스트만 추출
            st.session_state.mock_questions = [
                q.get("question", "") if isinstance(q, dict) else q
                for q in resume_q_list
            ]
            # 자소서 질문 모드 플래그 리셋 (다음 시작 시 일반 모드)
            st.session_state["resume_question_mode"] = False
            st.session_state["resume_question_list"] = []
        else:
            # 일반 모드: 질문 생성
            st.session_state.mock_questions = generate_questions(airline, question_count)
        st.session_state.mock_current_idx = 0
        st.session_state.mock_answers = []
        st.session_state.mock_transcriptions = []
        st.session_state.mock_times = []
        st.session_state.mock_voice_analyses = []
        st.session_state.mock_content_analyses = []
        st.session_state.mock_completed = False
        st.session_state.mock_airline = airline
        st.session_state.mock_mode = "voice" if answer_mode == "음성 녹음 (추천)" else "text"
        st.session_state.mock_evaluation = None
        st.session_state.answer_start_time = None
        st.session_state.timer_running = False
        st.session_state.recorded_audio = None
        # 음성 분석용 변수 초기화
        st.session_state.mock_audio_bytes_list = []
        st.session_state.mock_combined_voice_analysis = None
        st.session_state.mock_processed_audio_hash = None
        st.session_state.mock_response_times = []
        # 감정/고도화 분석 초기화
        st.session_state.mock_emotion_analyses = []
        st.session_state.mock_advanced_analyses = []
        st.session_state.mock_confidence_timeline = []
        st.session_state.mock_stress_timeline = []
        # Phase B1: 면접 강화 기능 초기화
        st.session_state.mock_interviewer_type = interviewer_type
        st.session_state.mock_enhanced_analyses = []
        st.session_state.mock_follow_up_questions = []
        st.session_state.mock_keyword_scores = []
        # 면접 모드 저장 (연습 / 실전 시뮬레이션)
        st.session_state.mock_interview_mode = st.session_state.get("_temp_mode", "practice")
        st.rerun()


elif not st.session_state.mock_completed:
    # =====================
    # 면접 진행 화면
    # =====================
    current_idx = st.session_state.mock_current_idx
    total = len(st.session_state.mock_questions)
    question = st.session_state.mock_questions[current_idx]
    airline = st.session_state.mock_airline
    airline_type = AIRLINE_TYPE.get(airline, "LCC")

    # 진행률
    st.progress((current_idx) / total)

    # 현재 면접 모드 확인
    interview_mode = st.session_state.get("mock_interview_mode", "practice")
    is_practice_mode = (interview_mode == "practice")

    col1, col2 = st.columns([3, 1])
    with col1:
        mode_label = "📚 연습" if is_practice_mode else "🎯 실전"
        st.subheader(f"질문 {current_idx + 1} / {total} [{mode_label}]")
    with col2:
        if st.button("면접 중단"):
            st.session_state.mock_started = False
            st.session_state.timer_running = False
            st.rerun()

    # =====================
    # 연습모드: 힌트 패널 + 질문 영역 (2컬럼)
    # 실전모드: 질문 영역만 (힌트 없음)
    # =====================
    if is_practice_mode:
        # 연습모드: 좌측 질문, 우측 힌트
        main_col, hint_col = st.columns([2, 1])
    else:
        # 실전모드: 질문만
        main_col = st.container()
        hint_col = None

    with main_col:
        # 면접관 표시 영역
        st.markdown("---")

        # 면접관 아바타/영상
        if did_available:
            # D-ID API로 실제 영상 면접관 생성
            with st.spinner("면접관 영상 생성 중..."):
                try:
                    video_result = create_interviewer_video(
                        question=question,
                        interviewer_type="female_professional",
                        airline_type="FSC" if airline in ["대한항공", "아시아나항공"] else "LCC"
                    )
                    if video_result and video_result.get("video_url"):
                        st.markdown(get_video_html(video_result["video_url"], width=400, autoplay=True), unsafe_allow_html=True)
                        st.caption("🎥 AI 영상 면접관이 질문합니다")
                    else:
                        # D-ID 실패 시 향상된 폴백 아바타
                        st.markdown(get_enhanced_fallback_avatar_html(question, "interviewer", "neutral"), unsafe_allow_html=True)
                except Exception as e:
                    # 오류 시에도 향상된 폴백 아바타 표시
                    st.markdown(get_enhanced_fallback_avatar_html(question, "interviewer", "neutral"), unsafe_allow_html=True)
        else:
            # D-ID 미설정 시 향상된 폴백 아바타 (CSS 애니메이션)
            st.markdown(get_enhanced_fallback_avatar_html(question, "interviewer", "neutral"), unsafe_allow_html=True)

        # TTS로 질문 읽기 (옵션)
        if st.session_state.mock_mode == "voice" and VIDEO_UTILS_AVAILABLE:
            if st.button("질문 다시 듣기"):
                with st.spinner("음성 생성 중..."):
                    audio_bytes = generate_tts_audio(question, voice="alloy", speed=0.85)
                    if audio_bytes:
                        get_loud_audio_component(audio_bytes, autoplay=True, gain=5.0)

        st.markdown("---")

    # =====================
    # 연습모드: 힌트 패널 표시
    # =====================
    if is_practice_mode and hint_col is not None:
        with hint_col:
            st.markdown("### 📚 STAR 기법 힌트")

            # 질문에 맞는 힌트 찾기
            hint = STAR_HINTS.get(question, STAR_HINTS.get("_default", {}))

            # 면접관 질문 의도
            st.markdown(f"**🎯 면접관 의도**")
            st.caption(hint.get("intent", "구체성과 진정성을 봅니다"))

            # STAR 강조점
            st.markdown(f"**⭐ STAR 비중**")
            st.caption(hint.get("star_focus", "S 20%, T 20%, A 40%, R 20%"))

            # 핵심 팁
            st.markdown(f"**💡 핵심 팁**")
            st.info(hint.get("tip", "숫자로 증명 + 배운 점 마무리"))

            # 예시 구조
            with st.expander("📝 예시 STAR 구조", expanded=False):
                example = hint.get("example_star", "S: 상황 / T: 과제 / A: 행동 / R: 결과")
                for part in example.split(" / "):
                    st.caption(f"• {part}")

            st.divider()

            # 빠른 참고 예시
            st.markdown("**🚀 빠른 참고**")
            sample_examples = random.sample(STAR_QUICK_EXAMPLES, min(2, len(STAR_QUICK_EXAMPLES)))
            for ex in sample_examples:
                with st.expander(f"{ex['역량']}", expanded=False):
                    st.caption(ex['hint'])

    # =====================
    # 답변 입력 영역
    # =====================

    if st.session_state.mock_mode == "voice":
        # 음성 녹음 모드
        st.subheader("음성으로 답변하세요")

        # 타이머 시작 (음성 모드에서도 시간 측정)
        if st.session_state.answer_start_time is None:
            st.session_state.answer_start_time = time.time()

        # 경과 시간 표시
        elapsed_display = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 0
        timer_color = "#28a745" if elapsed_display < 60 else "#ffc107" if elapsed_display < 90 else "#dc3545"
        st.markdown(f"""
        <div style="text-align: center; margin: 15px 0;">
            <div style="font-size: 36px; font-weight: bold; color: {timer_color};">
                {elapsed_display // 60:02d}:{elapsed_display % 60:02d}
            </div>
            <div style="font-size: 12px; color: #666;">적정 답변 시간: 60~90초</div>
        </div>
        """, unsafe_allow_html=True)

        # 음성 녹음 (st.audio_input 사용 - 롤플레잉과 동일)
        col_rec1, col_rec2 = st.columns([2, 1])

        with col_rec1:
            try:
                # 처리된 오디오 해시 추적 (중복 처리 방지)
                if "mock_processed_audio_hash" not in st.session_state:
                    st.session_state.mock_processed_audio_hash = None

                audio_data = st.audio_input("녹음 버튼을 클릭하고 답변하세요", key=f"voice_input_{current_idx}")

                if audio_data:
                    # 음성 데이터 먼저 읽기
                    audio_bytes = audio_data.read()

                    # 해시 기반 중복 체크 (더 정확함)
                    if SAFE_API_AVAILABLE:
                        audio_hash = get_audio_hash(audio_bytes)
                    else:
                        import hashlib
                        audio_hash = hashlib.md5(audio_bytes).hexdigest()

                    if audio_hash != st.session_state.mock_processed_audio_hash:
                        with st.spinner("음성 인식 중..."):

                            # STT (음성 → 텍스트)
                            result = transcribe_audio(audio_bytes, language="ko")

                            if result and result.get("text"):
                                transcribed_text = result["text"]
                                st.success(f"인식됨: {transcribed_text[:100]}{'...' if len(transcribed_text) > 100 else ''}")

                                # 응답 시간 계산
                                elapsed = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 60

                                # 음성 데이터 저장 (종합 분석용)
                                st.session_state.mock_audio_bytes_list.append(audio_bytes)
                                st.session_state.mock_response_times.append(elapsed)

                                # 개별 음성 분석
                                try:
                                    voice_analysis = analyze_voice_quality(result, expected_duration_range=(30, 90))
                                except Exception as e:
                                    voice_analysis = {"total_score": 70, "error": str(e)}

                                # 내용 분석
                                if VIDEO_UTILS_AVAILABLE:
                                    content_analysis = evaluate_answer_content(
                                        question, transcribed_text, airline, airline_type
                                    )
                                else:
                                    content_analysis = {"total_score": 0, "error": "분석 불가"}

                                # 고도화된 음성 분석 (감정 + 말속도 + 필러 + 에너지 등)
                                try:
                                    advanced_analysis = analyze_voice_advanced(
                                        audio_bytes=audio_bytes,
                                        transcribed_text=transcribed_text,
                                        question_context=question,
                                        audio_duration=float(elapsed) if elapsed else 60.0
                                    )
                                    st.session_state.mock_advanced_analyses.append(advanced_analysis)

                                    # 기존 감정 분석과의 호환성을 위해 감정 정보도 저장
                                    emotion_data = advanced_analysis.get("emotion", {})
                                    st.session_state.mock_emotion_analyses.append(emotion_data)
                                    st.session_state.mock_confidence_timeline.append(emotion_data.get("confidence_score", 5.0))
                                    st.session_state.mock_stress_timeline.append(emotion_data.get("stress_level", 5.0))
                                except Exception as e:
                                    # 분석 실패해도 면접 진행에는 영향 없음
                                    default_advanced = {
                                        "emotion": {"confidence_score": 5.0, "stress_level": 5.0, "engagement_level": 5.0, "emotion_stability": 5.0, "primary_emotion": "neutral", "emotion_description": "분석 대기", "suggestions": []},
                                        "speech_rate": {"wpm": 0, "rating": "분석불가", "feedback": ""},
                                        "filler_analysis": {"total_count": 0, "rating": "분석불가", "feedback": ""},
                                        "pause_analysis": {"rating": "분석불가", "feedback": ""},
                                        "energy_analysis": {"energy_trend": "유지", "feedback": ""},
                                        "pronunciation": {"clarity_score": 50, "feedback": ""},
                                        "structure_analysis": {"star_score": 50, "feedback": ""},
                                        "overall": {"voice_score": 50, "strengths": [], "improvements": ["분석 중 오류가 발생했습니다."], "detailed_feedback": ""}
                                    }
                                    st.session_state.mock_advanced_analyses.append(default_advanced)
                                    st.session_state.mock_emotion_analyses.append(default_advanced["emotion"])
                                    st.session_state.mock_confidence_timeline.append(5.0)
                                    st.session_state.mock_stress_timeline.append(5.0)

                                # Phase B1: 강화된 분석 수행
                                enhanced_analysis = None
                                follow_up = None
                                if INTERVIEW_ENHANCER_AVAILABLE:
                                    try:
                                        interviewer_type = st.session_state.get("mock_interviewer_type", "neutral")
                                        enhanced_analysis = analyze_interview_answer(
                                            question=question,
                                            answer=transcribed_text,
                                            elapsed_seconds=elapsed,
                                            airline=airline,
                                            interviewer_type=interviewer_type
                                        )
                                        st.session_state.mock_enhanced_analyses.append(enhanced_analysis)
                                        st.session_state.mock_keyword_scores.append(
                                            enhanced_analysis.get("keyword_analysis", {}).get("keyword_score", 0)
                                        )
                                        # 꼬리질문 저장
                                        if enhanced_analysis.get("should_follow_up") and enhanced_analysis.get("follow_up"):
                                            st.session_state.mock_follow_up_questions.append({
                                                "question_idx": current_idx,
                                                "follow_up": enhanced_analysis["follow_up"]
                                            })
                                    except Exception as e:
                                        st.session_state.mock_enhanced_analyses.append({"error": str(e)})
                                        st.session_state.mock_keyword_scores.append(0)

                                # 세션에 저장
                                st.session_state.mock_answers.append(transcribed_text)
                                st.session_state.mock_transcriptions.append(result)
                                st.session_state.mock_times.append(elapsed)
                                st.session_state.mock_voice_analyses.append(voice_analysis)
                                st.session_state.mock_content_analyses.append(content_analysis)

                                # 처리 완료 표시 (해시 저장)
                                st.session_state.mock_processed_audio_hash = audio_hash
                                st.session_state.answer_start_time = None  # 타이머 리셋

                                # 다음 질문으로
                                if current_idx + 1 >= total:
                                    st.session_state.mock_completed = True
                                else:
                                    st.session_state.mock_current_idx += 1
                                    st.session_state.mock_processed_audio_hash = None  # 다음 질문용 리셋

                                st.rerun()
                            else:
                                st.error("음성 인식 실패 - 다시 녹음하거나 아래 텍스트로 입력하세요")
                                st.session_state.mock_processed_audio_hash = audio_hash
            except Exception as e:
                st.warning(f"음성 입력 기능을 사용할 수 없습니다: {e}")

        with col_rec2:
            st.markdown("""
            **녹음 팁**
            - 마이크 아이콘 클릭 후 답변 후 정지
            - 조용한 환경에서 녹음
            - 60~90초 내 답변 권장
            """)

        st.divider()

        # 텍스트 폴백 (음성 인식 실패 시)
        with st.expander("텍스트로 직접 입력하기"):
            fallback_answer = st.text_area(
                "음성 인식이 안 될 경우 여기에 입력하세요",
                height=150,
                key=f"fallback_{current_idx}"
            )

            if st.button("텍스트 답변 제출", type="secondary", use_container_width=True):
                if fallback_answer.strip():
                    elapsed = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 60

                    # 텍스트 모드는 음성 분석 없음
                    voice_analysis = {"total_score": 0, "note": "텍스트 입력 (음성 분석 없음)"}

                    # 내용 분석
                    if VIDEO_UTILS_AVAILABLE:
                        with st.spinner("답변 분석 중..."):
                            content_analysis = evaluate_answer_content(
                                question, fallback_answer.strip(), airline, airline_type
                            )
                    else:
                        content_analysis = {"total_score": 0, "error": "분석 불가"}

                    # Phase B1: 강화된 분석 수행
                    if INTERVIEW_ENHANCER_AVAILABLE:
                        try:
                            interviewer_type = st.session_state.get("mock_interviewer_type", "neutral")
                            enhanced_analysis = analyze_interview_answer(
                                question=question,
                                answer=fallback_answer.strip(),
                                elapsed_seconds=elapsed,
                                airline=airline,
                                interviewer_type=interviewer_type
                            )
                            st.session_state.mock_enhanced_analyses.append(enhanced_analysis)
                            st.session_state.mock_keyword_scores.append(
                                enhanced_analysis.get("keyword_analysis", {}).get("keyword_score", 0)
                            )
                            if enhanced_analysis.get("should_follow_up") and enhanced_analysis.get("follow_up"):
                                st.session_state.mock_follow_up_questions.append({
                                    "question_idx": current_idx,
                                    "follow_up": enhanced_analysis["follow_up"]
                                })
                        except Exception as e:
                            st.session_state.mock_enhanced_analyses.append({"error": str(e)})
                            st.session_state.mock_keyword_scores.append(0)
                    else:
                        st.session_state.mock_enhanced_analyses.append({})
                        st.session_state.mock_keyword_scores.append(0)

                    st.session_state.mock_answers.append(fallback_answer.strip())
                    st.session_state.mock_times.append(elapsed)
                    st.session_state.mock_voice_analyses.append(voice_analysis)
                    st.session_state.mock_content_analyses.append(content_analysis)
                    # 텍스트 모드는 음성/감정 분석 없음 - 빈 데이터 추가
                    st.session_state.mock_advanced_analyses.append({
                        "overall": {"voice_score": 0, "strengths": [], "improvements": []},
                        "speech_rate": {}, "filler_analysis": {}, "energy_analysis": {},
                        "pronunciation": {}, "structure_analysis": {}
                    })
                    st.session_state.mock_emotion_analyses.append({
                        "confidence_score": 5.0, "stress_level": 5.0,
                        "engagement_level": 5.0, "emotion_stability": 5.0,
                        "primary_emotion": "neutral"
                    })
                    st.session_state.mock_confidence_timeline.append(5.0)
                    st.session_state.mock_stress_timeline.append(5.0)
                    st.session_state.answer_start_time = None

                    if current_idx + 1 >= total:
                        st.session_state.mock_completed = True
                    else:
                        st.session_state.mock_current_idx += 1

                    st.rerun()
                else:
                    st.warning("답변을 입력해주세요.")

        # 패스 버튼
        st.divider()
        if st.button("이 질문 패스", use_container_width=True):
            st.session_state.mock_answers.append("[답변 못함]")
            st.session_state.mock_times.append(0)
            st.session_state.mock_voice_analyses.append({"total_score": 0, "skipped": True})
            st.session_state.mock_content_analyses.append({"total_score": 0, "skipped": True})
            # 패스 시 기본 분석 데이터 추가
            st.session_state.mock_advanced_analyses.append({
                "overall": {"voice_score": 0, "strengths": [], "improvements": ["질문을 패스했습니다"]},
                "speech_rate": {}, "filler_analysis": {}, "energy_analysis": {},
                "pronunciation": {}, "structure_analysis": {}
            })
            st.session_state.mock_emotion_analyses.append({
                "confidence_score": 5.0, "stress_level": 5.0,
                "engagement_level": 5.0, "emotion_stability": 5.0,
                "primary_emotion": "neutral"
            })
            st.session_state.mock_confidence_timeline.append(5.0)
            st.session_state.mock_stress_timeline.append(5.0)
            # Phase B1: 강화 분석 빈 데이터 추가
            st.session_state.mock_enhanced_analyses.append({"skipped": True})
            st.session_state.mock_keyword_scores.append(0)
            st.session_state.answer_start_time = None

            if current_idx + 1 >= total:
                st.session_state.mock_completed = True
            else:
                st.session_state.mock_current_idx += 1

            st.rerun()

    else:
        # 텍스트 입력 모드 (타이머 없이 바로 입력)
        # 답변 시작 시간 자동 기록 (첫 로드 시)
        if st.session_state.answer_start_time is None:
            st.session_state.answer_start_time = time.time()

        answer = st.text_area(
            "답변을 입력하세요",
            height=200,
            key=f"answer_{current_idx}",
            placeholder="실제 면접에서 말하듯이 작성해주세요..."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("답변 제출", type="primary", disabled=not answer.strip(), use_container_width=True):
                elapsed = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 0

                # 내용 분석
                if VIDEO_UTILS_AVAILABLE:
                    with st.spinner("답변 분석 중..."):
                        content_analysis = evaluate_answer_content(
                            question, answer.strip(), airline, airline_type
                        )
                else:
                    content_analysis = {"total_score": 0}

                # Phase B1: 강화된 분석 수행
                if INTERVIEW_ENHANCER_AVAILABLE:
                    try:
                        interviewer_type = st.session_state.get("mock_interviewer_type", "neutral")
                        enhanced_analysis = analyze_interview_answer(
                            question=question,
                            answer=answer.strip(),
                            elapsed_seconds=elapsed,
                            airline=airline,
                            interviewer_type=interviewer_type
                        )
                        st.session_state.mock_enhanced_analyses.append(enhanced_analysis)
                        st.session_state.mock_keyword_scores.append(
                            enhanced_analysis.get("keyword_analysis", {}).get("keyword_score", 0)
                        )
                        if enhanced_analysis.get("should_follow_up") and enhanced_analysis.get("follow_up"):
                            st.session_state.mock_follow_up_questions.append({
                                "question_idx": current_idx,
                                "follow_up": enhanced_analysis["follow_up"]
                            })
                    except Exception as e:
                        st.session_state.mock_enhanced_analyses.append({"error": str(e)})
                        st.session_state.mock_keyword_scores.append(0)
                else:
                    st.session_state.mock_enhanced_analyses.append({})
                    st.session_state.mock_keyword_scores.append(0)

                st.session_state.mock_answers.append(answer.strip())
                st.session_state.mock_times.append(elapsed)
                st.session_state.mock_voice_analyses.append({})  # 텍스트 모드는 음성 분석 없음
                st.session_state.mock_content_analyses.append(content_analysis)
                # 텍스트 모드는 고도화 음성/감정 분석 없음 - 빈 데이터 추가
                st.session_state.mock_advanced_analyses.append({
                    "overall": {"voice_score": 0, "strengths": [], "improvements": []},
                    "speech_rate": {}, "filler_analysis": {}, "energy_analysis": {},
                    "pronunciation": {}, "structure_analysis": {}
                })
                st.session_state.mock_emotion_analyses.append({
                    "confidence_score": 5.0, "stress_level": 5.0,
                    "engagement_level": 5.0, "emotion_stability": 5.0,
                    "primary_emotion": "neutral"
                })
                st.session_state.mock_confidence_timeline.append(5.0)
                st.session_state.mock_stress_timeline.append(5.0)
                st.session_state.timer_running = False
                st.session_state.answer_start_time = None

                if current_idx + 1 >= total:
                    st.session_state.mock_completed = True
                else:
                    st.session_state.mock_current_idx += 1

                st.rerun()

        with col2:
            if st.button("패스 (답변 못함)", use_container_width=True):
                elapsed = int(time.time() - st.session_state.answer_start_time) if st.session_state.answer_start_time else 0
                st.session_state.mock_answers.append("[답변 못함]")
                st.session_state.mock_times.append(elapsed)
                st.session_state.mock_voice_analyses.append({"total_score": 0, "skipped": True})
                st.session_state.mock_content_analyses.append({"total_score": 0, "skipped": True})
                # 패스 시 기본 분석 데이터 추가
                st.session_state.mock_advanced_analyses.append({
                    "overall": {"voice_score": 0, "strengths": [], "improvements": ["질문을 패스했습니다"]},
                    "speech_rate": {}, "filler_analysis": {}, "energy_analysis": {},
                    "pronunciation": {}, "structure_analysis": {}
                })
                st.session_state.mock_emotion_analyses.append({
                    "confidence_score": 5.0, "stress_level": 5.0,
                    "engagement_level": 5.0, "emotion_stability": 5.0,
                    "primary_emotion": "neutral"
                })
                st.session_state.mock_confidence_timeline.append(5.0)
                st.session_state.mock_stress_timeline.append(5.0)
                # Phase B1: 강화 분석 빈 데이터 추가
                st.session_state.mock_enhanced_analyses.append({"skipped": True})
                st.session_state.mock_keyword_scores.append(0)
                st.session_state.timer_running = False
                st.session_state.answer_start_time = None

                if current_idx + 1 >= total:
                    st.session_state.mock_completed = True
                else:
                    st.session_state.mock_current_idx += 1

                st.rerun()


else:
    # =====================
    # 면접 완료 - 종합 평가
    # =====================
    st.subheader("모의면접 완료")

    st.markdown(f"**지원 항공사:** {st.session_state.mock_airline}")
    st.markdown(f"**답변 방식:** {'음성' if st.session_state.mock_mode == 'voice' else '텍스트'}")
    st.markdown(f"**총 질문 수:** {len(st.session_state.mock_questions)}개")

    total_time = sum(st.session_state.mock_times)
    st.markdown(f"**총 소요 시간:** {total_time // 60}분 {total_time % 60}초")

    # 종합 음성 분석 수행 (음성 모드이고, 음성 데이터가 있는 경우)
    if st.session_state.mock_mode == "voice" and st.session_state.mock_audio_bytes_list and VIDEO_UTILS_AVAILABLE:
        if st.session_state.mock_combined_voice_analysis is None:
            try:
                with st.spinner("종합 음성 분석 중..."):
                    # 모든 음성 데이터 합쳐서 분석
                    combined_audio = b''.join(st.session_state.mock_audio_bytes_list)
                    voice_result = analyze_voice_complete(
                        combined_audio,
                        response_times=st.session_state.mock_response_times
                    )
                    st.session_state.mock_combined_voice_analysis = voice_result
            except Exception as e:
                st.session_state.mock_combined_voice_analysis = {"error": str(e)}

    # Phase B1: 면접관 정보 표시
    if INTERVIEW_ENHANCER_AVAILABLE and st.session_state.get("mock_interviewer_type"):
        interviewer = get_interviewer_character(st.session_state.mock_interviewer_type)
        st.info(f"**면접관:** {interviewer.name} ({st.session_state.mock_interviewer_type.upper()}) - {interviewer.personality}")

    st.divider()

    # 질문별 결과 탭 (Phase B1: 키워드 분석 탭 추가)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 질문별 분석", "🎤 음성 평가", "💭 감정 분석", "🔑 키워드 분석", "📊 종합 평가"])

    with tab1:
        for i, (q, a, t) in enumerate(zip(
            st.session_state.mock_questions,
            st.session_state.mock_answers,
            st.session_state.mock_times
        ), 1):
            content = st.session_state.mock_content_analyses[i-1] if i-1 < len(st.session_state.mock_content_analyses) else {}

            with st.expander(f"Q{i}. {q[:50]}...", expanded=False):
                st.markdown(f"**답변:** {a}")
                st.caption(f"소요 시간: {t}초")

                if content and "total_score" in content:
                    st.markdown(f"**내용 점수:** {content.get('total_score', 0)}/100")

                    # STAR 체크
                    star = content.get("star_check", {})
                    if star:
                        cols = st.columns(4)
                        for j, (key, label) in enumerate([
                            ("situation", "S"), ("task", "T"), ("action", "A"), ("result", "R")
                        ]):
                            with cols[j]:
                                if star.get(key):
                                    st.success(f" {label}")
                                else:
                                    st.error(f" {label}")

                    # 개선점
                    improvements = content.get("improvements", [])
                    if improvements:
                        st.markdown("**개선점:**")
                        for imp in improvements:
                            st.markdown(f"- {imp}")

    with tab2:
        if st.session_state.mock_mode == "voice":
            # 종합 음성 분석 결과 표시
            voice_analysis = st.session_state.mock_combined_voice_analysis

            if voice_analysis and "error" not in voice_analysis:
                # 종합 점수 표시
                total_score = voice_analysis.get("total_score", 0)
                grade = voice_analysis.get("grade", "N/A")

                grade_colors = {"S": "#FFD700", "A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#F44336"}
                grade_color = grade_colors.get(grade, "#666")

                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #1e3a5f, #2d5a87); border-radius: 15px; margin-bottom: 20px;">
                    <div style="font-size: 48px; font-weight: bold; color: {grade_color};">{grade}</div>
                    <div style="font-size: 24px; color: #fff;">{total_score}/100점</div>
                    <div style="font-size: 14px; color: #ccc; margin-top: 10px;">{voice_analysis.get('summary', '')}</div>
                </div>
                """, unsafe_allow_html=True)

                # 텍스트 분석 (말 속도, 필러, 휴지, 발음)
                st.subheader("텍스트 분석")
                text_analysis = voice_analysis.get("text_analysis", {})

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    rate = text_analysis.get("speech_rate", {})
                    st.metric("말 속도", f"{rate.get('wpm', 0)} WPM", help="적정: 120-150 WPM")
                    st.progress(min(rate.get("score", 0) / 10, 1.0))
                    st.caption(rate.get("feedback", ""))

                with col2:
                    filler = text_analysis.get("filler_words", {})
                    st.metric("필러 단어", f"{filler.get('count', 0)}개", help="음, 어, 그 등")
                    st.progress(min(filler.get("score", 0) / 10, 1.0))
                    st.caption(filler.get("feedback", ""))

                with col3:
                    pauses = text_analysis.get("pauses", {})
                    st.metric("긴 휴지", f"{pauses.get('long_pauses', 0)}회", help="2초 이상 멈춤")
                    st.progress(min(pauses.get("score", 0) / 10, 1.0))
                    st.caption(pauses.get("feedback", ""))

                with col4:
                    clarity = text_analysis.get("clarity", {})
                    st.metric("발음 명확도", f"{clarity.get('score', 0)}/10")
                    st.progress(min(clarity.get("score", 0) / 10, 1.0))
                    st.caption(clarity.get("feedback", ""))

                st.divider()

                # 음성 분석 (떨림, 말끝, 억양, 서비스톤)
                st.subheader("음성 전달력 분석")
                voice_detail = voice_analysis.get("voice_analysis", {})

                col1, col2 = st.columns(2)

                with col1:
                    tremor = voice_detail.get("tremor", {})
                    st.markdown(f"**목소리 떨림**: {tremor.get('level', 'N/A')}")
                    st.progress(min(tremor.get("score", 0) / 10, 1.0))
                    st.caption(tremor.get("feedback", ""))

                    pitch = voice_detail.get("pitch_variation", {})
                    st.markdown(f"**억양 변화**: {pitch.get('type', 'N/A')}")
                    st.progress(min(pitch.get("score", 0) / 10, 1.0))
                    st.caption(pitch.get("feedback", ""))

                with col2:
                    ending = voice_detail.get("ending_clarity", {})
                    st.markdown(f"**말끝 처리**: {ending.get('issue', 'N/A')}")
                    st.progress(min(ending.get("score", 0) / 10, 1.0))
                    st.caption(ending.get("feedback", ""))

                    service = voice_detail.get("service_tone", {})
                    st.markdown(f"**서비스 톤**: {'밝음' if service.get('greeting_bright') else '개선 필요'}")
                    st.progress(min(service.get("score", 0) / 10, 1.0))
                    st.caption(service.get("feedback", ""))

                # 응답 시간 분석
                rt_analysis = voice_analysis.get("response_time_analysis", {})
                if rt_analysis:
                    st.divider()
                    st.subheader("응답 시간 분석")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("평균 응답 시간", f"{rt_analysis.get('avg_time', 0):.1f}초")
                    with col2:
                        st.metric("응답 시간 점수", f"{rt_analysis.get('score', 0)}/10")
                    with col3:
                        st.caption(rt_analysis.get("feedback", ""))

                # 개선 포인트
                improvements = voice_analysis.get("top_improvements", [])
                if improvements:
                    st.divider()
                    st.subheader("우선 개선 포인트")
                    for i, imp in enumerate(improvements, 1):
                        st.markdown(f"{i}. {imp}")

            elif voice_analysis and "error" in voice_analysis:
                st.warning(f"음성 분석 오류: {voice_analysis.get('error')}")

            elif not st.session_state.mock_audio_bytes_list:
                st.info("음성 모드로 녹음한 데이터가 없습니다. 텍스트 입력을 사용한 경우 음성 분석이 제공되지 않습니다.")

            # 질문별 음성 분석 (개별)
            st.divider()
            st.subheader("질문별 음성 분석")
            for i, voice in enumerate(st.session_state.mock_voice_analyses, 1):
                if voice and voice.get("total_score", 0) > 0:
                    with st.expander(f"질문 {i} 음성 분석", expanded=False):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric("말 속도", f"{voice.get('speech_rate', {}).get('wpm', 0)} WPM")
                            st.caption(voice.get('speech_rate', {}).get('feedback', ''))

                        with col2:
                            st.metric("필러 단어", f"{voice.get('filler_words', {}).get('count', 0)}개")
                            st.caption(voice.get('filler_words', {}).get('feedback', ''))

                        with col3:
                            st.metric("음성 점수", f"{voice.get('total_score', 0)}/100")

            # Phase D1: 고도화된 음성 분석 그래프
            if VOICE_ENHANCER_AVAILABLE and st.session_state.mock_answers:
                st.divider()
                st.subheader("📊 음성 분석 그래프")

                # 전체 답변 텍스트 결합
                combined_transcript = " ".join(st.session_state.mock_answers)
                total_duration = sum(st.session_state.mock_response_times) if st.session_state.mock_response_times else 60.0

                # 말 속도 그래프 데이터
                speed_data = get_speech_speed_graph_data(combined_transcript, total_duration, "ko")

                # 말 속도 시각화
                with st.expander("🎤 말 속도 분석", expanded=True):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        # 시간대별 말 속도 그래프
                        import pandas as pd
                        if speed_data.get("timeline"):
                            speed_df = pd.DataFrame(speed_data["timeline"])
                            st.line_chart(speed_df.set_index("timestamp")["wpm"], use_container_width=True)
                            st.caption("시간대별 말 속도 변화 (WPM)")

                    with col2:
                        avg_wpm = speed_data.get("average_wpm", 0)
                        optimal = speed_data.get("optimal_range", (110, 140))
                        st.metric("평균 속도", f"{avg_wpm:.0f} WPM")
                        st.caption(f"적정 범위: {optimal[0]}-{optimal[1]} WPM")

                        if avg_wpm < optimal[0]:
                            st.warning("말 속도가 느립니다. 조금 더 빠르게 말해보세요.")
                        elif avg_wpm > optimal[1]:
                            st.warning("말 속도가 빠릅니다. 천천히 말해보세요.")
                        else:
                            st.success("적절한 말 속도입니다!")

                        # 빠른/느린 구간 표시
                        fast_segs = speed_data.get("fast_segments", [])
                        slow_segs = speed_data.get("slow_segments", [])
                        if fast_segs:
                            st.caption(f"빠른 구간: {len(fast_segs)}개")
                        if slow_segs:
                            st.caption(f"느린 구간: {len(slow_segs)}개")

                # 톤/억양 그래프 (시뮬레이션 데이터 사용)
                with st.expander("🎵 음성 톤 분석", expanded=False):
                    tone_data = get_tone_graph_data(total_duration)

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        if tone_data.get("timeline"):
                            tone_df = pd.DataFrame(tone_data["timeline"])
                            st.line_chart(tone_df.set_index("timestamp")["pitch"], use_container_width=True)
                            st.caption("시간대별 음성 톤 변화 (Hz)")

                    with col2:
                        pattern = tone_data.get("pattern", "stable")
                        pattern_names = {
                            "monotone": "단조로움",
                            "stable": "안정적",
                            "dynamic": "역동적",
                            "nervous": "긴장됨",
                            "confident": "자신감"
                        }
                        st.metric("톤 패턴", pattern_names.get(pattern, pattern))
                        st.metric("평균 피치", f"{tone_data.get('average_pitch', 0):.0f} Hz")

                        if pattern == "monotone":
                            st.info("억양에 변화를 주면 더 생동감 있게 전달됩니다.")
                        elif pattern == "nervous":
                            st.info("심호흡 후 편안하게 말해보세요.")

                # 음량 그래프 (시뮬레이션 데이터 사용)
                with st.expander("🔊 음량 분석", expanded=False):
                    volume_data = get_volume_graph_data(total_duration)

                    col1, col2 = st.columns([2, 1])

                    with col1:
                        if volume_data.get("timeline"):
                            vol_df = pd.DataFrame(volume_data["timeline"])
                            st.line_chart(vol_df.set_index("timestamp")["db"], use_container_width=True)
                            st.caption("시간대별 음량 변화 (dB)")

                    with col2:
                        level = volume_data.get("level", "optimal")
                        level_names = {
                            "too_quiet": "너무 작음",
                            "quiet": "조금 작음",
                            "optimal": "적절함",
                            "loud": "조금 큼",
                            "too_loud": "너무 큼"
                        }
                        st.metric("음량 수준", level_names.get(level, level))
                        st.metric("평균 음량", f"{volume_data.get('average_db', 0):.0f} dB")

                        if level in ["too_quiet", "quiet"]:
                            st.info("목소리를 조금 더 크게 말해보세요.")
                        elif level in ["too_loud", "loud"]:
                            st.info("면접관과의 거리를 고려해 음량을 조절하세요.")

                # 침묵/멈춤 분석
                with st.expander("⏸️ 멈춤/침묵 분석", expanded=False):
                    silence_data = get_silence_analysis(total_duration)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("침묵 비율", f"{silence_data.get('ratio', 0) * 100:.1f}%")
                        st.caption("전체 발화 대비 침묵 비율")

                    with col2:
                        st.metric("자연스러운 멈춤", f"{silence_data.get('natural_pauses', 0)}회")
                        st.metric("머뭇거림", f"{silence_data.get('hesitations', 0)}회")

                    with col3:
                        st.metric("긴 침묵", f"{silence_data.get('long_pauses', 0)}회")
                        quality = silence_data.get("quality_score", 0)
                        if quality >= 80:
                            st.success("적절한 멈춤 활용!")
                        elif quality >= 60:
                            st.info("멈춤 활용을 개선해보세요.")
                        else:
                            st.warning("긴 침묵을 줄여보세요.")

                    st.caption(silence_data.get("feedback", ""))

        else:
            st.info("텍스트 모드에서는 음성 평가가 제공되지 않습니다. 음성 모드로 면접을 진행하면 상세한 음성 분석을 받을 수 있습니다.")

    # 고도화된 음성 분석 탭 (100점짜리 UI)
    with tab3:
        st.markdown("""
        <style>
        .voice-score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            color: white;
            margin-bottom: 24px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        }
        .voice-score-number {
            font-size: 72px;
            font-weight: 800;
            line-height: 1;
            margin: 10px 0;
        }
        .voice-score-label {
            font-size: 18px;
            opacity: 0.9;
        }
        .voice-grade {
            display: inline-block;
            padding: 8px 24px;
            background: rgba(255,255,255,0.2);
            border-radius: 30px;
            font-weight: 700;
            margin-top: 10px;
        }
        .metric-card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border-left: 4px solid;
            margin-bottom: 16px;
        }
        .metric-card.speech { border-left-color: #3b82f6; }
        .metric-card.filler { border-left-color: #f59e0b; }
        .metric-card.pause { border-left-color: #8b5cf6; }
        .metric-card.energy { border-left-color: #10b981; }
        .metric-card.structure { border-left-color: #ec4899; }
        .metric-card.pronunciation { border-left-color: #06b6d4; }
        .metric-title {
            font-size: 14px;
            color: #64748b;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 28px;
            font-weight: 700;
            color: #1e293b;
        }
        .metric-rating {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 8px;
        }
        .rating-good { background: #dcfce7; color: #166534; }
        .rating-ok { background: #fef3c7; color: #92400e; }
        .rating-bad { background: #fee2e2; color: #991b1b; }
        .strength-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: #f0fdf4;
            border-radius: 10px;
            margin-bottom: 8px;
            color: #166534;
        }
        .improvement-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: #fef3c7;
            border-radius: 10px;
            margin-bottom: 8px;
            color: #92400e;
        }
        </style>
        """, unsafe_allow_html=True)

        if st.session_state.mock_mode == "voice" and st.session_state.mock_advanced_analyses:
            analyses = st.session_state.mock_advanced_analyses
            emotions = st.session_state.mock_emotion_analyses

            # 종합 점수 계산
            overall_scores = [a.get("overall", {}).get("voice_score", 50) for a in analyses]
            avg_score = sum(overall_scores) / len(overall_scores) if overall_scores else 50

            # 등급 계산
            if avg_score >= 90:
                grade = "S"
                grade_text = "최우수"
            elif avg_score >= 80:
                grade = "A"
                grade_text = "우수"
            elif avg_score >= 70:
                grade = "B"
                grade_text = "양호"
            elif avg_score >= 60:
                grade = "C"
                grade_text = "보통"
            else:
                grade = "D"
                grade_text = "개선필요"

            # ===== 상단: 종합 점수 카드 =====
            st.markdown(f"""
            <div class="voice-score-card">
                <div class="voice-score-label">종합 음성 점수</div>
                <div class="voice-score-number">{avg_score:.0f}</div>
                <div class="voice-grade">{grade} 등급 - {grade_text}</div>
            </div>
            """, unsafe_allow_html=True)

            # ===== 레이더 차트 + 감정 변화 차트 =====
            col_radar, col_trend = st.columns(2)

            with col_radar:
                st.markdown("##### 🎯 음성 역량 분석")
                try:
                    import plotly.graph_objects as go

                    # 각 항목 평균 계산
                    avg_speech = sum(a.get("speech_rate", {}).get("wpm", 120) for a in analyses) / len(analyses)
                    avg_filler = 100 - sum(a.get("filler_analysis", {}).get("filler_ratio", 0.05) * 100 * 10 for a in analyses) / len(analyses)
                    avg_pause = sum(100 - a.get("pause_analysis", {}).get("pause_ratio", 0.25) * 100 for a in analyses) / len(analyses) if analyses else 70
                    avg_energy = sum(a.get("energy_analysis", {}).get("energy_score", 70) for a in analyses) / len(analyses) if analyses else 70
                    avg_pronunciation = sum(a.get("pronunciation", {}).get("clarity_score", 70) for a in analyses) / len(analyses)
                    avg_structure = sum(a.get("structure_analysis", {}).get("star_score", 50) for a in analyses) / len(analyses)

                    # 점수 정규화 (0-100)
                    speech_score = min(100, max(0, 50 + (avg_speech - 120) * 0.5)) if avg_speech else 70
                    filler_score = max(0, min(100, avg_filler))
                    pause_score = max(0, min(100, avg_pause)) if isinstance(avg_pause, (int, float)) else 70
                    energy_score = max(0, min(100, avg_energy))
                    pronunciation_score = max(0, min(100, avg_pronunciation))
                    structure_score = max(0, min(100, avg_structure))

                    categories = ['말 속도', '명확성', '휴지 활용', '에너지', '발음', 'STAR 구조']
                    values = [speech_score, filler_score, pause_score, energy_score, pronunciation_score, structure_score]
                    values.append(values[0])  # 닫기

                    fig_radar = go.Figure()
                    fig_radar.add_trace(go.Scatterpolar(
                        r=values,
                        theta=categories + [categories[0]],
                        fill='toself',
                        fillcolor='rgba(102, 126, 234, 0.3)',
                        line=dict(color='#667eea', width=3),
                        name='음성 역량'
                    ))

                    fig_radar.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10)),
                            angularaxis=dict(tickfont=dict(size=12))
                        ),
                        showlegend=False,
                        height=320,
                        margin=dict(t=30, b=30, l=60, r=60)
                    )

                    st.plotly_chart(fig_radar, use_container_width=True)

                except ImportError:
                    st.info("Plotly가 설치되지 않아 차트를 표시할 수 없습니다.")

            with col_trend:
                st.markdown("##### 📈 감정 변화 추이")
                try:
                    import plotly.graph_objects as go

                    if emotions:
                        x_labels = [f"Q{i+1}" for i in range(len(emotions))]
                        confidence_vals = [e.get("confidence_score", 5.0) for e in emotions]
                        stress_vals = [e.get("stress_level", 5.0) for e in emotions]

                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(
                            x=x_labels, y=confidence_vals,
                            mode='lines+markers+text', name='자신감',
                            line=dict(color='#10b981', width=3),
                            marker=dict(size=12),
                            text=[f"{v:.1f}" for v in confidence_vals],
                            textposition="top center"
                        ))
                        fig_trend.add_trace(go.Scatter(
                            x=x_labels, y=stress_vals,
                            mode='lines+markers+text', name='스트레스',
                            line=dict(color='#ef4444', width=3),
                            marker=dict(size=12),
                            text=[f"{v:.1f}" for v in stress_vals],
                            textposition="bottom center"
                        ))

                        fig_trend.update_layout(
                            yaxis=dict(range=[0, 10.5], title="점수"),
                            xaxis=dict(title="질문"),
                            height=320,
                            legend=dict(orientation="h", y=1.15, x=0.5, xanchor="center"),
                            margin=dict(t=50, b=30)
                        )

                        st.plotly_chart(fig_trend, use_container_width=True)
                    else:
                        st.info("감정 데이터가 없습니다.")

                except ImportError:
                    st.info("Plotly가 설치되지 않아 차트를 표시할 수 없습니다.")

            st.divider()

            # ===== 상세 분석 카드 =====
            st.markdown("### 📊 상세 분석")

            # 첫 번째 행: 말 속도, 필러 단어, 휴지
            col1, col2, col3 = st.columns(3)

            # 평균값 계산
            avg_wpm = sum(a.get("speech_rate", {}).get("wpm", 0) for a in analyses) / len(analyses)
            total_fillers = sum(a.get("filler_analysis", {}).get("total_count", 0) for a in analyses)
            avg_filler_ratio = sum(a.get("filler_analysis", {}).get("filler_ratio", 0) for a in analyses) / len(analyses)

            speech_rating = "적절" if 100 <= avg_wpm <= 160 else ("빠름" if avg_wpm > 160 else "느림")
            filler_rating = "우수" if avg_filler_ratio < 0.03 else ("양호" if avg_filler_ratio < 0.08 else "개선필요")

            with col1:
                rating_class = "rating-good" if speech_rating == "적절" else "rating-ok"
                st.markdown(f"""
                <div class="metric-card speech">
                    <div class="metric-title">🎙️ 말 속도</div>
                    <div class="metric-value">{avg_wpm:.0f} <span style="font-size:16px;color:#64748b">WPM</span>
                        <span class="metric-rating {rating_class}">{speech_rating}</span>
                    </div>
                    <div style="color:#64748b;font-size:13px;margin-top:8px">적정 범위: 100-160 WPM</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                rating_class = "rating-good" if filler_rating == "우수" else ("rating-ok" if filler_rating == "양호" else "rating-bad")
                st.markdown(f"""
                <div class="metric-card filler">
                    <div class="metric-title">💬 필러 단어</div>
                    <div class="metric-value">{total_fillers}회
                        <span class="metric-rating {rating_class}">{filler_rating}</span>
                    </div>
                    <div style="color:#64748b;font-size:13px;margin-top:8px">비율: {avg_filler_ratio*100:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                # 에너지 트렌드
                energy_trends = [a.get("energy_analysis", {}).get("energy_trend", "유지") for a in analyses]
                trend_counts = {"상승": energy_trends.count("상승"), "유지": energy_trends.count("유지"), "하락": energy_trends.count("하락")}
                main_trend = max(trend_counts, key=trend_counts.get)
                trend_icon = "📈" if main_trend == "상승" else ("➡️" if main_trend == "유지" else "📉")
                rating_class = "rating-good" if main_trend in ["상승", "유지"] else "rating-ok"

                st.markdown(f"""
                <div class="metric-card energy">
                    <div class="metric-title">{trend_icon} 에너지 흐름</div>
                    <div class="metric-value">{main_trend}
                        <span class="metric-rating {rating_class}">{"좋음" if main_trend != "하락" else "주의"}</span>
                    </div>
                    <div style="color:#64748b;font-size:13px;margin-top:8px">답변 중 에너지 변화 패턴</div>
                </div>
                """, unsafe_allow_html=True)

            # 두 번째 행: 발음, STAR 구조, 종합
            col4, col5, col6 = st.columns(3)

            avg_clarity = sum(a.get("pronunciation", {}).get("clarity_score", 70) for a in analyses) / len(analyses)
            avg_star = sum(a.get("structure_analysis", {}).get("star_score", 50) for a in analyses) / len(analyses)

            with col4:
                clarity_rating = "우수" if avg_clarity >= 80 else ("양호" if avg_clarity >= 60 else "개선필요")
                rating_class = "rating-good" if clarity_rating == "우수" else ("rating-ok" if clarity_rating == "양호" else "rating-bad")

                st.markdown(f"""
                <div class="metric-card pronunciation">
                    <div class="metric-title">🔊 발음 명확도</div>
                    <div class="metric-value">{avg_clarity:.0f}점
                        <span class="metric-rating {rating_class}">{clarity_rating}</span>
                    </div>
                    <div style="color:#64748b;font-size:13px;margin-top:8px">음성 전달력 평가</div>
                </div>
                """, unsafe_allow_html=True)

            with col5:
                star_rating = "우수" if avg_star >= 70 else ("양호" if avg_star >= 50 else "개선필요")
                rating_class = "rating-good" if star_rating == "우수" else ("rating-ok" if star_rating == "양호" else "rating-bad")

                st.markdown(f"""
                <div class="metric-card structure">
                    <div class="metric-title">⭐ STAR 구조</div>
                    <div class="metric-value">{avg_star:.0f}점
                        <span class="metric-rating {rating_class}">{star_rating}</span>
                    </div>
                    <div style="color:#64748b;font-size:13px;margin-top:8px">상황-과제-행동-결과 구조</div>
                </div>
                """, unsafe_allow_html=True)

            with col6:
                # 감정 안정성
                if emotions:
                    avg_stability = sum(e.get("emotion_stability", 5.0) for e in emotions) / len(emotions)
                    stability_rating = "안정" if avg_stability >= 7 else ("보통" if avg_stability >= 5 else "불안정")
                    rating_class = "rating-good" if stability_rating == "안정" else ("rating-ok" if stability_rating == "보통" else "rating-bad")
                else:
                    avg_stability = 5.0
                    stability_rating = "보통"
                    rating_class = "rating-ok"

                st.markdown(f"""
                <div class="metric-card pause">
                    <div class="metric-title">🧘 감정 안정성</div>
                    <div class="metric-value">{avg_stability:.1f}/10
                        <span class="metric-rating {rating_class}">{stability_rating}</span>
                    </div>
                    <div style="color:#64748b;font-size:13px;margin-top:8px">면접 중 심리 상태</div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # ===== 강점 & 개선점 =====
            st.markdown("### 💪 강점 & 개선점")

            col_strength, col_improve = st.columns(2)

            # 모든 분석에서 강점/개선점 수집
            all_strengths = []
            all_improvements = []
            for a in analyses:
                overall = a.get("overall", {})
                all_strengths.extend(overall.get("strengths", []))
                all_improvements.extend(overall.get("improvements", []))

            # 중복 제거
            unique_strengths = list(dict.fromkeys(all_strengths))[:5]
            unique_improvements = list(dict.fromkeys(all_improvements))[:5]

            with col_strength:
                st.markdown("##### ✅ 잘한 점")
                if unique_strengths:
                    for s in unique_strengths:
                        st.markdown(f"""<div class="strength-item">✓ {s}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="strength-item">✓ 면접에 참여해주셔서 감사합니다</div>""", unsafe_allow_html=True)

            with col_improve:
                st.markdown("##### ⚠️ 개선할 점")
                if unique_improvements:
                    for i in unique_improvements:
                        st.markdown(f"""<div class="improvement-item">→ {i}</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class="improvement-item">→ 더 많은 연습으로 완성도를 높여보세요</div>""", unsafe_allow_html=True)

            st.divider()

            # ===== 질문별 상세 분석 =====
            st.markdown("### 🔍 질문별 상세 분석")

            for i, (analysis, emotion) in enumerate(zip(analyses, emotions), 1):
                voice_score = analysis.get("overall", {}).get("voice_score", 50)
                speech = analysis.get("speech_rate", {})
                filler = analysis.get("filler_analysis", {})
                energy = analysis.get("energy_analysis", {})
                structure = analysis.get("structure_analysis", {})
                primary_emotion = emotion.get("primary_emotion", "neutral")

                # 감정 아이콘
                emotion_icons = {
                    "neutral": "😐", "confident": "💪", "nervous": "😰",
                    "calm": "😌", "excited": "🤩", "stressed": "😓",
                    "happy": "😊", "focused": "🎯", "enthusiastic": "🔥"
                }
                icon = emotion_icons.get(primary_emotion, "❓")

                with st.expander(f"Q{i}: {icon} 음성 점수 {voice_score:.0f}점 | {primary_emotion.upper()}", expanded=False):
                    q_col1, q_col2, q_col3, q_col4 = st.columns(4)

                    with q_col1:
                        st.metric("말 속도", f"{speech.get('wpm', 0):.0f} WPM", delta=speech.get('rating', ''))
                    with q_col2:
                        st.metric("필러 단어", f"{filler.get('total_count', 0)}회", delta=filler.get('rating', ''))
                    with q_col3:
                        st.metric("에너지", energy.get('energy_trend', '유지'))
                    with q_col4:
                        st.metric("STAR 점수", f"{structure.get('star_score', 0):.0f}점")

                    # 피드백
                    st.markdown("---")
                    st.markdown("**💡 피드백:**")
                    st.markdown(f"- 말 속도: {speech.get('feedback', '분석 중')}")
                    st.markdown(f"- 필러: {filler.get('feedback', '분석 중')}")
                    st.markdown(f"- 구조: {structure.get('feedback', '분석 중')}")

            # Phase D2: 감정 분석 고도화 (자신감/긴장도 타임라인)
            if EMOTION_ENHANCER_AVAILABLE and st.session_state.mock_response_times:
                st.divider()
                st.markdown("### 📊 감정 분석 타임라인")

                total_duration = sum(st.session_state.mock_response_times)
                import pandas as pd

                # 자신감/긴장도 타임라인 데이터
                conf_timeline = get_confidence_timeline(total_duration)
                stress_timeline = get_stress_timeline(total_duration)

                # 자신감 타임라인 그래프
                with st.expander("💪 자신감 변화", expanded=True):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        conf_df = pd.DataFrame({
                            'timestamp': conf_timeline['timestamps'],
                            'confidence': conf_timeline['values']
                        })
                        st.line_chart(conf_df.set_index('timestamp')['confidence'], use_container_width=True)
                        st.caption("시간대별 자신감 변화")

                    with col2:
                        conf_score = conf_timeline['overall_score']
                        conf_level = conf_timeline['level']
                        level_names = {
                            "very_low": "매우 낮음", "low": "낮음",
                            "moderate": "보통", "high": "높음", "very_high": "매우 높음"
                        }
                        st.metric("자신감 점수", f"{conf_score:.0f}/100")
                        st.metric("수준", level_names.get(conf_level, conf_level))
                        st.metric("추세", {"improving": "상승 ↑", "declining": "하락 ↓", "stable": "안정 →", "fluctuating": "변동 ↕"}.get(conf_timeline['trend'], "-"))

                    st.info(conf_timeline['feedback'])

                # 긴장도 타임라인 그래프
                with st.expander("😰 긴장도 변화", expanded=False):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        stress_df = pd.DataFrame({
                            'timestamp': stress_timeline['timestamps'],
                            'stress': stress_timeline['values']
                        })
                        st.line_chart(stress_df.set_index('timestamp')['stress'], use_container_width=True)
                        st.caption("시간대별 긴장도 변화 (낮을수록 좋음)")

                    with col2:
                        stress_score = stress_timeline['overall_score']
                        stress_level = stress_timeline['level']
                        level_names = {
                            "relaxed": "매우 편안", "calm": "편안",
                            "slight": "약간 긴장", "moderate": "보통",
                            "high": "높음", "very_high": "매우 높음"
                        }
                        st.metric("긴장도", f"{stress_score:.0f}/100")
                        st.metric("수준", level_names.get(stress_level, stress_level))

                        if stress_timeline['peak_time']:
                            st.metric("피크 시점", f"{stress_timeline['peak_time']:.0f}초")

                    st.info(stress_timeline['feedback'])

                # 구간별 피드백
                with st.expander("📋 구간별 상세 피드백", expanded=False):
                    segments = get_segment_analysis(total_duration)

                    for i, seg in enumerate(segments, 1):
                        seg_names = {1: "초반", 2: "중반", 3: "후반"}
                        seg_name = seg_names.get(i, f"{i}구간")

                        st.markdown(f"**{seg_name}** ({seg['start']:.0f}~{seg['end']:.0f}초)")

                        scol1, scol2, scol3 = st.columns(3)
                        with scol1:
                            st.metric("자신감", f"{seg['confidence']:.0f}")
                        with scol2:
                            st.metric("긴장도", f"{seg['stress']:.0f}")
                        with scol3:
                            emotion_kr = {
                                "neutral": "중립", "confident": "자신감",
                                "nervous": "긴장", "calm": "차분",
                                "anxious": "불안", "enthusiastic": "열정",
                                "hesitant": "주저"
                            }
                            st.metric("감정", emotion_kr.get(seg['emotion'], seg['emotion']))

                        st.caption(seg['feedback'])
                        if seg.get('suggestions'):
                            for sug in seg['suggestions']:
                                st.caption(f"💡 {sug}")
                        st.markdown("---")

        else:
            st.info("음성 모드로 면접을 진행하면 상세한 음성 분석 결과를 확인할 수 있습니다. 텍스트 모드에서는 음성 분석이 제공되지 않습니다.")

    # Phase B1: 키워드 분석 탭
    with tab4:
        st.markdown("""
        <style>
        .keyword-card {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            color: white;
            margin-bottom: 20px;
            box-shadow: 0 8px 32px rgba(240, 147, 251, 0.3);
        }
        .keyword-score {
            font-size: 56px;
            font-weight: 800;
            line-height: 1;
        }
        .keyword-badge {
            display: inline-block;
            padding: 6px 16px;
            background: rgba(255,255,255,0.2);
            border-radius: 20px;
            margin: 4px;
            font-size: 14px;
        }
        .time-indicator {
            padding: 15px;
            border-radius: 12px;
            margin: 8px 0;
        }
        .time-optimal { background: #dcfce7; border-left: 4px solid #22c55e; }
        .time-short { background: #fef3c7; border-left: 4px solid #f59e0b; }
        .time-long { background: #fee2e2; border-left: 4px solid #ef4444; }
        .follow-up-card {
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 12px;
            padding: 16px;
            margin: 12px 0;
        }
        .follow-up-question {
            font-size: 16px;
            font-weight: 600;
            color: #0369a1;
        }
        </style>
        """, unsafe_allow_html=True)

        if INTERVIEW_ENHANCER_AVAILABLE and st.session_state.get("mock_enhanced_analyses"):
            enhanced_list = st.session_state.mock_enhanced_analyses
            keyword_scores = st.session_state.get("mock_keyword_scores", [])
            follow_ups = st.session_state.get("mock_follow_up_questions", [])

            # 평균 키워드 점수 계산 (패스한 질문의 0점도 포함)
            # 패스/건너뛴 질문도 0점으로 평균에 반영하여 페널티 부여
            avg_keyword_score = sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0

            # 등급 계산
            if avg_keyword_score >= 80:
                grade = "A"
                grade_text = "우수"
            elif avg_keyword_score >= 60:
                grade = "B"
                grade_text = "양호"
            elif avg_keyword_score >= 40:
                grade = "C"
                grade_text = "보통"
            else:
                grade = "D"
                grade_text = "개선필요"

            # 상단 종합 점수 카드
            st.markdown(f"""
            <div class="keyword-card">
                <div style="font-size: 16px; opacity: 0.9;">키워드 활용도</div>
                <div class="keyword-score">{avg_keyword_score:.0f}</div>
                <div style="margin-top: 10px;">
                    <span class="keyword-badge">{grade} 등급</span>
                    <span class="keyword-badge">{grade_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 면접관 정보
            interviewer_type = st.session_state.get("mock_interviewer_type", "neutral")
            interviewer = get_interviewer_character(interviewer_type)
            st.caption(f"면접관: {interviewer.name} | 압박 수준: {interviewer.pressure_level}/10")

            st.divider()

            # 질문별 키워드 분석
            st.markdown("### 🔍 질문별 키워드 분석")

            for i, (q, a, t, enhanced) in enumerate(zip(
                st.session_state.mock_questions,
                st.session_state.mock_answers,
                st.session_state.mock_times,
                enhanced_list
            ), 1):
                if enhanced.get("skipped") or enhanced.get("error"):
                    continue

                kw_analysis = enhanced.get("keyword_analysis", {})
                time_analysis = enhanced.get("time_analysis", {})
                kw_score = kw_analysis.get("keyword_score", 0)

                with st.expander(f"Q{i}. 키워드 점수: {kw_score}/100 | 시간: {t}초", expanded=False):
                    col_kw, col_time = st.columns(2)

                    with col_kw:
                        st.markdown("**키워드 분석**")

                        # STAR 구조
                        star = kw_analysis.get("star_structure", {})
                        if star:
                            star_cols = st.columns(4)
                            for j, (key, label) in enumerate([
                                ("situation", "S"), ("task", "T"), ("action", "A"), ("result", "R")
                            ]):
                                with star_cols[j]:
                                    if star.get("components", {}).get(key):
                                        st.success(f"{label}")
                                    else:
                                        st.error(f"{label}")

                        # 발견된 키워드
                        airline_kw = kw_analysis.get("airline_keywords", {}).get("found", {})
                        found_list = []
                        for cat_kws in airline_kw.values():
                            found_list.extend(cat_kws)
                        if found_list:
                            st.markdown("**사용된 키워드:**")
                            st.markdown(" ".join([f"`{kw}`" for kw in found_list[:6]]))

                        # 누락된 키워드
                        missing = kw_analysis.get("missing_keywords", [])
                        if missing:
                            st.markdown("**보완 필요:**")
                            for m in missing[:3]:
                                st.caption(f"- {m}")

                    with col_time:
                        st.markdown("**시간 관리**")
                        time_status = time_analysis.get("status", "unknown")
                        time_class = "time-optimal" if time_status == "optimal" else ("time-short" if time_status == "too_short" else "time-long")

                        status_text = {"optimal": "적절", "too_short": "너무 짧음", "too_long": "너무 김"}.get(time_status, "알 수 없음")
                        st.markdown(f"""
                        <div class="time-indicator {time_class}">
                            <strong>{status_text}</strong><br>
                            <small>{time_analysis.get('feedback', '')}</small>
                        </div>
                        """, unsafe_allow_html=True)

                        # 권장 시간 배분
                        ideal = time_analysis.get("ideal_range", (60, 90))
                        st.caption(f"권장 시간: {ideal[0]}~{ideal[1]}초")

                        # 말 속도
                        pace = time_analysis.get("pace_analysis", {})
                        if pace:
                            st.caption(f"속도: {pace.get('pace', '알 수 없음')} ({pace.get('cps', 0):.1f} 글자/초)")

            # 꼬리질문 섹션
            if follow_ups:
                st.divider()
                st.markdown("### 💬 AI 꼬리질문")
                st.caption("면접관이 추가로 물어봤을 수 있는 질문들입니다. 이 질문들에도 답변할 수 있도록 준비하세요.")

                for fu in follow_ups:
                    q_idx = fu.get("question_idx", 0)
                    fu_data = fu.get("follow_up", {})
                    original_q = st.session_state.mock_questions[q_idx] if q_idx < len(st.session_state.mock_questions) else ""

                    st.markdown(f"""
                    <div class="follow-up-card">
                        <div style="color: #64748b; font-size: 12px;">Q{q_idx + 1}에 대한 꼬리질문</div>
                        <div class="follow-up-question">{fu_data.get('follow_up_question', '')}</div>
                        <div style="margin-top: 8px; color: #64748b; font-size: 13px;">
                            목적: {fu_data.get('purpose', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    expected = fu_data.get("expected_elements", [])
                    if expected:
                        st.caption(f"답변에 포함하면 좋을 요소: {', '.join(expected)}")

            # 종합 추천
            st.divider()
            st.markdown("### 💡 키워드 활용 추천")

            all_recommendations = []
            for enhanced in enhanced_list:
                if enhanced and not enhanced.get("skipped") and not enhanced.get("error"):
                    recs = enhanced.get("keyword_analysis", {}).get("recommendations", [])
                    all_recommendations.extend(recs)

            unique_recs = list(dict.fromkeys(all_recommendations))[:5]
            if unique_recs:
                for rec in unique_recs:
                    st.markdown(f"- {rec}")
            else:
                st.success("키워드를 잘 활용하셨습니다!")

        else:
            st.info("키워드 분석 기능을 사용할 수 없거나 분석 데이터가 없습니다.")

    with tab5:
        if st.session_state.mock_evaluation is None:
            with st.spinner("종합 평가 생성 중... (최대 1분)"):
                evaluation = evaluate_interview_combined(
                    st.session_state.mock_airline,
                    st.session_state.mock_questions,
                    st.session_state.mock_answers,
                    st.session_state.mock_times,
                    st.session_state.mock_voice_analyses,
                    st.session_state.mock_content_analyses,
                )
                st.session_state.mock_evaluation = evaluation

                # 자동 점수 저장 (API 오류가 없을 때만)
                if SCORE_UTILS_AVAILABLE and "error" not in evaluation and not evaluation.get("api_error"):
                    # 평가 결과에서 점수 파싱 시도
                    if "result" in evaluation:
                        parsed = parse_evaluation_score(evaluation["result"], "모의면접")
                        total_score = parsed.get("total", 0)
                    else:
                        total_score = 0

                    # 평균 점수로 대체 (파싱 실패 시)
                    if total_score == 0 and "avg_voice" in evaluation and "avg_content" in evaluation:
                        total_score = (evaluation["avg_voice"] + evaluation["avg_content"]) // 2

                    if total_score > 0:
                        save_practice_score(
                            practice_type="모의면접",
                            total_score=total_score,
                            detailed_scores=parsed.get("detailed") if "parsed" in dir() else None,
                            scenario=f"{st.session_state.mock_airline} 모의면접 ({len(st.session_state.mock_questions)}문항)"
                        )

                        # Phase 3: 벤치마킹 점수 저장
                        if BENCHMARK_AVAILABLE:
                            try:
                                user_id = st.session_state.get("user_id", "anonymous")
                                benchmark_scores = {
                                    "음성점수": evaluation.get("avg_voice", total_score),
                                    "내용점수": evaluation.get("avg_content", total_score),
                                    "종합점수": total_score,
                                }
                                # 고도화 분석이 있으면 감정점수 추가
                                if st.session_state.mock_advanced_analyses:
                                    emotions = st.session_state.mock_emotion_analyses
                                    if emotions:
                                        avg_conf = sum(e.get("confidence_score", 5) for e in emotions) / len(emotions)
                                        benchmark_scores["감정점수"] = int(avg_conf * 10)
                                add_benchmark_score(
                                    user_id=user_id,
                                    airline=st.session_state.mock_airline,
                                    question_type="모의면접",
                                    scores=benchmark_scores,
                                    anonymous=True
                                )
                            except Exception as e:
                                pass  # 벤치마크 저장 실패해도 면접 결과에는 영향 없음

                        # 면접 히스토리 저장 (C안 - 풀 구현)
                        if HISTORY_UTILS_AVAILABLE:
                            try:
                                # 질문별 데이터 구조화
                                questions_data = []
                                for i, q in enumerate(st.session_state.mock_questions):
                                    q_data = {
                                        "index": i,
                                        "category": "common" if i == 0 else "experience",
                                        "question_text": q,
                                        "answer_text": st.session_state.mock_answers[i] if i < len(st.session_state.mock_answers) else "",
                                        "answer_duration_sec": st.session_state.mock_times[i] if i < len(st.session_state.mock_times) else 0,
                                        "voice_analysis": st.session_state.mock_voice_analyses[i] if i < len(st.session_state.mock_voice_analyses) else {},
                                        "content_analysis": st.session_state.mock_content_analyses[i] if i < len(st.session_state.mock_content_analyses) else {},
                                        "feedback": {
                                            "strengths": [],
                                            "improvements": [],
                                            "ai_comment": ""
                                        }
                                    }
                                    # content_analysis에서 피드백 추출
                                    if q_data["content_analysis"]:
                                        ca = q_data["content_analysis"]
                                        q_data["feedback"]["strengths"] = ca.get("strengths", [])
                                        q_data["feedback"]["improvements"] = ca.get("improvements", [])
                                        q_data["feedback"]["ai_comment"] = ca.get("feedback", "")
                                    questions_data.append(q_data)

                                # 세션 데이터 구성
                                session_data = {
                                    "type": "모의면접",
                                    "airline": st.session_state.mock_airline,
                                    "mode": st.session_state.mock_mode,
                                    "question_count": len(st.session_state.mock_questions),
                                    "total_duration_sec": sum(st.session_state.mock_times) if st.session_state.mock_times else 0,
                                    "scores": {
                                        "total": total_score,
                                        "voice_avg": evaluation.get("avg_voice", 0),
                                        "content_avg": evaluation.get("avg_content", 0)
                                    },
                                    "questions": questions_data,
                                    "evaluation": {
                                        "overall_feedback": evaluation.get("result", ""),
                                        "strengths": [],
                                        "weaknesses": [],
                                        "recommendations": []
                                    }
                                }

                                # 히스토리 저장
                                session_id = save_interview_session(session_data)
                                if session_id:
                                    st.session_state["_last_saved_session_id"] = session_id
                            except Exception as e:
                                pass  # 히스토리 저장 실패해도 면접 결과에는 영향 없음
            st.rerun()
        else:
            eval_result = st.session_state.mock_evaluation
            if "error" in eval_result:
                st.error(f"평가 오류: {eval_result['error']}")
            else:
                # 점수 표시
                if "avg_voice" in eval_result and "avg_content" in eval_result:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("음성 평균", f"{eval_result['avg_voice']}/100")
                    with col2:
                        st.metric("내용 평균", f"{eval_result['avg_content']}/100")
                    with col3:
                        combined = (eval_result['avg_voice'] + eval_result['avg_content']) // 2
                        st.metric("종합 점수", f"{combined}/100")

                st.markdown("---")

                # 비교 피드백 (이전 세션 대비 성장 분석)
                if COMPARISON_FEEDBACK_AVAILABLE:
                    try:
                        # 이전 피드백 컨텍스트 조회
                        prev_context = get_previous_feedback_context(
                            airline=st.session_state.mock_airline,
                            max_sessions=3
                        )

                        if prev_context.get("has_history") and prev_context.get("sessions_referenced", 0) > 0:
                            combined = (eval_result['avg_voice'] + eval_result['avg_content']) // 2

                            # 비교 피드백 생성
                            comparison_result = generate_comparison_feedback(
                                current_answer=" ".join(st.session_state.mock_answers[:3]),
                                current_score=combined,
                                previous_context=prev_context,
                            )

                            # UI 렌더링
                            comparison_html = render_comparison_feedback_ui(comparison_result)
                            if comparison_html:
                                st.markdown("### 이전 세션 대비 성장 분석")
                                st.markdown(comparison_html, unsafe_allow_html=True)
                                st.markdown("---")
                    except Exception as e:
                        pass  # 비교 피드백 실패해도 기본 평가는 표시

                st.markdown(eval_result.get("result", ""))

    # =====================
    # PDF 리포트 다운로드
    # =====================
    if REPORT_AVAILABLE:
        st.divider()
        st.subheader("리포트 다운로드")

        col_pdf1, col_pdf2 = st.columns([2, 1])
        with col_pdf1:
            st.caption("면접 결과를 PDF로 저장하여 나중에 확인하거나 멘토에게 공유할 수 있습니다.")
        with col_pdf2:
            try:
                pdf_bytes = generate_mock_interview_report(
                    airline=st.session_state.mock_airline,
                    questions=st.session_state.mock_questions,
                    answers=st.session_state.mock_answers,
                    times=st.session_state.mock_times,
                    voice_analyses=st.session_state.mock_voice_analyses,
                    content_analyses=st.session_state.mock_content_analyses,
                    combined_voice_analysis=st.session_state.mock_combined_voice_analysis,
                    evaluation_result=st.session_state.mock_evaluation,
                )
                filename = get_mock_interview_report_filename(st.session_state.mock_airline)

                st.download_button(
                    label="PDF 다운로드",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
            except Exception as e:
                st.error(f"PDF 생성 오류: {e}")

    st.divider()

    # 결과 확인 및 이동 버튼
    st.subheader("다음 단계")

    result_col1, result_col2, result_col3, result_col4 = st.columns(4)

    with result_col1:
        if st.button("다시 도전하기", type="primary", use_container_width=True):
            st.session_state.mock_started = False
            st.session_state.mock_evaluation = None
            # 음성 분석 변수도 초기화
            st.session_state.mock_audio_bytes_list = []
            st.session_state.mock_combined_voice_analysis = None
            st.session_state.mock_processed_audio_hash = None
            st.session_state.mock_response_times = []
            st.rerun()

    with result_col2:
        if st.button("처음으로", use_container_width=True):
            for key in defaults:
                st.session_state[key] = defaults[key]
            st.rerun()

    with result_col3:
        # 성장그래프로 이동 (대시보드)
        st.page_link("pages/6_성장그래프.py", label="성장그래프 보기", use_container_width=True)

    with result_col4:
        # 면접 히스토리로 이동
        st.page_link("pages/25_면접히스토리.py", label="면접 기록 보기", use_container_width=True)

    # 약점 기반 추천
    if st.session_state.mock_evaluation and "avg_content" in st.session_state.mock_evaluation:
        avg_content = st.session_state.mock_evaluation.get("avg_content", 0)
        if avg_content < 70:
            st.markdown("---")
            st.markdown("### 추천 연습")
            weak_col1, weak_col2 = st.columns(2)
            with weak_col1:
                st.warning("내용 점수가 70점 미만이에요. 자소서 기반 질문으로 연습해보세요!")
                st.page_link("pages/17_자소서기반질문.py", label="자소서 기반 질문 연습", use_container_width=True)
            with weak_col2:
                st.info("롤플레잉으로 실전 감각을 키워보세요!")
                st.page_link("pages/1_롤플레잉.py", label="롤플레잉 연습", use_container_width=True)
