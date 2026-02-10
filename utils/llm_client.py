# llm_client.py
# OpenAI API 클라이언트 (ai_tutor와 동일한 방식)

import json
import time
import requests
from typing import Optional, Dict, Any, List
import streamlit as st

from utils.env_config import get_api_key, check_openai_key, mask_api_key
from utils.prompt_templates import (
    MOCK_INTERVIEW_SYSTEM,
    RESUME_REVIEW_SYSTEM,
    CHATBOT_SYSTEM,
    NEWS_ANALYSIS_SYSTEM,
    SYSTEM_PROMPT_KOREAN_AIR_2026,
    REWRITE_SYSTEM_PROMPT,
    check_forbidden_patterns,
    calculate_realtime_score,
    build_user_prompt,
    build_rewrite_prompt,
    score_by_code
)

# 타임아웃 설정
API_TIMEOUTS = {
    "openai_chat": 90,
    "openai_vision": 120,
    "default": 60,
}

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2


def show_api_key_error():
    """API 키 오류 메시지 표시"""
    is_valid, message = check_openai_key()
    if not is_valid:
        st.error(f"API 키 오류: {message}")
        st.info("Streamlit Cloud의 Secrets에 `OPENAI_API_KEY`를 추가하세요.")
        return False
    return True


def safe_parse_openai_response(response: requests.Response) -> Optional[Dict[str, Any]]:
    """OpenAI API 응답 안전하게 파싱"""
    try:
        if response.status_code != 200:
            error_msg = f"API 오류 (HTTP {response.status_code})"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_detail = error_data['error'].get('message', '')
                    error_msg += f": {error_detail}"
            except json.JSONDecodeError:
                pass
            st.error(error_msg)
            return None

        data = response.json()
        choices = data.get("choices")
        if not choices or len(choices) == 0:
            st.error("API 응답에 choices가 없습니다.")
            return None

        first_choice = choices[0]
        message = first_choice.get("message")
        if not isinstance(message, dict):
            st.error("API 응답 형식이 올바르지 않습니다.")
            return None

        content = message.get("content", "")
        if not content:
            st.warning("API가 빈 응답을 반환했습니다.")
            return None

        return {
            "content": content,
            "raw": data
        }

    except json.JSONDecodeError as e:
        st.error(f"API 응답 JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        st.error(f"API 응답 처리 중 오류: {e}")
        return None


def call_openai_chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    timeout: int = None,
    json_mode: bool = False,
    max_retries: int = MAX_RETRIES
) -> Optional[Dict[str, Any]]:
    """
    OpenAI Chat API 호출 (재시도 로직 포함)

    Args:
        messages: 메시지 리스트 [{"role": "...", "content": "..."}]
        model: 사용할 모델 (기본: gpt-4o-mini)
        timeout: 타임아웃 (초)
        json_mode: JSON 모드 사용 여부
        max_retries: 최대 재시도 횟수

    Returns:
        성공 시: {"content": str, "raw": dict}
        실패 시: None
    """
    api_key = get_api_key()
    if not api_key:
        show_api_key_error()
        return None

    if timeout is None:
        timeout = API_TIMEOUTS["openai_chat"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )

            result = safe_parse_openai_response(response)
            if result:
                return result

            if response.status_code in [429, 500, 502, 503, 504]:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            else:
                return None

        except requests.Timeout:
            last_error = "시간 초과"
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            st.error(f"API 요청 시간 초과 ({timeout}초)")
            return None

        except requests.ConnectionError:
            last_error = "연결 오류"
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            st.error("인터넷 연결을 확인해주세요.")
            return None

        except Exception as e:
            st.error(f"API 호출 오류: {e}")
            return None

    return None


def call_gpt(
    prompt: str,
    system: str = None,
    model: str = "gpt-4o-mini",
    temperature: float = 0.3
) -> str:
    """
    간단한 GPT 호출 래퍼

    Args:
        prompt: 사용자 프롬프트
        system: 시스템 프롬프트
        model: 모델 (기본: gpt-4o-mini)
        temperature: 온도 (낮을수록 일관된 응답)

    Returns:
        GPT 응답 텍스트
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    result = call_openai_chat(messages, model=model)
    if result:
        content = result["content"]

        # 금지 패턴 검사
        forbidden = check_forbidden_patterns(content)
        if forbidden:
            content += "\n\n[주의] 이 응답에는 검증이 필요한 표현이 포함되어 있을 수 있습니다."

        return content

    return "[오류] API 호출에 실패했습니다. 잠시 후 다시 시도해주세요."


def get_interview_feedback(question: str, answer: str) -> str:
    """모의면접 피드백 요청"""
    prompt = f"""
