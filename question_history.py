# question_history.py
# 질문 중복 방지 시스템 - 사용자가 같은 질문을 반복해서 받지 않도록 관리

import os
import json
import hashlib
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Any
from logging_config import get_logger

logger = get_logger(__name__)

# 히스토리 파일 경로
HISTORY_DIR = os.path.join(os.path.dirname(__file__), "data")
HISTORY_FILE = os.path.join(HISTORY_DIR, "question_history.json")

# 스레드 안전을 위한 파일 잠금
_file_lock = threading.Lock()

# 히스토리 만료 기간 (일) - 이 기간이 지나면 같은 질문 다시 가능
HISTORY_EXPIRY_DAYS = 7


def _ensure_dir():
    """데이터 디렉토리 생성"""
    os.makedirs(HISTORY_DIR, exist_ok=True)


def _get_question_hash(question: str) -> str:
    """질문의 해시값 생성 (중복 체크용)"""
    normalized = question.strip().lower()
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def _load_history() -> Dict[str, Any]:
    """히스토리 로드 (스레드 안전)"""
    _ensure_dir()
    with _file_lock:
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"히스토리 로드 실패: {e}")
        return {
            "mock_interview": {},      # 모의면접 질문 히스토리
            "roleplay": {},            # 롤플레잉 시나리오 히스토리
            "english_interview": {},   # 영어면접 질문 히스토리
            "last_cleanup": datetime.now().isoformat()
        }


def _save_history(history: Dict[str, Any]):
    """히스토리 저장 (스레드 안전)"""
    _ensure_dir()
    with _file_lock:
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"히스토리 저장 실패: {e}")


def _cleanup_old_entries(history: Dict[str, Any]) -> Dict[str, Any]:
    """만료된 히스토리 엔트리 정리"""
    cutoff = (datetime.now() - timedelta(days=HISTORY_EXPIRY_DAYS)).isoformat()

    for category in ["mock_interview", "roleplay", "english_interview"]:
        if category not in history:
            history[category] = {}
            continue

        # 항공사/카테고리별로 정리
        for key in list(history[category].keys()):
            entries = history[category][key]
            if isinstance(entries, dict):
                # 만료된 항목 제거
                history[category][key] = {
                    q_hash: timestamp
                    for q_hash, timestamp in entries.items()
                    if timestamp > cutoff
                }
                # 비어있으면 키 제거
                if not history[category][key]:
                    del history[category][key]

    history["last_cleanup"] = datetime.now().isoformat()
    return history


def get_asked_questions(category: str, sub_key: str = "default") -> Set[str]:
    """
    이미 질문한 질문들의 해시값 집합 반환

    Args:
        category: "mock_interview", "roleplay", "english_interview"
        sub_key: 항공사명 또는 카테고리명

    Returns:
        이미 질문한 질문들의 해시값 집합
    """
    history = _load_history()

    # 정리 주기 체크 (하루에 한 번)
    last_cleanup = history.get("last_cleanup", "")
    if not last_cleanup or last_cleanup < (datetime.now() - timedelta(days=1)).isoformat():
        history = _cleanup_old_entries(history)
        _save_history(history)

    cat_history = history.get(category, {})
    sub_history = cat_history.get(sub_key, {})

    return set(sub_history.keys())


def mark_question_asked(
    question: str,
    category: str,
    sub_key: str = "default"
):
    """
    질문을 '이미 물어봄'으로 표시

    Args:
        question: 질문 텍스트
        category: "mock_interview", "roleplay", "english_interview"
        sub_key: 항공사명 또는 카테고리명
    """
    history = _load_history()

    if category not in history:
        history[category] = {}
    if sub_key not in history[category]:
        history[category][sub_key] = {}

    q_hash = _get_question_hash(question)
    history[category][sub_key][q_hash] = datetime.now().isoformat()

    _save_history(history)


def mark_questions_asked(
    questions: List[str],
    category: str,
    sub_key: str = "default"
):
    """여러 질문을 한 번에 '이미 물어봄'으로 표시"""
    history = _load_history()

    if category not in history:
        history[category] = {}
    if sub_key not in history[category]:
        history[category][sub_key] = {}

    now = datetime.now().isoformat()
    for question in questions:
        q_hash = _get_question_hash(question)
        history[category][sub_key][q_hash] = now

    _save_history(history)


