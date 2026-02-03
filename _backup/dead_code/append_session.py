#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 세션 내용 추가

import os

path = r"C:\Users\ADMIN\Desktop\29일 최종세션.txt"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 기존 "문서 끝" 부분을 찾아서 그 앞에 새 내용 삽입
new_section = """================================================================================
## 29일 밤 세션 추가 (긴급 - 내일 첫 작업)
================================================================================

### 발견된 문제점
1. **MediaPipe API 완전 변경**: 0.10.30 이상에서 `mp.solutions` 제거됨
2. **웹캠 비디오 크기 너무 큼**
3. **실시간 분석 피드백 안 뜸**

### 해결 작업 완료

**1. MediaPipe Tasks API로 webcam_analyzer.py 완전 재작성**
```python
# 기존 (작동 안 함)
import mediapipe as mp
mp_face = mp.solutions.face_mesh  # AttributeError!

# 새 방식 (Tasks API)
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
```

**2. 모델 파일 다운로드 (models/ 디렉토리)**
- face_landmarker.task (3.7MB)
- pose_landmarker_heavy.task (30.6MB)
- hand_landmarker.task (7.8MB)

**3. 분석기 독립 테스트 성공 (quick_test.py)**
```
점수: 45 | 피드백: 3개 | 얼굴: True | 머리기울기: 24.5도
  -> [high] 머리가 심하게 기울어졌습니다
  -> [medium] 고개를 약간 왼쪽으로 기울이세요
  -> [medium] 시선이 화면 중앙에서 벗어났습니다
```
**핵심: 분석기 자체는 정상! Streamlit 통합이 문제**

**4. Streamlit 수정 스크립트 생성**
- fix_webcam_size.py: 비디오 크기 320x240, CSS 280px 제한
- fix_realtime_feedback.py: 2컬럼 레이아웃 (웹캠|피드백)

### 신규 파일 목록
- C:\\Users\\ADMIN\\ai_tutor\\models\\face_landmarker.task
- C:\\Users\\ADMIN\\ai_tutor\\models\\pose_landmarker_heavy.task
- C:\\Users\\ADMIN\\ai_tutor\\models\\hand_landmarker.task
- C:\\Users\\ADMIN\\ai_tutor\\quick_test.py
- C:\\Users\\ADMIN\\ai_tutor\\fix_webcam_size.py
- C:\\Users\\ADMIN\\ai_tutor\\fix_realtime_feedback.py

### 내일 첫 작업 순서
```bash
cd C:\\Users\\ADMIN\\ai_tutor
streamlit run 홈.py --server.port 8501
# 브라우저에서 모의면접 -> 웹캠 분석 테스트
# 확인: 비디오 크기, 실시간 피드백, 나쁜 자세 경고
```

### 수정 안 됐으면
```bash
python fix_webcam_size.py
python fix_realtime_feedback.py
```

### 주의사항
- MediaPipe는 반드시 Tasks API 사용 (mp.solutions 금지)
- 모델 파일이 models/ 디렉토리에 있어야 함

"""

old_ending = "================================================================================\n# 문서 끝\n================================================================================"

if old_ending in content:
    content = content.replace(old_ending, new_section + old_ending)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("세션 내용 추가 완료!")
else:
    # 그냥 끝에 추가
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + new_section)
    print("세션 내용 끝에 추가 완료!")
