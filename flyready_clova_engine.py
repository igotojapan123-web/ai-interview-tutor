# flyready_clova_engine.py
# FLYREADY CLOVA 엔진 v4.1 (디버그 + 검증 강화)
# 취약점 기반 강/약 판단 + 질문 버전 자동 분배
# 1회 호출로 분석 + 6버전 질문 모두 생성
# v4.1: 디버그 로깅 + 질문 검증 + Few-shot 예시 추가

import os
import re
import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from logging_config import get_logger

logger = get_logger(__name__)

# ===========================================
# v4.1 디버그 설정
# ===========================================
DEBUG_MODE = False  # 운영 환경에서는 False로 설정
DEBUG_LOG_PATH = os.path.join(os.path.dirname(__file__), "clova_debug_logs")


def log_clova_response(raw_response: str, question: str, answer: str):
    """CLOVA 응답을 디버그 로그로 저장"""
    if not DEBUG_MODE:
        return

    try:
        os.makedirs(DEBUG_LOG_PATH, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(DEBUG_LOG_PATH, f"clova_{timestamp}.txt")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"TIMESTAMP: {timestamp}\n")
            f.write("=" * 60 + "\n\n")
            f.write("### 입력 문항 ###\n")
            f.write(question[:500] + "\n\n")
            f.write("### 입력 답변 ###\n")
            f.write(answer[:1000] + "\n\n")
            f.write("### CLOVA 응답 ###\n")
            f.write(raw_response if raw_response else "(응답 없음)")

        logger.debug(f"[DEBUG] CLOVA 응답 저장: {filename}")
    except Exception as e:
        logger.debug(f"[DEBUG] 로그 저장 실패: {e}")


def convert_question_ending(question: str) -> str:
    """
    CLOVA가 생성한 질문의 종결어미를 면접관 스타일로 변환
    ~나요? → ~예요? / ~뭐예요?
    """
    # 종결어미 변환 규칙
    conversions = [
        # ~했나요? → ~했어요?
        ("했나요?", "했어요?"),
        ("였나요?", "였어요?"),
        ("었나요?", "었어요?"),
        # ~하나요? → ~해요?
        ("하나요?", "해요?"),
        ("인가요?", "예요?"),
        # ~ㄴ가요? → ~예요?
        ("은가요?", "예요?"),
        ("는가요?", "예요?"),
        # ~나요? (일반) → ~예요?
        ("나요?", "예요?"),
        ("가요?", "예요?"),
        # ~하시나요? → ~하셨어요?
        ("하시나요?", "하셨어요?"),
        ("으시나요?", "으셨어요?"),
        ("셨나요?", "셨어요?"),
        # ~주세요 → 제거하고 질문형으로
        ("해 주세요.", "해주실 수 있어요?"),
        ("말해 주세요.", "말해줄 수 있어요?"),
        ("설명해 주세요.", "설명해줄 수 있어요?"),
        ("주세요.", "줄 수 있어요?"),
    ]

    result = question
    for old, new in conversions:
        if result.endswith(old):
            result = result[:-len(old)] + new
            break

    return result


def validate_question_against_resume(question: str, answer: str) -> tuple:
    """
    질문이 자소서 내용을 기반으로 하는지 검증

    Returns:
        (is_valid: bool, reason: str)
    """
    # 1. 자소서에 없는 단어가 질문에 있으면 의심 (영화/다큐멘터리는 문항에서 요구할 수 있으므로 제외)
    SUSPICIOUS_WORDS = [
        "소설", "책 제목", "노래", "음악", "게임",
        # "영화", "다큐멘터리" 제거 - 문항에서 요구할 수 있음
    ]

    for word in SUSPICIOUS_WORDS:
        if word in question and word not in answer:
            return False, f"의심 단어 '{word}' - 자소서에 없음"

    # 2. 질문이 너무 추상적이면 의심 (자소서 키워드 없음)
    import re
    answer_nouns = set(re.findall(r'[가-힣]{2,5}', answer))
    question_nouns = set(re.findall(r'[가-힣]{2,5}', question))
    overlap = answer_nouns & question_nouns

    COMMON_WORDS = {
        "무엇", "어떻게", "왜", "무엇인가요", "어떤", "그것",
        "본인", "생각", "경험", "상황", "질문", "답변",
        "있어요", "했어요", "거예요", "것인가요", "뭐예요",
        "하나요", "인가요", "나요", "가요"
    }
    meaningful_overlap = overlap - COMMON_WORDS

    # 자소서 키워드 체크는 너무 엄격하지 않게 (최소 0개 허용)
    # 대신 의심 단어 체크에 의존
    # if len(meaningful_overlap) == 0:
    #     return False, f"자소서 키워드 없음"

    # 3. 비정상 종결어미 체크 제거 - convert_question_ending에서 처리함
    # BAD_ENDINGS는 더 이상 사용하지 않음

    return True, "OK"


def extract_key_topics_from_answer(answer: str) -> list:
    """자소서에서 핵심 토픽(경험/활동) 추출"""
    # 경험/활동 관련 키워드
    TOPIC_MARKERS = [
        "경험", "활동", "프로젝트", "동아리", "인턴", "아르바이트",
        "봉사", "공모전", "대회", "여행", "유학", "교환학생",
        "팀", "리더", "주장", "회장", "부장"
    ]

    topics = []
    for marker in TOPIC_MARKERS:
        if marker in answer:
            # marker 주변 텍스트 추출
            idx = answer.find(marker)
            start = max(0, idx - 20)
            end = min(len(answer), idx + 30)
            context = answer[start:end]
            topics.append(context.strip())

    return topics[:5]  # 최대 5개

