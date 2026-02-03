# resume_template.py
# Phase C3: 자소서 템플릿 모듈
# FlyReady Lab Enhancement

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re


class ResumeItemType(Enum):
    """자소서 항목 유형"""
    MOTIVATION = "지원동기"
    PERSONALITY = "성격의 장단점"
    SERVICE = "서비스 경험"
    TEAMWORK = "팀워크/협업"
    GOAL = "입사 후 포부"
    STRENGTH = "본인의 강점"
    CRISIS = "위기관리 경험"
    GROWTH = "성장 과정"


@dataclass
class TemplateSection:
    """템플릿 섹션"""
    title: str
    description: str
    example: str
    char_limit: Tuple[int, int]  # (min, max)
    keywords_to_include: List[str]
    tips: List[str]


@dataclass
class ResumeTemplate:
    """자소서 템플릿"""
    airline: str
    item_type: ResumeItemType
    total_char_limit: Tuple[int, int]
    sections: List[TemplateSection]
    airline_keywords: List[str]
    must_include: List[str]
    avoid: List[str]
    example_outline: str


# =====================
# 항공사별 특성 데이터
# =====================

AIRLINE_CHARACTERISTICS = {
    "대한항공": {
        "type": "FSC",
        "core_values": ["Excellence in Flight", "안전", "세계적 수준", "프리미엄 서비스"],
        "talent_keywords": ["글로벌", "도전", "전문성", "소통", "신뢰"],
        "interview_style": "격식 있는 FSC 스타일, 글로벌 역량 중시",
        "emphasis": ["외국어 능력", "글로벌 경험", "품격 있는 서비스"],
        "avoid": ["LCC 언급", "단순 업무 선호", "안정 지향만"],
    },
    "아시아나항공": {
        "type": "FSC",
        "core_values": ["아름다운 사람들", "최상의 서비스", "안전 최우선"],
        "talent_keywords": ["창의", "열정", "신뢰", "도전", "배려"],
        "interview_style": "부드럽지만 깊이 있는 질문, 서비스 마인드 중시",
        "emphasis": ["세심한 배려", "고객 감동", "팀워크"],
        "avoid": ["합병 관련 부정적 언급", "불안정 표현"],
    },
    "제주항공": {
        "type": "LCC",
        "core_values": ["가성비", "안전", "고객 만족", "LCC 선두"],
        "talent_keywords": ["열정", "혁신", "동반성장", "고객중심", "효율"],
        "interview_style": "실용적이고 효율적, 멀티태스킹 능력 중시",
        "emphasis": ["효율성", "긍정 에너지", "유연성"],
        "avoid": ["비싼", "고급", "FSC 동경"],
    },
    "진에어": {
        "type": "LCC",
        "core_values": ["즐거운 여행", "합리적 가격", "트렌디"],
        "talent_keywords": ["Fun", "젊음", "도전", "소통", "창의"],
        "interview_style": "밝고 자유로운 분위기, MZ 감성 중시",
        "emphasis": ["밝은 에너지", "트렌드 감각", "유연한 사고"],
        "avoid": ["무거운 분위기", "형식적 표현"],
    },
    "티웨이항공": {
        "type": "LCC",
        "core_values": ["합리적 여행", "따뜻한 서비스", "안전"],
        "talent_keywords": ["소통", "도전", "전문성", "즐거움", "따뜻함"],
        "interview_style": "따뜻하고 친근한 분위기, 서비스 마인드 중시",
        "emphasis": ["따뜻한 배려", "고객 친화", "성장 의지"],
        "avoid": ["차가운", "기계적", "효율만 강조"],
    },
    "에어부산": {
        "type": "LCC",
        "core_values": ["부산 대표", "친근한 서비스", "안전 운항"],
        "talent_keywords": ["안전", "고객", "혁신", "소통", "지역사랑"],
        "interview_style": "친근하고 편안한 분위기",
        "emphasis": ["부산/지역 애정", "친근함", "안전 의식"],
        "avoid": [],
    },
    "에어서울": {
        "type": "LCC",
        "core_values": ["도심 연결", "편안한 여행"],
        "talent_keywords": ["서비스", "안전", "도전", "협력"],
        "interview_style": "안정적이고 차분한 분위기",
        "emphasis": ["편안한 서비스", "협력", "안전 의식"],
        "avoid": [],
    },
    "이스타항공": {
        "type": "LCC",
        "core_values": ["새로운 시작", "안전", "고객 행복"],
        "talent_keywords": ["열정", "도전", "성장", "팀워크", "적응력"],
        "interview_style": "열정과 도전 정신 중시",
        "emphasis": ["열정", "적응력", "성장 의지"],
        "avoid": ["불안", "위기 언급 시 부정적 톤"],
    },
    "에어프레미아": {
        "type": "HSC",
        "core_values": ["하이브리드 항공", "합리적 프리미엄", "장거리 LCC"],
        "talent_keywords": ["프리미엄", "도전", "혁신", "전문성", "글로벌"],
        "interview_style": "혁신적이고 전문성 중시",
        "emphasis": ["장거리 적응", "체력", "프리미엄 서비스"],
        "avoid": ["저가만 강조"],
    },
    "에어로케이": {
        "type": "LCC",
        "core_values": ["안전 운항", "고객 중심"],
        "talent_keywords": ["안전", "고객", "소통", "성장", "책임감"],
        "interview_style": "기본기 중시, 안정적 분위기",
        "emphasis": ["안전 의식", "책임감", "성장 의지"],
        "avoid": [],
    },
    "플라이강원": {
        "type": "LCC",
        "core_values": ["강원 연결", "지역 발전"],
        "talent_keywords": ["도전", "열정", "지역 사랑"],
        "interview_style": "지역 애정 중시",
        "emphasis": ["지역 애정", "도전 정신", "적응력"],
        "avoid": [],
    },
}

