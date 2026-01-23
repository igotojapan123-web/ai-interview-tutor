# pages/12_표정연습.py
# 동영상으로 표정/자세 연습 - 전면 개편 버전

import streamlit as st
import streamlit.components.v1 as components
import os
import sys
import json
import base64
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env_config import OPENAI_API_KEY

# 페이지 설정
from sidebar_common import render_sidebar

st.set_page_config(page_title="표정 연습", page_icon="🎬", layout="wide")
render_sidebar("표정연습")


st.markdown('<meta name="google" content="notranslate"><style>html{translate:no;}</style>', unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# 동영상 녹화 컴포넌트
try:
    from video_recorder import get_video_recorder_html, extract_frames_from_video, check_ffmpeg_available
    VIDEO_RECORDER_AVAILABLE = True
except ImportError:
    VIDEO_RECORDER_AVAILABLE = False

# ========================================
# 데이터 파일 경로
# ========================================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HISTORY_FILE = os.path.join(DATA_DIR, "expression_history.json")

# ========================================
# 연습 시나리오 데이터
# ========================================
PRACTICE_SCENARIOS = {
    "greeting": {
        "name": "인사 미소",
        "icon": "👋",
        "description": "승객을 처음 맞이할 때의 환한 미소",
        "situation": "기내에 탑승하는 승객을 맞이하며 '안녕하세요, 환영합니다'라고 인사합니다.",
        "target_expression": {
            "eyes": "눈이 살짝 휘어지며 눈웃음",
            "mouth": "입꼬리가 자연스럽게 올라감",
            "overall": "밝고 환영하는 느낌"
        },
        "tips": [
            "눈과 입이 함께 웃어야 진정성 있어 보입니다",
            "고개를 살짝 숙이며 인사하면 더 정중해 보입니다",
            "시선은 승객의 눈을 부드럽게 바라봅니다"
        ],
        "common_mistakes": [
            "입만 웃고 눈은 웃지 않는 '가식적 미소'",
            "너무 과한 미소로 부담스러운 인상",
            "시선이 다른 곳을 향함"
        ],
        "practice_phrase": "안녕하세요, 환영합니다!"
    },
    "apology": {
        "name": "사과 표정",
        "icon": "🙏",
        "description": "서비스 불편에 대해 진심으로 사과할 때",
        "situation": "기내식이 품절되어 승객에게 사과하며 대안을 제시합니다.",
        "target_expression": {
            "eyes": "진지하고 안타까운 눈빛",
            "mouth": "미소를 거두고 진지한 표정",
            "overall": "진심 어린 유감의 표현"
        },
        "tips": [
            "진지한 표정이되 너무 어둡지 않게",
            "눈썹을 살짝 모아 안타까움 표현",
            "고개를 살짝 숙여 사과의 뜻 전달"
        ],
        "common_mistakes": [
            "사과하면서 웃는 것 (진정성 없어 보임)",
            "너무 무표정한 사과",
            "시선 회피"
        ],
        "practice_phrase": "죄송합니다, 불편을 드려 정말 죄송합니다."
    },
    "guidance": {
        "name": "안내 표정",
        "icon": "👆",
        "description": "시설이나 서비스를 안내할 때의 친절한 표정",
        "situation": "승객에게 화장실 위치나 비상구를 안내합니다.",
        "target_expression": {
            "eyes": "또렷하고 명확한 눈빛",
            "mouth": "살짝 미소 띤 친절한 표정",
            "overall": "신뢰감 있고 전문적인 느낌"
        },
        "tips": [
            "안내하는 방향을 손으로 가리키며 시선도 함께",
            "친절하되 전문적인 느낌 유지",
            "말의 속도는 명확하고 또박또박"
        ],
        "common_mistakes": [
            "손만 가리키고 시선은 다른 곳",
            "무표정하게 안내",
            "너무 빠르게 설명"
        ],
        "practice_phrase": "화장실은 기내 중앙에 있습니다."
    },
    "empathy": {
        "name": "공감 표정",
        "icon": "💝",
        "description": "승객의 불편이나 어려움에 공감할 때",
        "situation": "비행이 무서운 승객을 안심시키며 공감합니다.",
        "target_expression": {
            "eyes": "따뜻하고 이해하는 눈빛",
            "mouth": "부드러운 미소",
            "overall": "편안하고 안심되는 느낌"
        },
        "tips": [
            "상대방의 눈높이에 맞춰 시선 조절",
            "고개를 살짝 기울여 경청하는 자세",
            "부드러운 목소리 톤 유지"
        ],
        "common_mistakes": [
            "건성으로 듣는 태도",
            "지나친 동정심 표현",
            "문제를 가볍게 여기는 태도"
        ],
        "practice_phrase": "걱정되시죠, 제가 옆에서 도와드릴게요."
    },
    "service": {
        "name": "서비스 미소",
        "icon": "☕",
        "description": "음료/식사 서비스 시의 상냥한 미소",
        "situation": "기내 음료 서비스를 제공하며 선택을 묻습니다.",
        "target_expression": {
            "eyes": "밝고 상냥한 눈빛",
            "mouth": "자연스러운 미소",
            "overall": "친근하고 서비스 정신이 느껴지는"
        },
        "tips": [
            "메뉴를 설명할 때 손동작과 함께",
            "승객의 선택에 긍정적 반응",
            "서비스 후에도 미소 유지"
        ],
        "common_mistakes": [
            "기계적인 반복 멘트",
            "피곤해 보이는 표정",
            "서비스 후 바로 무표정"
        ],
        "practice_phrase": "음료 드시겠어요? 커피, 주스, 물 있습니다."
    },
    "emergency": {
        "name": "비상 상황 표정",
        "icon": "🚨",
        "description": "비상 시 침착하고 신뢰감 있는 표정",
        "situation": "난기류로 인해 좌석벨트 착용을 안내합니다.",
        "target_expression": {
            "eyes": "진지하고 신뢰감 있는 눈빛",
            "mouth": "미소 없이 진지한 표정",
            "overall": "침착하고 전문적인 느낌"
        },
        "tips": [
            "당황하지 않고 침착하게",
            "명확하고 단호한 목소리",
            "승객을 안심시키는 자신감"
        ],
        "common_mistakes": [
            "당황한 표정",
            "너무 긴장한 모습",
            "불안해 보이는 태도"
        ],
        "practice_phrase": "좌석벨트를 착용해 주시기 바랍니다."
    }
}

# ========================================
# 표정 예시 데이터
# ========================================
EXPRESSION_EXAMPLES = {
    "smile_types": {
        "duchenne": {
            "name": "듀센 스마일 (진짜 미소)",
            "description": "눈과 입이 함께 웃는 진정한 미소",
            "characteristics": [
                "눈가에 자연스러운 주름 (까마귀발)",
                "눈이 살짝 가늘어짐",
                "볼이 올라감",
                "입꼬리가 자연스럽게 상승"
            ],
            "how_to": [
                "즐거운 기억을 떠올리세요",
                "눈으로 먼저 웃는다고 생각하세요",
                "광대뼈 근육을 함께 움직이세요"
            ],
            "rating": "최고"
        },
        "pan_am": {
            "name": "팬암 스마일 (직업적 미소)",
            "description": "입만 웃는 직업적 미소",
            "characteristics": [
                "입꼬리만 올라감",
                "눈은 웃지 않음",
                "어색하고 가식적으로 보임"
            ],
            "how_to_avoid": [
                "눈웃음을 의식적으로 연습",
                "거울 보며 눈 주변 근육 움직이기",
                "진심으로 웃는 연습"
            ],
            "rating": "피해야 함"
        }
    },
    "good_vs_bad": {
        "eye_contact": {
            "good": "면접관/승객의 눈을 부드럽게 바라봄 (70% 정도)",
            "bad": "시선 회피, 두리번거림, 뚫어지게 쳐다봄"
        },
        "posture": {
            "good": "어깨 펴고 바른 자세, 살짝 앞으로 기울임",
            "bad": "구부정한 자세, 기대앉음, 팔짱"
        },
        "expression": {
            "good": "자연스러운 미소, 적절한 표정 변화",
            "bad": "무표정, 과한 미소, 불안한 표정"
        },
        "gesture": {
            "good": "자연스러운 손동작, 열린 자세",
            "bad": "손 꼼지락, 머리 만지기, 닫힌 자세"
        }
    },
    "fsc_vs_lcc": {
        "FSC": {
            "name": "FSC (대한항공, 아시아나)",
            "style": "품위 있고 절제된 미소",
            "characteristics": [
                "우아하고 세련된 느낌",
                "절제된 표현",
                "고급스러운 이미지",
                "차분하고 신뢰감 있는 태도"
            ],
            "tips": [
                "미소는 은은하게",
                "동작은 우아하고 천천히",
                "말투는 정중하고 격식 있게",
                "자신감 있되 겸손하게"
            ],
            "color": "#003876"
        },
        "LCC": {
            "name": "LCC (제주항공, 진에어 등)",
            "style": "밝고 에너지 넘치는 미소",
            "characteristics": [
                "친근하고 활발한 느낌",
                "적극적인 표현",
                "젊고 역동적인 이미지",
                "편안하고 친숙한 태도"
            ],
            "tips": [
                "밝고 환한 미소",
                "적극적이고 활기찬 태도",
                "친근한 말투",
                "에너지 넘치는 모습"
            ],
            "color": "#FF6600"
        }
    }
}

# ========================================
# 상세 가이드 데이터
# ========================================
DETAILED_GUIDE = {
    "duchenne_smile": {
        "title": "듀센 스마일 마스터하기",
        "description": "프랑스 신경학자 듀센이 발견한 '진짜 미소'를 연습합니다.",
        "steps": [
            {
                "step": 1,
                "title": "눈 주변 근육 인식하기",
                "content": "눈가의 '눈둘레근(orbicularis oculi)'을 의식합니다. 이 근육은 의지대로 움직이기 어렵습니다.",
                "exercise": "눈을 감았다 뜨면서 눈가 근육의 움직임을 느껴보세요."
            },
            {
                "step": 2,
                "title": "즐거운 기억 떠올리기",
                "content": "진짜 웃음은 감정에서 나옵니다. 행복했던 순간을 떠올리세요.",
                "exercise": "가장 즐거웠던 여행, 친구와의 시간을 생각하며 웃어보세요."
            },
            {
                "step": 3,
                "title": "눈으로 먼저 웃기",
                "content": "입보다 눈이 먼저 웃어야 자연스럽습니다.",
                "exercise": "입은 가리고 눈만으로 웃는 연습을 해보세요."
            },
            {
                "step": 4,
                "title": "거울 앞 연습",
                "content": "거울을 보며 자연스러운 미소를 찾아가세요.",
                "exercise": "매일 5분씩 거울 앞에서 미소 짓는 연습을 합니다."
            }
        ]
    },
    "eye_smile": {
        "title": "눈웃음 연습법",
        "description": "눈웃음은 진정성과 호감도를 높이는 핵심입니다.",
        "techniques": [
            {
                "name": "눈 찡긋하기",
                "how": "양쪽 눈을 동시에 살짝 찡긋합니다",
                "effect": "친근함과 장난기 표현"
            },
            {
                "name": "반달 눈 만들기",
                "how": "눈을 가늘게 뜨며 반달 모양으로",
                "effect": "따뜻하고 부드러운 인상"
            },
            {
                "name": "눈꼬리 올리기",
                "how": "눈꼬리가 올라가도록 웃음",
                "effect": "밝고 긍정적인 인상"
            }
        ],
        "daily_exercise": [
            "아침에 거울 보며 눈웃음 10초 유지",
            "대화 중 상대방 눈 보며 미소 짓기",
            "셀카 찍을 때 눈웃음 연습"
        ]
    },
    "natural_smile": {
        "title": "자연스러운 미소 만들기",
        "description": "어색하지 않은 자연스러운 미소를 위한 팁",
        "tips": [
            {
                "title": "입꼬리 각도",
                "content": "입꼬리를 너무 올리면 어색합니다. 자연스럽게 살짝만 올리세요.",
                "degree": "약 15-20도 정도"
            },
            {
                "title": "치아 노출",
                "content": "윗니가 살짝 보이는 정도가 자연스럽습니다.",
                "tip": "아래 치아는 보이지 않게"
            },
            {
                "title": "미소 유지 시간",
                "content": "인사 시 2-3초 정도 미소를 유지합니다.",
                "tip": "너무 오래 유지하면 어색함"
            },
            {
                "title": "미소 진입과 퇴장",
                "content": "갑자기 웃거나 갑자기 무표정이 되지 않도록",
                "tip": "서서히 미소 짓고 서서히 풀기"
            }
        ],
        "practice_routine": [
            "1. 무표정에서 시작",
            "2. 1초에 걸쳐 미소 짓기",
            "3. 2-3초 미소 유지",
            "4. 1초에 걸쳐 미소 풀기",
            "5. 이 과정을 10회 반복"
        ]
    },
    "posture": {
        "title": "면접 자세 완성하기",
        "sections": [
            {
                "part": "머리/목",
                "correct": "턱을 살짝 당기고 목을 길게",
                "incorrect": "턱이 들리거나 목이 앞으로 빠짐",
                "tip": "귀-어깨-골반이 일직선"
            },
            {
                "part": "어깨",
                "correct": "양쪽 어깨 수평, 살짝 뒤로",
                "incorrect": "한쪽이 처지거나 앞으로 말림",
                "tip": "어깨를 귀에서 멀리"
            },
            {
                "part": "허리/등",
                "correct": "허리를 세우고 등을 펴기",
                "incorrect": "구부정하거나 너무 뻣뻣함",
                "tip": "자연스러운 S자 커브 유지"
            },
            {
                "part": "손",
                "correct": "무릎 위에 자연스럽게 포개기",
                "incorrect": "팔짱, 주머니에 손, 꼼지락",
                "tip": "긴장되면 손끝을 살짝 맞대기"
            }
        ]
    }
}


# ========================================
# 유틸리티 함수
# ========================================

def load_history() -> List[Dict]:
    """연습 기록 로드"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("history", [])
        except:
            return []
    return []


def save_history(history: List[Dict]):
    """연습 기록 저장"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump({"history": history, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M")}, f, ensure_ascii=False, indent=2)