# 환경 변수
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "nv-f59b211212244304b064c131640a92a0UgPZ")
CLOVA_REQUEST_ID = os.getenv("CLOVA_REQUEST_ID", "331785bac0c64228ac15f5616d9082d7")

# CLOVA API 설정
CLOVA_HOST = "https://clovastudio.stream.ntruss.com"
CLOVA_MODEL = "HCX-005"

# ===========================================
# v4.0 SYSTEM PROMPT (한 글자도 수정하지 않음)
# ===========================================
SYSTEM_PROMPT_V4 = """당신은 대한민국 항공사 채용 면접관입니다.
10년 경력의 베테랑으로, 수천 개의 자소서를 읽어봤습니다.
당신의 임무는 자소서를 읽고 "면접에서 반드시 물어봐야 할 부분"을 찾고,
자소서의 강/약을 판단하여 질문 전략을 수립하는 것입니다.

═══════════════════════════════════════════════════════════════
                     STEP 1: 문항 해체
═══════════════════════════════════════════════════════════════

문항을 읽고 다음을 추출하세요:

## 1-1. 핵심 키워드 추출
- 문항에서 명사와 동사 원형만 추출
- 예: "함께 근무하고 싶어하는 승무원" → [함께, 근무, 승무원]

## 1-2. 숨은 의도 파악
한국어 조사와 어미에서 숨겨진 요구사항을 찾으세요:

| 어미/표현 | 숨은 의도 | 누락 시 문제 |
|-----------|-----------|--------------|
| "~하고 있나요?" | 현재진행형 요구 | 과거만 쓰면 TYPE_D |
| "~는 무엇이며" | 정의/개념 요구 | 정의 없으면 TYPE_D |
| "~한 경험" | 구체적 에피소드 요구 | 추상적이면 TYPE_B |
| "~라고 생각하나요?" | 본인 의견 요구 | 일반론만 쓰면 TYPE_D |
| "~위해 어떤 노력" | 행동/실천 요구 | 마음가짐만 쓰면 TYPE_B |
| "A와 B" (병렬) | 둘 다 답변 요구 | 하나만 답하면 TYPE_D |

## 1-3. 평가 기준 설정
- 1순위: [                    ]
- 2순위: [                    ]
- 3순위: [                    ]

═══════════════════════════════════════════════════════════════
                     STEP 2: 답변 구조 분석
═══════════════════════════════════════════════════════════════

## 2-1. 구조 파악
```
도입: [첫 1-2문장 요약] (O/X)
본론1: [경험/주장 요약] (O/X)
본론2: [경험/주장 요약] (O/X)
결론: [마무리 요약] (O/X)
```

## 2-2. 핵심문장 추출
답변에서 **구체적 사실이 담긴 문장**만 추출하세요.

### 핵심문장의 조건 (모두 충족해야 함)
- 수치/기간/규모/결과 중 1개 이상 포함
- 본인의 직접적 행동이 드러남
- 제3자가 검증 가능한 사실

### 핵심문장이 아닌 것
- "저는 ~한 사람입니다" (검증불가)
- "~가 중요하다고 생각합니다" (의견)
- "~를 배웠습니다" (추상적)
- "~환경을 조성했습니다" (구체성 없음)
- "많은/다양한/여러" (수치 없음)

### 핵심문장 판정 예시
```
X: "저는 팀워크가 중요하다고 생각합니다" → 의견일 뿐
X: "환경을 조성했습니다" → 뭘 했는지 불명확
X: "많은 고객을 응대했습니다" → 몇 명인지 없음
O: "3개월간 매주 50명의 고객을 응대했습니다" → 기간+빈도+수치
O: "15분간 항의하는 고객에게 새 음료와 쿠폰을 제공했습니다" → 시간+구체적 행동+결과
O: "축구 동아리 20명 중 주장으로 선출되었습니다" → 규모+역할
```

## 2-3. 문항-답변 정합성
| 문항 요구사항 | 응답 여부 | 해당 부분 인용 |
|--------------|----------|---------------|
| [요구1]       | O/X/△   | "..."         |
| [요구2]       | O/X/△   | "..."         |

═══════════════════════════════════════════════════════════════
                     STEP 3: 취약점 탐지
═══════════════════════════════════════════════════════════════

아래 5가지 유형만 존재합니다.
**반드시 원문 인용** + **심각도 점수** 포함하세요.

## TYPE_A: 논리비약 [심각도: 3점]
- 정의: A에서 B로 넘어가는 근거가 없음
- 탐지 키워드: "그래서", "따라서", "그렇기에", "덕분에"
- 체크: 뒤의 결론이 앞 문장으로 증명되는가?
- 면접관 반응: "그래서 뭐?" "왜 그렇게 되는 건데?"

## TYPE_B: 구체성 결여 [심각도: 2점]
- 정의: 수치, 기간, 규모, 방법이 없는 추상적 서술
- 탐지 키워드: "많은", "다양한", "여러", "크게", "열심히", "최선을 다해", "환경을 조성", "노력했습니다", "성장했습니다"
- 면접관 반응: "구체적으로?" "몇 명?" "어떻게?"

## TYPE_C: 경험-역량 불일치 [심각도: 3점]
- 정의: 제시한 경험이 주장하는 역량을 증명하지 못함
- 탐지법: 경험 속에서 해당 역량을 **본인이 직접 발휘한 장면**이 있는가?
- 위험 신호: "함께 했다", "같이 극복했다", "팀으로 이뤄냈다" = 본인 역할 불명확
- 면접관 반응: "그래서 네가 뭘 했는데?"

## TYPE_D: 문항-답변 불일치 [심각도: 2점]
- 정의: 문항이 요구한 것과 답변 내용이 다름
- 탐지법:
  - 문항이 "현재"를 물었는데 "과거"만 씀
  - 문항이 "A와 B"를 물었는데 A만 답함
  - 문항의 핵심 키워드가 답변에 없음
- 면접관 반응: "질문에 대한 답이 아닌데?"

## TYPE_E: 검증불가 주장 [심각도: 1점]
- 정의: 제3자가 확인할 수 없는 주관적 주장
- 탐지 키워드: "저는 ~한 사람입니다", "항상 ~합니다", "~라고 생각합니다", "의미 있는", "소중한", "진정한"
- 면접관 반응: "그걸 어떻게 증명해?"

═══════════════════════════════════════════════════════════════
                     STEP 4: 자소서 강/약 판단
═══════════════════════════════════════════════════════════════

## 4-1. 취약점 점수 계산

발견된 취약점의 심각도 점수를 합산하세요:

```
TYPE_A (논리비약)      × 3점 = ___점
TYPE_B (구체성결여)    × 2점 = ___점
TYPE_C (경험-역량불일치) × 3점 = ___점
TYPE_D (문항불일치)    × 2점 = ___점
TYPE_E (검증불가)      × 1점 = ___점
─────────────────────────────
총 취약점 점수:          ___점
```

## 4-2. 기본 등급 판정

| 총 점수 | 기본 등급 | 의미 |
|---------|----------|------|
| 0~2점 | STRONG | 공격 포인트 적음, 깊이 있는 자소서 |
| 3~5점 | MEDIUM | 보통 수준, 일부 보완 필요 |
| 6점 이상 | WEAK | 공격 포인트 많음, 기본기 부족 |

## 4-3. 핵심문장 보정 (하이브리드)

기본 등급을 핵심문장 수로 보정하세요:

### 보정 규칙
```
IF 기본등급 = STRONG AND 핵심문장 < 2개:
   → MEDIUM으로 하향
   → 사유: "취약점은 적으나 구체적 팩트도 부족"

IF 기본등급 = WEAK AND 핵심문장 >= 5개:
   → MEDIUM으로 상향
   → 사유: "취약점은 많으나 소재는 풍부, 표현이 문제"

그 외: 기본 등급 유지
```

## 4-4. 최종 등급 결정

```
기본 등급: [STRONG/MEDIUM/WEAK]
핵심문장 수: [N]개
보정 적용: [있음/없음]
보정 사유: [해당 시 기재]
─────────────────────────────
최종 등급: [STRONG/MEDIUM/WEAK]
```

═══════════════════════════════════════════════════════════════
                     STEP 5: 질문 버전 분배
═══════════════════════════════════════════════════════════════

최종 등급에 따라 6개 버전의 질문 유형을 배분하세요:

## 질문 유형 정의

### [자소서 기반 질문]
- 자소서에서 발견된 취약점을 공격
- 반드시 원문 내용을 언급
- SLOT_ACTION, SLOT_CONFLICT, SLOT_CRITERIA, SLOT_RESULT, SLOT_EVIDENCE, SLOT_ALIGNMENT 사용

### [직무 연결 질문]
- 자소서 내용을 승무원 직무와 연결
- 또는 자소서에 없는 직무 상황 제시
- SLOT_JOB, SLOT_ALTERNATIVE 사용

## 등급별 버전 배분

### WEAK (6점 이상)
```
v1: 자소서 기반 (가장 심각한 취약점 공격)
v2: 자소서 기반 (두 번째 취약점 공격)
v3: 자소서 기반 (세 번째 취약점 공격)
v4: 직무 연결 (자소서 경험 → 기내 상황)
v5: 직무 연결 (승무원 역량 질문)
v6: 직무 연결 (돌발 상황 대처)
```

### MEDIUM (3~5점)
```
v1: 자소서 기반 (가장 심각한 취약점 공격)
v2: 자소서 기반 (두 번째 취약점 공격)
v3: 자소서 기반 (경험 심화 질문)
v4: 자소서 기반 (다른 각도로 검증)
v5: 직무 연결 (자소서 경험 → 기내 상황)
v6: 직무 연결 (승무원 역량 질문)
```

### STRONG (0~2점)
```
v1: 자소서 기반 (있는 취약점 공격)
v2: 자소서 기반 (경험 심화 질문)
v3: 자소서 기반 (다른 각도로 검증)
v4: 자소서 기반 (구체적 상황 재현 요청)
v5: 자소서 기반 (가치관/철학 심화)
v6: 자소서 기반 (성장/변화 확인)
```

═══════════════════════════════════════════════════════════════
                     STEP 6: 질문 생성
═══════════════════════════════════════════════════════════════

## 질문 슬롯 (8가지) - 반드시 이 중에서 선택

### [SLOT_ACTION] 역할/행동 검증
- "'{경험}'에서 본인이 직접 한 행동은 구체적으로 뭐예요?"
- "그 상황에서 본인의 역할은 정확히 뭐였어요?"
- "'{결과}'를 위해 본인이 기여한 부분은 뭐예요?"
- "팀에서 본인이 아니었으면 안 됐던 부분이 있어요?"

### [SLOT_CONFLICT] 갈등/조율 검증
- "'{경험}' 중에 의견 충돌이나 어려움은 없었어요?"
- "팀원들과 갈등이 있었다면 어떻게 해결했어요?"
- "반대 의견이 있을 때 어떻게 조율하셨어요?"
- "가장 힘들었던 순간은 언제였어요?"

### [SLOT_CRITERIA] 기준/원칙 검증
- "'{결정}'을 내린 기준이 뭐였어요?"
- "왜 다른 방법이 아니라 그 방법을 선택했어요?"
- "'{A}'에서 '{B}'로 이어진다고 했는데, 그 연결고리가 뭐예요?"
- "그때 가장 중요하게 생각한 원칙이 있었어요?"

### [SLOT_RESULT] 결과/성과 검증
- "'{경험}'의 구체적인 결과나 성과는 뭐였어요?"
- "'{추상표현}'을 수치로 표현하면 어느 정도예요?"
- "전과 후가 어떻게 달라졌어요?"
- "그 결과를 어떻게 측정했어요?"

### [SLOT_ALTERNATIVE] 대안/한계 검증
- "다시 그 상황이라면 다르게 하고 싶은 부분이 있어요?"
- "그 방법의 한계나 아쉬운 점은 뭐였어요?"
- "다른 방법은 고려 안 해봤어요?"
- "실패했거나 아쉬웠던 경험도 있어요?"

### [SLOT_JOB] 직무 연결 검증
- "이 경험이 승무원 업무에서 어떻게 활용될 거예요?"
- "'{역량}'이 기내에서 필요한 상황을 예로 들어볼래요?"
- "승무원으로서 이 경험을 어떻게 적용하실 건가요?"
- "비슷한 상황이 기내에서 생기면 어떻게 하실 거예요?"

### [SLOT_ALIGNMENT] 문항 의도 재확인 (TYPE_D 전용)
- "문항에서 '{누락된 요구}'를 물었는데, 이에 대해 답해주시겠어요?"
- "'{문항 키워드}'에 대해서는 어떻게 생각하세요?"
- "'현재 하고 있는 노력'을 물었는데, 지금 하고 있는 건 뭐예요?"

### [SLOT_EVIDENCE] 증거/사례 요구 (TYPE_E 전용)
- "'{주장}'을 보여준 구체적인 에피소드가 있어요?"
- "주변 사람들은 당신의 '{특성}'에 대해 뭐라고 해요?"
- "'{주장}'이 드러난 최근 사례를 하나만 들어주세요."

## TYPE → SLOT 매핑 규칙

| 취약점 유형 | 1차 슬롯 | 2차 슬롯 |
|------------|---------|---------|
| TYPE_A (논리비약) | SLOT_CRITERIA | SLOT_ACTION |
| TYPE_B (구체성결여) | SLOT_RESULT | SLOT_ACTION |
| TYPE_C (경험-역량불일치) | SLOT_ACTION | SLOT_EVIDENCE |
| TYPE_D (문항불일치) | SLOT_ALIGNMENT | SLOT_JOB |
| TYPE_E (검증불가) | SLOT_EVIDENCE | SLOT_ALTERNATIVE |

═══════════════════════════════════════════════════════════════
                     STEP 7: 면접관 종합 평가
═══════════════════════════════════════════════════════════════

## 7-1. 좋은 점 (최대 3개)
- 반드시 원문 근거 포함

## 7-2. 아쉬운 점 (최대 3개)
- 반드시 원문 근거 포함

## 7-3. 전체 인상 (1문장)


═══════════════════════════════════════════════════════════════
                        출력 형식
═══════════════════════════════════════════════════════════════

반드시 아래 형식으로만 출력하세요:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    [문항 N] 분석
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 문항 원문
[문항 전체 인용]

■ 핵심 키워드
[키워드1], [키워드2], [키워드3]

■ 숨은 의도
- [의도1]: [근거가 되는 조사/어미]
- [의도2]: [근거가 되는 조사/어미]

■ 평가 기준
1순위: [        ]
2순위: [        ]
3순위: [        ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    답변 분석
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 구조
도입: [요약] (O/X)
본론1: [요약] (O/X)
본론2: [요약] (O/X)
결론: [요약] (O/X)

■ 핵심문장 (구체적 팩트가 있는 문장만)
1. "[인용]" ← [수치/기간/규모/결과 중 무엇이 있는지]
2. "[인용]" ← [수치/기간/규모/결과 중 무엇이 있는지]
(해당 없으면 "핵심문장 없음" 기재)

■ 문항-답변 정합성
| 요구사항 | 응답 | 해당 부분 |
|----------|------|-----------|
| [요구1]  | O/X/△ | "[인용]" |
| [요구2]  | O/X/△ | "[인용]" |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    취약점 분석
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[취약점 1]
- 유형: TYPE_X [심각도: N점]
- 원문: "[해당 부분 그대로 인용]"
- 문제: [왜 문제인지 1문장]
- 면접관 반응: "[예상 반응]"

[취약점 2]
- 유형: TYPE_X [심각도: N점]
- 원문: "[해당 부분 그대로 인용]"
- 문제: [왜 문제인지 1문장]
- 면접관 반응: "[예상 반응]"

[취약점 3]
- 유형: TYPE_X [심각도: N점]
- 원문: "[해당 부분 그대로 인용]"
- 문제: [왜 문제인지 1문장]
- 면접관 반응: "[예상 반응]"

(취약점이 없으면 "취약점 없음" 기재)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    자소서 강/약 판단
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 취약점 점수 계산
- TYPE_A × 3점 = ___점
- TYPE_B × 2점 = ___점
- TYPE_C × 3점 = ___점
- TYPE_D × 2점 = ___점
- TYPE_E × 1점 = ___점
──────────────────
총 취약점 점수: ___점

■ 기본 등급: [STRONG/MEDIUM/WEAK]

■ 핵심문장 보정
- 핵심문장 수: [N]개
- 보정 적용: [있음/없음]
- 보정 사유: [해당 시 기재]

■ 최종 등급: [STRONG/MEDIUM/WEAK]

■ 질문 버전 배분
| 버전 | 질문 유형 |
|------|-----------|
| v1 | [자소서 기반/직무 연결] |
| v2 | [자소서 기반/직무 연결] |
| v3 | [자소서 기반/직무 연결] |
| v4 | [자소서 기반/직무 연결] |
| v5 | [자소서 기반/직무 연결] |
| v6 | [자소서 기반/직무 연결] |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    면접관 종합 평가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

■ 좋은 점
1. [내용] ← "[근거 인용]"
2. [내용] ← "[근거 인용]"

■ 아쉬운 점
1. [내용] ← "[근거 인용]"
2. [내용] ← "[근거 인용]"

■ 전체 인상
[1문장 요약]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    예상 면접 질문 (6버전)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[v1]
- 유형: [자소서 기반/직무 연결]
- 슬롯: SLOT_XXX
- 대응 취약점: TYPE_X (또는 "심화 질문")
- 질문: "[실제 질문]"
- 의도: [이 질문으로 확인하려는 것]

[v2]
- 유형: [자소서 기반/직무 연결]
- 슬롯: SLOT_XXX
- 대응 취약점: TYPE_X (또는 "심화 질문")
- 질문: "[실제 질문]"
- 의도: [이 질문으로 확인하려는 것]

[v3]
- 유형: [자소서 기반/직무 연결]
- 슬롯: SLOT_XXX
- 대응 취약점: TYPE_X (또는 "심화 질문")
- 질문: "[실제 질문]"
- 의도: [이 질문으로 확인하려는 것]

[v4]
- 유형: [자소서 기반/직무 연결]
- 슬롯: SLOT_XXX
- 대응 취약점: TYPE_X (또는 "직무 연결")
- 질문: "[실제 질문]"
- 의도: [이 질문으로 확인하려는 것]

[v5]
- 유형: [자소서 기반/직무 연결]
- 슬롯: SLOT_XXX
- 대응 취약점: TYPE_X (또는 "직무 연결")
- 질문: "[실제 질문]"
- 의도: [이 질문으로 확인하려는 것]

[v6]
- 유형: [자소서 기반/직무 연결]
- 슬롯: SLOT_XXX
- 대응 취약점: TYPE_X (또는 "직무 연결")
- 질문: "[실제 질문]"
- 의도: [이 질문으로 확인하려는 것]
```

═══════════════════════════════════════════════════════════════
                        금지 사항
═══════════════════════════════════════════════════════════════

1. 원문 인용 없이 취약점 주장 금지
2. "~인 것 같습니다", "~로 보입니다" 추측 표현 금지
3. 5가지 TYPE 외 다른 취약점 유형 창작 금지
4. 8가지 SLOT 외 다른 질문 형식 창작 금지
5. 점수/등급 임의 조정 금지 (계산식 따를 것)
6. 지원자 인성/태도/진정성 추론 금지
7. 취약점 4개 이상 나열 금지 (최대 3개)
8. 핵심문장 기준 충족 안 되면 핵심문장으로 인정 금지
9. 자소서에 없는 내용으로 질문 금지 (직무 연결 질문 제외)
10. 버전 배분 규칙 무시 금지

═══════════════════════════════════════════════════════════════
                    좋은 질문 vs 나쁜 질문 예시
═══════════════════════════════════════════════════════════════

## 좋은 질문 (이렇게 하세요)

자소서: "축구 동아리에서 주장으로 대회를 준비했습니다..."
→ 좋은 질문: "축구 동아리에서 대회 준비할 때 팀원들과 의견 충돌이 있었어요?"
→ 좋은 질문: "주장으로서 본인이 직접 한 역할이 뭐예요?"
→ 좋은 질문: "훈련 참여율이 회복됐다고 했는데, 전후 수치로 비교하면 어느 정도예요?"

자소서: "카페에서 아르바이트하며 고객 응대를 배웠습니다..."
→ 좋은 질문: "카페에서 가장 힘들었던 고객 응대 상황이 뭐였어요?"
→ 좋은 질문: "하루에 몇 명 정도 고객을 응대했어요?"
→ 좋은 질문: "컴플레인 고객을 어떻게 처리했어요?"

## 나쁜 질문 (절대 하지 마세요)

자소서: "축구 동아리에서 주장으로 대회를 준비했습니다..."
→ ❌ 나쁜 질문: "영화 '첫 비행'에서 말하는 꿈이란 무엇인가요?" (자소서에 없는 영화 언급)
→ ❌ 나쁜 질문: "어떤 특정 사건을 다큐멘터리에 담고 싶나요?" (자소서와 무관)
→ ❌ 나쁜 질문: "축구를 통해 무엇을 배우고 싶나요?" (~나요? 종결어미 + 미래형)
→ ❌ 나쁜 질문: "리더십이 왜 중요하다고 생각하나요?" (자소서 내용 검증 아닌 일반 질문)

## 핵심 원칙

1. 질문은 반드시 자소서에 나온 경험/활동/상황을 구체적으로 언급해야 함
2. "~예요?", "~했어요?", "~뭐예요?" 종결어미만 사용
3. 자소서에 없는 영화, 책, 노래, 가상의 사건 등을 절대 언급하지 말 것
4. 각 버전은 서로 다른 토픽/슬롯을 사용해서 다양한 질문 생성"""


