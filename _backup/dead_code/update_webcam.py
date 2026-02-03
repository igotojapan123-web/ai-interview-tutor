#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# webcam_analyzer.py 업데이트 스크립트

code = '''# webcam_analyzer.py
# Phase 2: 실시간 웹캠 분석 - 정확도 향상 버전

import logging
import math
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)

MEDIAPIPE_AVAILABLE = False
OPENCV_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    pass

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    pass

try:
    import numpy as np
except ImportError:
    np = None


class FeedbackType(str, Enum):
    POSTURE = "posture"
    EYE_CONTACT = "eye_contact"
    EXPRESSION = "expression"
    GESTURE = "gesture"
    HEAD_POSITION = "head_position"
    SHOULDER = "shoulder"
    FACE_POSITION = "face_position"


class FeedbackPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RealtimeFeedback:
    feedback_type: FeedbackType
    message: str
    priority: FeedbackPriority
    score: float
    suggestion: str = ""
    detail: str = ""


class WebcamAnalyzer:
    EYE_CONTACT_THRESHOLD = 0.18
    HEAD_CENTER_STRICT_X = 0.10
    HEAD_CENTER_STRICT_Y = 0.12
    HEAD_CENTER_WARN_X = 0.06
    HEAD_CENTER_WARN_Y = 0.08
    SHOULDER_TILT_STRICT = 0.03
    SHOULDER_TILT_WARN = 0.02
    FACE_SIZE_MIN = 0.12
    FACE_SIZE_MAX = 0.50
    HEAD_TILT_STRICT = 6.0
    HEAD_TILT_WARN = 3.5

    def __init__(self):
        self.face_mesh = None
        self.pose = None
        self.hands = None
        self._initialized = False
        self._eye_hist = deque(maxlen=8)
        self._head_x_hist = deque(maxlen=8)
        self._head_y_hist = deque(maxlen=8)
        self._shoulder_hist = deque(maxlen=8)
        self._tilt_hist = deque(maxlen=8)
        self._face_size_hist = deque(maxlen=8)

    def initialize(self):
        if not MEDIAPIPE_AVAILABLE or not OPENCV_AVAILABLE:
            return False
        try:
            self.face_mesh = mp.solutions.face_mesh.FaceMesh(
                max_num_faces=1, refine_landmarks=True,
                min_detection_confidence=0.7, min_tracking_confidence=0.7)
            self.pose = mp.solutions.pose.Pose(
                min_detection_confidence=0.7, min_tracking_confidence=0.7,
                model_complexity=2)
            self.hands = mp.solutions.hands.Hands(
                max_num_hands=2, min_detection_confidence=0.7,
                min_tracking_confidence=0.7)
            self._initialized = True
            return True
        except:
            return False

    def analyze_frame(self, frame):
        if not self._initialized:
            return self._fallback()
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            face = self._analyze_face(rgb)
            pose = self._analyze_pose(rgb)
            hands = self._analyze_hands(rgb, face)
            feedback = self._gen_feedback(face, pose, hands)
            score = self._calc_score(face, pose, hands)
            return {"face": face, "pose": pose, "hands": hands,
                    "feedback": feedback, "overall_score": score}
        except:
            return self._fallback()

    def _analyze_face(self, rgb):
        if not self.face_mesh:
            return {"detected": False}
        res = self.face_mesh.process(rgb)
        if not res.multi_face_landmarks:
            return {"detected": False, "reason": "얼굴 미감지"}
        lm = res.multi_face_landmarks[0].landmark
        xs = [p.x for p in lm]
        ys = [p.y for p in lm]
        fsize = ((max(xs)-min(xs)) + (max(ys)-min(ys))) / 2
        self._face_size_hist.append(fsize)
        avg_fsize = sum(self._face_size_hist) / len(self._face_size_hist)
        nose = lm[4]
        self._head_x_hist.append(nose.x)
        self._head_y_hist.append(nose.y)
        avg_x = sum(self._head_x_hist) / len(self._head_x_hist)
        avg_y = sum(self._head_y_hist) / len(self._head_y_hist)
        off_x = abs(avg_x - 0.5)
        off_y = abs(avg_y - 0.5)
        le, re = lm[33], lm[263]
        tilt = math.degrees(math.atan2(re.y - le.y, re.x - le.x))
        self._tilt_hist.append(tilt)
        avg_tilt = sum(self._tilt_hist) / len(self._tilt_hist)
        eye_ok = self._check_eye(lm)
        self._eye_hist.append(1.0 if eye_ok else 0.0)
        eye_ratio = sum(self._eye_hist) / len(self._eye_hist)
        expr = self._check_expr(lm)
        pos = "centered"
        if off_x >= self.HEAD_CENTER_WARN_X or off_y >= self.HEAD_CENTER_WARN_Y:
            parts = []
            if avg_x < 0.5 - self.HEAD_CENTER_STRICT_X: parts.append("왼쪽")
            elif avg_x > 0.5 + self.HEAD_CENTER_STRICT_X: parts.append("오른쪽")
            if avg_y < 0.5 - self.HEAD_CENTER_STRICT_Y: parts.append("위")
            elif avg_y > 0.5 + self.HEAD_CENTER_STRICT_Y: parts.append("아래")
            pos = " ".join(parts) if parts else "약간 벗어남"
        return {"detected": True, "eye_contact": eye_ok, "eye_contact_ratio": eye_ratio,
                "head_position": pos, "head_offset_x": off_x, "head_offset_y": off_y,
                "head_tilt_deg": avg_tilt, "expression": expr, "face_size": avg_fsize,
                "face_center": (avg_x, avg_y)}

    def _check_eye(self, lm):
        li, ri = lm[468], lm[473]
        lei, leo = lm[133], lm[33]
        rei, reo = lm[362], lm[263]
        lw = abs(leo.x - lei.x)
        rw = abs(reo.x - rei.x)
        if lw > 0 and rw > 0:
            lc = (lei.x + leo.x) / 2
            rc = (rei.x + reo.x) / 2
            lo = abs(li.x - lc) / lw
            ro = abs(ri.x - rc) / rw
            return ((lo + ro) / 2) < self.EYE_CONTACT_THRESHOLD
        return False

    def _check_expr(self, lm):
        ul, ll = lm[13], lm[14]
        ml, mr = lm[61], lm[291]
        cy = (ul.y + ll.y) / 2
        lift = ((cy - ml.y) + (cy - mr.y)) / 2
        if lift > 0.015: return "smile"
        elif lift < -0.008: return "tense"
        return "neutral"

    def _analyze_pose(self, rgb):
        if not self.pose:
            return {"detected": False}
        res = self.pose.process(rgb)
        if not res.pose_landmarks:
            return {"detected": False}
        lm = res.pose_landmarks.landmark
        ls, rs = lm[11], lm[12]
        if ls.visibility < 0.5 or rs.visibility < 0.5:
            return {"detected": False}
        diff = abs(ls.y - rs.y)
        self._shoulder_hist.append(diff)
        avg_diff = sum(self._shoulder_hist) / len(self._shoulder_hist)
        aligned = avg_diff < self.SHOULDER_TILT_STRICT
        warning = avg_diff >= self.SHOULDER_TILT_WARN
        tdir = ""
        if warning:
            tdir = "왼쪽 어깨 올라감" if ls.y < rs.y else "오른쪽 어깨 올라감"
        bcx = (ls.x + rs.x) / 2
        score = 100
        if not aligned: score -= 35
        elif warning: score -= 20
        if abs(bcx - 0.5) > 0.10: score -= 20
        return {"detected": True, "shoulder_aligned": aligned, "shoulder_warning": warning,
                "shoulder_diff": avg_diff, "tilt_direction": tdir, "body_center_x": bcx,
                "posture_score": max(0, score)}

    def _analyze_hands(self, rgb, face):
        if not self.hands:
            return {"detected": False, "count": 0, "touching_face": False}
        res = self.hands.process(rgb)
        if not res.multi_hand_landmarks:
            return {"detected": False, "count": 0, "touching_face": False}
        fc = face.get("face_center", (0.5, 0.5))
        fs = face.get("face_size", 0.2)
        touch = False
        for h in res.multi_hand_landmarks:
            for i in [4, 8, 12, 16, 20]:
                t = h.landmark[i]
                if math.sqrt((t.x-fc[0])**2 + (t.y-fc[1])**2) < fs * 1.3:
                    touch = True
                    break
        return {"detected": True, "count": len(res.multi_hand_landmarks), "touching_face": touch}

    def _gen_feedback(self, face, pose, hands):
        fb = []
        if not face.get("detected"):
            fb.append(RealtimeFeedback(FeedbackType.FACE_POSITION, "얼굴이 감지되지 않습니다",
                      FeedbackPriority.CRITICAL, 0, "카메라를 정면으로 바라봐주세요"))
            return fb
        er = face.get("eye_contact_ratio", 0)
        if er < 0.75:
            p = FeedbackPriority.CRITICAL if er < 0.5 else FeedbackPriority.HIGH
            m = "시선이 카메라를 벗어났습니다" if er < 0.5 else "시선이 불안정합니다"
            fb.append(RealtimeFeedback(FeedbackType.EYE_CONTACT, m, p, er*100, "카메라 렌즈를 바라보세요"))
        hp = face.get("head_position", "centered")
        if hp != "centered":
            ho = face.get("head_offset_x", 0) + face.get("head_offset_y", 0)
            p = FeedbackPriority.HIGH if ho > 0.15 else FeedbackPriority.MEDIUM
            fb.append(RealtimeFeedback(FeedbackType.HEAD_POSITION, f"얼굴이 {hp}으로 치우쳤습니다",
                      p, max(0, 100-ho*250), "화면 중앙에 위치시키세요"))
        ht = abs(face.get("head_tilt_deg", 0))
        if ht > self.HEAD_TILT_WARN:
            p = FeedbackPriority.HIGH if ht > self.HEAD_TILT_STRICT else FeedbackPriority.MEDIUM
            fb.append(RealtimeFeedback(FeedbackType.HEAD_POSITION, "고개가 기울어져 있습니다",
                      p, max(0, 100-ht*8), "고개를 똑바로 세워주세요", f"{ht:.1f}도"))
        fs = face.get("face_size", 0.25)
        if fs < self.FACE_SIZE_MIN:
            fb.append(RealtimeFeedback(FeedbackType.FACE_POSITION, "너무 멀리 있습니다",
                      FeedbackPriority.MEDIUM, 55, "가까이 앉아주세요"))
        elif fs > self.FACE_SIZE_MAX:
            fb.append(RealtimeFeedback(FeedbackType.FACE_POSITION, "너무 가깝습니다",
                      FeedbackPriority.MEDIUM, 55, "떨어져 앉아주세요"))
        if pose.get("detected"):
            if not pose.get("shoulder_aligned"):
                fb.append(RealtimeFeedback(FeedbackType.SHOULDER, "어깨가 기울어져 있습니다",
                          FeedbackPriority.HIGH, pose.get("posture_score", 45),
                          "어깨를 수평으로 맞춰주세요", pose.get("tilt_direction", "")))
            elif pose.get("shoulder_warning"):
                fb.append(RealtimeFeedback(FeedbackType.SHOULDER, "어깨가 약간 기울어져 있습니다",
                          FeedbackPriority.MEDIUM, pose.get("posture_score", 65), "수평 유지하세요"))
            bc = pose.get("body_center_x", 0.5)
            if abs(bc - 0.5) > 0.10:
                d = "왼쪽" if bc < 0.5 else "오른쪽"
                fb.append(RealtimeFeedback(FeedbackType.POSTURE, f"몸이 {d}으로 치우침",
                          FeedbackPriority.MEDIUM, 65, "중앙에 앉으세요"))
        if hands.get("touching_face"):
            fb.append(RealtimeFeedback(FeedbackType.GESTURE, "손이 얼굴에 닿아 있습니다",
                      FeedbackPriority.HIGH, 35, "손을 내려놓으세요"))
        if face.get("expression") == "tense":
            fb.append(RealtimeFeedback(FeedbackType.EXPRESSION, "표정이 긴장됨",
                      FeedbackPriority.MEDIUM, 50, "미소를 지어보세요"))
        return fb

    def _calc_score(self, face, pose, hands):
        if not face.get("detected"): return 0.0
        s = 100.0
        er = face.get("eye_contact_ratio", 0)
        if er < 0.5: s -= 35
        elif er < 0.65: s -= 25
        elif er < 0.8: s -= 15
        elif er < 0.9: s -= 8
        ho = face.get("head_offset_x", 0) + face.get("head_offset_y", 0)
        s -= min(20, ho * 120)
        ht = abs(face.get("head_tilt_deg", 0))
        if ht > self.HEAD_TILT_STRICT: s -= 15
        elif ht > self.HEAD_TILT_WARN: s -= 8
        if pose.get("detected"):
            if not pose.get("shoulder_aligned"): s -= 20
            elif pose.get("shoulder_warning"): s -= 12
        if hands.get("touching_face"): s -= 10
        return max(0, min(100, round(s, 1)))

    def _fallback(self):
        return {"face": {"detected": False}, "pose": {"detected": False},
                "hands": {"detected": False, "count": 0, "touching_face": False},
                "feedback": [RealtimeFeedback(FeedbackType.FACE_POSITION, "분석 불가",
                             FeedbackPriority.CRITICAL, 0, "카메라 확인")],
                "overall_score": 0}

    def release(self):
        if self.face_mesh: self.face_mesh.close()
        if self.pose: self.pose.close()
        if self.hands: self.hands.close()
        self._initialized = False


_instance = None

def get_webcam_analyzer():
    global _instance
    if _instance is None:
        _instance = WebcamAnalyzer()
    if not _instance._initialized:
        _instance.initialize()
    return _instance

def is_webcam_analysis_available():
    return MEDIAPIPE_AVAILABLE and OPENCV_AVAILABLE
'''

if __name__ == "__main__":
    import os
    target = os.path.join(os.path.dirname(__file__), "webcam_analyzer.py")
    with open(target, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Updated: {target}")
