# motivation.py
# 응원 팝업 - 사용 시간에 따른 동기부여 메시지

import streamlit as st
from datetime import datetime, timedelta
import random

# 명언 데이터
MOTIVATIONAL_QUOTES = {
    60: [  # 1시간
        {"quote": "할 수 있습니다!", "author": "당신을 응원합니다"},
        {"quote": "시작이 반이다. 이미 절반은 성공한 거예요!", "author": "속담"},
        {"quote": "꿈을 향해 한 걸음씩 나아가고 계시네요!", "author": "AI 코치"},
        {"quote": "1시간 동안 열심히 준비하셨네요. 대단해요!", "author": "AI 코치"},
    ],
    120: [  # 2시간
        {"quote": "성공은 준비된 자에게 온다.", "author": "루이 파스퇴르"},
        {"quote": "노력은 배신하지 않습니다!", "author": "명언"},
        {"quote": "2시간 동안 집중하셨군요. 정말 대단해요!", "author": "AI 코치"},
        {"quote": "당신의 열정이 느껴집니다!", "author": "AI 코치"},
    ],
    180: [  # 3시간
        {"quote": "포기하지 마세요!", "author": "당신을 응원합니다"},
        {"quote": "오늘 흘린 땀은 내일의 결실이 됩니다.", "author": "명언"},
        {"quote": "3시간이나! 정말 열심히 하시네요!", "author": "AI 코치"},
        {"quote": "승무원이 될 당신의 모습이 보여요!", "author": "AI 코치"},
    ],
    240: [  # 4시간
        {"quote": "지금 이 순간이 가장 빛나는 당신입니다.", "author": "AI 코치"},
        {"quote": "꿈을 꾸는 것만으로도 용기있는 일이에요.", "author": "명언"},
        {"quote": "4시간의 노력, 반드시 보상받을 거예요!", "author": "AI 코치"},
    ],
    300: [  # 5시간
        {"quote": "잠시 휴식도 필요해요. 건강이 최고입니다!", "author": "AI 코치"},
        {"quote": "열정도 좋지만 컨디션 관리도 중요해요!", "author": "AI 코치"},
        {"quote": "물 한 잔 마시고 스트레칭 어때요?", "author": "AI 코치"},
    ],
}

# 추가 명언
FAMOUS_QUOTES = [
    {"quote": "성공의 비결은 단 한 가지, 포기하지 않는 것이다.", "author": "윈스턴 처칠"},
    {"quote": "네가 할 수 있다고 믿든, 할 수 없다고 믿든, 어느 쪽이든 옳다.", "author": "헨리 포드"},
    {"quote": "천 리 길도 한 걸음부터.", "author": "노자"},
    {"quote": "실패는 성공의 어머니다.", "author": "토마스 에디슨"},
    {"quote": "오늘 할 수 있는 일에 최선을 다하라.", "author": "마하트마 간디"},
    {"quote": "준비하지 않는 것은 실패를 준비하는 것이다.", "author": "벤자민 프랭클린"},
    {"quote": "나는 나의 운명의 주인이고, 나의 영혼의 선장이다.", "author": "윌리엄 어니스트 헨리"},
    {"quote": "작은 진전이라도 진전은 진전이다.", "author": "명언"},
    {"quote": "오늘의 나는 어제보다 나은 사람이다.", "author": "명언"},
    {"quote": "자신을 믿어라. 당신은 생각보다 강하다.", "author": "명언"},
]


def init_session_time():
    """세션 시작 시간 초기화"""
    if "session_start_time" not in st.session_state:
        st.session_state.session_start_time = datetime.now()
    if "shown_motivation_times" not in st.session_state:
        st.session_state.shown_motivation_times = set()


def get_session_minutes() -> int:
    """세션 경과 시간 (분)"""
    if "session_start_time" not in st.session_state:
        return 0
    elapsed = datetime.now() - st.session_state.session_start_time
    return int(elapsed.total_seconds() / 60)


def check_and_show_motivation():
    """시간 체크 및 응원 팝업 표시"""
    init_session_time()

    minutes = get_session_minutes()

    # 체크할 시간대 (분 단위)
    check_times = [60, 120, 180, 240, 300]

    for check_time in check_times:
        if minutes >= check_time and check_time not in st.session_state.shown_motivation_times:
            st.session_state.shown_motivation_times.add(check_time)
            st.session_state.show_motivation_popup = True
            st.session_state.motivation_time = check_time
            return True

    return False


def show_motivation_popup():
    """응원 팝업 표시 (dialog 사용)"""
    if not st.session_state.get("show_motivation_popup", False):
        return

    check_time = st.session_state.get("motivation_time", 60)
    quotes = MOTIVATIONAL_QUOTES.get(check_time, FAMOUS_QUOTES)
    selected = random.choice(quotes)

    hours = check_time // 60

    # 팝업 스타일
    st.markdown(f"""
    <div id="motivation-popup" style="
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px 50px;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        z-index: 9999;
        text-align: center;
        max-width: 500px;
        animation: popIn 0.5s ease-out;
    ">
        <div style="font-size: 50px; margin-bottom: 20px;">
            {"🌟" if hours <= 2 else "💪" if hours <= 3 else "☕"}
        </div>
        <div style="font-size: 14px; opacity: 0.8; margin-bottom: 10px;">
            {hours}시간 동안 함께하고 계시네요!
        </div>
        <div style="font-size: 24px; font-weight: bold; margin-bottom: 15px; line-height: 1.4;">
            "{selected['quote']}"
        </div>
        <div style="font-size: 14px; opacity: 0.9;">
            - {selected['author']}
        </div>
    </div>
    <div id="motivation-overlay" style="
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        z-index: 9998;
    "></div>
    <style>
        @keyframes popIn {{
            0% {{ transform: translate(-50%, -50%) scale(0.5); opacity: 0; }}
            100% {{ transform: translate(-50%, -50%) scale(1); opacity: 1; }}
        }}
    </style>
    """, unsafe_allow_html=True)

    # 닫기 버튼
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✨ 계속 화이팅!", key="close_motivation", use_container_width=True):
            st.session_state.show_motivation_popup = False
            st.rerun()


def show_motivation_toast():
    """토스트 형식의 간단한 응원 메시지"""
    if not st.session_state.get("show_motivation_popup", False):
        return

    check_time = st.session_state.get("motivation_time", 60)
    quotes = MOTIVATIONAL_QUOTES.get(check_time, FAMOUS_QUOTES)
    selected = random.choice(quotes)
    hours = check_time // 60

    st.toast(f'🌟 {hours}시간째 열공중! "{selected["quote"]}" - {selected["author"]}', icon="💪")
    st.session_state.show_motivation_popup = False


def get_random_quote() -> dict:
    """랜덤 명언 반환"""
    return random.choice(FAMOUS_QUOTES)


def display_daily_quote():
    """오늘의 명언 표시"""
    quote = get_random_quote()
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 12px; padding: 20px; margin: 10px 0; text-align: center; border-left: 4px solid #667eea;">
        <div style="font-size: 18px; color: #333; font-style: italic;">"{quote['quote']}"</div>
        <div style="font-size: 14px; color: #666; margin-top: 10px;">- {quote['author']}</div>
    </div>
    """, unsafe_allow_html=True)
