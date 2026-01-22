# pages/15_국민체력.py
# 국민체력100 팁 - 항공사별 요구등급 및 운동 가이드

import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_tester_password

st.set_page_config(page_title="국민체력 가이드", page_icon="💪", layout="wide")

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="국민체력")
except ImportError:
    pass

st.markdown('<meta name="google" content="notranslate"><style>html{translate:no;}</style>', unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# 비밀번호
check_tester_password()

# CSS
st.markdown("""
<style>
.grade-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 10px 0;
}
.grade-1 { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.grade-2 { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.grade-3 { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
.exercise-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border-left: 4px solid #667eea;
}
.airline-req {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)

# ========================================
# 메인
# ========================================
st.title("💪 국민체력100 가이드")
st.markdown("항공사 입사에 필요한 체력 기준과 운동 팁!")

st.info("💡 **국민체력100**은 국민체육진흥공단에서 운영하는 체력인증 시스템입니다. 전국 체력인증센터에서 무료로 측정 가능합니다.")

# 탭
tab1, tab2, tab3, tab4 = st.tabs(["✈️ 항공사별 요구사항", "📊 등급 기준표", "🏃 운동 가이드", "📍 인증센터"])

# ========================================
# 탭1: 항공사별 요구사항
# ========================================
with tab1:
    st.markdown("### ✈️ 항공사별 체력 요구사항")

    st.warning("⚠️ 체력 기준은 채용 시기마다 변경될 수 있습니다. 반드시 공식 채용공고를 확인하세요.")

    # 체력 필수 항공사
    st.markdown("#### 🏋️ 체력측정 필수 항공사")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="airline-req">
            <h4>🛫 파라타항공</h4>
            <p><strong>요구사항:</strong> 국민체력100 체력평가 결과서 제출 <span style="color: #dc3545; font-weight: bold;">필수</span></p>
            <p><strong>제출 시기:</strong> 서류전형 시</p>
            <p><strong>권장 등급:</strong> 2등급 이상</p>
            <hr>
            <small>💡 신생 항공사로 체력 기준을 엄격하게 적용</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="airline-req">
            <h4>🛫 에어프레미아</h4>
            <p><strong>요구사항:</strong> 자체 체력측정 실시</p>
            <p><strong>측정 항목:</strong> 악력, 윗몸일으키기, 버피테스트, 유연성, 암리치</p>
            <p><strong>측정 시기:</strong> 컬처핏 면접 시</p>
            <hr>
            <small>💡 장거리 노선 특화로 체력 중시</small>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="airline-req">
            <h4>🛫 이스타항공</h4>
            <p><strong>요구사항:</strong> 자체 체력시험 실시</p>
            <p><strong>측정 항목:</strong> 오래달리기, 높이뛰기, 목소리 데시벨</p>
            <p><strong>측정 시기:</strong> 체력TEST 단계</p>
            <hr>
            <small>💡 2025년부터 채용 절차에 체력시험 도입</small>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="airline-req">
            <h4>🛫 대한항공</h4>
            <p><strong>요구사항:</strong> 수영 25m 완영 <span style="color: #dc3545; font-weight: bold;">필수</span></p>
            <p><strong>측정 시기:</strong> 건강검진 단계</p>
            <p><strong>기타:</strong> 별도 체력인증 불필요</p>
            <hr>
            <small>💡 수영 능력만 별도 검증</small>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 체력 권장 항공사
    st.markdown("#### 💪 체력 우수자 우대 항공사")

    st.markdown("""
    | 항공사 | 체력 관련 사항 | 비고 |
    |--------|---------------|------|
    | 아시아나항공 | 수영 테스트 포함 | 건강검진 단계 |
    | 진에어 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 제주항공 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 티웨이항공 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 에어부산 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 에어서울 | 별도 체력측정 없음 | 기본 체력 권장 |
    | 에어로케이 | 안전분야 자격 우대 | 체력 관련 자격 우대 |
    """)

    st.success("💡 **팁:** 체력측정이 필수가 아니더라도, 국민체력100 인증을 받아두면 자기소개서와 면접에서 어필할 수 있습니다!")

# ========================================
# 탭2: 등급 기준표
# ========================================
with tab2:
    st.markdown("### 📊 국민체력100 등급 기준표")

    st.info("📌 국민체력100은 7개 항목을 측정하여 종합 등급을 부여합니다. 아래는 20대 여성 기준입니다.")

    # 등급 설명
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="grade-card grade-1">
            <h2>1등급</h2>
            <p>상위 10% 이내</p>
            <p style="font-size: 14px;">매우 우수</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="grade-card grade-2">
            <h2>2등급</h2>
            <p>상위 11~35%</p>
            <p style="font-size: 14px;">우수</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="grade-card grade-3">
            <h2>3등급</h2>
            <p>상위 36~65%</p>
            <p style="font-size: 14px;">보통</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 항목별 기준표
    st.markdown("#### 📋 항목별 등급 기준 (20대 여성)")

    st.markdown("##### 1. 근력 - 악력 (kg)")
    st.markdown("""
    | 등급 | 19세 | 20-24세 | 25-29세 |
    |------|------|---------|---------|
    | **1등급** | 32.0 이상 | 31.5 이상 | 31.0 이상 |
    | **2등급** | 27.0~31.9 | 26.5~31.4 | 26.0~30.9 |
    | **3등급** | 23.0~26.9 | 22.5~26.4 | 22.0~25.9 |
    """)

    st.markdown("##### 2. 근지구력 - 윗몸일으키기 (회/60초)")
    st.markdown("""
    | 등급 | 19세 | 20-24세 | 25-29세 |
    |------|------|---------|---------|
    | **1등급** | 45 이상 | 43 이상 | 40 이상 |
    | **2등급** | 35~44 | 33~42 | 30~39 |
    | **3등급** | 25~34 | 23~32 | 20~29 |
    """)

    st.markdown("##### 3. 유연성 - 앉아 윗몸 앞으로 굽히기 (cm)")
    st.markdown("""
    | 등급 | 19세 | 20-24세 | 25-29세 |
    |------|------|---------|---------|
    | **1등급** | 20.0 이상 | 19.5 이상 | 19.0 이상 |
    | **2등급** | 14.0~19.9 | 13.5~19.4 | 13.0~18.9 |
    | **3등급** | 8.0~13.9 | 7.5~13.4 | 7.0~12.9 |
    """)

    st.markdown("##### 4. 심폐지구력 - 왕복오래달리기 (회)")
    st.markdown("""
    | 등급 | 19세 | 20-24세 | 25-29세 |
    |------|------|---------|---------|
    | **1등급** | 55 이상 | 52 이상 | 48 이상 |
    | **2등급** | 40~54 | 37~51 | 33~47 |
    | **3등급** | 25~39 | 22~36 | 18~32 |
    """)

    st.markdown("##### 5. 순발력 - 제자리멀리뛰기 (cm)")
    st.markdown("""
    | 등급 | 19세 | 20-24세 | 25-29세 |
    |------|------|---------|---------|
    | **1등급** | 195 이상 | 190 이상 | 185 이상 |
    | **2등급** | 170~194 | 165~189 | 160~184 |
    | **3등급** | 145~169 | 140~164 | 135~159 |
    """)

    st.markdown("##### 6. 민첩성 - 10m 왕복달리기 (초, 낮을수록 좋음)")
    st.markdown("""
    | 등급 | 19세 | 20-24세 | 25-29세 |
    |------|------|---------|---------|
    | **1등급** | 7.8 이하 | 7.9 이하 | 8.0 이하 |
    | **2등급** | 7.9~8.5 | 8.0~8.6 | 8.1~8.7 |
    | **3등급** | 8.6~9.2 | 8.7~9.3 | 8.8~9.4 |
    """)

    st.markdown("##### 7. BMI (kg/m²)")
    st.markdown("""
    | 등급 | 기준 |
    |------|------|
    | **1등급** | 18.5 ~ 22.9 |
    | **2등급** | 17.0~18.4 또는 23.0~24.9 |
    | **3등급** | 25.0 이상 또는 17.0 미만 |
    """)

    st.caption("※ 위 기준은 참고용이며, 정확한 기준은 국민체력100 공식 사이트에서 확인하세요.")

# ========================================
# 탭3: 운동 가이드
# ========================================
with tab3:
    st.markdown("### 🏃 항목별 운동 가이드")

    st.success("💡 2~3개월 꾸준히 훈련하면 1~2등급 달성 가능합니다!")

    # 악력
    st.markdown("""
    <div class="exercise-card">
        <h4>💪 악력 향상</h4>
        <p><strong>목표:</strong> 30kg 이상</p>
        <hr>
        <p><strong>추천 운동:</strong></p>
        <ul>
            <li>악력기 사용 (하루 3세트 x 20회)</li>
            <li>수건 짜기 운동</li>
            <li>손가락 스트레칭</li>
            <li>암벽등반 (보울더링)</li>
        </ul>
        <p><strong>팁:</strong> 양손 균형있게 훈련, 매일 5분씩!</p>
    </div>
    """, unsafe_allow_html=True)

    # 윗몸일으키기
    st.markdown("""
    <div class="exercise-card">
        <h4>🔥 윗몸일으키기</h4>
        <p><strong>목표:</strong> 60초에 40회 이상</p>
        <hr>
        <p><strong>추천 운동:</strong></p>
        <ul>
            <li>플랭크 (1분 x 3세트)</li>
            <li>크런치 (20회 x 3세트)</li>
            <li>레그레이즈 (15회 x 3세트)</li>
            <li>러시안 트위스트</li>
        </ul>
        <p><strong>팁:</strong> 반동 없이 복근 힘만으로! 속도보다 정확한 자세가 중요!</p>
    </div>
    """, unsafe_allow_html=True)

    # 유연성
    st.markdown("""
    <div class="exercise-card">
        <h4>🧘 유연성 (앉아 윗몸 앞으로 굽히기)</h4>
        <p><strong>목표:</strong> 15cm 이상</p>
        <hr>
        <p><strong>추천 운동:</strong></p>
        <ul>
            <li>햄스트링 스트레칭 (매일 아침/저녁)</li>
            <li>고관절 스트레칭</li>
            <li>요가 (다운독, 전굴 자세)</li>
            <li>폼롤러 마사지</li>
        </ul>
        <p><strong>팁:</strong> 따뜻한 상태에서 스트레칭! 샤워 후가 효과적!</p>
    </div>
    """, unsafe_allow_html=True)

    # 왕복오래달리기
    st.markdown("""
    <div class="exercise-card">
        <h4>🏃‍♀️ 왕복오래달리기 (셔틀런)</h4>
        <p><strong>목표:</strong> 50회 이상</p>
        <hr>
        <p><strong>추천 운동:</strong></p>
        <ul>
            <li>인터벌 달리기 (30초 전력 + 30초 휴식) x 10세트</li>
            <li>계단 오르기</li>
            <li>점프 스쿼트 (20회 x 3세트)</li>
            <li>버피테스트 (10회 x 3세트)</li>
        </ul>
        <p><strong>팁:</strong> 심폐지구력이 가장 오래 걸림! 최소 4주 이상 꾸준히!</p>
    </div>
    """, unsafe_allow_html=True)

    # 제자리멀리뛰기
    st.markdown("""
    <div class="exercise-card">
        <h4>🦘 제자리멀리뛰기</h4>
        <p><strong>목표:</strong> 180cm 이상</p>
        <hr>
        <p><strong>추천 운동:</strong></p>
        <ul>
            <li>스쿼트 점프 (15회 x 3세트)</li>
            <li>런지 점프</li>
            <li>박스 점프</li>
            <li>줄넘기 (이중 뛰기)</li>
        </ul>
        <p><strong>팁:</strong> 팔 스윙과 함께! 착지 시 무릎 살짝 굽히기!</p>
    </div>
    """, unsafe_allow_html=True)

    # 10m 왕복달리기
    st.markdown("""
    <div class="exercise-card">
        <h4>⚡ 10m 왕복달리기 (민첩성)</h4>
        <p><strong>목표:</strong> 8.0초 이하</p>
        <hr>
        <p><strong>추천 운동:</strong></p>
        <ul>
            <li>래더 드릴 (사다리 훈련)</li>
            <li>콘 터치 훈련</li>
            <li>셔플 스텝</li>
            <li>방향 전환 연습</li>
        </ul>
        <p><strong>팁:</strong> 방향 전환 시 무게 중심 낮추기! 발 빠르게!</p>
    </div>
    """, unsafe_allow_html=True)

    # 버피테스트 (에어프레미아)
    st.markdown("---")
    st.markdown("#### 🌟 에어프레미아 체력측정 대비")

    st.markdown("""
    <div class="exercise-card" style="border-left-color: #f093fb;">
        <h4>🔥 버피테스트</h4>
        <p>에어프레미아 체력측정 항목</p>
        <hr>
        <p><strong>동작 순서:</strong></p>
        <ol>
            <li>서서 시작</li>
            <li>스쿼트 자세로 손 바닥 짚기</li>
            <li>플랭크 자세로 점프</li>
            <li>푸시업 1회</li>
            <li>다리 당겨 스쿼트 자세</li>
            <li>점프하며 손 위로</li>
        </ol>
        <p><strong>훈련:</strong> 1분에 15개 목표로 매일 3세트!</p>
    </div>
    """, unsafe_allow_html=True)

    # 주간 운동 계획
    st.markdown("---")
    st.markdown("#### 📅 주간 운동 계획 예시")

    st.markdown("""
    | 요일 | 운동 내용 | 시간 |
    |------|----------|------|
    | **월** | 근력 (악력, 윗몸일으키기) + 유연성 | 40분 |
    | **화** | 심폐지구력 (인터벌 달리기) | 30분 |
    | **수** | 휴식 + 가벼운 스트레칭 | 20분 |
    | **목** | 순발력 (점프 운동) + 민첩성 | 40분 |
    | **금** | 심폐지구력 (셔틀런 연습) | 30분 |
    | **토** | 전체 항목 모의 테스트 | 60분 |
    | **일** | 완전 휴식 | - |
    """)

# ========================================
# 탭4: 인증센터
# ========================================
with tab4:
    st.markdown("### 📍 국민체력100 인증센터")

    st.info("💡 전국 300여개 인증센터에서 **무료**로 체력측정이 가능합니다!")

    st.markdown("""
    #### 🔍 인증센터 찾기

    **공식 사이트:** [국민체력100](https://nfa.kspo.or.kr/)

    #### 📋 측정 절차
    1. **예약**: 국민체력100 홈페이지/앱에서 가까운 센터 예약
    2. **방문**: 예약 시간에 센터 방문 (운동복, 실내화 지참)
    3. **측정**: 7개 항목 체력측정 (약 1시간)
    4. **결과**: 측정 후 즉시 결과 확인 + 인증서 발급

    #### 💰 비용
    - **무료** (1회/연)
    - 추가 측정 시 소정의 비용 발생할 수 있음

    #### 📄 결과서 발급
    - 측정 완료 후 **체력인증서** 즉시 발급
    - PDF 다운로드 또는 출력 가능
    - 파라타항공 제출용으로 활용
    """)

    st.markdown("---")

    st.markdown("#### 🗺️ 주요 지역 인증센터")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **서울**
        - 서울올림픽기념국민체육진흥공단
        - 각 구민체육센터

        **경기**
        - 수원시체육회관
        - 성남시민체육관
        - 고양시체육관

        **인천**
        - 인천시체육회
        - 계양체육관
        """)

    with col2:
        st.markdown("""
        **부산**
        - 부산시체육회
        - 해운대스포츠센터

        **대구**
        - 대구시체육회
        - 수성구체육관

        **기타**
        - 전국 대학교 체육관
        - 국민체육센터
        """)

    st.warning("⚠️ 인증센터별 운영 시간이 다르니 반드시 예약 후 방문하세요!")

    # QR 코드 대신 링크
    st.markdown("---")
    st.link_button("🔗 국민체력100 공식 사이트 바로가기", "https://nfa.kspo.or.kr/", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)
