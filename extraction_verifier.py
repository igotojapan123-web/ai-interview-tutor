# extraction_verifier.py
# 방안 1+2: Two-Stage Extraction + Original Text Verification
# LLM 추출 결과를 원문과 대조하여 검증/교정

import re
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher

from text_utils import normalize_ws, split_sentences


# =========================
# 0. 문장 완전성 검증 (불완전한 조각 필터링)
# =========================

# 완전한 문장의 끝 패턴 (습니다, 입니다, 했다, 있다, 등)
COMPLETE_SENTENCE_ENDINGS = re.compile(
    r'(습니다|입니다|했다|였다|있다|없다|됩니다|합니다|됐다|한다|된다|'
    r'하다|이다|었다|았다|겠다|ㅂ니다|해요|에요|어요|네요|군요|죠|요)\.?$'
)

# 불완전한 조각 패턴 (이런 것으로 끝나면 불완전)
INCOMPLETE_PATTERNS = re.compile(
    r'(을 향한|를 향한|을 위한|를 위한|을 통한|를 통한|'
    r'에 대한|와 함께|과 함께|을 위해|를 위해|에서의|로서의|'
    r'하는|되는|있는|없는|했던|된|한|의)$'
)

# 명사로 끝나는 불완전 조각 (서술어 없이 명사로만 끝나는 경우)
# 예: "다큐멘터리같은 제 삶은 한 장면" - 장면으로 끝남, 서술어 없음
NOUN_ENDING_FRAGMENTS = re.compile(
    r'.{5,}(같은|라는|라고|라며|에서|에게|으로|처럼|보다|만큼|까지|부터|'
    r'장면|모습|사람|마음|생각|자세|태도|모습|순간|경험|능력|역량|가치|'
    r'이유|계기|동기|목표|꿈|비전|열정|노력|성장|변화|도전|시작점|기점|출발점)$'
)

# 제목 형태 패턴 (괄호, 콜론 등으로 감싸진 형태)
TITLE_PATTERNS = re.compile(
    r'^[\s]*[《「\[【『].*[》」\]】』][\s]*$|'  # 괄호로 감싸진 제목
    r'^[\s]*[가-힣]+\s*[:：]\s*[가-힣]+[\s]*$|'  # 한글:한글 형태의 제목
    r'^[\s]*[\(（].+[\)）][\s]*$'  # 소괄호로 감싸진 제목
)


def is_complete_sentence(text: str) -> bool:
    """
    문장이 완전한지 확인
    - 완전한 문장: ~습니다, ~입니다, ~했다 등으로 끝남
    - 불완전한 조각: ~을 향한, ~를 위해, 명사로만 끝나는 경우
    - 25자 미만은 반드시 완전한 문장 끝이 있어야 함
    """
    if not text or len(text.strip()) < 10:
        return False

    text = text.strip()

    # 따옴표 제거 후 체크
    text_clean = text.strip("'\"''""")

    # 0. 제목 형태 패턴 체크 (무조건 실패)
    #    예: 《첫 비행: 꿈의 시작점》, (한글: 부제목)
    if TITLE_PATTERNS.search(text_clean):
        return False

    # 1. 불완전한 조각 패턴 체크 (무조건 실패)
    if INCOMPLETE_PATTERNS.search(text_clean):
        return False

    # 2. 명사로 끝나는 불완전 조각 체크 (무조건 실패)
    #    예: "다큐멘터리같은 제 삶은 한 장면" - 서술어 없음
    if NOUN_ENDING_FRAGMENTS.search(text_clean):
        return False

    # 3. 완전한 문장 끝 패턴 체크 → 통과
    if COMPLETE_SENTENCE_ENDINGS.search(text_clean):
        return True

    # 4. 마침표로 끝나는 경우 → 통과
    if text_clean.endswith('.'):
        return True

    # 5. 25자 미만인데 완전한 끝이 없음 → 실패
    if len(text_clean) < 25:
        return False

    # 6. 25자 이상이면 통과 (긴 문장은 LLM 추출 신뢰)
    return True


