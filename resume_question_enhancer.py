# resume_question_enhancer.py
# Phase C2: 자소서 기반 질문 고도화 모듈
# FlyReady Lab Enhancement

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re
import random


class QuestionIntent(Enum):
    """질문 의도 유형"""
    VERIFICATION = "verification"      # 검증 (진위 확인)
    DEPTH = "depth"                    # 심층 (상세 탐색)
    CONSISTENCY = "consistency"        # 일관성 (앞뒤 비교)
    PRESSURE = "pressure"              # 압박 (스트레스 테스트)
    TRAP = "trap"                      # 함정 (취약점 공략)
    VALUE = "value"                    # 가치관 (판단 기준)


class FollowUpType(Enum):
    """꼬리질문 유형"""
    CONDITION_CHANGE = "condition_change"     # 조건 변화
    PRIORITY_CONFLICT = "priority_conflict"   # 우선순위 충돌
    LIMIT_RECOGNITION = "limit_recognition"   # 한계 인식
    REPEATABILITY = "repeatability"           # 재현성 검증
    ALTERNATIVE = "alternative"               # 대안 탐색
    DEEPER = "deeper"                         # 깊이 있는 후속


@dataclass
class InterviewerPerspective:
    """면접관 관점 분석 결과"""
    attention_points: List[str]          # 주목 포인트
    verification_needs: List[str]        # 검증이 필요한 부분
    potential_concerns: List[str]        # 우려 사항
    positive_signals: List[str]          # 긍정 신호
    interview_strategy: str              # 면접 전략


@dataclass
class TrapQuestion:
    """함정 질문"""
    question: str
    intent: QuestionIntent
    trap_type: str                        # 함정 유형
    expected_weak_answer: str             # 약한 답변 예시
    ideal_answer_strategy: str            # 이상적 답변 전략
    follow_up_if_trapped: str             # 함정에 빠졌을 때 꼬리질문


@dataclass
class ExpectedAnswer:
    """예상 답변 가이드"""
    question: str
    model_answer: str                     # 모범 답변
    key_points: List[str]                 # 핵심 포인트
    common_mistakes: List[str]            # 흔한 실수
    scoring_criteria: List[str]           # 평가 기준


@dataclass
class FollowUpSimulation:
    """꼬리질문 시뮬레이션"""
    initial_question: str
    follow_up_chain: List[Dict[str, str]]  # [{question, expected_response, next_followup}...]
    total_depth: int
    difficulty_progression: List[str]      # [쉬움, 보통, 어려움...]


# =====================
# 면접관 관점 분석 패턴
# =====================

INTERVIEWER_ATTENTION_PATTERNS = {
    "specific_numbers": {
        "pattern": r'\d+년|\d+개월|\d+명|\d+%|\d+등|\d+위|\d+회',
        "attention": "수치의 정확성을 검증하고 싶어함",
        "question_type": "검증 질문",
    },
    "role_claim": {
        "pattern": r'(리더|팀장|대표|회장|부회장|총무)',
        "attention": "실제 역할 수행 내용을 확인하고 싶어함",
        "question_type": "역할 검증",
    },
    "achievement": {
        "pattern": r'(수상|1등|우승|최우수|대상|선발)',
        "attention": "성과의 과정과 기여도를 알고 싶어함",
        "question_type": "성과 검증",
    },
    "conflict_resolution": {
        "pattern": r'(갈등|해결|극복|어려움|문제)',
        "attention": "구체적인 해결 과정을 듣고 싶어함",
        "question_type": "과정 검증",
    },
    "service_experience": {
        "pattern": r'(고객|서비스|응대|클레임|불만)',
        "attention": "실제 서비스 상황 대처법을 확인하고 싶어함",
        "question_type": "경험 검증",
    },
    "language_ability": {
        "pattern": r'(영어|중국어|일본어|외국어|토익|토플|회화)',
        "attention": "실제 언어 사용 능력을 테스트하고 싶어함",
        "question_type": "능력 검증",
    },
    "abstract_claim": {
        "pattern": r'(열정|최선|노력|열심히|다양한|많은)',
        "attention": "추상적 표현의 구체적 증거를 원함",
        "question_type": "구체화 요청",
    },
}

