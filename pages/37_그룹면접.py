# pages/37_그룹면접.py
# FlyReady Lab - 그룹 면접 (멀티플레이어 모의면접)
# Phase 5: room_manager, multiplayer_service, peer_evaluation 통합

# 정식 웹사이트 이전 안내
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redirect_to_web import show_redirect_and_stop
show_redirect_and_stop()

import streamlit as st
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# 로깅 먼저 설정
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# 사이드바 유틸리티
try:
    from sidebar_common import init_page, end_page
    SIDEBAR_AVAILABLE = True
except ImportError:
    SIDEBAR_AVAILABLE = False
    def init_page():
        pass
    def end_page():
        pass

# 안전한 실행 유틸리티
try:
    from safe_api import (
        safe_execute, validate_dict, validate_list,
        validate_room_name, validate_chat_message, validate_username,
        sanitize_user_input, escape_html
    )
    SAFE_API_AVAILABLE = True
except ImportError:
    SAFE_API_AVAILABLE = False
    def safe_execute(func, *args, default=None, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"safe_execute 실패: {e}")
            return default
    def validate_room_name(name):
        return (bool(name and len(name) >= 2), str(name)[:30] if name else "", "")
    def validate_chat_message(msg):
        return (bool(msg), str(msg)[:500] if msg else "", "")
    def validate_username(name):
        return (bool(name and len(name) >= 2), str(name)[:20] if name else "", "")
    def sanitize_user_input(text, **kwargs):
        return str(text)[:5000] if text else ""
    def escape_html(text):
        return str(text).replace("<", "&lt;").replace(">", "&gt;") if text else ""

# Phase 5 모듈 임포트 (에러 처리 포함)
ROOM_MANAGER_AVAILABLE = False
MULTIPLAYER_AVAILABLE = False
PEER_EVAL_AVAILABLE = False

try:
    from room_manager import (
        create_room, get_room, join_room, leave_room,
        list_available_rooms, update_participant_status,
        start_session, send_message, get_messages,
        ROOM_TEMPLATES, RoomType, RoomStatus, ParticipantStatus
    )
    ROOM_MANAGER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"room_manager 로드 실패: {e}")

try:
    from multiplayer_service import (
        start_group_interview, get_interview_progress,
        get_current_turn_info, get_live_leaderboard, calculate_winner,
        DEBATE_TOPICS, start_debate, get_debate_state, submit_argument,
        get_multiplayer_service, start_answer_timer, check_timer
    )
    MULTIPLAYER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"multiplayer_service 로드 실패: {e}")

try:
    from peer_evaluation import (
        submit_peer_evaluation, get_evaluation_template,
        add_reaction, REACTIONS, EVALUATION_CRITERIA,
        get_evaluations_received, get_reaction_summary
    )
    PEER_EVAL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"peer_evaluation 로드 실패: {e}")

try:
    from airline_questions import get_available_airlines
except ImportError:
    def get_available_airlines():
        return ["대한항공", "아시아나항공", "진에어", "티웨이항공"]

# ========================================
# 페이지 설정 및 CSS
# ========================================

def get_custom_css():
    """그룹 면접 전용 CSS"""
    return """
    <style>
    /* 카드 스타일 */
    .room-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .room-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        border-color: #2563eb;
    }

    /* 방 정보 헤더 */
    .room-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .room-title {
        font-size: 18px;
        font-weight: 700;
        color: #0f172a;
    }
    .room-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-interview { background: #dbeafe; color: #1d4ed8; }
    .badge-debate { background: #fef3c7; color: #d97706; }
    .badge-study { background: #d1fae5; color: #059669; }

    /* 참가자 아바타 */
    .participant-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
        margin-right: 8px;
    }
    .avatar-ready { background: #dcfce7; color: #16a34a; border: 2px solid #16a34a; }
    .avatar-not-ready { background: #fee2e2; color: #dc2626; border: 2px solid #dc2626; }
    .avatar-answering { background: #dbeafe; color: #2563eb; border: 2px solid #2563eb; animation: pulse 1.5s infinite; }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.05); opacity: 0.8; }
    }

    /* 현재 질문 카드 */
    .question-card {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        color: white;
        border-radius: 20px;
        padding: 32px;
        margin: 24px 0;
        text-align: center;
        box-shadow: 0 10px 40px rgba(37, 99, 235, 0.3);
    }
    .question-number {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 8px;
    }
    .question-text {
        font-size: 22px;
        font-weight: 600;
        line-height: 1.5;
    }

    /* 타이머 */
    .timer-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 16px;
        background: #0f172a;
        border-radius: 12px;
        margin: 16px 0;
    }
    .timer-text {
        font-size: 32px;
        font-weight: 700;
        color: #fff;
        font-family: 'JetBrains Mono', monospace;
    }
    .timer-warning { color: #fbbf24; }
    .timer-danger { color: #ef4444; animation: blink 0.5s infinite; }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* 리더보드 */
    .leaderboard {
        background: #f8fafc;
        border-radius: 16px;
        padding: 20px;
    }
    .leaderboard-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        background: white;
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid #e2e8f0;
    }
    .rank-1 { border-left: 4px solid #fbbf24; }
    .rank-2 { border-left: 4px solid #94a3b8; }
    .rank-3 { border-left: 4px solid #f97316; }
    .rank-number {
        font-size: 20px;
        font-weight: 700;
        width: 36px;
        text-align: center;
    }

    /* 채팅 패널 */
    .chat-container {
        background: #f8fafc;
        border-radius: 16px;
        padding: 16px;
        max-height: 300px;
        overflow-y: auto;
    }
    .chat-message {
        padding: 8px 12px;
        margin-bottom: 8px;
        border-radius: 8px;
        background: white;
    }
    .chat-system {
        background: #e0e7ff;
        color: #3730a3;
        text-align: center;
        font-size: 13px;
    }
    .chat-user {
        background: white;
        border: 1px solid #e2e8f0;
    }
    .chat-reaction {
        background: #fef3c7;
        font-size: 13px;
    }

    /* 반응 버튼 */
    .reaction-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        border: 2px solid #e2e8f0;
        background: white;
        font-size: 24px;
        cursor: pointer;
        transition: all 0.2s;
        margin: 4px;
    }
    .reaction-btn:hover {
        transform: scale(1.15);
        border-color: #2563eb;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* 토론 모드 */
    .debate-side {
        padding: 20px;
        border-radius: 16px;
        margin: 8px 0;
    }
    .side-pro {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
        border: 2px solid #16a34a;
    }
    .side-con {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 2px solid #dc2626;
    }
    .phase-indicator {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        background: #0f172a;
        color: white;
        font-weight: 600;
        font-size: 14px;
    }

    /* 결과 화면 */
    .winner-card {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
        color: white;
        border-radius: 24px;
        padding: 40px;
        text-align: center;
        margin: 24px 0;
    }
    .winner-trophy {
        font-size: 64px;
        margin-bottom: 16px;
    }
    .winner-name {
        font-size: 28px;
        font-weight: 700;
    }

    /* 평가 폼 */
    .evaluation-category {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .evaluation-title {
        font-weight: 600;
        font-size: 15px;
        color: #0f172a;
        margin-bottom: 8px;
    }

    /* 관전자 뷰 */
    .spectator-badge {
        background: #8b5cf6;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
    }

    /* 모바일 대응 */
    @media (max-width: 768px) {
        .question-card {
            padding: 20px;
        }
        .question-text {
            font-size: 18px;
        }
        .timer-text {
            font-size: 24px;
        }
    }
    </style>
    """


