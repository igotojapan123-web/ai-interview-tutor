# score_utils.py
# 점수 자동 수집 및 관리 유틸리티

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 데이터 파일 경로
SCORES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_scores.json")
GOALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_goals.json")

# =====================
# 영역별 세부 평가 항목 정의
# =====================

EVALUATION_CATEGORIES = {
    "롤플레잉": {
        "icon": "🎭",
        "items": {
            "empathy": {"name": "공감 표현", "description": "승객의 감정을 이해하고 공감하는 능력"},
            "solution": {"name": "해결책 제시", "description": "적절한 대안과 해결 방법 제시"},
            "professionalism": {"name": "전문성", "description": "규정 이해와 전문적인 안내"},
            "attitude": {"name": "태도/말투", "description": "친절하고 존중하는 태도"},
        }
    },
    "영어면접": {
        "icon": "🌍",
        "items": {
            "pronunciation": {"name": "발음", "description": "명확하고 정확한 발음"},
            "fluency": {"name": "유창성", "description": "자연스럽고 막힘없는 말하기"},
            "grammar": {"name": "문법", "description": "올바른 문법 사용"},
            "content": {"name": "내용", "description": "답변의 논리성과 구체성"},
            "vocabulary": {"name": "어휘력", "description": "적절하고 다양한 어휘 사용"},
        }
    },
    "모의면접": {
        "icon": "👔",
        "items": {
            "first_impression": {"name": "첫인상", "description": "자세, 표정, 인사"},
            "answer_quality": {"name": "답변 내용", "description": "논리성, 구체성, 진정성"},
            "communication": {"name": "의사소통", "description": "명확하고 자신감 있는 전달"},
            "attitude": {"name": "태도", "description": "적극성, 열정, 예의"},
            "adaptability": {"name": "순발력", "description": "예상치 못한 질문 대처 능력"},
        }
    },
    "토론면접": {
        "icon": "💬",
        "items": {
            "logic": {"name": "논리성", "description": "주장의 논리적 일관성"},
            "listening": {"name": "경청", "description": "다른 의견을 듣고 반응"},
            "expression": {"name": "표현력", "description": "명확하고 설득력 있는 표현"},
            "attitude": {"name": "토론 태도", "description": "협력적이고 존중하는 자세"},
            "leadership": {"name": "리더십", "description": "토론을 이끌거나 정리하는 능력"},
        }
    },
    "자소서": {
        "icon": "📝",
        "items": {
            "structure": {"name": "구조", "description": "체계적인 구성"},
            "specificity": {"name": "구체성", "description": "구체적인 사례와 경험"},
            "differentiation": {"name": "차별화", "description": "나만의 강점 어필"},
            "motivation": {"name": "지원동기", "description": "진정성 있는 동기"},
            "fit": {"name": "직무적합성", "description": "승무원 자질과의 연결"},
        }
    },
}


def load_scores() -> Dict:
    """점수 데이터 로드"""
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"점수 로드 오류: {e}")
    return {"scores": [], "detailed_scores": []}


def save_scores(data: Dict):
    """점수 데이터 저장"""
    try:
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"점수 저장 오류: {e}")


def load_goals() -> Dict:
    """목표 데이터 로드"""
    if os.path.exists(GOALS_FILE):
        try:
            with open(GOALS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"목표 로드 오류: {e}")
    return {
        "weekly_goal": 10,  # 주간 연습 목표 횟수
        "monthly_goal": 40,  # 월간 연습 목표 횟수
        "target_score": 80,  # 목표 점수
        "focus_areas": [],  # 집중 연습 영역
    }


def save_goals(data: Dict):
    """목표 데이터 저장"""
    try:
        with open(GOALS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"목표 저장 오류: {e}")


def save_practice_score(
    practice_type: str,
    total_score: int,
    detailed_scores: Optional[Dict[str, int]] = None,
    memo: str = "",
    scenario: str = ""
):
    """
    연습 점수 자동 저장

    Args:
        practice_type: 연습 유형 (롤플레잉, 영어면접, 모의면접, 토론면접, 자소서)
        total_score: 총점 (0-100)
        detailed_scores: 세부 항목별 점수 {"empathy": 80, "solution": 70, ...}
        memo: 메모
        scenario: 시나리오/질문 정보
    """
    data = load_scores()

    score_entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "type": practice_type,
        "score": total_score,
        "memo": memo,
        "scenario": scenario,
    }

    # 기본 점수 저장
    data["scores"].append(score_entry)

    # 세부 점수 저장
    if detailed_scores:
        detailed_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M"),
            "type": practice_type,
            "scores": detailed_scores,
            "total": total_score,
        }
        if "detailed_scores" not in data:
            data["detailed_scores"] = []
        data["detailed_scores"].append(detailed_entry)

    save_scores(data)


