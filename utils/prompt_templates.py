"""
FLYREADY 자소서 첨삭 시스템 v2.0
대한항공 2026 객실승무원 채용 특화
심리학 + 행동경제학 기반
"""

import re

# ═══════════════════════════════════════════
# 1. 실시간 체크 (LLM 불필요)
# ═══════════════════════════════════════════

COMMON_CHECKS = {
    # 기본 (20점)
    "char_count": {
        "name": "적정 분량",
        "weight": 10,
        "check": lambda text, limit: len(text.replace(" ", "").replace("\n", "")) >= limit * 0.85,
        "fail_msg": "글자수가 제한의 85% 미만입니다. 더 채워주세요.",
        "type": "warning"
    },
    "char_not_over": {
        "name": "글자수 초과",
        "weight": 5,
        "check": lambda text, limit: len(text.replace(" ", "").replace("\n", "")) <= limit,
        "fail_msg": "글자수를 초과했습니다!",
        "type": "critical"
    },
    "sentence_count": {
        "name": "충분한 문장",
        "weight": 5,
        "check": lambda text, limit: text.count('.') + text.count('!') + text.count('?') >= 4,
        "fail_msg": "문장이 너무 적습니다. 최소 4문장 이상 작성하세요.",
        "type": "warning"
    },

    # 구체성 (20점)
    "has_numbers": {
        "name": "구체적 숫자",
        "weight": 8,
        "check": lambda text, limit: len(re.findall(r'\d+', text)) >= 2,
        "fail_msg": "숫자가 2개 이상 필요합니다. (예: 기간, 인원, 성과 등)",
        "type": "warning"
    },
    "has_action_verbs": {
        "name": "행동 동사",
        "weight": 7,
        "check": lambda text, limit: any(w in text for w in [
            "제안", "설계", "도입", "개선", "분석", "기획", "주도",
            "실행", "달성", "구축", "운영", "조율", "해결", "발견",
            "진행", "완료", "성공", "이끌", "참여", "협력"
        ]),
        "fail_msg": "구체적 행동 동사가 없습니다. '제안했다', '도입했다' 등 사용하세요.",
        "type": "warning"
    },
    "no_abstract": {
        "name": "추상 표현 감지",
        "weight": 5,
        "check": lambda text, limit: not any(w in text for w in [
            "열심히", "최선을 다", "노력하겠", "항상 밝은",
            "밝고 활발", "성실하게", "꼭 이루고", "간절히"
        ]),
        "fail_msg": "'열심히', '최선을 다해' 등 추상 표현 발견. 구체적 행동으로 교체하세요.",
        "type": "critical"
    },

    # 구조 (15점)
    "strong_opening": {
        "name": "첫 문장 클리셰",
        "weight": 8,
        "check": lambda text, limit: not any(text.strip().startswith(w) for w in [
            "어릴 때", "어렸을 때", "저는", "제가", "항상",
            "대한항공은", "승무원은", "어린 시절", "저의"
        ]),
        "fail_msg": "첫 문장이 클리셰입니다. 구체적 장면/숫자로 시작하세요. (앵커링 효과)",
        "type": "critical"
    },
    "strong_ending": {
        "name": "마지막 문장",
        "weight": 7,
        "check": lambda text, limit: not text.strip().endswith(("되겠습니다.", "하겠습니다.", "싶습니다.")),
        "fail_msg": "마지막 문장이 평범합니다. 나만의 고유한 문장으로 마무리하세요. (피크엔드 법칙)",
        "type": "warning"
    },

    # 대한항공 연결 (15점)
    "korean_air_keyword": {
        "name": "대한항공 키워드",
        "weight": 8,
        "check": lambda text, limit: any(w in text for w in [
            "대한항공", "안전", "스카이팀", "통합", "아시아나",
            "메가 캐리어", "글로벌", "프리미엄", "KE", "대한항공"
        ]),
        "fail_msg": "대한항공 관련 키워드가 없습니다. 기업 가치와 연결하세요.",
        "type": "warning"
    },
    "safety_mention": {
        "name": "안전 키워드",
        "weight": 7,
        "check": lambda text, limit: "안전" in text,
        "fail_msg": "'안전' 키워드가 없습니다. 대한항공의 최우선 가치입니다.",
        "type": "warning"
    },

    # 클리셰 방지 (10점)
    "no_cliche": {
        "name": "탈락 클리셰",
        "weight": 10,
        "check": lambda text, limit: not any(w in text for w in [
            "어릴 때부터 비행기",
            "승무원 언니",
            "하늘을 나는 꿈",
            "비행기를 타면 설레",
            "멋진 유니폼",
            "글로벌 시대",
            "급변하는 사회",
            "꿈을 이루기 위해"
        ]),
        "fail_msg": "탈락 패턴 발견! 클리셰 표현을 삭제하세요.",
        "type": "fatal"
    }
}