def filter_new_questions(
    questions: List[Any],
    category: str,
    sub_key: str = "default",
    question_field: str = "question"
) -> List[Any]:
    """
    이미 질문한 것을 제외한 새 질문만 반환

    Args:
        questions: 질문 리스트 (문자열 또는 딕셔너리)
        category: 카테고리
        sub_key: 서브키
        question_field: 딕셔너리인 경우 질문 텍스트가 있는 필드명

    Returns:
        새 질문만 포함된 리스트
    """
    asked = get_asked_questions(category, sub_key)

    new_questions = []
    for q in questions:
        if isinstance(q, str):
            q_text = q
        elif isinstance(q, dict):
            q_text = q.get(question_field, "")
        else:
            continue

        if _get_question_hash(q_text) not in asked:
            new_questions.append(q)

    return new_questions


def get_history_stats(category: str = None) -> Dict[str, Any]:
    """히스토리 통계 반환"""
    history = _load_history()

    stats = {}
    categories = [category] if category else ["mock_interview", "roleplay", "english_interview"]

    for cat in categories:
        cat_history = history.get(cat, {})
        total = sum(len(v) for v in cat_history.values() if isinstance(v, dict))
        stats[cat] = {
            "total_asked": total,
            "sub_keys": list(cat_history.keys()),
            "by_sub_key": {k: len(v) for k, v in cat_history.items() if isinstance(v, dict)}
        }

    return stats


def reset_history(category: str = None, sub_key: str = None):
    """
    히스토리 리셋

    Args:
        category: 특정 카테고리만 리셋 (None이면 전체)
        sub_key: 특정 서브키만 리셋 (None이면 카테고리 전체)
    """
    history = _load_history()

    if category is None:
        # 전체 리셋
        history = {
            "mock_interview": {},
            "roleplay": {},
            "english_interview": {},
            "last_cleanup": datetime.now().isoformat()
        }
    elif sub_key is None:
        # 카테고리 전체 리셋
        history[category] = {}
    else:
        # 특정 서브키만 리셋
        if category in history and sub_key in history[category]:
            del history[category][sub_key]

    _save_history(history)
    logger.info(f"히스토리 리셋: category={category}, sub_key={sub_key}")


# ============================================
# 편의 함수: 각 기능별 중복 방지 래퍼
# ============================================

def get_fresh_mock_questions(
    all_questions: List[str],
    airline: str,
    count: int = 6
) -> List[str]:
    """
    모의면접용: 아직 안 나온 질문만 선택
    모든 질문이 소진되면 히스토리 리셋 후 다시 선택
    """
    import random

    # 새 질문만 필터링
    fresh = filter_new_questions(all_questions, "mock_interview", airline)

    # 새 질문이 요청 개수보다 적으면 히스토리 리셋
    if len(fresh) < count:
        logger.info(f"모의면접 질문 소진 - {airline} 히스토리 리셋")
        reset_history("mock_interview", airline)
        fresh = all_questions

    # 랜덤 선택
    selected = random.sample(fresh, min(count, len(fresh)))

    # 선택된 질문 기록
    mark_questions_asked(selected, "mock_interview", airline)

    return selected


def get_fresh_roleplay_scenarios(
    all_scenarios: List[Dict],
    category: str = "all",
    count: int = 1
) -> List[Dict]:
    """
    롤플레잉용: 아직 안 나온 시나리오만 선택
    """
    import random

    # 시나리오 ID 또는 title로 필터링
    fresh = filter_new_questions(
        all_scenarios,
        "roleplay",
        category,
        question_field="title"
    )

    # 새 시나리오가 부족하면 히스토리 리셋
    if len(fresh) < count:
        logger.info(f"롤플레잉 시나리오 소진 - {category} 히스토리 리셋")
        reset_history("roleplay", category)
        fresh = all_scenarios

    # 랜덤 선택
    selected = random.sample(fresh, min(count, len(fresh)))

    # 선택된 시나리오 기록
    for scenario in selected:
        mark_question_asked(scenario.get("title", ""), "roleplay", category)

    return selected


def get_fresh_english_questions(
    all_questions: List[Dict],
    category: str,
    count: int = 3
) -> List[Dict]:
    """
    영어면접용: 아직 안 나온 질문만 선택
    """
    import random

    fresh = filter_new_questions(
        all_questions,
        "english_interview",
        category,
        question_field="question"
    )

    if len(fresh) < count:
        logger.info(f"영어면접 질문 소진 - {category} 히스토리 리셋")
        reset_history("english_interview", category)
        fresh = all_questions

    selected = random.sample(fresh, min(count, len(fresh)))

    for q in selected:
        mark_question_asked(q.get("question", ""), "english_interview", category)

    return selected