def parse_evaluation_score(evaluation_text: str, practice_type: str) -> Dict:
    """
    AI 평가 텍스트에서 점수 추출

    Args:
        evaluation_text: AI가 생성한 평가 텍스트
        practice_type: 연습 유형

    Returns:
        {"total": 75, "detailed": {"empathy": 80, "solution": 70, ...}}
    """
    import re

    result = {"total": 0, "detailed": {}}

    # 총점 추출 패턴들
    total_patterns = [
        r"(\d+)\s*점\s*만점에\s*(\d+)\s*점",  # "100점 만점에 75점"
        r"종합\s*점수[:\s]*(\d+)",  # "종합 점수: 75"
        r"총점[:\s]*(\d+)",  # "총점: 75"
        r"(\d+)\s*/\s*100",  # "75/100"
        r"(\d+)점",  # "75점" (마지막 fallback)
    ]

    for pattern in total_patterns:
        match = re.search(pattern, evaluation_text)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                result["total"] = int(groups[1])
            else:
                result["total"] = int(groups[0])
            break

    # 세부 항목 점수 추출
    if practice_type in EVALUATION_CATEGORIES:
        items = EVALUATION_CATEGORIES[practice_type]["items"]
        for key, info in items.items():
            name = info["name"]
            # 패턴: "공감 표현" 다음에 나오는 숫자/25 또는 숫자점
            patterns = [
                rf"{name}[:\s|]*(\d+)\s*/\s*25",  # "공감 표현: 20/25"
                rf"{name}[:\s|]*(\d+)\s*점",  # "공감 표현: 20점"
                rf"\|\s*{name}\s*\|\s*(\d+)",  # "| 공감 표현 | 20"
            ]
            for pattern in patterns:
                match = re.search(pattern, evaluation_text)
                if match:
                    score = int(match.group(1))
                    # 25점 만점이면 100점 만점으로 변환
                    if score <= 25:
                        score = int(score * 4)
                    result["detailed"][key] = min(score, 100)
                    break

    return result


def get_category_averages(practice_type: str, days: int = 30) -> Dict[str, float]:
    """
    특정 연습 유형의 카테고리별 평균 점수

    Args:
        practice_type: 연습 유형
        days: 최근 N일

    Returns:
        {"empathy": 75.5, "solution": 68.2, ...}
    """
    data = load_scores()
    detailed_scores = data.get("detailed_scores", [])

    if not detailed_scores:
        return {}

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # 해당 유형의 최근 점수들 수집
    category_scores = {}
    for entry in detailed_scores:
        if entry.get("type") != practice_type:
            continue
        if entry.get("date", "") < cutoff_date:
            continue

        scores = entry.get("scores", {})
        for key, score in scores.items():
            if key not in category_scores:
                category_scores[key] = []
            category_scores[key].append(score)

    # 평균 계산
    averages = {}
    for key, scores in category_scores.items():
        if scores:
            averages[key] = sum(scores) / len(scores)

    return averages


def get_all_category_averages(days: int = 30) -> Dict[str, Dict[str, float]]:
    """
    모든 연습 유형의 카테고리별 평균 점수

    Returns:
        {
            "롤플레잉": {"empathy": 75, "solution": 68, ...},
            "영어면접": {"pronunciation": 70, ...},
            ...
        }
    """
    result = {}
    for practice_type in EVALUATION_CATEGORIES.keys():
        averages = get_category_averages(practice_type, days)
        if averages:
            result[practice_type] = averages
    return result


def get_overall_radar_data(days: int = 30) -> Dict[str, float]:
    """
    전체 레이더 차트용 데이터 (영역별 평균)

    Returns:
        {"롤플레잉": 72.5, "영어면접": 68.0, "모의면접": 75.0, ...}
    """
    data = load_scores()
    scores = data.get("scores", [])

    if not scores:
        return {}

    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    type_scores = {}
    for entry in scores:
        if entry.get("date", "") < cutoff_date:
            continue
        practice_type = entry.get("type", "")
        score = entry.get("score", 0)

        if practice_type not in type_scores:
            type_scores[practice_type] = []
        type_scores[practice_type].append(score)

    # 평균 계산
    result = {}
    for practice_type, scores_list in type_scores.items():
        if scores_list:
            result[practice_type] = sum(scores_list) / len(scores_list)

    return result


