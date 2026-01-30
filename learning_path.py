# learning_path.py
# FlyReady Lab - 개인화된 학습 경로 생성기

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from logging_config import get_logger

logger = get_logger(__name__)

# 데이터 저장 경로
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

LEARNING_PATHS_FILE = DATA_DIR / "learning_paths.json"
REVIEW_SCHEDULE_FILE = DATA_DIR / "review_schedule.json"
WRONG_ANSWERS_FILE = DATA_DIR / "wrong_answers.json"

# ============================================================================
# 학습 모듈 정의
# ============================================================================

LEARNING_MODULES: Dict[str, Dict[str, Any]] = {
    "service_mind": {
        "id": "service_mind",
        "name": "기본 서비스 마인드",
        "description": "승무원으로서 갖춰야 할 기본적인 서비스 마인드와 고객 응대 자세를 학습합니다.",
        "difficulty": 1,
        "estimated_hours": 5,
        "prerequisites": [],
        "skills_covered": ["고객 응대", "서비스 태도", "친절함", "프로페셔널리즘"],
        "category": "기초"
    },
    "situation_response": {
        "id": "situation_response",
        "name": "상황별 응대",
        "description": "클레임, 긴급상황, VIP 고객 등 다양한 상황에서의 응대 방법을 학습합니다.",
        "difficulty": 3,
        "estimated_hours": 8,
        "prerequisites": ["service_mind"],
        "skills_covered": ["클레임 처리", "긴급상황 대응", "VIP 응대", "문제 해결"],
        "category": "실전"
    },
    "self_introduction": {
        "id": "self_introduction",
        "name": "자기소개/지원동기",
        "description": "효과적인 자기소개와 지원동기 작성 및 답변 방법을 학습합니다.",
        "difficulty": 2,
        "estimated_hours": 6,
        "prerequisites": [],
        "skills_covered": ["자기소개", "지원동기", "스토리텔링", "어필 포인트"],
        "category": "면접"
    },
    "job_related": {
        "id": "job_related",
        "name": "직무 관련 질문",
        "description": "승무원 직무와 관련된 질문에 대한 답변 방법을 학습합니다.",
        "difficulty": 3,
        "estimated_hours": 7,
        "prerequisites": ["self_introduction"],
        "skills_covered": ["직무 이해", "역할 인식", "업무 능력", "팀워크"],
        "category": "면접"
    },
    "personality_interview": {
        "id": "personality_interview",
        "name": "인성 면접",
        "description": "인성 면접에서 자주 나오는 질문 유형과 답변 전략을 학습합니다.",
        "difficulty": 3,
        "estimated_hours": 8,
        "prerequisites": ["self_introduction"],
        "skills_covered": ["가치관", "성격", "대인관계", "갈등 해결"],
        "category": "면접"
    },
    "english_interview": {
        "id": "english_interview",
        "name": "영어 면접",
        "description": "영어 면접 대비를 위한 핵심 표현과 답변 연습을 진행합니다.",
        "difficulty": 4,
        "estimated_hours": 10,
        "prerequisites": ["self_introduction"],
        "skills_covered": ["영어 회화", "영어 표현", "발음", "자신감"],
        "category": "면접"
    },
    "debate_interview": {
        "id": "debate_interview",
        "name": "토론 면접",
        "description": "그룹 토론 면접에서의 역할과 전략을 학습합니다.",
        "difficulty": 4,
        "estimated_hours": 6,
        "prerequisites": ["personality_interview"],
        "skills_covered": ["논리적 사고", "의사소통", "경청", "리더십"],
        "category": "면접"
    },
    "aviation_knowledge": {
        "id": "aviation_knowledge",
        "name": "항공 상식",
        "description": "항공 업계 관련 기본 상식과 최신 트렌드를 학습합니다.",
        "difficulty": 2,
        "estimated_hours": 5,
        "prerequisites": [],
        "skills_covered": ["항공 용어", "업계 동향", "항공사 정보", "안전 절차"],
        "category": "기초"
    }
}

# ============================================================================
# 학습 단계 정의
# ============================================================================

