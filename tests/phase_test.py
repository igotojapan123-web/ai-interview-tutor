# phase_test.py
# Phase 1 & 2 실제 기능 테스트 스크립트
# 솔직하고 정확한 테스트 결과 보고

import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(name, status, detail=""):
    icon = "[OK]" if status else "[FAIL]"
    print(f"  {icon} {name}")
    if detail:
        print(f"       -> {detail}")

def test_phase1_video():
    """Phase 1: D-ID 영상 면접관 테스트"""
    print_section("Phase 1: D-ID 영상 면접관 테스트")

    results = {"passed": 0, "failed": 0, "warnings": []}

    # 1. video_utils import 테스트
    try:
        from video_utils import (
            check_did_api_available,
            create_interviewer_video,
            get_video_html,
            get_fallback_avatar_html,
            get_enhanced_fallback_avatar_html,
            get_did_api_key,
        )
        print_result("video_utils import", True)
        results["passed"] += 1
    except ImportError as e:
        print_result("video_utils import", False, str(e))
        results["failed"] += 1
        return results

    # 2. D-ID API 키 확인
    api_key = get_did_api_key()
    if api_key:
        print_result("D-ID API 키 존재", True, f"키 길이: {len(api_key)}자")
        results["passed"] += 1

        # 3. API 연결 테스트
        is_available = check_did_api_available()
        if is_available:
            print_result("D-ID API 연결", True, "실제 영상 생성 가능")
            results["passed"] += 1
        else:
            print_result("D-ID API 연결", False, "API 키가 유효하지 않거나 크레딧 부족")
            results["failed"] += 1
            results["warnings"].append("D-ID API 연결 실패 - 폴백 아바타만 사용 가능")
    else:
        print_result("D-ID API 키 존재", False, "환경변수 DID_API_KEY 또는 D_ID_API_KEY 없음")
        results["failed"] += 1
        results["warnings"].append("D-ID API 키 없음 - 실제 영상 생성 불가, CSS 아바타만 표시됨")

    # 4. 폴백 아바타 HTML 생성 테스트
    try:
        html = get_enhanced_fallback_avatar_html("테스트 질문입니다", "interviewer", "neutral")
        if "<div" in html and "avatar" in html.lower():
            print_result("폴백 아바타 HTML 생성", True, f"HTML 길이: {len(html)}자")
            results["passed"] += 1
        else:
            print_result("폴백 아바타 HTML 생성", False, "HTML 형식이 올바르지 않음")
            results["failed"] += 1
    except Exception as e:
        print_result("폴백 아바타 HTML 생성", False, str(e))
        results["failed"] += 1

    return results


def test_phase1_emotion():
    """Phase 1: 음성 감정 분석 테스트"""
    print_section("Phase 1: 음성 감정 분석 테스트")

    results = {"passed": 0, "failed": 0, "warnings": []}

    # 1. voice_utils import 테스트
    try:
        from voice_utils import (
            analyze_interview_emotion,
            extract_voice_features_for_emotion,
            get_default_emotion_result,
        )
        print_result("voice_utils 감정 분석 함수 import", True)
        results["passed"] += 1
    except ImportError as e:
        print_result("voice_utils 감정 분석 함수 import", False, str(e))
        results["failed"] += 1
        return results

    # 2. librosa 패키지 확인
    try:
        import librosa
        print_result("librosa 패키지 설치됨", True, f"버전: {librosa.__version__}")
        results["passed"] += 1
        librosa_available = True
    except ImportError:
        print_result("librosa 패키지 설치됨", False, "pip install librosa 필요")
        results["failed"] += 1
        results["warnings"].append("librosa 미설치 - 감정 분석이 기본값만 반환됨")
        librosa_available = False

    # 3. numpy 확인
    try:
        import numpy as np
        print_result("numpy 패키지 설치됨", True, f"버전: {np.__version__}")
        results["passed"] += 1
    except ImportError:
        print_result("numpy 패키지 설치됨", False)
        results["failed"] += 1

    # 4. 기본값 반환 테스트
    try:
        default_result = get_default_emotion_result()
        required_keys = ["confidence_score", "stress_level", "engagement_level", "emotion_stability", "primary_emotion"]
        if all(key in default_result for key in required_keys):
            print_result("기본 감정 분석 결과 형식", True)
            results["passed"] += 1
        else:
            print_result("기본 감정 분석 결과 형식", False, "필수 키 누락")
            results["failed"] += 1
    except Exception as e:
        print_result("기본 감정 분석 결과 형식", False, str(e))
        results["failed"] += 1

    # 5. 실제 분석 테스트 (더미 데이터)
    if librosa_available:
        print("  [INFO] 실제 음성 파일 분석 테스트는 음성 파일이 필요합니다")
        results["warnings"].append("실제 음성 분석은 음성 파일 녹음 후 테스트 가능")

    return results


