# multiplayer_service.py
# FlyReady Lab 멀티플레이어 면접 서비스
# room_manager를 기반으로 한 고수준 멀티플레이어 기능

import json
import random
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from logging_config import get_logger
from room_manager import (
    get_room_manager, get_room, set_questions, get_current_question,
    next_question, submit_answer, get_all_answers, next_turn,
    get_room_state, RoomType, RoomStatus, ParticipantStatus
)
from airline_questions import get_airline_questions, get_airline_values

logger = get_logger(__name__)

# 데이터 디렉토리
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

MATCH_HISTORY_FILE = DATA_DIR / "match_history.json"
COMPETITION_SCORES_FILE = DATA_DIR / "competition_scores.json"

# ========================================
# 토론 주제 목록 (한국어)
# ========================================

DEBATE_TOPICS = [
    {
        "id": "mask_policy",
        "topic": "기내 마스크 착용 의무화에 대한 찬반",
        "description": "코로나19 이후 기내 마스크 착용 의무화 정책의 유지 여부에 대해 토론합니다.",
        "pro_points": ["승객 건강 보호", "집단 감염 예방", "면역력 약한 승객 배려"],
        "con_points": ["개인 선택권 존중", "불편함과 호흡 곤란", "일상 회복 필요"]
    },
    {
        "id": "lcc_vs_fsc",
        "topic": "LCC와 FSC 중 어디가 더 좋은 직장인가",
        "description": "저비용항공사(LCC)와 대형항공사(FSC)의 근무환경과 경력 발전을 비교합니다.",
        "pro_points": ["FSC: 안정성, 높은 급여, 체계적 교육, 글로벌 네트워크"],
        "con_points": ["LCC: 빠른 성장, 다양한 경험, 유연한 문화, 젊은 조직"]
    },
    {
        "id": "ai_crew",
        "topic": "AI 승무원 도입에 대한 찬반",
        "description": "인공지능 로봇 승무원의 기내 서비스 도입 가능성에 대해 토론합니다.",
        "pro_points": ["일관된 서비스 품질", "언어 장벽 해소", "비용 절감"],
        "con_points": ["인간적 감성 서비스 불가", "긴급 상황 대응 한계", "일자리 감소"]
    },
    {
        "id": "electronic_devices",
        "topic": "기내 전자기기 사용 제한 완화에 대한 찬반",
        "description": "이착륙 시 전자기기 사용 제한 완화 정책에 대해 토론합니다.",
        "pro_points": ["현대인의 필수품", "항공 기술 발전으로 안전", "고객 편의성 증대"],
        "con_points": ["안전 우선 원칙", "승무원 안내 집중 방해", "비상시 대응 지연"]
    },
    {
        "id": "alcohol_service",
        "topic": "기내 주류 판매 제한에 대한 찬반",
        "description": "기내 음주 관련 문제 예방을 위한 주류 판매 제한에 대해 토론합니다.",
        "pro_points": ["난동 승객 예방", "안전한 비행 환경", "승무원 업무 부담 감소"],
        "con_points": ["성인의 선택권", "프리미엄 서비스 제한", "매출 감소"]
    },
    {
        "id": "uniform_freedom",
        "topic": "승무원 복장 자율화에 대한 찬반",
        "description": "승무원 유니폼 착용 의무 완화에 대해 토론합니다.",
        "pro_points": ["개성 표현", "편안한 근무환경", "시대 변화 반영"],
        "con_points": ["브랜드 통일성", "전문성 표현", "승객 식별 용이"]
    },
    {
        "id": "child_free_zone",
        "topic": "기내 어린이 탑승 제한 구역 설정에 대한 찬반",
        "description": "비즈니스석 등 특정 구역의 어린이 탑승 제한에 대해 토론합니다.",
        "pro_points": ["조용한 비행 환경", "업무 승객 배려", "고객 선택권"],
        "con_points": ["가족 차별", "어린이 권리", "항공사 이미지"]
    },
    {
        "id": "pet_cabin",
        "topic": "반려동물 기내 동반 확대에 대한 찬반",
        "description": "반려동물의 기내(객실) 동반 탑승 확대에 대해 토론합니다.",
        "pro_points": ["반려동물 복지", "반려인 증가 추세", "화물칸 스트레스 방지"],
        "con_points": ["알레르기 승객", "소음 문제", "위생 관리 어려움"]
    },
]


# ========================================
# 보상 시스템
# ========================================

REWARDS = {
    "winner": {
        "points": 100,
        "title": "면접 우승자",
        "description": "그룹 면접에서 1위를 차지했습니다."
    },
    "runner_up": {
        "points": 70,
        "title": "준우승",
        "description": "그룹 면접에서 2위를 차지했습니다."
    },
    "third_place": {
        "points": 50,
        "title": "3위",
        "description": "그룹 면접에서 3위를 차지했습니다."
    },
    "participant": {
        "points": 30,
        "title": "참가자",
        "description": "그룹 면접에 참가하여 끝까지 완주했습니다."
    },
    "best_answer": {
        "points": 20,
        "title": "베스트 답변",
        "description": "가장 높은 점수의 답변을 했습니다."
    },
    "debate_winner": {
        "points": 80,
        "title": "토론 승리",
        "description": "토론에서 승리했습니다."
    },
    "best_argument": {
        "points": 15,
        "title": "베스트 논점",
        "description": "가장 설득력 있는 주장을 펼쳤습니다."
    },
    "streak_3": {
        "points": 25,
        "title": "3연승",
        "description": "연속 3회 우승했습니다."
    },
    "streak_5": {
        "points": 50,
        "title": "5연승",
        "description": "연속 5회 우승했습니다."
    },
    "perfect_score": {
        "points": 30,
        "title": "퍼펙트 스코어",
        "description": "모든 질문에서 80점 이상을 받았습니다."
    },
}


# ========================================
# 토론 상태 관리
# ========================================

class DebatePhase(str, Enum):
    """토론 진행 단계"""
    OPENING = "opening"          # 입론
    ARGUMENT = "argument"        # 본론
    REBUTTAL = "rebuttal"        # 반론
    CLOSING = "closing"          # 최종 변론
    EVALUATION = "evaluation"    # 평가


