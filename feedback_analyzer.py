# feedback_analyzer.py
# 사용자 답변 분석 및 피드백 생성 모듈
#
# 기반 문서:
# - cabincrew: 3축 분석(선택/기준/검증), 잘한점 1개, 아쉬운점 1개, 보완방향, 면접관시점
# - interview: 판단 말투 템플릿 (단정X, 평가X, 해석형 말투)
# - ryulhwan: 추가 피드백 요소 (유지포인트, 위험수정경고, 다음질문예고, 항공사관점, 답변밀도, 완성도단계)
#
# 핵심 공식: "이 답변에서는 A는 보이지만, B는 아직 확인되지 않습니다."

import os
import json
import re
from typing import Dict, Any, Optional, List, Tuple

import requests

from config import LLM_MODEL_NAME, LLM_TIMEOUT_SEC, LLM_API_URL
from text_utils import normalize_ws, _fix_particles_after_format, _auto_fix_particles_kor
from extraction_verifier import extract_key_sentences_verified, _calculate_similarity


# =========================
# 질문 의도 정의 (Set A / Set B)
# =========================

QUESTION_INTENT = {
    "q1": "태도와 기본적인 사고 방향성을 확인하려는 질문입니다.",
    "q2": "경험에서 드러난 선택과 판단 기준을 검증하려는 질문입니다.",
    "q3": "앞선 답변에서 드러난 기준의 일관성을 심화 검증하려는 질문입니다.",
    "q4": "항공사가 중요하게 보는 가치와 지원자의 기준이 정렬되는지 확인하려는 질문입니다.",
    "q5": "돌발 상황에서의 사고 구조 안정성과 판단 일관성을 확인하려는 질문입니다.",
}


# =========================
# 질문 유형별 판단 템플릿 (interview 문서 기반)
# 핵심: 단정 X, 평가 X, 해석형 말투
# =========================

# Q1 공통 질문 템플릿
JUDGMENT_TEMPLATES_Q1 = {
    "basic": "이 답변에서는\n{strength}는 확인되지만,\n{weakness}는 충분히 드러나지 않습니다.",
    "interviewer": "이 답변만 놓고 보면,\n면접관은 당신을 '{perception}'으로 인식할 가능성이 있습니다.",
    "improvement": "이 답변은 방향성은 분명하지만,\n그 방향을 실제로 증명할 수 있는 장면이 추가되면 신뢰도가 더 높아질 수 있습니다.",
}

# Q2 자소서 기반 심층 질문 템플릿
JUDGMENT_TEMPLATES_Q2 = {
    "criteria_weak": "이 답변에서는\n어떤 행동을 했는지는 분명하지만,\n왜 그 방식을 선택했는지에 대한 개인 기준은 면접관이 추론해야 하는 상태입니다.",
    "verify_weak": "이 답변은 하나의 경험을 통해 판단을 설명하고 있으나,\n다른 상황에서도 동일한 기준이 유지될지에 대한 검증은 충분히 드러나지 않습니다.",
    "interviewer": "이 답변만 놓고 보면,\n면접관은 '{perception}'고 인식할 가능성이 있습니다.",
}

# Q3 꼬리 질문 템플릿
JUDGMENT_TEMPLATES_Q3 = {
    "criteria_fixed": "앞선 답변에서 제시한 기준은 분명하지만,\n그 기준이 흔들릴 수 있었던 상황까지는 충분히 다뤄지지 않았습니다.",
    "responsibility": "이 답변에서는 상황 설명은 충분하나,\n해당 선택에서 본인이 어디까지 책임을 지고 판단했는지는 추가 확인이 필요합니다.",
    "consistency": "이 답변만 보면,\n앞선 질문에서 드러난 판단 기준이\n이번 상황에서도 동일하게 적용되는지는 명확하지 않습니다.",
}

