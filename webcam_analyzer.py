# webcam_analyzer.py
# Phase 2: 실시간 웹캠 분석 모듈 (MediaPipe + OpenCV)

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# MediaPipe/OpenCV 가용성 확인
MEDIAPIPE_AVAILABLE = False
OPENCV_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    logger.warning("OpenCV not installed. Run: pip install opencv-python")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    logger.warning("MediaPipe not installed. Run: pip install mediapipe")

try:
    import numpy as np
except ImportError:
    import warnings
    warnings.warn("NumPy not installed")
    np = None


class FeedbackType(str, Enum):
    """피드백 유형"""
    POSTURE = "posture"
    EYE_CONTACT = "eye_contact"
    EXPRESSION = "expression"
    GESTURE = "gesture"
    HEAD_POSITION = "head_position"


class FeedbackPriority(str, Enum):
    """피드백 우선순위"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RealtimeFeedback:
    """실시간 피드백 데이터"""
    feedback_type: FeedbackType
    message: str
    priority: FeedbackPriority
    score: float  # 0-100
    suggestion: str = ""


class WebcamAnalyzer:
    """
    실시간 웹캠 분석 클래스
    MediaPipe를 사용한 자세, 표정, 시선 분석
    """

    # 최적 기준값
    OPTIMAL_EYE_CONTACT_RATIO = 0.7  # 70% 시선 맞춤
    OPTIMAL_HEAD_CENTERED_THRESHOLD = 0.15  # 중앙 기준 허용 오차
    OPTIMAL_SHOULDER_LEVEL_THRESHOLD = 0.05  # 어깨 수평 허용 오차

    def __init__(self):
        self.mp_face_mesh = None
        self.mp_pose = None
        self.mp_hands = None
        self.mp_drawing = None
        self.face_mesh = None
        self.pose = None
        self.hands = None
        self._initialized = False

        # 분석 히스토리 (평균 계산용)
        self._eye_contact_history: List[bool] = []
        self._head_position_history: List[str] = []
        self._expression_history: List[str] = []

    def initialize(self) -> bool:
        """MediaPipe 모델 초기화"""
        if not MEDIAPIPE_AVAILABLE or not OPENCV_AVAILABLE:
            logger.warning("MediaPipe or OpenCV not available")
            return False

        try:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_pose = mp.solutions.pose
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils

            # Face Mesh 초기화 (얼굴 478개 랜드마크)
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,  # 눈/입술 정밀 추적
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

            # Pose 초기화 (몸 33개 랜드마크)
            self.pose = self.mp_pose.Pose(
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                model_complexity=1  # 0=lite, 1=full, 2=heavy
            )

            # Hands 초기화 (손 21개 랜드마크 x 2)
            self.hands = self.mp_hands.Hands(
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

            self._initialized = True
            logger.info("WebcamAnalyzer initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WebcamAnalyzer: {e}")
            return False

    def analyze_frame(self, frame: 'np.ndarray') -> Dict[str, Any]:
        """
        단일 프레임 분석 (실시간용)

        Args:
            frame: BGR 이미지 (OpenCV 형식)

        Returns:
            분석 결과 딕셔너리
        """
        if not self._initialized:
            return self._get_fallback_result()

        try:
            # BGR -> RGB 변환 (MediaPipe는 RGB 사용)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False  # 성능 최적화

            # 병렬 분석
            face_result = self._analyze_face(rgb_frame)
            pose_result = self._analyze_pose(rgb_frame)
            hand_result = self._analyze_hands(rgb_frame)

            # 결과 통합
            result = {
                "face": face_result,
                "pose": pose_result,
                "hands": hand_result,
                "feedback": self._generate_realtime_feedback(face_result, pose_result, hand_result),
                "overall_score": self._calculate_frame_score(face_result, pose_result, hand_result),
            }

            return result

        except Exception as e:
            logger.warning(f"Frame analysis error: {e}")
            return self._get_fallback_result()

    def _analyze_face(self, rgb_frame: 'np.ndarray') -> Dict[str, Any]:
        """얼굴 분석 (시선, 표정, 위치)"""
        if self.face_mesh is None:
            return {"detected": False}

        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return {"detected": False}

        face_landmarks = results.multi_face_landmarks[0]
        h, w = rgb_frame.shape[:2]

        # 주요 랜드마크 추출
        landmarks = face_landmarks.landmark

        # 코 끝 (얼굴 중심)
        nose_tip = landmarks[4]

        # 눈 랜드마크 (왼쪽/오른쪽 눈 중심)
        left_eye_center = self._get_eye_center(landmarks, "left")
        right_eye_center = self._get_eye_center(landmarks, "right")

        # 시선 방향 계산
        eye_contact = self._calculate_eye_contact(landmarks, w, h)

        # 머리 위치 (중앙 기준)
        head_position = self._calculate_head_position(nose_tip, w, h)

        # 표정 분석 (입술 모양 기반)
        expression = self._analyze_expression(landmarks)

        # 히스토리 업데이트
        self._eye_contact_history.append(eye_contact)
        self._head_position_history.append(head_position)
        self._expression_history.append(expression)

        # 히스토리 제한 (최근 30프레임)
        if len(self._eye_contact_history) > 30:
            self._eye_contact_history.pop(0)
            self._head_position_history.pop(0)
            self._expression_history.pop(0)

        return {
            "detected": True,
            "eye_contact": eye_contact,
            "eye_contact_ratio": sum(self._eye_contact_history) / len(self._eye_contact_history) if self._eye_contact_history else 0,
            "head_position": head_position,
            "head_x": nose_tip.x,
            "head_y": nose_tip.y,
            "expression": expression,
            "face_center": (nose_tip.x, nose_tip.y),
        }

    def _get_eye_center(self, landmarks, side: str) -> Tuple[float, float]:
        """눈 중심점 계산"""
        if side == "left":
            # 왼쪽 눈 랜드마크 인덱스
            indices = [33, 133, 160, 144, 153, 154, 155, 157, 158, 159, 161, 163]
        else:
            # 오른쪽 눈 랜드마크 인덱스
            indices = [362, 263, 387, 373, 380, 381, 382, 384, 385, 386, 388, 390]

        x_sum = sum(landmarks[i].x for i in indices)
        y_sum = sum(landmarks[i].y for i in indices)
        return (x_sum / len(indices), y_sum / len(indices))

    def _calculate_eye_contact(self, landmarks, w: int, h: int) -> bool:
        """시선이 카메라를 향하는지 판단"""
        # 홍채 위치 기반 시선 추적
        # 왼쪽 홍채: 468, 오른쪽 홍채: 473
        left_iris = landmarks[468]
        right_iris = landmarks[473]

        # 왼쪽 눈 영역
        left_eye_inner = landmarks[133]
        left_eye_outer = landmarks[33]

        # 오른쪽 눈 영역
        right_eye_inner = landmarks[362]
        right_eye_outer = landmarks[263]

        # 홍채가 눈 중앙에 있는지 확인
        left_eye_width = abs(left_eye_outer.x - left_eye_inner.x)
        right_eye_width = abs(right_eye_outer.x - right_eye_inner.x)

        # 홍채의 상대적 위치 (0=외측, 1=내측)
        left_iris_ratio = (left_iris.x - left_eye_outer.x) / left_eye_width if left_eye_width > 0 else 0.5
        right_iris_ratio = (right_iris.x - right_eye_inner.x) / right_eye_width if right_eye_width > 0 else 0.5

        # 중앙 범위 (0.3~0.7)이면 시선 맞춤으로 판단
        left_centered = 0.3 < left_iris_ratio < 0.7
        right_centered = 0.3 < abs(1 - right_iris_ratio) < 0.7

        return left_centered and right_centered

    def _calculate_head_position(self, nose_tip, w: int, h: int) -> str:
        """머리 위치 판단"""
        # 화면 중앙 기준 (0.5, 0.5)
        x_offset = nose_tip.x - 0.5
        y_offset = nose_tip.y - 0.5

        threshold = self.OPTIMAL_HEAD_CENTERED_THRESHOLD

        if abs(x_offset) < threshold and abs(y_offset) < threshold:
            return "centered"
        elif x_offset < -threshold:
            return "left"
        elif x_offset > threshold:
            return "right"
        elif y_offset < -threshold:
            return "up"
        elif y_offset > threshold:
            return "down"
        else:
            return "tilted"

    def _analyze_expression(self, landmarks) -> str:
        """표정 분석 (입술 기반)"""
        # 입술 랜드마크
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]
        left_mouth = landmarks[61]
        right_mouth = landmarks[291]

        # 입 벌림 정도
        mouth_open = abs(upper_lip.y - lower_lip.y)

        # 입 너비
        mouth_width = abs(left_mouth.x - right_mouth.x)

        # 입꼬리 높이 (미소 판단)
        left_corner = landmarks[61]
        right_corner = landmarks[291]
        mouth_center_y = (upper_lip.y + lower_lip.y) / 2

        corner_lift = ((mouth_center_y - left_corner.y) + (mouth_center_y - right_corner.y)) / 2

        # 표정 판단
        if corner_lift > 0.01 and mouth_width > 0.15:
            return "smile"
        elif mouth_open > 0.03:
            return "speaking"
        elif corner_lift < -0.01:
            return "serious"
        else:
            return "neutral"

    def _analyze_pose(self, rgb_frame: 'np.ndarray') -> Dict[str, Any]:
        """자세 분석"""
        if self.pose is None:
            return {"detected": False}

        results = self.pose.process(rgb_frame)

        if not results.pose_landmarks:
            return {"detected": False}

        landmarks = results.pose_landmarks.landmark

        # 어깨 랜드마크 (11=왼쪽, 12=오른쪽)
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]

        # 어깨 기울기
        shoulder_diff = abs(left_shoulder.y - right_shoulder.y)
        shoulder_aligned = shoulder_diff < self.OPTIMAL_SHOULDER_LEVEL_THRESHOLD

        # 어깨 너비 (화면 대비)
        shoulder_width = abs(left_shoulder.x - right_shoulder.x)

        # 몸 중심
        body_center_x = (left_shoulder.x + right_shoulder.x) / 2

        # 자세 점수 계산
        posture_score = 100
        if not shoulder_aligned:
            posture_score -= 20
        if abs(body_center_x - 0.5) > 0.15:
            posture_score -= 15

        return {
            "detected": True,
            "shoulder_aligned": shoulder_aligned,
            "shoulder_diff": shoulder_diff,
            "shoulder_width": shoulder_width,
            "body_center_x": body_center_x,
            "posture_score": max(0, posture_score),
        }

    def _analyze_hands(self, rgb_frame: 'np.ndarray') -> Dict[str, Any]:
        """손 분석"""
        if self.hands is None:
            return {"detected": False, "count": 0}

        results = self.hands.process(rgb_frame)

        if not results.multi_hand_landmarks:
            return {"detected": False, "count": 0}

        hand_count = len(results.multi_hand_landmarks)

        # 손 위치 분석
        hand_positions = []
        for hand_landmarks in results.multi_hand_landmarks:
            # 손목 위치 (랜드마크 0)
            wrist = hand_landmarks.landmark[0]
            hand_positions.append({
                "x": wrist.x,
                "y": wrist.y,
                "visible": True
            })

        # 손이 얼굴 근처에 있는지 (긴장 제스처 감지)
        touching_face = False
        for pos in hand_positions:
            if pos["y"] < 0.4:  # 화면 상단 40%에 손이 있으면
                touching_face = True
                break

        return {
            "detected": True,
            "count": hand_count,
            "positions": hand_positions,
            "touching_face": touching_face,
        }

    def _generate_realtime_feedback(
        self,
        face: Dict[str, Any],
        pose: Dict[str, Any],
        hands: Dict[str, Any]
    ) -> List[RealtimeFeedback]:
        """실시간 피드백 생성"""
        feedback_list = []

        # 얼굴 미감지
        if not face.get("detected"):
            feedback_list.append(RealtimeFeedback(
                feedback_type=FeedbackType.POSTURE,
                message="얼굴이 감지되지 않습니다",
                priority=FeedbackPriority.HIGH,
                score=0,
                suggestion="카메라를 정면으로 바라봐주세요"
            ))
            return feedback_list

        # 시선 피드백
        eye_ratio = face.get("eye_contact_ratio", 0)
        if eye_ratio < 0.5:
            feedback_list.append(RealtimeFeedback(
                feedback_type=FeedbackType.EYE_CONTACT,
                message="시선을 카메라로 향해주세요",
                priority=FeedbackPriority.HIGH,
                score=eye_ratio * 100,
                suggestion="면접관(카메라)과 눈을 맞추세요"
            ))

        # 머리 위치 피드백
        head_pos = face.get("head_position", "centered")
        if head_pos != "centered":
            pos_messages = {
                "left": "고개가 왼쪽으로 치우쳤습니다",
                "right": "고개가 오른쪽으로 치우쳤습니다",
                "up": "고개를 조금 내려주세요",
                "down": "고개를 조금 들어주세요",
                "tilted": "고개를 바르게 해주세요",
            }
            feedback_list.append(RealtimeFeedback(
                feedback_type=FeedbackType.HEAD_POSITION,
                message=pos_messages.get(head_pos, "고개를 바르게 해주세요"),
                priority=FeedbackPriority.MEDIUM,
                score=70,
                suggestion="화면 중앙을 바라봐주세요"
            ))

        # 자세 피드백
        if pose.get("detected") and not pose.get("shoulder_aligned", True):
            feedback_list.append(RealtimeFeedback(
                feedback_type=FeedbackType.POSTURE,
                message="어깨가 기울어져 있습니다",
                priority=FeedbackPriority.MEDIUM,
                score=pose.get("posture_score", 70),
                suggestion="어깨를 수평으로 맞춰주세요"
            ))

        # 손 피드백 (얼굴 만짐)
        if hands.get("touching_face"):
            feedback_list.append(RealtimeFeedback(
                feedback_type=FeedbackType.GESTURE,
                message="손이 얼굴 근처에 있습니다",
                priority=FeedbackPriority.LOW,
                score=60,
                suggestion="손을 편하게 내려놓으세요"
            ))

        # 표정 피드백
        expression = face.get("expression", "neutral")
        if expression == "serious":
            feedback_list.append(RealtimeFeedback(
                feedback_type=FeedbackType.EXPRESSION,
                message="표정이 굳어 보입니다",
                priority=FeedbackPriority.LOW,
                score=70,
                suggestion="자연스러운 미소를 지어보세요"
            ))

        return feedback_list

    def _calculate_frame_score(
        self,
        face: Dict[str, Any],
        pose: Dict[str, Any],
        hands: Dict[str, Any]
    ) -> float:
        """프레임 종합 점수 계산"""
        if not face.get("detected"):
            return 0.0

        score = 0.0
        weights = {"face": 0.5, "pose": 0.3, "hands": 0.2}

        # 얼굴 점수
        face_score = 0.0
        if face.get("eye_contact"):
            face_score += 40
        if face.get("head_position") == "centered":
            face_score += 30
        if face.get("expression") in ["neutral", "smile"]:
            face_score += 30
        score += face_score * weights["face"]

        # 자세 점수
        if pose.get("detected"):
            score += pose.get("posture_score", 70) * weights["pose"]
        else:
            score += 70 * weights["pose"]  # 기본값

        # 손 점수
        hand_score = 80  # 기본값
        if hands.get("touching_face"):
            hand_score -= 20
        score += hand_score * weights["hands"]

        return round(min(100, max(0, score)), 1)

    def _get_fallback_result(self) -> Dict[str, Any]:
        """폴백 결과 (분석 실패 시)"""
        return {
            "face": {"detected": False},
            "pose": {"detected": False},
            "hands": {"detected": False, "count": 0},
            "feedback": [],
            "overall_score": 0,
            "error": "Analysis not available"
        }

    def get_annotated_frame(self, frame: 'np.ndarray') -> 'np.ndarray':
        """분석 결과가 오버레이된 프레임 반환 (디버그/시각화용)"""
        if not self._initialized or not OPENCV_AVAILABLE:
            return frame

        try:
            annotated = frame.copy()
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False

            # Face Mesh 그리기
            face_results = self.face_mesh.process(rgb_frame)
            if face_results.multi_face_landmarks:
                for face_landmarks in face_results.multi_face_landmarks:
                    self.mp_drawing.draw_landmarks(
                        annotated,
                        face_landmarks,
                        self.mp_face_mesh.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing.DrawingSpec(
                            color=(0, 255, 0), thickness=1
                        )
                    )

            # Pose 그리기
            pose_results = self.pose.process(rgb_frame)
            if pose_results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated,
                    pose_results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS
                )

            return annotated

        except Exception as e:
            logger.warning(f"Annotation error: {e}")
            return frame

    def release(self):
        """리소스 해제"""
        if self.face_mesh:
            self.face_mesh.close()
        if self.pose:
            self.pose.close()
        if self.hands:
            self.hands.close()
        self._initialized = False


# 싱글톤 인스턴스
webcam_analyzer = WebcamAnalyzer()


def get_webcam_analyzer() -> WebcamAnalyzer:
    """WebcamAnalyzer 인스턴스 반환"""
    if not webcam_analyzer._initialized:
        webcam_analyzer.initialize()
    return webcam_analyzer


def is_webcam_analysis_available() -> bool:
    """웹캠 분석 기능 사용 가능 여부"""
    return MEDIAPIPE_AVAILABLE and OPENCV_AVAILABLE
