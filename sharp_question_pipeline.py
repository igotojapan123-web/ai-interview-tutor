"""
========================================
면접 질문 생성 시스템 v3.0 - HyperCLOVA X
========================================

5단계 GATE 검증이 통합된 다단계 파이프라인
- HyperCLOVA X 한국어 최적화 모델 사용
- 할루시네이션 방지
- 문맥 정확성 보장
- 논리적 타당성 검증
- 품질 보장
"""

import os
import json
import time
import hashlib
import re
import requests
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging_config import get_logger

logger = get_logger(__name__)

# ===========================================
# HyperCLOVA X 클라이언트 (CLOVA Studio 서비스 앱)
# ===========================================
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "nv-f59b211212244304b064c131640a92a0UgPZ")
CLOVA_REQUEST_ID = os.getenv("CLOVA_REQUEST_ID", "331785bac0c64228ac15f5616d9082d7")
CLOVA_HOST = "https://clovastudio.stream.ntruss.com"
CLOVA_MODEL = "HCX-005"  # 서비스 앱에서 승인된 모델


# ===========================================
# STEP 1: 자소서 파싱 프롬프트
# ===========================================

RESUME_PARSER_PROMPT = """
당신은 항공사 면접 전문가입니다.
아래 자소서에서 문항과 답변을 정확히 분리하세요.

<resume>
{resume_text}
</resume>

## 출력 형식 (JSON)

{{
  "questions": [
    {{
      "q_num": 1,
      "question_text": "문항 원문 (그대로 복사)",
      "answer_text": "답변 원문 (그대로 복사)"
    }}
  ]
}}

## 규칙
- 문항과 답변을 정확히 구분
- 원문을 수정하거나 요약하지 말 것
- 문항이 명시되지 않으면 문맥으로 추론
"""


# ===========================================
# STEP 2+3 통합: 분석 + 취약점 탐지 (API 1회로 처리)
# ===========================================

COMBINED_ANALYSIS_PROMPT = """
아래 자소서 답변을 분석하고 면접 질문으로 공격 가능한 포인트를 찾으세요.

<question>
{question_text}
</question>

<answer>
{answer_text}
</answer>

## 출력 형식 (JSON)

{{
  "key_sentences": [
    {{
      "sentence": "원문 문장 (정확히 복사 - 한 글자도 바꾸지 말 것)",
      "type": "가치선언|경험제시|깨달음|포부",
      "attack_angle": "공격 각도 (손해/실패/반례/숫자검증 등)"
    }}
  ],
  "vulnerabilities": [
    {{
      "type": "exaggeration|abstraction|no_evidence|receiver_bias",
      "target_sentence": "해당 문장 (원문 그대로)",
      "attack_angle": "공격 각도"
    }}
  ]
}}

## 규칙
- sentence는 반드시 원문 그대로 복사 (한 글자도 바꾸지 말 것!)
- 핵심 문장 3-5개 추출
- 취약점 2-4개 탐지
"""


# ===========================================
# 통합 프롬프트: 분석 + 질문생성 (API 1회) - 클로바 스튜디오 최적화
# ===========================================

UNIFIED_ANALYSIS_AND_QUESTION_PROMPT = """
## 자기소개서
{answer_text}

---

## 취약점 유형 + 질문 공식

| 취약점 | 질문 패턴 |
|--------|----------|
| 가치선언 | "~라고 하셨는데, ~ 때문에 손해 본 적은 없습니까?" |
| 수혜주장 | "~덕분에 극복했다고 하셨는데, 반대로 본인이 기여한 건 구체적으로 뭡니까?" |
| 성과주장 | "~했다고 하셨는데, 실제로 몇 승/몇 번/몇 명이었습니까?" |
| 선택상황 | "~한 건 본인 선택입니까, [다른사람] 결정입니까?" |
| 방법론 | "~에 안 맞는 사람이 있으면요? 계속 안 맞으면요?" |
| 긍정주장 | "~라고 하셨는데, 반대로 ~못한/~안된 경우는 없었습니까?" |

## 출력 (JSON)
```json
{{
  "key_sentences": [{{"sentence": "원문", "weakness": "취약점유형"}}],
  "questions": [
    {{
      "id": "Q1",
      "type": "역방향|수혜자검증|성과검증|선택검증|한계탐색|딜레마",
      "quoted_sentence": "원문",
      "question": "~입니까?/~없습니까?/~뭡니까? 형태",
      "intent": "검증의도",
      "follow_up": {{"trigger": "예상답변", "question": "꼬리질문"}}
    }}
  ]
}}
```

## 금지: "어떻게~", "설명해주세요", "~하시겠습니까?"
## 필수: "~없습니까?", "~입니까?", "~뭡니까?"

질문 3개 생성.
"""


# ===========================================
# 클로바 최적화: 분석 + 공격 각도 제안 프롬프트
# ===========================================

CLOVA_4STAGE_ANALYSIS_PROMPT = """당신은 항공사 채용 압박 면접 전문가입니다.
자기소개서를 분석하고, 각 취약점에 대해 적절한 공격 질문을 제안합니다.

## 분석 원칙
- 문항을 먼저 완전히 이해한 후 답변을 분석합니다
- 추측하지 않고 텍스트에 명시된 내용만 판단합니다

## 취약점 유형 + 공격 질문 매칭

| 문맥 | 취약점 | 적절한 공격 질문 |
|------|--------|-----------------|
| 가치/신념 선언 | 논리_비약 | "~때문에 손해 본 적은 없습니까?" |
| 팀/공동체 언급 | 수혜_주장 | "반대로 본인이 기여한 건 뭡니까?" |
| 성과/결과 언급 | 구체성_부족 | "실제로 몇 번/얼마였습니까?" |
| 선택/결정 언급 | 증명_불가 | "본인 선택입니까, [누구] 결정입니까?" |
| 극복/성장 언급 | 과장_의심 | "못했던 경우는 없었습니까?" |
| 방법/태도 언급 | 한계_존재 | "안 통하는 사람은 어떻게 합니까?" |

## 질문 형식 규칙 (매우 중요!)

### 필수 어미 (이것만 사용!)
- "~없습니까?"
- "~입니까?"
- "~뭡니까?"

### 금지 패턴 (절대 사용 금지!)
- "~나요?" ❌
- "~어요?" ❌
- "~하시겠습니까?" / "~겠습니까?" ❌
- "설명해주세요" / "말씀해주세요" ❌
- "어떻게 ~" ❌ (어떻게로 시작하는 질문 금지)
- "이러한", "그러한", "이런", "그런" ❌ (막연한 지시어 금지 - 구체적 내용 명시!)
  - ❌ "이러한 이미지를 유지하고 있는지" → 무슨 이미지?
  - ⭕ "안정감 있는 응대라는 이미지를 유지하고 있는지"

### 한국어 문법 규칙 (필수!)
- "뭡니까" 앞에는 "가/이" 사용: "의미가 뭡니까?" ⭕ / "의미를 뭡니까?" ❌
- "~는지"와 "뭡니까"는 같이 못 씀: "무엇인지 뭡니까?" ❌
- 완결된 문장으로만 질문: "어떤 노력을 해왔습니까?" ⭕

### 필수 구조
"[짧은 인용]~라고 하셨는데, [공격]~입니까?"

## 출력 형식 (JSON)

```json
{{
  "items": [
    {{
      "item_num": 1,
      "vulnerabilities": [
        {{
          "type": "논리_비약|구체성_부족|수혜_주장|증명_불가|한계_존재",
          "target_text": "자소서 원문 (20자 이내로 핵심만)",
          "attack_angle": "손해/실패/반례/숫자/선택/한계 중 하나",
          "suggested_question": "[인용]~라고 하셨는데, [공격]~입니까? 형식",
          "followup": "꼬리질문"
        }}
      ]
    }}
  ]
}}
```

## 좋은 질문 예시

1. 가치 선언 → 손해 공격
   - 원문: "팀워크가 제일 중요하다"
   - 질문: "팀워크가 중요하다고 하셨는데, 팀워크 때문에 손해 본 적은 없습니까?"

2. 공동체 수혜 → 기여 검증
   - 원문: "공동체 덕분에 극복했다"
   - 질문: "공동체 덕분이라고 하셨는데, 본인 혼자서는 뭘 못 합니까?"

3. 선택/결정 → 주체 검증
   - 원문: "중학생 때 유학을 갔다"
   - 질문: "중학생 때 유학 간 건 본인 선택입니까, 부모님 결정입니까?"

4. 성과 언급 → 숫자 검증
   - 원문: "환경을 조성했다"
   - 질문: "환경을 조성했다고 하셨는데, 그래서 결과가 어땠습니까? 몇 승 몇 패였습니까?"

5. 방법 언급 → 한계 탐색
   - 원문: "대화로 해결했다"
   - 질문: "대화로 해결했다고 하셨는데, 대화해도 안 되면요?"

## 자기소개서
{full_resume}

각 문항에서 취약점 3-5개를 찾고, 각각에 적절한 공격 질문을 제안하세요.
"""


# ===========================================
# FLYREADY 질문 패턴 매핑 (로컬 처리)
# ===========================================

