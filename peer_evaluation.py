# peer_evaluation.py
# FlyReady Lab 멀티플레이어 모의면접 동료 평가 시스템

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import Counter, defaultdict

from logging_config import get_logger

# 로거 설정
logger = get_logger(__name__)

# 데이터 디렉토리 설정
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

EVALUATIONS_FILE = DATA_DIR / "peer_evaluations.json"
REACTIONS_FILE = DATA_DIR / "peer_reactions.json"

# ========================================
# 평가 기준 정의
# ========================================

EVALUATION_CRITERIA = {
    "content": {
        "name": "답변 내용",
        "description": "답변의 내용적 측면을 평가합니다.",
        "subcriteria": {
            "specificity": {
                "name": "구체성",
                "description": "답변이 구체적인 예시와 경험을 포함하는지 평가합니다.",
                "weight": 0.35
            },
            "relevance": {
                "name": "관련성",
                "description": "답변이 질문의 의도에 맞게 작성되었는지 평가합니다.",
                "weight": 0.35
            },
            "logic": {
                "name": "논리성",
                "description": "답변의 논리적 흐름과 일관성을 평가합니다.",
                "weight": 0.30
            }
        },
        "max_score": 25
    },
    "delivery": {
        "name": "전달력",
        "description": "답변을 전달하는 방식을 평가합니다.",
        "subcriteria": {
            "voice": {
                "name": "목소리",
                "description": "발음, 속도, 크기가 적절한지 평가합니다.",
                "weight": 0.35
            },
            "confidence": {
                "name": "자신감",
                "description": "자신감 있는 태도로 답변하는지 평가합니다.",
                "weight": 0.35
            },
            "eye_contact": {
                "name": "시선처리",
                "description": "시선이 자연스럽고 적절한지 평가합니다.",
                "weight": 0.30
            }
        },
        "max_score": 25
    },
    "attitude": {
        "name": "태도",
        "description": "면접 태도를 평가합니다.",
        "subcriteria": {
            "service_mind": {
                "name": "서비스 마인드",
                "description": "서비스 정신이 느껴지는지 평가합니다.",
                "weight": 0.35
            },
            "enthusiasm": {
                "name": "열정",
                "description": "열정과 의지가 느껴지는지 평가합니다.",
                "weight": 0.35
            },
            "authenticity": {
                "name": "진정성",
                "description": "진솔하고 진정성 있게 답변하는지 평가합니다.",
                "weight": 0.30
            }
        },
        "max_score": 25
    },
    "structure": {
        "name": "구조",
        "description": "답변의 구조적 측면을 평가합니다.",
        "subcriteria": {
            "opening": {
                "name": "두괄식",
                "description": "핵심 메시지를 먼저 전달하는지 평가합니다.",
                "weight": 0.35
            },
            "star_method": {
                "name": "STAR 기법",
                "description": "상황-과제-행동-결과 구조로 답변하는지 평가합니다.",
                "weight": 0.35
            },
            "conclusion": {
                "name": "결론",
                "description": "명확한 결론으로 마무리하는지 평가합니다.",
                "weight": 0.30
            }
        },
        "max_score": 25
    }
}

# 점수 가중치
SCORE_WEIGHTS = {
    "ai": 0.6,
    "peer": 0.4
}

# 빠른 반응 정의
REACTIONS = {
    "like": {
        "emoji": "👍",
        "name": "좋아요",
        "description": "좋은 답변이에요"
    },
    "amazing": {
        "emoji": "👏",
        "name": "대단해요",
        "description": "정말 인상적인 답변이에요"
    },
    "confident": {
        "emoji": "💪",
        "name": "자신감 있어요",
        "description": "자신감이 느껴져요"
    },
    "creative": {
        "emoji": "💡",
        "name": "창의적이에요",
        "description": "창의적인 답변이에요"
    },
    "empathy": {
        "emoji": "❤️",
        "name": "공감해요",
        "description": "공감이 가는 답변이에요"
    }
}

# 평가자 배지
EVALUATOR_BADGES = {
    "helpful_evaluator": {
        "name": "도움이 되는 평가자",
        "description": "10회 이상 도움이 되는 평가를 작성했습니다.",
        "requirement": 10
    },
    "consistent_evaluator": {
        "name": "일관된 평가자",
        "description": "평가 편차가 적고 일관성 있는 평가를 합니다.",
        "requirement": 0.8  # 신뢰도 80% 이상
    },
    "active_evaluator": {
        "name": "적극적인 평가자",
        "description": "50회 이상 동료 평가에 참여했습니다.",
        "requirement": 50
    },
    "master_evaluator": {
        "name": "마스터 평가자",
        "description": "100회 이상 평가하고 신뢰도 90% 이상입니다.",
        "requirement": {"count": 100, "reliability": 0.9}
    }
}


# ========================================
# 데이터 관리
# ========================================