# ========================================
# 세션 상태 초기화
# ========================================

def init_session_state():
    """세션 상태 초기화"""
    defaults = {
        'user_id': None,
        'user_name': None,
        'current_room_id': None,
        'is_host': False,
        'is_spectator': False,
        'view_mode': 'browser',  # browser, waiting, in_progress, results, debate, spectator
        'last_refresh': datetime.now(),
        'auto_refresh': True,
        'show_create_dialog': False,
        'show_join_dialog': False,
        'chat_input': '',
        'answer_input': '',
        'selected_airline': '대한항공',
        'evaluation_scores': {},
        'evaluation_feedback': '',
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # 사용자 ID 자동 생성
    if not st.session_state.user_id:
        st.session_state.user_id = f"user_{str(uuid.uuid4())[:8]}"
        st.session_state.user_name = f"참가자_{st.session_state.user_id[-4:]}"


# ========================================
# 유틸리티 함수
# ========================================

def get_room_type_badge(room_type: str) -> tuple:
    """방 유형에 따른 배지 정보 반환"""
    badges = {
        'group_interview': ('그룹 면접', 'badge-interview', '👥'),
        'debate': ('토론 면접', 'badge-debate', '🎭'),
        'study_group': ('스터디 그룹', 'badge-study', '📚'),
    }
    return badges.get(room_type, ('알 수 없음', '', '❓'))


def format_time_ago(timestamp: str) -> str:
    """시간 경과 포맷팅"""
    created = datetime.fromisoformat(timestamp)
    diff = datetime.now() - created

    if diff.seconds < 60:
        return "방금 전"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60}분 전"
    elif diff.seconds < 86400:
        return f"{diff.seconds // 3600}시간 전"
    else:
        return f"{diff.days}일 전"


def format_remaining_time(seconds: int) -> str:
    """남은 시간 포맷팅"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"


# ========================================
# 1. 메인 뷰 - 방 브라우저
# ========================================

def render_room_browser():
    """방 브라우저 렌더링"""
    st.markdown("### 🏠 방 찾기")

    # 상단 액션 버튼들
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        if st.button("➕ 방 만들기", use_container_width=True, type="primary"):
            st.session_state.show_create_dialog = True
            st.rerun()

    with col2:
        if st.button("🔑 코드로 참가", use_container_width=True):
            st.session_state.show_join_dialog = True
            st.rerun()

    with col3:
        if st.button("⚡ 빠른 매칭", use_container_width=True):
            quick_match()

    with col4:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # 필터 옵션
    col_filter1, col_filter2 = st.columns(2)

    with col_filter1:
        room_type_filter = st.selectbox(
            "방 유형",
            options=['전체', '그룹 면접', '토론 면접', '스터디 그룹'],
            key="room_type_filter"
        )

    with col_filter2:
        airline_filter = st.selectbox(
            "목표 항공사",
            options=['전체'] + get_available_airlines(),
            key="airline_filter"
        )

    # 방 유형 매핑
    type_map = {
        '전체': None,
        '그룹 면접': 'group_interview',
        '토론 면접': 'debate',
        '스터디 그룹': 'study_group'
    }

    # 방 목록 조회
    filter_type = type_map.get(room_type_filter)
    available_rooms = list_available_rooms(filter_type)

    if not available_rooms:
        st.info("🔍 참가 가능한 방이 없습니다. 새 방을 만들어보세요!")
    else:
        st.markdown(f"**{len(available_rooms)}개의 방**이 열려있습니다")

        for room_info in available_rooms:
            render_room_card(room_info)


def render_room_card(room_info: Dict[str, Any]):
    """방 카드 렌더링"""
    badge_name, badge_class, badge_emoji = get_room_type_badge(room_info['room_type'])

    with st.container():
        st.markdown(f"""
        <div class="room-card">
            <div class="room-header">
                <span class="room-title">{badge_emoji} {room_info['room_name']}</span>
                <span class="room-badge {badge_class}">{badge_name}</span>
            </div>
            <div style="color: #64748b; font-size: 14px; margin-bottom: 12px;">
                👤 {room_info['current_participants']}/{room_info['max_participants']}명 ·
                🕐 {format_time_ago(room_info['created_at'])}
            </div>
            <div style="font-family: monospace; color: #94a3b8; font-size: 13px;">
                코드: <strong>{room_info['room_id']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"참가하기", key=f"join_{room_info['room_id']}", use_container_width=True):
            try:
                join_room(
                    room_info['room_id'],
                    st.session_state.user_id,
                    st.session_state.user_name
                )
                st.session_state.current_room_id = room_info['room_id']
                st.session_state.view_mode = 'waiting'
                st.rerun()
            except Exception as e:
                st.error(f"참가 실패: {str(e)}")