# =====================
# 항목별 템플릿 구조
# =====================

ITEM_TEMPLATE_STRUCTURES = {
    ResumeItemType.MOTIVATION: {
        "sections": [
            {
                "title": "도입 (훅)",
                "description": "관심을 끄는 시작 - 구체적 계기나 인상적인 장면",
                "char_ratio": 0.2,
                "required": True,
            },
            {
                "title": "항공사 연구",
                "description": "해당 항공사만의 특성, 가치, 차별점 언급",
                "char_ratio": 0.25,
                "required": True,
            },
            {
                "title": "가치관 연결",
                "description": "본인의 경험/가치관과 항공사의 연결점",
                "char_ratio": 0.35,
                "required": True,
            },
            {
                "title": "포부",
                "description": "입사 후 기여하고 싶은 구체적인 부분",
                "char_ratio": 0.2,
                "required": True,
            },
        ],
        "ideal_length": (400, 500),
        "tips": [
            "어릴 때부터 꿈이었다는 진부한 표현 피하기",
            "해당 항공사만의 특성을 반드시 언급",
            "추상적 열정보다 구체적 경험 중심으로",
        ],
    },
    ResumeItemType.PERSONALITY: {
        "sections": [
            {
                "title": "장점 제시",
                "description": "핵심 장점 1-2가지 명확하게 제시",
                "char_ratio": 0.15,
                "required": True,
            },
            {
                "title": "장점 증명 에피소드",
                "description": "장점을 보여주는 구체적 경험 (STAR)",
                "char_ratio": 0.35,
                "required": True,
            },
            {
                "title": "단점 인정",
                "description": "솔직하게 인정하되 치명적이지 않은 것",
                "char_ratio": 0.15,
                "required": True,
            },
            {
                "title": "극복 노력 & 결과",
                "description": "단점을 개선하기 위한 구체적 노력과 변화",
                "char_ratio": 0.35,
                "required": True,
            },
        ],
        "ideal_length": (450, 550),
        "tips": [
            "장점은 승무원 직무와 연결되는 것으로",
            "단점을 장점으로 포장하지 말 것 (솔직함 중요)",
            "극복 과정에서 성장을 보여주기",
        ],
    },
    ResumeItemType.SERVICE: {
        "sections": [
            {
                "title": "상황 (Situation)",
                "description": "언제, 어디서, 어떤 상황이었는지",
                "char_ratio": 0.2,
                "required": True,
            },
            {
                "title": "과제 (Task)",
                "description": "어떤 문제/과제가 있었는지",
                "char_ratio": 0.15,
                "required": True,
            },
            {
                "title": "행동 (Action)",
                "description": "본인이 취한 구체적 행동들",
                "char_ratio": 0.35,
                "required": True,
            },
            {
                "title": "결과 & 교훈 (Result)",
                "description": "결과와 그 경험에서 배운 점",
                "char_ratio": 0.3,
                "required": True,
            },
        ],
        "ideal_length": (450, 600),
        "tips": [
            "STAR 구조를 반드시 활용",
            "본인의 행동을 가장 구체적으로 작성",
            "결과는 가능하면 수치화",
        ],
    },
    ResumeItemType.TEAMWORK: {
        "sections": [
            {
                "title": "팀 상황",
                "description": "어떤 팀에서 어떤 프로젝트/활동이었는지",
                "char_ratio": 0.2,
                "required": True,
            },
            {
                "title": "문제/갈등",
                "description": "팀에서 발생한 어려움이나 갈등",
                "char_ratio": 0.2,
                "required": True,
            },
            {
                "title": "본인 역할 & 행동",
                "description": "본인이 맡은 역할과 취한 행동",
                "char_ratio": 0.35,
                "required": True,
            },
            {
                "title": "결과 & 기여",
                "description": "팀 성과와 본인의 기여도",
                "char_ratio": 0.25,
                "required": True,
            },
        ],
        "ideal_length": (400, 550),
        "tips": [
            "팀 성과만 강조하지 말고 본인 기여 명확히",
            "갈등 해결 과정이 있으면 플러스",
            "리더/팔로워 역할 모두 가치 있음을 보여주기",
        ],
    },
    ResumeItemType.GOAL: {
        "sections": [
            {
                "title": "단기 목표",
                "description": "입사 후 1-2년 내 달성하고 싶은 목표",
                "char_ratio": 0.3,
                "required": True,
            },
            {
                "title": "실행 방법",
                "description": "목표 달성을 위한 구체적 방법",
                "char_ratio": 0.3,
                "required": True,
            },
            {
                "title": "장기 비전",
                "description": "5-10년 후 성장 비전, 회사 기여",
                "char_ratio": 0.25,
                "required": True,
            },
            {
                "title": "회사와의 연결",
                "description": "개인 성장과 회사 발전의 연결",
                "char_ratio": 0.15,
                "required": True,
            },
        ],
        "ideal_length": (350, 450),
        "tips": [
            "최고가 되겠다는 추상적 목표 피하기",
            "구체적이고 실현 가능한 목표 제시",
            "회사 비전과 연결해서 마무리",
        ],
    },
}