LEARNING_STAGES: Dict[int, Dict[str, Any]] = {
    1: {
        "stage": 1,
        "name": "기초 다지기",
        "description": "기본적인 서비스 마인드와 항공 상식을 학습하는 단계입니다.",
        "required_modules": ["service_mind", "aviation_knowledge"],
        "min_completion_rate": 0.7,
        "min_practice_sessions": 5,
        "estimated_days": 7
    },
    2: {
        "stage": 2,
        "name": "실전 연습",
        "description": "자기소개, 지원동기 등 면접의 기본을 연습하는 단계입니다.",
        "required_modules": ["self_introduction", "job_related"],
        "min_completion_rate": 0.75,
        "min_practice_sessions": 15,
        "estimated_days": 14
    },
    3: {
        "stage": 3,
        "name": "심화 학습",
        "description": "인성, 영어, 토론 면접 등 심화 영역을 학습하는 단계입니다.",
        "required_modules": ["personality_interview", "english_interview", "situation_response"],
        "min_completion_rate": 0.8,
        "min_practice_sessions": 25,
        "estimated_days": 21
    },
    4: {
        "stage": 4,
        "name": "최종 점검",
        "description": "모든 영역을 종합적으로 복습하고 실전 감각을 키우는 단계입니다.",
        "required_modules": ["debate_interview"],
        "min_completion_rate": 0.85,
        "min_practice_sessions": 35,
        "estimated_days": 7
    }
}

# ============================================================================
# 복습 간격 정의 (간격 반복 학습)
# ============================================================================

REVIEW_INTERVALS: Dict[str, int] = {
    "perfect": 30,      # 완벽히 기억함 - 30일 후 복습
    "good": 14,         # 잘 기억함 - 14일 후 복습
    "okay": 7,          # 보통 - 7일 후 복습
    "hard": 3,          # 어려움 - 3일 후 복습
    "forgot": 1         # 완전히 잊음 - 1일 후 복습
}

# ============================================================================
# 마일스톤 정의
# ============================================================================

MILESTONES: List[Dict[str, Any]] = [
    {
        "id": "first_practice",
        "name": "첫 연습 완료",
        "description": "첫 번째 면접 연습을 완료했습니다!",
        "condition": {"practice_count": 1},
        "reward_points": 10
    },
    {
        "id": "five_practices",
        "name": "연습의 시작",
        "description": "5회 연습을 완료했습니다!",
        "condition": {"practice_count": 5},
        "reward_points": 30
    },
    {
        "id": "ten_practices",
        "name": "꾸준한 연습생",
        "description": "10회 연습을 완료했습니다!",
        "condition": {"practice_count": 10},
        "reward_points": 50
    },
    {
        "id": "stage_1_complete",
        "name": "기초 마스터",
        "description": "1단계 기초 다지기를 완료했습니다!",
        "condition": {"stage": 1, "completed": True},
        "reward_points": 100
    },
    {
        "id": "stage_2_complete",
        "name": "실전 연습 달인",
        "description": "2단계 실전 연습을 완료했습니다!",
        "condition": {"stage": 2, "completed": True},
        "reward_points": 150
    },
    {
        "id": "stage_3_complete",
        "name": "심화 학습 완료",
        "description": "3단계 심화 학습을 완료했습니다!",
        "condition": {"stage": 3, "completed": True},
        "reward_points": 200
    },
    {
        "id": "stage_4_complete",
        "name": "최종 점검 완료",
        "description": "4단계 최종 점검을 완료했습니다!",
        "condition": {"stage": 4, "completed": True},
        "reward_points": 300
    },
    {
        "id": "english_master",
        "name": "영어 면접 마스터",
        "description": "영어 면접 모듈을 80% 이상 완료했습니다!",
        "condition": {"module": "english_interview", "completion_rate": 0.8},
        "reward_points": 100
    },
    {
        "id": "perfect_week",
        "name": "완벽한 일주일",
        "description": "7일 연속 학습을 완료했습니다!",
        "condition": {"consecutive_days": 7},
        "reward_points": 100
    },
    {
        "id": "thirty_days",
        "name": "30일 도전 성공",
        "description": "30일 연속 학습을 완료했습니다!",
        "condition": {"consecutive_days": 30},
        "reward_points": 500
    },
    {
        "id": "wrong_answer_master",
        "name": "오답 정복자",
        "description": "50개의 오답 노트를 마스터했습니다!",
        "condition": {"mastered_wrong_answers": 50},
        "reward_points": 150
    }
]


# ============================================================================
# 데이터 로드/저장 유틸리티
# ============================================================================

def _load_json(file_path: Path) -> Dict:
    """JSON 파일 로드"""
    try:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"JSON 파일 로드 실패: {file_path}, 오류: {e}")
        return {}


