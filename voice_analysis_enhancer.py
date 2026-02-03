# voice_analysis_enhancer.py
# Phase D1: 음성 분석 고도화 모듈
# FlyReady Lab Enhancement

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math


class SpeechSpeedLevel(Enum):
    """말하기 속도 수준"""
    TOO_SLOW = "too_slow"
    SLOW = "slow"
    OPTIMAL = "optimal"
    FAST = "fast"
    TOO_FAST = "too_fast"


class VolumeLevel(Enum):
    """음량 수준"""
    TOO_QUIET = "too_quiet"
    QUIET = "quiet"
    OPTIMAL = "optimal"
    LOUD = "loud"
    TOO_LOUD = "too_loud"


class TonePattern(Enum):
    """톤 패턴"""
    MONOTONE = "monotone"             # 단조로운
    STABLE = "stable"                 # 안정적
    DYNAMIC = "dynamic"               # 역동적
    NERVOUS = "nervous"               # 긴장된
    CONFIDENT = "confident"           # 자신감 있는


@dataclass
class TimePoint:
    """시간대별 데이터 포인트"""
    timestamp: float  # seconds
    value: float
    label: Optional[str] = None


@dataclass
class SpeechSpeedAnalysis:
    """말 속도 분석 결과"""
    average_wpm: float
    average_sps: float  # syllables per second
    speed_level: SpeechSpeedLevel
    timeline: List[TimePoint]  # 시간대별 속도
    speed_variation: float  # 속도 변화량 (표준편차)
    optimal_range: Tuple[int, int]
    score: int  # 0-100

    # 구간별 분석
    fast_segments: List[Dict[str, Any]]
    slow_segments: List[Dict[str, Any]]

    # 피드백
    feedback: str
    improvement_tips: List[str]

    # 호환성 속성
    @property
    def overall_speed(self) -> float:
        return self.average_sps

    @property
    def level(self) -> SpeechSpeedLevel:
        return self.speed_level

    @property
    def graph_data(self) -> List[Dict]:
        return [{"timestamp": p.timestamp, "value": p.value, "label": p.label} for p in self.timeline]


@dataclass
class ToneAnalysis:
    """음성 톤 분석 결과"""
    average_pitch: float  # Hz
    pitch_range: Tuple[float, float]
    pitch_variation: float
    tone_pattern: TonePattern
    timeline: List[TimePoint]  # 시간대별 톤 변화

    # 구간별 분석
    high_pitch_segments: List[Dict[str, Any]]
    low_pitch_segments: List[Dict[str, Any]]

    # 점수
    expressiveness_score: int  # 표현력 점수 0-100
    stability_score: int  # 안정성 점수 0-100

    # 피드백
    feedback: str
    improvement_tips: List[str]

    # 호환성 속성
    @property
    def pattern(self) -> TonePattern:
        return self.tone_pattern

    @property
    def graph_data(self) -> List[Dict]:
        return [{"timestamp": p.timestamp, "value": p.value, "label": p.label} for p in self.timeline]


@dataclass
class VolumeAnalysis:
    """음량 분석 결과"""
    average_db: float
    volume_range: Tuple[float, float]
    volume_variation: float
    volume_level: VolumeLevel
    timeline: List[TimePoint]  # 시간대별 음량

    # 구간별 분석
    quiet_segments: List[Dict[str, Any]]
    loud_segments: List[Dict[str, Any]]

    # 적절성 점수
    appropriateness_score: int  # 0-100
    consistency_score: int  # 일관성 점수

    # 피드백
    feedback: str
    improvement_tips: List[str]

    # 호환성 속성
    @property
    def level(self) -> VolumeLevel:
        return self.volume_level

    @property
    def average_volume(self) -> float:
        return self.average_db

    @property
    def graph_data(self) -> List[Dict]:
        return [{"timestamp": p.timestamp, "value": p.value, "label": p.label} for p in self.timeline]


@dataclass
class SilenceAnalysis:
    """침묵 구간 분석 결과"""
    total_silence_duration: float  # seconds
    silence_ratio: float  # 전체 대비 비율
    silence_count: int
    average_silence_duration: float

    # 침묵 구간 목록
    silence_segments: List[Dict[str, Any]]

    # 침묵 유형별 분류
    natural_pauses: int  # 자연스러운 멈춤
    hesitations: int  # 머뭇거림
    long_pauses: int  # 긴 침묵

    # 점수
    pause_quality_score: int  # 0-100

    # 피드백
    feedback: str
    improvement_tips: List[str]

    # 호환성 속성
    @property
    def problematic_silences(self) -> List[Dict]:
        """문제가 되는 침묵 구간 (1초 이상)"""
        return [s for s in self.silence_segments if s.get("duration", 0) >= 1.0]


