# resume_enhancer.py
# Phase C1: 자소서 첨삭 고도화 모듈
# FlyReady Lab Enhancement

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re


class StorytellingElement(Enum):
    """스토리텔링 구성 요소"""
    HOOK = "hook"               # 도입부 훅
    CONFLICT = "conflict"       # 갈등/문제 상황
    ACTION = "action"           # 행동/대응
    RESOLUTION = "resolution"   # 해결/결과
    LESSON = "lesson"           # 깨달음/교훈
    CONNECTION = "connection"   # 직무 연결


@dataclass
class SentenceAnalysis:
    """문장별 분석 결과"""
    sentence: str
    index: int
    length: int
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    score: int = 0
    has_concrete_example: bool = False
    has_quantifiable_data: bool = False
    storytelling_role: Optional[StorytellingElement] = None


@dataclass
class KeywordDensityResult:
    """키워드 밀도 분석 결과"""
    keyword: str
    count: int
    density: float  # 키워드 등장 비율 (백분율)
    positions: List[int]  # 등장 위치 (문장 인덱스)
    distribution_score: int  # 분포 균형 점수 (0-100)
    is_overused: bool
    is_underused: bool


@dataclass
class StorytellingScore:
    """스토리텔링 점수 결과"""
    total_score: int
    element_scores: Dict[StorytellingElement, int]
    present_elements: List[StorytellingElement]
    missing_elements: List[StorytellingElement]
    flow_score: int  # 흐름 점수
    engagement_score: int  # 몰입도 점수
    feedback: List[str]


# =====================
# 항공사별 키워드 데이터 (확장)
# =====================

