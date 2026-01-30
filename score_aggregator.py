# score_aggregator.py
# FlyReady Lab - Score Aggregation Module for Anonymous Statistics and Rankings

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import statistics

from logging_config import get_logger

# Logger setup
logger = get_logger(__name__)

# ======================
# Constants and Configuration
# ======================

# Data file path
DATA_DIR = Path(__file__).parent / "data"
SCORE_AGGREGATE_FILE = DATA_DIR / "score_aggregate.json"

# Score categories
SCORE_CATEGORIES = ["음성점수", "내용점수", "감정점수", "종합점수"]

# Airline types
AIRLINE_TYPES = {
    "FSC": ["대한항공", "아시아나"],
    "LCC": ["제주항공", "진에어", "티웨이", "에어부산", "이스타항공"]
}

# ======================
# Benchmark Data (Hardcoded Passing Averages)
# ======================

PASSING_AVERAGES: Dict[str, Dict[str, float]] = {
    # FSC (Full Service Carrier) - Higher standards
    "대한항공": {
        "음성점수": 82.0,
        "내용점수": 85.0,
        "감정점수": 80.0,
        "종합점수": 83.0,
    },
    "아시아나": {
        "음성점수": 80.0,
        "내용점수": 83.0,
        "감정점수": 78.0,
        "종합점수": 81.0,
    },
    # LCC (Low Cost Carrier) - Moderate standards
    "제주항공": {
        "음성점수": 75.0,
        "내용점수": 78.0,
        "감정점수": 73.0,
        "종합점수": 76.0,
    },
    "진에어": {
        "음성점수": 74.0,
        "내용점수": 77.0,
        "감정점수": 72.0,
        "종합점수": 75.0,
    },
    "티웨이": {
        "음성점수": 73.0,
        "내용점수": 76.0,
        "감정점수": 71.0,
        "종합점수": 74.0,
    },
    "에어부산": {
        "음성점수": 74.0,
        "내용점수": 77.0,
        "감정점수": 72.0,
        "종합점수": 75.0,
    },
    "이스타항공": {
        "음성점수": 72.0,
        "내용점수": 75.0,
        "감정점수": 70.0,
        "종합점수": 73.0,
    },
}

# Default passing averages for unknown airlines
DEFAULT_PASSING_AVERAGE: Dict[str, float] = {
    "음성점수": 75.0,
    "내용점수": 78.0,
    "감정점수": 73.0,
    "종합점수": 76.0,
}


# ======================
# Data Management Functions
# ======================

def _ensure_data_dir() -> None:
    """Ensure data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_data() -> Dict:
    """
    Load score aggregate data from JSON file.

    Returns:
        Dictionary containing all score records
    """
    _ensure_data_dir()

    if SCORE_AGGREGATE_FILE.exists():
        try:
            with open(SCORE_AGGREGATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data.get('records', []))} score records")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading score data: {e}")

    return {"records": [], "last_updated": None}


def _save_data(data: Dict) -> bool:
    """
    Save score aggregate data to JSON file.

    Args:
        data: Dictionary containing all score records

    Returns:
        True if successful, False otherwise
    """
    _ensure_data_dir()

    try:
        data["last_updated"] = datetime.now().isoformat()
        with open(SCORE_AGGREGATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug(f"Saved {len(data.get('records', []))} score records")
        return True
    except Exception as e:
        logger.error(f"Error saving score data: {e}")
        return False


def _anonymize_user_id(user_id: str) -> str:
    """
    Create anonymous hash of user ID.

    Args:
        user_id: Original user identifier

    Returns:
        Anonymized hash string
    """
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


# ======================
# Score Collection Functions
# ======================

def add_score(
    user_id: str,
    airline: str,
    question_type: str,
    scores: Dict[str, float],
    anonymous: bool = True
) -> bool:
    """
    Add a new score record.

    Args:
        user_id: User identifier
        airline: Target airline name
        question_type: Type of question (e.g., 자기소개, 지원동기, etc.)
        scores: Dictionary with score categories as keys
            Expected keys: 음성점수, 내용점수, 감정점수, 종합점수
        anonymous: Whether to anonymize user_id (default: True)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate scores
        for category in SCORE_CATEGORIES:
            if category in scores:
                score = scores[category]
                if not isinstance(score, (int, float)) or score < 0 or score > 100:
                    logger.warning(f"Invalid score for {category}: {score}")
                    scores[category] = max(0, min(100, float(score)))

        # Create record
        record = {
            "user_id": _anonymize_user_id(user_id) if anonymous else user_id,
            "airline": airline,
            "question_type": question_type,
            "scores": {k: float(v) for k, v in scores.items() if k in SCORE_CATEGORIES},
            "timestamp": datetime.now().isoformat(),
            "week": datetime.now().isocalendar()[1],
            "month": datetime.now().month,
            "year": datetime.now().year,
        }

        # Load, append, and save
        data = _load_data()
        data["records"].append(record)

        if _save_data(data):
            logger.info(f"Added score record for airline={airline}, type={question_type}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error adding score: {e}")
        return False


