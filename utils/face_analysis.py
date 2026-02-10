"""
MediaPipe Face Mesh 기반 표정 분석 모듈
API 비용 0원, 로컬 처리
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple

try:
    import mediapipe as mp
    import cv2
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


@dataclass
class FaceAnalysisResult:
    """표정 분석 결과"""
    smile_score: float  # 0-100
    eye_contact: bool
    head_tilt: float  # degrees
    stability_score: float  # 0-100
    feedback_messages: List[str]


class FaceAnalyzer:
    """MediaPipe 기반 표정 분석기"""

    # 주요 랜드마크 인덱스
    MOUTH_LEFT = 61
    MOUTH_RIGHT = 291
    MOUTH_TOP = 13
    MOUTH_BOTTOM = 14
    LEFT_EYE_CENTER = 468  # Iris
    RIGHT_EYE_CENTER = 473  # Iris
    NOSE_TIP = 1
    FOREHEAD = 10

    def __init__(self):
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError("MediaPipe가 설치되지 않았습니다. pip install mediapipe")

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,  # 홍채 랜드마크 포함
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.landmarks_history: List[np.ndarray] = []

    def process_frame(self, frame: np.ndarray) -> Optional[FaceAnalysisResult]:
        """
        프레임 분석

        Args:
            frame: BGR 이미지 (OpenCV 형식)

        Returns:
            FaceAnalysisResult 또는 None (얼굴 미감지 시)
        """
        # RGB 변환
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None

        landmarks = results.multi_face_landmarks[0].landmark

        # 랜드마크를 numpy 배열로 변환
        h, w = frame.shape[:2]
        points = np.array([
            [lm.x * w, lm.y * h, lm.z * w]
            for lm in landmarks
        ])

        # 히스토리에 추가 (최근 30프레임)
        self.landmarks_history.append(points)
        if len(self.landmarks_history) > 30:
            self.landmarks_history.pop(0)

        # 분석 수행
        smile_score = self._calculate_smile_score(points)
        eye_contact = self._calculate_eye_contact(points, w)
        head_tilt = self._calculate_head_tilt(points)
        stability = self._calculate_stability()

        # 피드백 메시지 생성
        feedback = self._generate_feedback(smile_score, eye_contact, head_tilt, stability)

        return FaceAnalysisResult(
            smile_score=smile_score,
            eye_contact=eye_contact,
            head_tilt=head_tilt,
            stability_score=stability,
            feedback_messages=feedback
        )

    def _calculate_smile_score(self, points: np.ndarray) -> float:
        """미소 점수 계산 (입꼬리 높이 기반)"""
        # 입꼬리 좌우 높이
        left_corner = points[self.MOUTH_LEFT]
        right_corner = points[self.MOUTH_RIGHT]
        mouth_center = points[self.MOUTH_TOP]

        # 입꼬리가 입 중앙보다 올라간 정도
        left_lift = mouth_center[1] - left_corner[1]
        right_lift = mouth_center[1] - right_corner[1]

        avg_lift = (left_lift + right_lift) / 2

        # 정규화 (경험적 값 기반)
        score = min(100, max(0, avg_lift * 5 + 50))
        return round(score, 1)

    def _calculate_eye_contact(self, points: np.ndarray, frame_width: int) -> bool:
        """눈 맞춤 여부 (홍채가 눈 중앙에 있는지)"""
        # 홍채 위치 확인 (refine_landmarks=True 필요)
        try:
            left_iris = points[self.LEFT_EYE_CENTER]
            right_iris = points[self.RIGHT_EYE_CENTER]

            # 얼굴 중앙 기준
            face_center_x = frame_width / 2

            # 홍채가 화면 중앙 근처를 보고 있는지
            iris_center_x = (left_iris[0] + right_iris[0]) / 2
            deviation = abs(iris_center_x - face_center_x) / frame_width

            return deviation < 0.15  # 15% 이내면 눈 맞춤
        except:
            return False

    def _calculate_head_tilt(self, points: np.ndarray) -> float:
        """고개 기울기 (도 단위)"""
        nose = points[self.NOSE_TIP]
        forehead = points[self.FOREHEAD]

        # 코끝-이마 벡터의 기울기
        dx = forehead[0] - nose[0]
        dy = forehead[1] - nose[1]

        angle = np.degrees(np.arctan2(dx, dy))
        return round(angle, 1)

    def _calculate_stability(self) -> float:
        """표정 안정성 (변화량 기반)"""
        if len(self.landmarks_history) < 5:
            return 100.0

        # 최근 5프레임의 변화량
        recent = self.landmarks_history[-5:]
        variations = []

        for i in range(1, len(recent)):
            diff = np.mean(np.abs(recent[i] - recent[i-1]))
            variations.append(diff)

        avg_variation = np.mean(variations)

        # 변화량이 작을수록 안정적
        stability = max(0, 100 - avg_variation * 10)
        return round(stability, 1)

    def _generate_feedback(
        self,
        smile: float,
        eye_contact: bool,
        tilt: float,
        stability: float
    ) -> List[str]:
        """피드백 메시지 생성 (수치 기반만)"""
        messages = []

        # 미소
        if smile >= 70:
            messages.append("좋습니다! 자연스러운 미소가 유지되고 있습니다.")
        elif smile >= 40:
            messages.append("입꼬리를 조금 더 올려주세요.")
        else:
            messages.append("표정이 경직되어 있습니다. 미소를 지어보세요.")

        # 눈 맞춤
        if eye_contact:
            messages.append("카메라 응시가 잘 되고 있습니다.")
        else:
            messages.append("카메라를 정면으로 바라봐 주세요.")

        # 고개 기울기
        if abs(tilt) <= 5:
            pass  # 정상
        elif tilt > 5:
            messages.append(f"고개가 오른쪽으로 {tilt:.0f}도 기울어져 있습니다.")
        else:
            messages.append(f"고개가 왼쪽으로 {abs(tilt):.0f}도 기울어져 있습니다.")

        # 안정성
        if stability < 60:
            messages.append("표정 변화가 많습니다. 안정적으로 유지해보세요.")

        return messages

    def reset_history(self):
        """히스토리 초기화"""
        self.landmarks_history.clear()

    def close(self):
        """리소스 해제"""
        self.face_mesh.close()


def draw_feedback_overlay(
    frame: np.ndarray,
    result: FaceAnalysisResult
) -> np.ndarray:
    """프레임에 피드백 오버레이 그리기"""
    if not MEDIAPIPE_AVAILABLE:
        return frame

    overlay = frame.copy()
    h, w = frame.shape[:2]

    # 미소 게이지 바
    bar_width = 200
    bar_height = 20
    bar_x = 20
    bar_y = 30

    # 배경
    cv2.rectangle(overlay, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)

    # 미소 점수 바
    fill_width = int(bar_width * result.smile_score / 100)
    color = (0, 255, 0) if result.smile_score >= 60 else (0, 255, 255) if result.smile_score >= 40 else (0, 0, 255)
    cv2.rectangle(overlay, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), color, -1)

    # 레이블
    cv2.putText(overlay, f"Smile: {result.smile_score:.0f}%", (bar_x, bar_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # 눈 맞춤 인디케이터
    eye_color = (0, 255, 0) if result.eye_contact else (0, 0, 255)
    cv2.circle(overlay, (bar_x + bar_width + 30, bar_y + 10), 10, eye_color, -1)
    cv2.putText(overlay, "Eye Contact", (bar_x + bar_width + 50, bar_y + 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # 알파 블렌딩
    result_frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    return result_frame


def is_available() -> bool:
    """MediaPipe 사용 가능 여부"""
    return MEDIAPIPE_AVAILABLE