def add_to_history(context: str, result: Dict):
    """기록에 추가"""
    history = load_history()
    history.append({
        "id": f"expr_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "context": context,
        "result": result,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    # 최근 50개만 유지
    if len(history) > 50:
        history = history[-50:]
    save_history(history)
    return history


def analyze_video_frames(frames_base64: List[str], context: str = "면접") -> Optional[Dict[str, Any]]:
    """GPT-4 Vision으로 프레임 분석"""
    if not OPENAI_API_KEY or not frames_base64:
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    system_prompt = """항공사 면접 코칭 전문가입니다. 동영상에서 추출한 프레임들을 분석합니다.

JSON 형식으로만 응답:
{
    "expression": {
        "score": 1-10,
        "smile": "좋음/보통/부족",
        "smile_type": "듀센스마일/팬암스마일/무표정",
        "smile_consistency": "일관됨/변동있음/부족",
        "eye_contact": "좋음/보통/부족",
        "eye_smile": "있음/부족/없음",
        "naturalness": "자연스러움/어색함/긴장됨",
        "feedback": "표정 피드백"
    },
    "posture": {
        "score": 1-10,
        "consistency": "일관됨/흔들림",
        "shoulders": "바름/처짐/비대칭",
        "head_position": "바름/기울어짐/숙임",
        "feedback": "자세 피드백"
    },
    "impression": {
        "score": 1-10,
        "confidence": "높음/보통/낮음",
        "friendliness": "높음/보통/낮음",
        "professionalism": "높음/보통/낮음",
        "trustworthiness": "높음/보통/낮음",
        "feedback": "인상 피드백"
    },
    "time_analysis": {
        "start": "초반 상태",
        "mid": "중반 상태",
        "end": "후반 상태",
        "consistency_score": 1-10,
        "feedback": "시간별 변화 피드백"
    },
    "fsc_lcc_fit": {
        "fsc_score": 1-10,
        "lcc_score": 1-10,
        "recommendation": "FSC/LCC/둘 다 적합"
    },
    "overall_score": 1-100,
    "strengths": ["강점1", "강점2", "강점3"],
    "improvements": ["개선점1", "개선점2", "개선점3"],
    "specific_tips": ["구체적 팁1", "구체적 팁2"],
    "tip": "핵심 팁"
}"""

    content_list = [{"type": "text", "text": f"{context} 동영상에서 추출한 {len(frames_base64)}개 프레임입니다. 시간 순서대로 표정과 자세를 분석해주세요."}]

    for frame in frames_base64[:5]:
        content_list.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{frame}", "detail": "low"}
        })

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content_list}
        ],
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=90)
        r.raise_for_status()
        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())
    except Exception as e:
        st.error(f"분석 오류: {e}")
        return None


