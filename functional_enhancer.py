# -*- coding: utf-8 -*-
"""
functional_enhancer.py
B. 기능적 (-) 해결 모듈

해결하는 문제:
6. 음성 인식 오류 → 다중 STT 검증 + 자동 보정
7. 피드백 지연 → 예상 시간 표시 + 부분 결과
8. 실시간 피드백 없음 → 연습 중 AI 실시간 코칭
9. 발음 평가 부정확 → 음성 파형 분석 + 모범 발음 비교
10. 비언어 분석 부족 → 자세, 손동작, 고개 끄덕임 분석
11. 세션 데이터 손실 → 자동 저장 + 복구 기능
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Callable
from enum import Enum
from datetime import datetime
import json
import re
import time
import hashlib


# ============================================================
# 6. 음성 인식 오류 해결: 다중 STT 검증
# ============================================================

@dataclass
class STTResult:
    """STT 결과"""
    text: str
    confidence: float
    source: str
    alternatives: List[str] = field(default_factory=list)


@dataclass
class ValidatedSTTResult:
    """검증된 STT 결과"""
    final_text: str
    confidence: float
    corrections: List[Dict]  # 자동 보정 내역
    sources_used: List[str]
    is_reliable: bool


class MultiSTTValidator:
    """다중 STT 검증 시스템"""

    # 항공 관련 용어 사전 (자동 보정용)
    AIRLINE_TERMS = {
        "대한항공": ["대한 항공", "대한공항", "대항항공"],
        "아시아나항공": ["아시아나 항공", "아시아나공항", "아시아나 한공"],
        "승무원": ["승무 원", "승무언", "승무원이", "승무원은"],
        "기내": ["기 내", "기네", "기나이"],
        "서비스": ["서비스가", "서어비스", "써비스"],
        "안전": ["안 전", "안젼", "안전한"],
        "고객": ["고 객", "고개", "고겍"],
    }

    # 흔한 오인식 패턴
    COMMON_ERRORS = {
        "여기": "열기",
        "이거": "의거",
        "그래서": "그래써",
        "했습니다": "햇습니다",
        "있습니다": "잇습니다",
    }

    def __init__(self):
        pass

    def validate_and_correct(
        self,
        primary_result: STTResult,
        secondary_results: List[STTResult] = None
    ) -> ValidatedSTTResult:
        """다중 STT 결과 검증 및 보정"""

        corrections = []
        sources_used = [primary_result.source]

        # 기본 텍스트
        final_text = primary_result.text

        # 1. 항공 용어 자동 보정
        for correct_term, wrong_terms in self.AIRLINE_TERMS.items():
            for wrong in wrong_terms:
                if wrong in final_text:
                    final_text = final_text.replace(wrong, correct_term)
                    corrections.append({
                        "type": "airline_term",
                        "original": wrong,
                        "corrected": correct_term
                    })

        # 2. 흔한 오류 보정
        for wrong, correct in self.COMMON_ERRORS.items():
            if wrong in final_text:
                final_text = final_text.replace(wrong, correct)
                corrections.append({
                    "type": "common_error",
                    "original": wrong,
                    "corrected": correct
                })

        # 3. 보조 STT 결과와 비교 (있는 경우)
        if secondary_results:
            for sec in secondary_results:
                sources_used.append(sec.source)
                # 신뢰도가 더 높은 결과 채택
                if sec.confidence > primary_result.confidence + 0.1:
                    final_text = sec.text
                    corrections.append({
                        "type": "source_switch",
                        "original": primary_result.text,
                        "corrected": sec.text,
                        "reason": f"{sec.source} 신뢰도가 더 높음"
                    })

        # 신뢰도 계산
        base_confidence = primary_result.confidence
        correction_penalty = len(corrections) * 0.02
        final_confidence = max(0.5, min(1.0, base_confidence - correction_penalty + 0.1))

        return ValidatedSTTResult(
            final_text=final_text,
            confidence=final_confidence,
            corrections=corrections,
            sources_used=sources_used,
            is_reliable=final_confidence >= 0.7
        )

    def suggest_manual_check(self, result: ValidatedSTTResult) -> Optional[str]:
        """수동 확인 필요 여부"""
        if not result.is_reliable:
            return "음성 인식 신뢰도가 낮습니다. 텍스트를 확인해주세요."
        if len(result.corrections) >= 3:
            return "여러 부분이 자동 보정되었습니다. 확인해주세요."
        return None


# ============================================================
# 7. 피드백 지연 해결: 진행 상황 표시
# ============================================================

@dataclass
class ProgressInfo:
    """진행 상황 정보"""
    current_step: int
    total_steps: int
    step_name: str
    estimated_seconds: int
    elapsed_seconds: float
    partial_result: Optional[Any] = None

    @property
    def progress_percent(self) -> float:
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100

    @property
    def remaining_seconds(self) -> int:
        return max(0, self.estimated_seconds - int(self.elapsed_seconds))


class ProgressTracker:
    """진행 상황 추적기"""

    # 작업별 예상 시간 (초)
    TASK_ESTIMATES = {
        "stt_processing": 5,
        "llm_analysis": 10,
        "voice_analysis": 8,
        "emotion_analysis": 6,
        "posture_analysis": 5,
        "expression_analysis": 5,
        "score_calculation": 2,
        "feedback_generation": 8,
        "report_generation": 5,
    }

    def __init__(self):
        self.start_time = None
        self.current_step = 0
        self.steps = []

    def start(self, task_names: List[str]) -> None:
        """추적 시작"""
        self.start_time = time.time()
        self.current_step = 0
        self.steps = task_names

    def update(self, step_index: int, partial_result: Any = None) -> ProgressInfo:
        """진행 상황 업데이트"""
        if not self.steps:
            return ProgressInfo(0, 0, "", 0, 0)

        self.current_step = step_index
        step_name = self.steps[step_index] if step_index < len(self.steps) else "완료"

        # 남은 시간 계산
        remaining_tasks = self.steps[step_index:]
        estimated_remaining = sum(
            self.TASK_ESTIMATES.get(task, 5) for task in remaining_tasks
        )

        elapsed = time.time() - self.start_time if self.start_time else 0

        return ProgressInfo(
            current_step=step_index + 1,
            total_steps=len(self.steps),
            step_name=step_name,
            estimated_seconds=estimated_remaining,
            elapsed_seconds=elapsed,
            partial_result=partial_result
        )

    def get_user_message(self, progress: ProgressInfo) -> str:
        """사용자용 메시지"""
        step_messages = {
            "stt_processing": "음성을 텍스트로 변환하고 있어요...",
            "llm_analysis": "AI가 답변을 분석하고 있어요...",
            "voice_analysis": "음성 특성을 분석하고 있어요...",
            "emotion_analysis": "감정 상태를 분석하고 있어요...",
            "posture_analysis": "자세를 분석하고 있어요...",
            "expression_analysis": "표정을 분석하고 있어요...",
            "score_calculation": "점수를 계산하고 있어요...",
            "feedback_generation": "피드백을 생성하고 있어요...",
            "report_generation": "리포트를 만들고 있어요...",
        }

        msg = step_messages.get(progress.step_name, "처리 중...")

        if progress.remaining_seconds > 0:
            msg += f" (약 {progress.remaining_seconds}초)"

        return msg


# ============================================================
# 8. 실시간 피드백: 연습 중 AI 코칭
# ============================================================

class CoachingType(Enum):
    """코칭 유형"""
    SPEED = "speed"
    VOLUME = "volume"
    FILLER = "filler"
    PAUSE = "pause"
    POSTURE = "posture"
    EXPRESSION = "expression"
    CONTENT = "content"


@dataclass
class RealTimeCoaching:
    """실시간 코칭 메시지"""
    coaching_type: CoachingType
    message: str
    severity: str  # "info", "warning", "critical"
    timestamp: float
    suggestion: Optional[str] = None


class RealTimeCoachingSystem:
    """실시간 코칭 시스템"""

    # 코칭 임계값
    THRESHOLDS = {
        "speed_too_fast": 180,  # WPM
        "speed_too_slow": 100,
        "volume_too_low": -30,  # dB
        "volume_too_high": -10,
        "pause_too_long": 3.0,  # 초
        "filler_frequency": 5,  # 분당
    }

    # 코칭 메시지
    COACHING_MESSAGES = {
        CoachingType.SPEED: {
            "too_fast": ("조금 천천히 말해보세요", "warning", "호흡을 가다듬고 또박또박 말해보세요"),
            "too_slow": ("조금 더 활기차게 말해보세요", "info", "자신감 있게 속도를 올려보세요"),
        },
        CoachingType.VOLUME: {
            "too_low": ("목소리가 작아요, 더 크게!", "warning", "배에 힘을 주고 말해보세요"),
            "too_high": ("목소리가 너무 커요", "info", "조금 부드럽게 말해보세요"),
        },
        CoachingType.PAUSE: {
            "too_long": ("잠깐 멈췄어요, 괜찮아요!", "info", "침착하게 다음 말을 이어가세요"),
        },
        CoachingType.FILLER: {
            "too_many": ("'음', '어' 사용을 줄여보세요", "warning", "생각이 필요하면 잠시 멈춰도 괜찮아요"),
        },
        CoachingType.POSTURE: {
            "slouching": ("어깨를 펴세요!", "warning", "바른 자세가 자신감을 줘요"),
            "looking_away": ("카메라를 바라봐주세요", "warning", "눈맞춤이 중요해요"),
        },
        CoachingType.EXPRESSION: {
            "no_smile": ("자연스러운 미소를 지어보세요", "info", "밝은 표정이 좋은 인상을 줘요"),
            "tense": ("표정이 긴장되어 보여요", "info", "심호흡하고 편안하게!"),
        },
    }

    def __init__(self):
        self.coaching_history: List[RealTimeCoaching] = []
        self.last_coaching_time: Dict[CoachingType, float] = {}
        self.min_interval = 5.0  # 같은 유형 코칭 최소 간격 (초)

    def analyze_realtime(
        self,
        speech_speed: Optional[float] = None,
        volume_db: Optional[float] = None,
        pause_duration: Optional[float] = None,
        filler_count_per_min: Optional[float] = None,
        posture_status: Optional[str] = None,
        expression_status: Optional[str] = None
    ) -> Optional[RealTimeCoaching]:
        """실시간 분석 및 코칭"""

        current_time = time.time()
        coaching = None

        # 속도 체크
        if speech_speed is not None:
            if speech_speed > self.THRESHOLDS["speed_too_fast"]:
                coaching = self._create_coaching(CoachingType.SPEED, "too_fast", current_time)
            elif speech_speed < self.THRESHOLDS["speed_too_slow"]:
                coaching = self._create_coaching(CoachingType.SPEED, "too_slow", current_time)

        # 음량 체크
        if volume_db is not None and coaching is None:
            if volume_db < self.THRESHOLDS["volume_too_low"]:
                coaching = self._create_coaching(CoachingType.VOLUME, "too_low", current_time)
            elif volume_db > self.THRESHOLDS["volume_too_high"]:
                coaching = self._create_coaching(CoachingType.VOLUME, "too_high", current_time)

        # 침묵 체크
        if pause_duration is not None and coaching is None:
            if pause_duration > self.THRESHOLDS["pause_too_long"]:
                coaching = self._create_coaching(CoachingType.PAUSE, "too_long", current_time)

        # 필러 체크
        if filler_count_per_min is not None and coaching is None:
            if filler_count_per_min > self.THRESHOLDS["filler_frequency"]:
                coaching = self._create_coaching(CoachingType.FILLER, "too_many", current_time)

        # 자세 체크
        if posture_status is not None and coaching is None:
            if posture_status in ["slouching", "looking_away"]:
                coaching = self._create_coaching(CoachingType.POSTURE, posture_status, current_time)

        # 표정 체크
        if expression_status is not None and coaching is None:
            if expression_status in ["no_smile", "tense"]:
                coaching = self._create_coaching(CoachingType.EXPRESSION, expression_status, current_time)

        if coaching:
            self.coaching_history.append(coaching)

        return coaching

    def _create_coaching(
        self,
        coaching_type: CoachingType,
        status: str,
        current_time: float
    ) -> Optional[RealTimeCoaching]:
        """코칭 메시지 생성"""

        # 최소 간격 체크
        last_time = self.last_coaching_time.get(coaching_type, 0)
        if current_time - last_time < self.min_interval:
            return None

        messages = self.COACHING_MESSAGES.get(coaching_type, {})
        msg_data = messages.get(status)

        if not msg_data:
            return None

        message, severity, suggestion = msg_data
        self.last_coaching_time[coaching_type] = current_time

        return RealTimeCoaching(
            coaching_type=coaching_type,
            message=message,
            severity=severity,
            timestamp=current_time,
            suggestion=suggestion
        )

    def get_session_summary(self) -> Dict:
        """세션 코칭 요약"""
        type_counts = {}
        for coaching in self.coaching_history:
            type_name = coaching.coaching_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_coachings": len(self.coaching_history),
            "by_type": type_counts,
            "most_frequent": max(type_counts, key=type_counts.get) if type_counts else None
        }


# ============================================================
# 9. 발음 평가: 음성 파형 분석
# ============================================================

@dataclass
class PronunciationAnalysis:
    """발음 분석 결과"""
    overall_score: float
    clarity_score: float
    accuracy_score: float
    rhythm_score: float
    problem_sounds: List[str]
    improvements: List[str]


class PronunciationAnalyzer:
    """발음 분석기"""

    # 한국어 발음 주의 음소
    KOREAN_PROBLEM_SOUNDS = {
        "ㄹ": "ㄹ 발음이 불명확해요",
        "ㅃ": "된소리가 약해요",
        "ㅆ": "쌍시옷 발음을 더 강하게",
        "받침": "받침 발음이 뭉개져요",
    }

    # 영어 발음 주의 음소
    ENGLISH_PROBLEM_SOUNDS = {
        "th": "th 발음에 주의하세요",
        "r": "r과 l을 구분해주세요",
        "v": "v와 b를 구분해주세요",
        "f": "f 발음을 입술로 만들어주세요",
    }

    def __init__(self):
        pass

    def analyze(
        self,
        audio_features: Dict,
        language: str = "ko",
        reference_text: Optional[str] = None
    ) -> PronunciationAnalysis:
        """발음 분석"""

        # 기본 분석 (실제로는 음성 특성 분석 필요)
        clarity = audio_features.get("clarity", 75)
        accuracy = audio_features.get("accuracy", 70)
        rhythm = audio_features.get("rhythm", 72)

        overall = (clarity * 0.4 + accuracy * 0.4 + rhythm * 0.2)

        # 문제 음소 감지 (시뮬레이션)
        problem_sounds = []
        improvements = []

        if language == "ko":
            if clarity < 70:
                problem_sounds.append("받침")
                improvements.append("받침 발음을 또렷하게 해보세요")
            if accuracy < 70:
                problem_sounds.append("ㄹ")
                improvements.append("ㄹ 발음을 혀를 입천장에 붙여서 발음해보세요")
        else:
            if clarity < 70:
                problem_sounds.append("th")
                improvements.append("th는 혀를 이빨 사이에 두고 발음하세요")
            if accuracy < 70:
                problem_sounds.append("r")
                improvements.append("r은 혀를 말아서, l은 혀를 붙여서 발음하세요")

        if not improvements:
            improvements.append("발음이 좋습니다! 현재 수준을 유지하세요")

        return PronunciationAnalysis(
            overall_score=round(overall, 1),
            clarity_score=round(clarity, 1),
            accuracy_score=round(accuracy, 1),
            rhythm_score=round(rhythm, 1),
            problem_sounds=problem_sounds,
            improvements=improvements
        )

    def compare_with_reference(
        self,
        user_audio_features: Dict,
        reference_audio_features: Dict
    ) -> Dict:
        """모범 발음과 비교"""
        return {
            "similarity_score": 75,  # 시뮬레이션
            "speed_difference": user_audio_features.get("speed", 100) - reference_audio_features.get("speed", 120),
            "pitch_difference": user_audio_features.get("pitch", 200) - reference_audio_features.get("pitch", 180),
            "recommendation": "모범 발음보다 조금 빠르게 말하고 있어요. 천천히 따라해보세요."
        }


# ============================================================
# 10. 비언어 분석 확장
# ============================================================

@dataclass
class ExtendedNonverbalAnalysis:
    """확장된 비언어 분석"""
    head_nod_count: int
    hand_gesture_score: float
    body_movement_score: float
    eye_contact_ratio: float
    overall_score: float
    feedback: List[str]


class ExtendedNonverbalAnalyzer:
    """확장된 비언어 분석기"""

    def __init__(self):
        pass

    def analyze(
        self,
        video_features: Dict,
        duration: float
    ) -> ExtendedNonverbalAnalysis:
        """확장된 비언어 분석"""

        # 시뮬레이션 (실제로는 비디오 분석 필요)
        head_nods = video_features.get("head_nods", 5)
        hand_gestures = video_features.get("hand_gesture_score", 70)
        body_movement = video_features.get("body_movement_score", 75)
        eye_contact = video_features.get("eye_contact_ratio", 0.7)

        overall = (hand_gestures * 0.3 + body_movement * 0.3 + eye_contact * 100 * 0.4)

        feedback = []

        # 고개 끄덕임 분석
        nods_per_minute = head_nods / (duration / 60)
        if nods_per_minute < 2:
            feedback.append("대화 중 적절한 고개 끄덕임을 추가해보세요")
        elif nods_per_minute > 10:
            feedback.append("고개 끄덕임이 너무 많아요. 자연스럽게 줄여보세요")

        # 손동작 분석
        if hand_gestures < 60:
            feedback.append("적절한 손동작이 설명에 도움이 됩니다")
        elif hand_gestures > 90:
            feedback.append("손동작이 산만해 보일 수 있어요. 조금 절제해보세요")

        # 몸 움직임 분석
        if body_movement < 60:
            feedback.append("너무 경직되어 보여요. 자연스럽게 움직여도 괜찮아요")
        elif body_movement > 90:
            feedback.append("몸을 많이 움직이면 불안해 보일 수 있어요")

        # 눈맞춤
        if eye_contact < 0.5:
            feedback.append("눈맞춤이 부족해요. 카메라를 자주 바라봐주세요")

        if not feedback:
            feedback.append("비언어적 표현이 매우 좋습니다!")

        return ExtendedNonverbalAnalysis(
            head_nod_count=head_nods,
            hand_gesture_score=round(hand_gestures, 1),
            body_movement_score=round(body_movement, 1),
            eye_contact_ratio=round(eye_contact, 2),
            overall_score=round(overall, 1),
            feedback=feedback
        )


# ============================================================
# 11. 세션 데이터 보호: 자동 저장/복구
# ============================================================

@dataclass
class SessionData:
    """세션 데이터"""
    session_id: str
    user_id: str
    page: str
    data: Dict
    created_at: datetime
    updated_at: datetime
    is_complete: bool = False


class SessionManager:
    """세션 관리자"""

    def __init__(self, storage_dir: str = "session_backup"):
        self.storage_dir = storage_dir
        self.active_sessions: Dict[str, SessionData] = {}

    def create_session(self, user_id: str, page: str, initial_data: Dict = None) -> str:
        """세션 생성"""
        session_id = hashlib.md5(
            f"{user_id}_{page}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        session = SessionData(
            session_id=session_id,
            user_id=user_id,
            page=page,
            data=initial_data or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.active_sessions[session_id] = session
        return session_id

    def update_session(self, session_id: str, data: Dict) -> bool:
        """세션 업데이트 (자동 저장)"""
        if session_id not in self.active_sessions:
            return False

        session = self.active_sessions[session_id]
        session.data.update(data)
        session.updated_at = datetime.now()

        # 자동 저장 (실제로는 파일/DB에 저장)
        self._save_to_storage(session)

        return True

    def recover_session(self, user_id: str, page: str) -> Optional[SessionData]:
        """세션 복구"""
        # 해당 사용자/페이지의 최근 세션 찾기
        for session in self.active_sessions.values():
            if session.user_id == user_id and session.page == page and not session.is_complete:
                return session

        # 저장소에서 복구 시도
        return self._load_from_storage(user_id, page)

    def complete_session(self, session_id: str) -> bool:
        """세션 완료"""
        if session_id not in self.active_sessions:
            return False

        self.active_sessions[session_id].is_complete = True
        return True

    def _save_to_storage(self, session: SessionData) -> None:
        """저장소에 저장 (시뮬레이션)"""
        # 실제로는 파일/DB에 저장
        pass

    def _load_from_storage(self, user_id: str, page: str) -> Optional[SessionData]:
        """저장소에서 로드 (시뮬레이션)"""
        # 실제로는 파일/DB에서 로드
        return None

    def get_recovery_prompt(self, session: SessionData) -> Dict:
        """복구 확인 프롬프트"""
        time_diff = datetime.now() - session.updated_at
        minutes_ago = int(time_diff.total_seconds() / 60)

        return {
            "show_prompt": True,
            "message": f"이전에 진행하던 연습이 있어요! ({minutes_ago}분 전)",
            "session_id": session.session_id,
            "data_summary": {
                "page": session.page,
                "progress": session.data.get("progress", 0),
                "questions_answered": session.data.get("questions_answered", 0),
            }
        }


# ============================================================
# 편의 함수들
# ============================================================

# 싱글톤 인스턴스
_stt_validator = MultiSTTValidator()
_progress_tracker = ProgressTracker()
_realtime_coach = RealTimeCoachingSystem()
_pronunciation_analyzer = PronunciationAnalyzer()
_nonverbal_analyzer = ExtendedNonverbalAnalyzer()
_session_manager = SessionManager()


def validate_stt(primary: STTResult, secondary: List[STTResult] = None) -> ValidatedSTTResult:
    """STT 결과 검증"""
    return _stt_validator.validate_and_correct(primary, secondary)


def start_progress_tracking(tasks: List[str]) -> None:
    """진행 상황 추적 시작"""
    _progress_tracker.start(tasks)


def update_progress(step: int, partial: Any = None) -> ProgressInfo:
    """진행 상황 업데이트"""
    return _progress_tracker.update(step, partial)


def get_progress_message(progress: ProgressInfo) -> str:
    """사용자용 진행 메시지"""
    return _progress_tracker.get_user_message(progress)


def get_realtime_coaching(**kwargs) -> Optional[RealTimeCoaching]:
    """실시간 코칭"""
    return _realtime_coach.analyze_realtime(**kwargs)


def analyze_pronunciation(audio_features: Dict, language: str = "ko") -> PronunciationAnalysis:
    """발음 분석"""
    return _pronunciation_analyzer.analyze(audio_features, language)


def analyze_nonverbal_extended(video_features: Dict, duration: float) -> ExtendedNonverbalAnalysis:
    """확장된 비언어 분석"""
    return _nonverbal_analyzer.analyze(video_features, duration)


def create_session(user_id: str, page: str, data: Dict = None) -> str:
    """세션 생성"""
    return _session_manager.create_session(user_id, page, data)


def update_session(session_id: str, data: Dict) -> bool:
    """세션 업데이트"""
    return _session_manager.update_session(session_id, data)


def recover_session(user_id: str, page: str) -> Optional[SessionData]:
    """세션 복구"""
    return _session_manager.recover_session(user_id, page)