def test_phase2_webcam():
    """Phase 2: 웹캠 분석 테스트"""
    print_section("Phase 2: 웹캠 분석 테스트")

    results = {"passed": 0, "failed": 0, "warnings": []}

    # 1. webcam_analyzer import 테스트
    try:
        from webcam_analyzer import (
            WebcamAnalyzer,
            get_webcam_analyzer,
            is_webcam_analysis_available,
            MEDIAPIPE_AVAILABLE,
            OPENCV_AVAILABLE,
        )
        print_result("webcam_analyzer import", True)
        results["passed"] += 1
    except ImportError as e:
        print_result("webcam_analyzer import", False, str(e))
        results["failed"] += 1
        return results

    # 2. OpenCV 확인
    if OPENCV_AVAILABLE:
        import cv2
        print_result("OpenCV 설치됨", True, f"버전: {cv2.__version__}")
        results["passed"] += 1
    else:
        print_result("OpenCV 설치됨", False, "pip install opencv-python 필요")
        results["failed"] += 1
        results["warnings"].append("OpenCV 미설치 - 웹캠 분석 불가")

    # 3. MediaPipe 확인
    if MEDIAPIPE_AVAILABLE:
        import mediapipe as mp
        print_result("MediaPipe 설치됨", True)
        results["passed"] += 1
    else:
        print_result("MediaPipe 설치됨", False, "pip install mediapipe 필요")
        results["failed"] += 1
        results["warnings"].append("MediaPipe 미설치 - 얼굴/자세 분석 불가")

    # 4. 분석 기능 가용성
    is_available = is_webcam_analysis_available()
    if is_available:
        print_result("웹캠 분석 기능 사용 가능", True)
        results["passed"] += 1
    else:
        print_result("웹캠 분석 기능 사용 가능", False, "패키지 미설치로 비활성화됨")
        results["failed"] += 1

    # 5. webcam_component import 테스트
    try:
        from webcam_component import (
            create_webcam_streamer,
            get_realtime_feedback_html,
            get_score_gauge_html,
            get_webcam_placeholder_html,
            is_webcam_available,
            WEBRTC_AVAILABLE,
        )
        print_result("webcam_component import", True)
        results["passed"] += 1

        # streamlit-webrtc 확인
        if WEBRTC_AVAILABLE:
            print_result("streamlit-webrtc 설치됨", True)
            results["passed"] += 1
        else:
            print_result("streamlit-webrtc 설치됨", False, "pip install streamlit-webrtc av 필요")
            results["failed"] += 1
            results["warnings"].append("streamlit-webrtc 미설치 - 웹캠 스트리밍 불가")

    except ImportError as e:
        print_result("webcam_component import", False, str(e))
        results["failed"] += 1

    # 6. HTML 생성 함수 테스트
    try:
        from webcam_component import get_score_gauge_html, get_webcam_placeholder_html

        gauge_html = get_score_gauge_html(75.5)
        if "<div" in gauge_html and "75" in gauge_html:
            print_result("점수 게이지 HTML 생성", True)
            results["passed"] += 1
        else:
            print_result("점수 게이지 HTML 생성", False)
            results["failed"] += 1

        placeholder_html = get_webcam_placeholder_html()
        if "<div" in placeholder_html:
            print_result("웹캠 플레이스홀더 HTML 생성", True)
            results["passed"] += 1
        else:
            print_result("웹캠 플레이스홀더 HTML 생성", False)
            results["failed"] += 1

    except Exception as e:
        print_result("HTML 생성 함수 테스트", False, str(e))
        results["failed"] += 1

    return results


