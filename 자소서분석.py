# app.py
# 메인 Streamlit 앱 - UI + 질문 생성 + 피드백

import re
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from logging_config import get_logger

logger = get_logger(__name__)

import streamlit as st

# 내부 모듈 import
from config import (
    AIRLINES, AIRLINE_VALUES, VALUES_DEFAULT,
    _canonical_airline_name, _raw_airline_key, airline_profile,
    SOFT_TIMEOUT_SEC,
    FSC_VALUE_DATA, LCC_VALUE_DATA, HSC_VALUE_DATA,
    VALUE_Q_TEMPLATES_FSC, VALUE_Q_TEMPLATES_LCC,
    # 버전별 VALUE_Q 템플릿
    VALUE_Q_TEMPLATES_FSC_SOFT, VALUE_Q_TEMPLATES_FSC_SHARP,
    VALUE_Q_TEMPLATES_LCC_SOFT, VALUE_Q_TEMPLATES_LCC_SHARP,
    Q1_FIXED, Q1_POOL, Q5_POOL, Q5_FORBIDDEN_WORDS,
    # 항공사 유형별 질문 풀
    Q1_POOL_FSC, Q1_POOL_LCC, Q1_POOL_HSC, Q1_POOL_COMMON,
    Q5_POOL_FSC, Q5_POOL_LCC, Q5_POOL_HSC, Q5_POOL_COMMON,
    # 버전별 말투 차이 (SHARP=날카로움, SOFT=부드러움)
    Q5_POOL_COMMON_SHARP, Q5_POOL_COMMON_SOFT,
    Q5_POOL_FSC_SHARP, Q5_POOL_FSC_SOFT,
    Q5_POOL_LCC_SHARP, Q5_POOL_LCC_SOFT,
    # Q1 버전별 말투
    Q1_POOL_COMMON_SOFT, Q1_POOL_COMMON_SHARP,
    Q1_POOL_FSC_SOFT, Q1_POOL_FSC_SHARP,
    Q1_POOL_LCC_SOFT, Q1_POOL_LCC_SHARP,
    Q1_POOL_HSC_SOFT, Q1_POOL_HSC_SHARP,
    # 버전별 풀 선택 함수
    get_q1_pool_by_airline, get_q5_pool_by_airline, get_value_q_templates,
    # 통합/인수합병 관련 질문
    INTEGRATED_LCC_Q_TEMPLATES, INTEGRATED_LCC_AIRLINES,
    # 새 공격 포인트 → 질문 번역 템플릿
    Q2_ATTACK_TEMPLATES, Q2_ATTACK_TEMPLATES_SOFT,
    Q2_RISK_TEMPLATES, Q2_RISK_TEMPLATES_SOFT,
    Q2_ALTERNATIVE_TEMPLATES, Q2_ALTERNATIVE_TEMPLATES_SOFT,
    # 추상적 문장용 템플릿
    ABSTRACT_SENTENCE_PATTERNS,
    Q2_ABSTRACT_TEMPLATES, Q2_ABSTRACT_TEMPLATES_SOFT,
    # 꿈/소망 문장용 템플릿
    Q2_DREAM_TEMPLATES, Q2_DREAM_TEMPLATES_SOFT,
    # Q3 꼬리질문 4가지 유형
    Q3_CONDITION_CHANGE, Q3_PRIORITY_CONFLICT,
    Q3_LIMIT_RECOGNITION, Q3_REPEATABILITY,
    # Q3 꿈/목표 전용 템플릿
    Q3_DREAM_CONDITION, Q3_DREAM_PRIORITY,
    Q3_DREAM_LIMIT, Q3_DREAM_REPEAT,
    # 요금제 및 이력서 설정
    PLAN_CONFIG, DEFAULT_PLAN,
    RESUME_MAJOR_OPTIONS, RESUME_EXPERIENCE_OPTIONS, RESUME_GAP_OPTIONS,
    # 면접 팁 및 2026 채용 트렌드
    AIRLINE_PREFERRED_TYPE, ENGLISH_INTERVIEW_AIRLINES,
    INTERVIEW_TIPS, FSC_VS_LCC_INTERVIEW,
    COMMON_INTERVIEW_MISTAKES, CREW_ESSENTIAL_QUALITIES,
    KOREAN_AIR_INTERVIEW_INFO, HIRING_TRENDS_2026,
    # 면접관 톤 규칙 및 한국어 질문 생성 규칙
    INTERVIEWER_TONE_RULES, KOREAN_QUESTION_RULES,
    TONE_CONVERSION_RULES, ABSOLUTE_PROHIBITIONS,
    # Q2 공격 구조 및 Few-shot 예시
    Q2_ATTACK_STRUCTURES, Q2_FORBIDDEN_PATTERNS, Q2_FEWSHOT_EXAMPLES,
)
from text_utils import (
    normalize_ws, stable_int_hash, split_sentences, split_essay_items,
    extract_evidence_sentences, extract_risk_keywords_kor,
    fmt_anchor_text, _strip_ellipsis_tokens, _trim_no_ellipsis,
    _sanity_kor_endings, _auto_fix_particles_kor, _fix_particles_after_format,
    _sanitize_question_strict, _dedup_keep_order, build_basis_text,
)
from analysis import (
    _pick_anchor_by_rule, _srcai_analyze_text,
    _classify_prompt_type_kor, _extract_topic_keywords_short,
    _pick_situation_snippet, _pick_two_basis_by_type,
)
from llm_utils import (
    _ensure_llm_state_boxes, _llm_gc, _calc_llm_hash_from_qa_sets,
    _llm_try_extract_or_reuse, _llm_type_to_internal,
    _llm_extract_for_slot, generate_q3_from_answer,
    generate_resume_questions,
)
from extraction_verifier import is_complete_sentence
from feedback_analyzer import analyze_answer


# ----------------------------
# 비밀번호 보호 (테스터 5명만 접근 가능)
# ----------------------------


# ----------------------------
# SRCAI 적용 함수 (session_state 접근 필요)
# ----------------------------

def _srcai_apply_to_qa_sets(qa_sets: List[Dict[str, str]]) -> None:
    if "ps_srcai_sentences" not in st.session_state:
        st.session_state.ps_srcai_sentences = []
    if "ps_srcai_roles" not in st.session_state:
        st.session_state.ps_srcai_roles = []
    if "ps_srcai_selected_actions" not in st.session_state:
        st.session_state.ps_srcai_selected_actions = []
    if "ps_srcai_selected_results" not in st.session_state:
        st.session_state.ps_srcai_selected_results = []
    if "ps_srcai_selected_questionables" not in st.session_state:
        st.session_state.ps_srcai_selected_questionables = []

    per_sentences: List[List[str]] = []
    per_roles: List[List[str]] = []
    per_actions: List[List[str]] = []
    per_results: List[List[str]] = []
    per_questionables: List[List[str]] = []

    if not qa_sets:
        st.session_state.ps_srcai_sentences = per_sentences
        st.session_state.ps_srcai_roles = per_roles
        st.session_state.ps_srcai_selected_actions = per_actions
        st.session_state.ps_srcai_selected_results = per_results
        st.session_state.ps_srcai_selected_questionables = per_questionables
        return

    for qa in qa_sets:
        ans_raw = qa.get("answer", "") or ""
        analyzed = _srcai_analyze_text(ans_raw)
        per_sentences.append(analyzed["sentences"])
        per_roles.append(analyzed["roles"])
        per_actions.append(analyzed["selected_action_sentences"])
        per_results.append(analyzed["selected_result_sentences"])
        per_questionables.append(analyzed["selected_questionable_sentences"])

    st.session_state.ps_srcai_sentences = per_sentences
    st.session_state.ps_srcai_roles = per_roles
    st.session_state.ps_srcai_selected_actions = per_actions
    st.session_state.ps_srcai_selected_results = per_results
    st.session_state.ps_srcai_selected_questionables = per_questionables


# ----------------------------
# Basis 선택 로직 (session_state 접근 필요)
# ----------------------------

def _is_valid_basis_text(text: str) -> bool:
    """basis 텍스트가 유효한지 검증 (불완전한 문장 필터링)"""
    if not text or len(text.strip()) < 10:
        return False
    text = text.strip()

    # 불완전한 문장 패턴 (관형형 어미로 끝남 - 명사가 와야 함)
    incomplete_endings = [
        "향한", "위한", "통한", "대한", "관한",
        "하는", "되는", "같은", "다른", "있는", "없는",
        "라는", "이라는", "라고 하는",
        "과의", "와의", "에서의", "으로의", "로의",
        "처럼", "같이", "대로",
    ]
    for ending in incomplete_endings:
        if text.endswith(ending):
            return False

    # 연결어미로 끝나는 문장
    connecting_endings = [
        "하고", "하며", "하면서", "하여", "해서",
        "되고", "되며", "으며", "며", "면서",
        "지만", "는데", "니까", "므로", "어서", "아서",
        "려고", "으려고", "고자", "도록",
    ]
    for ending in connecting_endings:
        if text.endswith(ending):
            return False

    # 조사로만 끝나는 짧은 문장
    if re.search(r"[을를이가은는와과]$", text) and len(text) < 25:
        return False

    return True


def _pick_basis_from_llm_or_fallback(
    idx0: int,
    qtype_internal: str,
    answer_raw: str,
    llm_item: Optional[Dict[str, Any]],
) -> tuple:
    if isinstance(llm_item, dict):
        acts = llm_item.get("action_sentences", [])
        ress = llm_item.get("result_sentences", [])
        if isinstance(acts, list) and isinstance(ress, list):
            # 유효한 문장만 필터링 (불완전한 문장 제외)
            valid_acts = [a for a in acts if isinstance(a, str) and _is_valid_basis_text(a)]
            valid_ress = [r for r in ress if isinstance(r, str) and _is_valid_basis_text(r)]

            A_raw = valid_acts[0] if valid_acts else ""
            B_raw = valid_ress[0] if valid_ress else (valid_acts[1] if len(valid_acts) > 1 else "")
            if A_raw or B_raw:
                A = {"text": _trim_no_ellipsis(_strip_ellipsis_tokens(A_raw), 120) if A_raw else "", "kind": "action"}
                B = {"text": _trim_no_ellipsis(_strip_ellipsis_tokens(B_raw), 120) if B_raw else "", "kind": "result"}
                if A["text"] and B["text"]:
                    return A, B
                fbA, fbB = _pick_two_basis_by_type(qtype=qtype_internal, answer=answer_raw, version_seed=idx0 + 1)
                if not A["text"]:
                    A["text"] = fbA.get("text", "")
                    A["kind"] = fbA.get("kind", "action")
                if not B["text"]:
                    B["text"] = fbB.get("text", "")
                    B["kind"] = fbB.get("kind", "role")
                return A, B

    try:
        per_actions = st.session_state.get("ps_srcai_selected_actions", [])
        per_results = st.session_state.get("ps_srcai_selected_results", [])
        act_cands = per_actions[idx0] if isinstance(per_actions, list) and idx0 < len(per_actions) else []
        res_cands = per_results[idx0] if isinstance(per_results, list) and idx0 < len(per_results) else []
        if isinstance(act_cands, list) or isinstance(res_cands, list):
            # 유효한 문장만 필터링 (불완전한 문장 제외)
            valid_act_cands = [a for a in act_cands if isinstance(a, str) and _is_valid_basis_text(a)] if isinstance(act_cands, list) else []
            valid_res_cands = [r for r in res_cands if isinstance(r, str) and _is_valid_basis_text(r)] if isinstance(res_cands, list) else []

            A_raw = valid_act_cands[0] if valid_act_cands else ""
            B_raw = (valid_res_cands[0] if valid_res_cands else "") or (
                valid_act_cands[1] if len(valid_act_cands) > 1 else ""
            )
            if A_raw or B_raw:
                A = {"text": _trim_no_ellipsis(_strip_ellipsis_tokens(A_raw), 120) if A_raw else "", "kind": "action"}
                B = {"text": _trim_no_ellipsis(_strip_ellipsis_tokens(B_raw), 120) if B_raw else "", "kind": "result"}
                if A["text"] or B["text"]:
                    if not A["text"] or not B["text"]:
                        fbA, fbB = _pick_two_basis_by_type(qtype=qtype_internal, answer=answer_raw, version_seed=idx0 + 1)
                        if not A["text"]:
                            A["text"] = fbA.get("text", "")
                            A["kind"] = fbA.get("kind", "action")
                        if not B["text"]:
                            B["text"] = fbB.get("text", "")
                            B["kind"] = fbB.get("kind", "role")
                    return A, B
    except Exception:
        pass

    return _pick_two_basis_by_type(qtype=qtype_internal, answer=answer_raw, version_seed=idx0 + 1)


