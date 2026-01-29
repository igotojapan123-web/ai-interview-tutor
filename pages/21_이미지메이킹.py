# pages/21_이미지메이킹.py
# 항공사 면접 이미지메이킹 가이드
# 셀프체크 + 타임라인 + NG사례 + 항공사비교 + 계절별팁

import streamlit as st
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page

init_page(
    title="이미지메이킹",
    current_page="이미지메이킹",
    wide_layout=True
)


st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<style>
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    translate: no !important;
}
.notranslate, [translate="no"] {
    translate: no !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate" lang="ko">', unsafe_allow_html=True)

# ========================================
# 항공사별 이미지 데이터 (11개)
# ========================================
AIRLINE_IMAGE = {
    "대한항공": {
        "color": "#0F4C81",
        "style": "클래식 & 단정",
        "makeup": "자연스러운 누드톤, 깔끔한 아이라인, 코랄/핑크 립",
        "hair": "단정한 업스타일, 쪽머리, 망사망 사용",
        "outfit": "네이비/화이트 조합, 정장 스커트",
        "keywords": ["단정함", "신뢰감", "프로페셔널"],
        "tip": "가장 보수적인 이미지. 과한 메이크업 지양",
        "type": "FSC"
    },
    "아시아나항공": {
        "color": "#C4161C",
        "style": "우아함 & 세련됨",
        "makeup": "레드/코랄 립 강조, 깔끔한 눈매, 자연스러운 피부",
        "hair": "깔끔한 업스타일, 낮은 쪽머리",
        "outfit": "그레이/화이트 정장, 여성스러운 라인",
        "keywords": ["우아함", "세련됨", "아름다운 사람들"],
        "tip": "브랜드 슬로건처럼 '아름다운 사람들' 이미지",
        "type": "FSC"
    },
    "진에어": {
        "color": "#F15A29",
        "style": "발랄 & 활기",
        "makeup": "밝은 톤, 오렌지/코랄 계열, 생기있는 피부",
        "hair": "깔끔한 포니테일, 반묶음 가능",
        "outfit": "밝은 색상 포인트 가능, 캐주얼 정장",
        "keywords": ["Fun", "Young", "Dynamic"],
        "tip": "LCC 중에서도 젊고 활기찬 이미지 강조",
        "type": "LCC"
    },
    "제주항공": {
        "color": "#FF6600",
        "style": "밝음 & 친근",
        "makeup": "화사한 피부, 자연스러운 눈, 오렌지/코랄 립",
        "hair": "깔끔한 정리, 포니테일 OK",
        "outfit": "오렌지 포인트, 밝은 분위기",
        "keywords": ["친근함", "밝음", "긍정"],
        "tip": "시그니처 오렌지 컬러와 어울리는 이미지",
        "type": "LCC"
    },
    "티웨이항공": {
        "color": "#E31937",
        "style": "밝음 & 친절",
        "makeup": "깨끗한 피부, 레드/핑크 립",
        "hair": "단정한 정리, 포니테일 가능",
        "outfit": "레드 포인트 악세서리 가능",
        "keywords": ["즐거움", "친절", "여행"],
        "tip": "친근하고 밝은 이미지",
        "type": "LCC"
    },
    "에어부산": {
        "color": "#00AEEF",
        "style": "상쾌 & 친근",
        "makeup": "깔끔하고 자연스러운 메이크업",
        "hair": "단정한 정리, 포니테일 가능",
        "outfit": "블루 계열 포인트",
        "keywords": ["부산", "바다", "친근"],
        "tip": "부산의 상쾌한 이미지와 연결",
        "type": "LCC"
    },
    "에어서울": {
        "color": "#1C1C1C",
        "style": "모던 & 시크",
        "makeup": "깔끔한 피부, 자연스러운 눈매, MLBB 립",
        "hair": "깔끔한 업스타일 또는 포니테일",
        "outfit": "블랙/화이트 모던 정장",
        "keywords": ["도시적", "세련됨", "모던"],
        "tip": "도시적이고 세련된 이미지",
        "type": "LCC"
    },
    "이스타항공": {
        "color": "#00A651",
        "style": "활동적 & 건강",
        "makeup": "건강한 피부, 생기있는 메이크업",
        "hair": "활동적인 포니테일, 단정한 업스타일",
        "outfit": "깔끔한 정장, 그린 포인트",
        "keywords": ["활력", "건강", "새로움"],
        "tip": "체력시험이 있는 만큼 건강하고 활동적인 이미지",
        "type": "LCC"
    },
    "에어프레미아": {
        "color": "#00A0B0",
        "style": "모던 & 프레시",
        "makeup": "자연스럽고 깨끗한 피부, 생기있는 메이크업",
        "hair": "깔끔한 포니테일 또는 단발",
        "outfit": "깔끔한 비즈니스 캐주얼 가능",
        "keywords": ["신선함", "프리미엄", "글로벌"],
        "tip": "하이브리드 항공사답게 조금 더 유연한 이미지 가능",
        "type": "HSC"
    },
    "에어로케이": {
        "color": "#003B7A",
        "style": "깔끔 & 신뢰",
        "makeup": "깔끔한 피부, 자연스러운 메이크업",
        "hair": "단정한 업스타일",
        "outfit": "네이비/블랙 정장",
        "keywords": ["신뢰", "안전", "깔끔"],
        "tip": "안전을 강조하는 만큼 신뢰감 있는 이미지",
        "type": "LCC"
    },
    "파라타항공": {
        "color": "#6B2D8B",
        "style": "프레시 & 자신감",
        "makeup": "건강한 피부, 밝은 톤, 코랄/핑크 립",
        "hair": "깔끔한 업스타일 또는 포니테일",
        "outfit": "단정한 정장, 보라 계열 포인트 가능",
        "keywords": ["자신감", "젊음", "도전"],
        "tip": "신생 항공사로 체력과 자신감 있는 이미지 어필",
        "type": "LCC"
    },
}

# ========================================
# 메이크업 가이드
# ========================================
MAKEUP_GUIDE = {
    "베이스": {
        "steps": [
            "1. 스킨케어로 촉촉한 피부 준비",
            "2. 프라이머로 모공 정리",
            "3. 파운데이션은 본인 피부톤과 동일하게",
            "4. 컨실러로 다크서클, 잡티 커버",
            "5. 파우더로 가볍게 세팅"
        ],
        "tips": [
            "너무 하얀 화장 X (목과 경계선 주의)",
            "매트보다는 세미매트 추천",
            "면접장 조명 아래서 확인 필수"
        ]
    },
    "눈": {
        "steps": [
            "1. 아이브로우: 자연스러운 아치형",
            "2. 아이섀도우: 베이지~브라운 그라데이션",
            "3. 아이라인: 가늘게, 눈꼬리 살짝 빼기",
            "4. 마스카라: 깔끔하게 한두 겹"
        ],
        "tips": [
            "글리터/펄 아이섀도우 지양",
            "속눈썹 연장은 자연스러운 정도만",
            "눈 밑 펄 하이라이터 X"
        ]
    },
    "입술": {
        "steps": [
            "1. 립밤으로 각질 정리",
            "2. 립라이너로 입술선 정리 (선택)",
            "3. 립스틱 바르기",
            "4. 티슈로 가볍게 눌러 지속력 UP"
        ],
        "tips": [
            "FSC: 코랄, 핑크, MLBB 추천",
            "LCC: 오렌지, 레드 포인트 가능",
            "너무 진한 레드/다크톤 지양"
        ]
    },
    "치크": {
        "steps": [
            "1. 미소 지었을 때 볼록한 부분에",
            "2. 브러시로 가볍게 터치",
            "3. 자연스럽게 블렌딩"
        ],
        "tips": [
            "피부톤에 맞는 코랄/피치 계열",
            "너무 진하게 X",
            "하이라이터는 C존에만 살짝"
        ]
    }
}

# ========================================
# 헤어스타일 가이드
# ========================================
HAIR_GUIDE = {
    "쪽머리 (Bun)": {
        "description": "가장 클래식한 승무원 헤어스타일",
        "suitable": ["대한항공", "아시아나항공", "에어로케이"],
        "steps": [
            "1. 머리를 깔끔하게 빗어 뒤로 모으기",
            "2. 높이는 귀 윗선~정수리 중간",
            "3. 고무줄로 단단히 묶기",
            "4. 돌돌 말아서 쪽 만들기",
            "5. 헤어핀으로 고정",
            "6. 망사망으로 감싸 마무리",
            "7. 스프레이로 잔머리 정리"
        ],
        "tips": ["잔머리 정리 필수", "망사망 색상은 머리색과 동일하게"]
    },
    "포니테일": {
        "description": "깔끔하고 활동적인 느낌",
        "suitable": ["진에어", "제주항공", "에어프레미아", "이스타항공", "파라타항공"],
        "steps": [
            "1. 머리를 빗어 뒤로 모으기",
            "2. 귀 윗선 높이에서 묶기",
            "3. 고무줄을 머리카락으로 감싸기",
            "4. 스프레이로 잔머리 정리"
        ],
        "tips": ["너무 높거나 낮지 않게", "머리끝은 깔끔하게 정리"]
    },
    "반묶음 (하프업)": {
        "description": "부드럽고 여성스러운 느낌",
        "suitable": ["LCC 일부"],
        "steps": [
            "1. 윗머리만 뒤로 모으기",
            "2. 귀 윗선에서 단정하게 묶기",
            "3. 아랫머리는 깔끔하게 정리"
        ],
        "tips": ["단발~중단발에 적합", "FSC는 피하는 것이 좋음"]
    },
    "단발": {
        "description": "깔끔하고 세련된 느낌",
        "suitable": ["에어프레미아", "에어서울", "LCC"],
        "steps": [
            "1. 깔끔하게 손질된 단발",
            "2. 헤어핀으로 귀 뒤로 넘기기",
            "3. 스프레이로 고정"
        ],
        "tips": ["어깨 위 길이", "앞머리는 이마가 보이게 정리"]
    }
}

# ========================================
# 복장 가이드
# ========================================
OUTFIT_GUIDE = {
    "정장 상의": {
        "do": ["몸에 맞는 사이즈", "네이비, 그레이, 블랙", "싱글 버튼 자켓", "어깨선 딱 맞는 것"],
        "dont": ["화려한 패턴이나 색상", "너무 짧은 자켓", "과한 장식"]
    },
    "스커트": {
        "do": ["무릎 위 3~5cm (H라인)", "편하게 앉을 수 있는 핏", "상의와 어울리는 색상"],
        "dont": ["너무 짧은 미니", "너무 타이트한 핏", "깊은 슬릿"]
    },
    "블라우스": {
        "do": ["화이트, 베이비블루, 연핑크", "깔끔한 카라", "적당한 목선"],
        "dont": ["시스루 소재", "과한 프릴/장식", "너무 깊은 브이넥"]
    },
    "구두": {
        "do": ["베이지 또는 블랙 단색", "5~7cm 굽", "앞코 막힌 펌프스"],
        "dont": ["오픈토, 슬링백", "화려한 장식", "너무 높거나 낮은 굽"]
    },
    "악세서리": {
        "do": ["작은 진주/골드 귀걸이", "심플한 목걸이 (선택)", "깔끔한 손목시계"],
        "dont": ["큰 후프 귀걸이", "화려한 목걸이", "팔찌/반지 여러 개"]
    }
}

# ========================================
# NG 사례 데이터
# ========================================
NG_CASES = {
    "메이크업 NG": [
        {"ng": "너무 하얀 파운데이션 (목과 얼굴 색 차이)", "fix": "본인 피부톤과 동일한 색상 선택, 목까지 자연스럽게 블렌딩"},
        {"ng": "과한 펄/글리터 아이섀도우", "fix": "매트~세미매트 베이지/브라운 계열로 변경"},
        {"ng": "쌍꺼풀 테이프가 눈에 보이는 경우", "fix": "메시 타입 사용하거나, 안 하는 것이 나음"},
        {"ng": "속눈썹 연장이 너무 과한 경우", "fix": "자연스러운 C~J컬, 길이는 본인 눈 폭 이내"},
        {"ng": "너무 진한 컨투어링", "fix": "얼굴형 보정은 최소한으로, 자연스러운 쉐딩만"},
        {"ng": "립스틱이 치아에 묻은 경우", "fix": "바르고 손가락을 입에 넣었다 빼기 (안쪽 제거)"},
        {"ng": "눈밑 다크서클이 그대로 보이는 경우", "fix": "살구색 컨실러로 보색 커버 후 파운데이션"},
    ],
    "헤어 NG": [
        {"ng": "잔머리가 삐죽삐죽 튀어나옴", "fix": "왁스스틱 + 헤어스프레이로 밀착 정리"},
        {"ng": "머리색이 너무 밝은 금발/탈색", "fix": "자연스러운 다크브라운까지만 (면접 2주 전 염색)"},
        {"ng": "뿌리 염색이 자란 투톤 상태", "fix": "면접 1주 전 뿌리 리터치 필수"},
        {"ng": "앞머리가 눈을 가리는 경우", "fix": "이마가 보이게 옆으로 넘기거나 핀으로 고정"},
        {"ng": "쪽머리가 삐뚤거나 지저분한 경우", "fix": "충분히 연습하거나 미용실에서 세팅"},
        {"ng": "헤어 악세서리가 화려한 경우", "fix": "검정/갈색 기본 핀만 사용, 장식 핀 X"},
    ],
    "복장 NG": [
        {"ng": "정장 사이즈가 안 맞음 (너무 크거나 작음)", "fix": "수선 필수! 어깨선과 허리라인 맞추기"},
        {"ng": "스타킹에 올이 나간 상태", "fix": "여분 스타킹 2개 이상 항상 지참"},
        {"ng": "구두에 때가 타거나 굽이 닳은 경우", "fix": "면접 전날 구두약으로 관리, 필요시 새 구두"},
        {"ng": "속옷 라인이 비치는 경우", "fix": "심리스 속옷 착용, 누드톤 선택"},
        {"ng": "향수가 너무 강한 경우", "fix": "무향 or 아주 가볍게만 (면접관이 불쾌할 수 있음)"},
        {"ng": "네일이 화려한 경우 (네일아트, 긴 손톱)", "fix": "투명 or 연한 핑크, 짧고 깔끔하게"},
        {"ng": "가방이 너무 크거나 캐주얼한 경우", "fix": "A4 서류 들어가는 깔끔한 토트백 추천"},
    ],
    "태도/자세 NG": [
        {"ng": "구부정한 자세로 대기", "fix": "등은 곧게, 어깨는 편하게 펴기"},
        {"ng": "다리를 꼬거나 벌리고 앉기", "fix": "무릎 붙이고, 다리는 살짝 비스듬히"},
        {"ng": "시선이 불안정 (두리번거림)", "fix": "면접관 미간~코 사이를 편안하게 응시"},
        {"ng": "미소 없이 굳은 표정", "fix": "대기 시부터 가볍게 미소, 입꼬리 올리기"},
        {"ng": "손을 너무 많이 움직이거나 만지작거림", "fix": "양손은 무릎 위에 가지런히"},
    ],
}

# ========================================
# 셀프 체크 질문
# ========================================
SELF_CHECK = {
    "메이크업": [
        "파운데이션 색상이 목과 자연스럽게 연결되나요?",
        "아이섀도우가 매트/세미매트 계열인가요?",
        "아이라인이 자연스럽게 그려졌나요?",
        "립 색상이 항공사 분위기에 맞나요?",
        "전체적으로 자연스럽고 깨끗한 느낌인가요?",
        "치크가 과하지 않게 들어갔나요?",
        "다크서클이 잘 커버되었나요?",
    ],
    "헤어": [
        "잔머리가 깔끔하게 정리되었나요?",
        "앞머리가 이마를 가리지 않나요?",
        "머리색이 자연스러운 톤인가요?",
        "헤어스타일이 지원 항공사에 적합한가요?",
        "뒷모습도 깔끔한가요?",
    ],
    "복장": [
        "정장 사이즈가 몸에 맞나요?",
        "블라우스가 깔끔하고 주름 없나요?",
        "스커트 길이가 적절한가요? (무릎 위 3~5cm)",
        "스타킹에 올이 없나요?",
        "구두가 깨끗하고 굽 상태가 좋은가요?",
        "악세서리가 심플한가요?",
        "속옷 라인이 비치지 않나요?",
        "전신 거울로 뒷모습까지 확인했나요?",
    ],
    "태도": [
        "바른 자세로 서고 앉을 수 있나요?",
        "자연스러운 미소를 유지할 수 있나요?",
        "시선 처리가 안정적인가요?",
        "걸음걸이가 단정한가요?",
        "인사할 때 허리 각도가 적절한가요? (30~45도)",
    ],
}

# ========================================
# 면접 당일 타임라인
# ========================================
TIMELINE = [
    {"time": "3시간 전", "tasks": ["기상 + 가벼운 스트레칭", "세안 + 스킨케어 (충분히 흡수시키기)", "아침 식사 (가볍게, 냄새나는 음식 X)"], "icon": ""},
    {"time": "2시간 30분 전", "tasks": ["베이스 메이크업 시작", "컨실러 → 파운데이션 → 세팅", "눈썹 정리"], "icon": ""},
    {"time": "2시간 전", "tasks": ["아이 메이크업 + 립 + 치크", "메이크업 전체 확인 (자연광에서)", "수정할 부분 터치업"], "icon": ""},
    {"time": "1시간 30분 전", "tasks": ["헤어스타일 세팅", "잔머리 정리 + 스프레이 고정", "앞/옆/뒷모습 확인"], "icon": ""},
    {"time": "1시간 전", "tasks": ["복장 착용 (블라우스 → 스커트 → 자켓)", "스타킹 올 확인", "구두 착용 + 전신 확인"], "icon": ""},
    {"time": "45분 전", "tasks": ["소지품 최종 점검 (서류, 여분 스타킹, 거울, 립)", "핸드폰 무음 확인", "집 출발"], "icon": ""},
    {"time": "30분 전", "tasks": ["면접장 도착 (여유있게!)", "화장실에서 최종 점검", "미소 연습 + 자세 확인"], "icon": ""},
    {"time": "10분 전", "tasks": ["대기실에서 바른 자세로 대기", "가벼운 미소 유지", "심호흡으로 긴장 완화"], "icon": ""},
]

# ========================================
# 계절별 팁
# ========================================
SEASON_TIPS = {
    "여름 (6~8월)": {
        "메이크업": [
            "세팅 스프레이 필수 (땀으로 무너짐 방지)",
            "워터프루프 마스카라/아이라이너 사용",
            "파우더 휴대하여 T존 수시 터치",
            "립틴트 + 립밤 조합 (지속력 UP)",
        ],
        "헤어": [
            "습기로 잔머리 더 심함 → 왁스스틱 필수",
            "무스/젤로 고정력 강화",
            "면접장 도착 후 화장실에서 재정리",
        ],
        "복장": [
            "얇은 소재 정장 (린넨은 피하기 - 구김)",
            "땀 흡수 좋은 이너 착용",
            "여분 블라우스 가져가기 (땀 대비)",
            "데오도란트 사용 (무향 추천)",
        ],
    },
    "겨울 (12~2월)": {
        "메이크업": [
            "보습 강화 (건조함으로 각질 주의)",
            "촉촉한 파운데이션 선택",
            "립밤 충분히 바른 후 립스틱",
            "코 주변 건조함 커버",
        ],
        "헤어": [
            "정전기 방지 스프레이 사용",
            "모자/목도리로 인한 헤어 무너짐 주의",
            "면접장 도착 후 헤어 재정리 필수",
        ],
        "복장": [
            "코트는 면접장 밖에서 벗기",
            "히트텍 착용 가능 (목선이 안 보이는 것)",
            "부츠는 X → 펌프스 별도 지참",
            "손이 차가우면 악수 전 주머니에 손 넣어두기",
        ],
    },
    "환절기 (3~5월, 9~11월)": {
        "메이크업": [
            "아침/낮 온도차 고려하여 세팅",
            "자외선 차단제 필수 (봄 자외선 강함)",
            "적당한 보습 + 세팅 밸런스",
        ],
        "헤어": [
            "바람이 강한 날 스프레이 추가 사용",
            "우천 시 우산 + 헤어 보호",
        ],
        "복장": [
            "가디건/얇은 자켓 겹쳐입기 가능",
            "우천 대비 구두 커버 지참",
            "바람에 스커트 날림 주의 (H라인 추천)",
        ],
    },
}

# ========================================
# 화상면접 팁
# ========================================
ONLINE_TIPS = {
    "카메라/조명": [
        "카메라는 눈높이에 맞추기 (노트북 받침 사용)",
        "자연광 or 링라이트를 정면에서 비추기",
        "역광 절대 X (얼굴이 어두워짐)",
        "배경은 깔끔한 단색 벽 (화이트/베이지)",
    ],
    "메이크업 차이": [
        "카메라는 색감을 줄이므로 10~20% 더 진하게",
        "립 색상을 좀 더 선명하게",
        "치크를 조금 더 넣기 (화면에서 밋밋해 보일 수 있음)",
        "하이라이터는 화면에서 번들거려 보이므로 X",
    ],
    "복장": [
        "상의는 무조건 정장 (하의도 입는 것 추천)",
        "화면에서 무늬가 번져보일 수 있음 → 단색 추천",
        "흰색은 화면에서 날아감 → 아이보리/베이지 추천",
    ],
    "기타": [
        "테스트 촬영으로 화면 속 본인 모습 미리 확인",
        "이어폰/마이크 상태 점검",
        "알림/팝업 모두 끄기",
        "가족에게 면접 시간 알려서 방해 방지",
    ],
}


# ========================================
# CSS
# ========================================
st.markdown("""
<style>
.timeline-item {
    background: white;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 4px solid #667eea;
}
.ng-card {
    background: #fff5f5;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    border-left: 3px solid #dc3545;
}
.fix-card {
    background: #f0fff4;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 6px 0;
    border-left: 3px solid #28a745;
}
.check-score {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border-radius: 20px;
    padding: 30px;
    text-align: center;
    margin: 20px 0;
}
.season-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 16px;
    margin: 8px 0;
}
</style>
""", unsafe_allow_html=True)


# ========================================
# 메인 UI
# ========================================
st.title("이미지메이킹 가이드")
st.caption("항공사 면접을 위한 메이크업, 헤어, 복장, 셀프체크까지!")

# 탭
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
 " 셀프 체크", "⏰ 당일 타임라인", " 메이크업",
 " 헤어", " 복장", "️ NG 사례", "️ 항공사별"
])