@dataclass
class EnhancedVoiceAnalysis:
    """종합 음성 분석 결과"""
    speech_speed: SpeechSpeedAnalysis
    tone: ToneAnalysis
    volume: VolumeAnalysis
    silence: SilenceAnalysis

    # 종합 점수
    overall_score: int
    grade: str  # S, A, B, C, D

    # 강점 / 개선점
    strengths: List[str]
    improvements: List[str]

    # 우선순위 개선 포인트
    priority_improvements: List[Dict[str, Any]]


# =====================
# 분석 기준 상수
# =====================

SPEECH_SPEED_CRITERIA = {
    "ko": {
        "too_slow": (0, 80),
        "slow": (80, 110),
        "optimal": (110, 140),
        "fast": (140, 170),
        "too_fast": (170, 999),
    },
    "en": {
        "too_slow": (0, 100),
        "slow": (100, 130),
        "optimal": (130, 160),
        "fast": (160, 190),
        "too_fast": (190, 999),
    }
}

VOLUME_CRITERIA = {
    "too_quiet": (-60, -40),
    "quiet": (-40, -25),
    "optimal": (-25, -10),
    "loud": (-10, 0),
    "too_loud": (0, 20),
}

SILENCE_THRESHOLDS = {
    "natural_pause": (0.3, 1.0),  # 0.3-1초: 자연스러운 멈춤
    "hesitation": (1.0, 2.0),  # 1-2초: 머뭇거림
    "long_pause": (2.0, float("inf")),  # 2초 이상: 긴 침묵
}


# =====================
# 말 속도 분석기
# =====================

