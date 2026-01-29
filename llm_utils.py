# llm_utils.py
# LLM 상태 관리, API 호출, JSON 파싱, 추출 로직

# LLM 프롬프트 버전 - 프롬프트 변경 시 버전 올려서 캐시 무효화
_LLM_PROMPT_VERSION = "v2_q2_topic_20260119"

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
    INTERVIEWER_TONE_RULES, KOREAN_QUESTION_RULES, ABSOLUTE_PROHIBITIONS,
)
from text_utils import normalize_ws
from analysis import _classify_prompt_type_kor
from extraction_verifier import verify_llm_extraction, two_stage_extraction
from logging_config import get_logger

logger = get_logger(__name__)


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
        except Exception as e:
            logger.warning(f"LLM GC timestamp parsing failed: {e}")
            ts = 0.0
        if (now - ts) > LLM_TTL_SEC:
            to_del.append(k)
    for k in to_del:
        try:
            del box[k]
        except Exception as e:
            logger.warning(f"LLM GC box deletion failed: {e}")
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
    프롬프트 버전도 포함하여 프롬프트 변경 시 캐시 무효화.
    """
    parts: List[str] = []
    # 프롬프트 버전 포함 (프롬프트 변경 시 캐시 무효화)
    parts.append(f"PROMPT_VERSION:{_LLM_PROMPT_VERSION}")
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

    # 시스템 프롬프트: 면접관 사고방식 + 패턴 매칭 강제
    system = (
        "너는 대한민국 항공사 실제 면접관 사고방식을 학습한 자소서 분석 전문 LLM이다. "
        "너의 사고 언어, 출력 언어, 내부 검증 언어는 모두 한국어다. "
        "영어로 사고하거나 영어 문장을 한국어로 번역하는 행위를 절대 금지한다. "
        "\n\n"
        "⚠️ 핵심 원칙: 너는 '분석'을 하지 않는다. '패턴 매칭 + 조합'만 한다.\n"
        "1. 자소서 문장을 읽고 아래 라벨 중 해당되는 것을 찾는다\n"
        "2. 아래 학습된 예시 패턴에서 가장 유사한 것을 선택한다\n"
        "3. 그 패턴의 interviewer_interpretation, probe_points를 조합해 Q2를 생성한다\n"
        "\n"
        "【문장 라벨 분류 체계】\n"
        "- CLAIM: 본인 주장 ('저는 ~한 사람입니다', '~를 중요하게 생각합니다')\n"
        "- ACTION: 실제 행동 ('~를 진행했습니다', '~를 제안했습니다')\n"
        "- RESULT: 결과 ('~를 달성했습니다', '~가 줄었습니다')\n"
        "- EVAL: 자기평가 ('~능력을 키웠습니다', '~를 배웠습니다')\n"
        "- RISK: 위험 발언 ('유연하게', '최대한', '규정보다 고객 우선')\n"
        "- EVADE: 회피 표현 ('예상치 못한 변수', '불가피하게', '갈등을 최소화')\n"
        "\n"
        "❗ 감상, 요약, 칭찬, 일반론은 절대 하지 않는다. "
        "❗ 핵심 문장은 반드시 자소서 원문 그대로 추출. 의미 압축, 재서술, 키워드화 절대 금지. "
        "너의 목표는 말을 잘하는 지원자를 찾는 것이 아니라, 사고 기준이 맞는 지원자를 걸러내는 것이다. "
        "JSON만 출력한다."
    )

    # 면접관 시점 분석 프롬프트 - 문항 이해 + 면접톤 + 한국어 규칙 통합
    user = (
        "# 면접관 시점 자소서 분석\n\n"
        "════════════════════════\n"
        "★★★ 가장 중요: 문항을 먼저 이해하라 ★★★\n"
        "════════════════════════\n\n"
        "【문항 이해 없이 답변만 분석하면 이상한 Q2가 나온다】\n"
        "❌ 나쁜 예: '다큐멘터리같은 제 삶은 한 장면'라고 하셨는데, 어떤 의미인지 궁금합니다.\n"
        "   → 문항이 '인생을 영화로 표현하면?'인데, 비유적 표현을 literal하게 공격함\n"
        "✅ 좋은 예: 인생을 다큐멘터리로 표현하셨는데, 실제로 가장 기억에 남는 '한 장면'은 무엇이었고, 그게 승무원 직무와 어떻게 연결되나요?\n"
        "   → 문항 의도(자기이해/표현력)를 파악하고, 직무 연결성을 검증\n\n"
        "────────────────────────\n"
        "[0. 문항 유형 분류 및 Q2 전략 - 가장 먼저 수행]\n"
        "────────────────────────\n\n"
        "【STEP 1: 문항 유형 분류】\n"
        "모든 분석 전에, 문항(질문)의 유형을 먼저 파악한다:\n\n"
        "① 경험 요구형: '~한 경험이 있나요?', '어떤 노력을 하고 있나요?'\n"
        "   → 면접관 의도: 실제 행동과 결과 검증\n"
        "   → Q2 전략: 주장의 구체성, 재현 가능성, 책임 소재 검증\n\n"
        "② 가치/태도형: '무엇이 중요하다고 생각하나요?', '어떤 가치관을 가지고 있나요?'\n"
        "   → 면접관 의도: 가치관이 회사/직무와 맞는지 확인\n"
        "   → Q2 전략: 가치관이 충돌할 때의 우선순위, 실제 적용 사례 검증\n\n"
        "③ 자기표현형: '자신을 ~로 표현하면?', '본인의 강점/약점은?', '영화/색깔/동물로 비유하면?'\n"
        "   → 면접관 의도: 자기이해 수준, 표현력, 직무 연결성 확인\n"
        "   → Q2 전략: 비유의 의미를 직무 상황에 연결, '실제로 그런 상황에서 어떻게?'\n"
        "   ⚠️ 비유적 표현을 문자 그대로 공격하지 말 것!\n\n"
        "④ 지원동기형: '왜 승무원이 되고 싶나요?', '왜 우리 항공사인가요?'\n"
        "   → 면접관 의도: 진정성, 직무 이해도, 회사 이해도 확인\n"
        "   → Q2 전략: 동기의 구체성, 다른 선택지 대비 이유, 현실적 각오 검증\n\n"
        "④ 상황대처형: '~한 상황이면 어떻게 하겠습니까?'\n"
        "   → 면접관 의도: 판단 기준, 우선순위, 규정 준수 여부 확인\n"
        "   → Q2 전략: 극단 상황으로 압박, 책임 소재 명확화\n\n"
        "【STEP 2: 문항 의도 명시】\n"
        "출력 JSON에 반드시 포함:\n"
        "- question_type: 위 5가지 중 하나\n"
        "- question_intent: 면접관이 이 문항으로 확인하고 싶은 것 (1문장)\n"
        "- q2_strategy: 이 문항 유형에 맞는 Q2 전략 (1문장)\n\n"
        "【STEP 3: 문항 맥락을 고려한 답변 분석】\n"
        "문항 유형에 따라 답변에서 찾아야 할 것이 다름:\n"
        "- 경험 요구형 → 구체적 행동, 결과, 책임 있는 주장\n"
        "- 자기표현형 → 비유의 의미, 직무 연결성, 자기이해 수준\n"
        "- 지원동기형 → 동기의 진정성, 회사/직무 이해도\n\n"
        "────────────────────────\n"
        "[1. 한국어 문법 절대 규칙]\n"
        "────────────────────────\n"
        "⚠️ 모든 문장은 한국어 원어민이 말로 사용하는 자연스러운 구어체여야 한다.\n"
        "영어식 사고, 번역체, 명사 나열형 문장은 즉시 폐기한다.\n\n"
        "【어색한 문장의 5가지 원인 - 모두 금지】\n"
        "1) 영어식 사고 → 한국어 번역\n"
        "   ❌ '지원자는 팀워크를 중요하게 생각하며, 이를 통해 문제를 해결했습니다'\n"
        "   ✅ '문제를 해결할 때, 팀워크를 가장 중요하게 생각했습니다'\n\n"
        "2) 조사 오남용/생략 (조사가 의미의 50% 결정)\n"
        "   ❌ '안전벨트 사인 켜져있는데' → ✅ '안전벨트 사인이 켜져있는데'\n"
        "   ❌ 'FSC랑 LCC 서비스 차이가' → ✅ 'FSC와 LCC의 서비스 차이가'\n"
        "   ❌ '콜벨이 네 개 울렸어요' → ✅ '콜벨 네 개가 울렸어요'\n\n"
        "3) 한 문장에 의도 2개 이상 금지\n"
        "   ❌ '그 경험에서 무엇을 느꼈고, 왜 그렇게 행동했으며, 결과는 무엇이었습니까?'\n"
        "   ✅ '그 상황에서 왜 그렇게 행동했습니까?' (결과는 꼬리 질문으로 분리)\n\n"
        "4) 명사 과다 사용 금지 (한국어는 동사 중심 언어)\n"
        "   ❌ '문제 해결에 대한 노력' → ✅ '문제를 해결하려고 노력했습니다'\n"
        "   ❌ '의사소통의 중요성 인식' → ✅ '의사소통이 중요하다고 느꼈습니다'\n\n"
        "5) 불필요한 추상어 금지\n"
        "   ❌ 전반적으로, 종합적으로, 다양한, 효율적인, 긍정적인\n"
        "   ✅ 구체적인 행동·상황·결과로 치환\n\n"
        "【한국어 기본 어순 공식】\n"
        "[배경/상황] → [행동] → [이유] → [결과/판단]\n"
        "❌ '저는 팀워크를 중요하게 생각해서 그 상황에서 그렇게 행동했습니다'\n"
        "✅ '그 상황에서 팀원들과 협력해야 한다고 판단했고, 그래서 그렇게 행동했습니다'\n\n"
        "【인용 형식】\n"
        "❌ '~고 하세요. 뭐라고 할 거예요?' → ✅ '~라고 하시면, 어떻게 하시겠어요?'\n\n"
        "【출력 전 체크리스트 - 하나라도 NO면 다시 생성】\n"
        "□ 이 문장을 사람이 실제로 말할 수 있는가?\n"
        "□ 번역한 흔적이 있는가?\n"
        "□ 조사 하나라도 이상하지 않은가?\n"
        "□ 질문 의도가 하나인가?\n\n"
        "────────────────────────\n"
        "[1. 핵심 추출 규칙 - 가장 중요]\n"
        "────────────────────────\n"
        "**claim과 over_idealized_points는 반드시 자소서 원문을 그대로 복사!**\n\n"
        "⚠️ 핵심문장 = 완전한 문장이어야 함\n"
        "- 반드시 '~습니다', '~했다', '~입니다', '~있습니다' 등으로 끝나는 완전한 문장\n"
        "- 주어 + 서술어가 있는 문장만 추출\n"
        "- 면접관이 '왜 그렇게 생각하세요?' 라고 물을 수 있는 문장만 추출\n\n"
        "✅ 올바른 추출 (완전한 문장):\n"
        "- '저는 팀원들과 소통하며 문제를 해결했습니다'\n"
        "- '고객의 입장에서 생각하는 것이 가장 중요하다고 생각합니다'\n"
        "- '어떤 상황에서도 긍정적인 태도를 유지하려고 노력합니다'\n\n"
        "❌ 틀린 추출 (불완전한 조각 - 절대 금지):\n"
        "- '따뜻한 미소와 승객분들을 향한' ← 문장이 아님, 조각임\n"
        "- '소통으로 문제 해결' ← 요약됨\n"
        "- '팀워크 중시' ← 명사구임\n"
        "- '긍정적인 태도' ← 문장이 아님\n"
        "- '~를 위해', '~을 통해' 로 끝나는 것 ← 불완전\n\n"
        "**체크: 문장 끝이 '~다', '~요' 로 끝나는가? 아니면 폐기!**\n\n"
        "────────────────────────\n"
        "[2. 추출 대상 6가지]\n"
        "────────────────────────\n\n"
        "### claim (핵심 주장) - 원문 필수\n"
        "지원자가 자신을 설명하는 문장 1개를 원문 그대로 복사\n"
        "예시:\n"
        "- '저는 어떤 상황에서도 긍정적인 에너지를 유지하는 사람입니다'\n"
        "- '고객의 입장에서 생각하는 것을 가장 중요시합니다'\n\n"
        "### q2_topic (Q2용 핵심 주제) - ⭐매우 중요⭐\n"
        "claim에서 Q2 질문에 넣을 '핵심 주제 명사구'만 추출 (5~20자)\n"
        "- claim이 '승무원의 따뜻한 미소와 배려에 감명받아 승무원이 되기로 결심했습니다'\n"
        "  → q2_topic: '승무원의 따뜻한 미소와 배려'\n"
        "- claim이 '팀원들과 소통하며 갈등을 해결한 경험이 있습니다'\n"
        "  → q2_topic: '팀원들과의 갈등 해결 경험'\n"
        "- claim이 '고객의 입장에서 생각하는 것을 가장 중요시합니다'\n"
        "  → q2_topic: '고객 입장에서 생각하는 것'\n\n"
        "⚠️ q2_topic 규칙:\n"
        "- 동사 어미(~했습니다, ~입니다) 제거\n"
        "- 주제의 핵심만 명사구로 추출\n"
        "- Q2 질문 템플릿: \"'{q2_topic}'에 대해 말씀하셨는데, 구체적으로...\"\n"
        "- 이 템플릿에 자연스럽게 들어가야 함\n\n"
        "### decision_criteria (판단 기준)\n"
        "지원자가 선택/행동할 때 사용한 기준 2개 (추론 가능)\n\n"
        "### rejected_alternatives (선택 안 한 대안)\n"
        "지원자가 선택하지 않은 방법 2개\n\n"
        "### over_idealized_points (이상적 표현) - ⭐가장 중요 - 원문 필수\n"
        "자소서에서 너무 이상적/추상적인 **완전한 문장** 4개 이상을 원문 그대로 복사\n"
        "면접관은 이 문장들로 공격한다.\n\n"
        "⚠️ 반드시 완전한 문장만 추출 (조각/명사구 금지)\n"
        "- '~습니다', '~했다', '~입니다'로 끝나야 함\n"
        "- 면접관이 '정말요? 구체적으로요?' 라고 물을 수 있어야 함\n\n"
        "추출 대상 문장 패턴 (완전한 문장만):\n"
        "1. '저는 ~하는 사람입니다' 등 자기평가 문장\n"
        "2. '~를 통해 ~를 배웠습니다' 등 교훈 문장\n"
        "3. '~를 해결했습니다/극복했습니다' 등 결과 문장\n"
        "4. '~가 중요하다고 생각합니다' 등 가치관 문장\n"
        "5. '항상/언제나 ~하려고 노력합니다' 등 태도 문장\n\n"
        "❌ 이런 건 추출 금지:\n"
        "- '따뜻한 미소와 승객분들을 향한' ← 문장 아님\n"
        "- '고객 중심의 서비스 마인드' ← 명사구\n"
        "- '팀워크와 소통 능력' ← 명사 나열\n\n"
        "### risk_points (취약점)\n"
        "이 판단이 문제될 수 있는 상황 3개 (생성 가능)\n\n"
        "### deep_questions (심층 면접 질문) - ⭐⭐⭐ 가장 중요 ⭐⭐⭐\n"
        "자소서 핵심문장을 기반으로 심층 면접 질문을 생성한다.\n"
        "⚠️ 반드시 3개를 생성해야 함! (1개나 2개는 절대 안됨, 무조건 3개!)\n"
        "⚠️ 각 질문은 서로 다른 핵심문장을 기반으로 해야 함!\n\n"
        "【핵심문장 유형 분류 (5가지)】\n"
        "1. 가치선언: 본인의 가치관/신념 선언 ('팀워크가 제일 중요하다고 생각합니다')\n"
        "2. 경험제시: 구체적 경험 언급 ('16살에 혼자 중국으로 유학을 갔습니다')\n"
        "3. 깨달음: 경험에서 얻은 교훈 ('공동체 속에서 함께 있으니 극복할 수 있었습니다')\n"
        "4. 실천사례: 실제로 한 행동 ('함께 웃으면서 할 수 있는 환경을 조성했습니다')\n"
        "5. 개념사용: 특정 개념/용어 사용 ('팀컬러라는 것이 존재합니다')\n\n"
        "【유형별 질문 전략】\n"
        "- 가치선언 → 반례 상황 제시: '그렇게 생각하신다면, [반례 상황]에서도 같은 생각이십니까?'\n"
        "- 경험제시 → 구체화 요구: '그때 구체적으로 어떤 상황이었고, 본인은 어떻게 했습니까?'\n"
        "- 깨달음 → 역방향 질문: '덕분에 극복했다고 하셨는데, 반대로 본인이 기여한 건 뭐였습니까?'\n"
        "- 실천사례 → 한계 탐색: '그 방식이 통하지 않는 상황은요? 그래도 같은 방식을 고수합니까?'\n"
        "- 개념사용 → 정의 확인: '그게 정확히 무슨 의미입니까? 구체적인 예를 들어주세요.'\n\n"
        "【날카로운 질문의 필수 요소】 ⚠️ 반드시 지켜야 함!\n"
        "1. 핵심문장을 정면으로 공격 (모순/한계/진정성 의심)\n"
        "2. 불편한 질문 던지기 (지원자가 '헉' 할 정도로)\n"
        "3. 구체적 상황으로 몰아붙이기\n\n"
        "【'헉' 질문 유형 5가지】\n"
        "① 수혜자 vs 기여자: '도움 받았다는 얘기가 많은데, 본인이 누군가에게 없어서는 안 될 존재였던 적 있습니까?'\n"
        "② 모순 공격: '팀워크가 중요하다면서, 팀워크 때문에 본인이 손해 본 적은 없습니까?'\n"
        "③ 불편한 진실: '16살에 혼자 중국 유학 간 건 본인 선택입니까, 부모님 결정입니까?'\n"
        "④ 한계 시험: '함께 웃는 환경을 만들었다는데, 경기에서 계속 지는데 웃을 수 있습니까?'\n"
        "⑤ 진정성 검증: '따뜻하게 맞이받아서 따뜻하게 맞이하고 싶다는 건, 직업 선택 이유로 충분합니까?'\n\n"
        "【실제 날카로운 질문 예시 20개】\n"
        "- '자소서 전체를 보면 도움 받았다는 표현이 많은데, 본인이 누군가에게 없어서는 안 될 존재였던 적 있습니까?'\n"
        "- '팀워크가 제일 중요하다고 하셨는데, 팀워크 때문에 본인이 손해 본 경험은 없습니까? 있다면 그래도 팀워크가 중요합니까?'\n"
        "- '축구 동아리 주장인데 강팀보다 함께 웃는 팀을 선택하셨잖아요. 이기고 싶다는 팀원과 갈등은 없었습니까?'\n"
        "- '혼자였으면 절대 극복 못 했다고 하셨는데, 그럼 본인은 혼자서는 뭘 못 하는 사람입니까?'\n"
        "- '향수병을 극복했다고 하셨는데, 지금도 가끔 외로울 때 그때처럼 힘드십니까? 완전히 극복한 겁니까?'\n"
        "- '함께 웃는 환경을 조성했다고 하셨는데, 그 환경에서 빠진 사람은 없었습니까?'\n"
        "- '다큐멘터리는 있는 그대로를 찍는 장르인데, 본인 인생에서 편집하고 싶은 장면은 없습니까?'\n"
        "- '중학생 때부터 승무원이 꿈이라면서, 그 이후로 한 번도 다른 꿈을 가진 적 없습니까? 10년 넘게요?'\n"
        "- '승무원의 미소와 배려가 기억난다고 하셨는데, 불친절했던 승무원 경험은 없습니까? 있다면 왜 안 쓰셨습니까?'\n"
        "- '작은 선택들이 쌓여서 지금의 나라고 하셨는데, 그중 가장 후회되는 선택은 뭡니까?'\n\n"
        "【꼬리질문 예시】\n"
        "- '대화로 해결하겠습니다' → '그 대화를 세 번 했는데 안 바뀌면요? 네 번째도 대화합니까?'\n"
        "- '제가 먼저 맞추겠습니다' → '그러다 본인이 지치면요? 지쳐서 서비스 품질 떨어지면 누구 책임입니까?'\n"
        "- '부모님께 전화했습니다' → '부모님이 그러면 돌아와라 하셨으면 돌아왔습니까?'\n"
        "- '친구들과 함께 극복했습니다' → '그 친구들 지금도 연락합니까? 언제 마지막으로 연락했습니까?'\n"
        "- '따뜻하게 맞이하겠습니다' → '근데 승객이 본인한테 차갑게 대하면요? 그래도 따뜻합니까?'\n\n"
        "【예상 답변 + 꼬리질문】\n"
        "각 deep_question에 대해 예상되는 답변 3가지와 각각의 꼬리질문을 준비한다.\n"
        "예시:\n"
        "Q2: '팀워크가 안 되는 동료와 비행해야 한다면 어떻게 하시겠습니까?'\n"
        "- 예상답변1: '대화로 풀겠습니다' → 꼬리: '대화해도 안 바뀌면요?'\n"
        "- 예상답변2: '제가 먼저 맞추겠습니다' → 꼬리: '계속 맞추기만 하면 본인은 지치지 않습니까?'\n"
        "- 예상답변3: '업무와 감정을 분리하겠습니다' → 꼬리: '감정 분리가 진짜 되십니까? 안 됐던 적은요?'\n\n"
        "────────────────────────\n"
        "[3. 추가 추출: 핵심 키워드와 근거 문장]\n"
        "────────────────────────\n\n"
        "### key_keywords (핵심 키워드)\n"
        "자소서에서 지원자의 강점/특성을 나타내는 핵심 단어 3~5개\n"
        "- 반드시 자소서에 등장하는 단어여야 함\n"
        "- 예시: '소통', '책임감', '팀워크', '고객 중심', '문제 해결'\n\n"
        "### evidence_sentences (근거 문장)\n"
        "핵심 키워드를 뒷받침하는 구체적 행동/결과 문장 3~5개\n"
        "- 반드시 자소서 원문 그대로 복사\n"
        "- '~했습니다', '~했다' 등 구체적 행동이 드러나는 문장\n"
        "- 예시:\n"
        "  - '매일 아침 30분씩 팀원들과 미팅을 진행했습니다'\n"
        "  - '고객 불만 건수를 30% 줄이는 성과를 달성했습니다'\n"
        "  - '갈등 상황에서 양측의 의견을 먼저 들었습니다'\n\n"
        "────────────────────────\n"
        "[4. Q2 질문 생성 규칙 - 패턴 매칭 기반]\n"
        "────────────────────────\n\n"
        "⚠️ Q2 생성 프로세스 (LLM은 이 순서대로만 생성):\n"
        "1. 자소서 문장에서 라벨 분류 (CLAIM/EVADE/RISK/EVAL/ACTION/RESULT)\n"
        "2. 위 학습된 패턴 8개 중 가장 유사한 패턴 선택\n"
        "3. 선택한 패턴의 '파고들 포인트'와 '좋은 Q2' 구조를 참고\n"
        "4. 자소서 원문의 구체적 단어를 넣어 Q2 조합\n"
        "→ LLM은 '창작'이 아니라 '조합'만 한다!\n\n"
        "⚠️ Q2 질문 절대 규칙:\n"
        "- 반드시 가정·판단·책임·충돌 중 최소 2개 이상 포함\n"
        "- '어땠나요 / 왜 중요한가요 / 느낀 점' 유형 질문 금지\n"
        "- 가치 동의 질문 금지 ('중요하다고 생각하시죠?' ❌)\n"
        "- 규정·안전·회사 기준을 벗어나는 답변은 위험 신호\n"
        "- 자소서에 없는 상황을 가정하지 마라 (원문 근거 필수)\n\n"
        "【Q2 질문 공격 구조 4가지】\n"
        "① 가정 붕괴형:\n"
        "   '만약 [자소서에서 언급한 조건]이 깨졌다면도 같은 선택을 했을까요?'\n"
        "   '그 상황이 한 번 더 반복된다면 동일한 판단을 할 수 있나요?'\n\n"
        "② 책임 전가 차단형:\n"
        "   '그 결과가 좋지 않았다면, 그 책임은 누구에게 있다고 보시나요?'\n"
        "   '본인의 판단으로 상황이 더 악화될 가능성은 없었나요?'\n\n"
        "③ 극단 상황 압박형:\n"
        "   '시간이 지금의 절반밖에 없었다면 어떤 선택을 했을까요?'\n"
        "   '상사의 지시가 본인 판단과 정반대였다면 어떻게 했을까요?'\n\n"
        "④ 직무 전이 검증형 (항공사 면접 핵심):\n"
        "   '이 경험이 실제 기내 클레임 상황에서도 그대로 적용될 수 있을까요?'\n"
        "   '승객 안전과 감정 중 하나만 선택해야 한다면 어떻게 판단하시겠어요?'\n\n"
        "【나쁜 Q2 패턴 - 절대 생성 금지】\n"
        "❌ '팀워크가 중요하다고 생각하시나요?' → 가치 동의 질문\n"
        "❌ '갈등 해결 경험이 있네요, 어땠나요?' → 감상 유도형\n"
        "❌ '리더십이 중요하다고 생각하시나요?' → 동의 유도형\n"
        "❌ '고객 응대는 힘들지 않았나요?' → 감상 질문\n"
        "❌ '유연성이 본인 장점인가요?' → 자기평가 유도\n"
        "❌ '배려심이 많으신 편인가요?' → 성향 확인\n"
        "❌ '성장하셨군요. 기분이 어떠셨어요?' → 감상 유도\n"
        "❌ '자세히 설명해 주세요.' → 설명 요청 (압박 없음)\n\n"
        "────────────────────────\n"
        "[5. 학습된 패턴 예시 - 이 패턴에서 선택하라]\n"
        "────────────────────────\n\n"
        "【패턴 1: 협업/중재 주장 - CLAIM+EVADE】\n"
        "원문: '팀 프로젝트 중 일정 지연으로 팀원 간 갈등이 발생했지만, 저는 중간에서 각자의 의견을 정리하고 대안을 제시해 프로젝트를 마무리할 수 있었습니다.'\n"
        "라벨: [CLAIM, EVADE]\n"
        "면접관 해석:\n"
        "- 갈등의 구체 내용과 강도가 빠져 있어 실제 난이도가 낮았을 수 있다\n"
        "- '중간에서 정리'가 실제로는 회피적 중재(결정 미룸)일 수 있다\n"
        "- 대안 제시가 본인 주도인지 합의 결과인지 불명확하다\n"
        "파고들 포인트: 소통 안 되는 상황/본인 판단 기준/결과 나쁠 때 책임\n"
        "✅ 좋은 Q2: '팀원 중 한 명이 끝까지 대안을 거부했다면, 그 상황에서도 같은 방식으로 해결할 수 있었을까요?'\n"
        "❌ 나쁜 Q2: '팀워크가 중요하다고 생각하시나요?' (가치 동의 질문 - 검증 불가)\n\n"
        "【패턴 2: 리더십 주장 - CLAIM】\n"
        "원문: '동아리 회장으로서 팀 분위기와 성과를 동시에 관리했습니다.'\n"
        "라벨: [CLAIM]\n"
        "면접관 해석:\n"
        "- '동시에'라는 단어는 검증 대상이며 충돌 상황이 반드시 있었을 가능성이 높다\n"
        "- 의견 수렴이 결단 회피로 보일 위험이 있다\n"
        "파고들 포인트: 성과-분위기 충돌 순간/팀원 반발 결정/실패한 판단\n"
        "✅ 좋은 Q2: '분위기를 위해 성과를 포기해야 했던 순간이 있었다면, 그때도 같은 선택을 했을까요?'\n"
        "❌ 나쁜 Q2: '리더십이 중요하다고 생각하시나요?' (동의 유도형)\n\n"
        "【패턴 3: 고객응대 주장 - CLAIM+EVADE】\n"
        "원문: '고객 응대 아르바이트를 하며 다양한 고객을 응대했고, 문제 상황에서도 침착하게 해결했습니다.'\n"
        "라벨: [CLAIM, EVADE]\n"
        "면접관 해석:\n"
        "- '다양한 고객/문제 상황'이 추상적이라 실제 난이도가 검증되지 않는다\n"
        "- 침착은 태도 표현일 뿐 실제 조치(행동)가 빠져 있다\n"
        "파고들 포인트: 가장 어려운 클레임 유형/시간 압박 시 첫 행동/규정과 고객 충돌\n"
        "✅ 좋은 Q2: '가장 감정적으로 힘들었던 고객 유형은 무엇이었고, 그때 침착이 유지됐나요? 깨졌다면 어떻게 회복했나요?'\n"
        "❌ 나쁜 Q2: '고객 응대는 힘들지 않았나요?' (감상 질문)\n\n"
        "【패턴 4: 책임전가 표현 - CLAIM+EVADE+RISK】\n"
        "원문: '예상치 못한 변수로 계획에 차질이 발생했지만, 유연하게 대처하여 일정을 맞췄습니다.'\n"
        "라벨: [CLAIM, EVADE, RISK]\n"
        "면접관 해석:\n"
        "- '변수'는 책임 전가에 자주 쓰이는 표현이며 통제 실패를 숨길 수 있다\n"
        "- '유연하게'는 규정/기준 없이 즉흥 대응으로 해석될 위험이 있다\n"
        "파고들 포인트: 변수 예상 못한 이유/유연 대응의 한계선/재발 시 예방\n"
        "✅ 좋은 Q2: '그 변수를 사전에 예상하지 못한 이유는 무엇이고, 지금이라면 어떤 지표로 미리 감지할 수 있을까요?'\n"
        "❌ 나쁜 Q2: '유연성이 본인 장점인가요?' (자기평가 유도)\n\n"
        "【패턴 5: 고객만족 위험발언 - RISK+CLAIM】\n"
        "원문: '고객 만족을 위해 최대한 유연하게 대응하려 노력했습니다.'\n"
        "라벨: [RISK, CLAIM]\n"
        "면접관 해석:\n"
        "- 항공사 면접에서 '유연함'은 규정/안전과 충돌 시 위험 발언이 될 수 있다\n"
        "- 경청/설득은 좋지만 '어디까지 가능한지' 기준이 없으면 부적합하다\n"
        "파고들 포인트: 규정과 고객 충돌 순간/불가 통보 방식/안전 우선순위\n"
        "✅ 좋은 Q2: '고객 요구가 규정이나 안전 기준과 충돌했을 때도 유연하게 대응하실 건가요? 본인이 지킬 선은 어디까지인가요?'\n"
        "❌ 나쁜 Q2: '고객 만족이 왜 중요하다고 생각하나요?' (일반론 유도)\n\n"
        "【패턴 6: 미사여구 문장 - CLAIM+EVAL+EVADE】\n"
        "원문: '저는 항상 상대방의 입장에서 생각하며 갈등을 최소화하려 노력해왔습니다.'\n"
        "라벨: [CLAIM, EVAL, EVADE]\n"
        "면접관 해석:\n"
        "- 미사여구 문장으로 실제 사건/행동이 없다\n"
        "- '항상'은 과장 신호이며 반례 검증이 필요하다\n"
        "파고들 포인트: 갈등 해결 안 된 사례/상대 요구가 부당했을 때/회사 기준과 배려 충돌\n"
        "✅ 좋은 Q2: '상대방 입장을 이해했음에도 갈등이 해결되지 않았던 경험이 있다면, 그때는 어떻게 정리하셨나요?'\n"
        "❌ 나쁜 Q2: '배려심이 많으신 편인가요?' (성향 확인)\n\n"
        "【패턴 7: 검증불가 자기평가 - EVAL+EVADE】\n"
        "원문: '문제 해결 능력을 크게 향상시킬 수 있었습니다.'\n"
        "라벨: [EVAL, EVADE]\n"
        "면접관 해석:\n"
        "- 자기평가 문장으로 검증 불가\n"
        "- 전/후 비교가 없으면 성장 서사 조작으로 보일 수 있다\n"
        "파고들 포인트: 전과 후의 행동/기준 변화/실패 경험/한계 인식\n"
        "✅ 좋은 Q2: '향상됐다고 느낀 근거가 무엇인가요? 이전에는 어떻게 했고, 지금은 무엇이 달라졌나요?'\n"
        "❌ 나쁜 Q2: '성장하셨군요. 기분이 어떠셨어요?' (감상 유도)\n\n"
        "【패턴 8: 실질적 행동+결과 - ACTION+RESULT】\n"
        "원문: '바쁜 시간대에도 실수를 줄이기 위해 체크리스트를 만들어 업무 정확도를 높였습니다. 그 결과 컴플레인이 줄었습니다.'\n"
        "라벨: [ACTION, RESULT]\n"
        "면접관 해석:\n"
        "- 현장형 개선 시도는 강점이지만 '어떤 실수'와 '어떤 체크'인지가 핵심이다\n"
        "- 컴플레인 감소가 체크리스트 덕분인지 외부 요인인지 분리 검증 필요\n"
        "파고들 포인트: 가장 치명적 실수 유형/시간 압박 시 체크 우선순위/체크리스트 실패 상황\n"
        "✅ 좋은 Q2: '시간이 너무 촉박해서 체크를 다 못 한다면, 무엇부터 확인하고 무엇을 포기하시겠어요?'\n"
        "❌ 나쁜 Q2: '체크리스트를 잘 만드셨네요. 자세히 설명해 주세요.' (설명 요청 - 압박 없음)\n\n"
        "────────────────────────\n"
        "[6. 면접관 실제 해석 패턴 (추가 학습용)]\n"
        "────────────────────────\n\n"
        "【해석 예시 1 — 협업 미사여구】\n"
        "원문: '팀원들과 원활하게 소통하며 갈등을 조정해 프로젝트를 성공적으로 마무리했습니다.'\n"
        "면접관 실제 해석:\n"
        "- 갈등의 강도 낮음 또는 없음\n"
        "- 본인이 실제로 불편한 선택을 했는지 불명확\n"
        "- '조정'이라는 단어로 책임 회피 가능성 있음\n"
        "검증 리스크: 어려운 상황을 피해 갔을 가능성 / 중재자 역할을 했다는 착각\n"
        "파고들 포인트: 갈등이 깨졌을 때 / 소통이 통하지 않을 때 / 본인 판단으로 누군가 손해를 봤는지\n\n"
        "【해석 예시 2 — 리더십 과대포장】\n"
        "원문: '동아리 회장으로서 팀 분위기와 성과를 동시에 관리했습니다.'\n"
        "면접관 실제 해석:\n"
        "- 성과가 떨어졌을 가능성 숨김\n"
        "- 분위기를 명분으로 결단 회피했을 가능성\n"
        "- '동시에'라는 표현은 검증 대상\n"
        "검증 리스크: 인기 위주의 리더십 / 갈등 회피형 리더\n"
        "파고들 포인트: 분위기 vs 성과 충돌 순간 / 반대 의견을 억누른 경험 / 실패한 결정\n\n"
        "【해석 예시 3 — 책임 회피 문장】\n"
        "원문: '예상치 못한 변수로 인해 계획에 차질이 발생했습니다.'\n"
        "면접관 실제 해석:\n"
        "- 변수 = 본인 통제 실패일 가능성\n"
        "- 책임을 상황에 전가\n"
        "검증 리스크: 책임 인식 부족 / 판단 기준 부재\n"
        "파고들 포인트: 본인 판단으로 줄일 수 있었는지 / 그 변수를 예상하지 못한 이유 / 동일 상황 재발 시 대처\n\n"
        "【해석 예시 4 — 고객 중심 위험 발언 (항공사 핵심)】\n"
        "원문: '고객 만족을 위해 최대한 유연하게 대응하려 노력했습니다.'\n"
        "면접관 실제 해석:\n"
        "- 규정 위반 가능성\n"
        "- 고객 편향 사고\n"
        "검증 리스크: 안전·규정 경시 / 회사 기준 미흡\n"
        "파고들 포인트: 규정과 충돌한 사례 / 어디까지가 허용 범위인지 / 선을 넘지 않은 이유\n\n"
        "【해석 예시 5 — 성과 과장】\n"
        "원문: '그 경험을 통해 문제 해결 능력을 크게 향상시킬 수 있었습니다.'\n"
        "면접관 실제 해석:\n"
        "- 결과가 아니라 자기평가\n"
        "- 검증 불가 문장\n"
        "검증 리스크: 성장 서사 조작 / 실질 변화 없음\n"
        "파고들 포인트: 이전과 이후의 구체적 차이 / 실패 경험 포함 여부 / 한계 인식\n\n"
        "────────────────────────\n"
        "[7. 출력 형식]\n"
        "────────────────────────\n"
        "```json\n"
        "{\n"
        '  "items": [\n'
        '    {\n'
        '      "question": "문항 원문 그대로",\n'
        '      "question_type": "경험요구형|가치태도형|자기표현형|지원동기형|상황대처형 중 하나",\n'
        '      "question_intent": "면접관이 이 문항으로 확인하고 싶은 것 (1문장)",\n'
        '      "q2_strategy": "이 문항 유형에 맞는 Q2 전략 (1문장)",\n'
        '      "claim": "원문 그대로 (15자 이상 완전한 문장)",\n'
        '      "q2_topic": "claim에서 추출한 핵심 주제 명사구 (5~20자)",\n'
        '      "sentence_labels": [\n'
        '        {"sentence": "추출한 문장 원문", "labels": ["CLAIM", "EVADE"]}\n'
        '      ],\n'
        '      "matched_pattern": "패턴1~8 중 가장 유사한 번호",\n'
        '      "interviewer_interpretation": ["면접관이 의심하는 점1", "면접관이 의심하는 점2"],\n'
        '      "decision_criteria": ["판단기준1", "판단기준2"],\n'
        '      "rejected_alternatives": ["선택 안 한 대안1", "선택 안 한 대안2"],\n'
        '      "over_idealized_points": ["완전한 문장 원문1", "완전한 문장 원문2", "완전한 문장 원문3"],\n'
        '      "risk_points": ["취약점1", "취약점2", "취약점3"],\n'
        '      "probe_points": ["파고들 포인트1", "파고들 포인트2"],\n'
        '      "repeatability_questions": ["기존 Q2질문1", "Q2질문2", "Q2질문3"],\n'
        '      "deep_questions": [\n'
        '        {\n'
        '          "source_sentence": "핵심문장1 (자소서 원문 그대로)",\n'
        '          "sentence_type": "가치선언",\n'
        '          "question": "심층질문1 (핵심문장 인용 + 반례 상황 + 어떻게 하시겠습니까?)",\n'
        '          "expected_answers": [\n'
        '            {"answer": "예상답변1-1", "followup": "꼬리질문1-1"},\n'
        '            {"answer": "예상답변1-2", "followup": "꼬리질문1-2"},\n'
        '            {"answer": "예상답변1-3", "followup": "꼬리질문1-3"}\n'
        '          ]\n'
        '        },\n'
        '        {\n'
        '          "source_sentence": "핵심문장2 (자소서 원문 그대로)",\n'
        '          "sentence_type": "경험제시",\n'
        '          "question": "심층질문2 (핵심문장 인용 + 반례 상황 + 어떻게 하시겠습니까?)",\n'
        '          "expected_answers": [\n'
        '            {"answer": "예상답변2-1", "followup": "꼬리질문2-1"},\n'
        '            {"answer": "예상답변2-2", "followup": "꼬리질문2-2"},\n'
        '            {"answer": "예상답변2-3", "followup": "꼬리질문2-3"}\n'
        '          ]\n'
        '        },\n'
        '        {\n'
        '          "source_sentence": "핵심문장3 (자소서 원문 그대로)",\n'
        '          "sentence_type": "깨달음",\n'
        '          "question": "심층질문3 (핵심문장 인용 + 반례 상황 + 어떻게 하시겠습니까?)",\n'
        '          "expected_answers": [\n'
        '            {"answer": "예상답변3-1", "followup": "꼬리질문3-1"},\n'
        '            {"answer": "예상답변3-2", "followup": "꼬리질문3-2"},\n'
        '            {"answer": "예상답변3-3", "followup": "꼬리질문3-3"}\n'
        '          ]\n'
        '        }\n'
        '      ],\n'
        '      "key_keywords": ["키워드1", "키워드2", "키워드3"],\n'
        '      "evidence_sentences": ["근거문장1", "근거문장2", "근거문장3"]\n'
        '    }\n'
        '  ]\n'
        "}\n"
        "```\n\n"
        "────────────────────────\n"
        "[8. 최종 검증 체크리스트]\n"
        "────────────────────────\n"
        "★ 문항 이해 (가장 중요)\n"
        "□ question_type - 문항 유형이 5가지 중 하나로 정확히 분류되었는가?\n"
        "□ question_intent - 면접관 의도가 문항 유형에 맞게 파악되었는가?\n"
        "□ q2_strategy - Q2 전략이 문항 유형에 적합한가?\n"
        "□ repeatability_questions(Q2) - 문항 유형에 맞는 Q2인가?\n"
        "   - 자기표현형 문항에 literal한 공격 질문 ❌\n"
        "   - 경험요구형 문항에 추상적 감상 질문 ❌\n\n"
        "★ 문장 추출\n"
        "□ claim - 완전한 문장인가? (~습니다/~입니다/~했다 로 끝나는가?)\n"
        "□ claim - 자소서 원문 그대로인가? (15자 이상)\n"
        "□ over_idealized_points - 모두 완전한 문장인가? (조각/명사구 금지!)\n"
        "□ over_idealized_points - '~를 향한', '~를 위해', '~한 장면' 같은 불완전 조각 없는가?\n"
        "□ evidence_sentences - 구체적 행동/결과가 있는 원문인가?\n\n"
        "★ Q2 품질 (deep_questions 중심)\n"
        "□ deep_questions - 핵심문장을 직접 인용하고 있는가?\n"
        "□ deep_questions - 구체적인 반례/압박 상황이 설정되어 있는가?\n"
        "□ deep_questions - '어떻게 하시겠습니까?' 등 구체적 답변을 요구하는가?\n"
        "□ deep_questions - 예상답변 3개와 각각의 꼬리질문이 있는가?\n"
        "□ 번역투/요약 표현이 없는가?\n\n"
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
    except Exception as e:
        logger.warning(f"LLM response JSON parsing failed: {e}")
        return None


def _llm_validate_required_keys(parsed: Dict[str, Any]) -> bool:
    """
    LLM JSON 필수 키 검증 (새 deep_questions 스키마 지원).
    deep_questions 또는 기존 필드(over_idealized_points, risk_points) 중 하나라도 있으면 통과.
    """
    if not isinstance(parsed, dict):
        return False
    items = parsed.get("items", [])
    if not isinstance(items, list) or not items:
        return False
    for it in items:
        if not isinstance(it, dict):
            return False
        # 새 방식(deep_questions) 또는 기존 방식(over_idealized_points) 중 하나라도 있으면 OK
        has_deep_questions = isinstance(it.get("deep_questions"), list) and len(it.get("deep_questions", [])) > 0
        has_old_style = isinstance(it.get("over_idealized_points"), list) and len(it.get("over_idealized_points", [])) > 0
        # 둘 다 없어도 claim만 있으면 통과 (폴백 사용 가능)
        has_claim = isinstance(it.get("claim"), str) and len(it.get("claim", "").strip()) > 0
        if not (has_deep_questions or has_old_style or has_claim):
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

        # 문항 이해 필드 추출 (새로 추가)
        question_type = it.get("question_type", "")
        if not isinstance(question_type, str):
            question_type = ""
        question_type = question_type.strip()

        question_intent = it.get("question_intent", "")
        if not isinstance(question_intent, str):
            question_intent = ""
        question_intent = question_intent.strip()

        q2_strategy = it.get("q2_strategy", "")
        if not isinstance(q2_strategy, str):
            q2_strategy = ""
        q2_strategy = q2_strategy.strip()

        # 새 스키마 필드 추출
        claim = it.get("claim", "")
        if not isinstance(claim, str):
            claim = ""
        # claim도 최소 길이 체크 (너무 짧으면 요약된 것)
        if len(claim.strip()) < 10:
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
        # 최소 10자 이상인 문장만 유효 (요약된 짧은 문장 제외)
        over_idealized_points = [
            p for p in over_idealized_points
            if isinstance(p, str) and p.strip() and len(p.strip()) >= 10
        ]

        risk_points = it.get("risk_points", [])
        if not isinstance(risk_points, list):
            risk_points = []
        risk_points = [r for r in risk_points if isinstance(r, str) and r.strip()]

        repeatability_questions = it.get("repeatability_questions", [])
        if not isinstance(repeatability_questions, list):
            repeatability_questions = []
        repeatability_questions = [q for q in repeatability_questions if isinstance(q, str) and q.strip()]

        # 핵심 키워드 추출 (새 필드)
        key_keywords = it.get("key_keywords", [])
        if not isinstance(key_keywords, list):
            key_keywords = []
        # 키워드는 짧아도 됨 (2자 이상)
        key_keywords = [k for k in key_keywords if isinstance(k, str) and k.strip() and len(k.strip()) >= 2]

        # 근거 문장 추출 (새 필드) - 원문이므로 최소 길이 체크
        evidence_sentences = it.get("evidence_sentences", [])
        if not isinstance(evidence_sentences, list):
            evidence_sentences = []
        evidence_sentences = [
            e for e in evidence_sentences
            if isinstance(e, str) and e.strip() and len(e.strip()) >= 15
        ]

        # 문장 라벨 추출 (새 필드 - 패턴 매칭용)
        sentence_labels = it.get("sentence_labels", [])
        if not isinstance(sentence_labels, list):
            sentence_labels = []
        # 각 항목이 dict이고 sentence, labels 필드가 있는지 검증
        valid_labels = []
        for sl in sentence_labels:
            if isinstance(sl, dict) and sl.get("sentence") and sl.get("labels"):
                valid_labels.append({
                    "sentence": str(sl.get("sentence", "")),
                    "labels": [str(l) for l in sl.get("labels", []) if l]
                })
        sentence_labels = valid_labels

        # 매칭된 패턴 번호 (새 필드)
        matched_pattern = it.get("matched_pattern", "")
        if not isinstance(matched_pattern, str):
            matched_pattern = str(matched_pattern) if matched_pattern else ""

        # 면접관 해석 (새 필드)
        interviewer_interpretation = it.get("interviewer_interpretation", [])
        if not isinstance(interviewer_interpretation, list):
            interviewer_interpretation = []
        interviewer_interpretation = [
            i for i in interviewer_interpretation
            if isinstance(i, str) and i.strip()
        ]

        # 파고들 포인트 (새 필드)
        probe_points = it.get("probe_points", [])
        if not isinstance(probe_points, list):
            probe_points = []
        probe_points = [p for p in probe_points if isinstance(p, str) and p.strip()]

        # deep_questions (심층 면접 질문 - 새 핵심 필드)
        deep_questions = it.get("deep_questions", [])
        if not isinstance(deep_questions, list):
            deep_questions = []
        # 각 항목이 dict이고 필수 필드가 있는지 검증
        valid_deep_questions = []
        for dq in deep_questions:
            if isinstance(dq, dict):
                question = dq.get("question", "")
                source_sentence = dq.get("source_sentence", "")
                sentence_type = dq.get("sentence_type", "")
                expected_answers = dq.get("expected_answers", [])

                # 질문이 유효한지 확인 (최소 10자 이상)
                if isinstance(question, str) and len(question.strip()) >= 10:
                    # expected_answers 검증
                    valid_answers = []
                    if isinstance(expected_answers, list):
                        for ea in expected_answers:
                            if isinstance(ea, dict):
                                ans = ea.get("answer", "")
                                followup = ea.get("followup", "")
                                if isinstance(ans, str) and isinstance(followup, str):
                                    valid_answers.append({
                                        "answer": ans.strip(),
                                        "followup": followup.strip()
                                    })

                    valid_deep_questions.append({
                        "source_sentence": source_sentence.strip() if isinstance(source_sentence, str) else "",
                        "sentence_type": sentence_type.strip() if isinstance(sentence_type, str) else "",
                        "question": question.strip(),
                        "expected_answers": valid_answers
                    })
        deep_questions = valid_deep_questions

        # 유효 개수 카운트 (핵심 공격 포인트들)
        if claim:
            total_valid += 1
        total_valid += len(over_idealized_points)
        total_valid += len(risk_points)
        total_valid += len(repeatability_questions)
        total_valid += len(key_keywords)
        total_valid += len(evidence_sentences)
        total_valid += len(sentence_labels)
        total_valid += len(interviewer_interpretation)
        total_valid += len(probe_points)
        total_valid += len(deep_questions)  # deep_questions도 카운트

        out_items.append({
            "question": q_raw if q_raw else "자기소개서",
            "question_type": question_type,
            "question_intent": question_intent,
            "q2_strategy": q2_strategy,
            "claim": claim,
            "sentence_labels": sentence_labels,
            "matched_pattern": matched_pattern,
            "interviewer_interpretation": interviewer_interpretation,
            "probe_points": probe_points,
            "decision_criteria": decision_criteria,
            "rejected_alternatives": rejected_alternatives,
            "over_idealized_points": over_idealized_points,
            "risk_points": risk_points,
            "repeatability_questions": repeatability_questions,
            "deep_questions": deep_questions,  # deep_questions 추가
            "key_keywords": key_keywords,
            "evidence_sentences": evidence_sentences,
        })

    # 부족한 아이템 채우기
    for j in range(len(out_items), len(qa_sets or [])):
        qa = qa_sets[j] or {}
        out_items.append({
            "question": (qa.get("prompt", "") or "").strip() or "자기소개서",
            "question_type": "",
            "question_intent": "",
            "q2_strategy": "",
            "claim": "",
            "sentence_labels": [],
            "matched_pattern": "",
            "interviewer_interpretation": [],
            "probe_points": [],
            "decision_criteria": [],
            "rejected_alternatives": [],
            "over_idealized_points": [],
            "risk_points": [],
            "repeatability_questions": [],
            "deep_questions": [],  # deep_questions 추가
            "key_keywords": [],
            "evidence_sentences": [],
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

        # ========================================
        # Stage 2: 원문 검증 (방안 1+2)
        # ========================================
        try:
            verified_data = verify_llm_extraction(data, qa_sets)
            if verified_data:
                data = verified_data
                # 검증 통계 추가
                if "verification_stats" in data:
                    stats = data["verification_stats"]
                    data["verification_confidence"] = stats.get("confidence_ratio", 0)
        except Exception as e:
            # 검증 실패해도 원본 데이터 유지
            logger.warning(f"LLM extraction verification failed: {e}")
            pass

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


def generate_q3_from_answer(q2_question: str, user_answer: str, essay_context: str = "") -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or ""
    if not api_key:
        return None
    system_prompt = "당신은 항공사 면접관입니다. 지원자의 답변을 듣고 꼬리질문을 해야 합니다."
    user_prompt = f"면접관 질문: {q2_question}\n지원자 답변: {user_answer}\n\n꼬리질문 1개만 생성하세요."
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": LLM_MODEL_NAME, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.7, "max_tokens": 200}
        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
        r.raise_for_status()
        resp = r.json()
        content = (resp.get("choices", [{}])[0] or {}).get("message", {}).get("content", "")
        return content.strip() if content else None
    except Exception as e:
        logger.warning(f"Single Q2 generation failed: {e}")
        return None


def generate_resume_questions(resume_data: dict, airline: str, num_questions: int = 2) -> list:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or ""
    if not api_key:
        return []
    info_parts = [f"항공사: {airline}"]
    if resume_data.get("major"): info_parts.append(f"전공: {resume_data['major']}")
    if resume_data.get("experience"): info_parts.append(f"경력: {resume_data['experience']}")
    if resume_data.get("gap"): info_parts.append(f"공백: {resume_data['gap']}")
    info_text = ", ".join(info_parts)
    system_prompt = "당신은 항공사 면접관입니다."
    user_prompt = f"지원자 정보: {info_text}\n면접 질문 {num_questions}개를 생성하세요."
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": LLM_MODEL_NAME, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.7, "max_tokens": 400}
        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=LLM_TIMEOUT_SEC)
        r.raise_for_status()
        resp = r.json()
        content = (resp.get("choices", [{}])[0] or {}).get("message", {}).get("content", "")
        if not content: return []
        questions = [line.strip().lstrip("0123456789.-) ") for line in content.strip().split("\n") if line.strip()]
        return questions[:num_questions]
    except Exception as e:
        logger.warning(f"Resume questions generation failed: {e}")
        return []


# ============================================================
# 프리미엄 자소서 분석 - 면접관 시선 완벽 분석
# ============================================================

PREMIUM_ANALYSIS_PROMPT = """당신은 10년차 항공사 면접관입니다. 자소서를 읽고 심층 면접 질문을 생성합니다.

