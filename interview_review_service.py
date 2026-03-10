"""
FLYREADY 면접 복습 & AI 추천 서비스
- 주간 복습 추천
- 성장 추이 분석
- 다시 연습하기 추천
- MongoDB 마이그레이션 대비 구조
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

# 히스토리 유틸리티 임포트
try:
    from interview_history_utils import (
        get_all_sessions,
        get_weak_questions,
        get_category_stats,
        get_recent_scores,
        get_total_stats,
    )
    HISTORY_AVAILABLE = True
except ImportError:
    HISTORY_AVAILABLE = False


# ============================================================
# 카테고리 정의
# ============================================================

CATEGORY_NAMES = {
    "common": "공통 질문",
    "personality": "인성/성격",
    "experience": "경험/역량",
    "situation": "상황 대처",
    "airline": "항공사 관련",
    "service": "서비스 마인드",
    "teamwork": "팀워크",
    "stress": "스트레스 관리",
    "motivation": "지원 동기",
    "english": "영어",
    "unknown": "기타",
}

CATEGORY_TIPS = {
    "common": "자기소개는 1분 내외로 핵심만 전달하세요.",
    "personality": "구체적인 사례와 함께 답변하면 신뢰감이 높아집니다.",
    "experience": "STAR 기법을 활용하여 체계적으로 답변하세요.",
    "situation": "실제 있었던 상황처럼 구체적으로 답변하세요.",
    "airline": "항공사 최신 뉴스와 특징을 미리 파악하세요.",
    "service": "고객 중심 사고를 보여주는 답변이 좋습니다.",
    "teamwork": "협력 경험을 구체적으로 설명하세요.",
    "stress": "긍정적인 스트레스 해소 방법을 준비하세요.",
    "motivation": "항공사와 본인의 연결고리를 강조하세요.",
    "english": "간결하고 명확한 문장으로 답변하세요.",
    "unknown": "차분하게 질문의 의도를 파악하고 답변하세요.",
}


# ============================================================
# 주간 추천
# ============================================================

def get_weekly_recommendation() -> Dict:
    """
    이번 주 복습 추천

    Returns:
        {
            "has_data": bool,
            "weak_areas": ["카테고리1", "카테고리2"],
            "recommended_questions": [
                {"question_text": "...", "category": "...", "last_score": 55}
            ],
            "message": "이번 주 추천 메시지",
            "focus_tip": "집중 연습 팁",
            "weekly_goal": {"target_sessions": 5, "current": 3}
        }
    """
    if not HISTORY_AVAILABLE:
        return _empty_recommendation()

    try:
        # 최근 7일 세션 가져오기
        all_sessions = get_all_sessions(limit=100)
        if not all_sessions:
            return _empty_recommendation()

        # 최근 7일 필터
        week_ago = datetime.now() - timedelta(days=7)
        recent_sessions = []
        for s in all_sessions:
            created_at = s.get("created_at", "")
            if created_at:
                try:
                    session_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if session_date.replace(tzinfo=None) >= week_ago:
                        recent_sessions.append(s)
                except:
                    pass

        # 약점 질문 분석
        weak_questions = get_weak_questions(threshold=65)

        # 카테고리별 집계
        category_scores = defaultdict(list)
        for q in weak_questions:
            cat = q.get("category", "unknown")
            score = q.get("score", 0)
            category_scores[cat].append(score)

        # 약점 영역 (평균 점수 낮은 순)
        weak_areas = []
        for cat, scores in category_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                weak_areas.append((cat, avg, len(scores)))

        weak_areas.sort(key=lambda x: (x[1], -x[2]))  # 점수 낮고, 개수 많은 순
        top_weak_areas = [CATEGORY_NAMES.get(w[0], w[0]) for w in weak_areas[:3]]

        # 추천 질문 (가장 낮은 점수 순)
        weak_questions_sorted = sorted(weak_questions, key=lambda x: x.get("score", 0))[:5]
        recommended_questions = [
            {
                "question_text": q.get("question_text", ""),
                "category": CATEGORY_NAMES.get(q.get("category", "unknown"), "기타"),
                "last_score": q.get("score", 0),
                "session_date": q.get("session_date", ""),
            }
            for q in weak_questions_sorted
        ]

        # 메시지 생성
        if top_weak_areas:
            main_weak = top_weak_areas[0]
            message = f"'{main_weak}' 영역을 집중 연습하면 좋을 것 같아요!"
            focus_tip = CATEGORY_TIPS.get(
                weak_areas[0][0] if weak_areas else "unknown",
                "꾸준한 연습이 실력 향상의 비결입니다!"
            )
        else:
            message = "꾸준히 연습하고 계시네요! 지금처럼 유지하세요."
            focus_tip = "다양한 유형의 질문에 도전해보세요."

        # 주간 목표
        weekly_goal = {
            "target_sessions": 5,
            "current": len(recent_sessions),
            "achieved": len(recent_sessions) >= 5,
        }

        return {
            "has_data": True,
            "weak_areas": top_weak_areas,
            "recommended_questions": recommended_questions,
            "message": message,
            "focus_tip": focus_tip,
            "weekly_goal": weekly_goal,
        }

    except Exception as e:
        print(f"[interview_review_service] get_weekly_recommendation error: {e}")
        return _empty_recommendation()


def _empty_recommendation() -> Dict:
    """빈 추천 데이터"""
    return {
        "has_data": False,
        "weak_areas": [],
        "recommended_questions": [],
        "message": "아직 면접 기록이 없어요. 첫 모의면접을 시작해보세요!",
        "focus_tip": "첫 면접이 가장 어렵습니다. 용기를 내어 시작해보세요!",
        "weekly_goal": {"target_sessions": 5, "current": 0, "achieved": False},
    }


# ============================================================
# 성장 추이 분석
# ============================================================

def get_improvement_trend(days: int = 30) -> Dict:
    """
    성장 추이 데이터

    Args:
        days: 분석 기간 (일)

    Returns:
        {
            "has_data": bool,
            "period": {"start": "2026-01-01", "end": "2026-02-06"},
            "total_sessions": 15,
            "score_trend": [
                {"date": "2026-02-01", "score": 72, "sessions": 2}
            ],
            "improvement": {
                "voice": {"start": 65, "end": 75, "change": +10},
                "content": {"start": 60, "end": 72, "change": +12}
            },
            "best_day": "2026-02-05",
            "streak": {"current": 3, "longest": 7}
        }
    """
    if not HISTORY_AVAILABLE:
        return _empty_trend()

    try:
        all_sessions = get_all_sessions(limit=200)
        if not all_sessions:
            return _empty_trend()

        # 기간 필터
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()

        filtered_sessions = []
        for s in all_sessions:
            created_at = s.get("created_at", "")
            if created_at:
                try:
                    session_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    if session_date.replace(tzinfo=None) >= start_date:
                        filtered_sessions.append({
                            **s,
                            "_parsed_date": session_date.replace(tzinfo=None)
                        })
                except:
                    pass

        if not filtered_sessions:
            return _empty_trend()

        # 날짜별 집계
        daily_scores = defaultdict(list)
        for s in filtered_sessions:
            date_str = s["_parsed_date"].strftime("%Y-%m-%d")
            scores = s.get("scores", {})
            total_score = scores.get("total", 0)
            if total_score > 0:
                daily_scores[date_str].append(total_score)

        # 점수 추이 데이터
        score_trend = []
        for date_str in sorted(daily_scores.keys()):
            scores = daily_scores[date_str]
            score_trend.append({
                "date": date_str,
                "score": round(sum(scores) / len(scores), 1),
                "sessions": len(scores),
            })

        # 개선도 계산 (처음 3개 vs 마지막 3개)
        improvement = _calculate_improvement(filtered_sessions)

        # 최고 점수 날짜
        best_day = max(score_trend, key=lambda x: x["score"])["date"] if score_trend else None

        # 연속 연습 일수
        streak = _calculate_streak(daily_scores)

        return {
            "has_data": True,
            "period": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
            },
            "total_sessions": len(filtered_sessions),
            "score_trend": score_trend,
            "improvement": improvement,
            "best_day": best_day,
            "streak": streak,
        }

    except Exception as e:
        print(f"[interview_review_service] get_improvement_trend error: {e}")
        return _empty_trend()


def _calculate_improvement(sessions: List[Dict]) -> Dict:
    """개선도 계산"""
    if len(sessions) < 2:
        return {"voice": None, "content": None}

    # 시간순 정렬
    sorted_sessions = sorted(sessions, key=lambda x: x.get("_parsed_date", datetime.min))

    # 처음 3개, 마지막 3개
    first_n = sorted_sessions[:min(3, len(sorted_sessions))]
    last_n = sorted_sessions[-min(3, len(sorted_sessions)):]

    def avg_score(session_list, key):
        scores = [s.get("scores", {}).get(key, 0) for s in session_list]
        valid_scores = [s for s in scores if s > 0]
        return round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0

    voice_start = avg_score(first_n, "voice_avg")
    voice_end = avg_score(last_n, "voice_avg")
    content_start = avg_score(first_n, "content_avg")
    content_end = avg_score(last_n, "content_avg")

    return {
        "voice": {
            "start": voice_start,
            "end": voice_end,
            "change": round(voice_end - voice_start, 1),
        },
        "content": {
            "start": content_start,
            "end": content_end,
            "change": round(content_end - content_start, 1),
        },
    }


def _calculate_streak(daily_scores: Dict) -> Dict:
    """연속 연습 일수 계산"""
    if not daily_scores:
        return {"current": 0, "longest": 0}

    dates = sorted([datetime.strptime(d, "%Y-%m-%d") for d in daily_scores.keys()])
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # 현재 연속
    current_streak = 0
    check_date = today
    while check_date.strftime("%Y-%m-%d") in daily_scores or \
          (check_date - timedelta(days=1)).strftime("%Y-%m-%d") in daily_scores:
        if check_date.strftime("%Y-%m-%d") in daily_scores:
            current_streak += 1
        check_date -= timedelta(days=1)
        if current_streak > len(dates):
            break

    # 최장 연속
    longest_streak = 0
    current_run = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            current_run += 1
        else:
            longest_streak = max(longest_streak, current_run)
            current_run = 1
    longest_streak = max(longest_streak, current_run)

    return {
        "current": current_streak,
        "longest": longest_streak,
    }


def _empty_trend() -> Dict:
    """빈 추이 데이터"""
    return {
        "has_data": False,
        "period": None,
        "total_sessions": 0,
        "score_trend": [],
        "improvement": {"voice": None, "content": None},
        "best_day": None,
        "streak": {"current": 0, "longest": 0},
    }


# ============================================================
# 다시 연습하기 추천
# ============================================================

def get_practice_again_list(limit: int = 10) -> List[Dict]:
    """
    다시 연습하기 추천 목록

    Args:
        limit: 최대 개수

    Returns:
        [
            {
                "question_text": "자기소개 해주세요",
                "category": "공통 질문",
                "reason": "점수 60점 미만",
                "last_score": 55,
                "last_date": "2026-02-05",
                "attempt_count": 3,
                "priority": "high"
            }
        ]
    """
    if not HISTORY_AVAILABLE:
        return []

    try:
        weak_questions = get_weak_questions(threshold=70)

        # 우선순위 계산
        practice_list = []
        question_stats = defaultdict(lambda: {"scores": [], "dates": [], "count": 0})

        for q in weak_questions:
            q_text = q.get("question_text", "")
            if q_text:
                question_stats[q_text]["scores"].append(q.get("score", 0))
                question_stats[q_text]["dates"].append(q.get("session_date", ""))
                question_stats[q_text]["count"] += 1
                question_stats[q_text]["category"] = q.get("category", "unknown")

        for q_text, stats in question_stats.items():
            last_score = stats["scores"][-1] if stats["scores"] else 0
            avg_score = sum(stats["scores"]) / len(stats["scores"]) if stats["scores"] else 0
            last_date = stats["dates"][-1] if stats["dates"] else ""

            # 우선순위 결정
            if avg_score < 50:
                priority = "high"
                reason = "평균 점수 50점 미만"
            elif avg_score < 60:
                priority = "high"
                reason = "평균 점수 60점 미만"
            elif stats["count"] >= 3 and avg_score < 70:
                priority = "medium"
                reason = "반복 연습 필요"
            else:
                priority = "low"
                reason = "점수 개선 권장"

            practice_list.append({
                "question_text": q_text,
                "category": CATEGORY_NAMES.get(stats["category"], "기타"),
                "reason": reason,
                "last_score": last_score,
                "avg_score": round(avg_score, 1),
                "last_date": last_date,
                "attempt_count": stats["count"],
                "priority": priority,
            })

        # 우선순위 순 정렬
        priority_order = {"high": 0, "medium": 1, "low": 2}
        practice_list.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["avg_score"]))

        return practice_list[:limit]

    except Exception as e:
        print(f"[interview_review_service] get_practice_again_list error: {e}")
        return []


# ============================================================
# 카테고리 분석
# ============================================================

def get_category_analysis() -> Dict:
    """
    카테고리별 점수 분석

    Returns:
        {
            "has_data": bool,
            "categories": [
                {
                    "name": "공통 질문",
                    "code": "common",
                    "avg_score": 72,
                    "count": 15,
                    "trend": "improving",  # improving, stable, declining
                    "tip": "..."
                }
            ],
            "strongest": "서비스 마인드",
            "weakest": "상황 대처"
        }
    """
    if not HISTORY_AVAILABLE:
        return {"has_data": False, "categories": [], "strongest": None, "weakest": None}

    try:
        stats = get_category_stats()
        if not stats:
            return {"has_data": False, "categories": [], "strongest": None, "weakest": None}

        categories = []
        for code, data in stats.items():
            categories.append({
                "name": CATEGORY_NAMES.get(code, code),
                "code": code,
                "avg_score": data.get("avg_score", 0),
                "count": data.get("count", 0),
                "trend": _determine_trend(code),
                "tip": CATEGORY_TIPS.get(code, ""),
            })

        # 점수 순 정렬
        categories.sort(key=lambda x: x["avg_score"], reverse=True)

        strongest = categories[0]["name"] if categories else None
        weakest = categories[-1]["name"] if categories else None

        return {
            "has_data": True,
            "categories": categories,
            "strongest": strongest,
            "weakest": weakest,
        }

    except Exception as e:
        print(f"[interview_review_service] get_category_analysis error: {e}")
        return {"has_data": False, "categories": [], "strongest": None, "weakest": None}


def _determine_trend(category: str) -> str:
    """카테고리 추세 판단 (간단 버전)"""
    # TODO: 실제 시계열 분석 추가
    return "stable"


# ============================================================
# 면접 준비도 점수
# ============================================================

def get_readiness_score() -> Dict:
    """
    종합 면접 준비도 점수

    Returns:
        {
            "score": 75,
            "grade": "B+",
            "level": "준비 중",
            "breakdown": {
                "consistency": 80,  # 꾸준함
                "improvement": 70,  # 성장세
                "coverage": 65,     # 다양성
                "mastery": 72       # 숙련도
            },
            "next_level": {
                "name": "합격 유력",
                "required_score": 85,
                "gap": 10
            }
        }
    """
    if not HISTORY_AVAILABLE:
        return _empty_readiness()

    try:
        total_stats = get_total_stats()
        if not total_stats or total_stats.get("total_sessions", 0) == 0:
            return _empty_readiness()

        # 각 항목 점수 계산
        consistency = _calc_consistency_score(total_stats)
        improvement = _calc_improvement_score()
        coverage = _calc_coverage_score()
        mastery = total_stats.get("avg_score", 0)

        # 종합 점수 (가중 평균)
        total_score = (
            consistency * 0.2 +
            improvement * 0.3 +
            coverage * 0.2 +
            mastery * 0.3
        )
        total_score = round(total_score, 1)

        # 등급 및 레벨
        grade, level = _determine_grade(total_score)
        next_level = _get_next_level(total_score)

        return {
            "score": total_score,
            "grade": grade,
            "level": level,
            "breakdown": {
                "consistency": round(consistency, 1),
                "improvement": round(improvement, 1),
                "coverage": round(coverage, 1),
                "mastery": round(mastery, 1),
            },
            "next_level": next_level,
        }

    except Exception as e:
        print(f"[interview_review_service] get_readiness_score error: {e}")
        return _empty_readiness()


def _calc_consistency_score(stats: Dict) -> float:
    """꾸준함 점수"""
    sessions = stats.get("total_sessions", 0)
    # 30회 이상이면 100점
    return min(100, sessions / 30 * 100)


def _calc_improvement_score() -> float:
    """성장세 점수"""
    trend = get_improvement_trend(30)
    if not trend.get("has_data"):
        return 50  # 기본값

    improvement = trend.get("improvement", {})
    voice_change = improvement.get("voice", {}).get("change", 0) or 0
    content_change = improvement.get("content", {}).get("change", 0) or 0

    # 변화량을 점수로 변환 (-20 ~ +20 -> 0 ~ 100)
    avg_change = (voice_change + content_change) / 2
    score = 50 + avg_change * 2.5
    return max(0, min(100, score))


def _calc_coverage_score() -> float:
    """다양성 점수 (연습한 카테고리 수)"""
    try:
        stats = get_category_stats()
        practiced_categories = len([c for c in stats.values() if c.get("count", 0) > 0])
        total_categories = len(CATEGORY_NAMES)
        return (practiced_categories / total_categories) * 100
    except:
        return 50


def _determine_grade(score: float) -> tuple:
    """등급 및 레벨 결정"""
    if score >= 90:
        return "A+", "합격 유력"
    elif score >= 85:
        return "A", "합격 유력"
    elif score >= 80:
        return "B+", "준비 완료"
    elif score >= 75:
        return "B", "준비 중"
    elif score >= 70:
        return "C+", "연습 필요"
    elif score >= 60:
        return "C", "연습 필요"
    else:
        return "D", "시작 단계"


def _get_next_level(score: float) -> Dict:
    """다음 레벨 정보"""
    levels = [
        (90, "합격 유력"),
        (85, "합격 유력"),
        (80, "준비 완료"),
        (75, "준비 중"),
        (70, "연습 필요"),
        (60, "연습 필요"),
    ]

    for threshold, name in levels:
        if score < threshold:
            return {
                "name": name,
                "required_score": threshold,
                "gap": round(threshold - score, 1),
            }

    return {"name": "최고 레벨", "required_score": 100, "gap": round(100 - score, 1)}


def _empty_readiness() -> Dict:
    """빈 준비도 데이터"""
    return {
        "score": 0,
        "grade": "-",
        "level": "시작 전",
        "breakdown": {
            "consistency": 0,
            "improvement": 0,
            "coverage": 0,
            "mastery": 0,
        },
        "next_level": {"name": "시작 단계", "required_score": 60, "gap": 60},
    }


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("FLYREADY 면접 복습 서비스 테스트")
    print("=" * 50)

    print("\n1. 주간 추천:")
    rec = get_weekly_recommendation()
    print(f"   메시지: {rec['message']}")
    print(f"   약점 영역: {rec['weak_areas']}")

    print("\n2. 성장 추이:")
    trend = get_improvement_trend(30)
    print(f"   데이터 있음: {trend['has_data']}")
    print(f"   총 세션: {trend['total_sessions']}")

    print("\n3. 다시 연습하기:")
    practice = get_practice_again_list(5)
    print(f"   추천 개수: {len(practice)}")

    print("\n4. 카테고리 분석:")
    cat = get_category_analysis()
    print(f"   강점: {cat['strongest']}")
    print(f"   약점: {cat['weakest']}")

    print("\n5. 준비도 점수:")
    ready = get_readiness_score()
    print(f"   점수: {ready['score']} ({ready['grade']})")
    print(f"   레벨: {ready['level']}")

    print("\n✅ 테스트 완료")