def get_growth_comparison(days_recent: int = 7, days_past: int = 30) -> Dict:
    """
    성장 비교 데이터

    Args:
        days_recent: 최근 기간 (일)
        days_past: 비교 기간 (일)

    Returns:
        {
            "recent_avg": 75.5,
            "past_avg": 68.2,
            "growth": 7.3,
            "growth_percent": 10.7,
            "by_type": {
                "롤플레잉": {"recent": 80, "past": 70, "growth": 10},
                ...
            }
        }
    """
    data = load_scores()
    scores = data.get("scores", [])

    if not scores:
        return {}

    today = datetime.now().date()
    recent_cutoff = (today - timedelta(days=days_recent)).strftime("%Y-%m-%d")
    past_cutoff = (today - timedelta(days=days_past)).strftime("%Y-%m-%d")

    recent_scores = []
    past_scores = []
    type_recent = {}
    type_past = {}

    for entry in scores:
        date_str = entry.get("date", "")
        score = entry.get("score", 0)
        practice_type = entry.get("type", "")

        if date_str >= recent_cutoff:
            recent_scores.append(score)
            if practice_type not in type_recent:
                type_recent[practice_type] = []
            type_recent[practice_type].append(score)
        elif date_str >= past_cutoff:
            past_scores.append(score)
            if practice_type not in type_past:
                type_past[practice_type] = []
            type_past[practice_type].append(score)

    recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
    past_avg = sum(past_scores) / len(past_scores) if past_scores else 0
    growth = recent_avg - past_avg
    growth_percent = (growth / past_avg * 100) if past_avg > 0 else 0

    # 유형별 비교
    by_type = {}
    all_types = set(type_recent.keys()) | set(type_past.keys())
    for t in all_types:
        r = sum(type_recent.get(t, [])) / len(type_recent[t]) if type_recent.get(t) else 0
        p = sum(type_past.get(t, [])) / len(type_past[t]) if type_past.get(t) else 0
        by_type[t] = {
            "recent": round(r, 1),
            "past": round(p, 1),
            "growth": round(r - p, 1),
        }

    return {
        "recent_avg": round(recent_avg, 1),
        "past_avg": round(past_avg, 1),
        "growth": round(growth, 1),
        "growth_percent": round(growth_percent, 1),
        "by_type": by_type,
    }