## 자소서 문항
{question}

## 지원자 답변
{answer}

---

## STEP 1: 핵심문장 추출 및 유형 분류

답변에서 면접관이 파고들 핵심문장 3-5개를 추출하고, 각각의 유형을 분류하세요.

### 문장 유형 (5가지)
1. **가치선언**: 본인의 가치관/신념을 선언 (예: "팀워크가 제일 중요하다고 생각합니다")
2. **경험제시**: 구체적 경험을 언급 (예: "16살에 혼자 중국으로 유학을 갔습니다")
3. **깨달음**: 경험에서 얻은 교훈 (예: "공동체 속에서 함께 있으니 극복할 수 있었습니다")
4. **실천사례**: 실제로 한 행동 (예: "함께 웃으면서 할 수 있는 환경을 조성했습니다")
5. **개념사용**: 특정 개념/용어 사용 (예: "팀컬러라는 것이 존재합니다")

### 면접 타겟 (각 유형별 공략법)
- 가치선언 → **깊이검증**: "정말 그렇게 생각하십니까? 반대 상황에서도?"
- 경험제시 → **구체화요구**: "그때 구체적으로 어떤 상황이었습니까?"
- 깨달음 → **역방향질문**: "그럼 본인이 기여한 건 무엇입니까?"
- 실천사례 → **한계탐색**: "그 방식이 통하지 않는 상황은요?"
- 개념사용 → **정의확인**: "그게 정확히 무슨 의미입니까?"

