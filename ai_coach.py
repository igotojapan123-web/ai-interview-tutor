# ai_coach.py
# FlyReady Lab - AI Coaching Engine for Flight Attendant Interview Preparation
# AI 기반 개인 맞춤형 코칭 엔진

import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from logging_config import get_logger
from config import LLM_MODEL_NAME, LLM_API_URL, LLM_TIMEOUT_SEC
from env_config import OPENAI_API_KEY
from score_aggregator import get_statistics, compare_to_passing, PASSING_AVERAGES, SCORE_CATEGORIES

# Logger setup
logger = get_logger(__name__)

# ======================
# Constants and Configuration
# ======================

# Data paths
DATA_DIR = Path(__file__).parent / "data"
USER_SCORES_FILE = Path(__file__).parent / "user_scores.json"
SCORE_AGGREGATE_FILE = DATA_DIR / "score_aggregate.json"

# Score thresholds
WEAKNESS_THRESHOLD = 70  # Below this is considered weak
STRENGTH_THRESHOLD = 85  # Above this is considered strong
IMPROVEMENT_THRESHOLD = 5  # Points improvement needed

# Practice type mappings (Korean)
PRACTICE_TYPES = {
    "자소서": "자기소개서",
    "롤플레잉": "롤플레잉 시나리오",
    "모의면접": "모의 면접",
}

# Skill categories for different practice types
SKILL_CATEGORIES = {
    "자소서": ["structure", "specificity", "airline_fit", "star"],
    "롤플레잉": ["empathy", "solution", "professionalism", "attitude"],
    "모의면접": ["음성점수", "내용점수", "감정점수", "종합점수"],
}

# Korean skill names
SKILL_NAMES_KR = {
    "structure": "답변 구조화",
    "specificity": "구체적 경험 제시",
    "airline_fit": "항공사 적합성",
    "star": "STAR 기법 활용",
    "empathy": "공감 능력",
    "solution": "문제 해결력",
    "professionalism": "전문성",
    "attitude": "서비스 태도",
    "음성점수": "음성 전달력",
    "내용점수": "내용 충실도",
    "감정점수": "감정 표현력",
    "종합점수": "종합 평가",
}

# Airline-specific keywords
AIRLINE_KEYWORDS = {
    "대한항공": ["Excellence in Flight", "글로벌 리더십", "프리미엄 서비스", "한국의 자부심",
                "안전 최우선", "고객 감동", "World's Best Airline", "스카이팀"],
    "아시아나": ["Beautiful People", "따뜻한 서비스", "섬세한 배려", "아름다운 사람들",
                "스타얼라이언스", "진심 어린 서비스", "고객 중심"],
    "제주항공": ["가성비 서비스", "젊은 감각", "합리적 가격", "친근한 서비스",
                "효율적인 운영", "고객 친화적"],
    "진에어": ["JIN으로 날다", "신나는 여행", "자유로운 분위기", "젊고 활기찬",
               "합리적인 서비스", "트렌디"],
    "티웨이": ["함께 나누는 행복", "고객과 함께", "저비용 고효율", "안전한 비행"],
    "에어부산": ["부산 정신", "활기찬 서비스", "지역 항공사의 자부심", "고객 만족"],
    "이스타항공": ["새로운 출발", "도전 정신", "고객 가치", "혁신적 서비스"],
}


# ======================
# Helper Functions
# ======================

def _load_user_scores() -> Dict:
    """Load user scores data from JSON file."""
    try:
        if USER_SCORES_FILE.exists():
            with open(USER_SCORES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"사용자 점수 데이터 로드 오류: {e}")
    return {"scores": [], "detailed_scores": []}


def _load_score_aggregate() -> Dict:
    """Load score aggregate data from JSON file."""
    try:
        if SCORE_AGGREGATE_FILE.exists():
            with open(SCORE_AGGREGATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"점수 통계 데이터 로드 오류: {e}")
    return {"records": [], "last_updated": None}


