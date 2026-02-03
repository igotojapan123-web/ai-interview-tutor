# roleplay_enhancer.py
# FlyReady Lab - 롤플레잉 기능 강화 모듈
# Phase B2: 시나리오 확대, 난이도 조절

import random
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# =============================================================================
# 1. 난이도 시스템
# =============================================================================

class DifficultyLevel(Enum):
    """난이도 레벨"""
    BEGINNER = 1       # 입문자 - 기본 상황
    INTERMEDIATE = 2   # 중급 - 복잡한 상황
    ADVANCED = 3       # 고급 - 감정적 승객
    EXPERT = 4         # 전문가 - 다중 문제 상황


@dataclass
class DifficultySettings:
    """난이도별 설정"""
    level: DifficultyLevel
    name: str
    description: str
    timer_seconds: int
    escalation_speed: float  # 감정 악화 속도 (1.0 = 기본)
    hint_available: bool
    max_turns: int
    passenger_patience: int  # 승객 인내심 (높을수록 관대)
    response_complexity: str  # simple, moderate, complex
    bonus_multiplier: float  # 점수 보너스


DIFFICULTY_PRESETS = {
    DifficultyLevel.BEGINNER: DifficultySettings(
        level=DifficultyLevel.BEGINNER,
        name="입문",
        description="기본적인 서비스 상황. 승객이 비교적 이해심 있음.",
        timer_seconds=45,
        escalation_speed=0.5,
        hint_available=True,
        max_turns=6,
        passenger_patience=8,
        response_complexity="simple",
        bonus_multiplier=1.0,
    ),
    DifficultyLevel.INTERMEDIATE: DifficultySettings(
        level=DifficultyLevel.INTERMEDIATE,
        name="중급",
        description="복잡한 요청과 기대치가 높은 승객.",
        timer_seconds=35,
        escalation_speed=0.8,
        hint_available=True,
        max_turns=8,
        passenger_patience=6,
        response_complexity="moderate",
        bonus_multiplier=1.2,
    ),
    DifficultyLevel.ADVANCED: DifficultySettings(
        level=DifficultyLevel.ADVANCED,
        name="고급",
        description="감정적이고 불만이 많은 승객. 세심한 응대 필요.",
        timer_seconds=30,
        escalation_speed=1.0,
        hint_available=False,
        max_turns=10,
        passenger_patience=4,
        response_complexity="complex",
        bonus_multiplier=1.5,
    ),
    DifficultyLevel.EXPERT: DifficultySettings(
        level=DifficultyLevel.EXPERT,
        name="전문가",
        description="다중 문제 상황. 여러 승객 동시 응대.",
        timer_seconds=25,
        escalation_speed=1.3,
        hint_available=False,
        max_turns=12,
        passenger_patience=3,
        response_complexity="complex",
        bonus_multiplier=2.0,
    ),
}


def get_difficulty_settings(level: int) -> DifficultySettings:
    """난이도 설정 가져오기"""
    try:
        diff_level = DifficultyLevel(level)
        return DIFFICULTY_PRESETS[diff_level]
    except (ValueError, KeyError):
        return DIFFICULTY_PRESETS[DifficultyLevel.INTERMEDIATE]


# =============================================================================
# 2. 연속 시나리오 (Chained Scenarios)
# =============================================================================

@dataclass
class ChainedScenario:
    """연속 시나리오 - 한 상황이 다른 상황으로 발전"""
    id: str
    title: str
    stages: List[Dict[str, Any]]  # 단계별 상황
    total_difficulty: int
    estimated_time: int  # 예상 소요 시간 (분)
    skills_tested: List[str]