def _save_json(file_path: Path, data: Dict) -> bool:
    """JSON 파일 저장"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"JSON 파일 저장 실패: {file_path}, 오류: {e}")
        return False


# ============================================================================
# 학습 경로 생성
# ============================================================================

def generate_learning_path(
    user_id: str,
    target_airline: str,
    deadline_days: int
) -> Dict[str, Any]:
    """
    개인화된 학습 경로를 생성합니다.

    Args:
        user_id: 사용자 ID
        target_airline: 목표 항공사
        deadline_days: 면접까지 남은 일수

    Returns:
        생성된 학습 경로 정보
    """
    logger.info(f"학습 경로 생성 시작: user_id={user_id}, airline={target_airline}, deadline={deadline_days}일")

    # 사용자 현재 상태 확인
    current_stage = get_user_stage(user_id)

    # 남은 시간에 따른 학습 강도 계산
    if deadline_days <= 7:
        intensity = "집중"
        daily_hours = 4.0
    elif deadline_days <= 14:
        intensity = "강화"
        daily_hours = 3.0
    elif deadline_days <= 30:
        intensity = "표준"
        daily_hours = 2.0
    else:
        intensity = "여유"
        daily_hours = 1.5

    # 필수 모듈 순서 결정
    module_order = _determine_module_order(current_stage, deadline_days)

    # 학습 경로 생성
    learning_path = {
        "user_id": user_id,
        "target_airline": target_airline,
        "deadline_days": deadline_days,
        "deadline_date": (datetime.now() + timedelta(days=deadline_days)).isoformat(),
        "created_at": datetime.now().isoformat(),
        "current_stage": current_stage,
        "intensity": intensity,
        "daily_hours": daily_hours,
        "module_order": module_order,
        "completed_modules": [],
        "current_module_index": 0,
        "progress": {
            "total_modules": len(module_order),
            "completed_count": 0,
            "completion_rate": 0.0
        }
    }

    # 저장
    paths_data = _load_json(LEARNING_PATHS_FILE)
    paths_data[user_id] = learning_path
    _save_json(LEARNING_PATHS_FILE, paths_data)

    logger.info(f"학습 경로 생성 완료: {len(module_order)}개 모듈, {intensity} 강도")

    return learning_path


def _determine_module_order(current_stage: int, deadline_days: int) -> List[str]:
    """
    현재 단계와 남은 시간을 기반으로 모듈 학습 순서를 결정합니다.
    """
    # 기본 순서 (권장 학습 순서)
    base_order = [
        "service_mind",
        "aviation_knowledge",
        "self_introduction",
        "job_related",
        "personality_interview",
        "situation_response",
        "english_interview",
        "debate_interview"
    ]

    # 시간이 촉박하면 핵심 모듈 우선
    if deadline_days <= 7:
        return ["self_introduction", "job_related", "personality_interview"]
    elif deadline_days <= 14:
        return [
            "self_introduction",
            "job_related",
            "personality_interview",
            "english_interview",
            "situation_response"
        ]
    elif deadline_days <= 30:
        return [
            "service_mind",
            "self_introduction",
            "job_related",
            "personality_interview",
            "english_interview",
            "situation_response",
            "aviation_knowledge"
        ]
    else:
        return base_order


def get_recommended_modules(user_id: str) -> List[Dict[str, Any]]:
    """
    사용자의 약점을 기반으로 추천 학습 모듈을 반환합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        추천 모듈 목록 (우선순위 순)
    """
    logger.info(f"추천 모듈 조회: user_id={user_id}")

    # 사용자 학습 경로 로드
    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id, {})

    # 오답 노트에서 약점 분석
    wrong_answers = _load_json(WRONG_ANSWERS_FILE)
    user_wrong = wrong_answers.get(user_id, {}).get("items", [])

    # 카테고리별 오답 수 계산
    category_counts: Dict[str, int] = {}
    for item in user_wrong:
        if not item.get("mastered", False):
            category = item.get("category", "기타")
            category_counts[category] = category_counts.get(category, 0) + 1

    # 완료되지 않은 모듈 필터링
    completed = set(user_path.get("completed_modules", []))

    recommendations = []
    for module_id, module_info in LEARNING_MODULES.items():
        if module_id in completed:
            continue

        # 우선순위 점수 계산
        priority_score = 0

        # 선수 과목이 완료된 경우 점수 추가
        prerequisites_met = all(p in completed for p in module_info["prerequisites"])
        if prerequisites_met:
            priority_score += 10
        else:
            priority_score -= 20  # 선수 과목 미완료 시 페널티

        # 약점 카테고리와 관련된 모듈 점수 추가
        for skill in module_info["skills_covered"]:
            if skill in category_counts:
                priority_score += category_counts[skill] * 2

        # 난이도에 따른 조정
        if module_info["difficulty"] <= 2:
            priority_score += 5  # 쉬운 모듈 먼저

        recommendations.append({
            **module_info,
            "priority_score": priority_score,
            "prerequisites_met": prerequisites_met
        })

    # 우선순위 점수로 정렬
    recommendations.sort(key=lambda x: x["priority_score"], reverse=True)

    logger.info(f"추천 모듈 {len(recommendations)}개 반환")
    return recommendations


def get_next_lesson(user_id: str) -> Optional[Dict[str, Any]]:
    """
    사용자가 다음으로 학습해야 할 레슨/연습을 반환합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        다음 레슨 정보 또는 None
    """
    logger.info(f"다음 레슨 조회: user_id={user_id}")

    # 복습 항목 확인 (복습이 우선)
    review_items = get_review_items(user_id)
    if review_items:
        logger.info(f"복습 필요 항목 {len(review_items)}개 발견")
        return {
            "type": "review",
            "message": "복습이 필요한 항목이 있습니다.",
            "items": review_items[:5],  # 최대 5개
            "total_review_count": len(review_items)
        }

    # 학습 경로에서 다음 모듈 확인
    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id)

    if not user_path:
        logger.info("학습 경로가 없습니다. 새로운 경로 생성이 필요합니다.")
        return {
            "type": "new_path_required",
            "message": "학습 경로가 설정되지 않았습니다. 먼저 학습 경로를 생성해주세요."
        }

    module_order = user_path.get("module_order", [])
    current_index = user_path.get("current_module_index", 0)

    if current_index >= len(module_order):
        logger.info("모든 모듈 학습 완료")
        return {
            "type": "completed",
            "message": "축하합니다! 모든 학습 모듈을 완료했습니다."
        }

    current_module_id = module_order[current_index]
    current_module = LEARNING_MODULES.get(current_module_id)

    if not current_module:
        logger.error(f"모듈을 찾을 수 없음: {current_module_id}")
        return None

    return {
        "type": "module",
        "module": current_module,
        "progress": {
            "current": current_index + 1,
            "total": len(module_order)
        },
        "message": f"다음 학습: {current_module['name']}"
    }


# ============================================================================
# 단계별 학습 관리
# ============================================================================

def get_user_stage(user_id: str) -> int:
    """
    사용자의 현재 학습 단계를 반환합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        현재 단계 (1-4)
    """
    logger.info(f"사용자 단계 조회: user_id={user_id}")

    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id)

    if not user_path:
        return 1  # 기본값: 1단계

    # 완료된 모듈 확인
    completed_modules = set(user_path.get("completed_modules", []))

    # 각 단계의 요구사항 확인
    for stage_num in [4, 3, 2, 1]:  # 높은 단계부터 확인
        stage = LEARNING_STAGES[stage_num]
        required = set(stage["required_modules"])

        if required.issubset(completed_modules):
            return min(stage_num + 1, 4)  # 다음 단계로 (최대 4)

    return 1


def get_stage_requirements(stage: int) -> Dict[str, Any]:
    """
    특정 단계로 진급하기 위한 요구사항을 반환합니다.

    Args:
        stage: 단계 번호 (1-4)

    Returns:
        단계 요구사항 정보
    """
    if stage not in LEARNING_STAGES:
        logger.warning(f"유효하지 않은 단계: {stage}")
        return {}

    stage_info = LEARNING_STAGES[stage]

    # 필요한 모듈 정보 추가
    required_modules_info = []
    for module_id in stage_info["required_modules"]:
        if module_id in LEARNING_MODULES:
            required_modules_info.append(LEARNING_MODULES[module_id])

    return {
        **stage_info,
        "required_modules_info": required_modules_info,
        "total_estimated_hours": sum(m["estimated_hours"] for m in required_modules_info)
    }


# ============================================================================
# 커리큘럼 관리
# ============================================================================

def create_daily_plan(user_id: str, available_hours: float) -> Dict[str, Any]:
    """
    사용자의 가용 시간을 기반으로 일일 학습 계획을 생성합니다.

    Args:
        user_id: 사용자 ID
        available_hours: 학습 가능 시간 (시간 단위)

    Returns:
        일일 학습 계획
    """
    logger.info(f"일일 계획 생성: user_id={user_id}, available_hours={available_hours}")

    plan = {
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "available_hours": available_hours,
        "tasks": []
    }

    remaining_time = available_hours

    # 1. 복습 항목 (15-20분)
    review_items = get_review_items(user_id)
    if review_items and remaining_time >= 0.25:
        review_time = min(0.33, remaining_time * 0.2)  # 최대 20분 또는 가용 시간의 20%
        plan["tasks"].append({
            "type": "review",
            "title": "오답 및 복습",
            "description": f"{len(review_items)}개 항목 복습",
            "duration_hours": review_time,
            "items": review_items[:5]
        })
        remaining_time -= review_time

    # 2. 메인 학습 (60-70%)
    next_lesson = get_next_lesson(user_id)
    if next_lesson and next_lesson.get("type") == "module":
        module = next_lesson["module"]
        main_time = remaining_time * 0.7
        plan["tasks"].append({
            "type": "main_study",
            "title": module["name"],
            "description": module["description"],
            "duration_hours": main_time,
            "module_id": module["id"]
        })
        remaining_time -= main_time

    # 3. 실전 연습 (나머지 시간)
    if remaining_time > 0.25:
        plan["tasks"].append({
            "type": "practice",
            "title": "실전 면접 연습",
            "description": "배운 내용을 실전처럼 연습합니다.",
            "duration_hours": remaining_time
        })

    plan["total_planned_hours"] = sum(t["duration_hours"] for t in plan["tasks"])

    logger.info(f"일일 계획 생성 완료: {len(plan['tasks'])}개 태스크")
    return plan


def create_weekly_plan(user_id: str) -> Dict[str, Any]:
    """
    주간 학습 계획을 생성합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        주간 학습 계획
    """
    logger.info(f"주간 계획 생성: user_id={user_id}")

    # 사용자 학습 경로 로드
    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id, {})

    daily_hours = user_path.get("daily_hours", 2.0)

    # 일주일 계획 생성
    weekly_plan = {
        "user_id": user_id,
        "week_start": datetime.now().strftime("%Y-%m-%d"),
        "week_end": (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
        "daily_target_hours": daily_hours,
        "days": []
    }

    # 요일별 계획
    day_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

    for i in range(7):
        date = datetime.now() + timedelta(days=i)
        day_idx = date.weekday()

        # 주말에는 조금 더 많은 시간 할당
        if day_idx >= 5:  # 토, 일
            hours = daily_hours * 1.5
        else:
            hours = daily_hours

        daily_plan = create_daily_plan(user_id, hours)
        daily_plan["day_name"] = day_names[day_idx]
        daily_plan["date"] = date.strftime("%Y-%m-%d")

        weekly_plan["days"].append(daily_plan)

    weekly_plan["total_weekly_hours"] = sum(d["total_planned_hours"] for d in weekly_plan["days"])

    logger.info(f"주간 계획 생성 완료: 총 {weekly_plan['total_weekly_hours']:.1f}시간")
    return weekly_plan


def adjust_plan_for_deadline(user_id: str, deadline_days: int) -> Dict[str, Any]:
    """
    마감일에 따라 학습 강도를 조정합니다.

    Args:
        user_id: 사용자 ID
        deadline_days: 면접까지 남은 일수

    Returns:
        조정된 학습 계획 정보
    """
    logger.info(f"마감 기반 계획 조정: user_id={user_id}, deadline={deadline_days}일")

    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id)

    if not user_path:
        logger.warning(f"학습 경로가 없습니다: user_id={user_id}")
        return {"error": "학습 경로가 설정되지 않았습니다."}

    # 강도 조정
    if deadline_days <= 3:
        intensity = "초집중"
        daily_hours = 5.0
        focus_modules = ["self_introduction", "job_related"]
        message = "면접이 코앞입니다! 핵심 질문에만 집중하세요."
    elif deadline_days <= 7:
        intensity = "집중"
        daily_hours = 4.0
        focus_modules = ["self_introduction", "job_related", "personality_interview"]
        message = "마지막 일주일! 실전 연습에 집중하세요."
    elif deadline_days <= 14:
        intensity = "강화"
        daily_hours = 3.0
        focus_modules = None  # 모든 모듈
        message = "2주 남았습니다. 꾸준히 연습하세요."
    else:
        intensity = "표준"
        daily_hours = 2.0
        focus_modules = None
        message = "충분한 시간이 있습니다. 체계적으로 준비하세요."

    # 경로 업데이트
    user_path["intensity"] = intensity
    user_path["daily_hours"] = daily_hours
    user_path["deadline_days"] = deadline_days
    user_path["deadline_date"] = (datetime.now() + timedelta(days=deadline_days)).isoformat()

    if focus_modules:
        user_path["focus_modules"] = focus_modules

    paths_data[user_id] = user_path
    _save_json(LEARNING_PATHS_FILE, paths_data)

    adjustment = {
        "intensity": intensity,
        "daily_hours": daily_hours,
        "deadline_days": deadline_days,
        "focus_modules": focus_modules,
        "message": message
    }

    logger.info(f"계획 조정 완료: {intensity} 강도, 일일 {daily_hours}시간")
    return adjustment


# ============================================================================
# 간격 반복 학습 시스템
# ============================================================================

def get_review_items(user_id: str) -> List[Dict[str, Any]]:
    """
    복습이 필요한 항목을 반환합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        복습 필요 항목 목록
    """
    logger.info(f"복습 항목 조회: user_id={user_id}")

    review_data = _load_json(REVIEW_SCHEDULE_FILE)
    user_schedule = review_data.get(user_id, {}).get("items", [])

    now = datetime.now()
    due_items = []

    for item in user_schedule:
        next_review = datetime.fromisoformat(item["next_review_date"])
        if next_review <= now:
            due_items.append(item)

    # 긴급도 순으로 정렬 (오래된 항목 먼저)
    due_items.sort(key=lambda x: x["next_review_date"])

    logger.info(f"복습 필요 항목 {len(due_items)}개")
    return due_items


def schedule_review(
    user_id: str,
    item_id: str,
    performance: str
) -> Dict[str, Any]:
    """
    수행 결과에 따라 다음 복습 일정을 설정합니다.

    Args:
        user_id: 사용자 ID
        item_id: 항목 ID
        performance: 수행 결과 ("perfect", "good", "okay", "hard", "forgot")

    Returns:
        업데이트된 복습 일정 정보
    """
    logger.info(f"복습 일정 설정: user_id={user_id}, item_id={item_id}, performance={performance}")

    if performance not in REVIEW_INTERVALS:
        logger.warning(f"유효하지 않은 수행 결과: {performance}")
        performance = "okay"

    interval_days = REVIEW_INTERVALS[performance]
    next_review_date = datetime.now() + timedelta(days=interval_days)

    review_data = _load_json(REVIEW_SCHEDULE_FILE)

    if user_id not in review_data:
        review_data[user_id] = {"items": []}

    # 기존 항목 찾기 또는 새로 추가
    found = False
    for item in review_data[user_id]["items"]:
        if item["item_id"] == item_id:
            item["next_review_date"] = next_review_date.isoformat()
            item["last_performance"] = performance
            item["review_count"] = item.get("review_count", 0) + 1
            item["updated_at"] = datetime.now().isoformat()
            found = True
            break

    if not found:
        review_data[user_id]["items"].append({
            "item_id": item_id,
            "next_review_date": next_review_date.isoformat(),
            "last_performance": performance,
            "review_count": 1,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })

    _save_json(REVIEW_SCHEDULE_FILE, review_data)

    result = {
        "item_id": item_id,
        "performance": performance,
        "interval_days": interval_days,
        "next_review_date": next_review_date.isoformat(),
        "message": f"{interval_days}일 후에 복습 예정입니다."
    }

    logger.info(f"복습 일정 설정 완료: {interval_days}일 후")
    return result


# ============================================================================
# 오답 노트
# ============================================================================

def add_wrong_answer(
    user_id: str,
    question: str,
    user_answer: str,
    correct_guidance: str,
    category: str
) -> Dict[str, Any]:
    """
    오답 노트에 항목을 추가합니다.

    Args:
        user_id: 사용자 ID
        question: 질문 내용
        user_answer: 사용자 답변
        correct_guidance: 올바른 답변 가이드
        category: 카테고리 (예: "자기소개", "인성 면접" 등)

    Returns:
        추가된 오답 항목 정보
    """
    logger.info(f"오답 추가: user_id={user_id}, category={category}")

    wrong_data = _load_json(WRONG_ANSWERS_FILE)

    if user_id not in wrong_data:
        wrong_data[user_id] = {"items": [], "stats": {"total": 0, "mastered": 0}}

    item_id = str(uuid.uuid4())

    new_item = {
        "item_id": item_id,
        "question": question,
        "user_answer": user_answer,
        "correct_guidance": correct_guidance,
        "category": category,
        "mastered": False,
        "review_count": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    wrong_data[user_id]["items"].append(new_item)
    wrong_data[user_id]["stats"]["total"] += 1

    _save_json(WRONG_ANSWERS_FILE, wrong_data)

    # 복습 일정에도 추가
    schedule_review(user_id, item_id, "forgot")

    logger.info(f"오답 추가 완료: item_id={item_id}")
    return new_item


def get_wrong_answers(
    user_id: str,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    오답 노트를 조회합니다.

    Args:
        user_id: 사용자 ID
        category: 필터링할 카테고리 (None이면 전체)

    Returns:
        오답 항목 목록
    """
    logger.info(f"오답 조회: user_id={user_id}, category={category}")

    wrong_data = _load_json(WRONG_ANSWERS_FILE)
    user_data = wrong_data.get(user_id, {})
    items = user_data.get("items", [])

    # 마스터되지 않은 항목만 필터링
    items = [item for item in items if not item.get("mastered", False)]

    if category:
        items = [item for item in items if item.get("category") == category]

    # 최신 순으로 정렬
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    logger.info(f"오답 {len(items)}개 반환")
    return items