def quick_match():
    """빠른 매칭 - 자동으로 방 참가"""
    available = list_available_rooms()

    if not available:
        st.warning("⚠️ 참가 가능한 방이 없습니다. 새 방을 만드세요!")
        return

    # 가장 참가자가 많은 방 선택 (곧 시작될 가능성 높음)
    best_room = max(available, key=lambda x: x['current_participants'])

    try:
        join_room(
            best_room['room_id'],
            st.session_state.user_id,
            st.session_state.user_name
        )
        st.session_state.current_room_id = best_room['room_id']
        st.session_state.view_mode = 'waiting'
        st.success(f"✅ '{best_room['room_name']}' 방에 참가했습니다!")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"참가 실패: {str(e)}")


# ========================================
# 2. 방 만들기 다이얼로그
# ========================================

def render_create_room_dialog():
    """방 만들기 다이얼로그"""
    st.markdown("### ✨ 새 방 만들기")

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← 뒤로가기"):
            st.session_state.show_create_dialog = False
            st.rerun()

    st.markdown("---")

    # 방 이름
    room_name = st.text_input(
        "방 이름",
        value=f"{st.session_state.user_name}의 면접방",
        max_chars=30,
        help="다른 참가자들에게 보여질 방 이름입니다"
    )

    # 방 유형
    room_type_options = {
        '👥 그룹 면접': 'group_interview',
        '🎭 토론 면접': 'debate',
        '📚 스터디 그룹': 'study_group'
    }

    selected_type_label = st.selectbox(
        "방 유형",
        options=list(room_type_options.keys()),
        help="면접 진행 방식을 선택하세요"
    )
    room_type = room_type_options[selected_type_label]

    # 방 유형별 설명
    type_descriptions = {
        'group_interview': "AI가 출제하는 질문에 순서대로 답변합니다. 실시간 점수와 피드백을 받을 수 있어요.",
        'debate': "찬성/반대 팀으로 나뉘어 주제에 대해 토론합니다. 논리적 사고력을 키울 수 있어요.",
        'study_group': "자유롭게 토론하고 정보를 공유하는 스터디 모임입니다."
    }
    st.info(f"💡 {type_descriptions[room_type]}")

    # 항공사 선택
    target_airline = st.selectbox(
        "목표 항공사",
        options=get_available_airlines(),
        help="해당 항공사 맞춤 질문이 출제됩니다"
    )

    # 상세 설정
    col1, col2 = st.columns(2)

    with col1:
        max_participants = st.slider(
            "최대 참가자 수",
            min_value=2,
            max_value=6,
            value=4,
            help="2~6명까지 설정 가능합니다"
        )

    with col2:
        if room_type == 'group_interview':
            question_count = st.slider(
                "질문 개수",
                min_value=3,
                max_value=10,
                value=5,
                help="면접에서 출제될 질문 수"
            )
        else:
            question_count = 5

    # 답변 시간 설정
    time_limit = st.slider(
        "답변 시간 제한 (초)",
        min_value=60,
        max_value=180,
        value=120,
        step=30,
        help="각 답변의 시간 제한"
    )

    st.markdown("---")

    # 방 만들기 버튼
    if st.button("🚀 방 만들기", use_container_width=True, type="primary"):
        # 입력값 검증
        is_valid, cleaned_name, error_msg = validate_room_name(room_name)
        if not is_valid:
            st.error(error_msg or "방 이름을 입력해주세요")
            return

        try:
            settings = {
                'target_airline': target_airline,
                'question_count': question_count,
                'time_limit_per_answer': time_limit
            }

            room = create_room(
                host_id=st.session_state.user_id,
                room_name=cleaned_name,  # 검증된 이름 사용
                room_type=room_type,
                max_participants=max_participants,
                settings=settings
            )

            st.session_state.current_room_id = room['room_id']
            st.session_state.is_host = True
            st.session_state.view_mode = 'waiting'
            st.session_state.show_create_dialog = False

            st.success(f"✅ 방이 만들어졌습니다! 코드: **{room['room_id']}**")
            time.sleep(1)
            st.rerun()

        except Exception as e:
            st.error(f"방 만들기 실패: {str(e)}")


# ========================================
# 3. 코드로 참가 다이얼로그
# ========================================

def render_join_dialog():
    """코드로 참가 다이얼로그"""
    st.markdown("### 🔑 코드로 참가하기")

    col_back, _ = st.columns([1, 3])
    with col_back:
        if st.button("← 뒤로가기", key="join_back"):
            st.session_state.show_join_dialog = False
            st.rerun()

    st.markdown("---")

    room_code = st.text_input(
        "방 코드 입력",
        max_chars=6,
        placeholder="6자리 코드",
        help="친구에게 받은 방 코드를 입력하세요"
    ).upper()

    display_name = st.text_input(
        "표시 이름",
        value=st.session_state.user_name,
        max_chars=20,
        help="다른 참가자들에게 보여질 이름입니다"
    )

    if st.button("참가하기", use_container_width=True, type="primary"):
        if not room_code or len(room_code) != 6:
            st.error("6자리 방 코드를 입력해주세요")
            return

        # 이름 검증
        is_valid, cleaned_name, error_msg = validate_username(display_name)
        if not is_valid:
            st.error(error_msg or "표시 이름을 입력해주세요")
            return

        try:
            st.session_state.user_name = cleaned_name  # 검증된 이름 사용

            room = join_room(
                room_code,
                st.session_state.user_id,
                st.session_state.user_name
            )

            st.session_state.current_room_id = room_code
            st.session_state.view_mode = 'waiting'
            st.session_state.show_join_dialog = False

            st.success(f"✅ '{room['room_name']}' 방에 참가했습니다!")
            time.sleep(1)
            st.rerun()

        except Exception as e:
            st.error(f"참가 실패: {str(e)}")