질문: {question}

지원자 답변:
{answer}

위 답변에 대해 상세한 피드백을 제공해주세요.
"""
    return call_gpt(prompt, system=MOCK_INTERVIEW_SYSTEM)


def get_resume_feedback(essay_prompt: str, content: str, char_limit: int = 600) -> str:
    """자소서 첨삭 요청 (기존 호환용)"""
    prompt = f"""
자소서 문항: {essay_prompt}
글자수 제한: {char_limit}자
현재 글자수: {len(content)}자

자소서 내용:
---
{content}
---

위 자소서를 첨삭해주세요.
"""
    return call_gpt(prompt, system=RESUME_REVIEW_SYSTEM)


# ═══════════════════════════════════════
# 하이브리드 채점 v3.0 - AI 정성 채점 (40점)
# ═══════════════════════════════════════

AI_SCORING_PROMPT = """당신은 대한항공 객실승무원 채용 자소서 채점관입니다.

[채점 원칙]
1. 절대 후하게 주지 마세요. 학원식 자소서는 5점 이하입니다.
2. 각 항목을 독립적으로 채점하세요. 하나가 좋다고 다른 것도 올리지 마세요.
3. 반드시 JSON 형식으로만 응답하세요.

[채점 기준]

## 설득력 (15점)
- 0~3점: 선언만 있고 증거 없음 ("저는 성실합니다")
- 4~6점: 경험은 있지만 피상적 ("팀 프로젝트를 했습니다")
- 7~9점: 구체적 경험이 있지만 직무 연결 부족
- 10~12점: 경험+성과+직무 연결이 있음
- 13~15점: 강렬한 장면+구체적 성과+자연스러운 직무 연결 (상위 5%)

## 차별성 (15점)
- 0~3점: 누구나 쓸 수 있는 내용 (카페 아르바이트, 봉사활동)
- 4~6점: 소재는 평범하지만 시각이 약간 다름
- 7~9점: 독특한 시각이나 해석이 있음
- 10~12점: 면접관이 "이건 기억에 남겠다" 싶은 수준
- 13~15점: 소재+시각+표현 모두 독창적 (상위 3%)

## 직무 연결 (10점)
- 0~2점: 승무원 직무와 연결 없음
- 3~4점: "승무원이 되겠다" 선언만
- 5~6점: 경험을 승무원 직무에 연결하려 했으나 억지스러움
- 7~8점: 자연스러운 직무 연결
- 9~10점: 읽는 면접관이 "이 사람이 기내에서 일하는 모습이 그려진다"

[금지]
- 10점 이상 주려면 반드시 구체적 근거를 제시하세요.
- "잘 쓴 편" 같은 애매한 표현 금지. 점수에 맞는 근거만.

[응답 형식 — 반드시 JSON만]
{"persuasion": {"score": 0, "reason": "..."}, "uniqueness": {"score": 0, "reason": "..."}, "job_relevance": {"score": 0, "reason": "..."}}
"""

QUESTION_CONTEXTS = {
    1: "대한항공의 객실승무원이 되고 싶은 이유와 본인이 객실승무원 직무에 적합하다고 생각하는 이유를 구체적으로 서술하시오.",
    2: "객실승무원에게 필요한 역량 한 가지를 제시하고, 그 이유를 안전과 서비스 부문으로 나누어 서술하시오.",
    3: "본인이 선호하지 않거나 부담을 느끼는 과제를 맡게 되었을 때, 이를 어떻게 받아들이고 수행하였는지 구체적인 경험을 바탕으로 서술하시오."
}


def score_by_ai(text: str, question_num: int) -> dict:
    """
    AI 정성 채점 (40점 만점)
    JSON 강제 출력 + temperature=0.1로 일관성 확보
    """
    import json

    api_key = get_api_key()
    if not api_key:
        return {
            "total": 0,
            "persuasion": {"score": 0, "max": 15, "reason": "API 키 없음"},
            "uniqueness": {"score": 0, "max": 15, "reason": "API 키 없음"},
            "job_relevance": {"score": 0, "max": 10, "reason": "API 키 없음"},
            "error": "API 키가 설정되지 않았습니다."
        }

    user_prompt = f"""[문항 {question_num}번]
{QUESTION_CONTEXTS.get(question_num, "")}

