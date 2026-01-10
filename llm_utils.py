# llm_utils.py
# LLM 상태 관리, API 호출, JSON 파싱, 추출 로직

import os
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple

import requests
import streamlit as st

from config import (
    ENABLE_PLAN_LIMITS, LLM_MODEL_NAME, LLM_TIMEOUT_SEC,
    LLM_TTL_SEC, LLM_API_URL,
    LLM_STATE_PENDING, LLM_STATE_COMPLETED, LLM_STATE_FAILED, LLM_STATE_ABORTED,
    LLM_REQUIRED_KEYS,
)
from text_utils import normalize_ws
from analysis import _classify_prompt_type_kor


def _now_ts() -> float:
    return time.time()


def _ensure_llm_state_boxes():
    if "_llm_extract_box" not in st.session_state:
        st.session_state._llm_extract_box = {}
    if "_llm_plan" not in st.session_state:
        st.session_state._llm_plan = {
            "tier": "Standard",
            "enable_limits": False,
            "standard_daily_count": 0,
            "standard_daily_ymd": "",
            "premium_monthly_count": 0,
            "premium_monthly_ym": "",
        }


def _llm_gc():
    _ensure_llm_state_boxes()
    box = st.session_state.get("_llm_extract_box", {})
    if not isinstance(box, dict) or not box:
        return
    now = _now_ts()
    to_del = []
    for k, v in box.items():
        try:
            ts = float((v or {}).get("ts", 0.0))
        except Exception:
            ts = 0.0
        if (now - ts) > LLM_TTL_SEC:
            to_del.append(k)
    for k in to_del:
        try:
            del box[k]
        except Exception:
            pass
    st.session_state._llm_extract_box = box


def _ymd_local_kor() -> str:
    return time.strftime("%Y-%m-%d", time.localtime())


def _ym_local() -> str:
    return time.strftime("%Y-%m", time.localtime())


def _plan_touch_and_maybe_reset():
    _ensure_llm_state_boxes()
    plan = st.session_state._llm_plan
    ymd = _ymd_local_kor()
    ym = _ym_local()
    if plan.get("standard_daily_ymd") != ymd:
        plan["standard_daily_ymd"] = ymd
        plan["standard_daily_count"] = 0
    if plan.get("premium_monthly_ym") != ym:
        plan["premium_monthly_ym"] = ym
        plan["premium_monthly_count"] = 0
    plan["enable_limits"] = bool(ENABLE_PLAN_LIMITS)
    st.session_state._llm_plan = plan


def _plan_can_run_llm() -> bool:
    _plan_touch_and_maybe_reset()
    plan = st.session_state._llm_plan
    if not plan.get("enable_limits", False):
        return True
    tier = plan.get("tier", "Standard")
    if tier == "Standard":
        return int(plan.get("standard_daily_count", 0)) < 1
    return int(plan.get("premium_monthly_count", 0)) < 60


def _plan_commit_usage_once(llm_hash: str) -> None:
    """
    COMPLETED 커밋 시점에서만 카운트 증가.
    동일 해시가 이미 counted면 중복 증가 금지.
    """
    _plan_touch_and_maybe_reset()
    box = st.session_state.get("_llm_extract_box", {})
    if not isinstance(box, dict):
        return
    rec = box.get(llm_hash, {}) or {}
    if rec.get("counted", False):
        return
    plan = st.session_state._llm_plan
    tier = plan.get("tier", "Standard")
    if tier == "Standard":
        plan["standard_daily_count"] = int(plan.get("standard_daily_count", 0)) + 1
    else:
        plan["premium_monthly_count"] = int(plan.get("premium_monthly_count", 0)) + 1
    st.session_state._llm_plan = plan
    rec["counted"] = True
    box[llm_hash] = rec
    st.session_state._llm_extract_box = box


