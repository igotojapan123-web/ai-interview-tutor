"""
Real-time Feedback Engine.

Provides instant feedback during interview practice.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of real-time feedback."""
    PACE = "pace"
    VOLUME = "volume"
    FILLER_WORD = "filler_word"
    EYE_CONTACT = "eye_contact"
    POSTURE = "posture"
    TIME_WARNING = "time_warning"
    ENCOURAGEMENT = "encouragement"
    TIP = "tip"


class FeedbackPriority(str, Enum):
    """Feedback priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FeedbackItem:
    """A single feedback item."""
    type: FeedbackType
    priority: FeedbackPriority
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    dismissed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "priority": self.priority.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


@dataclass
class SessionContext:
    """Context for a feedback session."""
    session_id: str
    user_id: str
    question: str
    time_limit: int
    start_time: datetime = field(default_factory=datetime.utcnow)
    elapsed_time: float = 0
    feedback_history: List[FeedbackItem] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class RealtimeFeedbackEngine:
    """
    Real-time feedback engine for interview practice.

    Features:
    - Audio analysis feedback (pace, volume, fillers)
    - Video analysis feedback (eye contact, posture)
    - Time management alerts
    - Encouragement and tips
    - Adaptive feedback based on user history
    """

    # Feedback thresholds
    PACE_SLOW_THRESHOLD = 100  # WPM
    PACE_FAST_THRESHOLD = 170  # WPM
    VOLUME_LOW_THRESHOLD = 0.2
    VOLUME_HIGH_THRESHOLD = 0.9
    EYE_CONTACT_THRESHOLD = 50  # percentage
    FILLER_INTERVAL = 3  # Don't alert more than once per 3 seconds for same filler

    # Time warnings (percentage of time limit)
    TIME_WARNINGS = [0.5, 0.75, 0.9, 1.0]

    def __init__(self):
        self._sessions: Dict[str, SessionContext] = {}
        self._listeners: Dict[str, List[Callable]] = {}
        self._last_filler_time: Dict[str, float] = {}

    # =========================================================================
    # Session Management
    # =========================================================================

    def create_session(
        self,
        session_id: str,
        user_id: str,
        question: str,
        time_limit: int
    ) -> SessionContext:
        """Create a new feedback session."""
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            question=question,
            time_limit=time_limit,
        )
        self._sessions[session_id] = context
        logger.info(f"Created feedback session: {session_id}")
        return context

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get session context."""
        return self._sessions.get(session_id)

    def end_session(self, session_id: str) -> Optional[SessionContext]:
        """End a feedback session."""
        session = self._sessions.pop(session_id, None)
        if session:
            logger.info(f"Ended feedback session: {session_id}")
        return session

    # =========================================================================
    # Feedback Registration
    # =========================================================================

    def register_listener(
        self,
        session_id: str,
        callback: Callable[[FeedbackItem], None]
    ) -> None:
        """Register a feedback listener."""
        if session_id not in self._listeners:
            self._listeners[session_id] = []
        self._listeners[session_id].append(callback)

    def unregister_listener(
        self,
        session_id: str,
        callback: Callable
    ) -> None:
        """Unregister a feedback listener."""
        if session_id in self._listeners:
            self._listeners[session_id] = [
                cb for cb in self._listeners[session_id] if cb != callback
            ]

    async def _emit_feedback(
        self,
        session_id: str,
        feedback: FeedbackItem
    ) -> None:
        """Emit feedback to all listeners."""
        session = self._sessions.get(session_id)
        if session:
            session.feedback_history.append(feedback)

        callbacks = self._listeners.get(session_id, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(feedback)
                else:
                    callback(feedback)
            except Exception as e:
                logger.error(f"Feedback callback error: {e}")

    # =========================================================================
    # Audio Feedback
    # =========================================================================

    async def process_audio_chunk(
        self,
        session_id: str,
        audio_data: bytes,
        transcript: Optional[str] = None,
        analysis: Optional[Dict] = None
    ) -> List[FeedbackItem]:
        """
        Process audio chunk and generate feedback.

        Args:
            session_id: Session identifier
            audio_data: Audio chunk data
            transcript: Transcribed text (if available)
            analysis: Pre-computed audio analysis

        Returns:
            List of generated feedback items
        """
        session = self._sessions.get(session_id)
        if not session:
            return []

        feedback_items = []

        # Update elapsed time
        session.elapsed_time = (datetime.utcnow() - session.start_time).total_seconds()

        # Check time warnings
        time_feedback = await self._check_time_warnings(session)
        if time_feedback:
            feedback_items.append(time_feedback)

        if analysis:
            # Check pace
            pace_feedback = await self._check_pace(session, analysis)
            if pace_feedback:
                feedback_items.append(pace_feedback)

            # Check volume
            volume_feedback = await self._check_volume(session, analysis)
            if volume_feedback:
                feedback_items.append(volume_feedback)

        # Check filler words in transcript
        if transcript:
            filler_feedback = await self._check_fillers(session, transcript)
            if filler_feedback:
                feedback_items.append(filler_feedback)

        # Emit all feedback
        for feedback in feedback_items:
            await self._emit_feedback(session_id, feedback)

        return feedback_items

    async def _check_pace(
        self,
        session: SessionContext,
        analysis: Dict
    ) -> Optional[FeedbackItem]:
        """Check speaking pace and generate feedback."""
        wpm = analysis.get("words_per_minute", 0)
        session.metrics["last_wpm"] = wpm

        # Only alert if significantly off
        if wpm > 0 and wpm < self.PACE_SLOW_THRESHOLD:
            return FeedbackItem(
                type=FeedbackType.PACE,
                priority=FeedbackPriority.MEDIUM,
                message="조금 더 빠르게 말씀해주세요",
                data={"wpm": wpm, "direction": "slow"}
            )
        elif wpm > self.PACE_FAST_THRESHOLD:
            return FeedbackItem(
                type=FeedbackType.PACE,
                priority=FeedbackPriority.HIGH,
                message="천천히 또박또박 말씀해주세요",
                data={"wpm": wpm, "direction": "fast"}
            )

        return None

    async def _check_volume(
        self,
        session: SessionContext,
        analysis: Dict
    ) -> Optional[FeedbackItem]:
        """Check volume level and generate feedback."""
        volume = analysis.get("volume_level", 0.5)
        session.metrics["last_volume"] = volume

        if volume < self.VOLUME_LOW_THRESHOLD:
            return FeedbackItem(
                type=FeedbackType.VOLUME,
                priority=FeedbackPriority.HIGH,
                message="목소리가 작습니다. 조금 더 크게 말씀해주세요",
                data={"volume": volume, "direction": "low"}
            )
        elif volume > self.VOLUME_HIGH_THRESHOLD:
            return FeedbackItem(
                type=FeedbackType.VOLUME,
                priority=FeedbackPriority.LOW,
                message="목소리가 큽니다. 조금 낮춰주세요",
                data={"volume": volume, "direction": "high"}
            )

        return None

    async def _check_fillers(
        self,
        session: SessionContext,
        transcript: str
    ) -> Optional[FeedbackItem]:
        """Check for filler words."""
        fillers = ["음", "어", "그", "저", "뭐", "um", "uh", "like"]
        transcript_lower = transcript.lower()

        current_time = session.elapsed_time

        for filler in fillers:
            if filler in transcript_lower:
                # Check cooldown
                last_time = self._last_filler_time.get(f"{session.session_id}:{filler}", 0)
                if current_time - last_time >= self.FILLER_INTERVAL:
                    self._last_filler_time[f"{session.session_id}:{filler}"] = current_time

                    # Count total fillers
                    total = session.metrics.get("filler_count", 0) + 1
                    session.metrics["filler_count"] = total

                    return FeedbackItem(
                        type=FeedbackType.FILLER_WORD,
                        priority=FeedbackPriority.LOW,
                        message=f"'{filler}' 대신 잠시 멈춤을 활용해보세요",
                        data={"filler": filler, "count": total}
                    )

        return None

    async def _check_time_warnings(
        self,
        session: SessionContext
    ) -> Optional[FeedbackItem]:
        """Check time and generate warnings."""
        if session.time_limit <= 0:
            return None

        progress = session.elapsed_time / session.time_limit
        warned_at = session.metrics.get("time_warnings_given", [])

        for threshold in self.TIME_WARNINGS:
            if progress >= threshold and threshold not in warned_at:
                warned_at.append(threshold)
                session.metrics["time_warnings_given"] = warned_at

                if threshold >= 1.0:
                    return FeedbackItem(
                        type=FeedbackType.TIME_WARNING,
                        priority=FeedbackPriority.HIGH,
                        message="시간이 종료되었습니다. 답변을 마무리해주세요",
                        data={"progress": progress, "threshold": threshold}
                    )
                elif threshold >= 0.9:
                    return FeedbackItem(
                        type=FeedbackType.TIME_WARNING,
                        priority=FeedbackPriority.HIGH,
                        message="10초 남았습니다. 마무리해주세요",
                        data={"progress": progress, "threshold": threshold}
                    )
                elif threshold >= 0.75:
                    remaining = int((1 - progress) * session.time_limit)
                    return FeedbackItem(
                        type=FeedbackType.TIME_WARNING,
                        priority=FeedbackPriority.MEDIUM,
                        message=f"{remaining}초 남았습니다",
                        data={"progress": progress, "remaining": remaining}
                    )
                elif threshold >= 0.5:
                    return FeedbackItem(
                        type=FeedbackType.TIME_WARNING,
                        priority=FeedbackPriority.LOW,
                        message="절반의 시간이 지났습니다",
                        data={"progress": progress}
                    )

        return None

    # =========================================================================
    # Video Feedback
    # =========================================================================

    async def process_video_frame(
        self,
        session_id: str,
        frame_analysis: Dict[str, Any]
    ) -> List[FeedbackItem]:
        """
        Process video frame analysis and generate feedback.

        Args:
            session_id: Session identifier
            frame_analysis: Frame analysis results

        Returns:
            List of generated feedback items
        """
        session = self._sessions.get(session_id)
        if not session:
            return []

        feedback_items = []

        # Check eye contact
        eye_feedback = await self._check_eye_contact(session, frame_analysis)
        if eye_feedback:
            feedback_items.append(eye_feedback)

        # Check posture
        posture_feedback = await self._check_posture(session, frame_analysis)
        if posture_feedback:
            feedback_items.append(posture_feedback)

        # Emit feedback
        for feedback in feedback_items:
            await self._emit_feedback(session_id, feedback)

        return feedback_items

    async def _check_eye_contact(
        self,
        session: SessionContext,
        analysis: Dict
    ) -> Optional[FeedbackItem]:
        """Check eye contact and generate feedback."""
        eye_contact = analysis.get("eye_contact", 100)

        # Track eye contact over time
        history = session.metrics.get("eye_contact_history", [])
        history.append(eye_contact)
        if len(history) > 30:  # Keep last 30 samples
            history = history[-30:]
        session.metrics["eye_contact_history"] = history

        # Calculate average
        avg_eye_contact = sum(history) / len(history)

        # Alert if consistently low
        if len(history) >= 10 and avg_eye_contact < self.EYE_CONTACT_THRESHOLD:
            last_warning = session.metrics.get("last_eye_contact_warning", 0)
            if session.elapsed_time - last_warning >= 10:  # Every 10 seconds max
                session.metrics["last_eye_contact_warning"] = session.elapsed_time
                return FeedbackItem(
                    type=FeedbackType.EYE_CONTACT,
                    priority=FeedbackPriority.MEDIUM,
                    message="카메라를 바라봐주세요",
                    data={"eye_contact": avg_eye_contact}
                )

        return None

    async def _check_posture(
        self,
        session: SessionContext,
        analysis: Dict
    ) -> Optional[FeedbackItem]:
        """Check posture and generate feedback."""
        head_position = analysis.get("head_position", "centered")
        pose_score = analysis.get("pose_score", 100)

        if head_position != "centered":
            last_warning = session.metrics.get("last_posture_warning", 0)
            if session.elapsed_time - last_warning >= 15:  # Every 15 seconds max
                session.metrics["last_posture_warning"] = session.elapsed_time

                messages = {
                    "left": "카메라 중앙을 바라봐주세요 (약간 왼쪽을 보고 계세요)",
                    "right": "카메라 중앙을 바라봐주세요 (약간 오른쪽을 보고 계세요)",
                    "tilted": "고개를 바르게 해주세요",
                }

                return FeedbackItem(
                    type=FeedbackType.POSTURE,
                    priority=FeedbackPriority.LOW,
                    message=messages.get(head_position, "자세를 바르게 해주세요"),
                    data={"head_position": head_position, "score": pose_score}
                )

        return None

    # =========================================================================
    # Encouragement & Tips
    # =========================================================================

    async def send_encouragement(
        self,
        session_id: str,
        trigger: str = "general"
    ) -> Optional[FeedbackItem]:
        """Send encouraging feedback."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        messages = {
            "start": "좋아요! 자신감 있게 시작해주세요",
            "good_pace": "말하기 속도가 좋습니다!",
            "good_eye_contact": "아이컨택이 좋아요!",
            "halfway": "잘 하고 계세요! 조금만 더 힘내세요",
            "general": "잘 하고 계세요!",
        }

        message = messages.get(trigger, messages["general"])

        feedback = FeedbackItem(
            type=FeedbackType.ENCOURAGEMENT,
            priority=FeedbackPriority.LOW,
            message=message,
            data={"trigger": trigger}
        )

        await self._emit_feedback(session_id, feedback)
        return feedback

    async def send_tip(
        self,
        session_id: str,
        tip_type: str = "general"
    ) -> Optional[FeedbackItem]:
        """Send helpful tip."""
        session = self._sessions.get(session_id)
        if not session:
            return None

        tips = {
            "structure": "답변은 '상황-행동-결과' 순서로 구성해보세요",
            "specific": "구체적인 예시를 들어 설명해보세요",
            "conclusion": "마무리 멘트로 핵심을 한 번 더 강조해보세요",
            "smile": "자연스러운 미소를 잊지 마세요",
            "general": "천천히, 명확하게 답변해주세요",
        }

        tip = tips.get(tip_type, tips["general"])

        feedback = FeedbackItem(
            type=FeedbackType.TIP,
            priority=FeedbackPriority.LOW,
            message=tip,
            data={"tip_type": tip_type}
        )

        await self._emit_feedback(session_id, feedback)
        return feedback

    # =========================================================================
    # Session Summary
    # =========================================================================

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of feedback session."""
        session = self._sessions.get(session_id)
        if not session:
            return {}

        # Count feedback by type
        feedback_counts = {}
        for fb in session.feedback_history:
            fb_type = fb.type.value
            feedback_counts[fb_type] = feedback_counts.get(fb_type, 0) + 1

        return {
            "session_id": session_id,
            "duration": session.elapsed_time,
            "total_feedback": len(session.feedback_history),
            "feedback_by_type": feedback_counts,
            "metrics": session.metrics,
            "feedback_history": [fb.to_dict() for fb in session.feedback_history],
        }


# Singleton instance
realtime_feedback = RealtimeFeedbackEngine()
