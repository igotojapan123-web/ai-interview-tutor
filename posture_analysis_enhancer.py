# posture_analysis_enhancer.py
# Phase D3: 자세 분석 고도화 모듈
# FlyReady Lab Enhancement

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math
import random


class PostureLevel(Enum):
    """자세 수준"""
    POOR = "poor"
    FAIR = "fair"
    GOOD = "good"
    EXCELLENT = "excellent"


class ShoulderPosition(Enum):
    """어깨 위치"""
    HUNCHED = "hunched"         # 움츠림
    UNEVEN = "uneven"           # 불균형
    TENSE = "tense"             # 긴장됨
    RELAXED = "relaxed"         # 편안함
    PROPER = "proper"           # 바른 자세


class GazeDirection(Enum):
    """시선 방향"""
    DOWN = "down"               # 아래
    AWAY = "away"               # 회피
    WANDERING = "wandering"     # 산만
    FOCUSED = "focused"         # 집중
    DIRECT = "direct"           # 직접 응시


class HandPosition(Enum):
    """손 위치"""
    FIDGETING = "fidgeting"     # 손장난
    CROSSED = "crossed"         # 팔짱
    HIDDEN = "hidden"           # 숨김
    NATURAL = "natural"         # 자연스러움
    GESTURING = "gesturing"     # 제스처


@dataclass
class TimePoint:
    """시간대별 데이터"""
    timestamp: float
    value: float
    status: str
    label: str = ""


@dataclass
class ShoulderAnalysis:
    """어깨 분석 결과"""
    position: ShoulderPosition
    alignment_score: float  # 0-100
    timeline: List[TimePoint]

    # 문제 구간
    hunched_segments: List[Dict[str, Any]]
    tense_segments: List[Dict[str, Any]]

    # 피드백
    feedback: str
    correction_tips: List[str]


@dataclass
class GazeAnalysis:
    """시선 분석 결과"""
    primary_direction: GazeDirection
    eye_contact_ratio: float  # 0-1
    focus_score: float  # 0-100
    timeline: List[TimePoint]

    # 문제 구간
    away_segments: List[Dict[str, Any]]
    wandering_segments: List[Dict[str, Any]]

    # 피드백
    feedback: str
    improvement_tips: List[str]


@dataclass
class HandAnalysis:
    """손 분석 결과"""
    primary_position: HandPosition
    natural_score: float  # 0-100
    gesture_effectiveness: float  # 0-100
    timeline: List[TimePoint]

    # 문제 구간
    fidget_segments: List[Dict[str, Any]]
    crossed_segments: List[Dict[str, Any]]

    # 피드백
    feedback: str
    improvement_tips: List[str]


@dataclass
class EnhancedPostureAnalysis:
    """종합 자세 분석 결과"""
    shoulder: ShoulderAnalysis
    gaze: GazeAnalysis
    hand: HandAnalysis

    # 종합 점수
    overall_score: int  # 0-100
    level: PostureLevel
    grade: str  # S, A, B, C, D

    # 시간대별 종합
    posture_timeline: List[TimePoint]

    # 강점/개선점
    strengths: List[str]
    improvements: List[str]

    # 실시간 교정 가이드
    correction_guides: List[Dict[str, Any]]

    # 우선순위 개선 포인트
    priority_corrections: List[Dict[str, Any]]


# =====================
# 분석 기준 상수
# =====================

SHOULDER_CRITERIA = {
    "hunched": {"score_range": (0, 40), "feedback": "어깨가 움츠러져 있습니다"},
    "uneven": {"score_range": (30, 50), "feedback": "어깨 높이가 불균형합니다"},
    "tense": {"score_range": (40, 60), "feedback": "어깨에 긴장이 느껴집니다"},
    "relaxed": {"score_range": (60, 80), "feedback": "어깨가 편안합니다"},
    "proper": {"score_range": (80, 100), "feedback": "바른 어깨 자세입니다"},
}