def _calc_llm_hash_from_qa_sets(qa_sets: List[Dict[str, str]]) -> str:
    """
    동일 자소서(문항+답변 결합) 재호출 금지용 해시.
    """
    parts: List[str] = []
    for qa in (qa_sets or []):
        p = (qa.get("prompt", "") or "").replace("\r\n", "\n").replace("\r", "\n")
        a = (qa.get("answer", "") or "").replace("\r\n", "\n").replace("\r", "\n")
        parts.append("Q:" + p)
        parts.append("A:" + a)
        parts.append("---")
    joined = "\n".join(parts)
    return hashlib.sha256(joined.encode("utf-8", errors="ignore")).hexdigest() if joined else ""


def _llm_type_to_internal(llm_type: str, fallback_internal: str) -> str:
    t = normalize_ws(llm_type or "")
    # LLM 출력값 정규화
    if t in ("경험요구", "경험 요구", "경험_요구"):
        return "경험 요구형"
    if t in ("가치태도", "가치 태도", "가치_태도"):
        return "가치·태도 정합성형"
    if t in ("동기정체성", "동기 정체성", "동기_정체성"):
        return "동기·정체성형"
    return fallback_internal


def _internal_prompt_to_llm_type(prompt: str) -> str:
    it = _classify_prompt_type_kor(prompt)
    if it == "경험 요구형":
        return "경험요구"
    if it == "가치·태도 정합성형":
        return "가치태도"
    if it == "동기·정체성형":
        return "동기정체성"
    return "경험요구"