@dataclass
class DebateState:
    """토론 상태"""
    topic: Dict[str, Any] = field(default_factory=dict)
    phase: str = DebatePhase.OPENING
    positions: Dict[str, str] = field(default_factory=dict)  # user_id -> "pro" or "con"
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    rebuttals: List[Dict[str, Any]] = field(default_factory=list)
    current_speaker_id: Optional[str] = None
    turn_order: List[str] = field(default_factory=list)
    current_turn_idx: int = 0
    rebuttal_round: int = 0
    max_rebuttal_rounds: int = 2
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    scores: Dict[str, Dict[str, float]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DebateState":
        return cls(**data)


# ========================================
# 인터뷰 세션 상태
# ========================================

@dataclass
class InterviewSession:
    """그룹 면접 세션 상태"""
    room_id: str
    airline: str
    question_count: int
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    questions: List[str] = field(default_factory=list)
    current_question_idx: int = 0
    scores: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)  # user_id -> [score_data]
    timer_data: Dict[str, Any] = field(default_factory=dict)
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ========================================
# 멀티플레이어 서비스 클래스
# ========================================

class MultiplayerService:
    """멀티플레이어 면접 서비스"""

    def __init__(self):
        self._ensure_data_files()
        self._interview_sessions: Dict[str, InterviewSession] = {}
        self._debate_states: Dict[str, DebateState] = {}
        self._timers: Dict[str, Dict[str, Any]] = {}
        self._spectators: Dict[str, List[str]] = {}  # room_id -> [user_id]
        self._spectator_comments: Dict[str, List[Dict[str, Any]]] = {}
        self._live_scores: Dict[str, Dict[str, Dict[str, float]]] = {}  # room_id -> user_id -> category -> score
        logger.info("멀티플레이어 서비스 초기화 완료")

    def _ensure_data_files(self) -> None:
        """데이터 파일 초기화"""
        if not MATCH_HISTORY_FILE.exists():
            self._save_match_history([])
            logger.info(f"매치 히스토리 파일 생성: {MATCH_HISTORY_FILE}")

        if not COMPETITION_SCORES_FILE.exists():
            self._save_competition_scores({})
            logger.info(f"경쟁 점수 파일 생성: {COMPETITION_SCORES_FILE}")

    def _load_match_history(self) -> List[Dict[str, Any]]:
        """매치 히스토리 로드"""
        try:
            with open(MATCH_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_match_history(self, history: List[Dict[str, Any]]) -> None:
        """매치 히스토리 저장"""
        with open(MATCH_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def _load_competition_scores(self) -> Dict[str, Any]:
        """경쟁 점수 로드"""
        try:
            with open(COMPETITION_SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_competition_scores(self, scores: Dict[str, Any]) -> None:
        """경쟁 점수 저장"""
        with open(COMPETITION_SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)

    # ========================================
    # 1. 그룹 면접 세션
    # ========================================

    def start_group_interview(
        self,
        room_id: str,
        airline: str,
        question_count: int = 5
    ) -> Dict[str, Any]:
        """그룹 면접 시작

        Args:
            room_id: 방 ID
            airline: 항공사명
            question_count: 질문 개수 (기본 5개)

        Returns:
            면접 세션 정보
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        if room["status"] != RoomStatus.IN_PROGRESS:
            raise ValueError("방이 진행 상태가 아닙니다. 먼저 세션을 시작하세요.")

        # 질문 생성
        questions = get_airline_questions(airline, question_count)

        # 방에 질문 설정
        set_questions(room_id, questions)

        # 세션 생성
        session = InterviewSession(
            room_id=room_id,
            airline=airline,
            question_count=question_count,
            questions=questions
        )

        self._interview_sessions[room_id] = session

        # 라이브 스코어 초기화
        self._live_scores[room_id] = {}
        for p in room["participants"]:
            self._live_scores[room_id][p["user_id"]] = {
                "content": 0.0,
                "structure": 0.0,
                "delivery": 0.0,
                "relevance": 0.0,
                "total": 0.0
            }

        logger.info(f"그룹 면접 시작: {room_id}, 항공사: {airline}, 질문 수: {question_count}")

        return {
            "room_id": room_id,
            "airline": airline,
            "questions": questions,
            "question_count": question_count,
            "participants": [p["user_name"] for p in room["participants"]],
            "started_at": session.started_at,
            "airline_values": get_airline_values(airline)
        }

    def get_interview_progress(self, room_id: str) -> Dict[str, Any]:
        """면접 진행 상황 조회

        Args:
            room_id: 방 ID

        Returns:
            진행 상황 정보
        """
        session = self._interview_sessions.get(room_id)
        if not session:
            raise ValueError(f"진행 중인 면접 세션이 없습니다: {room_id}")

        room = get_room(room_id)
        state = room.get("state", {}) if room else {}

        # 경과 시간 계산
        started = datetime.fromisoformat(session.started_at)
        elapsed = datetime.now() - started
        elapsed_seconds = int(elapsed.total_seconds())

        # 질문별 답변 완료 현황
        questions_answered = []
        for i, q in enumerate(session.questions):
            answers = get_all_answers(room_id, i)
            questions_answered.append({
                "question_idx": i,
                "question": q,
                "answered_count": len(answers),
                "total_participants": len(room["participants"]) if room else 0
            })

        return {
            "room_id": room_id,
            "airline": session.airline,
            "current_question_idx": state.get("current_question_idx", 0),
            "total_questions": len(session.questions),
            "elapsed_time": elapsed_seconds,
            "elapsed_time_formatted": f"{elapsed_seconds // 60}분 {elapsed_seconds % 60}초",
            "questions_answered": questions_answered,
            "current_speaker": state.get("current_speaker_id"),
            "phase": state.get("phase", "questioning"),
            "completed": session.completed
        }

    def evaluate_group_interview(self, room_id: str) -> Dict[str, Any]:
        """그룹 면접 평가 생성

        Args:
            room_id: 방 ID

        Returns:
            전체 참가자 평가 결과
        """
        session = self._interview_sessions.get(room_id)
        if not session:
            raise ValueError(f"진행 중인 면접 세션이 없습니다: {room_id}")

        room = get_room(room_id)
        if not room:
            raise ValueError(f"방을 찾을 수 없습니다: {room_id}")

        evaluations = {}

        # 각 참가자별 평가
        for participant in room["participants"]:
            user_id = participant["user_id"]
            user_name = participant["user_name"]

            user_answers = []
            total_score = 0

            # 각 질문에 대한 답변 수집
            for q_idx, question in enumerate(session.questions):
                answers = get_all_answers(room_id, q_idx)
                user_answer = next((a for a in answers if a["user_id"] == user_id), None)

                if user_answer:
                    # AI 평가 호출 (voice_utils의 evaluate_answer_content 사용)
                    try:
                        from voice_utils import evaluate_answer_content
                        evaluation = evaluate_answer_content(
                            question=question,
                            answer_text=user_answer.get("answer_text", ""),
                            airline=session.airline
                        )
                        score = evaluation.get("total_score", 0)
                    except Exception as e:
                        logger.warning(f"답변 평가 실패: {e}")
                        score = 50  # 기본 점수
                        evaluation = {"error": str(e)}

                    user_answers.append({
                        "question_idx": q_idx,
                        "question": question,
                        "answer": user_answer.get("answer_text", ""),
                        "score": score,
                        "evaluation": evaluation
                    })
                    total_score += score

            # 평균 점수 계산
            avg_score = total_score / len(session.questions) if session.questions else 0

            evaluations[user_id] = {
                "user_id": user_id,
                "user_name": user_name,
                "answers": user_answers,
                "total_score": total_score,
                "average_score": round(avg_score, 1),
                "questions_answered": len(user_answers),
                "total_questions": len(session.questions)
            }

        session.completed = True

        logger.info(f"그룹 면접 평가 완료: {room_id}")

        return {
            "room_id": room_id,
            "airline": session.airline,
            "evaluations": evaluations,
            "completed_at": datetime.now().isoformat()
        }

    def get_rankings(self, room_id: str) -> List[Dict[str, Any]]:
        """참가자 순위 조회

        Args:
            room_id: 방 ID

        Returns:
            순위 목록
        """
        live_scores = self._live_scores.get(room_id, {})

        if not live_scores:
            # 라이브 스코어가 없으면 저장된 답변 기반으로 계산
            room = get_room(room_id)
            if not room:
                return []

            rankings = []
            for p in room["participants"]:
                user_id = p["user_id"]
                total = 0
                count = 0

                for answer in room.get("answers", []):
                    if answer["user_id"] == user_id:
                        # 답변이 있으면 기본 점수 부여
                        total += 50  # 기본 점수
                        count += 1

                avg = total / count if count > 0 else 0
                rankings.append({
                    "user_id": user_id,
                    "user_name": p["user_name"],
                    "total_score": total,
                    "average_score": round(avg, 1),
                    "answers_count": count
                })
        else:
            room = get_room(room_id)
            rankings = []

            for user_id, scores in live_scores.items():
                participant = next(
                    (p for p in room["participants"] if p["user_id"] == user_id),
                    None
                ) if room else None

                rankings.append({
                    "user_id": user_id,
                    "user_name": participant["user_name"] if participant else user_id,
                    "total_score": scores.get("total", 0),
                    "content_score": scores.get("content", 0),
                    "structure_score": scores.get("structure", 0),
                    "delivery_score": scores.get("delivery", 0),
                    "relevance_score": scores.get("relevance", 0)
                })

        # 총점 기준 정렬
        rankings.sort(key=lambda x: x["total_score"], reverse=True)

        # 순위 부여
        for i, r in enumerate(rankings):
            r["rank"] = i + 1

        return rankings

    # ========================================
    # 2. 턴 관리
    # ========================================

    def get_current_turn_info(self, room_id: str) -> Dict[str, Any]:
        """현재 턴 정보 조회

        Args:
            room_id: 방 ID

        Returns:
            현재 턴 정보
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        state = room.get("state", {})
        timer = self._timers.get(room_id, {})

        # 현재 발언자 정보
        current_speaker_id = state.get("current_speaker_id")
        current_speaker = next(
            (p for p in room["participants"] if p["user_id"] == current_speaker_id),
            None
        )

        # 남은 시간 계산
        remaining_seconds = None
        if timer and timer.get("end_time"):
            end_time = datetime.fromisoformat(timer["end_time"])
            remaining = end_time - datetime.now()
            remaining_seconds = max(0, int(remaining.total_seconds()))

        # 현재 질문
        current_question = get_current_question(room_id)

        return {
            "room_id": room_id,
            "current_speaker_id": current_speaker_id,
            "current_speaker_name": current_speaker["user_name"] if current_speaker else None,
            "current_question": current_question,
            "current_question_idx": state.get("current_question_idx", 0),
            "turn_order": state.get("turn_order", []),
            "current_turn_idx": state.get("current_turn_idx", 0),
            "round_number": state.get("round_number", 1),
            "remaining_seconds": remaining_seconds,
            "timer_active": timer.get("active", False)
        }

    def start_answer_timer(
        self,
        room_id: str,
        user_id: str,
        duration: int = 120
    ) -> Dict[str, Any]:
        """답변 타이머 시작

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            duration: 시간 제한 (초)

        Returns:
            타이머 정보
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration)

        self._timers[room_id] = {
            "user_id": user_id,
            "duration": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "active": True
        }

        logger.debug(f"타이머 시작: {room_id}, 사용자: {user_id}, 시간: {duration}초")

        return {
            "room_id": room_id,
            "user_id": user_id,
            "duration": duration,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }

    def check_timer(self, room_id: str) -> Dict[str, Any]:
        """타이머 확인

        Args:
            room_id: 방 ID

        Returns:
            타이머 상태
        """
        timer = self._timers.get(room_id)
        if not timer:
            return {"active": False, "message": "타이머가 없습니다."}

        if not timer.get("active"):
            return {"active": False, "message": "타이머가 비활성 상태입니다."}

        end_time = datetime.fromisoformat(timer["end_time"])
        now = datetime.now()

        if now >= end_time:
            timer["active"] = False
            return {
                "active": False,
                "time_up": True,
                "message": "시간이 종료되었습니다!",
                "user_id": timer["user_id"]
            }

        remaining = end_time - now
        return {
            "active": True,
            "time_up": False,
            "remaining_seconds": int(remaining.total_seconds()),
            "user_id": timer["user_id"]
        }

    def skip_turn(self, room_id: str, user_id: str) -> Dict[str, Any]:
        """현재 턴 건너뛰기

        Args:
            room_id: 방 ID
            user_id: 건너뛸 사용자 ID

        Returns:
            다음 턴 정보
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        state = room.get("state", {})

        # 현재 발언자 확인
        if state.get("current_speaker_id") != user_id:
            raise ValueError("현재 발언자만 턴을 건너뛸 수 있습니다.")

        # 타이머 중지
        if room_id in self._timers:
            self._timers[room_id]["active"] = False

        # 다음 턴으로 이동
        new_state = next_turn(room_id)

        logger.info(f"턴 건너뛰기: {room_id}, 사용자: {user_id}")

        return {
            "room_id": room_id,
            "skipped_user_id": user_id,
            "new_speaker_id": new_state.get("current_speaker_id"),
            "round_number": new_state.get("round_number", 1)
        }

    # ========================================
    # 3. 실시간 점수 추적
    # ========================================

    def update_live_score(
        self,
        room_id: str,
        user_id: str,
        score: float,
        category: str
    ) -> Dict[str, Any]:
        """실시간 점수 업데이트

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            score: 점수
            category: 카테고리 (content, structure, delivery, relevance)

        Returns:
            업데이트된 점수 정보
        """
        valid_categories = ["content", "structure", "delivery", "relevance"]
        if category not in valid_categories:
            raise ValueError(f"유효하지 않은 카테고리입니다: {category}")

        if room_id not in self._live_scores:
            self._live_scores[room_id] = {}

        if user_id not in self._live_scores[room_id]:
            self._live_scores[room_id][user_id] = {
                "content": 0.0,
                "structure": 0.0,
                "delivery": 0.0,
                "relevance": 0.0,
                "total": 0.0
            }

        # 점수 누적
        self._live_scores[room_id][user_id][category] += score

        # 총점 재계산
        scores = self._live_scores[room_id][user_id]
        scores["total"] = (
            scores["content"] +
            scores["structure"] +
            scores["delivery"] +
            scores["relevance"]
        )

        logger.debug(f"점수 업데이트: {room_id}/{user_id}, {category}: +{score}")

        return {
            "room_id": room_id,
            "user_id": user_id,
            "category": category,
            "added_score": score,
            "current_scores": scores
        }

    def get_live_leaderboard(self, room_id: str) -> List[Dict[str, Any]]:
        """실시간 리더보드 조회

        Args:
            room_id: 방 ID

        Returns:
            리더보드
        """
        return self.get_rankings(room_id)

    def get_score_comparison(self, room_id: str) -> Dict[str, Any]:
        """점수 비교 조회

        Args:
            room_id: 방 ID

        Returns:
            참가자 점수 비교 데이터
        """
        live_scores = self._live_scores.get(room_id, {})
        room = get_room(room_id)

        if not room or not live_scores:
            return {"message": "비교할 점수가 없습니다."}

        comparison = {
            "room_id": room_id,
            "participants": [],
            "categories": ["content", "structure", "delivery", "relevance"],
            "max_scores": {"content": 0, "structure": 0, "delivery": 0, "relevance": 0, "total": 0}
        }

        for user_id, scores in live_scores.items():
            participant = next(
                (p for p in room["participants"] if p["user_id"] == user_id),
                None
            )

            comparison["participants"].append({
                "user_id": user_id,
                "user_name": participant["user_name"] if participant else user_id,
                "scores": scores
            })

            # 최고 점수 업데이트
            for cat in comparison["categories"]:
                if scores.get(cat, 0) > comparison["max_scores"][cat]:
                    comparison["max_scores"][cat] = scores[cat]

            if scores.get("total", 0) > comparison["max_scores"]["total"]:
                comparison["max_scores"]["total"] = scores["total"]

        return comparison

    # ========================================
    # 4. 토론 모드
    # ========================================

    def start_debate(
        self,
        room_id: str,
        topic: str,
        positions: Dict[str, str]
    ) -> Dict[str, Any]:
        """토론 시작

        Args:
            room_id: 방 ID
            topic: 토론 주제 (topic_id 또는 주제 텍스트)
            positions: 참가자별 포지션 {user_id: "pro" or "con"}

        Returns:
            토론 상태
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        # 주제 찾기
        topic_data = None
        for t in DEBATE_TOPICS:
            if t["id"] == topic or t["topic"] == topic:
                topic_data = t
                break

        if not topic_data:
            # 사용자 정의 주제
            topic_data = {
                "id": "custom",
                "topic": topic,
                "description": "사용자 정의 토론 주제",
                "pro_points": [],
                "con_points": []
            }

        # 포지션 검증
        for user_id, pos in positions.items():
            if pos not in ["pro", "con"]:
                raise ValueError(f"유효하지 않은 포지션입니다: {pos}")

        # 턴 순서 설정 (찬성/반대 번갈아)
        pro_users = [uid for uid, pos in positions.items() if pos == "pro"]
        con_users = [uid for uid, pos in positions.items() if pos == "con"]

        turn_order = []
        max_len = max(len(pro_users), len(con_users))
        for i in range(max_len):
            if i < len(pro_users):
                turn_order.append(pro_users[i])
            if i < len(con_users):
                turn_order.append(con_users[i])

        # 토론 상태 생성
        debate_state = DebateState(
            topic=topic_data,
            positions=positions,
            turn_order=turn_order,
            current_speaker_id=turn_order[0] if turn_order else None
        )

        self._debate_states[room_id] = debate_state

        logger.info(f"토론 시작: {room_id}, 주제: {topic_data['topic']}")

        return {
            "room_id": room_id,
            "topic": topic_data,
            "positions": positions,
            "turn_order": turn_order,
            "phase": debate_state.phase,
            "current_speaker_id": debate_state.current_speaker_id,
            "started_at": debate_state.started_at
        }

    def get_debate_state(self, room_id: str) -> Dict[str, Any]:
        """토론 상태 조회

        Args:
            room_id: 방 ID

        Returns:
            현재 토론 상태
        """
        debate = self._debate_states.get(room_id)
        if not debate:
            raise ValueError(f"진행 중인 토론이 없습니다: {room_id}")

        room = get_room(room_id)

        # 현재 발언자 정보
        current_speaker = None
        if room and debate.current_speaker_id:
            current_speaker = next(
                (p for p in room["participants"] if p["user_id"] == debate.current_speaker_id),
                None
            )

        return {
            "room_id": room_id,
            "topic": debate.topic,
            "phase": debate.phase,
            "positions": debate.positions,
            "current_speaker_id": debate.current_speaker_id,
            "current_speaker_name": current_speaker["user_name"] if current_speaker else None,
            "current_speaker_position": debate.positions.get(debate.current_speaker_id),
            "turn_order": debate.turn_order,
            "current_turn_idx": debate.current_turn_idx,
            "rebuttal_round": debate.rebuttal_round,
            "arguments_count": len(debate.arguments),
            "rebuttals_count": len(debate.rebuttals),
            "started_at": debate.started_at
        }

    def submit_argument(
        self,
        room_id: str,
        user_id: str,
        argument: str
    ) -> Dict[str, Any]:
        """주장 제출

        Args:
            room_id: 방 ID
            user_id: 사용자 ID
            argument: 주장 내용

        Returns:
            제출된 주장 정보
        """
        debate = self._debate_states.get(room_id)
        if not debate:
            raise ValueError(f"진행 중인 토론이 없습니다: {room_id}")

        if debate.current_speaker_id != user_id:
            raise ValueError("현재 발언자만 주장을 제출할 수 있습니다.")

        position = debate.positions.get(user_id)

        argument_data = {
            "user_id": user_id,
            "position": position,
            "argument": argument,
            "phase": debate.phase,
            "submitted_at": datetime.now().isoformat()
        }

        if debate.phase == DebatePhase.REBUTTAL:
            debate.rebuttals.append(argument_data)
        else:
            debate.arguments.append(argument_data)

        # 다음 발언자로 이동
        debate.current_turn_idx = (debate.current_turn_idx + 1) % len(debate.turn_order)
        debate.current_speaker_id = debate.turn_order[debate.current_turn_idx]

        # 한 바퀴 돌면 다음 단계로
        if debate.current_turn_idx == 0:
            if debate.phase == DebatePhase.OPENING:
                debate.phase = DebatePhase.ARGUMENT
            elif debate.phase == DebatePhase.ARGUMENT:
                debate.phase = DebatePhase.REBUTTAL
                debate.rebuttal_round = 1
            elif debate.phase == DebatePhase.REBUTTAL:
                if debate.rebuttal_round < debate.max_rebuttal_rounds:
                    debate.rebuttal_round += 1
                else:
                    debate.phase = DebatePhase.CLOSING
            elif debate.phase == DebatePhase.CLOSING:
                debate.phase = DebatePhase.EVALUATION

        logger.info(f"주장 제출: {room_id}, 사용자: {user_id}, 단계: {debate.phase}")

        return {
            "room_id": room_id,
            "argument": argument_data,
            "next_speaker_id": debate.current_speaker_id,
            "current_phase": debate.phase,
            "turn_idx": debate.current_turn_idx
        }

    def start_rebuttal_round(self, room_id: str) -> Dict[str, Any]:
        """반론 라운드 시작

        Args:
            room_id: 방 ID

        Returns:
            반론 라운드 정보
        """
        debate = self._debate_states.get(room_id)
        if not debate:
            raise ValueError(f"진행 중인 토론이 없습니다: {room_id}")

        debate.phase = DebatePhase.REBUTTAL
        debate.rebuttal_round += 1
        debate.current_turn_idx = 0
        debate.current_speaker_id = debate.turn_order[0] if debate.turn_order else None

        logger.info(f"반론 라운드 시작: {room_id}, 라운드: {debate.rebuttal_round}")

        return {
            "room_id": room_id,
            "phase": debate.phase,
            "rebuttal_round": debate.rebuttal_round,
            "current_speaker_id": debate.current_speaker_id
        }

    def evaluate_debate(self, room_id: str) -> Dict[str, Any]:
        """토론 평가

        Args:
            room_id: 방 ID

        Returns:
            토론 평가 결과
        """
        debate = self._debate_states.get(room_id)
        if not debate:
            raise ValueError(f"진행 중인 토론이 없습니다: {room_id}")

        room = get_room(room_id)

        # 각 참가자별 점수 계산
        scores = {}

        for user_id, position in debate.positions.items():
            participant = next(
                (p for p in room["participants"] if p["user_id"] == user_id),
                None
            ) if room else None

            # 주장 수
            argument_count = sum(
                1 for a in debate.arguments
                if a["user_id"] == user_id
            )

            # 반론 수
            rebuttal_count = sum(
                1 for r in debate.rebuttals
                if r["user_id"] == user_id
            )

            # 간단한 점수 계산 (실제로는 AI 평가 추가 가능)
            base_score = 50
            argument_score = argument_count * 15
            rebuttal_score = rebuttal_count * 10
            total_score = min(100, base_score + argument_score + rebuttal_score)

            scores[user_id] = {
                "user_id": user_id,
                "user_name": participant["user_name"] if participant else user_id,
                "position": position,
                "argument_count": argument_count,
                "rebuttal_count": rebuttal_count,
                "total_score": total_score,
                "feedback": self._generate_debate_feedback(
                    argument_count, rebuttal_count, position
                )
            }

        # 팀별 점수
        pro_total = sum(s["total_score"] for s in scores.values() if s["position"] == "pro")
        con_total = sum(s["total_score"] for s in scores.values() if s["position"] == "con")

        # 승자 결정
        if pro_total > con_total:
            winner = "pro"
            winner_label = "찬성팀"
        elif con_total > pro_total:
            winner = "con"
            winner_label = "반대팀"
        else:
            winner = "draw"
            winner_label = "무승부"

        debate.scores = scores
        debate.phase = DebatePhase.EVALUATION

        logger.info(f"토론 평가 완료: {room_id}, 승자: {winner_label}")

        return {
            "room_id": room_id,
            "topic": debate.topic["topic"],
            "winner": winner,
            "winner_label": winner_label,
            "pro_total_score": pro_total,
            "con_total_score": con_total,
            "individual_scores": scores,
            "arguments_summary": {
                "total": len(debate.arguments),
                "pro": sum(1 for a in debate.arguments if a["position"] == "pro"),
                "con": sum(1 for a in debate.arguments if a["position"] == "con")
            },
            "rebuttals_summary": {
                "total": len(debate.rebuttals),
                "rounds": debate.rebuttal_round
            },
            "evaluated_at": datetime.now().isoformat()
        }

    def _generate_debate_feedback(
        self,
        argument_count: int,
        rebuttal_count: int,
        position: str
    ) -> str:
        """토론 피드백 생성"""
        feedback_parts = []

        if argument_count >= 2:
            feedback_parts.append("주장을 충실히 전달했습니다.")
        elif argument_count == 1:
            feedback_parts.append("주장을 더 적극적으로 펼치면 좋겠습니다.")
        else:
            feedback_parts.append("주장 기회를 놓쳤습니다. 적극적인 참여가 필요합니다.")

        if rebuttal_count >= 2:
            feedback_parts.append("반론에도 적극적으로 참여했습니다.")
        elif rebuttal_count == 1:
            feedback_parts.append("반론 참여가 조금 부족했습니다.")
        else:
            feedback_parts.append("반론 기회를 더 활용해보세요.")

        return " ".join(feedback_parts)

    # ========================================
    # 5. 관전자 모드
    # ========================================

    def get_spectator_view(self, room_id: str) -> Dict[str, Any]:
        """관전자 뷰 데이터 조회

        Args:
            room_id: 방 ID

        Returns:
            관전자용 데이터
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        spectators = self._spectators.get(room_id, [])
        comments = self._spectator_comments.get(room_id, [])

        # 현재 상태
        state = room.get("state", {})

        # 진행 중인 세션 정보
        session = self._interview_sessions.get(room_id)
        debate = self._debate_states.get(room_id)

        view_data = {
            "room_id": room_id,
            "room_name": room["room_name"],
            "room_type": room["room_type"],
            "status": room["status"],
            "participants": [
                {
                    "user_id": p["user_id"],
                    "user_name": p["user_name"],
                    "status": p["status"]
                }
                for p in room["participants"]
            ],
            "spectator_count": len(spectators),
            "recent_comments": comments[-10:] if comments else [],  # 최근 10개 댓글
            "current_speaker_id": state.get("current_speaker_id"),
            "phase": state.get("phase", "waiting")
        }

        # 면접 세션 정보 추가
        if session:
            view_data["interview"] = {
                "airline": session.airline,
                "current_question": get_current_question(room_id),
                "question_idx": state.get("current_question_idx", 0),
                "total_questions": len(session.questions)
            }

        # 토론 정보 추가
        if debate:
            view_data["debate"] = {
                "topic": debate.topic["topic"],
                "phase": debate.phase,
                "positions": debate.positions,
                "arguments_count": len(debate.arguments)
            }

        # 실시간 리더보드
        live_scores = self._live_scores.get(room_id)
        if live_scores:
            view_data["leaderboard"] = self.get_rankings(room_id)[:3]  # 상위 3명

        return view_data

    def add_spectator(self, room_id: str, user_id: str) -> Dict[str, Any]:
        """관전자 추가

        Args:
            room_id: 방 ID
            user_id: 관전자 ID

        Returns:
            관전자 정보
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        # 참가자가 아닌지 확인
        if any(p["user_id"] == user_id for p in room["participants"]):
            raise ValueError("참가자는 관전자가 될 수 없습니다.")

        if room_id not in self._spectators:
            self._spectators[room_id] = []

        if user_id not in self._spectators[room_id]:
            self._spectators[room_id].append(user_id)

        logger.info(f"관전자 추가: {room_id}, 사용자: {user_id}")

        return {
            "room_id": room_id,
            "user_id": user_id,
            "spectator_count": len(self._spectators[room_id])
        }

    def remove_spectator(self, room_id: str, user_id: str) -> bool:
        """관전자 제거

        Args:
            room_id: 방 ID
            user_id: 관전자 ID

        Returns:
            성공 여부
        """
        if room_id not in self._spectators:
            return False

        if user_id in self._spectators[room_id]:
            self._spectators[room_id].remove(user_id)
            logger.info(f"관전자 제거: {room_id}, 사용자: {user_id}")
            return True

        return False

    def spectator_comment(
        self,
        room_id: str,
        user_id: str,
        comment: str
    ) -> Dict[str, Any]:
        """관전자 댓글 추가

        Args:
            room_id: 방 ID
            user_id: 관전자 ID
            comment: 댓글 내용

        Returns:
            댓글 정보
        """
        # 관전자 확인
        if room_id not in self._spectators or user_id not in self._spectators[room_id]:
            raise ValueError("관전자만 댓글을 작성할 수 있습니다.")

        if room_id not in self._spectator_comments:
            self._spectator_comments[room_id] = []

        comment_data = {
            "user_id": user_id,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }

        self._spectator_comments[room_id].append(comment_data)

        # 최대 100개 유지
        if len(self._spectator_comments[room_id]) > 100:
            self._spectator_comments[room_id] = self._spectator_comments[room_id][-100:]

        logger.debug(f"관전자 댓글: {room_id}, 사용자: {user_id}")

        return comment_data

    # ========================================
    # 6. 매치 히스토리 & 결과
    # ========================================

    def save_match_result(self, room_id: str) -> Dict[str, Any]:
        """매치 결과 저장

        Args:
            room_id: 방 ID

        Returns:
            저장된 매치 결과
        """
        room = get_room(room_id)
        if not room:
            raise ValueError(f"존재하지 않는 방입니다: {room_id}")

        session = self._interview_sessions.get(room_id)
        debate = self._debate_states.get(room_id)

        match_id = str(uuid.uuid4())[:8]

        # 기본 매치 정보
        match_result = {
            "match_id": match_id,
            "room_id": room_id,
            "room_name": room["room_name"],
            "room_type": room["room_type"],
            "participants": [
                {
                    "user_id": p["user_id"],
                    "user_name": p["user_name"]
                }
                for p in room["participants"]
            ],
            "created_at": room["created_at"],
            "completed_at": datetime.now().isoformat()
        }

        # 면접 결과
        if session:
            rankings = self.get_rankings(room_id)
            match_result["interview"] = {
                "airline": session.airline,
                "question_count": session.question_count,
                "rankings": rankings,
                "winner_id": rankings[0]["user_id"] if rankings else None,
                "winner_name": rankings[0]["user_name"] if rankings else None
            }

        # 토론 결과
        if debate:
            match_result["debate"] = {
                "topic": debate.topic["topic"],
                "winner_position": None,  # evaluate_debate에서 설정
                "scores": debate.scores
            }

        # 히스토리에 저장
        history = self._load_match_history()
        history.append(match_result)

        # 최대 1000개 유지
        if len(history) > 1000:
            history = history[-1000:]

        self._save_match_history(history)

        logger.info(f"매치 결과 저장: {match_id}")

        return match_result

    def get_match_history(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 매치 히스토리 조회

        Args:
            user_id: 사용자 ID

        Returns:
            매치 히스토리
        """
        history = self._load_match_history()

        # 해당 사용자가 참가한 매치만 필터
        user_history = [
            m for m in history
            if any(p["user_id"] == user_id for p in m.get("participants", []))
        ]

        # 최신순 정렬
        user_history.sort(key=lambda x: x.get("completed_at", ""), reverse=True)

        return user_history

    def get_match_details(self, match_id: str) -> Optional[Dict[str, Any]]:
        """매치 상세 조회

        Args:
            match_id: 매치 ID

        Returns:
            매치 상세 정보
        """
        history = self._load_match_history()

        for match in history:
            if match.get("match_id") == match_id:
                return match

        return None

    def get_best_performances(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최고 성과 조회 (쇼케이스용)

        Args:
            limit: 조회 개수

        Returns:
            최고 성과 목록
        """
        history = self._load_match_history()

        # 면접 매치에서 고득점자 추출
        performances = []

        for match in history:
            interview = match.get("interview", {})
            rankings = interview.get("rankings", [])

            for rank in rankings:
                if rank.get("rank") == 1:  # 1위만
                    performances.append({
                        "match_id": match["match_id"],
                        "user_id": rank["user_id"],
                        "user_name": rank["user_name"],
                        "score": rank.get("total_score", 0),
                        "airline": interview.get("airline", ""),
                        "completed_at": match.get("completed_at", "")
                    })

        # 점수순 정렬
        performances.sort(key=lambda x: x["score"], reverse=True)

        return performances[:limit]

    # ========================================
    # 7. AI 통합 (그룹 면접용)
    # ========================================

    def generate_ai_questions(
        self,
        airline: str,
        count: int = 5
    ) -> List[str]:
        """AI 질문 생성

        Args:
            airline: 항공사명
            count: 질문 개수

        Returns:
            질문 목록
        """
        return get_airline_questions(airline, count)

    def evaluate_answer_with_ai(
        self,
        question: str,
        answer: str,
        airline: str
    ) -> Dict[str, Any]:
        """AI로 답변 평가

        Args:
            question: 질문
            answer: 답변
            airline: 항공사

        Returns:
            평가 결과
        """
        try:
            from voice_utils import evaluate_answer_content
            return evaluate_answer_content(
                question=question,
                answer_text=answer,
                airline=airline
            )
        except Exception as e:
            logger.error(f"AI 평가 실패: {e}")
            return {
                "error": str(e),
                "total_score": 50  # 기본 점수
            }

    def provide_ai_feedback(
        self,
        room_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """참가자에게 AI 피드백 제공

        Args:
            room_id: 방 ID
            user_id: 사용자 ID

        Returns:
            피드백
        """
        session = self._interview_sessions.get(room_id)
        if not session:
            return {"message": "면접 세션이 없습니다."}

        room = get_room(room_id)
        if not room:
            return {"message": "방을 찾을 수 없습니다."}

        # 사용자 답변 수집
        user_answers = []
        for q_idx, question in enumerate(session.questions):
            answers = get_all_answers(room_id, q_idx)
            user_answer = next((a for a in answers if a["user_id"] == user_id), None)
            if user_answer:
                user_answers.append({
                    "question": question,
                    "answer": user_answer.get("answer_text", "")
                })

        if not user_answers:
            return {"message": "답변 기록이 없습니다."}

        # 종합 피드백 생성
        strengths = []
        improvements = []

        for ua in user_answers:
            evaluation = self.evaluate_answer_with_ai(
                ua["question"], ua["answer"], session.airline
            )

            if "strengths" in evaluation:
                strengths.extend(evaluation["strengths"])
            if "improvements" in evaluation:
                improvements.extend(evaluation["improvements"])

        # 중복 제거
        strengths = list(set(strengths))[:5]
        improvements = list(set(improvements))[:5]

        return {
            "user_id": user_id,
            "airline": session.airline,
            "answers_evaluated": len(user_answers),
            "overall_strengths": strengths,
            "overall_improvements": improvements,
            "tip": f"{session.airline} 면접에서는 항공사의 핵심가치를 답변에 녹여내는 것이 중요합니다."
        }

    # ========================================
    # 8. 경쟁 기능
    # ========================================

    def calculate_winner(self, room_id: str) -> Dict[str, Any]:
        """우승자 결정

        Args:
            room_id: 방 ID

        Returns:
            우승자 정보
        """
        rankings = self.get_rankings(room_id)

        if not rankings:
            return {"message": "랭킹이 없습니다."}

        winner = rankings[0]

        return {
            "room_id": room_id,
            "winner_id": winner["user_id"],
            "winner_name": winner["user_name"],
            "winner_score": winner["total_score"],
            "rankings": rankings
        }

    def award_points(self, room_id: str) -> Dict[str, Any]:
        """경쟁 포인트 지급

        Args:
            room_id: 방 ID

        Returns:
            지급된 포인트 정보
        """
        rankings = self.get_rankings(room_id)

        if not rankings:
            return {"message": "랭킹이 없습니다."}

        scores = self._load_competition_scores()
        awarded = {}

        for rank in rankings:
            user_id = rank["user_id"]
            rank_num = rank["rank"]

            if user_id not in scores:
                scores[user_id] = {
                    "total_points": 0,
                    "wins": 0,
                    "matches": 0,
                    "streak": 0,
                    "best_streak": 0
                }

            # 포인트 결정
            if rank_num == 1:
                reward = REWARDS["winner"]
                scores[user_id]["wins"] += 1
                scores[user_id]["streak"] += 1
            elif rank_num == 2:
                reward = REWARDS["runner_up"]
                scores[user_id]["streak"] = 0
            elif rank_num == 3:
                reward = REWARDS["third_place"]
                scores[user_id]["streak"] = 0
            else:
                reward = REWARDS["participant"]
                scores[user_id]["streak"] = 0

            # 포인트 추가
            points = reward["points"]
            scores[user_id]["total_points"] += points
            scores[user_id]["matches"] += 1

            # 최고 연승 기록 업데이트
            if scores[user_id]["streak"] > scores[user_id]["best_streak"]:
                scores[user_id]["best_streak"] = scores[user_id]["streak"]

            # 연승 보너스
            if scores[user_id]["streak"] == 3:
                bonus = REWARDS["streak_3"]["points"]
                scores[user_id]["total_points"] += bonus
                points += bonus
            elif scores[user_id]["streak"] == 5:
                bonus = REWARDS["streak_5"]["points"]
                scores[user_id]["total_points"] += bonus
                points += bonus

            awarded[user_id] = {
                "user_name": rank["user_name"],
                "rank": rank_num,
                "points_awarded": points,
                "total_points": scores[user_id]["total_points"]
            }

        self._save_competition_scores(scores)

        logger.info(f"포인트 지급 완료: {room_id}")

        return {
            "room_id": room_id,
            "awarded": awarded
        }

    def get_weekly_competition_ranking(self) -> List[Dict[str, Any]]:
        """주간 경쟁 랭킹 조회

        Returns:
            주간 랭킹
        """
        scores = self._load_competition_scores()

        # 랭킹 생성
        rankings = []
        for user_id, data in scores.items():
            rankings.append({
                "user_id": user_id,
                "total_points": data.get("total_points", 0),
                "wins": data.get("wins", 0),
                "matches": data.get("matches", 0),
                "win_rate": round(
                    data.get("wins", 0) / max(data.get("matches", 1), 1) * 100, 1
                ),
                "best_streak": data.get("best_streak", 0)
            })

        # 포인트순 정렬
        rankings.sort(key=lambda x: x["total_points"], reverse=True)

        # 순위 부여
        for i, r in enumerate(rankings):
            r["rank"] = i + 1

        return rankings


# ========================================
# 싱글톤 인스턴스
# ========================================

_multiplayer_service: Optional[MultiplayerService] = None


def get_multiplayer_service() -> MultiplayerService:
    """MultiplayerService 싱글톤 인스턴스 반환"""
    global _multiplayer_service
    if _multiplayer_service is None:
        _multiplayer_service = MultiplayerService()
    return _multiplayer_service


# ========================================
# 편의 함수들 (모듈 레벨에서 직접 호출 가능)
# ========================================

# 그룹 면접
def start_group_interview(room_id: str, airline: str, question_count: int = 5) -> Dict[str, Any]:
    """그룹 면접 시작"""
    return get_multiplayer_service().start_group_interview(room_id, airline, question_count)


def get_interview_progress(room_id: str) -> Dict[str, Any]:
    """면접 진행 상황 조회"""
    return get_multiplayer_service().get_interview_progress(room_id)


def evaluate_group_interview(room_id: str) -> Dict[str, Any]:
    """그룹 면접 평가"""
    return get_multiplayer_service().evaluate_group_interview(room_id)


def get_rankings(room_id: str) -> List[Dict[str, Any]]:
    """랭킹 조회"""
    return get_multiplayer_service().get_rankings(room_id)


# 턴 관리
def get_current_turn_info(room_id: str) -> Dict[str, Any]:
    """현재 턴 정보"""
    return get_multiplayer_service().get_current_turn_info(room_id)


def start_answer_timer(room_id: str, user_id: str, duration: int = 120) -> Dict[str, Any]:
    """답변 타이머 시작"""
    return get_multiplayer_service().start_answer_timer(room_id, user_id, duration)


def check_timer(room_id: str) -> Dict[str, Any]:
    """타이머 확인"""
    return get_multiplayer_service().check_timer(room_id)


def skip_turn(room_id: str, user_id: str) -> Dict[str, Any]:
    """턴 건너뛰기"""
    return get_multiplayer_service().skip_turn(room_id, user_id)


# 실시간 점수
def update_live_score(room_id: str, user_id: str, score: float, category: str) -> Dict[str, Any]:
    """실시간 점수 업데이트"""
    return get_multiplayer_service().update_live_score(room_id, user_id, score, category)


def get_live_leaderboard(room_id: str) -> List[Dict[str, Any]]:
    """실시간 리더보드"""
    return get_multiplayer_service().get_live_leaderboard(room_id)


def get_score_comparison(room_id: str) -> Dict[str, Any]:
    """점수 비교"""
    return get_multiplayer_service().get_score_comparison(room_id)


# 토론
def start_debate(room_id: str, topic: str, positions: Dict[str, str]) -> Dict[str, Any]:
    """토론 시작"""
    return get_multiplayer_service().start_debate(room_id, topic, positions)


def get_debate_state(room_id: str) -> Dict[str, Any]:
    """토론 상태 조회"""
    return get_multiplayer_service().get_debate_state(room_id)


def submit_argument(room_id: str, user_id: str, argument: str) -> Dict[str, Any]:
    """주장 제출"""
    return get_multiplayer_service().submit_argument(room_id, user_id, argument)


def start_rebuttal_round(room_id: str) -> Dict[str, Any]:
    """반론 라운드 시작"""
    return get_multiplayer_service().start_rebuttal_round(room_id)


def evaluate_debate(room_id: str) -> Dict[str, Any]:
    """토론 평가"""
    return get_multiplayer_service().evaluate_debate(room_id)


# 관전자
def get_spectator_view(room_id: str) -> Dict[str, Any]:
    """관전자 뷰"""
    return get_multiplayer_service().get_spectator_view(room_id)


def add_spectator(room_id: str, user_id: str) -> Dict[str, Any]:
    """관전자 추가"""
    return get_multiplayer_service().add_spectator(room_id, user_id)


def remove_spectator(room_id: str, user_id: str) -> bool:
    """관전자 제거"""
    return get_multiplayer_service().remove_spectator(room_id, user_id)


def spectator_comment(room_id: str, user_id: str, comment: str) -> Dict[str, Any]:
    """관전자 댓글"""
    return get_multiplayer_service().spectator_comment(room_id, user_id, comment)


# 매치 히스토리
def save_match_result(room_id: str) -> Dict[str, Any]:
    """매치 결과 저장"""
    return get_multiplayer_service().save_match_result(room_id)


def get_match_history(user_id: str) -> List[Dict[str, Any]]:
    """매치 히스토리"""
    return get_multiplayer_service().get_match_history(user_id)


def get_match_details(match_id: str) -> Optional[Dict[str, Any]]:
    """매치 상세"""
    return get_multiplayer_service().get_match_details(match_id)


def get_best_performances(limit: int = 10) -> List[Dict[str, Any]]:
    """최고 성과"""
    return get_multiplayer_service().get_best_performances(limit)


# 경쟁
def calculate_winner(room_id: str) -> Dict[str, Any]:
    """우승자 결정"""
    return get_multiplayer_service().calculate_winner(room_id)


def award_points(room_id: str) -> Dict[str, Any]:
    """포인트 지급"""
    return get_multiplayer_service().award_points(room_id)


def get_weekly_competition_ranking() -> List[Dict[str, Any]]:
    """주간 랭킹"""
    return get_multiplayer_service().get_weekly_competition_ranking()
