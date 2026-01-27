# analysis.py
# 자소서 분석, 키워드 추출, 앵커 선택, SRCAI 함수들

import re
from logging_config import get_logger
from typing import List, Dict, Tuple, Any, Optional

from text_utils import (
    normalize_ws, split_sentences, stable_int_hash,
    _strip_ellipsis_tokens, _trim_no_ellipsis, _sanity_kor_endings,
    _auto_fix_particles_kor, _dedup_keep_order
)
from config import STOPWORDS_KOR, OTHER_CHOICE_CANDIDATES

logger = get_logger(__name__)


# ----------------------------
# 포인트 풀(pool) 구축 (결정론)
# ----------------------------

def _find_item_no_for_sentence(items: List[Tuple[str, str]], sent: str) -> int:
    s = normalize_ws(sent)
    if not s:
        return 0
    for idx, (_, body) in enumerate(items, start=1):
        b = body.replace("\n", " ")
        if s in b:
            return idx
    return 0


def build_point_pool(items: List[Tuple[str, str]], evidence: List[str], risk_keywords: List[str]) -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []
    all_sents: List[str] = []

    for _, body in items:
        all_sents.extend(split_sentences(body))
    for s in evidence:
        if s not in all_sents:
            all_sents.append(s)

    patt_amb = re.compile(r"(노력|최선|원활|기여|해결|개선|향상|만족|긍정|열심|성실)")
    patt_owner = re.compile(r"(팀|함께|저희|우리|전반|지원|도움|협업|소통|커뮤니케이션|진행|수행|처리|대응|관리|조치|확인|하게 되었|되었)")
    patt_num = re.compile(r"(\d+|%|퍼센트|기간|개월|주|일|시간|분|명|건|만원|원|매출|성과|달성|증가|감소)")
    patt_conf = re.compile(r"(갈등|불만|민원|클레임|CS|사고|안전|위험|규정|컴플라이언스|컴플|위반|긴급|지연)")
    patt_dec = re.compile(r"(판단|결정|선택|기준|근거|우선|우선순위|전략|방향|트레이드오프|리스크)")

    def add_point(cat: str, sent: str, source: str):
        ss = normalize_ws(sent)
        if not ss:
            return
        item_no = _find_item_no_for_sentence(items, ss)
        pool.append({
            "category": cat,
            "text": ss,
            "item_no": item_no,
            "source": source,
        })

    for rk in risk_keywords:
        add_point("모호 표현", rk, "risk_keyword")

    for s in all_sents:
        ss = normalize_ws(s)
        if not ss:
            continue
        if patt_amb.search(ss):
            add_point("모호 표현", ss, "sentence_scan")
        if patt_owner.search(ss):
            add_point("책임 주체", ss, "sentence_scan")
        if patt_num.search(ss):
            add_point("수치/기간/결과", ss, "sentence_scan")
        if patt_conf.search(ss):
            add_point("갈등/민원/안전", ss, "sentence_scan")
        if patt_dec.search(ss):
            add_point("선택/판단/기준", ss, "sentence_scan")

    uniq = []
    seen = set()
    for p in pool:
        key = (p["category"], p["text"])
        if key in seen:
            continue
        seen.add(key)
        if len(p["text"]) > 180:
            p["text"] = p["text"][:177] + "..."
        uniq.append(p)

    return uniq


def pick_unique(pool: List[Any], start_idx: int, used_idx: set, step: int = 1) -> int:
    if not pool:
        return -1
    n = len(pool)
    idx = start_idx % n
    for _ in range(n):
        if idx not in used_idx:
            used_idx.add(idx)
            return idx
        idx = (idx + step) % n
    return start_idx % n


# =========================
# STEP 4 — Anchor(근거) 선택 규칙 보완
# =========================

# "수식/비유/서사/감정/다짐/가치 선언" 차단은 SRCAI NONQ 패턴 + 추가 차단(보수적)으로 강제
_ANCHOR_HARD_BLOCK_PATTERNS = [
    re.compile(r"(영화|드라마|소설|비유|마치|처럼|같이|은유|상징)"),
    re.compile(r"(중요하다고\s*생각|깨달|느꼈|배웠|알게\s*되었|다짐|하겠습니다|하고\s*싶습니다|노력하겠습니다|최선을\s*다하겠습니다)"),
    re.compile(r"(가치관|신념|철학|태도|마인드|마음가짐)"),
    re.compile(r"(전반적으로|항상|누구나|모두가|말하자면|라고\s*할\s*수)"),
]

# "선택이 있었던 행동", "역할 조정/대응/판단" 우선 (행동문장 점수)
_ANCHOR_ACTION_PRIORITY_PATTERNS = [
    re.compile(r"(판단|결정|선택|우선|우선순위|기준|근거|전략|방향|트레이드오프|리스크)"),
    re.compile(r"(조정|재조정|분담|역할|배정|나누|정렬|정리|조율|협의|공유|보고|설득)"),
    re.compile(r"(대응|처리|조치|확인|안내|관리|해결|개선|수정|운영|수행)"),
]

# 결과문장 점수(수치/성과/변화 등)
_ANCHOR_RESULT_PRIORITY_PATTERNS = [
    re.compile(r"(\d+|%|퍼센트|개월|주|일|시간|분|명|건|만원|원)"),
    re.compile(r"(성과|개선|해결|달성|증가|감소|재발\s*방지|만족|불만\s*해소|오류\s*감소|효율)"),
    re.compile(r"(그\s*결과|결과적으로|덕분에|이후|변화|전후|비교)"),
]


def _anchor_is_hard_blocked(sent: str) -> bool:
    s = normalize_ws(sent or "")
    if not s:
        return True
    for p in _ANCHOR_HARD_BLOCK_PATTERNS:
        if p.search(s):
            return True
    # 기존 SRCAI NONQUESTIONABLE도 차단
    try:
        if _srcai_is_nonquestionable(s):
            return True
    except Exception as e:
            logger.debug("_srcai_is_nonquestionable check failed: %s", e)
    return False


def _anchor_is_action_like(sent: str) -> bool:
    s = normalize_ws(sent or "")
    if not s or _anchor_is_hard_blocked(s):
        return False
    # SRCAI action verb 포함 또는 "했다/수행/진행/대응/처리" 등 보수적 판정
    try:
        if _srcai_has_action_verb(s):
            return True
    except Exception as e:
            logger.debug("_srcai_has_action_verb check failed: %s", e)
    if re.search(r"(했|하였다|했습니다|진행|수행|처리|대응|조치|확인|안내|관리|개선|조정|정리|공유|보고|설득)", s):
        return True
    return False


def _anchor_is_result_like(sent: str) -> bool:
    s = normalize_ws(sent or "")
    if not s or _anchor_is_hard_blocked(s):
        return False
    # SRCAI result change 포함(가장 강한 신호) 또는 결과 연결어/성과/수치 기반
    try:
        if _srcai_has_result_change(s):
            return True
    except Exception as e:
            logger.debug("_srcai_has_result_change check failed: %s", e)
    if any(tok in s for tok in _SRCAI_RESULT_CONNECTORS):
        return True
    if re.search(r"(성과|개선|해결|달성|증가|감소|만족|효율|재발\s*방지|오류\s*감소|불만\s*해소)", s) and (re.search(r"\d", s) or re.search(r"(되었|됐다|되었습|되었고|되었으며|되었다)", s)):
        return True
    if re.search(r"\d", s) and re.search(r"(증가|감소|개선|달성|해결|줄|늘|단축|향상)", s):
        return True
    return False


