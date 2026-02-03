# -*- coding: utf-8 -*-
"""
learning_experience_enhancer.py
C. 학습 경험 (-) 해결 모듈

해결하는 문제:
12. 학습 경로 없음 → AI 맞춤 학습 계획 자동 생성
13. 약점 집중 연습 없음 → 약점 자동 감지 → 집중 연습 추천
14. 진도 목표 없음 → 마일스톤 설정
15. 성장 예측 없음 → 합격선 도달 예측
16. 실패 원인 모호 → 구체적 실패 분석 + 개선 방법
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import json


# ============================================================
# 12. AI 맞춤 학습 계획
# ============================================================

class SkillCategory(Enum):
    """스킬 카테고리"""
    SPEECH = "speech"
    CONTENT = "content"
    ATTITUDE = "attitude"
    ENGLISH = "english"
    RESUME = "resume"
    NONVERBAL = "nonverbal"


@dataclass
class WeeklyPlan:
    """주간 학습 계획"""
    week_number: int
    start_date: datetime
    end_date: datetime
    daily_tasks: Dict[str, List[Dict]]  # day -> tasks
    focus_areas: List[str]
    target_score: float
    estimated_hours: float


@dataclass
class PersonalizedPlan:
    """개인 맞춤 학습 계획"""
    user_id: str
    created_at: datetime
    target_airline: str
    target_date: Optional[datetime]
    current_level: str
    weekly_plans: List[WeeklyPlan]
    priority_skills: List[str]
    total_weeks: int


class PersonalizedPlanGenerator:
    """개인 맞춤 계획 생성기"""

    # 레벨별 주간 학습 시간 권장
    WEEKLY_HOURS = {
        "beginner": 10,
        "intermediate": 7,
        "advanced": 5,
    }

    # 카테고리별 학습 활동
    ACTIVITIES = {
        SkillCategory.SPEECH: [
            {"name": "발성 연습", "duration": 15, "page": "26_기내방송연습.py"},
            {"name": "속도 조절 연습", "duration": 20, "page": "4_모의면접.py"},
            {"name": "톤 변화 연습", "duration": 15, "page": "26_기내방송연습.py"},
        ],
        SkillCategory.CONTENT: [
            {"name": "자기소개 연습", "duration": 30, "page": "4_모의면접.py"},
            {"name": "지원동기 연습", "duration": 30, "page": "4_모의면접.py"},
            {"name": "꼬리질문 연습", "duration": 45, "page": "13_실전연습.py"},
        ],
        SkillCategory.ATTITUDE: [
            {"name": "롤플레잉 연습", "duration": 30, "page": "1_롤플레잉.py"},
            {"name": "상황 대처 연습", "duration": 30, "page": "1_롤플레잉.py"},
        ],
        SkillCategory.ENGLISH: [
            {"name": "영어 자기소개", "duration": 30, "page": "2_영어면접.py"},
            {"name": "영어 질문 연습", "duration": 40, "page": "2_영어면접.py"},
        ],
        SkillCategory.RESUME: [
            {"name": "자소서 작성", "duration": 60, "page": "21_자소서템플릿.py"},
            {"name": "자소서 첨삭", "duration": 30, "page": "20_자소서첨삭.py"},
        ],
        SkillCategory.NONVERBAL: [
            {"name": "표정 연습", "duration": 20, "page": "12_표정연습.py"},
            {"name": "자세 연습", "duration": 15, "page": "12_표정연습.py"},
        ],
    }

    def __init__(self):
        pass

    def generate_plan(
        self,
        user_id: str,
        target_airline: str,
        target_date: Optional[datetime] = None,
        current_scores: Dict[str, float] = None,
        available_hours_per_week: float = 7
    ) -> PersonalizedPlan:
        """개인 맞춤 계획 생성"""

        # 현재 레벨 판단
        avg_score = sum(current_scores.values()) / len(current_scores) if current_scores else 50
        if avg_score >= 80:
            current_level = "advanced"
        elif avg_score >= 60:
            current_level = "intermediate"
        else:
            current_level = "beginner"

        # 우선순위 스킬 결정
        priority_skills = self._determine_priority_skills(current_scores)

        # 총 주 수 계산
        if target_date:
            days_until = (target_date - datetime.now()).days
            total_weeks = max(1, days_until // 7)
        else:
            total_weeks = 8  # 기본 8주

        # 주간 계획 생성
        weekly_plans = []
        for week in range(total_weeks):
            start = datetime.now() + timedelta(weeks=week)
            end = start + timedelta(days=6)

            daily_tasks = self._generate_daily_tasks(
                priority_skills,
                available_hours_per_week,
                week + 1,
                total_weeks
            )

            weekly_plans.append(WeeklyPlan(
                week_number=week + 1,
                start_date=start,
                end_date=end,
                daily_tasks=daily_tasks,
                focus_areas=priority_skills[:2],
                target_score=min(100, avg_score + (week + 1) * 3),
                estimated_hours=available_hours_per_week
            ))

        return PersonalizedPlan(
            user_id=user_id,
            created_at=datetime.now(),
            target_airline=target_airline,
            target_date=target_date,
            current_level=current_level,
            weekly_plans=weekly_plans,
            priority_skills=priority_skills,
            total_weeks=total_weeks
        )

    def _determine_priority_skills(self, scores: Dict[str, float]) -> List[str]:
        """우선순위 스킬 결정"""
        if not scores:
            return ["content", "speech", "attitude"]

        # 점수 낮은 순 정렬
        sorted_skills = sorted(scores.items(), key=lambda x: x[1])
        return [skill for skill, _ in sorted_skills[:3]]

    def _generate_daily_tasks(
        self,
        priority_skills: List[str],
        weekly_hours: float,
        current_week: int,
        total_weeks: int
    ) -> Dict[str, List[Dict]]:
        """일별 태스크 생성"""
        daily_tasks = {}
        days = ["월", "화", "수", "목", "금", "토", "일"]
        daily_minutes = int((weekly_hours * 60) / 5)  # 주 5일 기준

        for i, day in enumerate(days):
            if i < 5:  # 평일
                tasks = []
                remaining = daily_minutes

                for skill in priority_skills:
                    try:
                        category = SkillCategory(skill)
                        activities = self.ACTIVITIES.get(category, [])
                        if activities and remaining > 0:
                            activity = activities[i % len(activities)]
                            if activity["duration"] <= remaining:
                                tasks.append({
                                    "name": activity["name"],
                                    "duration": activity["duration"],
                                    "page": activity["page"],
                                    "skill": skill
                                })
                                remaining -= activity["duration"]
                    except ValueError:
                        pass

                daily_tasks[day] = tasks
            else:  # 주말
                daily_tasks[day] = [{"name": "자유 복습", "duration": 30, "page": None, "skill": "review"}]

        return daily_tasks


# ============================================================
# 13. 약점 자동 감지 및 집중 연습 추천
# ============================================================

@dataclass
class WeaknessAnalysis:
    """약점 분석 결과"""
    skill: str
    current_score: float
    target_score: float
    gap: float
    severity: str  # "critical", "moderate", "minor"
    specific_issues: List[str]
    recommended_exercises: List[Dict]


class WeaknessDetector:
    """약점 감지기"""

    # 스킬별 세부 항목
    SKILL_DETAILS = {
        "speech": ["속도", "톤", "발음", "음량", "억양"],
        "content": ["구조", "논리", "구체성", "키워드", "일관성"],
        "attitude": ["자신감", "공감", "문제해결", "침착함", "적극성"],
        "english": ["문법", "발음", "유창성", "어휘", "표현"],
        "nonverbal": ["표정", "자세", "눈맞춤", "제스처", "미소"],
    }

    # 연습 추천
    EXERCISE_RECOMMENDATIONS = {
        "속도": {"name": "속도 조절 연습", "page": "26_기내방송연습.py", "tip": "메트로놈 앱과 함께 연습하세요"},
        "톤": {"name": "톤 변화 연습", "page": "26_기내방송연습.py", "tip": "녹음 후 들어보며 변화를 주세요"},
        "발음": {"name": "발음 교정", "page": "26_기내방송연습.py", "tip": "어려운 발음을 반복 연습하세요"},
        "구조": {"name": "STAR 기법 연습", "page": "4_모의면접.py", "tip": "상황-과제-행동-결과 순서로 말하세요"},
        "논리": {"name": "논리 구성 연습", "page": "5_토론면접.py", "tip": "주장-근거-예시-결론 순서로"},
        "자신감": {"name": "자신감 연습", "page": "12_표정연습.py", "tip": "거울을 보며 당당하게 말하세요"},
        "표정": {"name": "미소 연습", "page": "12_표정연습.py", "tip": "자연스러운 미소를 연습하세요"},
    }

    def __init__(self):
        pass

    def detect_weaknesses(
        self,
        skill_scores: Dict[str, float],
        detail_scores: Dict[str, Dict[str, float]] = None,
        target_score: float = 80
    ) -> List[WeaknessAnalysis]:
        """약점 감지"""

        weaknesses = []

        for skill, score in skill_scores.items():
            gap = target_score - score

            if gap <= 0:
                continue  # 이미 목표 달성

            # 심각도 판단
            if gap >= 20:
                severity = "critical"
            elif gap >= 10:
                severity = "moderate"
            else:
                severity = "minor"

            # 세부 이슈 파악
            specific_issues = []
            details = detail_scores.get(skill, {}) if detail_scores else {}
            for detail, detail_score in details.items():
                if detail_score < target_score - 5:
                    specific_issues.append(f"{detail} 부족 ({detail_score:.0f}점)")

            # 연습 추천
            recommended = []
            skill_details = self.SKILL_DETAILS.get(skill, [])
            for detail in skill_details[:3]:
                rec = self.EXERCISE_RECOMMENDATIONS.get(detail)
                if rec:
                    recommended.append(rec)

            weaknesses.append(WeaknessAnalysis(
                skill=skill,
                current_score=score,
                target_score=target_score,
                gap=gap,
                severity=severity,
                specific_issues=specific_issues if specific_issues else [f"{skill} 전반적 개선 필요"],
                recommended_exercises=recommended
            ))

        # 심각도 순 정렬
        severity_order = {"critical": 0, "moderate": 1, "minor": 2}
        weaknesses.sort(key=lambda w: severity_order.get(w.severity, 3))

        return weaknesses

    def get_focus_recommendation(self, weaknesses: List[WeaknessAnalysis]) -> Dict:
        """집중 연습 추천"""
        if not weaknesses:
            return {
                "message": "모든 영역에서 목표를 달성했습니다!",
                "focus_skill": None,
                "exercises": []
            }

        top_weakness = weaknesses[0]

        return {
            "message": f"'{top_weakness.skill}' 영역에 집중하세요! (현재 {top_weakness.current_score:.0f}점)",
            "focus_skill": top_weakness.skill,
            "gap": top_weakness.gap,
            "exercises": top_weakness.recommended_exercises,
            "specific_issues": top_weakness.specific_issues
        }


# ============================================================
# 14. 마일스톤 시스템
# ============================================================

@dataclass
class Milestone:
    """마일스톤"""
    milestone_id: str
    title: str
    description: str
    target_value: float
    current_value: float
    deadline: Optional[datetime]
    is_completed: bool = False
    completed_at: Optional[datetime] = None

    @property
    def progress_percent(self) -> float:
        if self.target_value == 0:
            return 100.0
        return min(100.0, (self.current_value / self.target_value) * 100)


class MilestoneManager:
    """마일스톤 관리자"""

    # 기본 마일스톤 템플릿
    DEFAULT_MILESTONES = [
        ("first_practice", "첫 연습 완료", "첫 모의면접을 완료하세요", 1),
        ("score_60", "60점 달성", "모의면접에서 60점 이상 받기", 60),
        ("score_70", "70점 달성", "모의면접에서 70점 이상 받기", 70),
        ("score_80", "합격선 돌파", "모의면접에서 80점 이상 받기", 80),
        ("score_90", "고득점 달성", "모의면접에서 90점 이상 받기", 90),
        ("streak_7", "일주일 연속", "7일 연속 학습하기", 7),
        ("streak_30", "한 달 연속", "30일 연속 학습하기", 30),
        ("all_category", "전 영역 정복", "모든 카테고리 80점 이상", 100),
    ]

    def __init__(self):
        pass

    def create_milestones(
        self,
        user_id: str,
        target_date: Optional[datetime] = None
    ) -> List[Milestone]:
        """마일스톤 생성"""

        milestones = []
        base_date = datetime.now()

        for i, (mid, title, desc, target) in enumerate(self.DEFAULT_MILESTONES):
            # 데드라인 설정
            if target_date:
                # 목표일까지 균등 분배
                days_per_milestone = (target_date - base_date).days // len(self.DEFAULT_MILESTONES)
                deadline = base_date + timedelta(days=days_per_milestone * (i + 1))
            else:
                deadline = None

            milestones.append(Milestone(
                milestone_id=mid,
                title=title,
                description=desc,
                target_value=target,
                current_value=0,
                deadline=deadline
            ))

        return milestones

    def update_milestone(
        self,
        milestone: Milestone,
        current_value: float
    ) -> Milestone:
        """마일스톤 업데이트"""
        milestone.current_value = current_value

        if current_value >= milestone.target_value and not milestone.is_completed:
            milestone.is_completed = True
            milestone.completed_at = datetime.now()

        return milestone

    def get_next_milestone(self, milestones: List[Milestone]) -> Optional[Milestone]:
        """다음 마일스톤"""
        for m in milestones:
            if not m.is_completed:
                return m
        return None


# ============================================================
# 15. 성장 예측
# ============================================================

@dataclass
class GrowthPrediction:
    """성장 예측"""
    current_score: float
    predicted_score_1week: float
    predicted_score_2week: float
    predicted_score_1month: float
    days_to_target: int
    growth_rate: float  # 일당 점수 상승
    confidence: float
    factors: List[str]


class GrowthPredictor:
    """성장 예측기"""

    def __init__(self):
        pass

    def predict(
        self,
        score_history: List[Dict],
        target_score: float = 80,
        practice_frequency: float = 1.0
    ) -> GrowthPrediction:
        """성장 예측"""

        if not score_history:
            return GrowthPrediction(
                current_score=0,
                predicted_score_1week=10,
                predicted_score_2week=20,
                predicted_score_1month=40,
                days_to_target=60,
                growth_rate=0.5,
                confidence=10,
                factors=["연습 데이터가 부족합니다"]
            )

        # 현재 점수
        recent_scores = [s["score"] for s in score_history[-5:]]
        current = sum(recent_scores) / len(recent_scores)

        # 성장률 계산
        if len(score_history) >= 7:
            old_scores = [s["score"] for s in score_history[-14:-7]]
            new_scores = [s["score"] for s in score_history[-7:]]
            if old_scores:
                old_avg = sum(old_scores) / len(old_scores)
                new_avg = sum(new_scores) / len(new_scores)
                weekly_growth = new_avg - old_avg
                daily_growth = weekly_growth / 7
            else:
                daily_growth = 0.3
        else:
            daily_growth = 0.5  # 기본값

        # 연습 빈도 반영
        effective_growth = daily_growth * practice_frequency

        # 예측
        pred_1week = min(100, current + effective_growth * 7)
        pred_2week = min(100, current + effective_growth * 14)
        pred_1month = min(100, current + effective_growth * 30)

        # 목표 도달 일수
        gap = target_score - current
        if gap <= 0:
            days_to_target = 0
        elif effective_growth > 0:
            days_to_target = int(gap / effective_growth)
        else:
            days_to_target = 180

        # 신뢰도
        confidence = min(90, 30 + len(score_history) * 2)

        # 영향 요인
        factors = []
        if practice_frequency < 1:
            factors.append("연습 빈도를 높이면 더 빨리 성장할 수 있어요")
        if daily_growth < 0:
            factors.append("최근 성적이 하락 중이에요. 기본기를 점검하세요")
        if daily_growth > 1:
            factors.append("빠르게 성장하고 있어요! 이 페이스를 유지하세요")
        if not factors:
            factors.append("꾸준히 성장하고 있어요!")

        return GrowthPrediction(
            current_score=round(current, 1),
            predicted_score_1week=round(pred_1week, 1),
            predicted_score_2week=round(pred_2week, 1),
            predicted_score_1month=round(pred_1month, 1),
            days_to_target=days_to_target,
            growth_rate=round(effective_growth, 2),
            confidence=confidence,
            factors=factors
        )


# ============================================================
# 16. 구체적 실패 분석
# ============================================================

@dataclass
class FailureAnalysis:
    """실패 분석"""
    category: str
    issue: str
    severity: str
    specific_moment: Optional[str]
    root_cause: str
    improvement_steps: List[str]
    example_good_answer: Optional[str]


class FailureAnalyzer:
    """실패 분석기"""

    # 실패 패턴 및 해결책
    FAILURE_PATTERNS = {
        "speech_too_fast": {
            "issue": "말이 너무 빨라요",
            "root_cause": "긴장으로 인한 속도 증가",
            "steps": ["심호흡 후 시작하기", "문장 끝에서 잠시 멈추기", "중요한 단어 강조하며 천천히"],
        },
        "speech_monotone": {
            "issue": "톤이 단조로워요",
            "root_cause": "감정 표현 부족",
            "steps": ["중요한 부분에서 톤 높이기", "열정을 담아 말하기", "질문에 맞는 감정 표현"],
        },
        "content_vague": {
            "issue": "답변이 추상적이에요",
            "root_cause": "구체적 경험/숫자 부족",
            "steps": ["STAR 기법 사용하기", "구체적 숫자/날짜 포함", "실제 경험 사례 추가"],
        },
        "content_too_short": {
            "issue": "답변이 너무 짧아요",
            "root_cause": "내용 준비 부족",
            "steps": ["핵심 포인트 3개 준비", "예시를 덧붙이기", "결론 명확히 하기"],
        },
        "content_off_topic": {
            "issue": "질문과 다른 답변이에요",
            "root_cause": "질문 이해 부족",
            "steps": ["질문 핵심 파악하기", "답변 전 질문 다시 생각", "질문 키워드 포함해 답변"],
        },
        "attitude_nervous": {
            "issue": "긴장이 많이 보여요",
            "root_cause": "연습 부족/자신감 부족",
            "steps": ["충분한 연습으로 자신감 얻기", "심호흡으로 긴장 완화", "면접관을 친구처럼 생각하기"],
        },
        "nonverbal_no_smile": {
            "issue": "표정이 경직됐어요",
            "root_cause": "긴장/의식적 표정 관리 부족",
            "steps": ["자연스러운 미소 연습", "거울 보며 표정 체크", "편안한 마음가짐 유지"],
        },
        "nonverbal_no_eye_contact": {
            "issue": "눈맞춤이 부족해요",
            "root_cause": "카메라/면접관 의식",
            "steps": ["카메라를 면접관 눈이라 생각", "답변 중 70% 눈맞춤 유지", "잠시 시선 돌려도 OK"],
        },
    }

    def __init__(self):
        pass

    def analyze(
        self,
        category: str,
        score: float,
        details: Dict
    ) -> List[FailureAnalysis]:
        """실패 분석"""

        failures = []

        # 점수가 낮은 세부 항목 찾기
        for detail, value in details.items():
            if value < 70:
                pattern_key = f"{category}_{detail}"
                pattern = self.FAILURE_PATTERNS.get(pattern_key)

                if pattern:
                    failures.append(FailureAnalysis(
                        category=category,
                        issue=pattern["issue"],
                        severity="high" if value < 50 else "medium",
                        specific_moment=details.get("timestamp"),
                        root_cause=pattern["root_cause"],
                        improvement_steps=pattern["steps"],
                        example_good_answer=None
                    ))

        # 패턴이 없는 경우 일반 분석
        if not failures and score < 70:
            failures.append(FailureAnalysis(
                category=category,
                issue=f"{category} 영역 개선 필요",
                severity="medium",
                specific_moment=None,
                root_cause="전반적인 연습 부족",
                improvement_steps=["해당 영역 집중 연습", "피드백 꼼꼼히 확인", "반복 연습"],
                example_good_answer=None
            ))

        return failures

    def get_priority_improvement(self, failures: List[FailureAnalysis]) -> Optional[Dict]:
        """우선 개선 사항"""
        if not failures:
            return None

        # 심각도 높은 것 우선
        high_severity = [f for f in failures if f.severity == "high"]
        target = high_severity[0] if high_severity else failures[0]

        return {
            "issue": target.issue,
            "first_step": target.improvement_steps[0] if target.improvement_steps else "연습 계속하기",
            "root_cause": target.root_cause,
            "all_steps": target.improvement_steps
        }


# ============================================================
# 편의 함수들
# ============================================================

_plan_generator = PersonalizedPlanGenerator()
_weakness_detector = WeaknessDetector()
_milestone_manager = MilestoneManager()
_growth_predictor = GrowthPredictor()
_failure_analyzer = FailureAnalyzer()


def generate_personalized_plan(
    user_id: str,
    target_airline: str,
    target_date: datetime = None,
    current_scores: Dict = None
) -> PersonalizedPlan:
    """개인 맞춤 계획 생성"""
    return _plan_generator.generate_plan(user_id, target_airline, target_date, current_scores)


def detect_weaknesses(
    skill_scores: Dict[str, float],
    target_score: float = 80
) -> List[WeaknessAnalysis]:
    """약점 감지"""
    return _weakness_detector.detect_weaknesses(skill_scores, target_score=target_score)


def get_focus_recommendation(skill_scores: Dict[str, float]) -> Dict:
    """집중 연습 추천"""
    weaknesses = detect_weaknesses(skill_scores)
    return _weakness_detector.get_focus_recommendation(weaknesses)


def create_milestones(user_id: str, target_date: datetime = None) -> List[Milestone]:
    """마일스톤 생성"""
    return _milestone_manager.create_milestones(user_id, target_date)


def get_next_milestone(milestones: List[Milestone]) -> Optional[Milestone]:
    """다음 마일스톤"""
    return _milestone_manager.get_next_milestone(milestones)


def predict_growth(score_history: List[Dict], target_score: float = 80) -> GrowthPrediction:
    """성장 예측"""
    return _growth_predictor.predict(score_history, target_score)


def analyze_failure(category: str, score: float, details: Dict) -> List[FailureAnalysis]:
    """실패 분석"""
    return _failure_analyzer.analyze(category, score, details)


def get_priority_improvement(category: str, score: float, details: Dict) -> Optional[Dict]:
    """우선 개선 사항"""
    failures = analyze_failure(category, score, details)
    return _failure_analyzer.get_priority_improvement(failures)
