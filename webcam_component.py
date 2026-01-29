# webcam_component.py
# Phase 2: Streamlit 웹캠 컴포넌트 (streamlit-webrtc 기반)

import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
import queue
import threading

logger = logging.getLogger(__name__)

# streamlit-webrtc 가용성 확인
WEBRTC_AVAILABLE = False
try:
    from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
    import av
    WEBRTC_AVAILABLE = True
except ImportError:
    logger.warning("streamlit-webrtc not installed. Run: pip install streamlit-webrtc av")

# webcam_analyzer import
try:
    from webcam_analyzer import (
        get_webcam_analyzer,
        is_webcam_analysis_available,
        RealtimeFeedback,
        FeedbackPriority,
    )
    ANALYZER_AVAILABLE = True
except ImportError:
    ANALYZER_AVAILABLE = False
    logger.warning("webcam_analyzer not available")

try:
    import numpy as np
except ImportError:
    np = None


@dataclass
class WebcamSessionState:
    """웹캠 세션 상태"""
    is_active: bool = False
    frame_count: int = 0
    feedback_history: List[Dict[str, Any]] = field(default_factory=list)
    score_history: List[float] = field(default_factory=list)
    current_feedback: List[RealtimeFeedback] = field(default_factory=list)
    average_score: float = 0.0


class VideoProcessor:
    """실시간 비디오 프로세서 (streamlit-webrtc 콜백)"""

    def __init__(self):
        self.analyzer = None
        self.feedback_queue = queue.Queue(maxsize=10)
        self.score_queue = queue.Queue(maxsize=10)
        self.frame_count = 0
        self.analysis_interval = 3  # 3프레임마다 분석 (성능 최적화)
        self._lock = threading.Lock()

    def initialize_analyzer(self):
        """분석기 초기화"""
        if ANALYZER_AVAILABLE:
            self.analyzer = get_webcam_analyzer()

    def recv(self, frame: 'av.VideoFrame') -> 'av.VideoFrame':
        """
        프레임 수신 콜백 (streamlit-webrtc에서 호출)

        Args:
            frame: av.VideoFrame 객체

        Returns:
            처리된 av.VideoFrame
        """
        self.frame_count += 1

        # numpy 배열로 변환
        img = frame.to_ndarray(format="bgr24")

        # 분석 (일정 간격마다)
        if self.analyzer and self.frame_count % self.analysis_interval == 0:
            try:
                result = self.analyzer.analyze_frame(img)

                # 피드백 큐에 추가
                if result.get("feedback"):
                    try:
                        self.feedback_queue.put_nowait(result["feedback"])
                    except queue.Full:
                        pass

                # 점수 큐에 추가
                score = result.get("overall_score", 0)
                try:
                    self.score_queue.put_nowait(score)
                except queue.Full:
                    pass

                # 시각화 오버레이 (선택적)
                # img = self.analyzer.get_annotated_frame(img)

            except Exception as e:
                logger.warning(f"Frame processing error: {e}")

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def get_latest_feedback(self) -> List[RealtimeFeedback]:
        """최신 피드백 가져오기"""
        feedback_list = []
        try:
            while not self.feedback_queue.empty():
                feedback_list = self.feedback_queue.get_nowait()
        except queue.Empty:
            pass
        return feedback_list

    def get_average_score(self) -> float:
        """평균 점수 계산"""
        scores = []
        try:
            while not self.score_queue.empty():
                scores.append(self.score_queue.get_nowait())
        except queue.Empty:
            pass

        if scores:
            return sum(scores) / len(scores)
        return 0.0