# 문항별 추가 체크
Q1_CHECKS = {
    "no_dream_start": {
        "name": "꿈 시작 금지",
        "weight": 10,
        "check": lambda text: not any(w in text[:100] for w in [
            "어릴 때부터", "꿈이었", "오랜 꿈", "항상 동경"
        ]),
        "fail_msg": "'어릴 때부터 꿈이었습니다' 시작 = 탈락 패턴. 구체적 경험으로 시작하세요.",
        "type": "fatal"
    },
    "experience_exists": {
        "name": "경험 증거",
        "weight": 10,
        "check": lambda text: any(w in text for w in [
            "경험", "당시", "때", "년", "개월", "동안", "했습니다", "했던"
        ]),
        "fail_msg": "구체적 경험이 없습니다. 직무적합성은 경험으로 증명하세요.",
        "type": "critical"
    }
}

Q2_CHECKS = {
    "single_competency": {
        "name": "역량 1가지만",
        "weight": 12,
        "check": lambda text: True,  # LLM에서 체크
        "fail_msg": "역량은 반드시 1가지만 제시하세요. 2개 이상 쓰면 감점됩니다.",
        "type": "warning"
    },
    "safety_section": {
        "name": "안전 섹션",
        "weight": 10,
        "check": lambda text: "안전" in text,
        "fail_msg": "'안전' 부문 서술이 없거나 부족합니다.",
        "type": "critical"
    },
    "service_section": {
        "name": "서비스 섹션",
        "weight": 10,
        "check": lambda text: any(w in text for w in ["서비스", "고객", "승객", "응대"]),
        "fail_msg": "'서비스' 부문 서술이 없거나 부족합니다.",
        "type": "critical"
    }
}

Q3_CHECKS = {
    "burden_acknowledged": {
        "name": "부담 인정",
        "weight": 8,
        "check": lambda text: any(w in text for w in [
            "부담", "어려", "고민", "걱정", "솔직히", "망설",
            "쉽지 않", "선뜻", "부담스러", "힘들"
        ]),
        "fail_msg": "부담을 솔직히 인정하세요. 희생 미화는 탈락 패턴입니다.",
        "type": "critical"
    },
    "no_sacrifice": {
        "name": "희생 미화 금지",
        "weight": 10,
        "check": lambda text: not any(w in text for w in [
            "남들이 싫어", "아무도 안 해서", "팀을 위해 희생",
            "마다하지 않", "남들이 꺼려", "누구도 하지 않"
        ]),
        "fail_msg": "희생 미화 패턴 발견! '남들이 싫어서 제가 했다' → 수동적. 삭제하세요.",
        "type": "fatal"
    },
    "has_result": {
        "name": "결과 제시",
        "weight": 8,
        "check": lambda text: any(w in text for w in [
            "결과", "성과", "달성", "완료", "성공", "개선", "변화"
        ]),
        "fail_msg": "구체적 결과/성과가 없습니다. 행동의 결과를 수치로 제시하세요.",
        "type": "warning"
    }
}

QUESTION_CHECKS = {
    1: Q1_CHECKS,
    2: Q2_CHECKS,
    3: Q3_CHECKS
}


