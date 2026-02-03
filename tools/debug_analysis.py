#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 웹캠 분석 상세 디버깅

import cv2
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webcam_analyzer import WebcamAnalyzer, MEDIAPIPE_AVAILABLE, OPENCV_AVAILABLE

print("=" * 70)
print("  웹캠 분석 상세 디버깅")
print("=" * 70)

# 웹캠 열기
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] 웹캠을 열 수 없습니다")
    sys.exit(1)

# 몇 프레임 건너뛰기 (카메라 워밍업)
for _ in range(10):
    cap.read()

print("[INFO] 분석기 초기화 중...")
analyzer = WebcamAnalyzer()
init_result = analyzer.initialize()
print(f"[INFO] 초기화 결과: {init_result}")

if not init_result:
    print("[ERROR] 분석기 초기화 실패")
    cap.release()
    sys.exit(1)

print("\n[INFO] 10프레임 분석 시작...")
print("=" * 70)

for i in range(10):
    ret, frame = cap.read()
    if not ret:
        print(f"[Frame {i+1}] 프레임 읽기 실패")
        continue

    result = analyzer.analyze_frame(frame)

    print(f"\n[Frame {i+1}] 상세 분석 결과:")
    print("-" * 50)

    # 얼굴 분석 결과
    face = result.get("face", {})
    print(f"  [얼굴]")
    print(f"    detected: {face.get('detected')}")
    if face.get("detected"):
        print(f"    eye_contact: {face.get('eye_contact')}")
        print(f"    eye_contact_ratio: {face.get('eye_contact_ratio', 0):.4f}")
        print(f"    head_position: {face.get('head_position')}")
        print(f"    head_offset_x: {face.get('head_offset_x', 0):.4f}")
        print(f"    head_offset_y: {face.get('head_offset_y', 0):.4f}")
        print(f"    head_tilt_deg: {face.get('head_tilt_deg', 0):.2f}")
        print(f"    face_size: {face.get('face_size', 0):.4f}")
        print(f"    expression: {face.get('expression')}")
    else:
        print(f"    reason: {face.get('reason', 'unknown')}")

    # 자세 분석 결과
    pose = result.get("pose", {})
    print(f"  [자세]")
    print(f"    detected: {pose.get('detected')}")
    if pose.get("detected"):
        print(f"    shoulder_aligned: {pose.get('shoulder_aligned')}")
        print(f"    shoulder_warning: {pose.get('shoulder_warning')}")
        print(f"    shoulder_diff: {pose.get('shoulder_diff', 0):.4f}")
        print(f"    tilt_direction: {pose.get('tilt_direction')}")
        print(f"    body_center_x: {pose.get('body_center_x', 0):.4f}")

    # 손 분석 결과
    hands = result.get("hands", {})
    print(f"  [손]")
    print(f"    detected: {hands.get('detected')}")
    print(f"    count: {hands.get('count', 0)}")
    print(f"    touching_face: {hands.get('touching_face')}")

    # 피드백
    feedbacks = result.get("feedback", [])
    print(f"  [피드백] 총 {len(feedbacks)}개")
    for fb in feedbacks:
        print(f"    - [{fb.priority.value}] {fb.message}")

    # 점수
    score = result.get("overall_score", 0)
    print(f"  [점수] {score:.1f}/100")

    # 피드백이 없는 이유 분석
    if not feedbacks and face.get("detected"):
        print(f"\n  [피드백 없음 분석]")
        eye_ratio = face.get("eye_contact_ratio", 0)
        print(f"    - 시선 비율 {eye_ratio:.2f} >= 0.6? {eye_ratio >= 0.6}")
        head_pos = face.get("head_position", "centered")
        print(f"    - 머리 위치 '{head_pos}' == 'centered'? {head_pos == 'centered'}")
        head_tilt = abs(face.get("head_tilt_deg", 0))
        print(f"    - 머리 기울기 {head_tilt:.1f} <= 3.0? {head_tilt <= 3.0}")
        face_size = face.get("face_size", 0.25)
        print(f"    - 얼굴 크기 {face_size:.3f} (0.10 ~ 0.55)? {0.10 <= face_size <= 0.55}")

    time.sleep(0.3)

cap.release()
analyzer.release()

print("\n" + "=" * 70)
print("  디버깅 완료")
print("=" * 70)
