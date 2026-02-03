# -*- coding: utf-8 -*-
"""
user_experience_enhancer.py
A. 심리적/감정적 (-) 해결 모듈

해결하는 문제:
1. 막막함 → 맞춤 학습 경로 자동 생성
2. 불안함 → 합격선 예측 시스템
3. 외로움 → 동료 매칭 시스템
4. 지침 → 스트릭/미션/경쟁 시스템
5. 자신감 부족 → 실시간 격려 피드백
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import random
import json


# ============================================================
# 1. 막막함 해결: 맞춤 학습 경로 자동 생성
# ============================================================

class SkillLevel(Enum):
    """스킬 레벨"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningCategory(Enum):
    """학습 카테고리"""
    INTERVIEW_KOREAN = "korean_interview"
    INTERVIEW_ENGLISH = "english_interview"
    ROLEPLAY = "roleplay"
    DEBATE = "debate"
    RESUME = "resume"
    EXPRESSION = "expression"
    POSTURE = "posture"
    VOICE = "voice"


@dataclass
class LearningStep:
    """학습 단계"""
    step_number: int
    category: str
    title: str
    description: str
    estimated_time: int  # 분
    priority: int  # 1-5
    is_completed: bool = False
    recommended_pages: List[str] = field(default_factory=list)


@dataclass
class LearningPath:
    """맞춤 학습 경로"""
    user_id: str
    target_airline: str
    target_date: Optional[datetime]
    steps: List[LearningStep]
    created_at: datetime
    current_step: int = 0
    total_estimated_hours: float = 0.0

    @property
    def progress_percent(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.is_completed)
        return (completed / len(self.steps)) * 100

    @property
    def remaining_steps(self) -> int:
        return sum(1 for s in self.steps if not s.is_completed)