# =====================
# 함정 질문 템플릿
# =====================

TRAP_QUESTION_TEMPLATES = {
    "과장_검증": [
        {
            "template": "방금 말씀하신 {achievement}에서, 본인 없이 팀원들만으로도 같은 결과를 냈을까요?",
            "trap_type": "기여도 함정",
            "weak_answer": "네, 아마 가능했을 것 같습니다",
            "strategy": "본인의 고유한 기여를 구체적으로 설명하되, 팀워크도 인정",
        },
        {
            "template": "{role}로서 가장 어려웠던 결정은 무엇이었고, 왜 그 선택을 후회하지 않나요?",
            "trap_type": "리더십 함정",
            "weak_answer": "후회하는 부분이 없습니다",
            "strategy": "어려웠던 결정을 인정하고, 배운 점 강조",
        },
    ],
    "일관성_검증": [
        {
            "template": "자소서에서는 {value1}을 강조하셨는데, 방금은 {value2}가 중요하다고 하셨네요. 둘 중 정말 중요한 건 뭔가요?",
            "trap_type": "가치관 불일치 함정",
            "weak_answer": "둘 다 중요합니다",
            "strategy": "상황에 따른 우선순위 조정 능력 보여주기",
        },
        {
            "template": "아까는 {claim1}라고 하셨는데, 자소서에는 {claim2}라고 쓰셨네요?",
            "trap_type": "진술 불일치 함정",
            "weak_answer": "그게... 표현이 달랐을 뿐입니다",
            "strategy": "차이점을 인정하고 맥락 설명, 핵심 메시지 재강조",
        },
    ],
    "압박_질문": [
        {
            "template": "솔직히 말해서, 그 정도 경험으로 {airline} 승무원이 될 수 있다고 생각하세요?",
            "trap_type": "자신감 함정",
            "weak_answer": "잘 모르겠습니다 / 노력하겠습니다",
            "strategy": "구체적 준비 과정 제시 + 배움 의지 표현",
        },
        {
            "template": "다른 지원자들도 비슷한 경험 얘기하는데, 본인이 특별한 이유가 뭔가요?",
            "trap_type": "차별화 함정",
            "weak_answer": "저는 더 열심히 할 것입니다",
            "strategy": "구체적인 차별점 + 독특한 관점 제시",
        },
    ],
    "가치관_충돌": [
        {
            "template": "안전과 서비스 중 하나만 선택해야 한다면?",
            "trap_type": "양자택일 함정",
            "weak_answer": "둘 다 중요합니다",
            "strategy": "안전 우선 원칙 명확히, 서비스는 안전 위에서 가능",
        },
        {
            "template": "회사 규정과 승객 요청이 충돌하면 어떻게 하시겠어요?",
            "trap_type": "규정 vs 고객 함정",
            "weak_answer": "상황에 따라 다릅니다",
            "strategy": "규정 준수 원칙 + 고객 만족을 위한 대안 제시",
        },
    ],
    "약점_공략": [
        {
            "template": "이 경험에서 실패했거나 아쉬웠던 부분은 없었나요?",
            "trap_type": "완벽주의 함정",
            "weak_answer": "특별히 없었습니다",
            "strategy": "아쉬운 점 인정 + 개선 과정 + 성장 포인트",
        },
        {
            "template": "팀원과 의견 충돌이 있었을 때, 결국 본인 의견을 포기한 적 있나요?",
            "trap_type": "유연성 vs 주관 함정",
            "weak_answer": "없습니다, 제 의견이 맞았으니까요",
            "strategy": "포기가 아닌 '조율' 경험, 더 나은 결과 도출",
        },
    ],
}

# =====================
# 예상 답변 평가 기준
# =====================

