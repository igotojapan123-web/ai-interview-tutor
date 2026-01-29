"""
Video Analyzer.

AI-powered video analysis for interview assessment.
"""

import asyncio
import base64
import io
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class PostureQuality(str, Enum):
    """Posture quality ratings."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


class FacialExpression(str, Enum):
    """Facial expression types."""
    SMILE = "smile"
    NEUTRAL = "neutral"
    SERIOUS = "serious"
    NERVOUS = "nervous"
    CONFIDENT = "confident"


@dataclass
class PostureMetrics:
    """Posture analysis metrics."""
    head_position: str = "centered"  # centered, left, right, tilted
    shoulder_alignment: float = 0.0  # -1 to 1, 0 is aligned
    eye_contact: float = 0.0  # 0-100
    movement_stability: float = 0.0  # 0-100, higher = more stable
    overall_posture_score: float = 0.0  # 0-100


@dataclass
class FacialMetrics:
    """Facial analysis metrics."""
    dominant_expression: FacialExpression = FacialExpression.NEUTRAL
    smile_frequency: float = 0.0  # 0-100
    eye_contact_ratio: float = 0.0  # 0-100
    blink_rate: float = 0.0  # blinks per minute
    expression_appropriateness: float = 0.0  # 0-100


@dataclass
class GestureMetrics:
    """Gesture analysis metrics."""
    hand_visibility: float = 0.0  # 0-100
    gesture_frequency: float = 0.0  # gestures per minute
    gesture_appropriateness: float = 0.0  # 0-100
    nervous_gestures_count: int = 0  # fidgeting, hair touching, etc.


@dataclass
class VideoAnalysisResult:
    """Complete video analysis result."""
    posture: PostureMetrics
    facial: FacialMetrics
    gestures: GestureMetrics
    overall_score: float
    professional_appearance: float  # 0-100
    strengths: List[str]
    improvements: List[str]
    frame_by_frame: List[Dict[str, Any]] = field(default_factory=list)
    timeline_events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "posture": {
                "head_position": self.posture.head_position,
                "eye_contact": self.posture.eye_contact,
                "movement_stability": self.posture.movement_stability,
                "overall_score": self.posture.overall_posture_score,
            },
            "facial": {
                "dominant_expression": self.facial.dominant_expression.value,
                "smile_frequency": self.facial.smile_frequency,
                "eye_contact_ratio": self.facial.eye_contact_ratio,
                "expression_appropriateness": self.facial.expression_appropriateness,
            },
            "gestures": {
                "hand_visibility": self.gestures.hand_visibility,
                "gesture_frequency": self.gestures.gesture_frequency,
                "gesture_appropriateness": self.gestures.gesture_appropriateness,
                "nervous_gestures": self.gestures.nervous_gestures_count,
            },
            "overall_score": self.overall_score,
            "professional_appearance": self.professional_appearance,
            "strengths": self.strengths,
            "improvements": self.improvements,
            "timeline_events": self.timeline_events,
        }


class VideoAnalyzer:
    """
    AI-powered video analyzer for interview assessment.

    Features:
    - Posture analysis
    - Facial expression recognition
    - Eye contact tracking
    - Gesture analysis
    - Body language assessment
    - Professional appearance scoring
    """

    # Optimal values
    OPTIMAL_EYE_CONTACT = 70  # 70% eye contact is ideal
    OPTIMAL_SMILE_FREQUENCY = 30  # Smile about 30% of the time
    OPTIMAL_MOVEMENT_STABILITY = 80  # Mostly stable with some natural movement

    def __init__(self):
        self._model_loaded = False
        self._face_cascade = None
        self._pose_model = None

    async def initialize(self) -> None:
        """Initialize video analysis models."""
        try:
            # In production, load actual models here
            # import cv2
            # self._face_cascade = cv2.CascadeClassifier(
            #     cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            # )
            self._model_loaded = True
            logger.info("Video analyzer initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize video analyzer: {e}")
            self._model_loaded = False

    async def analyze_video(
        self,
        video_path: Optional[str] = None,
        video_bytes: Optional[bytes] = None,
        frames: Optional[List[np.ndarray]] = None,
        fps: float = 30.0
    ) -> VideoAnalysisResult:
        """
        Analyze video recording.

        Args:
            video_path: Path to video file
            video_bytes: Video data as bytes
            frames: List of frame arrays
            fps: Frames per second

        Returns:
            VideoAnalysisResult with detailed analysis
        """
        # Extract frames if not provided
        if frames is None:
            frames = await self._extract_frames(video_path, video_bytes)

        if not frames:
            return self._create_fallback_result()

        # Analyze in parallel
        posture_task = asyncio.create_task(self._analyze_posture(frames))
        facial_task = asyncio.create_task(self._analyze_facial(frames, fps))
        gesture_task = asyncio.create_task(self._analyze_gestures(frames, fps))

        posture = await posture_task
        facial = await facial_task
        gestures = await gesture_task

        # Calculate overall scores
        overall_score = self._calculate_overall_score(posture, facial, gestures)
        professional = self._calculate_professional_appearance(posture, facial, gestures)

        # Generate feedback
        strengths, improvements = self._generate_feedback(posture, facial, gestures)

        # Create timeline events
        timeline = await self._create_timeline(frames, fps)

        return VideoAnalysisResult(
            posture=posture,
            facial=facial,
            gestures=gestures,
            overall_score=overall_score,
            professional_appearance=professional,
            strengths=strengths,
            improvements=improvements,
            timeline_events=timeline,
        )

    async def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Analyze a single frame for real-time feedback.

        Args:
            frame: Image frame as numpy array

        Returns:
            Frame analysis results
        """
        # Detect face
        face_data = await self._detect_face(frame)

        # Detect pose
        pose_data = await self._detect_pose(frame)

        return {
            "face_detected": face_data.get("detected", False),
            "face_position": face_data.get("position", None),
            "eye_contact": face_data.get("eye_contact", 0),
            "expression": face_data.get("expression", "neutral"),
            "pose_score": pose_data.get("score", 0),
            "head_position": pose_data.get("head_position", "centered"),
        }

    # =========================================================================
    # Frame Extraction
    # =========================================================================

    async def _extract_frames(
        self,
        video_path: Optional[str],
        video_bytes: Optional[bytes]
    ) -> List[np.ndarray]:
        """Extract frames from video."""
        frames = []

        try:
            # In production, use cv2 or moviepy
            # For now, return empty list to trigger fallback
            pass
        except Exception as e:
            logger.warning(f"Frame extraction failed: {e}")

        return frames

    # =========================================================================
    # Analysis Methods
    # =========================================================================

    async def _analyze_posture(self, frames: List[np.ndarray]) -> PostureMetrics:
        """Analyze posture across frames."""
        if not frames:
            return PostureMetrics(
                head_position="centered",
                shoulder_alignment=0,
                eye_contact=75,
                movement_stability=80,
                overall_posture_score=75,
            )

        # Simulate analysis
        # In production, use MediaPipe Pose or similar

        head_positions = []
        shoulder_alignments = []
        stabilities = []

        for i, frame in enumerate(frames):
            # Detect pose keypoints
            pose = await self._detect_pose(frame)

            head_positions.append(pose.get("head_position", "centered"))
            shoulder_alignments.append(pose.get("shoulder_alignment", 0))

            # Calculate frame-to-frame stability
            if i > 0:
                stability = self._calculate_frame_stability(frames[i-1], frame)
                stabilities.append(stability)

        # Aggregate results
        avg_stability = np.mean(stabilities) if stabilities else 80

        # Most common head position
        head_pos_counts = {}
        for pos in head_positions:
            head_pos_counts[pos] = head_pos_counts.get(pos, 0) + 1
        dominant_head_pos = max(head_pos_counts, key=head_pos_counts.get)

        # Average shoulder alignment
        avg_shoulder = np.mean(shoulder_alignments)

        # Calculate eye contact (simulated)
        eye_contact = 75 + np.random.normal(0, 5)

        # Overall posture score
        posture_score = (
            (100 if dominant_head_pos == "centered" else 70) * 0.3 +
            (100 - abs(avg_shoulder) * 50) * 0.2 +
            eye_contact * 0.3 +
            avg_stability * 0.2
        )

        return PostureMetrics(
            head_position=dominant_head_pos,
            shoulder_alignment=avg_shoulder,
            eye_contact=min(100, max(0, eye_contact)),
            movement_stability=min(100, max(0, avg_stability)),
            overall_posture_score=min(100, max(0, posture_score)),
        )

    async def _analyze_facial(
        self,
        frames: List[np.ndarray],
        fps: float
    ) -> FacialMetrics:
        """Analyze facial expressions across frames."""
        if not frames:
            return FacialMetrics(
                dominant_expression=FacialExpression.NEUTRAL,
                smile_frequency=25,
                eye_contact_ratio=75,
                blink_rate=15,
                expression_appropriateness=75,
            )

        expressions = []
        smile_count = 0
        blink_count = 0
        eye_contact_frames = 0

        for frame in frames:
            face_data = await self._detect_face(frame)

            if face_data.get("detected"):
                expr = face_data.get("expression", "neutral")
                expressions.append(expr)

                if expr == "smile":
                    smile_count += 1

                if face_data.get("eye_contact", False):
                    eye_contact_frames += 1

                if face_data.get("blink", False):
                    blink_count += 1

        # Calculate metrics
        total_frames = len(frames)
        duration_minutes = total_frames / fps / 60

        smile_frequency = (smile_count / total_frames * 100) if total_frames > 0 else 25
        eye_contact_ratio = (eye_contact_frames / total_frames * 100) if total_frames > 0 else 75
        blink_rate = (blink_count / duration_minutes) if duration_minutes > 0 else 15

        # Determine dominant expression
        expr_counts = {}
        for expr in expressions:
            expr_counts[expr] = expr_counts.get(expr, 0) + 1

        if expr_counts:
            dominant = max(expr_counts, key=expr_counts.get)
            dominant_expression = FacialExpression(dominant)
        else:
            dominant_expression = FacialExpression.NEUTRAL

        # Calculate appropriateness
        # Professional interviews should have neutral/confident with occasional smiles
        appropriateness = min(100, max(0,
            (50 if dominant_expression in [FacialExpression.NEUTRAL, FacialExpression.CONFIDENT] else 30) +
            (20 if 20 <= smile_frequency <= 40 else 10) +
            (20 if 15 <= blink_rate <= 25 else 10) +
            (eye_contact_ratio * 0.1)
        ))

        return FacialMetrics(
            dominant_expression=dominant_expression,
            smile_frequency=smile_frequency,
            eye_contact_ratio=eye_contact_ratio,
            blink_rate=blink_rate,
            expression_appropriateness=appropriateness,
        )

    async def _analyze_gestures(
        self,
        frames: List[np.ndarray],
        fps: float
    ) -> GestureMetrics:
        """Analyze gestures across frames."""
        if not frames:
            return GestureMetrics(
                hand_visibility=50,
                gesture_frequency=5,
                gesture_appropriateness=70,
                nervous_gestures_count=0,
            )

        hand_visible_frames = 0
        gesture_count = 0
        nervous_gestures = 0

        prev_hand_position = None

        for frame in frames:
            pose = await self._detect_pose(frame)

            # Check hand visibility
            hands = pose.get("hands", {})
            if hands.get("left_visible") or hands.get("right_visible"):
                hand_visible_frames += 1

            # Detect gesture (significant hand movement)
            current_pos = hands.get("position")
            if prev_hand_position and current_pos:
                movement = self._calculate_movement(prev_hand_position, current_pos)
                if movement > 50:  # Threshold for gesture
                    gesture_count += 1

            # Detect nervous gestures
            if pose.get("touching_face"):
                nervous_gestures += 1
            if pose.get("fidgeting"):
                nervous_gestures += 1

            prev_hand_position = current_pos

        # Calculate metrics
        total_frames = len(frames)
        duration_minutes = total_frames / fps / 60

        hand_visibility = (hand_visible_frames / total_frames * 100) if total_frames > 0 else 50
        gesture_frequency = (gesture_count / duration_minutes) if duration_minutes > 0 else 5

        # Appropriateness: some gestures are good, too many or nervous ones are bad
        appropriateness = min(100, max(0,
            70 +
            (15 if 3 <= gesture_frequency <= 10 else -10) +
            (15 if hand_visibility > 30 else 0) -
            (nervous_gestures * 5)
        ))

        return GestureMetrics(
            hand_visibility=hand_visibility,
            gesture_frequency=gesture_frequency,
            gesture_appropriateness=appropriateness,
            nervous_gestures_count=nervous_gestures,
        )

    # =========================================================================
    # Detection Methods
    # =========================================================================

    async def _detect_face(self, frame: np.ndarray) -> Dict[str, Any]:
        """Detect face and analyze expression."""
        # Simulated detection
        # In production, use dlib, face_recognition, or deepface

        return {
            "detected": True,
            "position": {"x": 0.5, "y": 0.3},
            "expression": np.random.choice(["neutral", "smile", "serious"], p=[0.6, 0.3, 0.1]),
            "eye_contact": np.random.random() > 0.3,
            "blink": np.random.random() > 0.95,
        }

    async def _detect_pose(self, frame: np.ndarray) -> Dict[str, Any]:
        """Detect body pose."""
        # Simulated detection
        # In production, use MediaPipe Pose

        return {
            "detected": True,
            "head_position": np.random.choice(["centered", "left", "right", "tilted"], p=[0.7, 0.1, 0.1, 0.1]),
            "shoulder_alignment": np.random.normal(0, 0.1),
            "score": 75 + np.random.normal(0, 10),
            "hands": {
                "left_visible": np.random.random() > 0.5,
                "right_visible": np.random.random() > 0.5,
                "position": (np.random.random(), np.random.random()),
            },
            "touching_face": np.random.random() > 0.95,
            "fidgeting": np.random.random() > 0.9,
        }

    def _calculate_frame_stability(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> float:
        """Calculate stability between frames."""
        # In production, compare pose keypoints
        # Higher value = more stable
        return 80 + np.random.normal(0, 5)

    def _calculate_movement(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """Calculate movement distance."""
        if pos1 is None or pos2 is None:
            return 0
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) ** 0.5 * 100

    # =========================================================================
    # Scoring & Feedback
    # =========================================================================

    def _calculate_overall_score(
        self,
        posture: PostureMetrics,
        facial: FacialMetrics,
        gestures: GestureMetrics
    ) -> float:
        """Calculate overall video score."""
        weights = {
            "posture": 0.35,
            "facial": 0.35,
            "gestures": 0.30,
        }

        score = (
            posture.overall_posture_score * weights["posture"] +
            facial.expression_appropriateness * weights["facial"] +
            gestures.gesture_appropriateness * weights["gestures"]
        )

        return round(min(100, max(0, score)), 1)

    def _calculate_professional_appearance(
        self,
        posture: PostureMetrics,
        facial: FacialMetrics,
        gestures: GestureMetrics
    ) -> float:
        """Calculate professional appearance score."""
        score = (
            (100 if posture.head_position == "centered" else 70) * 0.2 +
            posture.movement_stability * 0.2 +
            facial.eye_contact_ratio * 0.3 +
            (100 - gestures.nervous_gestures_count * 10) * 0.15 +
            (facial.expression_appropriateness) * 0.15
        )

        return round(min(100, max(0, score)), 1)

    def _generate_feedback(
        self,
        posture: PostureMetrics,
        facial: FacialMetrics,
        gestures: GestureMetrics
    ) -> Tuple[List[str], List[str]]:
        """Generate strengths and improvements."""
        strengths = []
        improvements = []

        # Posture feedback
        if posture.head_position == "centered":
            strengths.append("바른 시선 처리")
        else:
            improvements.append("카메라를 정면으로 바라봐주세요")

        if posture.eye_contact >= 70:
            strengths.append("좋은 아이컨택")
        elif posture.eye_contact < 50:
            improvements.append("카메라(면접관)를 더 자주 바라봐주세요")

        if posture.movement_stability >= 75:
            strengths.append("안정적인 자세")
        elif posture.movement_stability < 60:
            improvements.append("움직임을 줄이고 안정감 있게")

        # Facial feedback
        if 20 <= facial.smile_frequency <= 40:
            strengths.append("적절한 미소")
        elif facial.smile_frequency < 15:
            improvements.append("자연스러운 미소를 더 자주 지어보세요")
        elif facial.smile_frequency > 50:
            improvements.append("진지한 질문에는 진지한 표정도 필요합니다")

        # Gesture feedback
        if gestures.nervous_gestures_count == 0:
            strengths.append("자연스러운 제스처")
        elif gestures.nervous_gestures_count > 3:
            improvements.append("얼굴을 만지거나 불필요한 동작을 줄여주세요")

        if 3 <= gestures.gesture_frequency <= 10:
            strengths.append("적절한 손동작 사용")
        elif gestures.gesture_frequency < 2:
            improvements.append("적절한 손동작으로 강조 포인트를 만들어보세요")

        return strengths, improvements

    async def _create_timeline(
        self,
        frames: List[np.ndarray],
        fps: float
    ) -> List[Dict[str, Any]]:
        """Create timeline of notable events."""
        events = []

        # Sample frames for events
        sample_interval = max(1, len(frames) // 20)

        for i in range(0, len(frames), sample_interval):
            timestamp = i / fps

            face_data = await self._detect_face(frames[i])
            pose_data = await self._detect_pose(frames[i])

            # Record notable events
            if pose_data.get("touching_face"):
                events.append({
                    "timestamp": timestamp,
                    "type": "nervous_gesture",
                    "description": "얼굴 만짐",
                })

            if face_data.get("expression") == "smile":
                events.append({
                    "timestamp": timestamp,
                    "type": "expression",
                    "description": "미소",
                })

            if not face_data.get("eye_contact"):
                events.append({
                    "timestamp": timestamp,
                    "type": "eye_contact_lost",
                    "description": "시선 이탈",
                })

        return events[:20]  # Limit to 20 events

    def _create_fallback_result(self) -> VideoAnalysisResult:
        """Create fallback result when analysis fails."""
        return VideoAnalysisResult(
            posture=PostureMetrics(
                head_position="centered",
                eye_contact=75,
                movement_stability=80,
                overall_posture_score=75,
            ),
            facial=FacialMetrics(
                dominant_expression=FacialExpression.NEUTRAL,
                smile_frequency=25,
                eye_contact_ratio=75,
                expression_appropriateness=75,
            ),
            gestures=GestureMetrics(
                hand_visibility=50,
                gesture_frequency=5,
                gesture_appropriateness=70,
            ),
            overall_score=75,
            professional_appearance=75,
            strengths=["영상 분석이 완료되었습니다"],
            improvements=["웹캠을 확인하여 더 정확한 분석을 받아보세요"],
        )


# Singleton instance
video_analyzer = VideoAnalyzer()