class LearningPathGenerator:
    """맞춤 학습 경로 생성기"""

    # 카테고리별 기본 학습 단계
    CATEGORY_STEPS = {
        LearningCategory.INTERVIEW_KOREAN: [
            ("자기소개 연습", "1분 자기소개를 완성하세요", 30, ["4_모의면접.py"]),
            ("지원동기 답변", "항공사 지원동기를 준비하세요", 30, ["4_모의면접.py"]),
            ("인성 질문 연습", "장단점, 갈등해결 등 연습", 45, ["4_모의면접.py"]),
            ("꼬리질문 대비", "예상 꼬리질문에 대비하세요", 40, ["13_실전연습.py"]),
            ("압박면접 연습", "압박 상황에서 침착하게 대응", 45, ["13_실전연습.py"]),
        ],
        LearningCategory.INTERVIEW_ENGLISH: [
            ("영어 자기소개", "영어로 자기소개하기", 30, ["2_영어면접.py"]),
            ("기본 질문 연습", "Why cabin crew? 등 기본 질문", 40, ["2_영어면접.py"]),
            ("상황 설명 영어", "경험을 영어로 설명하기", 45, ["2_영어면접.py"]),
            ("발음 교정", "정확한 발음으로 말하기", 30, ["2_영어면접.py"]),
        ],
        LearningCategory.ROLEPLAY: [
            ("기본 서비스 상황", "음료/식사 서비스 연습", 30, ["1_롤플레잉.py"]),
            ("컴플레인 대응", "불만 고객 응대하기", 40, ["1_롤플레잉.py"]),
            ("비상 상황 대처", "기내 비상상황 대응", 45, ["1_롤플레잉.py"]),
            ("다중 승객 상황", "여러 승객 동시 응대", 40, ["1_롤플레잉.py"]),
        ],
        LearningCategory.DEBATE: [
            ("논리적 주장 연습", "찬반 논거 구성하기", 30, ["5_토론면접.py"]),
            ("반론 대응", "상대 반론에 대응하기", 40, ["5_토론면접.py"]),
            ("그룹 토론 참여", "다자 토론에서 존재감", 45, ["5_토론면접.py"]),
        ],
        LearningCategory.RESUME: [
            ("자소서 작성", "항공사별 자소서 작성", 60, ["21_자소서템플릿.py"]),
            ("자소서 첨삭", "AI 피드백으로 개선", 40, ["20_자소서첨삭.py"]),
            ("예상 질문 준비", "자소서 기반 질문 대비", 45, ["17_자소서기반질문.py"]),
        ],
        LearningCategory.EXPRESSION: [
            ("미소 연습", "자연스러운 미소 만들기", 20, ["12_표정연습.py"]),
            ("눈맞춤 연습", "적절한 눈맞춤 유지", 20, ["12_표정연습.py"]),
            ("표정 일관성", "답변 중 표정 유지하기", 30, ["12_표정연습.py"]),
        ],
        LearningCategory.POSTURE: [
            ("기본 자세", "바른 자세로 앉기", 15, ["12_표정연습.py"]),
            ("손동작 연습", "적절한 제스처 사용", 20, ["12_표정연습.py"]),
            ("자세 일관성", "답변 중 자세 유지", 25, ["12_표정연습.py"]),
        ],
        LearningCategory.VOICE: [
            ("발성 연습", "명확하게 말하기", 20, ["26_기내방송연습.py"]),
            ("속도 조절", "적절한 속도로 말하기", 20, ["26_기내방송연습.py"]),
            ("톤 변화", "단조롭지 않게 말하기", 25, ["26_기내방송연습.py"]),
        ],
    }

    # 항공사별 중점 카테고리
    AIRLINE_PRIORITIES = {
        "대한항공": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.INTERVIEW_ENGLISH, LearningCategory.RESUME],
        "아시아나항공": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.RESUME],
        "진에어": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.EXPRESSION],
        "제주항공": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.DEBATE, LearningCategory.ROLEPLAY],
        "티웨이항공": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.VOICE],
        "에어부산": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.EXPRESSION],
        "에어서울": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.INTERVIEW_ENGLISH, LearningCategory.ROLEPLAY],
        "이스타항공": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.POSTURE],
        "에어프레미아": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.INTERVIEW_ENGLISH, LearningCategory.DEBATE],
        "플라이강원": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.VOICE],
        "에어로케이": [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.EXPRESSION],
    }

    def __init__(self):
        pass

    def generate_path(
        self,
        user_id: str,
        target_airline: str,
        target_date: Optional[datetime] = None,
        skill_levels: Optional[Dict[str, SkillLevel]] = None,
        weak_areas: Optional[List[str]] = None
    ) -> LearningPath:
        """맞춤 학습 경로 생성"""

        steps: List[LearningStep] = []
        step_number = 1

        # 항공사별 우선순위 카테고리 가져오기
        priority_categories = self.AIRLINE_PRIORITIES.get(
            target_airline,
            [LearningCategory.INTERVIEW_KOREAN, LearningCategory.ROLEPLAY, LearningCategory.RESUME]
        )

        # 약점 영역이 있으면 우선순위에 추가
        if weak_areas:
            for area in weak_areas:
                try:
                    cat = LearningCategory(area)
                    if cat not in priority_categories:
                        priority_categories.insert(0, cat)
                except ValueError:
                    pass

        # 우선순위 순서로 학습 단계 추가
        for priority, category in enumerate(priority_categories, 1):
            category_steps = self.CATEGORY_STEPS.get(category, [])

            for title, desc, time_min, pages in category_steps:
                steps.append(LearningStep(
                    step_number=step_number,
                    category=category.value,
                    title=title,
                    description=desc,
                    estimated_time=time_min,
                    priority=min(priority, 5),
                    recommended_pages=pages
                ))
                step_number += 1

        # 나머지 카테고리도 추가 (낮은 우선순위)
        for category in LearningCategory:
            if category not in priority_categories:
                category_steps = self.CATEGORY_STEPS.get(category, [])
                for title, desc, time_min, pages in category_steps:
                    steps.append(LearningStep(
                        step_number=step_number,
                        category=category.value,
                        title=title,
                        description=desc,
                        estimated_time=time_min,
                        priority=5,
                        recommended_pages=pages
                    ))
                    step_number += 1

        # 총 예상 시간 계산
        total_minutes = sum(s.estimated_time for s in steps)
        total_hours = total_minutes / 60

        return LearningPath(
            user_id=user_id,
            target_airline=target_airline,
            target_date=target_date,
            steps=steps,
            created_at=datetime.now(),
            total_estimated_hours=total_hours
        )

    def get_next_recommended_step(self, path: LearningPath) -> Optional[LearningStep]:
        """다음 추천 학습 단계"""
        for step in path.steps:
            if not step.is_completed:
                return step
        return None

    def get_daily_plan(self, path: LearningPath, available_minutes: int = 60) -> List[LearningStep]:
        """오늘의 학습 계획"""
        daily_steps = []
        remaining_time = available_minutes

        for step in path.steps:
            if not step.is_completed and step.estimated_time <= remaining_time:
                daily_steps.append(step)
                remaining_time -= step.estimated_time
                if remaining_time <= 0:
                    break

        return daily_steps