def create_webcam_streamer(
    key: str = "interview_webcam",
    on_feedback: Optional[Callable[[List[RealtimeFeedback]], None]] = None,
    show_video: bool = True,
    analysis_enabled: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    웹캠 스트리머 생성

    Args:
        key: Streamlit 컴포넌트 키
        on_feedback: 피드백 콜백 함수
        show_video: 비디오 표시 여부
        analysis_enabled: 분석 활성화 여부

    Returns:
        웹캠 컨텍스트 또는 None
    """
    if not WEBRTC_AVAILABLE:
        return None

    # RTC 설정 (STUN 서버)
    rtc_config = RTCConfiguration({
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
        ]
    })

    # 비디오 프로세서 생성
    processor = VideoProcessor()
    if analysis_enabled and ANALYZER_AVAILABLE:
        processor.initialize_analyzer()

    # webrtc 스트리머 생성
    ctx = webrtc_streamer(
        key=key,
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_config,
        video_processor_factory=lambda: processor,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 640},
                "height": {"ideal": 480},
                "frameRate": {"ideal": 15, "max": 30}
            },
            "audio": False  # 오디오는 별도 처리
        },
        async_processing=True,
    )

    return {
        "context": ctx,
        "processor": processor,
        "is_playing": ctx.state.playing if ctx else False,
    }


def get_realtime_feedback_html(feedback_list: List[RealtimeFeedback]) -> str:
    """실시간 피드백을 HTML로 변환"""
    if not feedback_list:
        return """
        <div style="
            padding: 15px;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-radius: 12px;
            color: white;
            text-align: center;
        ">
            <span style="font-size: 24px;">✅</span>
            <p style="margin: 10px 0 0 0; font-weight: 500;">자세가 좋습니다!</p>
        </div>
        """

    # 우선순위별 색상
    priority_colors = {
        "high": "#ef4444",
        "medium": "#f59e0b",
        "low": "#3b82f6",
    }

    priority_icons = {
        "high": "⚠️",
        "medium": "💡",
        "low": "ℹ️",
    }

    feedback_html = ""
    for fb in feedback_list[:3]:  # 최대 3개만 표시
        color = priority_colors.get(fb.priority.value, "#6b7280")
        icon = priority_icons.get(fb.priority.value, "💡")

        feedback_html += f"""
        <div style="
            padding: 12px 15px;
            background: white;
            border-left: 4px solid {color};
            border-radius: 8px;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        ">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">{icon}</span>
                <span style="font-weight: 600; color: #1f2937;">{fb.message}</span>
            </div>
            <p style="margin: 5px 0 0 20px; font-size: 13px; color: #6b7280;">
                {fb.suggestion}
            </p>
        </div>
        """

    return f"""
    <div style="
        padding: 15px;
        background: #f8fafc;
        border-radius: 12px;
    ">
        <h4 style="margin: 0 0 12px 0; color: #374151; font-size: 14px;">
            📹 실시간 피드백
        </h4>
        {feedback_html}
    </div>
    """


def get_score_gauge_html(score: float) -> str:
    """점수 게이지 HTML"""
    # 색상 결정
    if score >= 80:
        color = "#10b981"
        label = "우수"
    elif score >= 60:
        color = "#f59e0b"
        label = "양호"
    else:
        color = "#ef4444"
        label = "개선필요"

    percentage = min(100, max(0, score))

    return f"""
    <div style="
        padding: 20px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    ">
        <div style="
            width: 120px;
            height: 120px;
            margin: 0 auto 15px;
            position: relative;
        ">
            <svg viewBox="0 0 36 36" style="transform: rotate(-90deg);">
                <path
                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="#e5e7eb"
                    stroke-width="3"
                />
                <path
                    d="M18 2.0845
                    a 15.9155 15.9155 0 0 1 0 31.831
                    a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="{color}"
                    stroke-width="3"
                    stroke-dasharray="{percentage}, 100"
                    stroke-linecap="round"
                />
            </svg>
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
            ">
                <div style="font-size: 28px; font-weight: 700; color: {color};">
                    {score:.0f}
                </div>
                <div style="font-size: 12px; color: #6b7280;">점</div>
            </div>
        </div>
        <div style="
            display: inline-block;
            padding: 4px 12px;
            background: {color}20;
            color: {color};
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        ">
            {label}
        </div>
    </div>
    """


def get_webcam_placeholder_html() -> str:
    """웹캠 미사용 시 플레이스홀더"""
    return """
    <div style="
        padding: 40px 20px;
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        border-radius: 16px;
        text-align: center;
        border: 2px dashed #d1d5db;
    ">
        <div style="font-size: 48px; margin-bottom: 15px;">📹</div>
        <h3 style="margin: 0 0 10px 0; color: #374151;">웹캠 분석 (선택사항)</h3>
        <p style="margin: 0; color: #6b7280; font-size: 14px;">
            웹캠을 켜면 자세, 시선, 표정을 실시간으로 분석합니다.
        </p>
        <div style="
            margin-top: 20px;
            padding: 10px 15px;
            background: white;
            border-radius: 8px;
            display: inline-block;
        ">
            <span style="color: #059669;">✅</span>
            <span style="color: #374151; font-size: 13px; margin-left: 5px;">
                웹캠 없이도 음성 면접이 가능합니다
            </span>
        </div>
    </div>
    """


def is_webcam_available() -> bool:
    """웹캠 기능 사용 가능 여부"""
    return WEBRTC_AVAILABLE and ANALYZER_AVAILABLE


# 사용 예시를 위한 Streamlit 앱 코드
def demo_webcam_analysis():
    """데모용 함수 (직접 실행 시)"""
    import streamlit as st

    st.set_page_config(page_title="웹캠 분석 데모", layout="wide")
    st.title("📹 실시간 웹캠 분석 데모")

    if not is_webcam_available():
        st.error("웹캠 분석 기능을 사용할 수 없습니다. 필요한 패키지를 설치해주세요.")
        st.code("pip install streamlit-webrtc av mediapipe opencv-python")
        return

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("웹캠")
        webcam = create_webcam_streamer(key="demo_webcam")

        if webcam and webcam["is_playing"]:
            st.success("웹캠 활성화됨")

    with col2:
        st.subheader("실시간 피드백")

        # 피드백 표시 영역
        feedback_placeholder = st.empty()
        score_placeholder = st.empty()

        if webcam and webcam["is_playing"]:
            processor = webcam["processor"]

            # 주기적으로 피드백 업데이트
            feedback = processor.get_latest_feedback()
            score = processor.get_average_score()

            feedback_placeholder.markdown(
                get_realtime_feedback_html(feedback),
                unsafe_allow_html=True
            )
            score_placeholder.markdown(
                get_score_gauge_html(score),
                unsafe_allow_html=True
            )
        else:
            feedback_placeholder.markdown(
                get_webcam_placeholder_html(),
                unsafe_allow_html=True
            )


if __name__ == "__main__":
    demo_webcam_analysis()