def display_result(result: Dict[str, Any]):
    """분석 결과 표시"""
    score = result.get("overall_score", 0)

    if score >= 80:
        color, emoji, grade = "#28a745", "🌟", "우수"
    elif score >= 60:
        color, emoji, grade = "#ffc107", "👍", "양호"
    else:
        color, emoji, grade = "#dc3545", "💪", "개선필요"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}20, {color}10); border: 2px solid {color}; border-radius: 20px; padding: 30px; text-align: center; margin-bottom: 20px;">
        <div style="font-size: 50px;">{emoji}</div>
        <div style="font-size: 42px; font-weight: bold; color: {color};">{score}점</div>
        <div style="font-size: 18px; color: #666;">{grade}</div>
    </div>
    """, unsafe_allow_html=True)

    # FSC/LCC 적합도
    fsc_lcc = result.get("fsc_lcc_fit", {})
    if fsc_lcc:
        st.markdown("### 🎯 FSC/LCC 적합도")
        col1, col2 = st.columns(2)
        with col1:
            fsc_score = fsc_lcc.get("fsc_score", 5)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #00387620, #00387610); border-radius: 12px; padding: 16px; text-align: center;">
                <div style="font-size: 14px; color: #003876;">FSC (대한항공, 아시아나)</div>
                <div style="font-size: 28px; font-weight: bold; color: #003876;">{fsc_score}/10</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            lcc_score = fsc_lcc.get("lcc_score", 5)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #FF660020, #FF660010); border-radius: 12px; padding: 16px; text-align: center;">
                <div style="font-size: 14px; color: #FF6600;">LCC (제주항공, 진에어 등)</div>
                <div style="font-size: 28px; font-weight: bold; color: #FF6600;">{lcc_score}/10</div>
            </div>
            """, unsafe_allow_html=True)

        if fsc_lcc.get("recommendation"):
            st.info(f"💡 추천: **{fsc_lcc.get('recommendation')}**")

    # 시간별 변화
    time_a = result.get("time_analysis", {})
    if time_a:
        st.markdown("### ⏱️ 시간별 표정 변화")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**초반**: {time_a.get('start', '-')}")
        with col2:
            st.info(f"**중반**: {time_a.get('mid', '-')}")
        with col3:
            st.info(f"**후반**: {time_a.get('end', '-')}")

        if time_a.get('feedback'):
            st.caption(f"📊 일관성 점수: {time_a.get('consistency_score', 0)}/10 - {time_a.get('feedback')}")

    # 세부 분석
    st.markdown("### 📊 세부 분석")
    col1, col2, col3 = st.columns(3)

    expr = result.get("expression", {})
    with col1:
        smile_type = expr.get('smile_type', '-')
        smile_color = "#28a745" if smile_type == "듀센스마일" else "#ffc107" if smile_type == "팬암스마일" else "#dc3545"
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color: #667eea;">😊 표정 {expr.get('score', 0)}/10</h4>
            <p>미소: {expr.get('smile', '-')}</p>
            <p>미소 유형: <span style="color: {smile_color}; font-weight: bold;">{smile_type}</span></p>
            <p>눈웃음: {expr.get('eye_smile', '-')}</p>
            <p>유지력: {expr.get('smile_consistency', '-')}</p>
            <small style="color: #666;">{expr.get('feedback', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    posture = result.get("posture", {})
    with col2:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color: #764ba2;">🧍 자세 {posture.get('score', 0)}/10</h4>
            <p>어깨: {posture.get('shoulders', '-')}</p>
            <p>머리: {posture.get('head_position', '-')}</p>
            <p>일관성: {posture.get('consistency', '-')}</p>
            <small style="color: #666;">{posture.get('feedback', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    imp = result.get("impression", {})
    with col3:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color: #f093fb;">✨ 인상 {imp.get('score', 0)}/10</h4>
            <p>자신감: {imp.get('confidence', '-')}</p>
            <p>친근함: {imp.get('friendliness', '-')}</p>
            <p>전문성: {imp.get('professionalism', '-')}</p>
            <p>신뢰감: {imp.get('trustworthiness', '-')}</p>
            <small style="color: #666;">{imp.get('feedback', '')}</small>
        </div>
        """, unsafe_allow_html=True)

    # 강점/개선점
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💪 강점")
        for s in result.get("strengths", []):
            st.success(f"✓ {s}")
    with col2:
        st.markdown("### 📈 개선점")
        for i in result.get("improvements", []):
            st.warning(f"△ {i}")

    # 구체적 팁
    if result.get("specific_tips"):
        st.markdown("### 🎯 구체적 연습 팁")
        for tip in result.get("specific_tips", []):
            st.info(f"💡 {tip}")

    # 핵심 팁
    if result.get("tip"):
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb20, #f5576c10); border-radius: 12px; padding: 20px; margin-top: 20px; text-align: center;">
            <strong style="color: #f5576c;">🌟 핵심 팁:</strong> {result.get('tip')}
        </div>
        """, unsafe_allow_html=True)


def get_mirror_mode_html():
    """거울 모드 HTML 컴포넌트"""
    return """
    <style>
        .mirror-container {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .mirror-box {
            position: relative;
            background: #000;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        }
        #mirror-video {
            width: 100%;
            display: block;
            transform: scaleX(-1);
        }
        .guide-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
        }
        .face-guide {
            position: absolute;
            top: 15%;
            left: 50%;
            transform: translateX(-50%);
            width: 200px;
            height: 280px;
            border: 3px dashed rgba(102, 126, 234, 0.6);
            border-radius: 50%;
            display: none;
        }
        .eye-line {
            position: absolute;
            top: 35%;
            left: 20%;
            right: 20%;
            border-top: 2px dashed rgba(102, 126, 234, 0.4);
            display: none;
        }
        .eye-line::before {
            content: '눈 위치';
            position: absolute;
            right: 0;
            top: -20px;
            font-size: 12px;
            color: rgba(102, 126, 234, 0.8);
        }
        .mouth-line {
            position: absolute;
            top: 55%;
            left: 30%;
            right: 30%;
            border-top: 2px dashed rgba(118, 75, 162, 0.4);
            display: none;
        }
        .mouth-line::before {
            content: '입 위치';
            position: absolute;
            right: 0;
            top: -20px;
            font-size: 12px;
            color: rgba(118, 75, 162, 0.8);
        }
        .shoulder-line {
            position: absolute;
            top: 75%;
            left: 10%;
            right: 10%;
            border-top: 2px dashed rgba(240, 147, 251, 0.4);
            display: none;
        }
        .shoulder-line::before {
            content: '어깨 라인 (수평 유지)';
            position: absolute;
            right: 0;
            top: -20px;
            font-size: 12px;
            color: rgba(240, 147, 251, 0.8);
        }
        .mirror-controls {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .mirror-btn {
            border: none;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .mirror-btn:hover {
            transform: scale(1.05);
        }
        .btn-guide {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .btn-flip {
            background: #f5f5f5;
            color: #333;
        }
        .btn-fullscreen {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
        }
        .timer-display {
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
            margin: 20px 0;
            font-family: monospace;
        }
        .timer-controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        .practice-tip {
            background: linear-gradient(135deg, #667eea10, #764ba210);
            border-radius: 12px;
            padding: 16px;
            margin-top: 20px;
            text-align: center;
        }
    </style>

    <div class="mirror-container">
        <div class="mirror-box">
            <video id="mirror-video" autoplay muted playsinline></video>
            <div class="guide-overlay">
                <div class="face-guide" id="face-guide"></div>
                <div class="eye-line" id="eye-line"></div>
                <div class="mouth-line" id="mouth-line"></div>
                <div class="shoulder-line" id="shoulder-line"></div>
            </div>
        </div>

        <div class="mirror-controls">
            <button class="mirror-btn btn-guide" onclick="toggleGuide()">
                📐 가이드라인 ON/OFF
            </button>
            <button class="mirror-btn btn-flip" onclick="toggleFlip()">
                🔄 좌우반전
            </button>
        </div>

        <div class="timer-display" id="timer">00:00</div>
        <div class="timer-controls">
            <button class="mirror-btn btn-guide" onclick="startTimer()">▶️ 시작</button>
            <button class="mirror-btn btn-flip" onclick="resetTimer()">🔄 리셋</button>
        </div>

        <div class="practice-tip">
            💡 <strong>연습 팁:</strong> 가이드라인을 켜고 얼굴 위치를 맞춰보세요. 어깨 라인이 수평인지 확인하세요.
        </div>
    </div>

    <script>
        let guideOn = false;
        let flipped = true;
        let timerInterval = null;
        let seconds = 0;

        async function initMirror() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' }
                });
                document.getElementById('mirror-video').srcObject = stream;
            } catch (err) {
                console.error('Camera error:', err);
            }
        }

        function toggleGuide() {
            guideOn = !guideOn;
            document.getElementById('face-guide').style.display = guideOn ? 'block' : 'none';
            document.getElementById('eye-line').style.display = guideOn ? 'block' : 'none';
            document.getElementById('mouth-line').style.display = guideOn ? 'block' : 'none';
            document.getElementById('shoulder-line').style.display = guideOn ? 'block' : 'none';
        }

        function toggleFlip() {
            flipped = !flipped;
            document.getElementById('mirror-video').style.transform = flipped ? 'scaleX(-1)' : 'scaleX(1)';
        }

        function startTimer() {
            if (timerInterval) return;
            timerInterval = setInterval(() => {
                seconds++;
                const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
                const secs = (seconds % 60).toString().padStart(2, '0');
                document.getElementById('timer').textContent = mins + ':' + secs;
            }, 1000);
        }

        function resetTimer() {
            clearInterval(timerInterval);
            timerInterval = null;
            seconds = 0;
            document.getElementById('timer').textContent = '00:00';
        }

        initMirror();
    </script>
    """


# ========================================
# 메인
# ========================================

st.title("🎬 표정 연습")
st.markdown("AI가 분석하는 맞춤형 표정 연습 시스템!")

if not OPENAI_API_KEY:
    st.error("OpenAI API 키가 필요합니다.")
    st.stop()

# 세션 상태
if "expr_result" not in st.session_state:
    st.session_state.expr_result = None

# 탭 구성 (6개)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎬 AI 분석",
    "🪞 거울 모드",
    "🎭 연습 시나리오",
    "📸 표정 예시",
    "📚 상세 가이드",
    "📊 연습 기록"
])

# ========================================
# Tab 1: AI 분석 (기존 기능 유지)
# ========================================
with tab1:
    st.markdown("### 📹 동영상 녹화 및 AI 분석")

    # 설정
    col1, col2 = st.columns(2)
    with col1:
        context = st.selectbox("연습 상황", ["1차 면접", "2차 면접", "최종 면접", "일반 연습"], key="ctx1")
    with col2:
        airline_type = st.selectbox("항공사 유형", ["FSC (대한항공, 아시아나)", "LCC (제주, 진에어 등)"], key="air1")

    st.markdown("---")

    # 동영상 녹화
    if VIDEO_RECORDER_AVAILABLE:
        with st.expander("📹 동영상 녹화하기", expanded=True):
            components.html(get_video_recorder_html(duration=15), height=700)

    st.markdown("---")

    # 동영상 업로드
    st.markdown("### 📤 녹화한 영상 업로드")
    video_file = st.file_uploader(
        "위에서 저장한 영상 파일을 업로드하세요",
        type=["webm", "mp4", "mov"],
        key="video_upload"
    )

    if video_file:
        st.video(video_file)
        st.success(f"✅ 영상 업로드됨: {video_file.name}")

        if st.button("🔍 AI 분석하기", type="primary", use_container_width=True):
            with st.spinner("🤖 동영상 분석 중... (프레임 추출 → AI 분석)"):
                video_bytes = video_file.getvalue()

                st.info("📽️ 동영상에서 프레임 추출 중...")

                if VIDEO_RECORDER_AVAILABLE and check_ffmpeg_available():
                    frames = extract_frames_from_video(video_bytes, num_frames=5)
                else:
                    st.warning("ffmpeg가 설치되지 않아 프레임 추출이 제한됩니다. 이미지를 직접 업로드해주세요.")
                    frames = []

                if frames:
                    st.success(f"✅ {len(frames)}개 프레임 추출 완료")

                    st.info("🧠 AI 표정 분석 중...")
                    result = analyze_video_frames(frames, f"{context}, {airline_type}")

                    if result:
                        st.session_state.expr_result = result
                        # 기록에 추가
                        add_to_history(f"{context} - {airline_type}", result)
                        st.rerun()
                    else:
                        st.error("분석에 실패했습니다.")
                else:
                    st.error("프레임 추출에 실패했습니다.")

    # 대체: 이미지 업로드
    with st.expander("📷 또는 이미지 직접 업로드"):
        images = st.file_uploader("이미지 여러 장 선택", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="img_upload")

        if images:
            cols = st.columns(min(len(images), 5))
            for i, img in enumerate(images[:5]):
                with cols[i]:
                    st.image(img, use_container_width=True)

            if st.button("🔍 이미지 분석", use_container_width=True):
                with st.spinner("분석 중..."):
                    frames = [base64.b64encode(img.getvalue()).decode('utf-8') for img in images[:5]]
                    result = analyze_video_frames(frames, f"{context}, {airline_type}")

                    if result:
                        st.session_state.expr_result = result
                        add_to_history(f"{context} - {airline_type}", result)
                        st.rerun()

    # 결과 표시
    if st.session_state.expr_result:
        st.markdown("---")
        st.markdown("### 📊 분석 결과")
        display_result(st.session_state.expr_result)

        if st.button("🔄 새로 연습하기", use_container_width=True):
            st.session_state.expr_result = None
            st.rerun()


# ========================================
# Tab 2: 거울 모드
# ========================================
with tab2:
    st.markdown("### 🪞 거울 모드")
    st.markdown("녹화 없이 실시간으로 표정을 확인하며 연습하세요!")

    st.info("💡 **사용법**: 가이드라인을 켜서 얼굴 위치와 어깨 라인을 맞춰보세요. 타이머로 미소 유지 시간을 측정할 수 있습니다.")

    components.html(get_mirror_mode_html(), height=750)

    # 거울 모드 연습 체크리스트
    st.markdown("### ✅ 거울 모드 연습 체크리스트")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**표정 체크**")
        st.checkbox("눈웃음이 자연스럽게 나오나요?", key="m1")
        st.checkbox("입꼬리가 적당히 올라가 있나요?", key="m2")
        st.checkbox("미소가 10초 이상 유지되나요?", key="m3")
        st.checkbox("표정이 긴장되어 보이지 않나요?", key="m4")

    with col2:
        st.markdown("**자세 체크**")
        st.checkbox("어깨가 수평인가요?", key="m5")
        st.checkbox("턱이 너무 들리거나 숙여지지 않았나요?", key="m6")
        st.checkbox("목이 앞으로 빠지지 않았나요?", key="m7")
        st.checkbox("전체적으로 자신감 있어 보이나요?", key="m8")


# ========================================
# Tab 3: 연습 시나리오
# ========================================
with tab3:
    st.markdown("### 🎭 상황별 연습 시나리오")
    st.markdown("실제 기내 상황을 상상하며 표정을 연습해보세요!")

    # 시나리오 선택
    scenario_options = {k: f"{v['icon']} {v['name']}" for k, v in PRACTICE_SCENARIOS.items()}
    selected_scenario = st.selectbox("연습할 시나리오 선택", list(scenario_options.keys()), format_func=lambda x: scenario_options[x])

    scenario = PRACTICE_SCENARIOS[selected_scenario]

    # 시나리오 정보 표시
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea20, #764ba210); border-radius: 16px; padding: 24px; margin: 20px 0;">
        <div style="font-size: 48px; text-align: center;">{scenario['icon']}</div>
        <h2 style="text-align: center; color: #667eea;">{scenario['name']}</h2>
        <p style="text-align: center; color: #666;">{scenario['description']}</p>
    </div>
    """, unsafe_allow_html=True)

    # 상황 설명
    st.markdown("#### 📍 상황")
    st.info(scenario['situation'])

    # 연습 문구
    st.markdown("#### 🗣️ 연습 문구")
    st.markdown(f"""
    <div style="background: #f8f9fa; border-left: 4px solid #667eea; padding: 16px; font-size: 18px; font-style: italic;">
        "{scenario['practice_phrase']}"
    </div>
    """, unsafe_allow_html=True)

    # 목표 표정
    st.markdown("#### 🎯 목표 표정")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style="font-size: 24px;">👁️</div>
            <div style="font-weight: bold; color: #667eea;">눈</div>
            <div style="font-size: 14px; color: #666;">{scenario['target_expression']['eyes']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style="font-size: 24px;">👄</div>
            <div style="font-weight: bold; color: #764ba2;">입</div>
            <div style="font-size: 14px; color: #666;">{scenario['target_expression']['mouth']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <div style="font-size: 24px;">✨</div>
            <div style="font-weight: bold; color: #f093fb;">전체</div>
            <div style="font-size: 14px; color: #666;">{scenario['target_expression']['overall']}</div>
        </div>
        """, unsafe_allow_html=True)

    # 팁과 실수
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ✅ 연습 팁")
        for tip in scenario['tips']:
            st.success(f"💡 {tip}")

    with col2:
        st.markdown("#### ⚠️ 흔한 실수")
        for mistake in scenario['common_mistakes']:
            st.error(f"❌ {mistake}")


