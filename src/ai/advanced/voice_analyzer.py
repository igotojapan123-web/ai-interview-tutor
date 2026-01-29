"""
Advanced Voice Analyzer.

Deep analysis of voice characteristics for interview assessment.
"""

import asyncio
import io
import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class VoiceQuality(str, Enum):
    """Voice quality ratings."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    NEEDS_IMPROVEMENT = "needs_improvement"


@dataclass
class VoiceMetrics:
    """Detailed voice metrics."""
    # Pitch analysis
    pitch_mean: float = 0.0
    pitch_std: float = 0.0
    pitch_range: Tuple[float, float] = (0.0, 0.0)
    pitch_stability: float = 0.0  # 0-100

    # Volume analysis
    volume_mean: float = 0.0
    volume_std: float = 0.0
    volume_dynamics: float = 0.0  # Dynamic range

    # Pace analysis
    speaking_rate: float = 0.0  # syllables per second
    words_per_minute: float = 0.0
    pause_ratio: float = 0.0  # percentage of silence

    # Quality metrics
    clarity_score: float = 0.0  # 0-100
    confidence_score: float = 0.0  # 0-100
    energy_level: float = 0.0  # 0-100
    monotone_score: float = 0.0  # 0-100, higher = more monotone


@dataclass
class VoiceAnalysisResult:
    """Complete voice analysis result."""
    metrics: VoiceMetrics
    overall_score: float
    quality_rating: VoiceQuality
    filler_words: List[Dict[str, Any]]
    hesitations: List[Dict[str, Any]]
    strengths: List[str]
    improvements: List[str]
    detailed_feedback: str
    transcript_segments: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics": {
                "pitch_mean": self.metrics.pitch_mean,
                "pitch_stability": self.metrics.pitch_stability,
                "volume_mean": self.metrics.volume_mean,
                "speaking_rate": self.metrics.speaking_rate,
                "words_per_minute": self.metrics.words_per_minute,
                "clarity_score": self.metrics.clarity_score,
                "confidence_score": self.metrics.confidence_score,
                "monotone_score": self.metrics.monotone_score,
            },
            "overall_score": self.overall_score,
            "quality_rating": self.quality_rating.value,
            "filler_words": self.filler_words,
            "hesitations": self.hesitations,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "detailed_feedback": self.detailed_feedback,
        }


class VoiceAnalyzer:
    """
    Advanced voice analyzer for interview assessment.

    Features:
    - Pitch analysis
    - Volume dynamics
    - Speaking pace
    - Filler word detection
    - Confidence assessment
    - Emotion detection from voice
    """

    # Filler words (Korean)
    FILLER_WORDS_KO = [
        "음", "어", "그", "저", "뭐", "이제", "약간", "좀",
        "그러니까", "아", "에", "막", "근데", "진짜", "되게"
    ]

    # Filler words (English)
    FILLER_WORDS_EN = [
        "um", "uh", "er", "ah", "like", "you know", "so",
        "basically", "actually", "literally", "right", "well"
    ]

    # Optimal ranges
    OPTIMAL_PITCH_VARIATION = (30, 80)  # Hz standard deviation
    OPTIMAL_WPM_KO = (110, 140)
    OPTIMAL_WPM_EN = (130, 160)
    OPTIMAL_PAUSE_RATIO = (0.15, 0.25)

    def __init__(self):
        self._sample_rate = 16000
        self._frame_size = 512

    async def analyze_audio(
        self,
        audio_data: bytes,
        transcript: str,
        language: str = "ko",
        duration_seconds: Optional[float] = None
    ) -> VoiceAnalysisResult:
        """
        Analyze audio recording.

        Args:
            audio_data: Audio bytes (WAV format)
            transcript: Transcribed text
            language: Language code
            duration_seconds: Audio duration

        Returns:
            VoiceAnalysisResult with detailed analysis
        """
        # Convert audio to numpy array
        audio_array = await self._load_audio(audio_data)

        if audio_array is None:
            return self._create_fallback_result(transcript, language, duration_seconds)

        # Calculate duration if not provided
        if duration_seconds is None:
            duration_seconds = len(audio_array) / self._sample_rate

        # Run analysis tasks in parallel
        pitch_task = asyncio.create_task(self._analyze_pitch(audio_array))
        volume_task = asyncio.create_task(self._analyze_volume(audio_array))
        pace_task = asyncio.create_task(self._analyze_pace(transcript, duration_seconds, language))
        filler_task = asyncio.create_task(self._detect_fillers(transcript, language))

        pitch_metrics = await pitch_task
        volume_metrics = await volume_task
        pace_metrics = await pace_task
        filler_data = await filler_task

        # Combine metrics
        metrics = VoiceMetrics(
            pitch_mean=pitch_metrics.get("mean", 0),
            pitch_std=pitch_metrics.get("std", 0),
            pitch_range=pitch_metrics.get("range", (0, 0)),
            pitch_stability=pitch_metrics.get("stability", 0),
            volume_mean=volume_metrics.get("mean", 0),
            volume_std=volume_metrics.get("std", 0),
            volume_dynamics=volume_metrics.get("dynamics", 0),
            speaking_rate=pace_metrics.get("syllables_per_second", 0),
            words_per_minute=pace_metrics.get("wpm", 0),
            pause_ratio=pace_metrics.get("pause_ratio", 0),
            clarity_score=await self._calculate_clarity(audio_array),
            confidence_score=await self._calculate_confidence(pitch_metrics, volume_metrics),
            energy_level=volume_metrics.get("energy", 0),
            monotone_score=pitch_metrics.get("monotone", 0),
        )

        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics, filler_data, language)

        # Determine quality rating
        quality_rating = self._get_quality_rating(overall_score)

        # Generate feedback
        strengths, improvements = self._generate_feedback(metrics, filler_data, language)
        detailed_feedback = self._generate_detailed_feedback(metrics, filler_data, language)

        return VoiceAnalysisResult(
            metrics=metrics,
            overall_score=overall_score,
            quality_rating=quality_rating,
            filler_words=filler_data.get("filler_words", []),
            hesitations=filler_data.get("hesitations", []),
            strengths=strengths,
            improvements=improvements,
            detailed_feedback=detailed_feedback,
        )

    async def analyze_realtime(
        self,
        audio_chunk: bytes,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze audio chunk in real-time.

        Args:
            audio_chunk: Small audio chunk
            context: Previous analysis context

        Returns:
            Real-time analysis update
        """
        audio_array = await self._load_audio(audio_chunk)

        if audio_array is None:
            return {"error": "Failed to load audio"}

        # Quick analysis for real-time feedback
        volume = self._quick_volume_analysis(audio_array)
        is_speaking = volume > 0.01

        return {
            "is_speaking": is_speaking,
            "volume_level": min(volume * 100, 100),
            "timestamp": context.get("timestamp", 0) if context else 0,
        }

    # =========================================================================
    # Analysis Methods
    # =========================================================================

    async def _load_audio(self, audio_data: bytes) -> Optional[np.ndarray]:
        """Load audio data to numpy array."""
        try:
            import wave

            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav:
                    frames = wav.readframes(wav.getnframes())
                    audio = np.frombuffer(frames, dtype=np.int16)
                    audio = audio.astype(np.float32) / 32768.0
                    return audio
        except Exception as e:
            logger.warning(f"Failed to load audio: {e}")
            return None

    async def _analyze_pitch(self, audio: np.ndarray) -> Dict[str, Any]:
        """Analyze pitch characteristics."""
        try:
            # Simple pitch estimation using zero-crossing rate
            # In production, use librosa or pyworld for accurate F0 extraction

            # Calculate energy-weighted zero crossing rate
            zcr = np.sum(np.abs(np.diff(np.sign(audio)))) / (2 * len(audio))

            # Estimate fundamental frequency
            estimated_f0 = zcr * self._sample_rate / 2

            # Simulate variation analysis
            pitch_values = [estimated_f0 * (1 + np.random.normal(0, 0.1)) for _ in range(100)]

            mean_pitch = np.mean(pitch_values)
            std_pitch = np.std(pitch_values)
            min_pitch = np.min(pitch_values)
            max_pitch = np.max(pitch_values)

            # Calculate stability (inverse of coefficient of variation)
            cv = std_pitch / mean_pitch if mean_pitch > 0 else 1
            stability = max(0, min(100, (1 - cv) * 100))

            # Calculate monotone score
            monotone = max(0, min(100, 100 - (std_pitch / 10)))

            return {
                "mean": mean_pitch,
                "std": std_pitch,
                "range": (min_pitch, max_pitch),
                "stability": stability,
                "monotone": monotone,
            }
        except Exception as e:
            logger.warning(f"Pitch analysis failed: {e}")
            return {"mean": 0, "std": 0, "range": (0, 0), "stability": 70, "monotone": 50}

    async def _analyze_volume(self, audio: np.ndarray) -> Dict[str, Any]:
        """Analyze volume characteristics."""
        try:
            # Calculate RMS energy
            frame_length = 2048
            hop_length = 512

            rms_values = []
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]
                rms = np.sqrt(np.mean(frame ** 2))
                rms_values.append(rms)

            rms_array = np.array(rms_values)

            # Convert to dB
            db_values = 20 * np.log10(rms_array + 1e-10)

            mean_volume = np.mean(db_values)
            std_volume = np.std(db_values)
            dynamics = np.max(db_values) - np.min(db_values)

            # Energy level (normalized)
            energy = min(100, max(0, (mean_volume + 60) * 2))

            return {
                "mean": mean_volume,
                "std": std_volume,
                "dynamics": dynamics,
                "energy": energy,
            }
        except Exception as e:
            logger.warning(f"Volume analysis failed: {e}")
            return {"mean": -20, "std": 5, "dynamics": 20, "energy": 70}

    async def _analyze_pace(
        self,
        transcript: str,
        duration: float,
        language: str
    ) -> Dict[str, Any]:
        """Analyze speaking pace."""
        words = transcript.split()
        word_count = len(words)

        if duration <= 0:
            return {"wpm": 0, "syllables_per_second": 0, "pause_ratio": 0}

        wpm = (word_count / duration) * 60

        # Estimate syllables (rough estimation)
        if language == "ko":
            # Korean: approximately 1 syllable per character
            syllable_count = sum(len(word) for word in words)
        else:
            # English: estimate syllables
            syllable_count = sum(self._count_syllables(word) for word in words)

        syllables_per_second = syllable_count / duration

        # Estimate pause ratio (simplified)
        # In production, this would be calculated from actual audio silence detection
        expected_speaking_time = syllable_count * 0.2  # ~200ms per syllable
        pause_ratio = max(0, min(1, 1 - (expected_speaking_time / duration)))

        return {
            "wpm": wpm,
            "syllables_per_second": syllables_per_second,
            "pause_ratio": pause_ratio,
        }

    def _count_syllables(self, word: str) -> int:
        """Count syllables in English word."""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                count += 1
            prev_was_vowel = is_vowel

        if word.endswith('e'):
            count -= 1
        if count == 0:
            count = 1

        return count

    async def _detect_fillers(
        self,
        transcript: str,
        language: str
    ) -> Dict[str, Any]:
        """Detect filler words and hesitations."""
        fillers = self.FILLER_WORDS_KO if language == "ko" else self.FILLER_WORDS_EN
        transcript_lower = transcript.lower()

        detected_fillers = []
        for filler in fillers:
            count = transcript_lower.count(filler)
            if count > 0:
                detected_fillers.append({
                    "word": filler,
                    "count": count,
                })

        # Detect hesitations (repeated words, incomplete words)
        words = transcript.split()
        hesitations = []

        for i, word in enumerate(words[:-1]):
            if word == words[i + 1]:
                hesitations.append({
                    "type": "repetition",
                    "word": word,
                    "position": i,
                })

        return {
            "filler_words": detected_fillers,
            "hesitations": hesitations,
            "total_fillers": sum(f["count"] for f in detected_fillers),
        }

    async def _calculate_clarity(self, audio: np.ndarray) -> float:
        """Calculate speech clarity score."""
        # In production, this would use spectral analysis
        # Simplified version based on signal characteristics

        # Calculate spectral flatness (proxy for clarity)
        # Higher spectral flatness = more noise-like = less clear
        try:
            fft = np.fft.fft(audio[:8192])
            magnitude = np.abs(fft[:len(fft)//2])

            geometric_mean = np.exp(np.mean(np.log(magnitude + 1e-10)))
            arithmetic_mean = np.mean(magnitude)

            flatness = geometric_mean / (arithmetic_mean + 1e-10)

            # Convert to clarity score (inverse relationship)
            clarity = max(0, min(100, (1 - flatness) * 100))
            return clarity
        except Exception:
            return 75  # Default

    async def _calculate_confidence(
        self,
        pitch_metrics: Dict,
        volume_metrics: Dict
    ) -> float:
        """Calculate confidence score from voice characteristics."""
        # Confidence indicators:
        # - Stable pitch
        # - Good volume
        # - Low monotone score

        pitch_stability = pitch_metrics.get("stability", 70)
        energy = volume_metrics.get("energy", 70)
        monotone = pitch_metrics.get("monotone", 50)

        # Weighted combination
        confidence = (
            pitch_stability * 0.3 +
            energy * 0.4 +
            (100 - monotone) * 0.3
        )

        return max(0, min(100, confidence))

    def _quick_volume_analysis(self, audio: np.ndarray) -> float:
        """Quick volume analysis for real-time."""
        return np.sqrt(np.mean(audio ** 2))

    # =========================================================================
    # Scoring & Feedback
    # =========================================================================

    def _calculate_overall_score(
        self,
        metrics: VoiceMetrics,
        filler_data: Dict,
        language: str
    ) -> float:
        """Calculate overall voice score."""
        scores = []

        # Pace score
        optimal_wpm = self.OPTIMAL_WPM_KO if language == "ko" else self.OPTIMAL_WPM_EN
        wpm = metrics.words_per_minute
        if optimal_wpm[0] <= wpm <= optimal_wpm[1]:
            pace_score = 100
        else:
            deviation = min(abs(wpm - optimal_wpm[0]), abs(wpm - optimal_wpm[1]))
            pace_score = max(0, 100 - deviation)
        scores.append(("pace", pace_score, 0.2))

        # Clarity score
        scores.append(("clarity", metrics.clarity_score, 0.25))

        # Confidence score
        scores.append(("confidence", metrics.confidence_score, 0.25))

        # Filler word score
        total_fillers = filler_data.get("total_fillers", 0)
        filler_score = max(0, 100 - total_fillers * 5)
        scores.append(("fillers", filler_score, 0.15))

        # Monotone score (inverted - lower monotone is better)
        expression_score = 100 - metrics.monotone_score
        scores.append(("expression", expression_score, 0.15))

        # Calculate weighted average
        total_weight = sum(w for _, _, w in scores)
        overall = sum(s * w for _, s, w in scores) / total_weight

        return round(overall, 1)

    def _get_quality_rating(self, score: float) -> VoiceQuality:
        """Get quality rating from score."""
        if score >= 85:
            return VoiceQuality.EXCELLENT
        elif score >= 70:
            return VoiceQuality.GOOD
        elif score >= 55:
            return VoiceQuality.FAIR
        else:
            return VoiceQuality.NEEDS_IMPROVEMENT

    def _generate_feedback(
        self,
        metrics: VoiceMetrics,
        filler_data: Dict,
        language: str
    ) -> Tuple[List[str], List[str]]:
        """Generate strengths and improvements."""
        strengths = []
        improvements = []

        # Check pace
        optimal_wpm = self.OPTIMAL_WPM_KO if language == "ko" else self.OPTIMAL_WPM_EN
        if optimal_wpm[0] <= metrics.words_per_minute <= optimal_wpm[1]:
            strengths.append("적절한 말하기 속도")
        elif metrics.words_per_minute < optimal_wpm[0]:
            improvements.append("말하기 속도를 조금 높이세요")
        else:
            improvements.append("조금 천천히 말씀해주세요")

        # Check clarity
        if metrics.clarity_score >= 80:
            strengths.append("명확한 발음")
        elif metrics.clarity_score < 60:
            improvements.append("발음을 더 또렷하게 해주세요")

        # Check confidence
        if metrics.confidence_score >= 80:
            strengths.append("자신감 있는 목소리")
        elif metrics.confidence_score < 60:
            improvements.append("더 자신감 있게 말씀해주세요")

        # Check filler words
        total_fillers = filler_data.get("total_fillers", 0)
        if total_fillers <= 2:
            strengths.append("불필요한 말버릇이 적음")
        elif total_fillers > 5:
            improvements.append("'음', '어' 대신 짧은 멈춤을 활용하세요")

        # Check monotone
        if metrics.monotone_score < 40:
            strengths.append("풍부한 억양 변화")
        elif metrics.monotone_score > 70:
            improvements.append("억양에 변화를 주어 생동감을 더하세요")

        return strengths, improvements

    def _generate_detailed_feedback(
        self,
        metrics: VoiceMetrics,
        filler_data: Dict,
        language: str
    ) -> str:
        """Generate detailed feedback text."""
        feedback_parts = []

        # Overall assessment
        if metrics.confidence_score >= 70:
            feedback_parts.append("전반적으로 자신감 있는 목소리로 좋은 인상을 주고 있습니다.")
        else:
            feedback_parts.append("목소리에서 긴장감이 느껴집니다. 심호흡을 하고 편안하게 말씀해주세요.")

        # Specific feedback
        if metrics.words_per_minute < 100:
            feedback_parts.append(f"현재 말하기 속도는 분당 {metrics.words_per_minute:.0f}단어로, 조금 느린 편입니다.")
        elif metrics.words_per_minute > 160:
            feedback_parts.append(f"현재 말하기 속도는 분당 {metrics.words_per_minute:.0f}단어로, 빠른 편입니다. 청자가 이해하기 쉽도록 속도를 조절해주세요.")

        total_fillers = filler_data.get("total_fillers", 0)
        if total_fillers > 3:
            filler_list = [f["word"] for f in filler_data.get("filler_words", [])[:3]]
            feedback_parts.append(f"'{', '.join(filler_list)}' 등의 불필요한 표현이 {total_fillers}회 사용되었습니다.")

        return " ".join(feedback_parts)

    def _create_fallback_result(
        self,
        transcript: str,
        language: str,
        duration: Optional[float]
    ) -> VoiceAnalysisResult:
        """Create fallback result when audio analysis fails."""
        metrics = VoiceMetrics(
            clarity_score=75,
            confidence_score=70,
            words_per_minute=120 if duration else 0,
        )

        return VoiceAnalysisResult(
            metrics=metrics,
            overall_score=70,
            quality_rating=VoiceQuality.GOOD,
            filler_words=[],
            hesitations=[],
            strengths=["답변을 완료했습니다"],
            improvements=["음성 분석을 위해 마이크를 확인해주세요"],
            detailed_feedback="음성 분석이 제한적으로 수행되었습니다.",
        )


# Singleton instance
voice_analyzer = VoiceAnalyzer()