# =====================
# 키워드 추천 엔진
# =====================

class KeywordRecommender:
    """항공사별 키워드 추천"""

    # 공통 서비스 키워드
    COMMON_SERVICE_KEYWORDS = [
        "고객 만족", "안전 의식", "서비스 마인드", "배려심",
        "소통 능력", "팀워크", "책임감", "긍정 에너지",
    ]

    # 항목별 필수 키워드
    ITEM_KEYWORDS = {
        ResumeItemType.MOTIVATION: ["지원 계기", "항공사 특성", "직무 이해", "가치관 일치"],
        ResumeItemType.PERSONALITY: ["강점", "성장", "극복", "자기 객관화"],
        ResumeItemType.SERVICE: ["고객 응대", "문제 해결", "상황 판단", "결과 도출"],
        ResumeItemType.TEAMWORK: ["협업", "역할 분담", "갈등 해결", "기여"],
        ResumeItemType.GOAL: ["목표 설정", "실행 계획", "성장 비전", "회사 기여"],
    }

    def get_recommended_keywords(
        self,
        airline: str,
        item_type: ResumeItemType
    ) -> Dict[str, List[str]]:
        """항공사+항목 맞춤 키워드 추천"""

        airline_data = AIRLINE_CHARACTERISTICS.get(airline, {})

        # 항공사 유형별 키워드
        airline_type = airline_data.get("type", "LCC")
        type_keywords = {
            "FSC": ["글로벌", "품격", "전문성", "프리미엄"],
            "LCC": ["효율", "밝은 에너지", "유연성", "고객 친화"],
            "HSC": ["혁신", "프리미엄", "차별화", "글로벌"],
        }

        return {
            "airline_core": airline_data.get("core_values", [])[:3],
            "airline_talent": airline_data.get("talent_keywords", [])[:4],
            "type_keywords": type_keywords.get(airline_type, []),
            "item_keywords": self.ITEM_KEYWORDS.get(item_type, []),
            "common_keywords": self.COMMON_SERVICE_KEYWORDS[:4],
        }

    def check_keyword_usage(
        self,
        text: str,
        airline: str,
        item_type: ResumeItemType
    ) -> Dict[str, any]:
        """키워드 사용 현황 체크"""

        recommendations = self.get_recommended_keywords(airline, item_type)

        # 모든 추천 키워드 합치기
        all_keywords = []
        for category, keywords in recommendations.items():
            all_keywords.extend(keywords)

        # 사용 여부 체크
        used = [kw for kw in all_keywords if kw in text]
        missing = [kw for kw in all_keywords if kw not in text]

        # 점수 계산
        score = int((len(used) / len(all_keywords)) * 100) if all_keywords else 0

        return {
            "used_keywords": used,
            "missing_keywords": missing[:8],
            "usage_score": score,
            "recommendation": self._get_recommendation(score, missing),
        }

    def _get_recommendation(self, score: int, missing: List[str]) -> str:
        if score >= 70:
            return "키워드 사용이 양호합니다!"
        elif score >= 40:
            return f"다음 키워드를 추가해보세요: {', '.join(missing[:3])}"
        else:
            return f"핵심 키워드가 부족합니다. 추가 필요: {', '.join(missing[:5])}"


