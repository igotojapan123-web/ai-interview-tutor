# progress_tracker.py
# FlyReady Lab - 종합 학습 진도 추적 모듈
# 세션, 시간, 점수, 스킬, 목표, 통계 및 차트 데이터 생성

import json
import os
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict
import statistics

from logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# 경로 설정
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 데이터 파일 경로
PROGRESS_FILE = DATA_DIR / "progress_tracker.json"
SESSION_HISTORY_FILE = DATA_DIR / "session_history.json"
SKILL_TRACKING_FILE = DATA_DIR / "skill_tracking.json"


# =============================================================================
# 스킬 카테고리 정의
# =============================================================================

SKILL_CATEGORIES = {
    "음성_스킬": {
        "발음": "발음의 정확성과 명확성",
        "속도": "말하는 속도의 적절성",
        "톤": "음성 톤의 자연스러움",
        "자신감": "음성에서 느껴지는 자신감"
    },
    "내용_스킬": {
        "구조": "답변 구조의 논리성",
        "구체성": "답변 내용의 구체성",
        "관련성": "질문과의 관련성",
        "키워드": "핵심 키워드 사용"
    },
    "감정_스킬": {
        "자신감": "전반적인 자신감 표현",
        "안정성": "감정의 안정성",
        "참여도": "면접에 대한 적극성"
    }
}

# 모든 스킬 목록 (플랫화)
ALL_SKILLS = []
for category, skills in SKILL_CATEGORIES.items():
    for skill_name in skills.keys():
        ALL_SKILLS.append(f"{category}_{skill_name}")


# =============================================================================
# 데이터 구조
# =============================================================================