def calculate_realtime_score(text, question_number, char_limit=600):
    """
    실시간 완성도 점수 계산 (LLM 불필요)

    Returns:
        (score: int, feedbacks: list[dict], passed_checks: list[str])
    """
    if not text or len(text.strip()) < 10:
        return 0, [{"type": "warning", "name": "내용 없음", "message": "자소서 내용을 입력하세요.", "weight": 0}], []

    score = 0
    max_score = 0
    feedbacks = []
    passed_checks = []

    # 공통 체크
    for key, check in COMMON_CHECKS.items():
        max_score += check["weight"]
        try:
            if check["check"](text, char_limit):
                score += check["weight"]
                passed_checks.append(check["name"])
            else:
                feedbacks.append({
                    "type": check.get("type", "warning"),
                    "name": check["name"],
                    "message": check["fail_msg"],
                    "weight": check["weight"]
                })
        except:
            pass

    # 문항별 체크
    q_checks = QUESTION_CHECKS.get(question_number, {})
    for key, check in q_checks.items():
        max_score += check["weight"]
        try:
            if check["check"](text):
                score += check["weight"]
                passed_checks.append(check["name"])
            else:
                feedbacks.append({
                    "type": check.get("type", "warning"),
                    "name": check["name"],
                    "message": check["fail_msg"],
                    "weight": check["weight"]
                })
        except:
            pass

    percentage = round((score / max_score) * 100) if max_score > 0 else 0

    # 심각도 순 정렬 (fatal > critical > warning)
    type_order = {"fatal": 0, "critical": 1, "warning": 2}
    feedbacks.sort(key=lambda x: type_order.get(x["type"], 3))

    return percentage, feedbacks, passed_checks


# ═══════════════════════════════════════════
# 2. LLM 시스템 프롬프트
# ═══════════════════════════════════════════

