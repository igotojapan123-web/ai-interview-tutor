# pages/20_자소서첨삭.py
# AI 기반 자기소개서 첨삭 - 재첨삭 + 예시 + 키워드 + 버전비교 + 문장분석

import os
import json
import re
import streamlit as st
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES_WITH_RESUME
from sidebar_common import init_page, end_page
from logging_config import get_logger

# 로거 설정
logger = get_logger(__name__)

# Phase C1: 자소서 고도화 모듈
try:
    from resume_enhancer import (
        analyze_resume_enhanced,
        get_sentence_analysis,
        get_keyword_density,
        get_storytelling_score,
        compare_with_passed_resume,
        AIRLINE_KEYWORD_DATA,
    )
    RESUME_ENHANCER_AVAILABLE = True
except ImportError:
    RESUME_ENHANCER_AVAILABLE = False

# Initialize page with new layout
init_page(
    title="AI 자소서 첨삭",
    current_page="자소서첨삭",
    wide_layout=True
)


# Streamlit Material Icon 텍스트 숨김
st.markdown("""
<style>
/* Material Icon 텍스트 폴백 숨김 - 정확한 타겟 */
[data-testid="stIconMaterial"] {
    font-size: 0 !important;
    line-height: 0 !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# OpenAI API (캐시된 싱글톤)
# ----------------------------
@st.cache_resource
def get_openai_client():
    """OpenAI 클라이언트 싱글톤 (앱 재시작 전까지 재사용)"""
    try:
        from openai import OpenAI
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except ImportError as e:
        logger.error(f"OpenAI 모듈 import 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI 클라이언트 초기화 실패: {e}")
        return None

client = get_openai_client()
API_AVAILABLE = client is not None

# ----------------------------
# 데이터 경로
# ----------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RESUME_FILE = os.path.join(DATA_DIR, "my_resumes.json")
os.makedirs(DATA_DIR, exist_ok=True)


@st.cache_data(ttl=60)
def load_my_resumes():
    """저장된 자소서 목록 로드"""
    try:
        if os.path.exists(RESUME_FILE):
            with open(RESUME_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"자소서 JSON 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"자소서 로드 실패: {e}")
    return []


def save_my_resumes(resumes):
    with open(RESUME_FILE, "w", encoding="utf-8") as f:
        json.dump(resumes, f, ensure_ascii=False, indent=2)
    load_my_resumes.clear()  # 캐시 무효화


# ----------------------------
# 항공사별 핵심 키워드
# ----------------------------
# 항공사 공식 자료 기반 핵심 키워드 (2025년 기준)
AIRLINE_KEYWORDS = {
    "대한항공": {
        "인재상": ["진취성", "국제감각", "서비스정신", "성실", "팀워크"],
        "가치": ["Excellence in Flight", "KE Way", "Beyond Excellence", "Journey Together", "Better Tomorrow"],
        "추천키워드": ["글로벌 역량", "도전 정신", "전문성", "팀워크", "안전 의식", "프리미엄 서비스", "신뢰"],
    },
    "아시아나항공": {
        "인재상": ["고객중심", "안전의식", "서비스마인드", "글로벌역량"],
        "가치": ["Beautiful People, Asiana", "안전", "서비스", "지속가능성", "ESG"],
        "추천키워드": ["고객 감동", "세심한 배려", "안전 문화", "팀 협업", "서비스 정신", "Better flight, Better tomorrow"],
    },
    "진에어": {
        "인재상": ["실용적", "고객친화", "유쾌함", "안전의식", "독창성"],
        "가치": ["Fly, better fly", "Safety", "Practicality", "Customer Service", "Delight"],
        "추천키워드": ["JINIABLE", "유쾌함", "실용성", "고객 친화", "안전", "트렌디", "창의적 서비스"],
    },
    "제주항공": {
        "인재상": ["안전의식", "고객지향", "팀워크", "도전정신", "비용의식"],
        "가치": ["Fun & Fly", "7C", "안전", "저비용", "신뢰", "팀워크", "도전"],
        "추천키워드": ["고객 중심", "효율", "도전", "팀워크", "신뢰", "긍정", "Confident"],
    },
    "티웨이항공": {
        "인재상": ["안전최우선", "스마트함", "고객만족", "나눔", "지속가능"],
        "가치": ["I want T'way", "5S: Safety, Smart, Satisfaction, Sharing, Sustainability"],
        "추천키워드": ["안전", "스마트", "고객만족", "나눔", "지속가능", "친절", "사회공헌"],
    },
    "에어부산": {
        "인재상": ["안전의식", "지역친화", "서비스마인드", "효율성"],
        "가치": ["FLY SMART", "안전운항", "산업안전", "정보보안"],
        "추천키워드": ["스마트", "지역 사랑", "안전", "효율", "고객 감동", "부산", "팀워크"],
    },
    "에어서울": {
        "인재상": ["안전의식", "친절함", "신뢰성", "활력"],
        "가치": ["It's mint time", "최고안전", "행복서비스", "신뢰"],
        "추천키워드": ["민트", "상쾌함", "안전", "친절", "젊음", "신뢰", "아시아나계열"],
    },
    "이스타항공": {
        "인재상": ["고객지향", "도전정신", "사회공헌", "글로벌마인드"],
        "가치": ["Fly with EASTAR", "항공여행 대중화", "사회공익", "글로벌 국민항공사"],
        "추천키워드": ["도전", "재도약", "고객 행복", "대중화", "글로벌", "적응력", "열정"],
    },
    "에어프레미아": {
        "인재상": ["프리미엄서비스", "글로벌역량", "전문성", "고객중심"],
        "가치": ["Premium for all", "HSC (Hybrid Service Carrier)", "B787-9", "중장거리"],
        "추천키워드": ["프리미엄", "하이브리드", "전문성", "글로벌", "장거리", "체력", "차별화"],
    },
    "에어로케이": {
        "인재상": ["도전정신", "유연성", "성장지향", "안전의식"],
        "가치": ["새로운 하늘길", "청주기반", "A320 단일기종", "신생항공사"],
        "추천키워드": ["도전", "성장", "유연성", "안전", "청주", "기회", "열정"],
    },
    "파라타항공": {
        "인재상": ["신뢰 구축 역량", "변화 적응력", "새 기준 수용", "고객 가치 중심"],
        "가치": ["Fly new", "안전과 정시성", "투명함", "쾌적함", "고객가치 최우선", "도전과 혁신"],
        "추천키워드": ["신뢰", "투명함", "도전", "혁신", "적응력", "양양", "재출범"],
    },
}

# ----------------------------
# 자소서 항목별 가이드 + 예시
# ----------------------------
RESUME_ITEMS = {
    "지원동기": {
        "description": "왜 이 항공사에 지원했는지",
        "tips": [
            "항공사의 특징/가치와 본인의 가치관 연결",
            "구체적인 경험이나 계기 언급",
            "단순히 '승무원이 꿈'이 아닌 깊이 있는 이유"
        ],
        "bad_examples": ["어릴 때부터 승무원이 꿈이었습니다", "비행기를 좋아해서"],
        "max_chars": 500,
        "good_examples": [
            {
                "title": "구체적 경험 + 항공사 가치 연결",
                "content": "대학교 3학년 때 교환학생으로 독일에서 생활하며 다양한 문화권의 친구들과 소통하는 즐거움을 알게 되었습니다. 귀국 항공편에서 만난 승무원분이 불안해하는 외국인 승객에게 영어와 간단한 독일어로 따뜻하게 안내하는 모습에 깊은 인상을 받았습니다. 그 순간 '서비스란 단순한 업무가 아니라 사람과 사람을 연결하는 것'이라는 깨달음을 얻었고, 이것이 귀사의 'Connecting for a better world'라는 미션과 정확히 맞닿아 있다고 느꼈습니다.",
                "why_good": "구체적 에피소드 → 깨달음 → 항공사 미션과 자연스럽게 연결"
            },
            {
                "title": "직무 이해 + 진정성",
                "content": "호텔 프론트에서 2년간 근무하며 다양한 국적의 고객을 응대했습니다. 특히 불편사항을 해결해드린 후 감사 이메일을 받을 때마다 '이 일이 나에게 맞다'고 확신했습니다. 승무원은 제한된 공간과 시간 안에서 고객에게 최상의 경험을 제공해야 하는 더 높은 차원의 서비스 직무라고 생각합니다. 호텔에서 쌓은 응대 역량을 기내라는 특수한 환경에서 발휘하고 싶습니다.",
                "why_good": "관련 경험의 구체적 성과 → 직무 이해도 → 성장 의지"
            },
        ],
    },
    "성격의 장단점": {
        "description": "본인의 성격 특성과 극복 노력",
        "tips": [
            "장점: 서비스 직무와 연결되는 특성",
            "단점: 극복 노력과 성장 과정 필수",
            "구체적인 에피소드로 증명"
        ],
        "bad_examples": ["성격이 밝습니다", "완벽주의가 단점입니다"],
        "max_chars": 500,
        "good_examples": [
            {
                "title": "장점을 에피소드로 증명",
                "content": "저의 장점은 '상대방의 불편함을 먼저 알아채는 관찰력'입니다. 카페 아르바이트 시절, 한 어르신이 메뉴판을 오래 보고 계셔서 다가가 인기 메뉴를 추천드렸더니 '눈치가 참 빠르다'며 단골이 되셨습니다. 단점은 새로운 일을 시작할 때 지나치게 준비하려는 성향입니다. 이를 개선하기 위해 '80%면 시작하자'는 규칙을 만들었고, 완벽한 계획보다 빠른 실행과 수정이 더 좋은 결과를 만든다는 것을 배웠습니다.",
                "why_good": "장점: 구체적 에피소드 → 단점: 인정 + 개선 방법 + 배운 점"
            },
        ],
    },
    "서비스 경험": {
        "description": "고객 응대 및 서비스 관련 경험",
        "tips": [
            "STAR 기법 활용 (상황-과제-행동-결과)",
            "어려운 고객 대응 경험이면 더 좋음",
            "배운 점과 성장 포인트 명시"
        ],
        "bad_examples": ["카페에서 일했습니다", "친절하게 응대했습니다"],
        "max_chars": 600,
        "good_examples": [
            {
                "title": "STAR 기법 완벽 적용",
                "content": "[상황] 백화점 안내데스크에서 근무하던 중, 외국인 관광객 가족이 아이를 잃어버려 매우 당황한 상태로 찾아왔습니다. [과제] 언어 소통이 제한된 상황에서 빠르게 아이를 찾아야 했습니다. [행동] 먼저 침착하게 번역 앱으로 아이의 인상착의를 확인하고, 각 층 담당자에게 즉시 무전 연락했습니다. 동시에 부모님께 물을 드리며 안심시켜 드렸습니다. [결과] 5분 만에 3층 장난감 매장에서 아이를 찾았고, 가족은 울며 감사를 표했습니다. 이후 외국인 응대 매뉴얼을 제안하여 팀 전체에 공유했습니다.",
                "why_good": "STAR 구조 명확 + 위기 대응력 + 후속 개선 활동까지"
            },
        ],
    },
    "팀워크/협업": {
        "description": "팀으로 일한 경험과 본인의 역할",
        "tips": [
            "갈등 상황과 해결 과정",
            "본인의 구체적인 역할과 기여",
            "팀 성과와 개인 성장 연결"
        ],
        "bad_examples": ["팀 프로젝트를 잘 했습니다", "화합을 중요시합니다"],
        "max_chars": 600,
        "good_examples": [
            {
                "title": "갈등 해결 + 본인 역할 명확",
                "content": "대학 졸업 전시를 준비할 때, 6명의 팀원 중 2명이 방향성 차이로 심하게 대립했습니다. 저는 중재자 역할을 자처하여 각자의 의견을 개별적으로 들은 후, 두 아이디어의 공통점을 찾아 절충안을 제시했습니다. '둘 다 관객 참여를 원한다'는 접점을 발견하고, 이를 중심으로 재구성했습니다. 결과적으로 관객 투표 1위를 차지했고, 팀원들에게 '네가 없었으면 공중분해됐을 것'이라는 말을 들었습니다. 갈등은 서로 다른 열정의 충돌이며, 조율이 곧 팀의 힘이라는 것을 배웠습니다.",
                "why_good": "구체적 갈등 상황 → 본인의 역할(중재) → 성과 + 배운 점"
            },
        ],
    },
    "입사 후 포부": {
        "description": "입사 후 어떤 승무원이 될 것인지",
        "tips": [
            "구체적이고 실현 가능한 목표",
            "항공사 비전과 연결",
            "단기/장기 목표 구분"
        ],
        "bad_examples": ["최고의 승무원이 되겠습니다", "열심히 하겠습니다"],
        "max_chars": 400,
        "good_examples": [
            {
                "title": "단기/장기 목표 + 구체적 실행 계획",
                "content": "입사 후 1년간은 안전 업무와 기내 서비스의 기본기를 완벽히 익히는 데 집중하겠습니다. 선배 승무원들의 노하우를 매 비행 후 기록하며 나만의 서비스 매뉴얼을 만들겠습니다. 3년 차에는 중국어 능력을 HSK 5급까지 향상시켜 중화권 노선 전문 승무원으로 성장하겠습니다. 궁극적으로는 신입 교육에 참여하여 제가 받은 도움을 후배들에게 돌려주는 선순환을 만들고 싶습니다.",
                "why_good": "시기별 구체적 목표 + 실행 방법 + 장기 비전까지"
            },
        ],
    },
}


# ----------------------------
# AI 첨삭 함수
# ----------------------------
def get_ai_feedback(airline, item_type, content, prev_feedback=None):
    """AI 자소서 첨삭 (재첨삭 시 이전 피드백 참조)"""
    if not API_AVAILABLE:
        return None

    item_info = RESUME_ITEMS.get(item_type, {})
    keywords = AIRLINE_KEYWORDS.get(airline, {})

    re_review = ""
    if prev_feedback:
        re_review = f"""
이것은 재첨삭 요청입니다. 이전 첨삭 피드백은 다음과 같았습니다:
---
{prev_feedback}
---
이전 피드백을 반영하여 얼마나 개선되었는지도 평가해주세요.
개선된 부분은 칭찬하고, 아직 부족한 부분은 추가 조언해주세요.
"""

    keyword_info = ""
    if keywords:
        keyword_info = f"""
이 항공사의 인재상 키워드: {', '.join(keywords.get('인재상', []))}
핵심 가치: {', '.join(keywords.get('가치', []))}
추천 키워드: {', '.join(keywords.get('추천키워드', []))}
"""

    system_prompt = f"""당신은 10년 경력의 항공사 인사담당자입니다.
{airline} 객실승무원 채용 자기소개서를 첨삭해주세요.

항목: {item_type}
항목 설명: {item_info.get('description', '')}
{keyword_info}
{re_review}

첨삭 기준:
1. 구체성: 추상적 표현 → 구체적 경험/수치
2. 진정성: 진부한 표현 → 본인만의 이야기
3. 연결성: 직무/항공사와의 연결
4. 키워드: 항공사 인재상 키워드 반영 여부
5. 문장력: 문법, 맞춤법, 가독성

피드백 형식:
## 총평
(전반적인 평가 2-3문장)

## 점수: X/100점

## 좋은 점
- (구체적으로)

## 개선할 점
- (구체적으로 + 수정 예시)

## 키워드 분석
- 포함된 키워드: ...
- 추가 추천 키워드: ...

## 수정 제안
(실제 수정된 버전 제시)
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"다음 자소서를 첨삭해주세요:\n\n{content}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"오류 발생: {str(e)}"


def extract_score(feedback):
    """피드백에서 점수 추출"""
    if not feedback:
        return None
    match = re.search(r'(\d{1,3})\s*/\s*100', feedback)
    if match:
        return int(match.group(1))
    return None


# ----------------------------
# 문장 분석 함수
# ----------------------------
def analyze_text(content):
    """텍스트 실시간 분석"""
    if not content:
        return {}

    chars = len(content)
    chars_no_space = len(content.replace(" ", "").replace("\n", ""))
    sentences = [s.strip() for s in re.split(r'[.!?。]\s*', content) if s.strip()]
    sentence_count = len(sentences)
    avg_sentence_len = chars_no_space / max(sentence_count, 1)

    # ~습니다 반복 체크
    formal_endings = len(re.findall(r'습니다|했습니다|됩니다|겠습니다|있습니다', content))

    # 접속사 반복
    conjunctions = len(re.findall(r'그리고|또한|그래서|하지만|그러나|따라서', content))

    # 1인칭 표현
    first_person = len(re.findall(r'저는|저의|제가|제 ', content))

    return {
        "chars": chars,
        "chars_no_space": chars_no_space,
        "sentences": sentence_count,
        "avg_sentence_len": round(avg_sentence_len, 1),
        "formal_endings": formal_endings,
        "conjunctions": conjunctions,
        "first_person": first_person,
    }


# ----------------------------
# CSS
# ----------------------------
st.markdown("""
<style>
/* 모든 입력 필드에서 복사/붙여넣기 허용 - 강화된 선택자 */
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

/* 전체 문서에서 텍스트 선택 허용 */
* {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}

/* 버튼과 특수 요소는 제외 */
button, .stButton, [role="button"] {
    -webkit-user-select: none !important;
    user-select: none !important;
}

/* 폰트 및 기본 스타일 */
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
* {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.keyword-tag {
    display: inline-block;
    background: #667eea20;
    border: 1px solid #667eea;
    color: #667eea;
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 13px;
    margin: 4px;
    line-height: 1.4;
}
.keyword-found {
    background: #28a74530;
    border-color: #28a745;
    color: #28a745;
    font-weight: bold;
}
.example-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 16px;
    margin: 10px 0;
    border-left: 4px solid #667eea;
}
.score-badge {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 14px;
}
.analysis-box {
    background: white;
    border-radius: 10px;
    padding: 12px 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    text-align: center;
    margin: 3px;
    min-width: 75px;
    word-break: keep-all;
}
.analysis-box div {
    line-height: 1.6;
    letter-spacing: -0.3px;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------
# UI 메인
# ----------------------------

st.markdown("---")

if not API_AVAILABLE:
    st.error("OpenAI API를 사용할 수 없습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")

# 탭 구성 (고도화 분석 탭 추가)
if RESUME_ENHANCER_AVAILABLE:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["️ 첨삭받기", " 고급 분석", " 합격 예시", " 작성 가이드", " 내 자소서"])
else:
    tab1, tab2, tab3, tab4 = st.tabs(["️ 첨삭받기", " 합격 예시", " 작성 가이드", " 내 자소서"])
    tab5 = None


# ========================================
# 탭1: 첨삭받기
# ========================================
with tab1:
    st.subheader("️ 자소서 첨삭받기")

    selected_airline = st.selectbox("지원 항공사", AIRLINES_WITH_RESUME)

    # 항공사 키워드 표시
    keywords = AIRLINE_KEYWORDS.get(selected_airline, {})
    if keywords:
        with st.expander("이 항공사 핵심 키워드"):
            kw_list = keywords.get("인재상", [])
            rec_list = keywords.get("추천키워드", [])
            val_list = keywords.get("가치", [])
            
            keywords_html = f"""
            <div translate="no" class="notranslate" lang="ko">
                <p style="font-weight:600; margin-bottom:8px;">인재상</p>
                <div style="margin-bottom:16px;">
                    {' '.join([f'<span class="keyword-tag">{k}</span>' for k in kw_list])}
                </div>
                <p style="font-weight:600; margin-bottom:8px;">추천 키워드</p>
                <div style="margin-bottom:16px;">
                    {' '.join([f'<span class="keyword-tag">{k}</span>' for k in rec_list])}
                </div>
                <p style="font-size:13px; color:#666;">핵심 가치: {', '.join(val_list)}</p>
            </div>
            """
            st.markdown(keywords_html, unsafe_allow_html=True)

    st.markdown("---")

    # 문항 개수 선택
    num_items = st.slider("문항 수 (1~5개)", min_value=1, max_value=5, value=1)

    # 각 문항별 질문 + 답변 입력
    questions = []
    answers = []
    all_valid = True

    for i in range(num_items):
        st.markdown(f"####  문항 {i+1}")

        q = st.text_input(
            f"질문 {i+1}",
            placeholder="예: 지원동기를 작성하세요 (500자 이내)",
            key=f"question_{i}",
            label_visibility="collapsed"
        )
        a = st.text_area(
            f"답변 {i+1}",
            height=200,
            placeholder="위 질문에 대한 답변을 작성하세요...",
            key=f"answer_{i}"
        )
        questions.append(q)
        answers.append(a)

        # 문장 분석 (실시간)
        if a and len(a) >= 10:
            analysis = analyze_text(a)
            cols = st.columns(6)
            with cols[0]:
                color = "#28a745" if 200 <= analysis["chars"] <= 800 else "#ffc107" if analysis["chars"] < 200 else "#dc3545"
                st.markdown(f'<div class="analysis-box"><div style="color:{color}; font-size:18px; font-weight:bold;">{analysis["chars"]}</div><div style="font-size:11px;">글자수</div></div>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f'<div class="analysis-box"><div style="font-size:18px; font-weight:bold;">{analysis["sentences"]}</div><div style="font-size:11px;">문장 수</div></div>', unsafe_allow_html=True)
            with cols[2]:
                avg_color = "#28a745" if 20 <= analysis["avg_sentence_len"] <= 40 else "#ffc107"
                st.markdown(f'<div class="analysis-box"><div style="color:{avg_color}; font-size:18px; font-weight:bold;">{analysis["avg_sentence_len"]}</div><div style="font-size:11px;">평균문장길이</div></div>', unsafe_allow_html=True)
            with cols[3]:
                fe_color = "#dc3545" if analysis["formal_endings"] > 5 else "#28a745"
                st.markdown(f'<div class="analysis-box"><div style="color:{fe_color}; font-size:18px; font-weight:bold;">{analysis["formal_endings"]}</div><div style="font-size:11px;">~습니다</div></div>', unsafe_allow_html=True)
            with cols[4]:
                st.markdown(f'<div class="analysis-box"><div style="font-size:18px; font-weight:bold;">{analysis["conjunctions"]}</div><div style="font-size:11px;">접속사</div></div>', unsafe_allow_html=True)
            with cols[5]:
                st.markdown(f'<div class="analysis-box"><div style="font-size:18px; font-weight:bold;">{analysis["first_person"]}</div><div style="font-size:11px;">1인칭</div></div>', unsafe_allow_html=True)

            # 키워드 매칭
            if keywords:
                rec_keywords = keywords.get("추천키워드", [])
                found = [k for k in rec_keywords if k in a]
                not_found = [k for k in rec_keywords if k not in a]
                if found:
                    found_html = " ".join([f'<span class="keyword-tag keyword-found"> {k}</span>' for k in found])
                    st.markdown(f"**포함된 키워드:** {found_html}", unsafe_allow_html=True)
                if not_found:
                    nf_html = " ".join([f'<span class="keyword-tag">{k}</span>' for k in not_found[:4]])
                    st.markdown(f"**추가 추천:** {nf_html}", unsafe_allow_html=True)

        # 유효성 체크
        if not q.strip() or len(a.strip()) < 50:
            all_valid = False

        if i < num_items - 1:
            st.markdown("---")

    # 버튼 영역
    st.markdown("---")
    col1, col2 = st.columns([3, 1])

    with col1:
        submit = st.button("AI 첨삭받기", type="primary", use_container_width=True, disabled=not all_valid)
    with col2:
        save_btn = st.button("저장", use_container_width=True, disabled=not all_valid)

    if not all_valid and any(q.strip() for q in questions):
        st.caption("️ 모든 문항에 질문을 입력하고, 답변은 50자 이상 작성해주세요.")

    if save_btn and all_valid:
        resumes = load_my_resumes()
        for i in range(num_items):
            resumes.append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S") + f"_{i}",
                "airline": selected_airline,
                "item": questions[i],
                "content": answers[i],
                "created_at": datetime.now().isoformat()
            })
        save_my_resumes(resumes)
        st.success("저장되었습니다!")

    # 첨삭 실행
    if submit and all_valid:
        with st.spinner("AI가 첨삭 중입니다..."):
            for i in range(num_items):
                st.markdown("---")
                st.markdown(f"###  문항 {i+1} 첨삭 결과")
                st.caption(f"질문: {questions[i]}")

                feedback = get_ai_feedback(selected_airline, questions[i], answers[i])

                if feedback:
                    current_score = extract_score(feedback)
                    st.markdown(feedback)

                    # 결과 자동 저장
                    resumes = load_my_resumes()
                    resumes.append({
                        "id": datetime.now().strftime("%Y%m%d%H%M%S") + f"_fb_{i}",
                        "airline": selected_airline,
                        "item": questions[i],
                        "content": answers[i],
                        "feedback": feedback,
                        "score": current_score,
                        "created_at": datetime.now().isoformat()
                    })
                    save_my_resumes(resumes)

            st.success("모든 문항 첨삭 완료! 결과가 자동 저장되었습니다.")

            # 자동 저장
            save_draft(
                selected_airline,
                "review",
                {
                    "questions": questions,
                    "answers": answers,
                }
            )

            # 다음 단계 버튼
            render_next_step_button("review", {
                "airline": selected_airline,
                "questions": questions,
                "answers": answers,
            })


# ========================================
# 탭2: 고급 분석 (Phase C1)
# ========================================
if RESUME_ENHANCER_AVAILABLE and tab5 is not None:
    with tab2:
        st.subheader(" 고급 자소서 분석")
        st.info("문장별 분석, 키워드 밀도, 스토리텔링 점수, 합격 자소서 비교 등 심층 분석을 받아보세요.")

        # 분석용 입력
        adv_airline = st.selectbox("지원 항공사", AIRLINES_WITH_RESUME, key="adv_airline_select")

        # 자소서 항목: 기본 옵션 + 직접 입력
        col_item1, col_item2 = st.columns([2, 1])
        with col_item1:
            item_options = list(RESUME_ITEMS.keys()) + ["직접 입력"]
            adv_item_select = st.selectbox("자소서 항목", item_options, key="adv_item_select")
        with col_item2:
            adv_question_count = st.number_input(
                "문항 수 (글자수 제한용)",
                min_value=1, max_value=10, value=1,
                help="같은 항목이 여러 문항인 경우 (예: 지원동기 500자 x 2문항)",
                key="adv_question_count"
            )

        # 직접 입력 선택시 텍스트 입력창 표시
        if adv_item_select == "직접 입력":
            adv_item_type = st.text_input(
                "항목명 직접 입력",
                placeholder="예: 입사 후 포부, 직무 관련 경험 등",
                key="adv_item_custom"
            )
            if not adv_item_type:
                adv_item_type = "기타"
        else:
            adv_item_type = adv_item_select

        adv_content = st.text_area(
            "자소서 내용",
            height=250,
            placeholder="분석할 자소서 내용을 입력하세요...",
            key="adv_content"
        )

        # 문항 수 표시
        if adv_question_count > 1:
            st.caption(f"  {adv_item_type} 항목 {adv_question_count}개 문항 분석")

        if st.button("고급 분석 시작", type="primary", use_container_width=True, disabled=len(adv_content) < 100):
            if len(adv_content) >= 100:
                with st.spinner("심층 분석 중..."):
                    analysis = analyze_resume_enhanced(adv_content, adv_airline, adv_item_type)

                # 등급 및 점수 표시
                grade = analysis.get("grade", "N/A")
                total_score = analysis.get("total_score", 0)
                grade_colors = {"S": "#FFD700", "A": "#4CAF50", "B": "#2196F3", "C": "#FF9800", "D": "#f44336"}
                grade_color = grade_colors.get(grade, "#6b7280")

                st.markdown(f"""
                <div style="text-align: center; padding: 25px; background: {grade_color}15; border-radius: 15px; margin: 20px 0;">
                    <div style="font-size: 60px; font-weight: bold; color: {grade_color};">{grade}</div>
                    <div style="font-size: 14px; color: #666;">종합 등급</div>
                    <div style="font-size: 28px; color: #333; margin-top: 8px;">{total_score}점</div>
                </div>
                """, unsafe_allow_html=True)

                # 세부 점수
                col1, col2, col3 = st.columns(3)
                sentence_data = analysis.get("sentence_analysis", {})
                story_data = analysis.get("storytelling_analysis", {})
                comp_data = analysis.get("comparison_analysis", {})

                with col1:
                    st.metric("문장 평균 점수", f"{sentence_data.get('avg_score', 0)}점")
                with col2:
                    st.metric("스토리텔링 점수", f"{story_data.get('total_score', 0)}점")
                with col3:
                    st.metric("합격기준 대비", f"{comp_data.get('comparison_score', 0)}점")

                st.divider()

                # 문장별 분석
                st.markdown("### 문장별 분석")
                issues = sentence_data.get("issues", [])
                if issues:
                    for issue in issues:
                        with st.expander(f"문장 {issue.get('index', 0)+1}: {issue.get('sentence', '')}", expanded=False):
                            for prob in issue.get("issues", []):
                                st.warning(f" {prob}")
                            for sug in issue.get("suggestions", []):
                                st.info(f" {sug}")
                else:
                    st.success("문장에서 특별한 문제가 발견되지 않았습니다!")

                st.divider()

                # 키워드 분석
                st.markdown("### 키워드 밀도 분석")
                kw_data = analysis.get("keyword_analysis", {})
                included_kw = kw_data.get("included", [])
                missing_kw = kw_data.get("missing", [])
                avoid_kw = kw_data.get("should_avoid", [])

                if included_kw:
                    included_html = " ".join([f'<span class="keyword-tag keyword-found"> {k}</span>' for k in included_kw])
                    st.markdown(f"**포함된 핵심 키워드:** {included_html}", unsafe_allow_html=True)

                if missing_kw:
                    missing_html = " ".join([f'<span class="keyword-tag">{k}</span>' for k in missing_kw])
                    st.markdown(f"**추가 권장 키워드:** {missing_html}", unsafe_allow_html=True)

                if avoid_kw:
                    st.warning(f" 피해야 할 키워드가 포함됨: {', '.join(avoid_kw)}")

                # 키워드 밀도 테이블
                density_results = kw_data.get("density_results", [])
                if density_results:
                    with st.expander("키워드 밀도 상세", expanded=False):
                        for d in density_results:
                            if d.get("count", 0) > 0:
                                status = " 과다" if d.get("is_overused") else ""
                                st.markdown(f"- **{d.get('keyword')}**: {d.get('count')}회 ({d.get('density', 0)}%) {status}")

                st.divider()

                # 스토리텔링 분석
                st.markdown("### 스토리텔링 구조 분석")
                story_col1, story_col2 = st.columns(2)

                with story_col1:
                    st.metric("흐름 점수", f"{story_data.get('flow_score', 0)}점")
                    present = story_data.get("present_elements", [])
                    element_kr = {
                        "hook": "도입 훅",
                        "conflict": "갈등/문제",
                        "action": "행동",
                        "resolution": "해결/결과",
                        "lesson": "깨달음",
                        "connection": "직무연결"
                    }
                    if present:
                        st.markdown("**포함된 요소:**")
                        for p in present:
                            st.markdown(f"- {element_kr.get(p, p)}")

                with story_col2:
                    st.metric("몰입도 점수", f"{story_data.get('engagement_score', 0)}점")
                    missing = story_data.get("missing_elements", [])
                    if missing:
                        st.markdown("**부족한 요소:**")
                        for m in missing[:3]:
                            st.markdown(f"- {element_kr.get(m, m)}")

                # 스토리텔링 피드백
                story_feedback = story_data.get("feedback", [])
                if story_feedback:
                    st.markdown("**개선 제안:**")
                    for fb in story_feedback:
                        st.info(f" {fb}")

                st.divider()

                # 합격 자소서 비교
                st.markdown("### 합격 자소서 비교")
                length_data = comp_data.get("length", {})
                kw_comp = comp_data.get("keywords", {})

                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                    current_len = length_data.get("current", 0)
                    ideal_range = length_data.get("ideal_range", (400, 500))
                    len_status = length_data.get("status", "")
                    st.metric("현재 글자수", f"{current_len}자", delta=f"{len_status} (권장: {ideal_range[0]}-{ideal_range[1]})")

                with comp_col2:
                    kw_count = kw_comp.get("current_count", 0)
                    kw_range = kw_comp.get("ideal_range", (3, 5))
                    kw_status = kw_comp.get("status", "")
                    st.metric("핵심 키워드", f"{kw_count}개", delta=f"{kw_status} (권장: {kw_range[0]}-{kw_range[1]})")

                # 종합 피드백
                overall_fb = comp_data.get("overall_feedback", [])
                if overall_fb:
                    for fb in overall_fb:
                        st.info(f" {fb}")

                st.divider()

                # 개선 우선순위
                st.markdown("### 개선 우선순위")
                priorities = analysis.get("improvement_priorities", [])
                for i, p in enumerate(priorities):
                    st.markdown(f"**{i+1}.** {p}")

        if len(adv_content) > 0 and len(adv_content) < 100:
            st.caption(" 최소 100자 이상 입력해주세요.")


# ========================================
# 탭3: 합격 예시
# ========================================
# 조건부 탭 변수 설정
tab_examples = tab3 if RESUME_ENHANCER_AVAILABLE else tab2
tab_guide = tab4 if RESUME_ENHANCER_AVAILABLE else tab3
tab_my_resume = tab5 if RESUME_ENHANCER_AVAILABLE else tab4

with tab_examples:
    st.subheader(" 합격 자소서 예시")
    st.info("항목별 좋은 자소서 예시를 참고하세요. 그대로 베끼면 안 되지만, 구조와 방식을 배울 수 있습니다!")

    for item_name, info in RESUME_ITEMS.items():
        examples = info.get("good_examples", [])
        if not examples:
            continue

        st.markdown(f"###  {item_name}")
        st.caption(f"{info['description']}")

        for ex in examples:
            with st.expander(f" {ex['title']}"):
                st.markdown(f"""
                <div class="example-card">
                    <div style="white-space: pre-wrap; line-height: 1.8;">{ex['content']}</div>
                </div>
                """, unsafe_allow_html=True)

                st.success(f" **왜 좋은가:** {ex['why_good']}")

        st.markdown("---")

    st.caption("※ 위 예시는 학습 참고용이며, 본인의 실제 경험으로 작성해야 합니다.")


# ========================================
# 탭: 작성 가이드
# ========================================
with tab_guide:
    st.subheader(" 항목별 작성 가이드")

    for item_name, info in RESUME_ITEMS.items():
        with st.expander(f" {item_name}"):
            st.markdown(f"**{info['description']}**")
            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("** 작성 팁**")
                for tip in info["tips"]:
                    st.markdown(f"- {tip}")
            with col2:
                st.markdown("** 피해야 할 표현**")
                for bad in info["bad_examples"]:
                    st.error(bad)

            st.caption(f"권장 글자수: {info['max_chars']}자 이내")

    st.markdown("---")

    st.info("""
    **STAR 기법이란?**
    - **S**ituation (상황): 어떤 상황이었는지
    - **T**ask (과제): 무엇을 해야 했는지
    - **A**ction (행동): 어떻게 행동했는지
    - **R**esult (결과): 어떤 결과를 얻었는지
    """)

    # 항공사별 키워드 총정리
    st.markdown("---")
    st.markdown("### 항공사별 핵심 키워드 총정리")

    for airline_name, kw in AIRLINE_KEYWORDS.items():
        with st.expander(f"️ {airline_name}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**인재상:**")
                st.markdown(", ".join(kw.get("인재상", [])))
                st.markdown("**핵심 가치:**")
                st.markdown(", ".join(kw.get("가치", [])))
            with col2:
                st.markdown("**추천 키워드:**")
                for k in kw.get("추천키워드", []):
                    st.markdown(f"- {k}")


# ========================================
# 탭4: 내 자소서 (버전 비교 포함)
# ========================================
with tab_my_resume:
    st.subheader(" 저장된 자소서")

    resumes = load_my_resumes()

    if not resumes:
        st.info("저장된 자소서가 없습니다. '첨삭받기' 탭에서 저장해보세요!")
    else:
        # 점수 추이
        scored = [r for r in resumes if r.get("score")]
        if len(scored) >= 2:
            st.markdown("#### 점수 추이")
            import pandas as pd
            chart_data = []
            for r in scored:
                chart_data.append({
                    "날짜": r.get("created_at", "")[:10],
                    "점수": r["score"],
                })
            df = pd.DataFrame(chart_data)
            st.line_chart(df.set_index("날짜"))
            st.markdown("---")

        # 항목별 필터
        items_in_resumes = list(set(r.get("item", "") for r in resumes))
        filter_item = st.selectbox("항목 필터", ["전체"] + items_in_resumes, key="resume_filter")

        filtered = resumes if filter_item == "전체" else [r for r in resumes if r.get("item") == filter_item]
        filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)

        # 버전 비교 기능
        if filter_item != "전체" and len(filtered) >= 2:
            st.markdown("---")
            st.markdown("#### 버전 비교")
            col1, col2 = st.columns(2)
            with col1:
                v1_idx = st.selectbox("이전 버전",
                    range(len(filtered)),
                    format_func=lambda i: f"{filtered[i].get('created_at','')[:10]} ({filtered[i].get('score','?')}점)" if filtered[i].get('score') else f"{filtered[i].get('created_at','')[:10]}",
                    key="v1_select"
                )
            with col2:
                v2_options = [i for i in range(len(filtered)) if i != v1_idx]
                if v2_options:
                    v2_idx = st.selectbox("최신 버전",
                        v2_options,
                        format_func=lambda i: f"{filtered[i].get('created_at','')[:10]} ({filtered[i].get('score','?')}점)" if filtered[i].get('score') else f"{filtered[i].get('created_at','')[:10]}",
                        key="v2_select"
                    )

                    if st.button("비교하기", use_container_width=True):
                        r1 = filtered[v1_idx]
                        r2 = filtered[v2_idx]

                        col_a, col_b = st.columns(2)
                        with col_a:
                            s1 = r1.get("score", "?")
                            st.markdown(f"**이전 ({r1.get('created_at','')[:10]})** | 점수: {s1}")
                            st.text_area("", r1.get("content", ""), height=200, key="compare_v1", disabled=True)
                        with col_b:
                            s2 = r2.get("score", "?")
                            st.markdown(f"**최신 ({r2.get('created_at','')[:10]})** | 점수: {s2}")
                            st.text_area("", r2.get("content", ""), height=200, key="compare_v2", disabled=True)

                        if isinstance(s1, int) and isinstance(s2, int):
                            diff = s2 - s1
                            if diff > 0:
                                st.success(f" {diff}점 개선되었습니다!")
                            elif diff == 0:
                                st.info("점수가 동일합니다.")
                            else:
                                st.warning(f" {abs(diff)}점 하락했습니다.")

            st.markdown("---")

        # 개별 자소서 목록
        st.markdown("#### 저장 목록")
        for resume in filtered:
            date_str = resume.get("created_at", "")[:10]
            has_feedback = "feedback" in resume
            score = resume.get("score")
            score_str = f" | {score}점" if score else ""
            re_review = " " if resume.get("is_re_review") else ""

            with st.expander(f" {resume.get('airline', '')} - {resume.get('item', '')} ({date_str}{score_str}){re_review}"):
                st.markdown("**원본:**")
                st.write(resume.get("content", ""))

                if has_feedback:
                    st.markdown("---")
                    st.markdown("**AI 첨삭:**")
                    st.markdown(resume.get("feedback", ""))

                if st.button("️ 삭제", key=f"del_{resume.get('id')}"):
                    all_resumes = load_my_resumes()
                    all_resumes = [r for r in all_resumes if r.get("id") != resume.get("id")]
                    save_my_resumes(all_resumes)
                    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