---

## STEP 2: 심층질문 생성 (Q2용)

각 핵심문장에 대해 **구체적인 반례 상황**을 설정한 질문을 만드세요.

### 좋은 Q2 질문 예시
- 핵심문장: "팀워크가 제일 중요하다고 생각합니다"
- 나쁜 질문: "팀워크가 왜 중요하다고 생각하시나요?" (너무 열린 질문)
- 좋은 질문: "팀워크가 제일 중요하다고 하셨는데, 팀워크가 안 되는 동료와 비행해야 한다면 어떻게 하시겠습니까?"

### 질문 생성 규칙
1. 핵심문장을 직접 인용하여 시작
2. **구체적인 반례/압박 상황** 설정 (승무원 업무 맥락)
3. "어떻게 하시겠습니까?" 또는 "그래도 같은 생각이십니까?"로 마무리
4. 1-2문장으로 짧게

---

## STEP 3: 예상 답변 + 꼬리질문 (Q3용)

각 Q2에 대해 예상되는 답변 3가지와 각각의 꼬리질문을 준비하세요.

### 예시
Q2: "팀워크가 안 되는 동료와 비행해야 한다면 어떻게 하시겠습니까?"

| 예상 답변 | 꼬리질문 |
|----------|---------|
| "대화로 풀겠습니다" | "대화해도 안 바뀌면요? 3개월째 그 상태면요?" |
| "제가 먼저 맞추겠습니다" | "계속 맞추기만 하면 본인은 지치지 않습니까?" |
| "업무와 감정을 분리하겠습니다" | "감정 분리가 진짜 되십니까? 안 됐던 적은요?" |