SYSTEM_PROMPT_KOREAN_AIR_2026 = """
당신은 대한항공 객실승무원 채용 자소서 전문 첨삭관입니다.
10년간 대한항공 채용 면접관 경험이 있으며, 심리학과 행동경제학에 기반한 자소서 설계를 전문으로 합니다.

═══ 대한항공 2026 채용 정보 (사실 기반) ═══
- 자소서: 3문항, 각 600자 이내
- 전형: 서류 → 1차(온라인) → 2차+영어구술 → 3차+인성검사 → 건강검진/수영 → 최종

[1번 문항] "대한항공의 객실승무원이 되고 싶은 이유와 본인이 객실승무원 직무에 적합하다고 생각하는 이유를 구체적으로 서술하시오." (600자)
[2번 문항] "객실승무원에게 필요한 역량 한 가지를 제시하고, 그 이유를 안전과 서비스 부문으로 나누어 서술하시오." (600자)
[3번 문항] "본인이 선호하지 않거나 부담을 느끼는 과제를 맡게 되었을 때, 이를 어떻게 받아들이고 수행하였는지 구체적인 경험을 바탕으로 서술하시오." (600자)

═══ 대한항공 기업 정보 (사실 기반) ═══
- 1969년 설립, 스카이팀 창립 멤버, 44개국 120여 도시 취항
- 2024.12.11: 아시아나항공 지분 63.88% 인수 완료
- 아시아나는 더 이상 경쟁사가 아님. 통합 파트너.
- 인재상: 도전적, 글로벌, 전문적, 협력적

═══ 채점 기준 (100점) ═══

[구조 — 25점]
- 1번: 키워드 1개로 지원동기+적합성 관통 (8점)
- 2번: 안전/서비스 비중 1:1 균형 (7점)
- 3번: 5단계(부담인정→판단→노력→행동→포부) (6점)
- 공통: 600자 이내 + 적정 분량 (4점)

[내용 — 35점]
- 구체적 숫자/데이터 2개 이상 (8점)
- 경험↔승무원 직무 연결 (8점)
- "안전" 키워드 자연 반영 (7점)
- 통합 대한항공 이슈 반영 (7점)
- 인재상 키워드 자연스러움 (5점)

[표현 — 25점]
- 첫 문장 강렬함 = 앵커링 효과 (7점)
- 마지막 문장 여운 = 피크엔드 법칙 (6점)
- "열심히/최선" 추상어 없음 (6점)
- 어색/반복 없음 (6점)

[차별성 — 15점]
- 나만의 고유 경험 (5점)
- 심리학/행동경제학 관점 흔적 (5점)
- 면접관 마음 설계 흔적 (5점)

═══ 탈락 패턴 5가지 (즉시 감점) ═══
1. "어릴 때부터 승무원이 꿈" → 부정적 앵커링 → -15점
2. 지원동기/적합성 나눠 쓰기 → 600자 부족 → -10점
3. 2번에서 개념만 설명, 경험 없음 → -15점
4. 3번에서 희생 미화 → -12점
5. "최선을 다하겠습니다" 반복 → -8점

═══ 심리학/행동경제학 분석 관점 ═══
- 앵커링(Anchoring): 첫 문장에 강렬한 장면/숫자로 주의 고정
- 피크엔드 법칙(Peak-End Rule): 마지막 문장에 핵심 메시지 배치
- 구체성 편향(Concreteness Bias): 추상 → 구체 숫자로 교체
- 프레이밍(Framing): 평범한 경험을 직무 프레임으로 재구성
- 미러링(Mirroring): 대한항공 가치 키워드를 자연스럽게 반복

═══ 절대 원칙 ═══
1. 사실만 말하세요. 추측, 창작, 거짓 정보 절대 금지.
2. 합격/불합격 예측 절대 금지.
3. 지원자 경험을 창작/각색하는 행위 금지.

═══ 출력 형식 (반드시 이 JSON 형식으로) ═══
{
  "total_score": 점수(0-100),
  "grade": "S/A/B/C/D",
  "scores": {
    "structure": {"score": 0-25, "comment": "한 줄 평가"},
    "content": {"score": 0-35, "comment": "한 줄 평가"},
    "expression": {"score": 0-25, "comment": "한 줄 평가"},
    "differentiation": {"score": 0-15, "comment": "한 줄 평가"}
  },
  "fatal_patterns": ["발견된 탈락 패턴 목록. 없으면 빈 배열"],
  "psychology_analysis": {
    "anchoring": "첫 문장 앵커링 효과 분석 (1-2문장)",
    "peak_end": "마지막 문장 피크엔드 효과 분석 (1-2문장)",
    "framing": "경험의 프레이밍 분석 (1-2문장)",
    "concreteness": "구체성 수준 분석 (1-2문장)"
  },
  "sentence_feedback": [
    {
      "original": "원문 문장",
      "issue": "문제점",
      "suggestion": "수정 제안",
      "reason": "왜 이 수정이 효과적인지"
    }
  ],
  "overall_feedback": "3줄 이내 종합 평가",
  "improvement_priority": ["가장 먼저 고칠 것 3가지"]
}
"""

