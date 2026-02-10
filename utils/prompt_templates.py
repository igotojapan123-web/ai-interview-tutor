"""
FLYREADY 자소서 첨삭 시스템
대한항공 2026 객실승무원 채용 특화
심리학 + 행동경제학 기반
"""

import re

# ═══════════════════════════════════════════
# 1. 실시간 체크 (LLM 불필요) - 지식베이스 기반
# ═══════════════════════════════════════════

COMMON_CHECKS = {
    # 기본 분량
    "char_count": {
        "name": "적정 분량",
        "weight": 4,
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

    # 🚨 즉시 탈락 패턴 (빨간색)
    "no_childhood_dream": {
        "name": "어릴 때 꿈 클리셰",
        "weight": 15,
        "check": lambda text, limit: not any(w in text for w in [
            "어릴 때부터 비행기", "어릴 때부터 꿈", "승무원 언니",
            "하늘을 나는 꿈", "비행기를 타면 설레", "멋진 유니폼",
            "어린 시절부터", "오랜 꿈", "항상 동경"
        ]),
        "fail_msg": "🚨 탈락 패턴! '어릴 때부터 꿈' 클리셰는 즉시 -15점. 구체적 경험으로 시작하세요.",
        "type": "fatal"
    },
    "no_sacrifice_glorify": {
        "name": "희생 미화 금지",
        "weight": 12,
        "check": lambda text, limit: not any(w in text for w in [
            "남들이 싫어해서", "아무도 안 해서", "팀을 위해 희생",
            "마다하지 않", "남들이 꺼려", "누구도 하지 않"
        ]),
        "fail_msg": "🚨 탈락 패턴! 희생 미화는 수동적 인상. '왜 내가 적합했는가' 판단 과정으로 교체하세요.",
        "type": "fatal"
    },
    "no_vague_society": {
        "name": "모호한 사회론",
        "weight": 5,
        "check": lambda text, limit: not any(w in text for w in [
            "급변하는 사회", "글로벌 시대", "4차 산업혁명"
        ]),
        "fail_msg": "모호한 사회론 발견. 구체적 대한항공 이슈로 교체하세요.",
        "type": "warning"
    },

    # ⚠️ 주요 감점 (노란색)
    "strong_opening": {
        "name": "첫 문장 점검",
        "weight": 5,
        "check": lambda text, limit: not any(text.strip().startswith(w) for w in [
            "저는", "제가", "항상", "대한항공은", "승무원은", "저의"
        ]),
        "fail_msg": "⚠️ 첫 문장이 '저는~', '대한항공은~'으로 시작. 구체적 장면/숫자로 시작하세요. (앵커링)",
        "type": "critical"
    },
    "no_abstract_expressions": {
        "name": "추상 표현 감지",
        "weight": 3,
        "check": lambda text, limit: not any(w in text for w in [
            "열심히", "최선을 다", "노력하겠", "항상 밝은",
            "밝고 활발", "성실하게", "꼭 이루고", "간절히"
        ]),
        "fail_msg": "⚠️ '열심히', '최선을 다해' 등 추상 표현 발견. 구체적 행동으로 교체하세요. (-3점씩)",
        "type": "critical"
    },
    "strong_ending": {
        "name": "마지막 문장",
        "weight": 3,
        "check": lambda text, limit: not text.strip().endswith(("되겠습니다.", "하겠습니다.", "싶습니다.")),
        "fail_msg": "⚠️ 마지막 문장이 '~하겠습니다'로만 끝남. 나만의 고유한 문장으로 마무리하세요. (피크엔드)",
        "type": "warning"
    },

    # 구체성 - 숫자
    "has_numbers": {
        "name": "구체적 숫자",
        "weight": 5,
        "check": lambda text, limit: len(re.findall(r'\d+', text)) >= 1,
        "fail_msg": "⚠️ 숫자가 없습니다. 구체적 숫자 2개 이상 권장 (기간, 인원, 성과 등). 숫자 0개 = -5점",
        "type": "warning"
    },
    "has_two_numbers": {
        "name": "숫자 2개 이상",
        "weight": 3,
        "check": lambda text, limit: len(re.findall(r'\d+', text)) >= 2,
        "fail_msg": "💡 숫자 1개만 있음. 2개 이상 권장 (구체성 편향 - 숫자가 3배 더 신뢰)",
        "type": "warning"
    },

    # 안전 키워드
    "safety_mention": {
        "name": "안전 키워드",
        "weight": 5,
        "check": lambda text, limit: "안전" in text,
        "fail_msg": "⚠️ '안전' 키워드 없음 = -5점. 대한항공의 최우선 가치입니다.",
        "type": "warning"
    },

    # 행동 동사
    "has_action_verbs": {
        "name": "행동 동사",
        "weight": 3,
        "check": lambda text, limit: any(w in text for w in [
            "제안", "설계", "도입", "개선", "분석", "기획", "주도",
            "실행", "달성", "구축", "운영", "조율", "해결", "발견"
        ]),
        "fail_msg": "💡 행동 동사 부족. '제안', '설계', '도입', '분석' 등 사용 권장",
        "type": "warning"
    }
}

# 문항별 추가 체크
Q1_CHECKS = {
    "no_dream_start": {
        "name": "꿈 시작 금지",
        "weight": 15,
        "check": lambda text: not any(w in text[:100] for w in [
            "어릴 때부터", "꿈이었", "오랜 꿈", "항상 동경"
        ]),
        "fail_msg": "🚨 '어릴 때부터 꿈이었습니다' 시작 = -15점. 구체적 경험으로 시작하세요.",
        "type": "fatal"
    },
    "no_split_motive": {
        "name": "지원동기/적합성 분리 금지",
        "weight": 10,
        "check": lambda text: True,  # LLM에서 체크
        "fail_msg": "🚨 지원동기/적합성 분리 = -10점. 600자는 짧음. 키워드 1개로 관통하세요.",
        "type": "critical"
    },
    "experience_exists": {
        "name": "경험 증거",
        "weight": 8,
        "check": lambda text: any(w in text for w in [
            "경험", "당시", "때", "년", "개월", "동안", "했습니다", "했던"
        ]),
        "fail_msg": "구체적 경험 없음. 직무적합성은 '선언'이 아닌 '경험'으로 증명하세요.",
        "type": "critical"
    }
}

Q2_CHECKS = {
    "single_competency": {
        "name": "역량 1가지만",
        "weight": 10,
        "check": lambda text: True,  # LLM에서 체크
        "fail_msg": "🚨 역량 2개 이상 = -10점. 반드시 1가지만 제시하세요.",
        "type": "critical"
    },
    "safety_section": {
        "name": "안전 섹션",
        "weight": 7,
        "check": lambda text: "안전" in text,
        "fail_msg": "⚠️ '안전' 부문 서술이 없습니다. 안전/서비스 균형 1:1 필수!",
        "type": "critical"
    },
    "service_section": {
        "name": "서비스 섹션",
        "weight": 7,
        "check": lambda text: any(w in text for w in ["서비스", "고객", "승객", "응대"]),
        "fail_msg": "⚠️ '서비스' 부문 서술이 없습니다. 안전/서비스 균형 1:1 필수!",
        "type": "critical"
    },
    "has_experience": {
        "name": "개념이 아닌 경험",
        "weight": 15,
        "check": lambda text: any(w in text for w in [
            "경험", "당시", "때", "했습니다", "했던", "년", "개월"
        ]),
        "fail_msg": "🚨 개념 설명만 = -15점. 나만의 경험으로 역량을 증명하세요.",
        "type": "fatal"
    }
}

Q3_CHECKS = {
    "burden_acknowledged": {
        "name": "부담 인정",
        "weight": 5,
        "check": lambda text: any(w in text for w in [
            "부담", "어려", "고민", "걱정", "솔직히", "망설",
            "쉽지 않", "선뜻", "부담스러", "힘들"
        ]),
        "fail_msg": "⚠️ 부담 인정 없이 바로 해결 = -5점. 솔직히 부담을 인정하세요. (자기노출 효과)",
        "type": "critical"
    },
    "has_judgment": {
        "name": "판단 기준",
        "weight": 8,
        "check": lambda text: any(w in text for w in [
            "판단", "결정", "생각", "적합", "맞다고", "이유"
        ]),
        "fail_msg": "'왜 내가 하기로 결정했는가' 판단 과정이 없습니다. 사고 체계를 보여주세요.",
        "type": "warning"
    },
    "has_result": {
        "name": "결과 제시",
        "weight": 8,
        "check": lambda text: any(w in text for w in [
            "결과", "성과", "달성", "완료", "성공", "개선", "변화", "%", "향상"
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

═══ 대한항공 2026 채용 정보 ═══
- 자소서: 3문항, 각 600자 이내
- 전형: 서류 → 1차(온라인) → 2차+영어구술 → 3차+인성검사 → 건강검진/수영 → 최종
- 지원자격: 기졸업자 또는 2026.08 이전 졸업예정자, 교정시력 1.0 이상
- 어학: TOEIC 550+ / TOEIC Speaking IM+ / OPIc IM+ (2024.04.22 이후 응시분)

[1번] "대한항공의 객실 승무원이 되고싶은 이유와 본인이 객실 승무원 직무에 적합하다고 생각하는 이유를 구체적으로 서술하시오"
[2번] "객실승무원에게 필요한 역량 한 가지를 제시하고, 그 이유를 안전과 서비스 부문으로 나누어 서술하시오"
[3번] "본인이 선호하지 않거나 부담을 느끼는 과제를 맡게 되었을 때, 이를 어떻게 받아들이고 수행하였는지 구체적인 경험을 바탕으로 서술하시오"

═══ 대한항공 기업 정보 ═══
- 1969년 설립, 스카이팀 창립 멤버, 44개국 120여 도시 취항
- 2024.12.11: 아시아나항공 지분 63.88% 인수 완료 → 세계 11위 메가 캐리어
- 2026.01: 아시아나 인천공항 T2 이전 완료
- 2026.12: 아시아나 → 대한항공 브랜드 완전 통합 예정
- LCC 통합: 진에어·에어서울·에어부산 → 진에어로 통합 (2027년)
- ⚠️ 아시아나는 더 이상 경쟁사가 아님. 면접에서 경쟁사로 언급 시 감점!
- 인재상: 도전적(변화 대응), 글로벌(다문화 이해), 전문적(안전/서비스), 협력적(팀 시너지)

═══ 채점 기준 100점 ═══

[구조 — 25점]
- 1번: 키워드 1개로 지원동기+적합성 관통 (8점)
- 2번: 안전/서비스 비중 1:1 균형 (7점)
- 3번: 5단계(부담인정→판단→노력→행동→포부) (6점)
- 공통: 600자 이내 적정 분량 (4점)

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

═══ 🚨 즉시 탈락 패턴 (빨간색) ═══
- "어릴 때부터 비행기/꿈/승무원 언니" → -15점
- "하늘을 나는 꿈/비행기를 타면 설레/멋진 유니폼" → -15점
- 지원동기/적합성 분리 서술 (1번) → -10점
- 역량 2개 이상 제시 (2번) → -10점
- "남들이 싫어해서/팀을 위해 희생" (3번) → -12점
- "최선을 다하겠습니다" 반복 → -8점
- "아무도 안 해서 제가/마다하지 않" → -10점

═══ ⚠️ 주요 감점 (노란색) ═══
- 첫 문장 "저는~", "제가~", "대한항공은~" 시작 → -5점
- "열심히/최선을 다해/노력하겠/항상 밝은/밝고 활발" → -3점씩
- 마지막 문장 "~되겠습니다/~하겠습니다"로만 끝 → -3점
- 숫자 0개 → -5점
- "안전" 키워드 없음 → -5점
- 2번: 안전/서비스 비중 7:3 이상 편중 → -7점
- 3번: 부담 인정 없이 바로 해결 → -5점

═══ 심리학 원칙 ═══
- 앵커링(Anchoring): 첫 문장에 강렬한 장면/숫자로 주의 고정. 초두효과와 결합
- 피크엔드(Peak-End): 마지막 문장에 핵심 메시지. 기억에 남는 여운
- 자기노출 효과: 솔직한 약점 인정 → 역설적 신뢰 상승 ("솔직히 부담이 컸습니다")
- 인지적 재평가: 표면→본질 파악 ("줄이 길다"→"할 일이 없다")
- 사회적 증거: 제3자 평가/반응 활용
- 권위 효과: 본인 선언 X, 상사 평가 인용 → 신뢰도 급상승
- 처리 유창성: 진부한 표현은 기억 안 남음. 예상 깨는 디테일이 각인

═══ 행동경제학 원칙 ═══
- 구체성 편향: 추상보다 구체적 숫자가 3배 신뢰 ("서비스 경험 많음" vs "6개월간 제로")
- 프레이밍: 동일 경험도 프레임에 따라 가치 변화 ("카페 알바"→"안전 환경 설계 경험")
- 넛지 설계: 선언→구체적 행동 설계. 강제 아닌 자연스러운 유도
- 미러링: 대한항공 가치 키워드 자연스럽게 반복 → 무의식적 친밀감
- 선택 설계: 단순 실행자 X, '경험을 설계하는 사람'으로 포지셔닝
- 손실 회피: 기회 아닌 '해야 할 과제'로 프레이밍

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
실제 문항: "대한항공의 객실 승무원이 되고싶은 이유와 본인이 객실 승무원 직무에 적합하다고 생각하는 이유를 구체적으로 서술하시오"

[면접관이 진짜 보는 것]
1. "왜 대한항공인가" — 다른 항공사가 아닌 대한항공만의 이유 (안전, 통합, 글로벌)
2. "왜 이 사람인가" — 직무적합성의 행동 증거 (선언 X, 경험 O)
3. 지원동기와 적합성이 하나의 키워드로 연결되는가
⚠️ 600자는 매우 짧음. 하나의 키워드로 전체를 관통하지 않으면 글자 수 무너짐

[합격 구조]
- 첫 문장: 구체적 장면/숫자로 시작 (앵커링)
- 중반: 경험 → 대한항공 가치 연결 (미러링)
- 끝 문장: 고유한 메시지 (피크엔드)

[즉시 탈락 패턴]
- "어릴 때부터 비행기를 타면 설레는 마음" → 부정적 앵커링 즉시 작동 → -15점
- "밝고 활발한 성격" → 자기 봉사 편향, 본인 선언은 증거 아님 → -5점
- 지원동기/적합성 분리 서술 → -10점
- "대한민국을 대표하는 항공사" 같은 일반론 → -5점
""",
    2: """
[분석 대상: 2번 문항 — 역량 (안전+서비스)]
실제 문항: "객실승무원에게 필요한 역량 한 가지를 제시하고, 그 이유를 안전과 서비스 부문으로 나누어 서술하시오"

[면접관이 진짜 보는 것]
1. 역량을 반드시 1가지만 제시했는가 (2개 이상 = 감점)
2. 안전/서비스를 동일한 비중으로 서술했는가 (한쪽 편중 = 탈락)
3. 개념 설명이 아닌 나만의 경험으로 증명했는가
⚠️ 이 문항은 '균형감각 테스트'. 안전만 길게 or 서비스만 길게 = 바로 감점

[합격 구조]
- [역량] 첫 문장에 역량 1가지 명확 선언
- [안전] 안전 파트 (~150자): 안전 관련 경험 + 숫자
- [서비스] 서비스 파트 (~150자): 서비스 관련 경험 + 숫자
- [포부] 안전+서비스 모두 키워드 반복 마무리
- 비중: 안전/서비스 거의 1:1

[역량 예시]
- 팀워크: 체육대회 응급처치 역할분담 + 호텔 체크인 지연 동료 분담
- 상황 판단력: 편의점 정전 3단계 대응 + 고객 피로 파악
- 커뮤니케이션: 산악회 기상악화 3단계 지시 + 일본인 고객 비언어 신호

[즉시 탈락 패턴]
- "책임감이라 생각합니다" → 확증 편향의 역효과, '또 이거네' → -10점
- 역량 개념만 설명하고 경험 없음 → -15점
- 안전만 길게 or 서비스만 길게 (7:3 이상) → -7점
- "저는 책임감이 강한 사람" 자기 선언만 → -10점
""",
    3: """
[분석 대상: 3번 문항 — 부담스러운 과제 수행]
실제 문항: "본인이 선호하지 않거나 부담을 느끼는 과제를 맡게 되었을 때, 이를 어떻게 받아들이고 수행하였는지 구체적인 경험을 바탕으로 서술하시오"

[면접관이 진짜 보는 것]
1. 부담을 솔직히 인정하는가 (희생 미화 X)
2. 맡기로 한 판단 기준이 명확한가 (= 사고 체계)
3. 부담을 줄이기 위한 구체적 노력이 있는가
4. 실제 행동 2가지 이상과 결과(숫자)가 있는가
⚠️ 핵심은 '사고 체계'. "내가 하는 게 가장 맞다"고 스스로 납득한 과정

[5단계 합격 구조]
1. [부담] 솔직히 부담 인정 ("솔직히 부담이 컸습니다" → 자기노출 효과)
2. [판단] 왜 내가 하기로 결정했는가 (판단 기준)
3. [노력] 부담을 줄이기 위한 구체적 노력
4. [행동] 실제 행동 2가지 이상 + 결과(숫자)
5. [포부] 승무원 직무 연결

[즉시 탈락 패턴]
- "팀을 위해 했다" → 외적 동기만. 내적 판단 과정 없음 → -12점
- "남들이 싫어해서 제가 했습니다" → 수동적 → -10점
- "결과적으로 좋은 성적" → 후광 효과에 기대. 과정 없이 결과만 → -8점
- 부담 인정 없이 바로 해결 → -5점
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


# ═══════════════════════════════════════════
# 4. 하이브리드 채점 v3.0 - 코드 기반 정량 채점 (60점)
# ═══════════════════════════════════════════

def score_by_code(text: str, question_num: int) -> dict:
    """
    코드가 직접 채점. 매번 100% 동일한 점수.
    총 60점 = 구조(20) + 내용(25) + 표현(15)
    """
    import re

    score = 0
    details = {}

    # ═══════════════════════════════════
    # A. 구조 점수 (20점)
    # ═══════════════════════════════════

    structure_score = 0

    # A-1. 글자수 적정성 (5점)
    char_count = len(text.replace(" ", "").replace("\n", ""))
    if char_count > 600:
        structure_score += 0
        details["char_count"] = {"score": 0, "reason": f"600자 초과 ({char_count}자)"}
    elif char_count >= 540:  # 90%+
        structure_score += 5
        details["char_count"] = {"score": 5, "reason": f"적정 ({char_count}자)"}
    elif char_count >= 480:  # 80%+
        structure_score += 3
        details["char_count"] = {"score": 3, "reason": f"약간 부족 ({char_count}자)"}
    elif char_count >= 360:  # 60%+
        structure_score += 1
        details["char_count"] = {"score": 1, "reason": f"부족 ({char_count}자)"}
    else:
        structure_score += 0
        details["char_count"] = {"score": 0, "reason": f"심각하게 부족 ({char_count}자)"}

    # A-2. 문장 수 (3점)
    sentences = [s.strip() for s in re.split(r'[.!?]\s', text) if len(s.strip()) > 5]
    sentence_count = len(sentences)
    if sentence_count >= 6:
        structure_score += 3
    elif sentence_count >= 4:
        structure_score += 2
    elif sentence_count >= 2:
        structure_score += 1
    details["sentence_count"] = {"score": min(3, max(0, sentence_count - 3)), "count": sentence_count}

    # A-3. 문항별 구조 체크 (12점)
    if question_num == 1:
        has_why_ke = any(kw in text for kw in ["대한항공", "KE", "통합", "메가", "스카이팀"])
        has_why_me = any(kw in text for kw in ["경험", "했습니다", "했고", "만들었", "도입", "제안"])
        has_plan = any(kw in text for kw in ["입사 후", "되겠습니다", "기여", "목표", "싶습니다"])

        if has_why_ke:
            structure_score += 4
        if has_why_me:
            structure_score += 4
        if has_plan:
            structure_score += 4
        details["q1_structure"] = {
            "why_ke": has_why_ke,
            "why_me": has_why_me,
            "plan": has_plan
        }

    elif question_num == 2:
        safety_keywords = ["안전", "비상", "위기", "매뉴얼", "브리핑", "보호"]
        service_keywords = ["서비스", "고객", "승객", "만족", "배려", "소통", "공감"]

        safety_count = sum(1 for kw in safety_keywords if kw in text)
        service_count = sum(1 for kw in service_keywords if kw in text)

        total = safety_count + service_count
        safety_ratio = 0.5
        if total > 0:
            safety_ratio = safety_count / total
            if 0.3 <= safety_ratio <= 0.7:
                structure_score += 6
            elif 0.2 <= safety_ratio <= 0.8:
                structure_score += 3
            else:
                structure_score += 0
        else:
            structure_score += 0

        competency_markers = ["역량은", "능력은", "자질은", "가장 필요한", "가장 중요한", "필요한 역량"]
        has_competency = any(m in text for m in competency_markers)
        if has_competency:
            structure_score += 3

        has_section = ("안전" in text and "서비스" in text)
        if has_section:
            structure_score += 3

        details["q2_structure"] = {
            "safety_ratio": round(safety_ratio * 100) if total > 0 else 0,
            "service_ratio": round((1 - safety_ratio) * 100) if total > 0 else 0,
            "has_competency": has_competency,
            "has_both_sections": has_section
        }

    elif question_num == 3:
        burden_markers = ["부담", "어려", "힘들", "싫", "꺼려", "불안", "걱정", "선뜻"]
        judgment_markers = ["판단", "결정", "생각", "적합", "해야", "맡기로", "받아들"]
        effort_markers = ["노력", "분석", "파악", "확인", "면담", "관찰", "청취"]
        action_markers = ["도입", "제안", "설계", "만들", "변경", "실행", "적용"]
        result_markers = ["결과", "향상", "감소", "증가", "개선", "성공", "변화", "%"]

        has_burden = any(m in text for m in burden_markers)
        has_judgment = any(m in text for m in judgment_markers)
        has_effort = any(m in text for m in effort_markers)
        has_action = any(m in text for m in action_markers)
        has_result = any(m in text for m in result_markers)

        steps = [has_burden, has_judgment, has_effort, has_action, has_result]
        step_count = sum(steps)

        if step_count >= 5:
            structure_score += 12
        elif step_count >= 4:
            structure_score += 9
        elif step_count >= 3:
            structure_score += 6
        elif step_count >= 2:
            structure_score += 3
        else:
            structure_score += 0

        details["q3_structure"] = {
            "burden": has_burden,
            "judgment": has_judgment,
            "effort": has_effort,
            "action": has_action,
            "result": has_result,
            "step_count": step_count
        }

    # ═══════════════════════════════════
    # B. 내용 점수 (25점)
    # ═══════════════════════════════════

    content_score = 0

    # B-1. 숫자/데이터 포함 (8점)
    numbers = re.findall(r'\d+', text)
    meaningful_numbers = [n for n in numbers if n not in ["600", "500", "800", "1000"]]
    num_count = len(meaningful_numbers)

    if num_count >= 4:
        content_score += 8
    elif num_count >= 3:
        content_score += 6
    elif num_count >= 2:
        content_score += 4
    elif num_count >= 1:
        content_score += 2
    else:
        content_score += 0
    details["numbers"] = {"score": min(8, num_count * 2), "count": num_count, "found": meaningful_numbers[:5]}

    # B-2. 행동 동사 (5점)
    action_verbs = ["제안", "도입", "설계", "개선", "분석", "기획", "운영",
                    "주도", "달성", "확보", "구축", "실행", "변경", "적용",
                    "만들", "이끌", "해결", "발견", "줄이", "높이"]
    found_verbs = [v for v in action_verbs if v in text]
    verb_count = len(found_verbs)

    if verb_count >= 4:
        content_score += 5
    elif verb_count >= 3:
        content_score += 4
    elif verb_count >= 2:
        content_score += 3
    elif verb_count >= 1:
        content_score += 1
    details["action_verbs"] = {"score": min(5, verb_count + 1), "found": found_verbs}

    # B-3. 안전 키워드 (5점)
    safety_words = ["안전", "비상", "위기", "매뉴얼", "브리핑", "보호", "예방", "사고"]
    safety_found = [w for w in safety_words if w in text]
    if len(safety_found) >= 2:
        content_score += 5
    elif len(safety_found) >= 1:
        content_score += 3
    else:
        content_score += 0
    details["safety"] = {"found": safety_found}

    # B-4. 대한항공/통합 이슈 (4점)
    ke_keywords = ["대한항공", "통합", "메가 캐리어", "아시아나", "스카이팀",
                   "44개국", "120", "세계 11위", "KE Way", "프리미엄"]
    ke_found = [k for k in ke_keywords if k in text]
    if len(ke_found) >= 2:
        content_score += 4
    elif len(ke_found) >= 1:
        content_score += 2
    details["ke_keywords"] = {"found": ke_found}

    # B-5. 인재상 키워드 (3점)
    talent_keywords = ["도전", "글로벌", "전문", "협력", "소통", "팀", "성장", "변화"]
    talent_found = [t for t in talent_keywords if t in text]
    if len(talent_found) >= 2:
        content_score += 3
    elif len(talent_found) >= 1:
        content_score += 1
    details["talent"] = {"found": talent_found}

    # ═══════════════════════════════════
    # C. 표현 점수 (15점)
    # ═══════════════════════════════════

    expression_score = 0

    # C-1. 탈락 패턴 감점 (벌점제)
    fatal_patterns = {
        "어릴 때부터": -8,
        "승무원 언니": -8,
        "하늘을 나는 꿈": -8,
        "비행기를 타면 설레": -5,
        "남들이 싫어해서": -6,
        "팀을 위해 희생": -6,
        "아무도 안 해서": -5,
    }
    penalty = 0
    triggered_fatal = []
    for pattern, deduction in fatal_patterns.items():
        if pattern in text:
            penalty += deduction
            triggered_fatal.append(pattern)
    details["fatal_patterns"] = {"triggered": triggered_fatal, "penalty": penalty}

    # C-2. 클리셰 감점
    cliche_patterns = ["최선을 다", "열심히", "노력하겠", "항상 밝은", "밝고 활발",
                       "성실하게", "간절히", "꼭 이루고"]
    found_cliches = [c for c in cliche_patterns if c in text]
    cliche_penalty = len(found_cliches) * -2
    details["cliches"] = {"found": found_cliches, "penalty": cliche_penalty}

    # C-3. 첫 문장 품질 (5점)
    first_sentence = sentences[0] if sentences else ""
    weak_starts = ["저는", "제가", "항상", "대한항공은", "객실승무원은", "어릴"]
    strong_start = not any(first_sentence.startswith(ws) for ws in weak_starts)
    has_number_in_first = bool(re.search(r'\d', first_sentence))

    if strong_start and has_number_in_first:
        expression_score += 5
    elif strong_start:
        expression_score += 3
    elif has_number_in_first:
        expression_score += 2
    else:
        expression_score += 0
    details["first_sentence"] = {
        "text": first_sentence[:50],
        "strong_start": strong_start,
        "has_number": has_number_in_first
    }

    # C-4. 마지막 문장 품질 (5점)
    last_sentence = sentences[-1] if sentences else ""
    generic_endings = ["되겠습니다", "하겠습니다", "싶습니다", "바랍니다"]
    is_generic_end = any(last_sentence.endswith(ge) for ge in generic_endings)

    if not is_generic_end and len(last_sentence) > 20:
        expression_score += 5
    elif not is_generic_end:
        expression_score += 3
    elif len(last_sentence) > 30:
        expression_score += 1
    details["last_sentence"] = {
        "text": last_sentence[:50],
        "is_generic": is_generic_end
    }

    # C-5. 반복 표현 체크 (5점)
    words = re.findall(r'[가-힣]{2,}', text)
    word_freq = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1
    repeated = {w: c for w, c in word_freq.items() if c >= 3 and w not in ["대한항공", "승무원", "서비스", "안전"]}

    if len(repeated) == 0:
        expression_score += 5
    elif len(repeated) <= 2:
        expression_score += 3
    else:
        expression_score += 0
    details["repetition"] = {"repeated_words": repeated}

    # 벌점 적용
    expression_score = max(0, expression_score + penalty + cliche_penalty)

    # ═══════════════════════════════════
    # 최종 코드 점수
    # ═══════════════════════════════════

    total_code_score = structure_score + content_score + expression_score
    total_code_score = max(0, min(60, total_code_score))

    return {
        "total": total_code_score,
        "structure": {"score": min(20, structure_score), "max": 20},
        "content": {"score": min(25, content_score), "max": 25},
        "expression": {"score": min(15, max(0, expression_score)), "max": 15},
        "details": details
    }


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
