"""
Emotion Detection Module.

AI-powered emotion recognition for interview analysis.
Detects emotions from facial expressions, voice tone, and text.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class Emotion(Enum):
    """Primary emotions detected during interviews."""

    # Basic emotions
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"

    # Interview-specific emotions
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    EXCITED = "excited"
    CONFUSED = "confused"
    FOCUSED = "focused"
    STRESSED = "stressed"
    CALM = "calm"
    ENTHUSIASTIC = "enthusiastic"


@dataclass
class EmotionScore:
    """Score for a single emotion."""

    emotion: Emotion
    confidence: float  # 0.0 to 1.0
    intensity: float  # 0.0 to 1.0
    source: str  # 'facial', 'voice', 'text', 'combined'


@dataclass
class EmotionTransition:
    """Represents an emotion change over time."""

    from_emotion: Emotion
    to_emotion: Emotion
    timestamp: datetime
    trigger: Optional[str] = None  # What might have caused the change


@dataclass
class EmotionAnalysisResult:
    """Complete emotion analysis result."""

    # Primary detected emotion
    primary_emotion: Emotion
    primary_confidence: float

    # All emotion scores
    emotion_scores: Dict[Emotion, float] = field(default_factory=dict)

    # Source-specific emotions
    facial_emotion: Optional[Emotion] = None
    facial_confidence: float = 0.0
    voice_emotion: Optional[Emotion] = None
    voice_confidence: float = 0.0
    text_emotion: Optional[Emotion] = None
    text_confidence: float = 0.0

    # Emotional state metrics
    valence: float = 0.0  # Positive/negative (-1 to 1)
    arousal: float = 0.0  # Calm/excited (0 to 1)
    dominance: float = 0.0  # Submissive/dominant (0 to 1)

    # Interview-specific metrics
    stress_level: float = 0.0  # 0 to 1
    confidence_level: float = 0.0  # 0 to 1
    engagement_level: float = 0.0  # 0 to 1

    # Temporal analysis
    emotion_stability: float = 0.0  # 0 to 1 (how stable emotions are)
    transitions: List[EmotionTransition] = field(default_factory=list)

    # Recommendations
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "primary_emotion": self.primary_emotion.value,
            "primary_confidence": round(self.primary_confidence, 3),
            "emotion_scores": {
                e.value: round(s, 3)
                for e, s in self.emotion_scores.items()
            },
            "facial": {
                "emotion": self.facial_emotion.value if self.facial_emotion else None,
                "confidence": round(self.facial_confidence, 3),
            },
            "voice": {
                "emotion": self.voice_emotion.value if self.voice_emotion else None,
                "confidence": round(self.voice_confidence, 3),
            },
            "text": {
                "emotion": self.text_emotion.value if self.text_emotion else None,
                "confidence": round(self.text_confidence, 3),
            },
            "metrics": {
                "valence": round(self.valence, 3),
                "arousal": round(self.arousal, 3),
                "dominance": round(self.dominance, 3),
            },
            "interview_metrics": {
                "stress_level": round(self.stress_level, 3),
                "confidence_level": round(self.confidence_level, 3),
                "engagement_level": round(self.engagement_level, 3),
            },
            "emotion_stability": round(self.emotion_stability, 3),
            "transitions": [
                {
                    "from": t.from_emotion.value,
                    "to": t.to_emotion.value,
                    "timestamp": t.timestamp.isoformat(),
                    "trigger": t.trigger,
                }
                for t in self.transitions
            ],
            "suggestions": self.suggestions,
        }


class EmotionDetector:
    """
    Multi-modal emotion detection for interview analysis.

    Combines facial expression analysis, voice tone analysis,
    and text sentiment to provide comprehensive emotion detection.
    """

    # Emotion to VAD (Valence, Arousal, Dominance) mapping
    EMOTION_VAD = {
        Emotion.NEUTRAL: (0.0, 0.0, 0.5),
        Emotion.HAPPY: (0.8, 0.5, 0.6),
        Emotion.SAD: (-0.6, -0.3, 0.3),
        Emotion.ANGRY: (-0.5, 0.8, 0.8),
        Emotion.FEARFUL: (-0.7, 0.6, 0.2),
        Emotion.SURPRISED: (0.2, 0.8, 0.5),
        Emotion.DISGUSTED: (-0.6, 0.3, 0.6),
        Emotion.CONFIDENT: (0.6, 0.4, 0.8),
        Emotion.NERVOUS: (-0.3, 0.6, 0.3),
        Emotion.EXCITED: (0.7, 0.8, 0.6),
        Emotion.CONFUSED: (-0.2, 0.3, 0.3),
        Emotion.FOCUSED: (0.3, 0.5, 0.6),
        Emotion.STRESSED: (-0.4, 0.7, 0.4),
        Emotion.CALM: (0.4, -0.2, 0.5),
        Emotion.ENTHUSIASTIC: (0.8, 0.7, 0.7),
    }

    # Facial action units to emotion mapping
    FACIAL_AU_EMOTIONS = {
        # AU combinations that indicate emotions
        frozenset([1, 2, 5, 26]): Emotion.SURPRISED,  # Brow raise + jaw drop
        frozenset([6, 12]): Emotion.HAPPY,  # Cheek raise + lip corner pull
        frozenset([1, 4, 15]): Emotion.SAD,  # Inner brow raise + brow lower + lip corner depress
        frozenset([4, 5, 7, 23]): Emotion.ANGRY,  # Brow lower + lid raise + lid tight + lip tight
        frozenset([1, 2, 4, 5, 20, 26]): Emotion.FEARFUL,  # Various fear indicators
        frozenset([9, 15, 16]): Emotion.DISGUSTED,  # Nose wrinkle + lip depress
    }

    # Text sentiment keywords
    EMOTION_KEYWORDS = {
        Emotion.CONFIDENT: [
            "confident", "sure", "certain", "definitely", "absolutely",
            "believe", "convinced", "positive", "experienced", "capable",
        ],
        Emotion.NERVOUS: [
            "um", "uh", "nervous", "worried", "anxious", "unsure",
            "maybe", "perhaps", "i think", "i guess", "not sure",
        ],
        Emotion.ENTHUSIASTIC: [
            "excited", "love", "passionate", "eager", "thrilled",
            "amazing", "fantastic", "great opportunity", "really want",
        ],
        Emotion.CONFUSED: [
            "confused", "don't understand", "unclear", "what do you mean",
            "could you explain", "sorry", "repeat", "clarify",
        ],
        Emotion.STRESSED: [
            "pressure", "stressed", "difficult", "challenging", "hard",
            "struggle", "overwhelmed", "tough", "demanding",
        ],
    }

    def __init__(self):
        """Initialize emotion detector."""
        self._emotion_history: Dict[str, List[Tuple[datetime, Emotion, float]]] = {}
        self._session_baselines: Dict[str, Dict[str, float]] = {}

    async def detect_emotion(
        self,
        session_id: str,
        facial_features: Optional[Dict[str, Any]] = None,
        voice_features: Optional[Dict[str, Any]] = None,
        text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> EmotionAnalysisResult:
        """
        Detect emotions from multiple modalities.

        Args:
            session_id: Session identifier for temporal tracking
            facial_features: Facial analysis data (landmarks, AUs, etc.)
            voice_features: Voice analysis data (pitch, energy, etc.)
            text: Transcript text for sentiment analysis
            context: Additional context (question type, time elapsed, etc.)

        Returns:
            Comprehensive emotion analysis result
        """
        # Analyze each modality
        facial_result = await self._analyze_facial(facial_features)
        voice_result = await self._analyze_voice(voice_features)
        text_result = await self._analyze_text(text)

        # Combine results with weighted fusion
        combined = await self._fuse_emotions(
            facial_result,
            voice_result,
            text_result,
            context,
        )

        # Track emotion history
        self._update_history(session_id, combined)

        # Analyze temporal patterns
        transitions = self._analyze_transitions(session_id)
        stability = self._calculate_stability(session_id)

        # Calculate interview-specific metrics
        stress = self._calculate_stress(combined, voice_result)
        confidence = self._calculate_confidence(combined, voice_result, text_result)
        engagement = self._calculate_engagement(combined, facial_result, voice_result)

        # Generate suggestions
        suggestions = self._generate_suggestions(
            combined["primary"],
            stress,
            confidence,
            engagement,
            context,
        )

        # Get VAD values
        valence, arousal, dominance = self._calculate_vad(combined)

        result = EmotionAnalysisResult(
            primary_emotion=combined["primary"],
            primary_confidence=combined["confidence"],
            emotion_scores=combined["scores"],
            facial_emotion=facial_result.get("emotion"),
            facial_confidence=facial_result.get("confidence", 0.0),
            voice_emotion=voice_result.get("emotion"),
            voice_confidence=voice_result.get("confidence", 0.0),
            text_emotion=text_result.get("emotion"),
            text_confidence=text_result.get("confidence", 0.0),
            valence=valence,
            arousal=arousal,
            dominance=dominance,
            stress_level=stress,
            confidence_level=confidence,
            engagement_level=engagement,
            emotion_stability=stability,
            transitions=transitions,
            suggestions=suggestions,
        )

        logger.debug(
            f"Emotion detected: {result.primary_emotion.value} "
            f"(confidence: {result.primary_confidence:.2f})"
        )

        return result

    async def _analyze_facial(
        self,
        features: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze facial features for emotion detection."""
        if not features:
            return {"emotion": None, "confidence": 0.0, "scores": {}}

        scores = {}

        # Analyze facial action units if available
        if "action_units" in features:
            aus = set(features["action_units"])
            for au_set, emotion in self.FACIAL_AU_EMOTIONS.items():
                overlap = len(aus & au_set) / len(au_set)
                if overlap > 0:
                    scores[emotion] = scores.get(emotion, 0.0) + overlap * 0.5

        # Analyze facial landmarks geometry
        if "landmarks" in features:
            # Mouth shape analysis
            mouth_ratio = features.get("mouth_aspect_ratio", 0.5)
            if mouth_ratio > 0.6:  # Open mouth
                scores[Emotion.SURPRISED] = scores.get(Emotion.SURPRISED, 0.0) + 0.3
            elif mouth_ratio > 0.3:  # Slight smile
                scores[Emotion.HAPPY] = scores.get(Emotion.HAPPY, 0.0) + 0.2

            # Eye analysis
            eye_openness = features.get("eye_aspect_ratio", 0.3)
            if eye_openness > 0.35:
                scores[Emotion.SURPRISED] = scores.get(Emotion.SURPRISED, 0.0) + 0.2
            elif eye_openness < 0.2:
                scores[Emotion.FOCUSED] = scores.get(Emotion.FOCUSED, 0.0) + 0.2

            # Brow analysis
            brow_height = features.get("brow_height", 0.5)
            if brow_height > 0.6:
                scores[Emotion.SURPRISED] = scores.get(Emotion.SURPRISED, 0.0) + 0.2
            elif brow_height < 0.4:
                scores[Emotion.FOCUSED] = scores.get(Emotion.FOCUSED, 0.0) + 0.15
                scores[Emotion.ANGRY] = scores.get(Emotion.ANGRY, 0.0) + 0.1

        # Direct emotion predictions if available (from ML model)
        if "emotion_predictions" in features:
            for emotion_str, prob in features["emotion_predictions"].items():
                try:
                    emotion = Emotion(emotion_str.lower())
                    scores[emotion] = scores.get(emotion, 0.0) + prob * 0.8
                except ValueError:
                    continue

        # Default to neutral if no signals
        if not scores:
            scores[Emotion.NEUTRAL] = 0.5

        # Normalize scores
        total = sum(scores.values())
        if total > 0:
            scores = {e: s / total for e, s in scores.items()}

        # Get primary emotion
        primary = max(scores.items(), key=lambda x: x[1])

        return {
            "emotion": primary[0],
            "confidence": primary[1],
            "scores": scores,
        }

    async def _analyze_voice(
        self,
        features: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze voice features for emotion detection."""
        if not features:
            return {"emotion": None, "confidence": 0.0, "scores": {}}

        scores = {}

        # Pitch analysis
        pitch_mean = features.get("pitch_mean", 150)
        pitch_std = features.get("pitch_std", 30)
        pitch_range = features.get("pitch_range", 100)

        # High pitch variation often indicates excitement or nervousness
        if pitch_std > 50:
            scores[Emotion.EXCITED] = 0.3
            scores[Emotion.NERVOUS] = 0.2
        elif pitch_std < 20:
            scores[Emotion.CALM] = 0.3
            scores[Emotion.NEUTRAL] = 0.2

        # Energy/volume analysis
        energy_mean = features.get("energy_mean", 0.5)
        energy_std = features.get("energy_std", 0.1)

        if energy_mean > 0.7:
            scores[Emotion.EXCITED] = scores.get(Emotion.EXCITED, 0.0) + 0.2
            scores[Emotion.CONFIDENT] = scores.get(Emotion.CONFIDENT, 0.0) + 0.2
        elif energy_mean < 0.3:
            scores[Emotion.SAD] = scores.get(Emotion.SAD, 0.0) + 0.2
            scores[Emotion.NERVOUS] = scores.get(Emotion.NERVOUS, 0.0) + 0.15

        # Speech rate analysis
        speech_rate = features.get("speech_rate", 150)  # words per minute

        if speech_rate > 180:
            scores[Emotion.NERVOUS] = scores.get(Emotion.NERVOUS, 0.0) + 0.3
            scores[Emotion.EXCITED] = scores.get(Emotion.EXCITED, 0.0) + 0.2
        elif speech_rate < 100:
            scores[Emotion.CALM] = scores.get(Emotion.CALM, 0.0) + 0.2
            scores[Emotion.SAD] = scores.get(Emotion.SAD, 0.0) + 0.1

        # Pause analysis
        pause_ratio = features.get("pause_ratio", 0.2)

        if pause_ratio > 0.4:
            scores[Emotion.NERVOUS] = scores.get(Emotion.NERVOUS, 0.0) + 0.2
            scores[Emotion.CONFUSED] = scores.get(Emotion.CONFUSED, 0.0) + 0.15

        # Voice quality analysis
        jitter = features.get("jitter", 0.02)
        shimmer = features.get("shimmer", 0.03)

        if jitter > 0.05 or shimmer > 0.1:
            scores[Emotion.STRESSED] = scores.get(Emotion.STRESSED, 0.0) + 0.3
            scores[Emotion.NERVOUS] = scores.get(Emotion.NERVOUS, 0.0) + 0.2

        # Spectral features
        spectral_centroid = features.get("spectral_centroid", 2000)

        if spectral_centroid > 3000:
            scores[Emotion.EXCITED] = scores.get(Emotion.EXCITED, 0.0) + 0.15
        elif spectral_centroid < 1500:
            scores[Emotion.SAD] = scores.get(Emotion.SAD, 0.0) + 0.15

        # Default to neutral if no signals
        if not scores:
            scores[Emotion.NEUTRAL] = 0.5

        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {e: s / total for e, s in scores.items()}

        primary = max(scores.items(), key=lambda x: x[1])

        return {
            "emotion": primary[0],
            "confidence": primary[1],
            "scores": scores,
        }

    async def _analyze_text(
        self,
        text: Optional[str],
    ) -> Dict[str, Any]:
        """Analyze text for emotional content."""
        if not text:
            return {"emotion": None, "confidence": 0.0, "scores": {}}

        text_lower = text.lower()
        scores = {}

        # Keyword-based emotion detection
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            keyword_count = sum(1 for kw in keywords if kw in text_lower)
            if keyword_count > 0:
                # Scale based on keyword frequency
                score = min(keyword_count * 0.15, 0.6)
                scores[emotion] = score

        # Analyze sentence structure
        words = text.split()
        word_count = len(words)

        # Short, incomplete sentences may indicate nervousness
        if word_count < 5:
            scores[Emotion.NERVOUS] = scores.get(Emotion.NERVOUS, 0.0) + 0.1

        # Long, detailed responses indicate confidence
        if word_count > 50:
            scores[Emotion.CONFIDENT] = scores.get(Emotion.CONFIDENT, 0.0) + 0.15

        # Exclamation marks indicate excitement
        exclamation_count = text.count("!")
        if exclamation_count > 0:
            scores[Emotion.EXCITED] = scores.get(Emotion.EXCITED, 0.0) + min(exclamation_count * 0.1, 0.3)
            scores[Emotion.ENTHUSIASTIC] = scores.get(Emotion.ENTHUSIASTIC, 0.0) + min(exclamation_count * 0.1, 0.2)

        # Question marks may indicate confusion
        question_count = text.count("?")
        if question_count > 1:
            scores[Emotion.CONFUSED] = scores.get(Emotion.CONFUSED, 0.0) + 0.1

        # Hedging language
        hedging = ["maybe", "perhaps", "i think", "sort of", "kind of", "possibly"]
        hedge_count = sum(1 for h in hedging if h in text_lower)
        if hedge_count > 0:
            scores[Emotion.NERVOUS] = scores.get(Emotion.NERVOUS, 0.0) + hedge_count * 0.08

        # Power language
        power_words = ["will", "can", "definitely", "absolutely", "always", "i am"]
        power_count = sum(1 for pw in power_words if pw in text_lower)
        if power_count > 0:
            scores[Emotion.CONFIDENT] = scores.get(Emotion.CONFIDENT, 0.0) + power_count * 0.08

        # Default to neutral
        if not scores:
            scores[Emotion.NEUTRAL] = 0.5

        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {e: s / total for e, s in scores.items()}

        primary = max(scores.items(), key=lambda x: x[1])

        return {
            "emotion": primary[0],
            "confidence": primary[1],
            "scores": scores,
        }

    async def _fuse_emotions(
        self,
        facial: Dict[str, Any],
        voice: Dict[str, Any],
        text: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Fuse emotions from multiple modalities."""
        # Modality weights (can be adjusted based on reliability)
        weights = {
            "facial": 0.4,  # Facial expressions are very reliable
            "voice": 0.35,  # Voice features are good indicators
            "text": 0.25,  # Text provides context but less immediate
        }

        # Adjust weights based on availability and confidence
        available_weight = 0.0
        if facial.get("confidence", 0) > 0:
            available_weight += weights["facial"]
        else:
            weights["facial"] = 0

        if voice.get("confidence", 0) > 0:
            available_weight += weights["voice"]
        else:
            weights["voice"] = 0

        if text.get("confidence", 0) > 0:
            available_weight += weights["text"]
        else:
            weights["text"] = 0

        # Normalize weights
        if available_weight > 0:
            weights = {k: v / available_weight for k, v in weights.items()}

        # Combine scores
        combined_scores: Dict[Emotion, float] = {}

        for source, source_data in [("facial", facial), ("voice", voice), ("text", text)]:
            if weights[source] > 0:
                for emotion, score in source_data.get("scores", {}).items():
                    weighted_score = score * weights[source] * source_data.get("confidence", 1.0)
                    combined_scores[emotion] = combined_scores.get(emotion, 0.0) + weighted_score

        # Apply context adjustments
        if context:
            question_type = context.get("question_type", "")
            time_elapsed = context.get("time_elapsed", 0)

            # Technical questions may increase stress/confusion
            if question_type == "technical":
                combined_scores[Emotion.STRESSED] = combined_scores.get(Emotion.STRESSED, 0.0) + 0.05
                combined_scores[Emotion.FOCUSED] = combined_scores.get(Emotion.FOCUSED, 0.0) + 0.05

            # Long elapsed time may increase nervousness
            if time_elapsed > 60:  # More than 1 minute
                combined_scores[Emotion.NERVOUS] = combined_scores.get(Emotion.NERVOUS, 0.0) + 0.05

        # Default to neutral if no emotions detected
        if not combined_scores:
            combined_scores[Emotion.NEUTRAL] = 1.0

        # Normalize
        total = sum(combined_scores.values())
        if total > 0:
            combined_scores = {e: s / total for e, s in combined_scores.items()}

        # Get primary emotion
        primary = max(combined_scores.items(), key=lambda x: x[1])

        return {
            "primary": primary[0],
            "confidence": primary[1],
            "scores": combined_scores,
        }

    def _update_history(
        self,
        session_id: str,
        combined: Dict[str, Any],
    ) -> None:
        """Update emotion history for temporal analysis."""
        if session_id not in self._emotion_history:
            self._emotion_history[session_id] = []

        self._emotion_history[session_id].append((
            datetime.now(),
            combined["primary"],
            combined["confidence"],
        ))

        # Keep last 100 entries per session
        if len(self._emotion_history[session_id]) > 100:
            self._emotion_history[session_id] = self._emotion_history[session_id][-100:]

    def _analyze_transitions(
        self,
        session_id: str,
    ) -> List[EmotionTransition]:
        """Analyze emotion transitions over time."""
        history = self._emotion_history.get(session_id, [])
        if len(history) < 2:
            return []

        transitions = []
        prev_emotion = history[0][1]

        for timestamp, emotion, confidence in history[1:]:
            if emotion != prev_emotion and confidence > 0.5:
                transitions.append(EmotionTransition(
                    from_emotion=prev_emotion,
                    to_emotion=emotion,
                    timestamp=timestamp,
                ))
                prev_emotion = emotion

        return transitions[-10:]  # Return last 10 transitions

    def _calculate_stability(self, session_id: str) -> float:
        """Calculate emotional stability (lower transitions = higher stability)."""
        history = self._emotion_history.get(session_id, [])
        if len(history) < 5:
            return 0.5  # Not enough data

        # Count unique emotions in recent history
        recent = history[-20:]
        emotions = [e[1] for e in recent]
        unique_emotions = len(set(emotions))

        # Count transitions
        transitions = sum(1 for i in range(1, len(emotions)) if emotions[i] != emotions[i-1])

        # Higher stability = fewer transitions and fewer unique emotions
        transition_ratio = 1 - (transitions / (len(emotions) - 1))
        uniqueness_ratio = 1 - (unique_emotions / len(Emotion))

        return (transition_ratio * 0.7 + uniqueness_ratio * 0.3)

    def _calculate_stress(
        self,
        combined: Dict[str, Any],
        voice: Dict[str, Any],
    ) -> float:
        """Calculate stress level."""
        stress_emotions = [Emotion.STRESSED, Emotion.NERVOUS, Emotion.FEARFUL, Emotion.ANGRY]

        stress_score = sum(
            combined["scores"].get(e, 0.0)
            for e in stress_emotions
        )

        # Voice features can indicate stress
        if voice.get("confidence", 0) > 0:
            voice_scores = voice.get("scores", {})
            stress_score += sum(
                voice_scores.get(e, 0.0) * 0.3
                for e in stress_emotions
            )

        return min(stress_score, 1.0)

    def _calculate_confidence(
        self,
        combined: Dict[str, Any],
        voice: Dict[str, Any],
        text: Dict[str, Any],
    ) -> float:
        """Calculate confidence level."""
        confidence_emotions = [Emotion.CONFIDENT, Emotion.CALM, Emotion.FOCUSED]
        anti_confidence = [Emotion.NERVOUS, Emotion.CONFUSED, Emotion.FEARFUL]

        positive = sum(
            combined["scores"].get(e, 0.0)
            for e in confidence_emotions
        )

        negative = sum(
            combined["scores"].get(e, 0.0)
            for e in anti_confidence
        )

        # Text power language adds confidence
        if text.get("emotion") == Emotion.CONFIDENT:
            positive += text.get("confidence", 0) * 0.2

        confidence = positive - (negative * 0.5)
        return max(0.0, min(confidence + 0.5, 1.0))

    def _calculate_engagement(
        self,
        combined: Dict[str, Any],
        facial: Dict[str, Any],
        voice: Dict[str, Any],
    ) -> float:
        """Calculate engagement level."""
        engagement_emotions = [
            Emotion.EXCITED, Emotion.ENTHUSIASTIC,
            Emotion.FOCUSED, Emotion.HAPPY, Emotion.CONFIDENT,
        ]

        disengaged_emotions = [Emotion.SAD, Emotion.NEUTRAL]

        positive = sum(
            combined["scores"].get(e, 0.0)
            for e in engagement_emotions
        )

        negative = sum(
            combined["scores"].get(e, 0.0)
            for e in disengaged_emotions
        )

        engagement = positive - (negative * 0.3) + 0.5
        return max(0.0, min(engagement, 1.0))

    def _calculate_vad(
        self,
        combined: Dict[str, Any],
    ) -> Tuple[float, float, float]:
        """Calculate Valence, Arousal, Dominance values."""
        valence = 0.0
        arousal = 0.0
        dominance = 0.0

        for emotion, score in combined["scores"].items():
            if emotion in self.EMOTION_VAD:
                v, a, d = self.EMOTION_VAD[emotion]
                valence += v * score
                arousal += a * score
                dominance += d * score

        return valence, arousal, dominance

    def _generate_suggestions(
        self,
        primary_emotion: Emotion,
        stress: float,
        confidence: float,
        engagement: float,
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Generate coaching suggestions based on emotional state."""
        suggestions = []

        # High stress suggestions
        if stress > 0.6:
            suggestions.append("Take a deep breath to calm your nerves")
            suggestions.append("Remember to speak slowly and clearly")

        # Low confidence suggestions
        if confidence < 0.4:
            suggestions.append("Use more assertive language like 'I will' instead of 'I think'")
            suggestions.append("Maintain eye contact to project confidence")

        # Low engagement
        if engagement < 0.4:
            suggestions.append("Show more enthusiasm when discussing your experiences")
            suggestions.append("Vary your tone to sound more engaged")

        # Emotion-specific suggestions
        emotion_suggestions = {
            Emotion.NERVOUS: [
                "You're doing great - nervousness shows you care!",
                "Focus on your breathing between answers",
            ],
            Emotion.CONFUSED: [
                "It's okay to ask for clarification",
                "Take a moment to gather your thoughts before answering",
            ],
            Emotion.STRESSED: [
                "Remember, this is a conversation, not an interrogation",
                "You've prepared for this - trust your knowledge",
            ],
            Emotion.NEUTRAL: [
                "Try to show more emotion and enthusiasm",
                "Let your personality shine through",
            ],
        }

        if primary_emotion in emotion_suggestions:
            suggestions.extend(emotion_suggestions[primary_emotion])

        return suggestions[:5]  # Return top 5 suggestions

    def reset_session(self, session_id: str) -> None:
        """Reset emotion history for a session."""
        if session_id in self._emotion_history:
            del self._emotion_history[session_id]
        if session_id in self._session_baselines:
            del self._session_baselines[session_id]

    async def get_session_summary(
        self,
        session_id: str,
    ) -> Dict[str, Any]:
        """Get emotional summary for a session."""
        history = self._emotion_history.get(session_id, [])

        if not history:
            return {"error": "No emotion data for session"}

        # Calculate emotion distribution
        emotion_counts: Dict[Emotion, int] = {}
        for _, emotion, _ in history:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        total = len(history)
        distribution = {
            e.value: count / total
            for e, count in emotion_counts.items()
        }

        # Calculate average metrics
        transitions = self._analyze_transitions(session_id)
        stability = self._calculate_stability(session_id)

        # Determine dominant emotion
        dominant = max(emotion_counts.items(), key=lambda x: x[1])

        return {
            "session_id": session_id,
            "total_detections": total,
            "dominant_emotion": dominant[0].value,
            "dominant_percentage": dominant[1] / total,
            "emotion_distribution": distribution,
            "total_transitions": len(transitions),
            "stability_score": stability,
            "summary": self._generate_session_summary(
                dominant[0],
                stability,
                len(transitions),
            ),
        }

    def _generate_session_summary(
        self,
        dominant: Emotion,
        stability: float,
        transition_count: int,
    ) -> str:
        """Generate a natural language summary of the session."""
        stability_desc = "stable" if stability > 0.7 else "varied" if stability > 0.4 else "fluctuating"

        summaries = {
            Emotion.CONFIDENT: f"You appeared confident throughout with {stability_desc} emotional presence.",
            Emotion.NERVOUS: f"Some nervousness was detected, but this is natural in interviews. Your emotions were {stability_desc}.",
            Emotion.CALM: f"You maintained a calm demeanor with {stability_desc} emotions.",
            Emotion.FOCUSED: f"You showed good focus and concentration. Emotional state was {stability_desc}.",
            Emotion.STRESSED: f"Signs of stress were detected. Try relaxation techniques before your next practice.",
            Emotion.ENTHUSIASTIC: f"Great enthusiasm! Your energy was {stability_desc} throughout.",
            Emotion.NEUTRAL: f"You maintained a neutral expression. Consider showing more emotion to engage better.",
        }

        return summaries.get(
            dominant,
            f"Your dominant emotion was {dominant.value} with {stability_desc} emotional patterns.",
        )


# Global instance
emotion_detector = EmotionDetector()