def mark_mastered(user_id: str, item_id: str) -> Dict[str, Any]:
    """
    오답 항목을 마스터 처리합니다.

    Args:
        user_id: 사용자 ID
        item_id: 항목 ID

    Returns:
        처리 결과
    """
    logger.info(f"마스터 처리: user_id={user_id}, item_id={item_id}")

    wrong_data = _load_json(WRONG_ANSWERS_FILE)

    if user_id not in wrong_data:
        return {"error": "사용자 데이터가 없습니다."}

    found = False
    for item in wrong_data[user_id]["items"]:
        if item["item_id"] == item_id:
            item["mastered"] = True
            item["mastered_at"] = datetime.now().isoformat()
            item["updated_at"] = datetime.now().isoformat()
            found = True
            break

    if not found:
        return {"error": "항목을 찾을 수 없습니다."}

    wrong_data[user_id]["stats"]["mastered"] += 1
    _save_json(WRONG_ANSWERS_FILE, wrong_data)

    result = {
        "item_id": item_id,
        "mastered": True,
        "message": "항목을 마스터했습니다! 훌륭해요!"
    }

    logger.info(f"마스터 처리 완료: item_id={item_id}")
    return result


# ============================================================================
# 진행 마일스톤
# ============================================================================

def check_milestone_completion(user_id: str) -> List[Dict[str, Any]]:
    """
    사용자가 달성한 마일스톤을 확인합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        달성된 마일스톤 목록
    """
    logger.info(f"마일스톤 확인: user_id={user_id}")

    # 사용자 데이터 로드
    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id, {})

    wrong_data = _load_json(WRONG_ANSWERS_FILE)
    user_wrong = wrong_data.get(user_id, {})

    # 사용자 통계 계산
    completed_modules = user_path.get("completed_modules", [])
    practice_count = user_path.get("practice_count", 0)
    consecutive_days = user_path.get("consecutive_days", 0)
    mastered_wrong = user_wrong.get("stats", {}).get("mastered", 0)

    current_stage = get_user_stage(user_id)

    # 기존 달성 마일스톤
    achieved_milestones = set(user_path.get("achieved_milestones", []))

    # 새로 달성한 마일스톤 확인
    newly_achieved = []

    for milestone in MILESTONES:
        if milestone["id"] in achieved_milestones:
            continue

        condition = milestone["condition"]
        achieved = False

        # 연습 횟수 기반
        if "practice_count" in condition:
            if practice_count >= condition["practice_count"]:
                achieved = True

        # 단계 완료 기반
        if "stage" in condition and "completed" in condition:
            if current_stage > condition["stage"]:
                achieved = True

        # 연속 학습일 기반
        if "consecutive_days" in condition:
            if consecutive_days >= condition["consecutive_days"]:
                achieved = True

        # 오답 마스터 기반
        if "mastered_wrong_answers" in condition:
            if mastered_wrong >= condition["mastered_wrong_answers"]:
                achieved = True

        # 모듈 완료율 기반
        if "module" in condition and "completion_rate" in condition:
            module_id = condition["module"]
            if module_id in completed_modules:
                achieved = True

        if achieved:
            newly_achieved.append(milestone)

    # 새로 달성한 마일스톤 저장
    if newly_achieved:
        for m in newly_achieved:
            achieved_milestones.add(m["id"])

        user_path["achieved_milestones"] = list(achieved_milestones)
        paths_data[user_id] = user_path
        _save_json(LEARNING_PATHS_FILE, paths_data)

    logger.info(f"새로 달성한 마일스톤 {len(newly_achieved)}개")
    return newly_achieved