ANSWER_SCORING_CRITERIA = {
    "지원동기": [
        "항공사 특성에 대한 이해도",
        "개인 경험과의 연결성",
        "진정성 있는 동기 제시",
        "입사 후 기여 의지",
        "직무 이해도",
    ],
    "성격의 장단점": [
        "자기 객관화 능력",
        "장점의 구체적 증명",
        "단점 인정의 솔직함",
        "개선 노력의 구체성",
        "직무 적합성 연결",
    ],
    "서비스 경험": [
        "STAR 구조 활용",
        "상황 설명의 구체성",
        "본인 행동의 명확성",
        "결과의 측정 가능성",
        "교훈 도출",
    ],
    "팀워크/협업": [
        "팀 상황 이해",
        "본인 역할 명확성",
        "갈등 해결 과정",
        "기여도 증명",
        "팀 성과와 개인 기여 균형",
    ],
    "입사 후 포부": [
        "구체적 목표 설정",
        "실현 가능한 계획",
        "단계별 성장 로드맵",
        "회사 비전과의 연결",
        "장기적 관점",
    ],
}

# =====================
# 꼬리질문 체인 템플릿
# =====================

FOLLOWUP_CHAIN_TEMPLATES = {
    "경험_검증": [
        {
            "depth": 1,
            "question": "그때 구체적으로 어떤 행동을 하셨나요?",
            "expected": "구체적 행동 나열",
            "difficulty": "쉬움",
        },
        {
            "depth": 2,
            "question": "그 행동을 선택한 이유는요?",
            "expected": "판단 근거 설명",
            "difficulty": "보통",
        },
        {
            "depth": 3,
            "question": "다른 방법도 있었을 텐데, 왜 그 방법이었나요?",
            "expected": "대안 비교 및 선택 근거",
            "difficulty": "어려움",
        },
        {
            "depth": 4,
            "question": "만약 그 방법이 안 됐다면 어떻게 했을 것 같아요?",
            "expected": "유연성 및 대안 사고",
            "difficulty": "매우 어려움",
        },
    ],
    "역할_검증": [
        {
            "depth": 1,
            "question": "그 역할에서 가장 중요하게 생각한 게 뭐였나요?",
            "expected": "핵심 가치 제시",
            "difficulty": "쉬움",
        },
        {
            "depth": 2,
            "question": "팀원들은 그걸 어떻게 평가했나요?",
            "expected": "타인 피드백 공유",
            "difficulty": "보통",
        },
        {
            "depth": 3,
            "question": "가장 어려웠던 팀원은 누구였고, 어떻게 대했나요?",
            "expected": "갈등 관리 능력",
            "difficulty": "어려움",
        },
        {
            "depth": 4,
            "question": "그 팀원이 지금 여기 있다면 뭐라고 말할 것 같아요?",
            "expected": "관계 성찰 및 객관성",
            "difficulty": "매우 어려움",
        },
    ],
    "가치관_검증": [
        {
            "depth": 1,
            "question": "왜 그게 중요하다고 생각하세요?",
            "expected": "가치관 근거",
            "difficulty": "쉬움",
        },
        {
            "depth": 2,
            "question": "그 가치관이 충돌할 때는 어떻게 하시나요?",
            "expected": "우선순위 판단",
            "difficulty": "보통",
        },
        {
            "depth": 3,
            "question": "그래도 선택해야 한다면요?",
            "expected": "결단력 표현",
            "difficulty": "어려움",
        },
        {
            "depth": 4,
            "question": "그 선택으로 손해 본 적 있나요?",
            "expected": "일관성 및 책임감",
            "difficulty": "매우 어려움",
        },
    ],
    "서비스_검증": [
        {
            "depth": 1,
            "question": "그 고객은 어떤 상태였나요?",
            "expected": "상황 파악 능력",
            "difficulty": "쉬움",
        },
        {
            "depth": 2,
            "question": "본인이 먼저 알아챈 건가요, 고객이 말한 건가요?",
            "expected": "관찰력/민감성",
            "difficulty": "보통",
        },
        {
            "depth": 3,
            "question": "규정상 안 되는 요청이었다면 어떻게 했을까요?",
            "expected": "규정과 서비스 균형",
            "difficulty": "어려움",
        },
        {
            "depth": 4,
            "question": "그 고객이 또 불만을 제기한다면요?",
            "expected": "지속적 서비스 마인드",
            "difficulty": "매우 어려움",
        },
    ],
}