# 취약점 유형별 질문 공식
FLYREADY_QUESTION_PATTERNS = {
    "논리_비약": [
        ("역방향", "'{quote}'라고 하셨는데, {opposite} 때문에 손해 본 적은 없습니까?"),
        ("한계탐색", "'{quote}'라고 하셨는데, 그게 안 통하는 경우는 없었습니까?"),
        ("딜레마", "'{quote}'라고 하셨는데, {opposite}와 충돌하면 어떻게 합니까?"),
    ],
    "구체성_부족": [
        ("성과검증", "'{quote}'라고 하셨는데, 실제로 몇 번/몇 승/몇 명이었습니까?"),
        ("수혜자검증", "'{quote}'라고 하셨는데, 반대로 본인이 기여한 건 구체적으로 뭡니까?"),
        ("검증", "'{quote}'라고 하셨는데, 구체적인 결과는 뭡니까?"),
    ],
    "불일치": [
        ("딜레마", "'{quote}'라고 하셨는데, 앞서 말씀하신 것과 다른데 어느 쪽입니까?"),
        ("역방향", "'{quote}'라고 하셨는데, 정반대 상황에서도 그렇게 합니까?"),
    ],
    "증명_불가": [
        ("선택검증", "'{quote}'라고 하셨는데, 본인 선택입니까 아니면 다른 사람 결정입니까?"),
        ("수혜자검증", "'{quote}'라고 하셨는데, 혼자서는 못 했을 겁니까?"),
        ("성과검증", "'{quote}'라고 하셨는데, 증거나 결과물이 있습니까?"),
    ]
}

# 범용 공격 패턴 (취약점 유형에 관계없이 적용 가능)
FLYREADY_UNIVERSAL_PATTERNS = [
    ("역방향", "'{quote}'라고 하셨는데, 그 때문에 손해 본 적은 없습니까?"),
    ("한계탐색", "'{quote}'라고 하셨는데, 안 되는 경우는 없었습니까?"),
    ("수혜자검증", "'{quote}'라고 하셨는데, 반대로 본인이 한 건 뭡니까?"),
    ("성과검증", "'{quote}'라고 하셨는데, 구체적으로 뭡니까?"),
    ("선택검증", "'{quote}'라고 하셨는데, 본인 의지입니까?"),
]

# 꼬리질문 패턴
FLYREADY_FOLLOWUP_PATTERNS = {
    "역방향": ["그래도 {keyword}가 중요합니까?", "다시 그 상황이면 똑같이 합니까?"],
    "한계탐색": ["계속 안 되면요?", "그래도 안 바뀌면요?", "포기합니까?"],
    "수혜자검증": ["그럼 본인 없어도 됐겠네요?", "혼자서도 할 수 있었습니까?"],
    "성과검증": ["그게 성공입니까, 실패입니까?", "만족합니까?"],
    "선택검증": ["가기 싫었습니까?", "후회하지 않습니까?"],
    "딜레마": ["하나만 선택하면요?", "둘 다 안 되면요?"],
}


def extract_opposite_concept(text: str) -> str:
    """텍스트에서 반대 개념 추출"""
    opposites = {
        "팀워크": "개인 성과",
        "협력": "경쟁",
        "공동체": "혼자",
        "함께": "혼자",
        "도움": "방해",
        "성공": "실패",
        "극복": "포기",
        "노력": "재능",
        "긍정": "부정",
        "적극": "소극",
        "소통": "갈등",
        "배려": "이기심",
        "책임": "회피",
        "도전": "안주",
        "성장": "정체",
    }

    for keyword, opposite in opposites.items():
        if keyword in text:
            return opposite
    return "반대 상황"


def extract_keyword_from_quote(quote: str) -> str:
    """인용문에서 핵심 키워드 추출"""
    # 주요 명사/동사 추출 (간단한 휴리스틱)
    keywords = ["팀워크", "협력", "공동체", "유학", "경험", "노력", "도전", "성장",
                "환경", "분위기", "소통", "배려", "책임", "리더십", "서비스"]

    for kw in keywords:
        if kw in quote:
            return kw

    # 못 찾으면 첫 명사구 반환
    words = quote.split()
    if len(words) >= 2:
        return words[0] + words[1]
    return quote[:10] if len(quote) > 10 else quote


def generate_questions_from_vulnerabilities(vulnerabilities: List[Dict], full_answer: str) -> List[Dict]:
    """
    취약점 목록에서 질문 생성
    - CLOVA가 제안한 질문이 있으면 그것을 사용 (형식만 검증/수정)
    - 없으면 FLYREADY 패턴으로 폴백

    Args:
        vulnerabilities: CLOVA가 분석한 취약점 리스트
        full_answer: 원본 자소서 답변 텍스트

    Returns:
        생성된 질문 리스트
    """
    questions = []
    used_quotes = set()  # 중복 인용 방지

    for vuln in vulnerabilities:
        vuln_type = vuln.get("type", "논리_비약")
        target_text = vuln.get("target_text", "")
        suggested_q = vuln.get("suggested_question", "")
        followup = vuln.get("followup", "")
        attack_angle = vuln.get("attack_angle", "")

        if not target_text or target_text in used_quotes:
            continue

        used_quotes.add(target_text)

        # CLOVA가 제안한 질문이 있으면 형식 검증 후 사용
        if suggested_q and len(suggested_q) >= 15:
            question_text = _validate_and_fix_question_format(suggested_q)

            # 꼬리질문도 CLOVA 제안 사용
            if not followup:
                followup = _generate_followup(attack_angle, target_text)

            questions.append({
                "id": f"Q{len(questions) + 1}",
                "type": attack_angle or vuln_type,
                "quoted_sentence": target_text,
                "question": question_text,
                "intent": f"{vuln_type} 공격",
                "follow_up": {
                    "trigger": "변명/회피 시",
                    "question": followup
                },
                "vulnerability_type": vuln_type,
                "source": "clova_suggested"
            })
        else:
            # CLOVA 제안이 없으면 FLYREADY 패턴 폴백
            patterns = FLYREADY_QUESTION_PATTERNS.get(vuln_type, FLYREADY_UNIVERSAL_PATTERNS)
            q_type, template = patterns[0]

            opposite = extract_opposite_concept(target_text)
            keyword = extract_keyword_from_quote(target_text)

            question_text = template.format(
                quote=target_text[:40] + "..." if len(target_text) > 40 else target_text,
                opposite=opposite,
                keyword=keyword
            )

            followup_templates = FLYREADY_FOLLOWUP_PATTERNS.get(q_type, ["그래서요?"])
            followup_text = followup_templates[0].format(keyword=keyword)

            questions.append({
                "id": f"Q{len(questions) + 1}",
                "type": q_type,
                "quoted_sentence": target_text,
                "question": question_text,
                "intent": f"{vuln_type} 공격",
                "follow_up": {
                    "trigger": "변명/회피 시",
                    "question": followup_text
                },
                "vulnerability_type": vuln_type,
                "source": "flyready_pattern"
            })

    return questions


def _validate_and_fix_question_format(question: str) -> str:
    """
    질문 형식 검증 및 수정

    주의: 문자열 치환으로 한국어 문법을 고치려 하면 안 됨!
    - "의미를 설명해주세요" → "의미를 뭡니까" (X) 틀린 한국어
    - 잘못된 질문은 그냥 None 반환하여 제외시킴
    """
    result = question.strip()

    # =============================================
    # 1. 이중 문장부호 제거 (최우선!)
    # =============================================
    result = result.replace(".?", "?")
    result = result.replace("??", "?")
    result = result.replace("。?", "?")
    result = result.replace(" ?", "?")  # 공백+물음표 정리

    # =============================================
    # 2. 한국어 뉘앙스 교정 (덕분에+부정 → 때문에)
    # =============================================
    negative_words = ["손해", "실패", "못", "안 ", "없", "잃", "포기", "힘들", "어려"]
    if "덕분에" in result:
        for neg in negative_words:
            if neg in result:
                result = result.replace("덕분에", "때문에")
                break

    # =============================================
    # 3. 금지 패턴 검사 → None 반환 (치환 안 함!)
    # =============================================
    # 잘못된 질문은 고치지 않고 그냥 제외
    forbidden_patterns = [
        "설명해", "말씀해",           # 설명 요청형
        "어떻게",                      # 어떻게~
        "겠습니까", "하시겠",          # ~겠습니까
        "나요?", "어요?", "죠?",       # 비격식체
        "는지 뭡니까", "인지 뭡니까",  # 문법 오류 패턴
        "를 뭡니까", "을 뭡니까",      # 문법 오류 (가/이 뭡니까가 맞음)
    ]
    for forbidden in forbidden_patterns:
        if forbidden in result:
            return None  # 제외 대상

    # =============================================
    # 3-2. 막연한 지시어 검사 (무엇을 가리키는지 불분명)
    # =============================================
    # "이러한 이미지" → 무슨 이미지? / "이러한 능력" → 무슨 능력?
    vague_demonstratives = ["이러한 ", "그러한 ", "이런 ", "그런 ", "such "]
    for vague in vague_demonstratives:
        if vague in result:
            return None  # 제외 대상 (구체적 내용 없이 지시어만 사용)

    # =============================================
    # 4. 어미 정리 (물음표만 추가)
    # =============================================
    # 이미 "까?"로 끝나면 OK
    if result.endswith("까?"):
        return result

    # "까"로 끝나는데 "?"가 없으면 추가
    if result.endswith("까"):
        return result + "?"

    # "요?"로 끝나는 비격식체 → 제외
    if result.endswith("요?"):
        return None

    # 물음표로 끝나지 않으면 추가
    if not result.endswith("?"):
        result = result + "?"

    return result


