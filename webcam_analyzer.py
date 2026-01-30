# webcam_analyzer.py
# Phase 2: 실시간 웹캠 분석 - MediaPipe Tasks API 버전 (0.10.30+)

import logging
import math
import os
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)

# 모델 파일 경로
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
FACE_MODEL = os.path.join(MODEL_DIR, "face_landmarker.task")
POSE_MODEL = os.path.join(MODEL_DIR, "pose_landmarker_heavy.task")
HAND_MODEL = os.path.join(MODEL_DIR, "hand_landmarker.task")

MEDIAPIPE_AVAILABLE = False
OPENCV_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    pass

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision
    from mediapipe import Image as MpImage
    from mediapipe import ImageFormat
    # 모델 파일 존재 여부 확인
    if os.path.exists(FACE_MODEL) and os.path.exists(POSE_MODEL) and os.path.exists(HAND_MODEL):
        MEDIAPIPE_AVAILABLE = True
    else:
        logger.warning(f"MediaPipe model files not found in {MODEL_DIR}")
except ImportError as e:
    logger.warning(f"MediaPipe import error: {e}")

try:
    import numpy as np
except ImportError:
    np = None


class FeedbackType(str, Enum):
    POSTURE = "posture"
    EYE_CONTACT = "eye_contact"
    EXPRESSION = "expression"
    GESTURE = "gesture"
    HEAD_POSITION = "head_position"
    SHOULDER = "shoulder"
    FACE_POSITION = "face_position"


class FeedbackPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RealtimeFeedback:
    feedback_type: FeedbackType
    message: str
    priority: FeedbackPriority
    score: float
    suggestion: str = ""
    detail: str = ""


