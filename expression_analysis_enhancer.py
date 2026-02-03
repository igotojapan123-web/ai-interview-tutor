# expression_analysis_enhancer.py
# Phase D4: 표정 분석 고도화 모듈
# FlyReady Lab Enhancement

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math
import random


class SmileLevel(Enum):
    """미소 수준"""
    NONE = "none"
    SLIGHT = "slight"
    MODERATE = "moderate"
    BRIGHT = "bright"
    OVEREXCITED = "overexcited"


class ExpressionType(Enum):
    """표정 유형"""
    NEUTRAL = "neutral"
    SMILE = "smile"
    TENSE = "tense"
    FOCUSED = "focused"
    NERVOUS = "nervous"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"


class EyeContactLevel(Enum):
    """눈 맞춤 수준"""
    AVOIDING = "avoiding"
    INSUFFICIENT = "insufficient"
    MODERATE = "moderate"
    APPROPRIATE = "appropriate"
    INTENSE = "intense"


@dataclass
class TimePoint:
    """시간대별 데이터"""
    timestamp: float
    value: float
    status: str
    label: str = ""


@dataclass
class SmileAnalysis:
    """미소 분석 결과"""
    smile_score: float  # 0-100
    level: SmileLevel
    timeline: List[TimePoint]

    # 미소 구간
    smile_segments: List[Dict[str, Any]]
    no_smile_segments: List[Dict[str, Any]]

    # 미소 통계
    smile_frequency: float  # 미소 빈도 (회/분)
    average_smile_duration: float  # 평균 미소 지속시간 (초)

    # 피드백
    feedback: str
    improvement_tips: List[str]


@dataclass
class EyeContactAnalysis:
    """눈 맞춤 분석 결과"""
    eye_contact_ratio: float  # 0-1
    level: EyeContactLevel
    timeline: List[TimePoint]

    # 눈 맞춤 구간
    good_contact_segments: List[Dict[str, Any]]
    poor_contact_segments: List[Dict[str, Any]]

    # 통계
    avg_contact_duration: float  # 평균 눈맞춤 지속시간
    contact_frequency: float  # 눈맞춤 빈도

    # 피드백
    feedback: str
    improvement_tips: List[str]


@dataclass
class NaturalnessAnalysis:
    """자연스러움 분석 결과"""
    naturalness_score: float  # 0-100
    timeline: List[TimePoint]

    # 자연스러움 요소
    expression_consistency: float  # 표정 일관성
    transition_smoothness: float  # 전환 부드러움
    authenticity_score: float  # 진정성

    # 피드백
    feedback: str
    improvement_tips: List[str]


@dataclass
class EnhancedExpressionAnalysis:
    """종합 표정 분석 결과"""
    smile: SmileAnalysis
    eye_contact: EyeContactAnalysis
    naturalness: NaturalnessAnalysis

    # 종합 점수
    overall_score: int  # 0-100
    grade: str  # S, A, B, C, D

    # 주요 표정
    dominant_expression: ExpressionType
    expression_distribution: Dict[str, float]

    # 시간대별 종합
    expression_timeline: List[TimePoint]

    # 강점/개선점
    strengths: List[str]
    improvements: List[str]

    # 표정 코칭
    coaching_tips: List[Dict[str, Any]]


# =====================
# 분석 기준 상수
# =====================

SMILE_CRITERIA = {
    "none": {"range": (0, 20), "feedback": "미소가 거의 없습니다"},
    "slight": {"range": (20, 45), "feedback": "살짝 미소짓고 있습니다"},
    "moderate": {"range": (45, 70), "feedback": "적당한 미소입니다"},
    "bright": {"range": (70, 90), "feedback": "밝은 미소입니다"},
    "overexcited": {"range": (90, 100), "feedback": "미소가 과할 수 있습니다"},
}

EYE_CONTACT_CRITERIA = {
    "optimal_ratio": (0.5, 0.7),  # 적정 눈맞춤 비율
    "optimal_duration": (3, 7),   # 적정 눈맞춤 지속시간 (초)
}