# ============================================================
# 2. 불안함 해결: 합격선 예측 시스템
# ============================================================

@dataclass
class PredictionResult:
    """합격 예측 결과"""
    current_score: float
    target_score: float  # 합격선
    gap: float
    predicted_days: int  # 예상 도달 일수
    confidence: float  # 예측 신뢰도 (0-100)
    trend: str  # "improving", "stable", "declining"
    message: str
    recommendations: List[str]


class PassPredictionSystem:
    """합격선 예측 시스템"""

    # 항공사별 예상 합격선
    PASS_THRESHOLDS = {
        "대한항공": 85,
        "아시아나항공": 83,
        "진에어": 78,
        "제주항공": 77,
        "티웨이항공": 76,
        "에어부산": 75,
        "에어서울": 77,
        "이스타항공": 74,
        "에어프레미아": 80,
        "플라이강원": 73,
        "에어로케이": 73,
    }

    def __init__(self):
        pass

    def predict(
        self,
        airline: str,
        score_history: List[Dict],  # [{"date": datetime, "score": float, "category": str}]
        practice_frequency: float = 1.0  # 일 평균 연습 횟수
    ) -> PredictionResult:
        """합격 가능성 예측"""

        target_score = self.PASS_THRESHOLDS.get(airline, 80)

        if not score_history:
            return PredictionResult(
                current_score=0,
                target_score=target_score,
                gap=target_score,
                predicted_days=90,
                confidence=10,
                trend="stable",
                message="아직 연습 기록이 없습니다. 첫 연습을 시작해보세요!",
                recommendations=["모의면접 시작하기", "자기소개 연습하기"]
            )

        # 최근 점수 계산
        recent_scores = [s["score"] for s in score_history[-10:]]
        current_score = sum(recent_scores) / len(recent_scores)

        # 트렌드 분석
        if len(score_history) >= 5:
            older = sum(s["score"] for s in score_history[-10:-5]) / min(5, len(score_history) - 5) if len(score_history) > 5 else current_score
            newer = sum(s["score"] for s in score_history[-5:]) / 5

            if newer > older + 2:
                trend = "improving"
                daily_improvement = (newer - older) / 5
            elif newer < older - 2:
                trend = "declining"
                daily_improvement = 0.1  # 기본값
            else:
                trend = "stable"
                daily_improvement = 0.3  # 기본값
        else:
            trend = "stable"
            daily_improvement = 0.5

        # 예상 도달 일수 계산
        gap = target_score - current_score
        if gap <= 0:
            predicted_days = 0
        else:
            # 연습 빈도 고려
            effective_improvement = daily_improvement * practice_frequency
            if effective_improvement > 0:
                predicted_days = int(gap / effective_improvement)
            else:
                predicted_days = 180  # 최대값

        # 신뢰도 계산
        confidence = min(90, 30 + len(score_history) * 3)

        # 메시지 생성
        if gap <= 0:
            message = f"축하합니다! 이미 {airline} 합격선을 넘었습니다!"
        elif predicted_days <= 14:
            message = f"잘하고 있어요! 약 {predicted_days}일 후면 합격선에 도달할 것 같습니다."
        elif predicted_days <= 30:
            message = f"꾸준히 연습하면 약 {predicted_days}일 후 합격선에 도달할 수 있습니다."
        else:
            message = f"현재 속도로 약 {predicted_days}일이 예상됩니다. 연습량을 늘려보세요!"

        # 추천 사항
        recommendations = []
        if trend == "declining":
            recommendations.append("최근 점수가 하락 중입니다. 기본기를 다시 점검해보세요.")
        if gap > 15:
            recommendations.append("약점 카테고리에 집중하세요.")
        if practice_frequency < 1:
            recommendations.append("매일 연습하면 더 빨리 합격선에 도달할 수 있습니다.")
        if not recommendations:
            recommendations.append("현재 페이스를 유지하세요!")

        return PredictionResult(
            current_score=round(current_score, 1),
            target_score=target_score,
            gap=round(max(0, gap), 1),
            predicted_days=predicted_days,
            confidence=confidence,
            trend=trend,
            message=message,
            recommendations=recommendations
        )


