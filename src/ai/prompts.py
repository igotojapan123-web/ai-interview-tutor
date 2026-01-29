"""
AI Prompt Templates.

Structured prompts for the interview AI engine.
"""

from typing import Dict, List, Optional
from enum import Enum


class InterviewType(str, Enum):
    """Types of interview sessions."""
    SELF_INTRODUCTION = "self_introduction"
    MOTIVATION = "motivation"
    SITUATIONAL = "situational"
    SERVICE_MIND = "service_mind"
    ENGLISH = "english"
    GROUP_DISCUSSION = "group_discussion"
    FINAL_INTERVIEW = "final_interview"


class PromptTemplates:
    """Collection of AI prompts for interview simulation."""

    # ==========================================================================
    # System Prompts
    # ==========================================================================

    INTERVIEWER_SYSTEM_PROMPT = """당신은 항공사 면접관입니다. {airline_name}의 채용 면접을 진행합니다.

역할:
- 전문적이고 친절한 면접관으로서 지원자를 평가합니다
- 실제 항공사 면접과 동일한 질문과 평가 기준을 적용합니다
- 지원자의 답변에 대해 적절한 후속 질문을 합니다

평가 기준:
1. 서비스 마인드 (고객 중심 사고)
2. 의사소통 능력 (명확성, 자신감)
3. 팀워크 및 협동심
4. 문제 해결 능력
5. 항공사 및 직무 이해도
6. 외모/태도 (자세, 표정, 제스처)

주의사항:
- 한국어로 진행하되, 영어 면접 요청 시 영어로 전환
- 지원자를 존중하면서 전문적인 톤 유지
- 실제 면접처럼 시간을 의식하여 진행"""

    FEEDBACK_SYSTEM_PROMPT = """당신은 항공사 면접 전문 코치입니다.
지원자의 답변을 분석하고 구체적인 피드백을 제공합니다.

피드백 구조:
1. 전체 점수 (100점 만점)
2. 세부 항목별 점수
   - 내용 적절성 (30점)
   - 표현력/전달력 (25점)
   - 논리성/구조 (20점)
   - 자신감/태도 (15점)
   - 시간 관리 (10점)
3. 강점 (2-3개)
4. 개선점 (2-3개)
5. 구체적인 개선 제안
6. 예시 답변 (선택적)

피드백 스타일:
- 구체적이고 실행 가능한 조언
- 긍정적인 부분 먼저 언급
- 개선점은 건설적으로 제시
- 실제 합격 사례 기반의 조언"""

    # ==========================================================================
    # Interview Questions by Type
    # ==========================================================================

    QUESTIONS: Dict[InterviewType, List[Dict]] = {
        InterviewType.SELF_INTRODUCTION: [
            {
                "question": "1분 자기소개 해주세요.",
                "time_limit": 60,
                "tips": "이름, 지원동기, 강점을 간결하게"
            },
            {
                "question": "30초 자기소개 해주세요.",
                "time_limit": 30,
                "tips": "핵심만 짧고 임팩트 있게"
            },
            {
                "question": "본인을 한 단어로 표현한다면?",
                "time_limit": 45,
                "tips": "단어 선택 이유와 에피소드 연결"
            }
        ],
        InterviewType.MOTIVATION: [
            {
                "question": "왜 승무원이 되고 싶으신가요?",
                "time_limit": 90,
                "tips": "진정성 있는 동기와 구체적 계기"
            },
            {
                "question": "왜 {airline_name}에 지원하셨나요?",
                "time_limit": 90,
                "tips": "항공사 특성과 본인의 가치관 연결"
            },
            {
                "question": "10년 후 자신의 모습은?",
                "time_limit": 60,
                "tips": "승무원 커리어 내 성장 계획"
            }
        ],
        InterviewType.SITUATIONAL: [
            {
                "question": "기내에서 승객이 갑자기 쓰러졌습니다. 어떻게 대처하시겠습니까?",
                "time_limit": 120,
                "tips": "STAR 기법: 상황-과제-행동-결과"
            },
            {
                "question": "승객이 무리한 요구를 한다면 어떻게 하시겠습니까?",
                "time_limit": 90,
                "tips": "고객 중심 사고 + 규정 준수 균형"
            },
            {
                "question": "동료와 의견 충돌이 생긴다면?",
                "time_limit": 90,
                "tips": "협력과 존중 강조"
            }
        ],
        InterviewType.SERVICE_MIND: [
            {
                "question": "서비스란 무엇이라고 생각하시나요?",
                "time_limit": 60,
                "tips": "본인만의 서비스 철학"
            },
            {
                "question": "최고의 서비스를 받은 경험을 말씀해주세요.",
                "time_limit": 90,
                "tips": "구체적 경험 + 느낀 점 + 적용 방법"
            },
            {
                "question": "화난 고객을 응대한 경험이 있나요?",
                "time_limit": 90,
                "tips": "실제 경험 + 해결 과정 + 배운 점"
            }
        ],
        InterviewType.ENGLISH: [
            {
                "question": "Please introduce yourself in English.",
                "time_limit": 60,
                "tips": "Clear pronunciation, confident delivery"
            },
            {
                "question": "Why do you want to be a flight attendant?",
                "time_limit": 90,
                "tips": "Genuine motivation, specific examples"
            },
            {
                "question": "Tell me about a time you helped someone.",
                "time_limit": 90,
                "tips": "STAR method in English"
            }
        ]
    }

    # ==========================================================================
    # Evaluation Criteria
    # ==========================================================================

    EVALUATION_CRITERIA = {
        "content": {
            "weight": 0.30,
            "description": "답변 내용의 적절성과 깊이",
            "rubric": {
                90: "핵심을 정확히 파악, 구체적 예시와 함께 설득력 있게 전달",
                70: "핵심 이해, 적절한 내용이나 구체성 부족",
                50: "기본적인 내용 전달, 깊이 부족",
                30: "질문 의도 파악 부족, 관련성 낮은 답변"
            }
        },
        "delivery": {
            "weight": 0.25,
            "description": "표현력, 발음, 속도, 자신감",
            "rubric": {
                90: "자연스럽고 자신감 있는 전달, 명확한 발음",
                70: "대체로 자연스러운 전달, 약간의 긴장",
                50: "다소 경직된 전달, 발음이나 속도 개선 필요",
                30: "자신감 부족, 전달력 미흡"
            }
        },
        "structure": {
            "weight": 0.20,
            "description": "논리적 구조와 흐름",
            "rubric": {
                90: "명확한 도입-본론-결론, 논리적 연결",
                70: "구조 있으나 연결 다소 부자연스러움",
                50: "구조 미흡, 산만한 전개",
                30: "논리적 흐름 부재"
            }
        },
        "attitude": {
            "weight": 0.15,
            "description": "태도, 자세, 표정, 아이컨택",
            "rubric": {
                90: "밝은 표정, 바른 자세, 적절한 아이컨택",
                70: "대체로 좋은 태도, 일부 개선 필요",
                50: "다소 경직, 표정 관리 필요",
                30: "태도 개선 많이 필요"
            }
        },
        "time": {
            "weight": 0.10,
            "description": "시간 관리",
            "rubric": {
                90: "제한 시간 내 완성도 있게 마무리",
                70: "시간 약간 초과/미달, 내용은 적절",
                50: "시간 관리 미흡",
                30: "시간 크게 초과/미달"
            }
        }
    }

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    @classmethod
    def get_questions(
        cls,
        interview_type: InterviewType,
        airline_name: str = "항공사"
    ) -> List[Dict]:
        """Get questions for interview type."""
        questions = cls.QUESTIONS.get(interview_type, [])
        # Replace airline placeholder
        return [
            {
                **q,
                "question": q["question"].format(airline_name=airline_name)
            }
            for q in questions
        ]

    @classmethod
    def get_interviewer_prompt(cls, airline_name: str = "항공사") -> str:
        """Get interviewer system prompt."""
        return cls.INTERVIEWER_SYSTEM_PROMPT.format(airline_name=airline_name)

    @classmethod
    def get_feedback_prompt(cls) -> str:
        """Get feedback analyzer system prompt."""
        return cls.FEEDBACK_SYSTEM_PROMPT

    @classmethod
    def create_question_prompt(
        cls,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """Create prompt for asking a question."""
        prompt = f"면접 질문: {question}"
        if context:
            prompt += f"\n\n이전 맥락: {context}"
        return prompt

    @classmethod
    def create_feedback_prompt(
        cls,
        question: str,
        answer: str,
        answer_duration: float,
        time_limit: int
    ) -> str:
        """Create prompt for feedback analysis."""
        return f"""다음 면접 답변을 분석해주세요.

질문: {question}
제한 시간: {time_limit}초
실제 답변 시간: {answer_duration:.1f}초

답변 내용:
{answer}

위 평가 기준에 따라 JSON 형식으로 피드백을 제공해주세요:
{{
    "overall_score": 0-100,
    "scores": {{
        "content": 0-100,
        "delivery": 0-100,
        "structure": 0-100,
        "attitude": 0-100,
        "time": 0-100
    }},
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"],
    "suggestions": "구체적인 개선 제안",
    "sample_answer": "예시 답변 (선택적)"
}}"""