# Q4 인재상/가치 질문 템플릿
JUDGMENT_TEMPLATES_Q4 = {
    "alignment": "이 답변에서는\n회사가 중요하게 보는 가치와 당신의 기준이 같은 방향을 향하고 있다는 점은 보이지만,\n그 기준이 우선되는 상황까지는 확인되지 않습니다.",
    "risk": "이 답변만 보면,\n면접관은 가치에 대한 이해는 충분하지만,\n실제 판단 순간에 어떤 기준을 우선할지는 추가 확인이 필요하다고 느낄 수 있습니다.",
    "conflict": "이 항공사 기준에서 보면,\n해당 가치는 중요하게 인식되고 있으나\n안전·규정·책임과 같은 다른 가치와 충돌할 경우의 판단은 아직 드러나지 않습니다.",
}

# Q5 돌발/확장 질문 템플릿
JUDGMENT_TEMPLATES_Q5 = {
    "choice": "이 답변에서는\n선택의 방향성은 확인되지만,\n다른 선택지를 배제한 이유까지는 충분히 드러나지 않습니다.",
    "interviewer": "이 답변만 놓고 보면,\n면접관은 \"비슷한 상황이 반복될 때도 같은 판단을 할 수 있을까?\"라는 의문을 가질 수 있습니다.",
    "stability": "돌발 상황에 대한 기본적인 대응 방향은 보이지만,\n판단의 기준이 한 가지 상황에만 의존하고 있는지 여부는 추가로 확인이 필요합니다.",
}


# =========================
# 3축 분석 문제 신호
# =========================

DECISION_PROBLEM_PATTERNS = [
    "노력했습니다", "노력하겠습니다", "최선을 다",
    "중요하다고 생각", "중요합니다", "필요하다고",
    "해야 한다고", "해야 합니다",
]

CRITERIA_PROBLEM_PATTERNS = [
    "팀워크가 중요", "협업이 중요", "소통이 중요",
    "책임감을 느껴", "책임감이 중요",
    "고객이 우선", "안전이 우선", "서비스가 중요",
]

VERIFIABILITY_PROBLEM_PATTERNS = [
    "성공했습니다", "해결했습니다", "극복했습니다",
    "좋은 결과", "좋은 성과", "만족했습니다",
]


# =========================
# 핵심문장 추출 및 검증 (방안 1+2 연동)
# =========================

def extract_verified_key_context(
    essay_answer: str,
    attack_point: str = "",
    max_sentences: int = 3
) -> Dict[str, Any]:
    """
    자소서 답변에서 검증된 핵심 문장을 추출.
    attack_point가 주어지면 관련성 높은 문장 우선.

    Returns:
        {
            "key_sentences": ["문장1", "문장2", ...],
            "attack_relevance": 공격 포인트와의 연관성 점수,
            "context_summary": 핵심 컨텍스트 요약
        }
    """
    result = {
        "key_sentences": [],
        "attack_relevance": 0.0,
        "context_summary": ""
    }

    if not essay_answer:
        return result

    # 검증된 핵심 문장 추출
    verified_sentences = extract_key_sentences_verified(essay_answer, max_sentences=max_sentences + 2)

    if not verified_sentences:
        return result

    # 공격 포인트가 있으면 관련성 순으로 재정렬
    if attack_point:
        for sent_info in verified_sentences:
            relevance = _calculate_similarity(sent_info["text"], attack_point)
            sent_info["attack_relevance"] = relevance

        # 관련성 + 기본 점수 조합으로 정렬
        verified_sentences.sort(
            key=lambda x: -(x.get("attack_relevance", 0) * 0.3 + x["score"] * 0.7)
        )

        # 최고 관련성 기록
        if verified_sentences:
            result["attack_relevance"] = max(
                s.get("attack_relevance", 0) for s in verified_sentences
            )

    # 상위 문장 선택
    selected = verified_sentences[:max_sentences]
    result["key_sentences"] = [s["text"] for s in selected]

    # 컨텍스트 요약 생성
    if selected:
        types_found = set()
        for s in selected:
            types_found.update(s.get("types", []))

        if "action" in types_found:
            result["context_summary"] = "행동과 선택이 드러나는 경험"
        elif "decision" in types_found:
            result["context_summary"] = "판단 기준이 드러나는 경험"
        elif "result" in types_found:
            result["context_summary"] = "결과가 드러나는 경험"
        else:
            result["context_summary"] = "관련 경험"

    return result