CHAINED_SCENARIOS = {
    "cascade_complaint": ChainedScenario(
        id="cascade_complaint",
        title="연쇄 컴플레인 상황",
        stages=[
            {
                "stage": 1,
                "title": "음료 서비스 문제",
                "situation": "승객이 주문한 음료가 품절되었습니다.",
                "passenger_mood": "약간 실망",
                "trigger_next": "사과만 하고 대안을 제시하지 않으면",
            },
            {
                "stage": 2,
                "title": "추가 불만 제기",
                "situation": "승객이 이전 불만에 더해 좌석 리클라인이 불편하다고 합니다.",
                "passenger_mood": "짜증남",
                "trigger_next": "또 제대로 해결하지 않으면",
            },
            {
                "stage": 3,
                "title": "폭발",
                "situation": "승객이 책임자를 부르며 공식 컴플레인을 하겠다고 합니다.",
                "passenger_mood": "분노",
                "trigger_next": None,
            },
        ],
        total_difficulty=4,
        estimated_time=10,
        skills_tested=["문제 해결", "감정 관리", "에스컬레이션 방지"],
    ),
    "medical_escalation": ChainedScenario(
        id="medical_escalation",
        title="의료 상황 악화",
        stages=[
            {
                "stage": 1,
                "title": "가벼운 불편감 호소",
                "situation": "승객이 머리가 어지럽다며 물을 요청합니다.",
                "passenger_mood": "걱정됨",
                "trigger_next": "상태 체크 없이 물만 주면",
            },
            {
                "stage": 2,
                "title": "증상 악화",
                "situation": "승객이 구역질을 하며 더 안 좋아졌습니다.",
                "passenger_mood": "불안",
                "trigger_next": "의료 키트나 의사 호출 없이 방치하면",
            },
            {
                "stage": 3,
                "title": "응급 상황",
                "situation": "승객이 의식이 흐려지고 있습니다. 기내 의사를 호출해야 합니다.",
                "passenger_mood": "위급",
                "trigger_next": None,
            },
        ],
        total_difficulty=4,
        estimated_time=8,
        skills_tested=["의료 대응", "상황 판단", "응급 프로토콜"],
    ),
    "vip_service_chain": ChainedScenario(
        id="vip_service_chain",
        title="VIP 연속 서비스",
        stages=[
            {
                "stage": 1,
                "title": "특별 요청",
                "situation": "비즈니스 클래스 VIP 승객이 특별한 식사 요청을 합니다.",
                "passenger_mood": "기대감",
                "trigger_next": "요청을 제대로 처리하지 않으면",
            },
            {
                "stage": 2,
                "title": "추가 서비스",
                "situation": "승객이 와인 페어링과 디저트 추천을 요청합니다.",
                "passenger_mood": "까다로움",
                "trigger_next": "전문성 부족하면",
            },
            {
                "stage": 3,
                "title": "최종 평가",
                "situation": "승객이 전체 서비스에 대한 피드백을 줍니다.",
                "passenger_mood": "평가 중",
                "trigger_next": None,
            },
        ],
        total_difficulty=3,
        estimated_time=12,
        skills_tested=["VIP 서비스", "전문 지식", "프리미엄 응대"],
    ),
}


def get_chained_scenario(scenario_id: str) -> Optional[ChainedScenario]:
    """연속 시나리오 가져오기"""
    return CHAINED_SCENARIOS.get(scenario_id)


def get_all_chained_scenarios() -> List[ChainedScenario]:
    """모든 연속 시나리오 목록"""
    return list(CHAINED_SCENARIOS.values())


# =============================================================================
# 3. 다중 승객 시나리오
# =============================================================================

@dataclass
class MultiPassengerScenario:
    """다중 승객이 관련된 시나리오"""
    id: str
    title: str
    situation: str
    passengers: List[Dict[str, Any]]  # 복수의 승객
    conflict_type: str  # passenger_vs_passenger, group_complaint, etc.
    resolution_approach: str
    difficulty: int
    skills_tested: List[str]