def get_next_milestone(user_id: str) -> Optional[Dict[str, Any]]:
    """
    다음으로 달성할 마일스톤을 반환합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        다음 마일스톤 정보 또는 None
    """
    logger.info(f"다음 마일스톤 조회: user_id={user_id}")

    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id, {})
    achieved_milestones = set(user_path.get("achieved_milestones", []))

    # 아직 달성하지 못한 마일스톤 중 첫 번째 반환
    for milestone in MILESTONES:
        if milestone["id"] not in achieved_milestones:
            # 진행률 계산
            progress = _calculate_milestone_progress(user_id, milestone)
            return {
                **milestone,
                "progress": progress
            }

    logger.info("모든 마일스톤 달성 완료")
    return None


def _calculate_milestone_progress(user_id: str, milestone: Dict) -> Dict[str, Any]:
    """마일스톤 진행률을 계산합니다."""
    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id, {})

    wrong_data = _load_json(WRONG_ANSWERS_FILE)
    user_wrong = wrong_data.get(user_id, {})

    condition = milestone["condition"]

    if "practice_count" in condition:
        current = user_path.get("practice_count", 0)
        target = condition["practice_count"]
        return {
            "current": current,
            "target": target,
            "percentage": min(100, int(current / target * 100))
        }

    if "consecutive_days" in condition:
        current = user_path.get("consecutive_days", 0)
        target = condition["consecutive_days"]
        return {
            "current": current,
            "target": target,
            "percentage": min(100, int(current / target * 100))
        }

    if "mastered_wrong_answers" in condition:
        current = user_wrong.get("stats", {}).get("mastered", 0)
        target = condition["mastered_wrong_answers"]
        return {
            "current": current,
            "target": target,
            "percentage": min(100, int(current / target * 100))
        }

    return {"current": 0, "target": 1, "percentage": 0}