# ========================================
# 4. 대기실 뷰
# ========================================

def render_waiting_room():
    """대기실 렌더링"""
    room = get_room(st.session_state.current_room_id)

    if not room:
        st.error("방을 찾을 수 없습니다")
        st.session_state.current_room_id = None
        st.session_state.view_mode = 'browser'
        st.rerun()
        return

    # 방 상태 확인
    if room['status'] == RoomStatus.IN_PROGRESS:
        st.session_state.view_mode = 'in_progress'
        st.rerun()
        return
    elif room['status'] == RoomStatus.COMPLETED:
        st.session_state.view_mode = 'results'
        st.rerun()
        return

    badge_name, badge_class, badge_emoji = get_room_type_badge(room['room_type'])

    # 헤더
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 24px;">
        <span class="room-badge {badge_class}" style="font-size: 14px; padding: 8px 16px;">
            {badge_emoji} {badge_name}
        </span>
        <h2 style="margin: 16px 0 8px 0;">{room['room_name']}</h2>
        <p style="color: #64748b; font-size: 16px; margin: 0;">
            방 코드: <strong style="font-family: monospace; font-size: 18px; color: #2563eb;">{room['room_id']}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 참가자 목록
    col_main, col_chat = st.columns([2, 1])

    with col_main:
        st.markdown("#### 👥 참가자")

        participants = room.get('participants', [])
        ready_count = sum(1 for p in participants if p['status'] == ParticipantStatus.READY)

        st.progress(ready_count / len(participants) if participants else 0)
        st.caption(f"준비 완료: {ready_count}/{len(participants)}명")

        for p in participants:
            is_host = p['user_id'] == room['host_id']
            is_me = p['user_id'] == st.session_state.user_id
            is_ready = p['status'] == ParticipantStatus.READY

            avatar_class = 'avatar-ready' if is_ready else 'avatar-not-ready'
            status_text = '✅ 준비 완료' if is_ready else '⏳ 대기 중'

            st.markdown(f"""
            <div style="display: flex; align-items: center; padding: 12px;
                        background: {'#f0f9ff' if is_me else '#f8fafc'};
                        border-radius: 12px; margin-bottom: 8px;
                        border: {'2px solid #2563eb' if is_me else '1px solid #e2e8f0'};">
                <div class="participant-avatar {avatar_class}">
                    {p['user_name'][0].upper()}
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #0f172a;">
                        {p['user_name']} {'👑' if is_host else ''} {'(나)' if is_me else ''}
                    </div>
                    <div style="font-size: 13px; color: #64748b;">{status_text}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 액션 버튼들
        st.markdown("---")

        # 내 상태 확인
        my_participant = next((p for p in participants if p['user_id'] == st.session_state.user_id), None)
        my_status = my_participant['status'] if my_participant else ParticipantStatus.NOT_READY

        col_ready, col_leave = st.columns(2)

        with col_ready:
            if my_status == ParticipantStatus.READY:
                if st.button("⏳ 대기로 변경", use_container_width=True):
                    update_participant_status(
                        st.session_state.current_room_id,
                        st.session_state.user_id,
                        ParticipantStatus.NOT_READY
                    )
                    st.rerun()
            else:
                if st.button("✅ 준비 완료", use_container_width=True, type="primary"):
                    update_participant_status(
                        st.session_state.current_room_id,
                        st.session_state.user_id,
                        ParticipantStatus.READY
                    )
                    st.rerun()

        with col_leave:
            if st.button("🚪 방 나가기", use_container_width=True):
                leave_room(st.session_state.current_room_id, st.session_state.user_id)
                st.session_state.current_room_id = None
                st.session_state.is_host = False
                st.session_state.view_mode = 'browser'
                st.rerun()

        # 호스트 전용: 시작 버튼
        if room['host_id'] == st.session_state.user_id:
            st.markdown("---")
            st.markdown("##### 👑 호스트 전용")

            all_ready = all(p['status'] == ParticipantStatus.READY for p in participants)
            can_start = all_ready and len(participants) >= 2

            if not can_start:
                if len(participants) < 2:
                    st.warning("⚠️ 최소 2명이 필요합니다")
                elif not all_ready:
                    st.warning("⚠️ 모든 참가자가 준비 완료해야 합니다")

            if st.button(
                "🚀 면접 시작",
                use_container_width=True,
                type="primary",
                disabled=not can_start
            ):
                try:
                    # 세션 시작
                    start_session(st.session_state.current_room_id, st.session_state.user_id)

                    # 그룹 면접이면 면접 세션 시작
                    if room['room_type'] == 'group_interview':
                        settings = room.get('settings', {})
                        start_group_interview(
                            st.session_state.current_room_id,
                            settings.get('target_airline', '대한항공'),
                            settings.get('question_count', 5)
                        )

                    st.session_state.view_mode = 'in_progress'
                    st.rerun()

                except Exception as e:
                    st.error(f"시작 실패: {str(e)}")

    with col_chat:
        render_chat_panel(room['room_id'])

    # 자동 새로고침
    if st.session_state.auto_refresh:
        time.sleep(3)
        st.rerun()


# ========================================
# 5. 면접 진행 뷰
# ========================================

def render_interview_in_progress():
    """면접 진행 중 화면"""
    # 멀티플레이어 서비스 체크
    if not MULTIPLAYER_AVAILABLE:
        st.error("멀티플레이어 서비스가 로드되지 않았습니다.")
        st.info("로비로 돌아갑니다...")
        st.session_state.view_mode = 'browser'
        return

    room = get_room(st.session_state.current_room_id)

    if not room:
        st.error("방을 찾을 수 없습니다")
        st.session_state.view_mode = 'browser'
        st.rerun()
        return

    # 완료 상태 확인
    if room['status'] == RoomStatus.COMPLETED:
        st.session_state.view_mode = 'results'
        st.rerun()
        return

    # 토론 모드 분기
    if room['room_type'] == 'debate':
        render_debate_mode(room)
        return

    try:
        turn_info = get_current_turn_info(st.session_state.current_room_id)
        progress = get_interview_progress(st.session_state.current_room_id)
    except Exception as e:
        logger.error(f"면접 진행 상황 로드 실패: {e}")
        st.error(f"진행 상황을 불러올 수 없습니다: {str(e)}")
        return

    state = room.get('state', {})

    # 헤더 정보
    col_info1, col_info2, col_info3 = st.columns(3)

    with col_info1:
        st.metric(
            "질문",
            f"{state.get('current_question_idx', 0) + 1}/{len(room.get('questions', []))}",
            delta=None
        )

    with col_info2:
        st.metric(
            "라운드",
            f"{state.get('round_number', 1)}",
            delta=None
        )

    with col_info3:
        st.metric(
            "경과 시간",
            progress.get('elapsed_time_formatted', '0분 0초'),
            delta=None
        )

    # 현재 질문 표시
    current_question = turn_info.get('current_question', '질문을 불러오는 중...')
    question_idx = turn_info.get('current_question_idx', 0) + 1

    st.markdown(f"""
    <div class="question-card">
        <div class="question-number">질문 {question_idx}</div>
        <div class="question-text">{current_question}</div>
    </div>
    """, unsafe_allow_html=True)

    # 레이아웃
    col_main, col_side = st.columns([2, 1])

    with col_main:
        # 현재 발언자 표시
        current_speaker_id = turn_info.get('current_speaker_id')
        current_speaker_name = turn_info.get('current_speaker_name', '알 수 없음')
        is_my_turn = current_speaker_id == st.session_state.user_id

        # 타이머
        remaining = turn_info.get('remaining_seconds')
        if remaining is not None:
            timer_class = ''
            if remaining <= 10:
                timer_class = 'timer-danger'
            elif remaining <= 30:
                timer_class = 'timer-warning'

            st.markdown(f"""
            <div class="timer-container">
                <div>🎙️ <strong>{current_speaker_name}</strong>님 차례</div>
                <div class="timer-text {timer_class}">{format_remaining_time(remaining)}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="timer-container">
                <div>🎙️ <strong>{current_speaker_name}</strong>님 차례</div>
            </div>
            """, unsafe_allow_html=True)

        # 내 차례일 때 답변 입력
        if is_my_turn:
            st.markdown("### 📝 내 답변")

            answer_text = st.text_area(
                "답변을 입력하세요",
                height=150,
                placeholder="질문에 대한 답변을 작성해주세요...",
                key="answer_input_area"
            )

            col_submit, col_skip = st.columns([2, 1])

            with col_submit:
                if st.button("✅ 답변 제출", use_container_width=True, type="primary"):
                    if answer_text.strip():
                        try:
                            from room_manager import submit_answer as rm_submit_answer, next_turn

                            # 답변 제출
                            rm_submit_answer(
                                st.session_state.current_room_id,
                                st.session_state.user_id,
                                answer_text.strip()
                            )

                            # 다음 턴으로
                            next_turn(st.session_state.current_room_id)

                            st.success("✅ 답변이 제출되었습니다!")
                            time.sleep(1)
                            st.rerun()

                        except Exception as e:
                            st.error(f"제출 실패: {str(e)}")
                    else:
                        st.warning("답변을 입력해주세요")

            with col_skip:
                if st.button("⏭️ 건너뛰기", use_container_width=True):
                    try:
                        from multiplayer_service import skip_turn
                        skip_turn(st.session_state.current_room_id, st.session_state.user_id)
                        st.rerun()
                    except Exception as e:
                        st.error(f"실패: {str(e)}")

        else:
            # 다른 사람 차례일 때 반응 버튼
            st.markdown("### 👏 반응 보내기")
            st.markdown("발표자에게 응원을 보내세요!")

            reaction_cols = st.columns(5)
            for idx, (reaction_key, reaction_info) in enumerate(REACTIONS.items()):
                with reaction_cols[idx]:
                    if st.button(
                        reaction_info['emoji'],
                        key=f"reaction_{reaction_key}",
                        help=reaction_info['name']
                    ):
                        try:
                            add_reaction(
                                st.session_state.user_id,
                                current_speaker_id,
                                st.session_state.current_room_id,
                                reaction_key
                            )
                            st.toast(f"{reaction_info['emoji']} {reaction_info['name']}!")
                        except Exception as e:
                            st.error(str(e))

    with col_side:
        # 리더보드
        st.markdown("### 🏆 실시간 순위")

        try:
            leaderboard = get_live_leaderboard(st.session_state.current_room_id)

            for entry in leaderboard[:5]:
                rank = entry.get('rank', 0)
                rank_class = f"rank-{rank}" if rank <= 3 else ""
                rank_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(rank, f'{rank}위')

                is_me = entry.get('user_id') == st.session_state.user_id

                st.markdown(f"""
                <div class="leaderboard-item {rank_class}" style="{'background: #eff6ff;' if is_me else ''}">
                    <span class="rank-number">{rank_emoji}</span>
                    <span style="flex: 1; font-weight: {'600' if is_me else '400'};">
                        {entry.get('user_name', '익명')} {'(나)' if is_me else ''}
                    </span>
                    <span style="font-weight: 600; color: #2563eb;">
                        {entry.get('total_score', 0):.0f}점
                    </span>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.info("순위 정보가 없습니다")

        st.markdown("---")

        # 미니 채팅
        with st.expander("💬 채팅", expanded=False):
            render_chat_panel(st.session_state.current_room_id, compact=True)

    # 자동 새로고침
    if st.session_state.auto_refresh:
        time.sleep(2)
        st.rerun()


# ========================================
# 6. 토론 모드 뷰
# ========================================

def render_debate_mode(room: Dict[str, Any]):
    """토론 모드 렌더링"""
    try:
        debate_state = get_debate_state(st.session_state.current_room_id)
    except:
        # 토론이 아직 시작되지 않음 - 주제 선택
        render_debate_setup(room)
        return

    topic = debate_state.get('topic', {})
    phase = debate_state.get('phase', 'opening')
    positions = debate_state.get('positions', {})

    # 단계 표시
    phase_labels = {
        'opening': '🎬 입론',
        'argument': '💬 본론',
        'rebuttal': '⚔️ 반론',
        'closing': '🎯 최종 변론',
        'evaluation': '📊 평가'
    }

    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 24px;">
        <span class="phase-indicator">{phase_labels.get(phase, phase)}</span>
        <h2 style="margin: 16px 0;">{topic.get('topic', '주제 없음')}</h2>
        <p style="color: #64748b;">{topic.get('description', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # 찬반 팀 표시
    col_pro, col_con = st.columns(2)

    with col_pro:
        st.markdown("""
        <div class="debate-side side-pro">
            <h4>👍 찬성팀</h4>
        </div>
        """, unsafe_allow_html=True)

        for user_id, pos in positions.items():
            if pos == 'pro':
                participant = next(
                    (p for p in room['participants'] if p['user_id'] == user_id),
                    None
                )
                if participant:
                    is_me = user_id == st.session_state.user_id
                    st.markdown(f"• {participant['user_name']} {'(나)' if is_me else ''}")

    with col_con:
        st.markdown("""
        <div class="debate-side side-con">
            <h4>👎 반대팀</h4>
        </div>
        """, unsafe_allow_html=True)

        for user_id, pos in positions.items():
            if pos == 'con':
                participant = next(
                    (p for p in room['participants'] if p['user_id'] == user_id),
                    None
                )
                if participant:
                    is_me = user_id == st.session_state.user_id
                    st.markdown(f"• {participant['user_name']} {'(나)' if is_me else ''}")

    # 현재 발언자 및 입력
    current_speaker_id = debate_state.get('current_speaker_id')
    is_my_turn = current_speaker_id == st.session_state.user_id

    if is_my_turn and phase != 'evaluation':
        st.markdown("### 📝 내 주장")

        my_position = positions.get(st.session_state.user_id, 'pro')
        position_label = '찬성' if my_position == 'pro' else '반대'

        st.info(f"💡 {position_label} 입장에서 주장을 펼쳐주세요!")

        argument = st.text_area(
            "주장을 입력하세요",
            height=150,
            placeholder="논리적인 근거와 함께 주장을 작성해주세요..."
        )

        if st.button("✅ 주장 제출", use_container_width=True, type="primary"):
            if argument.strip():
                try:
                    submit_argument(
                        st.session_state.current_room_id,
                        st.session_state.user_id,
                        argument.strip()
                    )
                    st.success("✅ 주장이 제출되었습니다!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"제출 실패: {str(e)}")
            else:
                st.warning("주장을 입력해주세요")

    elif phase == 'evaluation':
        st.markdown("### 📊 토론 평가 중...")
        st.info("잠시 후 결과가 발표됩니다!")

    else:
        current_speaker_name = debate_state.get('current_speaker_name', '알 수 없음')
        st.info(f"🎙️ 현재 발언자: **{current_speaker_name}**님")

    # 자동 새로고침
    if st.session_state.auto_refresh:
        time.sleep(2)
        st.rerun()


def render_debate_setup(room: Dict[str, Any]):
    """토론 설정 화면 (호스트용)"""
    st.markdown("### 🎭 토론 주제 선택")

    if room['host_id'] != st.session_state.user_id:
        st.info("⏳ 호스트가 토론 주제를 선택하고 있습니다...")
        time.sleep(2)
        st.rerun()
        return

    # 주제 선택
    topic_options = {t['topic']: t for t in DEBATE_TOPICS}
    selected_topic = st.selectbox(
        "토론 주제",
        options=list(topic_options.keys())
    )

    topic_data = topic_options[selected_topic]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**👍 찬성 측 논점**")
        for point in topic_data.get('pro_points', []):
            st.markdown(f"• {point}")

    with col2:
        st.markdown("**👎 반대 측 논점**")
        for point in topic_data.get('con_points', []):
            st.markdown(f"• {point}")

    # 팀 배치
    st.markdown("---")
    st.markdown("### 👥 팀 배치")

    participants = room.get('participants', [])
    positions = {}

    for p in participants:
        default_pos = 'pro' if len([v for v in positions.values() if v == 'pro']) < len(participants) // 2 else 'con'

        pos = st.radio(
            f"{p['user_name']}",
            options=['pro', 'con'],
            format_func=lambda x: '👍 찬성' if x == 'pro' else '👎 반대',
            horizontal=True,
            key=f"pos_{p['user_id']}"
        )
        positions[p['user_id']] = pos

    if st.button("🚀 토론 시작", use_container_width=True, type="primary"):
        try:
            start_debate(
                st.session_state.current_room_id,
                selected_topic,
                positions
            )
            st.success("✅ 토론이 시작됩니다!")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"시작 실패: {str(e)}")


# ========================================
# 7. 결과 뷰
# ========================================

def render_results_view():
    """결과 화면 렌더링"""
    room = get_room(st.session_state.current_room_id)

    if not room:
        st.error("방 정보를 찾을 수 없습니다")
        st.session_state.view_mode = 'browser'
        st.rerun()
        return

    st.markdown("## 🎉 면접 완료!")

    # 우승자 표시
    try:
        winner_info = calculate_winner(st.session_state.current_room_id)

        if winner_info and 'winner_name' in winner_info:
            st.markdown(f"""
            <div class="winner-card">
                <div class="winner-trophy">🏆</div>
                <div style="font-size: 16px; opacity: 0.9;">오늘의 우승자</div>
                <div class="winner-name">{winner_info['winner_name']}</div>
                <div style="font-size: 24px; margin-top: 8px;">{winner_info.get('winner_score', 0):.0f}점</div>
            </div>
            """, unsafe_allow_html=True)
    except:
        pass

    # 전체 순위
    st.markdown("### 📊 최종 순위")

    try:
        rankings = get_live_leaderboard(st.session_state.current_room_id)

        for entry in rankings:
            rank = entry.get('rank', 0)
            rank_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(rank, f'{rank}.')
            is_me = entry.get('user_id') == st.session_state.user_id

            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    st.markdown(f"### {rank_emoji}")

                with col2:
                    st.markdown(f"**{entry.get('user_name', '익명')}** {'(나)' if is_me else ''}")
                    st.caption(f"답변 {entry.get('answers_count', 0)}개")

                with col3:
                    st.markdown(f"### {entry.get('total_score', 0):.0f}점")
    except Exception as e:
        st.info("순위 정보를 불러올 수 없습니다")

    st.markdown("---")

    # 동료 평가 섹션
    if PEER_EVAL_AVAILABLE:
        st.markdown("### ✍️ 동료 평가")
        st.info("함께한 참가자들을 평가해주세요! 평가는 서로의 성장에 도움이 됩니다.")
        render_peer_evaluation_form(room)

        # 받은 반응 요약
        st.markdown("### 👏 내가 받은 반응")
        try:
            reaction_summary = get_reaction_summary(st.session_state.user_id)

            if reaction_summary.get('total_reactions', 0) > 0:
                cols = st.columns(5)
                for idx, item in enumerate(reaction_summary.get('reaction_breakdown', [])[:5]):
                    with cols[idx]:
                        st.metric(
                            item['emoji'],
                            f"{item['count']}개",
                            delta=None
                        )
            else:
                st.info("아직 받은 반응이 없습니다")
        except Exception as e:
            logger.error(f"반응 요약 로드 실패: {e}")
    else:
        st.info("동료 평가 기능이 현재 사용 불가합니다.")

    st.markdown("---")

    # 액션 버튼
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 새 방 만들기", use_container_width=True, type="primary"):
            st.session_state.current_room_id = None
            st.session_state.view_mode = 'browser'
            st.session_state.show_create_dialog = True
            st.rerun()

    with col2:
        if st.button("🏠 로비로 돌아가기", use_container_width=True):
            leave_room(st.session_state.current_room_id, st.session_state.user_id)
            st.session_state.current_room_id = None
            st.session_state.view_mode = 'browser'
            st.rerun()


def render_peer_evaluation_form(room: Dict[str, Any]):
    """동료 평가 폼 렌더링"""
    participants = room.get('participants', [])
    other_participants = [p for p in participants if p['user_id'] != st.session_state.user_id]

    if not other_participants:
        st.info("평가할 참가자가 없습니다")
        return

    # 평가 대상 선택
    target_options = {p['user_name']: p['user_id'] for p in other_participants}
    selected_name = st.selectbox(
        "평가 대상",
        options=list(target_options.keys())
    )
    target_id = target_options[selected_name]

    # 평가 항목
    st.markdown("#### 평가 항목")

    scores = {}

    for category, info in EVALUATION_CRITERIA.items():
        st.markdown(f"""
        <div class="evaluation-category">
            <div class="evaluation-title">{info['name']}</div>
            <div style="color: #64748b; font-size: 13px; margin-bottom: 8px;">
                {info['description']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        score = st.slider(
            f"{info['name']} 점수",
            min_value=0,
            max_value=info['max_score'],
            value=info['max_score'] // 2,
            key=f"eval_{category}",
            label_visibility="collapsed"
        )
        scores[category] = {'total': score, 'subcriteria': {}}

    # 피드백
    feedback = st.text_area(
        "추가 피드백 (선택)",
        placeholder="구체적인 피드백을 남겨주세요...",
        height=100
    )

    if st.button("📤 평가 제출", use_container_width=True, type="primary"):
        try:
            submit_peer_evaluation(
                evaluator_id=st.session_state.user_id,
                target_id=target_id,
                room_id=st.session_state.current_room_id,
                question_idx=0,  # 전체 평가
                scores=scores,
                feedback=feedback
            )
            st.success(f"✅ {selected_name}님에 대한 평가가 제출되었습니다!")
        except Exception as e:
            st.error(f"평가 제출 실패: {str(e)}")


# ========================================
# 8. 관전자 뷰
# ========================================

def render_spectator_view():
    """관전자 화면 렌더링"""
    room = get_room(st.session_state.current_room_id)

    if not room:
        st.error("방을 찾을 수 없습니다")
        st.session_state.view_mode = 'browser'
        st.rerun()
        return

    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
        <span class="spectator-badge">👁️ 관전 모드</span>
        <span style="color: #64748b;">실시간으로 면접을 관전하고 있습니다</span>
    </div>
    """, unsafe_allow_html=True)

    # 방 정보
    st.markdown(f"### {room['room_name']}")

    # 현재 상태에 따른 표시
    if room['status'] == RoomStatus.WAITING:
        st.info("⏳ 면접이 곧 시작됩니다...")

    elif room['status'] == RoomStatus.IN_PROGRESS:
        try:
            turn_info = get_current_turn_info(st.session_state.current_room_id)
            current_question = turn_info.get('current_question', '질문을 불러오는 중...')

            st.markdown(f"""
            <div class="question-card">
                <div class="question-text">{current_question}</div>
            </div>
            """, unsafe_allow_html=True)

            st.info(f"🎙️ 현재 발언자: **{turn_info.get('current_speaker_name', '알 수 없음')}**님")

        except:
            pass

        # 리더보드
        try:
            leaderboard = get_live_leaderboard(st.session_state.current_room_id)

            st.markdown("### 🏆 실시간 순위")
            for entry in leaderboard[:5]:
                rank = entry.get('rank', 0)
                rank_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}.get(rank, f'{rank}.')

                st.markdown(f"{rank_emoji} **{entry.get('user_name', '익명')}** - {entry.get('total_score', 0):.0f}점")
        except:
            pass

    elif room['status'] == RoomStatus.COMPLETED:
        st.success("🎉 면접이 종료되었습니다!")

    # 나가기 버튼
    if st.button("🚪 관전 종료", use_container_width=True):
        try:
            from multiplayer_service import remove_spectator
            remove_spectator(st.session_state.current_room_id, st.session_state.user_id)
        except:
            pass
        st.session_state.current_room_id = None
        st.session_state.is_spectator = False
        st.session_state.view_mode = 'browser'
        st.rerun()

    # 자동 새로고침
    if st.session_state.auto_refresh:
        time.sleep(3)
        st.rerun()


# ========================================
# 채팅 패널
# ========================================

def render_chat_panel(room_id: str, compact: bool = False):
    """채팅 패널 렌더링"""
    st.markdown("#### 💬 채팅")

    # 메시지 조회
    messages = get_messages(room_id)

    # 메시지 표시 영역
    container_height = "200px" if compact else "300px"

    chat_html = f'<div class="chat-container" style="max-height: {container_height};">'

    for msg in messages[-20:]:  # 최근 20개만
        msg_type = msg.get('message_type', 'chat')
        user_name = escape_html(msg.get('user_name', '익명'))  # XSS 방지
        message = escape_html(msg.get('message', ''))  # XSS 방지

        if msg_type == 'system':
            chat_html += f'<div class="chat-message chat-system">{message}</div>'
        elif msg_type == 'reaction':
            chat_html += f'<div class="chat-message chat-reaction">{message}</div>'
        else:
            is_me = msg.get('user_id') == st.session_state.user_id
            chat_html += f'''
            <div class="chat-message chat-user">
                <span style="font-weight: 600; color: {'#2563eb' if is_me else '#0f172a'};">
                    {user_name}
                </span>
                <span style="color: #64748b;"> {message}</span>
            </div>
            '''

    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # 메시지 입력
    col_input, col_send = st.columns([4, 1])

    with col_input:
        chat_input = st.text_input(
            "메시지",
            placeholder="메시지를 입력하세요...",
            key=f"chat_{room_id}",
            label_visibility="collapsed"
        )

    with col_send:
        if st.button("전송", key=f"send_{room_id}"):
            # 채팅 메시지 검증
            is_valid, cleaned_msg, error_msg = validate_chat_message(chat_input)
            if is_valid:
                try:
                    send_message(
                        room_id,
                        st.session_state.user_id,
                        cleaned_msg  # 검증된 메시지 사용
                    )
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


# ========================================
# 메인 실행
# ========================================

def main():
    """메인 함수"""
    init_page(
        title="그룹 면접",
        page_title="FlyReady Lab - 그룹 면접",
        current_page="그룹면접"
    )

    # CSS 적용
    st.markdown(get_custom_css(), unsafe_allow_html=True)

    # 필수 모듈 체크
    if not ROOM_MANAGER_AVAILABLE:
        st.error("⚠️ 그룹 면접 기능을 사용하려면 room_manager 모듈이 필요합니다.")
        st.info("관리자에게 문의하세요.")
        logger.error("room_manager 모듈 로드 실패로 그룹 면접 페이지 비활성화")
        return

    if not MULTIPLAYER_AVAILABLE:
        st.warning("⚠️ 멀티플레이어 서비스가 제한됩니다. 일부 기능이 동작하지 않을 수 있습니다.")
        logger.warning("multiplayer_service 모듈 로드 실패")

    if not PEER_EVAL_AVAILABLE:
        logger.warning("peer_evaluation 모듈 로드 실패 - 동료 평가 기능 비활성화")

    # 세션 상태 초기화
    init_session_state()

    # 사용자 이름 설정 (최초 방문 시)
    if not st.session_state.get('name_set'):
        with st.sidebar:
            st.markdown("### 👤 프로필 설정")
            new_name = st.text_input(
                "닉네임",
                value=st.session_state.user_name,
                max_chars=20
            )
            if new_name != st.session_state.user_name:
                st.session_state.user_name = new_name

            st.session_state.name_set = True

            st.markdown("---")
            st.markdown(f"**사용자 ID:** `{st.session_state.user_id}`")

            # 자동 새로고침 토글
            st.session_state.auto_refresh = st.checkbox(
                "자동 새로고침",
                value=st.session_state.auto_refresh,
                help="실시간 업데이트를 위한 자동 새로고침"
            )

    # 다이얼로그 표시
    if st.session_state.show_create_dialog:
        render_create_room_dialog()
    elif st.session_state.show_join_dialog:
        render_join_dialog()
    else:
        # 뷰 모드에 따른 렌더링
        view_mode = st.session_state.view_mode

        if view_mode == 'browser':
            render_room_browser()
        elif view_mode == 'waiting':
            render_waiting_room()
        elif view_mode == 'in_progress':
            render_interview_in_progress()
        elif view_mode == 'results':
            render_results_view()
        elif view_mode == 'spectator':
            render_spectator_view()
        else:
            render_room_browser()

    end_page()


if __name__ == "__main__":
    main()