def _score_action_anchor(sent: str) -> int:
    s = normalize_ws(sent or "")
    if not s:
        return -999
    sc = 0
    # 선택/판단/역할조정/대응이 드러날수록 가산
    for p in _ANCHOR_ACTION_PRIORITY_PATTERNS:
        if p.search(s):
            sc += 3
    if re.search(r"\d", s):
        sc += 1
    # 너무 짧으면 감점
    if len(s) < 12:
        sc -= 2
    if 40 <= len(s) <= 160:
        sc += 1
    return sc


def _score_result_anchor(sent: str) -> int:
    s = normalize_ws(sent or "")
    if not s:
        return -999
    sc = 0
    for p in _ANCHOR_RESULT_PRIORITY_PATTERNS:
        if p.search(s):
            sc += 3
    if len(s) < 12:
        sc -= 2
    if 30 <= len(s) <= 180:
        sc += 1
    return sc


def _pick_anchor_by_rule(qtype_internal: str, action_sents: List[str], result_sents: List[str]) -> str:
    """
    [최종 확정 규칙 반영]
    - anchor는 Action/Result 문장만 허용.
    - 유형별 우선순위: Action 1순위, Result 2순위 (경험/가치/동기 전부 동일 우선순위 유지)
    - 선택/판단/역할조정/대응이 드러나는 Action 우선(점수 기반).
    - Action/Result 0개면 anchor는 생성하지 않음("").
    """
    acts = _dedup_keep_order(action_sents)
    ress = _dedup_keep_order(result_sents)

    # Action 후보 필터
    act_cands = [s for s in acts if _anchor_is_action_like(s)]
    # Result 후보 필터
    res_cands = [s for s in ress if _anchor_is_result_like(s)]

    if act_cands:
        ranked = sorted(
            [(_score_action_anchor(s), stable_int_hash(s), s) for s in act_cands],
            key=lambda x: (-x[0], x[1])
        )
        return ranked[0][2]

    if res_cands:
        ranked = sorted(
            [(_score_result_anchor(s), stable_int_hash(s), s) for s in res_cands],
            key=lambda x: (-x[0], x[1])
        )
        return ranked[0][2]

    return ""


# ---- STEP 2 경험 추출/요약 로직 ----

_EVENT_BOUNDARY_RE = re.compile(
    r"(?:^|\s)(처음|당시|그때|이후|그러던 중|한편|또한|반면|그 다음|다음으로|결국|마지막으로|그러나|하지만|반대로|한번은|어느 날|어느날)"
)

_SITUATION_RE = re.compile(r"(당시|그때|이후|처음|중|상황|현장|매장|학교|동아리|프로젝트|행사|대회|수업|알바|근무|대기|탑승|예약|운영|팀|조|파트|담당|역할|혼자|처음\s*응대|최초\s*대응)")
_DECISION_RE = re.compile(r"(판단|결정|선택|우선|우선순위|기준|근거|전략|방향|하기로\s*했|정했|택했|결론|조치하기로|대응하기로|바꾸기로|중단|진행하기로|요청했|공유했|보고했|설득했|안내했|확인했|조정했|정리했)")
_OUTCOME_RE = re.compile(r"(결과|성과|달성|증가|감소|개선|변화|영향|해결|마무리|전후|비교|이후\s*달라|덕분에|그래서|결국|재발\s*방지|만족|불만\s*해소)")
_TRIGGER_RE = re.compile(r"(오류|지연|누락|착오|문제|갈등|충돌|항의|불만|민원|클레임|CS|사고|위험|규정\s*위반|혼선|긴급|돌발|변경|취소|과부하|오해)")


def _has_situation(text: str) -> bool:
    s = normalize_ws(text)
    return bool(_SITUATION_RE.search(s))


def _has_decision(text: str) -> bool:
    s = normalize_ws(text)
    return bool(_DECISION_RE.search(s))


def _has_outcome(text: str) -> bool:
    s = normalize_ws(text)
    return bool(_OUTCOME_RE.search(s) or re.search(r"\d", s))


def _experience_components_count(text: str) -> int:
    c = 0
    if _has_situation(text):
        c += 1
    if _has_decision(text):
        c += 1
    if _has_outcome(text):
        c += 1
    return c


def _is_valid_experience_block(text: str) -> bool:
    s = normalize_ws(text)
    if not s:
        return False
    comp = _experience_components_count(s)
    return comp >= 2


def _split_into_event_blocks(raw_text: str) -> List[str]:
    t = raw_text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not t:
        return []

    paras = [normalize_ws(p) for p in re.split(r"\n\s*\n+", t) if normalize_ws(p)]
    if len(paras) >= 2:
        return paras

    sents = split_sentences(t)
    if not sents:
        return [normalize_ws(t)] if normalize_ws(t) else []

    blocks: List[str] = []
    buf: List[str] = []
    for s in sents:
        ss = normalize_ws(s)
        if not ss:
            continue

        is_boundary = bool(_EVENT_BOUNDARY_RE.search(ss))
        if buf and is_boundary and len(" ".join(buf)) >= 120:
            blocks.append(normalize_ws(" ".join(buf)))
            buf = [ss]
        else:
            buf.append(ss)

        if len(" ".join(buf)) >= 420:
            blocks.append(normalize_ws(" ".join(buf)))
            buf = []

    if buf:
        blocks.append(normalize_ws(" ".join(buf)))

    uniq, seen = [], set()
    for b in blocks:
        bb = normalize_ws(b)
        if not bb or bb in seen:
            continue
        seen.add(bb)
        uniq.append(bb)
    return uniq


def _extract_trigger(text: str) -> str:
    s = _strip_ellipsis_tokens(normalize_ws(text))
    if not s:
        return ""
    sents = split_sentences(s)
    first = sents[0] if sents else s
    m = _TRIGGER_RE.search(first)
    if m:
        kw = m.group(1)
        pos = max(0, m.start() - 10)
        end = min(len(first), m.end() + 10)
        frag = normalize_ws(first[pos:end])
        frag = _strip_ellipsis_tokens(frag)
        if len(frag) > 30:
            frag = kw
        return frag
    if re.search(r"(요청|문의|상황|이슈)", first):
        return "요청이 발생한"
    return "예상치 못한 상황이 발생한"