def get_all_scores(
    airline: Optional[str] = None,
    question_type: Optional[str] = None
) -> List[Dict]:
    """
    Get filtered scores.

    Args:
        airline: Filter by airline (optional)
        question_type: Filter by question type (optional)

    Returns:
        List of score records matching filters
    """
    try:
        data = _load_data()
        records = data.get("records", [])

        if airline:
            records = [r for r in records if r.get("airline") == airline]

        if question_type:
            records = [r for r in records if r.get("question_type") == question_type]

        logger.debug(f"Retrieved {len(records)} scores (airline={airline}, type={question_type})")
        return records

    except Exception as e:
        logger.error(f"Error getting scores: {e}")
        return []


def get_score_count() -> int:
    """
    Get total number of recorded scores.

    Returns:
        Total count of score records
    """
    try:
        data = _load_data()
        count = len(data.get("records", []))
        logger.debug(f"Total score count: {count}")
        return count
    except Exception as e:
        logger.error(f"Error getting score count: {e}")
        return 0


# ======================
# Statistics Functions
# ======================

def calculate_percentile(
    score: float,
    category: str,
    airline: Optional[str] = None
) -> float:
    """
    Calculate user's percentile for a given score.

    Args:
        score: User's score
        category: Score category (음성점수, 내용점수, 감정점수, 종합점수)
        airline: Filter by airline (optional)

    Returns:
        Percentile (0-100), or -1 if insufficient data
    """
    try:
        if category not in SCORE_CATEGORIES:
            logger.warning(f"Invalid category: {category}")
            return -1.0

        records = get_all_scores(airline=airline)

        if not records:
            logger.debug("No records for percentile calculation")
            return -1.0

        # Extract scores for the category
        all_scores = [
            r["scores"].get(category)
            for r in records
            if r.get("scores", {}).get(category) is not None
        ]

        if len(all_scores) < 5:  # Need minimum records for meaningful percentile
            logger.debug(f"Insufficient data for percentile: {len(all_scores)} records")
            return -1.0

        # Calculate percentile
        count_below = sum(1 for s in all_scores if s < score)
        percentile = (count_below / len(all_scores)) * 100

        logger.debug(f"Percentile for {score} in {category}: {percentile:.1f}%")
        return round(percentile, 1)

    except Exception as e:
        logger.error(f"Error calculating percentile: {e}")
        return -1.0