# ========================================
# 탭1: 셀프 체크
# ========================================
with tab1:
    st.subheader(" 이미지 셀프 체크")
    st.markdown("각 항목을 체크하고 현재 준비도를 확인하세요!")

    total_checks = 0
    total_checked = 0

    for category, questions in SELF_CHECK.items():
        emoji_map = {"메이크업": "", "헤어": "", "복장": "", "태도": ""}
        emoji = emoji_map.get(category, "")

        st.markdown(f"#### {emoji} {category}")

        checked = 0
        for i, q in enumerate(questions):
            if st.checkbox(q, key=f"check_{category}_{i}"):
                checked += 1
        total_checked += checked
        total_checks += len(questions)

        progress = checked / len(questions)
        if progress == 1.0:
            st.success(f" {category} 완벽!")
        elif progress >= 0.7:
            st.info(f" {category} {int(progress*100)}% 준비됨")
        elif progress > 0:
            st.warning(f" {category} {int(progress*100)}% - 더 준비하세요!")

        st.markdown("---")

    # 종합 점수
    overall = int(total_checked / total_checks * 100) if total_checks > 0 else 0

    if overall >= 90:
        grade_text = "완벽한 준비! "
        grade_color = "#28a745"
    elif overall >= 70:
        grade_text = "거의 다 됐어요! "
        grade_color = "#4facfe"
    elif overall >= 50:
        grade_text = "조금 더 준비하세요! "
        grade_color = "#ffc107"
    else:
        grade_text = "아직 준비가 필요해요! "
        grade_color = "#dc3545"

    st.markdown(f"""
    <div class="check-score">
        <div style="font-size: 48px; font-weight: bold;">{overall}%</div>
        <div style="font-size: 18px; margin-top: 10px;">{grade_text}</div>
        <div style="font-size: 14px; opacity: 0.8; margin-top: 5px;">{total_checked}/{total_checks} 항목 체크</div>
    </div>
    """, unsafe_allow_html=True)