NATURALNESS_CRITERIA = {
    "consistency_weight": 0.4,
    "smoothness_weight": 0.3,
    "authenticity_weight": 0.3,
}


# =====================
# 미소 분석기
# =====================

class SmileAnalyzer:
    """미소 분석"""

    def analyze(
        self,
        duration: float,
        smile_data: Optional[List[Dict]] = None
    ) -> SmileAnalysis:
        """미소 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(duration, smile_data)

        # 미소 점수 계산
        smile_values = [p.value for p in timeline]
        smile_score = sum(smile_values) / len(smile_values) if smile_values else 50

        # 미소 수준 결정
        level = self._get_smile_level(smile_score)

        # 미소 구간 분석
        smile_segs, no_smile_segs = self._analyze_segments(timeline)

        # 통계 계산
        frequency = len(smile_segs) / (duration / 60) if duration > 0 else 0
        avg_duration = self._calculate_avg_duration(smile_segs)

        # 피드백 생성
        feedback, tips = self._generate_feedback(level, smile_score, frequency)

        return SmileAnalysis(
            smile_score=round(smile_score, 1),
            level=level,
            timeline=timeline,
            smile_segments=smile_segs,
            no_smile_segments=no_smile_segs,
            smile_frequency=round(frequency, 1),
            average_smile_duration=round(avg_duration, 1),
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        smile_data: Optional[List[Dict]]
    ) -> List[TimePoint]:
        """시간대별 미소 타임라인"""
        timeline = []
        num_points = max(5, int(duration / 8))

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            # 시뮬레이션: 적당한 미소
            base_smile = 55 + random.gauss(0, 15)
            base_smile = max(10, min(95, base_smile))

            if base_smile >= 65:
                status = "smiling"
            elif base_smile >= 40:
                status = "slight"
            else:
                status = "neutral"

            timeline.append(TimePoint(
                timestamp=timestamp,
                value=base_smile,
                status=status,
                label=self._get_smile_label(base_smile)
            ))

        return timeline

    def _get_smile_label(self, score: float) -> str:
        """미소 라벨"""
        if score >= 70:
            return "밝은 미소"
        elif score >= 50:
            return "미소"
        elif score >= 30:
            return "살짝 미소"
        else:
            return "무표정"

    def _get_smile_level(self, score: float) -> SmileLevel:
        """미소 수준 결정"""
        for level, info in SMILE_CRITERIA.items():
            min_v, max_v = info["range"]
            if min_v <= score < max_v:
                return SmileLevel(level)
        return SmileLevel.MODERATE

    def _analyze_segments(
        self,
        timeline: List[TimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """미소/무표정 구간 분석"""
        smile = []
        no_smile = []

        for point in timeline:
            if point.status == "smiling":
                smile.append({
                    "timestamp": point.timestamp,
                    "score": point.value,
                    "intensity": "high" if point.value >= 75 else "medium"
                })
            elif point.status == "neutral":
                no_smile.append({
                    "timestamp": point.timestamp,
                    "score": point.value
                })

        return smile, no_smile

    def _calculate_avg_duration(self, segments: List[Dict]) -> float:
        """평균 지속시간 계산"""
        if len(segments) < 2:
            return 2.0
        # 간격으로 추정
        gaps = []
        for i in range(1, len(segments)):
            gap = segments[i]["timestamp"] - segments[i-1]["timestamp"]
            gaps.append(gap)
        return sum(gaps) / len(gaps) if gaps else 2.0

    def _generate_feedback(
        self,
        level: SmileLevel,
        score: float,
        frequency: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if level == SmileLevel.NONE:
            feedback = "표정이 굳어 있습니다. 자연스러운 미소를 지어보세요."
            tips = [
                "답변 시작 전 미소로 시작하세요",
                "거울 앞에서 자연스러운 미소 연습하기",
                "눈으로 미소짓는 연습하기 (눈웃음)",
                "긴장을 풀고 편안한 표정 유지하기",
            ]
        elif level == SmileLevel.SLIGHT:
            feedback = "살짝 미소짓고 있습니다. 조금 더 밝게 웃어도 좋아요."
            tips = [
                "핵심 포인트에서 미소를 더해보세요",
                "자연스럽게 치아가 보이는 미소 연습",
            ]
        elif level == SmileLevel.MODERATE:
            feedback = "적절한 미소입니다. 친근하고 프로페셔널해 보여요."
            tips = ["현재 미소를 유지하세요"]
        elif level == SmileLevel.BRIGHT:
            feedback = "밝은 미소가 인상적입니다! 호감을 줍니다."
            tips = ["너무 과하지 않게 현재 수준 유지"]
        else:  # OVEREXCITED
            feedback = "미소가 조금 과할 수 있습니다. 자연스럽게 조절해보세요."
            tips = [
                "진지한 내용에서는 미소를 줄이세요",
                "상황에 맞는 표정 연습하기",
            ]

        return feedback, tips


# =====================
# 눈 맞춤 분석기
# =====================

class EyeContactAnalyzer:
    """눈 맞춤 분석"""

    def analyze(
        self,
        duration: float,
        eye_data: Optional[List[Dict]] = None
    ) -> EyeContactAnalysis:
        """눈 맞춤 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(duration, eye_data)

        # 눈 맞춤 비율 계산
        contact_values = [1 if p.status in ["good", "appropriate"] else 0 for p in timeline]
        eye_contact_ratio = sum(contact_values) / len(contact_values) if contact_values else 0.5

        # 수준 결정
        level = self._get_contact_level(eye_contact_ratio)

        # 구간 분석
        good_segs, poor_segs = self._analyze_segments(timeline)

        # 통계
        avg_duration = self._calculate_avg_contact_duration(good_segs, duration)
        frequency = len(good_segs) / (duration / 60) if duration > 0 else 0

        # 피드백 생성
        feedback, tips = self._generate_feedback(level, eye_contact_ratio)

        return EyeContactAnalysis(
            eye_contact_ratio=round(eye_contact_ratio, 2),
            level=level,
            timeline=timeline,
            good_contact_segments=good_segs,
            poor_contact_segments=poor_segs,
            avg_contact_duration=round(avg_duration, 1),
            contact_frequency=round(frequency, 1),
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        eye_data: Optional[List[Dict]]
    ) -> List[TimePoint]:
        """시간대별 눈 맞춤 타임라인"""
        timeline = []
        num_points = max(5, int(duration / 6))

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            # 시뮬레이션
            contact = random.random()

            if contact >= 0.7:
                status = "appropriate"
                value = 80 + random.gauss(0, 10)
            elif contact >= 0.4:
                status = "good"
                value = 60 + random.gauss(0, 10)
            elif contact >= 0.2:
                status = "poor"
                value = 40 + random.gauss(0, 10)
            else:
                status = "avoiding"
                value = 20 + random.gauss(0, 10)

            value = max(5, min(100, value))

            timeline.append(TimePoint(
                timestamp=timestamp,
                value=value,
                status=status,
                label=self._get_contact_label(status)
            ))

        return timeline

    def _get_contact_label(self, status: str) -> str:
        """눈 맞춤 라벨"""
        labels = {
            "appropriate": "적절한 눈맞춤",
            "good": "눈맞춤",
            "poor": "부족",
            "avoiding": "회피"
        }
        return labels.get(status, status)

    def _get_contact_level(self, ratio: float) -> EyeContactLevel:
        """눈 맞춤 수준 결정"""
        if ratio < 0.25:
            return EyeContactLevel.AVOIDING
        elif ratio < 0.45:
            return EyeContactLevel.INSUFFICIENT
        elif ratio < 0.6:
            return EyeContactLevel.MODERATE
        elif ratio < 0.8:
            return EyeContactLevel.APPROPRIATE
        else:
            return EyeContactLevel.INTENSE

    def _analyze_segments(
        self,
        timeline: List[TimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """좋은/나쁜 눈맞춤 구간"""
        good = []
        poor = []

        for point in timeline:
            if point.status in ["good", "appropriate"]:
                good.append({
                    "timestamp": point.timestamp,
                    "quality": point.status
                })
            else:
                poor.append({
                    "timestamp": point.timestamp,
                    "issue": point.status
                })

        return good, poor

    def _calculate_avg_contact_duration(
        self,
        segments: List[Dict],
        duration: float
    ) -> float:
        """평균 눈맞춤 지속시간"""
        if not segments:
            return 0
        return duration / len(segments) * 0.6  # 추정치

    def _generate_feedback(
        self,
        level: EyeContactLevel,
        ratio: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if level == EyeContactLevel.AVOIDING:
            feedback = "눈을 자주 피하고 있습니다. 면접관과 눈을 맞춰주세요."
            tips = [
                "면접관의 눈과 코 사이를 부드럽게 바라보세요",
                "3-5초 정도 눈을 맞추고 자연스럽게 시선 이동",
                "거울 보며 눈 맞춤 연습하기",
            ]
        elif level == EyeContactLevel.INSUFFICIENT:
            feedback = "눈 맞춤이 부족합니다. 조금 더 자주 눈을 맞춰보세요."
            tips = [
                "중요한 포인트에서 눈 맞추기",
                "답변 시작과 끝에 눈 맞춤",
            ]
        elif level == EyeContactLevel.MODERATE:
            feedback = "보통 수준의 눈 맞춤입니다. 조금 더 자신감 있게 봐도 좋아요."
            tips = ["눈 맞춤 빈도를 조금 높여보세요"]
        elif level == EyeContactLevel.APPROPRIATE:
            feedback = "적절한 눈 맞춤입니다. 자신감 있어 보여요!"
            tips = ["현재 수준을 유지하세요"]
        else:  # INTENSE
            feedback = "눈 맞춤이 강합니다. 자연스럽게 시선을 분산해보세요."
            tips = [
                "때때로 자연스럽게 시선 이동하기",
                "응시가 부담을 줄 수 있으니 주의",
            ]

        return feedback, tips


# =====================
# 자연스러움 분석기
# =====================

class NaturalnessAnalyzer:
    """자연스러움 분석"""

    def analyze(
        self,
        duration: float,
        expression_data: Optional[List[Dict]] = None
    ) -> NaturalnessAnalysis:
        """자연스러움 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(duration, expression_data)

        # 각 요소 계산
        consistency = self._calculate_consistency(timeline)
        smoothness = self._calculate_smoothness(timeline)
        authenticity = self._calculate_authenticity(timeline)

        # 종합 점수
        naturalness_score = (
            consistency * NATURALNESS_CRITERIA["consistency_weight"] +
            smoothness * NATURALNESS_CRITERIA["smoothness_weight"] +
            authenticity * NATURALNESS_CRITERIA["authenticity_weight"]
        )

        # 피드백 생성
        feedback, tips = self._generate_feedback(naturalness_score, consistency, smoothness)

        return NaturalnessAnalysis(
            naturalness_score=round(naturalness_score, 1),
            timeline=timeline,
            expression_consistency=round(consistency, 1),
            transition_smoothness=round(smoothness, 1),
            authenticity_score=round(authenticity, 1),
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        expression_data: Optional[List[Dict]]
    ) -> List[TimePoint]:
        """시간대별 자연스러움 타임라인"""
        timeline = []
        num_points = max(5, int(duration / 10))

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            naturalness = 65 + random.gauss(5, 12)
            naturalness = max(30, min(95, naturalness))

            if naturalness >= 80:
                status = "very_natural"
            elif naturalness >= 60:
                status = "natural"
            elif naturalness >= 45:
                status = "slightly_stiff"
            else:
                status = "stiff"

            timeline.append(TimePoint(
                timestamp=timestamp,
                value=naturalness,
                status=status,
                label=self._get_naturalness_label(status)
            ))

        return timeline

    def _get_naturalness_label(self, status: str) -> str:
        """자연스러움 라벨"""
        labels = {
            "very_natural": "매우 자연스러움",
            "natural": "자연스러움",
            "slightly_stiff": "약간 어색",
            "stiff": "경직"
        }
        return labels.get(status, status)

    def _calculate_consistency(self, timeline: List[TimePoint]) -> float:
        """표정 일관성 계산"""
        if len(timeline) < 2:
            return 70

        values = [p.value for p in timeline]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = math.sqrt(variance)

        # 변화가 작을수록 일관적
        consistency = max(40, min(95, 100 - std * 2))
        return consistency

    def _calculate_smoothness(self, timeline: List[TimePoint]) -> float:
        """전환 부드러움 계산"""
        if len(timeline) < 2:
            return 70

        changes = []
        for i in range(1, len(timeline)):
            change = abs(timeline[i].value - timeline[i-1].value)
            changes.append(change)

        avg_change = sum(changes) / len(changes)

        # 급격한 변화가 적을수록 부드러움
        smoothness = max(40, min(95, 100 - avg_change * 1.5))
        return smoothness

    def _calculate_authenticity(self, timeline: List[TimePoint]) -> float:
        """진정성 점수 계산"""
        # 시뮬레이션: 자연스러운 상태가 많을수록 진정성 높음
        natural_count = sum(1 for p in timeline if p.status in ["natural", "very_natural"])
        ratio = natural_count / len(timeline) if timeline else 0.5
        authenticity = 50 + ratio * 45
        return min(95, authenticity)

    def _generate_feedback(
        self,
        score: float,
        consistency: float,
        smoothness: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if score >= 80:
            feedback = "표정이 매우 자연스럽습니다. 진정성 있어 보여요!"
            tips = ["현재 상태를 유지하세요"]
        elif score >= 65:
            feedback = "자연스러운 표정입니다."
            tips = ["더욱 편안하게 표현해보세요"]
        elif score >= 50:
            feedback = "표정이 약간 어색합니다. 더 편안하게 연습해보세요."
            tips = [
                "거울 보며 자연스러운 표정 연습",
                "긴장을 풀고 편안하게 호흡하기",
            ]
        else:
            feedback = "표정이 경직되어 있습니다. 긴장을 풀어보세요."
            tips = [
                "심호흡으로 긴장 완화하기",
                "일상적인 대화하듯이 편안하게",
                "표정 근육 스트레칭 해보기",
            ]

        if consistency < 60:
            tips.append("일관된 표정 유지 연습하기")
        if smoothness < 60:
            tips.append("급격한 표정 변화 피하기")

        return feedback, tips


# =====================
# 통합 분석기
# =====================

class EnhancedExpressionAnalyzer:
    """통합 표정 분석기"""

    def __init__(self):
        self.smile_analyzer = SmileAnalyzer()
        self.eye_contact_analyzer = EyeContactAnalyzer()
        self.naturalness_analyzer = NaturalnessAnalyzer()

    def analyze_complete(
        self,
        duration: float,
        smile_data: Optional[List[Dict]] = None,
        eye_data: Optional[List[Dict]] = None,
        expression_data: Optional[List[Dict]] = None
    ) -> EnhancedExpressionAnalysis:
        """종합 표정 분석"""

        # 개별 분석
        smile = self.smile_analyzer.analyze(duration, smile_data)
        eye_contact = self.eye_contact_analyzer.analyze(duration, eye_data)
        naturalness = self.naturalness_analyzer.analyze(duration, expression_data)

        # 종합 점수 계산
        overall_score = int(
            smile.smile_score * 0.35 +
            eye_contact.eye_contact_ratio * 100 * 0.35 +
            naturalness.naturalness_score * 0.30
        )

        # 등급 결정
        grade = self._determine_grade(overall_score)

        # 주요 표정 결정
        dominant, distribution = self._analyze_expression_distribution(
            smile, eye_contact, naturalness
        )

        # 종합 타임라인
        expression_timeline = self._create_combined_timeline(
            smile.timeline, eye_contact.timeline, naturalness.timeline
        )

        # 강점/개선점 수집
        strengths, improvements = self._collect_feedback(smile, eye_contact, naturalness)

        # 코칭 팁
        coaching = self._generate_coaching_tips(smile, eye_contact, naturalness)

        return EnhancedExpressionAnalysis(
            smile=smile,
            eye_contact=eye_contact,
            naturalness=naturalness,
            overall_score=overall_score,
            grade=grade,
            dominant_expression=dominant,
            expression_distribution=distribution,
            expression_timeline=expression_timeline,
            strengths=strengths,
            improvements=improvements,
            coaching_tips=coaching,
        )

    def _determine_grade(self, score: int) -> str:
        """등급 결정"""
        if score >= 90:
            return "S"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"

    def _analyze_expression_distribution(
        self,
        smile: SmileAnalysis,
        eye_contact: EyeContactAnalysis,
        naturalness: NaturalnessAnalysis
    ) -> Tuple[ExpressionType, Dict[str, float]]:
        """표정 분포 분석"""
        distribution = {}

        # 미소 기반
        if smile.smile_score >= 65:
            distribution["friendly"] = 35
        elif smile.smile_score >= 40:
            distribution["professional"] = 30

        # 눈맞춤 기반
        if eye_contact.eye_contact_ratio >= 0.6:
            distribution["focused"] = 25
        elif eye_contact.eye_contact_ratio < 0.35:
            distribution["nervous"] = 20

        # 자연스러움 기반
        if naturalness.naturalness_score >= 70:
            distribution["natural"] = 20
        else:
            distribution["tense"] = 15

        # 나머지
        remaining = 100 - sum(distribution.values())
        distribution["neutral"] = remaining

        # 주요 표정 결정
        if smile.smile_score >= 65 and eye_contact.eye_contact_ratio >= 0.5:
            dominant = ExpressionType.FRIENDLY
        elif eye_contact.eye_contact_ratio >= 0.6 and naturalness.naturalness_score >= 65:
            dominant = ExpressionType.PROFESSIONAL
        elif naturalness.naturalness_score < 50:
            dominant = ExpressionType.TENSE
        elif smile.smile_score >= 50:
            dominant = ExpressionType.SMILE
        else:
            dominant = ExpressionType.NEUTRAL

        return dominant, distribution

    def _create_combined_timeline(
        self,
        smile: List[TimePoint],
        eye: List[TimePoint],
        natural: List[TimePoint]
    ) -> List[TimePoint]:
        """종합 타임라인 생성"""
        combined = []
        num = min(len(smile), len(eye), len(natural))

        for i in range(num):
            avg_score = (smile[i].value + eye[i].value + natural[i].value) / 3

            if avg_score >= 80:
                status = "excellent"
            elif avg_score >= 65:
                status = "good"
            elif avg_score >= 50:
                status = "fair"
            else:
                status = "poor"

            combined.append(TimePoint(
                timestamp=smile[i].timestamp,
                value=avg_score,
                status=status,
                label={"excellent": "훌륭", "good": "좋음", "fair": "보통", "poor": "개선필요"}.get(status, status)
            ))

        return combined

    def _collect_feedback(
        self,
        smile: SmileAnalysis,
        eye_contact: EyeContactAnalysis,
        naturalness: NaturalnessAnalysis
    ) -> Tuple[List[str], List[str]]:
        """강점/개선점 수집"""
        strengths = []
        improvements = []

        # 미소
        if smile.smile_score >= 60:
            strengths.append("친근한 미소")
        elif smile.smile_score < 40:
            improvements.append("미소 연습 필요")

        # 눈 맞춤
        if eye_contact.eye_contact_ratio >= 0.55:
            strengths.append("좋은 눈 맞춤")
        elif eye_contact.eye_contact_ratio < 0.35:
            improvements.append("눈 맞춤 개선 필요")

        # 자연스러움
        if naturalness.naturalness_score >= 70:
            strengths.append("자연스러운 표정")
        elif naturalness.naturalness_score < 50:
            improvements.append("표정 자연스러움 연습")

        return strengths[:4], improvements[:4]

    def _generate_coaching_tips(
        self,
        smile: SmileAnalysis,
        eye_contact: EyeContactAnalysis,
        naturalness: NaturalnessAnalysis
    ) -> List[Dict[str, Any]]:
        """표정 코칭 팁 생성"""
        tips = []

        items = [
            ("미소", smile.smile_score, smile.feedback, smile.improvement_tips),
            ("눈맞춤", eye_contact.eye_contact_ratio * 100, eye_contact.feedback, eye_contact.improvement_tips),
            ("자연스러움", naturalness.naturalness_score, naturalness.feedback, naturalness.improvement_tips),
        ]

        items.sort(key=lambda x: x[1])

        for name, score, feedback, item_tips in items[:2]:
            if score < 70:
                tips.append({
                    "category": name,
                    "score": round(score, 1),
                    "issue": feedback,
                    "tips": item_tips[:2],
                    "priority": "high" if score < 50 else "medium",
                })

        return tips


# =====================
# 편의 함수
# =====================

def analyze_expression_enhanced(duration: float) -> Dict:
    """표정 고도화 분석 (간편 함수)"""
    analyzer = EnhancedExpressionAnalyzer()
    result = analyzer.analyze_complete(duration)

    return {
        "overall_score": result.overall_score,
        "grade": result.grade,
        "dominant_expression": result.dominant_expression.value,
        "smile": {
            "score": result.smile.smile_score,
            "level": result.smile.level.value,
            "frequency": result.smile.smile_frequency,
            "feedback": result.smile.feedback,
            "tips": result.smile.improvement_tips,
        },
        "eye_contact": {
            "ratio": result.eye_contact.eye_contact_ratio,
            "level": result.eye_contact.level.value,
            "avg_duration": result.eye_contact.avg_contact_duration,
            "feedback": result.eye_contact.feedback,
            "tips": result.eye_contact.improvement_tips,
        },
        "naturalness": {
            "score": result.naturalness.naturalness_score,
            "consistency": result.naturalness.expression_consistency,
            "smoothness": result.naturalness.transition_smoothness,
            "authenticity": result.naturalness.authenticity_score,
            "feedback": result.naturalness.feedback,
            "tips": result.naturalness.improvement_tips,
        },
        "strengths": result.strengths,
        "improvements": result.improvements,
        "coaching_tips": result.coaching_tips,
    }


def get_smile_timeline(duration: float) -> Dict:
    """미소 타임라인 데이터"""
    analyzer = SmileAnalyzer()
    result = analyzer.analyze(duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.value for p in result.timeline],
        "statuses": [p.status for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "smile_score": result.smile_score,
        "level": result.level.value,
        "frequency": result.smile_frequency,
        "feedback": result.feedback,
    }


def get_eye_contact_timeline(duration: float) -> Dict:
    """눈 맞춤 타임라인 데이터"""
    analyzer = EyeContactAnalyzer()
    result = analyzer.analyze(duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.value for p in result.timeline],
        "statuses": [p.status for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "eye_contact_ratio": result.eye_contact_ratio,
        "level": result.level.value,
        "feedback": result.feedback,
    }


def get_naturalness_timeline(duration: float) -> Dict:
    """자연스러움 타임라인 데이터"""
    analyzer = NaturalnessAnalyzer()
    result = analyzer.analyze(duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.value for p in result.timeline],
        "statuses": [p.status for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "naturalness_score": result.naturalness_score,
        "consistency": result.expression_consistency,
        "smoothness": result.transition_smoothness,
        "feedback": result.feedback,
    }


def get_expression_coaching(duration: float) -> List[Dict]:
    """표정 코칭 팁"""
    analyzer = EnhancedExpressionAnalyzer()
    result = analyzer.analyze_complete(duration)
    return result.coaching_tips