# 문항별 컨텍스트
QUESTION_CONTEXTS = {
    1: """
[분석 대상: 1번 문항 — 지원동기 + 직무적합성]
실제 문항: "대한항공의 객실승무원이 되고 싶은 이유와 본인이 객실승무원 직무에 적합하다고 생각하는 이유를 구체적으로 서술하시오."

[1번 문항 특별 체크]
1. 키워드 1개로 지원동기+적합성이 하나의 흐름으로 관통하는가?
2. "왜 대한항공인가" — 다른 항공사가 아닌 대한항공만의 이유가 있는가?
3. "왜 이 사람인가" — 직무적합성의 행동 증거가 있는가? (선언 X, 경험 O)
4. 600자는 매우 짧음. 지원동기/적합성을 나눠 쓰면 글자수 부족.

[즉시 탈락 패턴]
- "어릴 때부터 비행기를 타면 설레는 마음" → -15점
- 지원동기/적합성 분리 서술 → -10점
- "대한민국을 대표하는 항공사" 같은 일반론 → -5점
""",
    2: """
[분석 대상: 2번 문항 — 역량 (안전+서비스)]
실제 문항: "객실승무원에게 필요한 역량 한 가지를 제시하고, 그 이유를 안전과 서비스 부문으로 나누어 서술하시오."

[2번 문항 특별 체크]
1. 역량을 반드시 1가지만 제시했는가? (2개 이상 = 즉시 감점)
2. 안전/서비스를 동일한 비중으로 서술했는가? (한쪽 편중 = 탈락)
3. 개념 설명이 아닌 나만의 경험으로 증명했는가?
4. 안전과 서비스 각각에 구체적 경험+숫자가 있는가?

[즉시 탈락 패턴]
- 역량 개념만 설명하고 경험 없음 → -15점
- 안전만 길게 or 서비스만 길게 → -12점
- "저는 책임감이 강한 사람" 자기 선언만 → -10점
""",
    3: """
[분석 대상: 3번 문항 — 부담스러운 과제 수행]
실제 문항: "본인이 선호하지 않거나 부담을 느끼는 과제를 맡게 되었을 때, 이를 어떻게 받아들이고 수행하였는지 구체적인 경험을 바탕으로 서술하시오."

[3번 문항 특별 체크]
1. 부담을 솔직히 인정하는가? (희생 미화 X)
2. 맡기로 한 판단 기준이 명확한가? (= 사고 체계)
3. 부담을 줄이기 위한 구체적 노력이 있는가?
4. 실제 행동 2가지 이상 + 결과(숫자)가 있는가?
5. 5단계 구조: 부담인정→판단→노력→행동→포부

[즉시 탈락 패턴]
- "팀을 위해 희생했습니다" → -12점
- "남들이 싫어해서 제가 했습니다" → -10점
- 과정 생략하고 "결과적으로 좋은 성적" → -8점
"""
}


def build_user_prompt(question_number, resume_text):
    """문항별 특화 프롬프트 생성"""
    context = QUESTION_CONTEXTS.get(question_number, "")
    return f"""
{context}

[자소서 원문]
{resume_text}

위 자소서를 분석하고 JSON 형식으로 채점 결과를 출력하세요.
"""


# ═══════════════════════════════════════════
# 3. 기존 호환용 (다른 기능들)
# ═══════════════════════════════════════════

FACT_BASED_PRINCIPLE = """
[절대 원칙]
1. 사실만 말하세요. 추측, 창작, 거짓 정보 절대 금지.
2. 모르는 것은 "정확한 정보를 찾을 수 없습니다"라고 답하세요.
3. 합격/불합격 예측 절대 금지.
"""

FORBIDDEN_PATTERNS = [
    "합격할 것", "합격 가능성", "떨어질 것", "불합격할 것",
    "확실히", "반드시 ~할 것", "틀림없이",
    "내부 정보에 따르면", "관계자에 따르면",
]

# 챗봇용 프롬프트
CHATBOT_SYSTEM = """
당신은 대한항공 및 승무원 채용 준비 전문 AI 어시스턴트입니다.

{fact_principle}

[답변 가능 범위]
- 대한항공 기업 정보 (공식 출처 기반)
- 대한항공 채용 프로세스 (공식 공고 기반)
- 면접 준비 방법 (일반적 면접 스킬)
- 자소서 작성 조언 (구조/문장력 중심)

[답변 불가 범위 - 반드시 거절]
- 면접 결과 예측
- 비공식 합격 커트라인
- 검증 안 된 내부 정보

[답변 형식]
- 간결하고 명확하게
- 핵심 먼저, 부연 나중에
""".format(fact_principle=FACT_BASED_PRINCIPLE)

# 뉴스 분석용
NEWS_ANALYSIS_SYSTEM = """
당신은 대한항공 관련 뉴스를 면접 준비 관점에서 분석하는 전문가입니다.

{fact_principle}

[분석 기준]
- 면접 필수 숙지: 회사 실적, 합병, 사고, 정책 변경
- 알면 좋은 정보: 노선 확장, 서비스 변경, 수상
- 참고용: 일반 업계 뉴스
""".format(fact_principle=FACT_BASED_PRINCIPLE)

# 기존 호환용 (사용 안 함)
MOCK_INTERVIEW_SYSTEM = CHATBOT_SYSTEM
RESUME_REVIEW_SYSTEM = SYSTEM_PROMPT_KOREAN_AIR_2026


def check_forbidden_patterns(text: str) -> list:
    """금지 패턴 검사"""
    found = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            found.append(pattern)
    return found


