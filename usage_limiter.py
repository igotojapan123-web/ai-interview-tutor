# usage_limiter.py
# 무료 베타 테스트 사용량 제한 시스템

import streamlit as st
from datetime import datetime, timedelta
import json
import os

# 일일 사용 제한 설정
DAILY_LIMITS = {
    "모의면접": 5,
    "롤플레잉": 5,
    "영어면접": 5,
    "토론면접": 5,
    "자소서첨삭": 3,
    "자소서기반질문": 3,
    "기내방송연습": 10,
    "항공상식퀴즈": 20,
    "TTS": 30,  # TTS 호출 횟수
    "LLM": 50,  # LLM API 호출 횟수
}

# 베타 테스트 기간
BETA_END_DATE = datetime(2025, 2, 1)  # 필요시 수정

def get_today_key():
    """오늘 날짜 키"""
    return datetime.now().strftime("%Y-%m-%d")

def get_usage_key(feature: str):
    """사용량 세션 키"""
    return f"usage_{feature}_{get_today_key()}"

def get_usage(feature: str) -> int:
    """현재 사용량 조회"""
    key = get_usage_key(feature)
    return st.session_state.get(key, 0)

def get_remaining(feature: str) -> int:
    """남은 사용량 조회"""
    limit = DAILY_LIMITS.get(feature, 10)
    used = get_usage(feature)
    return max(0, limit - used)

def increment_usage(feature: str, count: int = 1):
    """사용량 증가"""
    key = get_usage_key(feature)
    current = st.session_state.get(key, 0)
    st.session_state[key] = current + count

def check_limit(feature: str) -> bool:
    """사용 가능 여부 체크 (True = 사용 가능)"""
    return get_remaining(feature) > 0

def show_usage_warning(feature: str):
    """사용량 경고 표시"""
    remaining = get_remaining(feature)
    limit = DAILY_LIMITS.get(feature, 10)
    used = get_usage(feature)

    if remaining <= 0:
        st.error(f"🚫 오늘 {feature} 사용량을 모두 소진했습니다. (일일 {limit}회)")
        st.info("내일 다시 이용해주세요! 정식 출시 후에는 무제한으로 이용 가능합니다.")
        return False
    elif remaining <= 2:
        st.warning(f"⚠️ {feature} 오늘 남은 횟수: {remaining}회 / {limit}회")

    return True

def show_usage_status(feature: str):
    """사용량 상태 표시 (사이드바/상단용)"""
    remaining = get_remaining(feature)
    limit = DAILY_LIMITS.get(feature, 10)

    if remaining <= 0:
        color = "#ef4444"
        status = "소진"
    elif remaining <= 2:
        color = "#f59e0b"
        status = f"{remaining}회 남음"
    else:
        color = "#10b981"
        status = f"{remaining}회 남음"

    return f'<span style="background:{color}22;color:{color};padding:3px 10px;border-radius:12px;font-size:0.8rem;font-weight:600;">오늘 {status}</span>'

def render_beta_banner():
    """베타 테스트 배너 표시"""
    days_left = (BETA_END_DATE - datetime.now()).days

    if days_left > 0:
        st.markdown(f'''
        <div style="
            background: linear-gradient(135deg, #8b5cf6, #6366f1);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        ">
            <div>
                <span style="font-weight: 700;">🎉 무료 베타 테스트 진행 중!</span>
                <span style="opacity: 0.9; margin-left: 10px;">모든 기능을 무료로 체험해보세요</span>
            </div>
            <div style="
                background: rgba(255,255,255,0.2);
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: 600;
            ">
                D-{days_left}
            </div>
        </div>
        ''', unsafe_allow_html=True)

def render_usage_summary():
    """전체 사용량 요약 (홈페이지용)"""
    html = '''
    <div style="
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 20px 0;
    ">
        <div style="font-weight: 700; margin-bottom: 15px; color: #1e3a5f;">
            📊 오늘의 사용량
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px;">
    '''

    main_features = ["모의면접", "롤플레잉", "자소서첨삭", "자소서기반질문"]

    for feature in main_features:
        remaining = get_remaining(feature)
        limit = DAILY_LIMITS.get(feature, 10)
        percent = (remaining / limit) * 100

        if remaining <= 0:
            color = "#ef4444"
        elif remaining <= 2:
            color = "#f59e0b"
        else:
            color = "#10b981"

        html += f'''
        <div style="text-align: center; padding: 10px;">
            <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 5px;">{feature}</div>
            <div style="
                background: #f1f5f9;
                border-radius: 10px;
                height: 8px;
                overflow: hidden;
                margin-bottom: 5px;
            ">
                <div style="
                    background: {color};
                    height: 100%;
                    width: {percent}%;
                    border-radius: 10px;
                "></div>
            </div>
            <div style="font-size: 0.85rem; font-weight: 600; color: {color};">{remaining}/{limit}</div>
        </div>
        '''

    html += '</div></div>'
    return html

def check_and_use(feature: str) -> bool:
    """
    사용량 체크 및 차감 (한 번에 처리)
    Returns: True = 사용 가능, False = 제한 초과
    """
    if not check_limit(feature):
        show_usage_warning(feature)
        return False

    increment_usage(feature)
    return True

# LLM/TTS 호출용 래퍼 함수
def use_llm():
    """LLM API 호출 시 사용량 차감"""
    if check_limit("LLM"):
        increment_usage("LLM")
        return True
    return False

def use_tts():
    """TTS API 호출 시 사용량 차감"""
    if check_limit("TTS"):
        increment_usage("TTS")
        return True
    return False