def get_statistics(
    airline: Optional[str] = None,
    category: str = "종합점수"
) -> Dict[str, float]:
    """
    Get statistical summary for scores.

    Args:
        airline: Filter by airline (optional)
        category: Score category (default: 종합점수)

    Returns:
        Dictionary with mean, median, std, min, max, count
        Empty dict if insufficient data
    """
    try:
        if category not in SCORE_CATEGORIES:
            logger.warning(f"Invalid category: {category}")
            return {}

        records = get_all_scores(airline=airline)

        if not records:
            return {}

        # Extract scores
        all_scores = [
            r["scores"].get(category)
            for r in records
            if r.get("scores", {}).get(category) is not None
        ]

        if len(all_scores) < 2:
            return {}

        stats = {
            "mean": round(statistics.mean(all_scores), 2),
            "median": round(statistics.median(all_scores), 2),
            "std": round(statistics.stdev(all_scores), 2) if len(all_scores) > 1 else 0.0,
            "min": round(min(all_scores), 2),
            "max": round(max(all_scores), 2),
            "count": len(all_scores),
        }

        logger.debug(f"Statistics for {category} (airline={airline}): {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return {}


def get_score_distribution(
    category: str,
    airline: Optional[str] = None,
    bins: int = 10
) -> Dict[str, int]:
    """
    Get score distribution for charts.

    Args:
        category: Score category
        airline: Filter by airline (optional)
        bins: Number of bins for distribution (default: 10)

    Returns:
        Dictionary with bin ranges as keys and counts as values
        e.g., {"0-10": 5, "10-20": 12, ...}
    """
    try:
        if category not in SCORE_CATEGORIES:
            logger.warning(f"Invalid category: {category}")
            return {}

        records = get_all_scores(airline=airline)

        if not records:
            return {}

        # Extract scores
        all_scores = [
            r["scores"].get(category)
            for r in records
            if r.get("scores", {}).get(category) is not None
        ]

        if not all_scores:
            return {}

        # Create bins
        bin_size = 100 / bins
        distribution = {}

        for i in range(bins):
            lower = int(i * bin_size)
            upper = int((i + 1) * bin_size)
            bin_label = f"{lower}-{upper}"
            distribution[bin_label] = 0

        # Count scores in each bin
        for score in all_scores:
            bin_index = min(int(score / bin_size), bins - 1)
            lower = int(bin_index * bin_size)
            upper = int((bin_index + 1) * bin_size)
            bin_label = f"{lower}-{upper}"
            distribution[bin_label] += 1

        logger.debug(f"Distribution for {category}: {distribution}")
        return distribution

    except Exception as e:
        logger.error(f"Error getting distribution: {e}")
        return {}


# ======================
# Ranking Functions
# ======================

def _get_records_in_period(
    start_date: datetime,
    end_date: datetime,
    airline: Optional[str] = None
) -> List[Dict]:
    """
    Get records within a date range.

    Args:
        start_date: Period start
        end_date: Period end
        airline: Filter by airline (optional)

    Returns:
        List of records within the period
    """
    records = get_all_scores(airline=airline)

    filtered = []
    for record in records:
        try:
            timestamp = datetime.fromisoformat(record.get("timestamp", ""))
            if start_date <= timestamp <= end_date:
                filtered.append(record)
        except (ValueError, TypeError):
            continue

    return filtered


def _aggregate_user_scores(records: List[Dict]) -> Dict[str, Dict]:
    """
    Aggregate scores by user, keeping best score per user.

    Args:
        records: List of score records

    Returns:
        Dictionary with user_id as key and best record as value
    """
    user_best = {}

    for record in records:
        user_id = record.get("user_id", "")
        total_score = record.get("scores", {}).get("종합점수", 0)

        if user_id not in user_best or total_score > user_best[user_id].get("scores", {}).get("종합점수", 0):
            user_best[user_id] = record

    return user_best


def get_weekly_ranking(
    airline: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Get weekly top scores.

    Args:
        airline: Filter by airline (optional)
        limit: Maximum number of results (default: 10)

    Returns:
        List of top score records with rank
    """
    try:
        now = datetime.now()
        # Get start of current week (Monday)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        records = _get_records_in_period(start_of_week, end_of_week, airline)

        if not records:
            logger.debug("No records for weekly ranking")
            return []

        # Aggregate by user (best score per user)
        user_best = _aggregate_user_scores(records)

        # Sort by total score
        sorted_users = sorted(
            user_best.values(),
            key=lambda x: x.get("scores", {}).get("종합점수", 0),
            reverse=True
        )[:limit]

        # Add rank
        ranking = []
        for rank, record in enumerate(sorted_users, 1):
            ranking.append({
                "rank": rank,
                "user_id": record.get("user_id", "")[:8] + "...",  # Truncated for privacy
                "airline": record.get("airline", ""),
                "score": record.get("scores", {}).get("종합점수", 0),
                "timestamp": record.get("timestamp", ""),
            })

        logger.debug(f"Weekly ranking: {len(ranking)} entries")
        return ranking

    except Exception as e:
        logger.error(f"Error getting weekly ranking: {e}")
        return []


def get_monthly_ranking(
    airline: Optional[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Get monthly top scores.

    Args:
        airline: Filter by airline (optional)
        limit: Maximum number of results (default: 10)

    Returns:
        List of top score records with rank
    """
    try:
        now = datetime.now()
        # Get start of current month
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Get end of current month
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1) - timedelta(seconds=1)

        records = _get_records_in_period(start_of_month, end_of_month, airline)

        if not records:
            logger.debug("No records for monthly ranking")
            return []

        # Aggregate by user (best score per user)
        user_best = _aggregate_user_scores(records)

        # Sort by total score
        sorted_users = sorted(
            user_best.values(),
            key=lambda x: x.get("scores", {}).get("종합점수", 0),
            reverse=True
        )[:limit]

        # Add rank
        ranking = []
        for rank, record in enumerate(sorted_users, 1):
            ranking.append({
                "rank": rank,
                "user_id": record.get("user_id", "")[:8] + "...",  # Truncated for privacy
                "airline": record.get("airline", ""),
                "score": record.get("scores", {}).get("종합점수", 0),
                "timestamp": record.get("timestamp", ""),
            })

        logger.debug(f"Monthly ranking: {len(ranking)} entries")
        return ranking

    except Exception as e:
        logger.error(f"Error getting monthly ranking: {e}")
        return []


def get_user_rank(
    user_id: str,
    airline: Optional[str] = None
) -> Dict[str, any]:
    """
    Get user's current rank.

    Args:
        user_id: User identifier
        airline: Filter by airline (optional)

    Returns:
        Dictionary with weekly_rank, monthly_rank, total_users, percentile
    """
    try:
        anonymous_id = _anonymize_user_id(user_id)

        # Get weekly ranking
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        weekly_records = _get_records_in_period(start_of_week, end_of_week, airline)
        weekly_user_best = _aggregate_user_scores(weekly_records)

        # Get monthly ranking
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1) - timedelta(seconds=1)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1) - timedelta(seconds=1)

        monthly_records = _get_records_in_period(start_of_month, end_of_month, airline)
        monthly_user_best = _aggregate_user_scores(monthly_records)

        # Sort and find user's rank
        weekly_sorted = sorted(
            weekly_user_best.items(),
            key=lambda x: x[1].get("scores", {}).get("종합점수", 0),
            reverse=True
        )
        monthly_sorted = sorted(
            monthly_user_best.items(),
            key=lambda x: x[1].get("scores", {}).get("종합점수", 0),
            reverse=True
        )

        weekly_rank = None
        for rank, (uid, _) in enumerate(weekly_sorted, 1):
            if uid == anonymous_id:
                weekly_rank = rank
                break

        monthly_rank = None
        for rank, (uid, _) in enumerate(monthly_sorted, 1):
            if uid == anonymous_id:
                monthly_rank = rank
                break

        # Get user's best score for percentile
        user_best_score = None
        if anonymous_id in monthly_user_best:
            user_best_score = monthly_user_best[anonymous_id].get("scores", {}).get("종합점수")

        percentile = -1.0
        if user_best_score is not None:
            percentile = calculate_percentile(user_best_score, "종합점수", airline)

        result = {
            "weekly_rank": weekly_rank,
            "weekly_total_users": len(weekly_user_best),
            "monthly_rank": monthly_rank,
            "monthly_total_users": len(monthly_user_best),
            "percentile": percentile,
            "user_best_score": user_best_score,
        }

        logger.debug(f"User rank for {anonymous_id[:8]}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting user rank: {e}")
        return {
            "weekly_rank": None,
            "weekly_total_users": 0,
            "monthly_rank": None,
            "monthly_total_users": 0,
            "percentile": -1.0,
            "user_best_score": None,
        }