[자소서]
{text}

위 자소서를 채점해주세요. 반드시 JSON만 출력하세요."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": AI_SCORING_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,  # 최대한 일관되게
        "response_format": {"type": "json_object"},  # JSON 강제
        "max_tokens": 500,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            return {
                "total": 0,
                "persuasion": {"score": 0, "max": 15, "reason": f"API 오류: {response.status_code}"},
                "uniqueness": {"score": 0, "max": 15, "reason": ""},
                "job_relevance": {"score": 0, "max": 10, "reason": ""},
                "error": f"API 오류 (HTTP {response.status_code})"
            }

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)

        # 점수 범위 강제 (AI가 범위 넘기는 거 방지)
        persuasion = max(0, min(15, result.get("persuasion", {}).get("score", 0)))
        uniqueness = max(0, min(15, result.get("uniqueness", {}).get("score", 0)))
        job_relevance = max(0, min(10, result.get("job_relevance", {}).get("score", 0)))

        return {
            "total": persuasion + uniqueness + job_relevance,
            "persuasion": {
                "score": persuasion,
                "max": 15,
                "reason": result.get("persuasion", {}).get("reason", "")
            },
            "uniqueness": {
                "score": uniqueness,
                "max": 15,
                "reason": result.get("uniqueness", {}).get("reason", "")
            },
            "job_relevance": {
                "score": job_relevance,
                "max": 10,
                "reason": result.get("job_relevance", {}).get("reason", "")
            }
        }

    except json.JSONDecodeError as e:
        return {
            "total": 0,
            "persuasion": {"score": 0, "max": 15, "reason": "JSON 파싱 실패"},
            "uniqueness": {"score": 0, "max": 15, "reason": ""},
            "job_relevance": {"score": 0, "max": 10, "reason": ""},
            "error": f"JSON 파싱 오류: {e}"
        }
    except Exception as e:
        return {
            "total": 0,
            "persuasion": {"score": 0, "max": 15, "reason": str(e)},
            "uniqueness": {"score": 0, "max": 15, "reason": ""},
            "job_relevance": {"score": 0, "max": 10, "reason": ""},
            "error": str(e)
        }


def get_grade(score: int) -> str:
    """점수에 따른 등급 반환"""
    if score >= 90:
        return "S (제출 추천)"
    elif score >= 80:
        return "A (제출 가능)"
    elif score >= 70:
        return "B (수정 후 제출)"
    elif score >= 60:
        return "C (상당한 수정 필요)"
    elif score >= 50:
        return "D (구조부터 재작성)"
    else:
        return "F (전면 재작성)"


def score_resume_hybrid(text: str, question_num: int) -> dict:
    """
    하이브리드 채점 v3.0
    최종 채점 = 코드(60점) + AI(40점) = 100점
    """
    # STEP 1: 코드 채점 (항상 동일)
    code_result = score_by_code(text, question_num)

    # STEP 2: AI 채점 (JSON 강제, temp=0.1)
    ai_result = score_by_ai(text, question_num)

    # STEP 3: 합산
    total = code_result["total"] + ai_result["total"]

    return {
        "total_score": total,
        "grade": get_grade(total),
        "code_score": code_result,   # 60점 (매번 동일)
        "ai_score": ai_result,       # 40점 (±3점 오차)
        "breakdown": {
            "구조": f'{code_result["structure"]["score"]}/{code_result["structure"]["max"]}',
            "내용": f'{code_result["content"]["score"]}/{code_result["content"]["max"]}',
            "표현": f'{code_result["expression"]["score"]}/{code_result["expression"]["max"]}',
            "설득력": f'{ai_result["persuasion"]["score"]}/{ai_result["persuasion"]["max"]}',
            "차별성": f'{ai_result["uniqueness"]["score"]}/{ai_result["uniqueness"]["max"]}',
            "직무연결": f'{ai_result["job_relevance"]["score"]}/{ai_result["job_relevance"]["max"]}',
        }
    }


