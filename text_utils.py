# text_utils.py
# 텍스트 처리 유틸리티 함수들

import re
import hashlib
from typing import List, Tuple

from config import RISK_TRIGGERS


# ----------------------------
# Core helpers (deterministic)
# ----------------------------

def stable_int_hash(text: str) -> int:
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return int(h[:16], 16)


def normalize_ws(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s).strip()


def split_sentences(text: str) -> List[str]:
    t = normalize_ws(text.replace("\r\n", "\n").replace("\r", "\n"))
    parts = re.split(r"(?<=[\.\?\!。！？])\s+|\n+", t)
    sents = [normalize_ws(p) for p in parts if normalize_ws(p)]
    if len(sents) <= 1 and len(t) > 260:
        chunk = []
        buf = ""
        for ch in t:
            buf += ch
            if len(buf) >= 140:
                chunk.append(normalize_ws(buf))
                buf = ""
        if normalize_ws(buf):
            chunk.append(normalize_ws(buf))
        sents = chunk if chunk else sents
    return sents


def split_essay_items(essay: str) -> List[Tuple[str, str]]:
    t = essay.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not t:
        return []
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    if len(lines) < 2:
        return [("자기소개서", t)]

    prompt_idxs = []
    for i, line in enumerate(lines):
        if re.match(
            r"^(Q\s*\d+[\.\)]|문항\s*\d+[\.\)]|\d+[\.\)]|지원동기|성장과정|입사\s*후\s*포부|강점|약점|경험|역량)\b",
            line,
            flags=re.IGNORECASE,
        ):
            prompt_idxs.append(i)

    if not prompt_idxs:
        if len(lines[0]) <= 40 and len(lines) >= 3:
            return [(lines[0], "\n".join(lines[1:]))]
        return [("자기소개서", t)]

    items: List[Tuple[str, str]] = []
    prompt_idxs.append(len(lines))
    for a, b in zip(prompt_idxs[:-1], prompt_idxs[1:]):
        prompt = lines[a]
        body = "\n".join(lines[a + 1: b]).strip()
        if body:
            items.append((prompt, body))

    return items if items else [("자기소개서", t)]


def extract_evidence_sentences(essay: str, max_sents: int = 12) -> List[str]:
    sents = split_sentences(essay)
    if not sents:
        return []

    def score(sent: str) -> int:
        sc = 0
        if re.search(r"\d", sent):
            sc += 2
        if re.search(r"(성과|개선|해결|달성|증가|감소|수상|리드|주도|기여|협업|고객|안전|서비스|불만|민원|클레임|CS|매출|효율|품질)", sent):
            sc += 2
        if 40 <= len(sent) <= 180:
            sc += 1
        return sc

    ranked = sorted(sents, key=lambda s: (score(s), len(s)), reverse=True)
    out, seen = [], set()
    for s in ranked:
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= max_sents:
            break
    return out


# ----------------------------
# 핵심 키워드(=면접 공격 포인트) 추출 (Korean-only)
# ----------------------------

def extract_risk_keywords_kor(essay: str, top_k: int = 14) -> List[str]:
    t = normalize_ws(essay)
    if not t:
        return []

    sents = split_sentences(t)
    picks: List[str] = []

    for s in sents:
        ss = normalize_ws(s)
        if not ss:
            continue

        for trig in RISK_TRIGGERS:
            if trig in ss:
                pos = ss.find(trig)
                start = max(0, pos - 12)
                end = min(len(ss), pos + len(trig) + 18)
                frag = normalize_ws(ss[start:end])
                if frag and frag not in picks:
                    picks.append(frag)

        if re.search(r"(되었|되었습|되었고|하게 되었|진행했|수행했|처리했|대응했|관리했)", ss):
            frag = ss[:45] + ("..." if len(ss) > 45 else "")
            if frag and frag not in picks:
                picks.append(frag)

        if re.search(r"(기여했|도움이 되었|노력했|원활|개선했|향상시켰)", ss) and not re.search(r"\d", ss):
            frag = ss[:45] + ("..." if len(ss) > 45 else "")
            if frag and frag not in picks:
                picks.append(frag)

    cleaned = []
    seen = set()
    for p in picks:
        pp = normalize_ws(p)
        if not pp or pp in seen:
            continue
        seen.add(pp)
        if len(pp) > 60:
            pp = pp[:57] + "..."
        cleaned.append(pp)
        if len(cleaned) >= top_k:
            break
    return cleaned


# ----------------------------
# 텍스트 포맷팅/정리 함수
# ----------------------------