def _generate_followup(attack_angle: str, target_text: str) -> str:
    """공격 각도에 맞는 꼬리질문 생성"""
    followups = {
        "손해": "그래도 그게 중요합니까?",
        "실패": "다시 해도 똑같이 합니까?",
        "반례": "그런 상황에서도요?",
        "숫자": "그게 성공입니까, 실패입니까?",
        "선택": "후회하지 않습니까?",
        "한계": "계속 안 되면요?",
    }
    return followups.get(attack_angle, "그래서요?")


# 기존 프롬프트 (호환성 유지)
CLOVA_FAST_ANALYSIS_PROMPT = CLOVA_4STAGE_ANALYSIS_PROMPT


# 기존 프롬프트 (호환성 유지)
ANSWER_ANALYSIS_PROMPT = COMBINED_ANALYSIS_PROMPT
VULNERABILITY_DETECTION_PROMPT = """(사용 안 함 - COMBINED_ANALYSIS_PROMPT로 통합됨)

## 중요
- target_sentence는 반드시 원문에 있는 문장만
- 원문에 없는 문장을 타겟으로 하지 말 것
"""


# ===========================================
# STEP 4: 질문 생성 프롬프트 (검증 규칙 내장)
# ===========================================

QUESTION_GENERATOR_PROMPT = """
당신은 베테랑 항공사 면접관입니다.
지원자가 "헉" 하고 당황할 만큼 날카로운 질문을 만드세요.

<question>
{question_text}
</question>

<answer>
{answer_text}
</answer>

<vulnerabilities>
{vulnerabilities}
</vulnerabilities>

<key_sentences>
{key_sentences}
</key_sentences>

## [!] 절대 금지 (위반 시 무효)

### 1. 할루시네이션 금지
- key_sentences에 있는 문장만 인용
- 없는 문장 인용하면 즉시 탈락

### 2. 약한 질문 금지 (매우 중요!)
다음 패턴은 절대 사용 금지:
- "어떻게 ~했습니까?"
- "어떤 ~을 했습니까?"
- "무슨 ~을 했습니까?"
- "~에 대해 말씀해 주세요"
- "~를 설명해 주세요"
- "어떻게 기여했습니까?"
- "어떻게 활용했습니까?"
- "어떻게 경험했습니까?"

이런 질문은 지원자가 자소서 내용만 반복하면 끝나기 때문에 가치가 없음!

## 날카로운 질문의 5가지 공격 패턴 (반드시 사용!)

1. **손해/실패 공격**: "~라고 하셨는데, ~ 때문에 손해 본 적은 없습니까?"
2. **반례 공격**: "~라고 하셨는데, [반대 상황]에서도 그렇게 합니까?"
3. **숫자 검증**: "~라고 하셨는데, 실제로 몇 번/몇 승/몇 명이었습니까?"
4. **선택 검증**: "~한 건 본인 선택입니까, [다른 사람] 결정입니까?"
5. **한계 탐색**: "~라고 하셨는데, 그게 안 통하는 사람은 어떻게 합니까?"

## 질문 유형

| 유형 | 공격 방식 | 예시 |
|------|----------|------|
| 역방향 | 주장의 반대 상황 | "팀워크 때문에 손해 본 적은?" |
| 검증 | 숫자/증거 요구 | "몇 승 몇 패였습니까?" |
| 선택검증 | 결정 주체 확인 | "본인 선택입니까, 부모님 결정입니까?" |
| 한계탐색 | 방법 실패 시 | "안 맞는 팀원은 어떻게?" |
| 딜레마 | 양자택일 강요 | "분위기와 성과 중 하나만 선택하면?" |

## 필수 예시 (이 수준으로 만들 것!)

[예시 1]
- 원문: "팀워크가 제일 중요하다고 생각합니다"
- 질문: "팀워크가 제일 중요하다고 하셨는데, 팀워크 때문에 본인이 손해 본 적은 없습니까?"
- 꼬리: "그래도 팀워크가 중요합니까?"

[예시 2]
- 원문: "같이 웃으면서 축구경기를 할 수 있는 환경을 조성하였습니다"
- 질문: "함께 웃는 환경을 조성했다고 하셨는데, 경기에서 계속 지는데도 웃을 수 있습니까? 몇 승 몇 패였습니까?"
- 꼬리: "그럼 '환경 조성'은 성공입니까, 실패입니까?"

[예시 3]
- 원문: "혼자였으면 절대 극복하지 못할 것들을 공동체 속에 함께 있으니 극복할 수 있었습니다"
- 질문: "혼자였으면 절대 극복 못 했다고 하셨는데, 그럼 본인은 혼자서는 뭘 못 하는 사람입니까?"
- 꼬리: "승무원은 혼자 판단해야 할 때도 있는데, 괜찮겠습니까?"

[예시 4]
- 원문: "16살이라는 나이에 중국 칭다오로 홀로 유학을 가게되었습니다"
- 질문: "16살에 홀로 유학 간 건 본인 선택입니까, 부모님 결정입니까?"
- 꼬리: "본인은 가기 싫었습니까?"

[예시 5]
- 원문: "각 팀마다 팀컬러가 다릅니다"
- 질문: "팀컬러가 다르다고 하셨는데, 본인이 만든 팀컬러에 안 맞는 팀원이 있으면 어떻게 합니까?"
- 꼬리: "대화해도 안 바뀌면요? 내보냅니까?"

[예시 6]
- 원문: "서로 부족한 부분을 채워주며"
- 질문: "서로 부족한 부분을 채워줬다고 하셨는데, 채워주지 못했던 상황은 없었습니까?"
- 꼬리: "그때 어떻게 하셨습니까?"

## 출력 형식 (JSON)

{{
  "questions": [
    {{
      "id": "Q1",
      "type": "역방향|검증|선택검증|한계탐색|딜레마",
      "quoted_sentence": "key_sentences에서 정확히 복사한 원문",
      "question": "날카로운 질문 (위 예시 수준으로)",
      "intent": "질문 의도",
      "follow_up": {{
        "trigger": "예상 답변",
        "question": "빠져나갈 수 없는 꼬리질문"
      }}
    }}
  ]
}}

## 생성 규칙
- 3개 질문 생성
- 각 질문은 서로 다른 소재 공격
- 모든 질문은 위 예시 수준의 날카로움 필수
- "어떻게 ~했습니까?" 패턴 사용 시 즉시 탈락
"""


# ===========================================
# STEP 5: 자체 검증 프롬프트
# ===========================================

SELF_VALIDATION_PROMPT = """
아래 생성된 질문이 품질 기준을 통과하는지 검증하세요.

<original_answer>
{answer_text}
</original_answer>

<generated_question>
{question}
</generated_question>

<quoted_sentence>
{quoted_sentence}
</quoted_sentence>

## 5단계 GATE 검증

### GATE 1: 할루시네이션 검증 (가장 중요!)
- quoted_sentence가 original_answer에 실제로 존재하는가?
- 정확히 일치하거나 의미상 동일한가?
- 단어 하나라도 다르면 FAIL

### GATE 2: 문맥 검증
- 단어의 문맥적 의미를 정확히 이해했는가?
- 답변의 서사 흐름을 이해하고 있는가?

### GATE 3: 논리 검증
- 질문의 전제가 타당한가?
- A → B 연결이 논리적인가?

### GATE 4: 윤리 검증
- 민감정보를 부적절하게 다루는가?
- 질문이 아니라 비난/판단이 되었는가?
- 지원자가 답변 가능한 질문인가?

### GATE 5: 품질 검증
- 직무(승무원)와 연결 가능한가?
- 예측 가능한 뻔한 질문인가?
- "~해 주실 수 있습니까?" 같은 공손체 사용했는가?

## 출력 형식 (JSON)

{{
  "gate_1_hallucination": {{
    "found_in_original": true/false,
    "similarity": "정확일치|유사|불일치",
    "pass": true/false
  }},
  "gate_2_context": {{
    "word_meaning_correct": true/false,
    "pass": true/false
  }},
  "gate_3_logic": {{
    "premise_valid": true/false,
    "inference_valid": true/false,
    "pass": true/false
  }},
  "gate_4_ethics": {{
    "answerable": true/false,
    "is_judgment_not_question": true/false,
    "pass": true/false
  }},
  "gate_5_quality": {{
    "sharpness_score": 1-100,
    "uses_polite_form": true/false,
    "pass": true/false
  }},
  "final_verdict": "PASS|FAIL",
  "fail_reason": "실패 이유 (있으면)"
}}
"""


