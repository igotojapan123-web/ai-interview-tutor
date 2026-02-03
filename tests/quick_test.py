import cv2
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webcam_analyzer import WebcamAnalyzer

print("웹캠 열기...")
cap = cv2.VideoCapture(0)
for _ in range(30):  # 워밍업
    cap.read()

print("분석기 초기화...")
analyzer = WebcamAnalyzer()
analyzer.initialize()

print("\n5초간 분석합니다. 일부러 나쁜 자세를 취해보세요!")
print("(고개 기울이기, 턱 괴기, 시선 피하기 등)\n")

import time
start = time.time()
while time.time() - start < 5:
    ret, frame = cap.read()
    if not ret:
        continue

    result = analyzer.analyze_frame(frame)
    face = result.get("face", {})
    feedbacks = result.get("feedback", [])
    score = result.get("overall_score", 0)

    print(f"점수: {score:.0f} | 피드백: {len(feedbacks)}개 | 얼굴: {face.get('detected')} | 머리기울기: {face.get('head_tilt_deg', 0):.1f}도")

    if feedbacks:
        for fb in feedbacks:
            print(f"  -> [{fb.priority.value}] {fb.message}")

    time.sleep(0.5)

cap.release()
analyzer.release()
print("\n완료!")