def verify_attack_point_in_essay(
    attack_point: str,
    essay_answer: str,
    min_similarity: float = 0.35
) -> Dict[str, Any]:
    """
    공격 포인트가 실제 자소서에 존재하는지 검증.

    Returns:
        {
            "verified": True/False,
            "original": 원본 공격 포인트,
            "matched": 매칭된 원문 (없으면 원본 유지),
            "confidence": 신뢰도,
            "match_type": "exact" | "similar" | "unverified"
        }
    """
    result = {
        "verified": False,
        "original": attack_point,
        "matched": attack_point,
        "confidence": 0.0,
        "match_type": "unverified"
    }

    if not attack_point or not essay_answer:
        return result

    attack_norm = normalize_ws(attack_point)
    essay_norm = normalize_ws(essay_answer)

    # 1. 완전 포함 체크
    if attack_norm in essay_norm:
        result["verified"] = True
        result["confidence"] = 1.0
        result["match_type"] = "exact"
        return result

    # 2. 문장 단위 유사도 체크
    from text_utils import split_sentences
    sentences = split_sentences(essay_answer)

    best_match = None
    best_score = 0.0

    for sent in sentences:
        sent_norm = normalize_ws(sent)
        if not sent_norm or len(sent_norm) < 10:
            continue

        # 포함 관계 체크
        if attack_norm in sent_norm or sent_norm in attack_norm:
            result["verified"] = True
            result["matched"] = sent
            result["confidence"] = 0.95
            result["match_type"] = "exact"
            return result

        # 유사도 계산
        score = _calculate_similarity(attack_norm, sent_norm)
        if score > best_score:
            best_score = score
            best_match = sent

    # 3. 유사도 기반 매칭
    if best_match and best_score >= min_similarity:
        result["verified"] = True
        result["matched"] = best_match
        result["confidence"] = best_score
        result["match_type"] = "similar" if best_score >= 0.7 else "partial"
        return result

    return result


# =========================
# LLM 분석 프롬프트 빌더
# =========================