@dataclass
class PracticeSession:
    """연습 세션 데이터"""
    session_id: str
    user_id: str
    session_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0
    scores: Dict[str, float] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "session_type": self.session_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "scores": self.scores,
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PracticeSession":
        return cls(
            session_id=data["session_id"],
            user_id=data["user_id"],
            session_type=data["session_type"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration_seconds=data.get("duration_seconds", 0),
            scores=data.get("scores", {}),
            details=data.get("details", {})
        )


@dataclass
class ScoreRecord:
    """점수 기록"""
    user_id: str
    category: str
    score: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "category": self.category,
            "score": self.score,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoreRecord":
        return cls(
            user_id=data["user_id"],
            category=data["category"],
            score=data["score"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            details=data.get("details", {})
        )


@dataclass
class SkillRecord:
    """스킬 기록"""
    user_id: str
    skill: str
    score: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "skill": self.skill,
            "score": self.score,
            "timestamp": self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillRecord":
        return cls(
            user_id=data["user_id"],
            skill=data["skill"],
            score=data["score"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


@dataclass
class DailyGoal:
    """일일 목표"""
    user_id: str
    date: str  # YYYY-MM-DD
    practice_count: int
    target_score: int
    completed_count: int = 0
    achieved_score: float = 0
    is_met: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "date": self.date,
            "practice_count": self.practice_count,
            "target_score": self.target_score,
            "completed_count": self.completed_count,
            "achieved_score": self.achieved_score,
            "is_met": self.is_met
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyGoal":
        return cls(
            user_id=data["user_id"],
            date=data["date"],
            practice_count=data["practice_count"],
            target_score=data["target_score"],
            completed_count=data.get("completed_count", 0),
            achieved_score=data.get("achieved_score", 0),
            is_met=data.get("is_met", False)
        )


# =============================================================================
# 진도 추적 시스템
# =============================================================================

class ProgressTracker:
    """종합 진도 추적 시스템 (싱글톤)"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._active_sessions: Dict[str, PracticeSession] = {}
        self._progress_data: Dict[str, Any] = {}
        self._session_history: List[Dict[str, Any]] = []
        self._skill_data: Dict[str, List[Dict[str, Any]]] = {}

        self._load_data()
        logger.info("ProgressTracker 초기화 완료")

    # =========================================================================
    # 데이터 로드/저장
    # =========================================================================

    def _load_data(self):
        """모든 데이터 로드"""
        try:
            # 진도 데이터 로드
            if PROGRESS_FILE.exists():
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    self._progress_data = json.load(f)
            else:
                self._progress_data = {"users": {}, "scores": [], "goals": {}}

            # 세션 히스토리 로드
            if SESSION_HISTORY_FILE.exists():
                with open(SESSION_HISTORY_FILE, "r", encoding="utf-8") as f:
                    self._session_history = json.load(f)
            else:
                self._session_history = []

            # 스킬 데이터 로드
            if SKILL_TRACKING_FILE.exists():
                with open(SKILL_TRACKING_FILE, "r", encoding="utf-8") as f:
                    self._skill_data = json.load(f)
            else:
                self._skill_data = {}

            logger.info("진도 데이터 로드 완료")
        except Exception as e:
            logger.error(f"데이터 로드 실패: {e}")
            self._progress_data = {"users": {}, "scores": [], "goals": {}}
            self._session_history = []
            self._skill_data = {}

    def _save_progress_data(self):
        """진도 데이터 저장"""
        try:
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"진도 데이터 저장 실패: {e}")

    def _save_session_history(self):
        """세션 히스토리 저장"""
        try:
            with open(SESSION_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._session_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"세션 히스토리 저장 실패: {e}")

    def _save_skill_data(self):
        """스킬 데이터 저장"""
        try:
            with open(SKILL_TRACKING_FILE, "w", encoding="utf-8") as f:
                json.dump(self._skill_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"스킬 데이터 저장 실패: {e}")

    def _ensure_user_data(self, user_id: str):
        """사용자 데이터 구조 보장"""
        if "users" not in self._progress_data:
            self._progress_data["users"] = {}

        if user_id not in self._progress_data["users"]:
            self._progress_data["users"][user_id] = {
                "created_at": datetime.now().isoformat(),
                "total_sessions": 0,
                "total_practice_time": 0,
                "scores_by_category": {},
                "last_active": datetime.now().isoformat()
            }

    # =========================================================================
    # 세션 추적
    # =========================================================================

    def start_session(self, user_id: str, session_type: str) -> str:
        """연습 세션 시작

        Args:
            user_id: 사용자 ID
            session_type: 세션 유형 (예: "면접연습", "자소서분석", "퀴즈")

        Returns:
            생성된 세션 ID
        """
        import secrets
        session_id = secrets.token_urlsafe(16)

        session = PracticeSession(
            session_id=session_id,
            user_id=user_id,
            session_type=session_type,
            start_time=datetime.now()
        )

        self._active_sessions[session_id] = session
        self._ensure_user_data(user_id)

        logger.info(f"세션 시작: user={user_id}, type={session_type}, session_id={session_id}")
        return session_id

    def end_session(self, session_id: str, session_data: dict = None) -> Optional[Dict[str, Any]]:
        """세션 종료 및 결과 저장

        Args:
            session_id: 세션 ID
            session_data: 세션 결과 데이터 (scores, details 등)

        Returns:
            완료된 세션 정보
        """
        if session_id not in self._active_sessions:
            logger.warning(f"존재하지 않는 세션: {session_id}")
            return None

        session = self._active_sessions[session_id]
        session.end_time = datetime.now()
        session.duration_seconds = (session.end_time - session.start_time).total_seconds()

        if session_data:
            session.scores = session_data.get("scores", {})
            session.details = session_data.get("details", {})

        # 세션 히스토리에 추가
        session_dict = session.to_dict()
        self._session_history.append(session_dict)
        self._save_session_history()

        # 사용자 통계 업데이트
        self._ensure_user_data(session.user_id)
        user_data = self._progress_data["users"][session.user_id]
        user_data["total_sessions"] += 1
        user_data["total_practice_time"] += session.duration_seconds
        user_data["last_active"] = datetime.now().isoformat()

        # 카테고리별 시간 추가
        if "time_by_category" not in user_data:
            user_data["time_by_category"] = {}
        cat = session.session_type
        user_data["time_by_category"][cat] = user_data["time_by_category"].get(cat, 0) + session.duration_seconds

        self._save_progress_data()

        # 일일 목표 업데이트
        self._update_daily_goal_progress(session.user_id, session.scores)

        # 활성 세션에서 제거
        del self._active_sessions[session_id]

        logger.info(f"세션 종료: session_id={session_id}, duration={session.duration_seconds:.1f}초")
        return session_dict

    def get_session_history(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """세션 히스토리 조회

        Args:
            user_id: 사용자 ID
            days: 조회할 기간 (일)

        Returns:
            세션 목록
        """
        cutoff = datetime.now() - timedelta(days=days)

        user_sessions = []
        for session in self._session_history:
            if session["user_id"] == user_id:
                session_time = datetime.fromisoformat(session["start_time"])
                if session_time >= cutoff:
                    user_sessions.append(session)

        # 최신 순으로 정렬
        user_sessions.sort(key=lambda x: x["start_time"], reverse=True)
        return user_sessions

    # =========================================================================
    # 시간 추적
    # =========================================================================

    def get_total_practice_time(self, user_id: str, period: str = "all") -> float:
        """총 연습 시간 조회

        Args:
            user_id: 사용자 ID
            period: 기간 ("today", "week", "month", "all")

        Returns:
            연습 시간 (초)
        """
        self._ensure_user_data(user_id)

        if period == "all":
            return self._progress_data["users"][user_id].get("total_practice_time", 0)

        # 기간별 계산
        now = datetime.now()
        if period == "today":
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            cutoff = now - timedelta(days=7)
        elif period == "month":
            cutoff = now - timedelta(days=30)
        else:
            cutoff = datetime.min

        total_time = 0
        for session in self._session_history:
            if session["user_id"] == user_id:
                session_time = datetime.fromisoformat(session["start_time"])
                if session_time >= cutoff:
                    total_time += session.get("duration_seconds", 0)

        return total_time

    def get_practice_time_by_category(self, user_id: str) -> Dict[str, float]:
        """카테고리별 연습 시간 조회

        Args:
            user_id: 사용자 ID

        Returns:
            카테고리별 시간 딕셔너리 (초)
        """
        self._ensure_user_data(user_id)
        return self._progress_data["users"][user_id].get("time_by_category", {})

    def get_average_session_duration(self, user_id: str) -> float:
        """평균 세션 길이 조회

        Args:
            user_id: 사용자 ID

        Returns:
            평균 세션 길이 (초)
        """
        user_sessions = [s for s in self._session_history if s["user_id"] == user_id]

        if not user_sessions:
            return 0

        total_duration = sum(s.get("duration_seconds", 0) for s in user_sessions)
        return total_duration / len(user_sessions)

    # =========================================================================
    # 점수 진도 추적
    # =========================================================================

    def track_score(self, user_id: str, category: str, score: float, details: dict = None):
        """점수 기록

        Args:
            user_id: 사용자 ID
            category: 카테고리 (예: "면접", "자소서", "퀴즈")
            score: 점수 (0-100)
            details: 추가 세부 정보
        """
        record = ScoreRecord(
            user_id=user_id,
            category=category,
            score=score,
            timestamp=datetime.now(),
            details=details or {}
        )

        if "scores" not in self._progress_data:
            self._progress_data["scores"] = []

        self._progress_data["scores"].append(record.to_dict())
        self._save_progress_data()

        logger.info(f"점수 기록: user={user_id}, category={category}, score={score}")

    def get_score_trend(self, user_id: str, category: str, days: int = 30) -> List[Dict[str, Any]]:
        """점수 추세 조회

        Args:
            user_id: 사용자 ID
            category: 카테고리
            days: 조회 기간 (일)

        Returns:
            날짜별 점수 목록
        """
        cutoff = datetime.now() - timedelta(days=days)

        scores = []
        for record in self._progress_data.get("scores", []):
            if record["user_id"] == user_id and record["category"] == category:
                record_time = datetime.fromisoformat(record["timestamp"])
                if record_time >= cutoff:
                    scores.append({
                        "date": record_time.strftime("%Y-%m-%d"),
                        "timestamp": record["timestamp"],
                        "score": record["score"]
                    })

        # 날짜순 정렬
        scores.sort(key=lambda x: x["timestamp"])
        return scores

    def get_improvement_rate(self, user_id: str, category: str) -> float:
        """개선율 계산 (주당 점수 변화)

        Args:
            user_id: 사용자 ID
            category: 카테고리

        Returns:
            주당 점수 개선율
        """
        trend = self.get_score_trend(user_id, category, days=30)

        if len(trend) < 2:
            return 0

        # 선형 회귀로 기울기 계산
        first_date = datetime.fromisoformat(trend[0]["timestamp"])

        x_values = []  # 일수
        y_values = []  # 점수

        for item in trend:
            item_date = datetime.fromisoformat(item["timestamp"])
            days_diff = (item_date - first_date).days
            x_values.append(days_diff)
            y_values.append(item["score"])

        if len(x_values) < 2:
            return 0

        # 간단한 선형 회귀
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0

        slope = (n * sum_xy - sum_x * sum_y) / denominator

        # 주당 개선율로 변환 (일당 기울기 * 7)
        weekly_rate = slope * 7
        return round(weekly_rate, 2)

    def get_best_score(self, user_id: str, category: str) -> Optional[Dict[str, Any]]:
        """최고 점수 조회

        Args:
            user_id: 사용자 ID
            category: 카테고리

        Returns:
            최고 점수 정보
        """
        best = None
        best_score = -1

        for record in self._progress_data.get("scores", []):
            if record["user_id"] == user_id and record["category"] == category:
                if record["score"] > best_score:
                    best_score = record["score"]
                    best = record

        return best

    def get_recent_average(self, user_id: str, category: str, count: int = 5) -> float:
        """최근 평균 점수 조회

        Args:
            user_id: 사용자 ID
            category: 카테고리
            count: 최근 기록 수

        Returns:
            평균 점수
        """
        scores = []
        for record in self._progress_data.get("scores", []):
            if record["user_id"] == user_id and record["category"] == category:
                scores.append((record["timestamp"], record["score"]))

        # 최신 순 정렬
        scores.sort(key=lambda x: x[0], reverse=True)
        recent_scores = [s[1] for s in scores[:count]]

        if not recent_scores:
            return 0

        return sum(recent_scores) / len(recent_scores)

    # =========================================================================
    # 스킬 기반 추적
    # =========================================================================

    def track_skill(self, user_id: str, skill: str, score: float):
        """개별 스킬 기록

        Args:
            user_id: 사용자 ID
            skill: 스킬 이름 (예: "음성_스킬_발음", "내용_스킬_구조")
            score: 점수 (0-100)
        """
        record = SkillRecord(
            user_id=user_id,
            skill=skill,
            score=score,
            timestamp=datetime.now()
        )

        if user_id not in self._skill_data:
            self._skill_data[user_id] = []

        self._skill_data[user_id].append(record.to_dict())
        self._save_skill_data()

        logger.info(f"스킬 기록: user={user_id}, skill={skill}, score={score}")

    def get_skill_profile(self, user_id: str) -> Dict[str, Any]:
        """스킬 프로필 (레이더 차트용)

        Args:
            user_id: 사용자 ID

        Returns:
            스킬별 최근 평균 점수
        """
        skill_scores = {}

        if user_id not in self._skill_data:
            return {"skills": [], "scores": [], "categories": SKILL_CATEGORIES}

        # 각 스킬의 최근 5개 점수 평균
        for category, skills in SKILL_CATEGORIES.items():
            for skill_name in skills.keys():
                full_skill = f"{category}_{skill_name}"
                scores = []

                for record in self._skill_data[user_id]:
                    if record["skill"] == full_skill:
                        scores.append((record["timestamp"], record["score"]))

                # 최신 순 정렬 후 최근 5개 평균
                scores.sort(key=lambda x: x[0], reverse=True)
                recent = [s[1] for s in scores[:5]]

                if recent:
                    skill_scores[full_skill] = sum(recent) / len(recent)
                else:
                    skill_scores[full_skill] = 0

        return {
            "skills": list(skill_scores.keys()),
            "scores": list(skill_scores.values()),
            "categories": SKILL_CATEGORIES
        }

    def get_skill_improvement(self, user_id: str, skill: str) -> Dict[str, Any]:
        """스킬 개선 추적

        Args:
            user_id: 사용자 ID
            skill: 스킬 이름

        Returns:
            개선 정보
        """
        if user_id not in self._skill_data:
            return {"skill": skill, "improvement": 0, "current": 0, "previous": 0}

        scores = []
        for record in self._skill_data[user_id]:
            if record["skill"] == skill:
                scores.append((record["timestamp"], record["score"]))

        if len(scores) < 2:
            current = scores[0][1] if scores else 0
            return {"skill": skill, "improvement": 0, "current": current, "previous": current}

        # 최신 순 정렬
        scores.sort(key=lambda x: x[0], reverse=True)

        # 최근 5개 평균 vs 이전 5개 평균
        recent = [s[1] for s in scores[:5]]
        previous = [s[1] for s in scores[5:10]] if len(scores) > 5 else recent

        current_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        improvement = current_avg - previous_avg

        return {
            "skill": skill,
            "improvement": round(improvement, 2),
            "current": round(current_avg, 2),
            "previous": round(previous_avg, 2)
        }

    # =========================================================================
    # 목표 진도
    # =========================================================================

    def set_daily_goal(self, user_id: str, practice_count: int, target_score: int):
        """일일 목표 설정

        Args:
            user_id: 사용자 ID
            practice_count: 목표 연습 횟수
            target_score: 목표 점수
        """
        today = datetime.now().strftime("%Y-%m-%d")

        goal = DailyGoal(
            user_id=user_id,
            date=today,
            practice_count=practice_count,
            target_score=target_score
        )

        if "goals" not in self._progress_data:
            self._progress_data["goals"] = {}

        if user_id not in self._progress_data["goals"]:
            self._progress_data["goals"][user_id] = {}

        self._progress_data["goals"][user_id][today] = goal.to_dict()
        self._save_progress_data()

        logger.info(f"일일 목표 설정: user={user_id}, count={practice_count}, score={target_score}")

    def _update_daily_goal_progress(self, user_id: str, scores: Dict[str, float]):
        """일일 목표 진도 업데이트 (내부 함수)"""
        today = datetime.now().strftime("%Y-%m-%d")

        goals = self._progress_data.get("goals", {}).get(user_id, {})
        if today not in goals:
            return

        goal = goals[today]
        goal["completed_count"] = goal.get("completed_count", 0) + 1

        # 점수 업데이트 (가장 높은 점수 사용)
        if scores:
            max_score = max(scores.values()) if scores else 0
            current_achieved = goal.get("achieved_score", 0)
            goal["achieved_score"] = max(current_achieved, max_score)

        # 목표 달성 확인
        goal["is_met"] = (
            goal["completed_count"] >= goal["practice_count"] and
            goal.get("achieved_score", 0) >= goal["target_score"]
        )

        self._save_progress_data()

    def check_daily_goal(self, user_id: str) -> Dict[str, Any]:
        """일일 목표 달성 확인

        Args:
            user_id: 사용자 ID

        Returns:
            목표 달성 상태
        """
        today = datetime.now().strftime("%Y-%m-%d")
        goals = self._progress_data.get("goals", {}).get(user_id, {})

        if today not in goals:
            return {
                "has_goal": False,
                "is_met": False,
                "progress_percent": 0
            }

        goal = goals[today]
        count_progress = min(goal.get("completed_count", 0) / max(goal["practice_count"], 1), 1)
        score_progress = min(goal.get("achieved_score", 0) / max(goal["target_score"], 1), 1)

        return {
            "has_goal": True,
            "is_met": goal.get("is_met", False),
            "practice_count": goal["practice_count"],
            "completed_count": goal.get("completed_count", 0),
            "target_score": goal["target_score"],
            "achieved_score": goal.get("achieved_score", 0),
            "count_progress": round(count_progress * 100, 1),
            "score_progress": round(score_progress * 100, 1),
            "overall_progress": round((count_progress + score_progress) / 2 * 100, 1)
        }

    def get_goal_streak(self, user_id: str) -> int:
        """목표 연속 달성 일수

        Args:
            user_id: 사용자 ID

        Returns:
            연속 달성 일수
        """
        goals = self._progress_data.get("goals", {}).get(user_id, {})

        if not goals:
            return 0

        streak = 0
        current_date = datetime.now().date()

        while True:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in goals and goals[date_str].get("is_met", False):
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break

        return streak

    def get_weekly_goal_completion(self, user_id: str) -> Dict[str, Any]:
        """주간 목표 달성율

        Args:
            user_id: 사용자 ID

        Returns:
            주간 달성율 정보
        """
        goals = self._progress_data.get("goals", {}).get(user_id, {})

        # 최근 7일
        today = datetime.now().date()
        week_goals = []
        met_count = 0

        for i in range(7):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in goals:
                week_goals.append(goals[date])
                if goals[date].get("is_met", False):
                    met_count += 1

        total = len(week_goals)

        return {
            "total_days_with_goal": total,
            "met_count": met_count,
            "completion_rate": round(met_count / max(total, 1) * 100, 1),
            "current_streak": self.get_goal_streak(user_id)
        }

    # =========================================================================
    # 통계 및 분석
    # =========================================================================

    def get_practice_statistics(self, user_id: str) -> Dict[str, Any]:
        """종합 통계

        Args:
            user_id: 사용자 ID

        Returns:
            종합 통계 정보
        """
        self._ensure_user_data(user_id)
        user_data = self._progress_data["users"][user_id]

        # 세션 통계
        user_sessions = [s for s in self._session_history if s["user_id"] == user_id]
        session_durations = [s.get("duration_seconds", 0) for s in user_sessions]

        # 점수 통계
        user_scores = [r for r in self._progress_data.get("scores", []) if r["user_id"] == user_id]
        score_values = [r["score"] for r in user_scores]

        return {
            "총_세션_수": user_data.get("total_sessions", 0),
            "총_연습_시간": user_data.get("total_practice_time", 0),
            "총_연습_시간_포맷": self._format_duration(user_data.get("total_practice_time", 0)),
            "평균_세션_길이": statistics.mean(session_durations) if session_durations else 0,
            "평균_세션_길이_포맷": self._format_duration(statistics.mean(session_durations) if session_durations else 0),
            "최장_세션": max(session_durations) if session_durations else 0,
            "총_점수_기록_수": len(user_scores),
            "평균_점수": round(statistics.mean(score_values), 1) if score_values else 0,
            "최고_점수": max(score_values) if score_values else 0,
            "최저_점수": min(score_values) if score_values else 0,
            "점수_표준편차": round(statistics.stdev(score_values), 2) if len(score_values) > 1 else 0,
            "카테고리별_시간": user_data.get("time_by_category", {}),
            "마지막_활동": user_data.get("last_active"),
            "가입일": user_data.get("created_at")
        }

    def _format_duration(self, seconds: float) -> str:
        """시간 포맷팅"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}시간 {minutes}분"
        elif minutes > 0:
            return f"{minutes}분 {secs}초"
        else:
            return f"{secs}초"

    def get_activity_heatmap(self, user_id: str, weeks: int = 12) -> List[Dict[str, Any]]:
        """활동 히트맵 데이터

        Args:
            user_id: 사용자 ID
            weeks: 주 수

        Returns:
            날짜별 활동 데이터
        """
        days = weeks * 7
        cutoff = datetime.now() - timedelta(days=days)

        # 날짜별 세션 수 계산
        activity = defaultdict(int)

        for session in self._session_history:
            if session["user_id"] == user_id:
                session_time = datetime.fromisoformat(session["start_time"])
                if session_time >= cutoff:
                    date_str = session_time.strftime("%Y-%m-%d")
                    activity[date_str] += 1

        # 모든 날짜에 대해 데이터 생성
        result = []
        current = datetime.now().date()

        for i in range(days):
            date = current - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            result.append({
                "date": date_str,
                "count": activity.get(date_str, 0),
                "weekday": date.weekday(),
                "week": i // 7
            })

        result.reverse()
        return result

    def get_peak_performance_time(self, user_id: str) -> Dict[str, Any]:
        """최고 성과 시간대 분석

        Args:
            user_id: 사용자 ID

        Returns:
            시간대별 성과 분석
        """
        # 시간대별 점수 수집
        hour_scores = defaultdict(list)

        for record in self._progress_data.get("scores", []):
            if record["user_id"] == user_id:
                timestamp = datetime.fromisoformat(record["timestamp"])
                hour = timestamp.hour
                hour_scores[hour].append(record["score"])

        # 시간대별 평균 계산
        hour_averages = {}
        for hour, scores in hour_scores.items():
            hour_averages[hour] = sum(scores) / len(scores)

        if not hour_averages:
            return {
                "best_hour": None,
                "best_avg_score": 0,
                "hourly_averages": {},
                "recommendation": "더 많은 연습 데이터가 필요합니다."
            }

        # 최고 시간대 찾기
        best_hour = max(hour_averages.keys(), key=lambda x: hour_averages[x])

        # 시간대 설명
        time_periods = {
            range(6, 9): "이른 아침",
            range(9, 12): "오전",
            range(12, 14): "점심 시간",
            range(14, 18): "오후",
            range(18, 21): "저녁",
            range(21, 24): "밤",
            range(0, 6): "새벽"
        }

        period_name = "알 수 없음"
        for period, name in time_periods.items():
            if best_hour in period:
                period_name = name
                break

        return {
            "best_hour": best_hour,
            "best_period": period_name,
            "best_avg_score": round(hour_averages[best_hour], 1),
            "hourly_averages": {str(k): round(v, 1) for k, v in sorted(hour_averages.items())},
            "recommendation": f"{period_name} 시간대({best_hour}시)에 가장 높은 성과를 보입니다."
        }

    def predict_score(self, user_id: str, category: str) -> Dict[str, Any]:
        """다음 점수 예측

        Args:
            user_id: 사용자 ID
            category: 카테고리

        Returns:
            예측 정보
        """
        trend = self.get_score_trend(user_id, category, days=30)

        if len(trend) < 3:
            return {
                "predicted_score": None,
                "confidence": "낮음",
                "reason": "예측을 위한 충분한 데이터가 없습니다."
            }

        # 최근 점수들
        recent_scores = [t["score"] for t in trend[-10:]]

        # 간단한 이동 평균 기반 예측
        if len(recent_scores) >= 5:
            # 최근 5개 평균과 추세 고려
            recent_avg = sum(recent_scores[-5:]) / 5
            improvement_rate = self.get_improvement_rate(user_id, category)

            # 일주일 후 예측
            predicted = recent_avg + improvement_rate
            predicted = max(0, min(100, predicted))  # 0-100 범위로 제한

            confidence = "높음" if len(trend) >= 10 else "중간"
        else:
            predicted = sum(recent_scores) / len(recent_scores)
            confidence = "낮음"

        return {
            "predicted_score": round(predicted, 1),
            "confidence": confidence,
            "current_average": round(sum(recent_scores) / len(recent_scores), 1),
            "improvement_rate": self.get_improvement_rate(user_id, category),
            "data_points": len(trend)
        }

    # =========================================================================
    # 차트 데이터 생성 (Plotly용)
    # =========================================================================

    def get_score_line_chart_data(self, user_id: str, category: str, days: int = 30) -> Dict[str, Any]:
        """점수 라인 차트 데이터

        Args:
            user_id: 사용자 ID
            category: 카테고리
            days: 기간

        Returns:
            Plotly 라인 차트용 데이터
        """
        trend = self.get_score_trend(user_id, category, days)

        dates = [t["date"] for t in trend]
        scores = [t["score"] for t in trend]

        # 이동 평균 계산 (5일)
        moving_avg = []
        for i in range(len(scores)):
            start = max(0, i - 4)
            window = scores[start:i + 1]
            moving_avg.append(sum(window) / len(window))

        return {
            "x": dates,
            "y_scores": scores,
            "y_moving_avg": moving_avg,
            "title": f"{category} 점수 추이",
            "x_label": "날짜",
            "y_label": "점수"
        }

    def get_skill_radar_chart_data(self, user_id: str) -> Dict[str, Any]:
        """스킬 레이더 차트 데이터

        Args:
            user_id: 사용자 ID

        Returns:
            Plotly 레이더 차트용 데이터
        """
        profile = self.get_skill_profile(user_id)

        # 스킬 이름 한글화
        skill_labels = []
        for skill in profile["skills"]:
            # "음성_스킬_발음" -> "발음"
            parts = skill.split("_")
            if len(parts) >= 3:
                skill_labels.append(parts[-1])
            else:
                skill_labels.append(skill)

        return {
            "categories": skill_labels,
            "values": profile["scores"],
            "title": "스킬 프로필",
            "max_value": 100
        }

    def get_time_bar_chart_data(self, user_id: str, period: str = "week") -> Dict[str, Any]:
        """시간 바 차트 데이터

        Args:
            user_id: 사용자 ID
            period: 기간 ("week", "month")

        Returns:
            Plotly 바 차트용 데이터
        """
        days = 7 if period == "week" else 30
        cutoff = datetime.now() - timedelta(days=days)

        # 날짜별 연습 시간
        daily_time = defaultdict(float)

        for session in self._session_history:
            if session["user_id"] == user_id:
                session_time = datetime.fromisoformat(session["start_time"])
                if session_time >= cutoff:
                    date_str = session_time.strftime("%Y-%m-%d")
                    daily_time[date_str] += session.get("duration_seconds", 0)

        # 날짜 순서대로 정렬
        dates = []
        times = []
        current = datetime.now().date()

        for i in range(days):
            date = current - timedelta(days=days - 1 - i)
            date_str = date.strftime("%Y-%m-%d")
            dates.append(date.strftime("%m/%d"))
            times.append(round(daily_time.get(date_str, 0) / 60, 1))  # 분 단위

        return {
            "x": dates,
            "y": times,
            "title": f"{'주간' if period == 'week' else '월간'} 연습 시간",
            "x_label": "날짜",
            "y_label": "연습 시간 (분)"
        }

    def get_category_pie_chart_data(self, user_id: str) -> Dict[str, Any]:
        """카테고리 파이 차트 데이터

        Args:
            user_id: 사용자 ID

        Returns:
            Plotly 파이 차트용 데이터
        """
        time_by_category = self.get_practice_time_by_category(user_id)

        if not time_by_category:
            return {
                "labels": ["데이터 없음"],
                "values": [1],
                "title": "카테고리별 연습 분포"
            }

        labels = list(time_by_category.keys())
        values = [round(v / 60, 1) for v in time_by_category.values()]  # 분 단위

        return {
            "labels": labels,
            "values": values,
            "title": "카테고리별 연습 분포",
            "unit": "분"
        }

    # =========================================================================
    # 비교 분석
    # =========================================================================

    def compare_with_previous_week(self, user_id: str) -> Dict[str, Any]:
        """이번 주와 지난 주 비교

        Args:
            user_id: 사용자 ID

        Returns:
            비교 분석 결과
        """
        now = datetime.now()
        this_week_start = now - timedelta(days=7)
        last_week_start = now - timedelta(days=14)

        # 이번 주 데이터
        this_week_sessions = 0
        this_week_time = 0
        this_week_scores = []

        # 지난 주 데이터
        last_week_sessions = 0
        last_week_time = 0
        last_week_scores = []

        for session in self._session_history:
            if session["user_id"] == user_id:
                session_time = datetime.fromisoformat(session["start_time"])

                if session_time >= this_week_start:
                    this_week_sessions += 1
                    this_week_time += session.get("duration_seconds", 0)
                elif session_time >= last_week_start:
                    last_week_sessions += 1
                    last_week_time += session.get("duration_seconds", 0)

        for record in self._progress_data.get("scores", []):
            if record["user_id"] == user_id:
                record_time = datetime.fromisoformat(record["timestamp"])

                if record_time >= this_week_start:
                    this_week_scores.append(record["score"])
                elif record_time >= last_week_start:
                    last_week_scores.append(record["score"])

        # 비교 계산
        def calc_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round((current - previous) / previous * 100, 1)

        this_avg = sum(this_week_scores) / len(this_week_scores) if this_week_scores else 0
        last_avg = sum(last_week_scores) / len(last_week_scores) if last_week_scores else 0

        return {
            "이번_주": {
                "세션_수": this_week_sessions,
                "총_시간": round(this_week_time / 60, 1),
                "평균_점수": round(this_avg, 1)
            },
            "지난_주": {
                "세션_수": last_week_sessions,
                "총_시간": round(last_week_time / 60, 1),
                "평균_점수": round(last_avg, 1)
            },
            "변화": {
                "세션_변화율": calc_change(this_week_sessions, last_week_sessions),
                "시간_변화율": calc_change(this_week_time, last_week_time),
                "점수_변화": round(this_avg - last_avg, 1)
            },
            "요약": self._generate_comparison_summary(
                this_week_sessions, last_week_sessions,
                this_week_time, last_week_time,
                this_avg, last_avg
            )
        }

    def compare_with_previous_month(self, user_id: str) -> Dict[str, Any]:
        """이번 달과 지난 달 비교

        Args:
            user_id: 사용자 ID

        Returns:
            비교 분석 결과
        """
        now = datetime.now()
        this_month_start = now - timedelta(days=30)
        last_month_start = now - timedelta(days=60)

        # 이번 달 데이터
        this_month_sessions = 0
        this_month_time = 0
        this_month_scores = []

        # 지난 달 데이터
        last_month_sessions = 0
        last_month_time = 0
        last_month_scores = []

        for session in self._session_history:
            if session["user_id"] == user_id:
                session_time = datetime.fromisoformat(session["start_time"])

                if session_time >= this_month_start:
                    this_month_sessions += 1
                    this_month_time += session.get("duration_seconds", 0)
                elif session_time >= last_month_start:
                    last_month_sessions += 1
                    last_month_time += session.get("duration_seconds", 0)

        for record in self._progress_data.get("scores", []):
            if record["user_id"] == user_id:
                record_time = datetime.fromisoformat(record["timestamp"])

                if record_time >= this_month_start:
                    this_month_scores.append(record["score"])
                elif record_time >= last_month_start:
                    last_month_scores.append(record["score"])

        def calc_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return round((current - previous) / previous * 100, 1)

        this_avg = sum(this_month_scores) / len(this_month_scores) if this_month_scores else 0
        last_avg = sum(last_month_scores) / len(last_month_scores) if last_month_scores else 0

        return {
            "이번_달": {
                "세션_수": this_month_sessions,
                "총_시간": round(this_month_time / 60, 1),
                "평균_점수": round(this_avg, 1)
            },
            "지난_달": {
                "세션_수": last_month_sessions,
                "총_시간": round(last_month_time / 60, 1),
                "평균_점수": round(last_avg, 1)
            },
            "변화": {
                "세션_변화율": calc_change(this_month_sessions, last_month_sessions),
                "시간_변화율": calc_change(this_month_time, last_month_time),
                "점수_변화": round(this_avg - last_avg, 1)
            }
        }

    def _generate_comparison_summary(
        self,
        this_sessions: int, last_sessions: int,
        this_time: float, last_time: float,
        this_score: float, last_score: float
    ) -> str:
        """비교 요약 생성"""
        summaries = []

        # 세션 비교
        if this_sessions > last_sessions:
            summaries.append(f"연습 횟수가 {this_sessions - last_sessions}회 증가했습니다.")
        elif this_sessions < last_sessions:
            summaries.append(f"연습 횟수가 {last_sessions - this_sessions}회 감소했습니다.")

        # 점수 비교
        score_diff = this_score - last_score
        if score_diff > 0:
            summaries.append(f"평균 점수가 {score_diff:.1f}점 상승했습니다.")
        elif score_diff < 0:
            summaries.append(f"평균 점수가 {abs(score_diff):.1f}점 하락했습니다.")

        if not summaries:
            return "지난 기간과 비슷한 성과를 보이고 있습니다."

        return " ".join(summaries)

    def get_percentile_history(self, user_id: str) -> List[Dict[str, Any]]:
        """백분위 순위 히스토리

        Args:
            user_id: 사용자 ID

        Returns:
            날짜별 백분위 순위
        """
        # 날짜별로 모든 사용자의 점수 수집
        date_scores = defaultdict(lambda: defaultdict(list))

        for record in self._progress_data.get("scores", []):
            date = datetime.fromisoformat(record["timestamp"]).strftime("%Y-%m-%d")
            uid = record["user_id"]
            date_scores[date][uid].append(record["score"])

        # 각 날짜에서 사용자의 백분위 계산
        percentile_history = []

        for date in sorted(date_scores.keys()):
            day_data = date_scores[date]

            # 각 사용자의 평균 점수
            user_avgs = {}
            for uid, scores in day_data.items():
                user_avgs[uid] = sum(scores) / len(scores)

            if user_id not in user_avgs:
                continue

            # 백분위 계산
            user_score = user_avgs[user_id]
            all_scores = list(user_avgs.values())

            if len(all_scores) == 1:
                percentile = 100
            else:
                below = sum(1 for s in all_scores if s < user_score)
                percentile = round(below / len(all_scores) * 100, 1)

            percentile_history.append({
                "date": date,
                "percentile": percentile,
                "score": round(user_score, 1),
                "total_users": len(all_scores)
            })

        return percentile_history


# =============================================================================
# 전역 인스턴스
# =============================================================================

_tracker = ProgressTracker()


def get_tracker() -> ProgressTracker:
    """진도 추적기 인스턴스 반환"""
    return _tracker


# =============================================================================
# 편의 함수
# =============================================================================

# 세션 추적
def start_session(user_id: str, session_type: str) -> str:
    """세션 시작"""
    return _tracker.start_session(user_id, session_type)


def end_session(session_id: str, session_data: dict = None) -> Optional[Dict[str, Any]]:
    """세션 종료"""
    return _tracker.end_session(session_id, session_data)


def get_session_history(user_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """세션 히스토리 조회"""
    return _tracker.get_session_history(user_id, days)


# 시간 추적
def get_total_practice_time(user_id: str, period: str = "all") -> float:
    """총 연습 시간 조회"""
    return _tracker.get_total_practice_time(user_id, period)


def get_practice_time_by_category(user_id: str) -> Dict[str, float]:
    """카테고리별 연습 시간"""
    return _tracker.get_practice_time_by_category(user_id)


def get_average_session_duration(user_id: str) -> float:
    """평균 세션 길이"""
    return _tracker.get_average_session_duration(user_id)


# 점수 추적
def track_score(user_id: str, category: str, score: float, details: dict = None):
    """점수 기록"""
    _tracker.track_score(user_id, category, score, details)


def get_score_trend(user_id: str, category: str, days: int = 30) -> List[Dict[str, Any]]:
    """점수 추세 조회"""
    return _tracker.get_score_trend(user_id, category, days)


def get_improvement_rate(user_id: str, category: str) -> float:
    """개선율 조회"""
    return _tracker.get_improvement_rate(user_id, category)


def get_best_score(user_id: str, category: str) -> Optional[Dict[str, Any]]:
    """최고 점수 조회"""
    return _tracker.get_best_score(user_id, category)


def get_recent_average(user_id: str, category: str, count: int = 5) -> float:
    """최근 평균 점수"""
    return _tracker.get_recent_average(user_id, category, count)


# 스킬 추적
def track_skill(user_id: str, skill: str, score: float):
    """스킬 기록"""
    _tracker.track_skill(user_id, skill, score)


def get_skill_profile(user_id: str) -> Dict[str, Any]:
    """스킬 프로필 조회"""
    return _tracker.get_skill_profile(user_id)


def get_skill_improvement(user_id: str, skill: str) -> Dict[str, Any]:
    """스킬 개선 조회"""
    return _tracker.get_skill_improvement(user_id, skill)


# 목표 추적
def set_daily_goal(user_id: str, practice_count: int, target_score: int):
    """일일 목표 설정"""
    _tracker.set_daily_goal(user_id, practice_count, target_score)


def check_daily_goal(user_id: str) -> Dict[str, Any]:
    """일일 목표 확인"""
    return _tracker.check_daily_goal(user_id)


def get_goal_streak(user_id: str) -> int:
    """목표 연속 달성 일수"""
    return _tracker.get_goal_streak(user_id)


def get_weekly_goal_completion(user_id: str) -> Dict[str, Any]:
    """주간 목표 달성율"""
    return _tracker.get_weekly_goal_completion(user_id)


# 통계
def get_practice_statistics(user_id: str) -> Dict[str, Any]:
    """종합 통계"""
    return _tracker.get_practice_statistics(user_id)


def get_activity_heatmap(user_id: str, weeks: int = 12) -> List[Dict[str, Any]]:
    """활동 히트맵 데이터"""
    return _tracker.get_activity_heatmap(user_id, weeks)


def get_peak_performance_time(user_id: str) -> Dict[str, Any]:
    """최고 성과 시간대"""
    return _tracker.get_peak_performance_time(user_id)


def predict_score(user_id: str, category: str) -> Dict[str, Any]:
    """점수 예측"""
    return _tracker.predict_score(user_id, category)


# 차트 데이터
def get_score_line_chart_data(user_id: str, category: str, days: int = 30) -> Dict[str, Any]:
    """점수 라인 차트 데이터"""
    return _tracker.get_score_line_chart_data(user_id, category, days)


def get_skill_radar_chart_data(user_id: str) -> Dict[str, Any]:
    """스킬 레이더 차트 데이터"""
    return _tracker.get_skill_radar_chart_data(user_id)


def get_time_bar_chart_data(user_id: str, period: str = "week") -> Dict[str, Any]:
    """시간 바 차트 데이터"""
    return _tracker.get_time_bar_chart_data(user_id, period)


def get_category_pie_chart_data(user_id: str) -> Dict[str, Any]:
    """카테고리 파이 차트 데이터"""
    return _tracker.get_category_pie_chart_data(user_id)


# 비교 분석
def compare_with_previous_week(user_id: str) -> Dict[str, Any]:
    """이전 주와 비교"""
    return _tracker.compare_with_previous_week(user_id)


def compare_with_previous_month(user_id: str) -> Dict[str, Any]:
    """이전 달과 비교"""
    return _tracker.compare_with_previous_month(user_id)


def get_percentile_history(user_id: str) -> List[Dict[str, Any]]:
    """백분위 히스토리"""
    return _tracker.get_percentile_history(user_id)
