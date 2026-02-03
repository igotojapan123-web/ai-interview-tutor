# interview_enhancer.py
# FlyReady Lab - 모의면접 기능 강화 모듈
# Phase B1: 핵심 면접 기능 500% 강화

import re
import json
import random
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# 설정
# =============================================================================

try:
    from config import LLM_MODEL_NAME, LLM_API_URL
    from env_config import OPENAI_API_KEY
except ImportError:
    LLM_MODEL_NAME = "gpt-4o-mini"
    LLM_API_URL = "https://api.openai.com/v1/chat/completions"
    OPENAI_API_KEY = ""


# =============================================================================
# 1. 면접관 캐릭터 시스템
# =============================================================================

class InterviewerType(Enum):
    """면접관 유형"""
    WARM = "warm"              # 온화한 면접관
    NEUTRAL = "neutral"        # 중립적 면접관
    SHARP = "sharp"            # 날카로운 면접관
    PRESSURE = "pressure"      # 압박 면접관


@dataclass
class InterviewerCharacter:
    """면접관 캐릭터"""
    type: InterviewerType
    name: str
    personality: str
    speaking_style: str
    feedback_style: str
    pressure_level: int  # 1-10
    follow_up_tendency: float  # 0-1 (꼬리질문 확률)
    avatar_style: str


# 면접관 캐릭터 정의
INTERVIEWER_CHARACTERS = {
    InterviewerType.WARM: InterviewerCharacter(
        type=InterviewerType.WARM,
        name="김민지 팀장",
        personality="따뜻하고 격려하는 성격. 지원자의 장점을 찾아주려 함",
        speaking_style="부드럽고 친근한 어조. 미소를 띤 표정.",
        feedback_style="긍정적인 점을 먼저 언급하고, 개선점은 조언 형태로 제시",
        pressure_level=3,
        follow_up_tendency=0.4,
        avatar_style="friendly"
    ),
    InterviewerType.NEUTRAL: InterviewerCharacter(
        type=InterviewerType.NEUTRAL,
        name="박서연 부장",
        personality="공정하고 객관적. 표준적인 면접 진행",
        speaking_style="명확하고 전문적인 어조. 중립적 표정.",
        feedback_style="객관적으로 장단점을 균형있게 제시",
        pressure_level=5,
        follow_up_tendency=0.5,
        avatar_style="professional"
    ),
    InterviewerType.SHARP: InterviewerCharacter(
        type=InterviewerType.SHARP,
        name="이정훈 상무",
        personality="분석적이고 날카로움. 답변의 논리적 허점을 파고듦",
        speaking_style="간결하고 직접적인 어조. 진지한 표정.",
        feedback_style="개선점을 직접적으로 지적. 구체적인 근거 요구",
        pressure_level=7,
        follow_up_tendency=0.7,
        avatar_style="serious"
    ),
    InterviewerType.PRESSURE: InterviewerCharacter(
        type=InterviewerType.PRESSURE,
        name="최현우 전무",
        personality="도전적이고 압박하는 스타일. 지원자의 한계를 테스트",
        speaking_style="빠르고 단호한 어조. 도전적인 시선.",
        feedback_style="부족한 점을 강조하고 즉각적인 대응 능력 평가",
        pressure_level=9,
        follow_up_tendency=0.9,
        avatar_style="intense"
    ),
}


def get_interviewer_character(interviewer_type: str) -> InterviewerCharacter:
    """면접관 캐릭터 가져오기"""
    type_map = {
        "warm": InterviewerType.WARM,
        "neutral": InterviewerType.NEUTRAL,
        "sharp": InterviewerType.SHARP,
        "pressure": InterviewerType.PRESSURE,
    }
    itype = type_map.get(interviewer_type.lower(), InterviewerType.NEUTRAL)
    return INTERVIEWER_CHARACTERS[itype]


def get_interviewer_prompt(character: InterviewerCharacter) -> str:
    """면접관 캐릭터 프롬프트 생성"""
    return f"""당신은 {character.name}입니다.

성격: {character.personality}
말투: {character.speaking_style}
피드백 스타일: {character.feedback_style}
압박 수준: {character.pressure_level}/10

이 캐릭터에 맞게 일관성 있게 행동하세요."""