# ═══════════════════════════════════════
# 하이브리드 채점 v3.0 - 피드백 생성 (점수 참고, 설명만)
# ═══════════════════════════════════════

FEEDBACK_PROMPT = """당신은 대한항공 자소서 전문 첨삭가입니다.

아래에 자소서와 이미 계산된 채점 결과가 있습니다.
점수를 다시 매기지 마세요. 점수는 이미 확정되었습니다.

당신의 역할:
1. 채점 결과를 바탕으로 구체적인 개선점을 설명하세요.
2. 가장 시급한 문제 3가지를 우선순위로 제시하세요.
3. 심리학/행동경제학 관점에서 1가지 전략을 제안하세요.

[규칙]
- 점수를 언급할 때는 이미 계산된 점수를 그대로 인용하세요.
- "~하면 좋겠습니다" 대신 "~로 바꾸세요"처럼 구체적으로.
- 칭찬은 1줄 이내. 나머지는 전부 개선점."""


def generate_feedback_stream(text: str, question_num: int, scoring_result: dict):
    """
    점수는 이미 확정됨. AI는 설명만 생성. (스트리밍)
    """
    api_key = get_api_key()
    if not api_key:
        yield "[오류] API 키가 설정되지 않았습니다."
        return

    user_prompt = f"""[문항 {question_num}번 자소서]
{text}

[확정된 채점 결과]
총점: {scoring_result["total_score"]}점/100점
등급: {scoring_result["grade"]}
- 구조: {scoring_result["breakdown"]["구조"]}
- 내용: {scoring_result["breakdown"]["내용"]}
- 표현: {scoring_result["breakdown"]["표현"]}
- 설득력: {scoring_result["breakdown"]["설득력"]} — {scoring_result["ai_score"]["persuasion"]["reason"]}
- 차별성: {scoring_result["breakdown"]["차별성"]} — {scoring_result["ai_score"]["uniqueness"]["reason"]}
- 직무연결: {scoring_result["breakdown"]["직무연결"]} — {scoring_result["ai_score"]["job_relevance"]["reason"]}

감점 요인:
- 탈락 패턴: {scoring_result["code_score"]["details"].get("fatal_patterns", {}).get("triggered", [])}
- 클리셰: {scoring_result["code_score"]["details"].get("cliches", {}).get("found", [])}
- 숫자: {scoring_result["code_score"]["details"].get("numbers", {}).get("count", 0)}개

위 결과를 바탕으로 피드백을 작성하세요."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": FEEDBACK_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
        "stream": True
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=90
        )

        if response.status_code != 200:
            yield f"[오류] API 응답 오류: {response.status_code}"
            return

        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        delta = data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    except requests.Timeout:
        yield "[오류] 응답 시간 초과"
    except requests.ConnectionError:
        yield "[오류] 네트워크 연결 오류"
    except Exception as e:
        yield f"[오류] {str(e)}"


def analyze_resume(resume_text: str, question_number: int, char_limit: int = 600) -> dict:
    """
    자소서 첨삭 분석 v2.0 (심리학/행동경제학 기반)

    Args:
        resume_text: 자소서 원문
        question_number: 문항 번호 (1, 2, 3)
        char_limit: 글자수 제한

    Returns:
        dict: {
            "realtime": {"score": int, "feedbacks": list, "passed": list},
            "llm": dict (JSON 파싱된 결과),
            "char_count": int,
            "char_limit": int,
            "question_number": int
        }
    """
    import json

    # 1단계: 실시간 점수 (LLM 불필요)
    realtime_score, realtime_feedbacks, passed_checks = calculate_realtime_score(
        resume_text, question_number, char_limit
    )

    # 2단계: LLM 심층 분석
    api_key = get_api_key()
    if not api_key:
        return {
            "realtime": {
                "score": realtime_score,
                "feedbacks": realtime_feedbacks,
                "passed": passed_checks
            },
            "llm": {"error": "API 키가 설정되지 않았습니다."},
            "char_count": len(resume_text.replace(" ", "").replace("\n", "")),
            "char_limit": char_limit,
            "question_number": question_number
        }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_KOREAN_AIR_2026},
        {"role": "user", "content": build_user_prompt(question_number, resume_text)}
    ]

    result = call_openai_chat(messages, model="gpt-4o-mini")

    llm_result = {}
    if result:
        try:
            llm_result = json.loads(result["content"])
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트 그대로 반환
            llm_result = {"raw_response": result["content"], "error": "JSON 파싱 실패"}
    else:
        llm_result = {"error": "API 호출 실패"}

    return {
        "realtime": {
            "score": realtime_score,
            "feedbacks": realtime_feedbacks,
            "passed": passed_checks
        },
        "llm": llm_result,
        "char_count": len(resume_text.replace(" ", "").replace("\n", "")),
        "char_limit": char_limit,
        "question_number": question_number
    }


def rewrite_resume(original_text: str, question_number: int, feedbacks: list) -> str:
    """
    자소서 수정본 자동 생성

    Args:
        original_text: 원본 자소서
        question_number: 문항 번호 (1, 2, 3)
        feedbacks: 발견된 문제점 리스트

    Returns:
        str: 수정된 자소서
    """
    api_key = get_api_key()
    if not api_key:
        return "[오류] API 키가 설정되지 않았습니다."

    messages = [
        {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
        {"role": "user", "content": build_rewrite_prompt(question_number, original_text, feedbacks)}
    ]

    result = call_openai_chat(messages, model="gpt-4o-mini", timeout=120)

    if result:
        return result["content"]
    else:
        return "[오류] 수정본 생성에 실패했습니다. 다시 시도해주세요."


def get_chat_response(user_message: str, conversation_history: list = None) -> str:
    """챗봇 응답 요청 (비스트리밍 - 레거시)"""
    context = ""
    if conversation_history:
        recent = conversation_history[-10:]
        for msg in recent:
            role = "사용자" if msg["role"] == "user" else "어시스턴트"
            context += f"{role}: {msg['content']}\n"

    prompt = f"""
{context}
사용자: {user_message}

