# interview_report_system.py
# 면접 제보 시스템 - 데이터 저장, 보상 계산, 중복 방지

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher

# 데이터 저장 경로
DATA_DIR = Path(__file__).parent / "data" / "interview_reports"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 제보 데이터 파일
REPORTS_FILE = DATA_DIR / "reports.json"
STATS_FILE = DATA_DIR / "stats.json"


def _load_reports() -> List[Dict]:
    """모든 제보 데이터 로드"""
    if REPORTS_FILE.exists():
        with open(REPORTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_reports(reports: List[Dict]):
    """제보 데이터 저장"""
    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)


def _load_stats() -> Dict:
    """통계 데이터 로드"""
    if STATS_FILE.exists():
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"total_reports": 0, "by_airline": {}, "last_updated": None}


def _save_stats(stats: Dict):
    """통계 데이터 저장"""
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def generate_user_hash(session_id: str) -> str:
    """익명 사용자 해시 생성"""
    return hashlib.sha256(session_id.encode()).hexdigest()[:16]


def check_duplicate_submission(user_hash: str, airline: str, interview_date: str) -> bool:
    """
    중복 제보 확인
    - 같은 user_hash가 같은 airline + interview_date로 24시간 내 재제보 금지
    """
    reports = _load_reports()
    now = datetime.now()

    for report in reports:
        if (report.get("user_hash") == user_hash and
            report.get("airline") == airline and
            report.get("interview_date") == interview_date):
            # 24시간 내 중복 확인
            submitted_at = datetime.fromisoformat(report.get("submitted_at", "2000-01-01"))
            if now - submitted_at < timedelta(hours=24):
                return True
    return False


def check_similar_questions(questions: List[Dict], airline: str, threshold: float = 0.9) -> List[str]:
    """
    유사 질문 확인
    - 기존 제보 중 90% 이상 유사한 질문이 있으면 경고
    """
    reports = _load_reports()
    existing_questions = []

    for report in reports:
        if report.get("airline") == airline:
            for q in report.get("questions", []):
                existing_questions.append(q.get("question", ""))

    warnings = []
    for new_q in questions:
        new_text = new_q.get("question", "")
        for existing_text in existing_questions:
            similarity = SequenceMatcher(None, new_text, existing_text).ratio()
            if similarity >= threshold:
                warnings.append(f"'{new_text[:30]}...'와 유사한 질문이 이미 존재합니다")
                break

    return warnings


def calculate_reward(submission: Dict) -> Optional[str]:
    """
    보상 계산

    - 8개 이상 + 꼬리질문 + 상세정보 → premium_14days
    - 5개 이상 + 상세정보 → premium_7days
    - 3개 이상 → premium_3days
    - 1개 이상 → premium_1day
    """
    questions = submission.get("questions", [])
    question_count = len(questions)
    has_followup = any(q.get("follow_up") for q in questions)
    has_details = (
        submission.get("interview_mood") and
        submission.get("duration_minutes")
    )

    if question_count >= 8 and has_followup and has_details:
        return "premium_14days"
    elif question_count >= 5 and has_details:
        return "premium_7days"
    elif question_count >= 3:
        return "premium_3days"
    elif question_count >= 1:
        return "premium_1day"
    return None


def get_reward_display(reward_code: str) -> Dict:
    """보상 코드를 표시용 정보로 변환"""
    rewards = {
        "premium_14days": {"days": 14, "label": "프리미엄 14일", "color": "gold"},
        "premium_7days": {"days": 7, "label": "프리미엄 7일", "color": "silver"},
        "premium_3days": {"days": 3, "label": "프리미엄 3일", "color": "bronze"},
        "premium_1day": {"days": 1, "label": "프리미엄 1일", "color": "basic"},
    }
    return rewards.get(reward_code, {"days": 0, "label": "보상 없음", "color": "none"})


def submit_report(
    airline: str,
    interview_date: str,
    interview_stage: str,
    questions: List[Dict],
    interview_mood: Optional[str] = None,
    interviewer_count: Optional[int] = None,
    duration_minutes: Optional[int] = None,
    additional_notes: Optional[str] = None,
    user_session_id: str = "anonymous"
) -> Dict:
    """
    면접 제보 제출

    Returns:
        {
            "success": bool,
            "message": str,
            "reward": Optional[str],
            "report_id": Optional[str],
            "warnings": List[str]
        }
    """
    user_hash = generate_user_hash(user_session_id)

    # 중복 확인
    if check_duplicate_submission(user_hash, airline, interview_date):
        return {
            "success": False,
            "message": "같은 항공사/날짜로 24시간 내 이미 제보하셨습니다.",
            "reward": None,
            "report_id": None,
            "warnings": []
        }

    # 유사 질문 경고 (차단은 안 함)
    warnings = check_similar_questions(questions, airline)

    # 보상 계산
    submission = {
        "questions": questions,
        "interview_mood": interview_mood,
        "duration_minutes": duration_minutes,
    }
    reward = calculate_reward(submission)

    # 제보 ID 생성
    report_id = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_hash[:6]}"

    # 제보 데이터 구성
    report = {
        "id": report_id,
        "airline": airline,
        "interview_date": interview_date,
        "interview_stage": interview_stage,
        "questions": questions,
        "interview_mood": interview_mood,
        "interviewer_count": interviewer_count,
        "duration_minutes": duration_minutes,
        "additional_notes": additional_notes,
        "submitted_at": datetime.now().isoformat(),
        "user_hash": user_hash,
        "reward": reward,
        "verified": False  # 추후 교차 검증용
    }

    # 저장
    reports = _load_reports()
    reports.append(report)
    _save_reports(reports)

    # 통계 업데이트
    _update_stats(airline)

    return {
        "success": True,
        "message": "제보가 성공적으로 접수되었습니다!",
        "reward": reward,
        "report_id": report_id,
        "warnings": warnings
    }