# ============================================================
# 3. 외로움 해결: 동료 매칭 시스템
# ============================================================

@dataclass
class StudyPartner:
    """스터디 파트너"""
    user_id: str
    nickname: str
    target_airline: str
    skill_level: str
    practice_time: str  # "morning", "afternoon", "evening", "night"
    study_style: str  # "intensive", "regular", "casual"
    introduction: str


@dataclass
class PartnerMatch:
    """파트너 매칭 결과"""
    partner: StudyPartner
    compatibility_score: float
    match_reasons: List[str]


class PartnerMatchingSystem:
    """동료 매칭 시스템"""

    def __init__(self):
        # 시뮬레이션용 더미 파트너 (실제로는 DB에서 가져옴)
        self.dummy_partners = [
            StudyPartner("user_001", "하늘이", "대한항공", "intermediate", "evening", "regular", "함께 열심히 해요!"),
            StudyPartner("user_002", "구름이", "아시아나항공", "beginner", "morning", "intensive", "매일 아침 연습합니다"),
            StudyPartner("user_003", "별이", "진에어", "advanced", "afternoon", "regular", "경험 나눠요~"),
            StudyPartner("user_004", "달이", "대한항공", "intermediate", "night", "casual", "편하게 연습해요"),
            StudyPartner("user_005", "해이", "제주항공", "beginner", "evening", "intensive", "열정 가득!"),
        ]

    def find_partners(
        self,
        user_airline: str,
        user_level: str = "intermediate",
        user_time: str = "evening",
        user_style: str = "regular",
        limit: int = 5
    ) -> List[PartnerMatch]:
        """호환되는 파트너 찾기"""

        matches = []

        for partner in self.dummy_partners:
            score = 0
            reasons = []

            # 같은 항공사 +30점
            if partner.target_airline == user_airline:
                score += 30
                reasons.append(f"같은 {user_airline} 지원자")

            # 비슷한 레벨 +25점
            if partner.skill_level == user_level:
                score += 25
                reasons.append("비슷한 실력 수준")

            # 같은 시간대 +25점
            if partner.practice_time == user_time:
                score += 25
                reasons.append("같은 시간대 연습")

            # 같은 스터디 스타일 +20점
            if partner.study_style == user_style:
                score += 20
                reasons.append("같은 학습 스타일")

            if score > 0:
                matches.append(PartnerMatch(
                    partner=partner,
                    compatibility_score=score,
                    match_reasons=reasons
                ))

        # 점수 순 정렬
        matches.sort(key=lambda m: m.compatibility_score, reverse=True)

        return matches[:limit]

    def create_study_room(self, partner_ids: List[str], room_name: str) -> Dict:
        """스터디룸 생성"""
        return {
            "room_id": f"room_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "room_name": room_name,
            "members": partner_ids,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }


# ============================================================
# 4. 지침 해결: 스트릭/미션/경쟁 시스템
# ============================================================

@dataclass
class DailyMission:
    """일일 미션"""
    mission_id: str
    title: str
    description: str
    category: str
    target_count: int
    current_count: int
    reward_points: int
    is_completed: bool = False

    @property
    def progress_percent(self) -> float:
        if self.target_count == 0:
            return 100.0
        return min(100.0, (self.current_count / self.target_count) * 100)