def _load_evaluations() -> List[Dict[str, Any]]:
    """평가 데이터 로드"""
    try:
        if EVALUATIONS_FILE.exists():
            with open(EVALUATIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(f"평가 데이터 로드 실패: {e}")
    return []


def _save_evaluations(evaluations: List[Dict[str, Any]]) -> None:
    """평가 데이터 저장"""
    with open(EVALUATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(evaluations, f, ensure_ascii=False, indent=2)


def _load_reactions() -> List[Dict[str, Any]]:
    """반응 데이터 로드"""
    try:
        if REACTIONS_FILE.exists():
            with open(REACTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(f"반응 데이터 로드 실패: {e}")
    return []


def _save_reactions(reactions: List[Dict[str, Any]]) -> None:
    """반응 데이터 저장"""
    with open(REACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(reactions, f, ensure_ascii=False, indent=2)


# ========================================
# 평가 제출 및 검증
# ========================================

def get_evaluation_template() -> Dict[str, Any]:
    """평가 양식 템플릿 반환

    Returns:
        빈 평가 양식 템플릿
    """
    template = {
        "scores": {},
        "feedback": "",
        "criteria_info": EVALUATION_CRITERIA
    }

    for category, info in EVALUATION_CRITERIA.items():
        template["scores"][category] = {
            "total": 0,
            "subcriteria": {}
        }
        for sub_key in info["subcriteria"]:
            template["scores"][category]["subcriteria"][sub_key] = 0

    logger.debug("평가 템플릿 생성")
    return template


def can_evaluate(evaluator_id: str, target_id: str, room_id: str) -> Dict[str, Any]:
    """평가 가능 여부 확인

    Args:
        evaluator_id: 평가자 ID
        target_id: 평가 대상 ID
        room_id: 방 ID

    Returns:
        평가 가능 여부 및 이유
    """
    # 자기 자신 평가 불가
    if evaluator_id == target_id:
        logger.debug(f"자기 평가 시도: {evaluator_id}")
        return {
            "can_evaluate": False,
            "reason": "자기 자신은 평가할 수 없습니다."
        }

    # 같은 방 참가 여부 확인 (room_manager에서 확인)
    try:
        from room_manager import get_room
        room = get_room(room_id)

        if not room:
            return {
                "can_evaluate": False,
                "reason": "존재하지 않는 방입니다."
            }

        participant_ids = [p["user_id"] for p in room.get("participants", [])]

        if evaluator_id not in participant_ids:
            return {
                "can_evaluate": False,
                "reason": "해당 방에 참가하지 않은 사용자입니다."
            }

        if target_id not in participant_ids:
            return {
                "can_evaluate": False,
                "reason": "평가 대상이 해당 방에 참가하지 않았습니다."
            }

    except ImportError:
        logger.warning("room_manager 모듈을 불러올 수 없습니다.")

    # 이미 평가했는지 확인
    evaluations = _load_evaluations()
    already_evaluated = any(
        e["evaluator_id"] == evaluator_id and
        e["target_id"] == target_id and
        e["room_id"] == room_id
        for e in evaluations
    )

    if already_evaluated:
        return {
            "can_evaluate": False,
            "reason": "이미 이 참가자를 평가했습니다."
        }

    return {
        "can_evaluate": True,
        "reason": "평가할 수 있습니다."
    }


def submit_peer_evaluation(
    evaluator_id: str,
    target_id: str,
    room_id: str,
    question_idx: int,
    scores: Dict[str, Any],
    feedback: str
) -> Dict[str, Any]:
    """동료 평가 제출

    Args:
        evaluator_id: 평가자 ID
        target_id: 평가 대상 ID
        room_id: 방 ID
        question_idx: 질문 인덱스
        scores: 평가 점수 딕셔너리
        feedback: 피드백 텍스트

    Returns:
        제출된 평가 정보
    """
    # 평가 가능 여부 확인
    check = can_evaluate(evaluator_id, target_id, room_id)
    if not check["can_evaluate"]:
        logger.warning(f"평가 불가: {check['reason']}")
        raise ValueError(check["reason"])

    # 점수 검증
    total_score = 0
    validated_scores = {}

    for category, info in EVALUATION_CRITERIA.items():
        if category not in scores:
            raise ValueError(f"'{info['name']}' 카테고리 점수가 필요합니다.")

        category_score = scores[category]
        max_score = info["max_score"]

        # 총점 또는 하위 항목 점수 확인
        if isinstance(category_score, dict) and "subcriteria" in category_score:
            # 하위 항목별 점수
            sub_total = 0
            validated_scores[category] = {"subcriteria": {}}

            for sub_key, sub_info in info["subcriteria"].items():
                sub_score = category_score["subcriteria"].get(sub_key, 0)
                sub_max = max_score * sub_info["weight"]

                if not 0 <= sub_score <= sub_max:
                    raise ValueError(
                        f"'{sub_info['name']}' 점수는 0~{sub_max:.1f} 사이여야 합니다."
                    )

                validated_scores[category]["subcriteria"][sub_key] = sub_score
                sub_total += sub_score

            validated_scores[category]["total"] = sub_total
            total_score += sub_total
        else:
            # 카테고리 총점만
            cat_score = category_score if isinstance(category_score, (int, float)) else category_score.get("total", 0)

            if not 0 <= cat_score <= max_score:
                raise ValueError(
                    f"'{info['name']}' 점수는 0~{max_score} 사이여야 합니다."
                )

            validated_scores[category] = {"total": cat_score, "subcriteria": {}}
            total_score += cat_score

    # 평가 ID 생성
    evaluation_id = str(uuid.uuid4())[:8]

    evaluation = {
        "evaluation_id": evaluation_id,
        "evaluator_id": evaluator_id,
        "target_id": target_id,
        "room_id": room_id,
        "question_idx": question_idx,
        "scores": validated_scores,
        "total_score": round(total_score, 1),
        "feedback": feedback,
        "created_at": datetime.now().isoformat(),
        "flagged": False,
        "flag_reason": None
    }

    evaluations = _load_evaluations()
    evaluations.append(evaluation)
    _save_evaluations(evaluations)

    logger.info(f"동료 평가 제출: {evaluator_id} -> {target_id} (점수: {total_score})")

    return evaluation


# ========================================
# 평가 조회
# ========================================

def get_evaluations_received(
    user_id: str,
    room_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """받은 평가 조회

    Args:
        user_id: 사용자 ID
        room_id: 방 ID (선택, 특정 방만 조회)

    Returns:
        받은 평가 목록
    """
    evaluations = _load_evaluations()

    received = [e for e in evaluations if e["target_id"] == user_id]

    if room_id:
        received = [e for e in received if e["room_id"] == room_id]

    # 최신순 정렬
    received.sort(key=lambda x: x["created_at"], reverse=True)

    logger.debug(f"받은 평가 조회: {user_id}, {len(received)}개")
    return received


def get_evaluations_given(
    user_id: str,
    room_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """작성한 평가 조회

    Args:
        user_id: 사용자 ID
        room_id: 방 ID (선택, 특정 방만 조회)

    Returns:
        작성한 평가 목록
    """
    evaluations = _load_evaluations()

    given = [e for e in evaluations if e["evaluator_id"] == user_id]

    if room_id:
        given = [e for e in given if e["room_id"] == room_id]

    # 최신순 정렬
    given.sort(key=lambda x: x["created_at"], reverse=True)

    logger.debug(f"작성한 평가 조회: {user_id}, {len(given)}개")
    return given


def get_peer_feedback_summary(user_id: str) -> Dict[str, Any]:
    """동료 피드백 요약

    Args:
        user_id: 사용자 ID

    Returns:
        피드백 요약 정보
    """
    evaluations = get_evaluations_received(user_id)

    if not evaluations:
        return {
            "user_id": user_id,
            "total_evaluations": 0,
            "message": "아직 받은 평가가 없습니다."
        }

    # 카테고리별 평균 점수
    category_scores = defaultdict(list)
    total_scores = []
    all_feedbacks = []

    for e in evaluations:
        total_scores.append(e["total_score"])
        all_feedbacks.append(e.get("feedback", ""))

        for category, score_data in e["scores"].items():
            category_scores[category].append(score_data["total"])

    category_averages = {}
    for category, scores in category_scores.items():
        avg = sum(scores) / len(scores)
        category_averages[category] = {
            "name": EVALUATION_CRITERIA[category]["name"],
            "average": round(avg, 1),
            "max_score": EVALUATION_CRITERIA[category]["max_score"],
            "evaluation_count": len(scores)
        }

    # 가장 높은/낮은 카테고리
    sorted_categories = sorted(
        category_averages.items(),
        key=lambda x: x[1]["average"] / x[1]["max_score"],
        reverse=True
    )

    return {
        "user_id": user_id,
        "total_evaluations": len(evaluations),
        "overall_average": round(sum(total_scores) / len(total_scores), 1),
        "max_possible_score": 100,
        "category_averages": category_averages,
        "strongest_category": sorted_categories[0][0] if sorted_categories else None,
        "weakest_category": sorted_categories[-1][0] if sorted_categories else None,
        "recent_feedbacks": [f for f in all_feedbacks if f][:5]
    }


# ========================================
# 점수 집계
# ========================================

def calculate_peer_score(user_id: str, room_id: str) -> Dict[str, Any]:
    """동료 평가 평균 점수 계산

    Args:
        user_id: 사용자 ID
        room_id: 방 ID

    Returns:
        평균 점수 정보
    """
    evaluations = get_evaluations_received(user_id, room_id)

    if not evaluations:
        return {
            "user_id": user_id,
            "room_id": room_id,
            "peer_score": 0,
            "evaluation_count": 0,
            "message": "동료 평가가 없습니다."
        }

    # 신뢰도 조정된 점수 계산
    adjusted_scores = []

    for e in evaluations:
        # 플래그된 평가는 제외
        if e.get("flagged"):
            continue

        # 평가자 신뢰도 가중치 적용
        evaluator_reliability = calculate_evaluator_reliability(e["evaluator_id"])
        reliability = evaluator_reliability.get("reliability", 1.0)

        adjusted_score = e["total_score"] * reliability
        adjusted_scores.append(adjusted_score)

    if not adjusted_scores:
        return {
            "user_id": user_id,
            "room_id": room_id,
            "peer_score": 0,
            "evaluation_count": 0,
            "message": "유효한 평가가 없습니다."
        }

    average_score = sum(adjusted_scores) / len(adjusted_scores)

    return {
        "user_id": user_id,
        "room_id": room_id,
        "peer_score": round(average_score, 1),
        "raw_average": round(sum(e["total_score"] for e in evaluations if not e.get("flagged")) / len([e for e in evaluations if not e.get("flagged")]), 1),
        "evaluation_count": len(adjusted_scores),
        "total_evaluations": len(evaluations)
    }


def get_combined_score(
    user_id: str,
    room_id: str,
    ai_score: float
) -> Dict[str, Any]:
    """AI와 동료 평가 결합 점수 계산

    Args:
        user_id: 사용자 ID
        room_id: 방 ID
        ai_score: AI 평가 점수 (0-100)

    Returns:
        결합 점수 정보
    """
    peer_result = calculate_peer_score(user_id, room_id)
    peer_score = peer_result.get("peer_score", 0)

    # 가중치 적용
    ai_weight = SCORE_WEIGHTS["ai"]
    peer_weight = SCORE_WEIGHTS["peer"]

    # 동료 평가가 없으면 AI 점수만 사용
    if peer_result.get("evaluation_count", 0) == 0:
        combined = ai_score
        peer_weight_used = 0
        ai_weight_used = 1.0
    else:
        combined = (ai_score * ai_weight) + (peer_score * peer_weight)
        ai_weight_used = ai_weight
        peer_weight_used = peer_weight

    return {
        "user_id": user_id,
        "room_id": room_id,
        "combined_score": round(combined, 1),
        "ai_score": round(ai_score, 1),
        "ai_weight": ai_weight_used,
        "peer_score": round(peer_score, 1),
        "peer_weight": peer_weight_used,
        "peer_evaluation_count": peer_result.get("evaluation_count", 0),
        "score_breakdown": {
            "ai_contribution": round(ai_score * ai_weight_used, 1),
            "peer_contribution": round(peer_score * peer_weight_used, 1)
        }
    }


# ========================================
# 피드백 분석
# ========================================

def analyze_feedback_patterns(user_id: str) -> Dict[str, Any]:
    """받은 피드백 패턴 분석

    Args:
        user_id: 사용자 ID

    Returns:
        피드백 패턴 분석 결과
    """
    evaluations = get_evaluations_received(user_id)

    if len(evaluations) < 3:
        return {
            "user_id": user_id,
            "message": "충분한 피드백이 모이면 패턴을 분석해 드립니다.",
            "evaluations_needed": 3 - len(evaluations)
        }

    # 카테고리별 점수 추이
    category_trends = defaultdict(list)
    for e in sorted(evaluations, key=lambda x: x["created_at"]):
        for category, score_data in e["scores"].items():
            category_trends[category].append({
                "score": score_data["total"],
                "date": e["created_at"][:10]
            })

    # 개선/하락 추세 분석
    trends = {}
    for category, scores in category_trends.items():
        if len(scores) >= 3:
            recent = sum(s["score"] for s in scores[-3:]) / 3
            older = sum(s["score"] for s in scores[:3]) / 3

            if recent > older * 1.1:
                trend = "improving"
                trend_label = "개선 중"
            elif recent < older * 0.9:
                trend = "declining"
                trend_label = "하락 중"
            else:
                trend = "stable"
                trend_label = "유지 중"

            trends[category] = {
                "trend": trend,
                "trend_label": trend_label,
                "recent_average": round(recent, 1),
                "older_average": round(older, 1)
            }

    # 일관되게 높은/낮은 카테고리
    consistent_high = []
    consistent_low = []

    for category, info in EVALUATION_CRITERIA.items():
        scores = [e["scores"][category]["total"] for e in evaluations]
        avg = sum(scores) / len(scores)
        ratio = avg / info["max_score"]

        if ratio >= 0.8:
            consistent_high.append({
                "category": category,
                "name": info["name"],
                "average_ratio": round(ratio, 2)
            })
        elif ratio <= 0.5:
            consistent_low.append({
                "category": category,
                "name": info["name"],
                "average_ratio": round(ratio, 2)
            })

    return {
        "user_id": user_id,
        "total_evaluations": len(evaluations),
        "category_trends": trends,
        "consistent_strengths": consistent_high,
        "consistent_weaknesses": consistent_low,
        "analysis_date": datetime.now().isoformat()
    }


def get_improvement_suggestions_from_peers(user_id: str) -> Dict[str, Any]:
    """동료 피드백에서 개선 제안 추출

    Args:
        user_id: 사용자 ID

    Returns:
        개선 제안 목록
    """
    evaluations = get_evaluations_received(user_id)

    if not evaluations:
        return {
            "user_id": user_id,
            "suggestions": [],
            "message": "아직 받은 평가가 없습니다."
        }

    # 피드백 텍스트 수집
    feedbacks = [e.get("feedback", "") for e in evaluations if e.get("feedback")]

    # 낮은 점수 카테고리 식별
    category_scores = defaultdict(list)
    for e in evaluations:
        for category, score_data in e["scores"].items():
            max_score = EVALUATION_CRITERIA[category]["max_score"]
            ratio = score_data["total"] / max_score
            category_scores[category].append(ratio)

    weak_categories = []
    for category, ratios in category_scores.items():
        avg_ratio = sum(ratios) / len(ratios)
        if avg_ratio < 0.6:
            weak_categories.append({
                "category": category,
                "name": EVALUATION_CRITERIA[category]["name"],
                "average_ratio": round(avg_ratio, 2),
                "suggestion": _generate_improvement_suggestion(category, avg_ratio)
            })

    # 정렬 (가장 개선이 필요한 순)
    weak_categories.sort(key=lambda x: x["average_ratio"])

    return {
        "user_id": user_id,
        "suggestions": weak_categories[:3],  # 상위 3개
        "feedback_excerpts": feedbacks[:5],
        "total_evaluations": len(evaluations)
    }


def _generate_improvement_suggestion(category: str, ratio: float) -> str:
    """카테고리별 개선 제안 생성"""
    suggestions = {
        "content": {
            "low": "답변에 구체적인 경험과 예시를 더 추가해 보세요. STAR 기법을 활용하면 좋습니다.",
            "medium": "답변의 관련성을 높이기 위해 질문의 핵심을 파악하고 그에 맞는 내용을 준비해 보세요."
        },
        "delivery": {
            "low": "발음과 말하는 속도를 연습해 보세요. 녹음해서 들어보면 도움이 됩니다.",
            "medium": "자신감 있게 말하되, 적절한 눈 맞춤을 유지해 보세요."
        },
        "attitude": {
            "low": "서비스 마인드를 보여주는 경험과 가치관을 답변에 녹여보세요.",
            "medium": "열정과 진정성이 느껴지도록 본인만의 이야기를 담아보세요."
        },
        "structure": {
            "low": "두괄식으로 핵심 메시지를 먼저 말하고, 명확한 결론으로 마무리해 보세요.",
            "medium": "STAR 기법(상황-과제-행동-결과)을 적용해 답변을 구조화해 보세요."
        }
    }

    level = "low" if ratio < 0.4 else "medium"
    return suggestions.get(category, {}).get(level, "꾸준히 연습하면 좋아질 거예요!")


def get_common_strengths(user_id: str) -> Dict[str, Any]:
    """동료들이 공통으로 칭찬한 점 추출

    Args:
        user_id: 사용자 ID

    Returns:
        공통 강점 목록
    """
    evaluations = get_evaluations_received(user_id)

    if not evaluations:
        return {
            "user_id": user_id,
            "strengths": [],
            "message": "아직 받은 평가가 없습니다."
        }

    # 높은 점수를 받은 카테고리/하위항목 수집
    high_scores = defaultdict(int)

    for e in evaluations:
        for category, score_data in e["scores"].items():
            max_score = EVALUATION_CRITERIA[category]["max_score"]
            ratio = score_data["total"] / max_score

            if ratio >= 0.8:
                high_scores[category] += 1

            # 하위 항목도 확인
            for sub_key, sub_score in score_data.get("subcriteria", {}).items():
                sub_info = EVALUATION_CRITERIA[category]["subcriteria"].get(sub_key, {})
                sub_max = max_score * sub_info.get("weight", 0.33)

                if sub_max > 0 and sub_score / sub_max >= 0.8:
                    high_scores[f"{category}.{sub_key}"] += 1

    # 가장 많이 칭찬받은 순 정렬
    sorted_strengths = sorted(high_scores.items(), key=lambda x: x[1], reverse=True)

    strengths = []
    for key, count in sorted_strengths[:5]:
        if "." in key:
            cat, sub = key.split(".")
            name = EVALUATION_CRITERIA[cat]["subcriteria"][sub]["name"]
            parent_name = EVALUATION_CRITERIA[cat]["name"]
            strengths.append({
                "category": cat,
                "subcategory": sub,
                "name": f"{parent_name} - {name}",
                "praise_count": count,
                "ratio": round(count / len(evaluations), 2)
            })
        else:
            name = EVALUATION_CRITERIA[key]["name"]
            strengths.append({
                "category": key,
                "name": name,
                "praise_count": count,
                "ratio": round(count / len(evaluations), 2)
            })

    return {
        "user_id": user_id,
        "strengths": strengths,
        "total_evaluations": len(evaluations)
    }


def get_common_weaknesses(user_id: str) -> Dict[str, Any]:
    """동료들이 공통으로 지적한 점 추출

    Args:
        user_id: 사용자 ID

    Returns:
        공통 약점 목록
    """
    evaluations = get_evaluations_received(user_id)

    if not evaluations:
        return {
            "user_id": user_id,
            "weaknesses": [],
            "message": "아직 받은 평가가 없습니다."
        }

    # 낮은 점수를 받은 카테고리/하위항목 수집
    low_scores = defaultdict(int)

    for e in evaluations:
        for category, score_data in e["scores"].items():
            max_score = EVALUATION_CRITERIA[category]["max_score"]
            ratio = score_data["total"] / max_score

            if ratio <= 0.5:
                low_scores[category] += 1

            # 하위 항목도 확인
            for sub_key, sub_score in score_data.get("subcriteria", {}).items():
                sub_info = EVALUATION_CRITERIA[category]["subcriteria"].get(sub_key, {})
                sub_max = max_score * sub_info.get("weight", 0.33)

                if sub_max > 0 and sub_score / sub_max <= 0.5:
                    low_scores[f"{category}.{sub_key}"] += 1

    # 가장 많이 지적받은 순 정렬
    sorted_weaknesses = sorted(low_scores.items(), key=lambda x: x[1], reverse=True)

    weaknesses = []
    for key, count in sorted_weaknesses[:5]:
        if "." in key:
            cat, sub = key.split(".")
            name = EVALUATION_CRITERIA[cat]["subcriteria"][sub]["name"]
            parent_name = EVALUATION_CRITERIA[cat]["name"]
            suggestion = _generate_improvement_suggestion(cat, 0.5)
            weaknesses.append({
                "category": cat,
                "subcategory": sub,
                "name": f"{parent_name} - {name}",
                "criticism_count": count,
                "ratio": round(count / len(evaluations), 2),
                "suggestion": suggestion
            })
        else:
            name = EVALUATION_CRITERIA[key]["name"]
            suggestion = _generate_improvement_suggestion(key, 0.5)
            weaknesses.append({
                "category": key,
                "name": name,
                "criticism_count": count,
                "ratio": round(count / len(evaluations), 2),
                "suggestion": suggestion
            })

    return {
        "user_id": user_id,
        "weaknesses": weaknesses,
        "total_evaluations": len(evaluations)
    }


# ========================================
# 평가 품질 관리
# ========================================

def flag_unfair_evaluation(evaluation_id: str, reason: str) -> Dict[str, Any]:
    """불공정 평가 신고

    Args:
        evaluation_id: 평가 ID
        reason: 신고 사유

    Returns:
        신고 결과
    """
    evaluations = _load_evaluations()

    for e in evaluations:
        if e["evaluation_id"] == evaluation_id:
            e["flagged"] = True
            e["flag_reason"] = reason
            e["flagged_at"] = datetime.now().isoformat()

            _save_evaluations(evaluations)

            logger.info(f"평가 신고됨: {evaluation_id}, 사유: {reason}")

            return {
                "evaluation_id": evaluation_id,
                "flagged": True,
                "reason": reason,
                "message": "신고가 접수되었습니다. 검토 후 조치하겠습니다."
            }

    raise ValueError("해당 평가를 찾을 수 없습니다.")


def calculate_evaluator_reliability(user_id: str) -> Dict[str, Any]:
    """평가자 신뢰도 계산

    Args:
        user_id: 평가자 ID

    Returns:
        신뢰도 정보
    """
    evaluations = _load_evaluations()

    # 이 사용자가 작성한 평가들
    given = [e for e in evaluations if e["evaluator_id"] == user_id]

    if len(given) < 5:
        return {
            "user_id": user_id,
            "reliability": 1.0,  # 기본 신뢰도
            "evaluation_count": len(given),
            "message": "평가 이력이 부족하여 기본 신뢰도가 적용됩니다."
        }

    # 신뢰도 요소들
    factors = []

    # 1. 신고된 평가 비율 (낮을수록 좋음)
    flagged_count = sum(1 for e in given if e.get("flagged"))
    flag_ratio = flagged_count / len(given)
    flag_score = 1 - (flag_ratio * 2)  # 신고 비율에 패널티
    factors.append(max(0, flag_score))

    # 2. 평가 점수 분포 (너무 극단적이면 감점)
    scores = [e["total_score"] for e in given]
    avg_score = sum(scores) / len(scores)

    # 표준편차 계산
    variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
    std_dev = variance ** 0.5

    # 적절한 분포 (표준편차 10-20 정도가 이상적)
    if 10 <= std_dev <= 20:
        distribution_score = 1.0
    elif std_dev < 5 or std_dev > 30:
        distribution_score = 0.7
    else:
        distribution_score = 0.85
    factors.append(distribution_score)

    # 3. 평가 완성도 (피드백 작성 비율)
    feedback_count = sum(1 for e in given if e.get("feedback"))
    feedback_ratio = feedback_count / len(given)
    factors.append(feedback_ratio)

    # 4. 활동량 보너스
    activity_bonus = min(1.0, len(given) / 50)  # 50개 이상이면 1.0
    factors.append(0.5 + activity_bonus * 0.5)

    # 종합 신뢰도 (0~1)
    reliability = sum(factors) / len(factors)
    reliability = round(max(0.3, min(1.0, reliability)), 2)

    return {
        "user_id": user_id,
        "reliability": reliability,
        "evaluation_count": len(given),
        "flagged_evaluations": flagged_count,
        "feedback_rate": round(feedback_ratio, 2),
        "score_std_dev": round(std_dev, 1),
        "reliability_level": _get_reliability_level(reliability)
    }


def _get_reliability_level(reliability: float) -> str:
    """신뢰도 레벨 문자열 반환"""
    if reliability >= 0.9:
        return "매우 높음"
    elif reliability >= 0.75:
        return "높음"
    elif reliability >= 0.5:
        return "보통"
    else:
        return "낮음"


def adjust_for_bias(evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """평가 편향 조정

    Args:
        evaluations: 평가 목록

    Returns:
        편향 조정된 평가 목록
    """
    if len(evaluations) < 3:
        return evaluations

    # 평가자별 평균 점수 계산 (관대/엄격 편향 파악)
    evaluator_averages = defaultdict(list)
    for e in evaluations:
        evaluator_averages[e["evaluator_id"]].append(e["total_score"])

    # 전체 평균
    all_scores = [e["total_score"] for e in evaluations]
    global_average = sum(all_scores) / len(all_scores)

    # 조정된 평가 목록 생성
    adjusted = []
    for e in evaluations:
        evaluator_id = e["evaluator_id"]
        evaluator_scores = evaluator_averages[evaluator_id]

        if len(evaluator_scores) >= 3:
            evaluator_avg = sum(evaluator_scores) / len(evaluator_scores)

            # 편향 보정
            bias = evaluator_avg - global_average
            adjusted_score = e["total_score"] - (bias * 0.5)  # 50% 보정
            adjusted_score = max(0, min(100, adjusted_score))
        else:
            adjusted_score = e["total_score"]

        adjusted_eval = e.copy()
        adjusted_eval["adjusted_score"] = round(adjusted_score, 1)
        adjusted_eval["original_score"] = e["total_score"]
        adjusted.append(adjusted_eval)

    logger.debug(f"편향 조정 완료: {len(adjusted)}개 평가")
    return adjusted


# ========================================
# 리더보드
# ========================================

def get_peer_review_leaderboard(period: str = "weekly") -> List[Dict[str, Any]]:
    """동료 평가 기준 리더보드

    Args:
        period: 기간 (weekly, monthly, all)

    Returns:
        리더보드 목록
    """
    evaluations = _load_evaluations()

    # 기간 필터
    now = datetime.now()
    if period == "weekly":
        cutoff = now - timedelta(days=7)
    elif period == "monthly":
        cutoff = now - timedelta(days=30)
    else:
        cutoff = datetime.min

    filtered = [
        e for e in evaluations
        if datetime.fromisoformat(e["created_at"]) >= cutoff
        and not e.get("flagged")
    ]

    # 사용자별 평균 점수 계산
    user_scores = defaultdict(list)
    for e in filtered:
        user_scores[e["target_id"]].append(e["total_score"])

    # 리더보드 생성 (최소 2개 평가 필요)
    leaderboard = []
    for user_id, scores in user_scores.items():
        if len(scores) >= 2:
            avg_score = sum(scores) / len(scores)
            leaderboard.append({
                "user_id": user_id,
                "average_score": round(avg_score, 1),
                "evaluation_count": len(scores),
                "highest_score": max(scores),
                "lowest_score": min(scores)
            })

    # 평균 점수 순 정렬
    leaderboard.sort(key=lambda x: x["average_score"], reverse=True)

    # 순위 부여
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1

    logger.debug(f"동료 평가 리더보드 조회: {period}, {len(leaderboard)}명")

    return {
        "period": period,
        "period_label": {"weekly": "주간", "monthly": "월간", "all": "전체"}[period],
        "leaderboard": leaderboard[:20],  # 상위 20명
        "generated_at": now.isoformat()
    }


def get_best_evaluator_leaderboard() -> Dict[str, Any]:
    """우수 평가자 리더보드

    Returns:
        평가자 리더보드
    """
    evaluations = _load_evaluations()

    # 평가자별 통계
    evaluator_stats = defaultdict(lambda: {
        "total_evaluations": 0,
        "feedback_count": 0,
        "flagged_count": 0
    })

    for e in evaluations:
        evaluator_id = e["evaluator_id"]
        evaluator_stats[evaluator_id]["total_evaluations"] += 1

        if e.get("feedback"):
            evaluator_stats[evaluator_id]["feedback_count"] += 1

        if e.get("flagged"):
            evaluator_stats[evaluator_id]["flagged_count"] += 1

    # 점수 계산 및 리더보드 생성
    leaderboard = []
    for user_id, stats in evaluator_stats.items():
        if stats["total_evaluations"] < 5:
            continue

        reliability = calculate_evaluator_reliability(user_id)["reliability"]
        feedback_rate = stats["feedback_count"] / stats["total_evaluations"]

        # 종합 점수 (활동량 + 신뢰도 + 피드백 비율)
        activity_score = min(stats["total_evaluations"], 100) / 100 * 30
        reliability_score = reliability * 40
        feedback_score = feedback_rate * 30

        total_score = activity_score + reliability_score + feedback_score

        leaderboard.append({
            "user_id": user_id,
            "total_score": round(total_score, 1),
            "total_evaluations": stats["total_evaluations"],
            "reliability": reliability,
            "feedback_rate": round(feedback_rate, 2),
            "badges": _get_evaluator_badges(user_id, stats, reliability)
        })

    # 점수 순 정렬
    leaderboard.sort(key=lambda x: x["total_score"], reverse=True)

    # 순위 부여
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1

    return {
        "leaderboard": leaderboard[:20],
        "generated_at": datetime.now().isoformat()
    }


def _get_evaluator_badges(
    user_id: str,
    stats: Dict[str, Any],
    reliability: float
) -> List[Dict[str, str]]:
    """평가자 배지 목록 반환"""
    badges = []

    if stats["total_evaluations"] >= EVALUATOR_BADGES["active_evaluator"]["requirement"]:
        badges.append({
            "id": "active_evaluator",
            "name": EVALUATOR_BADGES["active_evaluator"]["name"]
        })

    if reliability >= EVALUATOR_BADGES["consistent_evaluator"]["requirement"]:
        badges.append({
            "id": "consistent_evaluator",
            "name": EVALUATOR_BADGES["consistent_evaluator"]["name"]
        })

    master_req = EVALUATOR_BADGES["master_evaluator"]["requirement"]
    if (stats["total_evaluations"] >= master_req["count"] and
        reliability >= master_req["reliability"]):
        badges.append({
            "id": "master_evaluator",
            "name": EVALUATOR_BADGES["master_evaluator"]["name"]
        })

    return badges


def award_evaluator_badge(user_id: str) -> Dict[str, Any]:
    """평가자 배지 수여

    Args:
        user_id: 평가자 ID

    Returns:
        수여된 배지 정보
    """
    evaluations = _load_evaluations()

    # 작성한 평가 수
    given = [e for e in evaluations if e["evaluator_id"] == user_id]
    total_evaluations = len(given)
    feedback_count = sum(1 for e in given if e.get("feedback"))

    # 신뢰도
    reliability = calculate_evaluator_reliability(user_id)["reliability"]

    stats = {
        "total_evaluations": total_evaluations,
        "feedback_count": feedback_count,
        "flagged_count": sum(1 for e in given if e.get("flagged"))
    }

    earned_badges = _get_evaluator_badges(user_id, stats, reliability)

    # 새로 획득한 배지 확인 (이전 배지와 비교 필요, 여기서는 간단히 반환)
    return {
        "user_id": user_id,
        "earned_badges": earned_badges,
        "stats": {
            "total_evaluations": total_evaluations,
            "reliability": reliability,
            "feedback_rate": round(feedback_count / total_evaluations, 2) if total_evaluations > 0 else 0
        }
    }


# ========================================
# 빠른 반응 시스템
# ========================================

def add_reaction(
    user_id: str,
    target_id: str,
    room_id: str,
    reaction: str
) -> Dict[str, Any]:
    """빠른 반응 추가

    Args:
        user_id: 반응하는 사용자 ID
        target_id: 대상 사용자 ID
        room_id: 방 ID
        reaction: 반응 종류 (like, amazing, confident, creative, empathy)

    Returns:
        추가된 반응 정보
    """
    if reaction not in REACTIONS:
        raise ValueError(f"유효하지 않은 반응입니다. 가능한 반응: {list(REACTIONS.keys())}")

    if user_id == target_id:
        raise ValueError("자기 자신에게는 반응할 수 없습니다.")

    reaction_data = {
        "reaction_id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "target_id": target_id,
        "room_id": room_id,
        "reaction": reaction,
        "emoji": REACTIONS[reaction]["emoji"],
        "name": REACTIONS[reaction]["name"],
        "created_at": datetime.now().isoformat()
    }

    reactions = _load_reactions()
    reactions.append(reaction_data)
    _save_reactions(reactions)

    logger.debug(f"반응 추가: {user_id} -> {target_id} ({reaction})")

    return reaction_data


def get_reactions_received(
    user_id: str,
    room_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """받은 반응 조회

    Args:
        user_id: 사용자 ID
        room_id: 방 ID (선택, 특정 방만 조회)

    Returns:
        받은 반응 목록
    """
    reactions = _load_reactions()

    received = [r for r in reactions if r["target_id"] == user_id]

    if room_id:
        received = [r for r in received if r["room_id"] == room_id]

    # 최신순 정렬
    received.sort(key=lambda x: x["created_at"], reverse=True)

    return received


def get_reaction_summary(user_id: str) -> Dict[str, Any]:
    """반응 요약

    Args:
        user_id: 사용자 ID

    Returns:
        반응 요약 정보
    """
    reactions = get_reactions_received(user_id)

    if not reactions:
        return {
            "user_id": user_id,
            "total_reactions": 0,
            "message": "아직 받은 반응이 없습니다."
        }

    # 반응별 카운트
    reaction_counts = Counter(r["reaction"] for r in reactions)

    # 정렬된 반응 목록
    sorted_reactions = []
    for reaction_key, count in reaction_counts.most_common():
        reaction_info = REACTIONS[reaction_key]
        sorted_reactions.append({
            "reaction": reaction_key,
            "emoji": reaction_info["emoji"],
            "name": reaction_info["name"],
            "count": count
        })

    # 가장 많이 받은 반응
    most_common = sorted_reactions[0] if sorted_reactions else None

    return {
        "user_id": user_id,
        "total_reactions": len(reactions),
        "reaction_breakdown": sorted_reactions,
        "most_received": most_common,
        "unique_reactors": len(set(r["user_id"] for r in reactions))
    }


# ========================================
# 유틸리티 함수
# ========================================

def get_evaluation_criteria() -> Dict[str, Any]:
    """평가 기준 정보 반환"""
    return EVALUATION_CRITERIA


def get_available_reactions() -> Dict[str, Any]:
    """사용 가능한 반응 목록 반환"""
    return REACTIONS


def get_score_weights() -> Dict[str, float]:
    """점수 가중치 반환"""
    return SCORE_WEIGHTS