# ----------------------------
# 문항 분석 로직
# ----------------------------

def _analyze_qa_sets(qa_sets: List[Dict[str, str]], llm_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not qa_sets:
        return out

    llm_items = None
    if isinstance(llm_data, dict):
        li = llm_data.get("items", None)
        if isinstance(li, list):
            llm_items = li

    per_actions = st.session_state.get("ps_srcai_selected_actions", [])
    per_results = st.session_state.get("ps_srcai_selected_results", [])

    for i, qa in enumerate(qa_sets, start=1):
        p_raw = qa.get("prompt", "") or ""
        a_raw = qa.get("answer", "") or ""

        p = normalize_ws(p_raw)
        a = normalize_ws(a_raw)

        qtype_internal = _classify_prompt_type_kor(p)
        llm_item = None
        if isinstance(llm_items, list) and (i - 1) < len(llm_items):
            cand = llm_items[i - 1]
            if isinstance(cand, dict):
                llm_item = cand
                # question_type 필드 사용 (기존 type 필드도 폴백으로 지원)
                llm_qtype = cand.get("question_type", "") or cand.get("type", "")
                qtype_internal = _llm_type_to_internal(llm_qtype, qtype_internal)

        keywords = _extract_topic_keywords_short(a, top_k=10)
        situation = _pick_situation_snippet(a, qtype=qtype_internal)

        basisA, basisB = _pick_basis_from_llm_or_fallback(
            idx0=i - 1,
            qtype_internal=qtype_internal,
            answer_raw=a_raw,
            llm_item=llm_item,
        )

        action_sents: List[str] = []
        result_sents: List[str] = []

        if isinstance(llm_item, dict):
            acts = llm_item.get("action_sentences", [])
            ress = llm_item.get("result_sentences", [])
            if isinstance(acts, list):
                action_sents.extend([s for s in acts if isinstance(s, str) and s])
            if isinstance(ress, list):
                result_sents.extend([s for s in ress if isinstance(s, str) and s])

        try:
            if isinstance(per_actions, list) and (i - 1) < len(per_actions):
                aa = per_actions[i - 1]
                if isinstance(aa, list):
                    action_sents.extend([s for s in aa if isinstance(s, str) and s])
            if isinstance(per_results, list) and (i - 1) < len(per_results):
                rr = per_results[i - 1]
                if isinstance(rr, list):
                    result_sents.extend([s for s in rr if isinstance(s, str) and s])
        except Exception:
            pass

        out.append({
            "index": i,
            "prompt": p,
            "answer": a,
            "qtype": qtype_internal,
            "keywords": keywords,
            "situation": situation,
            "basisA": basisA,
            "basisB": basisB,
            "action_sents": _dedup_keep_order(action_sents),
            "result_sents": _dedup_keep_order(result_sents),
        })
    return out


# 캐시 무효화 버전 - 이 값을 바꾸면 모든 세션 캐시가 무효화됨
_CACHE_VERSION = "v2_incomplete_filter"

def _get_or_build_item_analysis_cache(qa_sets: List[Dict[str, str]], essay_hash: str, force_rebuild: bool = False) -> Dict[str, Any]:
    box = st.session_state.get("_item_analysis_box", {})
    llm_hash = _calc_llm_hash_from_qa_sets(qa_sets)
    # 캐시 버전을 키에 포함하여 이전 캐시 무효화
    key = f"{_CACHE_VERSION}|{essay_hash}|{llm_hash}" if llm_hash else f"{_CACHE_VERSION}|{essay_hash}"

    # 캐시된 결과 확인 (force_rebuild가 아닌 경우에만)
    if not force_rebuild and isinstance(box, dict) and key in box:
        cached = box[key]
        # 캐시된 결과에 LLM 데이터가 없는 경우, LLM 상태 확인하여 재시도
        llm_box = st.session_state.get("_llm_extract_box", {})
        llm_rec = llm_box.get(llm_hash, {}) if llm_hash and isinstance(llm_box, dict) else {}
        llm_state = llm_rec.get("state", "") if isinstance(llm_rec, dict) else ""

        # LLM이 COMPLETED 상태이고 데이터가 있으면 캐시 유효
        if llm_state == "COMPLETED" and isinstance(llm_rec.get("data"), dict):
            # 캐시된 분석 결과가 LLM 데이터 없이 만들어졌을 수 있으므로 확인
            # (items에 over_idealized_points 등이 있으면 LLM 데이터 반영됨)
            return cached
        # LLM이 아직 성공하지 않았거나, FAILED 상태면 캐시 사용
        elif llm_state in ("", "NO_RECORD", "PENDING"):
            return cached
        # LLM이 FAILED 상태였다가 성공할 수 있으므로, force_rebuild=True로 다시 시도
        # (이 경우는 아래에서 rebuild)
        elif llm_state == "FAILED":
            return cached  # 실패 상태면 캐시 사용 (재시도는 버튼 클릭 시)

    llm_data = _llm_try_extract_or_reuse(qa_sets)
    analyzed = _analyze_qa_sets(qa_sets, llm_data=llm_data)

    agg_text = "\n".join([x.get("answer", "") for x in analyzed if x.get("answer", "")]).strip()
    agg_evidence = extract_evidence_sentences(agg_text, max_sents=12) if agg_text else []
    agg_risk = extract_risk_keywords_kor(agg_text, top_k=14) if agg_text else []
    agg_keywords = []
    seen_kw = set()
    for it in analyzed:
        for kw in it.get("keywords", [])[:10]:
            if kw and kw not in seen_kw:
                seen_kw.add(kw)
                agg_keywords.append(kw)
            if len(agg_keywords) >= 14:
                break
        if len(agg_keywords) >= 14:
            break

    built = {
        "items": analyzed,
        "agg_text": agg_text,
        "agg_evidence": agg_evidence,
        "agg_risk": agg_risk,
        "agg_keywords": agg_keywords,
    }
    if not isinstance(box, dict):
        box = {}
    box[key] = built
    st.session_state["_item_analysis_box"] = box
    return built


# ----------------------------
# 질문 생성 헬퍼 함수
# ----------------------------

def _slot_q1_common(base: int, version: int, atype: str = "LCC") -> str:
    """Q1: 항공사 유형(FSC/LCC/HSC)에 맞는 질문 풀에서 버전별 선택

    버전에 따라 톤 선택: 홀수(1,3,5)=날카로운, 짝수(2,4,6)=부드러운
    """
    # 버전에 따라 톤 선택
    is_soft_version = (version % 2 == 0)

    # 항공사 유형에 맞는 질문 풀 선택 (버전별 톤 적용)
    if atype == "FSC":
        if is_soft_version:
            pool = Q1_POOL_COMMON_SOFT + Q1_POOL_FSC_SOFT
        else:
            pool = Q1_POOL_COMMON_SHARP + Q1_POOL_FSC_SHARP
    elif atype == "HSC":
        if is_soft_version:
            pool = Q1_POOL_COMMON_SOFT + Q1_POOL_HSC_SOFT
        else:
            pool = Q1_POOL_COMMON_SHARP + Q1_POOL_HSC_SHARP
    else:  # LCC
        if is_soft_version:
            pool = Q1_POOL_COMMON_SOFT + Q1_POOL_LCC_SOFT
        else:
            pool = Q1_POOL_COMMON_SHARP + Q1_POOL_LCC_SHARP

    if not pool:
        return "승무원으로서 안전과 서비스가 동시에 요구되는 상황에서 무엇을 먼저 선택하고 어떤 행동으로 마무리하겠습니까?"
    idx = (base + version * 7 + 1) % len(pool)
    # Q1도 풀에서 가져온 질문을 그대로 사용 (변형 금지)
    return normalize_ws(pool[idx])


def _is_abstract_sentence(point: str) -> bool:
    """추상적/비유적 문장인지 감지"""
    point_lower = point.lower()
    for pattern in ABSTRACT_SENTENCE_PATTERNS:
        if pattern in point_lower:
            return True
    return False


def _is_dream_sentence(point: str) -> bool:
    """꿈/소망/목표 문장인지 감지 (경험이 아닌 문장)"""
    dream_patterns = [
        "되고 싶", "싶다는 꿈", "꿈을 품", "꿈을 갖", "꿈이 생",
        "되겠다는", "되고자", "싶습니다", "싶었습니다",
        "목표를 갖", "목표가 생", "비전을",
        "다짐", "결심", "각오",
    ]
    point_lower = point.lower()
    for pattern in dream_patterns:
        if pattern in point_lower:
            return True
    return False


def _is_context_dependent_sentence(point: str) -> bool:
    """맥락 없이 이해 불가능한 문장인지 감지

    이런 문장은 공격 포인트로 사용하지 않음:
    - 특정 사건/사태 언급 (대한항공 사태, OO 프로젝트)
    - 비유/은유가 맥락 없이 이해 불가 (살보다 뼈를...)
    - 지시어만 있는 문장 (이번의, 그때의, 그것은...)
    - 너무 짧거나 의미 파악 불가
    - 불완전한 문장 (동사 없이 끝남, 연결어미로 끝남)

    자기소개서를 모르는 사람도 질문만 보고 대답할 수 있어야 함.
    """
    point = point.strip()

    # 너무 짧은 문장은 제외 (맥락 없이 이해 불가)
    if len(point) < 15:
        return True

    # 불완전한 문장 감지 (동사 없이 끝나는 패턴)
    incomplete_endings = [
        # 관형형 어미 (명사가 뒤에 와야 함)
        "을 향한", "를 향한", "에 향한", "향한",
        "을 위한", "를 위한", "에 위한", "위한",
        "과 함께", "와 함께",
        "을 통한", "를 통한", "통한",
        "에 대한", "에서의", "으로의", "로의",
        "과의", "와의", "에게의",
        "이라는", "라는", "라고 하는",
        # 관형사형 전성어미
        "하는", "되는", "인", "적인", "스러운",
        "같은", "다른", "새로운", "높은", "낮은",
        # 부사형으로 끝나는 불완전 문장
        "처럼", "같이", "대로",
        # 접속조사/보조사로 끝나는 문장
        "그리고", "그러나", "하지만", "따라서",
    ]
    for ending in incomplete_endings:
        if point.endswith(ending):
            return True

    # 연결어미로 끝나는 불완전한 문장
    connecting_endings = [
        "하고", "하며", "하면서", "하여", "해서",
        "되고", "되며", "되면서",
        "으며", "며", "면서",
        "지만", "는데", "ㄴ데",
        "으면", "면", "니까", "므로", "어서", "아서",
        "려고", "으려고", "고자", "도록",
    ]
    for ending in connecting_endings:
        if point.endswith(ending):
            return True

    # 조사로만 끝나는 불완전한 문장 (주어/목적어만 있고 동사 없음)
    if re.search(r"[을를이가은는도만]$", point) and len(point) < 25:
        return True

    # "~와/과" 로 끝나면 불완전 (병렬 구조가 끊김)
    if re.search(r"[와과]$", point):
        return True

    context_dependent_patterns = [
        # 특정 사건/사태 (고유명사 이벤트)
        "사태", "사건", "프로젝트", "당시", "그때", "그 당시",
        "OO", "XX", "○○", "××",  # 익명화된 표현

        # 비유/은유 (맥락 없이 이해 불가)
        "살보다", "뼈를", "피를", "눈물을", "피와 땀",
        "살과 뼈", "피와 눈물", "아픔이 함께",

        # 지시어/대명사 중심 문장
        "이번의", "이번에", "그때의", "그것은", "이것은",
        "그 순간", "그날", "그 일", "이 일",

        # 추상적/철학적 표현 (구체성 부족)
        "역사를", "발전과 역사", "새로운 시작과 끝",
        "인생의 전환점", "삶의 의미",

        # 문맥 의존적 비교 표현
        "그보다", "이보다", "저보다",
        "전보다", "예전보다", "이전보다",

        # 특정 직위/관계 언급 (구체적 상황 모름)
        "○○님", "△△님", "ㅇㅇ님",
    ]
    point_lower = point.lower()
    for pattern in context_dependent_patterns:
        if pattern in point_lower:
            return True

    # 문장이 지시어로 시작하면 맥락 의존
    if point.startswith(("그", "이", "저")) and len(point) < 30:
        return True

    # 완전한 문장인지 검사 (동사/형용사 어미가 있어야 함)
    complete_endings = [
        "다", "요", "죠", "니다", "습니다", "입니다",
        "했다", "했습니다", "했어요", "됐다", "됐습니다",
        "있다", "있습니다", "없다", "없습니다",
        "이다", "이었다", "였다",
    ]
    has_complete_ending = any(point.endswith(e) for e in complete_endings)

    # 완전한 어미가 없어도 의미있는 명사구는 허용 (예: "함께라서 극복할 수 있었다")
    meaningful_patterns = [
        r"할 수 있",
        r"수 있다",
        r"극복", "해결", "이겨냈", "성공",
        r"했습니다", r"했다", r"했어요",
    ]
    has_meaningful = any(re.search(p, point) for p in meaningful_patterns)

    if not has_complete_ending and not has_meaningful and len(point) < 40:
        return True

    return False


def _get_sentence_topic(point: str) -> str:
    """문장의 주제를 추출 (고객, 팀, 개인 등)"""
    point_lower = point.lower()

    if any(kw in point_lower for kw in ["고객", "손님", "승객", "탑승객", "서비스"]):
        return "customer"
    if any(kw in point_lower for kw in ["팀", "동료", "협력", "협동", "함께", "우리"]):
        return "team"
    if any(kw in point_lower for kw in ["상사", "사무장", "선배", "기장"]):
        return "senior"
    if any(kw in point_lower for kw in ["안전", "규정", "절차", "매뉴얼"]):
        return "safety"
    if any(kw in point_lower for kw in ["성장", "발전", "노력", "도전"]):
        return "growth"

    return "general"


def _extract_short_point(point: str) -> str:
    """긴 문장에서 핵심 키워드/표현만 추출 (의미있는 완전한 구문)"""
    # 따옴표 안의 내용 추출 (10자 이상이어야 의미있음)
    quote_match = re.search(r"['\"]([^'\"]{10,40})['\"]", point)
    if quote_match:
        return quote_match.group(1)

    # 의미있는 핵심 표현 패턴 (완전한 구문으로 추출)
    meaningful_patterns = [
        # 구체적인 표현들 (완전한 형태로)
        r"(따뜻하게 맞이하는)",
        r"(따뜻하게 맞이하)",
        r"(첫 여정을 따뜻하게 맞이)",
        r"(누군가의 첫 여정을 따뜻하게)",
        r"(다큐멘터리처럼)",
        r"(다큐멘터리[라고]?)",
        # 꿈/소망 관련
        r"(되고 싶다는 꿈을 품게)",
        r"(승무원이 되고 싶다)",
        r"(꿈을 품게 되었습니다)",
        r"(꿈을 품게 되었)",
        # 동사구 패턴 (완전한 형태)
        r"([가-힣]+하게 [가-힣]+하는)",
        r"([가-힣]+을 [가-힣]+하는)",
    ]
    for pattern in meaningful_patterns:
        match = re.search(pattern, point)
        if match:
            result = match.group(1)
            if 6 <= len(result) <= 30:  # 최소 6자 이상
                return result

    # 동사 어미로 끝나는 구문 추출 (더 자연스러운 끊김)
    # "~하는", "~하다", "~되었" 등으로 끝나는 부분 찾기
    verb_ending_match = re.search(r"([가-힣]{2,8}(?:하는|하다|되는|되다|되었|였다|했다|싶다|싶은))", point)
    if verb_ending_match:
        result = verb_ending_match.group(1)
        if 6 <= len(result) <= 20:
            return result

    # 폴백: 문장이 너무 길면 자연스러운 구문 경계에서 자르기
    if len(point) > 35:
        # 조사나 어미가 있는 위치에서 자르기
        cut_points = [" ", "을 ", "를 ", "이 ", "가 ", "은 ", "는 "]
        best_cut = 20
        for cp in cut_points:
            idx = point.find(cp, 15, 30)
            if idx > 0:
                best_cut = idx + len(cp.rstrip())
                break
        return point[:best_cut].rstrip()

    return point


def _extract_who_from_context(point: str, raw_answer: str = "") -> str:
    """문맥에서 상대방이 누구인지 추출 (고객, 동료, 승객 등)"""
    combined = (point + " " + raw_answer).lower()

    if any(kw in combined for kw in ["고객", "손님", "승객", "탑승객", "여행객"]):
        return "고객"
    if any(kw in combined for kw in ["동료", "팀원", "선배", "후배", "크루", "승무원"]):
        return "동료"
    if any(kw in combined for kw in ["상사", "팀장", "사무장", "기장"]):
        return "상사"
    if any(kw in combined for kw in ["가족", "부모", "친구"]):
        return "주변 사람들"

    # 폴백: 승무원 맥락에서는 주로 고객
    return "상대방"


def _extract_judgment_from_point(point: str) -> str:
    """point에서 구체적 판단/행동을 추출 (예: '서로 의지하겠다')"""
    # 키워드 기반 판단 추출
    judgment_map = [
        (["함께", "같이", "협력"], "함께 해결하겠다"),
        (["극복", "이겨", "해결"], "극복하겠다"),
        (["소통", "대화"], "소통하겠다"),
        (["의지", "지지", "도움"], "서로 의지하겠다"),
        (["성장", "발전", "성공"], "성장하겠다"),
        (["노력", "열심", "최선"], "노력하겠다"),
        (["도전", "시도"], "도전하겠다"),
        (["배려", "친절", "미소"], "배려하겠다"),
        (["믿음", "신뢰"], "신뢰하겠다"),
        (["포기", "버티"], "포기하지 않겠다"),
        (["꿈", "목표"], "꿈을 이루겠다"),
        (["감사", "감동"], "감사하겠다"),
    ]

    point_lower = point.lower()
    for keywords, judgment in judgment_map:
        for kw in keywords:
            if kw in point_lower:
                return judgment

    # 폴백: point에서 동사 추출 시도
    # "~했다", "~겠다" 등의 패턴에서 추출
    match = re.search(r"([가-힣]+(?:했|겠|하겠|할 수 있))", point)
    if match:
        return match.group(1)

    return "같은 선택을 하겠다"


def _extract_premise_from_point(point: str) -> Tuple[str, str]:
    """이상적 표현에서 숨겨진 전제와 전제가 깨진 상황을 추출

    문장 주제를 먼저 파악하여 주제에 맞는 전제만 선택함.
    예: 고객 관련 문장이 아니면 "고객이 냉담한" 전제 사용 안함.
    """
    # 먼저 문장 주제 파악
    sentence_topic = _get_sentence_topic(point)

    # 키워드 기반 전제 매핑 - 주제별로 분류
    # (keywords, premise, premise_broken, allowed_topics)
    # allowed_topics가 None이면 모든 주제에 사용 가능
    premise_map = [
        # ★ 1순위: 꿈/소망/목표 관련 (모든 주제에 허용)
        (["되고 싶", "싶다는 꿈", "꿈을 품", "꿈을 갖"], "그 꿈을 이룰 기회가 있다는 것", "현실적인 제약으로 그 꿈을 이루기 어려운 상황이라면", None),
        (["꿈", "목표", "비전"], "그 꿈을 향해 나아갈 수 있다는 것", "현실의 벽에 부딪혀 꿈이 흔들리는 상황이라면", None),

        # ★ 2순위: 구체적 상황/행동 (주제별 필터링)
        (["함께", "같이", "협력", "협동", "공동체"], "주변 사람들이 협조적이라는 것", "주변 사람들이 비협조적인 상황이라면", ["team", "general"]),
        (["극복", "이겨", "해결", "넘"], "문제가 해결될 수 있다는 것", "아무리 노력해도 해결되지 않는 상황이라면", None),
        (["소통", "대화", "커뮤니케이션", "이야기"], "상대방이 대화에 응한다는 것", "상대방이 대화 자체를 거부하는 상황이라면", None),
        (["팀워크", "팀", "우리"], "팀원들이 같은 방향을 보고 있다는 것", "팀원들 간 목표가 충돌하는 상황이라면", ["team", "general"]),
        (["고객", "손님", "승객", "탑승객"], "고객이 합리적이라는 것", "고객이 무리한 요구를 계속하는 상황이라면", ["customer"]),
        (["서비스"], "서비스가 환영받는다는 것", "서비스에 대해 무관심하거나 불만족하는 상황이라면", ["customer", "general"]),
        (["신뢰", "믿음", "믿"], "서로 신뢰할 수 있다는 것", "상대방이 약속을 어기거나 배신하는 상황이라면", None),
        (["도전", "새로운", "시도"], "새로운 시도가 환영받는다는 것", "변화를 거부하는 보수적인 환경이라면", None),
        (["의지", "지지", "응원", "도움"], "누군가 옆에서 도와준다는 것", "아무도 도와주지 않고 혼자인 상황이라면", None),
        (["외로", "타지", "낯선", "혼자"], "함께할 사람이 있다는 것", "완전히 혼자이고 의지할 사람이 없는 상황이라면", None),
        (["첫", "처음", "시작"], "첫 경험이 긍정적이라는 것", "첫 경험이 매우 부정적인 상황이라면", None),

        # ★ 3순위: 일반적/추상적 키워드 (주제별 필터링)
        (["웃", "즐거", "긍정", "밝"], "분위기가 좋다는 것", "분위기가 험악하거나 갈등이 심한 상황이라면", None),
        # "미소", "친절" 등은 고객 주제일 때만 "고객이 냉담한" 사용
        (["미소", "친절", "배려", "따뜻", "반겨", "맞이"], "그런 태도가 환영받는다는 것", "상대방이 그런 태도에 냉담하거나 무관심한 상황이라면", ["general", "team", "growth"]),
        (["미소", "친절", "배려", "따뜻", "반겨", "맞이"], "고객이 그런 서비스에 만족한다는 것", "고객이 그런 서비스에 냉담하거나 무관심한 상황이라면", ["customer"]),
        (["성장", "발전", "성공", "이루"], "노력하면 성과가 나온다는 것", "노력해도 성과가 전혀 나오지 않는 상황이라면", None),
        (["최선", "노력", "열심"], "노력이 인정받는다는 것", "아무리 열심히 해도 인정받지 못하는 상황이라면", None),
        (["안정", "평화", "안전"], "환경이 안정적이라는 것", "환경이 불안정하고 예측 불가능한 상황이라면", ["safety", "general"]),
        (["감동", "감사", "고마"], "상대방도 감사함을 느낀다는 것", "내 노력이 당연하게 여겨지는 상황이라면", None),
        (["기억", "잊지", "마음"], "그 기억이 힘이 된다는 것", "그 기억이 오히려 부담이 되는 상황이라면", None),
        (["차별", "공정", "평등", "모두를"], "모든 사람을 동등하게 대할 수 있다는 것", "현실적으로 차별 없이 대하기 어려운 상황이라면", None),
    ]

    point_lower = point.lower()
    for keywords, premise, premise_broken, allowed_topics in premise_map:
        # 주제 필터링: allowed_topics가 None이면 모든 주제 허용
        if allowed_topics is not None and sentence_topic not in allowed_topics:
            continue
        for kw in keywords:
            if kw in point_lower:
                return premise, premise_broken

    # 폴백: 원문에서 핵심 단어를 추출해서 전제 생성
    # "~했다", "~였다" 등의 표현에서 상황 추론
    if "수 있" in point_lower or "할 수" in point_lower:
        return "그것이 가능하다는 것", "그것이 불가능한 상황이라면"
    if "되었" in point_lower or "됐" in point_lower:
        return "긍정적인 결과가 나온다는 것", "결과가 부정적인 상황이라면"

    # 최종 폴백: 원문 기반 자연스러운 전제
    short_point = point[:20] + "..." if len(point) > 20 else point
    return f"'{short_point}'가 가능하다는 것", "그것이 불가능한 상황이라면"


def _apply_airline_tone(question: str, is_fsc: bool, is_soft: bool) -> str:
    """FSC/LCC 톤 규칙을 질문에 적용 (config.py 상수 활용)

    INTERVIEWER_TONE_RULES에서 정의된 규칙 적용:
    - FSC: 말수 적음, 감정 절제, 짧고 단정, 검증/판단/기준 위주
    - LCC: 구어체, 현장 상황 연상, 판단→행동→결과 빠르게 요구

    KOREAN_QUESTION_RULES["forbidden_expressions"]에서 금지 표현 제거
    TONE_CONVERSION_RULES에서 FSC/LCC + SOFT/SHARP 조합별 변환 적용
    """
    if not question:
        return question

    q = question.strip()

    # 금지 표현 제거 (KOREAN_QUESTION_RULES 활용)
    forbidden_expressions = KOREAN_QUESTION_RULES.get("forbidden_expressions", [])
    for expr in forbidden_expressions:
        if expr == "설명해주세요":
            q = q.replace(expr, "말씀해주세요")
        else:
            q = q.replace(expr, "")

    # 톤 변환 키 결정
    if is_fsc:
        tone_key = "FSC_SOFT" if is_soft else "FSC_SHARP"
        # FSC: 불필요한 완충 표현 제거
        fsc_trim = [
            ("혹시 ", ""),
            ("아마 ", ""),
            ("그런데요, ", ""),
            ("그러면요, ", ""),
            ("그럼요, ", ""),
        ]
        for old, new in fsc_trim:
            q = q.replace(old, new)
    else:
        tone_key = "LCC_SOFT" if is_soft else "LCC_SHARP"

    # TONE_CONVERSION_RULES에서 변환 규칙 적용
    tone_rule = TONE_CONVERSION_RULES.get(tone_key, {})
    conversions = tone_rule.get("conversions", [])
    for old, new in conversions:
        q = q.replace(old, new)

    # 중복 공백 제거
    while "  " in q:
        q = q.replace("  ", " ")

    return q.strip()


def _slot_q2_deep(
    base: int,
    version: int,
    qtype: str,
    situation: str,
    llm_item: Optional[Dict[str, Any]],
    basis: str,
    raw_answer: str = "",
    atype: str = "LCC",
) -> Tuple[str, str, str]:
    """Q2: 검증형 심층 질문 (새 프롬프트 기반 - deep_questions 우선 사용)

    FSC/LCC 톤 규칙:
    - FSC: 말수 적음, 감정 절제, 짧고 단정한 문장, 검증/판단/기준 위주
    - LCC: 구어체, 현장 상황 연상, 판단→행동→결과 빠르게 요구
    """

    # 버전에 따라 톤 선택: 홀수(1,3,5...)=날카로운, 짝수(2,4,6...)=부드러운
    is_soft_version = (version % 2 == 0)
    is_fsc = (atype == "FSC")

    # ========================================
    # 새 방식: deep_questions 직접 사용 (우선)
    # ========================================
    deep_questions = _llm_extract_for_slot(llm_item, "deep_questions", [])

    # 디버그: llm_item 상태 확인
    logger.debug(f"[DEBUG] llm_item is None: {llm_item is None}")
    if llm_item:
        logger.debug(f"[DEBUG] llm_item keys: {list(llm_item.keys()) if isinstance(llm_item, dict) else 'not a dict'}")
        logger.debug(f"[DEBUG] deep_questions count: {len(deep_questions) if deep_questions else 0}")

    if deep_questions and isinstance(deep_questions, list) and len(deep_questions) > 0:
        # 버전에 따라 다른 질문 선택
        q_idx = (base + version) % len(deep_questions)
        selected_q = deep_questions[q_idx]

        if isinstance(selected_q, dict):
            q2_text = selected_q.get("question", "")
            source_sentence = selected_q.get("source_sentence", "")

            # 질문이 유효한지 확인
            if q2_text and len(q2_text) >= 10:
                # FSC/LCC 톤 규칙 적용
                q2_text = _apply_airline_tone(q2_text, is_fsc, is_soft_version)

                # Q3용으로 source_sentence와 expected_answers 저장
                # expected_answers는 Q3 생성 시 사용됨
                expected_answers = selected_q.get("expected_answers", [])

                # session_state에 Q3용 데이터 저장 (있으면)
                if expected_answers and hasattr(st, 'session_state'):
                    st.session_state["_q2_expected_answers"] = expected_answers

                return q2_text, source_sentence, source_sentence

    # ========================================
    # 폴백: 기존 방식 (over_idealized_points 등)
    # ========================================
    over_idealized = _llm_extract_for_slot(llm_item, "over_idealized_points", [])
    risk_points = _llm_extract_for_slot(llm_item, "risk_points", [])
    rejected_alts = _llm_extract_for_slot(llm_item, "rejected_alternatives", [])
    claim = _llm_extract_for_slot(llm_item, "claim", "")

    # 유효한 포인트 필터링 (맥락 의존적 문장 + 불완전한 조각 제외)
    valid_idealized = [
        p for p in (over_idealized or [])
        if isinstance(p, str) and p.strip()
        and not _is_context_dependent_sentence(p)
        and is_complete_sentence(p)
    ]
    valid_risks = [
        r for r in (risk_points or [])
        if isinstance(r, str) and r.strip()
        and not _is_context_dependent_sentence(r)
        and is_complete_sentence(r)
    ]
    valid_alts = [
        a for a in (rejected_alts or [])
        if isinstance(a, str) and a.strip()
        and not _is_context_dependent_sentence(a)
        and is_complete_sentence(a)
    ]

    # 공격 포인트 선택 - 버전별로 다른 타입 우선순위 적용
    attack_point = ""
    attack_type = "idealized"

    version_mod = version % 3

    if version_mod == 1:
        priority_order = [
            ("idealized", valid_idealized),
            ("risk", valid_risks),
            ("alternative", valid_alts),
        ]
    elif version_mod == 2:
        priority_order = [
            ("risk", valid_risks),
            ("idealized", valid_idealized),
            ("alternative", valid_alts),
        ]
    else:
        priority_order = [
            ("alternative", valid_alts),
            ("idealized", valid_idealized),
            ("risk", valid_risks),
        ]

    for at, points in priority_order:
        if points:
            idx = (base + version * 7 + hash(at) % 5) % len(points)
            attack_point = normalize_ws(points[idx])
            attack_type = at
            break

    # 폴백 2: 자소서에서 직접 추출
    if not attack_point and raw_answer:
        sentences = split_sentences(raw_answer)
        idealistic_keywords = ["함께", "극복", "소통", "팀워크", "협력", "해결", "성장", "노력", "배려", "따뜻"]
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
            has_keyword = any(kw in sentence for kw in idealistic_keywords)
            if has_keyword and is_complete_sentence(sentence):
                attack_point = normalize_ws(sentence)[:100]
                attack_type = "idealized"
                break

    # 폴백 3: 아무 문장이나
    if not attack_point and raw_answer:
        sentences = split_sentences(raw_answer)
        valid_sentences = [
            s for s in sentences
            if isinstance(s, str) and len(s.strip()) >= 15 and is_complete_sentence(s.strip())
        ]
        if valid_sentences:
            idx = (base + version * 17) % len(valid_sentences)
            attack_point = normalize_ws(valid_sentences[idx])[:100]
            attack_type = "idealized"

    # 폴백 4: claim 사용
    if not attack_point and claim and is_complete_sentence(claim):
        attack_point = claim
        attack_type = "idealized"

    # 유효하지 않으면 기본 질문
    if not attack_point or not is_complete_sentence(attack_point):
        default_questions = [
            "자소서에 적어주신 경험 중 가장 기억에 남는 게 있으신가요?",
            "본인이 생각하는 가장 큰 강점은 무엇인가요?",
            "이 경험을 통해 얻은 가장 큰 교훈이 있다면요?",
            "자소서에 적어주신 내용 중 가장 자신있게 말씀하실 수 있는 부분은요?",
        ]
        q2_text = default_questions[(base + version) % len(default_questions)]
        return q2_text, claim, ""

    # 템플릿 기반 질문 생성 (기존 방식)
    if attack_type == "idealized":
        is_dream = _is_dream_sentence(attack_point)
        is_abstract = _is_abstract_sentence(attack_point)
        premise, premise_broken = _extract_premise_from_point(attack_point)

        if is_dream:
            if is_soft_version:
                templates = Q2_DREAM_TEMPLATES_SOFT
            else:
                templates = Q2_DREAM_TEMPLATES
            tpl_idx = (base + version * 19) % len(templates)
            q2_raw = templates[tpl_idx].format(
                point=attack_point,
                premise=premise,
                premise_broken=premise_broken
            )
        elif is_abstract:
            short_point = _extract_short_point(attack_point)
            if is_soft_version:
                templates = Q2_ABSTRACT_TEMPLATES_SOFT
            else:
                templates = Q2_ABSTRACT_TEMPLATES
            tpl_idx = (base + version * 19) % len(templates)
            q2_raw = templates[tpl_idx].format(
                point=attack_point,
                short_point=short_point
            )
        else:
            judgment = _extract_judgment_from_point(attack_point)
            who = _extract_who_from_context(attack_point, raw_answer)
            if is_soft_version:
                templates = Q2_ATTACK_TEMPLATES_SOFT
            else:
                templates = Q2_ATTACK_TEMPLATES
            tpl_idx = (base + version * 19) % len(templates)
            q2_raw = templates[tpl_idx].format(
                point=attack_point,
                premise=premise,
                premise_broken=premise_broken,
                judgment=judgment,
                who=who
            )

    elif attack_type == "risk":
        if is_soft_version:
            templates = Q2_RISK_TEMPLATES_SOFT
        else:
            templates = Q2_RISK_TEMPLATES
        tpl_idx = (base + version * 19) % len(templates)
        q2_raw = templates[tpl_idx].format(risk=attack_point)

    else:  # alternative
        if is_soft_version:
            templates = Q2_ALTERNATIVE_TEMPLATES_SOFT
        else:
            templates = Q2_ALTERNATIVE_TEMPLATES
        tpl_idx = (base + version * 19) % len(templates)
        q2_raw = templates[tpl_idx].format(alt=attack_point)

    q2_text = _sanitize_question_strict(_fix_particles_after_format(q2_raw))
    q2_text = _apply_airline_tone(q2_text, is_fsc, is_soft_version)

    return q2_text, claim, attack_point


def _generate_predicted_answer(attack_point: str, is_soft: bool) -> str:
    """Q2에 대한 예상 답변을 생성 (강요 X, 추측만)"""
    # 키워드 기반 예상 답변 매핑 (더 많은 키워드)
    prediction_map = [
        (["함께", "같이", "협력", "협동"], "그래도 함께 해결하려 노력하겠다"),
        (["극복", "이겨", "해결", "넘"], "다른 방법을 찾아보겠다"),
        (["소통", "대화", "커뮤니케이션"], "더 적극적으로 소통하겠다"),
        (["팀워크", "팀", "공동체"], "팀을 위해 양보하겠다"),
        (["미소", "친절", "배려", "따뜻", "반겨"], "그래도 친절을 유지하겠다"),
        (["성장", "발전", "성공"], "포기하지 않겠다"),
        (["도전", "새로운", "시도"], "실패해도 배움이 있다"),
        (["최선", "노력", "열심"], "더 열심히 하겠다"),
        (["의지", "지지", "응원", "도움"], "스스로 극복하려 노력하겠다"),
        (["외로", "타지", "낯선"], "혼자서도 버텨보겠다"),
        (["꿈", "목표", "되고 싶"], "꿈을 포기하지 않겠다"),
        (["첫", "처음", "시작"], "다시 시작하겠다"),
        (["감동", "감사", "고마"], "감사하는 마음을 잃지 않겠다"),
        (["기억", "잊지", "마음"], "그 기억을 소중히 간직하겠다"),
        (["신뢰", "믿음"], "신뢰를 회복하려 노력하겠다"),
        (["안정", "평화", "안전"], "침착하게 대응하겠다"),
        (["고객", "서비스", "손님"], "고객 입장에서 생각하겠다"),
    ]

    point_lower = attack_point.lower() if attack_point else ""
    for keywords, prediction in prediction_map:
        for kw in keywords:
            if kw in point_lower:
                return prediction

    return "상황에 맞게 대처하겠다"


def _slot_q3_followup(
    base: int,
    version: int,
    qtype: str,
    llm_item: Optional[Dict[str, Any]],
    claim: str,
    attack_point: str,
    atype: str = "LCC",
) -> str:
    """Q3: 꼬리 질문 (새 프롬프트 기반 - expected_answers 우선 사용)

    핵심 원칙:
    - 답변 강요 X, 사고 확장 O
    - Q2의 연장선 (새로운 주제 도입 금지)
    - "만약", "가능할까요" 같은 열린 표현 사용

    FSC/LCC 톤 규칙도 적용
    """
    is_soft_version = (version % 2 == 0)
    is_fsc = (atype == "FSC")

    # ========================================
    # 새 방식: expected_answers에서 꼬리질문 사용 (우선)
    # ========================================
    expected_answers = None
    if hasattr(st, 'session_state'):
        expected_answers = st.session_state.get("_q2_expected_answers", None)

    if expected_answers and isinstance(expected_answers, list) and len(expected_answers) > 0:
        # 버전에 따라 다른 예상답변/꼬리질문 선택
        ans_idx = (base + version) % len(expected_answers)
        selected_ans = expected_answers[ans_idx]

        if isinstance(selected_ans, dict):
            followup = selected_ans.get("followup", "")

            if followup and len(followup) >= 5:
                # FSC/LCC 톤 규칙 적용
                q3_text = _apply_airline_tone(followup, is_fsc, is_soft_version)
                return q3_text

    # ========================================
    # 폴백: 기존 템플릿 방식
    # ========================================
    premise, premise_broken = _extract_premise_from_point(attack_point)
    is_dream = _is_dream_sentence(attack_point)
    q3_type = (base + version) % 4

    if is_dream:
        if q3_type == 0:
            templates = Q3_DREAM_CONDITION
            tpl_idx = (base + version * 11) % len(templates)
            q3_text = templates[tpl_idx].format(premise_broken=premise_broken)
        elif q3_type == 1:
            templates = Q3_DREAM_PRIORITY
            tpl_idx = (base + version * 13) % len(templates)
            q3_text = templates[tpl_idx]
        elif q3_type == 2:
            templates = Q3_DREAM_LIMIT
            tpl_idx = (base + version * 17) % len(templates)
            q3_text = templates[tpl_idx]
        else:
            templates = Q3_DREAM_REPEAT
            tpl_idx = (base + version * 19) % len(templates)
            q3_text = templates[tpl_idx]
    else:
        if q3_type == 0:
            templates = Q3_CONDITION_CHANGE
            tpl_idx = (base + version * 11) % len(templates)
            q3_text = templates[tpl_idx].format(premise_broken=premise_broken)
        elif q3_type == 1:
            templates = Q3_PRIORITY_CONFLICT
            tpl_idx = (base + version * 13) % len(templates)
            q3_text = templates[tpl_idx]
        elif q3_type == 2:
            templates = Q3_LIMIT_RECOGNITION
            tpl_idx = (base + version * 17) % len(templates)
            q3_text = templates[tpl_idx]
        else:
            templates = Q3_REPEATABILITY
            tpl_idx = (base + version * 19) % len(templates)
            q3_text = templates[tpl_idx]

    q3_text = _sanitize_question_strict(_fix_particles_after_format(q3_text))
    q3_text = _apply_airline_tone(q3_text, is_fsc, is_soft_version)

    return q3_text


def _slot_q5_surprise(base: int, version: int, atype: str = "LCC") -> str:
    """Q5: 항공사 유형(FSC/LCC/HSC)에 맞는 돌발질문 풀에서 선택 (경험형 금지)

    버전에 따라 톤 선택: 홀수(1,3,5)=날카로운, 짝수(2,4,6)=부드러운
    """
    # 버전에 따라 톤 선택
    is_soft_version = (version % 2 == 0)

    # 항공사 유형에 맞는 질문 풀 선택 (버전별 톤 적용)
    if atype == "FSC":
        if is_soft_version:
            pool = Q5_POOL_COMMON_SOFT + Q5_POOL_FSC_SOFT
        else:
            pool = Q5_POOL_COMMON_SHARP + Q5_POOL_FSC_SHARP
    elif atype == "HSC":
        # HSC는 아직 SHARP/SOFT 분리 안 됨 - 기존 풀 사용하되 버전 반영
        if is_soft_version:
            pool = Q5_POOL_COMMON_SOFT + Q5_POOL_HSC
        else:
            pool = Q5_POOL_COMMON_SHARP + Q5_POOL_HSC
    else:  # LCC
        if is_soft_version:
            pool = Q5_POOL_COMMON_SOFT + Q5_POOL_LCC_SOFT
        else:
            pool = Q5_POOL_COMMON_SHARP + Q5_POOL_LCC_SHARP

    if not pool:
        return "압박이 큰 상황에서 설명을 짧게 정리해야 할 때, 어떤 순서로 말하고 어떤 행동부터 실행하겠습니까?"

    idx = (base + version * 17 + 5 * 101) % len(pool)
    q5_raw = pool[idx]

    for forbidden in Q5_FORBIDDEN_WORDS:
        if forbidden in q5_raw:
            for fallback_idx in range(len(pool)):
                alt_idx = (idx + fallback_idx + 1) % len(pool)
                alt = pool[alt_idx]
                if not any(f in alt for f in Q5_FORBIDDEN_WORDS):
                    q5_raw = alt
                    break
            break

    # Q5는 풀에서 가져온 질문을 그대로 사용 (변형 금지)
    return normalize_ws(q5_raw)


def _pick_det_idx(base: int, version: int, slot_seed: int, n: int) -> int:
    if n <= 0:
        return 0
    return (base + version * 17 + slot_seed * 101) % n


def _version_angle(version: int) -> int:
    if version <= 0:
        return 1
    return ((version - 1) % 5) + 1


def _pick_item_index(base: int, version: int, n_items: int) -> int:
    if n_items <= 0:
        return 0
    return (base + version * 7) % n_items


def _pick_basis_ab(base: int, version: int) -> int:
    return (base + version * 11) % 2


def _normalize_airline_name_in_text(text: str, airline: str) -> str:
    t = text
    raw = _raw_airline_key(airline)
    if raw == "제주":
        t = t.replace("제주항공", "제주항공").replace("제주", "제주항공")
    elif raw == "아시아나":
        t = t.replace("아시아나항공", "아시아나항공").replace("아시아나", "아시아나항공")
    elif raw == "티웨이":
        t = t.replace("티웨이항공", "티웨이항공").replace("티웨이", "티웨이항공")
    elif raw == "이스타":
        t = t.replace("이스타항공", "이스타항공").replace("이스타", "이스타항공")
    return t


def _fallback_questions_fixed_slots_item(
    base: int,
    version: int,
    airline: str,
    atype: str,
    item: Dict[str, Any]
) -> Dict[str, Dict[str, str]]:
    """폴백 질문 생성 (공격 포인트 기반 - 새 방식)"""
    qtype = item.get("qtype", "경험 요구형")
    situation = item.get("situation", "현장에서 변수가 발생한 상황")
    raw_answer = item.get("answer", "")
    basisA = (item.get("basisA", {}) or {}).get("text", "")
    basisB = (item.get("basisB", {}) or {}).get("text", "")
    pick_ab = _pick_basis_ab(base, version)
    basis = basisA if pick_ab == 0 else basisB
    if not basis:
        basis = raw_answer[:80] if raw_answer else "자기소개서 답변에서 언급한 내용"

    # 새 방식: _slot_q2_deep과 _slot_q3_followup 호출 (LLM 없이 폴백 사용)
    q1 = _slot_q1_common(base, version, atype)

    # Q2: 공격 포인트 기반 (llm_item=None이면 폴백 로직 작동)
    q2, claim, attack_point = _slot_q2_deep(
        base=base,
        version=version,
        qtype=qtype,
        situation=situation,
        llm_item=None,  # 폴백이므로 LLM 데이터 없음
        atype=atype,  # FSC/LCC 톤 적용
        basis=basis,
        raw_answer=raw_answer,
    )

    # Q3: 재현성/판단기준 기반 (llm_item=None이면 폴백 로직 작동)
    q3 = _slot_q3_followup(
        base=base,
        version=version,
        qtype=qtype,
        llm_item=None,  # 폴백이므로 LLM 데이터 없음
        claim=claim,
        attack_point=attack_point,
        atype=atype,  # FSC/LCC 톤 적용
    )

    # 항공사 유형에 맞는 가치 데이터 선택 (FSC/LCC/HSC)
    if atype == "FSC":
        value_data = FSC_VALUE_DATA
    elif atype == "HSC":
        value_data = HSC_VALUE_DATA
    else:
        value_data = LCC_VALUE_DATA

    # 통합 LCC 항공사(진에어/에어부산/에어서울)는 일부 버전에서 통합 관련 질문 사용
    airline_key = _raw_airline_key(airline)
    use_integration_q = (airline_key in INTEGRATED_LCC_AIRLINES) and (version % 3 == 0)

    if use_integration_q:
        # 통합 LCC 질문 사용
        q4_idx = (base + version) % len(INTEGRATED_LCC_Q_TEMPLATES)
        q4_text = INTEGRATED_LCC_Q_TEMPLATES[q4_idx]
    else:
        # 기존 인재상 질문 사용 (버전별 톤 적용)
        # HSC는 LCC 템플릿 사용 (장거리 특화이지만 저비용 구조 기반)
        # 홀수 버전(1,3,5)=날카로움, 짝수 버전(2,4,6)=부드러움
        is_soft_version = (version % 2 == 0)
        if atype == "FSC":
            value_tpls = VALUE_Q_TEMPLATES_FSC_SOFT if is_soft_version else VALUE_Q_TEMPLATES_FSC_SHARP
        else:
            value_tpls = VALUE_Q_TEMPLATES_LCC_SOFT if is_soft_version else VALUE_Q_TEMPLATES_LCC_SHARP
        q4_tpl_idx = _pick_det_idx(base, version, 4, len(value_tpls))
        kw = value_data.get("keywords", []) or []
        desc = _auto_fix_particles_kor(_sanity_kor_endings(_strip_ellipsis_tokens(value_data.get("desc", ""))))
        if not kw:
            kw = VALUES_DEFAULT.get(atype, VALUES_DEFAULT["LCC"])
        kw1 = kw[(base + version) % len(kw)]
        kw2 = kw[(base + version * 3 + 1) % len(kw)]
        if kw2 == kw1 and len(kw) > 1:
            kw2 = kw[(base + version * 3 + 2) % len(kw)]
        airline_disp = _canonical_airline_name(airline)
        q4_text = value_tpls[q4_tpl_idx].format(airline=airline_disp, kw1=kw1, kw2=kw2, desc=desc)
        q4_text = _normalize_airline_name_in_text(q4_text, airline)

    q4_text = _fix_particles_after_format(q4_text)  # 조사 보정 추가
    q4 = _sanitize_question_strict(q4_text)

    q5 = _slot_q5_surprise(base, version, atype)

    anchor = _pick_anchor_by_rule(
        qtype_internal=qtype,
        action_sents=item.get("action_sents", []) or [],
        result_sents=item.get("result_sents", []) or [],
    )

    basis_summary = _trim_no_ellipsis(f"문항 {item.get('index', 1)} 유형({qtype}) / 근거 후보: {basis}", 180)
    intent2 = "문항 질문과 답변의 쌍을 근거로, 평가자가 보는 포인트를 다른 각도에서 검증하기 위한 질문입니다."
    intent3 = "2번 질문과 동일 문항의 평가 주제를 유지하면서, 답변을 가정하지 않고 독립적으로 검증하기 위한 질문입니다."

    return {
        "q1": {
            "type": "공통 질문",
            "question": q1,
            "basis": build_basis_text(summary=q1, intent="기본 역량과 현장 대응을 확인하기 위한 공통 질문입니다."),
            "anchor": "",
        },
        "q2": {
            "type": "심층(자소서 기반)",
            "question": q2,
            "basis": build_basis_text(summary=basis_summary, intent=intent2),
            "anchor": fmt_anchor_text(anchor),
        },
        "q3": {
            "type": "꼬리 질문",
            "question": q3,
            "basis": build_basis_text(summary=_trim_no_ellipsis(f"문항 {item.get('index', 1)} 평가 주제 유지 / 상황: {situation}", 180), intent=intent3),
            "anchor": fmt_anchor_text(anchor),
        },
        "q4": {
            "type": "인재상/가치",
            "question": q4,
            "basis": build_basis_text(
                summary=f"[{airline_disp}] 핵심가치: {kw1}, {kw2}",
                intent=f"항공사 인재상과의 정합성 확인. {desc}"
            ),
            "anchor": "",
            "value_meta": f"{kw1}|{kw2}",
        },
        "q5": {
            "type": "돌발/확장",
            "question": q5,
            "basis": build_basis_text(summary=q5, intent="압박 상황에서의 사고 정리와 실행 우선순위를 확인하기 위한 질문입니다."),
            "anchor": "",
        },
    }


def generate_questions(essay: str, airline: str, version: int) -> Dict[str, Dict[str, str]]:
    atype = airline_profile(airline)

    essay_hash = hashlib.sha256(essay.encode("utf-8", errors="ignore")).hexdigest() if essay else ""
    cache = _get_or_build_item_analysis_cache(st.session_state.get("qa_sets", []), essay_hash)
    items = cache.get("items", []) or []
    llm_data = _llm_try_extract_or_reuse(st.session_state.get("qa_sets", []), airline=airline)
    llm_items = llm_data.get("items", []) if isinstance(llm_data, dict) else []

    essay_id = stable_int_hash(essay)
    base = stable_int_hash(f"{essay_id}|{airline}|{atype}|{len(items)}")

    if not items:
        dummy_item = {
            "index": 1,
            "qtype": "경험 요구형",
            "situation": "현장에서 변수가 발생한 상황",
            "basisA": {"text": "자기소개서 답변 내용"},
            "basisB": {"text": "자기소개서 답변 내용"},
            "action_sents": [],
            "result_sents": [],
        }
        return _fallback_questions_fixed_slots_item(base=base, version=version, airline=airline, atype=atype, item=dummy_item)

    pick_idx = _pick_item_index(base, version, len(items))
    item = items[pick_idx]

    llm_item = None
    if llm_items and pick_idx < len(llm_items):
        llm_item = llm_items[pick_idx] if isinstance(llm_items[pick_idx], dict) else None

    qtype = item.get("qtype", "경험 요구형")
    situation = item.get("situation", "현장에서 변수가 발생한 상황")
    raw_answer = item.get("answer", "")

    basisA = (item.get("basisA", {}) or {}).get("text", "")
    basisB = (item.get("basisB", {}) or {}).get("text", "")
    pick_ab = _pick_basis_ab(base, version)
    basis = basisA if pick_ab == 0 else basisB
    if not basis:
        basis = raw_answer[:80] if raw_answer else "자기소개서 답변에서 언급한 내용"
    basis = _trim_no_ellipsis(_auto_fix_particles_kor(_sanity_kor_endings(_strip_ellipsis_tokens(basis))), 120)

    angle = _version_angle(version)

    q1_text = _slot_q1_common(base, version, atype)

    # Q2: 공격 포인트 기반 질문 생성 (FSC/LCC 톤 적용)
    q2_text, claim, attack_point = _slot_q2_deep(base, version, qtype, situation, llm_item, basis, raw_answer, atype)

    # Q3: 재현성/판단기준 기반 꼬리 질문 (FSC/LCC 톤 적용)
    q3_text = _slot_q3_followup(base, version, qtype, llm_item, claim, attack_point, atype)

    q5_text = _slot_q5_surprise(base, version, atype)

    # 항공사 유형에 맞는 가치 데이터 선택 (FSC/LCC/HSC)
    if atype == "FSC":
        value_data = FSC_VALUE_DATA
    elif atype == "HSC":
        value_data = HSC_VALUE_DATA
    else:
        value_data = LCC_VALUE_DATA
    # HSC는 LCC 템플릿 사용 (장거리 특화이지만 저비용 구조 기반)
    # 홀수 버전(1,3,5)=날카로움, 짝수 버전(2,4,6)=부드러움
    is_soft_version = (version % 2 == 0)
    if atype == "FSC":
        value_tpls = VALUE_Q_TEMPLATES_FSC_SOFT if is_soft_version else VALUE_Q_TEMPLATES_FSC_SHARP
    else:
        value_tpls = VALUE_Q_TEMPLATES_LCC_SOFT if is_soft_version else VALUE_Q_TEMPLATES_LCC_SHARP

    # 진에어/에어부산/에어서울 통합 LCC 질문 (version % 3 == 0 일 때)
    airline_key = _canonical_airline_name(airline)
    use_integration_q = (airline_key in INTEGRATED_LCC_AIRLINES) and (version % 3 == 0)

    if use_integration_q:
        q4_idx = (base + version) % len(INTEGRATED_LCC_Q_TEMPLATES)
        q4_text = INTEGRATED_LCC_Q_TEMPLATES[q4_idx]
    else:
        q4_tpl_idx = _pick_det_idx(base, version, 4, len(value_tpls))
        kw = value_data.get("keywords", []) or []
        desc = _auto_fix_particles_kor(_sanity_kor_endings(_strip_ellipsis_tokens(value_data.get("desc", ""))))
        if not kw:
            kw = VALUES_DEFAULT.get(atype, VALUES_DEFAULT["LCC"])
        kw1 = kw[(base + version) % len(kw)]
        kw2 = kw[(base + version * 3 + 1) % len(kw)]
        if kw2 == kw1 and len(kw) > 1:
            kw2 = kw[(base + version * 3 + 2) % len(kw)]
        airline_disp = airline_key
        q4_text = value_tpls[q4_tpl_idx].format(airline=airline_disp, kw1=kw1, kw2=kw2, desc=desc)
        q4_text = _normalize_airline_name_in_text(q4_text, airline)
        q4_text = _fix_particles_after_format(q4_text)  # 조사 보정 추가
    q4_text = _sanitize_question_strict(q4_text)

    anchor = _pick_anchor_by_rule(
        qtype_internal=qtype,
        action_sents=item.get("action_sents", []) or [],
        result_sents=item.get("result_sents", []) or [],
    )
    anchor = fmt_anchor_text(anchor)

    # 새 공격 포인트 기반 근거 텍스트
    attack_info = _trim_no_ellipsis(f"공격 포인트: {attack_point}", 100) if attack_point else ""
    claim_info = _trim_no_ellipsis(f"주장: {claim}", 80) if claim else ""
    basis_summary = _trim_no_ellipsis(f"문항 {item.get('index', 1)} / {attack_info}", 180)
    intent2 = "자소서의 이상적 표현이나 취약 지점을 공격하여 지원자의 신념을 검증하는 질문입니다."
    intent3 = "Q2의 답변을 전제하지 않고, 재현성과 판단 기준을 독립적으로 검증하는 꼬리 질문입니다."

    out: Dict[str, Dict[str, str]] = {
        "q1": {
            "type": "공통 질문",
            "question": q1_text,
            "basis": build_basis_text(summary=q1_text, intent="기본 역량과 현장 대응을 확인하기 위한 공통 질문입니다."),
            "anchor": "",
        },
        "q2": {
            "type": "심층(자소서 기반)",
            "question": q2_text,
            "basis": build_basis_text(summary=basis_summary, intent=intent2),
            "anchor": anchor,
        },
        "q3": {
            "type": "꼬리 질문",
            "question": q3_text,
            "basis": build_basis_text(summary=_trim_no_ellipsis(f"문항 {item.get('index', 1)} 평가 주제 유지 / 상황: {situation}", 180), intent=intent3),
            "anchor": anchor,
        },
        "q4": {
            "type": "인재상/가치",
            "question": q4_text,
            "basis": build_basis_text(
                summary=f"[{airline_disp}] 핵심가치: {kw1}, {kw2}",
                intent=f"항공사 인재상과의 정합성 확인. {desc}"
            ),
            "anchor": "",
            "value_meta": f"{kw1}|{kw2}",
        },
        "q5": {
            "type": "돌발/확장",
            "question": q5_text,
            "basis": build_basis_text(summary=q5_text, intent="압박 상황에서의 사고 정리와 실행 우선순위를 확인하기 위한 질문입니다."),
            "anchor": "",
        },
    }
    return out


def safe_generate_questions(essay: str, airline: str, version: int) -> Dict[str, Dict[str, str]]:
    start = time.monotonic()
    atype = airline_profile(airline)
    essay_id = stable_int_hash(essay)
    essay_hash = hashlib.sha256(essay.encode("utf-8", errors="ignore")).hexdigest() if essay else ""

    cache = _get_or_build_item_analysis_cache(st.session_state.get("qa_sets", []), essay_hash)
    items = cache.get("items", []) or []
    base = stable_int_hash(f"{essay_id}|{airline}|{atype}|{len(items)}")

    try:
        out = generate_questions(essay=essay, airline=airline, version=version)
        if (time.monotonic() - start) > SOFT_TIMEOUT_SEC:
            if items:
                pick_idx = _pick_item_index(base, version, len(items))
                return _fallback_questions_fixed_slots_item(base=base, version=version, airline=airline, atype=atype, item=items[pick_idx])
            dummy_item = {"index": 1, "qtype": "경험 요구형", "situation": "현장에서 변수가 발생한 상황", "basisA": {"text": "자기소개서 답변 내용"}, "basisB": {"text": "자기소개서 답변 내용"}, "action_sents": [], "result_sents": []}
            return _fallback_questions_fixed_slots_item(base=base, version=version, airline=airline, atype=atype, item=dummy_item)

        for k in ["q1", "q2", "q3", "q4", "q5"]:
            if not out.get(k) or not out[k].get("question"):
                if items:
                    pick_idx = _pick_item_index(base, version, len(items))
                    return _fallback_questions_fixed_slots_item(base=base, version=version, airline=airline, atype=atype, item=items[pick_idx])
                dummy_item = {"index": 1, "qtype": "경험 요구형", "situation": "현장에서 변수가 발생한 상황", "basisA": {"text": "자기소개서 답변 내용"}, "basisB": {"text": "자기소개서 답변 내용"}, "action_sents": [], "result_sents": []}
                return _fallback_questions_fixed_slots_item(base=base, version=version, airline=airline, atype=atype, item=dummy_item)
        return out
    except Exception:
        if items:
            pick_idx = _pick_item_index(base, version, len(items))
            return _fallback_questions_fixed_slots_item(base=base, version=version, airline=airline, atype=atype, item=items[pick_idx])
        dummy_item = {"index": 1, "qtype": "경험 요구형", "situation": "현장에서 변수가 발생한 상황", "basisA": {"text": "자기소개서 답변 내용"}, "basisB": {"text": "자기소개서 답변 내용"}, "action_sents": [], "result_sents": []}
        return _fallback_questions_fixed_slots_item(base=base, version=version, airline=airline, atype=atype, item=dummy_item)


# ----------------------------
# STEP 6: 사실 기반 피드백
# ----------------------------

def overlap_keywords(answer: str, keywords: List[str]) -> List[str]:
    if not answer:
        return []
    hits = []
    for k in keywords:
        if k and (k in answer):
            hits.append(k)
    return hits


def answer_has_specifics(answer: str) -> bool:
    if not answer:
        return False
    if re.search(r"\d", answer):
        return True
    if re.search(r"(언제|어디서|누구|몇|기간|횟수|비율|퍼센트|명|건|만원|원|시간|분)", answer):
        return True
    return False


def build_feedback_kor(qtype: str, anchor: str, basis: str, answer: str, risk_keywords: List[str], evidence: List[str], value_meta: str = "") -> str:
    if not answer.strip():
        return ""

    hits = overlap_keywords(answer, risk_keywords)
    specifics = answer_has_specifics(answer)

    grounded = False
    if anchor:
        a = anchor[:60]
        grounded = (a in answer) or (len(hits) > 0)

    evidence_pick = ""
    if evidence and hits:
        for s in evidence:
            if any(h in s for h in hits[:5]):
                evidence_pick = s
                break
    if not evidence_pick and evidence:
        evidence_pick = evidence[0]

    lines = []
    lines.append("텍스트 근거 기반 점검:")

    if qtype == "인재상/가치" and value_meta:
        try:
            fit, conf = value_meta.split("|", 1)
        except Exception:
            fit, conf = "", ""
        if fit and conf:
            lines.append(f"- 가치 언급 여부(적합/충돌): {'적합' if fit in answer else '적합 미언급'} / {'충돌' if conf in answer else '충돌 미언급'}")
        else:
            lines.append("- 가치 언급 여부: 확인 불가(값 메타 누락)")

        lines.append(f"- 구체성(숫자/기간/장소/대상): {'있음' if specifics else '부족'}")
        lines.append("- 요구사항 충족 여부: '가치 2개(적합/충돌) + 자소서 경험 근거'가 답변에 포함되어야 함")
        if not specifics:
            lines.append("- 보완: 근거 경험을 행동/결과(수치)로 고정해서 말할 것")
        return "\n".join(lines)

    if hits:
        lines.append(f"- 위험 신호 키워드와의 연계: {', '.join(hits[:8])}")
    else:
        lines.append("- 위험 신호 키워드와의 연계: 감지되지 않음(자소서 표현을 그대로 가져와 검증 가능하게 답변할 것).")
    lines.append(f"- 구체성(숫자/기간/장소/대상): {'있음' if specifics else '부족'}")
    if anchor:
        lines.append(f"- 앵커(근거 표현) 연계: {'있음' if grounded else '약함'}")
    if evidence_pick:
        lines.append(f"- 참고 근거 문장: \"{evidence_pick[:180]}{'...' if len(evidence_pick) > 180 else ''}\"")
    lines.append("개선 포인트(검증 가능하게):")
    lines.append("- 주장 1개를 고르고, 그 주장에 대한 근거(수치/기간/행동)를 바로 제시.")
    if not specifics:
        lines.append("- 최소 1개 지표(건수/%, 시간/기간, 고객영향)를 넣어 답변을 확정적으로 만들기.")
    return "\n".join(lines)


# ----------------------------
# 커서 CSS
# ----------------------------

_AIRPLANE_CURSOR_SVG = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 64 64'>"
    "<path d='M2 34l60-10-60-10 8 10 14 4v12l-14 4-8 10z' fill='black'/>"
    "</svg>"
)