def _llm_build_messages_for_extract(qa_sets: List[Dict[str, str]]) -> List[Dict[str, str]]:
    items_payload = []
    for qa in (qa_sets or []):
        q = (qa.get("prompt", "") or "").strip()
        a = (qa.get("answer", "") or "").strip()
        items_payload.append({
            "question": q if q else "자기소개서",
            "answer": a,
        })

    # 시스템 프롬프트: 면접관처럼 의심하는 역할
    system = (
        "당신은 항공사 면접관입니다. "
        "지원자의 자소서를 읽고 '공격 포인트'를 찾아야 합니다. "
        "좋은 점이 아니라 의심할 점, 논리적 허점, 이상적인 표현을 찾으세요. "
        "JSON만 출력하세요."
    )

    # 면접관 시점 분석 프롬프트
    user = (
        "# 면접관 시점 자소서 분석\n\n"
        "## 당신의 역할\n"
        "당신은 까다로운 항공사 면접관입니다.\n"
        "지원자의 자소서를 읽고 '헉' 하게 만들 질문을 위한 공격 포인트를 찾으세요.\n"
        "좋은 점을 찾지 마세요. 의심할 점을 찾으세요.\n\n"
        "## 추출해야 할 6가지 공격 포인트\n\n"
        "### 1. claim (지원자의 핵심 주장)\n"
        "지원자가 자신에 대해 주장하는 핵심 문장 1개\n"
        "예시:\n"
        "- '나는 팀워크를 중시하는 사람이다'\n"
        "- '나는 어려움 속에서 성장하는 사람이다'\n"
        "- '나는 고객을 최우선으로 생각한다'\n\n"
        "### 2. decision_criteria (숨겨진 판단 기준)\n"
        "지원자가 선택/행동할 때 사용한 판단 기준 2개\n"
        "이건 명시적이지 않아도 됨. 행동에서 추론 가능.\n"
        "예시:\n"
        "- '혼자보다 함께일 때 더 잘 해결된다고 판단'\n"
        "- '분위기가 성과보다 중요하다고 인식'\n"
        "- '규정보다 고객 만족이 우선이라고 생각'\n\n"
        "### 3. rejected_alternatives (선택하지 않은 다른 길)\n"
        "지원자가 선택하지 않은 대안 2개\n"
        "면접관은 '왜 그건 안 했어요?'라고 물을 수 있음\n"
        "예시:\n"
        "- '혼자 해결하려는 방식'\n"
        "- '성과 중심의 팀 운영'\n"
        "- '규정을 엄격히 적용하는 방식'\n\n"
        "### 4. over_idealized_points (너무 이상적인 표현) ⭐가장 중요\n"
        "현실의 리스크가 전혀 언급되지 않은 이상적인 문장 4개\n"
        "면접관은 여기서 반드시 공격합니다. 자소서 전체에서 골고루 찾으세요.\n"
        "예시:\n"
        "- '함께라서 극복할 수 있었다'\n"
        "- '웃으면서 할 수 있는 환경을 만들었다'\n"
        "- '따뜻한 미소로 고객을 감동시켰다'\n"
        "- '팀원들과 소통하며 문제를 해결했다'\n"
        "- '포기하지 않고 끝까지 해냈다'\n"
        "- '배려와 존중으로 갈등을 해소했다'\n\n"
        "### 5. risk_points (취약 지점/블라인드 스팟)\n"
        "이 판단이 문제가 될 수 있는 상황 3개\n"
        "'그럼에도 불구하고' 질문의 재료\n"
        "예시:\n"
        "- '규정이 우선일 때도 팀 분위기를 택할 가능성'\n"
        "- '감정노동이 누적될 때 태도 유지의 지속 가능성'\n"
        "- '시간 압박 상황에서 판단이 흔들릴 가능성'\n"
        "- '권위적인 상사와 마찰이 생길 가능성'\n\n"
        "### 6. repeatability_questions (재현성 의문)\n"
        "이 행동이 다음에도 가능한지 의문을 제기하는 질문 형태 3개\n"
        "Q3 꼬리 질문으로 직접 사용됨\n"
        "예시:\n"
        "- '환경이 더 열악해도 같은 선택을 하실 건가요?'\n"
        "- '동료의 태도가 비협조적이어도 동일한 방식이 가능한가요?'\n"
        "- '시간이 촉박한 상황에서도 그렇게 하실 수 있나요?'\n"
        "- '상사가 반대해도 그렇게 하실 건가요?'\n\n"
        "## 출력 형식 (반드시 준수)\n"
        "```json\n"
        '{"items":[{"question":"문항요약","claim":"핵심주장","decision_criteria":["기준1","기준2"],"rejected_alternatives":["대안1","대안2"],"over_idealized_points":["이상적표현1","이상적표현2","이상적표현3","이상적표현4"],"risk_points":["취약점1","취약점2","취약점3"],"repeatability_questions":["재현성질문1","재현성질문2","재현성질문3"]}]}\n'
        "```\n\n"
        "## 중요 규칙\n"
        "1. 질문을 생성하지 마세요. 공격 포인트만 추출하세요.\n"
        "2. 긍정적인 평가를 하지 마세요. 의심만 하세요.\n"
        "3. 모든 필드를 반드시 채우세요. 빈 배열 금지.\n"
        "4. 자소서 원문의 표현을 최대한 활용하세요.\n"
        "5. over_idealized_points가 가장 중요합니다. 신중하게 찾으세요.\n\n"
        f"## 입력 (문항과 답변)\n{json.dumps({'items': items_payload}, ensure_ascii=False)}"
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _llm_post_chat_completions(api_key: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": messages,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
    r.raise_for_status()
    return r.json()


def _llm_parse_json_from_response(resp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        choices = resp.get("choices", [])
        if not choices:
            return None
        msg = (choices[0] or {}).get("message", {}) or {}
        content = msg.get("content", "")
        if not content:
            return None
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
        return None
    except Exception:
        return None


def _llm_validate_required_keys(parsed: Dict[str, Any]) -> bool:
    """
    LLM JSON 필수 키 검증 (새 공격 포인트 스키마용).
    claim은 문자열, 나머지(over_idealized_points, risk_points, repeatability_questions)는 리스트.
    """
    if not isinstance(parsed, dict):
        return False
    items = parsed.get("items", [])
    if not isinstance(items, list) or not items:
        return False
    for it in items:
        if not isinstance(it, dict):
            return False
        # claim은 문자열
        if "claim" not in it or not isinstance(it.get("claim"), str):
            return False
        # 나머지 핵심 필드는 리스트
        for key in ["over_idealized_points", "risk_points", "repeatability_questions"]:
            if key not in it:
                return False
            if not isinstance(it[key], list):
                return False
    return True


def _llm_extract_for_slot(llm_item: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """
    LLM item에서 특정 키 추출. 없으면 default 반환.
    """
    if not isinstance(llm_item, dict):
        return default
    val = llm_item.get(key, default)
    if val is None:
        return default
    return val


def _is_valid_experience(exp: str) -> bool:
    """
    경험이 유효한지 검증 - 최대한 관대하게 (거의 모든 것 통과)
    LLM이 추출한 것은 신뢰하고, 정말 심각한 오류만 제외
    """
    if not exp or not isinstance(exp, str):
        return False
    exp = exp.strip()
    # 빈 문자열만 제외
    if len(exp) < 1:
        return False
    # 나머지는 모두 통과 (LLM 추출 결과 신뢰)
    return True


def _is_valid_core_value(val: str) -> bool:
    """핵심 가치가 유효한지 검증 - 최대한 관대하게 (거의 모든 것 통과)"""
    if not val or not isinstance(val, str):
        return False
    val = val.strip()
    # 빈 문자열만 제외
    if len(val) < 1:
        return False
    # 나머지는 모두 통과 (LLM 추출 결과 신뢰)
    return True


def _llm_validate_and_sanitize_items(
    parsed: Dict[str, Any],
    qa_sets: List[Dict[str, str]]
) -> Tuple[List[Dict[str, Any]], int]:
    """
    LLM 추출 결과 검증 및 필터링 (새 공격 포인트 스키마용).
    - claim, decision_criteria, rejected_alternatives, over_idealized_points, risk_points, repeatability_questions 추출
    - 유효 추출 개수 반환
    """
    if not isinstance(parsed, dict):
        return [], 0
    items = parsed.get("items", [])
    if not isinstance(items, list):
        return [], 0

    out_items: List[Dict[str, Any]] = []
    total_valid = 0

    for idx, it in enumerate(items):
        if idx >= len(qa_sets or []):
            break
        qa = qa_sets[idx] or {}
        q_raw = qa.get("prompt", "") or ""
        if not isinstance(it, dict):
            it = {}

        # 새 스키마 필드 추출
        claim = it.get("claim", "")
        if not isinstance(claim, str):
            claim = ""

        decision_criteria = it.get("decision_criteria", [])
        if not isinstance(decision_criteria, list):
            decision_criteria = []
        decision_criteria = [c for c in decision_criteria if isinstance(c, str) and c.strip()]

        rejected_alternatives = it.get("rejected_alternatives", [])
        if not isinstance(rejected_alternatives, list):
            rejected_alternatives = []
        rejected_alternatives = [a for a in rejected_alternatives if isinstance(a, str) and a.strip()]

        over_idealized_points = it.get("over_idealized_points", [])
        if not isinstance(over_idealized_points, list):
            over_idealized_points = []
        over_idealized_points = [p for p in over_idealized_points if isinstance(p, str) and p.strip()]

        risk_points = it.get("risk_points", [])
        if not isinstance(risk_points, list):
            risk_points = []
        risk_points = [r for r in risk_points if isinstance(r, str) and r.strip()]

        repeatability_questions = it.get("repeatability_questions", [])
        if not isinstance(repeatability_questions, list):
            repeatability_questions = []
        repeatability_questions = [q for q in repeatability_questions if isinstance(q, str) and q.strip()]

        # 유효 개수 카운트 (핵심 공격 포인트들)
        if claim:
            total_valid += 1
        total_valid += len(over_idealized_points)
        total_valid += len(risk_points)
        total_valid += len(repeatability_questions)

        out_items.append({
            "question": q_raw if q_raw else "자기소개서",
            "claim": claim,
            "decision_criteria": decision_criteria,
            "rejected_alternatives": rejected_alternatives,
            "over_idealized_points": over_idealized_points,
            "risk_points": risk_points,
            "repeatability_questions": repeatability_questions,
        })

    # 부족한 아이템 채우기
    for j in range(len(out_items), len(qa_sets or [])):
        qa = qa_sets[j] or {}
        out_items.append({
            "question": (qa.get("prompt", "") or "").strip() or "자기소개서",
            "claim": "",
            "decision_criteria": [],
            "rejected_alternatives": [],
            "over_idealized_points": [],
            "risk_points": [],
            "repeatability_questions": [],
        })

    return out_items, total_valid


def _llm_try_extract_or_reuse(qa_sets: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
    """
    - STEP 3 진입 시점 1회 호출
    - 동일 해시는 COMPLETED면 재호출 금지
    - 실패 시 None 반환 (SRCAI 폴백)
    - COMPLETED에서만 사용량 커밋
    """
    _llm_gc()
    _ensure_llm_state_boxes()

    llm_hash = _calc_llm_hash_from_qa_sets(qa_sets)
    if not llm_hash:
        return None

    box = st.session_state.get("_llm_extract_box", {})
    if not isinstance(box, dict):
        box = {}

    rec = box.get(llm_hash)
    if isinstance(rec, dict):
        state = rec.get("state")
        ts = float(rec.get("ts", 0.0) or 0.0)
        if (
            state == LLM_STATE_COMPLETED
            and (time.time() - ts) <= LLM_TTL_SEC
            and isinstance(rec.get("data"), dict)
        ):
            return rec.get("data")
        if state == LLM_STATE_PENDING:
            return None

    if not _plan_can_run_llm():
        box[llm_hash] = {
            "state": LLM_STATE_ABORTED,
            "ts": _now_ts(),
            "data": None,
            "counted": False,
            "reason": "PLAN_LIMIT",
        }
        st.session_state._llm_extract_box = box
        return None

    box[llm_hash] = {
        "state": LLM_STATE_PENDING,
        "ts": _now_ts(),
        "data": None,
        "counted": False,
    }
    st.session_state._llm_extract_box = box

    api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_APIKEY")
        or os.getenv("OPENAI_KEY")
        or ""
    )
    if not api_key:
        box[llm_hash] = {
            "state": LLM_STATE_FAILED,
            "ts": _now_ts(),
            "data": None,
            "counted": False,
            "reason": "API 키가 설정되지 않았습니다. 다시 질문 생성 버튼을 눌러주세요.",
        }
        st.session_state._llm_extract_box = box
        return None

    try:
        messages = _llm_build_messages_for_extract(qa_sets)
        resp = _llm_post_chat_completions(api_key=api_key, messages=messages)
        parsed = _llm_parse_json_from_response(resp)

        if not parsed:
            box[llm_hash] = {
                "state": LLM_STATE_FAILED,
                "ts": _now_ts(),
                "data": None,
                "counted": False,
                "reason": "응답 파싱에 실패했습니다. 다시 질문 생성 버튼을 눌러주세요.",
            }
            st.session_state._llm_extract_box = box
            return None

        if not _llm_validate_required_keys(parsed):
            box[llm_hash] = {
                "state": LLM_STATE_FAILED,
                "ts": _now_ts(),
                "data": None,
                "counted": False,
                "reason": "응답 형식이 올바르지 않습니다. 다시 질문 생성 버튼을 눌러주세요.",
            }
            st.session_state._llm_extract_box = box
            return None

        validated_items, total_valid = _llm_validate_and_sanitize_items(parsed, qa_sets)

        # 추출 결과가 하나도 없으면 실패 처리
        if total_valid <= 0:
            box[llm_hash] = {
                "state": LLM_STATE_FAILED,
                "ts": _now_ts(),
                "data": None,
                "counted": False,
                "reason": "자소서에서 분석할 내용을 찾지 못했습니다. 다시 질문 생성 버튼을 눌러주세요.",
            }
            st.session_state._llm_extract_box = box
            return None

        # 성공: 추출 결과가 있음
        data = {
            "items": validated_items,
            "llm_hash": llm_hash,
            "ts": _now_ts(),
            "extraction_count": total_valid,
        }

        box[llm_hash] = {
            "state": LLM_STATE_COMPLETED,
            "ts": _now_ts(),
            "data": data,
            "counted": False,
        }
        st.session_state._llm_extract_box = box

        _plan_commit_usage_once(llm_hash)
        return data

    except Exception as e:
        box[llm_hash] = {
            "state": LLM_STATE_FAILED,
            "ts": _now_ts(),
            "data": None,
            "counted": False,
            "reason": f"분석 중 오류가 발생했습니다. 다시 질문 생성 버튼을 눌러주세요. ({type(e).__name__})",
        }
        st.session_state._llm_extract_box = box
        return None
