# -*- coding: utf-8 -*-
"""
realism_enhancer.py
D. 현실성 (-) 해결 모듈

해결하는 문제:
17. 면접관 1명만 → 2-4명 다중 면접관 시뮬레이션
18. 압박 질문 부족 → 꼬임/압박 질문 모드
19. 예상 밖 상황 없음 → 랜덤 돌발 상황
20. 컨디션 시뮬레이션 없음 → 피곤/마지막 응시자 모드
21. 실제 면접 환경 부족 → 시간 제한 + 긴장감 조성
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime
import random


# ============================================================
# 17. 다중 면접관 시뮬레이션
# ============================================================

class InterviewerRole(Enum):
    """면접관 역할"""
    MAIN = "main"  # 주 면접관
    HR = "hr"  # 인사담당
    SENIOR = "senior"  # 선배 승무원
    MANAGER = "manager"  # 부서장


@dataclass
class Interviewer:
    """면접관"""
    interviewer_id: str
    name: str
    role: InterviewerRole
    personality: str  # "friendly", "strict", "neutral", "analytical"
    focus_areas: List[str]
    question_style: str


@dataclass
class MultiInterviewerSession:
    """다중 면접관 세션"""
    session_id: str
    interviewers: List[Interviewer]
    current_interviewer_index: int
    question_history: List[Dict]
    mode: str  # "sequential", "random", "tag_team"


class MultiInterviewerSimulator:
    """다중 면접관 시뮬레이터"""

    # 면접관 프리셋
    INTERVIEWER_PRESETS = {
        "대한항공": [
            Interviewer("kal_1", "김 부장", InterviewerRole.MANAGER, "strict", ["서비스", "위기대처"], "압박형"),
            Interviewer("kal_2", "이 과장", InterviewerRole.HR, "neutral", ["인성", "동기"], "탐색형"),
            Interviewer("kal_3", "박 선임", InterviewerRole.SENIOR, "friendly", ["태도", "팀워크"], "공감형"),
        ],
        "아시아나항공": [
            Interviewer("oz_1", "정 부장", InterviewerRole.MANAGER, "analytical", ["논리", "영어"], "분석형"),
            Interviewer("oz_2", "최 과장", InterviewerRole.HR, "friendly", ["성격", "적합성"], "친화형"),
            Interviewer("oz_3", "강 선임", InterviewerRole.SENIOR, "neutral", ["서비스", "상황대처"], "실무형"),
        ],
    }

    # 역할별 질문 스타일
    ROLE_QUESTIONS = {
        InterviewerRole.MANAGER: [
            "왜 우리 회사여야 합니까?",
            "5년 후 자신의 모습은?",
            "가장 힘들었던 상황은?",
        ],
        InterviewerRole.HR: [
            "자기소개 해주세요",
            "장점과 단점은?",
            "스트레스 해소법은?",
        ],
        InterviewerRole.SENIOR: [
            "승무원의 가장 중요한 덕목은?",
            "어려운 승객을 어떻게 대하겠습니까?",
            "팀워크 경험을 말씀해주세요",
        ],
    }

    def __init__(self):
        pass

    def create_session(
        self,
        airline: str,
        num_interviewers: int = 3,
        mode: str = "sequential"
    ) -> MultiInterviewerSession:
        """다중 면접관 세션 생성"""

        presets = self.INTERVIEWER_PRESETS.get(airline, self.INTERVIEWER_PRESETS["대한항공"])
        interviewers = presets[:num_interviewers]

        return MultiInterviewerSession(
            session_id=f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            interviewers=interviewers,
            current_interviewer_index=0,
            question_history=[],
            mode=mode
        )

    def get_current_interviewer(self, session: MultiInterviewerSession) -> Interviewer:
        """현재 면접관"""
        return session.interviewers[session.current_interviewer_index]

    def get_next_question(self, session: MultiInterviewerSession) -> Dict:
        """다음 질문"""
        interviewer = self.get_current_interviewer(session)
        questions = self.ROLE_QUESTIONS.get(interviewer.role, [])

        if questions:
            question = random.choice(questions)
        else:
            question = "자기소개 해주세요"

        return {
            "interviewer": interviewer.name,
            "role": interviewer.role.value,
            "personality": interviewer.personality,
            "question": question
        }

    def rotate_interviewer(self, session: MultiInterviewerSession) -> None:
        """면접관 교체"""
        if session.mode == "sequential":
            session.current_interviewer_index = (session.current_interviewer_index + 1) % len(session.interviewers)
        elif session.mode == "random":
            session.current_interviewer_index = random.randint(0, len(session.interviewers) - 1)


# ============================================================
# 18. 압박/꼬임 질문 모드
# ============================================================

class PressureLevel(Enum):
    """압박 수준"""
    MILD = "mild"
    MODERATE = "moderate"
    INTENSE = "intense"


@dataclass
class PressureQuestion:
    """압박 질문"""
    question: str
    pressure_type: str  # "contradiction", "weakness", "challenge", "trap"
    level: PressureLevel
    expected_reaction: str
    tips: List[str]


class PressureQuestionGenerator:
    """압박 질문 생성기"""

    # 압박 질문 템플릿
    PRESSURE_QUESTIONS = {
        "contradiction": [
            PressureQuestion(
                "방금 말씀하신 내용과 자소서 내용이 다른 것 같은데요?",
                "contradiction", PressureLevel.MODERATE,
                "당황하지 않고 일관성 있게 설명",
                ["침착하게 부연 설명하기", "핵심 메시지는 유지하되 표현 보완"]
            ),
            PressureQuestion(
                "팀워크를 강조하셨는데, 개인 성과도 중요하지 않나요?",
                "contradiction", PressureLevel.MILD,
                "균형 잡힌 시각 제시",
                ["양쪽 모두 인정하기", "상황에 따른 유연성 강조"]
            ),
        ],
        "weakness": [
            PressureQuestion(
                "경험이 부족해 보이는데, 왜 뽑아야 하죠?",
                "weakness", PressureLevel.INTENSE,
                "자신감 있게 강점 어필",
                ["경험 대신 잠재력 강조", "배우려는 자세 어필", "구체적 노력 사례 제시"]
            ),
            PressureQuestion(
                "영어가 좀 약해 보이는데요?",
                "weakness", PressureLevel.MODERATE,
                "솔직하게 인정 후 개선 노력 설명",
                ["솔직히 인정하기", "구체적 개선 노력 설명", "향상된 부분 언급"]
            ),
        ],
        "challenge": [
            PressureQuestion(
                "왜 다른 항공사가 아니라 우리 회사입니까?",
                "challenge", PressureLevel.MODERATE,
                "진정성 있는 지원 동기 설명",
                ["해당 항공사만의 특별한 점 언급", "개인 가치관과 연결", "구체적 비전 제시"]
            ),
            PressureQuestion(
                "떨어지면 어떻게 하실 건가요?",
                "challenge", PressureLevel.MILD,
                "긍정적이고 성숙한 태도",
                ["아쉽지만 배움의 기회로", "다시 도전하겠다는 의지", "자기 발전 계획"]
            ),
        ],
        "trap": [
            PressureQuestion(
                "승무원 일이 힘든데 버틸 수 있겠어요?",
                "trap", PressureLevel.MODERATE,
                "도전과 열정 강조",
                ["힘든 점 인지하고 있음을 표현", "그럼에도 불구하고 하고 싶은 이유", "체력/정신력 관리 방법"]
            ),
            PressureQuestion(
                "솔직히 말해서, 특별해 보이지 않는데요?",
                "trap", PressureLevel.INTENSE,
                "당황하지 않고 차별점 설명",
                ["감정적으로 반응하지 않기", "구체적 차별점 조목조목 설명", "성장 가능성 강조"]
            ),
        ],
    }

    def __init__(self):
        pass

    def generate(
        self,
        pressure_type: str = None,
        level: PressureLevel = None,
        previous_answer: str = None
    ) -> PressureQuestion:
        """압박 질문 생성"""

        if pressure_type and pressure_type in self.PRESSURE_QUESTIONS:
            questions = self.PRESSURE_QUESTIONS[pressure_type]
        else:
            all_questions = []
            for qs in self.PRESSURE_QUESTIONS.values():
                all_questions.extend(qs)
            questions = all_questions

        if level:
            questions = [q for q in questions if q.level == level]

        if not questions:
            questions = self.PRESSURE_QUESTIONS["challenge"]

        return random.choice(questions)

    def get_all_types(self) -> List[str]:
        """모든 압박 유형"""
        return list(self.PRESSURE_QUESTIONS.keys())


# ============================================================
# 19. 랜덤 돌발 상황
# ============================================================

@dataclass
class SurpriseSituation:
    """돌발 상황"""
    situation_id: str
    title: str
    description: str
    trigger_point: str  # "beginning", "middle", "end", "after_answer"
    duration: int  # 초
    required_response: str
    scoring_criteria: List[str]


class SurpriseSituationGenerator:
    """돌발 상황 생성기"""

    SITUATIONS = [
        SurpriseSituation(
            "phone_ring", "전화벨 울림",
            "면접 중 휴대폰이 울립니다. 어떻게 하시겠습니까?",
            "middle", 5,
            "당황하지 않고 사과 후 끄기",
            ["침착함 유지", "즉각적 대처", "정중한 사과"]
        ),
        SurpriseSituation(
            "document_drop", "서류 떨어짐",
            "면접관이 서류를 떨어뜨렸습니다.",
            "middle", 3,
            "자연스럽게 주워드리기",
            ["순발력", "배려심", "자연스러움"]
        ),
        SurpriseSituation(
            "cough", "기침",
            "갑자기 기침이 나올 것 같습니다.",
            "after_answer", 5,
            "정중히 양해 구하고 대처",
            ["예의", "자연스러운 대처", "빠른 회복"]
        ),
        SurpriseSituation(
            "noise", "외부 소음",
            "밖에서 큰 소음이 들립니다.",
            "middle", 5,
            "동요하지 않고 계속하기",
            ["집중력", "침착함", "전문성"]
        ),
        SurpriseSituation(
            "wrong_name", "이름 잘못 부름",
            "면접관이 지원자의 이름을 잘못 불렀습니다.",
            "beginning", 3,
            "정중하게 정정하기",
            ["자신감", "정중함", "명확함"]
        ),
        SurpriseSituation(
            "time_pressure", "시간 압박",
            "면접관: '30초 안에 답변해주세요'",
            "middle", 30,
            "핵심만 간결하게 전달",
            ["순발력", "핵심 파악", "간결함"]
        ),
    ]

    def __init__(self):
        pass

    def get_random_situation(self, trigger_point: str = None) -> SurpriseSituation:
        """랜덤 돌발 상황"""
        if trigger_point:
            filtered = [s for s in self.SITUATIONS if s.trigger_point == trigger_point]
            if filtered:
                return random.choice(filtered)

        return random.choice(self.SITUATIONS)

    def should_trigger(self, elapsed_time: float, total_time: float) -> Tuple[bool, Optional[str]]:
        """돌발 상황 발생 여부 (확률 기반)"""
        progress = elapsed_time / total_time if total_time > 0 else 0

        # 확률 설정
        if progress < 0.1:
            trigger_point = "beginning"
            probability = 0.1
        elif progress < 0.7:
            trigger_point = "middle"
            probability = 0.05
        else:
            trigger_point = "end"
            probability = 0.08

        if random.random() < probability:
            return True, trigger_point

        return False, None


# ============================================================
# 20. 컨디션 시뮬레이션
# ============================================================

class ConditionType(Enum):
    """컨디션 유형"""
    OPTIMAL = "optimal"
    TIRED = "tired"
    NERVOUS = "nervous"
    LAST_CANDIDATE = "last_candidate"
    EARLY_MORNING = "early_morning"


@dataclass
class ConditionSettings:
    """컨디션 설정"""
    condition_type: ConditionType
    description: str
    interviewer_patience: float  # 0-1
    time_pressure: float  # 배수
    difficulty_modifier: float  # 배수
    tips: List[str]


class ConditionSimulator:
    """컨디션 시뮬레이터"""

    CONDITIONS = {
        ConditionType.OPTIMAL: ConditionSettings(
            ConditionType.OPTIMAL,
            "최적의 컨디션입니다",
            1.0, 1.0, 1.0,
            ["평소처럼 임하세요", "자신감을 가지세요"]
        ),
        ConditionType.TIRED: ConditionSettings(
            ConditionType.TIRED,
            "피곤한 상태입니다. 집중력이 떨어질 수 있습니다.",
            0.9, 1.0, 1.1,
            ["에너지를 끌어올리세요", "더 밝은 표정으로", "물을 마시고 심호흡"]
        ),
        ConditionType.NERVOUS: ConditionSettings(
            ConditionType.NERVOUS,
            "긴장된 상태입니다. 떨림이 있을 수 있습니다.",
            1.0, 1.2, 1.0,
            ["심호흡으로 진정하기", "준비한 것을 믿으세요", "천천히 말하기"]
        ),
        ConditionType.LAST_CANDIDATE: ConditionSettings(
            ConditionType.LAST_CANDIDATE,
            "마지막 응시자입니다. 면접관도 지쳤습니다.",
            0.7, 0.9, 1.2,
            ["에너지 넘치게!", "면접관을 깨우세요", "짧고 임팩트 있게"]
        ),
        ConditionType.EARLY_MORNING: ConditionSettings(
            ConditionType.EARLY_MORNING,
            "이른 아침 면접입니다 (07:00)",
            0.95, 1.0, 1.0,
            ["충분히 일찍 기상", "가벼운 스트레칭", "발성 연습"]
        ),
    }

    def __init__(self):
        pass

    def get_condition(self, condition_type: ConditionType) -> ConditionSettings:
        """컨디션 설정 조회"""
        return self.CONDITIONS.get(condition_type, self.CONDITIONS[ConditionType.OPTIMAL])

    def apply_condition_effects(
        self,
        base_score: float,
        condition: ConditionSettings
    ) -> float:
        """컨디션 효과 적용"""
        # 난이도가 높아지면 점수가 약간 낮아질 수 있음
        adjusted = base_score / condition.difficulty_modifier
        return max(0, min(100, adjusted))

    def get_random_condition(self) -> ConditionSettings:
        """랜덤 컨디션"""
        # 가중치 적용 (일반적인 상황이 더 자주)
        weights = [0.4, 0.2, 0.2, 0.1, 0.1]
        conditions = list(self.CONDITIONS.values())
        return random.choices(conditions, weights=weights)[0]


# ============================================================
# 21. 실제 면접 환경 조성
# ============================================================

@dataclass
class InterviewEnvironment:
    """면접 환경 설정"""
    time_limit: int  # 초
    warning_times: List[int]  # 경고 시점들 (남은 초)
    strict_mode: bool  # 시간 초과 시 자동 종료
    ambient_sounds: bool  # 배경 소리 여부
    tension_level: int  # 1-5


class EnvironmentSimulator:
    """환경 시뮬레이터"""

    # 환경 프리셋
    PRESETS = {
        "relaxed": InterviewEnvironment(
            time_limit=120, warning_times=[30, 10],
            strict_mode=False, ambient_sounds=False, tension_level=1
        ),
        "normal": InterviewEnvironment(
            time_limit=90, warning_times=[30, 15, 5],
            strict_mode=False, ambient_sounds=False, tension_level=3
        ),
        "strict": InterviewEnvironment(
            time_limit=60, warning_times=[20, 10, 5],
            strict_mode=True, ambient_sounds=True, tension_level=4
        ),
        "intense": InterviewEnvironment(
            time_limit=45, warning_times=[15, 5],
            strict_mode=True, ambient_sounds=True, tension_level=5
        ),
    }

    # 시간 경고 메시지
    TIME_WARNINGS = {
        60: "1분 남았습니다",
        30: "30초 남았습니다. 마무리해주세요.",
        15: "15초 남았습니다!",
        10: "10초!",
        5: "5초!",
    }

    def __init__(self):
        pass

    def get_preset(self, preset_name: str) -> InterviewEnvironment:
        """프리셋 조회"""
        return self.PRESETS.get(preset_name, self.PRESETS["normal"])

    def get_time_warning(self, remaining_seconds: int) -> Optional[str]:
        """시간 경고 메시지"""
        return self.TIME_WARNINGS.get(remaining_seconds)

    def check_time_exceeded(
        self,
        elapsed: float,
        environment: InterviewEnvironment
    ) -> Tuple[bool, Optional[str]]:
        """시간 초과 확인"""
        remaining = environment.time_limit - elapsed

        if remaining <= 0:
            if environment.strict_mode:
                return True, "시간이 초과되었습니다. 답변이 종료됩니다."
            else:
                return False, "시간이 초과되었습니다. 마무리해주세요."

        # 경고 체크
        for warning_time in environment.warning_times:
            if abs(remaining - warning_time) < 0.5:
                return False, self.get_time_warning(warning_time)

        return False, None

    def get_tension_effects(self, tension_level: int) -> Dict:
        """긴장감 효과"""
        effects = {
            1: {"message": "편안한 분위기입니다", "color": "green"},
            2: {"message": "약간의 긴장감이 있습니다", "color": "blue"},
            3: {"message": "적당한 긴장감입니다", "color": "yellow"},
            4: {"message": "높은 긴장감입니다", "color": "orange"},
            5: {"message": "매우 긴장되는 상황입니다", "color": "red"},
        }
        return effects.get(tension_level, effects[3])


# ============================================================
# 편의 함수들
# ============================================================

_multi_interviewer = MultiInterviewerSimulator()
_pressure_generator = PressureQuestionGenerator()
_surprise_generator = SurpriseSituationGenerator()
_condition_simulator = ConditionSimulator()
_environment_simulator = EnvironmentSimulator()


def create_multi_interviewer_session(
    airline: str,
    num_interviewers: int = 3
) -> MultiInterviewerSession:
    """다중 면접관 세션 생성"""
    return _multi_interviewer.create_session(airline, num_interviewers)


def get_next_interviewer_question(session: MultiInterviewerSession) -> Dict:
    """다음 면접관 질문"""
    return _multi_interviewer.get_next_question(session)


def generate_pressure_question(
    pressure_type: str = None,
    level: str = None
) -> PressureQuestion:
    """압박 질문 생성"""
    lvl = PressureLevel(level) if level else None
    return _pressure_generator.generate(pressure_type, lvl)


def get_random_surprise() -> SurpriseSituation:
    """랜덤 돌발 상황"""
    return _surprise_generator.get_random_situation()


def get_condition_settings(condition_type: str) -> ConditionSettings:
    """컨디션 설정"""
    ct = ConditionType(condition_type) if condition_type else ConditionType.OPTIMAL
    return _condition_simulator.get_condition(ct)


def get_environment_preset(preset_name: str) -> InterviewEnvironment:
    """환경 프리셋"""
    return _environment_simulator.get_preset(preset_name)


def check_time_status(elapsed: float, preset_name: str = "normal") -> Dict:
    """시간 상태 확인"""
    env = get_environment_preset(preset_name)
    exceeded, message = _environment_simulator.check_time_exceeded(elapsed, env)
    remaining = max(0, env.time_limit - elapsed)

    return {
        "exceeded": exceeded,
        "message": message,
        "remaining": remaining,
        "progress_percent": min(100, (elapsed / env.time_limit) * 100)
    }