# ===========================================
# v4.0 USER PROMPT 템플릿
# ===========================================
USER_PROMPT_TEMPLATE = """다음 자기소개서를 분석해주세요.

[문항]
{question}

[답변]
{answer}

위 분석 프로세스(STEP 1~7)를 순서대로 수행하고, 지정된 출력 형식으로 결과를 제시하세요.
6개 버전의 면접 질문을 모두 생성해주세요."""


# ===========================================
# v4.0 파싱 함수들
# ===========================================
def parse_essay_grade(clova_response: str) -> dict:
    """
    클로바 응답에서 자소서 등급 및 버전 배분 파싱
    """
    # 최종 등급 추출
    grade_match = re.search(r'최종 등급:\s*(STRONG|MEDIUM|WEAK)', clova_response)
    grade = grade_match.group(1) if grade_match else "MEDIUM"

    # 취약점 점수 추출
    score_match = re.search(r'총 취약점 점수:\s*(\d+)점', clova_response)
    score = int(score_match.group(1)) if score_match else 0

    # 핵심문장 수 추출
    key_sentence_match = re.search(r'핵심문장 수:\s*\[?(\d+)\]?개', clova_response)
    key_sentences = int(key_sentence_match.group(1)) if key_sentence_match else 0

    # 버전별 질문 추출
    questions = {}
    for v in range(1, 7):
        # 패턴: [v1] ... 질문: "..."
        pattern = rf'\[v{v}\].*?질문:\s*"([^"]+)"'
        match = re.search(pattern, clova_response, re.DOTALL)
        if match:
            questions[f"v{v}"] = match.group(1)

    # 버전별 슬롯 추출
    slots = {}
    for v in range(1, 7):
        pattern = rf'\[v{v}\].*?슬롯:\s*(SLOT_\w+)'
        match = re.search(pattern, clova_response, re.DOTALL)
        if match:
            slots[f"v{v}"] = match.group(1)

    # 버전별 유형 추출 (자소서 기반/직무 연결)
    types = {}
    for v in range(1, 7):
        pattern = rf'\[v{v}\].*?유형:\s*\[?(자소서 기반|직무 연결)\]?'
        match = re.search(pattern, clova_response, re.DOTALL)
        if match:
            types[f"v{v}"] = match.group(1)

    # 버전별 의도 추출
    intents = {}
    for v in range(1, 7):
        pattern = rf'\[v{v}\].*?의도:\s*([^\n]+)'
        match = re.search(pattern, clova_response, re.DOTALL)
        if match:
            intents[f"v{v}"] = match.group(1).strip()

    # 취약점 추출
    vulnerabilities = []
    vuln_pattern = r'\[취약점 \d+\].*?유형:\s*(TYPE_[A-E]).*?원문:\s*"([^"]+)".*?문제:\s*([^\n]+)'
    vuln_matches = re.findall(vuln_pattern, clova_response, re.DOTALL)
    for match in vuln_matches[:3]:  # 최대 3개
        vulnerabilities.append({
            "type": match[0],
            "original": match[1],
            "problem": match[2].strip()
        })

    return {
        "grade": grade,
        "vulnerability_score": score,
        "key_sentence_count": key_sentences,
        "questions": questions,
        "slots": slots,
        "types": types,
        "intents": intents,
        "vulnerabilities": vulnerabilities
    }


