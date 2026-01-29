"""
FlyReady Lab - 개인화 추천 시스템
사용자의 학습 이력, 취약점 분석을 통한 맞춤형 학습 추천
"""

import json
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
import math


class SkillCategory(Enum):
    """스킬 카테고리"""
    # 면접 관련
    SELF_INTRODUCTION = "self_introduction"       # 자기소개
    MOTIVATION = "motivation"                     # 지원동기
    SITUATIONAL = "situational"                   # 상황대처
    SERVICE_MIND = "service_mind"                 # 서비스 마인드
    TEAMWORK = "teamwork"                         # 팀워크
    STRESS_MANAGEMENT = "stress_management"       # 스트레스 관리

    # 언어 능력
    KOREAN_SPEAKING = "korean_speaking"           # 한국어 말하기
    ENGLISH_SPEAKING = "english_speaking"         # 영어 말하기
    ENGLISH_LISTENING = "english_listening"       # 영어 듣기
    SECOND_LANGUAGE = "second_language"           # 제2외국어

    # 이미지 관련
    POSTURE = "posture"                           # 자세/워킹
    MAKEUP = "makeup"                             # 메이크업
    GROOMING = "grooming"                         # 그루밍

    # 지식
    AVIATION_KNOWLEDGE = "aviation_knowledge"     # 항공상식
    SAFETY_KNOWLEDGE = "safety_knowledge"         # 안전지식
    SERVICE_KNOWLEDGE = "service_knowledge"       # 서비스지식
    AIRLINE_INFO = "airline_info"                 # 항공사 정보

    # 서류
    RESUME = "resume"                             # 이력서
    COVER_LETTER = "cover_letter"                 # 자기소개서
    DOCUMENT_PHOTO = "document_photo"             # 사진


class ContentType(Enum):
    """콘텐츠 유형"""
    VIDEO = "video"                  # 영상 강의
    ARTICLE = "article"              # 아티클
    QUIZ = "quiz"                    # 퀴즈
    PRACTICE = "practice"            # 연습
    MOCK_INTERVIEW = "mock_interview" # 모의면접
    TEMPLATE = "template"            # 템플릿
    CHECKLIST = "checklist"          # 체크리스트


class DifficultyLevel(Enum):
    """난이도"""
    BEGINNER = 1       # 초급
    INTERMEDIATE = 2   # 중급
    ADVANCED = 3       # 고급


@dataclass
class LearningContent:
    """학습 콘텐츠"""
    id: str
    title: str
    description: str
    content_type: str
    skill_category: str
    difficulty: int
    duration_minutes: int = 0
    tags: List[str] = field(default_factory=list)
    url: str = ""
    is_premium: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class UserActivity:
    """사용자 활동 기록"""
    user_id: str
    activity_type: str          # view, complete, quiz, interview, etc.
    content_id: str
    skill_category: str
    score: Optional[float] = None
    duration_seconds: int = 0
    timestamp: str = ""
    metadata: Dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass
class SkillProfile:
    """사용자 스킬 프로필"""
    user_id: str
    skills: Dict[str, float] = field(default_factory=dict)  # category -> score (0-100)
    last_updated: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class Recommendation:
    """추천 항목"""
    content_id: str
    title: str
    content_type: str
    skill_category: str
    reason: str                    # 추천 이유
    priority_score: float          # 우선순위 점수 (높을수록 중요)
    estimated_improvement: float   # 예상 향상도
    is_urgent: bool = False        # 긴급 추천 여부

    def to_dict(self):
        return asdict(self)