# ===========================================
# STEP 6: 재생성 프롬프트 (검증 실패 시)
# ===========================================

REGENERATION_PROMPT = """
아래 질문이 검증에서 탈락했습니다.
같은 취약점을 공격하되, 훨씬 더 날카로운 질문을 만드세요.

<failed_question>
{failed_question}
</failed_question>

<failure_reason>
{failure_reason}
</failure_reason>

<original_answer>
{answer_text}
</original_answer>

<key_sentences>
{key_sentences}
</key_sentences>

<target_vulnerability>
{vulnerability}
</target_vulnerability>

## [!] 절대 금지 - 약한 질문 패턴
절대 사용하지 마세요:
- "어떻게 ~했습니까?"
- "어떤 ~을 했습니까?"
- "~에 대해 말씀해 주세요"
- "~를 설명해 주세요"

## 반드시 사용해야 할 날카로운 패턴
다음 중 하나를 반드시 사용:

1. "~라고 하셨는데, ~ 때문에 손해 본 적은 없습니까?"
2. "~라고 하셨는데, 몇 번/몇 승/몇 명이었습니까?"
3. "~한 건 본인 선택입니까, [다른 사람] 결정입니까?"
4. "~라고 하셨는데, 그게 안 통하는 사람은 어떻게 합니까?"
5. "~라고 하셨는데, [반대 상황]에서도 그렇게 합니까?"

## 필수 예시 (이 수준으로!)
- "팀워크 때문에 본인이 손해 본 적은 없습니까?"
- "몇 승 몇 패였습니까?"
- "본인 선택입니까, 부모님 결정입니까?"
- "그래도 안 바뀌는 팀원은 어떻게 합니까?"

## 출력 형식 (JSON)

{{
  "new_question": {{
    "type": "역방향|검증|선택검증|한계탐색|딜레마",
    "quoted_sentence": "인용한 원문 (key_sentences에서 정확히)",
    "question": "날카로운 질문 (위 예시 수준으로!)",
    "intent": "질문 의도",
    "follow_up": {{
      "trigger": "예상 답변",
      "question": "꼬리질문"
    }}
  }}
}}
"""


# ===========================================
# LLM 호출 함수 (CLOVA Studio 네이티브 API)
# ===========================================