class SpeechSpeedAnalyzer:
    """말 속도 분석"""

    def __init__(self, language: str = "ko"):
        self.language = language
        self.criteria = SPEECH_SPEED_CRITERIA.get(language, SPEECH_SPEED_CRITERIA["ko"])

    def analyze(
        self,
        transcript: str,
        duration: float,
        segment_data: Optional[List[Dict]] = None
    ) -> SpeechSpeedAnalysis:
        """말 속도 분석"""

        # 기본 속도 계산
        words = transcript.split()
        word_count = len(words)

        if duration <= 0:
            wpm = 0
            sps = 0
        else:
            wpm = (word_count / duration) * 60

            # 음절 수 추정 (한국어: 글자수, 영어: 모음 기준)
            if self.language == "ko":
                syllable_count = sum(len(w) for w in words)
            else:
                syllable_count = self._count_syllables_en(transcript)

            sps = syllable_count / duration

        # 속도 수준 결정
        speed_level = self._get_speed_level(wpm)
        optimal_range = self.criteria["optimal"]

        # 타임라인 생성 (세그먼트 데이터가 있으면 활용)
        timeline = self._generate_timeline(segment_data, duration)

        # 속도 변화량 계산
        if timeline:
            values = [p.value for p in timeline]
            speed_variation = self._calculate_std(values)
        else:
            speed_variation = 0

        # 빠른/느린 구간 분석
        fast_segments, slow_segments = self._analyze_segments(timeline)

        # 점수 계산
        score = self._calculate_score(wpm, speed_variation)

        # 피드백 생성
        feedback, tips = self._generate_feedback(wpm, speed_level, speed_variation)

        return SpeechSpeedAnalysis(
            average_wpm=round(wpm, 1),
            average_sps=round(sps, 2),
            speed_level=speed_level,
            timeline=timeline,
            speed_variation=round(speed_variation, 2),
            optimal_range=optimal_range,
            score=score,
            fast_segments=fast_segments,
            slow_segments=slow_segments,
            feedback=feedback,
            improvement_tips=tips,
        )

    def _get_speed_level(self, wpm: float) -> SpeechSpeedLevel:
        """속도 수준 결정"""
        for level, (min_v, max_v) in self.criteria.items():
            if min_v <= wpm < max_v:
                return SpeechSpeedLevel(level)
        return SpeechSpeedLevel.OPTIMAL

    def _generate_timeline(
        self,
        segment_data: Optional[List[Dict]],
        duration: float
    ) -> List[TimePoint]:
        """시간대별 속도 타임라인 생성"""
        timeline = []

        if segment_data:
            for seg in segment_data:
                timestamp = seg.get("start", 0)
                # 세그먼트별 WPM 계산
                seg_text = seg.get("text", "")
                seg_duration = seg.get("duration", 1)
                if seg_duration > 0:
                    seg_wpm = (len(seg_text.split()) / seg_duration) * 60
                    timeline.append(TimePoint(
                        timestamp=timestamp,
                        value=seg_wpm,
                        label=self._get_speed_label(seg_wpm)
                    ))
        else:
            # 시뮬레이션 데이터 (실제 구현에서는 오디오 분석 필요)
            num_points = max(5, int(duration / 5))
            for i in range(num_points):
                timestamp = (duration / num_points) * i
                # 약간의 변화를 가진 시뮬레이션
                base_wpm = 120 + (i % 3 - 1) * 15
                timeline.append(TimePoint(
                    timestamp=timestamp,
                    value=base_wpm,
                    label=self._get_speed_label(base_wpm)
                ))

        return timeline

    def _get_speed_label(self, wpm: float) -> str:
        """속도 라벨"""
        if wpm < 100:
            return "느림"
        elif wpm > 150:
            return "빠름"
        else:
            return "적절"

    def _analyze_segments(
        self,
        timeline: List[TimePoint]
    ) -> Tuple[List[Dict], List[Dict]]:
        """빠른/느린 구간 분석"""
        fast_segments = []
        slow_segments = []

        for point in timeline:
            if point.value > 150:
                fast_segments.append({
                    "timestamp": point.timestamp,
                    "wpm": point.value,
                    "severity": "high" if point.value > 170 else "medium"
                })
            elif point.value < 100:
                slow_segments.append({
                    "timestamp": point.timestamp,
                    "wpm": point.value,
                    "severity": "high" if point.value < 80 else "medium"
                })

        return fast_segments, slow_segments

    def _calculate_score(self, wpm: float, variation: float) -> int:
        """점수 계산"""
        optimal = self.criteria["optimal"]
        mid = (optimal[0] + optimal[1]) / 2

        # 기본 점수 (적정 속도와의 차이)
        deviation = abs(wpm - mid)
        base_score = max(0, 100 - deviation)

        # 변화량 보정 (너무 큰 변화는 감점)
        if variation > 30:
            base_score -= (variation - 30) * 0.5

        return max(0, min(100, int(base_score)))

    def _calculate_std(self, values: List[float]) -> float:
        """표준편차 계산"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _count_syllables_en(self, text: str) -> int:
        """영어 음절 수 계산"""
        words = text.lower().split()
        count = 0
        for word in words:
            word_count = 0
            prev_vowel = False
            for char in word:
                is_vowel = char in "aeiouy"
                if is_vowel and not prev_vowel:
                    word_count += 1
                prev_vowel = is_vowel
            if word.endswith("e"):
                word_count = max(1, word_count - 1)
            count += max(1, word_count)
        return count

    def _generate_feedback(
        self,
        wpm: float,
        level: SpeechSpeedLevel,
        variation: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if level == SpeechSpeedLevel.TOO_SLOW:
            feedback = f"현재 말하기 속도({wpm:.0f} WPM)가 많이 느립니다. 청중의 집중력을 위해 속도를 높여보세요."
            tips = [
                "문장을 짧게 나누어 리듬감 있게 말하기",
                "핵심 단어 위주로 빠르게 전달하기",
                "연습할 때 타이머를 사용하여 속도 체크하기",
            ]
        elif level == SpeechSpeedLevel.SLOW:
            feedback = f"말하기 속도({wpm:.0f} WPM)가 조금 느립니다. 약간 더 빠르게 말해보세요."
            tips = [
                "불필요한 멈춤 줄이기",
                "자주 사용하는 표현을 유창하게 연습하기",
            ]
        elif level == SpeechSpeedLevel.OPTIMAL:
            feedback = f"말하기 속도({wpm:.0f} WPM)가 적절합니다. 좋은 페이스를 유지하고 있습니다."
            tips = ["현재 속도를 유지하세요"]
        elif level == SpeechSpeedLevel.FAST:
            feedback = f"말하기 속도({wpm:.0f} WPM)가 조금 빠릅니다. 중요한 부분에서는 천천히 강조해보세요."
            tips = [
                "문장 끝에서 짧게 멈추기",
                "숫자나 중요 정보는 천천히 말하기",
            ]
        else:  # TOO_FAST
            feedback = f"현재 말하기 속도({wpm:.0f} WPM)가 많이 빠릅니다. 청중이 이해하기 어려울 수 있습니다."
            tips = [
                "심호흡 후 천천히 시작하기",
                "각 문장 사이에 1초 정도 멈추기",
                "중요한 내용은 반복하며 강조하기",
                "긴장을 풀고 편안하게 말하기",
            ]

        # 변화량 관련 팁 추가
        if variation > 40:
            tips.append("말하기 속도를 일정하게 유지해보세요")

        return feedback, tips


# =====================
# 음성 톤 분석기
# =====================

class ToneAnalyzer:
    """음성 톤 분석"""

    def analyze(
        self,
        pitch_data: Optional[List[float]] = None,
        duration: float = 60,
        timestamps: Optional[List[float]] = None
    ) -> ToneAnalysis:
        """톤 분석"""

        # 시뮬레이션 데이터 (실제로는 오디오에서 추출)
        if pitch_data is None:
            pitch_data = self._generate_simulation_data(duration)

        if timestamps is None:
            timestamps = [i * (duration / len(pitch_data)) for i in range(len(pitch_data))]

        # 기본 통계
        avg_pitch = sum(pitch_data) / len(pitch_data) if pitch_data else 0
        min_pitch = min(pitch_data) if pitch_data else 0
        max_pitch = max(pitch_data) if pitch_data else 0
        pitch_variation = self._calculate_std(pitch_data)

        # 톤 패턴 결정
        tone_pattern = self._determine_tone_pattern(pitch_variation, pitch_data)

        # 타임라인 생성
        timeline = [
            TimePoint(timestamp=t, value=p, label=self._get_pitch_label(p))
            for t, p in zip(timestamps, pitch_data)
        ]

        # 고음/저음 구간 분석
        high_segments, low_segments = self._analyze_pitch_segments(
            pitch_data, timestamps, avg_pitch
        )

        # 점수 계산
        expressiveness = self._calculate_expressiveness(pitch_variation)
        stability = self._calculate_stability(pitch_data)

        # 피드백 생성
        feedback, tips = self._generate_feedback(tone_pattern, pitch_variation)

        return ToneAnalysis(
            average_pitch=round(avg_pitch, 1),
            pitch_range=(round(min_pitch, 1), round(max_pitch, 1)),
            pitch_variation=round(pitch_variation, 2),
            tone_pattern=tone_pattern,
            timeline=timeline,
            high_pitch_segments=high_segments,
            low_pitch_segments=low_segments,
            expressiveness_score=expressiveness,
            stability_score=stability,
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_simulation_data(self, duration: float) -> List[float]:
        """시뮬레이션 데이터 생성"""
        import random
        num_points = max(10, int(duration / 2))
        base = 150  # 기본 피치 (Hz)
        return [base + random.gauss(0, 20) for _ in range(num_points)]

    def _calculate_std(self, values: List[float]) -> float:
        """표준편차"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _determine_tone_pattern(
        self,
        variation: float,
        pitch_data: List[float]
    ) -> TonePattern:
        """톤 패턴 결정"""
        if variation < 15:
            return TonePattern.MONOTONE
        elif variation < 25:
            return TonePattern.STABLE
        elif variation < 40:
            return TonePattern.DYNAMIC
        else:
            # 급격한 변화가 많으면 긴장
            if self._has_sudden_changes(pitch_data):
                return TonePattern.NERVOUS
            else:
                return TonePattern.CONFIDENT

    def _has_sudden_changes(self, pitch_data: List[float]) -> bool:
        """급격한 변화 감지"""
        if len(pitch_data) < 2:
            return False
        changes = [abs(pitch_data[i] - pitch_data[i-1]) for i in range(1, len(pitch_data))]
        sudden_count = sum(1 for c in changes if c > 30)
        return sudden_count > len(changes) * 0.3

    def _get_pitch_label(self, pitch: float) -> str:
        """피치 라벨"""
        if pitch < 120:
            return "낮음"
        elif pitch > 200:
            return "높음"
        else:
            return "중간"

    def _analyze_pitch_segments(
        self,
        pitch_data: List[float],
        timestamps: List[float],
        avg_pitch: float
    ) -> Tuple[List[Dict], List[Dict]]:
        """고음/저음 구간 분석"""
        high_segments = []
        low_segments = []

        threshold = 30  # Hz

        for t, p in zip(timestamps, pitch_data):
            if p > avg_pitch + threshold:
                high_segments.append({
                    "timestamp": t,
                    "pitch": p,
                    "deviation": p - avg_pitch
                })
            elif p < avg_pitch - threshold:
                low_segments.append({
                    "timestamp": t,
                    "pitch": p,
                    "deviation": avg_pitch - p
                })

        return high_segments, low_segments

    def _calculate_expressiveness(self, variation: float) -> int:
        """표현력 점수"""
        # 적당한 변화가 있으면 높은 점수
        if 20 <= variation <= 35:
            return 90
        elif 15 <= variation <= 40:
            return 75
        elif variation < 15:
            return 50  # 단조로움
        else:
            return 60  # 너무 과한 변화

    def _calculate_stability(self, pitch_data: List[float]) -> int:
        """안정성 점수"""
        if len(pitch_data) < 2:
            return 70

        changes = [abs(pitch_data[i] - pitch_data[i-1]) for i in range(1, len(pitch_data))]
        avg_change = sum(changes) / len(changes)

        # 평균 변화가 작을수록 안정적
        if avg_change < 10:
            return 95
        elif avg_change < 20:
            return 80
        elif avg_change < 30:
            return 65
        else:
            return 50

    def _generate_feedback(
        self,
        pattern: TonePattern,
        variation: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if pattern == TonePattern.MONOTONE:
            feedback = "목소리가 단조롭습니다. 억양에 변화를 주면 더 생동감 있게 전달할 수 있습니다."
            tips = [
                "중요한 단어에서 톤을 높여보세요",
                "문장 끝에서 톤의 변화를 주세요",
                "질문과 답변의 톤을 다르게 연습하세요",
            ]
        elif pattern == TonePattern.STABLE:
            feedback = "안정적인 톤을 유지하고 있습니다. 포인트에서 약간의 변화를 주면 더 좋습니다."
            tips = [
                "핵심 메시지에서 톤 강조하기",
            ]
        elif pattern == TonePattern.DYNAMIC:
            feedback = "풍부한 억양 변화를 보여주고 있습니다. 훌륭합니다!"
            tips = ["현재 스타일을 유지하세요"]
        elif pattern == TonePattern.NERVOUS:
            feedback = "목소리에서 긴장감이 느껴집니다. 심호흡을 하고 편안하게 말해보세요."
            tips = [
                "답변 전 잠시 심호흡하기",
                "천천히 또박또박 말하기",
                "미리 답변을 연습하여 자신감 갖기",
            ]
        else:  # CONFIDENT
            feedback = "자신감 있는 목소리입니다. 좋은 인상을 주고 있습니다."
            tips = ["현재 톤을 유지하세요"]

        return feedback, tips


# =====================
# 음량 분석기
# =====================

class VolumeAnalyzer:
    """음량 분석"""

    def analyze(
        self,
        volume_data: Optional[List[float]] = None,
        duration: float = 60,
        timestamps: Optional[List[float]] = None
    ) -> VolumeAnalysis:
        """음량 분석"""

        # 시뮬레이션 데이터
        if volume_data is None:
            volume_data = self._generate_simulation_data(duration)

        if timestamps is None:
            timestamps = [i * (duration / len(volume_data)) for i in range(len(volume_data))]

        # 기본 통계
        avg_db = sum(volume_data) / len(volume_data) if volume_data else -20
        min_db = min(volume_data) if volume_data else -40
        max_db = max(volume_data) if volume_data else 0
        variation = self._calculate_std(volume_data)

        # 음량 수준 결정
        volume_level = self._get_volume_level(avg_db)

        # 타임라인
        timeline = [
            TimePoint(timestamp=t, value=v, label=self._get_volume_label(v))
            for t, v in zip(timestamps, volume_data)
        ]

        # 조용한/큰 구간 분석
        quiet_segments, loud_segments = self._analyze_volume_segments(
            volume_data, timestamps, avg_db
        )

        # 점수 계산
        appropriateness = self._calculate_appropriateness(avg_db)
        consistency = self._calculate_consistency(variation)

        # 피드백 생성
        feedback, tips = self._generate_feedback(volume_level, variation)

        return VolumeAnalysis(
            average_db=round(avg_db, 1),
            volume_range=(round(min_db, 1), round(max_db, 1)),
            volume_variation=round(variation, 2),
            volume_level=volume_level,
            timeline=timeline,
            quiet_segments=quiet_segments,
            loud_segments=loud_segments,
            appropriateness_score=appropriateness,
            consistency_score=consistency,
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_simulation_data(self, duration: float) -> List[float]:
        """시뮬레이션 데이터"""
        import random
        num_points = max(10, int(duration / 2))
        base = -18  # 기본 dB
        return [base + random.gauss(0, 5) for _ in range(num_points)]

    def _calculate_std(self, values: List[float]) -> float:
        """표준편차"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def _get_volume_level(self, avg_db: float) -> VolumeLevel:
        """음량 수준 결정"""
        for level, (min_v, max_v) in VOLUME_CRITERIA.items():
            if min_v <= avg_db < max_v:
                return VolumeLevel(level)
        return VolumeLevel.OPTIMAL

    def _get_volume_label(self, db: float) -> str:
        """음량 라벨"""
        if db < -30:
            return "작음"
        elif db > -10:
            return "큼"
        else:
            return "적절"

    def _analyze_volume_segments(
        self,
        volume_data: List[float],
        timestamps: List[float],
        avg_db: float
    ) -> Tuple[List[Dict], List[Dict]]:
        """조용한/큰 구간 분석"""
        quiet_segments = []
        loud_segments = []

        threshold = 10  # dB

        for t, v in zip(timestamps, volume_data):
            if v < avg_db - threshold:
                quiet_segments.append({
                    "timestamp": t,
                    "volume": v,
                    "deviation": avg_db - v
                })
            elif v > avg_db + threshold:
                loud_segments.append({
                    "timestamp": t,
                    "volume": v,
                    "deviation": v - avg_db
                })

        return quiet_segments, loud_segments

    def _calculate_appropriateness(self, avg_db: float) -> int:
        """적절성 점수"""
        optimal_mid = -17  # 적정 음량 중앙
        deviation = abs(avg_db - optimal_mid)
        return max(0, min(100, int(100 - deviation * 3)))

    def _calculate_consistency(self, variation: float) -> int:
        """일관성 점수"""
        if variation < 5:
            return 95
        elif variation < 10:
            return 80
        elif variation < 15:
            return 65
        else:
            return 50

    def _generate_feedback(
        self,
        level: VolumeLevel,
        variation: float
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if level == VolumeLevel.TOO_QUIET:
            feedback = "목소리가 너무 작습니다. 자신감 있게 크게 말해보세요."
            tips = [
                "배에서 소리를 내듯이 발성하기",
                "마이크와의 거리 조절하기",
                "연습할 때 큰 소리로 말하는 습관 들이기",
            ]
        elif level == VolumeLevel.QUIET:
            feedback = "목소리가 조금 작습니다. 약간 더 크게 말해보세요."
            tips = ["핵심 단어에서는 더 크게 강조하기"]
        elif level == VolumeLevel.OPTIMAL:
            feedback = "적절한 음량입니다. 좋습니다!"
            tips = ["현재 음량을 유지하세요"]
        elif level == VolumeLevel.LOUD:
            feedback = "목소리가 조금 큽니다. 면접관과의 거리를 고려해주세요."
            tips = ["부드럽게 말하는 연습하기"]
        else:  # TOO_LOUD
            feedback = "목소리가 너무 큽니다. 면접에서는 부담스러울 수 있습니다."
            tips = [
                "편안한 대화 톤으로 조절하기",
                "마이크 감도 조절하기",
            ]

        if variation > 12:
            tips.append("음량을 일정하게 유지해보세요")

        return feedback, tips


# =====================
# 침묵 구간 분석기
# =====================

class SilenceAnalyzer:
    """침묵 구간 분석"""

    def analyze(
        self,
        silence_segments: Optional[List[Dict]] = None,
        total_duration: float = 60
    ) -> SilenceAnalysis:
        """침묵 분석"""

        # 시뮬레이션 데이터
        if silence_segments is None:
            silence_segments = self._generate_simulation_data(total_duration)

        # start/end 형식을 duration 형식으로 변환
        processed_segments = []
        for seg in silence_segments:
            if "duration" in seg:
                processed_segments.append(seg)
            elif "start" in seg and "end" in seg:
                dur = seg["end"] - seg["start"]
                processed_segments.append({
                    "start": seg["start"],
                    "duration": dur,
                    "type": seg.get("type", "pause")
                })
            else:
                processed_segments.append(seg)

        silence_segments = processed_segments

        # 기본 통계
        total_silence = sum(s.get("duration", 0) for s in silence_segments)
        silence_ratio = total_silence / total_duration if total_duration > 0 else 0
        silence_count = len(silence_segments)
        avg_silence = total_silence / silence_count if silence_count > 0 else 0

        # 침묵 유형별 분류
        natural = 0
        hesitation = 0
        long_pause = 0

        for seg in silence_segments:
            dur = seg.get("duration", 0)
            if SILENCE_THRESHOLDS["natural_pause"][0] <= dur < SILENCE_THRESHOLDS["natural_pause"][1]:
                natural += 1
            elif SILENCE_THRESHOLDS["hesitation"][0] <= dur < SILENCE_THRESHOLDS["hesitation"][1]:
                hesitation += 1
            else:
                long_pause += 1

        # 점수 계산
        quality_score = self._calculate_quality_score(
            silence_ratio, natural, hesitation, long_pause
        )

        # 피드백 생성
        feedback, tips = self._generate_feedback(
            silence_ratio, hesitation, long_pause
        )

        return SilenceAnalysis(
            total_silence_duration=round(total_silence, 2),
            silence_ratio=round(silence_ratio, 3),
            silence_count=silence_count,
            average_silence_duration=round(avg_silence, 2),
            silence_segments=silence_segments,
            natural_pauses=natural,
            hesitations=hesitation,
            long_pauses=long_pause,
            pause_quality_score=quality_score,
            feedback=feedback,
            improvement_tips=tips,
        )

    def _generate_simulation_data(self, duration: float) -> List[Dict]:
        """시뮬레이션 데이터"""
        import random
        segments = []
        num_pauses = max(3, int(duration / 15))

        for i in range(num_pauses):
            timestamp = random.uniform(0, duration)
            dur = random.choice([0.5, 0.7, 1.0, 1.5, 2.0])
            segments.append({
                "start": timestamp,
                "duration": dur,
                "type": "pause"
            })

        return sorted(segments, key=lambda x: x["start"])

    def _calculate_quality_score(
        self,
        ratio: float,
        natural: int,
        hesitation: int,
        long_pause: int
    ) -> int:
        """품질 점수"""
        score = 100

        # 비율이 너무 높거나 낮으면 감점
        optimal_ratio = 0.15
        ratio_deviation = abs(ratio - optimal_ratio)
        score -= int(ratio_deviation * 200)

        # 머뭇거림 감점
        score -= hesitation * 5

        # 긴 침묵 큰 감점
        score -= long_pause * 15

        return max(0, min(100, score))

    def _generate_feedback(
        self,
        ratio: float,
        hesitations: int,
        long_pauses: int
    ) -> Tuple[str, List[str]]:
        """피드백 생성"""
        tips = []

        if long_pauses > 2:
            feedback = "답변 중 긴 침묵이 자주 발생합니다. 미리 답변을 준비하면 도움이 됩니다."
            tips = [
                "예상 질문에 대한 답변 미리 연습하기",
                "생각이 필요할 때는 '잠시 생각해보겠습니다'라고 말하기",
                "핵심 키워드를 떠올리며 답변 구조화하기",
            ]
        elif hesitations > 3:
            feedback = "머뭇거리는 구간이 있습니다. 자신감 있게 말해보세요."
            tips = [
                "'음', '어' 대신 짧은 멈춤 활용하기",
                "답변 시작 전 핵심 키워드 떠올리기",
            ]
        elif ratio > 0.25:
            feedback = "침묵 비율이 높습니다. 더 유창하게 말해보세요."
            tips = ["답변 연습을 통해 유창성 높이기"]
        elif ratio < 0.1:
            feedback = "적절한 멈춤 없이 말하고 있습니다. 중요한 포인트에서 잠시 멈추세요."
            tips = ["문장 사이에 짧은 멈춤 넣기", "청중이 이해할 시간 주기"]
        else:
            feedback = "적절한 멈춤을 사용하고 있습니다. 좋습니다!"
            tips = ["현재 페이스를 유지하세요"]

        return feedback, tips


# =====================
# 통합 분석기
# =====================

class EnhancedVoiceAnalyzer:
    """통합 음성 분석기"""

    def __init__(self, language: str = "ko"):
        self.speech_speed_analyzer = SpeechSpeedAnalyzer(language)
        self.tone_analyzer = ToneAnalyzer()
        self.volume_analyzer = VolumeAnalyzer()
        self.silence_analyzer = SilenceAnalyzer()

    def analyze_complete(
        self,
        transcript: str,
        duration: float,
        pitch_data: Optional[List[float]] = None,
        volume_data: Optional[List[float]] = None,
        silence_segments: Optional[List[Dict]] = None,
        segment_data: Optional[List[Dict]] = None
    ) -> EnhancedVoiceAnalysis:
        """종합 음성 분석"""

        # 개별 분석 실행
        speed = self.speech_speed_analyzer.analyze(transcript, duration, segment_data)
        tone = self.tone_analyzer.analyze(pitch_data, duration)
        volume = self.volume_analyzer.analyze(volume_data, duration)
        silence = self.silence_analyzer.analyze(silence_segments, duration)

        # 종합 점수 계산
        overall_score = int(
            speed.score * 0.25 +
            tone.expressiveness_score * 0.2 +
            tone.stability_score * 0.1 +
            volume.appropriateness_score * 0.2 +
            volume.consistency_score * 0.1 +
            silence.pause_quality_score * 0.15
        )

        # 등급 결정
        grade = self._determine_grade(overall_score)

        # 강점/개선점 수집
        strengths, improvements = self._collect_feedback(speed, tone, volume, silence)

        # 우선순위 개선 포인트
        priority = self._prioritize_improvements(speed, tone, volume, silence)

        return EnhancedVoiceAnalysis(
            speech_speed=speed,
            tone=tone,
            volume=volume,
            silence=silence,
            overall_score=overall_score,
            grade=grade,
            strengths=strengths,
            improvements=improvements,
            priority_improvements=priority,
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

    def _collect_feedback(
        self,
        speed: SpeechSpeedAnalysis,
        tone: ToneAnalysis,
        volume: VolumeAnalysis,
        silence: SilenceAnalysis
    ) -> Tuple[List[str], List[str]]:
        """강점/개선점 수집"""
        strengths = []
        improvements = []

        # 속도
        if speed.score >= 80:
            strengths.append("적절한 말하기 속도")
        else:
            improvements.append(speed.improvement_tips[0] if speed.improvement_tips else "속도 조절 필요")

        # 톤
        if tone.expressiveness_score >= 80:
            strengths.append("풍부한 억양 표현")
        if tone.stability_score >= 80:
            strengths.append("안정적인 목소리 톤")
        if tone.expressiveness_score < 60:
            improvements.append("억양에 변화 필요")

        # 음량
        if volume.appropriateness_score >= 80:
            strengths.append("적절한 음량")
        else:
            improvements.append(volume.improvement_tips[0] if volume.improvement_tips else "음량 조절 필요")

        # 침묵
        if silence.pause_quality_score >= 80:
            strengths.append("자연스러운 멈춤 활용")
        if silence.long_pauses > 1:
            improvements.append("긴 침묵 줄이기")

        return strengths[:4], improvements[:4]

    def _prioritize_improvements(
        self,
        speed: SpeechSpeedAnalysis,
        tone: ToneAnalysis,
        volume: VolumeAnalysis,
        silence: SilenceAnalysis
    ) -> List[Dict[str, Any]]:
        """우선순위 개선 포인트"""
        priorities = []

        # 점수가 낮은 항목 우선
        items = [
            ("말 속도", speed.score, speed.feedback, speed.improvement_tips),
            ("억양 표현", tone.expressiveness_score, tone.feedback, tone.improvement_tips),
            ("음량", volume.appropriateness_score, volume.feedback, volume.improvement_tips),
            ("멈춤 활용", silence.pause_quality_score, silence.feedback, silence.improvement_tips),
        ]

        # 점수 낮은 순 정렬
        items.sort(key=lambda x: x[1])

        for name, score, feedback, tips in items[:3]:
            if score < 80:
                priorities.append({
                    "category": name,
                    "score": score,
                    "feedback": feedback,
                    "tips": tips[:2],
                    "priority": "high" if score < 60 else "medium",
                })

        return priorities


# =====================
# 편의 함수
# =====================

def analyze_voice_enhanced(
    transcript: str,
    duration: float,
    language: str = "ko",
    pitch_data: Optional[List[float]] = None,
    volume_data: Optional[List[float]] = None,
    segment_data: Optional[List[Dict]] = None,
    silence_segments: Optional[List[Dict]] = None
) -> Dict:
    """음성 고도화 분석 (간편 함수)"""
    analyzer = EnhancedVoiceAnalyzer(language)
    result = analyzer.analyze_complete(
        transcript, duration, pitch_data, volume_data, silence_segments, segment_data
    )

    return {
        "overall_score": result.overall_score,
        "grade": result.grade,
        "speech_speed": {
            "wpm": result.speech_speed.average_wpm,
            "level": result.speech_speed.speed_level.value,
            "score": result.speech_speed.score,
            "feedback": result.speech_speed.feedback,
            "tips": result.speech_speed.improvement_tips,
        },
        "tone": {
            "pattern": result.tone.tone_pattern.value,
            "expressiveness": result.tone.expressiveness_score,
            "stability": result.tone.stability_score,
            "feedback": result.tone.feedback,
            "tips": result.tone.improvement_tips,
        },
        "volume": {
            "level": result.volume.volume_level.value,
            "appropriateness": result.volume.appropriateness_score,
            "consistency": result.volume.consistency_score,
            "feedback": result.volume.feedback,
            "tips": result.volume.improvement_tips,
        },
        "silence": {
            "ratio": result.silence.silence_ratio,
            "quality_score": result.silence.pause_quality_score,
            "hesitations": result.silence.hesitations,
            "feedback": result.silence.feedback,
            "tips": result.silence.improvement_tips,
        },
        "strengths": result.strengths,
        "improvements": result.improvements,
        "priority_improvements": result.priority_improvements,
    }


def get_speech_speed_graph_data(
    transcript: str,
    duration: float,
    language: str = "ko"
) -> Dict:
    """말 속도 그래프 데이터 (간편 함수)"""
    analyzer = SpeechSpeedAnalyzer(language)
    result = analyzer.analyze(transcript, duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "speeds": [p.value for p in result.timeline],
        "timeline": [
            {"timestamp": p.timestamp, "wpm": p.value, "label": p.label}
            for p in result.timeline
        ],
        "average_wpm": result.average_wpm,
        "optimal_range": result.optimal_range,
        "fast_segments": result.fast_segments,
        "slow_segments": result.slow_segments,
    }


def get_tone_graph_data(
    duration: float = 60,
    pitch_data: Optional[List[float]] = None
) -> Dict:
    """톤 변화 그래프 데이터 (간편 함수)"""
    analyzer = ToneAnalyzer()
    result = analyzer.analyze(pitch_data, duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "pitches": [p.value for p in result.timeline],
        "timeline": [
            {"timestamp": p.timestamp, "pitch": p.value, "label": p.label}
            for p in result.timeline
        ],
        "average_pitch": result.average_pitch,
        "pitch_range": result.pitch_range,
        "pattern": result.tone_pattern.value,
        "high_segments": result.high_pitch_segments,
        "low_segments": result.low_pitch_segments,
    }


def get_volume_graph_data(
    duration: float = 60,
    volume_data: Optional[List[float]] = None
) -> Dict:
    """음량 그래프 데이터 (간편 함수)"""
    analyzer = VolumeAnalyzer()
    result = analyzer.analyze(volume_data, duration)

    return {
        "timestamps": [p.timestamp for p in result.timeline],
        "volumes": [p.value for p in result.timeline],
        "timeline": [
            {"timestamp": p.timestamp, "db": p.value, "label": p.label}
            for p in result.timeline
        ],
        "average_db": result.average_db,
        "volume_range": result.volume_range,
        "level": result.volume_level.value,
        "quiet_segments": result.quiet_segments,
        "loud_segments": result.loud_segments,
    }


def get_silence_analysis(
    duration: float = 60,
    silence_segments: Optional[List[Dict]] = None
) -> Dict:
    """침묵 분석 (간편 함수)"""
    analyzer = SilenceAnalyzer()
    result = analyzer.analyze(silence_segments, duration)

    return {
        "total_silence": result.total_silence_duration,
        "ratio": result.silence_ratio,
        "silence_ratio": result.silence_ratio,
        "pause_count": result.silence_count,
        "natural_pauses": result.natural_pauses,
        "hesitations": result.hesitations,
        "long_pauses": result.long_pauses,
        "quality_score": result.pause_quality_score,
        "feedback": result.feedback,
        "tips": result.improvement_tips,
    }
