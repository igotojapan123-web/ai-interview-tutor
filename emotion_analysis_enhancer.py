# emotion_analysis_enhancer.py
# Phase D2: 감정 분석 고도화 모듈
# FlyReady Lab Enhancement

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math
import random


class ConfidenceLevel(Enum):
    """자신감 수준"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class StressLevel(Enum):
    """긴장도 수준"""
    RELAXED = "relaxed"
    CALM = "calm"
    SLIGHT = "slight"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EmotionType(Enum):
    """감정 유형"""
    NEUTRAL = "neutral"
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    ENTHUSIASTIC = "enthusiastic"
    HESITANT = "hesitant"
    CALM = "calm"
    ANXIOUS = "anxious"


@dataclass
class EmotionTimePoint:
    """시간대별 감정 데이터"""
    timestamp: float
    confidence: float  # 0-100
    stress: float  # 0-100
    engagement: float  # 0-100
    emotion: EmotionType
    label: str = ""


@dataclass
class SegmentFeedback:
    """구간별 피드백"""
    start_time: float
    end_time: float
    avg_confidence: float
    avg_stress: float
    dominant_emotion: EmotionType
    feedback: str
    suggestions: List[str]


@dataclass
class ConfidenceAnalysis:
    """자신감 분석 결과"""
    overall_score: float  # 0-100
    level: ConfidenceLevel
    timeline: List[EmotionTimePoint]

    # 구간 분석
    high_confidence_segments: List[Dict[str, Any]]
    low_confidence_segments: List[Dict[str, Any]]

    # 변화 패턴
    trend: str  # "improving", "declining", "stable", "fluctuating"
    stability_score: float  # 0-100

    # 피드백
    feedback: str
    improvement_tips: List[str]


@dataclass
class StressAnalysis:
    """긴장도 분석 결과"""
    overall_score: float  # 0-100 (높을수록 긴장)
    level: StressLevel
    timeline: List[EmotionTimePoint]

    # 구간 분석
    high_stress_segments: List[Dict[str, Any]]
    relaxed_segments: List[Dict[str, Any]]

    # 피크 분석
    peak_stress_time: Optional[float]
    peak_stress_value: float

    # 피드백
    feedback: str
    coping_tips: List[str]


@dataclass
class EngagementAnalysis:
    """몰입도 분석 결과"""
    overall_score: float  # 0-100
    timeline: List[EmotionTimePoint]

    # 구간별 몰입도
    high_engagement_segments: List[Dict[str, Any]]
    low_engagement_segments: List[Dict[str, Any]]

    # 피드백
    feedback: str
    tips: List[str]


@dataclass
class EnhancedEmotionAnalysis:
    """종합 감정 분석 결과"""
    confidence: ConfidenceAnalysis
    stress: StressAnalysis
    engagement: EngagementAnalysis

    # 종합 점수
    overall_score: int  # 0-100
    grade: str  # S, A, B, C, D

    # 주요 감정
    dominant_emotion: EmotionType
    emotion_distribution: Dict[str, float]

    # 구간별 피드백
    segment_feedbacks: List[SegmentFeedback]

    # 강점/개선점
    strengths: List[str]
    improvements: List[str]

    # 우선순위 개선 포인트
    priority_improvements: List[Dict[str, Any]]


# =====================
# 분석 기준 상수
# =====================

CONFIDENCE_THRESHOLDS = {
    "very_low": (0, 30),
    "low": (30, 50),
    "moderate": (50, 70),
    "high": (70, 85),
    "very_high": (85, 100),
}

STRESS_THRESHOLDS = {
    "relaxed": (0, 20),
    "calm": (20, 35),
    "slight": (35, 50),
    "moderate": (50, 65),
    "high": (65, 80),
    "very_high": (80, 100),
}


# =====================
# 자신감 분석기
# =====================

class ConfidenceAnalyzer:
    """자신감 분석"""

    def analyze(
        self,
        duration: float,
        voice_stability: Optional[float] = None,
        speech_rate_stability: Optional[float] = None,
        pause_patterns: Optional[List[Dict]] = None,
        timestamps: Optional[List[float]] = None
    ) -> ConfidenceAnalysis:
        """자신감 분석"""

        # 타임라인 생성 (시뮬레이션)
        timeline = self._generate_timeline(
            duration, voice_stability, speech_rate_stability
        )

        # 전체 자신감 점수 계산
        confidence_values = [p.confidence for p in timeline]
        overall_score = sum(confidence_values) / len(confidence_values) if confidence_values else 50

        # 자신감 수준 결정
        level = self._get_confidence_level(overall_score)

        # 구간 분석
        high_segments, low_segments = self._analyze_segments(timeline)

        # 추세 분석
        trend = self._analyze_trend(confidence_values)
        stability = self._calculate_stability(confidence_values)

        # 피드백 생성
        feedback, tips = self._generate_feedback(overall_score, level, trend)

        return ConfidenceAnalysis(
            overall_score=round(overall_score, 1),
            level=level,
            timeline=timeline,
            high_confidence_segments=high_segments,
            low_confidence_segments=low_segments,
            trend=trend,
            stability_score=stability,
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        voice_stability: Optional[float],
        speech_rate_stability: Optional[float]
    ) -> List[EmotionTimePoint]:
        """시간대별 자신감 타임라인 생성"""
        timeline = []
        num_points = max(5, int(duration / 10))

        base_confidence = 60  # 기본 자신감
        if voice_stability:
            base_confidence = min(90, 40 + voice_stability * 50)

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            # 자연스러운 변화 시뮬레이션
            variation = random.gauss(0, 10)

            # 시작/끝 보정 (시작: 긴장, 중간: 안정, 끝: 자신감)
            position_factor = i / max(num_points - 1, 1)
            if position_factor < 0.2:
                variation -= 10  # 시작 시 약간 낮음
            elif position_factor > 0.8:
                variation += 5  # 끝 무렵 회복

            confidence = max(10, min(95, base_confidence + variation))
            stress = max(10, min(90, 100 - confidence + random.gauss(0, 8)))
            engagement = max(20, min(95, 50 + random.gauss(10, 15)))

            emotion = self._determine_emotion(confidence, stress)

            timeline.append(EmotionTimePoint(
                timestamp=timestamp,
                confidence=confidence,
                stress=stress,
                engagement=engagement,
                emotion=emotion,
                label=self._get_confidence_label(confidence)
            ))

        return timeline

    def _determine_emotion(self, confidence: float, stress: float) -> EmotionType:
        """감정 유형 결정"""
        if confidence >= 75 and stress <= 30:
            return EmotionType.CONFIDENT
        elif confidence >= 70 and stress <= 40:
            return EmotionType.CALM
        elif stress >= 60:
            return EmotionType.ANXIOUS
        elif confidence <= 40:
            return EmotionType.HESITANT
        elif confidence >= 60 and stress <= 50:
            return EmotionType.ENTHUSIASTIC
        else:
            return EmotionType.NEUTRAL

    def _get_confidence_level(self, score: float) -> ConfidenceLevel:
        """자신감 수준 결정"""
        for level, (min_v, max_v) in CONFIDENCE_THRESHOLDS.items():
            if min_v <= score < max_v:
                return ConfidenceLevel(level)
        return ConfidenceLevel.MODERATE

    def _get_confidence_label(self, confidence: float) -> str:
        """자신감 라벨"""
        if confidence >= 80:
            return "높음"
        elif confidence >= 60:
            return "보통"
        elif confidence >= 40:
            return "낮음"
        else:
            return "매우 낮음"

    def _analyze_segments(
        self,
        timeline: List[EmotionTimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """고/저 자신감 구간 분석"""
        high_segments = []
        low_segments = []

        for point in timeline:
            if point.confidence >= 75:
                high_segments.append({
                    "timestamp": point.timestamp,
                    "confidence": point.confidence,
                    "emotion": point.emotion.value
                })
            elif point.confidence <= 40:
                low_segments.append({
                    "timestamp": point.timestamp,
                    "confidence": point.confidence,
                    "emotion": point.emotion.value
                })

        return high_segments, low_segments

    def _analyze_trend(self, values: List[float]) -> str:
        """추세 분석"""
        if len(values) < 3:
            return "stable"

        first_third = sum(values[:len(values)//3]) / (len(values)//3)
        last_third = sum(values[-len(values)//3:]) / (len(values)//3)

        diff = last_third - first_third

        if diff > 10:
            return "improving"
        elif diff < -10:
            return "declining"
        else:
            # 변동성 체크
            std = self._calculate_std(values)
            if std > 15:
                return "fluctuating"
            return "stable"

    def _calculate_stability(self, values: List[float]) -> float:
        """안정성 점수 계산"""
        if not values:
            return 50
        std = self._calculate_std(values)
        # 표준편차가 낮을수록 안정적
        stability = max(0, min(100, 100 - std * 3))
        return round(stability, 1)

    def _calculate_std(self, values: List[float]) -> float:
        """표준편차 계산"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _generate_feedback(
        self,
        score: float,
        level: ConfidenceLevel,
        trend: str
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if level == ConfidenceLevel.VERY_LOW:
            feedback = "자신감이 많이 부족해 보입니다. 충분한 연습과 준비로 자신감을 키워보세요."
            tips = [
                "거울 앞에서 답변 연습하기",
                "자주 묻는 질문 리스트 만들어 준비하기",
                "자신의 강점과 경험을 미리 정리해두기",
                "심호흡 후 천천히 답변 시작하기",
            ]
        elif level == ConfidenceLevel.LOW:
            feedback = "자신감이 다소 부족합니다. 더 많은 연습이 도움이 될 거예요."
            tips = [
                "답변 구조를 미리 정리하기",
                "핵심 키워드 위주로 기억하기",
                "긍정적인 바디랭귀지 연습하기",
            ]
        elif level == ConfidenceLevel.MODERATE:
            feedback = "보통 수준의 자신감을 보여주고 있습니다. 조금 더 확신을 갖고 말해보세요."
            tips = [
                "답변 끝에서 확실하게 마무리하기",
                "눈 맞춤을 더 자주 하기",
            ]
        elif level == ConfidenceLevel.HIGH:
            feedback = "좋은 자신감을 보여주고 있습니다!"
            tips = ["현재 자신감을 유지하세요"]
        else:  # VERY_HIGH
            feedback = "매우 뛰어난 자신감입니다! 훌륭해요."
            tips = ["오만하게 보이지 않도록 겸손함도 표현하세요"]

        # 추세별 추가 팁
        if trend == "declining":
            tips.append("답변이 길어질수록 자신감이 떨어집니다. 핵심만 간결하게 말해보세요.")
        elif trend == "fluctuating":
            tips.append("자신감이 불안정합니다. 일정한 톤을 유지해보세요.")
        elif trend == "improving":
            tips.insert(0, "답변 후반으로 갈수록 자신감이 회복되고 있어요. 좋은 신호입니다!")

        return feedback, tips