def get_weekly_report() -> Dict:
    """
    주간 리포트 데이터 생성

    Returns:
        {
            "period": "2024-01-08 ~ 2024-01-14",
            "total_practices": 15,
            "avg_score": 73.5,
            "best_area": "롤플레잉",
            "weak_area": "영어면접",
            "improvement": 5.2,
            "streak": 5,
            "recommendations": ["영어 발음 연습 필요", ...],
            "daily_breakdown": [{"date": "01-08", "count": 3, "avg": 75}, ...],
        }
    """
    data = load_scores()
    scores = data.get("scores", [])
    detailed = data.get("detailed_scores", [])

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    week_start_str = week_start.strftime("%Y-%m-%d")
    week_end_str = week_end.strftime("%Y-%m-%d")

    # 이번 주 점수 필터링
    week_scores = [s for s in scores if week_start_str <= s.get("date", "") <= week_end_str]

    if not week_scores:
        return {
            "period": f"{week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')}",
            "total_practices": 0,
            "message": "이번 주 연습 기록이 없습니다."
        }

    # 기본 통계
    total = len(week_scores)
    avg = sum(s.get("score", 0) for s in week_scores) / total

    # 유형별 통계
    type_scores = {}
    for s in week_scores:
        t = s.get("type", "기타")
        if t not in type_scores:
            type_scores[t] = []
        type_scores[t].append(s.get("score", 0))

    type_avgs = {t: sum(scores)/len(scores) for t, scores in type_scores.items()}
    best_area = max(type_avgs, key=type_avgs.get) if type_avgs else ""
    weak_area = min(type_avgs, key=type_avgs.get) if type_avgs else ""

    # 지난주 대비 성장
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)
    last_week_scores = [s for s in scores
                        if last_week_start.strftime("%Y-%m-%d") <= s.get("date", "") <= last_week_end.strftime("%Y-%m-%d")]
    last_avg = sum(s.get("score", 0) for s in last_week_scores) / len(last_week_scores) if last_week_scores else 0
    improvement = avg - last_avg

    # 일별 breakdown
    daily = {}
    for s in week_scores:
        d = s.get("date", "")
        if d not in daily:
            daily[d] = {"count": 0, "scores": []}
        daily[d]["count"] += 1
        daily[d]["scores"].append(s.get("score", 0))

    daily_breakdown = []
    for i in range(7):
        d = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        if d in daily:
            daily_breakdown.append({
                "date": d[-5:],
                "count": daily[d]["count"],
                "avg": round(sum(daily[d]["scores"]) / len(daily[d]["scores"]), 1)
            })
        else:
            daily_breakdown.append({"date": d[-5:], "count": 0, "avg": 0})

    # 추천 사항 생성
    recommendations = []
    if weak_area:
        recommendations.append(f"**{weak_area}** 영역 집중 연습 필요")

    # 세부 점수에서 약한 항목 찾기
    week_detailed = [d for d in detailed if week_start_str <= d.get("date", "") <= week_end_str]
    if week_detailed:
        all_items = {}
        for entry in week_detailed:
            for key, score in entry.get("scores", {}).items():
                if key not in all_items:
                    all_items[key] = []
                all_items[key].append(score)

        item_avgs = {k: sum(v)/len(v) for k, v in all_items.items()}
        if item_avgs:
            weakest_item = min(item_avgs, key=item_avgs.get)
            # 항목 이름 찾기
            for cat in EVALUATION_CATEGORIES.values():
                if weakest_item in cat["items"]:
                    item_name = cat["items"][weakest_item]["name"]
                    recommendations.append(f"**{item_name}** 항목 개선 필요 (평균 {item_avgs[weakest_item]:.0f}점)")
                    break

    if total < 10:
        recommendations.append("연습량을 늘려보세요 (주 10회 이상 권장)")

    return {
        "period": f"{week_start.strftime('%m/%d')} ~ {week_end.strftime('%m/%d')}",
        "total_practices": total,
        "avg_score": round(avg, 1),
        "best_area": best_area,
        "weak_area": weak_area,
        "improvement": round(improvement, 1),
        "daily_breakdown": daily_breakdown,
        "recommendations": recommendations,
        "type_breakdown": {t: {"count": len(s), "avg": round(sum(s)/len(s), 1)} for t, s in type_scores.items()},
    }


def get_goal_progress() -> Dict:
    """
    목표 달성률 계산

    Returns:
        {
            "weekly": {"goal": 10, "current": 7, "percent": 70},
            "monthly": {"goal": 40, "current": 25, "percent": 62.5},
            "score": {"goal": 80, "current_avg": 73, "gap": 7},
        }
    """
    goals = load_goals()
    data = load_scores()
    scores = data.get("scores", [])

    today = datetime.now().date()

    # 이번 주 연습 수
    week_start = today - timedelta(days=today.weekday())
    week_scores = [s for s in scores if s.get("date", "") >= week_start.strftime("%Y-%m-%d")]
    weekly_count = len(week_scores)

    # 이번 달 연습 수
    month_start = today.replace(day=1)
    month_scores = [s for s in scores if s.get("date", "") >= month_start.strftime("%Y-%m-%d")]
    monthly_count = len(month_scores)

    # 최근 점수 평균
    recent_scores = [s.get("score", 0) for s in scores[-10:]] if scores else []
    current_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0

    return {
        "weekly": {
            "goal": goals.get("weekly_goal", 10),
            "current": weekly_count,
            "percent": min(100, (weekly_count / goals.get("weekly_goal", 10)) * 100) if goals.get("weekly_goal", 10) > 0 else 0,
        },
        "monthly": {
            "goal": goals.get("monthly_goal", 40),
            "current": monthly_count,
            "percent": min(100, (monthly_count / goals.get("monthly_goal", 40)) * 100) if goals.get("monthly_goal", 40) > 0 else 0,
        },
        "score": {
            "goal": goals.get("target_score", 80),
            "current_avg": round(current_avg, 1),
            "gap": round(goals.get("target_score", 80) - current_avg, 1),
        },
    }