# ============================================================================
# 유틸리티 함수
# ============================================================================

def update_practice_count(user_id: str) -> int:
    """연습 횟수를 1 증가시키고 반환합니다."""
    paths_data = _load_json(LEARNING_PATHS_FILE)

    if user_id not in paths_data:
        paths_data[user_id] = {}

    paths_data[user_id]["practice_count"] = paths_data[user_id].get("practice_count", 0) + 1
    paths_data[user_id]["last_practice_date"] = datetime.now().isoformat()

    _save_json(LEARNING_PATHS_FILE, paths_data)

    return paths_data[user_id]["practice_count"]


def update_consecutive_days(user_id: str) -> int:
    """연속 학습일을 업데이트하고 반환합니다."""
    paths_data = _load_json(LEARNING_PATHS_FILE)

    if user_id not in paths_data:
        paths_data[user_id] = {}

    last_date_str = paths_data[user_id].get("last_practice_date")
    today = datetime.now().date()

    if last_date_str:
        last_date = datetime.fromisoformat(last_date_str).date()
        days_diff = (today - last_date).days

        if days_diff == 1:
            # 연속 학습
            paths_data[user_id]["consecutive_days"] = paths_data[user_id].get("consecutive_days", 0) + 1
        elif days_diff > 1:
            # 연속 끊김
            paths_data[user_id]["consecutive_days"] = 1
        # days_diff == 0이면 같은 날이므로 변경 없음
    else:
        paths_data[user_id]["consecutive_days"] = 1

    _save_json(LEARNING_PATHS_FILE, paths_data)

    return paths_data[user_id].get("consecutive_days", 1)