# ========================================
# 탭2: 당일 타임라인
# ========================================
with tab2:
    st.subheader("⏰ 면접 당일 준비 타임라인")
    st.info("면접 시간 기준으로 역산하여 준비하세요! (예: 10시 면접 → 7시 기상)")

    for item in TIMELINE:
        tasks_html = "<br>".join([f"• {t}" for t in item["tasks"]])
        st.markdown(f"""
        <div class="timeline-item">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="font-size: 28px;">{item['icon']}</div>
                <div>
                    <div style="font-weight: bold; font-size: 16px; color: #667eea;">면접 {item['time']}</div>
                    <div style="margin-top: 5px; font-size: 14px; color: #555;">{tasks_html}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 계절별 팁
    st.markdown("### ️ 계절별 추가 팁")

    season = st.selectbox("계절 선택", list(SEASON_TIPS.keys()), key="season_select")
    tips = SEASON_TIPS[season]

    cols = st.columns(3)
    for i, (cat, tip_list) in enumerate(tips.items()):
        with cols[i]:
            st.markdown(f"**{cat}**")
            for t in tip_list:
                st.caption(f"• {t}")

    # 화상면접 팁
    st.markdown("---")
    st.markdown("### 화상면접 이미지 팁")

    for category, tips_list in ONLINE_TIPS.items():
        with st.expander(f" {category}"):
            for t in tips_list:
                st.markdown(f"- {t}")


# ========================================
# 탭3: 메이크업
# ========================================
with tab3:
    st.subheader(" 면접 메이크업 가이드")

    for part, info in MAKEUP_GUIDE.items():
        with st.expander(f" {part} 메이크업", expanded=(part == "베이스")):
            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown("**순서:**")
                for step in info["steps"]:
                    st.markdown(step)
            with col2:
                st.markdown("**주의사항:**")
                for tip in info["tips"]:
                    st.info(tip)

    st.markdown("---")
    st.success("""
    **핵심 포인트**
    - 자연스럽고 깨끗한 피부 표현
    - 과하지 않은 눈 화장
    - 건강하고 밝은 입술
    - 전체적으로 '단정하고 신뢰감 있는' 인상
    """)


# ========================================
# 탭4: 헤어스타일
# ========================================
with tab4:
    st.subheader(" 면접 헤어스타일 가이드")

    for style, info in HAIR_GUIDE.items():
        with st.expander(f"‍️ {style}"):
            st.markdown(f"**{info['description']}**")
            st.caption(f"추천 항공사: {', '.join(info['suitable'])}")
            st.markdown("---")

            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown("**방법:**")
                for step in info["steps"]:
                    st.markdown(step)
            with col2:
                st.markdown("**팁:**")
                for tip in info["tips"]:
                    st.info(tip)

    st.markdown("---")
    st.warning("""
    **공통 주의사항**
    - 염색은 자연스러운 갈색까지만 (탈색 X)
    - 잔머리 정리 필수 (왁스/스프레이 활용)
    - 앞머리는 이마가 보이게 정리
    - 면접 전날 미용실에서 정리 추천
    """)


# ========================================
# 탭5: 복장
# ========================================
with tab5:
    st.subheader(" 면접 복장 가이드")

    for item_name, info in OUTFIT_GUIDE.items():
        with st.expander(f" {item_name}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("** DO**")
                for do in info["do"]:
                    st.success(do)
            with col2:
                st.markdown("** DON'T**")
                for dont in info["dont"]:
                    st.error(dont)

    st.markdown("---")
    st.info("""
    **면접 전 체크리스트**
    - 정장에 보풀/먼지 제거
    - 구두 광택
    - 스타킹 여분 2개 준비
    - 옷에서 냄새나지 않는지 확인
    - 전신 거울로 뒷모습까지 확인
    """)


# ========================================
# 탭6: NG 사례
# ========================================
with tab6:
    st.subheader("️ NG 사례 모음")
    st.markdown("이렇게 하면 감점! 흔한 실수와 올바른 대안을 확인하세요.")

    for category, cases in NG_CASES.items():
        st.markdown(f"### {'' if '메이크업' in category else '' if '헤어' in category else '' if '복장' in category else ''} {category}")

        for case in cases:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""<div class="ng-card"> {case['ng']}</div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="fix-card"> {case['fix']}</div>""", unsafe_allow_html=True)

        st.markdown("---")


