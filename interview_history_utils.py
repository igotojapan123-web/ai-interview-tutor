# interview_history_utils.py
# 면접 히스토리 CRUD 유틸리티
# MongoDB 마이그레이션 대비 설계

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# 로깅 설정
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# 파일 경로
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORY_FILE = DATA_DIR / "interview_history.json"

# MongoDB 전환 플래그 (나중에 환경변수로 변경)
USE_MONGODB = os.environ.get("USE_MONGODB", "false").lower() == "true"
MONGO_URI = os.environ.get("MONGO_URI", "")


def _ensure_data_dir():
    """데이터 디렉토리 확인/생성"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_history() -> Dict:
    """히스토리 파일 로드"""
    _ensure_data_dir()

    if not HISTORY_FILE.exists():
        return {
            "_version": "1.0",
            "_created_at": datetime.now().isoformat(),
            "sessions": []
        }

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"히스토리 파일 로드 실패: {e}")
        return {"_version": "1.0", "sessions": []}


def _save_history(data: Dict) -> bool:
    """히스토리 파일 저장"""
    _ensure_data_dir()

    try:
        # 백업 생성 (기존 파일이 있으면)
        if HISTORY_FILE.exists():
            backup_file = DATA_DIR / "interview_history_backup.json"
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                backup_data = f.read()
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(backup_data)

        # 새 데이터 저장
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        logger.error(f"히스토리 파일 저장 실패: {e}")
        return False


# ============================================
# CRUD 함수들
# ============================================

def save_interview_session(session_data: Dict) -> Optional[str]:
    """
    면접 세션 저장

    Args:
        session_data: {
            "type": "모의면접",
            "airline": "대한항공",
            "mode": "voice",
            "question_count": 6,
            "questions": [...],
            "evaluation": {...},
            "scores": {...}
        }

    Returns:
        session_id (UUID) 또는 None (실패 시)
    """
    try:
        # 세션 ID 생성
        session_id = str(uuid.uuid4())

        # 타임스탬프 추가
        now = datetime.now()

        # 세션 데이터 구조화
        session = {
            "session_id": session_id,
            "created_at": now.isoformat(),
            "created_date": now.strftime("%Y-%m-%d"),
            "created_time": now.strftime("%H:%M"),
            "type": session_data.get("type", "모의면접"),
            "airline": session_data.get("airline", ""),
            "mode": session_data.get("mode", "text"),
            "question_count": session_data.get("question_count", 0),
            "total_duration_sec": session_data.get("total_duration_sec", 0),

            "scores": session_data.get("scores", {
                "total": 0,
                "voice_avg": 0,
                "content_avg": 0
            }),

            "questions": session_data.get("questions", []),
            "evaluation": session_data.get("evaluation", {}),

            "metadata": {
                "app_version": "1.0",
                "saved_at": now.isoformat()
            }
        }

        # 저장
        history = _load_history()
        history["sessions"].insert(0, session)  # 최신이 앞에 오도록

        # 최대 500개 세션 유지 (오래된 것 삭제)
        if len(history["sessions"]) > 500:
            history["sessions"] = history["sessions"][:500]

        if _save_history(history):
            logger.info(f"면접 세션 저장 완료: {session_id}")
            return session_id
        return None

    except Exception as e:
        logger.error(f"면접 세션 저장 실패: {e}")
        return None


def get_all_sessions(limit: int = 50, offset: int = 0) -> List[Dict]:
    """
    전체 세션 조회 (최신순)

    Args:
        limit: 가져올 개수
        offset: 시작 위치

    Returns:
        세션 리스트
    """
    history = _load_history()
    sessions = history.get("sessions", [])
    return sessions[offset:offset + limit]


def get_session_by_id(session_id: str) -> Optional[Dict]:
    """세션 ID로 조회"""
    history = _load_history()
    for session in history.get("sessions", []):
        if session.get("session_id") == session_id:
            return session
    return None


def get_sessions_by_airline(airline: str, limit: int = 20) -> List[Dict]:
    """항공사별 세션 조회"""
    history = _load_history()
    sessions = [
        s for s in history.get("sessions", [])
        if s.get("airline", "").lower() == airline.lower()
    ]
    return sessions[:limit]


def get_sessions_by_date(start_date: str, end_date: str) -> List[Dict]:
    """
    날짜 범위로 세션 조회

    Args:
        start_date: "2026-02-01"
        end_date: "2026-02-06"
    """
    history = _load_history()
    sessions = []

    for session in history.get("sessions", []):
        created_date = session.get("created_date", "")
        if start_date <= created_date <= end_date:
            sessions.append(session)

    return sessions


def get_sessions_by_type(session_type: str, limit: int = 20) -> List[Dict]:
    """
    유형별 세션 조회 (모의면접, 영어면접, 롤플레잉 등)
    """
    history = _load_history()
    sessions = [
        s for s in history.get("sessions", [])
        if s.get("type", "") == session_type
    ]
    return sessions[:limit]


def get_weak_questions(score_threshold: int = 60, limit: int = 20) -> List[Dict]:
    """
    약점 질문 조회 (낮은 점수)

    Args:
        score_threshold: 이 점수 미만인 질문 필터링
        limit: 최대 개수

    Returns:
        [
            {
                "session_id": "...",
                "session_date": "2026-02-06",
                "airline": "대한항공",
                "question_index": 2,
                "question_text": "팀워크 경험?",
                "answer_text": "...",
                "score": 45,
                "feedback": {...}
            }
        ]
    """
    history = _load_history()
    weak_questions = []

    for session in history.get("sessions", []):
        for q in session.get("questions", []):
            # 점수 추출 (content_analysis 또는 voice_analysis에서)
            content_score = q.get("content_analysis", {}).get("total_score", 100)
            voice_score = q.get("voice_analysis", {}).get("total_score", 100)
            avg_score = (content_score + voice_score) / 2 if voice_score else content_score

            if avg_score < score_threshold:
                weak_questions.append({
                    "session_id": session.get("session_id"),
                    "session_date": session.get("created_date"),
                    "session_type": session.get("type"),
                    "airline": session.get("airline"),
                    "question_index": q.get("index", 0),
                    "category": q.get("category", ""),
                    "question_text": q.get("question_text", ""),
                    "answer_text": q.get("answer_text", ""),
                    "score": round(avg_score, 1),
                    "content_score": content_score,
                    "voice_score": voice_score,
                    "feedback": q.get("feedback", {})
                })

    # 점수 낮은 순으로 정렬
    weak_questions.sort(key=lambda x: x["score"])
    return weak_questions[:limit]


def get_question_history(question_text: str, similarity_threshold: float = 0.7) -> List[Dict]:
    """
    비슷한 질문에 대한 히스토리 조회 (같은 질문 비교용)

    Args:
        question_text: 비교할 질문
        similarity_threshold: 유사도 임계값 (간단한 단어 매칭)

    Returns:
        비슷한 질문 리스트 (날짜순)
    """
    history = _load_history()
    similar_questions = []

    # 간단한 키워드 기반 매칭 (나중에 임베딩으로 개선 가능)
    keywords = set(question_text.replace("?", "").replace(".", "").split())

    for session in history.get("sessions", []):
        for q in session.get("questions", []):
            q_text = q.get("question_text", "")
            q_keywords = set(q_text.replace("?", "").replace(".", "").split())

            # 교집합 비율로 유사도 계산
            if keywords and q_keywords:
                intersection = keywords & q_keywords
                union = keywords | q_keywords
                similarity = len(intersection) / len(union)

                if similarity >= similarity_threshold:
                    content_score = q.get("content_analysis", {}).get("total_score", 0)
                    voice_score = q.get("voice_analysis", {}).get("total_score", 0)

                    similar_questions.append({
                        "session_id": session.get("session_id"),
                        "session_date": session.get("created_date"),
                        "airline": session.get("airline"),
                        "question_text": q_text,
                        "answer_text": q.get("answer_text", ""),
                        "score": round((content_score + voice_score) / 2 if voice_score else content_score, 1),
                        "feedback": q.get("feedback", {}),
                        "similarity": round(similarity, 2)
                    })

    # 날짜순 정렬 (최신 먼저)
    similar_questions.sort(key=lambda x: x["session_date"], reverse=True)
    return similar_questions


def get_category_stats() -> Dict[str, Dict]:
    """
    카테고리별 통계

    Returns:
        {
            "common": {"count": 10, "avg_score": 75.5},
            "experience": {"count": 8, "avg_score": 68.2},
            ...
        }
    """
    history = _load_history()
    category_data = {}

    for session in history.get("sessions", []):
        for q in session.get("questions", []):
            category = q.get("category", "unknown")
            content_score = q.get("content_analysis", {}).get("total_score", 0)

            if category not in category_data:
                category_data[category] = {"scores": [], "count": 0}

            category_data[category]["scores"].append(content_score)
            category_data[category]["count"] += 1

    # 평균 계산
    result = {}
    for cat, data in category_data.items():
        scores = data["scores"]
        result[cat] = {
            "count": data["count"],
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0
        }

    return result


def get_airline_stats() -> Dict[str, Dict]:
    """항공사별 통계"""
    history = _load_history()
    airline_data = {}

    for session in history.get("sessions", []):
        airline = session.get("airline", "unknown")
        total_score = session.get("scores", {}).get("total", 0)

        if airline not in airline_data:
            airline_data[airline] = {"scores": [], "count": 0}

        airline_data[airline]["scores"].append(total_score)
        airline_data[airline]["count"] += 1

    result = {}
    for airline, data in airline_data.items():
        scores = data["scores"]
        result[airline] = {
            "count": data["count"],
            "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "recent_score": scores[0] if scores else 0
        }

    return result


def get_recent_scores(days: int = 30, limit: int = 50) -> List[Dict]:
    """
    최근 N일간 점수 추이

    Returns:
        [{"date": "2026-02-06", "score": 75, "type": "모의면접", "airline": "대한항공"}, ...]
    """
    from datetime import timedelta

    history = _load_history()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    scores = []
    for session in history.get("sessions", []):
        created_date = session.get("created_date", "")
        if created_date >= cutoff_date:
            scores.append({
                "date": created_date,
                "time": session.get("created_time", ""),
                "score": session.get("scores", {}).get("total", 0),
                "type": session.get("type", ""),
                "airline": session.get("airline", ""),
                "session_id": session.get("session_id", "")
            })

    return scores[:limit]


def delete_session(session_id: str) -> bool:
    """세션 삭제"""
    history = _load_history()
    original_count = len(history.get("sessions", []))

    history["sessions"] = [
        s for s in history.get("sessions", [])
        if s.get("session_id") != session_id
    ]

    if len(history["sessions"]) < original_count:
        return _save_history(history)
    return False


def get_total_stats() -> Dict:
    """전체 통계 요약"""
    history = _load_history()
    sessions = history.get("sessions", [])

    if not sessions:
        return {
            "total_sessions": 0,
            "total_questions": 0,
            "avg_score": 0,
            "best_score": 0,
            "recent_trend": "none"
        }

    total_questions = sum(len(s.get("questions", [])) for s in sessions)
    all_scores = [s.get("scores", {}).get("total", 0) for s in sessions]

    # 최근 5개 vs 이전 5개 비교로 트렌드 계산
    recent_5 = all_scores[:5] if len(all_scores) >= 5 else all_scores
    prev_5 = all_scores[5:10] if len(all_scores) >= 10 else []

    if recent_5 and prev_5:
        recent_avg = sum(recent_5) / len(recent_5)
        prev_avg = sum(prev_5) / len(prev_5)
        if recent_avg > prev_avg + 5:
            trend = "up"
        elif recent_avg < prev_avg - 5:
            trend = "down"
        else:
            trend = "stable"
    else:
        trend = "none"

    return {
        "total_sessions": len(sessions),
        "total_questions": total_questions,
        "avg_score": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
        "best_score": max(all_scores) if all_scores else 0,
        "worst_score": min(all_scores) if all_scores else 0,
        "recent_trend": trend,
        "first_session_date": sessions[-1].get("created_date", "") if sessions else "",
        "last_session_date": sessions[0].get("created_date", "") if sessions else ""
    }


# ============================================
# 유틸리티 함수
# ============================================

def format_session_summary(session: Dict) -> str:
    """세션 요약 텍스트 생성"""
    return (
        f"{session.get('created_date', '')} {session.get('created_time', '')} | "
        f"{session.get('airline', '')} {session.get('type', '')} | "
        f"{session.get('question_count', 0)}문항 | "
        f"점수: {session.get('scores', {}).get('total', 0)}점"
    )


def get_practice_types() -> List[str]:
    """연습 유형 목록"""
    return ["모의면접", "영어면접", "롤플레잉", "토론면접", "그룹면접", "실전연습"]


# ============================================
# MongoDB 전환용 (미래 대비)
# ============================================

if USE_MONGODB and MONGO_URI:
    try:
        from pymongo import MongoClient

        _mongo_client = MongoClient(MONGO_URI)
        _db = _mongo_client.flyready
        _collection = _db.interview_sessions

        logger.info("MongoDB 연결 성공")

        # MongoDB 사용 시 함수 오버라이드
        # (실제 구현은 나중에)

    except ImportError:
        logger.warning("pymongo 패키지가 설치되지 않음 - JSON 파일 사용")
    except Exception as e:
        logger.error(f"MongoDB 연결 실패: {e} - JSON 파일 사용")