위 질문에 답변해주세요.
"""
    return call_gpt(prompt, system=CHATBOT_SYSTEM, temperature=0.4)


# ═══════════════════════════════════════
# 챗봇 v2.0 시스템 프롬프트 (할루시네이션 제로)
# ═══════════════════════════════════════

CHATBOT_SYSTEM_SHORT = """당신은 FLYREADY의 승무원 면접 AI 코치입니다.

[절대 규칙]
1. 사실만 말합니다. 모르면 "확인이 필요합니다"라고 합니다.
2. 추측, 창작, 할루시네이션 절대 금지.
3. 출처가 불확실한 정보는 "~로 알려져 있으나 공식 확인 필요"라고 합니다.
4. 연봉, 복지 등 비공식 정보는 "업계 공개 정보 기반 추정치"임을 명시합니다.
5. 한국어로 답변. 간결하게. 핵심만.

[역할]
- 항공사 채용 정보 안내
- 자소서/면접 전략 조언
- 승무원 직무 정보 제공
- 심리학/행동경제학 기반 면접 코칭"""

CHATBOT_SYSTEM_FULL = """당신은 FLYREADY의 승무원 면접 전문 AI 코치입니다.
항공사 채용, 자소서, 면접에 대한 모든 질문에 사실 기반으로 답변합니다.

══════════════════════════════════
[절대 규칙 — 할루시네이션 제로 정책]
══════════════════════════════════
1. 사실만 말합니다. 데이터에 없는 정보는 "공식 확인이 필요합니다"라고 합니다.
2. 추측 금지. "아마~", "~일 것 같습니다" 등 금지. 대신 "공식 발표에 따르면~"
3. 창작 금지. 면접 질문, 합격 후기 등을 만들어내지 않습니다.
4. 출처 명시. 채용정보는 "대한항공 뉴스룸 기준", 연봉은 "업계 추정치"
5. "최신 정보는 대한항공 채용 홈페이지를 반드시 확인하세요."