# ========================================
# 탭7: 항공사별 (비교 기능 포함)
# ========================================
with tab7:
    st.subheader("️ 항공사별 이미지 가이드")

    # 비교 모드 선택
    mode = st.radio("보기 모드", ["개별 조회", "2개 항공사 비교"], horizontal=True, key="airline_mode")

    if mode == "개별 조회":
        selected = st.selectbox("항공사 선택", list(AIRLINE_IMAGE.keys()), key="single_airline")
        info = AIRLINE_IMAGE[selected]

        st.markdown(f"""
        <div style="background: {info['color']}; padding: 20px; border-radius: 12px; color: white; text-align: center;">
            <h2 style="margin: 0; color: white;">{selected}</h2>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{info['style']} | {info['type']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        keyword_html = " ".join([f'<span style="background: {info["color"]}20; color: {info["color"]}; padding: 5px 15px; border-radius: 20px; margin: 3px; display: inline-block; font-weight: 600;">#{kw}</span>' for kw in info["keywords"]])
        st.markdown(keyword_html, unsafe_allow_html=True)

        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("** 메이크업**")
            st.write(info["makeup"])
        with col2:
            st.markdown("** 헤어**")
            st.write(info["hair"])
        with col3:
            st.markdown("** 복장**")
            st.write(info["outfit"])

        st.info(f" **TIP:** {info['tip']}")

    else:  # 2개 비교
        col1, col2 = st.columns(2)
        with col1:
            airline1 = st.selectbox("항공사 1", list(AIRLINE_IMAGE.keys()), key="compare1")
        with col2:
            options2 = [a for a in AIRLINE_IMAGE.keys() if a != airline1]
            airline2 = st.selectbox("항공사 2", options2, key="compare2")

        info1 = AIRLINE_IMAGE[airline1]
        info2 = AIRLINE_IMAGE[airline2]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"""
            <div style="background: {info1['color']}; padding: 15px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin: 0; color: white;">{airline1}</h3>
                <p style="margin: 3px 0 0 0; opacity: 0.9; font-size: 14px;">{info1['style']} | {info1['type']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            st.markdown(f"** 메이크업:** {info1['makeup']}")
            st.markdown(f"** 헤어:** {info1['hair']}")
            st.markdown(f"** 복장:** {info1['outfit']}")
            st.caption(f"키워드: {', '.join(info1['keywords'])}")
            st.info(f" {info1['tip']}")

        with col2:
            st.markdown(f"""
            <div style="background: {info2['color']}; padding: 15px; border-radius: 10px; color: white; text-align: center;">
                <h3 style="margin: 0; color: white;">{airline2}</h3>
                <p style="margin: 3px 0 0 0; opacity: 0.9; font-size: 14px;">{info2['style']} | {info2['type']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("")
            st.markdown(f"** 메이크업:** {info2['makeup']}")
            st.markdown(f"** 헤어:** {info2['hair']}")
            st.markdown(f"** 복장:** {info2['outfit']}")
            st.caption(f"키워드: {', '.join(info2['keywords'])}")
            st.info(f" {info2['tip']}")

    # 전체 비교표
    st.markdown("---")
    st.markdown("### 전체 항공사 비교")

    comparison_data = []
    for airline, data in AIRLINE_IMAGE.items():
        comparison_data.append({
            "항공사": airline,
            "유형": data["type"],
            "스타일": data["style"],
            "키워드": ", ".join(data["keywords"])
        })

    st.dataframe(comparison_data, use_container_width=True, hide_index=True)

st.markdown('</div>', unsafe_allow_html=True)
