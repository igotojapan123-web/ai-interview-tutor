# benchmark_service.py
# FlyReady Lab - Benchmarking Service for User Goals, Progress Tracking, and Gamification

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import statistics
import math

from logging_config import get_logger
from score_aggregator import (
    _load_data,
    _anonymize_user_id,
    get_all_scores,
    get_statistics,
    get_passing_average,
    calculate_percentile,
    get_score_distribution,
    get_weekly_ranking,
    get_monthly_ranking,
    SCORE_CATEGORIES,
    PASSING_AVERAGES,
    DATA_DIR,
)

# Logger setup
logger = get_logger(__name__)

# ======================
# Constants and Configuration
# ======================

# Data file paths
USER_GOALS_FILE = DATA_DIR / "user_goals.json"
USER_ACHIEVEMENTS_FILE = DATA_DIR / "user_achievements.json"

# Badge definitions (Korean)
BADGES: Dict[str, Dict[str, Any]] = {
    "첫 면접": {
        "id": "first_interview",
        "name": "첫 면접",
        "description": "첫 번째 모의 면접을 완료하셨습니다!",
        "icon": "star",
        "condition": "complete_first_interview",
    },
    "연속 3일": {
        "id": "streak_3",
        "name": "연속 3일",
        "description": "3일 연속으로 연습하셨습니다!",
        "icon": "fire",
        "condition": "streak_3_days",
    },
    "연속 7일": {
        "id": "streak_7",
        "name": "연속 7일",
        "description": "7일 연속으로 연습하셨습니다! 대단해요!",
        "icon": "trophy",
        "condition": "streak_7_days",
    },
    "상위 10%": {
        "id": "top_10_percent",
        "name": "상위 10%",
        "description": "상위 10% 백분위에 도달하셨습니다!",
        "icon": "medal",
        "condition": "percentile_90",
    },
    "상위 5%": {
        "id": "top_5_percent",
        "name": "상위 5%",
        "description": "상위 5% 백분위에 도달하셨습니다! 최고예요!",
        "icon": "crown",
        "condition": "percentile_95",
    },
    "합격선 돌파": {
        "id": "passing_score",
        "name": "합격선 돌파",
        "description": "합격 평균 점수를 넘으셨습니다!",
        "icon": "check-circle",
        "condition": "above_passing",
    },
    "음성 마스터": {
        "id": "voice_master",
        "name": "음성 마스터",
        "description": "음성 점수 90점 이상을 달성하셨습니다!",
        "icon": "microphone",
        "condition": "voice_score_90",
    },
    "내용 마스터": {
        "id": "content_master",
        "name": "내용 마스터",
        "description": "내용 점수 90점 이상을 달성하셨습니다!",
        "icon": "book",
        "condition": "content_score_90",
    },
    "완벽한 면접": {
        "id": "perfect_interview",
        "name": "완벽한 면접",
        "description": "종합 점수 90점 이상을 달성하셨습니다! 완벽해요!",
        "icon": "gem",
        "condition": "total_score_90",
    },
}


# ======================
# Data Management Functions
# ======================

def _ensure_data_dir() -> None:
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_goals() -> Dict:
    """
    Load user goals data from JSON file.

    Returns:
        Dictionary containing all user goals
    """
    _ensure_data_dir()

    if USER_GOALS_FILE.exists():
        try:
            with open(USER_GOALS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"Loaded goals for {len(data)} users")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading goals data: {e}")

    return {}