def _build_analysis_prompt_set_a(
    question_key: str,
    question_text: str,
    user_answer: str,
    airline: str = "",
) -> str:
    """Set A (Q1, Q4, Q5) 분석용 LLM 프롬프트"""

    intent = QUESTION_INTENT.get(question_key, "지원자의 판단력을 확인하려는 질문입니다.")

    extra_criteria = ""
    if question_key == "q4":
        extra_criteria = """
4. 가치 정렬: 항공사 가치와 본인 기준이 같은 방향인가?
5. 충돌 대비: 다른 가치와 충돌 시 어떤 기준을 우선하는가?"""
    elif question_key == "q5":
        extra_criteria = """
4. 선택 구조: 다른 선택지를 배제한 이유가 있는가?
5. 판단 안정성: 비슷한 상황 반복 시에도 같은 판단이 가능한가?"""

    prompt = f"""당신은 항공사 면접관입니다. 지원자의 답변을 분석해주세요.

## 질문 의도
{intent}

## 질문
{question_text}

## 지원자 답변
{user_answer}

## 분석 기준 (3축)

### 1. 선택(Decision)
- 무엇을 선택했는가? 문장 하나로 요약 가능한가?
- 문제 신호: "노력했습니다", "중요하다고 생각합니다" (선택 주체가 안 보임)

### 2. 기준(Criteria)
- 왜 그 선택을 했는가? 본인만의 기준인가, 누구나 쓸 말인가?
- 문제 신호: "팀워크가 중요해서", "책임감을 느껴서"

### 3. 검증 가능성(Verifiability)
- 이 판단이 다른 상황에서도 유지될 수 있는가?
- 문제 신호: 단일 성공 사례, 결과만 있고 과정 없음
{extra_criteria}

## 출력 형식 (반드시 JSON)
핵심 공식: "이 답변에서는 A는 보이지만, B는 아직 확인되지 않습니다."
- A = 사용자가 잘한 핵심 1개 (칭찬 아님, 살릴 수 있는 요소)
- B = 면접관이 불안해할 핵심 1개 (단정/평가 금지, 해석형으로)

```json
{{
  "decision": {{
    "found": true/false,
    "summary": "선택 요약 (1문장)"
  }},
  "criteria": {{
    "found": true/false,
    "summary": "기준 요약 (1문장)",
    "is_unique": true/false
  }},
  "verifiability": {{
    "found": true/false,
    "has_limit_awareness": true/false
  }},
  "visible_strength": "보이는 강점 (예: 팀을 우선하는 판단 기준)",
  "not_confirmed": "아직 확인되지 않는 것 (예: 압박 상황에서도 유지될지에 대한 근거)",
  "improvement_action": "다음 답변에서 추가할 구체적 행동 1가지",
  "interviewer_perception": "면접관이 인식할 지원자 유형 (예: 기준은 있으나 검증이 부족한 지원자)",
  "keep_point": "반드시 유지해야 할 요소 (예: 팀 내 기준을 명확히 인식하고 있다는 점)",
  "risky_modification": "잘못 고치면 위험해지는 수정 방향 (예: 경험을 더 강조하려다 결과 위주로 바뀌면 판단 기준이 흐려질 수 있음)",
  "next_question_preview": "다음 질문에서 검증될 가능성이 큰 포인트 (예: 이 기준이 압박 상황에서도 유지되는지)",
  "airline_sensitive_point": "이 항공사 기준에서 특히 민감한 지점 (Q4/Q5 전용, 예: 팀워크보다 규정 판단이 더 중요하게 해석될 수 있음)",
  "answer_density": "high/medium/low - 설명 대비 판단 정보의 비율",
  "completion_stage": "초안 단계/구조 안정 단계/실전 가능 단계/압박 질문 대비 필요 중 하나"
}}
```

중요:
- JSON만 출력하세요.
- 단정("부족하다", "잘못했다") 금지
- 평가("미흡하다") 금지
- 해석형 표현 사용 ("~로 인식될 가능성", "~는 확인되지 않습니다")"""

    return prompt