def _event_score(text: str) -> int:
    s = normalize_ws(text)
    if not s:
        return 0

    comp = _experience_components_count(s)
    sc = comp * 10

    if _TRIGGER_RE.search(s):
        sc += 5
    if re.search(r"\d", s):
        sc += 3
    if _OUTCOME_RE.search(s):
        sc += 3
    if re.search(r"(대응|처리|해결|조치|안내|확인|관리|개선|수정|운영|수행|조정|정리|보고|리드|주도)", s):
        sc += 2
    if re.search(r"(고객|승객|민원|불만|클레임|CS|응대|서비스|안내)", s):
        sc += 2
    if re.search(r"(안전|규정|절차|위험|사고|긴급|위반)", s):
        sc += 2
    if re.search(r"(팀|함께|협업|소통|커뮤니케이션|조율|저희|우리)", s):
        sc += 1
    if 120 <= len(s) <= 520:
        sc += 1
    return sc


def _select_top_events(essay: str, max_events: int = 3) -> List[Dict[str, Any]]:
    blocks = _split_into_event_blocks(essay)
    if not blocks:
        return []

    candidates = []
    for b in blocks:
        bb = normalize_ws(b)
        if not bb:
            continue
        if not _is_valid_experience_block(bb):
            continue
        trig = _extract_trigger(bb)
        trig_key = stable_int_hash(trig or bb)
        sc = _event_score(bb)
        hid = stable_int_hash(bb)
        candidates.append((sc, trig_key, hid, bb, trig))

    if not candidates:
        return []

    candidates.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)

    chosen: List[Dict[str, Any]] = []
    seen_triggers = set()
    seen_blocks = set()

    for sc, trig_key, hid, bb, trig in candidates:
        if bb in seen_blocks:
            continue
        if trig_key in seen_triggers:
            continue
        seen_blocks.add(bb)
        seen_triggers.add(trig_key)
        chosen.append({"id": hid, "text": bb, "score": sc, "trigger": trig})
        if len(chosen) >= max_events:
            break

    return chosen


# ----------------------------
# 분해기(경량 전처리): 변수 품질 개선 전용
# ----------------------------

_OPINION_WORDS = ("생각", "느꼈", "중요하다고", "깨달", "배웠", "노력", "최선")
_SCENE_SCORE_PATTERNS = {
    "time": ("당시", "처음", "이후", "그때", "때", "시"),
    "place": ("기숙사", "현장", "동아리", "팀", "수업", "매장", "공항", "기내", "카운터", "대회", "행사", "프로젝트"),
    "role": ("주장", "담당", "책임", "응대", "정리", "조율", "안내", "확인", "리드", "주도", "지원", "보고"),
    "verb": ("했다", "했습니다", "하였다", "진행", "변경", "조정", "설명", "제안", "도움", "만들", "처리", "대응", "해결", "운영", "관리"),
    "result": ("그래서", "결과적으로", "이후", "변화", "개선", "해결", "증가", "감소", "달성", "전후"),
}


def _decomposer_split_candidates(text: str) -> List[str]:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"(?<=다)\.\s*", "다.\n", t)
    t = re.sub(r"(?<=요)\.\s*", "요.\n", t)
    t = re.sub(r"[\.\?\!]\s*", ".\n", t)
    parts = []
    for line in t.split("\n"):
        line = normalize_ws(line)
        if not line:
            continue
        for seg in re.split(r"\s*\.\s*", line):
            seg = normalize_ws(seg)
            if not seg:
                continue
            if len(seg) < 8:
                continue
            parts.append(_sanity_kor_endings(_strip_ellipsis_tokens(seg)))
    uniq, seen = [], set()
    for p in parts:
        pp = normalize_ws(p)
        if not pp or pp in seen:
            continue
        seen.add(pp)
        uniq.append(pp)
    return uniq


def _decomposer_scene_score(sent: str) -> int:
    s = normalize_ws(sent)
    if not s:
        return 0
    sc = 0
    for group in ("time", "place", "role", "verb", "result"):
        for tok in _SCENE_SCORE_PATTERNS[group]:
            if tok and tok in s:
                sc += 1
                break
    if re.search(r"\d", s):
        sc += 1
    if any(w in s for w in _OPINION_WORDS):
        sc -= 1
    return sc


def _decomposer_pick_top_scenes(
    primary_texts: List[str],
    fallback_text: str,
    top_k: int = 3
) -> List[str]:
    candidates: List[str] = []
    if primary_texts:
        for t in primary_texts:
            candidates.extend(_decomposer_split_candidates(t))
    if not candidates:
        candidates = _decomposer_split_candidates(fallback_text)

    if not candidates:
        return []

    scored = []
    for s in candidates:
        sc = _decomposer_scene_score(s)
        hid = stable_int_hash(s)
        scored.append((sc, hid, len(s), s))

    scored.sort(key=lambda x: (-x[0], x[1], -x[2]))

    top = []
    seen = set()
    for sc, hid, ln, s in scored:
        if s in seen:
            continue
        seen.add(s)
        top.append(s)
        if len(top) >= top_k:
            break
    return top


def _extract_action_phrase_light(scene_sent: str, fallback_text: str) -> str:
    t = _strip_ellipsis_tokens(normalize_ws(scene_sent)) or _strip_ellipsis_tokens(normalize_ws(fallback_text))
    if not t:
        return "우선순위를 정해 대응"

    verb_hits = [
        "대응", "처리", "해결", "조치", "안내", "확인", "관리", "개선", "수정", "운영", "수행",
        "조정", "정리", "보고", "설득", "제안", "설명", "리드", "주도", "응대"
    ]
    pos = -1
    for v in verb_hits:
        p = t.find(v)
        if p != -1:
            pos = p
            break

    if pos == -1:
        m = re.search(r"(했다|했습니다|하였다|했고|하며|해서)", t)
        if m:
            pos = max(0, m.start() - 10)

    if pos == -1:
        return "우선순위를 정해 대응"

    start = max(0, pos - 10)
    end = min(len(t), pos + 15)
    frag = normalize_ws(t[start:end])
    frag = _strip_ellipsis_tokens(frag)
    frag = re.sub(r"(팀워크|리더십|고객\s*응대|고객응대|서비스\s*경험|경험)\b", "", frag).strip()
    frag = normalize_ws(frag)

    if len(frag) < 6:
        frag = "우선순위를 정해 대응"
    if len(frag) > 25:
        frag = frag[:25].strip()
    return _sanity_kor_endings(frag)


def _extract_decision_phrase_light(scene_sent: str, fallback_text: str) -> str:
    t = _strip_ellipsis_tokens(normalize_ws(scene_sent)) or _strip_ellipsis_tokens(normalize_ws(fallback_text))
    if not t:
        return "우선순위를 정해 대응하기로 한 선택"

    keys = ["우선순위", "우선", "기준", "근거", "전략", "방향", "결정", "선택", "판단"]
    pos = -1
    hit = ""
    for k in keys:
        p = t.find(k)
        if p != -1:
            pos = p
            hit = k
            break

    if pos == -1:
        act = _extract_action_phrase_light(scene_sent, fallback_text)
        return _sanity_kor_endings(normalize_ws(f"{act}하기로 한 선택"))

    start = max(0, pos - 10)
    end = min(len(t), pos + 20)
    frag = normalize_ws(t[start:end])
    frag = _strip_ellipsis_tokens(frag)
    frag = re.sub(r"(팀워크|리더십|고객\s*응대|고객응대|서비스\s*경험|경험)\b", "", frag).strip()
    frag = normalize_ws(frag)
    if len(frag) < 8:
        frag = normalize_ws(f"{hit}을 중심으로 한 선택")
    if len(frag) > 35:
        frag = frag[:35].strip()
    return _sanity_kor_endings(frag)