def complete_module(user_id: str, module_id: str) -> Dict[str, Any]:
    """모듈 완료를 기록합니다."""
    logger.info(f"모듈 완료: user_id={user_id}, module_id={module_id}")

    paths_data = _load_json(LEARNING_PATHS_FILE)

    if user_id not in paths_data:
        paths_data[user_id] = {}

    if "completed_modules" not in paths_data[user_id]:
        paths_data[user_id]["completed_modules"] = []

    if module_id not in paths_data[user_id]["completed_modules"]:
        paths_data[user_id]["completed_modules"].append(module_id)
        paths_data[user_id]["current_module_index"] = paths_data[user_id].get("current_module_index", 0) + 1

    # 진행률 업데이트
    total = len(paths_data[user_id].get("module_order", []))
    completed = len(paths_data[user_id]["completed_modules"])

    paths_data[user_id]["progress"] = {
        "total_modules": total,
        "completed_count": completed,
        "completion_rate": completed / total if total > 0 else 0
    }

    _save_json(LEARNING_PATHS_FILE, paths_data)

    # 마일스톤 체크
    new_milestones = check_milestone_completion(user_id)

    result = {
        "module_id": module_id,
        "completed": True,
        "progress": paths_data[user_id]["progress"],
        "new_milestones": new_milestones,
        "message": f"'{LEARNING_MODULES.get(module_id, {}).get('name', module_id)}' 모듈을 완료했습니다!"
    }

    logger.info(f"모듈 완료 처리 완료: {module_id}")
    return result