def _build_analysis_prompt_set_b(
    question_key: str,
    question_text: str,
    user_answer: str,
    attack_point: str = "",
    essay_context: str = "",
    q2_answer: str = "",
) -> str:
    """Set B (Q2, Q3) 분석용 LLM 프롬프트"""

    intent = QUESTION_INTENT.get(question_key, "자소서 내용을 검증하려는 질문입니다.")

    q3_extra = ""
    if question_key == "q3" and q2_answer:
        q3_extra = f"""
## Q2 답변 (참고용)
{q2_answer}

### 추가 분석 기준 (Q3 전용)
- 앞선 답변의 기준이 이번에도 동일하게 적용되는가?
- 기준이 흔들릴 수 있었던 상황을 다뤘는가?
- 본인이 어디까지 책임지고 판단했는지 드러나는가?"""

    prompt = f"""당신은 항공사 면접관입니다. 자소서 기반 검증 질문에 대한 답변을 분석해주세요.

## 질문 의도
{intent}

## 공격 포인트 (질문이 검증하려는 것)
{attack_point if attack_point else "자소서에 쓴 경험/표현의 진정성"}

## 질문
{question_text}

## 지원자 답변
{user_answer}

## 자소서 관련 내용 (참고용)
{essay_context if essay_context else "(자소서 컨텍스트 없음)"}
{q3_extra}

## 분석 기준 (자소서 검증용 3축)

### 1. 공격 인정(Acknowledgment)
- 질문의 전제(약점 가능성)를 인정했는가?
- 문제 신호: 공격을 회피하거나 무시함

### 2. 방어 논리(Defense Logic)
- "그럼에도 불구하고"의 논리가 있는가?
- 문제 신호: 추상적 다짐만 있음 ("노력하겠습니다")

### 3. 자소서 일관성(Consistency)
- 자소서 경험과 일관되게 답했는가?
- 문제 신호: 자소서와 다른 말, 새로운 경험 급조

## 출력 형식 (반드시 JSON)
핵심 공식: "이 답변에서는 A는 보이지만, B는 아직 확인되지 않습니다."

```json
{{
  "acknowledgment": {{
    "found": true/false,
    "how": "인정 방식 요약"
  }},
  "defense_logic": {{
    "found": true/false,
    "summary": "방어 논리 요약",
    "has_alternative": true/false
  }},
  "consistency": {{
    "aligned": true/false
  }},
  "visible_strength": "보이는 강점 (예: 어떤 행동을 했는지는 분명함)",
  "not_confirmed": "아직 확인되지 않는 것 (예: 왜 그 방식을 선택했는지에 대한 개인 기준)",
  "improvement_action": "다음 답변에서 추가할 구체적 행동 1가지",
  "interviewer_perception": "면접관이 인식할 지원자 유형",
  "keep_point": "반드시 유지해야 할 요소",
  "risky_modification": "잘못 고치면 위험해지는 수정 방향",
  "next_question_preview": "다음 질문(꼬리질문)에서 검증될 가능성이 큰 포인트",
  "answer_density": "high/medium/low - 설명 대비 판단 정보의 비율",
  "completion_stage": "초안 단계/구조 안정 단계/실전 가능 단계/압박 질문 대비 필요 중 하나"
}}
```

중요:
- JSON만 출력하세요.
- 단정/평가 금지, 해석형 표현만 사용"""

    return prompt


# =========================
# LLM API 호출
# =========================

def _call_llm_for_analysis(prompt: str) -> Optional[Dict[str, Any]]:
    """LLM API 호출 및 JSON 파싱"""

    api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_APIKEY")
        or os.getenv("OPENAI_KEY")
        or ""
    )

    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "당신은 항공사 면접관입니다. JSON 형식으로만 응답하세요. 단정/평가 표현을 피하고 해석형 표현을 사용하세요."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    try:
        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
        r.raise_for_status()
        resp = r.json()

        choices = resp.get("choices", [])
        if not choices:
            return None

        content = choices[0].get("message", {}).get("content", "")
        if not content:
            return None

        return json.loads(content)

    except Exception as e:
        print(f"[feedback_analyzer] LLM 호출 실패: {e}")
        return None


# =========================
# 규칙 기반 보완 분석
# =========================

def _rule_based_check(answer: str) -> Dict[str, Any]:
    """규칙 기반 추가 체크 (LLM 보완용)"""

    ans = normalize_ws(answer or "")

    result = {
        "has_numbers": bool(re.search(r"\d+", ans)),
        "has_time_period": bool(re.search(r"(개월|주|일|시간|분|년|동안)", ans)),
        "has_action_verbs": bool(re.search(r"(했습니다|하였습니다|했고|진행했|수행했|처리했|대응했|확인했|안내했|조율했|정리했|보고했)", ans)),
        "length": len(ans),
        "sentence_count": len(re.findall(r"[.!?]", ans)),
        "decision_problems": [],
        "criteria_problems": [],
        "verifiability_problems": [],
    }

    for pattern in DECISION_PROBLEM_PATTERNS:
        if pattern in ans:
            result["decision_problems"].append(pattern)

    for pattern in CRITERIA_PROBLEM_PATTERNS:
        if pattern in ans:
            result["criteria_problems"].append(pattern)

    for pattern in VERIFIABILITY_PROBLEM_PATTERNS:
        if pattern in ans:
            result["verifiability_problems"].append(pattern)

    return result