@dataclass
class StreakInfo:
    """연속 학습 정보"""
    current_streak: int
    longest_streak: int
    last_practice_date: Optional[datetime]
    streak_rewards: List[Dict]  # 획득한 보상들


@dataclass
class LeaderboardEntry:
    """리더보드 항목"""
    rank: int
    user_id: str
    nickname: str
    score: float
    streak: int
    badge: str


class GamificationSystem:
    """게임화 시스템"""

    # 미션 템플릿
    MISSION_TEMPLATES = [
        ("daily_practice", "오늘의 연습", "모의면접 1회 완료하기", "interview", 1, 10),
        ("streak_3", "3일 연속 출석", "3일 연속 연습하기", "streak", 3, 30),
        ("high_score", "고득점 달성", "80점 이상 받기", "score", 1, 20),
        ("multi_category", "다양한 연습", "3가지 카테고리 연습하기", "variety", 3, 25),
        ("voice_practice", "음성 연습", "음성 분석 포함 연습 2회", "voice", 2, 15),
        ("resume_check", "자소서 점검", "자소서 첨삭 받기", "resume", 1, 15),
        ("expression_practice", "표정 연습", "표정 연습 10분", "expression", 1, 10),
    ]

    # 스트릭 보상
    STREAK_REWARDS = {
        3: {"type": "badge", "name": "3일 연속", "description": "3일 연속 학습 달성!"},
        7: {"type": "badge", "name": "일주일 완주", "description": "7일 연속 학습 달성!"},
        14: {"type": "badge", "name": "2주 챔피언", "description": "14일 연속 학습 달성!"},
        30: {"type": "badge", "name": "한 달 마스터", "description": "30일 연속 학습 달성!"},
        50: {"type": "special", "name": "불굴의 의지", "description": "50일 연속 학습 달성!"},
        100: {"type": "legendary", "name": "레전드", "description": "100일 연속 학습 달성!"},
    }

    def __init__(self):
        pass

    def get_daily_missions(self, user_id: str, completed_today: List[str] = None) -> List[DailyMission]:
        """오늘의 미션 목록"""
        if completed_today is None:
            completed_today = []

        missions = []
        for mission_id, title, desc, category, target, reward in self.MISSION_TEMPLATES[:5]:  # 하루 5개
            missions.append(DailyMission(
                mission_id=mission_id,
                title=title,
                description=desc,
                category=category,
                target_count=target,
                current_count=1 if mission_id in completed_today else 0,
                reward_points=reward,
                is_completed=mission_id in completed_today
            ))

        return missions

    def check_streak(self, practice_dates: List[datetime]) -> StreakInfo:
        """스트릭 확인"""
        if not practice_dates:
            return StreakInfo(
                current_streak=0,
                longest_streak=0,
                last_practice_date=None,
                streak_rewards=[]
            )

        # 날짜 정렬
        sorted_dates = sorted(set(d.date() for d in practice_dates))

        # 현재 스트릭 계산
        today = datetime.now().date()
        current_streak = 0

        for i in range(len(sorted_dates) - 1, -1, -1):
            expected_date = today - timedelta(days=len(sorted_dates) - 1 - i)
            if sorted_dates[i] == today - timedelta(days=current_streak):
                current_streak += 1
            else:
                break

        # 최장 스트릭 계산
        longest_streak = 1
        temp_streak = 1

        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1

        # 보상 확인
        rewards = []
        for streak_days, reward in self.STREAK_REWARDS.items():
            if current_streak >= streak_days:
                rewards.append(reward)

        return StreakInfo(
            current_streak=current_streak,
            longest_streak=max(longest_streak, current_streak),
            last_practice_date=practice_dates[-1] if practice_dates else None,
            streak_rewards=rewards
        )

    def get_leaderboard(self, airline: str = None, limit: int = 10) -> List[LeaderboardEntry]:
        """리더보드 조회 (더미 데이터)"""
        # 실제로는 DB에서 가져옴
        dummy_entries = [
            LeaderboardEntry(1, "user_top1", "합격예정자", 92.5, 45, "legendary"),
            LeaderboardEntry(2, "user_top2", "열정가득", 89.3, 32, "special"),
            LeaderboardEntry(3, "user_top3", "승무원꿈", 87.1, 28, "badge"),
            LeaderboardEntry(4, "user_top4", "하늘사랑", 85.8, 21, "badge"),
            LeaderboardEntry(5, "user_top5", "파이팅", 84.2, 18, "badge"),
            LeaderboardEntry(6, "user_top6", "노력중", 82.5, 14, "badge"),
            LeaderboardEntry(7, "user_top7", "시작이반", 80.1, 10, "badge"),
            LeaderboardEntry(8, "user_top8", "화이팅", 78.9, 7, ""),
            LeaderboardEntry(9, "user_top9", "도전자", 76.5, 5, ""),
            LeaderboardEntry(10, "user_top10", "새싹", 74.2, 3, ""),
        ]

        return dummy_entries[:limit]