# =====================
# 면접관 관점 분석기
# =====================

class InterviewerPerspectiveAnalyzer:
    """면접관 관점 분석"""

    def analyze_from_interviewer_view(
        self,
        resume_text: str,
        item_type: str,
        airline: str
    ) -> InterviewerPerspective:
        """면접관 관점에서 자소서 분석"""

        attention_points = []
        verification_needs = []
        potential_concerns = []
        positive_signals = []

        # 패턴 기반 분석
        for pattern_name, pattern_data in INTERVIEWER_ATTENTION_PATTERNS.items():
            matches = re.findall(pattern_data["pattern"], resume_text)
            if matches:
                attention_points.append(f"{pattern_data['attention']} ({', '.join(matches[:3])})")
                verification_needs.append(pattern_data["question_type"])

        # 긍정 신호 탐지
        positive_patterns = [
            (r'\d+년|\d+개월', "구체적 기간 제시"),
            (r'\d+%|향상|개선|증가', "성과 수치화"),
            (r'직접|스스로|주도적', "주도성 표현"),
            (r'배웠|깨달|성장', "성찰 능력"),
        ]

        for pattern, signal in positive_patterns:
            if re.search(pattern, resume_text):
                positive_signals.append(signal)

        # 우려 사항 탐지
        concern_patterns = [
            (r'어릴\s*때부터\s*(꿈|승무원)', "진부한 표현 - 더 최근 계기 필요"),
            (r'열심히|최선을|노력', "추상적 표현 - 구체적 증거 필요"),
            (r'다양한|많은|여러', "모호한 표현 - 구체화 필요"),
        ]

        for pattern, concern in concern_patterns:
            if re.search(pattern, resume_text):
                potential_concerns.append(concern)

        # 분량 체크
        text_length = len(resume_text.replace(" ", ""))
        if text_length < 300:
            potential_concerns.append("분량 부족 - 내용이 너무 짧음")
        elif text_length > 700:
            potential_concerns.append("분량 초과 - 핵심 요약 필요")

        # 면접 전략 결정
        if len(verification_needs) >= 3:
            strategy = "검증 중심 면접: 여러 주장에 대한 구체적 증거 요청"
        elif len(potential_concerns) >= 2:
            strategy = "개선점 탐색 면접: 약점 보완 의지 및 성장 가능성 확인"
        elif len(positive_signals) >= 3:
            strategy = "심층 탐색 면접: 경험의 깊이와 응용 능력 확인"
        else:
            strategy = "기본 검증 면접: 자소서 내용의 진정성 확인"

        return InterviewerPerspective(
            attention_points=attention_points[:5],
            verification_needs=list(set(verification_needs))[:4],
            potential_concerns=potential_concerns[:4],
            positive_signals=positive_signals[:4],
            interview_strategy=strategy,
        )


# =====================
# 함정 질문 생성기
# =====================