# =========================
# 피드백 포맷팅 (interview 문서 템플릿 적용)
# =========================

def _format_feedback_output(
    question_key: str,
    llm_analysis: Optional[Dict[str, Any]],
    rule_check: Dict[str, Any],
) -> str:
    """
    최종 피드백 포맷팅
    - cabincrew 구조: 질문의도, 잘한점, 아쉬운점, 보완방향, 면접관시점
    - interview 말투: 단정X, 평가X, 해석형 ("~는 확인되지 않습니다")
    - ryulhwan 추가: 유지포인트, 위험수정경고, 다음질문예고, 항공사관점, 답변밀도, 완성도단계

    피드백 순서 (ryulhwan 권장):
    1. 질문 의도
    2. 분석 결과 (잘한 점 + 아쉬운 점)
    3. 보완 방향 (행동 지시)
    4. 유지해야 할 포인트
    5. 위험해지는 수정 방향
    6. 다음 질문 예고
    7. 답변 밀도 + 완성도 단계
    8. 면접관 시점 한 문장
    """

    lines = []
    intent = QUESTION_INTENT.get(question_key, "지원자의 판단력을 확인하려는 질문입니다.")

    # 1. 질문 의도
    lines.append("[이 질문의 의도]")
    lines.append(f"  {intent}")
    lines.append("")

    if llm_analysis:
        visible = llm_analysis.get("visible_strength", "")
        not_confirmed = llm_analysis.get("not_confirmed", "")
        improvement = llm_analysis.get("improvement_action", "")
        perception = llm_analysis.get("interviewer_perception", "")
        keep_point = llm_analysis.get("keep_point", "")
        risky_mod = llm_analysis.get("risky_modification", "")
        next_preview = llm_analysis.get("next_question_preview", "")
        airline_sensitive = llm_analysis.get("airline_sensitive_point", "")
        density = llm_analysis.get("answer_density", "")
        stage = llm_analysis.get("completion_stage", "")

        # 2. 핵심 판단 (interview 공식 적용)
        # "이 답변에서는 A는 보이지만, B는 아직 확인되지 않습니다."
        if visible and not_confirmed:
            lines.append("[분석 결과]")
            lines.append(f"  이 답변에서는")
            lines.append(f"  [{visible}] 부분은 확인되지만,")
            lines.append(f"  [{not_confirmed}] 부분은 충분히 드러나지 않습니다.")
            lines.append("")

        # 3. 보완 방향 (행동 지시)
        if improvement:
            lines.append("[보완 방향]")
            lines.append(f"  다음 답변에서는 [{improvement}] 부분을 추가해보세요.")
            lines.append(f"  그러면 판단의 신뢰도가 더 높아질 수 있습니다.")
            lines.append("")

        # 4. 유지해야 할 포인트 (ryulhwan - 사용자 불안 감소)
        if keep_point:
            lines.append("[유지해야 할 포인트]")
            lines.append(f"  이 답변에서 [{keep_point}] 부분은")
            lines.append(f"  다음 답변에서도 유지하는 것이 좋습니다.")
            lines.append("")

        # 5. 위험한 수정 방향 (ryulhwan - 전문가 느낌)
        if risky_mod:
            lines.append("[주의: 이렇게 고치면 위험할 수 있습니다]")
            lines.append(f"  {risky_mod}")
            lines.append("")

        # 6. 다음 질문 예고 (ryulhwan - 전략적 준비 유도)
        if next_preview:
            lines.append("[다음 질문 예고]")
            lines.append(f"  다음 질문에서는")
            lines.append(f"  [{next_preview}] 부분이 이어서 확인될 가능성이 큽니다.")
            lines.append("")

        # 7. 항공사 관점 주의 포인트 (Q4, Q5 전용)
        if airline_sensitive and question_key in ("q4", "q5"):
            lines.append("[항공사 관점 주의 포인트]")
            lines.append(f"  이 항공사 기준에서는")
            lines.append(f"  {airline_sensitive}")
            lines.append("")

        # 8. 답변 밀도 + 완성도 단계 (ryulhwan - 점수 대신)
        if density or stage:
            lines.append("[현재 답변 상태]")
            if density:
                density_desc = {
                    "high": "설명 대비 판단 정보의 비율이 높아 면접 답변으로 활용하기에 효율적인 편입니다.",
                    "medium": "설명과 판단 정보의 비율이 적절합니다.",
                    "low": "상황 설명 비중이 높아 판단 기준이 상대적으로 묻힐 수 있습니다.",
                }.get(density.lower(), "")
                if density_desc:
                    lines.append(f"  답변 밀도: {density_desc}")
            if stage:
                lines.append(f"  완성도: {stage}")
            lines.append("")

        # 9. 면접관 시점 (interview 템플릿 - 마지막 한 문장)
        if perception:
            lines.append("[면접관 시점]")
            lines.append(f"  이 답변만 놓고 보면,")
            lines.append(f"  면접관은 당신을 [{perception}] 유형으로 인식할 가능성이 있습니다.")
            lines.append("")

    else:
        # LLM 실패 시 규칙 기반 피드백 (해석형 말투 유지)
        lines.append("[분석 결과]")

        # 문제 신호 기반 피드백 (단정 X, 해석형으로)
        visible = "답변의 방향성"
        not_confirmed = ""

        if rule_check["decision_problems"]:
            not_confirmed = "구체적인 선택 주체"
            lines.append(f"  이 답변에서는 의도는 확인되지만,")
            lines.append(f"  '{rule_check['decision_problems'][0]}' 같은 표현으로 인해")
            lines.append(f"  선택 주체가 충분히 드러나지 않습니다.")
        elif rule_check["criteria_problems"]:
            not_confirmed = "본인만의 판단 기준"
            lines.append(f"  이 답변에서는 가치에 대한 인식은 보이지만,")
            lines.append(f"  '{rule_check['criteria_problems'][0]}'는 누구나 쓸 수 있는 표현이라")
            lines.append(f"  본인만의 기준은 확인되지 않습니다.")
        elif not rule_check["has_numbers"] and not rule_check["has_time_period"]:
            not_confirmed = "구체적인 근거"
            lines.append(f"  이 답변에서는 방향성은 보이지만,")
            lines.append(f"  숫자나 기간 같은 구체적 근거가 충분히 드러나지 않습니다.")
        elif rule_check["length"] < 100:
            not_confirmed = "충분한 설명"
            lines.append(f"  이 답변에서는 핵심은 보이지만,")
            lines.append(f"  면접관이 판단하기에 충분한 정보가 드러나지 않습니다.")
        else:
            lines.append(f"  이 답변에서는 기본적인 방향성은 확인됩니다.")

        lines.append("")
        lines.append("[보완 방향]")
        lines.append(f"  다음 답변에서는 구체적인 상황 1가지와 본인의 선택 기준을 추가해보세요.")
        lines.append("")

        # 규칙 기반 유지 포인트 (ryulhwan)
        if rule_check["has_action_verbs"]:
            lines.append("[유지해야 할 포인트]")
            lines.append(f"  구체적인 행동을 표현한 부분은 유지하는 것이 좋습니다.")
            lines.append("")

        # 규칙 기반 위험 경고 (ryulhwan)
        lines.append("[주의: 이렇게 고치면 위험할 수 있습니다]")
        lines.append(f"  답변을 늘리려다 추상적인 다짐이나 결과 위주로 바뀌면")
        lines.append(f"  오히려 판단 기준이 흐려질 수 있습니다.")
        lines.append("")

        # 규칙 기반 완성도
        lines.append("[현재 답변 상태]")
        if rule_check["length"] < 100:
            lines.append(f"  완성도: 초안 단계")
        elif not rule_check["has_numbers"]:
            lines.append(f"  완성도: 구조 안정 단계 (구체적 근거 추가 필요)")
        else:
            lines.append(f"  완성도: 실전 가능 단계")
        lines.append("")

        lines.append("[면접관 시점]")
        lines.append(f"  이 답변만 놓고 보면,")
        lines.append(f"  면접관은 '의도는 이해되지만, 검증이 필요한 지원자'로 인식할 가능성이 있습니다.")

    # 최종 출력에 조사 보정 적용
    result = "\n".join(lines)
    result = _fix_particles_after_format(result)
    result = _auto_fix_particles_kor(result)
    return result