MULTI_PASSENGER_SCENARIOS = {
    "family_vs_single": MultiPassengerScenario(
        id="family_vs_single",
        title="가족 vs 개인 좌석 분쟁",
        situation="4인 가족이 앉으려는 4좌석 중 1좌석에 이미 개인 승객이 앉아 있습니다. 가족은 함께 앉고 싶어하고, 개인 승객은 창가 좌석을 포기하기 싫어합니다.",
        passengers=[
            {"role": "가족 대표", "mood": "요청적", "goal": "가족 4명이 함께 앉기"},
            {"role": "개인 승객", "mood": "방어적", "goal": "창가 좌석 유지"},
        ],
        conflict_type="passenger_vs_passenger",
        resolution_approach="양측 배려하며 대안 제시",
        difficulty=3,
        skills_tested=["갈등 중재", "협상", "공정한 판단"],
    ),
    "group_complaint": MultiPassengerScenario(
        id="group_complaint",
        title="단체 승객 집단 불만",
        situation="10명의 단체 여행객이 식사 서비스가 너무 늦다며 동시에 불만을 제기합니다.",
        passengers=[
            {"role": "단체 리더", "mood": "불만", "goal": "즉시 식사 서비스"},
            {"role": "단체원 1", "mood": "동조", "goal": "리더 지지"},
            {"role": "단체원 2", "mood": "중립", "goal": "상황 관망"},
        ],
        conflict_type="group_complaint",
        resolution_approach="리더 진정시키고 전체 설명",
        difficulty=4,
        skills_tested=["군중 관리", "설득력", "시간 관리"],
    ),
    "couple_fight": MultiPassengerScenario(
        id="couple_fight",
        title="커플 싸움 중재",
        situation="젊은 커플이 기내에서 크게 싸우고 있어 주변 승객들이 불편해합니다.",
        passengers=[
            {"role": "남성 승객", "mood": "화남", "goal": "자기 입장 주장"},
            {"role": "여성 승객", "mood": "서러움", "goal": "위로받고 싶음"},
            {"role": "옆 승객", "mood": "불편", "goal": "조용히 해줬으면"},
        ],
        conflict_type="passenger_internal",
        resolution_approach="각자 진정시키고 공간 분리 제안",
        difficulty=3,
        skills_tested=["감정 관리", "분리 대응", "프라이버시 배려"],
    ),
}


def get_multi_passenger_scenario(scenario_id: str) -> Optional[MultiPassengerScenario]:
    """다중 승객 시나리오 가져오기"""
    return MULTI_PASSENGER_SCENARIOS.get(scenario_id)


# =============================================================================
# 4. 적응형 난이도 시스템
# =============================================================================

class AdaptiveDifficultyManager:
    """사용자 성과 기반 적응형 난이도 관리"""

    def __init__(self):
        self.history = []  # 최근 성과 기록

    def record_performance(self, scenario_id: str, score: int, difficulty: int,
                          response_times: List[float], escalation_reached: int):
        """성과 기록"""
        self.history.append({
            "scenario_id": scenario_id,
            "score": score,
            "difficulty": difficulty,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "escalation_reached": escalation_reached,
            "timestamp": datetime.now().isoformat(),
        })
        # 최근 20개만 유지
        self.history = self.history[-20:]

    def get_recommended_difficulty(self) -> int:
        """추천 난이도 계산"""
        if len(self.history) < 3:
            return 2  # 기본 중급

        recent = self.history[-5:]
        avg_score = sum(h["score"] for h in recent) / len(recent)
        avg_difficulty = sum(h["difficulty"] for h in recent) / len(recent)
        avg_escalation = sum(h["escalation_reached"] for h in recent) / len(recent)

        # 점수 기반 조정
        if avg_score >= 85 and avg_escalation < 1:
            recommended = min(4, int(avg_difficulty) + 1)
        elif avg_score < 60 or avg_escalation >= 2:
            recommended = max(1, int(avg_difficulty) - 1)
        else:
            recommended = int(avg_difficulty)

        return recommended

    def get_skill_analysis(self) -> Dict[str, Any]:
        """스킬 분석"""
        if len(self.history) < 5:
            return {"status": "insufficient_data", "message": "분석을 위해 더 많은 연습이 필요합니다."}

        recent = self.history[-10:]

        # 평균 계산
        avg_score = sum(h["score"] for h in recent) / len(recent)
        avg_response_time = sum(h["avg_response_time"] for h in recent) / len(recent)
        avg_escalation = sum(h["escalation_reached"] for h in recent) / len(recent)

        # 강점/약점 파악
        strengths = []
        weaknesses = []

        if avg_score >= 80:
            strengths.append("전반적인 응대 능력 우수")
        else:
            weaknesses.append("응대 스킬 향상 필요")

        if avg_response_time <= 15:
            strengths.append("빠른 응답 속도")
        elif avg_response_time > 25:
            weaknesses.append("응답 속도 개선 필요")

        if avg_escalation < 1:
            strengths.append("승객 감정 관리 우수")
        elif avg_escalation >= 2:
            weaknesses.append("감정 에스컬레이션 방지 필요")

        return {
            "status": "analyzed",
            "avg_score": avg_score,
            "avg_response_time": avg_response_time,
            "avg_escalation": avg_escalation,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommended_focus": weaknesses[0] if weaknesses else "현재 수준 유지",
        }

    def get_scenario_recommendations(self, all_scenarios: Dict) -> List[str]:
        """스킬 기반 시나리오 추천"""
        analysis = self.get_skill_analysis()
        if analysis["status"] != "analyzed":
            return list(all_scenarios.keys())[:5]

        recommended = []
        difficulty = self.get_recommended_difficulty()

        # 난이도에 맞는 시나리오 필터링
        for sid, scenario in all_scenarios.items():
            if scenario.get("difficulty", 2) == difficulty:
                recommended.append(sid)

        # 약점 기반 추천
        if "감정 에스컬레이션" in analysis.get("weaknesses", []):
            # 감정 관리 연습 시나리오 추가
            for sid, scenario in all_scenarios.items():
                if "불만" in scenario.get("category", "") or "컴플레인" in scenario.get("category", ""):
                    if sid not in recommended:
                        recommended.insert(0, sid)

        return recommended[:8]