def filter_complete_sentences(sentences: List[str]) -> List[str]:
    """
    완전한 문장만 필터링하여 반환
    """
    return [s for s in sentences if is_complete_sentence(s)]


# =========================
# 1. 문장 유사도 계산
# =========================

def _calculate_similarity(text1: str, text2: str) -> float:
    """
    두 문자열의 유사도 계산 (0.0 ~ 1.0)
    SequenceMatcher 기반 + 한국어 키워드 보너스
    """
    t1 = normalize_ws(text1 or "")
    t2 = normalize_ws(text2 or "")

    if not t1 or not t2:
        return 0.0

    # 기본 유사도
    base_ratio = SequenceMatcher(None, t1, t2).ratio()

    # 키워드 중복 보너스
    words1 = set(re.findall(r'[가-힣]{2,}', t1))
    words2 = set(re.findall(r'[가-힣]{2,}', t2))

    if words1 and words2:
        common = words1 & words2
        keyword_ratio = len(common) / max(len(words1), len(words2))
        # 가중 평균: 기본 유사도 70% + 키워드 유사도 30%
        return base_ratio * 0.7 + keyword_ratio * 0.3

    return base_ratio


def _find_best_matching_sentence(
    extracted: str,
    original_sentences: List[str],
    min_similarity: float = 0.4
) -> Tuple[Optional[str], float]:
    """
    추출된 문장과 가장 유사한 원문 문장 찾기

    Returns:
        (최적 매칭 문장, 유사도) 또는 (None, 0.0)
    """
    if not extracted or not original_sentences:
        return None, 0.0

    extracted_norm = normalize_ws(extracted)
    best_match = None
    best_score = 0.0

    for sent in original_sentences:
        sent_norm = normalize_ws(sent)
        if not sent_norm:
            continue

        # 완전 일치 체크
        if extracted_norm in sent_norm or sent_norm in extracted_norm:
            return sent, 1.0

        # 유사도 계산
        score = _calculate_similarity(extracted_norm, sent_norm)
        if score > best_score:
            best_score = score
            best_match = sent

    if best_score >= min_similarity:
        return best_match, best_score

    return None, best_score


def _find_containing_sentence(
    fragment: str,
    original_sentences: List[str]
) -> Optional[str]:
    """
    주어진 단편이 포함된 원문 문장 찾기
    """
    if not fragment:
        return None

    frag_norm = normalize_ws(fragment)
    if len(frag_norm) < 5:  # 너무 짧은 단편은 스킵
        return None

    for sent in original_sentences:
        sent_norm = normalize_ws(sent)
        if frag_norm in sent_norm:
            return sent

    return None


# =========================
# 2. 원문에서 문장 추출
# =========================

def _extract_all_sentences_from_essays(qa_sets: List[Dict[str, str]]) -> List[str]:
    """
    모든 자소서 문항에서 문장 추출
    """
    all_sentences = []
    seen = set()

    for qa in (qa_sets or []):
        answer = qa.get("answer", "") or ""
        sents = split_sentences(answer)

        for sent in sents:
            sent_norm = normalize_ws(sent)
            if sent_norm and sent_norm not in seen and len(sent_norm) >= 10:
                seen.add(sent_norm)
                all_sentences.append(sent_norm)

    return all_sentences


def _extract_sentences_from_single_answer(answer: str) -> List[str]:
    """
    단일 답변에서 문장 추출
    """
    if not answer:
        return []

    sents = split_sentences(answer)
    result = []
    seen = set()

    for sent in sents:
        sent_norm = normalize_ws(sent)
        if sent_norm and sent_norm not in seen and len(sent_norm) >= 8:
            seen.add(sent_norm)
            result.append(sent_norm)

    return result


# =========================
# 3. Stage 2: 검증 및 교정
# =========================