# =====================
# 긴장도 분석기
# =====================

class StressAnalyzer:
    """긴장도 분석"""

    def analyze(
        self,
        duration: float,
        voice_tremor: Optional[float] = None,
        speech_hesitations: Optional[int] = None,
        filler_count: Optional[int] = None
    ) -> StressAnalysis:
        """긴장도 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(
            duration, voice_tremor, speech_hesitations, filler_count
        )

        # 전체 긴장도 계산
        stress_values = [p.stress for p in timeline]
        overall_score = sum(stress_values) / len(stress_values) if stress_values else 50

        # 긴장도 수준 결정
        level = self._get_stress_level(overall_score)

        # 구간 분석
        high_segments, relaxed_segments = self._analyze_segments(timeline)

        # 피크 분석
        peak_time, peak_value = self._find_peak(timeline)

        # 피드백 생성
        feedback, tips = self._generate_feedback(overall_score, level, peak_time)

        return StressAnalysis(
            overall_score=round(overall_score, 1),
            level=level,
            timeline=timeline,
            high_stress_segments=high_segments,
            relaxed_segments=relaxed_segments,
            peak_stress_time=peak_time,
            peak_stress_value=peak_value,
            feedback=feedback,
            coping_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        voice_tremor: Optional[float],
        speech_hesitations: Optional[int],
        filler_count: Optional[int]
    ) -> List[EmotionTimePoint]:
        """시간대별 긴장도 타임라인 생성"""
        timeline = []
        num_points = max(5, int(duration / 10))

        # 기본 긴장도 계산
        base_stress = 45
        if voice_tremor:
            base_stress = min(85, 30 + voice_tremor * 50)
        if speech_hesitations and speech_hesitations > 3:
            base_stress = min(90, base_stress + speech_hesitations * 3)
        if filler_count and filler_count > 5:
            base_stress = min(90, base_stress + filler_count * 2)

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            # 자연스러운 변화
            variation = random.gauss(0, 12)

            # 시작 시 긴장이 높고 점차 낮아지는 패턴
            position_factor = i / max(num_points - 1, 1)
            if position_factor < 0.2:
                variation += 15  # 시작 시 높은 긴장
            elif position_factor > 0.7:
                variation -= 10  # 끝 무렵 완화

            stress = max(10, min(95, base_stress + variation))
            confidence = max(15, min(90, 100 - stress + random.gauss(0, 10)))
            engagement = max(20, min(95, 60 + random.gauss(0, 15)))

            emotion = self._determine_emotion(confidence, stress)

            timeline.append(EmotionTimePoint(
                timestamp=timestamp,
                confidence=confidence,
                stress=stress,
                engagement=engagement,
                emotion=emotion,
                label=self._get_stress_label(stress)
            ))

        return timeline

    def _determine_emotion(self, confidence: float, stress: float) -> EmotionType:
        """감정 유형 결정"""
        if stress >= 70:
            return EmotionType.ANXIOUS
        elif stress >= 50:
            return EmotionType.NERVOUS
        elif stress <= 30 and confidence >= 60:
            return EmotionType.CONFIDENT
        elif stress <= 40:
            return EmotionType.CALM
        else:
            return EmotionType.NEUTRAL

    def _get_stress_level(self, score: float) -> StressLevel:
        """긴장도 수준 결정"""
        for level, (min_v, max_v) in STRESS_THRESHOLDS.items():
            if min_v <= score < max_v:
                return StressLevel(level)
        return StressLevel.MODERATE

    def _get_stress_label(self, stress: float) -> str:
        """긴장도 라벨"""
        if stress >= 70:
            return "높음"
        elif stress >= 50:
            return "보통"
        elif stress >= 30:
            return "낮음"
        else:
            return "매우 낮음"

    def _analyze_segments(
        self,
        timeline: List[EmotionTimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """고긴장/이완 구간 분석"""
        high_segments = []
        relaxed_segments = []

        for point in timeline:
            if point.stress >= 65:
                high_segments.append({
                    "timestamp": point.timestamp,
                    "stress": point.stress,
                    "emotion": point.emotion.value
                })
            elif point.stress <= 35:
                relaxed_segments.append({
                    "timestamp": point.timestamp,
                    "stress": point.stress,
                    "emotion": point.emotion.value
                })

        return high_segments, relaxed_segments

    def _find_peak(
        self,
        timeline: List[EmotionTimePoint]
    ) -> Tuple[Optional[float], float]:
        """피크 긴장도 찾기"""
        if not timeline:
            return None, 0

        peak_point = max(timeline, key=lambda p: p.stress)
        return peak_point.timestamp, peak_point.stress

    def _generate_feedback(
        self,
        score: float,
        level: StressLevel,
        peak_time: Optional[float]
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if level in [StressLevel.VERY_HIGH, StressLevel.HIGH]:
            feedback = "긴장도가 높습니다. 면접 전 긴장을 푸는 연습이 필요해요."
            tips = [
                "면접 전 깊은 호흡 3회 실시하기",
                "입장 전 어깨와 목 스트레칭하기",
                "긍정적인 자기 암시 활용하기",
                "'잘할 수 있다'고 스스로에게 말하기",
                "면접관도 당신이 잘 되길 바란다고 생각하기",
            ]
        elif level == StressLevel.MODERATE:
            feedback = "적당한 긴장감이 있습니다. 이 정도는 오히려 집중력에 도움이 됩니다."
            tips = [
                "현재 수준을 유지하면서 자연스럽게 대화하기",
                "답변 전 잠시 생각을 정리하는 시간 갖기",
            ]
        elif level == StressLevel.SLIGHT:
            feedback = "약간의 긴장감만 있습니다. 좋은 컨디션이에요!"
            tips = ["이 편안한 상태를 유지하세요"]
        else:  # RELAXED, CALM
            feedback = "매우 편안한 상태입니다. 훌륭해요!"
            tips = ["자연스러운 모습을 그대로 보여주세요"]

        return feedback, tips


# =====================
# 몰입도 분석기
# =====================

class EngagementAnalyzer:
    """몰입도 분석"""

    def analyze(
        self,
        duration: float,
        answer_relevance: Optional[float] = None,
        speech_fluency: Optional[float] = None
    ) -> EngagementAnalysis:
        """몰입도 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(duration, answer_relevance, speech_fluency)

        # 전체 몰입도 계산
        engagement_values = [p.engagement for p in timeline]
        overall_score = sum(engagement_values) / len(engagement_values) if engagement_values else 50

        # 구간 분석
        high_segments, low_segments = self._analyze_segments(timeline)

        # 피드백 생성
        feedback, tips = self._generate_feedback(overall_score)

        return EngagementAnalysis(
            overall_score=round(overall_score, 1),
            timeline=timeline,
            high_engagement_segments=high_segments,
            low_engagement_segments=low_segments,
            feedback=feedback,
            tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        answer_relevance: Optional[float],
        speech_fluency: Optional[float]
    ) -> List[EmotionTimePoint]:
        """시간대별 몰입도 타임라인"""
        timeline = []
        num_points = max(5, int(duration / 10))

        base_engagement = 60
        if answer_relevance:
            base_engagement = min(90, 40 + answer_relevance * 50)
        if speech_fluency:
            base_engagement = min(95, base_engagement + speech_fluency * 20)

        for i in range(num_points):
            timestamp = (duration / num_points) * i
            variation = random.gauss(0, 12)

            engagement = max(20, min(95, base_engagement + variation))
            confidence = max(30, min(90, engagement + random.gauss(0, 10)))
            stress = max(10, min(70, 50 + random.gauss(0, 15)))

            timeline.append(EmotionTimePoint(
                timestamp=timestamp,
                confidence=confidence,
                stress=stress,
                engagement=engagement,
                emotion=EmotionType.ENTHUSIASTIC if engagement > 70 else EmotionType.NEUTRAL,
                label="높음" if engagement > 70 else "보통" if engagement > 50 else "낮음"
            ))

        return timeline

    def _analyze_segments(
        self,
        timeline: List[EmotionTimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """고/저 몰입도 구간 분석"""
        high_segments = []
        low_segments = []

        for point in timeline:
            if point.engagement >= 70:
                high_segments.append({
                    "timestamp": point.timestamp,
                    "engagement": point.engagement
                })
            elif point.engagement <= 40:
                low_segments.append({
                    "timestamp": point.timestamp,
                    "engagement": point.engagement
                })

        return high_segments, low_segments

    def _generate_feedback(self, score: float) -> Tuple[str, List[str]]:
        """피드백 생성"""
        if score >= 75:
            feedback = "질문에 높은 몰입도를 보여주고 있습니다. 훌륭해요!"
            tips = ["이 열정을 유지하세요"]
        elif score >= 55:
            feedback = "적당한 몰입도입니다. 조금 더 열정적으로 답변해보세요."
            tips = [
                "답변 내용에 본인의 감정을 담아 표현하기",
                "구체적인 경험담을 활용하여 생동감 더하기",
            ]
        else:
            feedback = "몰입도가 낮아 보입니다. 질문에 더 집중해보세요."
            tips = [
                "질문을 다시 한번 머릿속으로 정리하기",
                "본인의 경험과 연결지어 생각하기",
                "열정적인 표현 연습하기",
            ]

        return feedback, tips


# =====================
# 통합 분석기
# =====================

class EnhancedEmotionAnalyzer:
    """통합 감정 분석기"""

    def __init__(self):
        self.confidence_analyzer = ConfidenceAnalyzer()
        self.stress_analyzer = StressAnalyzer()
        self.engagement_analyzer = EngagementAnalyzer()

    def analyze_complete(
        self,
        duration: float,
        voice_stability: Optional[float] = None,
        voice_tremor: Optional[float] = None,
        speech_hesitations: Optional[int] = None,
        filler_count: Optional[int] = None,
        answer_relevance: Optional[float] = None,
        speech_fluency: Optional[float] = None
    ) -> EnhancedEmotionAnalysis:
        """종합 감정 분석"""

        # 개별 분석
        confidence = self.confidence_analyzer.analyze(
            duration, voice_stability
        )
        stress = self.stress_analyzer.analyze(
            duration, voice_tremor, speech_hesitations, filler_count
        )
        engagement = self.engagement_analyzer.analyze(
            duration, answer_relevance, speech_fluency
        )

        # 종합 점수 계산
        overall_score = int(
            confidence.overall_score * 0.4 +
            (100 - stress.overall_score) * 0.35 +
            engagement.overall_score * 0.25
        )

        # 등급 결정
        grade = self._determine_grade(overall_score)

        # 주요 감정 결정
        dominant_emotion, emotion_distribution = self._analyze_emotions(
            confidence.timeline + stress.timeline
        )

        # 구간별 피드백 생성
        segment_feedbacks = self._generate_segment_feedbacks(
            confidence.timeline, stress.timeline, duration
        )

        # 강점/개선점 수집
        strengths, improvements = self._collect_feedback(confidence, stress, engagement)

        # 우선순위 개선 포인트
        priorities = self._prioritize_improvements(confidence, stress, engagement)

        return EnhancedEmotionAnalysis(
            confidence=confidence,
            stress=stress,
            engagement=engagement,
            overall_score=overall_score,
            grade=grade,
            dominant_emotion=dominant_emotion,
            emotion_distribution=emotion_distribution,
            segment_feedbacks=segment_feedbacks,
            strengths=strengths,
            improvements=improvements,
            priority_improvements=priorities,
        )

    def _determine_grade(self, score: int) -> str:
        """등급 결정"""
        if score >= 85:
            return "S"
        elif score >= 75:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 55:
            return "C"
        else:
            return "D"

    def _analyze_emotions(
        self,
        timeline: List[EmotionTimePoint]
    ) -> Tuple[EmotionType, Dict[str, float]]:
        """감정 분포 분석"""
        emotion_counts: Dict[str, int] = {}

        for point in timeline:
            emotion = point.emotion.value
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        total = sum(emotion_counts.values()) or 1
        distribution = {k: round(v / total * 100, 1) for k, v in emotion_counts.items()}

        # 주요 감정
        if emotion_counts:
            dominant = max(emotion_counts, key=emotion_counts.get)
            return EmotionType(dominant), distribution

        return EmotionType.NEUTRAL, distribution

    def _generate_segment_feedbacks(
        self,
        confidence_timeline: List[EmotionTimePoint],
        stress_timeline: List[EmotionTimePoint],
        duration: float
    ) -> List[SegmentFeedback]:
        """구간별 피드백 생성"""
        feedbacks = []

        # 3구간으로 나누기
        segment_count = 3
        segment_duration = duration / segment_count

        for i in range(segment_count):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration

            # 해당 구간의 데이터 추출
            conf_points = [p for p in confidence_timeline
                         if start_time <= p.timestamp < end_time]
            stress_points = [p for p in stress_timeline
                           if start_time <= p.timestamp < end_time]

            if not conf_points and not stress_points:
                continue

            avg_conf = sum(p.confidence for p in conf_points) / len(conf_points) if conf_points else 50
            avg_stress = sum(p.stress for p in stress_points) / len(stress_points) if stress_points else 50

            # 주요 감정
            all_emotions = [p.emotion for p in conf_points + stress_points]
            if all_emotions:
                emotion_counts = {}
                for e in all_emotions:
                    emotion_counts[e] = emotion_counts.get(e, 0) + 1
                dominant = max(emotion_counts, key=emotion_counts.get)
            else:
                dominant = EmotionType.NEUTRAL

            # 피드백 생성
            feedback, suggestions = self._create_segment_feedback(
                i + 1, avg_conf, avg_stress, dominant
            )

            feedbacks.append(SegmentFeedback(
                start_time=start_time,
                end_time=end_time,
                avg_confidence=round(avg_conf, 1),
                avg_stress=round(avg_stress, 1),
                dominant_emotion=dominant,
                feedback=feedback,
                suggestions=suggestions,
            ))

        return feedbacks

    def _create_segment_feedback(
        self,
        segment_num: int,
        avg_conf: float,
        avg_stress: float,
        emotion: EmotionType
    ) -> Tuple[str, List[str]]:
        """구간별 피드백 텍스트 생성"""
        segment_names = {1: "초반", 2: "중반", 3: "후반"}
        segment_name = segment_names.get(segment_num, f"{segment_num}구간")

        suggestions = []

        if avg_stress > 60:
            feedback = f"{segment_name}에서 긴장도가 높았습니다."
            suggestions.append("심호흡으로 긴장을 완화하세요")
        elif avg_conf < 50:
            feedback = f"{segment_name}에서 자신감이 부족해 보였습니다."
            suggestions.append("더 확신있게 답변해보세요")
        elif avg_conf >= 70 and avg_stress <= 40:
            feedback = f"{segment_name}에서 좋은 모습을 보여주었습니다!"
            suggestions.append("이 상태를 유지하세요")
        else:
            feedback = f"{segment_name}은 무난했습니다."
            suggestions.append("조금 더 자신감을 표현해보세요")

        return feedback, suggestions

    def _collect_feedback(
        self,
        confidence: ConfidenceAnalysis,
        stress: StressAnalysis,
        engagement: EngagementAnalysis
    ) -> Tuple[List[str], List[str]]:
        """강점/개선점 수집"""
        strengths = []
        improvements = []

        # 자신감
        if confidence.overall_score >= 70:
            strengths.append("자신감 있는 태도")
        elif confidence.overall_score < 50:
            improvements.append("자신감 향상 필요")

        # 긴장도
        if stress.overall_score <= 40:
            strengths.append("편안한 태도")
        elif stress.overall_score >= 65:
            improvements.append("긴장 완화 필요")

        # 몰입도
        if engagement.overall_score >= 70:
            strengths.append("높은 몰입도")
        elif engagement.overall_score < 50:
            improvements.append("몰입도 향상 필요")

        # 추세
        if confidence.trend == "improving":
            strengths.append("답변 진행에 따른 자신감 회복")
        elif confidence.trend == "declining":
            improvements.append("답변 후반 자신감 유지")

        return strengths[:4], improvements[:4]

    def _prioritize_improvements(
        self,
        confidence: ConfidenceAnalysis,
        stress: StressAnalysis,
        engagement: EngagementAnalysis
    ) -> List[Dict[str, Any]]:
        """우선순위 개선 포인트"""
        priorities = []

        items = [
            ("자신감", confidence.overall_score, confidence.feedback, confidence.improvement_tips),
            ("긴장 관리", 100 - stress.overall_score, stress.feedback, stress.coping_tips),
            ("몰입도", engagement.overall_score, engagement.feedback, engagement.tips),
        ]

        # 점수 낮은 순 정렬
        items.sort(key=lambda x: x[1])

        for name, score, feedback, tips in items[:2]:
            if score < 70:
                priorities.append({
                    "category": name,
                    "score": round(score, 1),
                    "feedback": feedback,
                    "tips": tips[:2],
                    "priority": "high" if score < 50 else "medium",
                })

        return priorities


# =====================
# 편의 함수
# =====================

def analyze_emotion_enhanced(
    duration: float,
    voice_stability: Optional[float] = None,
    voice_tremor: Optional[float] = None,
    speech_hesitations: Optional[int] = None,
    filler_count: Optional[int] = None,
    answer_relevance: Optional[float] = None
) -> Dict:
    """감정 고도화 분석 (간편 함수)"""
    analyzer = EnhancedEmotionAnalyzer()
    result = analyzer.analyze_complete(
        duration, voice_stability, voice_tremor,
        speech_hesitations, filler_count, answer_relevance
    )

    return {
        "overall_score": result.overall_score,
        "grade": result.grade,
        "dominant_emotion": result.dominant_emotion.value,
        "emotion_distribution": result.emotion_distribution,
        "confidence": {
            "score": result.confidence.overall_score,
            "level": result.confidence.level.value,
            "trend": result.confidence.trend,
            "feedback": result.confidence.feedback,
            "tips": result.confidence.improvement_tips,
        },
        "stress": {
            "score": result.stress.overall_score,
            "level": result.stress.level.value,
            "peak_time": result.stress.peak_stress_time,
            "feedback": result.stress.feedback,
            "tips": result.stress.coping_tips,
        },
        "engagement": {
            "score": result.engagement.overall_score,
            "feedback": result.engagement.feedback,
            "tips": result.engagement.tips,
        },
        "segment_feedbacks": [
            {
                "segment": f"{sf.start_time:.0f}-{sf.end_time:.0f}초",
                "confidence": sf.avg_confidence,
                "stress": sf.avg_stress,
                "emotion": sf.dominant_emotion.value,
                "feedback": sf.feedback,
            }
            for sf in result.segment_feedbacks
        ],
        "strengths": result.strengths,
        "improvements": result.improvements,
        "priority_improvements": result.priority_improvements,
    }


def get_confidence_timeline(duration: float, voice_stability: Optional[float] = None) -> Dict:
    """자신감 타임라인 데이터"""
    analyzer = ConfidenceAnalyzer()
    result = analyzer.analyze(duration, voice_stability)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.confidence for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "overall_score": result.overall_score,
        "level": result.level.value,
        "trend": result.trend,
        "feedback": result.feedback,
    }


def get_stress_timeline(
    duration: float,
    voice_tremor: Optional[float] = None,
    filler_count: Optional[int] = None
) -> Dict:
    """긴장도 타임라인 데이터"""
    analyzer = StressAnalyzer()
    result = analyzer.analyze(duration, voice_tremor, filler_count=filler_count)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.stress for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "overall_score": result.overall_score,
        "level": result.level.value,
        "peak_time": result.peak_stress_time,
        "peak_value": result.peak_stress_value,
        "feedback": result.feedback,
    }


def get_engagement_timeline(duration: float) -> Dict:
    """몰입도 타임라인 데이터"""
    analyzer = EngagementAnalyzer()
    result = analyzer.analyze(duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.engagement for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "overall_score": result.overall_score,
        "feedback": result.feedback,
    }


def get_segment_analysis(duration: float) -> List[Dict]:
    """구간별 감정 분석"""
    analyzer = EnhancedEmotionAnalyzer()
    result = analyzer.analyze_complete(duration)

    return [
        {
            "start": sf.start_time,
            "end": sf.end_time,
            "confidence": sf.avg_confidence,
            "stress": sf.avg_stress,
            "emotion": sf.dominant_emotion.value,
            "feedback": sf.feedback,
            "suggestions": sf.suggestions,
        }
        for sf in result.segment_feedbacks
    ]