class TrapQuestionGenerator:
    """함정 질문 생성"""

    def generate_trap_questions(
        self,
        resume_text: str,
        item_type: str,
        airline: str
    ) -> List[TrapQuestion]:
        """자소서 기반 함정 질문 생성"""

        trap_questions = []

        # 과장 표현 탐지
        achievement_matches = re.findall(r'(수상|1등|우승|최우수|대상|선발)', resume_text)
        role_matches = re.findall(r'(리더|팀장|대표|회장|부회장)', resume_text)

        # 과장 검증 함정
        if achievement_matches:
            for tpl in TRAP_QUESTION_TEMPLATES["과장_검증"]:
                q = tpl["template"].format(
                    achievement=achievement_matches[0],
                    role=role_matches[0] if role_matches else "담당자"
                )
                trap_questions.append(TrapQuestion(
                    question=q,
                    intent=QuestionIntent.VERIFICATION,
                    trap_type=tpl["trap_type"],
                    expected_weak_answer=tpl["weak_answer"],
                    ideal_answer_strategy=tpl["strategy"],
                    follow_up_if_trapped="그럼 팀에서 본인이 빠져도 괜찮았다는 건가요?",
                ))

        # 압박 질문
        for tpl in TRAP_QUESTION_TEMPLATES["압박_질문"]:
            q = tpl["template"].format(airline=airline)
            trap_questions.append(TrapQuestion(
                question=q,
                intent=QuestionIntent.PRESSURE,
                trap_type=tpl["trap_type"],
                expected_weak_answer=tpl["weak_answer"],
                ideal_answer_strategy=tpl["strategy"],
                follow_up_if_trapped="그게 노력만으로 될까요?",
            ))

        # 가치관 충돌
        for tpl in TRAP_QUESTION_TEMPLATES["가치관_충돌"]:
            trap_questions.append(TrapQuestion(
                question=tpl["template"],
                intent=QuestionIntent.VALUE,
                trap_type=tpl["trap_type"],
                expected_weak_answer=tpl["weak_answer"],
                ideal_answer_strategy=tpl["strategy"],
                follow_up_if_trapped="실제로 그런 상황이 있었나요?",
            ))

        # 약점 공략
        for tpl in TRAP_QUESTION_TEMPLATES["약점_공략"]:
            trap_questions.append(TrapQuestion(
                question=tpl["template"],
                intent=QuestionIntent.TRAP,
                trap_type=tpl["trap_type"],
                expected_weak_answer=tpl["weak_answer"],
                ideal_answer_strategy=tpl["strategy"],
                follow_up_if_trapped="그럼 완벽하게 했다는 건가요?",
            ))

        return trap_questions[:8]  # 최대 8개


# =====================
# 예상 답변 가이드 생성기
# =====================

class ExpectedAnswerGenerator:
    """예상 답변 가이드 생성"""

    def generate_answer_guide(
        self,
        question: str,
        resume_text: str,
        item_type: str
    ) -> ExpectedAnswer:
        """질문에 대한 예상 답변 가이드 생성"""

        # 질문 유형 분석
        is_why = "왜" in question or "이유" in question
        is_how = "어떻게" in question or "방법" in question
        is_what = "무엇" in question or "뭐" in question
        is_when = "언제" in question or "그때" in question

        # 답변 구조 가이드
        if is_why:
            structure = "이유 → 배경 → 결론"
            key_points = [
                "명확한 이유 먼저 제시",
                "구체적 배경/맥락 설명",
                "결론으로 연결",
            ]
        elif is_how:
            structure = "상황 → 행동 → 결과"
            key_points = [
                "상황 간략히 설정",
                "단계별 행동 설명",
                "결과와 배운 점",
            ]
        elif is_what:
            structure = "핵심 → 상세 → 의미"
            key_points = [
                "핵심 답변 먼저",
                "구체적 예시/상세",
                "의미/영향 설명",
            ]
        else:
            structure = "직답 → 설명 → 정리"
            key_points = [
                "질문에 직접 답변",
                "근거/설명 추가",
                "간결하게 정리",
            ]

        # 흔한 실수
        common_mistakes = [
            "질문과 다른 이야기로 빠지기",
            "너무 길게 답변하기",
            "추상적/일반적 표현만 사용",
            "구체적 예시 없이 주장만 하기",
            "자소서 내용 그대로 반복",
        ]

        # 평가 기준
        scoring = ANSWER_SCORING_CRITERIA.get(item_type, [
            "질문 이해도",
            "답변의 구체성",
            "논리적 구조",
            "직무 관련성",
            "진정성",
        ])

        # 모범 답변 구조 제시
        model_answer = f"[{structure}]\n"
        model_answer += "• 첫 문장: 질문의 핵심에 직접 답변\n"
        model_answer += "• 중간: 구체적 사례/근거로 뒷받침\n"
        model_answer += "• 마지막: 배운 점 또는 앞으로의 적용"

        return ExpectedAnswer(
            question=question,
            model_answer=model_answer,
            key_points=key_points,
            common_mistakes=common_mistakes[:3],
            scoring_criteria=scoring,
        )


# =====================
# 꼬리질문 시뮬레이터
# =====================