def _verify_single_point(
    point: str,
    original_sentences: List[str],
    min_similarity: float = 0.4
) -> Dict[str, Any]:
    """
    단일 공격 포인트 검증

    Returns:
        {
            "original": 원본 추출 텍스트,
            "verified": 검증된 텍스트 (원문에서 찾은 것),
            "confidence": 신뢰도 (0.0 ~ 1.0),
            "match_type": "exact" | "similar" | "fragment" | "unverified"
        }
    """
    point_norm = normalize_ws(point or "")
    if not point_norm:
        return {
            "original": point,
            "verified": point,
            "confidence": 0.0,
            "match_type": "unverified"
        }

    # 1. 완전 일치 체크
    for sent in original_sentences:
        sent_norm = normalize_ws(sent)
        if point_norm == sent_norm:
            return {
                "original": point,
                "verified": sent,
                "confidence": 1.0,
                "match_type": "exact"
            }

    # 2. 포함 관계 체크 (추출된 것이 원문의 일부인 경우)
    containing = _find_containing_sentence(point_norm, original_sentences)
    if containing:
        return {
            "original": point,
            "verified": containing,
            "confidence": 0.95,
            "match_type": "exact"
        }

    # 3. 유사도 기반 매칭
    best_match, best_score = _find_best_matching_sentence(
        point_norm, original_sentences, min_similarity
    )

    if best_match and best_score >= 0.7:
        return {
            "original": point,
            "verified": best_match,
            "confidence": best_score,
            "match_type": "similar"
        }

    if best_match and best_score >= min_similarity:
        return {
            "original": point,
            "verified": best_match,
            "confidence": best_score,
            "match_type": "fragment"
        }

    # 4. 매칭 실패 - 원본 유지하되 낮은 신뢰도
    return {
        "original": point,
        "verified": point,
        "confidence": 0.2,
        "match_type": "unverified"
    }


def _verify_list_points(
    points: List[str],
    original_sentences: List[str],
    min_similarity: float = 0.4,
    max_verified: int = 10
) -> List[Dict[str, Any]]:
    """
    공격 포인트 리스트 검증
    신뢰도가 높은 순으로 정렬하여 반환
    """
    if not points:
        return []

    verified_list = []

    for point in points:
        result = _verify_single_point(point, original_sentences, min_similarity)
        verified_list.append(result)

    # 신뢰도순 정렬 (높은 것 우선)
    verified_list.sort(key=lambda x: -x["confidence"])

    return verified_list[:max_verified]


# =========================
# 4. 전체 LLM 결과 검증
# =========================