# =========================
# 메인 분석 함수
# =========================

def analyze_answer_set_a(
    question_key: str,
    question_text: str,
    user_answer: str,
    airline: str = "",
) -> str:
    """Set A (Q1, Q4, Q5) 답변 분석 및 피드백 생성"""

    if not user_answer or not user_answer.strip():
        return ""

    prompt = _build_analysis_prompt_set_a(question_key, question_text, user_answer, airline)
    llm_result = _call_llm_for_analysis(prompt)
    rule_result = _rule_based_check(user_answer)

    return _format_feedback_output(question_key, llm_result, rule_result)


def analyze_answer_set_b(
    question_key: str,
    question_text: str,
    user_answer: str,
    attack_point: str = "",
    essay_context: str = "",
    q2_answer: str = "",
) -> str:
    """Set B (Q2, Q3) 답변 분석 및 피드백 생성

    방안 1+2 적용:
    - 공격 포인트를 원문과 대조 검증
    - 검증된 핵심 문장으로 컨텍스트 보강
    """

    if not user_answer or not user_answer.strip():
        return ""

    # 방안 1+2: 공격 포인트 검증
    verified_attack = attack_point
    if attack_point and essay_context:
        verification_result = verify_attack_point_in_essay(attack_point, essay_context)
        if verification_result["verified"]:
            verified_attack = verification_result["matched"]

    # 방안 1+2: 검증된 핵심 문장으로 컨텍스트 보강
    enhanced_context = essay_context
    if essay_context:
        key_context = extract_verified_key_context(
            essay_context,
            attack_point=verified_attack,
            max_sentences=3
        )
        if key_context["key_sentences"]:
            # 핵심 문장을 컨텍스트에 추가
            key_sents_text = " | ".join(key_context["key_sentences"])
            enhanced_context = f"{essay_context}\n\n[핵심 문장] {key_sents_text}"

    prompt = _build_analysis_prompt_set_b(
        question_key, question_text, user_answer,
        verified_attack, enhanced_context, q2_answer
    )
    llm_result = _call_llm_for_analysis(prompt)
    rule_result = _rule_based_check(user_answer)

    return _format_feedback_output(question_key, llm_result, rule_result)


def analyze_answer(
    question_key: str,
    question_text: str,
    user_answer: str,
    question_type: str = "",
    attack_point: str = "",
    essay_context: str = "",
    q2_answer: str = "",
    airline: str = "",
) -> str:
    """통합 분석 함수 - 질문 키에 따라 Set A/B 자동 분기"""

    if question_key in ("q1", "q4", "q5"):
        return analyze_answer_set_a(question_key, question_text, user_answer, airline)
    elif question_key in ("q2", "q3"):
        return analyze_answer_set_b(
            question_key, question_text, user_answer,
            attack_point, essay_context, q2_answer
        )
    else:
        return analyze_answer_set_a(question_key, question_text, user_answer, airline)