class FollowUpSimulator:
    """꼬리질문 시뮬레이션"""

    def simulate_followup_chain(
        self,
        initial_question: str,
        resume_text: str,
        max_depth: int = 4
    ) -> FollowUpSimulation:
        """꼬리질문 체인 시뮬레이션"""

        # 질문 유형 판단
        if any(kw in initial_question for kw in ["경험", "상황", "했", "했나요"]):
            chain_type = "경험_검증"
        elif any(kw in initial_question for kw in ["역할", "리더", "팀"]):
            chain_type = "역할_검증"
        elif any(kw in initial_question for kw in ["왜", "이유", "중요"]):
            chain_type = "가치관_검증"
        elif any(kw in initial_question for kw in ["고객", "서비스", "응대"]):
            chain_type = "서비스_검증"
        else:
            chain_type = "경험_검증"  # 기본값

        # 체인 템플릿 가져오기
        template_chain = FOLLOWUP_CHAIN_TEMPLATES.get(chain_type, FOLLOWUP_CHAIN_TEMPLATES["경험_검증"])

        # 시뮬레이션 체인 구성
        follow_up_chain = []
        difficulty_progression = []

        for i, tpl in enumerate(template_chain[:max_depth]):
            follow_up_chain.append({
                "depth": tpl["depth"],
                "question": tpl["question"],
                "expected_response": tpl["expected"],
                "tip": f"Depth {tpl['depth']}: {tpl['expected']}를 명확히 답변",
            })
            difficulty_progression.append(tpl["difficulty"])

        return FollowUpSimulation(
            initial_question=initial_question,
            follow_up_chain=follow_up_chain,
            total_depth=len(follow_up_chain),
            difficulty_progression=difficulty_progression,
        )

    def generate_dynamic_followup(
        self,
        user_answer: str,
        question_context: str
    ) -> List[str]:
        """사용자 답변 기반 동적 꼬리질문 생성"""

        followups = []

        # 추상적 답변 감지
        abstract_patterns = [
            r'열심히|최선|노력',
            r'다양한|많은|여러',
            r'좋은|잘|훌륭',
        ]

        for pattern in abstract_patterns:
            if re.search(pattern, user_answer):
                followups.append("구체적으로 어떤 행동을 하셨나요?")
                break

        # 수치 언급 시
        if re.search(r'\d+', user_answer):
            followups.append("그 수치는 어떻게 측정하신 건가요?")

        # 팀/협업 언급 시
        if re.search(r'팀|함께|협력|동료', user_answer):
            followups.append("그중 본인의 역할은 구체적으로 뭐였나요?")

        # 성과 언급 시
        if re.search(r'결과|성과|달성|개선', user_answer):
            followups.append("그 성과가 가능했던 핵심 요인은 뭘까요?")

        # 감정/태도 언급 시
        if re.search(r'느끼|생각|판단', user_answer):
            followups.append("그렇게 판단한 근거가 뭐였나요?")

        # 기본 꼬리질문
        if not followups:
            followups = [
                "좀 더 구체적으로 말씀해 주시겠어요?",
                "그때 가장 어려웠던 점은 뭐였나요?",
                "다시 그 상황이라면 같은 선택을 하실 건가요?",
            ]

        return followups[:3]


# =====================
# 통합 분석기
# =====================