def get_learning_summary(user_id: str) -> Dict[str, Any]:
    """사용자의 학습 현황 요약을 반환합니다."""
    logger.info(f"학습 요약 조회: user_id={user_id}")

    paths_data = _load_json(LEARNING_PATHS_FILE)
    user_path = paths_data.get(user_id, {})

    wrong_data = _load_json(WRONG_ANSWERS_FILE)
    user_wrong = wrong_data.get(user_id, {})

    review_data = _load_json(REVIEW_SCHEDULE_FILE)
    review_items = get_review_items(user_id)

    summary = {
        "user_id": user_id,
        "current_stage": get_user_stage(user_id),
        "target_airline": user_path.get("target_airline", "미설정"),
        "deadline_days": user_path.get("deadline_days"),
        "intensity": user_path.get("intensity", "표준"),
        "progress": user_path.get("progress", {}),
        "practice_count": user_path.get("practice_count", 0),
        "consecutive_days": user_path.get("consecutive_days", 0),
        "wrong_answers": {
            "total": user_wrong.get("stats", {}).get("total", 0),
            "mastered": user_wrong.get("stats", {}).get("mastered", 0),
            "remaining": user_wrong.get("stats", {}).get("total", 0) - user_wrong.get("stats", {}).get("mastered", 0)
        },
        "pending_reviews": len(review_items),
        "achieved_milestones": len(user_path.get("achieved_milestones", [])),
        "next_milestone": get_next_milestone(user_id)
    }

    logger.info("학습 요약 조회 완료")
    return summary