def fmt_anchor_text(a: str) -> str:
    if not a:
        return ""
    return a if len(a) <= 180 else (a[:177] + "...")


def _strip_ellipsis_tokens(s: str) -> str:
    if not s:
        return ""
    t = normalize_ws(s)
    t = t.replace("…", "")
    t = t.replace("...", "")
    t = normalize_ws(t)
    return t


def _trim_no_ellipsis(s: str, max_len: int) -> str:
    """
    문자열을 max_len 이하로 자르되, 단어 경계를 존중.
    - 한국어에서 단어가 중간에 잘리지 않도록 공백 기준으로 자름
    """
    t = _strip_ellipsis_tokens(normalize_ws(s))
    if not t:
        return ""
    if len(t) <= max_len:
        return t

    # max_len까지 자른 후
    truncated = t[:max_len]

    # 자른 지점이 단어 중간인지 확인
    if len(t) > max_len and t[max_len] not in " .,, ":
        # 마지막 공백 위치 찾기 (단어 경계)
        last_space = truncated.rfind(" ")
        if last_space > max_len * 0.4:  # 최소 40%는 유지
            truncated = truncated[:last_space]

    return truncated.strip().rstrip(",.")


def _sanity_kor_endings(s: str) -> str:
    """
    어휘/어미 안정성: '입니다다', '했다다' 등 중복 어미 제거 (경량)
    """
    t = _strip_ellipsis_tokens(normalize_ws(s))
    if not t:
        return ""
    fixes = [
        ("입니다다", "입니다"),
        ("합니다다", "합니다"),
        ("했습니다다", "했습니다"),
        ("하였다다", "하였다"),
        ("했다다", "했다"),
        ("됩니다다", "됩니다"),
        ("됐습니다다", "됐습니다"),
        ("이에요요", "이에요"),
        ("예요요", "예요"),
        ("요요", "요"),
    ]
    for a, b in fixes:
        t = t.replace(a, b)
    t = normalize_ws(t)
    return t


def _has_final_consonant_kor_char(ch: str) -> bool:
    if not ch:
        return False
    code = ord(ch)
    if 0xAC00 <= code <= 0xD7A3:
        jong = (code - 0xAC00) % 28
        return jong != 0
    return False


def _choose_particle_kor(word: str, pair: Tuple[str, str]) -> str:
    """
    pair: (받침 있음, 받침 없음) e.g. ("은","는"), ("이","가")
    """
    w = normalize_ws(word)
    if not w:
        return pair[1]
    last = w[-1]
    return pair[0] if _has_final_consonant_kor_char(last) else pair[1]


def _auto_fix_particles_kor(text: str) -> str:
    """
    매우 경량 조사 보정:
    - 'X은는', 'X는은' -> 'X은/는'
    - 'X이가', 'X가이' -> 'X이/가'
    의미 재작성 없이 조사 중복/오류만 정리.
    """
    t = normalize_ws(text)
    if not t:
        return ""

    # 중복 조사 제거 (단순)
    t = t.replace("은 는", "은 ").replace("는 은", "는 ")
    t = t.replace("이 가", "이 ").replace("가 이", "가 ")

    # 붙어있는 중복 케이스
    def repl_eunne(m):
        ch = m.group(1)
        return ch + _choose_particle_kor(ch, ("은", "는"))

    def repl_iga(m):
        ch = m.group(1)
        return ch + _choose_particle_kor(ch, ("이", "가"))

    t = re.sub(r"([가-힣])은는", repl_eunne, t)
    t = re.sub(r"([가-힣])는은", repl_eunne, t)
    t = re.sub(r"([가-힣])이가", repl_iga, t)
    t = re.sub(r"([가-힣])가이", repl_iga, t)

    # 띄어쓰기 케이스(매우 제한적으로)
    t = re.sub(r"([가-힣])\s*(은)\s*(는)", lambda m: m.group(1) + _choose_particle_kor(m.group(1), ("은", "는")), t)
    t = re.sub(r"([가-힣])\s*(이)\s*(가)", lambda m: m.group(1) + _choose_particle_kor(m.group(1), ("이", "가")), t)

    # 잘린 항공사 이름 복원 (예: 어로케이 → 에어로케이)
    truncated_airline_fixes = [
        ("어로케이", "에어로케이"),
        ("어프레미아", "에어프레미아"),
        ("스타항공", "이스타항공"),
        ("시아나항공", "아시아나항공"),
        ("웨이항공", "티웨이항공"),
        ("주항공", "제주항공"),
    ]
    for truncated, full in truncated_airline_fixes:
        if truncated in t and full not in t:
            t = t.replace(truncated, full)

    return normalize_ws(t)