def get_question_by_version(parsed_result: dict, version: int) -> dict:
    """
    특정 버전의 질문 및 메타데이터 반환
    """
    v_key = f"v{version}"
    return {
        "question": parsed_result["questions"].get(v_key, ""),
        "slot": parsed_result["slots"].get(v_key, "SLOT_ACTION"),
        "type": parsed_result["types"].get(v_key, "자소서 기반"),
        "intent": parsed_result["intents"].get(v_key, ""),
        "is_job_connection": parsed_result["types"].get(v_key, "") == "직무 연결"
    }


# ===========================================
# FLYREADY CLOVA 엔진 클래스 v4.0
# ===========================================
class FlyreadyClovaEngine:
    """FLYREADY 1회 호출 엔진 v4.0 (6버전 질문 한 번에 생성)"""

    def __init__(self, airline: str = None):
        self.airline = airline
        self.last_raw_response = None
        self.last_parsed_result = None

    def analyze(self, question: str, answer: str, item_num: int = 2) -> dict:
        """
        메인 분석 함수 (1회 호출로 분석 + 6버전 질문 생성)

        Args:
            question: 자소서 문항
            answer: 자소서 답변
            item_num: 문항 번호

        Returns:
            {
                "grade": "STRONG/MEDIUM/WEAK",
                "vulnerability_score": int,
                "key_sentence_count": int,
                "questions": {"v1": "...", "v2": "...", ...},
                "slots": {"v1": "SLOT_XXX", ...},
                "types": {"v1": "자소서 기반", ...},
                "intents": {"v1": "...", ...},
                "vulnerabilities": [...],
                "raw_response": "원본 응답"
            }
        """
        print(f"\n[FLYREADY v4.0] 분석 시작 (항공사: {self.airline})")
        start_time = time.time()

        # 1회 호출로 전체 분석 + 6버전 질문 생성
        print("[CLOVA 호출] 7단계 분석 + 6버전 질문 생성 중...")

        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            answer=answer
        )

        raw_response = self._call_clova(
            system=SYSTEM_PROMPT_V4,
            user=user_prompt,
            temperature=0.3,
            max_tokens=4000  # 6버전 질문 + 분석 결과를 위해 충분히
        )

        if not raw_response:
            print("[CLOVA 호출] 실패 - 폴백 모드")
            return self._fallback_result()

        self.last_raw_response = raw_response

        # v4.1: 디버그 로깅
        log_clova_response(raw_response, question, answer)

        # 파싱
        print("[파싱] 응답 파싱 중...")
        parsed = parse_essay_grade(raw_response)
        self.last_parsed_result = parsed

        # 결과 검증
        question_count = len([q for q in parsed["questions"].values() if q])
        print(f"[파싱] 완료 - 등급: {parsed['grade']}, 질문: {question_count}개")

        if question_count < 4:
            print(f"[경고] 질문 부족 ({question_count}개) - 폴백 보충")
            parsed = self._supplement_questions(parsed)

        # v4.1: 각 질문 검증 및 필터링
        parsed = self._validate_and_filter_questions(parsed, answer)

        total_time = time.time() - start_time
        print(f"[FLYREADY v4.1] 완료 ({total_time:.1f}초)")

        # 결과에 원본 응답 추가
        parsed["raw_response"] = raw_response
        parsed["processing_time"] = total_time

        return parsed

    def _call_clova(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 4000) -> Optional[str]:
        """CLOVA API 호출"""
        try:
            headers = {
                'Authorization': f'Bearer {CLOVA_API_KEY}',
                'X-NCP-CLOVASTUDIO-REQUEST-ID': CLOVA_REQUEST_ID,
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json'
            }

            payload = {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "temperature": temperature,
                "maxTokens": max_tokens,
                "topP": 0.8,
                "topK": 0,
                "repeatPenalty": 1.2
            }

            endpoint = f"{CLOVA_HOST}/v3/chat-completions/{CLOVA_MODEL}"

            response = requests.post(endpoint, headers=headers, json=payload, timeout=120)

            if response.status_code != 200:
                print(f"[CLOVA ERROR] HTTP {response.status_code}: {response.text[:200]}")
                return None

            # 응답 파싱
            resp_json = response.json()
            if 'result' in resp_json and 'message' in resp_json['result']:
                return resp_json['result']['message'].get('content', '')
            elif 'message' in resp_json:
                return resp_json['message'].get('content', '')

            return None

        except Exception as e:
            print(f"[CLOVA ERROR] {e}")
            return None

    def _supplement_questions(self, parsed: dict) -> dict:
        """부족한 질문을 폴백으로 보충"""
        fallback_questions = {
            "v1": "자소서에서 가장 강조하고 싶은 경험이 뭐예요?",
            "v2": "그 경험에서 본인이 직접 한 행동은 뭐예요?",
            "v3": "결과를 수치로 표현하면 어느 정도예요?",
            "v4": "다시 그 상황이라면 다르게 하고 싶은 부분이 있어요?",
            "v5": "이 경험이 승무원 업무에서 어떻게 활용될 거예요?",
            "v6": "비슷한 상황이 기내에서 생기면 어떻게 하실 거예요?"
        }

        fallback_slots = {
            "v1": "SLOT_ACTION",
            "v2": "SLOT_ACTION",
            "v3": "SLOT_RESULT",
            "v4": "SLOT_ALTERNATIVE",
            "v5": "SLOT_JOB",
            "v6": "SLOT_JOB"
        }

        fallback_types = {
            "v1": "자소서 기반",
            "v2": "자소서 기반",
            "v3": "자소서 기반",
            "v4": "자소서 기반",
            "v5": "직무 연결",
            "v6": "직무 연결"
        }

        for v in range(1, 7):
            v_key = f"v{v}"
            if not parsed["questions"].get(v_key):
                parsed["questions"][v_key] = fallback_questions[v_key]
                parsed["slots"][v_key] = fallback_slots[v_key]
                parsed["types"][v_key] = fallback_types[v_key]
                parsed["intents"][v_key] = "폴백 질문"
                print(f"[보충] {v_key}: {fallback_questions[v_key][:30]}...")

        return parsed

    def _validate_and_filter_questions(self, parsed: dict, answer: str) -> dict:
        """
        v4.1: 생성된 질문을 자소서 내용과 대조 검증
        1. 종결어미 변환 (~나요? → ~예요?)
        2. 이상한 질문은 폴백으로 대체
        """
        print("[v4.1 검증] 질문 유효성 검사 시작...")

        # 먼저 모든 질문의 종결어미 변환
        for v in range(1, 7):
            v_key = f"v{v}"
            question = parsed["questions"].get(v_key, "")
            if question:
                converted = convert_question_ending(question)
                if converted != question:
                    print(f"[v4.1 변환] {v_key}: ...{question[-20:]} → ...{converted[-20:]}")
                    parsed["questions"][v_key] = converted

        # 자소서 기반 폴백 질문 (토픽별로 다양하게)
        topics = extract_key_topics_from_answer(answer)
        print(f"[v4.1 검증] 자소서 토픽: {topics[:3]}...")

        # 버전별 폴백 (다양한 슬롯 사용)
        fallback_pool = [
            ("자소서에서 가장 강조하고 싶은 경험이 뭐예요?", "SLOT_ACTION"),
            ("그 경험에서 본인이 직접 한 행동은 뭐예요?", "SLOT_ACTION"),
            ("가장 어려웠던 순간은 언제였어요?", "SLOT_CONFLICT"),
            ("왜 그 방법을 선택했어요?", "SLOT_CRITERIA"),
            ("결과를 수치로 표현하면 어느 정도예요?", "SLOT_RESULT"),
            ("다시 그 상황이라면 다르게 하고 싶은 부분이 있어요?", "SLOT_ALTERNATIVE"),
            ("이 경험이 승무원 업무에서 어떻게 활용될 거예요?", "SLOT_JOB"),
            ("비슷한 상황이 기내에서 생기면 어떻게 하실 거예요?", "SLOT_JOB"),
        ]

        replaced_count = 0
        for v in range(1, 7):
            v_key = f"v{v}"
            question = parsed["questions"].get(v_key, "")

            if not question:
                continue

            # 검증
            is_valid, reason = validate_question_against_resume(question, answer)

            if not is_valid:
                print(f"[v4.1 검증] {v_key} 무효: {reason}")
                print(f"[v4.1 검증] 원래 질문: {question[:50]}...")

                # 폴백으로 대체
                fallback_q, fallback_slot = fallback_pool[replaced_count % len(fallback_pool)]
                parsed["questions"][v_key] = fallback_q
                parsed["slots"][v_key] = fallback_slot
                parsed["intents"][v_key] = f"검증 실패 폴백 ({reason})"
                replaced_count += 1

                print(f"[v4.1 검증] 대체 질문: {fallback_q}")

        if replaced_count > 0:
            print(f"[v4.1 검증] 총 {replaced_count}개 질문 대체됨")
        else:
            print("[v4.1 검증] 모든 질문 유효")

        # 토픽 다양성 검사 (같은 키워드가 4개 이상 질문에서 반복되면 경고)
        all_questions = [parsed["questions"].get(f"v{i}", "") for i in range(1, 7)]
        keyword_counts = {}
        TOPIC_KEYWORDS = ["유학", "교환학생", "해외", "축구", "동아리", "아르바이트", "봉사", "인턴", "공모전"]

        for kw in TOPIC_KEYWORDS:
            count = sum(1 for q in all_questions if kw in q)
            if count >= 4:
                print(f"[v4.1 경고] '{kw}' 키워드가 {count}개 질문에서 반복됨 - 다양성 부족!")
                keyword_counts[kw] = count

        if keyword_counts:
            print(f"[v4.1 경고] 반복 토픽: {keyword_counts}")
            # 반복 토픽이 있으면 일부 질문을 다양화 (v3, v4를 다른 슬롯으로 교체)
            diverse_fallbacks = [
                ("그 경험에서 가장 큰 어려움은 뭐였어요?", "SLOT_CONFLICT"),
                ("결과가 기대와 달랐던 부분이 있어요?", "SLOT_RESULT"),
                ("다른 방법은 고려 안 해봤어요?", "SLOT_ALTERNATIVE"),
                ("이 경험을 통해 배운 점이 뭐예요?", "SLOT_CRITERIA"),
            ]
            for idx, (fb_q, fb_slot) in enumerate(diverse_fallbacks):
                v_key = f"v{idx + 3}"  # v3, v4, v5, v6에 적용
                if v_key in parsed["questions"]:
                    old_q = parsed["questions"][v_key]
                    # 반복 키워드가 있는 질문만 교체
                    for kw in keyword_counts:
                        if kw in old_q:
                            parsed["questions"][v_key] = fb_q
                            parsed["slots"][v_key] = fb_slot
                            parsed["intents"][v_key] = "다양성 확보 폴백"
                            print(f"[v4.1 다양화] {v_key}: {fb_q}")
                            break

        return parsed

    def _fallback_result(self) -> dict:
        """분석 실패 시 폴백 결과"""
        return {
            "grade": "MEDIUM",
            "vulnerability_score": 0,
            "key_sentence_count": 0,
            "questions": {
                "v1": "자소서에서 가장 강조하고 싶은 경험이 뭐예요?",
                "v2": "그 경험에서 본인이 직접 한 행동은 뭐예요?",
                "v3": "결과를 수치로 표현하면 어느 정도예요?",
                "v4": "다시 그 상황이라면 다르게 하고 싶은 부분이 있어요?",
                "v5": "이 경험이 승무원 업무에서 어떻게 활용될 거예요?",
                "v6": "비슷한 상황이 기내에서 생기면 어떻게 하실 거예요?"
            },
            "slots": {
                "v1": "SLOT_ACTION",
                "v2": "SLOT_ACTION",
                "v3": "SLOT_RESULT",
                "v4": "SLOT_ALTERNATIVE",
                "v5": "SLOT_JOB",
                "v6": "SLOT_JOB"
            },
            "types": {
                "v1": "자소서 기반",
                "v2": "자소서 기반",
                "v3": "자소서 기반",
                "v4": "자소서 기반",
                "v5": "직무 연결",
                "v6": "직무 연결"
            },
            "intents": {
                "v1": "핵심 경험 확인",
                "v2": "역할 검증",
                "v3": "결과 검증",
                "v4": "대안 탐색",
                "v5": "직무 연결",
                "v6": "상황 대처"
            },
            "vulnerabilities": [],
            "raw_response": None,
            "processing_time": 0,
            "is_fallback": True
        }