st.markdown(
    f"""
    <meta name="google" content="notranslate">
    <meta name="robots" content="notranslate">
    <style>
      /* 구글 번역 방지 */
      html {{
        translate: no;
      }}
      .stApp, .stApp * {{
        cursor: url("{_AIRPLANE_CURSOR_SVG}") 4 4, auto !important;
      }}
      .stApp input, .stApp textarea, .stApp [contenteditable="true"] {{
        cursor: text !important;
      }}
      .stApp button, .stApp a, .stApp [role="button"] {{
        cursor: pointer !important;
      }}
      /* 질문 생성 버튼 - 부드러운 파스텔 블루 */
      button[kind="primary"] {{
        background-color: #A8D8EA !important;
        border-color: #A8D8EA !important;
        color: #2C3E50 !important;
      }}
      button[kind="primary"]:hover {{
        background-color: #8BC9DE !important;
        border-color: #8BC9DE !important;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

# 구글 번역 방지 - HTML lang 속성
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# ----------------------------
# UI / App
# ----------------------------

st.set_page_config(page_title="AI 면접 코칭 MVP", layout="wide")

if "question_version" not in st.session_state:
    st.session_state.question_version = 1
if "last_essay_hash" not in st.session_state:
    st.session_state.last_essay_hash = ""
if "questions" not in st.session_state:
    st.session_state.questions = {}
if "answers" not in st.session_state:
    st.session_state.answers = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": ""}
if "feedback" not in st.session_state:
    st.session_state.feedback = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": ""}
if "report_text" not in st.session_state:
    st.session_state.report_text = ""
if "q3_generated" not in st.session_state:
    st.session_state.q3_generated = False
if "_regen_last_request_id" not in st.session_state:
    st.session_state._regen_last_request_id = ""
if "_regen_in_progress" not in st.session_state:
    st.session_state._regen_in_progress = False
if "qa_sets" not in st.session_state:
    st.session_state.qa_sets = [{"prompt": "", "answer": ""}]

st.title("승무원 AI 면접 코칭")
st.caption("자소서 기반 면접 질문 생성 및 답변 연습")
colL, colR = st.columns([1, 1])

with colL:
    st.subheader("STEP 1) 기본 설정")
    airline_raw = st.selectbox(
        "지원 항공사",
        AIRLINES,
        index=AIRLINES.index("에어로케이") if "에어로케이" in AIRLINES else 0,
        format_func=_canonical_airline_name,
    )
    airline = _canonical_airline_name(airline_raw)
    st.session_state.selected_airline = airline  # LLM 호출 시 FSC/LCC 구분용
    atype = airline_profile(airline)
    st.info(f"항공사 타입: {atype}")
    st.caption("면접 언어: 한국어(고정)")

    # 항공사별 선호 인재상 표시
    airline_key = _raw_airline_key(airline)
    pref_type = AIRLINE_PREFERRED_TYPE.get(airline_key, {})
    if pref_type:
        st.markdown(f"**2026 선호 인재상:** {pref_type.get('nickname', '')}")
        st.caption(f"{pref_type.get('description', '')}")

    # 영어 면접 있는 항공사 안내
    if airline_key in ENGLISH_INTERVIEW_AIRLINES:
        st.warning("이 항공사는 **영어 면접 전형**이 있습니다.")

    # 이력서 정보 입력 (Basic/Pro 요금제용)
    current_plan = st.session_state.get("current_plan", DEFAULT_PLAN)
    plan_config = PLAN_CONFIG.get(current_plan, PLAN_CONFIG["basic"])

    if plan_config.get("resume_questions", 0) > 0:
        with st.expander("이력서 정보 (선택)", expanded=False):
            st.caption("개인정보 없이 필요한 항목만 선택하세요.")

            # 이력서 세션 상태 초기화
            if "resume_data" not in st.session_state:
                st.session_state.resume_data = {}

            resume_major = st.selectbox(
                "전공 계열",
                options=RESUME_MAJOR_OPTIONS,
                index=0,
                key="resume_major"
            )
            resume_exp = st.selectbox(
                "총 경력 기간",
                options=RESUME_EXPERIENCE_OPTIONS,
                index=0,
                key="resume_exp"
            )
            resume_gap = st.selectbox(
                "경력 공백",
                options=RESUME_GAP_OPTIONS,
                index=0,
                key="resume_gap"
            )

            st.markdown("**해당 항목 체크**")
            has_short_career = st.checkbox("1년 미만 퇴사 경력", key="has_short_career")
            has_overseas = st.checkbox("해외 경험 (어학연수/교환학생/워홀)", key="has_overseas")
            has_service_exp = st.checkbox("서비스직 경험", key="has_service_exp")
            has_language_cert = st.checkbox("어학 자격증 (토익/토플/HSK 등)", key="has_language_cert")
            major_mismatch = st.checkbox("전공-직무 연관성 낮음", key="major_mismatch")

            # 세션에 저장
            st.session_state.resume_data = {
                "major": resume_major,
                "experience": resume_exp,
                "gap": resume_gap,
                "has_short_career": has_short_career,
                "has_overseas": has_overseas,
                "has_service_exp": has_service_exp,
                "has_language_cert": has_language_cert,
                "major_mismatch": major_mismatch,
            }

with colR:
    st.subheader("STEP 2) 자기소개서 입력 (최대 5,000자)")
    add_col, _sp = st.columns([1, 3])
    with add_col:
        if st.button("+ 문항 추가", use_container_width=True):
            st.session_state.qa_sets.append({"prompt": "", "answer": ""})

    to_delete: Optional[int] = None
    for i, item in enumerate(st.session_state.qa_sets):
        top = st.columns([1, 1, 1, 1, 1])
        with top[0]:
            st.write(f"문항 {i+1}")
        with top[4]:
            if st.button("문항 삭제", key=f"del_{i}", use_container_width=True, disabled=(len(st.session_state.qa_sets) <= 1)):
                to_delete = i

        st.session_state.qa_sets[i]["prompt"] = st.text_input(
            "[문항 질문]",
            value=st.session_state.qa_sets[i].get("prompt", ""),
            key=f"prompt_{i}",
        )
        st.session_state.qa_sets[i]["answer"] = st.text_area(
            "[내 답변]",
            value=st.session_state.qa_sets[i].get("answer", ""),
            height=180,
            key=f"answer_{i}",
        )

    if to_delete is not None and len(st.session_state.qa_sets) > 1:
        st.session_state.qa_sets.pop(to_delete)
        st.rerun()

essay = "\n".join([normalize_ws(x.get("answer", "")) for x in st.session_state.qa_sets if normalize_ws(x.get("answer", ""))]).strip()

current_hash = hashlib.sha256(essay.encode("utf-8", errors="ignore")).hexdigest() if essay else ""
if st.session_state.last_essay_hash and current_hash and current_hash != st.session_state.last_essay_hash:
    st.session_state.question_version = 1
    st.session_state.questions = {}
    st.session_state.answers = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": ""}
    st.session_state.feedback = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": ""}
    st.session_state.report_text = ""
    st.session_state.q3_generated = False  # Q3 동적 생성 플래그 리셋
    st.session_state._regen_last_request_id = ""
    st.session_state._regen_in_progress = False
    st.session_state.ps_srcai_sentences = []
    st.session_state.ps_srcai_roles = []
    st.session_state.ps_srcai_selected_actions = []
    st.session_state.ps_srcai_selected_results = []
    st.session_state.ps_srcai_selected_questionables = []

st.session_state.last_essay_hash = current_hash
_srcai_apply_to_qa_sets(st.session_state.get("qa_sets", []))

st.divider()

# 리셋 버튼만 상단에 배치 (질문 생성 버튼은 STEP 4~5로 이동)
reset_col, info_col = st.columns([1, 3])
with reset_col:
    reset = st.button("리셋", use_container_width=True)
with info_col:
    st.caption("👇 아래 'STEP 4~5) 면접 질문' 옆의 **질문 생성** 버튼을 눌러주세요.")

if reset:
    st.session_state.question_version = 1
    st.session_state.questions = {}
    st.session_state.answers = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": ""}
    st.session_state.feedback = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": ""}
    st.session_state.report_text = ""
    st.session_state.q3_generated = False  # Q3 동적 생성 플래그 리셋
    st.session_state._regen_last_request_id = ""
    st.session_state._regen_in_progress = False
    st.rerun()

st.subheader("STEP 3) 자기소개서 분석")
if essay.strip():
    # 첫 진입 시 자동으로 LLM 호출 시도
    _ensure_llm_state_boxes()
    _llm_gc()

    llm_hash = _calc_llm_hash_from_qa_sets(st.session_state.get("qa_sets", []))
    llm_box = st.session_state.get("_llm_extract_box", {}) or {}
    rec_before = llm_box.get(llm_hash, {}) if llm_hash else {}
    llm_state_before = rec_before.get("state", "NO_RECORD") if isinstance(rec_before, dict) else "NO_RECORD"

    # NO_RECORD 상태면 자동으로 LLM 호출 (첫 진입 시)
    if llm_state_before == "NO_RECORD":
        with st.spinner("🔄 자기소개서를 분석 중입니다... (최초 1회, 약 10~20초 소요)"):
            cache = _get_or_build_item_analysis_cache(st.session_state.qa_sets, current_hash, force_rebuild=True)
    else:
        cache = _get_or_build_item_analysis_cache(st.session_state.qa_sets, current_hash)

    # LLM 추출 데이터 우선 사용, 없으면 폴백
    llm_data = None
    if llm_hash:
        rec = (st.session_state.get("_llm_extract_box", {}) or {}).get(llm_hash, {})
        if isinstance(rec, dict) and isinstance(rec.get("data"), dict):
            llm_data = rec.get("data")

    # 핵심 키워드: LLM 추출 > 폴백
    display_keywords = []
    if llm_data and llm_data.get("items"):
        for item in llm_data["items"]:
            if isinstance(item, dict):
                kw = item.get("key_keywords", [])
                if isinstance(kw, list):
                    display_keywords.extend(kw)
    if not display_keywords:
        display_keywords = cache.get("agg_risk", []) or cache.get("agg_keywords", []) or []

    # 근거 문장: LLM 추출 > 폴백
    display_evidence = []
    if llm_data and llm_data.get("items"):
        for item in llm_data["items"]:
            if isinstance(item, dict):
                ev = item.get("evidence_sentences", [])
                if isinstance(ev, list):
                    display_evidence.extend(ev)
    if not display_evidence:
        display_evidence = cache.get("agg_evidence", []) or []

    # 중복 제거
    display_keywords = list(dict.fromkeys(display_keywords))[:10]
    display_evidence = list(dict.fromkeys(display_evidence))[:8]

    st.markdown("### 자소서 분석 결과")
    st.caption("면접관이 주목할 키워드와 질문의 근거가 될 문장입니다.")

    c2, c3 = st.columns([1, 1])
    with c2:
        st.markdown("**핵심 키워드** (면접관이 물어볼 포인트)")
        if display_keywords:
            # 키워드를 태그처럼 표시
            keyword_html = " ".join([f"<span style='background-color:#e8f4f8;padding:4px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:14px;'>{kw}</span>" for kw in display_keywords])
            st.markdown(keyword_html, unsafe_allow_html=True)
        else:
            st.write("-")
    with c3:
        st.markdown("**근거 문장** (질문의 출처가 되는 문장)")
        if display_evidence:
            for i, s in enumerate(display_evidence, 1):
                # 문장이 너무 길면 자르기
                display_s = s[:100] + "..." if len(s) > 100 else s
                st.markdown(f"<div style='background-color:#f9f9f9;padding:8px 12px;border-left:3px solid #4a90d9;margin:4px 0;font-size:13px;'>{i}. {display_s}</div>", unsafe_allow_html=True)
        else:
            st.write("-")

    # LLM 호출 후 상태 다시 확인
    rec = (st.session_state.get("_llm_extract_box", {}) or {}).get(llm_hash, {}) if llm_hash else {}
    llm_state = rec.get("state", "NO_RECORD") if isinstance(rec, dict) else "NO_RECORD"
    llm_reason = rec.get("reason", "") if isinstance(rec, dict) else ""
    has_llm_data = bool(isinstance(rec, dict) and isinstance(rec.get("data"), dict))

    # LLM 상태에 따른 사용자 안내 (더 눈에 띄게)
    if llm_state == "FAILED":
        st.error(f"❌ {llm_reason}" if llm_reason else "❌ 분석에 실패했습니다.")
        st.warning("👆 위의 '질문 생성/갱신' 버튼을 다시 한번 눌러주세요. 죄송합니다.")
    elif llm_state == "PENDING":
        st.info("🔄 자소서 분석 중입니다. 잠시만 기다려주세요...")
    elif llm_state == "COMPLETED" and has_llm_data:
        st.success("✅ 자소서 분석 완료! 이제 '질문 생성/갱신' 버튼을 눌러 질문을 생성하세요.")
    elif llm_state == "NO_RECORD" and essay.strip():
        # 첫 진입 후에도 NO_RECORD면 API 문제
        st.warning("⚠️ 분석을 시작하지 못했습니다. '질문 생성/갱신' 버튼을 눌러주세요.")

    # 개발자용 디버그 정보 (접을 수 있게)
    with st.expander("[DEV] LLM 상태 상세", expanded=False):
        st.caption(
            f"상태={llm_state} / data={'Y' if has_llm_data else 'N'}"
            + (f" / reason={llm_reason}" if llm_reason else "")
        )

st.divider()

# STEP 4~5 헤더와 질문생성 버튼을 나란히 배치
step_header_col, step_btn_col = st.columns([2.5, 1.5])
with step_header_col:
    st.subheader("STEP 4~5) 면접 질문 5문항")
with step_btn_col:
    regen_step45 = st.button("질문 생성/갱신", key="regen_step45", use_container_width=True, type="primary", disabled=(not essay.strip()))

# STEP 4~5 버튼 클릭 시 전체 로직 실행
if regen_step45:
    current_ver = st.session_state.question_version
    st.session_state.question_version = (current_ver % 6) + 1
    request_id = hashlib.sha256(
        f"{current_hash}|{airline}|{st.session_state.question_version}".encode("utf-8", errors="ignore")
    ).hexdigest()

    should_run = (
        (not st.session_state._regen_in_progress)
        and (request_id != st.session_state._regen_last_request_id)
    )

    if should_run:
        st.session_state._regen_in_progress = True
        try:
            # LLM 실패 상태였다면 재시도를 위해 force_rebuild=True
            llm_hash_45 = _calc_llm_hash_from_qa_sets(st.session_state.qa_sets)
            llm_box_45 = st.session_state.get("_llm_extract_box", {})
            llm_rec_45 = llm_box_45.get(llm_hash_45, {}) if llm_hash_45 and isinstance(llm_box_45, dict) else {}
            llm_state_45 = llm_rec_45.get("state", "") if isinstance(llm_rec_45, dict) else ""
            need_rebuild = llm_state_45 in ("FAILED", "NO_RECORD", "")

            _get_or_build_item_analysis_cache(st.session_state.qa_sets, current_hash, force_rebuild=need_rebuild)
            st.session_state.questions = safe_generate_questions(
                essay=essay,
                airline=airline,
                version=st.session_state.question_version,
            )

            # 이력서 기반 질문 생성 (Basic/Pro 요금제)
            resume_data = st.session_state.get("resume_data", {})
            num_resume_q = plan_config.get("resume_questions", 0)
            if num_resume_q > 0 and resume_data:
                resume_qs = generate_resume_questions(resume_data, airline, num_resume_q)
                if resume_qs:
                    st.session_state.resume_questions = resume_qs
                    st.session_state.resume_data = {}
                else:
                    st.session_state.resume_questions = []
            else:
                st.session_state.resume_questions = []

            st.session_state._regen_last_request_id = request_id
        finally:
            st.session_state._regen_in_progress = False

    st.session_state.answers = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": "", "r1": "", "r2": ""}
    st.session_state.feedback = {"q1": "", "q2": "", "q3": "", "q4": "", "q5": "", "r1": "", "r2": ""}
    st.session_state.report_text = ""
    st.session_state.q3_generated = False
    st.rerun()

if st.session_state.questions:
    st.caption(f"현재 버전: {st.session_state.question_version} / 버튼을 눌러 다른 각도의 질문을 받아보세요")
    for key in ["q1", "q2", "q3", "q4", "q5"]:
        qobj = st.session_state.questions.get(key, {})
        qtype = qobj.get("type", "")
        qtext = qobj.get("question", "")
        basis = qobj.get("basis", "")
        anchor = qobj.get("anchor", "")

        with st.expander(f"{key.upper()} · {qtype}", expanded=True):
            # Q3 특별 처리: Q2 답변 기반 동적 생성
            if key == "q3":
                q2_answer = st.session_state.answers.get("q2", "").strip()
                q2_question = st.session_state.questions.get("q2", {}).get("question", "")

                # Q3가 동적 생성되지 않았고, Q2 답변이 충분하면 생성 버튼 표시
                if not st.session_state.get("q3_generated", False):
                    if q2_answer and len(q2_answer) >= 20:
                        st.info("Q2 답변을 기반으로 맞춤형 꼬리질문을 생성할 수 있습니다.")
                        if st.button("Q3 꼬리질문 생성", key="gen_q3_btn", type="primary"):
                            with st.spinner("Q3 생성 중..."):
                                new_q3 = generate_q3_from_answer(q2_question, q2_answer)
                                if new_q3:
                                    st.session_state.questions["q3"]["question"] = new_q3
                                    st.session_state.questions["q3"]["basis"] = "Q2 답변 기반 AI 동적 생성"
                                    st.session_state.q3_generated = True
                                    st.rerun()
                                else:
                                    st.error("Q3 생성에 실패했습니다. 기존 질문을 사용합니다.")
                    elif q2_answer:
                        st.warning("Q2 답변을 조금 더 입력하세요. (최소 20자)")
                    else:
                        st.warning("Q2 답변을 먼저 입력하세요. 답변을 기반으로 맞춤형 꼬리질문을 생성합니다.")

            st.markdown(f"**질문**\n\n{qtext}")
            if basis:
                st.markdown(f"**생성 근거**\n\n- {basis}")
            elif anchor:
                st.markdown(f"**생성 근거**\n\n- 이 질문은 자기소개서의 \"{anchor}\" 표현을 기반으로 생성됨")

            st.session_state.answers[key] = st.text_area(
                f"{key.upper()} 답변",
                value=st.session_state.answers.get(key, ""),
                height=120,
                key=f"ans_{key}",
            )

    # 이력서 기반 질문 표시 (Basic/Pro 요금제)
    resume_questions = st.session_state.get("resume_questions", [])
    if resume_questions:
        st.divider()
        st.subheader("이력서 기반 추가 질문")
        st.caption("이력서 정보를 기반으로 생성된 예상 질문입니다.")

        for i, rq in enumerate(resume_questions, 1):
            rkey = f"r{i}"
            with st.expander(f"R{i} · 이력서 검증", expanded=True):
                st.markdown(f"**질문**\n\n{rq}")
                st.markdown("**생성 근거**\n\n- 이력서 정보 기반 AI 생성")

                if rkey not in st.session_state.answers:
                    st.session_state.answers[rkey] = ""
                st.session_state.answers[rkey] = st.text_area(
                    f"R{i} 답변",
                    value=st.session_state.answers.get(rkey, ""),
                    height=120,
                    key=f"ans_{rkey}",
                )

    st.divider()
    st.subheader("STEP 6~7) 사실 기반 피드백 & 리포트")

    fb_btn, rep_btn = st.columns([1, 1])
    with fb_btn:
        do_feedback = st.button("피드백 생성", use_container_width=True)
    with rep_btn:
        do_report = st.button("리포트 생성", use_container_width=True)

    cache = _get_or_build_item_analysis_cache(st.session_state.qa_sets, current_hash)
    evidence = cache.get("agg_evidence", []) or []
    risk_keywords = cache.get("agg_risk", []) or []
    if not risk_keywords:
        risk_keywords = cache.get("agg_keywords", []) or []
    items = split_essay_items(essay)

    if do_feedback:
        # Q2 답변 미리 가져오기 (Q3 분석에 필요)
        q2_answer_for_q3 = st.session_state.answers.get("q2", "")

        # 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()

        question_labels = {"q1": "Q1 공통", "q2": "Q2 검증", "q3": "Q3 꼬리", "q4": "Q4 인재상", "q5": "Q5 돌발"}
        keys_to_process = ["q1", "q2", "q3", "q4", "q5"]

        for idx, key in enumerate(keys_to_process):
            status_text.text(f"분석 중... {question_labels.get(key, key)}")
            progress_bar.progress((idx + 1) / len(keys_to_process))

            qobj = st.session_state.questions.get(key, {})
            qtype = qobj.get("type", "")
            qtext = qobj.get("question", "")
            anchor = qobj.get("anchor", "")
            basis = qobj.get("basis", "")
            ans = st.session_state.answers.get(key, "")

            # 답변이 없으면 스킵
            if not ans or not ans.strip():
                st.session_state.feedback[key] = ""
                continue

            # 새 피드백 분석 시스템 사용
            # Set B (Q2, Q3)에는 공격 포인트와 자소서 컨텍스트 전달
            if key in ("q2", "q3"):
                # 공격 포인트: anchor 또는 basis에서 추출
                attack_point = anchor if anchor else basis
                # 자소서 컨텍스트: 전체 에세이 요약
                essay_context = "\n".join(evidence[:5]) if evidence else ""
                # Q3의 경우 Q2 답변도 전달
                q2_ans = q2_answer_for_q3 if key == "q3" else ""

                st.session_state.feedback[key] = analyze_answer(
                    question_key=key,
                    question_text=qtext,
                    user_answer=ans,
                    question_type=qtype,
                    attack_point=attack_point,
                    essay_context=essay_context,
                    q2_answer=q2_ans,
                    airline=airline,
                )
            else:
                # Set A (Q1, Q4, Q5)
                st.session_state.feedback[key] = analyze_answer(
                    question_key=key,
                    question_text=qtext,
                    user_answer=ans,
                    question_type=qtype,
                    airline=airline,
                )

        progress_bar.empty()
        status_text.empty()
        st.success("피드백 분석 완료!")

    if any(v.strip() for v in st.session_state.feedback.values()):
        st.markdown("### 피드백 분석 결과")
        question_labels = {"q1": "Q1 공통질문", "q2": "Q2 자소서검증", "q3": "Q3 꼬리질문", "q4": "Q4 인재상", "q5": "Q5 돌발질문"}

        for key in ["q1", "q2", "q3", "q4", "q5"]:
            fb = st.session_state.feedback.get(key, "")
            if fb.strip():
                with st.expander(f"{question_labels.get(key, key.upper())} 피드백", expanded=True):
                    # 피드백 내용을 섹션별로 하이라이트
                    for line in fb.split("\n"):
                        if line.startswith("[") and line.endswith("]"):
                            # 섹션 헤더
                            st.markdown(f"**{line}**")
                        elif line.strip().startswith("-") or line.strip().startswith("•"):
                            st.markdown(line)
                        elif line.strip():
                            st.markdown(line)

    if do_report:
        lines = []
        lines.append("AI 면접 코칭 결과 리포트 (MVP)")
        lines.append("=" * 40)
        lines.append(f"지원 항공사: {airline} / 타입: {atype}")
        lines.append("면접 언어: 한국어")
        lines.append(f"질문 버전(세션 카운터): {st.session_state.question_version}")
        lines.append("")
        lines.append("[자기소개서 요약]")
        lines.append("- 문항 수: " + str(len(items)))
        lines.append("- 핵심 키워드: " + (", ".join(risk_keywords[:14]) if risk_keywords else "-"))
        lines.append("- 근거 문장(상위):")
        for s in evidence[:6]:
            lines.append(f"  * {s}")
        prompts = [normalize_ws(x.get("prompt", "")) for x in st.session_state.qa_sets if normalize_ws(x.get("prompt", ""))]
        if prompts:
            lines.append("- 사용자 입력 문항 질문:")
            for p in prompts[:20]:
                lines.append(f"  * {p}")

        lines.append("")
        lines.append("[면접 질문/답변/피드백]")
        for key in ["q1", "q2", "q3", "q4", "q5"]:
            qobj = st.session_state.questions.get(key, {})
            qtype = qobj.get("type", "")
            qtext = qobj.get("question", "")
            basis = qobj.get("basis", "")
            ans = st.session_state.answers.get(key, "").strip()
            fb = st.session_state.feedback.get(key, "").strip()

            lines.append("-" * 40)
            lines.append(f"{key.upper()} ({qtype})")
            lines.append(f"Q: {qtext}")
            if basis:
                lines.append(f"근거: {basis}")
            lines.append("A: " + (ans if ans else "(미입력)"))
            if fb:
                lines.append("Feedback:")
                for l in fb.splitlines():
                    lines.append(f"  {l}")
            else:
                lines.append("Feedback: (미생성)")
        lines.append("")
        st.session_state.report_text = "\n".join(lines)

    if st.session_state.report_text.strip():
        st.markdown("### 결과 리포트")
        st.code(st.session_state.report_text, language="text")
        st.download_button(
            label="TXT 다운로드",
            data=st.session_state.report_text.encode("utf-8"),
            file_name="interview_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

else:
    st.warning("자기소개서를 입력한 뒤 '질문 생성/갱신 (STEP 4)'을 눌러 질문을 생성하세요.")