def _fix_particles_after_format(text: str) -> str:
    """
    템플릿 format 후 조사(을/를, 이/가, 은/는, 과/와) 보정.

    한글 마지막 글자의 받침 유무에 따라 올바른 조사를 선택:
    - 받침 있음: 을, 이, 은, 과
    - 받침 없음: 를, 가, 는, 와

    예시:
    - "채워주기을 하면서" → "채워주기를 하면서" (기: 받침 없음)
    - "도전을 하면서" → "도전을 하면서" (전: 받침 있음, 정상)
    """
    t = normalize_ws(text)
    if not t:
        return ""

    # 항공사 이름 (조사 보정에서 제외 - 이름 자체가 조사로 끝나는 경우 보호)
    airline_names = [
        "에어로케이", "에어프레미아", "이스타항공", "아시아나항공",
        "티웨이항공", "제주항공", "대한항공", "진에어", "에어부산", "에어서울"
    ]

    def is_airline_name(word: str, particle: str) -> bool:
        """단어+조사가 항공사 이름의 일부인지 확인"""
        full_word = word + particle
        for airline in airline_names:
            if full_word == airline or airline.startswith(full_word):
                return True
        return False

    # 을/를 보정: "한글을" 패턴에서 한글의 받침 확인
    def fix_eul_reul(m):
        word = m.group(1)  # 앞 단어 (한글 1~10자)
        particle = m.group(2)  # 을 또는 를
        suffix = m.group(3)  # 뒤따르는 문자 (공백, 조사 등)

        if not word:
            return m.group(0)

        last_char = word[-1]
        correct_particle = _choose_particle_kor(last_char, ("을", "를"))
        return word + correct_particle + suffix

    # 이/가 보정
    def fix_i_ga(m):
        word = m.group(1)
        particle = m.group(2)
        suffix = m.group(3)

        if not word:
            return m.group(0)

        last_char = word[-1]
        correct_particle = _choose_particle_kor(last_char, ("이", "가"))
        return word + correct_particle + suffix

    # 은/는 보정
    def fix_eun_neun(m):
        word = m.group(1)
        particle = m.group(2)
        suffix = m.group(3)

        if not word:
            return m.group(0)

        # 항공사 이름이면 원본 유지
        if is_airline_name(word, particle):
            return m.group(0)

        last_char = word[-1]
        correct_particle = _choose_particle_kor(last_char, ("은", "는"))
        return word + correct_particle + suffix

    # 과/와 보정
    def fix_gwa_wa(m):
        word = m.group(1)
        particle = m.group(2)
        suffix = m.group(3)

        if not word:
            return m.group(0)

        last_char = word[-1]
        correct_particle = _choose_particle_kor(last_char, ("과", "와"))
        return word + correct_particle + suffix

    # 패턴: 한글 단어 + 조사 + (공백 또는 다른 문자)
    # 을/를: "단어을 " 또는 "단어를 "
    t = re.sub(r"([가-힣]{1,15})(을|를)(\s|$|[,\.!?])", fix_eul_reul, t)

    # 이/가: "단어이 " 또는 "단어가 "
    # 주의: "누군가", "누구가", "언젠가" 등 "가"가 조사가 아닌 단어는 제외
    def fix_i_ga_safe(m):
        word = m.group(1)
        particle = m.group(2)
        suffix = m.group(3)

        # 항공사 이름이면 조사 보정하지 않음 (원본 유지)
        if is_airline_name(word, particle):
            return m.group(0)

        # "가"가 조사가 아닌 단어들 (변경하지 않음)
        exception_endings = ["누군", "누구", "언젠", "어딘", "무언", "뭔", "웬"]
        for exc in exception_endings:
            if word.endswith(exc):
                return m.group(0)  # 원본 그대로 반환

        if not word:
            return m.group(0)

        last_char = word[-1]
        correct_particle = _choose_particle_kor(last_char, ("이", "가"))
        return word + correct_particle + suffix

    t = re.sub(r"([가-힣]{1,15})(이|가)(\s|$|[,\.!?])", fix_i_ga_safe, t)

    # 은/는: "단어은 " 또는 "단어는 "
    t = re.sub(r"([가-힣]{1,15})(은|는)(\s|$|[,\.!?])", fix_eun_neun, t)

    # 과/와: "단어과 " 또는 "단어와 "
    t = re.sub(r"([가-힣]{1,15})(과|와)(\s|$|[,\.!?])", fix_gwa_wa, t)

    # 따옴표 뒤 조사 보정: "단어'가 " → "단어'이 " (커뮤니케이션'가 → 커뮤니케이션'이)
    def fix_quote_particle(m):
        word = m.group(1)
        quote = m.group(2)
        particle = m.group(3)
        suffix = m.group(4)

        if not word:
            return m.group(0)

        last_char = word[-1]
        if particle in ("이", "가"):
            correct_particle = _choose_particle_kor(last_char, ("이", "가"))
        elif particle in ("은", "는"):
            correct_particle = _choose_particle_kor(last_char, ("은", "는"))
        elif particle in ("을", "를"):
            correct_particle = _choose_particle_kor(last_char, ("을", "를"))
        elif particle in ("과", "와"):
            correct_particle = _choose_particle_kor(last_char, ("과", "와"))
        else:
            correct_particle = particle
        return word + quote + correct_particle + suffix

    # 따옴표 + 조사 패턴
    t = re.sub(r"([가-힣]{1,15})(['\"])([이가은는을를과와])(\s|$|[,\.!?])", fix_quote_particle, t)

    # 문법 오류 수정: 관형형 어미 "~은" → "~는" (동사의 경우)
    # "있은" → "있는", "없은" → "없는"
    t = t.replace("있은 ", "있는 ").replace("없은 ", "없는 ")
    t = t.replace("있은.", "있는.").replace("없은.", "없는.")
    t = t.replace("있은,", "있는,").replace("없은,", "없는,")
    t = re.sub(r"있은([가-힣])", r"있는\1", t)
    t = re.sub(r"없은([가-힣])", r"없는\1", t)

    # 동사 관형형 "~은" → "~는" 추가 수정
    verb_fixes = [
        ("짓은", "짓는"),  # 미소 짓은 → 미소 짓는
        ("웃은", "웃는"),  # 웃은 얼굴 → 웃는 얼굴
        ("갖은", "갖는"),  # 갖은 → 갖는
        ("받은", "받는"),  # (주의: 과거형도 있으므로 문맥에 따라)
    ]
    for wrong, correct in verb_fixes:
        # "~은 얼굴", "~은 모습" 등 현재 진행형 맥락에서만 수정
        t = re.sub(rf"{wrong}(\s*(?:얼굴|모습|표정|자세|태도|마음))", rf"{correct}\1", t)

    # 가정법 표현 개선: "이었다면" → "이라면" (더 자연스러운 표현)
    t = t.replace("이었다면", "이라면")
    t = t.replace("였다면 ", "라면 ")
    t = t.replace("이었더라면", "이라면")

    # 잘린 항공사 이름 복원 (예: 어로케이 → 에어로케이)
    truncated_airline_fixes = [
        ("어로케이", "에어로케이"),
        ("어프레미아", "에어프레미아"),
        ("스타항공", "이스타항공"),
        ("시아나항공", "아시아나항공"),
        ("웨이항공", "티웨이항공"),
        ("주항공", "제주항공"),
    ]
    for truncated, full in truncated_airline_fixes:
        # 잘린 형태가 있으면 전체 형태로 복원
        if truncated in t and full not in t:
            t = t.replace(truncated, full)

    return normalize_ws(t)