# =====================
# 템플릿 생성기
# =====================

class ResumeTemplateGenerator:
    """자소서 템플릿 생성"""

    def __init__(self):
        self.keyword_recommender = KeywordRecommender()

    def generate_template(
        self,
        airline: str,
        item_type: ResumeItemType,
        char_limit: int = 500
    ) -> ResumeTemplate:
        """항공사+항목별 맞춤 템플릿 생성"""

        airline_data = AIRLINE_CHARACTERISTICS.get(airline, {})
        item_structure = ITEM_TEMPLATE_STRUCTURES.get(item_type, {})

        # 섹션 생성
        sections = []
        for section_data in item_structure.get("sections", []):
            char_ratio = section_data.get("char_ratio", 0.25)
            section_limit = (int(char_limit * char_ratio * 0.8), int(char_limit * char_ratio * 1.2))

            sections.append(TemplateSection(
                title=section_data["title"],
                description=section_data["description"],
                example=self._generate_section_example(
                    airline, item_type, section_data["title"]
                ),
                char_limit=section_limit,
                keywords_to_include=self._get_section_keywords(
                    airline, item_type, section_data["title"]
                ),
                tips=self._get_section_tips(section_data["title"]),
            ))

        # 전체 예시 아웃라인
        example_outline = self._generate_outline_example(airline, item_type)

        return ResumeTemplate(
            airline=airline,
            item_type=item_type,
            total_char_limit=item_structure.get("ideal_length", (400, 500)),
            sections=sections,
            airline_keywords=airline_data.get("talent_keywords", []),
            must_include=airline_data.get("emphasis", []),
            avoid=airline_data.get("avoid", []),
            example_outline=example_outline,
        )

    def _generate_section_example(
        self,
        airline: str,
        item_type: ResumeItemType,
        section_title: str
    ) -> str:
        """섹션별 예시 문장 생성"""

        examples = {
            "도입 (훅)": {
                "대한항공": "인천공항에서 대한항공 승무원의 품격 있는 서비스를 경험하며...",
                "진에어": "진에어의 FUN한 기내 분위기를 처음 접했을 때...",
                "default": "항공 서비스를 직접 경험하며 느꼈던 감동의 순간...",
            },
            "항공사 연구": {
                "대한항공": "스카이팀 창립 멤버로서 글로벌 네트워크와 Excellence in Flight 철학...",
                "아시아나항공": "'아름다운 사람들'이라는 슬로건처럼 진정성 있는 서비스...",
                "default": "해당 항공사의 핵심 가치와 서비스 철학...",
            },
            "가치관 연결": {
                "default": "저의 [경험/가치관]과 항공사의 [가치]가 만나는 지점에서...",
            },
            "포부": {
                "default": "입사 후 [구체적 역할]에서 [구체적 기여]를 하고 싶습니다...",
            },
            "장점 제시": {
                "default": "저의 가장 큰 강점은 [구체적 장점]입니다...",
            },
            "장점 증명 에피소드": {
                "default": "[언제, 어디서] [어떤 상황]에서 이 강점을 발휘하여...",
            },
            "단점 인정": {
                "default": "반면, 저는 [솔직한 단점]한 부분이 있었습니다...",
            },
            "극복 노력 & 결과": {
                "default": "이를 개선하기 위해 [구체적 노력]을 했고, 그 결과...",
            },
        }

        section_examples = examples.get(section_title, {})
        return section_examples.get(airline, section_examples.get("default", ""))

    def _get_section_keywords(
        self,
        airline: str,
        item_type: ResumeItemType,
        section_title: str
    ) -> List[str]:
        """섹션별 추천 키워드"""

        airline_data = AIRLINE_CHARACTERISTICS.get(airline, {})

        section_keywords = {
            "도입 (훅)": ["계기", "인상", "경험"],
            "항공사 연구": airline_data.get("core_values", [])[:2],
            "가치관 연결": ["가치관", "경험", "연결"],
            "포부": ["기여", "성장", "목표"],
            "장점 제시": ["강점", "역량"],
            "장점 증명 에피소드": ["상황", "행동", "결과"],
            "단점 인정": ["솔직", "인정"],
            "극복 노력 & 결과": ["노력", "개선", "성장"],
            "상황 (Situation)": ["언제", "어디서", "상황"],
            "과제 (Task)": ["과제", "목표", "필요"],
            "행동 (Action)": ["직접", "행동", "대응"],
            "결과 & 교훈 (Result)": ["결과", "배움", "성장"],
        }

        return section_keywords.get(section_title, [])

    def _get_section_tips(self, section_title: str) -> List[str]:
        """섹션별 작성 팁"""

        tips = {
            "도입 (훅)": ["첫 문장에 시선을 끄는 장면 배치", "진부한 시작 피하기"],
            "항공사 연구": ["해당 항공사만의 특성 필수 언급", "단순 나열 아닌 이해 표현"],
            "가치관 연결": ["경험과 항공사 가치의 교집합 찾기"],
            "포부": ["추상적 목표 피하고 구체적으로"],
            "장점 증명 에피소드": ["STAR 구조 활용", "수치화된 결과 포함"],
            "단점 인정": ["치명적 단점 피하기", "너무 가벼운 것도 피하기"],
            "극복 노력 & 결과": ["구체적 행동 중심", "변화를 보여주기"],
        }

        return tips.get(section_title, [])

    def _generate_outline_example(
        self,
        airline: str,
        item_type: ResumeItemType
    ) -> str:
        """전체 아웃라인 예시"""

        airline_data = AIRLINE_CHARACTERISTICS.get(airline, {})
        core_value = airline_data.get("core_values", ["서비스"])[0]

        outlines = {
            ResumeItemType.MOTIVATION: f"""
[도입] 처음 {airline} 항공기를 탑승했을 때의 경험으로 시작
[연구] {airline}의 '{core_value}' 철학과 차별화된 서비스 언급
[연결] 나의 서비스 경험/가치관이 어떻게 {airline}과 맞닿아 있는지
[포부] {airline}에서 어떤 승무원이 되고 싶은지 구체적으로
""",
            ResumeItemType.PERSONALITY: """
[장점] 나의 핵심 강점 1가지 명확하게 제시
[증명] STAR 구조로 강점을 보여주는 경험 서술
[단점] 솔직하게 인정하되 극복 가능한 것으로
[극복] 개선을 위한 노력과 실제 변화 보여주기
""",
            ResumeItemType.SERVICE: """
[상황] 언제, 어디서, 어떤 고객 상황이었는지
[과제] 해결해야 할 문제/니즈가 무엇이었는지
[행동] 내가 직접 취한 행동들 (가장 구체적으로)
[결과] 결과 + 고객 반응 + 배운 점
""",
        }

        return outlines.get(item_type, "[섹션별 내용을 순서대로 작성]")


