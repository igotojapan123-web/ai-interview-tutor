#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 웹캠 컴포넌트 비디오 크기 수정

import os

path = os.path.join(os.path.dirname(__file__), "webcam_component.py")

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_section = '''def create_webcam_streamer(
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
    }'''

new_section = '''def create_webcam_streamer(
    key: str = "interview_webcam",
    on_feedback: Optional[Callable[[List[RealtimeFeedback]], None]] = None,
    show_video: bool = True,
    analysis_enabled: bool = True,
    compact: bool = True,  # 작은 크기 모드
) -> Optional[Dict[str, Any]]:
    """
    웹캠 스트리머 생성

    Args:
        key: Streamlit 컴포넌트 키
        on_feedback: 피드백 콜백 함수
        show_video: 비디오 표시 여부
        analysis_enabled: 분석 활성화 여부
        compact: 작은 크기 모드 (기본 True)

    Returns:
        웹캠 컨텍스트 또는 None
    """
    import streamlit as st

    if not WEBRTC_AVAILABLE:
        return None

    # 비디오 크기 제한 CSS (compact 모드)
    if compact:
        st.markdown("""
        <style>
        /* 웹캠 비디오 크기 제한 */
        [data-testid="stVerticalBlock"] video {
            max-width: 280px !important;
            max-height: 210px !important;
            border-radius: 8px;
            border: 2px solid #e5e7eb;
        }
        iframe[title*="webrtc"], iframe[src*="webrtc"] {
            max-width: 300px !important;
            max-height: 250px !important;
        }
        </style>
        """, unsafe_allow_html=True)

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

    # webrtc 스트리머 생성 (작은 해상도)
    video_width = 320 if compact else 640
    video_height = 240 if compact else 480

    ctx = webrtc_streamer(
        key=key,
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=rtc_config,
        video_processor_factory=lambda: processor,
        media_stream_constraints={
            "video": {
                "width": {"ideal": video_width, "max": video_width},
                "height": {"ideal": video_height, "max": video_height},
                "frameRate": {"ideal": 15, "max": 20}
            },
            "audio": False  # 오디오는 별도 처리
        },
        async_processing=True,
    )

    return {
        "context": ctx,
        "processor": processor,
        "is_playing": ctx.state.playing if ctx else False,
    }'''

if old_section in content:
    content = content.replace(old_section, new_section)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("webcam_component.py 비디오 크기 수정 완료")
else:
    print("수정할 섹션을 찾을 수 없습니다")
    # 디버깅: 찾지 못한 경우
    if "def create_webcam_streamer" in content:
        print("함수는 존재하지만 형식이 다릅니다")