def interviewer_filter(question: str) -> str:
    q = normalize_ws(question)
    q = _strip_ellipsis_tokens(q)
    q = _sanity_kor_endings(q)
    q = _auto_fix_particles_kor(q)
    return q


def _sanitize_question_strict(q: str) -> str:
    """질문 정리 - 최소한의 정리만 수행 (문법 변형 금지)"""
    t = normalize_ws(q)
    if not t:
        return ""
    # 지시어만 제거 (문법 변형 없음)
    t = t.replace("그런 ", "").replace("이런 ", "").replace("해당 ", "").replace("위의 ", "")
    t = normalize_ws(t)
    return t


def _dedup_keep_order(xs: List[str]) -> List[str]:
    out = []
    seen = set()
    for x in xs or []:
        xx = normalize_ws(x or "")
        if not xx:
            continue
        if xx in seen:
            continue
        seen.add(xx)
        out.append(xx)
    return out


def build_basis_text(summary: str, intent: str) -> str:
    s = _strip_ellipsis_tokens(normalize_ws(summary))
    i = _strip_ellipsis_tokens(normalize_ws(intent))
    s = _sanity_kor_endings(s)
    i = _sanity_kor_endings(i)
    s = _auto_fix_particles_kor(s)
    i = _auto_fix_particles_kor(i)
    return f"요약: {s}\n의도: {i}"
