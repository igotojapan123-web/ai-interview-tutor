"""
Speech Analyzer.

Analyzes speech patterns, pronunciation, and delivery.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SpeechMetric(str, Enum):
    """Speech analysis metrics."""
    PACE = "pace"  # Speaking speed
    CLARITY = "clarity"  # Pronunciation clarity
    FILLER_WORDS = "filler_words"  # Um, uh, etc.
    VOLUME = "volume"  # Speaking volume
    PITCH_VARIATION = "pitch_variation"  # Monotone vs varied
    PAUSES = "pauses"  # Strategic pauses


@dataclass
class SpeechAnalysis:
    """Result of speech analysis."""
    metrics: Dict[SpeechMetric, float]
    filler_word_count: int
    filler_words_detected: List[str]
    average_pace: float  # words per minute
    total_pause_time: float  # seconds
    recommendations: List[str]
    overall_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics": {k.value: v for k, v in self.metrics.items()},
            "filler_word_count": self.filler_word_count,
            "filler_words_detected": self.filler_words_detected,
            "average_pace": self.average_pace,
            "total_pause_time": self.total_pause_time,
            "recommendations": self.recommendations,
            "overall_score": self.overall_score
        }


class SpeechAnalyzer:
    """
    Analyzes speech patterns and delivery.

    Note: Full audio analysis requires additional audio processing libraries.
    This implementation provides text-based analysis and scoring.
    """

    # Korean filler words
    FILLER_WORDS_KO = [
        "음", "어", "그", "저", "그러니까", "뭐", "이제", "약간",
        "진짜", "좀", "아", "에", "막", "근데", "그래서"
    ]

    # English filler words
    FILLER_WORDS_EN = [
        "um", "uh", "like", "you know", "so", "basically",
        "actually", "literally", "right", "well"
    ]

    # Optimal speaking pace (words per minute)
    OPTIMAL_PACE_MIN = 120
    OPTIMAL_PACE_MAX = 150

    def __init__(self):
        self._all_fillers = self.FILLER_WORDS_KO + self.FILLER_WORDS_EN

    async def analyze_text(
        self,
        text: str,
        duration_seconds: float,
        language: str = "ko"
    ) -> SpeechAnalysis:
        """
        Analyze speech from transcribed text.

        Args:
            text: Transcribed speech text
            duration_seconds: Duration of speech
            language: Language code (ko, en)

        Returns:
            SpeechAnalysis with metrics and recommendations
        """
        # Count words
        words = text.split()
        word_count = len(words)

        # Calculate pace
        if duration_seconds > 0:
            pace = (word_count / duration_seconds) * 60  # WPM
        else:
            pace = 0

        # Detect filler words
        filler_words = self._detect_fillers(text, language)
        filler_count = len(filler_words)

        # Calculate metrics
        metrics = self._calculate_metrics(
            word_count, duration_seconds, pace, filler_count
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            metrics, pace, filler_count
        )

        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)

        return SpeechAnalysis(
            metrics=metrics,
            filler_word_count=filler_count,
            filler_words_detected=filler_words,
            average_pace=pace,
            total_pause_time=0,  # Would need audio for accurate measurement
            recommendations=recommendations,
            overall_score=overall_score
        )

    def _detect_fillers(self, text: str, language: str) -> List[str]:
        """Detect filler words in text."""
        text_lower = text.lower()
        detected = []

        fillers = self.FILLER_WORDS_KO if language == "ko" else self.FILLER_WORDS_EN

        for filler in fillers:
            count = text_lower.count(filler)
            if count > 0:
                detected.extend([filler] * count)

        return detected

    def _calculate_metrics(
        self,
        word_count: int,
        duration: float,
        pace: float,
        filler_count: int
    ) -> Dict[SpeechMetric, float]:
        """Calculate speech metrics."""
        # Pace score
        if self.OPTIMAL_PACE_MIN <= pace <= self.OPTIMAL_PACE_MAX:
            pace_score = 100
        elif pace < self.OPTIMAL_PACE_MIN:
            pace_score = max(50, 100 - (self.OPTIMAL_PACE_MIN - pace))
        else:
            pace_score = max(50, 100 - (pace - self.OPTIMAL_PACE_MAX))

        # Filler word score (deduct points for excessive fillers)
        filler_ratio = filler_count / max(word_count, 1) * 100
        if filler_ratio < 2:
            filler_score = 100
        elif filler_ratio < 5:
            filler_score = 80
        elif filler_ratio < 10:
            filler_score = 60
        else:
            filler_score = 40

        return {
            SpeechMetric.PACE: pace_score,
            SpeechMetric.FILLER_WORDS: filler_score,
            SpeechMetric.CLARITY: 75,  # Placeholder - needs audio
            SpeechMetric.VOLUME: 75,  # Placeholder - needs audio
            SpeechMetric.PITCH_VARIATION: 75,  # Placeholder - needs audio
            SpeechMetric.PAUSES: 75  # Placeholder - needs audio
        }

    def _generate_recommendations(
        self,
        metrics: Dict[SpeechMetric, float],
        pace: float,
        filler_count: int
    ) -> List[str]:
        """Generate recommendations based on metrics."""
        recommendations = []

        # Pace recommendations
        if pace < self.OPTIMAL_PACE_MIN:
            recommendations.append(
                f"말하는 속도가 느립니다 ({pace:.0f} WPM). "
                f"적절한 속도는 {self.OPTIMAL_PACE_MIN}-{self.OPTIMAL_PACE_MAX} WPM입니다."
            )
        elif pace > self.OPTIMAL_PACE_MAX:
            recommendations.append(
                f"말하는 속도가 빠릅니다 ({pace:.0f} WPM). "
                "청자가 이해하기 쉽도록 천천히 말해보세요."
            )

        # Filler word recommendations
        if filler_count > 3:
            recommendations.append(
                f"불필요한 말버릇이 {filler_count}회 감지되었습니다. "
                "'음', '어' 대신 짧은 멈춤을 활용해보세요."
            )

        # General recommendations
        if not recommendations:
            recommendations.append("전반적으로 좋은 전달력을 보여주고 있습니다.")

        recommendations.append("거울 앞에서 연습하며 표정과 제스처도 확인해보세요.")

        return recommendations

    def _calculate_overall_score(
        self,
        metrics: Dict[SpeechMetric, float]
    ) -> float:
        """Calculate overall speech score."""
        weights = {
            SpeechMetric.PACE: 0.25,
            SpeechMetric.FILLER_WORDS: 0.25,
            SpeechMetric.CLARITY: 0.20,
            SpeechMetric.VOLUME: 0.10,
            SpeechMetric.PITCH_VARIATION: 0.10,
            SpeechMetric.PAUSES: 0.10
        }

        return sum(
            metrics.get(metric, 70) * weight
            for metric, weight in weights.items()
        )

    async def analyze_pronunciation(
        self,
        text: str,
        expected_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze pronunciation accuracy.

        Note: Full implementation would require audio comparison.
        This provides text-based estimation.
        """
        if not expected_text:
            return {
                "accuracy": 100,
                "errors": [],
                "suggestions": []
            }

        # Simple text similarity
        expected_words = set(expected_text.lower().split())
        actual_words = set(text.lower().split())

        common = expected_words & actual_words
        accuracy = len(common) / max(len(expected_words), 1) * 100

        errors = list(expected_words - actual_words)

        return {
            "accuracy": accuracy,
            "errors": errors[:5],  # Top 5 errors
            "suggestions": [
                "발음이 불명확한 단어는 천천히 또박또박 연습해보세요."
            ] if errors else []
        }


# Singleton instance
speech_analyzer = SpeechAnalyzer()