# ========================================
# Tab 4: 표정 예시
# ========================================
with tab4:
    st.markdown("### 📸 표정 예시 및 비교")

    # 미소 유형
    st.markdown("#### 😊 미소의 종류")
    col1, col2 = st.columns(2)

    duchenne = EXPRESSION_EXAMPLES["smile_types"]["duchenne"]
    pan_am = EXPRESSION_EXAMPLES["smile_types"]["pan_am"]

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #28a74520, #28a74510); border: 2px solid #28a745; border-radius: 16px; padding: 20px;">
            <h3 style="color: #28a745;">✅ {duchenne['name']}</h3>
            <p>{duchenne['description']}</p>
            <p><strong>특징:</strong></p>
            <ul>
        """, unsafe_allow_html=True)
        for char in duchenne['characteristics']:
            st.markdown(f"- {char}")
        st.markdown("**연습법:**")
        for how in duchenne['how_to']:
            st.info(f"💡 {how}")

    with col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #dc354520, #dc354510); border: 2px solid #dc3545; border-radius: 16px; padding: 20px;">
            <h3 style="color: #dc3545;">❌ {pan_am['name']}</h3>
            <p>{pan_am['description']}</p>
            <p><strong>특징:</strong></p>
            <ul>
        """, unsafe_allow_html=True)
        for char in pan_am['characteristics']:
            st.markdown(f"- {char}")
        st.markdown("**피하는 법:**")
        for how in pan_am['how_to_avoid']:
            st.warning(f"⚠️ {how}")

    st.markdown("---")

    # Good vs Bad
    st.markdown("#### ⚖️ 좋은 표정 vs 나쁜 표정")

    good_bad = EXPRESSION_EXAMPLES["good_vs_bad"]
    for category, examples in good_bad.items():
        category_names = {"eye_contact": "👁️ 시선 처리", "posture": "🧍 자세", "expression": "😊 표정", "gesture": "🤚 제스처"}
        st.markdown(f"**{category_names.get(category, category)}**")
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ {examples['good']}")
        with col2:
            st.error(f"❌ {examples['bad']}")

    st.markdown("---")

    # FSC vs LCC
    st.markdown("#### 🛫 FSC vs LCC 스타일 차이")

    fsc_lcc = EXPRESSION_EXAMPLES["fsc_vs_lcc"]
    col1, col2 = st.columns(2)

    with col1:
        fsc = fsc_lcc["FSC"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {fsc['color']}20, {fsc['color']}10); border: 2px solid {fsc['color']}; border-radius: 16px; padding: 20px;">
            <h3 style="color: {fsc['color']};">{fsc['name']}</h3>
            <p style="font-size: 18px; font-weight: bold;">"{fsc['style']}"</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**특징:**")
        for char in fsc['characteristics']:
            st.markdown(f"- {char}")

        st.markdown("**면접 팁:**")
        for tip in fsc['tips']:
            st.info(f"💡 {tip}")

    with col2:
        lcc = fsc_lcc["LCC"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {lcc['color']}20, {lcc['color']}10); border: 2px solid {lcc['color']}; border-radius: 16px; padding: 20px;">
            <h3 style="color: {lcc['color']};">{lcc['name']}</h3>
            <p style="font-size: 18px; font-weight: bold;">"{lcc['style']}"</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**특징:**")
        for char in lcc['characteristics']:
            st.markdown(f"- {char}")

        st.markdown("**면접 팁:**")
        for tip in lcc['tips']:
            st.info(f"💡 {tip}")