class UserActivityTracker:
    """사용자 활동 추적"""

    def __init__(self, data_dir: str = "data/recommendations"):
        self.data_dir = data_dir
        self.activities_dir = os.path.join(data_dir, "activities")
        os.makedirs(self.activities_dir, exist_ok=True)

    def _get_user_file(self, user_id: str) -> str:
        return os.path.join(self.activities_dir, f"{user_id}.json")

    def log_activity(self, activity: UserActivity):
        """활동 기록"""
        if not activity.timestamp:
            activity.timestamp = datetime.now().isoformat()

        user_file = self._get_user_file(activity.user_id)
        activities = self.get_user_activities(activity.user_id)
        activities.append(activity.to_dict())

        # 최근 1000개만 유지
        activities = activities[-1000:]

        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(activities, f, ensure_ascii=False, indent=2)

    def get_user_activities(self, user_id: str,
                           activity_type: Optional[str] = None,
                           days: Optional[int] = None) -> List[Dict]:
        """사용자 활동 조회"""
        user_file = self._get_user_file(user_id)
        if not os.path.exists(user_file):
            return []

        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                activities = json.load(f)
        except Exception:
            return []

        # 타입 필터
        if activity_type:
            activities = [a for a in activities if a.get('activity_type') == activity_type]

        # 기간 필터
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            activities = [a for a in activities if a.get('timestamp', '') >= cutoff]

        return activities

    def get_skill_scores(self, user_id: str) -> Dict[str, List[float]]:
        """스킬별 점수 이력"""
        activities = self.get_user_activities(user_id)
        skill_scores = {}

        for activity in activities:
            if activity.get('score') is not None:
                skill = activity.get('skill_category')
                if skill:
                    if skill not in skill_scores:
                        skill_scores[skill] = []
                    skill_scores[skill].append(activity['score'])

        return skill_scores