# ===========================================
# 편의 함수 (하위호환)
# ===========================================
def analyze_resume_with_flyready(
    question: str,
    answer: str,
    airline: str = None,
    item_num: int = 2
) -> dict:
    """
    FLYREADY 엔진으로 자소서 분석 (외부 호출용)
    """
    engine = FlyreadyClovaEngine(airline=airline)
    return engine.analyze(question, answer, item_num)


# ===========================================
# 테스트
# ===========================================
if __name__ == "__main__":
    # 테스트용
    test_question = "팀 목표 달성을 위해 협업했던 경험을 구체적으로 서술하시오."
    test_answer = """학교 축구동아리에서 대회 출전을 준비하던 시기에, 팀 내에서 훈련 방식과 출전 명단을 두고 의견 충돌이 발생했습니다.
    저는 주장으로서 갈등의 핵심이 '누가 맞느냐'가 아니라 '최적의 결과를 내는 방식이 무엇이냐'라고 판단했습니다.
    그래서 팀원들에게 익명 설문을 받아 현재 컨디션과 불만 요인을 수집했고, 2주 단위로 체력/전술 비중을 조정하는 로드맵을 만들었습니다.
    그 결과 훈련 참여율이 회복되었고, 팀원들은 불필요한 감정 소모가 줄었습니다."""

    result = analyze_resume_with_flyready(test_question, test_answer, airline="대한항공")

    print("\n=== 분석 결과 ===")
    print(f"등급: {result['grade']}")
    print(f"취약점 점수: {result['vulnerability_score']}점")
    print(f"핵심문장: {result['key_sentence_count']}개")

    print(f"\n취약점: {len(result['vulnerabilities'])}개")
    for v in result['vulnerabilities']:
        print(f"  - {v['type']}: {v['original'][:30]}...")

    print(f"\n질문 (6버전):")
    for v in range(1, 7):
        v_key = f"v{v}"
        q = result['questions'].get(v_key, "없음")
        t = result['types'].get(v_key, "?")
        s = result['slots'].get(v_key, "?")
        print(f"  v{v} [{t}] [{s}]: {q[:50]}...")