def test_mock_interview_integration():
    """모의면접 페이지 통합 테스트"""
    print_section("모의면접 페이지 통합 테스트")

    results = {"passed": 0, "failed": 0, "warnings": []}

    # 모의면접 파일 문법 검사
    mock_interview_path = os.path.join(os.path.dirname(__file__), "pages", "4_모의면접.py")

    try:
        with open(mock_interview_path, "r", encoding="utf-8") as f:
            code = f.read()

        # 문법 검사
        compile(code, mock_interview_path, "exec")
        print_result("모의면접.py 문법 검사", True)
        results["passed"] += 1

        # 필수 import 확인
        required_imports = [
            "analyze_interview_emotion",  # Phase 1
            "get_enhanced_fallback_avatar_html",  # Phase 1
            "create_webcam_streamer",  # Phase 2
            "get_realtime_feedback_html",  # Phase 2
            "mock_emotion_analyses",  # Phase 1 세션 변수
            "mock_webcam_enabled",  # Phase 2 세션 변수
        ]

        for imp in required_imports:
            if imp in code:
                print_result(f"'{imp}' 코드에 존재", True)
                results["passed"] += 1
            else:
                print_result(f"'{imp}' 코드에 존재", False)
                results["failed"] += 1

    except SyntaxError as e:
        print_result("모의면접.py 문법 검사", False, f"Line {e.lineno}: {e.msg}")
        results["failed"] += 1
    except FileNotFoundError:
        print_result("모의면접.py 파일 존재", False, "파일을 찾을 수 없습니다")
        results["failed"] += 1
    except Exception as e:
        print_result("모의면접 통합 테스트", False, str(e))
        results["failed"] += 1

    return results


def main():
    print("\n" + "#" * 60)
    print("#  FlyReady Lab - Phase 1 & 2 실제 기능 테스트")
    print("#  날짜: 2025-01-29")
    print("#  목적: 솔직하고 정확한 기능 작동 확인")
    print("#" * 60)

    all_results = {
        "total_passed": 0,
        "total_failed": 0,
        "all_warnings": [],
    }

    # Phase 1 테스트
    video_results = test_phase1_video()
    emotion_results = test_phase1_emotion()

    # Phase 2 테스트
    webcam_results = test_phase2_webcam()

    # 통합 테스트
    integration_results = test_mock_interview_integration()

    # 결과 집계
    for r in [video_results, emotion_results, webcam_results, integration_results]:
        all_results["total_passed"] += r["passed"]
        all_results["total_failed"] += r["failed"]
        all_results["all_warnings"].extend(r.get("warnings", []))

    # 최종 결과
    print_section("최종 결과")
    print(f"\n  통과: {all_results['total_passed']}")
    print(f"  실패: {all_results['total_failed']}")

    if all_results["all_warnings"]:
        print("\n  [경고 사항]")
        for i, warning in enumerate(all_results["all_warnings"], 1):
            print(f"  {i}. {warning}")

    # 솔직한 요약
    print_section("솔직한 현실 요약")

    # D-ID 확인
    try:
        from video_utils import get_did_api_key, check_did_api_available
        if get_did_api_key() and check_did_api_available():
            print("  - D-ID 영상 면접관: 실제 작동 가능")
        else:
            print("  - D-ID 영상 면접관: CSS 애니메이션 아바타만 표시 (실제 영상 아님)")
    except:
        print("  - D-ID 영상 면접관: 확인 불가")

    # librosa 확인
    try:
        import librosa
        print("  - 음성 감정 분석: librosa 설치됨, 실제 분석 가능")
    except:
        print("  - 음성 감정 분석: librosa 미설치, 기본값만 반환됨 (실제 분석 안됨)")

    # MediaPipe/WebRTC 확인
    try:
        from webcam_analyzer import MEDIAPIPE_AVAILABLE, OPENCV_AVAILABLE
        from webcam_component import WEBRTC_AVAILABLE

        if MEDIAPIPE_AVAILABLE and OPENCV_AVAILABLE and WEBRTC_AVAILABLE:
            print("  - 웹캠 분석: 모든 패키지 설치됨, 실제 작동 가능")
        else:
            missing = []
            if not OPENCV_AVAILABLE:
                missing.append("OpenCV")
            if not MEDIAPIPE_AVAILABLE:
                missing.append("MediaPipe")
            if not WEBRTC_AVAILABLE:
                missing.append("streamlit-webrtc")
            print(f"  - 웹캠 분석: 미설치 패키지 있음 ({', '.join(missing)}) - 기능 비활성화됨")
    except:
        print("  - 웹캠 분석: 확인 불가")

    print("\n" + "=" * 60)

    return all_results["total_failed"] == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