# 전역 난이도 관리자
adaptive_difficulty_manager = AdaptiveDifficultyManager()


# =============================================================================
# 5. 향상된 승객 응답 시스템
# =============================================================================

class EnhancedPassengerBehavior:
    """향상된 승객 행동 시스템"""

    MOOD_STATES = {
        "calm": {"emoji": "😊", "patience": 10, "response_style": "cooperative"},
        "impatient": {"emoji": "😤", "patience": 5, "response_style": "demanding"},
        "angry": {"emoji": "😡", "patience": 2, "response_style": "confrontational"},
        "anxious": {"emoji": "😰", "patience": 7, "response_style": "nervous"},
        "sad": {"emoji": "😢", "patience": 8, "response_style": "emotional"},
        "confused": {"emoji": "😕", "patience": 6, "response_style": "questioning"},
    }

    PERSONALITY_TYPES = {
        "diplomatic": {
            "name": "외교적",
            "description": "이해심 있고 타협하려 함",
            "escalation_threshold": 4,
            "deescalation_chance": 0.6,
        },
        "demanding": {
            "name": "요구적",
            "description": "높은 기대치, 즉각적인 해결 원함",
            "escalation_threshold": 2,
            "deescalation_chance": 0.3,
        },
        "emotional": {
            "name": "감정적",
            "description": "감정에 따라 반응, 공감에 민감",
            "escalation_threshold": 3,
            "deescalation_chance": 0.5,
        },
        "logical": {
            "name": "논리적",
            "description": "합리적 설명에 반응, 감정보다 이유 중시",
            "escalation_threshold": 3,
            "deescalation_chance": 0.4,
        },
        "vip": {
            "name": "VIP",
            "description": "특별 대우 기대, 불만 시 공식 컴플레인",
            "escalation_threshold": 2,
            "deescalation_chance": 0.2,
        },
    }

    @staticmethod
    def get_mood_info(mood: str) -> Dict[str, Any]:
        """기분 정보 가져오기"""
        return EnhancedPassengerBehavior.MOOD_STATES.get(
            mood, EnhancedPassengerBehavior.MOOD_STATES["calm"]
        )

    @staticmethod
    def get_personality_info(personality: str) -> Dict[str, Any]:
        """성격 정보 가져오기"""
        return EnhancedPassengerBehavior.PERSONALITY_TYPES.get(
            personality, EnhancedPassengerBehavior.PERSONALITY_TYPES["diplomatic"]
        )

    @staticmethod
    def should_escalate(
        current_level: int,
        response_quality: str,  # good, neutral, poor
        personality: str,
        turn_count: int
    ) -> Tuple[bool, int]:
        """감정 에스컬레이션 여부 결정

        Returns:
            (should_escalate, new_level)
        """
        personality_info = EnhancedPassengerBehavior.get_personality_info(personality)
        threshold = personality_info["escalation_threshold"]
        deescalation_chance = personality_info["deescalation_chance"]

        if response_quality == "good":
            # 좋은 응대 시 진정 확률
            if random.random() < deescalation_chance:
                return False, max(0, current_level - 1)
            return False, current_level

        elif response_quality == "poor":
            # 나쁜 응대 시 에스컬레이션
            if turn_count >= threshold:
                return True, min(2, current_level + 1)
            return False, current_level

        else:  # neutral
            # 중립 응대 시 턴 수에 따라
            if turn_count > threshold * 2:
                return True, min(2, current_level + 1)
            return False, current_level

    @staticmethod
    def evaluate_response_quality(
        response: str,
        keywords: List[str],
        scenario_type: str
    ) -> str:
        """응답 품질 평가 (간단 버전)"""
        response_lower = response.lower()

        # 키워드 매칭
        keyword_count = sum(1 for kw in keywords if kw in response_lower or kw in response)

        # 공감 표현 체크
        empathy_phrases = ["죄송", "불편", "이해", "공감", "말씀", "도와드리"]
        empathy_count = sum(1 for phrase in empathy_phrases if phrase in response)

        # 해결책 제시 체크
        solution_phrases = ["해드리", "제공", "대안", "다른", "방법", "도와"]
        solution_count = sum(1 for phrase in solution_phrases if phrase in response)

        score = keyword_count * 2 + empathy_count * 3 + solution_count * 2

        if score >= 6:
            return "good"
        elif score >= 3:
            return "neutral"
        else:
            return "poor"