# =============================================================================
# 2. AI 꼬리질문 시스템
# =============================================================================

class FollowUpQuestionGenerator:
    """꼬리질문 생성기"""

    # 꼬리질문 유형
    FOLLOW_UP_TYPES = {
        "clarification": "답변 내용을 더 명확히 해달라는 질문",
        "deep_dive": "특정 부분을 더 깊이 파고드는 질문",
        "challenge": "답변의 논리나 근거에 도전하는 질문",
        "example": "구체적인 사례나 예시를 요청하는 질문",
        "application": "다른 상황에 어떻게 적용할지 묻는 질문",
        "reflection": "자신의 경험을 되돌아보게 하는 질문",
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENAI_API_KEY

    def should_ask_follow_up(
        self,
        answer: str,
        answer_score: int,
        interviewer: InterviewerCharacter
    ) -> Tuple[bool, str]:
        """꼬리질문 여부 결정

        Returns:
            (should_ask, reason)
        """
        # 기본 확률
        base_probability = interviewer.follow_up_tendency

        # 점수에 따른 조정
        if answer_score < 50:
            base_probability += 0.2  # 부족한 답변에 더 질문
        elif answer_score > 80:
            base_probability -= 0.1  # 좋은 답변에는 덜 질문

        # 답변 길이에 따른 조정
        if len(answer) < 100:
            base_probability += 0.3  # 짧은 답변에 더 질문
            reason = "답변이 짧아서 추가 설명 필요"
        elif len(answer) > 500:
            base_probability -= 0.1  # 긴 답변에는 덜 질문
            reason = "충분히 상세한 답변"
        else:
            reason = "추가 정보 확인 필요"

        # 키워드 체크 (STAR 구조 부족 시)
        star_keywords = ["상황", "과제", "행동", "결과", "그래서", "때문에", "덕분에"]
        keyword_count = sum(1 for kw in star_keywords if kw in answer)
        if keyword_count < 2:
            base_probability += 0.2
            reason = "STAR 구조 보완 필요"

        # 최종 결정
        should_ask = random.random() < min(base_probability, 0.95)

        return should_ask, reason

    def generate_follow_up(
        self,
        original_question: str,
        answer: str,
        interviewer: InterviewerCharacter,
        follow_up_type: str = None,
        airline: str = ""
    ) -> Dict[str, Any]:
        """꼬리질문 생성"""
        if not self.api_key:
            return self._generate_fallback_follow_up(original_question, answer)

        # 꼬리질문 유형 결정
        if follow_up_type is None:
            follow_up_type = self._determine_follow_up_type(answer, interviewer)

        system_prompt = f"""당신은 항공사 면접관입니다.
{get_interviewer_prompt(interviewer)}

다음 규칙을 따르세요:
1. 지원자의 답변을 기반으로 꼬리질문을 생성합니다.
2. 꼬리질문 유형: {self.FOLLOW_UP_TYPES.get(follow_up_type, '추가 질문')}
3. 질문은 자연스럽고 면접 상황에 적합해야 합니다.
4. 한국어로 작성하세요."""

        user_prompt = f"""원래 질문: {original_question}

지원자 답변: {answer}

위 답변에 대한 꼬리질문을 1개 생성하세요.
꼬리질문 유형: {follow_up_type}

출력 형식 (JSON):
{{
    "follow_up_question": "꼬리질문 내용",
    "question_type": "{follow_up_type}",
    "purpose": "이 질문을 하는 이유 (1문장)",
    "expected_elements": ["답변에 포함되어야 할 요소 3개"]
}}"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500,
            }

            r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=30)
            r.raise_for_status()
            resp = r.json()

            content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")

            # JSON 파싱
            try:
                # JSON 블록 추출
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass

            return {
                "follow_up_question": content.strip(),
                "question_type": follow_up_type,
                "purpose": "추가 정보 확인",
                "expected_elements": []
            }

        except Exception as e:
            logger.error(f"꼬리질문 생성 실패: {e}")
            return self._generate_fallback_follow_up(original_question, answer)

    def _determine_follow_up_type(self, answer: str, interviewer: InterviewerCharacter) -> str:
        """답변 내용과 면접관 유형에 따른 꼬리질문 유형 결정"""
        # 면접관 유형별 선호 질문 유형
        type_preferences = {
            InterviewerType.WARM: ["reflection", "example", "application"],
            InterviewerType.NEUTRAL: ["clarification", "example", "deep_dive"],
            InterviewerType.SHARP: ["challenge", "deep_dive", "clarification"],
            InterviewerType.PRESSURE: ["challenge", "deep_dive", "application"],
        }

        preferences = type_preferences.get(interviewer.type, ["clarification"])

        # 답변 분석하여 가중치 조정
        if len(answer) < 150:
            # 짧은 답변 - 구체적 사례 요청
            if "example" in preferences:
                return "example"
            return "clarification"

        if "했습니다" in answer and "어떻게" not in answer:
            # 행동만 있고 방법이 없음
            return "deep_dive"

        if "생각합니다" in answer or "것 같습니다" in answer:
            # 추측성 답변 - 도전
            if interviewer.pressure_level >= 7:
                return "challenge"
            return "clarification"

        return random.choice(preferences)

    def _generate_fallback_follow_up(self, question: str, answer: str) -> Dict[str, Any]:
        """API 없을 때 기본 꼬리질문"""
        fallback_questions = [
            f"그 상황에서 가장 어려웠던 점은 무엇이었나요?",
            f"그 경험에서 구체적으로 어떤 교훈을 얻었나요?",
            f"다시 그 상황이 된다면 어떻게 다르게 하시겠습니까?",
            f"그 결과가 팀이나 조직에 어떤 영향을 미쳤나요?",
            f"그때 배운 것을 승무원 업무에 어떻게 적용하시겠습니까?",
        ]

        return {
            "follow_up_question": random.choice(fallback_questions),
            "question_type": "example",
            "purpose": "구체적인 경험 확인",
            "expected_elements": ["구체적 상황", "본인의 역할", "결과"]
        }


# 전역 꼬리질문 생성기
follow_up_generator = FollowUpQuestionGenerator()


# =============================================================================
# 3. 답변 키워드 분석 시스템
# =============================================================================

class KeywordAnalyzer:
    """답변 키워드 분석기"""

    # 항공사별 핵심 키워드
    AIRLINE_KEYWORDS = {
        "대한항공": {
            "core_values": ["Excellence", "진취성", "국제감각", "서비스정신", "팀워크", "KE Way"],
            "service_keywords": ["글로벌", "프리미엄", "안전", "품격", "전문성"],
            "personality_keywords": ["책임감", "성실", "도전", "배려", "소통"],
        },
        "아시아나항공": {
            "core_values": ["Beautiful People", "안전", "서비스", "지속가능성", "ESG"],
            "service_keywords": ["정성", "세심함", "따뜻함", "고객중심", "혁신"],
            "personality_keywords": ["진정성", "열정", "협력", "공감", "성장"],
        },
        "제주항공": {
            "core_values": ["7C정신", "Fun&Fly", "안전", "저비용", "신뢰", "도전"],
            "service_keywords": ["실용", "효율", "친근함", "합리적", "젊음"],
            "personality_keywords": ["유연함", "적극성", "팀워크", "긍정", "창의"],
        },
        "진에어": {
            "core_values": ["JINISM", "Fly better fly", "Safety", "Practicality", "Delight"],
            "service_keywords": ["실용적", "스마트", "트렌디", "편안함", "즐거움"],
            "personality_keywords": ["독창성", "활력", "친화력", "적응력", "열정"],
        },
        "티웨이항공": {
            "core_values": ["5S", "Safety", "Smart", "Satisfaction", "Sharing", "Sustainability"],
            "service_keywords": ["안전", "스마트", "만족", "공유", "지속가능"],
            "personality_keywords": ["성실", "협동", "책임감", "긍정", "성장"],
        },
        "default": {
            "core_values": ["안전", "서비스", "팀워크", "고객만족"],
            "service_keywords": ["친절", "전문성", "배려", "소통", "위기대응"],
            "personality_keywords": ["책임감", "긍정", "협력", "열정", "성장"],
        },
    }

    # STAR 구조 키워드
    STAR_KEYWORDS = {
        "situation": ["상황", "당시", "때", "처음", "배경", "~에서", "경험"],
        "task": ["과제", "목표", "해야", "필요", "역할", "담당", "책임"],
        "action": ["했습니다", "노력", "시도", "방법", "접근", "실행", "조치"],
        "result": ["결과", "성과", "덕분에", "달성", "개선", "배운", "느낀"],
    }

    # 면접 필수 키워드
    INTERVIEW_ESSENTIAL_KEYWORDS = {
        "자기소개": ["저는", "경험", "강점", "지원", "준비"],
        "지원동기": ["항공사", "승무원", "꿈", "비전", "열정"],
        "강점약점": ["강점", "약점", "장점", "단점", "개선", "노력"],
        "팀워크": ["팀", "협력", "소통", "갈등", "조율", "해결"],
        "고객서비스": ["고객", "서비스", "응대", "만족", "불만", "해결"],
        "위기대응": ["위기", "긴급", "대처", "침착", "판단", "안전"],
    }

    def analyze_keywords(
        self,
        answer: str,
        question: str,
        airline: str
    ) -> Dict[str, Any]:
        """키워드 분석 수행"""
        result = {
            "airline_keywords": self._check_airline_keywords(answer, airline),
            "star_structure": self._check_star_structure(answer),
            "question_relevance": self._check_question_keywords(answer, question),
            "missing_keywords": [],
            "strength_keywords": [],
            "keyword_score": 0,
            "recommendations": [],
        }

        # 점수 계산
        airline_score = result["airline_keywords"]["score"]
        star_score = result["star_structure"]["score"]
        relevance_score = result["question_relevance"]["score"]

        result["keyword_score"] = int((airline_score * 0.3 + star_score * 0.4 + relevance_score * 0.3))

        # 누락된 키워드 식별
        result["missing_keywords"] = self._identify_missing_keywords(result)

        # 잘 사용된 키워드
        result["strength_keywords"] = self._identify_strength_keywords(result)

        # 추천사항 생성
        result["recommendations"] = self._generate_recommendations(result, airline)

        return result

    def _check_airline_keywords(self, answer: str, airline: str) -> Dict:
        """항공사별 키워드 체크"""
        keywords = self.AIRLINE_KEYWORDS.get(airline, self.AIRLINE_KEYWORDS["default"])
        answer_lower = answer.lower()

        found = {
            "core_values": [],
            "service_keywords": [],
            "personality_keywords": [],
        }

        for category in found.keys():
            for kw in keywords.get(category, []):
                if kw.lower() in answer_lower or kw in answer:
                    found[category].append(kw)

        total_expected = sum(len(keywords.get(cat, [])) for cat in found.keys())
        total_found = sum(len(v) for v in found.values())

        # 점수 계산 (최소 3개 이상 시 만점 가능)
        score = min(100, int((total_found / max(total_expected * 0.3, 1)) * 100))

        return {
            "found": found,
            "total_found": total_found,
            "score": score,
        }

    def _check_star_structure(self, answer: str) -> Dict:
        """STAR 구조 체크"""
        found = {}

        for component, keywords in self.STAR_KEYWORDS.items():
            found[component] = any(kw in answer for kw in keywords)

        complete_count = sum(1 for v in found.values() if v)
        score = int((complete_count / 4) * 100)

        return {
            "components": found,
            "complete_count": complete_count,
            "score": score,
            "is_complete": complete_count >= 3,
        }

    def _check_question_keywords(self, answer: str, question: str) -> Dict:
        """질문 관련 키워드 체크"""
        # 질문 유형 감지
        question_type = None
        for q_type, keywords in self.INTERVIEW_ESSENTIAL_KEYWORDS.items():
            if any(kw in question for kw in keywords[:3]):
                question_type = q_type
                break

        if question_type:
            expected_keywords = self.INTERVIEW_ESSENTIAL_KEYWORDS[question_type]
            found_keywords = [kw for kw in expected_keywords if kw in answer]
            score = min(100, int((len(found_keywords) / len(expected_keywords)) * 150))
        else:
            found_keywords = []
            score = 50  # 질문 유형 불명시 기본 점수

        return {
            "question_type": question_type,
            "found_keywords": found_keywords,
            "score": score,
        }

    def _identify_missing_keywords(self, result: Dict) -> List[str]:
        """누락된 핵심 키워드 식별"""
        missing = []

        # STAR 구조 누락
        star = result["star_structure"]["components"]
        if not star.get("situation"):
            missing.append("상황/배경 설명 부족")
        if not star.get("action"):
            missing.append("구체적 행동 설명 부족")
        if not star.get("result"):
            missing.append("결과/성과 언급 부족")

        # 항공사 키워드 부족
        if result["airline_keywords"]["total_found"] < 2:
            missing.append("항공사 핵심가치 언급 부족")

        return missing[:3]  # 최대 3개

    def _identify_strength_keywords(self, result: Dict) -> List[str]:
        """잘 사용된 키워드 식별"""
        strengths = []

        airline_found = result["airline_keywords"]["found"]
        for category, keywords in airline_found.items():
            if keywords:
                strengths.append(f"{keywords[0]} 언급")

        if result["star_structure"]["is_complete"]:
            strengths.append("STAR 구조 완성")

        return strengths[:3]

    def _generate_recommendations(self, result: Dict, airline: str) -> List[str]:
        """개선 추천사항 생성"""
        recommendations = []

        if result["keyword_score"] < 50:
            recommendations.append(f"{airline}의 핵심가치와 인재상을 더 반영해보세요")

        if not result["star_structure"]["is_complete"]:
            missing_components = [
                k for k, v in result["star_structure"]["components"].items()
                if not v
            ]
            if "result" in missing_components:
                recommendations.append("경험의 결과와 배운 점을 명확히 언급하세요")
            if "action" in missing_components:
                recommendations.append("본인이 취한 구체적인 행동을 설명하세요")

        if result["airline_keywords"]["total_found"] < 2:
            recommendations.append("항공사의 핵심가치를 자연스럽게 녹여보세요")

        return recommendations[:4]


# 전역 키워드 분석기
keyword_analyzer = KeywordAnalyzer()


# =============================================================================
# 4. 시간 관리 피드백 시스템
# =============================================================================

class TimeManagementAnalyzer:
    """답변 시간 관리 분석기"""

    # 이상적인 답변 시간 (초)
    IDEAL_TIME_RANGE = {
        "short": (30, 60),      # 짧은 답변 (자기소개 등)
        "standard": (60, 90),   # 표준 답변 (경험 질문 등)
        "detailed": (90, 120),  # 상세 답변 (상황 대응 등)
    }

    # 질문 유형별 권장 시간
    QUESTION_TIME_GUIDE = {
        "자기소개": "short",
        "지원동기": "standard",
        "강점": "standard",
        "약점": "standard",
        "경험": "detailed",
        "상황": "detailed",
        "갈등": "detailed",
        "팀워크": "standard",
        "서비스": "standard",
        "마지막": "short",
    }

    def analyze_time(
        self,
        elapsed_seconds: int,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        """답변 시간 분석"""
        # 질문 유형 감지
        question_type = self._detect_question_type(question)
        ideal_range = self.IDEAL_TIME_RANGE.get(
            self.QUESTION_TIME_GUIDE.get(question_type, "standard"),
            (60, 90)
        )

        min_time, max_time = ideal_range
        mid_time = (min_time + max_time) / 2

        # 점수 계산
        if min_time <= elapsed_seconds <= max_time:
            score = 100
            status = "optimal"
            feedback = "적절한 답변 시간입니다."
        elif elapsed_seconds < min_time:
            # 너무 짧음
            shortage = min_time - elapsed_seconds
            score = max(30, 100 - shortage * 2)
            status = "too_short"
            feedback = f"답변이 너무 짧습니다. {shortage}초 더 상세히 설명해보세요."
        else:
            # 너무 김
            excess = elapsed_seconds - max_time
            score = max(50, 100 - excess)
            status = "too_long"
            feedback = f"답변이 다소 깁니다. 핵심만 간결하게 정리해보세요."

        # 답변 길이와 시간의 관계 분석
        char_per_second = len(answer) / max(elapsed_seconds, 1)
        pace_analysis = self._analyze_pace(char_per_second)

        # 구조 제안
        structure_suggestion = self._suggest_structure(
            elapsed_seconds, len(answer), question_type
        )

        return {
            "elapsed_seconds": elapsed_seconds,
            "ideal_range": ideal_range,
            "question_type": question_type,
            "score": score,
            "status": status,
            "feedback": feedback,
            "pace_analysis": pace_analysis,
            "structure_suggestion": structure_suggestion,
            "time_breakdown": self._calculate_time_breakdown(ideal_range),
        }

    def _detect_question_type(self, question: str) -> str:
        """질문 유형 감지"""
        for q_type in self.QUESTION_TIME_GUIDE.keys():
            if q_type in question:
                return q_type

        # 기본 분류
        if "어떻게" in question or "설명" in question:
            return "상황"
        elif "왜" in question or "이유" in question:
            return "지원동기"
        else:
            return "standard"

    def _analyze_pace(self, char_per_second: float) -> Dict:
        """말하기 속도 분석 (글자/초)"""
        # 한국어 평균 말하기 속도: 4-6 글자/초
        if 4 <= char_per_second <= 6:
            return {
                "pace": "normal",
                "cps": char_per_second,
                "feedback": "적절한 속도로 말하고 있습니다."
            }
        elif char_per_second < 4:
            return {
                "pace": "slow",
                "cps": char_per_second,
                "feedback": "말이 다소 느립니다. 자신감 있게 말해보세요."
            }
        else:
            return {
                "pace": "fast",
                "cps": char_per_second,
                "feedback": "말이 빠릅니다. 천천히 명확하게 말해보세요."
            }

    def _suggest_structure(
        self,
        elapsed: int,
        answer_length: int,
        question_type: str
    ) -> str:
        """시간 배분 구조 제안"""
        if question_type in ["경험", "상황", "갈등"]:
            return """권장 시간 배분 (90초 기준):
- 상황 설명: 15초
- 과제/문제: 15초
- 행동: 40초 (가장 중요!)
- 결과 & 배운점: 20초"""
        elif question_type == "자기소개":
            return """권장 시간 배분 (45초 기준):
- 인사 & 이름: 5초
- 경력/경험 요약: 20초
- 강점 & 지원동기: 15초
- 마무리: 5초"""
        else:
            return """권장 시간 배분:
- 핵심 답변: 60%
- 구체적 예시: 30%
- 마무리: 10%"""

    def _calculate_time_breakdown(self, ideal_range: Tuple[int, int]) -> Dict:
        """STAR 구조별 시간 배분"""
        total = ideal_range[1]  # 최대 시간 기준
        return {
            "situation": int(total * 0.15),
            "task": int(total * 0.15),
            "action": int(total * 0.45),
            "result": int(total * 0.25),
        }


# 전역 시간 관리 분석기
time_analyzer = TimeManagementAnalyzer()


# =============================================================================
# 5. 통합 면접 강화 시스템
# =============================================================================

class EnhancedInterviewEngine:
    """강화된 면접 엔진"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.follow_up_generator = FollowUpQuestionGenerator(self.api_key)
        self.keyword_analyzer = keyword_analyzer
        self.time_analyzer = time_analyzer

    def analyze_answer_complete(
        self,
        question: str,
        answer: str,
        elapsed_seconds: int,
        airline: str,
        interviewer_type: str = "neutral"
    ) -> Dict[str, Any]:
        """답변 종합 분석"""
        interviewer = get_interviewer_character(interviewer_type)

        # 1. 키워드 분석
        keyword_result = self.keyword_analyzer.analyze_keywords(answer, question, airline)

        # 2. 시간 관리 분석
        time_result = self.time_analyzer.analyze_time(elapsed_seconds, question, answer)

        # 3. 꼬리질문 결정
        should_follow_up, follow_up_reason = self.follow_up_generator.should_ask_follow_up(
            answer, keyword_result["keyword_score"], interviewer
        )

        follow_up = None
        if should_follow_up:
            follow_up = self.follow_up_generator.generate_follow_up(
                question, answer, interviewer, airline=airline
            )

        # 4. 종합 점수 계산
        keyword_score = keyword_result["keyword_score"]
        time_score = time_result["score"]
        total_score = int(keyword_score * 0.7 + time_score * 0.3)

        return {
            "total_score": total_score,
            "keyword_analysis": keyword_result,
            "time_analysis": time_result,
            "follow_up": follow_up,
            "should_follow_up": should_follow_up,
            "follow_up_reason": follow_up_reason,
            "interviewer": {
                "name": interviewer.name,
                "type": interviewer.type.value,
                "pressure_level": interviewer.pressure_level,
            },
            "improvement_summary": self._generate_improvement_summary(
                keyword_result, time_result
            ),
        }

    def _generate_improvement_summary(
        self,
        keyword_result: Dict,
        time_result: Dict
    ) -> List[str]:
        """개선점 요약 생성"""
        improvements = []

        # 키워드 관련
        improvements.extend(keyword_result.get("recommendations", [])[:2])

        # 시간 관련
        if time_result["status"] != "optimal":
            improvements.append(time_result["feedback"])

        return improvements[:4]


# 전역 강화 면접 엔진
enhanced_interview_engine = EnhancedInterviewEngine()


# =============================================================================
# 편의 함수
# =============================================================================

def analyze_interview_answer(
    question: str,
    answer: str,
    elapsed_seconds: int,
    airline: str,
    interviewer_type: str = "neutral"
) -> Dict[str, Any]:
    """면접 답변 분석 (단일 함수)"""
    return enhanced_interview_engine.analyze_answer_complete(
        question, answer, elapsed_seconds, airline, interviewer_type
    )


def generate_follow_up_question(
    question: str,
    answer: str,
    airline: str = "",
    interviewer_type: str = "neutral"
) -> Dict[str, Any]:
    """꼬리질문 생성 (단일 함수)"""
    interviewer = get_interviewer_character(interviewer_type)
    return follow_up_generator.generate_follow_up(
        question, answer, interviewer, airline=airline
    )


def get_keyword_feedback(answer: str, question: str, airline: str) -> Dict:
    """키워드 피드백 (단일 함수)"""
    return keyword_analyzer.analyze_keywords(answer, question, airline)


def get_time_feedback(elapsed: int, question: str, answer: str) -> Dict:
    """시간 피드백 (단일 함수)"""
    return time_analyzer.analyze_time(elapsed, question, answer)


# =============================================================================
# 모듈 테스트
# =============================================================================

if __name__ == "__main__":
    print("=== Interview Enhancer Test ===")

    # 1. 면접관 캐릭터 테스트
    print("\n1. Interviewer Characters")
    for itype in InterviewerType:
        char = INTERVIEWER_CHARACTERS[itype]
        print(f"   {char.name} ({itype.value}): 압박 {char.pressure_level}/10")

    # 2. 키워드 분석 테스트
    print("\n2. Keyword Analysis")
    test_answer = "저는 대학교에서 서비스 동아리 활동을 하면서 팀워크의 중요성을 배웠습니다. 팀원들과 소통하며 고객 만족을 위해 노력했고, 그 결과 좋은 성과를 얻었습니다."
    test_question = "팀워크 경험을 말씀해주세요"

    result = keyword_analyzer.analyze_keywords(test_answer, test_question, "대한항공")
    print(f"   Score: {result['keyword_score']}")
    print(f"   STAR Complete: {result['star_structure']['is_complete']}")
    print(f"   Missing: {result['missing_keywords']}")

    # 3. 시간 분석 테스트
    print("\n3. Time Analysis")
    time_result = time_analyzer.analyze_time(75, test_question, test_answer)
    print(f"   Status: {time_result['status']}")
    print(f"   Score: {time_result['score']}")
    print(f"   Feedback: {time_result['feedback']}")

    # 4. 꼬리질문 테스트
    print("\n4. Follow-up Question (Fallback)")
    interviewer = get_interviewer_character("sharp")
    follow_up = follow_up_generator._generate_fallback_follow_up(test_question, test_answer)
    print(f"   Question: {follow_up['follow_up_question']}")

    print("\nModule ready!")