AIRLINE_KEYWORD_DATA = {
    "대한항공": {
        "core_values": ["Excellence in Flight", "안전", "세계적 수준", "프리미엄 서비스"],
        "talent_keywords": ["도전", "글로벌", "전문성", "소통", "신뢰"],
        "recommended_keywords": ["글로벌 역량", "도전 정신", "전문성 개발", "팀워크", "안전 의식", "문화 이해", "소통 능력"],
        "interview_focus": ["글로벌 경험", "외국어 능력", "서비스 마인드", "위기 대처"],
        "avoid_keywords": ["LCC", "저가", "단순히"],
        "bonus_keywords": ["스카이팀", "플래그캐리어", "국위 선양", "명품 서비스"],
    },
    "아시아나항공": {
        "core_values": ["아름다운 사람들", "최상의 서비스", "안전 최우선"],
        "talent_keywords": ["창의", "열정", "신뢰", "도전", "글로벌"],
        "recommended_keywords": ["고객 감동", "세심한 배려", "열정", "안전 문화", "팀 협업", "서비스 정신", "변화 적응"],
        "interview_focus": ["서비스 경험", "팀워크", "위기 관리", "고객 응대"],
        "avoid_keywords": ["합병", "인수", "불안정"],
        "bonus_keywords": ["스타얼라이언스", "아름다운 서비스", "고객 감동"],
    },
    "진에어": {
        "core_values": ["즐거운 여행", "합리적 가격", "트렌디"],
        "talent_keywords": ["Fun", "젊음", "도전", "소통", "창의"],
        "recommended_keywords": ["즐거움", "트렌드 감각", "유연한 사고", "밝은 에너지", "고객 친화", "도전", "창의적 서비스"],
        "interview_focus": ["밝은 성격", "트렌드 이해", "유연성", "고객 친화"],
        "avoid_keywords": ["무거운", "형식적"],
        "bonus_keywords": ["JIN AIR", "Fun한", "젊은 항공사"],
    },
    "제주항공": {
        "core_values": ["가성비", "안전", "고객 만족", "LCC 선두"],
        "talent_keywords": ["열정", "혁신", "동반성장", "고객중심"],
        "recommended_keywords": ["고객 중심", "효율", "열정", "혁신", "동반 성장", "긍정", "실행력"],
        "interview_focus": ["효율성", "멀티태스킹", "긍정적 태도", "팀워크"],
        "avoid_keywords": ["비싼", "고급"],
        "bonus_keywords": ["국내 1위 LCC", "동반성장", "제주 사랑"],
    },
    "티웨이항공": {
        "core_values": ["합리적 여행", "따뜻한 서비스", "안전"],
        "talent_keywords": ["소통", "도전", "전문성", "즐거움"],
        "recommended_keywords": ["따뜻한 서비스", "소통", "도전 의식", "성장", "고객 배려", "긍정 에너지", "전문성"],
        "interview_focus": ["따뜻함", "소통 능력", "서비스 마인드", "성장 의지"],
        "avoid_keywords": ["차가운", "기계적"],
        "bonus_keywords": ["따뜻한 동행", "티웨이 가족"],
    },
    "에어부산": {
        "core_values": ["부산 대표", "친근한 서비스", "안전 운항"],
        "talent_keywords": ["안전", "고객", "혁신", "소통"],
        "recommended_keywords": ["친근함", "지역 사랑", "안전", "소통", "고객 감동", "혁신", "팀워크"],
        "interview_focus": ["부산/지역 애정", "친근함", "안전 의식", "팀워크"],
        "avoid_keywords": [],
        "bonus_keywords": ["부산 사랑", "아시아나 계열", "지역 항공사"],
    },
    "에어서울": {
        "core_values": ["도심 연결", "편안한 여행"],
        "talent_keywords": ["서비스", "안전", "도전", "협력"],
        "recommended_keywords": ["편안한 서비스", "협력", "안전 의식", "도전", "성실", "고객 만족", "글로벌"],
        "interview_focus": ["안정감", "협력", "서비스 마인드"],
        "avoid_keywords": [],
        "bonus_keywords": ["아시아나 계열", "김포 기반"],
    },
    "이스타항공": {
        "core_values": ["새로운 시작", "안전", "고객 행복"],
        "talent_keywords": ["열정", "도전", "성장", "팀워크"],
        "recommended_keywords": ["열정", "새로운 도전", "성장", "팀워크", "긍정", "고객 행복", "적응력"],
        "interview_focus": ["열정", "적응력", "긍정적 태도", "성장 의지"],
        "avoid_keywords": ["불안", "위기"],
        "bonus_keywords": ["재도약", "새출발", "이스타 가족"],
    },
    "에어프레미아": {
        "core_values": ["하이브리드 항공", "합리적 프리미엄", "장거리 LCC"],
        "talent_keywords": ["프리미엄", "도전", "혁신", "전문성"],
        "recommended_keywords": ["프리미엄 마인드", "혁신", "도전", "전문성", "글로벌", "체력", "서비스 차별화"],
        "interview_focus": ["장거리 적응", "체력", "프리미엄 서비스", "혁신"],
        "avoid_keywords": ["저가만"],
        "bonus_keywords": ["하이브리드", "프리미엄 LCC", "장거리 전문"],
    },
    "에어로케이": {
        "core_values": ["안전 운항", "고객 중심"],
        "talent_keywords": ["안전", "고객", "소통", "성장"],
        "recommended_keywords": ["안전", "고객 중심", "소통", "성장", "열정", "책임감", "팀워크"],
        "interview_focus": ["안전 의식", "책임감", "성장 의지"],
        "avoid_keywords": [],
        "bonus_keywords": ["청주 기반", "신생 항공사"],
    },
    "플라이강원": {
        "core_values": ["강원 연결", "지역 발전"],
        "talent_keywords": ["도전", "열정", "지역 사랑"],
        "recommended_keywords": ["도전", "열정", "지역 애정", "서비스 마인드", "성장"],
        "interview_focus": ["지역 애정", "도전 정신", "적응력"],
        "avoid_keywords": [],
        "bonus_keywords": ["강원 사랑", "양양 기반"],
    },
}


# =====================
# 자소서 항목별 평가 기준
# =====================

RESUME_ITEM_CRITERIA = {
    "지원동기": {
        "required_elements": ["항공사 특징", "본인 가치관", "구체적 계기"],
        "bonus_elements": ["회사 비전 연결", "직무 이해도"],
        "common_issues": ["너무 일반적", "항공사 특성 미반영", "~이 꿈이었습니다 클리셰"],
        "ideal_structure": ["훅(관심 계기)", "항공사 연구", "가치관 연결", "포부"],
    },
    "성격의 장단점": {
        "required_elements": ["장점 에피소드", "단점 인정", "극복 노력"],
        "bonus_elements": ["성장 과정", "직무 연결"],
        "common_issues": ["추상적 표현", "단점 회피", "극복 노력 미흡"],
        "ideal_structure": ["장점 제시", "증명 에피소드", "단점 인정", "개선 노력", "결과"],
    },
    "서비스 경험": {
        "required_elements": ["상황 설명", "본인 행동", "결과"],
        "bonus_elements": ["어려운 고객", "STAR 구조", "배운 점"],
        "common_issues": ["구체적 행동 부족", "결과 미흡", "배운 점 없음"],
        "ideal_structure": ["상황(S)", "과제(T)", "행동(A)", "결과(R)", "교훈"],
    },
    "팀워크/협업": {
        "required_elements": ["팀 상황", "본인 역할", "기여"],
        "bonus_elements": ["갈등 해결", "리더십/팔로워십"],
        "common_issues": ["역할 불명확", "팀 성과만 강조", "본인 기여 미흡"],
        "ideal_structure": ["팀 상황", "문제/갈등", "본인 역할", "해결 과정", "결과"],
    },
    "입사 후 포부": {
        "required_elements": ["구체적 목표", "실현 방안"],
        "bonus_elements": ["단기/장기 구분", "회사 비전 연결"],
        "common_issues": ["추상적 목표", "실현 방안 부재", "~최고가 되겠습니다"],
        "ideal_structure": ["단기 목표", "실행 방법", "장기 비전", "회사 기여"],
    },
}


