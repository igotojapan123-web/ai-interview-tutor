# -*- coding: utf-8 -*-
"""
content_enhancer.py
F. 콘텐츠 (-) 해결 모듈

해결하는 문제:
26. 합격자 사례 부족 → 합격자 답변 음성 클립 + 분석
27. 항공사별 함정질문 없음 → 항공사별 함정질문 DB
28. 위기상황 대처 없음 → 기내 의료/비상상황 시뮬레이션
29. MBTI 맞춤 없음 → 성향별 맞춤 피드백
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime
import random


# ============================================================
# 26. 합격자 사례 분석
# ============================================================

@dataclass
class PasserExample:
    """합격자 사례"""
    example_id: str
    airline: str
    question: str
    answer: str
    score: float
    analysis: Dict
    key_points: List[str]
    audio_available: bool
    year: int


@dataclass
class AnswerComparison:
    """답변 비교 분석"""
    user_answer: str
    passer_answer: str
    similarity_score: float
    missing_elements: List[str]
    good_elements: List[str]
    improvement_tips: List[str]


class PasserExampleDatabase:
    """합격자 사례 DB"""

    # 합격자 답변 예시 (실제로는 DB에서 가져옴)
    EXAMPLES = [
        PasserExample(
            "ex_001", "대한항공",
            "왜 승무원이 되고 싶으신가요?",
            "어릴 적 가족여행에서 승무원분의 따뜻한 미소와 세심한 배려가 여행의 피로를 잊게 해주었습니다. "
            "그때부터 저도 누군가에게 행복한 추억을 선물하는 사람이 되고 싶다는 꿈을 키워왔습니다. "
            "대한항공의 Excellence in Flight 가치처럼, 모든 승객분들께 최상의 경험을 제공하고 싶습니다.",
            92.0,
            {"structure": 95, "content": 90, "emotion": 93, "relevance": 90},
            ["개인 경험 연결", "항공사 가치 언급", "진정성 있는 동기", "구체적 비전"],
            True, 2024
        ),
        PasserExample(
            "ex_002", "대한항공",
            "본인의 장점과 단점은?",
            "저의 장점은 어떤 상황에서도 침착함을 유지하는 것입니다. 카페 아르바이트 중 갑작스러운 정전 상황에서도 "
            "손님들을 안내하고 환불 처리를 완료했습니다. 단점은 완벽주의 성향인데, 이를 보완하기 위해 "
            "우선순위를 정하고 80%에서 만족하는 연습을 하고 있습니다.",
            88.0,
            {"structure": 90, "content": 85, "honesty": 90, "improvement": 88},
            ["STAR 기법 활용", "구체적 사례 제시", "단점의 개선 노력"],
            True, 2024
        ),
        PasserExample(
            "ex_003", "아시아나항공",
            "팀워크 경험을 말씀해주세요",
            "대학 축제 준비위원으로 활동하며 50명의 팀원을 조율해야 했습니다. 의견 충돌이 있을 때 "
            "각자의 입장을 경청하고 공통 목표를 상기시켜 합의점을 찾았습니다. 결과적으로 역대 최고 만족도를 "
            "기록했고, 협력의 중요성을 배웠습니다.",
            90.0,
            {"structure": 92, "content": 88, "leadership": 90, "result": 90},
            ["규모 제시", "갈등 해결 과정", "구체적 결과", "배운 점"],
            True, 2024
        ),
    ]

    def __init__(self):
        pass

    def get_examples(
        self,
        airline: str = None,
        question_type: str = None,
        limit: int = 5
    ) -> List[PasserExample]:
        """합격자 사례 조회"""
        examples = self.EXAMPLES

        if airline:
            examples = [e for e in examples if e.airline == airline]

        return examples[:limit]

    def get_example_for_question(self, question: str) -> Optional[PasserExample]:
        """질문에 맞는 사례 조회"""
        # 간단한 키워드 매칭 (실제로는 더 정교한 매칭 필요)
        keywords = {
            "승무원": ["왜 승무원", "지원동기"],
            "장점": ["장점", "단점", "강점", "약점"],
            "팀워크": ["팀워크", "협력", "갈등"],
        }

        question_lower = question.lower()
        for example in self.EXAMPLES:
            for key_type, key_list in keywords.items():
                if any(k in question_lower for k in key_list):
                    if any(k in example.question.lower() for k in key_list):
                        return example

        return self.EXAMPLES[0] if self.EXAMPLES else None

    def compare_with_passer(
        self,
        user_answer: str,
        question: str
    ) -> AnswerComparison:
        """합격자 답변과 비교"""
        example = self.get_example_for_question(question)

        if not example:
            return AnswerComparison(
                user_answer=user_answer,
                passer_answer="",
                similarity_score=0,
                missing_elements=["비교 사례 없음"],
                good_elements=[],
                improvement_tips=["다양한 연습을 계속하세요"]
            )

        # 간단한 비교 분석
        missing = []
        good = []

        for point in example.key_points:
            if point.lower() in user_answer.lower() or any(
                word in user_answer for word in point.split()[:2]
            ):
                good.append(point)
            else:
                missing.append(point)

        # 유사도 계산 (간단한 버전)
        similarity = len(good) / len(example.key_points) * 100 if example.key_points else 50

        tips = []
        if missing:
            tips.append(f"합격자 답변에는 '{missing[0]}'가 포함되어 있어요")
        if similarity < 50:
            tips.append("답변 구조를 더 체계적으로 만들어보세요")
        if not tips:
            tips.append("좋은 답변이에요! 연습을 계속하세요")

        return AnswerComparison(
            user_answer=user_answer,
            passer_answer=example.answer,
            similarity_score=round(similarity, 1),
            missing_elements=missing,
            good_elements=good,
            improvement_tips=tips
        )


# ============================================================
# 27. 항공사별 함정질문 DB
# ============================================================

@dataclass
class TrapQuestion:
    """함정 질문"""
    question_id: str
    airline: str
    question: str
    trap_type: str  # "contradiction", "weakness", "values", "pressure"
    difficulty: int  # 1-5
    intent: str
    wrong_answer_example: str
    correct_approach: str
    tips: List[str]
    frequency: int  # 출제 빈도 (1-5)


class TrapQuestionDatabase:
    """함정 질문 DB"""

    TRAP_QUESTIONS = [
        # 대한항공
        TrapQuestion(
            "trap_kal_001", "대한항공",
            "다른 항공사에도 지원하셨나요?",
            "values", 3,
            "지원 진정성 확인",
            "아니요, 대한항공만 지원했습니다. (거짓말로 보일 수 있음)",
            "솔직하게 인정하되, 대한항공이 1순위인 이유를 강조",
            ["솔직함이 중요", "타 항공사 비하 금지", "해당 항공사 열정 강조"],
            5
        ),
        TrapQuestion(
            "trap_kal_002", "대한항공",
            "연봉이 생각보다 낮을 수 있는데 괜찮으신가요?",
            "values", 2,
            "금전적 동기 vs 직업적 열정 확인",
            "돈보다 꿈이 중요해서 괜찮습니다. (비현실적으로 보일 수 있음)",
            "현실적으로 인지하고 있으며, 성장 기회가 더 중요하다고 강조",
            ["현실적 인식 표현", "성장 기회 강조", "장기적 비전 언급"],
            4
        ),
        TrapQuestion(
            "trap_kal_003", "대한항공",
            "결혼하면 그만두실 건가요?",
            "pressure", 4,
            "장기 근속 의지 확인",
            "결혼해도 계속 일하겠습니다. (너무 단정적)",
            "장기적 커리어 비전을 설명하고, 일과 삶의 균형 추구 표현",
            ["차별적 질문임을 인식", "커리어 비전 강조", "균형 잡힌 답변"],
            3
        ),
        # 아시아나항공
        TrapQuestion(
            "trap_oz_001", "아시아나항공",
            "대한항공과 아시아나의 차이점은 무엇인가요?",
            "values", 4,
            "지원 항공사 이해도 및 비교 분석력",
            "대한항공은 규모가 크고, 아시아나는 서비스가 좋아요. (단순 비교)",
            "아시아나만의 차별점을 구체적으로 언급, 타사 비하 금지",
            ["타사 비하 금지", "해당 항공사 강점 집중", "구체적 정보 활용"],
            5
        ),
        TrapQuestion(
            "trap_oz_002", "아시아나항공",
            "승무원이 힘들다는데 왜 하고 싶으세요?",
            "pressure", 3,
            "직업에 대한 현실 인식 확인",
            "힘들어도 할 수 있어요. (피상적)",
            "힘든 점 인지하지만, 그것을 감수할 가치가 있는 이유 설명",
            ["현실 인식 표현", "긍정적 관점 유지", "구체적 각오 표현"],
            4
        ),
        # 제주항공
        TrapQuestion(
            "trap_7c_001", "제주항공",
            "LCC와 FSC 중 어디가 더 좋다고 생각하세요?",
            "values", 3,
            "지원 항공사 유형에 대한 이해",
            "LCC가 더 좋아요 / FSC가 더 좋아요. (일방적 판단)",
            "각각의 장점을 인정하고, 해당 항공사 선택 이유 설명",
            ["양쪽 장점 인정", "지원 항공사 선택 이유", "균형 잡힌 시각"],
            4
        ),
    ]

    def __init__(self):
        pass

    def get_trap_questions(
        self,
        airline: str = None,
        trap_type: str = None,
        difficulty: int = None
    ) -> List[TrapQuestion]:
        """함정 질문 조회"""
        questions = self.TRAP_QUESTIONS

        if airline:
            questions = [q for q in questions if q.airline == airline]
        if trap_type:
            questions = [q for q in questions if q.trap_type == trap_type]
        if difficulty:
            questions = [q for q in questions if q.difficulty == difficulty]

        return questions

    def get_random_trap(self, airline: str = None) -> TrapQuestion:
        """랜덤 함정 질문"""
        questions = self.get_trap_questions(airline)
        return random.choice(questions) if questions else self.TRAP_QUESTIONS[0]

    def get_trap_types(self) -> List[str]:
        """함정 질문 유형 목록"""
        return list(set(q.trap_type for q in self.TRAP_QUESTIONS))


# ============================================================
# 28. 위기상황 대처 시뮬레이션
# ============================================================

class EmergencyType(Enum):
    """비상상황 유형"""
    MEDICAL = "medical"
    UNRULY_PASSENGER = "unruly_passenger"
    TECHNICAL = "technical"
    WEATHER = "weather"
    SECURITY = "security"


@dataclass
class EmergencyScenario:
    """비상상황 시나리오"""
    scenario_id: str
    emergency_type: EmergencyType
    title: str
    situation: str
    required_actions: List[str]
    correct_procedure: List[str]
    common_mistakes: List[str]
    difficulty: int  # 1-5
    time_limit: int  # 초


class EmergencySimulator:
    """비상상황 시뮬레이터"""

    SCENARIOS = [
        EmergencyScenario(
            "em_001", EmergencyType.MEDICAL,
            "승객 호흡곤란",
            "비행 중 50대 남성 승객이 갑자기 호흡곤란을 호소합니다. 얼굴이 창백하고 식은땀을 흘리고 있습니다.",
            ["상황 파악", "의료 장비 준비", "기내 의사 호출", "기장 보고"],
            [
                "1. 침착하게 상황 파악 (의식, 호흡, 맥박)",
                "2. 산소 마스크 준비",
                "3. '기내에 의사 선생님 계십니까?' 방송",
                "4. 기장에게 상황 보고",
                "5. 비상 착륙 준비 가능성 안내",
            ],
            ["당황해서 우왕좌왕", "혼자 해결하려 함", "기장 보고 누락"],
            4, 120
        ),
        EmergencyScenario(
            "em_002", EmergencyType.UNRULY_PASSENGER,
            "난동 승객",
            "술에 취한 승객이 다른 승객에게 소리를 지르며 위협적인 행동을 합니다.",
            ["상황 개입", "분리 시도", "동료 지원 요청", "필요시 제압"],
            [
                "1. 차분하게 접근하여 진정 시도",
                "2. 다른 승객들 안전 확보",
                "3. 동료 승무원 지원 요청",
                "4. 상황 악화 시 기장 보고",
                "5. 필요시 착륙 후 경찰 인계",
            ],
            ["혼자 대응", "감정적 대응", "물리적 충돌"],
            5, 90
        ),
        EmergencyScenario(
            "em_003", EmergencyType.TECHNICAL,
            "산소 마스크 작동",
            "기내 압력 저하로 산소 마스크가 내려왔습니다. 승객들이 당황하고 있습니다.",
            ["본인 마스크 착용", "승객 안내", "침착 유지", "안전벨트 확인"],
            [
                "1. 본인 산소 마스크 먼저 착용",
                "2. 차분한 목소리로 안내 방송",
                "3. 승객 마스크 착용 도움",
                "4. 안전벨트 착용 확인",
                "5. 기장 지시 대기",
            ],
            ["본인 마스크 늦게 착용", "당황한 모습 보임"],
            3, 60
        ),
    ]

    def __init__(self):
        pass

    def get_scenario(
        self,
        emergency_type: EmergencyType = None,
        difficulty: int = None
    ) -> EmergencyScenario:
        """시나리오 조회"""
        scenarios = self.SCENARIOS

        if emergency_type:
            scenarios = [s for s in scenarios if s.emergency_type == emergency_type]
        if difficulty:
            scenarios = [s for s in scenarios if s.difficulty == difficulty]

        return random.choice(scenarios) if scenarios else self.SCENARIOS[0]

    def evaluate_response(
        self,
        scenario: EmergencyScenario,
        user_actions: List[str]
    ) -> Dict:
        """응답 평가"""
        correct_count = 0
        missed_actions = []
        extra_good = []

        for action in scenario.required_actions:
            if any(action.lower() in ua.lower() for ua in user_actions):
                correct_count += 1
            else:
                missed_actions.append(action)

        score = (correct_count / len(scenario.required_actions)) * 100 if scenario.required_actions else 0

        return {
            "score": round(score, 1),
            "correct_actions": correct_count,
            "total_required": len(scenario.required_actions),
            "missed_actions": missed_actions,
            "feedback": self._generate_feedback(score, missed_actions)
        }

    def _generate_feedback(self, score: float, missed: List[str]) -> str:
        if score >= 90:
            return "훌륭합니다! 비상상황에 적절히 대처했습니다."
        elif score >= 70:
            return f"좋은 대응이지만, {missed[0]}도 잊지 마세요."
        elif score >= 50:
            return f"기본적인 대응은 했지만, 여러 중요한 단계가 누락되었습니다."
        else:
            return "비상상황 대응 절차를 더 연습해야 합니다."


# ============================================================
# 29. MBTI 맞춤 피드백
# ============================================================

@dataclass
class MBTIProfile:
    """MBTI 프로필"""
    mbti_type: str
    strengths: List[str]
    weaknesses: List[str]
    interview_tips: List[str]
    communication_style: str
    stress_response: str


class MBTIFeedbackSystem:
    """MBTI 맞춤 피드백 시스템"""

    PROFILES = {
        "ENFJ": MBTIProfile(
            "ENFJ",
            ["공감 능력 우수", "리더십", "소통 능력"],
            ["지나친 배려로 본인 주장 약화", "감정적 결정"],
            ["객관적 근거 제시하기", "구체적 수치 활용"],
            "따뜻하고 설득력 있는 소통",
            "타인의 평가에 민감할 수 있음"
        ),
        "ENFP": MBTIProfile(
            "ENFP",
            ["창의성", "열정", "적응력"],
            ["산만함", "마무리 약함"],
            ["답변 구조화하기", "핵심에 집중하기"],
            "에너지 넘치고 자유로운 소통",
            "구속감에 스트레스 받음"
        ),
        "ENTJ": MBTIProfile(
            "ENTJ",
            ["결단력", "목표 지향", "논리적"],
            ["공감 표현 부족", "너무 직접적"],
            ["부드러운 표현 연습", "경청 자세 보이기"],
            "효율적이고 직접적인 소통",
            "통제력 상실에 스트레스"
        ),
        "ISFJ": MBTIProfile(
            "ISFJ",
            ["성실함", "배려", "책임감"],
            ["자기 주장 약함", "변화에 소극적"],
            ["자신감 있게 말하기", "성과 어필하기"],
            "조용하고 배려 깊은 소통",
            "갈등 상황에 스트레스"
        ),
        "ISTJ": MBTIProfile(
            "ISTJ",
            ["꼼꼼함", "신뢰성", "책임감"],
            ["융통성 부족", "표현 소극적"],
            ["유연한 태도 보이기", "밝은 표정 유지"],
            "정확하고 체계적인 소통",
            "불확실성에 스트레스"
        ),
        "ESFJ": MBTIProfile(
            "ESFJ",
            ["친화력", "봉사 정신", "협력적"],
            ["타인 의존", "비판에 민감"],
            ["주도적 태도 보이기", "독립적 사고 표현"],
            "따뜻하고 협력적인 소통",
            "불화에 스트레스"
        ),
        # 기본 프로필 (다른 유형은 이것 참조)
        "DEFAULT": MBTIProfile(
            "DEFAULT",
            ["다양한 강점 보유"],
            ["개선 영역 존재"],
            ["본인 강점 활용하기", "약점 보완하기"],
            "상황에 따른 유연한 소통",
            "개인별 스트레스 요인"
        ),
    }

    def __init__(self):
        pass

    def get_profile(self, mbti_type: str) -> MBTIProfile:
        """MBTI 프로필 조회"""
        return self.PROFILES.get(mbti_type.upper(), self.PROFILES["DEFAULT"])

    def get_personalized_feedback(
        self,
        mbti_type: str,
        score: float,
        category: str
    ) -> Dict:
        """맞춤 피드백"""
        profile = self.get_profile(mbti_type)

        feedback = {
            "mbti": mbti_type,
            "strength_used": [],
            "improvement_based_on_type": [],
            "specific_tips": []
        }

        # 점수에 따른 피드백
        if score >= 80:
            feedback["strength_used"] = profile.strengths[:2]
            feedback["improvement_based_on_type"] = [
                f"잘하고 있어요! {profile.strengths[0]}이(가) 잘 드러났습니다."
            ]
        else:
            feedback["improvement_based_on_type"] = [
                f"{profile.weaknesses[0]} 부분을 보완해보세요."
            ]

        feedback["specific_tips"] = profile.interview_tips

        return feedback

    def get_stress_management_tip(self, mbti_type: str) -> str:
        """스트레스 관리 팁"""
        profile = self.get_profile(mbti_type)
        return f"당신의 스트레스 요인: {profile.stress_response}. 심호흡하고 준비한 것을 믿으세요!"


# ============================================================
# 편의 함수들
# ============================================================

_passer_db = PasserExampleDatabase()
_trap_db = TrapQuestionDatabase()
_emergency_sim = EmergencySimulator()
_mbti_system = MBTIFeedbackSystem()


def get_passer_examples(airline: str = None, limit: int = 5) -> List[PasserExample]:
    """합격자 사례 조회"""
    return _passer_db.get_examples(airline, limit=limit)


def compare_with_passer(user_answer: str, question: str) -> AnswerComparison:
    """합격자 답변과 비교"""
    return _passer_db.compare_with_passer(user_answer, question)


def get_trap_questions(airline: str = None, trap_type: str = None) -> List[TrapQuestion]:
    """함정 질문 조회"""
    return _trap_db.get_trap_questions(airline, trap_type)


def get_random_trap_question(airline: str = None) -> TrapQuestion:
    """랜덤 함정 질문"""
    return _trap_db.get_random_trap(airline)


def get_emergency_scenario(difficulty: int = None) -> EmergencyScenario:
    """비상상황 시나리오"""
    return _emergency_sim.get_scenario(difficulty=difficulty)


def evaluate_emergency_response(scenario: EmergencyScenario, actions: List[str]) -> Dict:
    """비상상황 응답 평가"""
    return _emergency_sim.evaluate_response(scenario, actions)


def get_mbti_profile(mbti_type: str) -> MBTIProfile:
    """MBTI 프로필"""
    return _mbti_system.get_profile(mbti_type)


def get_mbti_feedback(mbti_type: str, score: float, category: str) -> Dict:
    """MBTI 맞춤 피드백"""
    return _mbti_system.get_personalized_feedback(mbti_type, score, category)