def calculate_safety_service_ratio(text: str) -> dict:
    """
    2번 문항용: 안전/서비스 비중 측정

    Returns:
        {
            "safety_count": int,
            "service_count": int,
            "safety_ratio": float (0-100),
            "service_ratio": float (0-100),
            "balanced": bool,
            "warning": str or None
        }
    """
    # 문장 단위로 분리
    sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]

    safety_keywords = ["안전", "비상", "응급", "구조", "대피", "사고", "위험", "보호", "점검", "규정", "절차", "매뉴얼"]
    service_keywords = ["서비스", "고객", "승객", "응대", "만족", "배려", "친절", "케어", "요청", "불만", "해결", "소통"]

    safety_sentences = 0
    service_sentences = 0

    for sentence in sentences:
        has_safety = any(kw in sentence for kw in safety_keywords)
        has_service = any(kw in sentence for kw in service_keywords)

        if has_safety:
            safety_sentences += 1
        if has_service:
            service_sentences += 1

    total = safety_sentences + service_sentences
    if total == 0:
        return {
            "safety_count": 0,
            "service_count": 0,
            "safety_ratio": 50,
            "service_ratio": 50,
            "balanced": False,
            "warning": "안전/서비스 관련 내용이 감지되지 않습니다."
        }

    safety_ratio = round((safety_sentences / total) * 100)
    service_ratio = 100 - safety_ratio

    # 균형 판단 (30:70 ~ 70:30 범위면 OK)
    balanced = 30 <= safety_ratio <= 70

    warning = None
    if safety_ratio > 70:
        warning = f"안전 비중이 너무 높습니다 ({safety_ratio}%). 서비스 부문을 보강하세요."
    elif safety_ratio < 30:
        warning = f"서비스 비중이 너무 높습니다 ({service_ratio}%). 안전 부문을 보강하세요."

    return {
        "safety_count": safety_sentences,
        "service_count": service_sentences,
        "safety_ratio": safety_ratio,
        "service_ratio": service_ratio,
        "balanced": balanced,
        "warning": warning
    }


# ═══════════════════════════════════════════
# 4. 수정본 자동 생성 프롬프트
# ═══════════════════════════════════════════

REWRITE_SYSTEM_PROMPT = """
당신은 대한항공 객실승무원 자소서 전문 작성자입니다.
원본 자소서를 분석하고, 심리학/행동경제학 원칙에 따라 개선된 버전을 작성합니다.

═══ 수정 원칙 ═══
1. 원본의 핵심 경험/내용은 유지하되, 표현과 구조를 개선
2. 글자수 제한 엄수 (600자 이내)
3. 지원자가 쓰지 않은 경험을 창작하지 않음

═══ 필수 적용 ═══
- 앵커링: 첫 문장을 구체적 장면/숫자로 시작
- 피크엔드: 마지막 문장에 핵심 메시지와 여운
- 구체성: 추상적 표현 → 숫자/데이터로 교체
- 클리셰 제거: "어릴 때부터", "열심히", "최선을 다해" 등 삭제
- 대한항공 연결: 안전, KE Way 자연스럽게 반영

═══ 문항별 주의 ═══
[1번] 지원동기+적합성을 하나의 키워드로 관통
[2번] 안전/서비스 비중 1:1 균형
[3번] 부담 솔직히 인정, 희생 미화 금지

═══ 출력 형식 ═══
수정된 자소서만 출력하세요. 설명이나 주석 없이 본문만.
"""

def build_rewrite_prompt(question_number: int, original_text: str, feedbacks: list) -> str:
    """수정본 생성용 프롬프트"""
    feedback_text = "\n".join([f"- {fb}" for fb in feedbacks]) if feedbacks else "없음"

    return f"""
[문항 번호] {question_number}번

[원본 자소서]
{original_text}

[발견된 문제점]
{feedback_text}

위 문제점을 모두 개선한 수정본을 작성하세요.
글자수 600자 이내를 엄수하세요.
원본의 경험/내용은 유지하되 표현과 구조만 개선하세요.
"""