# ============================================================
# 5. 자신감 부족 해결: 실시간 격려 피드백
# ============================================================

class EncouragementLevel(Enum):
    """격려 수준"""
    EXCELLENT = "excellent"
    GOOD = "good"
    IMPROVING = "improving"
    KEEP_GOING = "keep_going"
    STRUGGLING = "struggling"


@dataclass
class EncouragementMessage:
    """격려 메시지"""
    level: EncouragementLevel
    message: str
    emoji: str
    tip: Optional[str] = None


class RealTimeEncouragementSystem:
    """실시간 격려 피드백 시스템"""

    # 상황별 격려 메시지
    MESSAGES = {
        EncouragementLevel.EXCELLENT: [
            ("완벽해요! 면접관도 감동할 거예요!", "star", "이 컨디션 유지하세요!"),
            ("대단해요! 합격이 눈앞이에요!", "fire", None),
            ("최고예요! 자신감 넘치는 모습이 멋져요!", "trophy", None),
            ("훌륭합니다! 프로 승무원 같아요!", "airplane", None),
        ],
        EncouragementLevel.GOOD: [
            ("잘하고 있어요! 조금만 더!", "thumbsup", "속도를 조금만 천천히 해보세요"),
            ("좋아요! 이 조자로 계속 가세요!", "clap", None),
            ("멋져요! 점점 나아지고 있어요!", "sparkles", None),
            ("훌륭해요! 거의 다 왔어요!", "muscle", None),
        ],
        EncouragementLevel.IMPROVING: [
            ("성장하고 있어요! 포기하지 마세요!", "seedling", "기본에 충실하면 됩니다"),
            ("발전 중이에요! 믿어요!", "chart_up", None),
            ("한 걸음씩 나아가고 있어요!", "footprints", None),
            ("어제보다 오늘 더 나아졌어요!", "sunrise", None),
        ],
        EncouragementLevel.KEEP_GOING: [
            ("괜찮아요, 누구나 처음은 어려워요", "hug", "천천히 다시 해보세요"),
            ("실수해도 괜찮아요, 연습이니까요!", "rainbow", None),
            ("포기하지 마세요! 할 수 있어요!", "heart", None),
            ("오늘 하루가 내일의 밑거름이에요!", "plant", None),
        ],
        EncouragementLevel.STRUGGLING: [
            ("힘들죠? 잠깐 쉬어도 괜찮아요", "coffee", "5분 휴식 후 다시 시도해보세요"),
            ("지금 힘든 게 당연해요, 성장통이에요", "butterfly", None),
            ("포기하고 싶을 때가 성장 직전이에요!", "diamond", None),
            ("당신은 이미 충분히 노력하고 있어요", "star2", None),
        ],
    }

    def __init__(self):
        pass

    def get_encouragement(
        self,
        score: float,
        previous_score: Optional[float] = None,
        streak: int = 0,
        time_of_day: str = "afternoon"
    ) -> EncouragementMessage:
        """상황에 맞는 격려 메시지"""

        # 점수 기반 레벨 결정
        if score >= 85:
            level = EncouragementLevel.EXCELLENT
        elif score >= 70:
            level = EncouragementLevel.GOOD
        elif score >= 55:
            level = EncouragementLevel.IMPROVING
        elif score >= 40:
            level = EncouragementLevel.KEEP_GOING
        else:
            level = EncouragementLevel.STRUGGLING

        # 이전 점수 대비 향상됐으면 레벨 업
        if previous_score and score > previous_score + 5:
            if level == EncouragementLevel.GOOD:
                level = EncouragementLevel.EXCELLENT
            elif level == EncouragementLevel.IMPROVING:
                level = EncouragementLevel.GOOD
            elif level == EncouragementLevel.KEEP_GOING:
                level = EncouragementLevel.IMPROVING

        # 메시지 선택
        messages = self.MESSAGES[level]
        msg, emoji, tip = random.choice(messages)

        # 스트릭 보너스 메시지
        if streak >= 7:
            msg = f"{streak}일 연속 연습 중! " + msg

        # 시간대별 추가 메시지
        if time_of_day == "morning":
            msg = "좋은 아침이에요! " + msg
        elif time_of_day == "night":
            msg += " 오늘 하루도 수고했어요!"

        return EncouragementMessage(
            level=level,
            message=msg,
            emoji=emoji,
            tip=tip
        )

    def get_progress_celebration(self, milestone: str) -> str:
        """진도 달성 축하 메시지"""
        celebrations = {
            "first_practice": "첫 연습 완료! 멋진 시작이에요!",
            "10_practices": "10회 연습 달성! 꾸준함이 힘이에요!",
            "50_practices": "50회 연습! 당신은 이미 준비된 사람이에요!",
            "100_practices": "100회 연습 달성! 합격은 시간문제예요!",
            "first_80": "첫 80점 달성! 이제 합격선이 보여요!",
            "first_90": "90점 돌파! 면접관도 감탄할 실력이에요!",
            "week_streak": "일주일 연속 연습! 습관이 되었네요!",
            "month_streak": "한 달 연속! 당신의 끈기에 박수!",
        }
        return celebrations.get(milestone, "축하해요! 대단한 성과예요!")