class WebcamAnalyzer:
    """MediaPipe Tasks API를 사용한 웹캠 분석기"""

    # 임계값 설정 (엄격한 기준)
    EYE_CONTACT_THRESHOLD = 0.15  # 시선 이탈 임계값
    HEAD_CENTER_STRICT_X = 0.08   # 머리 중앙 이탈 (심각)
    HEAD_CENTER_STRICT_Y = 0.10
    HEAD_CENTER_WARN_X = 0.05     # 머리 중앙 이탈 (경고)
    HEAD_CENTER_WARN_Y = 0.06
    SHOULDER_TILT_STRICT = 0.025  # 어깨 기울기 (심각)
    SHOULDER_TILT_WARN = 0.015    # 어깨 기울기 (경고)
    FACE_SIZE_MIN = 0.10          # 얼굴 크기 최소 (너무 멀리)
    FACE_SIZE_MAX = 0.55          # 얼굴 크기 최대 (너무 가까이)
    HEAD_TILT_STRICT = 5.0        # 머리 기울기 (심각) - 도
    HEAD_TILT_WARN = 3.0          # 머리 기울기 (경고) - 도

    def __init__(self):
        self.face_landmarker = None
        self.pose_landmarker = None
        self.hand_landmarker = None
        self._initialized = False
        self._frame_timestamp = 0

        # 히스토리 (노이즈 감소용, 5프레임)
        self._eye_hist = deque(maxlen=5)
        self._head_x_hist = deque(maxlen=5)
        self._head_y_hist = deque(maxlen=5)
        self._shoulder_hist = deque(maxlen=5)
        self._tilt_hist = deque(maxlen=5)
        self._face_size_hist = deque(maxlen=5)

    def initialize(self) -> bool:
        """분석기 초기화"""
        if not MEDIAPIPE_AVAILABLE or not OPENCV_AVAILABLE:
            logger.error(f"MediaPipe available: {MEDIAPIPE_AVAILABLE}, OpenCV available: {OPENCV_AVAILABLE}")
            return False

        try:
            # Face Landmarker 초기화
            face_options = vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=FACE_MODEL),
                running_mode=vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=True,
            )
            self.face_landmarker = vision.FaceLandmarker.create_from_options(face_options)

            # Pose Landmarker 초기화
            pose_options = vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=POSE_MODEL),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.pose_landmarker = vision.PoseLandmarker.create_from_options(pose_options)

            # Hand Landmarker 초기화
            hand_options = vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=HAND_MODEL),
                running_mode=vision.RunningMode.IMAGE,
                num_hands=2,
                min_hand_detection_confidence=0.5,
                min_hand_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.hand_landmarker = vision.HandLandmarker.create_from_options(hand_options)

            self._initialized = True
            logger.info("WebcamAnalyzer initialized successfully with MediaPipe Tasks API")
            return True

        except Exception as e:
            logger.error(f"WebcamAnalyzer initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """프레임 분석"""
        if not self._initialized:
            return self._fallback()

        try:
            # BGR -> RGB 변환
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # MediaPipe Image 생성
            mp_image = MpImage(image_format=ImageFormat.SRGB, data=rgb)

            # 각 분석 수행
            face = self._analyze_face(mp_image)
            pose = self._analyze_pose(mp_image)
            hands = self._analyze_hands(mp_image, face)

            # 피드백 생성
            feedback = self._gen_feedback(face, pose, hands)

            # 점수 계산
            score = self._calc_score(face, pose, hands)

            return {
                "face": face,
                "pose": pose,
                "hands": hands,
                "feedback": feedback,
                "overall_score": score
            }

        except Exception as e:
            logger.warning(f"Frame analysis error: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback()

    def _analyze_face(self, mp_image: MpImage) -> Dict[str, Any]:
        """얼굴 분석"""
        if not self.face_landmarker:
            return {"detected": False}

        try:
            result = self.face_landmarker.detect(mp_image)

            if not result.face_landmarks:
                return {"detected": False, "reason": "얼굴 미감지"}

            landmarks = result.face_landmarks[0]

            # 얼굴 바운딩 박스 계산
            xs = [lm.x for lm in landmarks]
            ys = [lm.y for lm in landmarks]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            face_width = max_x - min_x
            face_height = max_y - min_y
            face_size = (face_width + face_height) / 2

            self._face_size_hist.append(face_size)
            avg_face_size = sum(self._face_size_hist) / len(self._face_size_hist)

            # 코 위치 (얼굴 중심 기준점) - landmark 4번이 코끝
            nose = landmarks[4]
            self._head_x_hist.append(nose.x)
            self._head_y_hist.append(nose.y)

            avg_x = sum(self._head_x_hist) / len(self._head_x_hist)
            avg_y = sum(self._head_y_hist) / len(self._head_y_hist)

            # 중앙에서의 이탈 정도
            off_x = abs(avg_x - 0.5)
            off_y = abs(avg_y - 0.5)

            # 머리 기울기 계산 (눈 위치 기준)
            # 왼쪽 눈: 33, 오른쪽 눈: 263 (FaceMesh 기준)
            left_eye = landmarks[33]
            right_eye = landmarks[263]
            tilt = math.degrees(math.atan2(right_eye.y - left_eye.y, right_eye.x - left_eye.x))
            self._tilt_hist.append(tilt)
            avg_tilt = sum(self._tilt_hist) / len(self._tilt_hist)

            # 시선 분석 (눈동자 위치)
            eye_contact = self._check_eye_contact(landmarks)
            self._eye_hist.append(1.0 if eye_contact else 0.0)
            eye_ratio = sum(self._eye_hist) / len(self._eye_hist)

            # 표정 분석 (blendshapes 사용)
            expression = self._check_expression(result.face_blendshapes[0] if result.face_blendshapes else None)

            # 머리 위치 상태 판정
            head_position = "centered"
            if off_x >= self.HEAD_CENTER_WARN_X or off_y >= self.HEAD_CENTER_WARN_Y:
                parts = []
                if avg_x < 0.5 - self.HEAD_CENTER_STRICT_X:
                    parts.append("왼쪽")
                elif avg_x > 0.5 + self.HEAD_CENTER_STRICT_X:
                    parts.append("오른쪽")
                if avg_y < 0.5 - self.HEAD_CENTER_STRICT_Y:
                    parts.append("위")
                elif avg_y > 0.5 + self.HEAD_CENTER_STRICT_Y:
                    parts.append("아래")
                head_position = " ".join(parts) if parts else "약간 벗어남"

            return {
                "detected": True,
                "eye_contact": eye_contact,
                "eye_contact_ratio": eye_ratio,
                "head_position": head_position,
                "head_offset_x": off_x,
                "head_offset_y": off_y,
                "head_tilt_deg": avg_tilt,
                "expression": expression,
                "face_size": avg_face_size,
                "face_center": (avg_x, avg_y)
            }

        except Exception as e:
            logger.warning(f"Face analysis error: {e}")
            return {"detected": False, "reason": str(e)}

    def _check_eye_contact(self, landmarks) -> bool:
        """시선이 정면을 향하는지 확인"""
        try:
            # 왼쪽 눈 중심과 홍채
            left_eye_inner = landmarks[133]  # 왼쪽 눈 안쪽
            left_eye_outer = landmarks[33]   # 왼쪽 눈 바깥쪽
            left_iris = landmarks[468]       # 왼쪽 홍채 (refine_landmarks 필요)

            # 오른쪽 눈 중심과 홍채
            right_eye_inner = landmarks[362]
            right_eye_outer = landmarks[263]
            right_iris = landmarks[473]

            # 눈 너비
            left_width = abs(left_eye_outer.x - left_eye_inner.x)
            right_width = abs(right_eye_outer.x - right_eye_inner.x)

            if left_width > 0 and right_width > 0:
                # 눈 중심 계산
                left_center = (left_eye_inner.x + left_eye_outer.x) / 2
                right_center = (right_eye_inner.x + right_eye_outer.x) / 2

                # 홍채가 눈 중심에서 얼마나 벗어났는지
                left_offset = abs(left_iris.x - left_center) / left_width
                right_offset = abs(right_iris.x - right_center) / right_width

                avg_offset = (left_offset + right_offset) / 2
                return avg_offset < self.EYE_CONTACT_THRESHOLD

            return False

        except (IndexError, AttributeError):
            # 홍채 랜드마크가 없는 경우 (468, 473은 refine_landmarks=True 필요)
            return True  # 기본값

    def _check_expression(self, blendshapes) -> str:
        """표정 분석 (blendshapes 기반)"""
        if not blendshapes:
            return "neutral"

        try:
            # blendshapes에서 표정 관련 값 추출
            scores = {bs.category_name: bs.score for bs in blendshapes}

            # 미소 감지
            mouth_smile_left = scores.get("mouthSmileLeft", 0)
            mouth_smile_right = scores.get("mouthSmileRight", 0)
            avg_smile = (mouth_smile_left + mouth_smile_right) / 2

            # 긴장 감지 (눈썹, 입술)
            brow_down_left = scores.get("browDownLeft", 0)
            brow_down_right = scores.get("browDownRight", 0)
            jaw_clench = scores.get("jawForward", 0)

            if avg_smile > 0.3:
                return "smile"
            elif (brow_down_left + brow_down_right) / 2 > 0.3 or jaw_clench > 0.3:
                return "tense"
            else:
                return "neutral"

        except Exception:
            return "neutral"

    def _analyze_pose(self, mp_image: MpImage) -> Dict[str, Any]:
        """자세 분석"""
        if not self.pose_landmarker:
            return {"detected": False}

        try:
            result = self.pose_landmarker.detect(mp_image)

            if not result.pose_landmarks:
                return {"detected": False}

            landmarks = result.pose_landmarks[0]

            # 어깨 랜드마크 (11: 왼쪽 어깨, 12: 오른쪽 어깨)
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]

            # 가시성 확인
            if left_shoulder.visibility < 0.5 or right_shoulder.visibility < 0.5:
                return {"detected": False}

            # 어깨 높이 차이
            shoulder_diff = abs(left_shoulder.y - right_shoulder.y)
            self._shoulder_hist.append(shoulder_diff)
            avg_diff = sum(self._shoulder_hist) / len(self._shoulder_hist)

            # 어깨 정렬 상태
            aligned = avg_diff < self.SHOULDER_TILT_STRICT
            warning = avg_diff >= self.SHOULDER_TILT_WARN

            # 기울기 방향
            tilt_direction = ""
            if warning:
                if left_shoulder.y < right_shoulder.y:
                    tilt_direction = "왼쪽 어깨 올라감"
                else:
                    tilt_direction = "오른쪽 어깨 올라감"

            # 몸 중심
            body_center_x = (left_shoulder.x + right_shoulder.x) / 2

            # 자세 점수
            score = 100
            if not aligned:
                score -= 35
            elif warning:
                score -= 20
            if abs(body_center_x - 0.5) > 0.10:
                score -= 20

            return {
                "detected": True,
                "shoulder_aligned": aligned,
                "shoulder_warning": warning,
                "shoulder_diff": avg_diff,
                "tilt_direction": tilt_direction,
                "body_center_x": body_center_x,
                "posture_score": max(0, score)
            }

        except Exception as e:
            logger.warning(f"Pose analysis error: {e}")
            return {"detected": False}

    def _analyze_hands(self, mp_image: MpImage, face: Dict) -> Dict[str, Any]:
        """손 분석"""
        if not self.hand_landmarker:
            return {"detected": False, "count": 0, "touching_face": False}

        try:
            result = self.hand_landmarker.detect(mp_image)

            if not result.hand_landmarks:
                return {"detected": False, "count": 0, "touching_face": False}

            face_center = face.get("face_center", (0.5, 0.5))
            face_size = face.get("face_size", 0.2)

            touching_face = False

            for hand_landmarks in result.hand_landmarks:
                # 손가락 끝 랜드마크 확인 (4, 8, 12, 16, 20)
                fingertips = [4, 8, 12, 16, 20]
                for idx in fingertips:
                    tip = hand_landmarks[idx]
                    distance = math.sqrt(
                        (tip.x - face_center[0]) ** 2 +
                        (tip.y - face_center[1]) ** 2
                    )
                    if distance < face_size * 1.2:
                        touching_face = True
                        break

            return {
                "detected": True,
                "count": len(result.hand_landmarks),
                "touching_face": touching_face
            }

        except Exception as e:
            logger.warning(f"Hand analysis error: {e}")
            return {"detected": False, "count": 0, "touching_face": False}

    def _gen_feedback(self, face: Dict, pose: Dict, hands: Dict) -> List[RealtimeFeedback]:
        """피드백 생성"""
        feedback = []

        # 얼굴 미감지
        if not face.get("detected"):
            feedback.append(RealtimeFeedback(
                FeedbackType.FACE_POSITION,
                "얼굴이 감지되지 않습니다",
                FeedbackPriority.CRITICAL,
                0,
                "카메라를 정면으로 바라봐주세요"
            ))
            return feedback

        # 시선 체크
        eye_ratio = face.get("eye_contact_ratio", 0)
        if eye_ratio < 0.6:
            priority = FeedbackPriority.CRITICAL if eye_ratio < 0.4 else FeedbackPriority.HIGH
            msg = "시선이 카메라를 벗어났습니다" if eye_ratio < 0.4 else "시선이 불안정합니다"
            feedback.append(RealtimeFeedback(
                FeedbackType.EYE_CONTACT,
                msg,
                priority,
                eye_ratio * 100,
                "카메라 렌즈를 바라보세요"
            ))

        # 머리 위치
        head_pos = face.get("head_position", "centered")
        if head_pos != "centered":
            offset_sum = face.get("head_offset_x", 0) + face.get("head_offset_y", 0)
            priority = FeedbackPriority.HIGH if offset_sum > 0.12 else FeedbackPriority.MEDIUM
            feedback.append(RealtimeFeedback(
                FeedbackType.HEAD_POSITION,
                f"얼굴이 {head_pos}으로 치우쳤습니다",
                priority,
                max(0, 100 - offset_sum * 300),
                "화면 중앙에 위치시키세요"
            ))

        # 머리 기울기
        head_tilt = abs(face.get("head_tilt_deg", 0))
        if head_tilt > self.HEAD_TILT_WARN:
            priority = FeedbackPriority.HIGH if head_tilt > self.HEAD_TILT_STRICT else FeedbackPriority.MEDIUM
            feedback.append(RealtimeFeedback(
                FeedbackType.HEAD_POSITION,
                "고개가 기울어져 있습니다",
                priority,
                max(0, 100 - head_tilt * 10),
                "고개를 똑바로 세워주세요",
                f"{head_tilt:.1f}도"
            ))

        # 얼굴 크기 (거리)
        face_size = face.get("face_size", 0.25)
        if face_size < self.FACE_SIZE_MIN:
            feedback.append(RealtimeFeedback(
                FeedbackType.FACE_POSITION,
                "너무 멀리 있습니다",
                FeedbackPriority.MEDIUM,
                50,
                "카메라에 가까이 앉아주세요"
            ))
        elif face_size > self.FACE_SIZE_MAX:
            feedback.append(RealtimeFeedback(
                FeedbackType.FACE_POSITION,
                "너무 가깝습니다",
                FeedbackPriority.MEDIUM,
                50,
                "카메라에서 떨어져 앉아주세요"
            ))

        # 어깨 자세
        if pose.get("detected"):
            if not pose.get("shoulder_aligned"):
                feedback.append(RealtimeFeedback(
                    FeedbackType.SHOULDER,
                    "어깨가 기울어져 있습니다",
                    FeedbackPriority.HIGH,
                    pose.get("posture_score", 45),
                    "어깨를 수평으로 맞춰주세요",
                    pose.get("tilt_direction", "")
                ))
            elif pose.get("shoulder_warning"):
                feedback.append(RealtimeFeedback(
                    FeedbackType.SHOULDER,
                    "어깨가 약간 기울어져 있습니다",
                    FeedbackPriority.MEDIUM,
                    pose.get("posture_score", 65),
                    "어깨를 수평으로 유지하세요"
                ))

            # 몸 중심 이탈
            body_cx = pose.get("body_center_x", 0.5)
            if abs(body_cx - 0.5) > 0.10:
                direction = "왼쪽" if body_cx < 0.5 else "오른쪽"
                feedback.append(RealtimeFeedback(
                    FeedbackType.POSTURE,
                    f"몸이 {direction}으로 치우쳐 있습니다",
                    FeedbackPriority.MEDIUM,
                    65,
                    "화면 중앙에 앉아주세요"
                ))

        # 손이 얼굴에 닿음
        if hands.get("touching_face"):
            feedback.append(RealtimeFeedback(
                FeedbackType.GESTURE,
                "손이 얼굴에 닿아 있습니다",
                FeedbackPriority.HIGH,
                30,
                "손을 내려놓으세요"
            ))

        # 표정
        if face.get("expression") == "tense":
            feedback.append(RealtimeFeedback(
                FeedbackType.EXPRESSION,
                "표정이 긴장되어 보입니다",
                FeedbackPriority.LOW,
                60,
                "자연스러운 미소를 지어보세요"
            ))

        return feedback

    def _calc_score(self, face: Dict, pose: Dict, hands: Dict) -> float:
        """종합 점수 계산"""
        if not face.get("detected"):
            return 0.0

        score = 100.0

        # 시선 (최대 -35점)
        eye_ratio = face.get("eye_contact_ratio", 0)
        if eye_ratio < 0.4:
            score -= 35
        elif eye_ratio < 0.55:
            score -= 25
        elif eye_ratio < 0.7:
            score -= 15
        elif eye_ratio < 0.85:
            score -= 8

        # 머리 위치 (최대 -20점)
        offset_sum = face.get("head_offset_x", 0) + face.get("head_offset_y", 0)
        score -= min(20, offset_sum * 150)

        # 머리 기울기 (최대 -15점)
        head_tilt = abs(face.get("head_tilt_deg", 0))
        if head_tilt > self.HEAD_TILT_STRICT:
            score -= 15
        elif head_tilt > self.HEAD_TILT_WARN:
            score -= 8

        # 어깨 자세 (최대 -20점)
        if pose.get("detected"):
            if not pose.get("shoulder_aligned"):
                score -= 20
            elif pose.get("shoulder_warning"):
                score -= 12

        # 손 얼굴 접촉 (-10점)
        if hands.get("touching_face"):
            score -= 10

        return max(0, min(100, round(score, 1)))

    def _fallback(self) -> Dict[str, Any]:
        """분석 실패 시 기본 반환값"""
        return {
            "face": {"detected": False},
            "pose": {"detected": False},
            "hands": {"detected": False, "count": 0, "touching_face": False},
            "feedback": [RealtimeFeedback(
                FeedbackType.FACE_POSITION,
                "분석 불가",
                FeedbackPriority.CRITICAL,
                0,
                "카메라를 확인해주세요"
            )],
            "overall_score": 0
        }

    def release(self):
        """리소스 해제"""
        if self.face_landmarker:
            self.face_landmarker.close()
        if self.pose_landmarker:
            self.pose_landmarker.close()
        if self.hand_landmarker:
            self.hand_landmarker.close()
        self._initialized = False


# 싱글톤 인스턴스
_instance: Optional[WebcamAnalyzer] = None


def get_webcam_analyzer() -> WebcamAnalyzer:
    """웹캠 분석기 싱글톤 인스턴스 반환"""
    global _instance
    if _instance is None:
        _instance = WebcamAnalyzer()
    if not _instance._initialized:
        _instance.initialize()
    return _instance


def is_webcam_analysis_available() -> bool:
    """웹캠 분석 기능 사용 가능 여부"""
    return MEDIAPIPE_AVAILABLE and OPENCV_AVAILABLE