def _pick_other_choice(base: int, version: int, q_index: int) -> str:
    idx = (base + version * 9 + q_index * 3) % len(OTHER_CHOICE_CANDIDATES)
    return OTHER_CHOICE_CANDIDATES[idx]


# ----------------------------
# STEP 2 – SRCAI (문장 역할 분류 AI)
# ----------------------------

# B) 역할 태깅: 정확히 이 5개만
_SRCAI_ROLE_SITUATION = "SITUATION"
_SRCAI_ROLE_TASK = "TASK"
_SRCAI_ROLE_ACTION = "ACTION"
_SRCAI_ROLE_RESULT = "RESULT"
_SRCAI_ROLE_NONQ = "NONQUESTIONABLE"

# C) NONQUESTIONABLE 강제 차단
_SRCAI_NONQ_PATTERNS = [
    re.compile(r"(느꼈|깨달았|배웠|알게\s*되었|생각이\s*들)"),
    re.compile(r"(중요하다고\s*생각|지키겠습니다|하겠습니다|하고\s*싶습니다)"),
    re.compile(r"(전반적으로|항상|누구나|모두가|말하자면|라고\s*할\s*수)"),
    re.compile(r"(노력했|하려고\s*했|최선을\s*다했|힘썼)"),
]

# D) SITUATION 판별 패턴(상황)
_SRCAI_SITUATION_PATTERNS = [
    re.compile(r"(때|당시|에서|동안)"),
    re.compile(r"(였다|상황이었다|상태였다)"),
]

# E) TASK 판별 패턴(과제/문제)
_SRCAI_TASK_PATTERNS = [
    re.compile(r"(문제가\s*발생|갈등|어려움|부담|필요했다|요구되었다)"),
    re.compile(r"(을\s*맡|책임|역할|해야\s*했다)"),
]

# F) ACTION 판별 패턴(행동) - 구체 동사(어간/변형 포함 보수적 포함 매칭)
_SRCAI_ACTION_VERBS = [
    "조정", "대응", "정리", "설계", "실행", "개선", "해결",
    "소통", "공유", "협업", "분담", "설득", "지원",
]
_SRCAI_ACTION_METHOD_BONUS = [
    "을 통해", "를 통해", "을 사용", "를 사용", "으로", "방식으로",
]

# G) RESULT 판별 패턴(결과)
_SRCAI_RESULT_CONNECTORS = [
    "그 결과", "결과적으로", "덕분에",
]
_SRCAI_RESULT_CHANGE_VERBS = [
    "개선되", "감소", "증가", "해결되", "변화",
]
_SRCAI_RESULT_NOUNS = [
    "성과", "효율", "만족", "문제", "오류", "불만",
]

_SRCAI_WEAK_RESULT_FORMS = [
    re.compile(r"(좋아졌|나아졌)\b"),
]