class SkillAnalyzer:
    """스킬 분석 엔진"""

    # 스킬 가중치 (항공사 면접 기준)
    SKILL_WEIGHTS = {
        SkillCategory.SELF_INTRODUCTION.value: 0.12,
        SkillCategory.MOTIVATION.value: 0.12,
        SkillCategory.SITUATIONAL.value: 0.10,
        SkillCategory.SERVICE_MIND.value: 0.10,
        SkillCategory.ENGLISH_SPEAKING.value: 0.10,
        SkillCategory.KOREAN_SPEAKING.value: 0.08,
        SkillCategory.POSTURE.value: 0.08,
        SkillCategory.GROOMING.value: 0.06,
        SkillCategory.AVIATION_KNOWLEDGE.value: 0.06,
        SkillCategory.TEAMWORK.value: 0.06,
        SkillCategory.COVER_LETTER.value: 0.06,
        SkillCategory.STRESS_MANAGEMENT.value: 0.04,
        SkillCategory.SECOND_LANGUAGE.value: 0.02,
    }

    def __init__(self, data_dir: str = "data/recommendations"):
        self.data_dir = data_dir
        self.profiles_dir = os.path.join(data_dir, "profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.activity_tracker = UserActivityTracker(data_dir)

    def _get_profile_file(self, user_id: str) -> str:
        return os.path.join(self.profiles_dir, f"{user_id}.json")

    def analyze_user(self, user_id: str) -> SkillProfile:
        """사용자 스킬 분석"""
        skill_scores = self.activity_tracker.get_skill_scores(user_id)

        profile = SkillProfile(
            user_id=user_id,
            skills={},
            last_updated=datetime.now().isoformat()
        )

        for category in SkillCategory:
            cat_value = category.value
            if cat_value in skill_scores and skill_scores[cat_value]:
                scores = skill_scores[cat_value]
                # 가중 평균 (최근 점수에 더 높은 가중치)
                weights = [1.0 + 0.1 * i for i in range(len(scores))]
                weighted_sum = sum(s * w for s, w in zip(scores, weights))
                profile.skills[cat_value] = weighted_sum / sum(weights)
            else:
                profile.skills[cat_value] = 50.0  # 기본값

        # 프로필 저장
        self.save_profile(profile)

        return profile

    def save_profile(self, profile: SkillProfile):
        """프로필 저장"""
        profile_file = self._get_profile_file(profile.user_id)
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)

    def load_profile(self, user_id: str) -> Optional[SkillProfile]:
        """프로필 로드"""
        profile_file = self._get_profile_file(user_id)
        if not os.path.exists(profile_file):
            return None
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return SkillProfile.from_dict(data)
        except Exception:
            return None

    def get_weaknesses(self, user_id: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """취약 스킬 분석"""
        profile = self.load_profile(user_id)
        if not profile:
            profile = self.analyze_user(user_id)

        # 가중치 적용한 취약점 점수
        weakness_scores = []
        for skill, score in profile.skills.items():
            weight = self.SKILL_WEIGHTS.get(skill, 0.05)
            # 낮은 점수 + 높은 가중치 = 높은 취약점 점수
            weakness_score = (100 - score) * weight
            weakness_scores.append((skill, weakness_score, score))

        # 취약점 점수 높은 순 정렬
        weakness_scores.sort(key=lambda x: x[1], reverse=True)

        return [(skill, score) for skill, _, score in weakness_scores[:top_n]]

    def get_strengths(self, user_id: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """강점 스킬 분석"""
        profile = self.load_profile(user_id)
        if not profile:
            profile = self.analyze_user(user_id)

        strength_scores = []
        for skill, score in profile.skills.items():
            weight = self.SKILL_WEIGHTS.get(skill, 0.05)
            strength_score = score * weight
            strength_scores.append((skill, strength_score, score))

        strength_scores.sort(key=lambda x: x[1], reverse=True)

        return [(skill, score) for skill, _, score in strength_scores[:top_n]]

    def calculate_readiness_score(self, user_id: str) -> float:
        """면접 준비도 점수 계산 (0-100)"""
        profile = self.load_profile(user_id)
        if not profile:
            return 50.0

        total_score = 0
        for skill, score in profile.skills.items():
            weight = self.SKILL_WEIGHTS.get(skill, 0.05)
            total_score += score * weight

        return round(total_score, 1)

    def get_improvement_trend(self, user_id: str, days: int = 30) -> Dict[str, float]:
        """스킬 향상 추세"""
        activities = self.activity_tracker.get_user_activities(user_id, days=days)

        if not activities:
            return {}

        # 기간을 전반/후반으로 나누어 비교
        mid_point = len(activities) // 2
        first_half = activities[:mid_point]
        second_half = activities[mid_point:]

        trends = {}
        for category in SkillCategory:
            cat = category.value

            first_scores = [a['score'] for a in first_half
                          if a.get('skill_category') == cat and a.get('score') is not None]
            second_scores = [a['score'] for a in second_half
                           if a.get('skill_category') == cat and a.get('score') is not None]

            if first_scores and second_scores:
                first_avg = sum(first_scores) / len(first_scores)
                second_avg = sum(second_scores) / len(second_scores)
                trends[cat] = round(second_avg - first_avg, 1)

        return trends


class ContentRepository:
    """학습 콘텐츠 저장소"""

    def __init__(self, data_dir: str = "data/recommendations"):
        self.data_dir = data_dir
        self.content_file = os.path.join(data_dir, "learning_content.json")
        os.makedirs(data_dir, exist_ok=True)

        # 기본 콘텐츠 초기화
        if not os.path.exists(self.content_file):
            self._init_default_content()

    def _init_default_content(self):
        """기본 학습 콘텐츠 초기화"""
        default_content = [
            # 자기소개
            LearningContent(
                id="intro_001",
                title="자기소개 1분 스피치 완성 가이드",
                description="면접관의 눈길을 사로잡는 1분 자기소개 작성법",
                content_type=ContentType.ARTICLE.value,
                skill_category=SkillCategory.SELF_INTRODUCTION.value,
                difficulty=1,
                duration_minutes=15,
                tags=["자기소개", "1분스피치", "면접"]
            ),
            LearningContent(
                id="intro_002",
                title="자기소개 롤플레잉 연습",
                description="AI와 함께 자기소개 말하기 연습",
                content_type=ContentType.PRACTICE.value,
                skill_category=SkillCategory.SELF_INTRODUCTION.value,
                difficulty=2,
                duration_minutes=20,
                tags=["자기소개", "연습", "AI"]
            ),

            # 지원동기
            LearningContent(
                id="motiv_001",
                title="항공사별 지원동기 작성 비법",
                description="대한항공, 아시아나 등 항공사별 맞춤 지원동기",
                content_type=ContentType.ARTICLE.value,
                skill_category=SkillCategory.MOTIVATION.value,
                difficulty=2,
                duration_minutes=20,
                tags=["지원동기", "항공사", "대한항공", "아시아나"]
            ),

            # 상황대처
            LearningContent(
                id="situation_001",
                title="기내 돌발 상황 대처법",
                description="실제 면접에 출제된 상황 질문 30선",
                content_type=ContentType.QUIZ.value,
                skill_category=SkillCategory.SITUATIONAL.value,
                difficulty=2,
                duration_minutes=30,
                tags=["상황대처", "면접질문", "기내서비스"]
            ),
            LearningContent(
                id="situation_002",
                title="까다로운 승객 응대 시뮬레이션",
                description="AI와 함께하는 상황극 연습",
                content_type=ContentType.MOCK_INTERVIEW.value,
                skill_category=SkillCategory.SITUATIONAL.value,
                difficulty=3,
                duration_minutes=25,
                tags=["상황대처", "승객응대", "AI면접"],
                is_premium=True
            ),

            # 영어 스피킹
            LearningContent(
                id="eng_001",
                title="기내 영어 필수 표현 100",
                description="실제 비행에서 사용하는 영어 표현 학습",
                content_type=ContentType.ARTICLE.value,
                skill_category=SkillCategory.ENGLISH_SPEAKING.value,
                difficulty=1,
                duration_minutes=30,
                tags=["영어", "기내방송", "필수표현"]
            ),
            LearningContent(
                id="eng_002",
                title="영어 인터뷰 실전 연습",
                description="원어민 AI와 함께하는 영어 면접 연습",
                content_type=ContentType.MOCK_INTERVIEW.value,
                skill_category=SkillCategory.ENGLISH_SPEAKING.value,
                difficulty=3,
                duration_minutes=30,
                tags=["영어면접", "AI면접", "원어민"],
                is_premium=True
            ),

            # 이미지 메이킹
            LearningContent(
                id="image_001",
                title="승무원 면접 메이크업 가이드",
                description="항공사별 선호 메이크업 스타일 분석",
                content_type=ContentType.VIDEO.value,
                skill_category=SkillCategory.MAKEUP.value,
                difficulty=1,
                duration_minutes=25,
                tags=["메이크업", "이미지메이킹", "면접"]
            ),
            LearningContent(
                id="image_002",
                title="워킹 & 자세 교정",
                description="면접장 입장부터 퇴장까지 완벽 자세",
                content_type=ContentType.VIDEO.value,
                skill_category=SkillCategory.POSTURE.value,
                difficulty=1,
                duration_minutes=20,
                tags=["워킹", "자세", "이미지메이킹"]
            ),

            # 항공상식
            LearningContent(
                id="aviation_001",
                title="항공상식 퀴즈 100제",
                description="면접 필수 항공상식 총정리",
                content_type=ContentType.QUIZ.value,
                skill_category=SkillCategory.AVIATION_KNOWLEDGE.value,
                difficulty=2,
                duration_minutes=40,
                tags=["항공상식", "퀴즈", "면접"]
            ),

            # 자소서
            LearningContent(
                id="cover_001",
                title="합격 자소서 분석 및 작성법",
                description="실제 합격자 자소서 분석과 핵심 작성 전략",
                content_type=ContentType.ARTICLE.value,
                skill_category=SkillCategory.COVER_LETTER.value,
                difficulty=2,
                duration_minutes=35,
                tags=["자소서", "합격", "분석"]
            ),
            LearningContent(
                id="cover_002",
                title="AI 자소서 첨삭 받기",
                description="AI가 분석하는 나의 자소서 강점과 보완점",
                content_type=ContentType.PRACTICE.value,
                skill_category=SkillCategory.COVER_LETTER.value,
                difficulty=2,
                duration_minutes=30,
                tags=["자소서", "AI첨삭", "피드백"],
                is_premium=True
            ),
        ]

        self.save_all_content([c.to_dict() for c in default_content])

    def save_all_content(self, content_list: List[Dict]):
        """전체 콘텐츠 저장"""
        with open(self.content_file, 'w', encoding='utf-8') as f:
            json.dump(content_list, f, ensure_ascii=False, indent=2)

    def load_all_content(self) -> List[Dict]:
        """전체 콘텐츠 로드"""
        if not os.path.exists(self.content_file):
            return []
        try:
            with open(self.content_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def get_content_by_skill(self, skill_category: str) -> List[Dict]:
        """스킬별 콘텐츠 조회"""
        all_content = self.load_all_content()
        return [c for c in all_content if c.get('skill_category') == skill_category]

    def get_content_by_type(self, content_type: str) -> List[Dict]:
        """유형별 콘텐츠 조회"""
        all_content = self.load_all_content()
        return [c for c in all_content if c.get('content_type') == content_type]

    def get_content_by_id(self, content_id: str) -> Optional[Dict]:
        """ID로 콘텐츠 조회"""
        all_content = self.load_all_content()
        for c in all_content:
            if c.get('id') == content_id:
                return c
        return None


class RecommendationEngine:
    """개인화 추천 엔진"""

    # 스킬 카테고리 한글명
    SKILL_NAMES = {
        SkillCategory.SELF_INTRODUCTION.value: "자기소개",
        SkillCategory.MOTIVATION.value: "지원동기",
        SkillCategory.SITUATIONAL.value: "상황대처",
        SkillCategory.SERVICE_MIND.value: "서비스 마인드",
        SkillCategory.TEAMWORK.value: "팀워크",
        SkillCategory.STRESS_MANAGEMENT.value: "스트레스 관리",
        SkillCategory.KOREAN_SPEAKING.value: "한국어 스피킹",
        SkillCategory.ENGLISH_SPEAKING.value: "영어 스피킹",
        SkillCategory.ENGLISH_LISTENING.value: "영어 리스닝",
        SkillCategory.SECOND_LANGUAGE.value: "제2외국어",
        SkillCategory.POSTURE.value: "자세/워킹",
        SkillCategory.MAKEUP.value: "메이크업",
        SkillCategory.GROOMING.value: "그루밍",
        SkillCategory.AVIATION_KNOWLEDGE.value: "항공상식",
        SkillCategory.SAFETY_KNOWLEDGE.value: "안전지식",
        SkillCategory.SERVICE_KNOWLEDGE.value: "서비스지식",
        SkillCategory.AIRLINE_INFO.value: "항공사 정보",
        SkillCategory.RESUME.value: "이력서",
        SkillCategory.COVER_LETTER.value: "자기소개서",
        SkillCategory.DOCUMENT_PHOTO.value: "사진",
    }

    def __init__(self, data_dir: str = "data/recommendations"):
        self.data_dir = data_dir
        self.skill_analyzer = SkillAnalyzer(data_dir)
        self.content_repo = ContentRepository(data_dir)
        self.activity_tracker = UserActivityTracker(data_dir)

    def get_recommendations(self, user_id: str, limit: int = 5,
                           include_premium: bool = False) -> List[Recommendation]:
        """개인화 추천 생성"""
        recommendations = []

        # 1. 취약점 기반 추천
        weaknesses = self.skill_analyzer.get_weaknesses(user_id, top_n=3)
        for skill, score in weaknesses:
            content_list = self.content_repo.get_content_by_skill(skill)

            for content in content_list:
                if not include_premium and content.get('is_premium', False):
                    continue

                skill_name = self.SKILL_NAMES.get(skill, skill)

                rec = Recommendation(
                    content_id=content['id'],
                    title=content['title'],
                    content_type=content['content_type'],
                    skill_category=skill,
                    reason=f"'{skill_name}' 점수가 {score:.0f}점으로 보완이 필요합니다",
                    priority_score=100 - score,  # 낮은 점수일수록 높은 우선순위
                    estimated_improvement=min(15, (100 - score) * 0.2),
                    is_urgent=score < 40
                )
                recommendations.append(rec)

        # 2. 학습 진도 기반 추천 (오래 안한 콘텐츠)
        recent_activities = self.activity_tracker.get_user_activities(user_id, days=7)
        recent_skills = {a.get('skill_category') for a in recent_activities}

        for category in SkillCategory:
            if category.value not in recent_skills:
                content_list = self.content_repo.get_content_by_skill(category.value)
                if content_list:
                    content = content_list[0]
                    if not include_premium and content.get('is_premium', False):
                        continue

                    skill_name = self.SKILL_NAMES.get(category.value, category.value)
                    rec = Recommendation(
                        content_id=content['id'],
                        title=content['title'],
                        content_type=content['content_type'],
                        skill_category=category.value,
                        reason=f"'{skill_name}'을(를) 최근 7일간 학습하지 않았습니다",
                        priority_score=30,
                        estimated_improvement=5,
                        is_urgent=False
                    )
                    recommendations.append(rec)

        # 중복 제거 및 정렬
        seen_ids = set()
        unique_recs = []
        for rec in recommendations:
            if rec.content_id not in seen_ids:
                seen_ids.add(rec.content_id)
                unique_recs.append(rec)

        unique_recs.sort(key=lambda x: (x.is_urgent, x.priority_score), reverse=True)

        return unique_recs[:limit]

    def get_daily_mission(self, user_id: str) -> List[Recommendation]:
        """오늘의 학습 미션"""
        recommendations = self.get_recommendations(user_id, limit=3)

        # 다양한 콘텐츠 유형으로 구성
        content_types_used = set()
        missions = []

        for rec in recommendations:
            if rec.content_type not in content_types_used or len(missions) < 3:
                missions.append(rec)
                content_types_used.add(rec.content_type)

            if len(missions) >= 3:
                break

        return missions

    def get_study_plan(self, user_id: str, weeks: int = 4) -> Dict[int, List[Recommendation]]:
        """주간 학습 플랜 생성"""
        all_content = self.content_repo.load_all_content()
        weaknesses = self.skill_analyzer.get_weaknesses(user_id, top_n=10)
        weak_skills = {skill for skill, _ in weaknesses}

        # 난이도별, 스킬별 콘텐츠 분류
        plan = {}
        used_content = set()

        for week in range(1, weeks + 1):
            week_content = []
            target_difficulty = min(3, (week + 1) // 2)  # 주차별 난이도 상승

            for skill, score in weaknesses:
                skill_content = [c for c in all_content
                               if c.get('skill_category') == skill
                               and c['id'] not in used_content
                               and c.get('difficulty', 1) <= target_difficulty]

                if skill_content:
                    content = skill_content[0]
                    skill_name = self.SKILL_NAMES.get(skill, skill)

                    rec = Recommendation(
                        content_id=content['id'],
                        title=content['title'],
                        content_type=content['content_type'],
                        skill_category=skill,
                        reason=f"{week}주차: '{skill_name}' 강화",
                        priority_score=100 - score,
                        estimated_improvement=10,
                        is_urgent=False
                    )
                    week_content.append(rec)
                    used_content.add(content['id'])

                if len(week_content) >= 5:
                    break

            plan[week] = week_content

        return plan

    def get_skill_summary(self, user_id: str) -> Dict:
        """스킬 요약 대시보드 데이터"""
        profile = self.skill_analyzer.load_profile(user_id)
        if not profile:
            profile = self.skill_analyzer.analyze_user(user_id)

        readiness = self.skill_analyzer.calculate_readiness_score(user_id)
        weaknesses = self.skill_analyzer.get_weaknesses(user_id, top_n=3)
        strengths = self.skill_analyzer.get_strengths(user_id, top_n=3)
        trends = self.skill_analyzer.get_improvement_trend(user_id, days=30)

        return {
            "readiness_score": readiness,
            "skills": {
                self.SKILL_NAMES.get(k, k): v
                for k, v in profile.skills.items()
            },
            "weaknesses": [
                {"skill": self.SKILL_NAMES.get(s, s), "score": sc}
                for s, sc in weaknesses
            ],
            "strengths": [
                {"skill": self.SKILL_NAMES.get(s, s), "score": sc}
                for s, sc in strengths
            ],
            "trends": {
                self.SKILL_NAMES.get(k, k): v
                for k, v in trends.items()
            },
            "last_updated": profile.last_updated
        }


# Streamlit 통합용 함수들
def render_recommendation_page():
    """추천 페이지 렌더링"""
    import streamlit as st

    st.title("맞춤 학습 추천")

    user_id = st.session_state.get("user_id", "guest")
    engine = RecommendationEngine()

    # 스킬 요약
    summary = engine.get_skill_summary(user_id)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("면접 준비도", f"{summary['readiness_score']}점", delta=None)
    with col2:
        if summary['weaknesses']:
            weak = summary['weaknesses'][0]
            st.metric("보완 필요", weak['skill'], delta=f"{weak['score']:.0f}점")
    with col3:
        if summary['strengths']:
            strong = summary['strengths'][0]
            st.metric("강점 분야", strong['skill'], delta=f"{strong['score']:.0f}점")

    # 오늘의 미션
    st.subheader("오늘의 학습 미션")
    missions = engine.get_daily_mission(user_id)

    for i, mission in enumerate(missions, 1):
        with st.expander(f"미션 {i}: {mission.title}", expanded=i==1):
            st.markdown(f"**카테고리**: {engine.SKILL_NAMES.get(mission.skill_category, mission.skill_category)}")
            st.markdown(f"**추천 이유**: {mission.reason}")
            st.markdown(f"**예상 향상도**: +{mission.estimated_improvement:.0f}점")

            if mission.is_urgent:
                st.warning("긴급 보완 필요!")

            if st.button("학습 시작", key=f"start_{mission.content_id}"):
                st.session_state[f"learning_{mission.content_id}"] = True
                st.info("학습 페이지로 이동합니다...")

    # 맞춤 추천
    st.subheader("맞춤 콘텐츠 추천")
    recommendations = engine.get_recommendations(user_id, limit=5)

    for rec in recommendations:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{rec.title}**")
            st.caption(rec.reason)
        with col2:
            st.button("학습", key=f"learn_{rec.content_id}")


def render_skill_dashboard():
    """스킬 대시보드 렌더링"""
    import streamlit as st

    st.title("나의 스킬 분석")

    user_id = st.session_state.get("user_id", "guest")
    engine = RecommendationEngine()

    summary = engine.get_skill_summary(user_id)

    # 레이더 차트 (스킬 시각화)
    st.subheader("스킬 프로필")

    skills_data = summary['skills']

    # 테이블로 표시
    for skill, score in skills_data.items():
        progress = score / 100
        col1, col2, col3 = st.columns([2, 5, 1])
        with col1:
            st.write(skill)
        with col2:
            st.progress(progress)
        with col3:
            st.write(f"{score:.0f}점")

    # 향상 추세
    st.subheader("최근 30일 향상 추세")
    trends = summary['trends']

    if trends:
        for skill, change in trends.items():
            delta_color = "normal" if change >= 0 else "inverse"
            st.metric(skill, f"{change:+.1f}점", delta=None)
    else:
        st.info("아직 충분한 학습 데이터가 없습니다. 학습을 시작해보세요!")


def render_study_plan_page():
    """학습 플랜 페이지 렌더링"""
    import streamlit as st

    st.title("나만의 학습 플랜")

    user_id = st.session_state.get("user_id", "guest")
    engine = RecommendationEngine()

    weeks = st.slider("학습 기간 (주)", 2, 8, 4)

    if st.button("학습 플랜 생성"):
        plan = engine.get_study_plan(user_id, weeks)

        for week, contents in plan.items():
            st.subheader(f"{week}주차")

            for content in contents:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"- **{content.title}**")
                    st.caption(f"  {content.reason}")
                with col2:
                    st.checkbox("완료", key=f"done_{week}_{content.content_id}")


if __name__ == "__main__":
    # 테스트
    engine = RecommendationEngine()
    tracker = UserActivityTracker()

    test_user = "test_user_001"

    # 테스트 활동 기록
    activities = [
        UserActivity(test_user, "quiz", "situation_001", SkillCategory.SITUATIONAL.value, score=65),
        UserActivity(test_user, "quiz", "eng_001", SkillCategory.ENGLISH_SPEAKING.value, score=55),
        UserActivity(test_user, "practice", "intro_002", SkillCategory.SELF_INTRODUCTION.value, score=80),
        UserActivity(test_user, "quiz", "aviation_001", SkillCategory.AVIATION_KNOWLEDGE.value, score=45),
    ]

    for activity in activities:
        tracker.log_activity(activity)

    print("=== 개인화 추천 시스템 테스트 ===\n")

    # 스킬 분석
    print("1. 스킬 분석 결과:")
    summary = engine.get_skill_summary(test_user)
    print(f"   면접 준비도: {summary['readiness_score']}점")
    print(f"   취약 분야: {summary['weaknesses']}")
    print(f"   강점 분야: {summary['strengths']}")

    # 추천
    print("\n2. 맞춤 추천:")
    recs = engine.get_recommendations(test_user, limit=3)
    for rec in recs:
        print(f"   - {rec.title}")
        print(f"     이유: {rec.reason}")
        print(f"     우선순위: {rec.priority_score:.0f}")

    # 오늘의 미션
    print("\n3. 오늘의 학습 미션:")
    missions = engine.get_daily_mission(test_user)
    for i, m in enumerate(missions, 1):
        print(f"   미션 {i}: {m.title}")