# ============================================================
# 편의 함수들
# ============================================================

# 싱글톤 인스턴스
_path_generator = LearningPathGenerator()
_prediction_system = PassPredictionSystem()
_partner_system = PartnerMatchingSystem()
_gamification = GamificationSystem()
_encouragement = RealTimeEncouragementSystem()


def generate_learning_path(
    user_id: str,
    target_airline: str,
    target_date: Optional[datetime] = None,
    weak_areas: Optional[List[str]] = None
) -> LearningPath:
    """맞춤 학습 경로 생성"""
    return _path_generator.generate_path(user_id, target_airline, target_date, weak_areas=weak_areas)


def predict_pass_probability(
    airline: str,
    score_history: List[Dict],
    practice_frequency: float = 1.0
) -> PredictionResult:
    """합격 가능성 예측"""
    return _prediction_system.predict(airline, score_history, practice_frequency)


def find_study_partners(
    user_airline: str,
    user_level: str = "intermediate",
    user_time: str = "evening",
    limit: int = 5
) -> List[PartnerMatch]:
    """스터디 파트너 찾기"""
    return _partner_system.find_partners(user_airline, user_level, user_time, limit=limit)


def get_daily_missions(user_id: str, completed: List[str] = None) -> List[DailyMission]:
    """일일 미션 조회"""
    return _gamification.get_daily_missions(user_id, completed)


def check_streak(practice_dates: List[datetime]) -> StreakInfo:
    """스트릭 확인"""
    return _gamification.check_streak(practice_dates)


def get_leaderboard(airline: str = None, limit: int = 10) -> List[LeaderboardEntry]:
    """리더보드 조회"""
    return _gamification.get_leaderboard(airline, limit)


def get_encouragement(
    score: float,
    previous_score: Optional[float] = None,
    streak: int = 0
) -> EncouragementMessage:
    """격려 메시지"""
    return _encouragement.get_encouragement(score, previous_score, streak)


def get_progress_celebration(milestone: str) -> str:
    """진도 축하 메시지"""
    return _encouragement.get_progress_celebration(milestone)