# ======================
# Benchmark Functions
# ======================

def get_passing_average(airline: str, category: str) -> float:
    """
    Get passing score for a specific airline and category.

    Args:
        airline: Airline name
        category: Score category

    Returns:
        Passing average score
    """
    try:
        if airline in PASSING_AVERAGES:
            return PASSING_AVERAGES[airline].get(category, DEFAULT_PASSING_AVERAGE.get(category, 75.0))

        logger.debug(f"Using default passing average for airline: {airline}")
        return DEFAULT_PASSING_AVERAGE.get(category, 75.0)

    except Exception as e:
        logger.error(f"Error getting passing average: {e}")
        return 75.0


def compare_to_passing(user_scores: Dict[str, float], airline: str) -> Dict[str, Dict]:
    """
    Compare user scores to passing averages.

    Args:
        user_scores: Dictionary with score categories as keys
        airline: Target airline name

    Returns:
        Dictionary with comparison results for each category
        e.g., {
            "음성점수": {"user": 78, "passing": 82, "diff": -4, "status": "below"},
            ...
        }
    """
    try:
        results = {}

        for category in SCORE_CATEGORIES:
            user_score = user_scores.get(category)
            if user_score is None:
                continue

            passing_score = get_passing_average(airline, category)
            diff = user_score - passing_score

            if diff >= 5:
                status = "excellent"  # 5점 이상 상회
            elif diff >= 0:
                status = "passing"    # 합격선 이상
            elif diff >= -5:
                status = "close"      # 합격선 근접
            else:
                status = "below"      # 합격선 미달

            results[category] = {
                "user": round(user_score, 1),
                "passing": round(passing_score, 1),
                "diff": round(diff, 1),
                "status": status,
            }

        logger.debug(f"Comparison to passing for {airline}: {results}")
        return results

    except Exception as e:
        logger.error(f"Error comparing to passing: {e}")
        return {}