# ========================================
# Tab 5: 상세 가이드
# ========================================
with tab5:
    st.markdown("### 📚 표정 연습 상세 가이드")

    guide_tabs = st.tabs(["😊 듀센 스마일", "👁️ 눈웃음", "🙂 자연스러운 미소", "🧍 자세"])

    # 듀센 스마일
    with guide_tabs[0]:
        guide = DETAILED_GUIDE["duchenne_smile"]
        st.markdown(f"### {guide['title']}")
        st.markdown(guide['description'])

        for step in guide['steps']:
            with st.expander(f"Step {step['step']}: {step['title']}", expanded=step['step']==1):
                st.markdown(step['content'])
                st.info(f"🎯 **연습**: {step['exercise']}")

    # 눈웃음
    with guide_tabs[1]:
        guide = DETAILED_GUIDE["eye_smile"]
        st.markdown(f"### {guide['title']}")
        st.markdown(guide['description'])

        st.markdown("#### 테크닉")
        for tech in guide['techniques']:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 16px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
                <h4 style="color: #667eea;">{tech['name']}</h4>
                <p><strong>방법:</strong> {tech['how']}</p>
                <p><strong>효과:</strong> {tech['effect']}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### 일일 연습")
        for ex in guide['daily_exercise']:
            st.checkbox(ex, key=f"eye_{ex}")

    # 자연스러운 미소
    with guide_tabs[2]:
        guide = DETAILED_GUIDE["natural_smile"]
        st.markdown(f"### {guide['title']}")
        st.markdown(guide['description'])

        for tip in guide['tips']:
            with st.expander(tip['title']):
                st.markdown(tip['content'])
                if 'degree' in tip:
                    st.info(f"📐 권장 각도: {tip['degree']}")
                if 'tip' in tip:
                    st.success(f"💡 팁: {tip['tip']}")

        st.markdown("#### 연습 루틴")
        for i, routine in enumerate(guide['practice_routine'], 1):
            st.markdown(f"{routine}")

    # 자세
    with guide_tabs[3]:
        guide = DETAILED_GUIDE["posture"]
        st.markdown(f"### {guide['title']}")

        for section in guide['sections']:
            st.markdown(f"#### {section['part']}")
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ **올바른 자세**: {section['correct']}")
            with col2:
                st.error(f"❌ **잘못된 자세**: {section['incorrect']}")
            st.info(f"💡 **팁**: {section['tip']}")