# =====================
# 편의 함수
# =====================

def get_resume_template(airline: str, item_type: str) -> Dict:
    """자소서 템플릿 가져오기 (간편 함수)"""
    generator = ResumeTemplateGenerator()

    # 문자열을 Enum으로 변환
    item_enum = None
    for it in ResumeItemType:
        if it.value == item_type or item_type in it.value:
            item_enum = it
            break

    if not item_enum:
        item_enum = ResumeItemType.MOTIVATION

    template = generator.generate_template(airline, item_enum)

    return {
        "airline": template.airline,
        "item_type": template.item_type.value,
        "char_limit": template.total_char_limit,
        "sections": [
            {
                "title": s.title,
                "description": s.description,
                "example": s.example,
                "char_limit": s.char_limit,
                "keywords": s.keywords_to_include,
                "tips": s.tips,
            }
            for s in template.sections
        ],
        "airline_keywords": template.airline_keywords,
        "must_include": template.must_include,
        "avoid": template.avoid,
        "outline": template.example_outline,
    }


def get_keyword_recommendations(airline: str, item_type: str) -> Dict:
    """키워드 추천 (간편 함수)"""
    recommender = KeywordRecommender()

    item_enum = None
    for it in ResumeItemType:
        if it.value == item_type or item_type in it.value:
            item_enum = it
            break

    if not item_enum:
        item_enum = ResumeItemType.MOTIVATION

    return recommender.get_recommended_keywords(airline, item_enum)


def check_keyword_usage(text: str, airline: str, item_type: str) -> Dict:
    """키워드 사용 체크 (간편 함수)"""
    recommender = KeywordRecommender()

    item_enum = None
    for it in ResumeItemType:
        if it.value == item_type or item_type in it.value:
            item_enum = it
            break

    if not item_enum:
        item_enum = ResumeItemType.MOTIVATION

    return recommender.check_keyword_usage(text, airline, item_enum)


def get_airline_characteristics(airline: str) -> Dict:
    """항공사 특성 가져오기 (간편 함수)"""
    return AIRLINE_CHARACTERISTICS.get(airline, {})


def get_all_airlines() -> List[str]:
    """지원 항공사 목록 (간편 함수)"""
    return list(AIRLINE_CHARACTERISTICS.keys())


def get_all_item_types() -> List[str]:
    """지원 항목 유형 목록 (간편 함수)"""
    return [it.value for it in ResumeItemType]