# =============================================================================
# 6. 시나리오 생성 도우미
# =============================================================================

def generate_dynamic_scenario(
    category: str,
    difficulty: int,
    custom_params: Optional[Dict] = None
) -> Dict[str, Any]:
    """동적 시나리오 생성 (기본 템플릿 기반)"""

    templates = {
        "좌석 관련": {
            "situations": [
                "승객이 {reason}로 좌석 변경을 요청합니다.",
                "두 승객이 좌석 {conflict}로 다투고 있습니다.",
                "{passenger_type} 승객이 특별 좌석을 요구합니다.",
            ],
            "reasons": ["허리가 아파서", "아이와 떨어져서", "옆 승객이 시끄러워서"],
            "conflicts": ["리클라인", "팔걸이", "창문 가리개"],
            "passenger_types": ["노약자", "VIP", "단체 여행객"],
        },
        "기내 서비스": {
            "situations": [
                "승객이 {food_issue}라며 불만을 표합니다.",
                "{service_type} 서비스가 지연되어 승객이 화가 났습니다.",
                "승객이 {special_request}를 요청합니다.",
            ],
            "food_issues": ["음식이 차갑다", "알레르기 식단이 아니다", "음료가 품절됐다"],
            "service_types": ["식사", "음료", "면세품"],
            "special_requests": ["특별 디저트", "와인 추천", "채식 메뉴"],
        },
    }

    template = templates.get(category, templates["기내 서비스"])
    situation_template = random.choice(template["situations"])

    # 템플릿 채우기
    situation = situation_template
    for key in ["reason", "conflict", "passenger_type", "food_issue",
                "service_type", "special_request"]:
        plural_key = key + "s"
        if "{" + key + "}" in situation and plural_key in template:
            situation = situation.replace("{" + key + "}", random.choice(template[plural_key]))

    # 난이도에 따른 조정
    mood_levels = {1: "정중함", 2: "약간 불만", 3: "짜증남", 4: "분노"}
    patience_levels = {1: 8, 2: 6, 3: 4, 4: 2}

    return {
        "category": category,
        "title": f"[동적] {category} 상황",
        "difficulty": difficulty,
        "situation": situation,
        "passenger_mood": mood_levels.get(difficulty, "정중함"),
        "passenger_patience": patience_levels.get(difficulty, 6),
        "generated": True,
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# 편의 함수
# =============================================================================

def get_difficulty_info(level: int) -> Dict[str, Any]:
    """난이도 정보 반환"""
    settings = get_difficulty_settings(level)
    return {
        "level": settings.level.value,
        "name": settings.name,
        "description": settings.description,
        "timer": settings.timer_seconds,
        "hints_available": settings.hint_available,
        "bonus": settings.bonus_multiplier,
    }


def calculate_final_score(
    base_score: int,
    difficulty: int,
    response_time_avg: float,
    escalation_avoided: bool
) -> int:
    """최종 점수 계산"""
    settings = get_difficulty_settings(difficulty)

    # 기본 점수에 난이도 보너스 적용
    score = base_score * settings.bonus_multiplier

    # 응답 시간 보너스/감점
    if response_time_avg < 10:
        score *= 1.1  # 빠른 응답 보너스
    elif response_time_avg > 25:
        score *= 0.9  # 느린 응답 감점

    # 에스컬레이션 방지 보너스
    if escalation_avoided:
        score *= 1.15

    return min(100, int(score))


def get_performance_feedback(score: int, difficulty: int, analysis: Dict) -> str:
    """성과 피드백 생성"""
    if score >= 90:
        grade = "S"
        message = "탁월한 응대입니다! 전문 승무원 수준의 역량을 보여주셨습니다."
    elif score >= 80:
        grade = "A"
        message = "우수한 응대입니다. 대부분의 상황을 잘 처리하셨습니다."
    elif score >= 70:
        grade = "B"
        message = "양호한 응대입니다. 몇 가지 개선점이 있습니다."
    elif score >= 60:
        grade = "C"
        message = "보통 수준입니다. 더 많은 연습이 필요합니다."
    else:
        grade = "D"
        message = "개선이 필요합니다. 기본 응대 스킬을 연습해보세요."

    strengths = analysis.get("strengths", [])
    weaknesses = analysis.get("weaknesses", [])

    feedback = f"""
### {grade} 등급 ({score}점)

{message}

**강점:**
{chr(10).join(['- ' + s for s in strengths]) if strengths else '- 분석 중'}

**개선점:**
{chr(10).join(['- ' + w for w in weaknesses]) if weaknesses else '- 없음'}

**다음 연습 추천 난이도:** {analysis.get('recommended_focus', '중급')}
"""
    return feedback


# =============================================================================
# 모듈 테스트
# =============================================================================

if __name__ == "__main__":
    print("=== Roleplay Enhancer Test ===")

    # 1. 난이도 설정 테스트
    print("\n1. Difficulty Settings")
    for level in range(1, 5):
        settings = get_difficulty_settings(level)
        print(f"   Level {level}: {settings.name} - Timer: {settings.timer_seconds}s, Bonus: {settings.bonus_multiplier}x")

    # 2. 연속 시나리오 테스트
    print("\n2. Chained Scenarios")
    for scenario in get_all_chained_scenarios():
        print(f"   {scenario.title}: {len(scenario.stages)} stages, Difficulty: {scenario.total_difficulty}")

    # 3. 다중 승객 시나리오 테스트
    print("\n3. Multi-Passenger Scenarios")
    for sid, scenario in MULTI_PASSENGER_SCENARIOS.items():
        print(f"   {scenario.title}: {len(scenario.passengers)} passengers")

    # 4. 적응형 난이도 테스트
    print("\n4. Adaptive Difficulty")
    manager = AdaptiveDifficultyManager()
    manager.record_performance("test1", 75, 2, [12, 15, 18], 1)
    manager.record_performance("test2", 82, 2, [10, 12, 14], 0)
    manager.record_performance("test3", 88, 2, [8, 10, 12], 0)
    print(f"   Recommended difficulty: {manager.get_recommended_difficulty()}")

    # 5. 동적 시나리오 생성 테스트
    print("\n5. Dynamic Scenario")
    dynamic = generate_dynamic_scenario("좌석 관련", 2)
    print(f"   Generated: {dynamic['situation']}")

    print("\nModule ready!")