def _update_stats(airline: str):
    """통계 업데이트"""
    stats = _load_stats()
    stats["total_reports"] = stats.get("total_reports", 0) + 1
    stats["by_airline"] = stats.get("by_airline", {})
    stats["by_airline"][airline] = stats["by_airline"].get(airline, 0) + 1
    stats["last_updated"] = datetime.now().isoformat()
    _save_stats(stats)


def get_airline_report_count(airline: str) -> int:
    """특정 항공사의 제보 수 조회"""
    reports = _load_reports()
    return sum(1 for r in reports if r.get("airline") == airline)


def get_airline_reports(airline: str, days: int = 30) -> List[Dict]:
    """
    특정 항공사의 최근 N일 제보 조회

    Args:
        airline: 항공사명
        days: 최근 N일 (기본 30일)

    Returns:
        제보 리스트
    """
    reports = _load_reports()
    cutoff = datetime.now() - timedelta(days=days)

    filtered = []
    for r in reports:
        if r.get("airline") != airline:
            continue
        submitted = datetime.fromisoformat(r.get("submitted_at", "2000-01-01"))
        if submitted >= cutoff:
            filtered.append(r)

    return filtered


def get_question_stats(airline: str, days: int = 30) -> Dict:
    """
    질문 출현율 통계 계산

    Returns:
        {
            "total_reports": int,
            "questions": [
                {"question": str, "count": int, "percentage": float}
            ],
            "sufficient_data": bool
        }
    """
    reports = get_airline_reports(airline, days)
    total = len(reports)

    if total < 10:
        return {
            "total_reports": total,
            "questions": [],
            "sufficient_data": False,
            "needed": 10 - total
        }

    # 질문별 카운트
    question_counts = {}
    for report in reports:
        for q in report.get("questions", []):
            q_text = q.get("question", "").strip()
            if q_text:
                # 간단한 정규화 (소문자, 공백 정리)
                q_normalized = " ".join(q_text.lower().split())
                if q_normalized not in question_counts:
                    question_counts[q_normalized] = {
                        "original": q_text,
                        "count": 0
                    }
                question_counts[q_normalized]["count"] += 1

    # 정렬 및 출현율 계산
    sorted_questions = sorted(
        question_counts.values(),
        key=lambda x: x["count"],
        reverse=True
    )

    result_questions = []
    for q in sorted_questions[:20]:  # 상위 20개
        result_questions.append({
            "question": q["original"],
            "count": q["count"],
            "percentage": round(q["count"] / total * 100, 1)
        })

    return {
        "total_reports": total,
        "questions": result_questions,
        "sufficient_data": True,
        "needed": 0
    }


def get_recent_new_questions(airline: str, days: int = 7) -> List[Dict]:
    """
    최근 N일 내 처음 등장한 질문

    기존 30일 데이터에 없다가 최근 7일에 처음 등장한 질문
    """
    recent_reports = get_airline_reports(airline, days)
    older_reports = get_airline_reports(airline, 30)

    # 30일 전체에서 최근 7일 제외
    recent_ids = {r["id"] for r in recent_reports}
    older_questions = set()

    for r in older_reports:
        if r["id"] not in recent_ids:
            for q in r.get("questions", []):
                older_questions.add(q.get("question", "").lower().strip())

    # 최근 7일에만 있는 질문
    new_questions = {}
    for r in recent_reports:
        for q in r.get("questions", []):
            q_text = q.get("question", "")
            q_lower = q_text.lower().strip()
            if q_lower and q_lower not in older_questions:
                if q_lower not in new_questions:
                    new_questions[q_lower] = {"question": q_text, "count": 0}
                new_questions[q_lower]["count"] += 1

    return sorted(new_questions.values(), key=lambda x: x["count"], reverse=True)


def get_trending_questions(airline: str) -> List[Dict]:
    """
    급상승 질문 (전월 대비 +20%p 이상)
    """
    current_month = get_airline_reports(airline, 30)
    prev_month = get_airline_reports(airline, 60)

    if len(current_month) < 10 or len(prev_month) < 10:
        return []

    # 이번 달 출현율
    current_counts = {}
    for r in current_month:
        for q in r.get("questions", []):
            q_lower = q.get("question", "").lower().strip()
            current_counts[q_lower] = current_counts.get(q_lower, 0) + 1

    # 지난 달 (30~60일 전) 출현율
    current_ids = {r["id"] for r in current_month}
    prev_counts = {}
    prev_total = 0
    for r in prev_month:
        if r["id"] not in current_ids:
            prev_total += 1
            for q in r.get("questions", []):
                q_lower = q.get("question", "").lower().strip()
                prev_counts[q_lower] = prev_counts.get(q_lower, 0) + 1

    if prev_total == 0:
        return []

    # 급상승 계산
    trending = []
    current_total = len(current_month)

    for q_lower, count in current_counts.items():
        current_pct = count / current_total * 100
        prev_pct = prev_counts.get(q_lower, 0) / prev_total * 100
        diff = current_pct - prev_pct

        if diff >= 20:  # +20%p 이상
            # 원본 텍스트 찾기
            original = q_lower
            for r in current_month:
                for q in r.get("questions", []):
                    if q.get("question", "").lower().strip() == q_lower:
                        original = q.get("question", "")
                        break

            trending.append({
                "question": original,
                "diff": round(diff, 1),
                "current_pct": round(current_pct, 1)
            })

    return sorted(trending, key=lambda x: x["diff"], reverse=True)[:5]


# 통계 조회용 함수
def get_all_stats() -> Dict:
    """전체 통계 조회"""
    return _load_stats()
