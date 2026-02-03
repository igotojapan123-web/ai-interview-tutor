#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 웹캠 분석기 실시간 테스트 (수정본)

import cv2
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webcam_analyzer import WebcamAnalyzer, FeedbackPriority, MEDIAPIPE_AVAILABLE, OPENCV_AVAILABLE

def main():
    print("=" * 60)
    print("  웹캠 분석기 실시간 테스트")
    print("=" * 60)

    if not MEDIAPIPE_AVAILABLE or not OPENCV_AVAILABLE:
        print("[ERROR] MediaPipe 또는 OpenCV 사용 불가")
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] 웹캠 열기 실패")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("[INFO] 분석기 초기화 중...")
    analyzer = WebcamAnalyzer()
    if not analyzer.initialize():
        print("[ERROR] 분석기 초기화 실패")
        cap.release()
        return

    print("[OK] 초기화 완료! 'q'로 종료")
    print("=" * 60)

    frame_count = 0
    last_print = 0
    current_result = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # 매 프레임마다 분석
        current_result = analyzer.analyze_frame(frame)

        face = current_result.get("face", {})
        pose = current_result.get("pose", {})
        hands = current_result.get("hands", {})
        feedbacks = current_result.get("feedback", [])
        score = current_result.get("overall_score", 0)

        # 1초마다 콘솔 출력
        now = time.time()
        if now - last_print >= 1.0:
            last_print = now
            print(f"\n[분석 결과] 점수: {score:.0f}/100")
            print(f"  얼굴: {'감지' if face.get('detected') else '미감지'}")
            if face.get('detected'):
                print(f"    시선비율: {face.get('eye_contact_ratio', 0):.2f}")
                print(f"    머리위치: {face.get('head_position')}")
                print(f"    기울기: {face.get('head_tilt_deg', 0):.1f}도")
            print(f"  자세: {'감지' if pose.get('detected') else '미감지'}")
            print(f"  손얼굴접촉: {hands.get('touching_face', False)}")
            print(f"  피드백: {len(feedbacks)}개")
            for fb in feedbacks:
                print(f"    [{fb.priority.value}] {fb.message}")
            if not feedbacks and face.get('detected'):
                print("    ✅ 자세 좋음!")

        # 화면 표시
        # 배경 박스
        cv2.rectangle(frame, (5, 5), (350, 75), (0, 0, 0), -1)

        # 점수
        if score >= 70:
            score_color = (0, 200, 0)
        elif score >= 50:
            score_color = (0, 200, 200)
        else:
            score_color = (0, 0, 255)

        cv2.putText(frame, f"Score: {score:.0f}/100", (15, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, score_color, 2)

        # 감지 상태
        face_text = "Face: OK" if face.get('detected') else "Face: NO"
        face_color = (0, 200, 0) if face.get('detected') else (0, 0, 255)
        cv2.putText(frame, face_text, (15, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, face_color, 2)

        pose_text = "Pose: OK" if pose.get('detected') else "Pose: NO"
        pose_color = (0, 200, 0) if pose.get('detected') else (0, 0, 255)
        cv2.putText(frame, pose_text, (130, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, pose_color, 2)

        hand_text = "Hand: FACE!" if hands.get('touching_face') else "Hand: OK"
        hand_color = (0, 0, 255) if hands.get('touching_face') else (0, 200, 0)
        cv2.putText(frame, hand_text, (245, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, hand_color, 2)

        # 피드백 표시
        y = 100
        for i, fb in enumerate(feedbacks[:5]):
            cv2.rectangle(frame, (5, y-18), (635, y+7), (0, 0, 0), -1)

            if fb.priority.value == "critical":
                color = (0, 0, 255)
                prefix = "[!!!]"
            elif fb.priority.value == "high":
                color = (0, 100, 255)
                prefix = "[!!]"
            elif fb.priority.value == "medium":
                color = (0, 200, 200)
                prefix = "[!]"
            else:
                color = (200, 200, 0)
                prefix = "[i]"

            cv2.putText(frame, f"{prefix} {fb.message}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            y += 30

        if not feedbacks and face.get('detected'):
            cv2.rectangle(frame, (5, y-18), (400, y+7), (0, 0, 0), -1)
            cv2.putText(frame, "Good posture! Keep it up!", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Webcam Analysis (q to quit)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    analyzer.release()
    print("\n종료")

if __name__ == "__main__":
    main()