def _call_llm(system: str, user: str, temperature: float = 0.3) -> Optional[Dict]:
    """HyperCLOVA X 네이티브 API 호출 및 JSON 파싱"""
    try:
        headers = {
            'Authorization': f'Bearer {CLOVA_API_KEY}',
            'X-NCP-CLOVASTUDIO-REQUEST-ID': CLOVA_REQUEST_ID,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json'  # 스트리밍 대신 일반 JSON
        }

        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "temperature": temperature,
            "maxTokens": 4000,
            "topP": 0.8,
            "topK": 0,
            "repeatPenalty": 1.2  # 반복 방지 (클로바 스튜디오 권장값)
        }

        endpoint = f"{CLOVA_HOST}/v3/chat-completions/{CLOVA_MODEL}"

        response = requests.post(endpoint, headers=headers, json=payload, timeout=90)

        if response.status_code != 200:
            print(f"[LLM ERROR] HTTP {response.status_code}: {response.text}")
            return None

        # 일반 JSON 응답 처리
        try:
            resp_json = response.json()
            if 'result' in resp_json and 'message' in resp_json['result']:
                full_content = resp_json['result']['message'].get('content', '')
            elif 'message' in resp_json:
                full_content = resp_json['message'].get('content', '')
            else:
                # 스트리밍 형식 폴백
                full_content = ""
                for line in response.text.split('\n'):
                    if line.startswith('data:'):
                        try:
                            data = json.loads(line[5:])
                            if 'message' in data and 'content' in data['message']:
                                full_content = data['message']['content']
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[LLM ERROR] 응답 파싱 실패: {e}")
            return None

        if not full_content:
            print("[LLM ERROR] 응답에서 content를 찾을 수 없음")
            return None

        # JSON 파싱 시도 (여러 방법)
        try:
            return json.loads(full_content)
        except json.JSONDecodeError as e:
            # 방법 1: JSON 코드블록 추출 (```json ... ```)
            json_block = re.search(r'```(?:json)?\s*([\s\S]*?)```', full_content)
            if json_block:
                try:
                    return json.loads(json_block.group(1).strip())
                except json.JSONDecodeError:
                    pass

            # 방법 2: 첫 번째 완전한 JSON 객체 추출
            brace_count = 0
            start_idx = -1
            for i, char in enumerate(full_content):
                if char == '{':
                    if brace_count == 0:
                        start_idx = i
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0 and start_idx >= 0:
                        try:
                            return json.loads(full_content[start_idx:i+1])
                        except json.JSONDecodeError:
                            break

            # 방법 3: 단순 regex
            json_match = re.search(r'\{[\s\S]*?\}(?=\s*$|\s*\n)', full_content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            print(f"[LLM ERROR] JSON 파싱 실패: {full_content[:300]}...")
            return None

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return None


# ===========================================
# 검증 함수들
# ===========================================

def validate_quote_exists(quote: str, original_text: str) -> Dict:
    """인용 문장이 원문에 존재하는지 검증 (코드 기반)"""

    if not quote or not original_text:
        return {"exists": False, "match_type": "none", "confidence": 0}

    # 정규화 (공백, 따옴표 정리)
    def normalize(text):
        text = text.strip()
        text = re.sub(r'[\'\"''""]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    quote_norm = normalize(quote)
    original_norm = normalize(original_text)

    # 1. 정확 일치
    if quote_norm in original_norm:
        return {"exists": True, "match_type": "exact", "confidence": 100}

    # 2. 부분 일치 (핵심 단어 기준)
    quote_words = set(quote_norm.split())
    original_words = set(original_norm.split())

    if not quote_words:
        return {"exists": False, "match_type": "none", "confidence": 0}

    overlap = quote_words.intersection(original_words)
    overlap_ratio = len(overlap) / len(quote_words)

    # 3. 연속 단어 매칭 (더 엄격한 검증)
    quote_words_list = quote_norm.split()
    if len(quote_words_list) >= 3:
        # 3단어 이상 연속 일치 확인
        for i in range(len(quote_words_list) - 2):
            three_words = ' '.join(quote_words_list[i:i+3])
            if three_words in original_norm:
                return {"exists": True, "match_type": "partial", "confidence": int(overlap_ratio * 100)}

    if overlap_ratio >= 0.85:
        return {"exists": True, "match_type": "partial", "confidence": int(overlap_ratio * 100)}

    return {"exists": False, "match_type": "none", "confidence": int(overlap_ratio * 100)}


def check_question_diversity(questions: List[Dict]) -> Dict:
    """질문 다양성 검증"""

    types = [q.get("type", "unknown") for q in questions]

    type_counts = {}
    for t in types:
        type_counts[t] = type_counts.get(t, 0) + 1

    issues = []

    # 유형 다양성 체크
    if len(set(types)) < 3:
        issues.append(f"질문 유형이 {len(set(types))}가지뿐입니다. 최소 3가지 필요.")

    return {
        "type_distribution": type_counts,
        "issues": issues,
        "passed": len(issues) == 0
    }


def calculate_sharpness(question_text: str, q_type: str) -> int:
    """질문 날카로움 점수 계산"""

    score = 50  # 기본 점수

    # 가점 요소 - 날카로운 키워드
    sharp_keywords = [
        ("손해", 15), ("실패", 15), ("졌", 10), ("못", 10),
        ("몇 ", 15), ("몇승", 15), ("몇번", 15),
        ("안 통", 10), ("안 맞", 10), ("안 바뀌", 10),
        ("내보", 10), ("포기", 10), ("그만", 10)
    ]
    for keyword, bonus in sharp_keywords:
        if keyword in question_text:
            score += bonus
            break  # 첫 매칭만

    # 날카로운 패턴
    if "없습니까" in question_text or "없었습니까" in question_text:
        score += 15

    if "본인 선택입니까" in question_text or "결정입니까" in question_text:
        score += 15

    if "~라고 하셨는데" in question_text or "하셨는데" in question_text:
        score += 5

    # 유형별 가점
    if q_type in ["딜레마", "선택검증"]:
        score += 15
    elif q_type in ["한계탐색", "검증", "역방향"]:
        score += 10

    if len(question_text) <= 50:  # 짧고 직접적
        score += 5

    # 감점 요소 (약한 질문 패턴)
    # "구체적으로 뭡니까?"는 좋은 질문이므로 "구체적으로"는 허용
    weak_patterns = [
        ("어떻게 ", 35),  # "어떻게 극복했습니까?" 등
        ("어떤 ", 35),    # "어떤 노력을 했습니까?" 등
        ("무슨 ", 30),
        ("무엇을 ", 30),
        ("해 주실 수 있습니까", 40),
        ("설명해 주세요", 40),
        ("말씀해 주세요", 40),
        ("해 주시겠습니까", 40),
        ("활용할 계획", 35),
        ("대응하시겠습니까", 30),
        ("대처하시겠습니까", 30),
    ]

    for pattern, penalty in weak_patterns:
        if pattern in question_text:
            score -= penalty
            break

    # "~했습니까?" 로 끝나는 질문은 가점
    if question_text.endswith("습니까?") or question_text.endswith("입니까?"):
        score += 5

    return min(100, max(0, score))


# ===========================================
# 다단계 파이프라인 클래스
# ===========================================

class InterviewQuestionPipeline:
    """5단계 GATE 검증이 통합된 면접 질문 생성 파이프라인"""

    def __init__(self, airline: str = ""):
        self.airline = airline
        self._cache = {}
        self.max_regeneration_attempts = 0  # 재생성 비활성화 (속도 최적화)

    def _get_cache_key(self, qa_pairs: List[Dict]) -> str:
        """캐시 키 생성"""
        content = json.dumps(qa_pairs, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    # -----------------------------------------
    # STEP 1: 자소서 파싱
    # -----------------------------------------
    def step1_parse_resume(self, qa_pairs: List[Dict]) -> List[Dict]:
        """자소서 파싱 (이미 파싱된 경우 그대로 반환)"""
        # qa_pairs가 이미 prompt/answer 형태면 변환
        parsed = []
        for i, item in enumerate(qa_pairs):
            parsed.append({
                "q_num": i + 1,
                "question_text": item.get("prompt", ""),
                "answer_text": item.get("answer", "")
            })
        return parsed

    # -----------------------------------------
    # STEP 2: 답변 분석 + 핵심 문장 추출
    # -----------------------------------------
    def step2_analyze_answer(self, question_text: str, answer_text: str) -> Dict:
        """답변 분석 및 핵심 문장 추출"""
        print("[STEP 2] 답변 분석 중...")

        system = "당신은 자소서 분석 전문가입니다. JSON 형식으로만 응답하세요."
        user = ANSWER_ANALYSIS_PROMPT.format(
            question_text=question_text,
            answer_text=answer_text
        )

        result = _call_llm(system, user, temperature=0.2)

        if not result:
            return {"key_sentences": [], "claims": [], "tone": {}}

        # 핵심 문장 검증 (할루시네이션 방지)
        validated_sentences = []
        for sent in result.get("key_sentences", []):
            sentence = sent.get("sentence", "")
            check = validate_quote_exists(sentence, answer_text)
            if check["exists"]:
                validated_sentences.append(sent)
            else:
                print(f"[STEP 2] 할루시네이션 제거: '{sentence[:30]}...' (신뢰도: {check['confidence']}%)")

        result["key_sentences"] = validated_sentences
        return result

    # -----------------------------------------
    # STEP 3: 취약점 탐지
    # -----------------------------------------
    def step3_detect_vulnerabilities(self, question_text: str, answer_text: str, key_sentences: List[Dict]) -> Dict:
        """취약점 탐지"""
        print("[STEP 3] 취약점 탐지 중...")

        system = "당신은 면접 질문 전문가입니다. JSON 형식으로만 응답하세요."
        user = VULNERABILITY_DETECTION_PROMPT.format(
            question_text=question_text,
            answer_text=answer_text,
            key_sentences=json.dumps(key_sentences, ensure_ascii=False)
        )

        result = _call_llm(system, user, temperature=0.3)

        if not result:
            return {"vulnerabilities": []}

        # 취약점 타겟 문장 검증
        validated_vulns = []
        for vuln in result.get("vulnerabilities", []):
            target = vuln.get("target_sentence", "")
            check = validate_quote_exists(target, answer_text)
            if check["exists"]:
                validated_vulns.append(vuln)
            else:
                print(f"[STEP 3] 할루시네이션 제거: '{target[:30]}...'")

        result["vulnerabilities"] = validated_vulns
        return result

    # -----------------------------------------
    # STEP 4: 질문 생성
    # -----------------------------------------
    def step4_generate_questions(self, question_text: str, answer_text: str,
                                  vulnerabilities: Dict, key_sentences: List[Dict]) -> List[Dict]:
        """질문 생성"""
        print("[STEP 4] 질문 생성 중...")

        system = "당신은 항공사 면접관입니다. JSON 형식으로만 응답하세요."
        user = QUESTION_GENERATOR_PROMPT.format(
            question_text=question_text,
            answer_text=answer_text,
            vulnerabilities=json.dumps(vulnerabilities, ensure_ascii=False),
            key_sentences=json.dumps(key_sentences, ensure_ascii=False)
        )

        result = _call_llm(system, user, temperature=0.7)

        if not result:
            return []

        # result가 list인 경우 직접 반환, dict면 questions 키에서 추출
        if isinstance(result, list):
            return result
        return result.get("questions", [])

    # -----------------------------------------
    # STEP 5: 코드 기반 빠른 검증 (LLM 호출 없음)
    # -----------------------------------------
    def step5_validate_question(self, question: Dict, answer_text: str) -> Dict:
        """코드 기반 빠른 검증 - LLM 호출 없이 즉시 검증"""

        quoted = question.get("quoted_sentence", "")
        q_text = question.get("question", "")
        q_type = question.get("type", "")

        # GATE 1: 할루시네이션 검증 (코드 기반) - HyperCLOVA X는 정확 복사가 어려워 기준 완화
        quote_check = validate_quote_exists(quoted, answer_text)
        # 신뢰도 25% 이상이면 통과 (클로바가 원문을 요약/변형하는 경향이 있음)
        gate1_pass = quote_check["exists"] or quote_check["confidence"] >= 25

        if not gate1_pass:
            return {
                "passed": False,
                "failed_gate": "GATE1_HALLUCINATION",
                "reason": f"인용 문장이 원문에 없음 (신뢰도: {quote_check['confidence']}%)",
                "quote_check": quote_check
            }

        # GATE 5: 품질 검증 (코드 기반)
        sharpness = calculate_sharpness(q_text, q_type)

        # 공손체 사용 체크
        polite_patterns = ["해 주실 수 있습니까", "해 주시겠습니까", "말씀해 주세요", "설명해 주세요"]
        uses_polite = any(p in q_text for p in polite_patterns)

        if uses_polite:
            return {
                "passed": False,
                "failed_gate": "GATE5_QUALITY",
                "reason": "공손체 사용 (날카로움 부족)",
                "sharpness": sharpness
            }

        if sharpness < 40:  # 기준 완화: 65 → 40
            return {
                "passed": False,
                "failed_gate": "GATE5_QUALITY",
                "reason": f"날카로움 점수 미달 ({sharpness}점)",
                "sharpness": sharpness
            }

        return {
            "passed": True,
            "sharpness": sharpness
        }

    # -----------------------------------------
    # STEP 6: 재생성 (검증 실패 시)
    # -----------------------------------------
    def step6_regenerate_question(self, failed_question: Dict, failure_reason: str,
                                   answer_text: str, key_sentences: List[Dict],
                                   vulnerability: Dict) -> Optional[Dict]:
        """검증 실패 시 질문 재생성"""
        print(f"[STEP 6] 재생성 시도: {failure_reason}")

        system = "당신은 항공사 면접관입니다. JSON 형식으로만 응답하세요."
        user = REGENERATION_PROMPT.format(
            failed_question=json.dumps(failed_question, ensure_ascii=False),
            failure_reason=failure_reason,
            answer_text=answer_text,
            key_sentences=json.dumps(key_sentences, ensure_ascii=False),
            vulnerability=json.dumps(vulnerability, ensure_ascii=False)
        )

        result = _call_llm(system, user, temperature=0.8)

        if result and "new_question" in result:
            return result["new_question"]
        return None

    # -----------------------------------------
    # STEP 2+3 통합: 분석 + 취약점 (API 1회)
    # -----------------------------------------
    def step2_combined_analysis(self, question_text: str, answer_text: str) -> Dict:
        """분석 + 취약점 탐지를 한 번에 (API 1회로 처리)"""
        print("[STEP 2] 분석 + 취약점 탐지 중...")

        system = "당신은 자소서 분석 전문가입니다. JSON 형식으로만 응답하세요."
        user = COMBINED_ANALYSIS_PROMPT.format(
            question_text=question_text,
            answer_text=answer_text
        )

        result = _call_llm(system, user, temperature=0.2)

        if not result:
            return {"key_sentences": [], "vulnerabilities": []}

        # 핵심 문장 검증 (할루시네이션 방지)
        validated_sentences = []
        for sent in result.get("key_sentences", []):
            sentence = sent.get("sentence", "")
            check = validate_quote_exists(sentence, answer_text)
            if check["exists"]:
                validated_sentences.append(sent)

        # 취약점 검증
        validated_vulns = []
        for vuln in result.get("vulnerabilities", []):
            target = vuln.get("target_sentence", "")
            check = validate_quote_exists(target, answer_text)
            if check["exists"]:
                validated_vulns.append(vuln)

        return {
            "key_sentences": validated_sentences,
            "vulnerabilities": validated_vulns
        }

    # -----------------------------------------
    # 통합: 분석 + 질문생성 (API 1회) - 속도 최적화
    # -----------------------------------------
    def step_unified_analysis_and_questions(self, question_text: str, answer_text: str) -> Dict:
        """분석 + 질문생성을 한 번에 (API 1회로 처리) - 속도 최적화"""
        print("[UNIFIED] 분석 + 질문 생성 중 (API 1회)...")

        system = """당신은 국내 항공사 압박 면접 전문가입니다.

## 절대 규칙
1. 자소서에 있는 문장만 인용
2. 모든 질문은 "~입니까?", "~없습니까?", "~뭡니까?"로 끝남

## 질문 예시 (이 형식 그대로!)
- "팀워크 때문에 본인이 손해 본 적은 없습니까?"
- "실제로 몇 승 몇 패였습니까?"
- "본인 선택입니까, 부모님 결정입니까?"
- "안 맞는 사람은요? 계속 안 맞으면요?"
- "반대로 본인이 기여한 건 구체적으로 뭡니까?"
- "그 환경에서 웃지 못한 팀원은 없었습니까?"

## 금지 (사용시 탈락!)
- "설명해주세요" ❌
- "말씀해 주세요" ❌
- "~해 주실 수 있습니까?" ❌
- "~하실 것인지" ❌

JSON 형식으로만 응답하세요."""

        user = UNIFIED_ANALYSIS_AND_QUESTION_PROMPT.format(
            question_text=question_text,
            answer_text=answer_text
        )

        result = _call_llm(system, user, temperature=0.7)

        if not result:
            return {"key_sentences": [], "questions": []}

        # 핵심 문장 검증 (할루시네이션 방지)
        validated_sentences = []
        for sent in result.get("key_sentences", []):
            # sent가 문자열인 경우와 딕셔너리인 경우 모두 처리
            if isinstance(sent, str):
                sentence = sent
                sent_obj = {"sentence": sent, "attack_angle": ""}
            else:
                sentence = sent.get("sentence", "")
                sent_obj = sent

            check = validate_quote_exists(sentence, answer_text)
            if check["exists"]:
                validated_sentences.append(sent_obj)

        return {
            "key_sentences": validated_sentences,
            "questions": result.get("questions", [])
        }

    # -----------------------------------------
    # 단일 문항 처리
    # -----------------------------------------
    def process_single_item(self, q_num: int, question_text: str, answer_text: str) -> Dict:
        """단일 문항 처리 - 속도 최적화 버전 (API 1회: 분석+질문생성 통합)"""

        print(f"\n{'='*50}")
        print(f"문항 {q_num} 처리 시작")
        print(f"{'='*50}")

        start_time = time.time()

        # 통합 API 호출: 분석 + 질문생성 (API 1회)
        unified_result = self.step_unified_analysis_and_questions(question_text, answer_text)
        key_sentences = unified_result.get("key_sentences", [])
        raw_questions = unified_result.get("questions", [])
        print(f"[UNIFIED] 핵심 문장 {len(key_sentences)}개 + 질문 {len(raw_questions)}개 생성 ({time.time() - start_time:.1f}s)")

        if not raw_questions:
            print("[WARNING] 질문을 생성하지 못했습니다.")
            return {"q_num": q_num, "questions": [], "error": "질문 생성 실패"}

        # 호환성을 위한 변수 설정
        vuln_list = []
        vulnerabilities = {"vulnerabilities": vuln_list}

        # STEP 5-6: 검증 및 재생성
        validated_questions = []
        rejected_questions = []

        for q in raw_questions:
            validation = self.step5_validate_question(q, answer_text)

            if validation["passed"]:
                q["validation"] = validation
                validated_questions.append(q)
                print(f"[STEP 5] [PASS] Q{q.get('id', '?')} 통과 (날카로움: {validation.get('sharpness', 'N/A')}점)")
            else:
                # 재생성 시도
                regenerated = False
                for attempt in range(self.max_regeneration_attempts):
                    # 해당 취약점 찾기
                    target_vuln = {}
                    quoted = q.get("quoted_sentence", "")
                    for v in vuln_list:
                        if v.get("target_sentence", "") == quoted:
                            target_vuln = v
                            break

                    new_q = self.step6_regenerate_question(
                        q, validation.get("reason", ""),
                        answer_text, key_sentences, target_vuln
                    )

                    if new_q:
                        new_validation = self.step5_validate_question(new_q, answer_text)
                        if new_validation["passed"]:
                            new_q["validation"] = new_validation
                            new_q["id"] = q.get("id", "Q?")
                            validated_questions.append(new_q)
                            print(f"[STEP 6] [PASS] Q{q.get('id', '?')} 재생성 성공 (시도 {attempt+1})")
                            regenerated = True
                            break

                if not regenerated:
                    rejected_questions.append({
                        "question": q,
                        "validation": validation
                    })
                    print(f"[STEP 5] [X] Q{q.get('id', '?')} 탈락: {validation.get('reason', 'Unknown')}")

        print(f"\n[완료] 문항 {q_num}: 통과 {len(validated_questions)}개, 탈락 {len(rejected_questions)}개 ({time.time() - start_time:.1f}s)")

        return {
            "q_num": q_num,
            "question_text": question_text,
            "analysis": unified_result,
            "vulnerabilities": vulnerabilities,
            "validated_questions": validated_questions,
            "rejected_questions": rejected_questions
        }

    # -----------------------------------------
    # 전체 처리
    # -----------------------------------------
    def process(self, qa_pairs: List[Dict]) -> Dict:
        """전체 자소서 처리"""

        cache_key = self._get_cache_key(qa_pairs)
        if cache_key in self._cache:
            print("[CACHE HIT] 캐시된 결과 반환")
            return self._cache[cache_key]

        print("\n" + "=" * 60)
        print("면접 질문 생성 파이프라인 v2.0 시작")
        print("=" * 60)

        start_time = time.time()

        # STEP 1: 파싱
        parsed = self.step1_parse_resume(qa_pairs)
        print(f"[STEP 1] 문항 {len(parsed)}개 파싱 완료")

        # 각 문항 처리
        all_results = []
        all_questions = []

        for item in parsed:
            result = self.process_single_item(
                item["q_num"],
                item["question_text"],
                item["answer_text"]
            )
            all_results.append(result)
            all_questions.extend(result.get("validated_questions", []))

        # 다양성 검증
        diversity = check_question_diversity(all_questions)

        # 최종 결과
        final_result = {
            "items": all_results,
            "all_deep_questions": all_questions,
            "diversity_check": diversity,
            "summary": {
                "total_items": len(parsed),
                "total_validated": len(all_questions),
                "total_rejected": sum(len(r.get("rejected_questions", [])) for r in all_results),
                "processing_time": time.time() - start_time
            }
        }

        # 캐시 저장
        self._cache[cache_key] = final_result

        print("\n" + "=" * 60)
        print(f"파이프라인 완료! 총 {time.time() - start_time:.1f}초")
        print(f"검증 통과: {len(all_questions)}개")
        print("=" * 60)

        return final_result

    def get_questions_for_version(self, result: Dict, version: int) -> List[Dict]:
        """버전별 질문 선택"""
        all_questions = result.get("all_deep_questions", [])

        if not all_questions:
            return []

        # 버전에 따라 다른 질문 조합
        selected = []
        for i in range(3):
            idx = (version - 1 + i * 3) % len(all_questions)
            if idx < len(all_questions):
                selected.append(all_questions[idx])

        return selected


# ===========================================
# 편의 함수
# ===========================================

_pipeline_instance = None

def get_pipeline(airline: str = "") -> InterviewQuestionPipeline:
    """싱글톤 파이프라인 인스턴스"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = InterviewQuestionPipeline(airline)
    return _pipeline_instance


def analyze_resume(qa_pairs: List[Dict], airline: str = "") -> Dict:
    """자소서 분석 메인 함수"""
    pipeline = get_pipeline(airline)
    return pipeline.process(qa_pairs)


def get_sharp_questions(result: Dict, version: int = 1) -> List[Dict]:
    """버전별 질문 가져오기"""
    pipeline = get_pipeline()
    return pipeline.get_questions_for_version(result, version)


# ===========================================
# 클로바 최적화: 2단계 파이프라인 (분석 → 패턴 매핑)
# ===========================================

def analyze_resume_fast(qa_pairs: List[Dict], airline: str = "") -> Dict:
    """
    CLOVA 직접 질문 생성 + 로컬 형식 검증

    CLOVA가 문맥을 이해하고 적절한 질문을 직접 생성
    로컬은 형식만 검증/수정 (어미, 금지 패턴)
    """
    if not qa_pairs:
        return {"items": [], "all_deep_questions": [], "summary": {"processing_time": 0}}

    start_time = time.time()
    print("\n" + "=" * 60)
    print("CLOVA 직접 질문 생성 파이프라인")
    print("=" * 60)

    # 전체 자소서 텍스트 구성
    full_resume_parts = []
    full_answers = {}
    for i, qa in enumerate(qa_pairs, 1):
        prompt = qa.get("prompt", "")
        answer = qa.get("answer", "")
        full_resume_parts.append(f"[문항 {i}]\n질문: {prompt}\n답변: {answer}")
        full_answers[i] = answer

    full_resume = "\n\n".join(full_resume_parts)

    # =============================================
    # CLOVA: 분석 + 질문 직접 생성
    # =============================================
    print(f"\n[CLOVA] 자소서 분석 + 질문 생성 중... ({len(qa_pairs)}개 문항)")

    system = """당신은 국내 항공사 객실승무원 채용 면접관입니다.
자소서의 '검증 가능한 핵심 문장'을 찾아 날카로운 질문을 생성합니다.

## 취약점 유형별 질문 공식 (FLYREADY)

| 취약점 | 질문 공식 |
|--------|----------|
| 구체성_부족 | "[추상적 표현]의 구체적인 숫자/기간은 얼마입니까?" |
| 인과관계_불명확 | "[결과]에서 본인이 직접 기여한 부분은 뭡니까?" |
| 역할_모호 | "[활동]에서 본인이 맡은 구체적인 역할은 뭡니까?" |
| 가치선언 | "[가치] 때문에 손해 본 적은 없습니까?" |
| 선택결정 | "[선택]은 본인 의지입니까, 다른 사람 결정입니까?" |
| 성과주장 | "[성과]가 성공이라는 구체적 근거가 있습니까?" |
| 방법태도 | "[방법]이 안 통하면 어떻게 합니까?" |

## 질문 레벨 (다양하게 섞어서!)
- Level 1 사실확인: "정확히 언제, 어디서 있었던 일입니까?"
- Level 2 깊이검증: "가장 어려웠던 순간은 구체적으로 언제였습니까?"
- Level 3 연결적용: "그 경험이 기내 상황에서 어떻게 적용됩니까?"

## 어미 규칙
- 필수: ~입니까? ~없습니까? ~뭡니까? ~했습니까? ~않았습니까?
- 금지: ~나요? ~어요? 설명해주세요

## 한국어 뉘앙스
- "때문에" + 손해/실패 ✅
- "덕분에" + 손해/실패 ❌

## 좋은 예시 (각각 다른 유형!)
1. "팀워크가 중요하다고 하셨는데, 팀워크 때문에 손해 본 적은 없습니까?" [가치선언]
2. "유학 간 건 본인 선택입니까, 부모님 결정입니까?" [선택결정]
3. "공동체 덕분이라고 하셨는데, 본인이 기여한 건 뭡니까?" [인과관계]
4. "환경을 조성했다고 하셨는데, 구체적인 결과가 어땠습니까?" [성과주장]
5. "대화로 해결했다고 하셨는데, 대화해도 안 되면요?" [방법태도]
6. "'많은 고객'이라고 하셨는데, 구체적으로 몇 명입니까?" [구체성부족]
7. "'저희 팀'이라고 하셨는데, 본인이 한 일은 뭡니까?" [역할모호]
8. "부장이라고 하셨는데, 구체적인 책임 범위는 어디까지였습니까?" [역할모호]

## 중요: 최소 6개 이상, 다양한 유형으로 생성!

JSON 형식으로 응답하세요."""

    user = f"""다음 자기소개서를 분석하고, 각 문항별로 날카로운 압박 면접 질문 **6-10개**를 생성하세요.

{full_resume}

## 필수 요구사항
1. **다양한 취약점 유형** 사용 (구체성부족, 인과관계, 역할모호, 가치선언, 선택결정, 성과주장, 방법태도)
2. **다양한 질문 레벨** 사용 (사실확인, 깊이검증, 연결적용)
3. **각각 다른 문장** 인용 (같은 문장 반복 금지)
4. **6개 이상** 질문 생성

## 출력 형식
```json
{{
  "items": [
    {{
      "item_num": 1,
      "questions": [
        {{
          "quoted_text": "자소서 원문 인용 (20자 이내)",
          "question": "날카로운 질문 (~입니까? 어미)",
          "attack_type": "구체성부족/인과관계/역할모호/가치선언/선택결정/성과주장/방법태도",
          "level": "사실확인/깊이검증/연결적용",
          "followup": "꼬리질문"
        }}
      ]
    }}
  ]
}}
```

**중요: 최소 6개, 최대한 다양하게!**
"""

    clova_result = _call_llm(system, user, temperature=0.5)

    if not clova_result or not clova_result.get("items"):
        print("[CLOVA] API 호출 실패, 폴백 모드")
        # 스마트 폴백: 키워드 기반 질문 생성
        clova_result = _smart_fallback_questions(qa_pairs, full_answers)

    clova_time = time.time() - start_time
    print(f"[CLOVA] 완료 ({clova_time:.1f}초)")

    # =============================================
    # 로컬: 형식 검증 및 수정
    # =============================================
    print(f"\n[검증] 질문 형식 검증 중...")

    items = clova_result.get("items", [])
    all_questions = []

    for item in items:
        item_num = item.get("item_num", 1)
        raw_questions = item.get("questions", [])
        answer_text = full_answers.get(item_num, "")

        for q in raw_questions:
            question_text = q.get("question", "")
            if not question_text or len(question_text) < 10:
                continue

            # 형식 검증 및 수정 (금지 패턴이면 None 반환)
            fixed_question = _validate_and_fix_question_format(question_text)

            # None이면 금지 패턴이므로 제외
            if fixed_question is None:
                print(f"    [제외] 금지 패턴/문법 오류: '{question_text[:40]}...'")
                continue

            # =============================================
            # 품질 검증: 인용 없는 막연한 질문 필터링
            # =============================================
            quoted = q.get("quoted_text", "")

            # 1. 인용이 없거나 너무 짧으면 제외
            if not quoted or len(quoted) < 5:
                print(f"    [제외] 인용 없음: '{fixed_question[:40]}...'")
                continue

            # 2. "그 결정", "그 경험" 같은 막연한 표현 필터링
            vague_patterns = ["그 결정", "그 경험", "그 상황", "그것", "이것", "해당"]
            is_vague = any(vp in fixed_question for vp in vague_patterns) and quoted not in fixed_question
            if is_vague:
                print(f"    [제외] 막연한 질문: '{fixed_question[:40]}...'")
                continue

            # 3. 인용 원문 존재 검증
            check = validate_quote_exists(quoted, answer_text)
            if not check["exists"] and check["confidence"] < 30:
                print(f"    [제외] 인용 원문 없음: '{quoted[:30]}...'")
                continue

            all_questions.append({
                "id": f"Q{item_num}_{len(all_questions) + 1}",
                "item_num": item_num,
                "type": q.get("attack_type", "압박"),
                "quoted_sentence": quoted,
                "question": fixed_question,
                "intent": f"{q.get('attack_type', '압박')} 공격",
                "follow_up": {
                    "trigger": "변명/회피 시",
                    "question": q.get("followup", "그래서요?")
                },
                "source": "clova_direct"
            })

    # =============================================
    # 중복 제거
    # =============================================
    seen_questions = set()
    unique_questions = []
    for q in all_questions:
        # 질문 텍스트 정규화 (공백, 문장부호 제거 후 비교)
        q_text = q.get("question", "")
        q_normalized = ''.join(q_text.split()).replace("?", "").replace(".", "")

        if q_normalized not in seen_questions:
            seen_questions.add(q_normalized)
            unique_questions.append(q)
        else:
            print(f"    [중복 제거] '{q_text[:40]}...'")

    all_questions = unique_questions

    total_time = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"파이프라인 완료!")
    print(f"  - 총 시간: {total_time:.1f}초")
    print(f"  - 생성된 질문: {len(all_questions)}개")
    print(f"{'=' * 60}")

    return {
        "items": items,
        "all_deep_questions": all_questions,
        "summary": {
            "total_items": len(qa_pairs),
            "total_validated": len(all_questions),
            "processing_time": total_time,
            "method": "clova_direct"
        }
    }


def _smart_fallback_questions(qa_pairs: List[Dict], full_answers: Dict) -> Dict:
    """
    CLOVA 실패 시 FLYREADY 형식 질문 생성
    핵심: 자소서 원문을 직접 인용하여 질문에 포함
    """
    items = []

    # =============================================
    # FLYREADY 스타일 질문 템플릿
    # {keyword}: 찾은 키워드
    # {context}: 키워드 포함 문장 (인용)
    # =============================================
    FLYREADY_TEMPLATES = {
        # 가치/신념 → 손해 공격
        "팀워크": [
            "팀워크가 중요하다고 하셨는데, 팀워크 때문에 손해 본 적은 없습니까?",
            "팀워크를 강조하셨는데, 팀워크가 오히려 방해가 된 적은 없습니까?",
        ],
        "중요": [
            "'{context}'라고 하셨는데, 그 때문에 손해 본 적은 없습니까?",
            "'{context}'가 오히려 문제가 된 적은 없습니까?",
        ],
        "생각합니다": [
            "'{context}'라고 하셨는데, 그 생각이 틀렸던 적은 없습니까?",
        ],

        # 공동체 → 기여 검증
        "덕분": [
            "'{context}'라고 하셨는데, 반대로 본인이 기여한 건 구체적으로 뭡니까?",
            "'{context}'라고 하셨는데, 본인 혼자서는 뭘 못 합니까?",
        ],
        "함께": [
            "'{context}'라고 하셨는데, 본인 혼자 한 일은 구체적으로 뭡니까?",
        ],
        "공동체": [
            "공동체 덕분이라고 하셨는데, 본인이 없어도 됐겠습니까?",
        ],

        # 선택/결정 → 주체 검증
        "유학": [
            "유학 간 건 본인 선택입니까, 부모님 결정입니까?",
            "유학을 후회한 적은 없습니까?",
            "유학을 가기 싫었던 적은 없습니까?",
        ],
        "결정": [
            "'{context}'라고 하셨는데, 그 결정이 본인 의지입니까?",
            "'{context}'를 후회한 적은 없습니까?",
        ],
        "도전": [
            "'{context}'라고 하셨는데, 포기하고 싶었던 적은 없습니까?",
        ],

        # 성과 → 결과 검증
        "환경": [
            "환경을 조성했다고 하셨는데, 구체적인 결과는 어땠습니까?",
            "환경 조성이 실패한 경우는 없었습니까?",
        ],
        "성공": [
            "'{context}'라고 하셨는데, 실패한 경우는 없었습니까?",
        ],
        "극복": [
            "'{context}'라고 하셨는데, 극복 못한 건 없습니까?",
            "극복하지 못했으면 어떻게 됐을까요?",
        ],

        # 방법 → 한계 탐색
        "소통": [
            "소통으로 해결했다고 하셨는데, 소통해도 안 되면 어떻게 합니까?",
        ],
        "노력": [
            "'{context}'라고 하셨는데, 노력해도 안 되면요?",
        ],

        # 구체성 부족
        "많은": [
            "'{context}'라고 하셨는데, '많은'이 구체적으로 몇 번입니까?",
        ],
        "다양한": [
            "'{context}'라고 하셨는데, '다양한'이 구체적으로 몇 가지입니까?",
        ],

        # 주장/깨달음
        "배웠습니다": [
            "'{context}'라고 하셨는데, 그걸 실제로 적용한 경험이 있습니까?",
        ],
        "깨달았": [
            "'{context}'라고 하셨는데, 그 깨달음 전에는 어땠습니까?",
        ],

        # 향수병/어려움
        "향수병": [
            "향수병을 극복했다고 하셨는데, 극복 못한 순간은 없었습니까?",
        ],
        "어려움": [
            "'{context}'라고 하셨는데, 가장 힘들었던 순간은 구체적으로 언제였습니까?",
        ],
        "힘들": [
            "'{context}'라고 하셨는데, 포기하고 싶었던 순간은 없었습니까?",
        ],
    }

    # 꼬리질문 패턴
    FOLLOWUPS = {
        "손해": "그래도 중요합니까?",
        "선택": "후회하지 않습니까?",
        "기여": "본인 없어도 됐겠습니까?",
        "결과": "성공입니까, 실패입니까?",
        "한계": "계속 안 되면요?",
        "default": "그래서요?",
    }

    for i, qa in enumerate(qa_pairs, 1):
        answer = qa.get("answer", "")

        # 문장 분리
        sentences = []
        for s in answer.replace(".", ".\n").replace("?", "?\n").replace("!", "!\n").split("\n"):
            s = s.strip()
            if len(s) > 10:
                sentences.append(s)

        questions = []
        used_keywords = set()

        for sent in sentences:
            for keyword, templates in FLYREADY_TEMPLATES.items():
                if keyword in sent and keyword not in used_keywords:
                    # 인용 추출: 키워드 포함 구간
                    idx = sent.find(keyword)
                    start = max(0, idx - 10)
                    end = min(len(sent), idx + len(keyword) + 25)
                    context = sent[start:end].strip()

                    # 템플릿 선택
                    template = templates[len(questions) % len(templates)]

                    # 질문 생성
                    if "{context}" in template:
                        question = template.format(context=context)
                    else:
                        question = template

                    # 꼬리질문 선택
                    followup = FOLLOWUPS.get("default")
                    for key, fu in FOLLOWUPS.items():
                        if key in template:
                            followup = fu
                            break

                    questions.append({
                        "quoted_text": context,
                        "question": question,
                        "attack_type": keyword,
                        "followup": followup
                    })
                    used_keywords.add(keyword)

                    if len(questions) >= 10:
                        break

            if len(questions) >= 10:
                break

        items.append({
            "item_num": i,
            "questions": questions
        })

    return {"items": items}


# ===========================================
# 테스트
# ===========================================

if __name__ == "__main__":

    test_qa = [
        {
            "prompt": "동료 승무원들이 함께 근무하고 싶어하는 승무원이 되기 위해, 본인이 중요하게 생각하는 것은 무엇이며, 이를 위해 어떤 노력을 하고 있나요?",
            "answer": """전반적인 인생에 걸쳐 사람들과 같이 더불어 살 수 밖에 없습니다. 그렇기에 팀워크가 제일 중요하다고 생각합니다. 저는 16살이라는 나이에 중국 칭다오로 홀로 유학을 가게되었습니다. 타국에 홀로 떨어져서 기숙사 생활을 하니 말이 통하지 않는 무서움, 의지할 사람 없이 혼자 헤쳐나가야 한다는 부담감을 처음 느껴봤습니다. 하지만 기숙사에는 저와 같이 가족들과 떨어져서 홀로 유학을 온 사람들이 있었고 이 몇몇 사람들과 저는 함께 중국어 공부를 통해서 중국 생활에 적응하려고 노력했고, 중국어 공부를 비롯해 학교에서 배우는 경제학 수업이나 ACT 수업 등등 서로 부족한 부분을 채워주며 학교 생활도 같이 적응하려고 노력했습니다. 그렇기에 서로 더 의지하며 타지 생활의 외로움을 달랬습니다. 저는 실제로 홀로 중국에 유학을 갔을 때 향수병이 무엇인지 느껴봤고, 극복해본 결과 혼자였으면 절대 극복하지 못할 것들을 공동체 속에 함께 있으니 극복할 수 있었던 경험이 있습니다. 저의 이러한 경험들이 저에게 하여금 사람들과 공동체 속에서 어울릴 때의 가치와 공동체 의식의 중요성 그리고 더불어 살아가는 것이 무엇인지를 깨닫게 해주었습니다. 그래서 저는 많은 운동중에서도 축구라는 스포츠를 제일 선호합니다. 축구라는 스포츠는 11명이서 합을 맞추어 진행되는 스포츠입니다. 11명 중 한명만 정말 특출나게 잘한다고 하더라도 모든 경기에서 승리할 수는 없습니다, 그렇기에 축구에는 팀컬러 라는것이 존재하며 각 팀마다 팀컬러가 다릅니다. 저는 현재 세명대학교 항공서비스학과 축구 동아리 나르샤의 주장으로써 정말 잘하는 강팀을 만든다기 보다는 정말 축구를 잘 하지는 못하지만 좋아하는 인원도 같이 웃으면서 축구경기를 할 수 있는 환경을 조성하였습니다."""
        }
    ]

    result = analyze_resume(test_qa, "에어로케이")

    # UTF-8 파일로 결과 저장
    output_lines = []
    output_lines.append("=" * 60)
    output_lines.append("면접 질문 생성 파이프라인 v2.0 테스트 결과")
    output_lines.append("=" * 60)
    output_lines.append("")
    output_lines.append(f"총 검증 통과: {len(result.get('all_deep_questions', []))}개")
    output_lines.append(f"총 탈락: {result.get('summary', {}).get('total_rejected', 0)}개")
    output_lines.append(f"처리 시간: {result.get('summary', {}).get('processing_time', 0):.1f}초")
    output_lines.append("")

    for i, q in enumerate(result.get("all_deep_questions", []), 1):
        output_lines.append(f"[통과 질문 {i}]")
        output_lines.append(f"  유형: {q.get('type', 'N/A')}")
        output_lines.append(f"  인용: {q.get('quoted_sentence', 'N/A')}")
        output_lines.append(f"  질문: {q.get('question', 'N/A')}")
        output_lines.append(f"  의도: {q.get('intent', 'N/A')}")
        output_lines.append(f"  날카로움: {q.get('validation', {}).get('sharpness', 'N/A')}점")

        follow_up = q.get("follow_up", {})
        if follow_up:
            output_lines.append(f"  꼬리질문:")
            output_lines.append(f"    - 트리거: {follow_up.get('trigger', 'N/A')}")
            output_lines.append(f"    - 질문: {follow_up.get('question', 'N/A')}")
        output_lines.append("")

    # 탈락 질문도 출력
    output_lines.append("=" * 60)
    output_lines.append("[탈락 질문 목록]")
    output_lines.append("=" * 60)
    for item in result.get("items", []):
        for rj in item.get("rejected_questions", []):
            q = rj.get("question", {})
            val = rj.get("validation", {})
            output_lines.append(f"  유형: {q.get('type', 'N/A')}")
            output_lines.append(f"  질문: {q.get('question', 'N/A')}")
            output_lines.append(f"  탈락이유: {val.get('reason', 'N/A')}")
            output_lines.append("")

    # 파일 저장
    output_path = os.path.join(os.path.dirname(__file__), "test_result.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"\n결과가 저장됨: {output_path}")