══════════════════════════════════
[대한항공 2026 채용 정보]
══════════════════════════════════
- 대상: 기졸업자 또는 2026.08 이전 졸업 예정자
- 학력: 제한 없음
- 시력: 교정시력 1.0 이상
- 어학 (택 1): TOEIC 550+ / TOEIC Speaking IM+ / OPIc IM+ (2024.04.22 이후)
- 전형: 서류 → 1차(온라인영상) → 2차+영어구술 → 3차+인성검사 → 건강검진/수영 → 최종
- 입사: 2026년 1월 예정
- 자소서: 3문항 (각 600자)

══════════════════════════════════
[대한항공 기업 정보]
══════════════════════════════════
- 1969년 설립, 스카이팀 창립 멤버, 44개국 120여 도시
- 2024.12.11: 아시아나 지분 63.88% 인수 완료
- 2026.01: 아시아나 인천공항 T2 이전 완료
- 2026.12: 브랜드 완전 통합 예정 → 세계 11위 메가 캐리어
- LCC 통합: 진에어·에어서울·에어부산 → 진에어 (2027년)
- ⚠️ 아시아나는 더 이상 경쟁사 아님. 면접에서 경쟁사로 언급 시 감점!
- 인재상: 도전적, 글로벌, 전문적, 협력적

══════════════════════════════════
[연봉/복지 (업계 추정치, 공식 아님)]
══════════════════════════════════
- 인턴 (1~2년차): 약 3,600~4,000만
- 일반 승무원 (3~4년차): 약 4,000~4,500만
- AP 대리급 (5~7년차): 약 5,000~6,000만
- PS 과장급 (8~12년차): 약 6,500~7,500만
- SP 차장급 (13~17년차): 약 8,000만~
- CP 부장급 (18년차~): 약 8,000만~1억+
- 급여구조: 기본급 + 비행수당 + 퍼디움 + 랜딩비 + 상여금
- 복지: 항공권 최대 90% 할인(연 25회), 사원아파트(2년), 의료비 지원

══════════════════════════════════
[자소서 3문항 전략]
══════════════════════════════════
[1번] 지원동기+적합성
- 키워드 1개로 관통. 600자는 짧아서 분리하면 글자수 부족
- 첫문장: 구체적 장면/숫자로 앵커링
- 탈락패턴: "어릴 때부터 꿈"(-15점), 지원동기/적합성 분리(-10점)

[2번] 역량 (안전+서비스)
- 역량 반드시 1가지만. 2개 이상 = 감점
- 안전/서비스 비중 1:1 균형 필수
- 개념이 아닌 경험으로 증명
- 탈락패턴: 개념만(-15점), 비중 편중(-7점)

[3번] 부담 과제 극복
- 5단계: 부담인정→판단→노력→행동→포부
- 희생 미화 금지 ("남들이 싫어해서" = -12점)
- 핵심은 '왜 내가 하기로 결정했는가' 사고 체계

══════════════════════════════════
[면접 예상 질문 TOP 10]
══════════════════════════════════
1. 대한항공 지원 이유 → 안전 최우선 가치 + 개인 경험 연결
2. 승무원 가장 중요한 자질 → 안전 의식 + 경험 증거
3. 아시아나 통합 의견 → 세계 11위 메가 캐리어 + 서비스 통합 + 상호 존중
4. 팀 갈등 해결 → 개별 경청 → 진짜 원인 파악 → 구조적 해결
5. 무리한 요구 대응 → 감정 인정 → 공감 → 대안 제시
6. 기억에 남는 서비스 경험 → 매뉴얼 이상의 대응 + 팀 공유
7. 체력 관리 → 구체적 루틴 (주 4회 러닝 등) + 교대 근무 경험
8. 외국어 활용 경험 → 실전 활용 + 비언어적 소통 + 문화적 맥락
9. 10년 후 모습 → Senior Purser + 후배 멘토 + 통합 기여
10. 마지막 하고 싶은 말 → 나만의 고유한 한 문장 (피크엔드)