---

## JSON 출력 형식 (반드시 이 형식으로)
{{
  "key_sentences": [
    {{
      "sentence": "핵심문장 원문 그대로 (자르지 말 것)",
      "type": "가치선언/경험제시/깨달음/실천사례/개념사용",
      "interview_target": "깊이검증/구체화요구/역방향질문/한계탐색/정의확인",
      "trap": "이 문장의 함정 (지원자가 답변하기 어려운 포인트)",
      "counter_situation": "반례 상황 설명 (승무원 업무 맥락)"
    }}
  ],
  "deep_questions": [
    {{
      "source_sentence": "질문의 근거가 된 핵심문장",
      "question": "심층 면접 질문 (Q2용)",
      "question_type": "가치검증형/경험구체화형/역방향질문형/한계탐색형/개념정의형",
      "expected_answers": [
        {{
          "answer": "예상 답변 1",
          "followup": "꼬리질문 1 (Q3용)"
        }},
        {{
          "answer": "예상 답변 2",
          "followup": "꼬리질문 2 (Q3용)"
        }},
        {{
          "answer": "예상 답변 3",
          "followup": "꼬리질문 3 (Q3용)"
        }}
      ]
    }}
  ],
  "overall_weakness": "이 답변의 가장 큰 약점 (면접관 시선)"
}}
"""


def premium_analyze_resume(question: str, answer: str) -> Optional[Dict[str, Any]]:
    """
    프리미엄 자소서 분석 - 면접관 시선으로 완벽 분석

    Returns:
        분석 결과 딕셔너리 또는 None (실패 시)
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or ""
    if not api_key:
        return None

    prompt = PREMIUM_ANALYSIS_PROMPT.format(question=question, answer=answer)

    # 프리미엄 분석은 복잡하므로 타임아웃을 60초로 설정
    PREMIUM_TIMEOUT_SEC = 60
    MAX_RETRIES = 2

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "당신은 10년차 항공사 면접관입니다. 날카롭고 전문적인 시선으로 분석하세요. JSON 형식으로만 응답하세요."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=PREMIUM_TIMEOUT_SEC)
            r.raise_for_status()
            resp = r.json()

            content = (resp.get("choices", [{}])[0] or {}).get("message", {}).get("content", "")
            if not content:
                continue  # 재시도

            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                time.sleep(2)  # 2초 대기 후 재시도
                continue
        except Exception as e:
            logger.warning(f"LLM API call failed (attempt {attempt + 1}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(1)
                continue

    return None


def get_premium_q2_question(analysis: Dict[str, Any], version: int, is_soft: bool = False) -> str:
    """
    프리미엄 분석 결과에서 Q2 질문 추출

    Args:
        analysis: premium_analyze_resume의 결과
        version: 버전 번호 (1-6)
        is_soft: 부드러운 톤 여부

    Returns:
        Q2 질문 문자열
    """
    if not analysis:
        return "자소서에서 가장 중요하게 생각하신 경험에 대해 구체적으로 말씀해 주시겠어요?"

    questions = analysis.get("interview_questions", [])
    if not questions:
        return "자소서에서 가장 중요하게 생각하신 경험에 대해 구체적으로 말씀해 주시겠어요?"

    # 버전에 따라 다른 질문 선택 (1-5번 중)
    # 버전 1,2 -> 질문 1번 (웜업)
    # 버전 3,4 -> 질문 2,3번 (구체화/검증)
    # 버전 5,6 -> 질문 4번 (압박)
    if version <= 2:
        q_idx = 0  # 웜업 질문
    elif version <= 4:
        q_idx = (version - 2)  # 구체화/검증 질문
    else:
        q_idx = 3  # 압박 질문

    if q_idx >= len(questions):
        q_idx = 0

    q_obj = questions[q_idx]
    question_text = q_obj.get("question", "")

    if not question_text:
        return "자소서에서 가장 중요하게 생각하신 경험에 대해 구체적으로 말씀해 주시겠어요?"

    return question_text


def get_premium_q3_question(analysis: Dict[str, Any], version: int, is_soft: bool = False) -> str:
    """
    프리미엄 분석 결과에서 Q3 (꼬리질문) 추출

    Args:
        analysis: premium_analyze_resume의 결과
        version: 버전 번호 (1-6)
        is_soft: 부드러운 톤 여부

    Returns:
        Q3 질문 문자열
    """
    if not analysis:
        return "방금 말씀하신 상황에서 다르게 행동할 수도 있었을 텐데, 왜 그 방법을 선택하셨나요?"

    questions = analysis.get("interview_questions", [])
    if len(questions) < 5:
        return "방금 말씀하신 상황에서 다르게 행동할 수도 있었을 텐데, 왜 그 방법을 선택하셨나요?"

    # Q3는 5번 질문 (적용) 또는 남은 질문 중 선택
    q_obj = questions[4] if len(questions) > 4 else questions[-1]
    question_text = q_obj.get("question", "")

    if not question_text:
        return "방금 말씀하신 상황에서 다르게 행동할 수도 있었을 텐데, 왜 그 방법을 선택하셨나요?"

    return question_text


def get_premium_key_sentence(analysis: Dict[str, Any], index: int = 0) -> str:
    """
    프리미엄 분석 결과에서 핵심 문장 추출

    Args:
        analysis: premium_analyze_resume의 결과
        index: 핵심 문장 인덱스 (0, 1, 2)

    Returns:
        핵심 문장 문자열
    """
    if not analysis:
        return ""

    key_sentences = analysis.get("key_sentences", [])
    if index >= len(key_sentences):
        return ""

    return key_sentences[index].get("sentence", "")


# =========================
# 간단한 Q2/Q3 직접 생성 (빠른 버전)
# =========================

SIMPLE_Q2_PROMPT = """당신은 항공사 면접관입니다. 아래 자소서 답변을 읽고 면접 질문 1개를 만드세요.

[문항]
{question}

[답변]
{answer}

[규칙]
1. 답변에서 **검증이 필요한 부분**을 찾아서 질문하세요
2. "~에 대해 말씀해주세요" 같은 열린 질문 금지
3. 구체적인 사실/숫자/상황을 물어보세요
4. 한 문장으로 짧게 작성
5. 반말 금지, 존댓말 사용

{tone_instruction}

⚠️ 절대 하지 말 것:
- "다큐멘터리", "영화", "장면" 같은 비유적 표현을 그대로 질문에 넣지 말 것
- 답변의 문장을 그대로 따옴표로 인용하지 말 것
- 지원자가 쓴 표현을 그대로 반복하지 말 것

좋은 질문 예시:
- "그 상황에서 본인이 직접 한 행동이 무엇이었나요?"
- "몇 명이 참여했고, 본인 역할은 구체적으로 무엇이었나요?"
- "그 결과가 어떻게 측정되었나요?"

질문만 출력하세요 (설명 없이):"""

SIMPLE_Q3_PROMPT = """당신은 항공사 면접관입니다. Q2 질문에 대한 꼬리질문 1개를 만드세요.

[원래 자소서 답변 요약]
{answer_summary}

[Q2 질문]
{q2_question}

[규칙]
1. Q2 답변을 더 깊이 파고드는 질문
2. "왜?", "어떻게?", "만약~라면?" 형태
3. 한 문장으로 짧게
4. 존댓말 사용

{tone_instruction}

질문만 출력하세요:"""


def generate_simple_q2(question: str, answer: str, is_soft: bool = False) -> Optional[str]:
    """
    간단하고 빠른 Q2 질문 생성

    Args:
        question: 자소서 문항
        answer: 자소서 답변
        is_soft: 부드러운 톤 여부

    Returns:
        Q2 질문 문자열 또는 None
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or ""
    if not api_key:
        return None

    tone = "부드럽고 친근하게 질문하세요." if is_soft else "날카롭고 직접적으로 질문하세요."
    prompt = SIMPLE_Q2_PROMPT.format(
        question=question[:200],
        answer=answer[:500],  # 답변 길이 제한으로 속도 향상
        tone_instruction=tone
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 100,  # 짧은 응답만 필요
    }

    try:
        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)  # 10초로 단축
        r.raise_for_status()
        resp = r.json()
        content = (resp.get("choices", [{}])[0] or {}).get("message", {}).get("content", "")
        if content:
            # 불필요한 따옴표/설명 제거
            content = content.strip().strip('"').strip("'").strip()
            # 너무 길면 첫 문장만
            if len(content) > 100:
                content = content.split("?")[0] + "?"
            return content
    except Exception as e:
        logger.warning(f"Followup question generation failed: {e}")
        pass

    return None


def generate_simple_q3(answer: str, q2_question: str, is_soft: bool = False) -> Optional[str]:
    """
    간단하고 빠른 Q3 (꼬리질문) 생성

    Args:
        answer: 자소서 답변 요약
        q2_question: Q2 질문
        is_soft: 부드러운 톤 여부

    Returns:
        Q3 질문 문자열 또는 None
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY") or ""
    if not api_key:
        return None

    tone = "부드럽게 후속 질문하세요." if is_soft else "날카롭게 압박하는 질문을 하세요."
    prompt = SIMPLE_Q3_PROMPT.format(
        answer_summary=answer[:300],
        q2_question=q2_question,
        tone_instruction=tone
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
    }

    try:
        r = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)  # 10초로 단축
        r.raise_for_status()
        resp = r.json()
        content = (resp.get("choices", [{}])[0] or {}).get("message", {}).get("content", "")
        if content:
            content = content.strip().strip('"').strip("'").strip()
            if len(content) > 100:
                content = content.split("?")[0] + "?"
            return content
    except Exception as e:
        logger.warning(f"Alternative followup generation failed: {e}")
        pass

    return None