def get_airline_type(airline: str) -> str:
    """
    Get airline type (FSC or LCC).

    Args:
        airline: Airline name

    Returns:
        "FSC", "LCC", or "Unknown"
    """
    for airline_type, airlines in AIRLINE_TYPES.items():
        if airline in airlines:
            return airline_type
    return "Unknown"


def get_all_passing_averages() -> Dict[str, Dict[str, float]]:
    """
    Get all passing averages for all airlines.

    Returns:
        Copy of PASSING_AVERAGES dictionary
    """
    return PASSING_AVERAGES.copy()


# ======================
# Utility Functions
# ======================

def get_score_summary(airline: Optional[str] = None) -> Dict:
    """
    Get comprehensive score summary.

    Args:
        airline: Filter by airline (optional)

    Returns:
        Dictionary with overall statistics, distributions, and rankings
    """
    try:
        summary = {
            "total_records": get_score_count(),
            "statistics": {},
            "weekly_ranking": get_weekly_ranking(airline, limit=5),
            "monthly_ranking": get_monthly_ranking(airline, limit=5),
        }

        for category in SCORE_CATEGORIES:
            stats = get_statistics(airline, category)
            if stats:
                summary["statistics"][category] = stats

        logger.debug(f"Score summary generated for airline={airline}")
        return summary

    except Exception as e:
        logger.error(f"Error generating score summary: {e}")
        return {}


def clear_old_records(days: int = 365) -> int:
    """
    Remove records older than specified days.

    Args:
        days: Number of days to keep (default: 365)

    Returns:
        Number of records removed
    """
    try:
        data = _load_data()
        records = data.get("records", [])

        cutoff = datetime.now() - timedelta(days=days)

        new_records = []
        removed_count = 0

        for record in records:
            try:
                timestamp = datetime.fromisoformat(record.get("timestamp", ""))
                if timestamp >= cutoff:
                    new_records.append(record)
                else:
                    removed_count += 1
            except (ValueError, TypeError):
                new_records.append(record)  # Keep records with invalid timestamps

        data["records"] = new_records
        _save_data(data)

        logger.info(f"Cleared {removed_count} old records (older than {days} days)")
        return removed_count

    except Exception as e:
        logger.error(f"Error clearing old records: {e}")
        return 0


# ======================
# Module Initialization
# ======================

def initialize() -> bool:
    """
    Initialize the score aggregator module.
    Ensures data directory and file exist.

    Returns:
        True if successful
    """
    try:
        _ensure_data_dir()

        if not SCORE_AGGREGATE_FILE.exists():
            _save_data({"records": [], "last_updated": None})
            logger.info("Created new score aggregate file")

        logger.info("Score aggregator module initialized")
        return True

    except Exception as e:
        logger.error(f"Error initializing score aggregator: {e}")
        return False


# Initialize on import
initialize()