# =====================
# 문장 분석기
# =====================

class SentenceAnalyzer:
    """문장별 상세 분석"""

    # 추상적 표현 패턴
    ABSTRACT_PATTERNS = [
        (r'열심히', '구체적인 행동이나 수치로 대체'),
        (r'최선을', '어떤 방식으로 최선을 다했는지 구체화'),
        (r'많은', '구체적인 수치나 빈도로 대체'),
        (r'다양한', '실제 종류나 예시를 나열'),
        (r'노력했', '어떤 노력을 했는지 구체적으로'),
        (r'잘\s*(했|할|하)', '구체적인 성과나 방법으로'),
        (r'좋은\s*(경험|결과)', '어떤 점이 좋았는지 구체화'),
    ]

    # 진부한 표현 패턴
    CLICHE_PATTERNS = [
        (r'어릴\s*때부터\s*(꿈|승무원)', '더 최근의 구체적 계기로 대체'),
        (r'비행기를?\s*(좋아|타면서)', '직무에 대한 이해로 대체'),
        (r'최고의\s*승무원', '구체적인 목표로 대체'),
        (r'열심히\s*하겠습니다', '구체적인 실행 계획으로'),
        (r'고객님께\s*최상의', '구체적인 서비스 방식으로'),
        (r'밝은\s*미소', '서비스 상황에서의 구체적 행동으로'),
    ]

    # 수치/구체성 패턴
    CONCRETE_PATTERNS = [
        r'\d+년',
        r'\d+개월',
        r'\d+명',
        r'\d+%',
        r'\d+등',
        r'\d+위',
        r'\d+회',
        r'\d+시간',
    ]

    # 스토리텔링 역할 패턴
    STORYTELLING_PATTERNS = {
        StorytellingElement.HOOK: [
            r'^.{0,30}(처음|시작|계기)',
            r'^.{0,30}(언제|어느 날)',
        ],
        StorytellingElement.CONFLICT: [
            r'(어려|힘들|고민|갈등|문제|위기)',
            r'(실수|실패|좌절)',
        ],
        StorytellingElement.ACTION: [
            r'(노력|시도|행동|대응|해결)',
            r'(먼저|직접|적극적으로)',
        ],
        StorytellingElement.RESOLUTION: [
            r'(결과|성과|달성|해결)',
            r'(개선|향상|성공)',
        ],
        StorytellingElement.LESSON: [
            r'(깨달|배우|알게)',
            r'(교훈|성장|변화)',
        ],
        StorytellingElement.CONNECTION: [
            r'(승무원|항공사|서비스)',
            r'(직무|역량|기여)',
        ],
    }

    def analyze_sentence(self, sentence: str, index: int) -> SentenceAnalysis:
        """단일 문장 분석"""
        result = SentenceAnalysis(
            sentence=sentence,
            index=index,
            length=len(sentence),
        )

        # 길이 체크
        if len(sentence) < 15:
            result.issues.append("문장이 너무 짧습니다")
            result.suggestions.append("앞뒤 문장과 연결하거나 내용을 추가하세요")
        elif len(sentence) > 100:
            result.issues.append("문장이 너무 깁니다")
            result.suggestions.append("두 문장으로 나누어 가독성을 높이세요")

        # 추상적 표현 체크
        for pattern, suggestion in self.ABSTRACT_PATTERNS:
            if re.search(pattern, sentence):
                result.issues.append(f"추상적 표현: '{pattern.replace(chr(92), '')}'")
                result.suggestions.append(suggestion)

        # 진부한 표현 체크
        for pattern, suggestion in self.CLICHE_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                result.issues.append("진부한 표현 감지")
                result.suggestions.append(suggestion)

        # 구체성 체크
        for pattern in self.CONCRETE_PATTERNS:
            if re.search(pattern, sentence):
                result.has_quantifiable_data = True
                break

        # 구체적 예시 체크
        if re.search(r'(예를 들어|실제로|구체적으로|~할 때)', sentence):
            result.has_concrete_example = True

        # 스토리텔링 역할 판단
        for element, patterns in self.STORYTELLING_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    result.storytelling_role = element
                    break
            if result.storytelling_role:
                break

        # 점수 계산
        result.score = self._calculate_sentence_score(result)

        return result

    def _calculate_sentence_score(self, analysis: SentenceAnalysis) -> int:
        """문장 점수 계산"""
        score = 70  # 기본 점수

        # 감점 요소
        score -= len(analysis.issues) * 10

        # 가점 요소
        if analysis.has_concrete_example:
            score += 10
        if analysis.has_quantifiable_data:
            score += 10
        if analysis.storytelling_role:
            score += 5

        # 길이 적절성
        if 30 <= analysis.length <= 80:
            score += 5

        return max(0, min(100, score))

    def analyze_all_sentences(self, text: str) -> List[SentenceAnalysis]:
        """전체 텍스트의 문장별 분석"""
        sentences = self._split_sentences(text)
        return [self.analyze_sentence(s, i) for i, s in enumerate(sentences)]

    def _split_sentences(self, text: str) -> List[str]:
        """문장 분리"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


# =====================
# 키워드 밀도 분석기
# =====================

class KeywordDensityAnalyzer:
    """키워드 밀도 및 분포 분석"""

    def analyze_keyword_density(
        self,
        text: str,
        keywords: List[str],
        text_length: int = None
    ) -> List[KeywordDensityResult]:
        """키워드별 밀도 분석"""
        if text_length is None:
            text_length = len(text.replace(" ", ""))

        sentences = re.split(r'(?<=[.!?])\s+', text)
        results = []

        for keyword in keywords:
            count = len(re.findall(re.escape(keyword), text, re.IGNORECASE))
            density = (count * len(keyword) / text_length * 100) if text_length > 0 else 0

            # 등장 위치 찾기
            positions = []
            for i, sentence in enumerate(sentences):
                if keyword in sentence:
                    positions.append(i)

            # 분포 점수 계산
            distribution_score = self._calculate_distribution_score(positions, len(sentences))

            # 과다/과소 사용 판단
            is_overused = count > 3 or density > 3.0
            is_underused = count == 0

            results.append(KeywordDensityResult(
                keyword=keyword,
                count=count,
                density=round(density, 2),
                positions=positions,
                distribution_score=distribution_score,
                is_overused=is_overused,
                is_underused=is_underused,
            ))

        return results

    def _calculate_distribution_score(self, positions: List[int], total_sentences: int) -> int:
        """키워드 분포 균형 점수 (0-100)"""
        if not positions or total_sentences == 0:
            return 0

        if len(positions) == 1:
            return 50  # 한 번만 등장하면 중간 점수

        # 등장 위치의 균등 분포 계산
        ideal_gap = total_sentences / (len(positions) + 1)
        actual_gaps = []
        for i in range(1, len(positions)):
            actual_gaps.append(positions[i] - positions[i - 1])

        if not actual_gaps:
            return 50

        # 분산 계산
        avg_gap = sum(actual_gaps) / len(actual_gaps)
        variance = sum((g - ideal_gap) ** 2 for g in actual_gaps) / len(actual_gaps)

        # 점수 변환 (분산이 작을수록 높은 점수)
        max_variance = (total_sentences / 2) ** 2
        score = 100 - int((variance / max_variance) * 100) if max_variance > 0 else 50

        return max(0, min(100, score))

    def get_keyword_recommendations(
        self,
        text: str,
        airline: str
    ) -> Dict[str, List[str]]:
        """항공사별 키워드 추천"""
        airline_data = AIRLINE_KEYWORD_DATA.get(airline, {})
        recommended = airline_data.get("recommended_keywords", [])
        bonus = airline_data.get("bonus_keywords", [])
        avoid = airline_data.get("avoid_keywords", [])

        # 현재 포함된 키워드 분류
        included = [kw for kw in recommended if kw in text]
        missing = [kw for kw in recommended if kw not in text]
        included_bonus = [kw for kw in bonus if kw in text]
        used_avoid = [kw for kw in avoid if kw in text]

        return {
            "included": included,
            "missing": missing,
            "bonus_included": included_bonus,
            "should_avoid": used_avoid,
        }


# =====================
# 스토리텔링 분석기
# =====================

class StorytellingAnalyzer:
    """스토리텔링 구조 분석"""

    def analyze_storytelling(self, text: str) -> StorytellingScore:
        """스토리텔링 점수 분석"""
        sentence_analyzer = SentenceAnalyzer()
        sentences = sentence_analyzer.analyze_all_sentences(text)

        # 요소별 점수 초기화
        element_scores = {e: 0 for e in StorytellingElement}
        present_elements = []

        # 각 문장의 스토리텔링 역할 분석
        element_sentences = {e: [] for e in StorytellingElement}
        for analysis in sentences:
            if analysis.storytelling_role:
                element_sentences[analysis.storytelling_role].append(analysis)

        # 요소별 점수 계산
        for element, element_sents in element_sentences.items():
            if element_sents:
                present_elements.append(element)
                # 해당 요소의 문장들 평균 점수
                avg_score = sum(s.score for s in element_sents) / len(element_sents)
                element_scores[element] = int(avg_score)

        missing_elements = [e for e in StorytellingElement if e not in present_elements]

        # 흐름 점수 (요소들의 순서 적절성)
        flow_score = self._calculate_flow_score(sentences)

        # 몰입도 점수
        engagement_score = self._calculate_engagement_score(sentences, text)

        # 종합 점수
        total_score = self._calculate_total_storytelling_score(
            element_scores, flow_score, engagement_score, len(present_elements)
        )

        # 피드백 생성
        feedback = self._generate_feedback(
            present_elements, missing_elements, flow_score, engagement_score
        )

        return StorytellingScore(
            total_score=total_score,
            element_scores=element_scores,
            present_elements=present_elements,
            missing_elements=missing_elements,
            flow_score=flow_score,
            engagement_score=engagement_score,
            feedback=feedback,
        )

    def _calculate_flow_score(self, sentences: List[SentenceAnalysis]) -> int:
        """스토리 흐름 점수"""
        # 이상적인 순서: HOOK -> CONFLICT -> ACTION -> RESOLUTION -> LESSON -> CONNECTION
        ideal_order = [
            StorytellingElement.HOOK,
            StorytellingElement.CONFLICT,
            StorytellingElement.ACTION,
            StorytellingElement.RESOLUTION,
            StorytellingElement.LESSON,
            StorytellingElement.CONNECTION,
        ]

        # 실제 등장 순서 추출
        actual_order = []
        for s in sentences:
            if s.storytelling_role and s.storytelling_role not in actual_order:
                actual_order.append(s.storytelling_role)

        if len(actual_order) < 2:
            return 50  # 요소가 너무 적으면 중간 점수

        # 순서 일치도 계산
        score = 100
        for i, element in enumerate(actual_order):
            if element in ideal_order:
                ideal_idx = ideal_order.index(element)
                # 이상적 순서와의 차이에 따라 감점
                if i > 0 and actual_order[i - 1] in ideal_order:
                    prev_ideal_idx = ideal_order.index(actual_order[i - 1])
                    if ideal_idx < prev_ideal_idx:  # 순서 역전
                        score -= 15

        return max(0, min(100, score))

    def _calculate_engagement_score(
        self,
        sentences: List[SentenceAnalysis],
        text: str
    ) -> int:
        """몰입도 점수"""
        score = 50  # 기본 점수

        # 구체적 예시/수치 사용
        concrete_count = sum(1 for s in sentences if s.has_concrete_example or s.has_quantifiable_data)
        score += min(20, concrete_count * 5)

        # 감정/감각 표현
        emotion_patterns = [r'(느끼|감동|기쁘|슬프|긴장|설레)', r'(보이|들리|만지)']
        for pattern in emotion_patterns:
            if re.search(pattern, text):
                score += 5

        # 대화체/인용
        if re.search(r'["\'].*["\']', text) or re.search(r'~라고', text):
            score += 10

        # 문장 다양성 (길이)
        lengths = [s.length for s in sentences]
        if lengths:
            length_variance = sum((l - sum(lengths) / len(lengths)) ** 2 for l in lengths) / len(lengths)
            if length_variance > 200:  # 문장 길이 다양
                score += 10

        return max(0, min(100, score))

    def _calculate_total_storytelling_score(
        self,
        element_scores: Dict[StorytellingElement, int],
        flow_score: int,
        engagement_score: int,
        present_count: int
    ) -> int:
        """종합 스토리텔링 점수"""
        # 요소 점수 평균
        active_scores = [s for s in element_scores.values() if s > 0]
        element_avg = sum(active_scores) / len(active_scores) if active_scores else 0

        # 요소 개수 보너스 (최소 3개 권장)
        count_bonus = min(20, present_count * 5)

        # 종합 계산
        total = int(element_avg * 0.4 + flow_score * 0.25 + engagement_score * 0.25 + count_bonus)

        return max(0, min(100, total))

    def _generate_feedback(
        self,
        present: List[StorytellingElement],
        missing: List[StorytellingElement],
        flow: int,
        engagement: int
    ) -> List[str]:
        """스토리텔링 피드백 생성"""
        feedback = []

        # 누락된 요소 피드백
        element_tips = {
            StorytellingElement.HOOK: "도입부에 관심을 끄는 장면이나 질문으로 시작해보세요",
            StorytellingElement.CONFLICT: "어려움이나 고민했던 상황을 추가하면 깊이가 생깁니다",
            StorytellingElement.ACTION: "본인이 직접 취한 행동을 구체적으로 서술하세요",
            StorytellingElement.RESOLUTION: "행동의 결과나 변화를 명확히 보여주세요",
            StorytellingElement.LESSON: "경험에서 얻은 깨달음이나 성장을 언급하세요",
            StorytellingElement.CONNECTION: "경험을 승무원 직무와 연결지어 마무리하세요",
        }

        for element in missing[:3]:  # 최대 3개까지 피드백
            feedback.append(element_tips.get(element, ""))

        # 흐름 피드백
        if flow < 60:
            feedback.append("스토리의 흐름이 자연스럽지 않습니다. 시간 순서나 논리적 순서로 재배열해보세요.")

        # 몰입도 피드백
        if engagement < 60:
            feedback.append("구체적인 예시, 대화, 감정 표현을 추가하면 더 생생해집니다.")

        return feedback


# =====================
# 합격 자소서 비교 분석기
# =====================

class PassedResumeComparator:
    """합격 자소서와 비교 분석"""

    # 합격 자소서 특성 (항목별)
    PASSED_RESUME_FEATURES = {
        "지원동기": {
            "avg_length": (350, 500),
            "keyword_density": (3, 6),  # 핵심 키워드 개수
            "structure_elements": ["계기", "연구", "가치관", "포부"],
            "storytelling_score": 70,
        },
        "성격의 장단점": {
            "avg_length": (400, 550),
            "keyword_density": (2, 4),
            "structure_elements": ["장점", "에피소드", "단점", "극복"],
            "storytelling_score": 75,
        },
        "서비스 경험": {
            "avg_length": (450, 600),
            "keyword_density": (3, 5),
            "structure_elements": ["상황", "과제", "행동", "결과"],
            "storytelling_score": 80,
        },
        "팀워크/협업": {
            "avg_length": (400, 600),
            "keyword_density": (2, 4),
            "structure_elements": ["상황", "역할", "기여", "결과"],
            "storytelling_score": 75,
        },
        "입사 후 포부": {
            "avg_length": (300, 450),
            "keyword_density": (3, 5),
            "structure_elements": ["단기목표", "실행방안", "장기비전"],
            "storytelling_score": 65,
        },
    }

    def compare_with_passed(
        self,
        text: str,
        item_type: str,
        airline: str
    ) -> Dict:
        """합격 자소서와 비교"""
        features = self.PASSED_RESUME_FEATURES.get(item_type, {})
        if not features:
            return {"error": "지원하지 않는 항목 유형입니다"}

        # 분석 실행
        sentence_analyzer = SentenceAnalyzer()
        keyword_analyzer = KeywordDensityAnalyzer()
        storytelling_analyzer = StorytellingAnalyzer()

        sentences = sentence_analyzer.analyze_all_sentences(text)
        keyword_recs = keyword_analyzer.get_keyword_recommendations(text, airline)
        storytelling = storytelling_analyzer.analyze_storytelling(text)

        # 길이 비교
        current_length = len(text.replace(" ", ""))
        ideal_length = features.get("avg_length", (400, 500))
        length_status = "적절" if ideal_length[0] <= current_length <= ideal_length[1] else \
            "부족" if current_length < ideal_length[0] else "초과"

        # 키워드 비교
        current_keywords = len(keyword_recs.get("included", []))
        ideal_keywords = features.get("keyword_density", (3, 5))
        keyword_status = "적절" if ideal_keywords[0] <= current_keywords <= ideal_keywords[1] else \
            "부족" if current_keywords < ideal_keywords[0] else "많음"

        # 스토리텔링 비교
        ideal_storytelling = features.get("storytelling_score", 70)
        storytelling_gap = storytelling.total_score - ideal_storytelling

        # 종합 점수
        comparison_score = self._calculate_comparison_score(
            length_status, keyword_status, storytelling_gap, storytelling.total_score
        )

        return {
            "comparison_score": comparison_score,
            "length": {
                "current": current_length,
                "ideal_range": ideal_length,
                "status": length_status,
            },
            "keywords": {
                "current_count": current_keywords,
                "ideal_range": ideal_keywords,
                "status": keyword_status,
                "included": keyword_recs.get("included", []),
                "missing": keyword_recs.get("missing", [])[:5],
            },
            "storytelling": {
                "current_score": storytelling.total_score,
                "ideal_score": ideal_storytelling,
                "gap": storytelling_gap,
                "feedback": storytelling.feedback[:3],
            },
            "overall_feedback": self._generate_comparison_feedback(
                length_status, keyword_status, storytelling_gap
            ),
        }

    def _calculate_comparison_score(
        self,
        length_status: str,
        keyword_status: str,
        storytelling_gap: int,
        storytelling_score: int
    ) -> int:
        """합격 자소서 대비 점수"""
        score = 50  # 기본

        # 길이 점수
        if length_status == "적절":
            score += 15
        elif length_status in ["부족", "초과"]:
            score += 5

        # 키워드 점수
        if keyword_status == "적절":
            score += 15
        elif keyword_status in ["부족", "많음"]:
            score += 5

        # 스토리텔링 점수
        if storytelling_gap >= 0:
            score += 20
        elif storytelling_gap >= -10:
            score += 10
        else:
            score += 5

        return max(0, min(100, score))

    def _generate_comparison_feedback(
        self,
        length: str,
        keyword: str,
        story_gap: int
    ) -> List[str]:
        """비교 기반 피드백"""
        feedback = []

        if length == "부족":
            feedback.append("합격 자소서 대비 분량이 부족합니다. 구체적인 예시나 설명을 추가하세요.")
        elif length == "초과":
            feedback.append("합격 자소서 대비 분량이 많습니다. 핵심만 간결하게 정리하세요.")

        if keyword == "부족":
            feedback.append("항공사 핵심 키워드가 부족합니다. 인재상과 가치를 반영하세요.")

        if story_gap < -10:
            feedback.append("스토리텔링 구조가 합격 기준에 미달합니다. 구조를 개선하세요.")

        if not feedback:
            feedback.append("합격 자소서 수준에 근접합니다! 세부 표현을 다듬어보세요.")

        return feedback


# =====================
# 통합 분석기
# =====================

class EnhancedResumeAnalyzer:
    """통합 자소서 분석기"""

    def __init__(self):
        self.sentence_analyzer = SentenceAnalyzer()
        self.keyword_analyzer = KeywordDensityAnalyzer()
        self.storytelling_analyzer = StorytellingAnalyzer()
        self.comparator = PassedResumeComparator()

    def analyze_complete(
        self,
        text: str,
        airline: str,
        item_type: str
    ) -> Dict:
        """종합 분석"""

        # 기본 분석
        sentences = self.sentence_analyzer.analyze_all_sentences(text)
        airline_data = AIRLINE_KEYWORD_DATA.get(airline, {})
        recommended_keywords = airline_data.get("recommended_keywords", [])

        # 키워드 밀도 분석
        keyword_density = self.keyword_analyzer.analyze_keyword_density(text, recommended_keywords)
        keyword_recs = self.keyword_analyzer.get_keyword_recommendations(text, airline)

        # 스토리텔링 분석
        storytelling = self.storytelling_analyzer.analyze_storytelling(text)

        # 합격 자소서 비교
        comparison = self.comparator.compare_with_passed(text, item_type, airline)

        # 문장별 이슈 집계
        sentence_issues = []
        for s in sentences:
            if s.issues:
                sentence_issues.append({
                    "index": s.index,
                    "sentence": s.sentence[:50] + "..." if len(s.sentence) > 50 else s.sentence,
                    "issues": s.issues,
                    "suggestions": s.suggestions,
                })

        # 종합 점수 계산
        avg_sentence_score = sum(s.score for s in sentences) / len(sentences) if sentences else 0
        total_score = int(
            avg_sentence_score * 0.3 +
            storytelling.total_score * 0.35 +
            comparison.get("comparison_score", 50) * 0.35
        )

        # 등급 결정
        grade = self._determine_grade(total_score)

        return {
            "total_score": total_score,
            "grade": grade,
            "sentence_analysis": {
                "avg_score": round(avg_sentence_score, 0),
                "total_sentences": len(sentences),
                "issues_count": len(sentence_issues),
                "issues": sentence_issues[:5],  # 상위 5개
            },
            "keyword_analysis": {
                "density_results": [
                    {
                        "keyword": kd.keyword,
                        "count": kd.count,
                        "density": kd.density,
                        "is_overused": kd.is_overused,
                        "is_underused": kd.is_underused,
                    }
                    for kd in keyword_density[:7]
                ],
                "included": keyword_recs.get("included", []),
                "missing": keyword_recs.get("missing", [])[:5],
                "should_avoid": keyword_recs.get("should_avoid", []),
            },
            "storytelling_analysis": {
                "total_score": storytelling.total_score,
                "flow_score": storytelling.flow_score,
                "engagement_score": storytelling.engagement_score,
                "present_elements": [e.value for e in storytelling.present_elements],
                "missing_elements": [e.value for e in storytelling.missing_elements],
                "feedback": storytelling.feedback,
            },
            "comparison_analysis": comparison,
            "improvement_priorities": self._get_improvement_priorities(
                sentence_issues, keyword_recs, storytelling, comparison
            ),
        }

    def _determine_grade(self, score: int) -> str:
        """등급 결정"""
        if score >= 90:
            return 'S'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

    def _get_improvement_priorities(
        self,
        sentence_issues: List[Dict],
        keyword_recs: Dict,
        storytelling: StorytellingScore,
        comparison: Dict
    ) -> List[str]:
        """개선 우선순위"""
        priorities = []

        # 1. 스토리텔링 이슈
        if storytelling.total_score < 60:
            priorities.append(f"스토리텔링 구조 개선: {storytelling.feedback[0] if storytelling.feedback else '구조를 보완하세요'}")

        # 2. 키워드 이슈
        missing = keyword_recs.get("missing", [])
        if len(missing) >= 3:
            priorities.append(f"핵심 키워드 추가: {', '.join(missing[:3])}")

        # 3. 문장 이슈
        if len(sentence_issues) >= 3:
            priorities.append(f"문장 개선 필요: {sentence_issues[0].get('issues', [''])[0]}")

        # 4. 합격 비교 이슈
        comp_feedback = comparison.get("overall_feedback", [])
        if comp_feedback:
            priorities.append(comp_feedback[0])

        return priorities[:4] if priorities else ["전반적으로 좋습니다! 세부 표현을 다듬어보세요."]


# =====================
# 편의 함수
# =====================

def analyze_resume_enhanced(text: str, airline: str, item_type: str) -> Dict:
    """자소서 고도화 분석 (간편 함수)"""
    analyzer = EnhancedResumeAnalyzer()
    return analyzer.analyze_complete(text, airline, item_type)


def get_sentence_analysis(text: str) -> List[Dict]:
    """문장별 분석 (간편 함수)"""
    analyzer = SentenceAnalyzer()
    results = analyzer.analyze_all_sentences(text)
    return [
        {
            "index": r.index,
            "sentence": r.sentence,
            "score": r.score,
            "issues": r.issues,
            "suggestions": r.suggestions,
            "storytelling_role": r.storytelling_role.value if r.storytelling_role else None,
        }
        for r in results
    ]


def get_keyword_density(text: str, airline: str) -> Dict:
    """키워드 밀도 분석 (간편 함수)"""
    analyzer = KeywordDensityAnalyzer()
    airline_data = AIRLINE_KEYWORD_DATA.get(airline, {})
    keywords = airline_data.get("recommended_keywords", [])

    density = analyzer.analyze_keyword_density(text, keywords)
    recs = analyzer.get_keyword_recommendations(text, airline)

    return {
        "density": [
            {
                "keyword": d.keyword,
                "count": d.count,
                "density": d.density,
                "is_overused": d.is_overused,
                "is_underused": d.is_underused,
            }
            for d in density
        ],
        "recommendations": recs,
    }


def get_storytelling_score(text: str) -> Dict:
    """스토리텔링 점수 (간편 함수)"""
    analyzer = StorytellingAnalyzer()
    result = analyzer.analyze_storytelling(text)

    return {
        "total_score": result.total_score,
        "flow_score": result.flow_score,
        "engagement_score": result.engagement_score,
        "present_elements": [e.value for e in result.present_elements],
        "missing_elements": [e.value for e in result.missing_elements],
        "feedback": result.feedback,
    }


def compare_with_passed_resume(text: str, item_type: str, airline: str) -> Dict:
    """합격 자소서 비교 (간편 함수)"""
    comparator = PassedResumeComparator()
    return comparator.compare_with_passed(text, item_type, airline)