# ========================================
# Tab 6: 연습 기록
# ========================================
with tab6:
    st.markdown("### 📊 연습 기록")

    history = load_history()

    if not history:
        st.info("아직 기록이 없습니다. AI 분석 탭에서 연습을 시작해보세요!")
    else:
        # 통계
        scores = [h["result"].get("overall_score", 0) for h in history]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 연습 횟수", f"{len(scores)}회")
        with col2:
            st.metric("평균 점수", f"{sum(scores)/len(scores):.0f}점")
        with col3:
            st.metric("최고 점수", f"{max(scores)}점")
        with col4:
            # 최근 5회 평균
            recent = scores[-5:] if len(scores) >= 5 else scores
            st.metric("최근 평균", f"{sum(recent)/len(recent):.0f}점")

        # 점수 추이 (간단한 텍스트 그래프)
        st.markdown("#### 📈 점수 추이")
        recent_10 = history[-10:]
        for h in recent_10:
            score = h["result"].get("overall_score", 0)
            bar_len = int(score / 5)
            bar = "█" * bar_len + "░" * (20 - bar_len)

            if score >= 80:
                color = "🟢"
            elif score >= 60:
                color = "🟡"
            else:
                color = "🔴"

            st.markdown(f"`{h['timestamp'][-5:]}` {color} {bar} **{score}점** - {h['context'][:20]}")

        st.markdown("---")

        # 상세 기록
        st.markdown("#### 📋 상세 기록")
        for h in reversed(history[-10:]):
            with st.expander(f"📅 {h['timestamp']} - {h['result'].get('overall_score', 0)}점 ({h['context']})"):
                display_result(h["result"])

        # 기록 삭제
        if st.button("🗑️ 전체 기록 삭제", type="secondary"):
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
                st.success("기록이 삭제되었습니다.")
                st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