def _srcai_preprocess_for_split(text: str) -> str:
    # 분리용 사본에서만 처리(원문 보존)
    t = (text or "")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("\n", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _srcai_merge_short_sentences(sents: List[str], min_len: int = 6) -> List[str]:
    if not sents:
        return []
    out: List[str] = []
    i = 0
    while i < len(sents):
        cur = sents[i]
        if len(cur) < min_len:
            if i + 1 < len(sents):
                merged = normalize_ws(cur + " " + sents[i + 1])
                out.append(merged)
                i += 2
                continue
            elif out:
                out[-1] = normalize_ws(out[-1] + " " + cur)
                i += 1
                continue
        out.append(cur)
        i += 1
    # 2차 패스: 여전히 너무 짧은 문장이 생기면 뒤/앞 병합(결정론)
    final: List[str] = []
    for s in out:
        if final and len(s) < min_len:
            final[-1] = normalize_ws(final[-1] + " " + s)
        else:
            final.append(s)
    return final


def _srcai_safe_sentence_split(text: str) -> List[str]:
    """
    A) 문장 분해 (결정론)
    - 종결부호 기준: . ! ? …
    - 한국어 종결 어미 패턴 기준: "다." "요." "니다." "습니다." 등 (보수적)
    - 괄호/따옴표 내부는 우선순위 낮춤(가능하면 보수적으로) -> 괄호/따옴표 안의 종결부호에서는 분리하지 않음
    - 6자 미만 단독 문장은 인접 문장과 병합
    """
    src = _srcai_preprocess_for_split(text)
    if not src:
        return []

    sents: List[str] = []
    buf: List[str] = []
    depth_paren = 0
    in_quote = False

    def flush():
        seg = normalize_ws("".join(buf))
        if seg:
            sents.append(seg)
        buf.clear()

    i = 0
    while i < len(src):
        ch = src[i]
        buf.append(ch)

        if ch in "([{":
            depth_paren += 1
        elif ch in ")]}" and depth_paren > 0:
            depth_paren -= 1
        elif ch in "\"'""''":
            in_quote = not in_quote

        is_terminal = ch in [".", "!", "?", "…"]
        if is_terminal and depth_paren == 0 and not in_quote:
            j = i + 1
            if j >= len(src) or src[j].isspace():
                flush()
        i += 1

    if buf:
        flush()

    if len(sents) <= 1:
        parts = re.split(r"(?:(?<=니다)|(?<=습니다)|(?<=요)|(?<=다))\s+", src)
        sents = [normalize_ws(p) for p in parts if normalize_ws(p)]

    sents = _srcai_merge_short_sentences(sents, min_len=6)
    return sents


def _srcai_is_nonquestionable(sent: str) -> bool:
    s = normalize_ws(sent)
    if not s:
        return True
    for patt in _SRCAI_NONQ_PATTERNS:
        if patt.search(s):
            return True
    return False


def _srcai_has_action_verb(sent: str) -> bool:
    s = normalize_ws(sent)
    if not s:
        return False
    for v in _SRCAI_ACTION_VERBS:
        if v in s:
            return True
    return False


def _srcai_has_result_change(sent: str) -> bool:
    s = normalize_ws(sent)
    if not s:
        return False
    for v in _SRCAI_RESULT_CHANGE_VERBS:
        if v in s:
            return True
    return False


def _srcai_is_weak_result(sent: str) -> bool:
    s = normalize_ws(sent)
    if not s:
        return False
    for patt in _SRCAI_WEAK_RESULT_FORMS:
        if patt.search(s):
            return True
    return False


def _srcai_tag_role(sent: str) -> str:
    """
    B) 우선순위: RESULT > ACTION > TASK > SITUATION > NONQUESTIONABLE
    C) NONQUESTIONABLE 강제 차단은 최우선
    """
    s = normalize_ws(sent)
    if not s:
        return _SRCAI_ROLE_NONQ

    if _srcai_is_nonquestionable(s):
        return _SRCAI_ROLE_NONQ

    if any(tok in s for tok in _SRCAI_RESULT_CONNECTORS):
        return _SRCAI_ROLE_RESULT
    if _srcai_has_result_change(s):
        return _SRCAI_ROLE_RESULT
    if any(tok in s for tok in _SRCAI_RESULT_NOUNS) and (re.search(r"\d", s) or _srcai_has_result_change(s)):
        return _SRCAI_ROLE_RESULT

    if _srcai_has_action_verb(s):
        return _SRCAI_ROLE_ACTION
    if any(tok in s for tok in _SRCAI_ACTION_METHOD_BONUS) and re.search(r"(했|하였다|했습니다|진행|수행|처리|대응|조치|확인)", s):
        return _SRCAI_ROLE_ACTION

    for patt in _SRCAI_TASK_PATTERNS:
        if patt.search(s):
            return _SRCAI_ROLE_TASK

    for patt in _SRCAI_SITUATION_PATTERNS:
        if patt.search(s):
            return _SRCAI_ROLE_SITUATION

    return _SRCAI_ROLE_NONQ


def _srcai_select_questionables(sentences: List[str], roles: List[str], max_pick: int = 12) -> Tuple[List[str], List[str], List[str]]:
    """
    H) 질문 가능한 문장 선별
    - ACTION 통과: 역할 ACTION + NONQUESTIONABLE 금지 + 구체 동사 1개 이상 포함
    - RESULT 통과: 역할 RESULT + 변화/성과 동사 포함
      - "좋아졌다/나아졌다" 단독형은 결과 후보로는 남기되 우선순위 낮춤(컷에서 뒤로)
    - selected_questionable_sentences: action+result 원문 순서 결합, 최대 12개(초과 시 RESULT/ACTION 우선순위 유지 가능)
    """
    actions: List[Tuple[int, str]] = []
    results: List[Tuple[int, str, bool]] = []  # (idx, sent, weak)
    for idx, (s, r) in enumerate(zip(sentences, roles)):
        ss = s  # 원문 그대로 저장
        if r == _SRCAI_ROLE_ACTION:
            if (not _srcai_is_nonquestionable(ss)) and _srcai_has_action_verb(ss):
                actions.append((idx, ss))
        elif r == _SRCAI_ROLE_RESULT:
            if _srcai_has_result_change(ss):
                results.append((idx, ss, _srcai_is_weak_result(ss)))

    selected_actions = [s for _, s in actions]
    selected_results = [s for _, s, _w in results]

    combined: List[Tuple[int, str, int, bool]] = []
    for idx, s, weak in results:
        combined.append((idx, s, 0, weak))
    for idx, s in actions:
        combined.append((idx, s, 1, False))

    combined.sort(key=lambda x: x[0])
    if len(combined) <= max_pick:
        combined_sents = [s for _i, s, _rp, _wk in combined]
        return selected_actions, selected_results, combined_sents

    ranked = sorted(combined, key=lambda x: (x[2], 1 if x[3] else 0, x[0]))
    picked = ranked[:max_pick]
    picked.sort(key=lambda x: x[0])
    combined_sents = [s for _i, s, _rp, _wk in picked]
    return selected_actions, selected_results, combined_sents


def _srcai_analyze_text(text: str) -> Dict[str, Any]:
    sentences = _srcai_safe_sentence_split(text or "")
    roles = [_srcai_tag_role(s) for s in sentences]
    selected_actions, selected_results, selected_questionables = _srcai_select_questionables(sentences, roles, max_pick=12)
    return {
        "sentences": sentences,
        "roles": roles,
        "selected_action_sentences": selected_actions,
        "selected_result_sentences": selected_results,
        "selected_questionable_sentences": selected_questionables,
    }


# ----------------------------
# 문항 유형 분류
# ----------------------------

def _classify_prompt_type_kor(prompt: str) -> str:
    """
    문항 질문을 3가지 유형으로 분류:
    - 경험 요구형
    - 가치·태도 정합성형
    - 동기·정체성형
    분류 기준은 '평가자가 무엇을 근거로 평가하는 문항인가'에만 기반.
    """
    p = normalize_ws(prompt or "")
    if not p:
        return "경험 요구형"

    if re.search(r"(지원\s*동기|왜\s*지원|왜\s*승무원|승무원\s*지원|직무\s*이해|입사\s*후\s*포부|장기|지속|커리어|꿈|목표|정체성|가치관|나를\s*설명|어떤\s*사람|어떤\s*지원자)", p):
        return "동기·정체성형"

    if re.search(r"(가치|태도|고객|서비스|안전|규정|원칙|윤리|책임감|협업|소통|팀워크|배려|정직|성실|리더십|갈등|민원|클레임|CS|불만|우선순위|트레이드오프)", p):
        return "가치·태도 정합성형"

    if re.search(r"(경험|사례|에피소드|프로젝트|활동|대회|알바|근무|수업|동아리|문제\s*해결|성과|개선|갈등\s*해결|위기\s*대응|실패|성공)", p):
        return "경험 요구형"

    if re.search(r"(설명|말해|작성|서술|구체|상세)", p):
        return "경험 요구형"

    return "경험 요구형"


def _extract_topic_keywords_short(answer: str, top_k: int = 10) -> List[str]:
    t = normalize_ws(answer or "")
    if not t:
        return []
    raw = re.findall(r"[가-힣0-9]{2,10}", t)
    freq: Dict[str, int] = {}
    for w in raw:
        ww = w.strip()
        if not ww:
            continue
        if ww in STOPWORDS_KOR:
            continue
        if re.fullmatch(r"\d{2,}", ww):
            continue
        freq[ww] = freq.get(ww, 0) + 1

    scored = []
    for w, c in freq.items():
        sc = c * 10
        if re.search(r"\d", w):
            sc += 2
        if len(w) >= 4:
            sc += 1
        scored.append((sc, stable_int_hash(w), w))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out = []
    for _, _, w in scored:
        if w not in out:
            out.append(w)
        if len(out) >= top_k:
            break
    return out


def _extract_repeated_themes(answer: str, top_k: int = 6) -> List[str]:
    t = normalize_ws(answer or "")
    if not t:
        return []
    toks = [w for w in re.findall(r"[가-힣]{2,8}", t) if w not in STOPWORDS_KOR]
    freq: Dict[str, int] = {}
    for w in toks:
        freq[w] = freq.get(w, 0) + 1
    cand = [(c, stable_int_hash(w), w) for w, c in freq.items() if c >= 3]
    cand.sort(key=lambda x: (-x[0], x[1]))
    out = []
    for _, _, w in cand:
        out.append(w)
        if len(out) >= top_k:
            break
    return out


def _remove_self_references(text: str) -> str:
    """자기 지칭어(저는, 저의, 제가 등)를 제거하고 문장을 정리"""
    t = text
    # 문장 시작의 자기 지칭어 제거
    t = re.sub(r"^(저는|제가|저의|저도|저만|저를|저에게|제|본인은|본인이)\s*", "", t)
    # 문장 중간의 자기 지칭어도 정리 (필요시)
    t = re.sub(r"\s+(저는|제가)\s+", " ", t)
    return normalize_ws(t)


def _pick_situation_snippet(answer: str, qtype: str) -> str:
    """
    질문 문장에 '상황'을 명시하기 위한 짧은 상황 구문 생성(지칭어 금지 준수).
    - 과거형 서술문(~이었습니다, ~했습니다, ~겪었습니다 등)은 제외
    - 자기 지칭어(저는, 제가 등)로 시작하는 문장은 제외
    - 면접 질문에 적합한 가정/현재 상황만 선택
    """
    t = normalize_ws(answer or "")
    sents = split_sentences(t) if t else []

    # 상황 키워드 (질문에 적합한 것만)
    patt_situation = re.compile(r"(상황|현장|고객|승객|팀|동료|규정|절차|민원|불만|클레임|CS|갈등|충돌|지연|누락|오류|긴급|안전|변경|취소)")

    # 과거 서술/역사적 설명 패턴 (제외 대상)
    patt_past_narrative = re.compile(r"(이었습니다|였습니다|겪었습니다|있었습니다|왔습니다|했습니다|되었습니다|무너질|쌓아|아픔|위기는|역사|과거|발전을|위상을|사태는|이름은|기업으로서|것입니다|될 것입니다|하겠습니다|드리겠습니다|약속드|할 것입니다)")

    # 자기 지칭 시작 패턴 (제외 대상)
    patt_self_start = re.compile(r"^(저는|제가|저의|본인은|본인이)")

    # 1차: 과거 서술이 아니고, 자기 지칭으로 시작하지 않는 상황 문장 찾기
    for s in sents[:18]:
        ss0 = normalize_ws(s)
        ss = _trim_no_ellipsis(_strip_ellipsis_tokens(ss0), 90)
        if not ss:
            continue
        # 과거 서술/역사적 문장 제외
        if patt_past_narrative.search(ss):
            continue
        # 자기 지칭으로 시작하는 문장 제외
        if patt_self_start.match(ss):
            continue
        if patt_situation.search(ss):
            if "상황" not in ss and not re.search(r"(때|중)", ss):
                ss = normalize_ws(ss + " 상황")
            return _auto_fix_particles_kor(_sanity_kor_endings(ss))

    # 2차: 자기 지칭을 제거한 후 상황 추출 시도
    for s in sents[:18]:
        ss0 = normalize_ws(s)
        if patt_past_narrative.search(ss0):
            continue
        # 자기 지칭 제거 후 재검사
        ss_cleaned = _remove_self_references(ss0)
        ss = _trim_no_ellipsis(_strip_ellipsis_tokens(ss_cleaned), 90)
        if not ss or len(ss) < 10:  # 너무 짧으면 스킵
            continue
        if patt_situation.search(ss):
            if "상황" not in ss and not re.search(r"(때|중)", ss):
                ss = normalize_ws(ss + " 상황")
            return _auto_fix_particles_kor(_sanity_kor_endings(ss))

    # 3차: 기본 폴백
    if qtype == "경험 요구형":
        return "현장에서 변수가 발생한 상황"
    if qtype == "가치·태도 정합성형":
        return "고객 요구와 규정 준수가 동시에 걸린 상황"
    if qtype == "동기·정체성형":
        return "지원 동기와 현실 조건이 동시에 작동하는 상황"
    return "현장에서 예상치 못한 변수가 발생한 상황"


def _extract_action_candidates(answer: str, max_cands: int = 6) -> List[str]:
    t = normalize_ws(answer or "")
    if not t:
        return []
    sents = split_sentences(t)
    if not sents:
        return []
    patt = re.compile(r"(대응|처리|해결|조치|안내|확인|관리|개선|수정|운영|수행|조정|정리|보고|설득|제안|설명|리드|주도|응대|공유|협의|조율|요청)")
    cand = []
    seen = set()
    for s in sents[:26]:
        ss = _trim_no_ellipsis(_strip_ellipsis_tokens(normalize_ws(s)), 120)
        if not ss:
            continue
        if patt.search(ss) or re.search(r"(했다|했습니다|하였다|진행했|수행했|처리했|대응했|관리했|조치했|확인했)", ss):
            if ss in seen:
                continue
            seen.add(ss)
            cand.append(ss)
            if len(cand) >= max_cands:
                break
    return cand


def _extract_choice_candidates(answer: str, max_cands: int = 6) -> List[str]:
    t = normalize_ws(answer or "")
    if not t:
        return []
    sents = split_sentences(t)
    patt = re.compile(r"(우선순위|우선|선택|결정|판단|버리|포기|양보|집중|먼저|나중|충돌|갈등|트레이드오프|리스크)")
    cand = []
    seen = set()
    for s in sents[:26]:
        ss = _trim_no_ellipsis(_strip_ellipsis_tokens(normalize_ws(s)), 120)
        if not ss:
            continue
        if patt.search(ss):
            if ss in seen:
                continue
            seen.add(ss)
            cand.append(ss)
            if len(cand) >= max_cands:
                break
    return cand


def _extract_motivation_candidates(answer: str, max_cands: int = 6) -> List[str]:
    t = normalize_ws(answer or "")
    if not t:
        return []
    sents = split_sentences(t)
    patt = re.compile(r"(지원|동기|이유|목표|꿈|커리어|장기|지속|버티|현실|조건|압박|불확실|책임|역할|성장|학습)")
    cand = []
    seen = set()
    for s in sents[:26]:
        ss = _trim_no_ellipsis(_strip_ellipsis_tokens(normalize_ws(s)), 120)
        if not ss:
            continue
        if patt.search(ss):
            if ss in seen:
                continue
            seen.add(ss)
            cand.append(ss)
            if len(cand) >= max_cands:
                break
    return cand


def _clean_basis_text(text: str) -> str:
    """
    basis 텍스트를 질문에 적합한 핵심 구문으로 정리.
    - 선언형 어미(~것입니다, ~하겠습니다 등) 제거
    - 자기 지칭어 제거
    - 핵심 내용만 추출
    """
    t = normalize_ws(text or "")
    if not t:
        return ""

    # 자기 지칭어 제거
    t = re.sub(r"^(저는|제가|저의|본인은|본인이)\s*", "", t)
    t = re.sub(r"\s+(저는|제가)\s+", " ", t)

    # 선언형/미래형 어미 제거 (문장 끝)
    endings_to_remove = [
        r"할 것입니다\.?$",
        r"될 것입니다\.?$",
        r"것입니다\.?$",
        r"하겠습니다\.?$",
        r"드리겠습니다\.?$",
        r"있겠습니다\.?$",
        r"약속드립니다\.?$",
        r"임할 것입니다\.?$",
        r"맞이할 존재라는 자긍심으로 임할 것입니다\.?$",
    ]
    for pattern in endings_to_remove:
        t = re.sub(pattern, "", t)

    # 추가 정리: "~내용" 으로 끝나면 유지, 아니면 핵심구만
    t = normalize_ws(t)

    # 너무 길면 핵심 부분만 추출 (첫 번째 의미있는 구절)
    if len(t) > 60:
        # 주요 키워드 근처의 구문 추출
        key_patterns = [
            r"(고객[^,\.]*)",
            r"(서비스[^,\.]*)",
            r"(안전[^,\.]*)",
            r"(팀[^,\.]*협[^,\.]*)",
            r"(미소[^,\.]*)",
            r"(발전[^,\.]*)",
            r"(실수를 발판[^,\.]*)",
        ]
        for kp in key_patterns:
            match = re.search(kp, t)
            if match:
                extracted = match.group(1)
                if len(extracted) >= 8:
                    t = _trim_no_ellipsis(extracted, 60)
                    break

    return _trim_no_ellipsis(t, 80)


def _pick_two_basis_by_type(qtype: str, answer: str, version_seed: int) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    문항 유형별 허용 범위 안에서 근거 후보 A/B를 선택.
    """
    t = normalize_ws(answer or "")
    if not t:
        t = ""

    if qtype == "경험 요구형":
        acts = _extract_action_candidates(t, max_cands=8)
        A_raw = acts[0] if acts else "변수가 발생한 상황에서 해야 할 일을 정리하고 실행한 내용"
        B_raw = ""
        for s in acts[1:]:
            if re.search(r"(팀|동료|협업|소통|조율|보고|리드|주도|담당|책임)", s):
                B_raw = s
                break
        if not B_raw:
            B_raw = acts[1] if len(acts) > 1 else "팀과 역할을 나누어 실행한 내용"
        A = {"text": _clean_basis_text(A_raw), "kind": "action"}
        B = {"text": _clean_basis_text(B_raw), "kind": "role"}
        return A, B

    if qtype == "가치·태도 정합성형":
        choices = _extract_choice_candidates(t, max_cands=10)
        A_raw = ""
        for s in choices:
            if re.search(r"(충돌|갈등|동시에|우선순위|양보|포기|먼저|나중)", s):
                A_raw = s
                break
        if not A_raw:
            A_raw = choices[0] if choices else "고객 요구와 규정 준수가 동시에 걸린 상황에서 선택을 정리한 내용"
        B_raw = ""
        for s in choices:
            if re.search(r"(리스크|예외|문제|위험|부작용|재발|대안)", s):
                B_raw = s
                break
        if not B_raw:
            B_raw = choices[1] if len(choices) > 1 else "선택의 부작용을 고려해 보완한 내용"
        A = {"text": _clean_basis_text(A_raw), "kind": "priority"}
        B = {"text": _clean_basis_text(B_raw), "kind": "risk"}
        return A, B

    mots = _extract_motivation_candidates(t, max_cands=10)
    A_raw = ""
    for s in mots:
        if re.search(r"(지원|동기|이유|목표|꿈|직무|역할)", s):
            A_raw = s
            break
    if not A_raw:
        A_raw = mots[0] if mots else "직무 선택 이유와 목표를 설명한 내용"
    B_raw = ""
    for s in mots:
        if re.search(r"(장기|지속|버티|현실|조건|압박|불확실|유지)", s):
            B_raw = s
            break
    if not B_raw:
        B_raw = mots[1] if len(mots) > 1 else "현실 조건이 바뀌어도 지속할 수 있는 방식에 대한 내용"
    A = {"text": _clean_basis_text(A_raw), "kind": "reason"}
    B = {"text": _clean_basis_text(B_raw), "kind": "sustain"}
    return A, B


# ----------------------------
# LLM 없이 자소서에서 직접 경험/행동 추출 (폴백용)
# ----------------------------

# 경험 맥락 패턴 (어디서/언제/어떤 상황)
_EXPERIENCE_PATTERNS = [
    # 시간/시기 관련
    re.compile(r"([가-힣\s]{2,15}(?:시절|당시|때|중|동안))"),
    # 장소/활동 관련
    re.compile(r"([가-힣\s]{2,20}(?:에서|에서는))"),
    # 역할/활동 관련
    re.compile(r"([가-힣\s]{2,15}(?:으로|로)\s*(?:활동|근무|일)하면서)"),
    re.compile(r"([가-힣\s]{2,15}(?:아르바이트|알바|인턴|봉사|프로젝트|동아리|학교|대학|회사))"),
    # 경험 시작 표현
    re.compile(r"(처음\s*[가-힣]{2,10}(?:했을|했던|할)\s*때)"),
    re.compile(r"([가-힣]{2,8}(?:을|를)\s*(?:처음|시작)(?:했을|할)\s*때)"),
]

# 행동 패턴 (무엇을 했는지)
_ACTION_PATTERNS = [
    # 선택/결정 행동
    re.compile(r"([가-힣\s]{5,40}(?:을|를)\s*선택(?:했|하였|합니다))"),
    re.compile(r"([가-힣\s]{5,40}(?:하기로|하자고)\s*(?:했|결정|판단))"),
    # 구체적 행동
    re.compile(r"([가-힣\s]{5,50}(?:했습니다|하였습니다|했고|하였고))"),
    re.compile(r"((?:먼저|직접|스스로)\s*[가-힣\s]{3,30}(?:했|하였|드렸))"),
    # 주도/조율 행동
    re.compile(r"([가-힣\s]{3,30}(?:을|를)\s*(?:주도|조율|정리|설계|개선|해결)(?:했|하였))"),
    # 대응/처리 행동
    re.compile(r"([가-힣\s]{5,40}(?:에게|에)\s*[가-힣]{2,10}(?:했|드렸|하였))"),
]

# 제외할 패턴 (가치 선언, 추상적 표현)
_EXCLUDE_PATTERNS = [
    re.compile(r"(중요하다고\s*생각|깨달|느꼈|배웠|알게\s*되었)"),
    re.compile(r"(하겠습니다|할\s*것입니다|드리겠습니다|되겠습니다)"),
    re.compile(r"(노력|최선|열심|성실|원활|기여)"),
]


def _is_excluded_text(text: str) -> bool:
    """가치 선언/추상적 표현인지 확인"""
    s = normalize_ws(text or "")
    if not s:
        return True
    for p in _EXCLUDE_PATTERNS:
        if p.search(s):
            return True
    return False


def extract_specific_experiences(answer: str, max_count: int = 5) -> List[str]:
    """
    자소서 답변에서 구체적 경험 맥락 추출 (LLM 없이).
    예: "중국 유학 시절", "카페 아르바이트 중", "팀 프로젝트에서"
    """
    t = normalize_ws(answer or "")
    if not t:
        return []

    experiences = []
    seen = set()

    for pattern in _EXPERIENCE_PATTERNS:
        matches = pattern.findall(t)
        for match in matches:
            exp = normalize_ws(match)
            if not exp or len(exp) < 4 or len(exp) > 50:
                continue
            if exp in seen:
                continue
            if _is_excluded_text(exp):
                continue
            seen.add(exp)
            experiences.append(exp)
            if len(experiences) >= max_count:
                return experiences

    # 폴백: 문장에서 장소/상황 키워드 근처 추출
    if not experiences:
        sents = split_sentences(t)
        location_keywords = ["에서", "시절", "때", "중", "동안", "하면서", "으로서"]
        for sent in sents[:10]:
            for kw in location_keywords:
                if kw in sent:
                    # 키워드 앞 10~30자 추출
                    pos = sent.find(kw)
                    start = max(0, pos - 20)
                    end = pos + len(kw)
                    frag = normalize_ws(sent[start:end])
                    if frag and len(frag) >= 5 and frag not in seen:
                        if not _is_excluded_text(frag):
                            seen.add(frag)
                            experiences.append(frag)
                            if len(experiences) >= max_count:
                                return experiences

    return experiences


def extract_experience_actions(answer: str, max_count: int = 5) -> List[str]:
    """
    자소서 답변에서 구체적 행동 추출 (LLM 없이).
    예: "공동 학습을 주도했습니다", "고객에게 먼저 사과드린 후 대안을 제시"
    """
    t = normalize_ws(answer or "")
    if not t:
        return []

    actions = []
    seen = set()

    for pattern in _ACTION_PATTERNS:
        matches = pattern.findall(t)
        for match in matches:
            act = normalize_ws(match)
            if not act or len(act) < 8 or len(act) > 80:
                continue
            if act in seen:
                continue
            if _is_excluded_text(act):
                continue
            seen.add(act)
            actions.append(act)
            if len(actions) >= max_count:
                return actions

    # 폴백: 행동 동사가 있는 문장에서 추출
    if not actions:
        sents = split_sentences(t)
        action_verbs = ["했습니다", "하였습니다", "드렸습니다", "했고", "하였고", "선택했", "결정했", "주도했", "조율했"]
        for sent in sents[:15]:
            for verb in action_verbs:
                if verb in sent:
                    # 동사 앞 30~50자 추출
                    pos = sent.find(verb)
                    start = max(0, pos - 40)
                    end = pos + len(verb)
                    frag = normalize_ws(sent[start:end])
                    if frag and len(frag) >= 10 and frag not in seen:
                        if not _is_excluded_text(frag):
                            seen.add(frag)
                            actions.append(frag)
                            if len(actions) >= max_count:
                                return actions

    return actions


def _clean_experience_for_template(exp: str) -> str:
    """
    경험 텍스트를 템플릿에 맞게 정제 ('{experience}에서' 형식에 맞춤)

    목표: 짧은 명사구로 변환
    - O: "중국 유학", "축구 동아리 주장", "카페 아르바이트"
    - X: "다양한 문화와 언어를 경험" (동사형)
    - X: "중학생 때의 홀로 떠난 중국 유학 경험" (너무 김)
    """
    t = normalize_ws(exp or "")
    if not t:
        return ""

    # 1단계: 동사형 어미 제거 (가장 긴 것부터)
    verb_endings = [
        "을 경험했습니다", "를 경험했습니다", "을 경험", "를 경험",
        "을 했습니다", "를 했습니다", "을 하였습니다", "를 하였습니다",
        "했습니다", "하였습니다", "했던", "했고", "하며", "하면서",
        "되었습니다", "됐습니다", "이었습니다", "였습니다",
        "입니다", "습니다", "ㅂ니다",
    ]
    for end in verb_endings:
        if t.endswith(end):
            t = t[:-len(end)].strip()
            break

    # 2단계: 끝에 있는 조사/접미사 제거
    suffixes = [
        "경험에서", "경험에", "경험을", "경험이", "경험",
        "에서는", "에서", "에는", "에",
        "으로서", "으로", "로서", "로",
        "하면서", "할 때", "때", "시절", "당시",
        "을", "를", "이", "가", "의",
    ]
    for suf in suffixes:
        if t.endswith(suf) and len(t) > len(suf) + 2:
            t = t[:-len(suf)].strip()
            break

    # 3단계: 너무 긴 수식어 제거 (핵심 명사만 추출)
    # "중학생 때의 홀로 떠난 중국 유학" → "중국 유학"
    if len(t) > 15:
        # 장소/역할 패턴 찾기
        patterns = [
            r'(중국|일본|미국|호주|영국|독일|프랑스|베트남|태국)\s*(유학|생활|체류)',
            r'(대학|고등학교|중학교|학교)\s*(생활|시절)',
            r'(\w+)\s*(동아리|동호회|모임)\s*(주장|회장|부장|활동)?',
            r'(\w+)\s*(아르바이트|인턴|근무|실습)',
            r'(\w+)\s*(봉사|봉사활동)',
            r'(군대|군|병역)\s*(생활|복무)?',
        ]
        for pat in patterns:
            match = re.search(pat, t)
            if match:
                t = match.group(0).strip()
                break

        # 패턴 매칭 실패 시 마지막 핵심 단어들만 추출
        if len(t) > 15:
            words = t.split()
            if len(words) >= 2:
                # 마지막 2-3 단어만 사용
                t = " ".join(words[-2:]) if len(words[-2:][0]) > 1 else " ".join(words[-3:])

    # 4단계: 최종 정리
    t = t.strip()
    if not t or len(t) < 2:
        return ""

    return _trim_no_ellipsis(t, 20)


def _clean_action_for_template(act: str) -> str:
    """행동 텍스트를 템플릿에 맞게 정제 ('{action}을 하셨다고' 형식에 맞춤)"""
    t = normalize_ws(act or "")
    if not t:
        return ""

    # 끝에 있는 어미 제거 (긴 것부터 체크)
    endings = [
        "하였습니다", "했습니다", "드렸습니다", "됐습니다", "되었습니다",
        "하였고", "했고", "했다", "했어요", "했음",
        "합니다", "합니다", "합니다",
        "였습니다", "었습니다", "습니다",
    ]
    for end in endings:
        if t.endswith(end):
            t = t[:-len(end)].strip()
            break

    # "을/를/이/가" 제거 (템플릿에서 "을" 붙임)
    if t and t[-1] in "을를이가":
        t = t[:-1].strip()

    # 너무 길면 핵심만 추출 (마지막 동사구 중심)
    if len(t) > 40:
        # 마지막 부분만 사용
        parts = t.split()
        if len(parts) > 4:
            t = " ".join(parts[-4:])

    return _trim_no_ellipsis(t, 45)


def extract_experience_and_action_pair(answer: str) -> Tuple[str, str]:
    """
    자소서 답변에서 (경험 맥락, 행동) 쌍을 추출.
    면접 질문 생성용. 템플릿에 맞게 정제된 텍스트 반환.
    """
    experiences = extract_specific_experiences(answer, max_count=3)
    actions = extract_experience_actions(answer, max_count=3)

    experience = experiences[0] if experiences else ""
    action = actions[0] if actions else ""

    # 폴백
    if not experience:
        # 첫 문장에서 상황 추출 시도
        sents = split_sentences(answer)
        if sents:
            first = sents[0]
            if len(first) > 10:
                experience = first

    if not action:
        # 행동 동사가 있는 문장에서 추출
        sents = split_sentences(answer)
        for sent in sents[:10]:
            if re.search(r"(했습니다|하였습니다|했고|선택했|결정했|주도했)", sent):
                action = sent
                break

    # 템플릿에 맞게 정제
    experience = _clean_experience_for_template(experience)
    action = _clean_action_for_template(action)

    return experience, action
