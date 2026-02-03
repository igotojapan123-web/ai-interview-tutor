#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 웹캠 분석 상세 진단

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  웹캠 분석 상세 진단")
print("=" * 60)

# 1. OpenCV 확인
print("\n[1] OpenCV 확인...")
try:
    import cv2
    print(f"  OK - OpenCV {cv2.__version__}")

    # 웹캠 테스트
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"  OK - 웹캠 작동 (해상도: {frame.shape[1]}x{frame.shape[0]})")
        else:
            print("  FAIL - 웹캠 프레임 읽기 실패")
        cap.release()
    else:
        print("  FAIL - 웹캠 열기 실패")
except Exception as e:
    print(f"  FAIL - {e}")

# 2. MediaPipe 확인
print("\n[2] MediaPipe 확인...")
try:
    import mediapipe as mp
    print(f"  OK - MediaPipe {mp.__version__ if hasattr(mp, '__version__') else 'installed'}")
except Exception as e:
    print(f"  FAIL - {e}")

# 3. FaceMesh 초기화 테스트
print("\n[3] FaceMesh 초기화...")
try:
    import mediapipe as mp
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    print("  OK - FaceMesh 초기화 성공")
    face_mesh.close()
except Exception as e:
    print(f"  FAIL - {e}")
    import traceback
    traceback.print_exc()

# 4. Pose 초기화 테스트
print("\n[4] Pose 초기화...")
try:
    import mediapipe as mp
    pose = mp.solutions.pose.Pose(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        model_complexity=2
    )
    print("  OK - Pose 초기화 성공")
    pose.close()
except Exception as e:
    print(f"  FAIL - {e}")
    import traceback
    traceback.print_exc()

# 5. Hands 초기화 테스트
print("\n[5] Hands 초기화...")
try:
    import mediapipe as mp
    hands = mp.solutions.hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    print("  OK - Hands 초기화 성공")
    hands.close()
except Exception as e:
    print(f"  FAIL - {e}")
    import traceback
    traceback.print_exc()

# 6. WebcamAnalyzer 초기화 테스트
print("\n[6] WebcamAnalyzer 초기화...")
try:
    from webcam_analyzer import WebcamAnalyzer, MEDIAPIPE_AVAILABLE, OPENCV_AVAILABLE
    print(f"  MEDIAPIPE_AVAILABLE: {MEDIAPIPE_AVAILABLE}")
    print(f"  OPENCV_AVAILABLE: {OPENCV_AVAILABLE}")

    analyzer = WebcamAnalyzer()
    result = analyzer.initialize()
    if result:
        print("  OK - WebcamAnalyzer 초기화 성공")
    else:
        print("  FAIL - WebcamAnalyzer 초기화 실패 (False 반환)")
        print(f"    face_mesh: {analyzer.face_mesh is not None}")
        print(f"    pose: {analyzer.pose is not None}")
        print(f"    hands: {analyzer.hands is not None}")
        print(f"    _initialized: {analyzer._initialized}")
    analyzer.release()
except Exception as e:
    print(f"  FAIL - {e}")
    import traceback
    traceback.print_exc()

# 7. 실제 프레임 분석 테스트
print("\n[7] 실제 프레임 분석 테스트...")
try:
    import cv2
    import mediapipe as mp
    from webcam_analyzer import WebcamAnalyzer

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("  SKIP - 웹캠 없음")
    else:
        ret, frame = cap.read()
        cap.release()

        if ret:
            print(f"  프레임 크기: {frame.shape}")

            # 분석기로 분석
            analyzer = WebcamAnalyzer()
            init_result = analyzer.initialize()
            print(f"  분석기 초기화: {init_result}")

            if init_result:
                result = analyzer.analyze_frame(frame)
                print(f"  분석 결과:")
                print(f"    - 얼굴 감지: {result.get('face', {}).get('detected', False)}")
                print(f"    - 자세 감지: {result.get('pose', {}).get('detected', False)}")
                print(f"    - 피드백 수: {len(result.get('feedback', []))}")
                print(f"    - 전체 점수: {result.get('overall_score', 0)}")

                feedbacks = result.get('feedback', [])
                if feedbacks:
                    print(f"    - 피드백:")
                    for fb in feedbacks:
                        print(f"      [{fb.priority.value}] {fb.message}")
                else:
                    print(f"    - 피드백: 없음 (자세 양호)")

            analyzer.release()
        else:
            print("  FAIL - 프레임 읽기 실패")
except Exception as e:
    print(f"  FAIL - {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("  진단 완료")
print("=" * 60)