══════════════════════════════════
[심리학/행동경제학 원칙]
══════════════════════════════════
- 앵커링: 첫 문장에 강렬한 장면/숫자로 주의 고정
- 피크엔드: 마지막 문장에 핵심 메시지, 기억에 남는 여운
- 구체성 편향: 추상보다 숫자가 3배 신뢰
- 프레이밍: 평범한 경험→직무 관점 재구성
- 미러링: 대한항공 가치 키워드 자연스럽게 반복
- 자기노출 효과: 솔직한 약점 인정→역설적 신뢰

══════════════════════════════════
[답변 형식]
══════════════════════════════════
1. 간결하게. 핵심만. 불필요한 서론 금지.
2. 한국어로 답변.
3. 채용 정보 답변 시: 출처와 날짜 명시.
4. 모르는 것은 "확인이 필요합니다."
5. 연봉/복지 질문 시: "추정치"임을 명시."""


# ═══════════════════════════════════════
# FAQ 즉시 응답 (LLM 호출 없이 0.01초)
# ═══════════════════════════════════════

FAQ_RESPONSES = {
    "대한항공_지원자격": {
        "keywords": ["대한항공", "자격"],
        "response": """**2026 대한항공 객실승무원 지원 자격**
(출처: 대한항공 뉴스룸, 2025.09.22)

- 학력: 제한 없음 (기졸업자 또는 2026.08 이전 졸업 예정자)
- 시력: 교정시력 1.0 이상
- 어학 (택 1):
  - TOEIC 550점 이상
  - TOEIC Speaking IM 이상
  - OPIc IM 이상
  ※ 2024.04.22 이후 응시 시험만 인정
- 병역: 병역필 또는 면제자
- 해외여행 결격사유 없는 자

최신 정보는 대한항공 채용 홈페이지를 확인하세요."""
    },

    "대한항공_전형절차": {
        "keywords": ["대한항공", "전형"],
        "response": """**2026 대한항공 객실승무원 전형 절차**
(출처: 대한항공 뉴스룸, 2025.09.22)

1단계: 서류전형 (자소서 3문항, 각 600자)
2단계: 1차 면접 (온라인 — 영상 평가)
3단계: 2차 면접 + 영어구술 Test (대면)
4단계: 3차 면접 + 인성검사 (임원면접)
5단계: 건강검진 / 수영 Test
6단계: 최종합격 → 2026년 1월 입사 예정

1차 면접이 온라인(영상)입니다. 카메라 세팅, 조명, 시선 처리 준비가 필수입니다."""
    },

    "대한항공_연봉": {
        "keywords": ["연봉"],
        "response": """**대한항공 객실승무원 연봉 (추정치)**
업계 공개 정보 기반. 대한항공 공식 발표가 아닙니다.

- 인턴 (입사~2년): 약 3,600~4,000만원/년
- 일반 승무원 (3~5년): 약 4,000~4,500만원/년
- AP 대리급 (5~7년): 약 5,000~6,000만원/년
- PS 과장급 (8~12년): 약 6,500~7,500만원/년
- SP 차장급 (13~17년): 약 8,000만원~/년
- CP 부장급 (18년~): 약 8,000만~1억+/년

급여 구성: 기본급 + 비행수당 + 퍼디움(해외 체류비) + 랜딩비 + 상여금
※ 실제 급여는 비행시간, 노선, 직급에 따라 달라집니다."""
    },

    "아시아나_통합": {
        "keywords": ["아시아나", "통합"],
        "response": """**대한항공-아시아나 통합 현황**
(출처: 대한항공 뉴스룸, 공정거래위원회 심사 자료)

- 2024.12.11: 대한항공이 아시아나 지분 63.88% 인수 완료
- 2026.01: 아시아나 인천공항 제2터미널 이전 완료
- 2026.12: 아시아나 → 대한항공 브랜드 완전 통합 예정
- 2027년 초: 진에어·에어서울·에어부산 → 진에어로 LCC 통합
- 통합 후: 세계 11위 메가 캐리어 (연매출 ~23조, 항공기 ~230대)

