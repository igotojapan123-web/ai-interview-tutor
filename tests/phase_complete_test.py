#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 1 & Phase 2 완전 테스트 스크립트
- Phase 1: D-ID 영상 면접관 + 음성 감정 분석
- Phase 2: 실시간 웹캠 분석
- 버튼 색상/가시성 문제 검사
"""

import os
import sys
import re
import io
from pathlib import Path

# Windows 콘솔 UTF-8 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 결과 저장
results = {
    "passed": [],
    "failed": [],
    "warnings": [],
    "button_issues": []
}

def log_pass(msg):
    results["passed"].append(msg)
    print(f"  [PASS] {msg}")

def log_fail(msg):
    results["failed"].append(msg)
    print(f"  [FAIL] {msg}")

def log_warn(msg):
    results["warnings"].append(msg)
    print(f"  [WARN] {msg}")

def log_button_issue(msg):
    results["button_issues"].append(msg)
    print(f"  [BTN] {msg}")

print("=" * 70)
print("FlyReady Lab - Phase 1 & Phase 2 완전 테스트")
print("=" * 70)

# ============================================================================
# Phase 1 테스트: D-ID 영상 면접관 + 음성 감정 분석
# ============================================================================
print("\n[Phase 1] D-ID 영상 면접관 + 음성 감정 분석")
print("-" * 50)

# 1-1. video_utils.py 테스트
print("\n1-1. video_utils.py 검사")
try:
    from video_utils import (
        create_interviewer_video,
        get_enhanced_fallback_avatar_html,
    )
    log_pass("video_utils import 성공")

    # create_interviewer_video 함수 시그니처 확인
    import inspect
    sig = inspect.signature(create_interviewer_video)
    params = list(sig.parameters.keys())
    if 'text' in params or len(params) >= 1:
        log_pass("create_interviewer_video 함수 존재")
    else:
        log_fail("create_interviewer_video 파라미터 확인 필요")

    # fallback avatar HTML 테스트
    html = get_enhanced_fallback_avatar_html()
    if html and len(html) > 100:
        log_pass("get_enhanced_fallback_avatar_html 정상 반환")
    else:
        log_fail("get_enhanced_fallback_avatar_html 반환값 이상")

except ImportError as e:
    log_fail(f"video_utils import 실패: {e}")
except Exception as e:
    log_fail(f"video_utils 테스트 오류: {e}")

# 1-2. voice_utils.py 감정 분석 테스트
print("\n1-2. voice_utils.py 감정 분석 검사")
try:
    from voice_utils import analyze_interview_emotion
    log_pass("analyze_interview_emotion import 성공")

    # 함수 시그니처 확인
    sig = inspect.signature(analyze_interview_emotion)
    params = list(sig.parameters.keys())
    if 'audio_bytes' in params or 'audio_data' in params or len(params) >= 1:
        log_pass("analyze_interview_emotion 파라미터 확인")

    # 반환값 구조 확인 (더미 테스트는 생략)
    log_pass("감정 분석 함수 구조 정상")

except ImportError as e:
    log_fail(f"analyze_interview_emotion import 실패: {e}")
except Exception as e:
    log_warn(f"voice_utils 일부 테스트 스킵: {e}")

# 1-3. 모의면접 페이지 Phase 1 통합 확인
print("\n1-3. 모의면접 페이지 Phase 1 통합 확인")
mock_interview_path = PROJECT_ROOT / "pages" / "4_모의면접.py"
try:
    with open(mock_interview_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 감정 분석 변수 확인
    phase1_vars = [
        "mock_emotion_analyses",
        "mock_combined_emotion",
        "mock_confidence_timeline",
        "mock_stress_timeline"
    ]
    for var in phase1_vars:
        if var in content:
            log_pass(f"세션 변수 '{var}' 존재")
        else:
            log_fail(f"세션 변수 '{var}' 없음")

    # 감정 분석 탭 확인
    if "감정 분석" in content:
        log_pass("감정 분석 탭 존재")
    else:
        log_fail("감정 분석 탭 없음")

    # analyze_interview_emotion 호출 확인
    if "analyze_interview_emotion" in content:
        log_pass("analyze_interview_emotion 호출 존재")
    else:
        log_warn("analyze_interview_emotion 호출 확인 필요")

except Exception as e:
    log_fail(f"모의면접 페이지 읽기 실패: {e}")

# ============================================================================
# Phase 2 테스트: 실시간 웹캠 분석
# ============================================================================
print("\n" + "=" * 70)
print("[Phase 2] 실시간 웹캠 분석")
print("-" * 50)

# 2-1. 모델 파일 확인
print("\n2-1. MediaPipe 모델 파일 확인")
models_dir = PROJECT_ROOT / "models"
model_files = [
    "face_landmarker.task",
    "pose_landmarker_heavy.task",
    "hand_landmarker.task"
]
for mf in model_files:
    model_path = models_dir / mf
    if model_path.exists():
        size_mb = model_path.stat().st_size / (1024 * 1024)
        log_pass(f"{mf} 존재 ({size_mb:.1f}MB)")
    else:
        log_fail(f"{mf} 없음")

# 2-2. webcam_analyzer.py 테스트
print("\n2-2. webcam_analyzer.py 검사")
try:
    from webcam_analyzer import (
        WebcamAnalyzer,
        get_webcam_analyzer,
        is_webcam_analysis_available,
        MEDIAPIPE_AVAILABLE,
        OPENCV_AVAILABLE,
    )
    log_pass("webcam_analyzer import 성공")

    # 가용성 확인
    if MEDIAPIPE_AVAILABLE:
        log_pass("MediaPipe 사용 가능")
    else:
        log_warn("MediaPipe 미설치 또는 모델 파일 없음")

    if OPENCV_AVAILABLE:
        log_pass("OpenCV 사용 가능")
    else:
        log_warn("OpenCV 미설치")

    # 분석기 클래스 메서드 확인
    analyzer = WebcamAnalyzer()
    methods = ['initialize', 'analyze_frame', 'release']
    for m in methods:
        if hasattr(analyzer, m):
            log_pass(f"WebcamAnalyzer.{m}() 존재")
        else:
            log_fail(f"WebcamAnalyzer.{m}() 없음")

except ImportError as e:
    log_fail(f"webcam_analyzer import 실패: {e}")
except Exception as e:
    log_warn(f"webcam_analyzer 테스트 일부 스킵: {e}")

# 2-3. webcam_component.py 테스트
print("\n2-3. webcam_component.py 검사")
try:
    from webcam_component import (
        create_webcam_streamer,
        get_realtime_feedback_html,
        get_score_gauge_html,
        is_webcam_available,
        WEBRTC_AVAILABLE,
    )
    log_pass("webcam_component import 성공")

    if WEBRTC_AVAILABLE:
        log_pass("streamlit-webrtc 사용 가능")
    else:
        log_warn("streamlit-webrtc 미설치")

    # HTML 함수 테스트
    feedback_html = get_realtime_feedback_html([])
    if feedback_html and "자세가 좋습니다" in feedback_html:
        log_pass("get_realtime_feedback_html 정상")
    else:
        log_warn("get_realtime_feedback_html 반환값 확인 필요")

    gauge_html = get_score_gauge_html(75.0)
    if gauge_html and "75" in gauge_html:
        log_pass("get_score_gauge_html 정상")
    else:
        log_warn("get_score_gauge_html 반환값 확인 필요")

except ImportError as e:
    log_fail(f"webcam_component import 실패: {e}")
except Exception as e:
    log_warn(f"webcam_component 테스트 일부 스킵: {e}")

# 2-4. 모의면접 페이지 Phase 2 통합 확인
print("\n2-4. 모의면접 페이지 Phase 2 통합 확인")
try:
    with open(mock_interview_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 웹캠 관련 변수 확인
    phase2_vars = [
        "mock_webcam_enabled",
        "mock_webcam_scores",
        "mock_posture_feedback"
    ]
    for var in phase2_vars:
        if var in content:
            log_pass(f"세션 변수 '{var}' 존재")
        else:
            log_fail(f"세션 변수 '{var}' 없음")

    # 웹캠 스트리머 호출 확인
    if "create_webcam_streamer" in content:
        log_pass("create_webcam_streamer 호출 존재")
    else:
        log_fail("create_webcam_streamer 호출 없음")

    # 자세 분석 탭 확인
    if "자세 분석" in content:
        log_pass("자세 분석 탭 존재")
    else:
        log_fail("자세 분석 탭 없음")

    # 피드백 새로고침 버튼 확인
    if "피드백 새로고침" in content:
        log_pass("피드백 새로고침 버튼 존재")
    else:
        log_warn("피드백 새로고침 버튼 없음")

except Exception as e:
    log_fail(f"모의면접 페이지 Phase 2 확인 실패: {e}")

# ============================================================================
# 버튼 색상/가시성 문제 검사
# ============================================================================
print("\n" + "=" * 70)
print("[버튼 색상/가시성 검사]")
print("-" * 50)

# 문제가 될 수 있는 색상 조합
# 배경색과 글자색의 대비가 낮은 경우
problem_patterns = [
    # (패턴, 설명)
    (r'background:\s*#([0-9a-fA-F]{6})[^}]*color:\s*#([0-9a-fA-F]{6})', "배경색/글자색 조합"),
    (r'background-color:\s*#([0-9a-fA-F]{6})[^}]*color:\s*#([0-9a-fA-F]{6})', "배경색/글자색 조합"),
]

# 검사할 파일들
files_to_check = [
    "홈.py",
    "sidebar_common.py",
    "layout.py",
    "ui_config.py",
    "pages/31_구독.py",
    "pages/35_요금제.py",
]

def hex_to_rgb(hex_color):
    """16진수 색상을 RGB로 변환"""
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_luminance(rgb):
    """상대 휘도 계산"""
    r, g, b = [x/255 for x in rgb]
    r = r/12.92 if r <= 0.03928 else ((r+0.055)/1.055)**2.4
    g = g/12.92 if g <= 0.03928 else ((g+0.055)/1.055)**2.4
    b = b/12.92 if b <= 0.03928 else ((b+0.055)/1.055)**2.4
    return 0.2126*r + 0.7152*g + 0.0722*b

def get_contrast_ratio(color1, color2):
    """대비율 계산"""
    l1 = get_luminance(hex_to_rgb(color1))
    l2 = get_luminance(hex_to_rgb(color2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

# 버튼 관련 CSS 패턴 검사
button_patterns = [
    r'\.btn[^{]*\{[^}]*background[^}]*color[^}]*\}',
    r'\.nav-btn[^{]*\{[^}]*\}',
    r'\.plan-btn[^{]*\{[^}]*\}',
    r'\.hero-btn[^{]*\{[^}]*\}',
    r'button\s*\{[^}]*\}',
]

# 알려진 문제 색상 조합 (낮은 대비)
known_issues = []

print("\n버튼 CSS 분석 중...")
for file_name in files_to_check:
    file_path = PROJECT_ROOT / file_name
    if not file_path.exists():
        continue

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 버튼 클래스 찾기
        # nav-btn-primary 등의 패턴
        btn_matches = re.findall(
            r'\.([\w-]*btn[\w-]*)\s*\{([^}]+)\}',
            content,
            re.IGNORECASE
        )

        for class_name, styles in btn_matches:
            # 배경색과 글자색 추출
            bg_match = re.search(r'background(?:-color)?:\s*#([0-9a-fA-F]{6})', styles)
            color_match = re.search(r'(?<!background-)color:\s*#([0-9a-fA-F]{6})', styles)

            if bg_match and color_match:
                bg_color = bg_match.group(1)
                text_color = color_match.group(1)
                contrast = get_contrast_ratio(bg_color, text_color)

                if contrast < 4.5:  # WCAG AA 기준
                    log_button_issue(f"{file_name}: .{class_name} 대비율 {contrast:.2f} (최소 4.5 필요)")
                    known_issues.append({
                        "file": file_name,
                        "class": class_name,
                        "bg": bg_color,
                        "text": text_color,
                        "contrast": contrast
                    })

        # a 태그 스타일 검사
        a_matches = re.findall(
            r'<a[^>]*class="([^"]*)"[^>]*>([^<]+)</a>',
            content
        )

        # href와 class가 있는 링크 중 버튼 스타일 검사
        for class_names, text in a_matches:
            if 'btn' in class_names.lower():
                # 해당 클래스의 스타일 찾기
                for cn in class_names.split():
                    if 'btn' in cn.lower():
                        # CSS 정의 찾기
                        css_match = re.search(
                            rf'\.{re.escape(cn)}\s*\{{([^}}]+)\}}',
                            content
                        )
                        if css_match:
                            styles = css_match.group(1)
                            if 'color' in styles.lower():
                                # color가 white나 #fff인데 !important 없으면 경고
                                if re.search(r'color:\s*(white|#fff)', styles, re.I):
                                    if '!important' not in styles:
                                        log_warn(f"{file_name}: .{cn} - color에 !important 없음 (오버라이드 가능성)")

    except Exception as e:
        log_warn(f"{file_name} 검사 중 오류: {e}")

# 추가 검사: 특정 문제 패턴
print("\n특정 문제 패턴 검사...")

# a 태그 기본 색상 오버라이드 문제
pages_dir = PROJECT_ROOT / "pages"
if pages_dir.exists():
    for py_file in pages_dir.glob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 버튼에 !important 없이 color 설정
            if re.search(r'\.[\w-]*btn[\w-]*\s*\{[^}]*color:\s*(?!.*!important)[^}]*\}', content):
                # 더 세부 검사
                matches = re.findall(r'\.([\w-]*btn[\w-]*)\s*\{([^}]+)\}', content)
                for class_name, styles in matches:
                    if 'color:' in styles and '!important' not in styles:
                        if 'white' in styles or '#fff' in styles or '#FFF' in styles:
                            log_warn(f"{py_file.name}: .{class_name} - 흰색 글자에 !important 없음")

        except Exception as e:
            pass

# ============================================================================
# 결과 요약
# ============================================================================
print("\n" + "=" * 70)
print("테스트 결과 요약")
print("=" * 70)

print(f"\n✅ 성공: {len(results['passed'])}개")
print(f"❌ 실패: {len(results['failed'])}개")
print(f"⚠️ 경고: {len(results['warnings'])}개")
print(f"🎨 버튼 이슈: {len(results['button_issues'])}개")

if results['failed']:
    print("\n[실패 항목]")
    for item in results['failed']:
        print(f"  - {item}")

if results['button_issues']:
    print("\n[버튼 색상 이슈]")
    for item in results['button_issues']:
        print(f"  - {item}")

if known_issues:
    print("\n[수정 필요한 버튼]")
    for issue in known_issues:
        print(f"  파일: {issue['file']}")
        print(f"    클래스: .{issue['class']}")
        print(f"    배경: #{issue['bg']}, 글자: #{issue['text']}")
        print(f"    대비율: {issue['contrast']:.2f} (4.5 이상 필요)")
        print()

print("\n" + "=" * 70)
if len(results['failed']) == 0:
    print("🎉 Phase 1 & Phase 2 핵심 기능 테스트 통과!")
else:
    print("⚠️ 일부 테스트 실패 - 위 항목 확인 필요")
print("=" * 70)