class EnhancedResumeQuestionAnalyzer:
    """통합 자소서 질문 분석기"""

    def __init__(self):
        self.perspective_analyzer = InterviewerPerspectiveAnalyzer()
        self.trap_generator = TrapQuestionGenerator()
        self.answer_generator = ExpectedAnswerGenerator()
        self.followup_simulator = FollowUpSimulator()

    def analyze_complete(
        self,
        resume_text: str,
        airline: str,
        item_type: str,
        base_question: Optional[str] = None
    ) -> Dict:
        """종합 분석"""

        # 면접관 관점 분석
        perspective = self.perspective_analyzer.analyze_from_interviewer_view(
            resume_text, item_type, airline
        )

        # 함정 질문 생성
        trap_questions = self.trap_generator.generate_trap_questions(
            resume_text, item_type, airline
        )

        # 예상 답변 가이드 (기본 질문이 있으면)
        answer_guide = None
        if base_question:
            answer_guide = self.answer_generator.generate_answer_guide(
                base_question, resume_text, item_type
            )

        # 꼬리질문 시뮬레이션
        sample_question = base_question or f"{item_type}에 대해 자세히 말씀해 주세요."
        followup_sim = self.followup_simulator.simulate_followup_chain(
            sample_question, resume_text
        )

        return {
            "interviewer_perspective": {
                "attention_points": perspective.attention_points,
                "verification_needs": perspective.verification_needs,
                "potential_concerns": perspective.potential_concerns,
                "positive_signals": perspective.positive_signals,
                "interview_strategy": perspective.interview_strategy,
            },
            "trap_questions": [
                {
                    "question": tq.question,
                    "trap_type": tq.trap_type,
                    "weak_answer": tq.expected_weak_answer,
                    "strategy": tq.ideal_answer_strategy,
                    "followup": tq.follow_up_if_trapped,
                }
                for tq in trap_questions
            ],
            "answer_guide": {
                "question": answer_guide.question,
                "model_answer": answer_guide.model_answer,
                "key_points": answer_guide.key_points,
                "common_mistakes": answer_guide.common_mistakes,
                "scoring_criteria": answer_guide.scoring_criteria,
            } if answer_guide else None,
            "followup_simulation": {
                "initial_question": followup_sim.initial_question,
                "chain": followup_sim.follow_up_chain,
                "total_depth": followup_sim.total_depth,
                "difficulty": followup_sim.difficulty_progression,
            },
        }


# =====================
# 편의 함수
# =====================

def analyze_from_interviewer(text: str, airline: str, item_type: str) -> Dict:
    """면접관 관점 분석 (간편 함수)"""
    analyzer = InterviewerPerspectiveAnalyzer()
    result = analyzer.analyze_from_interviewer_view(text, item_type, airline)
    return {
        "attention_points": result.attention_points,
        "verification_needs": result.verification_needs,
        "potential_concerns": result.potential_concerns,
        "positive_signals": result.positive_signals,
        "interview_strategy": result.interview_strategy,
    }


def generate_trap_questions(text: str, airline: str, item_type: str) -> List[Dict]:
    """함정 질문 생성 (간편 함수)"""
    generator = TrapQuestionGenerator()
    questions = generator.generate_trap_questions(text, item_type, airline)
    return [
        {
            "question": q.question,
            "trap_type": q.trap_type,
            "weak_answer": q.expected_weak_answer,
            "strategy": q.ideal_answer_strategy,
            "followup": q.follow_up_if_trapped,
        }
        for q in questions
    ]


def get_answer_guide(question: str, text: str, item_type: str) -> Dict:
    """예상 답변 가이드 (간편 함수)"""
    generator = ExpectedAnswerGenerator()
    result = generator.generate_answer_guide(question, text, item_type)
    return {
        "question": result.question,
        "model_answer": result.model_answer,
        "key_points": result.key_points,
        "common_mistakes": result.common_mistakes,
        "scoring_criteria": result.scoring_criteria,
    }


def simulate_followup(question: str, text: str, max_depth: int = 4) -> Dict:
    """꼬리질문 시뮬레이션 (간편 함수)"""
    simulator = FollowUpSimulator()
    result = simulator.simulate_followup_chain(question, text, max_depth)
    return {
        "initial_question": result.initial_question,
        "chain": result.follow_up_chain,
        "total_depth": result.total_depth,
        "difficulty": result.difficulty_progression,
    }


def generate_dynamic_followup(answer: str, context: str) -> List[str]:
    """동적 꼬리질문 생성 (간편 함수)"""
    simulator = FollowUpSimulator()
    return simulator.generate_dynamic_followup(answer, context)


def analyze_resume_question_enhanced(
    text: str,
    airline: str,
    item_type: str,
    question: Optional[str] = None
) -> Dict:
    """자소서 질문 고도화 분석 (간편 함수)"""
    analyzer = EnhancedResumeQuestionAnalyzer()
    return analyzer.analyze_complete(text, airline, item_type, question)