면접에서 아시아나를 경쟁사로 언급하면 감점될 수 있습니다."""
    },
}


def check_faq(user_message: str) -> Optional[str]:
    """FAQ에 매칭되면 LLM 호출 없이 즉시 응답"""
    for key, faq in FAQ_RESPONSES.items():
        if all(kw in user_message for kw in faq["keywords"]):
            return faq["response"]
    return None


# ═══════════════════════════════════════
# 프롬프트 자동 선택 로직
# ═══════════════════════════════════════

DETAILED_KEYWORDS = [
    "채용", "공채", "지원", "접수", "서류", "면접", "전형",
    "자격", "어학", "토익", "오픽", "시력", "학력",
    "자소서", "자기소개서", "문항", "글자수", "600자",
    "지원동기", "적합성", "역량", "안전", "서비스",
    "대한항공", "아시아나", "진에어", "제주항공", "티웨이",
    "에어프레미아", "이스타", "에미레이트", "카타르",
    "항공사", "항공", "LCC", "승무원", "객실", "기내",
    "연봉", "월급", "복지", "인턴", "정규직",
    "질문", "답변", "영어", "구술", "인성", "PT",
    "전략", "구조", "팁", "합격", "탈락",
    "앵커링", "피크엔드", "프레이밍", "심리학",
    "통합", "합병", "인수", "메가", "스카이팀"
]


def select_system_prompt(user_message: str) -> str:
    """사용자 메시지에 따라 시스템 프롬프트 자동 선택"""
    if any(kw in user_message for kw in DETAILED_KEYWORDS):
        return CHATBOT_SYSTEM_FULL
    return CHATBOT_SYSTEM_SHORT


# ═══════════════════════════════════════
# 할루시네이션 방지 가드레일
# ═══════════════════════════════════════

def validate_response(response_text: str) -> list:
    """챗봇 응답에서 할루시네이션 징후 감지"""
    warnings = []

    # 단정적 미확인 정보 감지
    UNVERIFIED_PATTERNS = [
        ("합격률은", "합격률 데이터는 비공개입니다"),
        ("경쟁률은", "경쟁률 공식 발표 없음"),
        ("반드시 합격", "합격 보장 불가"),
        ("100%", "확률 단정 불가"),
    ]

    for pattern, warning_msg in UNVERIFIED_PATTERNS:
        if pattern in response_text:
            warnings.append(f"'{pattern}' — {warning_msg}")

    return warnings


def stream_chat_response(user_message: str, conversation_history: list = None):
    """
    챗봇 스트리밍 응답 v2.0 (제너레이터)
    1순위: FAQ 즉시 응답
    2순위: LLM 스트리밍 + 할루시네이션 검증
    """
    # 1. FAQ 체크 (0.01초)
    faq_response = check_faq(user_message)
    if faq_response:
        yield faq_response
        return

    # 2. API 키 확인
    api_key = get_api_key()
    if not api_key:
        yield "[오류] API 키가 설정되지 않았습니다."
        return

    # 3. 프롬프트 자동 선택
    system_prompt = select_system_prompt(user_message)

    # 4. 대화 히스토리 구성 (최근 10턴만)
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        recent = conversation_history[-10:]
        for msg in recent:
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"][:500]
                })

    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "stream": True,
        "temperature": 0.3,  # 낮은 온도 = 사실 기반
        "max_tokens": 800,
    }

    full_response = ""

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            yield f"[오류] API 응답 오류: {response.status_code}"
            return

        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    if data_str.strip() == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get('choices', [{}])[0].get('delta', {})
                        content = delta.get('content', '')
                        if content:
                            full_response += content
                            yield content
                    except json.JSONDecodeError:
                        continue

        # 5. 할루시네이션 가드레일
        warnings = validate_response(full_response)
        if warnings:
            yield "\n\n---\n"
            for w in warnings:
                yield f"* {w}\n"

    except requests.Timeout:
        yield "[오류] 응답 시간 초과"
    except requests.ConnectionError:
        yield "[오류] 네트워크 연결 오류"
    except Exception as e:
        yield f"[오류] {str(e)}"


def analyze_news(title: str, content: str) -> str:
    """뉴스 분석 요청"""
    prompt = f"""
뉴스 제목: {title}

뉴스 내용:
{content}

이 뉴스를 면접 준비 관점에서 분석해주세요.
"""
    return call_gpt(prompt, system=NEWS_ANALYSIS_SYSTEM, temperature=0.2)