def _call_llm(prompt: str, system_prompt: str = "") -> Optional[str]:
    """
    Call OpenAI API for LLM responses.

    Args:
        prompt: User prompt
        system_prompt: System prompt for context

    Returns:
        LLM response text or None if failed
    """
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API 키가 설정되지 않았습니다.")
        return None

    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": LLM_MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1500,
        }

        response = requests.post(
            LLM_API_URL,
            headers=headers,
            json=payload,
            timeout=LLM_TIMEOUT_SEC
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"LLM API 오류: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.Timeout:
        logger.error("LLM API 타임아웃")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API 요청 오류: {e}")
        return None
    except Exception as e:
        logger.error(f"LLM 호출 중 예상치 못한 오류: {e}")
        return None


def _get_user_scores_by_id(user_id: str) -> List[Dict]:
    """Get all scores for a specific user."""
    data = _load_user_scores()
    # Note: Current data structure doesn't have user_id, returning all scores
    # In production, filter by user_id
    return data.get("scores", [])


def _get_detailed_scores_by_id(user_id: str) -> List[Dict]:
    """Get detailed scores for a specific user."""
    data = _load_user_scores()
    return data.get("detailed_scores", [])


def _calculate_average_by_type(scores: List[Dict], practice_type: str) -> float:
    """Calculate average score for a specific practice type."""
    type_scores = [s.get("score", 0) for s in scores if s.get("type") == practice_type]
    if not type_scores:
        return 0.0
    return sum(type_scores) / len(type_scores)


def _get_recent_scores(scores: List[Dict], days: int = 7) -> List[Dict]:
    """Get scores from the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for score in scores:
        try:
            score_date = datetime.strptime(score.get("date", ""), "%Y-%m-%d")
            if score_date >= cutoff:
                recent.append(score)
        except ValueError:
            continue
    return recent


# ======================
# 1. Weakness Analysis
# ======================

def analyze_weaknesses(user_id: str) -> Dict[str, Any]:
    """
    사용자의 약점 영역을 분석합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        약점 분석 결과 딕셔너리
        - weak_categories: 낮은 점수의 카테고리 목록
        - skill_deficiencies: 구체적인 스킬 부족 영역
        - improvement_priorities: 개선 우선순위
        - summary: 한국어 요약
    """
    try:
        scores = _get_user_scores_by_id(user_id)
        detailed_scores = _get_detailed_scores_by_id(user_id)

        if not scores:
            return {
                "weak_categories": [],
                "skill_deficiencies": [],
                "improvement_priorities": [],
                "summary": "아직 연습 기록이 없습니다. 연습을 시작해보세요!",
            }

        # Analyze by practice type
        weak_categories = []
        skill_deficiencies = []

        for practice_type in PRACTICE_TYPES.keys():
            avg_score = _calculate_average_by_type(scores, practice_type)
            if avg_score > 0 and avg_score < WEAKNESS_THRESHOLD:
                weak_categories.append({
                    "type": practice_type,
                    "type_kr": PRACTICE_TYPES[practice_type],
                    "average_score": round(avg_score, 1),
                    "gap_to_target": round(WEAKNESS_THRESHOLD - avg_score, 1),
                })

        # Analyze detailed skill scores
        skill_totals: Dict[str, List[float]] = {}

        for detail in detailed_scores:
            if "scores" in detail:
                for skill, score in detail["scores"].items():
                    if skill not in skill_totals:
                        skill_totals[skill] = []
                    skill_totals[skill].append(score)

        for skill, scores_list in skill_totals.items():
            avg = sum(scores_list) / len(scores_list)
            if avg < WEAKNESS_THRESHOLD:
                skill_deficiencies.append({
                    "skill": skill,
                    "skill_kr": SKILL_NAMES_KR.get(skill, skill),
                    "average_score": round(avg, 1),
                    "gap_to_target": round(WEAKNESS_THRESHOLD - avg, 1),
                    "practice_count": len(scores_list),
                })

        # Sort by gap (largest gap = highest priority)
        skill_deficiencies.sort(key=lambda x: x["gap_to_target"], reverse=True)
        weak_categories.sort(key=lambda x: x["gap_to_target"], reverse=True)

        # Create improvement priorities
        improvement_priorities = []
        for i, deficiency in enumerate(skill_deficiencies[:3], 1):
            improvement_priorities.append({
                "priority": i,
                "skill": deficiency["skill_kr"],
                "current_score": deficiency["average_score"],
                "target_score": WEAKNESS_THRESHOLD,
            })

        # Generate summary
        summary_parts = []
        if weak_categories:
            types = [c["type_kr"] for c in weak_categories[:2]]
            summary_parts.append(f"현재 {', '.join(types)} 영역에서 보완이 필요합니다.")

        if skill_deficiencies:
            skills = [s["skill_kr"] for s in skill_deficiencies[:3]]
            summary_parts.append(f"특히 {', '.join(skills)} 역량을 집중적으로 연습하시면 좋겠습니다.")

        if not summary_parts:
            summary_parts.append("전반적으로 양호한 수준입니다. 꾸준히 연습을 이어가세요!")

        return {
            "weak_categories": weak_categories,
            "skill_deficiencies": skill_deficiencies,
            "improvement_priorities": improvement_priorities,
            "summary": " ".join(summary_parts),
        }

    except Exception as e:
        logger.error(f"약점 분석 오류: {e}")
        return {
            "weak_categories": [],
            "skill_deficiencies": [],
            "improvement_priorities": [],
            "summary": "분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        }


# ======================
# 2. Personalized Feedback Generation
# ======================

def generate_coaching_feedback(user_id: str, latest_practice: Dict) -> str:
    """
    최근 연습에 대한 AI 코칭 피드백을 생성합니다.

    Args:
        user_id: 사용자 ID
        latest_practice: 최근 연습 데이터

    Returns:
        개인 맞춤형 코칭 피드백 (한국어)
    """
    try:
        weaknesses = analyze_weaknesses(user_id)

        practice_type = latest_practice.get("type", "연습")
        score = latest_practice.get("score", 0)
        scenario = latest_practice.get("scenario", "")

        system_prompt = """당신은 항공사 승무원 면접 전문 코치입니다.
친절하고 격려하는 톤으로 피드백을 제공하세요.
한국어로 답변하세요.
피드백은 구체적이고 실행 가능한 조언을 포함해야 합니다."""

        prompt = f"""다음 연습 결과에 대한 코칭 피드백을 제공해주세요:

연습 유형: {PRACTICE_TYPES.get(practice_type, practice_type)}
점수: {score}점
시나리오: {scenario}

사용자의 현재 약점 영역:
{weaknesses.get('summary', '정보 없음')}

다음 내용을 포함하여 200자 이내로 피드백을 작성해주세요:
1. 이번 연습에 대한 긍정적인 평가
2. 개선이 필요한 구체적인 부분
3. 다음 연습을 위한 실천 가능한 조언"""

        llm_response = _call_llm(prompt, system_prompt)

        if llm_response:
            return llm_response

        # Fallback response if API is unavailable
        if score >= STRENGTH_THRESHOLD:
            return f"훌륭한 연습이었습니다! {score}점으로 목표에 도달했습니다. 이 페이스를 유지하며 꾸준히 연습해주세요."
        elif score >= WEAKNESS_THRESHOLD:
            return f"좋은 시도였습니다! {score}점을 기록했습니다. 조금 더 구체적인 경험을 덧붙이면 더 좋은 답변이 될 거예요."
        else:
            return f"포기하지 마세요! 현재 {score}점이지만, 연습을 거듭할수록 실력이 향상됩니다. 기본 구조를 먼저 잡아보세요."

    except Exception as e:
        logger.error(f"코칭 피드백 생성 오류: {e}")
        return "피드백을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."


def get_answer_improvement_suggestions(question: str, answer: str, score: int) -> List[str]:
    """
    특정 답변에 대한 개선 제안을 생성합니다.

    Args:
        question: 면접 질문
        answer: 사용자의 답변
        score: 받은 점수

    Returns:
        개선 제안 목록 (한국어)
    """
    try:
        system_prompt = """당신은 항공사 승무원 면접 전문 코치입니다.
답변을 분석하고 구체적인 개선점을 제시해주세요.
한국어로 답변하세요."""

        prompt = f"""다음 면접 답변을 분석하고 개선점을 제시해주세요:

질문: {question}
답변: {answer}
현재 점수: {score}점

다음 기준으로 3가지 개선 제안을 한 문장씩 간결하게 작성해주세요:
1. 내용의 구체성
2. 답변의 구조 (STAR 기법 활용)
3. 항공사 면접에 적합한 표현

형식:
- [제안1]
- [제안2]
- [제안3]"""

        llm_response = _call_llm(prompt, system_prompt)

        if llm_response:
            # Parse response into list
            suggestions = []
            for line in llm_response.split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("*"):
                    suggestions.append(line[1:].strip())
                elif line and len(suggestions) < 3:
                    suggestions.append(line)
            return suggestions[:3] if suggestions else [llm_response]

        # Fallback suggestions
        suggestions = []
        if score < 60:
            suggestions.append("구체적인 경험 사례를 추가하여 답변의 신뢰성을 높여보세요.")
            suggestions.append("STAR 기법(상황-과제-행동-결과)을 활용하여 답변을 구조화해보세요.")
            suggestions.append("승무원의 핵심 역량(서비스 마인드, 팀워크, 위기대응)과 연결지어 답변해보세요.")
        elif score < 80:
            suggestions.append("답변에 구체적인 숫자나 성과를 추가하면 더 설득력이 있습니다.")
            suggestions.append("결론에서 지원 항공사의 가치와 연결짓는 문장을 추가해보세요.")
            suggestions.append("답변 시작과 끝에 자신감 있는 표현을 사용해보세요.")
        else:
            suggestions.append("훌륭한 답변입니다! 전달력을 높이기 위해 발음과 속도 연습도 해보세요.")
            suggestions.append("면접관의 추가 질문에 대비한 심화 답변도 준비해두세요.")
            suggestions.append("같은 경험을 다른 질문에도 응용할 수 있도록 변형 연습을 해보세요.")

        return suggestions

    except Exception as e:
        logger.error(f"답변 개선 제안 생성 오류: {e}")
        return ["개선 제안을 생성하는 중 오류가 발생했습니다."]


def generate_practice_tips(weakness_areas: List[str]) -> Dict[str, str]:
    """
    약점 영역에 대한 연습 팁을 생성합니다.

    Args:
        weakness_areas: 약점 스킬 목록

    Returns:
        스킬별 연습 팁 딕셔너리 (한국어)
    """
    try:
        # Pre-defined tips for each skill area
        tips_database = {
            "structure": {
                "title": "답변 구조화 연습",
                "tip": "답변을 '결론-근거-예시-마무리' 순서로 구성하세요. 먼저 핵심 메시지를 말하고, 이를 뒷받침하는 경험을 덧붙이면 논리적인 답변이 됩니다.",
                "exercise": "1분 타이머를 맞추고 한 가지 주제로 구조화된 답변 연습을 해보세요.",
            },
            "specificity": {
                "title": "구체적 경험 제시 연습",
                "tip": "추상적인 표현 대신 구체적인 숫자, 날짜, 성과를 포함하세요. '많은 경험'보다 '3년간 200명 이상 고객 응대' 같은 표현이 효과적입니다.",
                "exercise": "자신의 경험 3가지를 숫자와 함께 구체적으로 정리해보세요.",
            },
            "airline_fit": {
                "title": "항공사 적합성 연습",
                "tip": "지원 항공사의 슬로건, 최근 뉴스, 서비스 특징을 숙지하고 답변에 자연스럽게 녹여내세요.",
                "exercise": "지원 항공사의 홈페이지와 뉴스를 읽고 키워드 10개를 정리해보세요.",
            },
            "star": {
                "title": "STAR 기법 활용 연습",
                "tip": "상황(Situation)-과제(Task)-행동(Action)-결과(Result) 순서로 경험을 정리하세요. 특히 '행동'과 '결과'를 구체적으로 설명하는 것이 중요합니다.",
                "exercise": "대표 경험 5가지를 STAR 형식으로 미리 정리해두세요.",
            },
            "empathy": {
                "title": "공감 능력 연습",
                "tip": "고객의 감정을 먼저 인정하고 공감하는 표현으로 시작하세요. '불편하셨겠습니다', '걱정되셨을 것 같습니다' 같은 표현이 효과적입니다.",
                "exercise": "다양한 고객 불만 상황에 대한 공감 표현을 10가지 준비해보세요.",
            },
            "solution": {
                "title": "문제 해결력 연습",
                "tip": "문제 상황에서 대안을 제시하고, 불가능한 경우에도 차선책을 안내하는 연습을 하세요. 'A는 어렵지만 B는 가능합니다'처럼 표현하세요.",
                "exercise": "자주 나오는 고객 불만 시나리오 5가지와 해결책을 정리해보세요.",
            },
            "professionalism": {
                "title": "전문성 연습",
                "tip": "정확한 규정과 절차를 알고 전문 용어를 적절히 사용하세요. 단, 고객에게는 쉽게 설명하는 능력도 중요합니다.",
                "exercise": "항공 안전 규정과 서비스 절차를 공부하고 정리해보세요.",
            },
            "attitude": {
                "title": "서비스 태도 연습",
                "tip": "어떤 상황에서도 친절하고 차분한 태도를 유지하세요. 목소리 톤, 표정, 말투 모두 서비스 태도에 포함됩니다.",
                "exercise": "거울을 보며 미소 짓고 인사하는 연습을 매일 5분씩 해보세요.",
            },
        }

        result = {}
        for area in weakness_areas:
            if area in tips_database:
                result[area] = tips_database[area]
            else:
                kr_name = SKILL_NAMES_KR.get(area, area)
                result[area] = {
                    "title": f"{kr_name} 연습",
                    "tip": f"{kr_name} 역량을 향상시키기 위해 관련 연습을 꾸준히 해주세요.",
                    "exercise": "관련 영상이나 자료를 참고하여 매일 연습해보세요.",
                }

        return result

    except Exception as e:
        logger.error(f"연습 팁 생성 오류: {e}")
        return {}


# ======================
# 3. Answer Correction/Enhancement
# ======================

def enhance_answer(original_answer: str, question: str, airline: str) -> str:
    """
    LLM을 사용하여 사용자의 답변을 개선합니다.

    Args:
        original_answer: 원본 답변
        question: 면접 질문
        airline: 지원 항공사

    Returns:
        개선된 답변 (한국어)
    """
    try:
        keywords = AIRLINE_KEYWORDS.get(airline, ["안전", "서비스", "고객 만족"])

        system_prompt = f"""당신은 {airline} 승무원 면접 전문 코치입니다.
지원자의 답변을 개선하되, 원래 의미와 경험은 유지하세요.
{airline}의 핵심 가치와 키워드를 자연스럽게 포함하세요.
한국어로 답변하세요."""

        prompt = f"""다음 면접 답변을 개선해주세요:

질문: {question}
원본 답변: {original_answer}

지원 항공사: {airline}
관련 키워드: {', '.join(keywords[:5])}

다음 사항을 고려하여 개선된 답변을 작성해주세요:
1. STAR 기법을 활용한 구조화
2. 구체적인 경험과 성과 강조
3. {airline}의 가치와 연결
4. 자연스럽고 진정성 있는 표현

개선된 답변:"""

        llm_response = _call_llm(prompt, system_prompt)

        if llm_response:
            return llm_response

        # Fallback: Return original with basic enhancement suggestion
        return f"{original_answer}\n\n[코칭 제안: STAR 기법(상황-과제-행동-결과)을 활용하여 답변을 구조화하고, {airline}의 핵심 가치인 '{keywords[0]}'를 자연스럽게 언급해보세요.]"

    except Exception as e:
        logger.error(f"답변 개선 오류: {e}")
        return original_answer


def get_star_structured_answer(question: str, answer: str) -> Dict[str, str]:
    """
    답변을 STAR 기법으로 재구성합니다.

    Args:
        question: 면접 질문
        answer: 사용자의 답변

    Returns:
        STAR 구조로 분리된 답변 딕셔너리
    """
    try:
        system_prompt = """당신은 면접 답변 구조화 전문가입니다.
주어진 답변을 STAR 기법으로 재구성해주세요.
한국어로 답변하세요."""

        prompt = f"""다음 답변을 STAR 기법으로 재구성해주세요:

질문: {question}
답변: {answer}

다음 형식으로 작성해주세요:
[상황(Situation)]: 언제, 어디서, 어떤 상황이었는지
[과제(Task)]: 무엇을 해결해야 했는지, 목표가 무엇이었는지
[행동(Action)]: 구체적으로 어떤 행동을 취했는지
[결과(Result)]: 어떤 성과나 결과를 얻었는지, 배운 점은 무엇인지"""

        llm_response = _call_llm(prompt, system_prompt)

        if llm_response:
            # Parse STAR components
            star_dict = {
                "situation": "",
                "task": "",
                "action": "",
                "result": "",
                "full_answer": llm_response,
            }

            lines = llm_response.split("\n")
            current_key = None

            for line in lines:
                line_lower = line.lower()
                if "[상황" in line or "situation" in line_lower:
                    current_key = "situation"
                    star_dict[current_key] = line.split(":")[-1].strip() if ":" in line else ""
                elif "[과제" in line or "task" in line_lower:
                    current_key = "task"
                    star_dict[current_key] = line.split(":")[-1].strip() if ":" in line else ""
                elif "[행동" in line or "action" in line_lower:
                    current_key = "action"
                    star_dict[current_key] = line.split(":")[-1].strip() if ":" in line else ""
                elif "[결과" in line or "result" in line_lower:
                    current_key = "result"
                    star_dict[current_key] = line.split(":")[-1].strip() if ":" in line else ""
                elif current_key and line.strip():
                    star_dict[current_key] += " " + line.strip()

            return star_dict

        # Fallback structure
        return {
            "situation": "해당 답변에서 상황을 추출하기 어렵습니다. 구체적인 시간, 장소, 상황을 추가해보세요.",
            "task": "해결해야 할 과제나 목표를 명확히 설명해주세요.",
            "action": "본인이 취한 구체적인 행동을 설명해주세요.",
            "result": "행동의 결과와 배운 점을 추가해주세요.",
            "full_answer": answer,
        }

    except Exception as e:
        logger.error(f"STAR 구조화 오류: {e}")
        return {
            "situation": "",
            "task": "",
            "action": "",
            "result": "",
            "full_answer": answer,
            "error": "구조화 중 오류가 발생했습니다.",
        }


def get_keyword_suggestions(question: str, airline: str) -> List[Dict[str, str]]:
    """
    답변에 포함할 키워드를 제안합니다.

    Args:
        question: 면접 질문
        airline: 지원 항공사

    Returns:
        추천 키워드 목록 (키워드, 사용 예시 포함)
    """
    try:
        airline_kw = AIRLINE_KEYWORDS.get(airline, [])

        # Common flight attendant interview keywords
        common_keywords = [
            {"keyword": "안전", "example": "'승객의 안전을 최우선으로 생각하며...'"},
            {"keyword": "서비스 마인드", "example": "'진심 어린 서비스로 고객에게 감동을...'"},
            {"keyword": "팀워크", "example": "'동료들과의 협력을 통해 시너지를...'"},
            {"keyword": "위기 대응", "example": "'예상치 못한 상황에서도 침착하게...'"},
            {"keyword": "글로벌 역량", "example": "'다양한 문화에 대한 이해를 바탕으로...'"},
        ]

        # Add airline-specific keywords
        suggestions = []
        for kw in airline_kw[:3]:
            suggestions.append({
                "keyword": kw,
                "example": f"'{airline}의 \"{kw}\" 가치에 공감하며...'",
                "type": "airline_specific",
            })

        # Add relevant common keywords
        for item in common_keywords[:3]:
            suggestions.append({
                "keyword": item["keyword"],
                "example": item["example"],
                "type": "common",
            })

        return suggestions

    except Exception as e:
        logger.error(f"키워드 제안 오류: {e}")
        return []


# ======================
# 4. Real-time Coaching Prompts
# ======================

def get_pre_interview_tips(airline: str) -> Dict[str, Any]:
    """
    면접 시작 전 팁을 제공합니다.

    Args:
        airline: 지원 항공사

    Returns:
        면접 전 팁 딕셔너리 (한국어)
    """
    try:
        keywords = AIRLINE_KEYWORDS.get(airline, ["서비스", "안전", "고객 만족"])

        # Get passing averages for the airline
        passing = PASSING_AVERAGES.get(airline, PASSING_AVERAGES.get("제주항공", {}))

        tips = {
            "greeting": f"{airline} 면접 연습을 시작합니다!",
            "encouragement": "긴장하지 말고 자신감 있게 답변해주세요. 당신의 진정성이 가장 중요합니다.",
            "airline_focus": f"{airline}의 핵심 가치인 '{keywords[0]}'을(를) 기억하며 답변해보세요.",
            "target_score": f"목표 점수는 {passing.get('종합점수', 75)}점 이상입니다.",
            "quick_tips": [
                "답변은 1-2분 내로 간결하게",
                "STAR 기법으로 구조화하기",
                "밝은 표정과 자신감 있는 목소리",
                "질문의 의도를 파악하고 답변하기",
            ],
            "keywords_to_remember": keywords[:5],
            "deep_breath": "시작 전 깊게 숨을 쉬고, 미소를 지어보세요.",
        }

        return tips

    except Exception as e:
        logger.error(f"면접 전 팁 생성 오류: {e}")
        return {
            "greeting": "면접 연습을 시작합니다!",
            "encouragement": "자신감을 가지고 최선을 다해보세요.",
        }


def get_mid_interview_encouragement(current_score: float, question_num: int) -> str:
    """
    면접 중간에 격려 메시지를 제공합니다.

    Args:
        current_score: 현재까지의 평균 점수
        question_num: 현재 문항 번호

    Returns:
        격려 메시지 (한국어)
    """
    try:
        if current_score >= 85:
            messages = [
                "정말 훌륭해요! 이 페이스를 유지해주세요.",
                "지금까지 아주 잘하고 있어요. 자신감을 가지세요!",
                "면접관에게 좋은 인상을 주고 있어요. 계속 이어가세요!",
            ]
        elif current_score >= 70:
            messages = [
                "잘하고 있어요! 조금만 더 구체적으로 답변해보세요.",
                "좋은 흐름이에요. 다음 질문에서 더 빛나보세요!",
                "포인트를 잘 짚고 있어요. 경험담을 더해보면 좋겠어요.",
            ]
        elif current_score >= 50:
            messages = [
                "괜찮아요! 다음 질문이 기회예요. 집중해보세요.",
                "조금 더 자신감 있게 답변해보세요. 할 수 있어요!",
                "STAR 기법을 떠올리며 구조적으로 답변해보세요.",
            ]
        else:
            messages = [
                "포기하지 마세요! 지금부터 달라질 수 있어요.",
                "심호흡하고, 다음 질문에 집중해보세요.",
                "긴장을 풀고, 본인의 경험을 솔직하게 이야기해보세요.",
            ]

        # Add question-specific encouragement
        import random
        base_message = random.choice(messages)

        if question_num <= 2:
            base_message += " 아직 시작이니 부담 갖지 마세요."
        elif question_num >= 5:
            base_message += " 거의 다 왔어요! 마지막까지 최선을 다해주세요."

        return base_message

    except Exception as e:
        logger.error(f"격려 메시지 생성 오류: {e}")
        return "잘하고 있어요! 계속 이어가세요."


def get_post_answer_quick_feedback(answer: str, question: str) -> Dict[str, Any]:
    """
    답변 직후 빠른 피드백을 제공합니다.

    Args:
        answer: 사용자의 답변
        question: 면접 질문

    Returns:
        빠른 피드백 딕셔너리 (한국어)
    """
    try:
        # Quick analysis without LLM for speed
        feedback = {
            "length_feedback": "",
            "structure_hint": "",
            "positive_point": "",
            "improvement_hint": "",
        }

        # Length analysis
        answer_length = len(answer)
        if answer_length < 100:
            feedback["length_feedback"] = "답변이 조금 짧아요. 구체적인 경험을 더 추가해보세요."
        elif answer_length > 500:
            feedback["length_feedback"] = "답변이 길어요. 핵심 포인트 위주로 간결하게 정리해보세요."
        else:
            feedback["length_feedback"] = "적절한 길이의 답변이에요."

        # Structure hints
        star_keywords = ["상황", "과제", "행동", "결과", "그래서", "했습니다", "배웠습니다"]
        has_structure = sum(1 for kw in star_keywords if kw in answer)

        if has_structure >= 3:
            feedback["structure_hint"] = "구조적으로 잘 정리된 답변이에요."
        else:
            feedback["structure_hint"] = "STAR 기법을 활용하면 더 체계적인 답변이 됩니다."

        # Positive points
        positive_keywords = ["열정", "노력", "성장", "배움", "협력", "서비스", "고객"]
        found_positives = [kw for kw in positive_keywords if kw in answer]
        if found_positives:
            feedback["positive_point"] = f"'{found_positives[0]}' 같은 긍정적인 키워드가 좋아요!"
        else:
            feedback["positive_point"] = "긍정적인 자세가 느껴지는 답변이에요."

        # Improvement hints
        if "왜냐하면" not in answer and "때문에" not in answer:
            feedback["improvement_hint"] = "이유나 근거를 덧붙이면 설득력이 높아져요."
        elif "결과" not in answer and "성과" not in answer:
            feedback["improvement_hint"] = "구체적인 결과나 성과를 추가해보세요."
        else:
            feedback["improvement_hint"] = "좋은 구성이에요. 전달력을 높이는 연습을 해보세요."

        return feedback

    except Exception as e:
        logger.error(f"빠른 피드백 생성 오류: {e}")
        return {
            "length_feedback": "답변 분석 중 오류가 발생했습니다.",
            "structure_hint": "",
            "positive_point": "",
            "improvement_hint": "",
        }


# ======================
# 5. Daily/Weekly Coaching Summary
# ======================

def get_daily_coaching_summary(user_id: str) -> Dict[str, Any]:
    """
    일일 코칭 요약을 생성합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        일일 요약 딕셔너리 (한국어)
    """
    try:
        scores = _get_user_scores_by_id(user_id)
        today = datetime.now().strftime("%Y-%m-%d")

        # Get today's scores
        today_scores = [s for s in scores if s.get("date") == today]

        if not today_scores:
            return {
                "date": today,
                "practice_count": 0,
                "message": "오늘은 아직 연습 기록이 없어요. 지금 바로 시작해볼까요?",
                "average_score": 0,
                "best_score": 0,
                "improvement": None,
                "recommendation": "가벼운 자기소개 연습부터 시작해보세요!",
            }

        practice_count = len(today_scores)
        scores_only = [s.get("score", 0) for s in today_scores]
        average_score = sum(scores_only) / len(scores_only)
        best_score = max(scores_only)

        # Compare with yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_scores = [s.get("score", 0) for s in scores if s.get("date") == yesterday]

        improvement = None
        if yesterday_scores:
            yesterday_avg = sum(yesterday_scores) / len(yesterday_scores)
            improvement = round(average_score - yesterday_avg, 1)

        # Generate message
        if average_score >= 85:
            message = f"훌륭한 하루였어요! {practice_count}회 연습으로 평균 {average_score:.0f}점을 달성했습니다."
        elif average_score >= 70:
            message = f"좋은 연습이었어요! {practice_count}회 연습, 평균 {average_score:.0f}점입니다."
        else:
            message = f"오늘 {practice_count}회 연습했어요. 꾸준함이 실력을 만듭니다!"

        if improvement and improvement > 0:
            message += f" 어제보다 {improvement}점 향상됐어요!"

        # Get weaknesses for recommendation
        weaknesses = analyze_weaknesses(user_id)
        recommendation = ""
        if weaknesses.get("improvement_priorities"):
            top_priority = weaknesses["improvement_priorities"][0]
            recommendation = f"오늘의 집중 영역: {top_priority['skill']} (현재 {top_priority['current_score']}점 -> 목표 {top_priority['target_score']}점)"
        else:
            recommendation = "전반적으로 잘하고 있어요! 다양한 유형의 질문을 연습해보세요."

        return {
            "date": today,
            "practice_count": practice_count,
            "message": message,
            "average_score": round(average_score, 1),
            "best_score": best_score,
            "improvement": improvement,
            "recommendation": recommendation,
            "practice_types": list(set(s.get("type", "") for s in today_scores)),
        }

    except Exception as e:
        logger.error(f"일일 요약 생성 오류: {e}")
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "practice_count": 0,
            "message": "요약을 생성하는 중 오류가 발생했습니다.",
            "error": str(e),
        }


def get_weekly_coaching_report(user_id: str) -> Dict[str, Any]:
    """
    주간 코칭 리포트를 생성합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        주간 리포트 딕셔너리 (한국어)
    """
    try:
        scores = _get_user_scores_by_id(user_id)
        detailed_scores = _get_detailed_scores_by_id(user_id)

        # Get this week's scores
        week_scores = _get_recent_scores(scores, days=7)

        if not week_scores:
            return {
                "period": "이번 주",
                "total_practices": 0,
                "message": "이번 주는 연습 기록이 없어요. 다음 주에는 매일 조금씩 연습해보세요!",
                "daily_goal": "하루 3회 연습을 목표로 해보세요.",
            }

        # Calculate statistics
        total_practices = len(week_scores)
        all_scores = [s.get("score", 0) for s in week_scores]
        average_score = sum(all_scores) / len(all_scores)
        best_score = max(all_scores)
        worst_score = min(all_scores)

        # Practice frequency by type
        type_counts = {}
        type_scores = {}
        for s in week_scores:
            ptype = s.get("type", "기타")
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
            if ptype not in type_scores:
                type_scores[ptype] = []
            type_scores[ptype].append(s.get("score", 0))

        # Calculate score trend
        if len(all_scores) >= 3:
            first_half = all_scores[:len(all_scores)//2]
            second_half = all_scores[len(all_scores)//2:]
            trend = sum(second_half)/len(second_half) - sum(first_half)/len(first_half)
        else:
            trend = 0

        # Get weaknesses
        weaknesses = analyze_weaknesses(user_id)

        # Generate recommendations
        recommendations = []

        if average_score < 70:
            recommendations.append("기본기를 다지는 연습에 집중하세요. STAR 기법부터 시작해보세요.")
        elif average_score < 85:
            recommendations.append("좋은 실력이에요! 이제 디테일을 다듬어 합격선을 넘어보세요.")
        else:
            recommendations.append("훌륭해요! 다양한 상황에 대비한 응용 연습을 해보세요.")

        if weaknesses.get("skill_deficiencies"):
            weak_skill = weaknesses["skill_deficiencies"][0]
            recommendations.append(f"{weak_skill['skill_kr']} 역량 향상에 집중하면 큰 도움이 됩니다.")

        if "롤플레잉" not in type_counts:
            recommendations.append("롤플레잉 연습도 추가해보세요. 실전 감각을 키울 수 있어요.")

        # Compare to last week
        last_week_scores = _get_recent_scores(scores, days=14)
        last_week_only = [s for s in last_week_scores if s not in week_scores]

        week_improvement = None
        if last_week_only:
            last_week_avg = sum(s.get("score", 0) for s in last_week_only) / len(last_week_only)
            week_improvement = round(average_score - last_week_avg, 1)

        # Generate summary message
        if trend > 5:
            trend_message = "점수가 꾸준히 상승하고 있어요!"
        elif trend > 0:
            trend_message = "조금씩 발전하고 있어요."
        elif trend > -5:
            trend_message = "실력을 유지하고 있어요."
        else:
            trend_message = "최근 점수가 하락 추세예요. 기본기를 점검해보세요."

        return {
            "period": "이번 주",
            "total_practices": total_practices,
            "average_score": round(average_score, 1),
            "best_score": best_score,
            "worst_score": worst_score,
            "trend": round(trend, 1),
            "trend_message": trend_message,
            "practice_by_type": type_counts,
            "score_by_type": {k: round(sum(v)/len(v), 1) for k, v in type_scores.items()},
            "week_improvement": week_improvement,
            "recommendations": recommendations,
            "weaknesses_summary": weaknesses.get("summary", ""),
            "focus_areas": [p["skill"] for p in weaknesses.get("improvement_priorities", [])[:3]],
        }

    except Exception as e:
        logger.error(f"주간 리포트 생성 오류: {e}")
        return {
            "period": "이번 주",
            "total_practices": 0,
            "message": "리포트를 생성하는 중 오류가 발생했습니다.",
            "error": str(e),
        }


def get_focus_areas_for_today(user_id: str) -> Dict[str, Any]:
    """
    오늘 집중해야 할 영역을 추천합니다.

    Args:
        user_id: 사용자 ID

    Returns:
        오늘의 집중 영역 딕셔너리 (한국어)
    """
    try:
        weaknesses = analyze_weaknesses(user_id)
        scores = _get_user_scores_by_id(user_id)
        recent = _get_recent_scores(scores, days=3)

        focus_areas = []
        practice_suggestions = []

        # Primary focus: weakest area
        if weaknesses.get("improvement_priorities"):
            top_priority = weaknesses["improvement_priorities"][0]
            focus_areas.append({
                "area": top_priority["skill"],
                "reason": f"현재 {top_priority['current_score']}점으로 개선이 가장 필요한 영역입니다.",
                "priority": 1,
            })

        # Check what hasn't been practiced recently
        recent_types = set(s.get("type", "") for s in recent)
        all_types = set(PRACTICE_TYPES.keys())
        missing_types = all_types - recent_types

        if missing_types:
            for ptype in list(missing_types)[:1]:
                focus_areas.append({
                    "area": PRACTICE_TYPES.get(ptype, ptype),
                    "reason": "최근 이 유형의 연습을 하지 않았어요.",
                    "priority": 2,
                })

        # Generate practice suggestions
        if not recent:
            practice_suggestions = [
                "오늘의 첫 연습으로 자기소개를 준비해보세요.",
                "STAR 기법을 활용한 경험 정리를 해보세요.",
                "거울을 보며 표정과 자세 연습을 해보세요.",
            ]
        else:
            # Based on recent performance
            recent_avg = sum(s.get("score", 0) for s in recent) / len(recent)

            if recent_avg < 60:
                practice_suggestions = [
                    "기본 질문에 대한 답변 스크립트를 작성해보세요.",
                    "경험담 3가지를 STAR 형식으로 정리해보세요.",
                    "천천히 또박또박 말하는 연습을 해보세요.",
                ]
            elif recent_avg < 80:
                practice_suggestions = [
                    "답변에 구체적인 숫자와 성과를 추가해보세요.",
                    "타이머를 맞추고 1분 30초 내 답변 연습을 해보세요.",
                    "지원 항공사의 최근 뉴스를 확인하고 키워드를 정리해보세요.",
                ]
            else:
                practice_suggestions = [
                    "압박 면접 상황을 가정하고 연습해보세요.",
                    "다양한 질문에 같은 경험을 응용하는 연습을 해보세요.",
                    "영어 자기소개도 준비해보세요.",
                ]

        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "greeting": "오늘도 화이팅! 면접 합격을 향해 한 걸음 더 나아가요.",
            "focus_areas": focus_areas,
            "practice_suggestions": practice_suggestions,
            "daily_goal": "오늘 목표: 3회 이상 연습하기",
            "motivation": "작은 노력이 쌓여 큰 결과를 만듭니다. 오늘도 최선을 다해봐요!",
        }

    except Exception as e:
        logger.error(f"오늘의 집중 영역 생성 오류: {e}")
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "greeting": "오늘도 화이팅!",
            "focus_areas": [],
            "practice_suggestions": ["자유롭게 연습을 시작해보세요!"],
            "error": str(e),
        }


# ======================
# Module Initialization
# ======================

def initialize() -> bool:
    """
    AI 코칭 모듈을 초기화합니다.

    Returns:
        초기화 성공 여부
    """
    try:
        # Ensure data directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Check API configuration
        if OPENAI_API_KEY:
            logger.info("AI 코칭 모듈 초기화 완료 (LLM 활성화)")
        else:
            logger.warning("AI 코칭 모듈 초기화 완료 (LLM 비활성화 - API 키 없음)")

        return True

    except Exception as e:
        logger.error(f"AI 코칭 모듈 초기화 오류: {e}")
        return False


# Initialize on import
initialize()