def _save_goals(data: Dict) -> bool:
    """
    Save user goals data to JSON file.

    Args:
        data: Dictionary containing all user goals

    Returns:
        True if successful, False otherwise
    """
    _ensure_data_dir()

    try:
        with open(USER_GOALS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Saved goals for {len(data)} users")
        return True
    except Exception as e:
        logger.error(f"Error saving goals data: {e}")
        return False


def _load_achievements() -> Dict:
    """
    Load user achievements data from JSON file.

    Returns:
        Dictionary containing all user achievements
    """
    _ensure_data_dir()

    if USER_ACHIEVEMENTS_FILE.exists():
        try:
            with open(USER_ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"Loaded achievements for {len(data)} users")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading achievements data: {e}")

    return {}


def _save_achievements(data: Dict) -> bool:
    """
    Save user achievements data to JSON file.

    Args:
        data: Dictionary containing all user achievements

    Returns:
        True if successful, False otherwise
    """
    _ensure_data_dir()

    try:
        with open(USER_ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Saved achievements for {len(data)} users")
        return True
    except Exception as e:
        logger.error(f"Error saving achievements data: {e}")
        return False


def _get_user_records(user_id: str) -> List[Dict]:
    """
    Get all score records for a specific user.

    Args:
        user_id: User identifier

    Returns:
        List of user's score records sorted by timestamp (newest first)
    """
    try:
        anonymous_id = _anonymize_user_id(user_id)
        data = _load_data()
        records = data.get("records", [])

        user_records = [r for r in records if r.get("user_id") == anonymous_id]

        # Sort by timestamp descending
        user_records.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )

        logger.debug(f"Found {len(user_records)} records for user {anonymous_id[:8]}")
        return user_records

    except Exception as e:
        logger.error(f"Error getting user records: {e}")
        return []


# ======================
# User Profile & Goals Functions
# ======================

def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Get user's practice history and stats.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with user profile information:
        - total_practices: Total number of practice sessions
        - first_practice_date: Date of first practice
        - last_practice_date: Date of most recent practice
        - avg_scores: Average scores by category
        - best_scores: Best scores by category
        - preferred_airline: Most practiced airline
        - practice_days: Number of unique days practiced
    """
    try:
        records = _get_user_records(user_id)

        if not records:
            logger.debug(f"No records found for user profile")
            return {
                "total_practices": 0,
                "first_practice_date": None,
                "last_practice_date": None,
                "avg_scores": {},
                "best_scores": {},
                "preferred_airline": None,
                "practice_days": 0,
            }

        # Calculate statistics
        scores_by_category: Dict[str, List[float]] = {cat: [] for cat in SCORE_CATEGORIES}
        airline_counts: Dict[str, int] = {}
        practice_dates: set = set()

        for record in records:
            # Collect scores
            for category in SCORE_CATEGORIES:
                score = record.get("scores", {}).get(category)
                if score is not None:
                    scores_by_category[category].append(score)

            # Count airlines
            airline = record.get("airline", "")
            if airline:
                airline_counts[airline] = airline_counts.get(airline, 0) + 1

            # Track practice dates
            timestamp = record.get("timestamp", "")
            if timestamp:
                try:
                    date = datetime.fromisoformat(timestamp).date()
                    practice_dates.add(date)
                except (ValueError, TypeError):
                    pass

        # Calculate averages and best scores
        avg_scores = {}
        best_scores = {}
        for category, scores in scores_by_category.items():
            if scores:
                avg_scores[category] = round(statistics.mean(scores), 1)
                best_scores[category] = round(max(scores), 1)

        # Determine preferred airline
        preferred_airline = max(airline_counts.keys(), key=lambda x: airline_counts[x]) if airline_counts else None

        # Get date range
        timestamps = [r.get("timestamp", "") for r in records if r.get("timestamp")]
        first_date = min(timestamps) if timestamps else None
        last_date = max(timestamps) if timestamps else None

        profile = {
            "total_practices": len(records),
            "first_practice_date": first_date,
            "last_practice_date": last_date,
            "avg_scores": avg_scores,
            "best_scores": best_scores,
            "preferred_airline": preferred_airline,
            "practice_days": len(practice_dates),
        }

        logger.info(f"Generated profile for user with {len(records)} practices")
        return profile

    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return {
            "total_practices": 0,
            "first_practice_date": None,
            "last_practice_date": None,
            "avg_scores": {},
            "best_scores": {},
            "preferred_airline": None,
            "practice_days": 0,
        }


def set_goal(
    user_id: str,
    target_airline: str,
    target_score: int,
    deadline_days: int
) -> bool:
    """
    Set a practice goal for the user.

    Args:
        user_id: User identifier
        target_airline: Target airline name
        target_score: Target score to achieve (0-100)
        deadline_days: Number of days to achieve the goal

    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate inputs
        if not 0 <= target_score <= 100:
            logger.warning(f"Invalid target score: {target_score}")
            return False

        if deadline_days <= 0:
            logger.warning(f"Invalid deadline days: {deadline_days}")
            return False

        anonymous_id = _anonymize_user_id(user_id)
        goals = _load_goals()

        # Create or update goal
        goals[anonymous_id] = {
            "target_airline": target_airline,
            "target_score": target_score,
            "deadline_days": deadline_days,
            "start_date": datetime.now().isoformat(),
            "deadline_date": (datetime.now() + timedelta(days=deadline_days)).isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        if _save_goals(goals):
            logger.info(f"Set goal for user: airline={target_airline}, score={target_score}, days={deadline_days}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error setting goal: {e}")
        return False


def get_goal_progress(user_id: str) -> Dict[str, Any]:
    """
    Calculate progress toward user's goal.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with goal progress information:
        - has_goal: Whether user has an active goal
        - target_airline: Target airline
        - target_score: Target score
        - current_score: Current average score
        - progress_percent: Percentage progress toward goal
        - days_remaining: Days remaining until deadline
        - days_elapsed: Days since goal was set
        - on_track: Whether user is on track to meet goal
    """
    try:
        anonymous_id = _anonymize_user_id(user_id)
        goals = _load_goals()

        if anonymous_id not in goals:
            return {"has_goal": False}

        goal = goals[anonymous_id]
        target_airline = goal.get("target_airline", "")
        target_score = goal.get("target_score", 0)

        # Parse dates
        start_date = datetime.fromisoformat(goal.get("start_date", datetime.now().isoformat()))
        deadline_date = datetime.fromisoformat(goal.get("deadline_date", datetime.now().isoformat()))
        now = datetime.now()

        days_elapsed = (now - start_date).days
        days_remaining = max(0, (deadline_date - now).days)
        total_days = goal.get("deadline_days", 1)

        # Get current score
        profile = get_user_profile(user_id)
        current_score = profile.get("avg_scores", {}).get("종합점수", 0)

        # Get starting score (from records before goal was set)
        records = _get_user_records(user_id)
        records_before_goal = [
            r for r in records
            if r.get("timestamp", "") < goal.get("start_date", "")
        ]

        if records_before_goal:
            starting_scores = [
                r.get("scores", {}).get("종합점수", 0)
                for r in records_before_goal
                if r.get("scores", {}).get("종합점수") is not None
            ]
            starting_score = statistics.mean(starting_scores) if starting_scores else 0
        else:
            starting_score = 0

        # Calculate progress
        score_needed = max(0, target_score - starting_score)
        score_gained = max(0, current_score - starting_score)
        progress_percent = min(100, (score_gained / score_needed * 100)) if score_needed > 0 else 100

        # Determine if on track
        time_progress = days_elapsed / total_days if total_days > 0 else 1
        on_track = progress_percent >= (time_progress * 100) if days_remaining > 0 else current_score >= target_score

        result = {
            "has_goal": True,
            "target_airline": target_airline,
            "target_score": target_score,
            "current_score": round(current_score, 1),
            "starting_score": round(starting_score, 1),
            "progress_percent": round(progress_percent, 1),
            "days_remaining": days_remaining,
            "days_elapsed": days_elapsed,
            "total_days": total_days,
            "on_track": on_track,
            "goal_achieved": current_score >= target_score,
        }

        logger.debug(f"Goal progress: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting goal progress: {e}")
        return {"has_goal": False}


def get_recommended_daily_practice(user_id: str) -> Dict[str, Any]:
    """
    Suggest practice frequency to reach goal.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with practice recommendations:
        - has_goal: Whether user has an active goal
        - recommended_sessions_per_day: Recommended practice sessions
        - current_avg_sessions_per_day: Current practice frequency
        - improvement_rate_needed: Daily score improvement needed
        - message: Human-readable recommendation message
    """
    try:
        progress = get_goal_progress(user_id)

        if not progress.get("has_goal"):
            return {
                "has_goal": False,
                "message": "목표가 설정되지 않았습니다. 목표를 먼저 설정해주세요.",
            }

        profile = get_user_profile(user_id)
        days_remaining = progress.get("days_remaining", 0)
        target_score = progress.get("target_score", 0)
        current_score = progress.get("current_score", 0)

        # Calculate current practice frequency
        total_practices = profile.get("total_practices", 0)
        practice_days = profile.get("practice_days", 1)
        current_avg_sessions = total_practices / practice_days if practice_days > 0 else 0

        # Calculate needed improvement rate
        score_gap = max(0, target_score - current_score)
        improvement_rate_needed = score_gap / days_remaining if days_remaining > 0 else score_gap

        # Recommend sessions based on improvement needed
        if progress.get("goal_achieved"):
            recommended_sessions = 1  # Maintenance mode
            message = "축하합니다! 목표를 달성했습니다! 꾸준히 연습하여 실력을 유지하세요."
        elif days_remaining == 0:
            recommended_sessions = 3
            message = "마감일입니다! 마지막까지 최선을 다해보세요!"
        elif improvement_rate_needed > 2:
            recommended_sessions = 3
            message = f"목표 달성을 위해 하루 3회 이상 집중 연습이 필요합니다. 매일 {improvement_rate_needed:.1f}점씩 향상해야 합니다."
        elif improvement_rate_needed > 1:
            recommended_sessions = 2
            message = f"목표 달성을 위해 하루 2회 연습을 권장합니다. 매일 {improvement_rate_needed:.1f}점씩 향상하면 됩니다."
        elif improvement_rate_needed > 0.5:
            recommended_sessions = 1
            message = f"꾸준히 하루 1회 연습하면 목표를 달성할 수 있습니다."
        else:
            recommended_sessions = 1
            message = "목표 달성에 순조롭습니다. 현재 페이스를 유지하세요!"

        result = {
            "has_goal": True,
            "recommended_sessions_per_day": recommended_sessions,
            "current_avg_sessions_per_day": round(current_avg_sessions, 1),
            "improvement_rate_needed": round(improvement_rate_needed, 2),
            "days_remaining": days_remaining,
            "score_gap": round(score_gap, 1),
            "message": message,
        }

        logger.debug(f"Daily practice recommendation: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting daily practice recommendation: {e}")
        return {
            "has_goal": False,
            "message": "추천을 생성하는 중 오류가 발생했습니다.",
        }


# ======================
# Comparison & Analysis Functions
# ======================

def compare_with_peers(user_id: str, airline: str) -> Dict[str, Any]:
    """
    Compare user's performance with other users preparing for the same airline.

    Args:
        user_id: User identifier
        airline: Airline name to filter peers

    Returns:
        Dictionary with peer comparison:
        - user_avg: User's average scores
        - peer_avg: Average scores of all users for this airline
        - user_percentile: User's percentile for each category
        - total_peers: Number of peers preparing for same airline
        - comparison: Category-wise comparison (above/below/equal)
    """
    try:
        profile = get_user_profile(user_id)
        user_avg = profile.get("avg_scores", {})

        # Get peer statistics
        peer_stats = {}
        total_peers = 0

        for category in SCORE_CATEGORIES:
            stats = get_statistics(airline=airline, category=category)
            if stats:
                peer_stats[category] = stats.get("mean", 0)
                total_peers = max(total_peers, stats.get("count", 0))

        # Calculate percentiles
        percentiles = {}
        comparison = {}

        for category in SCORE_CATEGORIES:
            user_score = user_avg.get(category, 0)
            if user_score > 0:
                percentiles[category] = calculate_percentile(user_score, category, airline)

                peer_score = peer_stats.get(category, 0)
                if user_score > peer_score + 2:
                    comparison[category] = "above"
                elif user_score < peer_score - 2:
                    comparison[category] = "below"
                else:
                    comparison[category] = "equal"

        result = {
            "user_avg": user_avg,
            "peer_avg": peer_stats,
            "user_percentile": percentiles,
            "total_peers": total_peers,
            "comparison": comparison,
            "airline": airline,
        }

        logger.debug(f"Peer comparison for airline {airline}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error comparing with peers: {e}")
        return {
            "user_avg": {},
            "peer_avg": {},
            "user_percentile": {},
            "total_peers": 0,
            "comparison": {},
            "airline": airline,
        }


def get_strength_weakness(user_id: str) -> Dict[str, Any]:
    """
    Identify user's strong and weak categories.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with strength/weakness analysis:
        - strengths: List of strong categories (above avg)
        - weaknesses: List of weak categories (below avg)
        - strongest: Best performing category
        - weakest: Worst performing category
        - scores_by_category: All category scores
        - recommendations: Improvement recommendations
    """
    try:
        profile = get_user_profile(user_id)
        avg_scores = profile.get("avg_scores", {})

        if not avg_scores:
            return {
                "strengths": [],
                "weaknesses": [],
                "strongest": None,
                "weakest": None,
                "scores_by_category": {},
                "recommendations": ["더 많은 연습이 필요합니다."],
            }

        # Exclude 종합점수 from individual category analysis
        category_scores = {k: v for k, v in avg_scores.items() if k != "종합점수"}

        if not category_scores:
            return {
                "strengths": [],
                "weaknesses": [],
                "strongest": None,
                "weakest": None,
                "scores_by_category": avg_scores,
                "recommendations": ["더 많은 연습이 필요합니다."],
            }

        # Calculate overall average
        overall_avg = statistics.mean(category_scores.values())

        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []

        for category, score in category_scores.items():
            if score > overall_avg + 3:
                strengths.append(category)
            elif score < overall_avg - 3:
                weaknesses.append(category)

        # Find strongest and weakest
        strongest = max(category_scores.keys(), key=lambda x: category_scores[x])
        weakest = min(category_scores.keys(), key=lambda x: category_scores[x])

        # Generate recommendations
        recommendations = []
        if weaknesses:
            for weak_cat in weaknesses:
                if weak_cat == "음성점수":
                    recommendations.append("발음과 억양 연습에 집중해보세요. 거울을 보며 말하는 연습이 도움됩니다.")
                elif weak_cat == "내용점수":
                    recommendations.append("답변 구조화 연습이 필요합니다. STAR 기법을 활용해보세요.")
                elif weak_cat == "감정점수":
                    recommendations.append("표정과 감정 표현 연습이 필요합니다. 미소를 유지하며 자신감 있게 답변해보세요.")
        else:
            recommendations.append("모든 영역에서 균형 잡힌 실력을 보여주고 있습니다!")

        result = {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "strongest": strongest,
            "weakest": weakest,
            "scores_by_category": avg_scores,
            "overall_average": round(overall_avg, 1),
            "recommendations": recommendations,
        }

        logger.debug(f"Strength/weakness analysis: {result}")
        return result

    except Exception as e:
        logger.error(f"Error analyzing strengths/weaknesses: {e}")
        return {
            "strengths": [],
            "weaknesses": [],
            "strongest": None,
            "weakest": None,
            "scores_by_category": {},
            "recommendations": ["분석 중 오류가 발생했습니다."],
        }


def get_improvement_trend(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Calculate improvement rate over time.

    Args:
        user_id: User identifier
        days: Number of days to analyze (default: 30)

    Returns:
        Dictionary with improvement trend:
        - daily_scores: Scores by date
        - improvement_rate: Average daily improvement
        - trend_direction: "improving", "declining", or "stable"
        - total_improvement: Total score change over period
        - data_points: Number of practice sessions in period
    """
    try:
        records = _get_user_records(user_id)

        if not records:
            return {
                "daily_scores": {},
                "improvement_rate": 0,
                "trend_direction": "stable",
                "total_improvement": 0,
                "data_points": 0,
            }

        # Filter records within the time period
        cutoff = datetime.now() - timedelta(days=days)
        recent_records = []

        for record in records:
            try:
                timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                if timestamp >= cutoff:
                    recent_records.append(record)
            except (ValueError, TypeError):
                continue

        if len(recent_records) < 2:
            return {
                "daily_scores": {},
                "improvement_rate": 0,
                "trend_direction": "stable",
                "total_improvement": 0,
                "data_points": len(recent_records),
            }

        # Sort by timestamp ascending
        recent_records.sort(key=lambda x: x.get("timestamp", ""))

        # Aggregate scores by date
        daily_scores: Dict[str, List[float]] = {}
        for record in recent_records:
            try:
                date_str = datetime.fromisoformat(record.get("timestamp", "")).strftime("%Y-%m-%d")
                score = record.get("scores", {}).get("종합점수")
                if score is not None:
                    if date_str not in daily_scores:
                        daily_scores[date_str] = []
                    daily_scores[date_str].append(score)
            except (ValueError, TypeError):
                continue

        # Calculate daily averages
        daily_averages = {
            date: round(statistics.mean(scores), 1)
            for date, scores in daily_scores.items()
        }

        if len(daily_averages) < 2:
            return {
                "daily_scores": daily_averages,
                "improvement_rate": 0,
                "trend_direction": "stable",
                "total_improvement": 0,
                "data_points": len(recent_records),
            }

        # Calculate trend
        sorted_dates = sorted(daily_averages.keys())
        first_score = daily_averages[sorted_dates[0]]
        last_score = daily_averages[sorted_dates[-1]]
        total_improvement = last_score - first_score

        # Calculate improvement rate (linear regression slope)
        n = len(sorted_dates)
        x_values = list(range(n))
        y_values = [daily_averages[d] for d in sorted_dates]

        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        improvement_rate = numerator / denominator if denominator != 0 else 0

        # Determine trend direction
        if improvement_rate > 0.5:
            trend_direction = "improving"
        elif improvement_rate < -0.5:
            trend_direction = "declining"
        else:
            trend_direction = "stable"

        result = {
            "daily_scores": daily_averages,
            "improvement_rate": round(improvement_rate, 2),
            "trend_direction": trend_direction,
            "total_improvement": round(total_improvement, 1),
            "data_points": len(recent_records),
            "period_days": days,
        }

        logger.debug(f"Improvement trend over {days} days: {result}")
        return result

    except Exception as e:
        logger.error(f"Error calculating improvement trend: {e}")
        return {
            "daily_scores": {},
            "improvement_rate": 0,
            "trend_direction": "stable",
            "total_improvement": 0,
            "data_points": 0,
        }


def predict_passing_probability(user_id: str, airline: str) -> Dict[str, Any]:
    """
    Estimate chance of passing based on current scores.

    Args:
        user_id: User identifier
        airline: Target airline

    Returns:
        Dictionary with passing probability:
        - probability: Estimated probability (0-100)
        - confidence: Confidence level of prediction
        - factors: Factors affecting prediction
        - current_vs_passing: Score comparison
        - message: Human-readable assessment
    """
    try:
        profile = get_user_profile(user_id)
        avg_scores = profile.get("avg_scores", {})

        if not avg_scores:
            return {
                "probability": 0,
                "confidence": "low",
                "factors": {},
                "current_vs_passing": {},
                "message": "충분한 연습 데이터가 없습니다. 더 많은 연습이 필요합니다.",
            }

        # Get passing scores for the airline
        passing_scores = PASSING_AVERAGES.get(airline, PASSING_AVERAGES.get("제주항공", {}))

        # Calculate score differences
        factors = {}
        total_weighted_diff = 0
        weights = {"음성점수": 0.3, "내용점수": 0.4, "감정점수": 0.2, "종합점수": 0.1}

        current_vs_passing = {}

        for category in SCORE_CATEGORIES:
            user_score = avg_scores.get(category, 0)
            passing_score = passing_scores.get(category, 75)
            diff = user_score - passing_score

            current_vs_passing[category] = {
                "user": round(user_score, 1),
                "passing": round(passing_score, 1),
                "diff": round(diff, 1),
            }

            weight = weights.get(category, 0.25)
            total_weighted_diff += diff * weight

            if diff >= 5:
                factors[category] = "excellent"
            elif diff >= 0:
                factors[category] = "passing"
            elif diff >= -5:
                factors[category] = "close"
            else:
                factors[category] = "needs_work"

        # Calculate probability using sigmoid function
        # Map weighted diff to probability
        probability = 100 / (1 + math.exp(-0.2 * total_weighted_diff))
        probability = max(5, min(95, probability))  # Clamp between 5 and 95

        # Determine confidence based on data quantity
        total_practices = profile.get("total_practices", 0)
        if total_practices >= 20:
            confidence = "high"
        elif total_practices >= 10:
            confidence = "medium"
        else:
            confidence = "low"

        # Generate message
        if probability >= 80:
            message = f"합격 가능성이 매우 높습니다! 현재 실력을 유지하세요."
        elif probability >= 60:
            message = f"합격 가능성이 좋습니다. 약간의 추가 연습으로 더 높은 확률을 달성할 수 있습니다."
        elif probability >= 40:
            message = f"합격 가능성이 중간 수준입니다. 꾸준한 연습이 필요합니다."
        elif probability >= 20:
            message = f"합격을 위해 더 많은 준비가 필요합니다. 약점 영역에 집중하세요."
        else:
            message = f"합격까지 많은 준비가 필요합니다. 기초부터 차근차근 연습해보세요."

        result = {
            "probability": round(probability, 1),
            "confidence": confidence,
            "factors": factors,
            "current_vs_passing": current_vs_passing,
            "message": message,
            "airline": airline,
            "total_practices": total_practices,
        }

        logger.debug(f"Passing probability for {airline}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error predicting passing probability: {e}")
        return {
            "probability": 0,
            "confidence": "low",
            "factors": {},
            "current_vs_passing": {},
            "message": "예측 중 오류가 발생했습니다.",
        }


# ======================
# Charts Data Generation Functions
# ======================

def get_percentile_gauge_data(
    user_score: float,
    airline: str,
    category: str
) -> Dict[str, Any]:
    """
    Generate data for a gauge chart showing user's percentile.

    Args:
        user_score: User's score
        airline: Airline name
        category: Score category

    Returns:
        Dictionary formatted for Plotly gauge chart:
        - value: Percentile value
        - reference: Passing score for reference
        - ranges: Color ranges for gauge
        - title: Chart title
    """
    try:
        percentile = calculate_percentile(user_score, category, airline)
        passing_score = get_passing_average(airline, category)

        # If percentile calculation failed, estimate based on score
        if percentile < 0:
            # Rough estimation
            percentile = min(100, max(0, (user_score - 50) * 2))

        result = {
            "value": round(percentile, 1),
            "reference": round(passing_score, 1),
            "user_score": round(user_score, 1),
            "ranges": {
                "low": {"min": 0, "max": 25, "color": "#ff6b6b"},
                "medium_low": {"min": 25, "max": 50, "color": "#ffd93d"},
                "medium_high": {"min": 50, "max": 75, "color": "#6bcb77"},
                "high": {"min": 75, "max": 100, "color": "#4d96ff"},
            },
            "title": f"{category} 백분위",
            "subtitle": f"{airline} 지원자 중",
        }

        logger.debug(f"Gauge data for {category}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error generating gauge data: {e}")
        return {
            "value": 50,
            "reference": 75,
            "user_score": user_score,
            "ranges": {},
            "title": category,
            "subtitle": "",
        }


def get_comparison_chart_data(
    user_scores: Dict[str, float],
    airline: str
) -> Dict[str, Any]:
    """
    Generate data for bar chart comparing user vs passing average.

    Args:
        user_scores: User's scores by category
        airline: Airline name

    Returns:
        Dictionary formatted for Plotly bar chart:
        - categories: List of category names
        - user_values: User's score values
        - passing_values: Passing average values
        - differences: Difference between user and passing
    """
    try:
        categories = []
        user_values = []
        passing_values = []
        differences = []

        for category in SCORE_CATEGORIES:
            user_score = user_scores.get(category)
            if user_score is not None:
                passing_score = get_passing_average(airline, category)

                categories.append(category)
                user_values.append(round(user_score, 1))
                passing_values.append(round(passing_score, 1))
                differences.append(round(user_score - passing_score, 1))

        result = {
            "categories": categories,
            "user_values": user_values,
            "passing_values": passing_values,
            "differences": differences,
            "airline": airline,
            "chart_title": f"{airline} 합격선 대비 점수 비교",
        }

        logger.debug(f"Comparison chart data for {airline}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error generating comparison chart data: {e}")
        return {
            "categories": [],
            "user_values": [],
            "passing_values": [],
            "differences": [],
            "airline": airline,
            "chart_title": "",
        }


def get_trend_chart_data(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    Generate data for line chart showing score trend over time.

    Args:
        user_id: User identifier
        days: Number of days to include (default: 30)

    Returns:
        Dictionary formatted for Plotly line chart:
        - dates: List of dates
        - scores_by_category: Scores for each category over time
        - trend_line: Linear trend values
    """
    try:
        trend_data = get_improvement_trend(user_id, days)
        daily_scores = trend_data.get("daily_scores", {})

        if not daily_scores:
            return {
                "dates": [],
                "scores_by_category": {},
                "trend_line": [],
                "chart_title": "점수 추이",
            }

        # Get all records for detailed category breakdown
        records = _get_user_records(user_id)
        cutoff = datetime.now() - timedelta(days=days)

        # Organize scores by date and category
        scores_by_date: Dict[str, Dict[str, List[float]]] = {}

        for record in records:
            try:
                timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                if timestamp < cutoff:
                    continue

                date_str = timestamp.strftime("%Y-%m-%d")
                if date_str not in scores_by_date:
                    scores_by_date[date_str] = {cat: [] for cat in SCORE_CATEGORIES}

                for category in SCORE_CATEGORIES:
                    score = record.get("scores", {}).get(category)
                    if score is not None:
                        scores_by_date[date_str][category].append(score)
            except (ValueError, TypeError):
                continue

        # Calculate daily averages by category
        sorted_dates = sorted(scores_by_date.keys())
        scores_by_category: Dict[str, List[Optional[float]]] = {cat: [] for cat in SCORE_CATEGORIES}

        for date in sorted_dates:
            for category in SCORE_CATEGORIES:
                scores = scores_by_date[date].get(category, [])
                if scores:
                    scores_by_category[category].append(round(statistics.mean(scores), 1))
                else:
                    scores_by_category[category].append(None)

        # Calculate trend line for total score
        total_scores = scores_by_category.get("종합점수", [])
        valid_scores = [(i, s) for i, s in enumerate(total_scores) if s is not None]

        trend_line = []
        if len(valid_scores) >= 2:
            x_vals = [v[0] for v in valid_scores]
            y_vals = [v[1] for v in valid_scores]

            x_mean = statistics.mean(x_vals)
            y_mean = statistics.mean(y_vals)

            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
            denominator = sum((x - x_mean) ** 2 for x in x_vals)

            slope = numerator / denominator if denominator != 0 else 0
            intercept = y_mean - slope * x_mean

            trend_line = [round(slope * i + intercept, 1) for i in range(len(sorted_dates))]

        result = {
            "dates": sorted_dates,
            "scores_by_category": scores_by_category,
            "trend_line": trend_line,
            "chart_title": f"최근 {days}일 점수 추이",
            "improvement_rate": trend_data.get("improvement_rate", 0),
            "trend_direction": trend_data.get("trend_direction", "stable"),
        }

        logger.debug(f"Trend chart data: {len(sorted_dates)} data points")
        return result

    except Exception as e:
        logger.error(f"Error generating trend chart data: {e}")
        return {
            "dates": [],
            "scores_by_category": {},
            "trend_line": [],
            "chart_title": "점수 추이",
        }


def get_distribution_chart_data(
    airline: str,
    category: str,
    user_score: float
) -> Dict[str, Any]:
    """
    Generate data for histogram with user position highlighted.

    Args:
        airline: Airline name
        category: Score category
        user_score: User's score to highlight

    Returns:
        Dictionary formatted for Plotly histogram:
        - distribution: Score distribution data
        - user_position: User's score position
        - passing_line: Passing score line position
        - percentile: User's percentile
    """
    try:
        distribution = get_score_distribution(category, airline=airline, bins=10)
        passing_score = get_passing_average(airline, category)
        percentile = calculate_percentile(user_score, category, airline)

        # Determine user's bin
        bin_size = 10
        user_bin_index = min(int(user_score / bin_size), 9)
        user_bin = f"{user_bin_index * bin_size}-{(user_bin_index + 1) * bin_size}"

        result = {
            "distribution": distribution,
            "user_score": round(user_score, 1),
            "user_bin": user_bin,
            "passing_score": round(passing_score, 1),
            "percentile": round(percentile, 1) if percentile >= 0 else None,
            "chart_title": f"{airline} - {category} 분포",
            "total_count": sum(distribution.values()) if distribution else 0,
        }

        logger.debug(f"Distribution chart data for {category}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error generating distribution chart data: {e}")
        return {
            "distribution": {},
            "user_score": user_score,
            "user_bin": "",
            "passing_score": 0,
            "percentile": None,
            "chart_title": "",
            "total_count": 0,
        }


# ======================
# Ranking & Competition Functions
# ======================

def get_leaderboard(
    airline: Optional[str] = None,
    period: str = "weekly",
    limit: int = 10
) -> List[Dict]:
    """
    Get leaderboard data.

    Args:
        airline: Filter by airline (optional)
        period: "weekly", "monthly", or "all_time"
        limit: Maximum number of results (default: 10)

    Returns:
        List of leaderboard entries with rank, user_id, score, airline
    """
    try:
        if period == "weekly":
            ranking = get_weekly_ranking(airline=airline, limit=limit)
        elif period == "monthly":
            ranking = get_monthly_ranking(airline=airline, limit=limit)
        else:
            # All-time ranking
            data = _load_data()
            records = data.get("records", [])

            if airline:
                records = [r for r in records if r.get("airline") == airline]

            # Aggregate by user
            user_best: Dict[str, Dict] = {}
            for record in records:
                user_id = record.get("user_id", "")
                total_score = record.get("scores", {}).get("종합점수", 0)

                if user_id not in user_best or total_score > user_best[user_id].get("scores", {}).get("종합점수", 0):
                    user_best[user_id] = record

            # Sort and rank
            sorted_users = sorted(
                user_best.values(),
                key=lambda x: x.get("scores", {}).get("종합점수", 0),
                reverse=True
            )[:limit]

            ranking = []
            for rank, record in enumerate(sorted_users, 1):
                ranking.append({
                    "rank": rank,
                    "user_id": record.get("user_id", "")[:8] + "...",
                    "airline": record.get("airline", ""),
                    "score": record.get("scores", {}).get("종합점수", 0),
                    "timestamp": record.get("timestamp", ""),
                })

        logger.debug(f"Leaderboard ({period}, airline={airline}): {len(ranking)} entries")
        return ranking

    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return []


def get_user_leaderboard_position(
    user_id: str,
    airline: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get user's position on various leaderboards.

    Args:
        user_id: User identifier
        airline: Filter by airline (optional)

    Returns:
        Dictionary with user's positions:
        - weekly_position: Weekly rank
        - monthly_position: Monthly rank
        - all_time_position: All-time rank
        - total_users_weekly: Total weekly participants
        - total_users_monthly: Total monthly participants
        - total_users_all_time: Total all-time participants
    """
    try:
        anonymous_id = _anonymize_user_id(user_id)

        # Helper function to find position
        def find_position(ranking: List[Dict]) -> Optional[int]:
            for entry in ranking:
                # Match first 8 chars of truncated ID
                if entry.get("user_id", "").startswith(anonymous_id[:8]):
                    return entry.get("rank")
            return None

        # Get all rankings
        weekly_ranking = get_leaderboard(airline=airline, period="weekly", limit=1000)
        monthly_ranking = get_leaderboard(airline=airline, period="monthly", limit=1000)
        all_time_ranking = get_leaderboard(airline=airline, period="all_time", limit=1000)

        result = {
            "weekly_position": find_position(weekly_ranking),
            "monthly_position": find_position(monthly_ranking),
            "all_time_position": find_position(all_time_ranking),
            "total_users_weekly": len(weekly_ranking),
            "total_users_monthly": len(monthly_ranking),
            "total_users_all_time": len(all_time_ranking),
            "airline": airline,
        }

        logger.debug(f"User leaderboard position: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting user leaderboard position: {e}")
        return {
            "weekly_position": None,
            "monthly_position": None,
            "all_time_position": None,
            "total_users_weekly": 0,
            "total_users_monthly": 0,
            "total_users_all_time": 0,
            "airline": airline,
        }


def get_competing_users_count(airline: str) -> Dict[str, int]:
    """
    Get count of users preparing for the same airline.

    Args:
        airline: Airline name

    Returns:
        Dictionary with user counts:
        - total: Total unique users
        - active_weekly: Users active this week
        - active_monthly: Users active this month
    """
    try:
        data = _load_data()
        records = data.get("records", [])

        # Filter by airline
        airline_records = [r for r in records if r.get("airline") == airline]

        # Count unique users
        all_users = set(r.get("user_id", "") for r in airline_records)

        # Count active users
        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        weekly_users = set()
        monthly_users = set()

        for record in airline_records:
            try:
                timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                user_id = record.get("user_id", "")

                if timestamp >= week_ago:
                    weekly_users.add(user_id)
                if timestamp >= month_ago:
                    monthly_users.add(user_id)
            except (ValueError, TypeError):
                continue

        result = {
            "total": len(all_users),
            "active_weekly": len(weekly_users),
            "active_monthly": len(monthly_users),
            "airline": airline,
        }

        logger.debug(f"Competing users for {airline}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting competing users count: {e}")
        return {
            "total": 0,
            "active_weekly": 0,
            "active_monthly": 0,
            "airline": airline,
        }


# ======================
# Motivation & Gamification Functions
# ======================

def get_achievement_badges(user_id: str) -> Dict[str, Any]:
    """
    Get all badges user has earned.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with earned badges:
        - earned: List of earned badge info
        - not_earned: List of badges not yet earned
        - total_earned: Count of earned badges
        - total_available: Count of all badges
    """
    try:
        anonymous_id = _anonymize_user_id(user_id)
        achievements = _load_achievements()

        user_achievements = achievements.get(anonymous_id, {})
        earned_badges = user_achievements.get("badges", [])

        earned = []
        not_earned = []

        for badge_name, badge_info in BADGES.items():
            badge_data = {
                "name": badge_name,
                "id": badge_info["id"],
                "description": badge_info["description"],
                "icon": badge_info["icon"],
            }

            if badge_info["id"] in earned_badges:
                # Add earned date if available
                earned_date = user_achievements.get("badge_dates", {}).get(badge_info["id"])
                badge_data["earned_date"] = earned_date
                earned.append(badge_data)
            else:
                not_earned.append(badge_data)

        result = {
            "earned": earned,
            "not_earned": not_earned,
            "total_earned": len(earned),
            "total_available": len(BADGES),
            "completion_percent": round(len(earned) / len(BADGES) * 100, 1) if BADGES else 0,
        }

        logger.debug(f"Achievement badges: {result['total_earned']}/{result['total_available']} earned")
        return result

    except Exception as e:
        logger.error(f"Error getting achievement badges: {e}")
        return {
            "earned": [],
            "not_earned": list(BADGES.values()),
            "total_earned": 0,
            "total_available": len(BADGES),
            "completion_percent": 0,
        }


def check_new_achievements(
    user_id: str,
    latest_scores: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Check if latest practice unlocked new achievements.

    Args:
        user_id: User identifier
        latest_scores: Scores from the latest practice session

    Returns:
        List of newly earned badges
    """
    try:
        anonymous_id = _anonymize_user_id(user_id)
        achievements = _load_achievements()

        if anonymous_id not in achievements:
            achievements[anonymous_id] = {"badges": [], "badge_dates": {}, "streak": 0}

        user_data = achievements[anonymous_id]
        current_badges = set(user_data.get("badges", []))
        new_badges = []

        # Get user profile for additional checks
        profile = get_user_profile(user_id)
        streak_info = get_streak_info(user_id)

        # Check each badge condition
        # 1. First interview
        if "first_interview" not in current_badges:
            if profile.get("total_practices", 0) >= 1:
                new_badges.append(BADGES["첫 면접"])
                current_badges.add("first_interview")

        # 2. Streak badges
        current_streak = streak_info.get("current_streak", 0)
        if "streak_3" not in current_badges and current_streak >= 3:
            new_badges.append(BADGES["연속 3일"])
            current_badges.add("streak_3")

        if "streak_7" not in current_badges and current_streak >= 7:
            new_badges.append(BADGES["연속 7일"])
            current_badges.add("streak_7")

        # 3. Percentile badges
        total_score = latest_scores.get("종합점수", 0)
        if total_score > 0:
            percentile = calculate_percentile(total_score, "종합점수")

            if "top_10_percent" not in current_badges and percentile >= 90:
                new_badges.append(BADGES["상위 10%"])
                current_badges.add("top_10_percent")

            if "top_5_percent" not in current_badges and percentile >= 95:
                new_badges.append(BADGES["상위 5%"])
                current_badges.add("top_5_percent")

        # 4. Passing score badge
        if "passing_score" not in current_badges:
            # Check against any airline's passing score
            for airline, passing_scores in PASSING_AVERAGES.items():
                if total_score >= passing_scores.get("종합점수", 100):
                    new_badges.append(BADGES["합격선 돌파"])
                    current_badges.add("passing_score")
                    break

        # 5. Master badges
        voice_score = latest_scores.get("음성점수", 0)
        content_score = latest_scores.get("내용점수", 0)

        if "voice_master" not in current_badges and voice_score >= 90:
            new_badges.append(BADGES["음성 마스터"])
            current_badges.add("voice_master")

        if "content_master" not in current_badges and content_score >= 90:
            new_badges.append(BADGES["내용 마스터"])
            current_badges.add("content_master")

        if "perfect_interview" not in current_badges and total_score >= 90:
            new_badges.append(BADGES["완벽한 면접"])
            current_badges.add("perfect_interview")

        # Save new achievements
        if new_badges:
            user_data["badges"] = list(current_badges)
            for badge in new_badges:
                user_data["badge_dates"][badge["id"]] = datetime.now().isoformat()

            achievements[anonymous_id] = user_data
            _save_achievements(achievements)

            logger.info(f"User earned {len(new_badges)} new badges")

        return [
            {
                "name": badge["name"],
                "description": badge["description"],
                "icon": badge["icon"],
            }
            for badge in new_badges
        ]

    except Exception as e:
        logger.error(f"Error checking new achievements: {e}")
        return []


def get_streak_info(user_id: str) -> Dict[str, Any]:
    """
    Get practice streak information.

    Args:
        user_id: User identifier

    Returns:
        Dictionary with streak info:
        - current_streak: Current consecutive days
        - longest_streak: Longest streak achieved
        - last_practice_date: Date of last practice
        - streak_active: Whether streak is still active
    """
    try:
        records = _get_user_records(user_id)

        if not records:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_practice_date": None,
                "streak_active": False,
            }

        # Get unique practice dates
        practice_dates = set()
        for record in records:
            try:
                timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                practice_dates.add(timestamp.date())
            except (ValueError, TypeError):
                continue

        if not practice_dates:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_practice_date": None,
                "streak_active": False,
            }

        sorted_dates = sorted(practice_dates, reverse=True)
        last_practice = sorted_dates[0]
        today = datetime.now().date()

        # Check if streak is active (practiced today or yesterday)
        days_since_last = (today - last_practice).days
        streak_active = days_since_last <= 1

        # Calculate current streak
        current_streak = 0
        if streak_active:
            check_date = last_practice
            for date in sorted_dates:
                if date == check_date:
                    current_streak += 1
                    check_date = date - timedelta(days=1)
                elif date < check_date:
                    break

        # Calculate longest streak
        longest_streak = 0
        streak = 0
        sorted_dates_asc = sorted(practice_dates)

        for i, date in enumerate(sorted_dates_asc):
            if i == 0:
                streak = 1
            else:
                if (date - sorted_dates_asc[i - 1]).days == 1:
                    streak += 1
                else:
                    longest_streak = max(longest_streak, streak)
                    streak = 1

        longest_streak = max(longest_streak, streak, current_streak)

        result = {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_practice_date": last_practice.isoformat(),
            "streak_active": streak_active,
            "days_since_last_practice": days_since_last,
        }

        logger.debug(f"Streak info: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting streak info: {e}")
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "last_practice_date": None,
            "streak_active": False,
        }


# ======================
# Module Initialization
# ======================

def initialize() -> bool:
    """
    Initialize the benchmark service module.
    Ensures data files exist.

    Returns:
        True if successful
    """
    try:
        _ensure_data_dir()

        if not USER_GOALS_FILE.exists():
            _save_goals({})
            logger.info("Created new user goals file")

        if not USER_ACHIEVEMENTS_FILE.exists():
            _save_achievements({})
            logger.info("Created new user achievements file")

        logger.info("Benchmark service module initialized")
        return True

    except Exception as e:
        logger.error(f"Error initializing benchmark service: {e}")
        return False


# Initialize on import
initialize()