def verify_llm_extraction(
    llm_data: Dict[str, Any],
    qa_sets: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    LLM 추출 결과 전체 검증 (Stage 2)

    - over_idealized_points: 원문 검증 필수 (가장 중요)
    - risk_points: LLM 생성이므로 검증 불필요
    - repeatability_questions: 질문이므로 검증 불필요
    - claim: 원문 검증 시도

    Returns:
        검증된 LLM 데이터 (동일 구조, verified 필드 추가)
    """
    if not llm_data or not isinstance(llm_data, dict):
        return llm_data

    items = llm_data.get("items", [])
    if not items:
        return llm_data

    # 전체 원문 문장 추출
    all_sentences = _extract_all_sentences_from_essays(qa_sets)

    verified_items = []
    total_verified_count = 0
    high_confidence_count = 0

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            verified_items.append(item)
            continue

        # 해당 문항의 답변 문장
        item_sentences = all_sentences
        if idx < len(qa_sets):
            answer = qa_sets[idx].get("answer", "")
            item_sentences = _extract_sentences_from_single_answer(answer)
            if not item_sentences:
                item_sentences = all_sentences

        verified_item = dict(item)  # 복사

        # over_idealized_points 검증 (가장 중요!)
        over_idealized = item.get("over_idealized_points", [])
        if over_idealized:
            # 1단계: 불완전한 문장 조각 필터링 (핵심!)
            # '~를 향한', '~를 위해' 같은 조각은 완전히 제거
            complete_points = [
                p for p in over_idealized
                if isinstance(p, str) and is_complete_sentence(p)
            ]

            # 불완전한 조각은 절대 사용 안 함 (빈 리스트 허용)

            # 2단계: 원문 검증
            verified_points = _verify_list_points(
                complete_points,
                item_sentences,
                min_similarity=0.35,
                max_verified=6
            )

            # 검증된 결과로 교체
            verified_item["over_idealized_points"] = [
                vp["verified"] for vp in verified_points
            ]
            verified_item["over_idealized_verification"] = verified_points

            # 통계
            for vp in verified_points:
                total_verified_count += 1
                if vp["confidence"] >= 0.7:
                    high_confidence_count += 1

        # claim 검증 (불완전한 조각이면 스킵)
        claim = item.get("claim", "")
        claim_result = None
        if claim:
            # 불완전한 조각인지 체크
            if not is_complete_sentence(claim):
                # 불완전한 조각이면 빈 문자열로 설정 (절대 사용 안 함)
                verified_item["claim"] = ""
                verified_item["claim_verification"] = {
                    "original": claim,
                    "verified": "",
                    "confidence": 0.0,
                    "reason": "불완전한 문장 조각"
                }
            else:
                claim_result = _verify_single_point(claim, item_sentences, min_similarity=0.3)
                verified_item["claim"] = claim_result["verified"]
                verified_item["claim_verification"] = claim_result

                if claim_result["confidence"] >= 0.7:
                    high_confidence_count += 1
                total_verified_count += 1

        # decision_criteria 검증 (선택적)
        decision_criteria = item.get("decision_criteria", [])
        if decision_criteria:
            verified_criteria = _verify_list_points(
                decision_criteria,
                item_sentences,
                min_similarity=0.3,
                max_verified=4
            )
            verified_item["decision_criteria"] = [
                vc["verified"] for vc in verified_criteria
            ]

        # risk_points, repeatability_questions는 LLM 생성이므로 그대로 유지

        # ========================================
        # 방안 1+2 추가: action_sentences, result_sentences 자동 추출
        # LLM이 추출하지 않는 필드를 extraction_verifier에서 채움
        # ========================================
        if idx < len(qa_sets):
            answer = qa_sets[idx].get("answer", "")
            if answer:
                key_sents = extract_key_sentences_verified(answer, max_sentences=8)

                action_sents = []
                result_sents = []

                for sent_info in key_sents:
                    sent_text = sent_info.get("text", "")
                    types = sent_info.get("types", [])

                    if "action" in types:
                        action_sents.append(sent_text)
                    if "result" in types:
                        result_sents.append(sent_text)
                    if "decision" in types:
                        # decision도 action에 포함 (판단/선택 행위)
                        if sent_text not in action_sents:
                            action_sents.append(sent_text)

                # 기존 값이 없으면 추가
                if not verified_item.get("action_sentences"):
                    verified_item["action_sentences"] = action_sents[:4]
                if not verified_item.get("result_sentences"):
                    verified_item["result_sentences"] = result_sents[:4]

        verified_items.append(verified_item)

    # 결과 조합
    result = dict(llm_data)
    result["items"] = verified_items
    result["verification_stats"] = {
        "total_verified": total_verified_count,
        "high_confidence": high_confidence_count,
        "confidence_ratio": high_confidence_count / max(total_verified_count, 1)
    }

    return result


# =========================
# 5. 핵심 문장 추출 개선
# =========================

def extract_key_sentences_verified(
    answer: str,
    max_sentences: int = 5
) -> List[Dict[str, Any]]:
    """
    답변에서 핵심 문장 추출 (검증 포함)

    핵심 문장 기준:
    1. 행동이 드러나는 문장 (했다, 처리했다 등)
    2. 수치/결과가 있는 문장
    3. 선택/판단이 드러나는 문장
    4. 이상적/추상적 표현 (공격 포인트)
    """
    if not answer:
        return []

    sentences = _extract_sentences_from_single_answer(answer)
    if not sentences:
        return []

    scored_sentences = []

    # 행동 패턴 (더 광범위하게)
    action_pattern = re.compile(
        r'(했습니다|하였습니다|했고|했다|처리했|대응했|해결했|조정했|'
        r'조치했|확인했|안내했|설득했|제안했|주도했|리드했|'
        r'진행했|실행했|수행했|완료했|마쳤|끝냈|시작했|'
        r'만들었|구축했|개선했|변경했|수정했|적용했|'
        r'도왔|지원했|참여했|기여했|담당했|맡았|'
        r'전달했|공유했|보고했|발표했|제출했)'
    )

    # 결과/수치 패턴 (더 광범위하게)
    result_pattern = re.compile(
        r'(\d+|%|개선|해결|달성|증가|감소|성과|결과|덕분에|이후|'
        r'성공|완성|완료|마무리|끝|극복|수상|선정|합격|'
        r'만족|호평|칭찬|인정|긍정적)'
    )

    # 선택/판단 패턴 (더 광범위하게)
    decision_pattern = re.compile(
        r'(선택|결정|판단|우선|우선순위|기준|근거|택했|정했|하기로|'
        r'결심|다짐|생각했|고민했|고려했|검토했)'
    )

    # 이상적 표현 패턴 (공격 포인트) - 더 세밀하게
    idealized_pattern = re.compile(
        r'(노력|최선|함께|소통|협력|배려|성장|배웠|느꼈|깨달|중요하다고|'
        r'열정|책임감|도전|극복|포기하지|끝까지|항상|언제나|'
        r'진심|마음을 담|미소|따뜻|배움|경험을 통해|'
        r'어떤 상황|어려움 속|힘들었지만|그럼에도|불구하고)'
    )

    for sent in sentences:
        score = 0
        types = []

        if action_pattern.search(sent):
            score += 30
            types.append("action")

        if result_pattern.search(sent):
            score += 25
            types.append("result")

        if decision_pattern.search(sent):
            score += 35
            types.append("decision")

        if idealized_pattern.search(sent):
            score += 20
            types.append("idealized")

        # 길이 보너스 (너무 짧거나 긴 것 페널티)
        length = len(sent)
        if 30 <= length <= 120:
            score += 10
        elif length < 20 or length > 200:
            score -= 10

        if score > 0:
            scored_sentences.append({
                "text": sent,
                "score": score,
                "types": types,
                "length": length
            })

    # 점수순 정렬
    scored_sentences.sort(key=lambda x: -x["score"])

    # 타입 다양성 확보 (같은 타입만 선택되지 않도록)
    selected = []
    type_counts = {"action": 0, "result": 0, "decision": 0, "idealized": 0}

    for sent in scored_sentences:
        if len(selected) >= max_sentences:
            break

        # 타입 다양성 체크
        main_type = sent["types"][0] if sent["types"] else "other"
        if main_type in type_counts and type_counts[main_type] >= 2:
            continue  # 같은 타입 2개 초과 방지

        selected.append(sent)
        for t in sent["types"]:
            if t in type_counts:
                type_counts[t] += 1

    return selected


# =========================
# 6. 통합 추출 함수
# =========================

def two_stage_extraction(
    qa_sets: List[Dict[str, str]],
    llm_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    방안 1+2 통합: Two-Stage Extraction + Verification

    Stage 1: LLM 추출 (외부에서 수행)
    Stage 2: 원문 검증 (이 함수에서 수행)

    Returns:
        {
            "verified_data": 검증된 LLM 데이터,
            "key_sentences": 문항별 핵심 문장 리스트,
            "stats": 검증 통계
        }
    """
    result = {
        "verified_data": None,
        "key_sentences": [],
        "stats": {
            "total_items": len(qa_sets) if qa_sets else 0,
            "llm_available": llm_data is not None,
            "verification_done": False
        }
    }

    # Stage 2-A: LLM 데이터 검증
    if llm_data:
        verified = verify_llm_extraction(llm_data, qa_sets)
        result["verified_data"] = verified
        result["stats"]["verification_done"] = True

        if "verification_stats" in verified:
            result["stats"]["llm_confidence"] = verified["verification_stats"]["confidence_ratio"]

    # Stage 2-B: 각 문항별 핵심 문장 추출
    for qa in (qa_sets or []):
        answer = qa.get("answer", "") or ""
        prompt = qa.get("prompt", "") or ""

        key_sents = extract_key_sentences_verified(answer, max_sentences=5)
        result["key_sentences"].append({
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "sentences": key_sents
        })

    return result
