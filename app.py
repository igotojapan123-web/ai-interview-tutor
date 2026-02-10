"""
대한항공 채용 준비
FlyReady Lab
v2.0 - 비밀번호 보호 적용
"""

import streamlit as st
from datetime import datetime, date

st.set_page_config(
    page_title="대한항공 면접 준비",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========== 비밀번호 보호 ==========
def check_password():
    """비밀번호 확인 (keway, 대소문자 무관)"""

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # 로그인 화면
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            text-align: center;
        }
        .login-title {
            font-size: 2rem;
            font-weight: 700;
            color: #00256C;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
            color: #64748b;
            margin-bottom: 2rem;
        }
    </style>
    <div class="login-container">
        <div class="login-title">✈️ FlyReady Lab</div>
        <div class="login-subtitle">대한항공 면접 준비</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("비밀번호를 입력하세요", type="password", key="password_input")

        if st.button("입장하기", use_container_width=True):
            if password.lower() == "keway":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")

    return False


# 비밀번호 확인
if not check_password():
    st.stop()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

    .main { background: linear-gradient(180deg, #f8fafc 0%, #fff 100%); }

    .hero {
        background: linear-gradient(135deg, #00256C 0%, #0052CC 50%, #0078D4 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(0, 37, 108, 0.4);
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: shimmer 3s infinite;
    }
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .hero h1 { font-size: 2.8rem; font-weight: 700; margin-bottom: 0.5rem; position: relative; }
    .hero p { opacity: 0.9; font-size: 1.1rem; position: relative; }

    .dday {
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #C4A661 0%, #FFD700 50%, #C4A661 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 1.5rem 0;
        position: relative;
    }

    .motto {
        background: linear-gradient(135deg, #1e293b, #334155);
        color: white;
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        text-align: center;
        font-size: 1.2rem;
    }
    .motto span { color: #C4A661; font-weight: 600; }

    .feature-card {
        background: white;
        border-radius: 24px;
        padding: 2.5rem;
        border: 1px solid #e2e8f0;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        height: 100%;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .feature-card::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #00256C, #0078D4);
        transform: scaleX(0);
        transition: transform 0.4s ease;
    }
    .feature-card:hover {
        transform: translateY(-12px);
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
    }
    .feature-card:hover::after { transform: scaleX(1); }

    .feature-icon { font-size: 4rem; margin-bottom: 1.5rem; }
    .feature-title { font-size: 1.5rem; font-weight: 700; color: #1e293b; margin-bottom: 0.75rem; }
    .feature-desc { color: #64748b; line-height: 1.8; font-size: 1rem; }

    .stButton > button {
        background: linear-gradient(135deg, #00256C, #0078D4);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 1rem 2rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(0, 37, 108, 0.4);
    }

    .ke-way {
        background: linear-gradient(135deg, #00256C 0%, #003d99 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
    }
    .ke-way:hover {
        transform: scale(1.02);
        box-shadow: 0 15px 40px rgba(0, 37, 108, 0.5);
    }
    .ke-way h3 {
        color: #C4A661;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .ke-way p { color: rgba(255,255,255,0.9); line-height: 1.6; }

    .footer {
        text-align: center;
        padding: 2rem;
        color: #64748b;
        font-size: 0.9rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 3rem;
    }
    .footer a { color: #00256C; text-decoration: none; font-weight: 500; }

    .sidebar-dday {
        background: linear-gradient(135deg, #00256C, #0078D4);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .sidebar-dday-num { font-size: 2.5rem; font-weight: 800; }

    /* 사이드바 네비게이션에서 app 숨기기 */
    [data-testid="stSidebarNav"] li:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)


def calculate_dday():
    deadline = date(2026, 2, 24)
    return (deadline - date.today()).days


def main():
    dday = calculate_dday()

    # Hero
    st.markdown(f"""
    <div class="hero">
        <h1>✈️ 대한항공 면접 준비</h1>
        <p>2026년 객실승무원 채용 대비</p>
        <div class="dday">{"D-" + str(dday) if dday > 0 else "D-Day!" if dday == 0 else "마감"}</div>
        <p style="opacity: 0.7; font-size: 0.95rem;">서류 마감 2026.02.24</p>
    </div>
    """, unsafe_allow_html=True)

    # 핵심 메시지 (손실 회피 + 앵커링)
    st.markdown("""
    <div class="motto">
        <span>서류 탈락 67%</span>는 첫 문장에서 결정됩니다.<br>
        면접관의 진짜 질문: <span>"이 사람과 12시간 비행해도 될까?"</span>
    </div>
    """, unsafe_allow_html=True)

    # 긴급성 메시지 (손실 회피)
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fef3c7, #fef9c3); border-radius: 12px; padding: 1rem 1.5rem; border-left: 4px solid #f59e0b; margin-bottom: 2rem; text-align: center;">
        <p style="margin: 0; color: #92400e; font-size: 1rem;">
            ⚠️ <strong>지금 시작하지 않으면</strong>, 마감일에 후회합니다.
            합격자들은 평균 <strong>6주 전</strong>부터 준비했습니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 3가지 핵심 기능
    st.markdown("### 핵심 기능")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📝</div>
            <div class="feature-title">자소서 첨삭</div>
            <div class="feature-desc">
                <span style="color: #ef4444; font-weight: 600;">탈락 패턴 분석</span><br>
                면접관이 3초 만에<br>넘기는 자소서 vs 합격 자소서
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("자소서 점검하기", use_container_width=True, key="btn1"):
            st.switch_page("pages/2_📝_자소서첨삭.py")

    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📰</div>
            <div class="feature-title">기업분석</div>
            <div class="feature-desc">
                <span style="color: #ef4444; font-weight: 600;">면접 출현율 94%</span><br>
                KE Way 모르면<br>즉시 감점
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("필수 정보 확인", use_container_width=True, key="btn2"):
            st.switch_page("pages/3_📰_기업분석_뉴스.py")

    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">질문하기</div>
            <div class="feature-desc">
                <span style="color: #3b82f6; font-weight: 600;">합격자 질문 TOP 10</span><br>
                같은 고민 했던<br>선배들의 해결법
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("궁금한 거 물어보기", use_container_width=True, key="btn3"):
            st.switch_page("pages/6_💬_AI챗봇.py")

    st.markdown("---")

    # KE Way
    st.markdown("### KE Way")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="ke-way">
            <h3>Beyond Excellence</h3>
            <p>최고 수준의 안전과 서비스로<br>고객 기대를 뛰어넘는다</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="ke-way">
            <h3>Journey Together</h3>
            <p>고객, 직원, 파트너와<br>함께 성장한다</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="ke-way">
            <h3>Better Tomorrow</h3>
            <p>지속 가능한 미래를 위해<br>책임 있게 행동한다</p>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="footer">
        <strong>FlyReady Lab</strong><br>
        본 서비스는 대한항공 공식 서비스가 아닙니다.<br>
        <a href="https://recruit.koreanair.com" target="_blank">대한항공 채용 페이지</a>에서 최신 정보를 확인하세요.
    </div>
    """, unsafe_allow_html=True)


# 사이드바 (진행률 효과 + 손실 회피)
with st.sidebar:
    dday = calculate_dday()
    if dday > 0:
        # D-Day에 따른 긴급성 색상
        urgency_color = "#ef4444" if dday <= 7 else "#f59e0b" if dday <= 14 else "#00256C"
        st.markdown(f"""
        <div class="sidebar-dday" style="background: linear-gradient(135deg, {urgency_color}, #0078D4);">
            <div style="font-size: 0.9rem; opacity: 0.9;">{'🚨 마감 임박!' if dday <= 7 else '서류 마감까지'}</div>
            <div class="sidebar-dday-num">D-{dday}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### ✅ 오늘의 체크리스트")
    check1 = st.checkbox("자소서 수정")
    check2 = st.checkbox("KE Way 암기")
    check3 = st.checkbox("예상 질문 준비")

    completed = sum([check1, check2, check3])
    if completed == 3:
        st.success("🎉 오늘 할 일 완료!")
    elif completed > 0:
        st.info(f"📊 {completed}/3 완료 - 조금만 더!")
    else:
        st.warning("⚠️ 오늘 하나라도 시작하세요")

    st.markdown("---")
    st.markdown("### 🚨 이것만은 외워가세요")
    st.markdown("""
    <div style="background: #00256C; color: white; padding: 1rem; border-radius: 8px; font-size: 0.85rem;">
        <strong style="color: #C4A661;">KE Way</strong><br>
        1. Beyond Excellence<br>
        2. Journey Together<br>
        3. Better Tomorrow<br><br>
        <strong style="color: #C4A661;">면접 출현율 94%</strong>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