GAZE_CRITERIA = {
    "eye_contact_optimal": (0.5, 0.8),  # 적정 눈 맞춤 비율
    "focus_threshold": 70,  # 집중도 기준점
}

HAND_CRITERIA = {
    "fidget_penalty": -5,  # 손장난 감점
    "gesture_bonus": 5,    # 제스처 가점
    "natural_threshold": 70,  # 자연스러움 기준점
}


# =====================
# 어깨 분석기
# =====================

class ShoulderAnalyzer:
    """어깨 자세 분석"""

    def analyze(
        self,
        duration: float,
        posture_data: Optional[List[Dict]] = None
    ) -> ShoulderAnalysis:
        """어깨 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(duration, posture_data)

        # 전체 정렬 점수 계산
        alignment_values = [p.value for p in timeline]
        alignment_score = sum(alignment_values) / len(alignment_values) if alignment_values else 70

        # 주요 위치 결정
        position = self._get_shoulder_position(alignment_score)

        # 문제 구간 분석
        hunched_segs, tense_segs = self._analyze_problem_segments(timeline)

        # 피드백 생성
        feedback, tips = self._generate_feedback(position, alignment_score)

        return ShoulderAnalysis(
            position=position,
            alignment_score=round(alignment_score, 1),
            timeline=timeline,
            hunched_segments=hunched_segs,
            tense_segments=tense_segs,
            feedback=feedback,
            correction_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        posture_data: Optional[List[Dict]]
    ) -> List[TimePoint]:
        """시간대별 어깨 상태 타임라인"""
        timeline = []
        num_points = max(5, int(duration / 10))

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            # 시뮬레이션: 시작/끝에 약간 움츠림, 중간에 안정
            position_factor = i / max(num_points - 1, 1)
            if position_factor < 0.15:
                base_score = 55 + random.gauss(0, 10)  # 시작 시 약간 긴장
            elif position_factor > 0.85:
                base_score = 65 + random.gauss(0, 8)   # 끝 무렵 회복
            else:
                base_score = 75 + random.gauss(0, 8)   # 중간 안정

            score = max(20, min(95, base_score))
            status = self._get_status_label(score)

            timeline.append(TimePoint(
                timestamp=timestamp,
                value=score,
                status=status,
                label=self._get_shoulder_label(score)
            ))

        return timeline

    def _get_status_label(self, score: float) -> str:
        """상태 라벨"""
        if score >= 80:
            return "optimal"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "warning"
        else:
            return "poor"

    def _get_shoulder_label(self, score: float) -> str:
        """어깨 라벨"""
        if score >= 80:
            return "바른 자세"
        elif score >= 60:
            return "양호"
        elif score >= 40:
            return "긴장"
        else:
            return "움츠림"

    def _get_shoulder_position(self, score: float) -> ShoulderPosition:
        """어깨 위치 결정"""
        if score >= 80:
            return ShoulderPosition.PROPER
        elif score >= 65:
            return ShoulderPosition.RELAXED
        elif score >= 50:
            return ShoulderPosition.TENSE
        elif score >= 35:
            return ShoulderPosition.UNEVEN
        else:
            return ShoulderPosition.HUNCHED

    def _analyze_problem_segments(
        self,
        timeline: List[TimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """문제 구간 분석"""
        hunched = []
        tense = []

        for point in timeline:
            if point.value < 40:
                hunched.append({
                    "timestamp": point.timestamp,
                    "score": point.value,
                    "severity": "high"
                })
            elif point.value < 55:
                tense.append({
                    "timestamp": point.timestamp,
                    "score": point.value,
                    "severity": "medium"
                })

        return hunched, tense

    def _generate_feedback(
        self,
        position: ShoulderPosition,
        score: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if position == ShoulderPosition.HUNCHED:
            feedback = "어깨가 많이 움츠러져 있습니다. 자신감 있는 자세를 보여주세요."
            tips = [
                "등을 곧게 펴고 어깨를 뒤로 젖히세요",
                "턱을 살짝 들어 시선을 정면으로 향하세요",
                "심호흡으로 긴장을 풀어보세요",
            ]
        elif position == ShoulderPosition.UNEVEN:
            feedback = "어깨 높이가 불균형합니다."
            tips = [
                "양쪽 어깨 높이를 맞춰주세요",
                "한쪽으로 기대지 않도록 주의하세요",
            ]
        elif position == ShoulderPosition.TENSE:
            feedback = "어깨에 긴장감이 보입니다. 조금 더 편안하게 힘을 빼세요."
            tips = [
                "어깨를 으쓱했다가 천천히 내리세요",
                "목과 어깨 스트레칭을 해보세요",
            ]
        elif position == ShoulderPosition.RELAXED:
            feedback = "어깨 자세가 양호합니다."
            tips = ["현재 자세를 유지하세요"]
        else:  # PROPER
            feedback = "어깨 자세가 훌륭합니다! 자신감 있어 보여요."
            tips = ["완벽한 자세입니다"]

        return feedback, tips


# =====================
# 시선 분석기
# =====================

class GazeAnalyzer:
    """시선 분석"""

    def analyze(
        self,
        duration: float,
        gaze_data: Optional[List[Dict]] = None
    ) -> GazeAnalysis:
        """시선 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(duration, gaze_data)

        # 눈 맞춤 비율 계산
        eye_contact_values = [1 if p.status in ["focused", "direct"] else 0 for p in timeline]
        eye_contact_ratio = sum(eye_contact_values) / len(eye_contact_values) if eye_contact_values else 0.5

        # 집중도 점수
        focus_values = [p.value for p in timeline]
        focus_score = sum(focus_values) / len(focus_values) if focus_values else 70

        # 주요 시선 방향 결정
        direction = self._get_primary_direction(focus_score, eye_contact_ratio)

        # 문제 구간 분석
        away_segs, wandering_segs = self._analyze_problem_segments(timeline)

        # 피드백 생성
        feedback, tips = self._generate_feedback(direction, eye_contact_ratio, focus_score)

        return GazeAnalysis(
            primary_direction=direction,
            eye_contact_ratio=round(eye_contact_ratio, 2),
            focus_score=round(focus_score, 1),
            timeline=timeline,
            away_segments=away_segs,
            wandering_segments=wandering_segs,
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        gaze_data: Optional[List[Dict]]
    ) -> List[TimePoint]:
        """시간대별 시선 타임라인"""
        timeline = []
        num_points = max(5, int(duration / 10))

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            # 시뮬레이션
            focus = 65 + random.gauss(10, 15)
            focus = max(20, min(95, focus))

            # 상태 결정
            if focus >= 80:
                status = "direct"
            elif focus >= 65:
                status = "focused"
            elif focus >= 50:
                status = "wandering"
            elif focus >= 35:
                status = "away"
            else:
                status = "down"

            timeline.append(TimePoint(
                timestamp=timestamp,
                value=focus,
                status=status,
                label=self._get_gaze_label(status)
            ))

        return timeline

    def _get_gaze_label(self, status: str) -> str:
        """시선 라벨"""
        labels = {
            "direct": "직접 응시",
            "focused": "집중",
            "wandering": "산만",
            "away": "회피",
            "down": "아래"
        }
        return labels.get(status, status)

    def _get_primary_direction(
        self,
        focus_score: float,
        eye_contact_ratio: float
    ) -> GazeDirection:
        """주요 시선 방향 결정"""
        if focus_score >= 80 and eye_contact_ratio >= 0.6:
            return GazeDirection.DIRECT
        elif focus_score >= 65 and eye_contact_ratio >= 0.4:
            return GazeDirection.FOCUSED
        elif eye_contact_ratio < 0.3:
            return GazeDirection.AWAY
        elif focus_score < 50:
            return GazeDirection.WANDERING
        else:
            return GazeDirection.FOCUSED

    def _analyze_problem_segments(
        self,
        timeline: List[TimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """문제 구간 분석"""
        away = []
        wandering = []

        for point in timeline:
            if point.status in ["away", "down"]:
                away.append({
                    "timestamp": point.timestamp,
                    "score": point.value,
                    "direction": point.status
                })
            elif point.status == "wandering":
                wandering.append({
                    "timestamp": point.timestamp,
                    "score": point.value
                })

        return away, wandering

    def _generate_feedback(
        self,
        direction: GazeDirection,
        ratio: float,
        score: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if direction == GazeDirection.DOWN:
            feedback = "시선이 아래를 향하고 있습니다. 면접관을 바라봐주세요."
            tips = [
                "턱을 살짝 들어 시선을 높이세요",
                "면접관의 눈과 코 사이를 부드럽게 바라보세요",
                "자료를 볼 때도 자주 눈을 들어주세요",
            ]
        elif direction == GazeDirection.AWAY:
            feedback = "시선이 자주 피하고 있습니다. 자신감 있게 눈을 맞춰보세요."
            tips = [
                "3-5초 정도 눈을 맞추고 자연스럽게 시선 이동",
                "시선 회피는 불안해 보일 수 있어요",
                "거울 보며 눈 맞춤 연습하기",
            ]
        elif direction == GazeDirection.WANDERING:
            feedback = "시선이 산만합니다. 집중력 있게 보여주세요."
            tips = [
                "한 곳에 시선을 고정하는 연습하기",
                "면접관에게 집중하세요",
            ]
        elif direction == GazeDirection.FOCUSED:
            feedback = "좋은 시선 처리입니다. 집중하고 있는 모습이에요."
            tips = ["현재 시선 처리를 유지하세요"]
        else:  # DIRECT
            feedback = "훌륭한 눈 맞춤입니다! 자신감 있어 보여요."
            tips = ["완벽합니다. 과하지 않게 유지하세요"]

        return feedback, tips


# =====================
# 손 분석기
# =====================

class HandAnalyzer:
    """손 자세 분석"""

    def analyze(
        self,
        duration: float,
        hand_data: Optional[List[Dict]] = None
    ) -> HandAnalysis:
        """손 분석"""

        # 타임라인 생성
        timeline = self._generate_timeline(duration, hand_data)

        # 자연스러움 점수 계산
        natural_values = [p.value for p in timeline]
        natural_score = sum(natural_values) / len(natural_values) if natural_values else 70

        # 제스처 효과성
        gesture_count = sum(1 for p in timeline if p.status == "gesturing")
        gesture_effectiveness = min(100, 50 + gesture_count * 10)

        # 주요 위치 결정
        position = self._get_primary_position(natural_score, timeline)

        # 문제 구간 분석
        fidget_segs, crossed_segs = self._analyze_problem_segments(timeline)

        # 피드백 생성
        feedback, tips = self._generate_feedback(position, natural_score)

        return HandAnalysis(
            primary_position=position,
            natural_score=round(natural_score, 1),
            gesture_effectiveness=round(gesture_effectiveness, 1),
            timeline=timeline,
            fidget_segments=fidget_segs,
            crossed_segments=crossed_segs,
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_timeline(
        self,
        duration: float,
        hand_data: Optional[List[Dict]]
    ) -> List[TimePoint]:
        """시간대별 손 상태 타임라인"""
        timeline = []
        num_points = max(5, int(duration / 10))

        for i in range(num_points):
            timestamp = (duration / num_points) * i

            # 시뮬레이션
            natural = 65 + random.gauss(5, 12)
            natural = max(25, min(95, natural))

            # 상태 결정
            rand_val = random.random()
            if natural >= 75:
                status = "gesturing" if rand_val > 0.7 else "natural"
            elif natural >= 55:
                status = "natural"
            elif natural >= 40:
                status = "fidgeting"
            else:
                status = "crossed" if rand_val > 0.5 else "hidden"

            timeline.append(TimePoint(
                timestamp=timestamp,
                value=natural,
                status=status,
                label=self._get_hand_label(status)
            ))

        return timeline

    def _get_hand_label(self, status: str) -> str:
        """손 상태 라벨"""
        labels = {
            "gesturing": "제스처",
            "natural": "자연스러움",
            "fidgeting": "손장난",
            "crossed": "팔짱",
            "hidden": "숨김"
        }
        return labels.get(status, status)

    def _get_primary_position(
        self,
        score: float,
        timeline: List[TimePoint]
    ) -> HandPosition:
        """주요 손 위치 결정"""
        # 가장 빈번한 상태 찾기
        status_counts: Dict[str, int] = {}
        for point in timeline:
            status_counts[point.status] = status_counts.get(point.status, 0) + 1

        if status_counts:
            most_common = max(status_counts, key=status_counts.get)
            return HandPosition(most_common)

        if score >= 70:
            return HandPosition.NATURAL
        elif score >= 50:
            return HandPosition.FIDGETING
        else:
            return HandPosition.CROSSED

    def _analyze_problem_segments(
        self,
        timeline: List[TimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """문제 구간 분석"""
        fidget = []
        crossed = []

        for point in timeline:
            if point.status == "fidgeting":
                fidget.append({
                    "timestamp": point.timestamp,
                    "score": point.value
                })
            elif point.status in ["crossed", "hidden"]:
                crossed.append({
                    "timestamp": point.timestamp,
                    "status": point.status
                })

        return fidget, crossed

    def _generate_feedback(
        self,
        position: HandPosition,
        score: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if position == HandPosition.FIDGETING:
            feedback = "손을 만지작거리고 있습니다. 차분하게 정리해주세요."
            tips = [
                "손을 무릎 위에 자연스럽게 올려놓으세요",
                "펜이나 물건을 만지지 마세요",
                "긴장될 때는 손바닥을 무릎에 대고 힘을 빼세요",
            ]
        elif position == HandPosition.CROSSED:
            feedback = "팔짱을 끼고 있습니다. 개방적인 자세를 보여주세요."
            tips = [
                "팔짱은 방어적으로 보일 수 있어요",
                "손을 무릎 위나 책상 위에 자연스럽게",
                "오픈된 자세가 친근함을 줍니다",
            ]
        elif position == HandPosition.HIDDEN:
            feedback = "손이 보이지 않습니다. 자연스럽게 보여주세요."
            tips = [
                "손을 책상 아래 숨기지 마세요",
                "손이 보이면 더 신뢰감을 줍니다",
            ]
        elif position == HandPosition.NATURAL:
            feedback = "자연스러운 손 위치입니다."
            tips = ["현재 자세를 유지하세요"]
        else:  # GESTURING
            feedback = "적절한 제스처를 사용하고 있습니다. 훌륭해요!"
            tips = ["과하지 않게 현재 수준을 유지하세요"]

        return feedback, tips


# =====================
# 통합 분석기
# =====================

class EnhancedPostureAnalyzer:
    """통합 자세 분석기"""

    def __init__(self):
        self.shoulder_analyzer = ShoulderAnalyzer()
        self.gaze_analyzer = GazeAnalyzer()
        self.hand_analyzer = HandAnalyzer()

    def analyze_complete(
        self,
        duration: float,
        posture_data: Optional[List[Dict]] = None,
        gaze_data: Optional[List[Dict]] = None,
        hand_data: Optional[List[Dict]] = None
    ) -> EnhancedPostureAnalysis:
        """종합 자세 분석"""

        # 개별 분석
        shoulder = self.shoulder_analyzer.analyze(duration, posture_data)
        gaze = self.gaze_analyzer.analyze(duration, gaze_data)
        hand = self.hand_analyzer.analyze(duration, hand_data)

        # 종합 점수 계산
        overall_score = int(
            shoulder.alignment_score * 0.3 +
            gaze.focus_score * 0.4 +
            hand.natural_score * 0.3
        )

        # 수준 결정
        level = self._determine_level(overall_score)

        # 등급 결정
        grade = self._determine_grade(overall_score)

        # 종합 타임라인
        posture_timeline = self._create_combined_timeline(
            shoulder.timeline, gaze.timeline, hand.timeline
        )

        # 강점/개선점 수집
        strengths, improvements = self._collect_feedback(shoulder, gaze, hand)

        # 실시간 교정 가이드
        guides = self._generate_correction_guides(shoulder, gaze, hand)

        # 우선순위 개선 포인트
        priorities = self._prioritize_corrections(shoulder, gaze, hand)

        return EnhancedPostureAnalysis(
            shoulder=shoulder,
            gaze=gaze,
            hand=hand,
            overall_score=overall_score,
            level=level,
            grade=grade,
            posture_timeline=posture_timeline,
            strengths=strengths,
            improvements=improvements,
            correction_guides=guides,
            priority_corrections=priorities,
        )

    def _determine_level(self, score: int) -> PostureLevel:
        """수준 결정"""
        if score >= 85:
            return PostureLevel.EXCELLENT
        elif score >= 70:
            return PostureLevel.GOOD
        elif score >= 55:
            return PostureLevel.FAIR
        else:
            return PostureLevel.POOR

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

    def _create_combined_timeline(
        self,
        shoulder: List[TimePoint],
        gaze: List[TimePoint],
        hand: List[TimePoint]
    ) -> List[TimePoint]:
        """종합 타임라인 생성"""
        combined = []
        num_points = min(len(shoulder), len(gaze), len(hand))

        for i in range(num_points):
            avg_score = (shoulder[i].value + gaze[i].value + hand[i].value) / 3

            if avg_score >= 80:
                status = "excellent"
            elif avg_score >= 65:
                status = "good"
            elif avg_score >= 50:
                status = "fair"
            else:
                status = "poor"

            combined.append(TimePoint(
                timestamp=shoulder[i].timestamp,
                value=avg_score,
                status=status,
                label={"excellent": "훌륭", "good": "좋음", "fair": "보통", "poor": "개선필요"}.get(status, status)
            ))

        return combined

    def _collect_feedback(
        self,
        shoulder: ShoulderAnalysis,
        gaze: GazeAnalysis,
        hand: HandAnalysis
    ) -> Tuple[List[str], List[str]]:
        """강점/개선점 수집"""
        strengths = []
        improvements = []

        # 어깨
        if shoulder.alignment_score >= 75:
            strengths.append("바른 어깨 자세")
        elif shoulder.alignment_score < 55:
            improvements.append("어깨 자세 교정 필요")

        # 시선
        if gaze.focus_score >= 75:
            strengths.append("좋은 눈 맞춤")
        elif gaze.focus_score < 55:
            improvements.append("시선 처리 개선 필요")

        if gaze.eye_contact_ratio >= 0.6:
            strengths.append("적절한 눈 맞춤 비율")
        elif gaze.eye_contact_ratio < 0.35:
            improvements.append("눈 맞춤 빈도 높이기")

        # 손
        if hand.natural_score >= 75:
            strengths.append("자연스러운 손 위치")
        elif hand.natural_score < 55:
            improvements.append("손 자세 개선 필요")

        if hand.primary_position == HandPosition.GESTURING:
            strengths.append("효과적인 제스처 활용")

        return strengths[:4], improvements[:4]

    def _generate_correction_guides(
        self,
        shoulder: ShoulderAnalysis,
        gaze: GazeAnalysis,
        hand: HandAnalysis
    ) -> List[Dict[str, Any]]:
        """실시간 교정 가이드 생성"""
        guides = []

        # 어깨 교정
        if shoulder.hunched_segments or shoulder.alignment_score < 60:
            guides.append({
                "category": "어깨",
                "issue": "어깨가 움츠러져 있습니다",
                "correction": "등을 펴고 어깨를 뒤로 젖혀주세요",
                "priority": "high" if shoulder.alignment_score < 45 else "medium"
            })

        # 시선 교정
        if gaze.away_segments or gaze.focus_score < 60:
            guides.append({
                "category": "시선",
                "issue": "시선이 불안정합니다",
                "correction": "면접관의 눈과 코 사이를 부드럽게 바라보세요",
                "priority": "high" if gaze.focus_score < 45 else "medium"
            })

        # 손 교정
        if hand.fidget_segments or hand.natural_score < 60:
            guides.append({
                "category": "손",
                "issue": "손 자세가 불안정합니다",
                "correction": "손을 무릎 위에 자연스럽게 올려놓으세요",
                "priority": "high" if hand.natural_score < 45 else "medium"
            })

        return guides

    def _prioritize_corrections(
        self,
        shoulder: ShoulderAnalysis,
        gaze: GazeAnalysis,
        hand: HandAnalysis
    ) -> List[Dict[str, Any]]:
        """우선순위 교정 포인트"""
        priorities = []

        items = [
            ("어깨", shoulder.alignment_score, shoulder.feedback, shoulder.correction_tips),
            ("시선", gaze.focus_score, gaze.feedback, gaze.improvement_tips),
            ("손", hand.natural_score, hand.feedback, hand.improvement_tips),
        ]

        # 점수 낮은 순 정렬
        items.sort(key=lambda x: x[1])

        for name, score, feedback, tips in items[:2]:
            if score < 75:
                priorities.append({
                    "category": name,
                    "score": round(score, 1),
                    "feedback": feedback,
                    "tips": tips[:2],
                    "priority": "high" if score < 55 else "medium",
                })

        return priorities


# =====================
# 편의 함수
# =====================

def analyze_posture_enhanced(duration: float) -> Dict:
    """자세 고도화 분석 (간편 함수)"""
    analyzer = EnhancedPostureAnalyzer()
    result = analyzer.analyze_complete(duration)

    return {
        "overall_score": result.overall_score,
        "level": result.level.value,
        "grade": result.grade,
        "shoulder": {
            "position": result.shoulder.position.value,
            "score": result.shoulder.alignment_score,
            "feedback": result.shoulder.feedback,
            "tips": result.shoulder.correction_tips,
        },
        "gaze": {
            "direction": result.gaze.primary_direction.value,
            "eye_contact_ratio": result.gaze.eye_contact_ratio,
            "focus_score": result.gaze.focus_score,
            "feedback": result.gaze.feedback,
            "tips": result.gaze.improvement_tips,
        },
        "hand": {
            "position": result.hand.primary_position.value,
            "natural_score": result.hand.natural_score,
            "gesture_effectiveness": result.hand.gesture_effectiveness,
            "feedback": result.hand.feedback,
            "tips": result.hand.improvement_tips,
        },
        "strengths": result.strengths,
        "improvements": result.improvements,
        "correction_guides": result.correction_guides,
        "priority_corrections": result.priority_corrections,
    }


def get_shoulder_timeline(duration: float) -> Dict:
    """어깨 타임라인 데이터"""
    analyzer = ShoulderAnalyzer()
    result = analyzer.analyze(duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.value for p in result.timeline],
        "statuses": [p.status for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "overall_score": result.alignment_score,
        "position": result.position.value,
        "feedback": result.feedback,
    }


def get_gaze_timeline(duration: float) -> Dict:
    """시선 타임라인 데이터"""
    analyzer = GazeAnalyzer()
    result = analyzer.analyze(duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.value for p in result.timeline],
        "statuses": [p.status for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "eye_contact_ratio": result.eye_contact_ratio,
        "focus_score": result.focus_score,
        "direction": result.primary_direction.value,
        "feedback": result.feedback,
    }


def get_hand_timeline(duration: float) -> Dict:
    """손 타임라인 데이터"""
    analyzer = HandAnalyzer()
    result = analyzer.analyze(duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "values": [p.value for p in result.timeline],
        "statuses": [p.status for p in result.timeline],
        "labels": [p.label for p in result.timeline],
        "natural_score": result.natural_score,
        "position": result.primary_position.value,
        "feedback": result.feedback,
    }


def get_posture_correction_guide(duration: float) -> List[Dict]:
    """실시간 교정 가이드"""
    analyzer = EnhancedPostureAnalyzer()
    result = analyzer.analyze_complete(duration)
    return result.correction_guides
