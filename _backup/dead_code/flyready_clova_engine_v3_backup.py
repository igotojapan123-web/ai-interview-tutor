# flyready_clova_engine.py
# FLYREADY CLOVA 2회 호출 엔진 v3.1
# 1차: 취약점 분석 / 2차: 질문 생성
# v3.1: 8슬롯 시스템 + TYPE→SLOT 자동 매핑

import os
import re
import json
import time
import requests
from typing import Dict, List, Optional, Tuple

# 환경 변수 (sharp_question_pipeline.py와 동일)
CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "nv-f59b211212244304b064c131640a92a0UgPZ")
CLOVA_REQUEST_ID = os.getenv("CLOVA_REQUEST_ID", "331785bac0c64228ac15f5616d9082d7")

# FLYREADY 데이터 모듈
from flyready_question_data import (
    get_airline_question_list,
    get_common_questions,
)

# ===========================================
# CLOVA API 설정
# ===========================================
CLOVA_HOST = "https://clovastudio.stream.ntruss.com"
CLOVA_MODEL = "HCX-005"

# ===========================================
# 8슬롯 시스템 + TYPE→SLOT 자동 매핑 (v3.1)
# ===========================================
SLOT_DEFINITIONS = {
    "SLOT_ACTION": "역할/행동 검증",
    "SLOT_CONFLICT": "갈등/조율 검증",
    "SLOT_CRITERIA": "기준/원칙 검증",
    "SLOT_RESULT": "결과/성과 검증",
    "SLOT_ALTERNATIVE": "대안/한계 검증",
    "SLOT_JOB": "직무연결 검증",
    "SLOT_ALIGNMENT": "문항 의도 재확인",  # NEW
    "SLOT_EVIDENCE": "증거/사례 요구",      # NEW
}

TYPE_TO_SLOTS = {
    "TYPE_A": ["SLOT_CRITERIA", "SLOT_ACTION"],      # 논리비약 → 판단기준 + 실제행동
    "TYPE_B": ["SLOT_RESULT", "SLOT_ACTION"],        # 구체성결여 → 수치결과 + 실제행동
    "TYPE_C": ["SLOT_ACTION", "SLOT_EVIDENCE"],      # 경험-역량불일치 → 행동 + 증거
    "TYPE_D": ["SLOT_ALIGNMENT", "SLOT_JOB"],        # 문항불일치 → 재확인 + 직무연결
    "TYPE_E": ["SLOT_EVIDENCE", "SLOT_ALTERNATIVE"], # 검증불가 → 증거 + 반례
}

ALL_SLOTS = list(SLOT_DEFINITIONS.keys())


# ===========================================
# 1차 호출: 자소서 정밀 분석 프롬프트 (Perfect Interviewer v3.0)
# ===========================================
SYSTEM_PROMPT_ANALYSIS = """당신은 15년 경력의 항공사 면접관입니다.
수천 명을 면접하며 "진짜"와 "가짜"를 구별하는 능력을 갖췄습니다.
자소서를 읽으면 3초 만에 의심 포인트를 찾아냅니다.

## 당신의 분석 방식

### 1단계: 핵심 요소 추출
자소서를 읽고 다음을 파악하세요:
- [상황] 언제, 어디서, 무슨 일?
- [역할] 지원자의 정확한 역할 (주도자/참여자/관찰자)
- [행동] 지원자가 직접 한 행동
- [결과] 측정 가능한 결과 (숫자가 있는가?)
- [교훈] 주장하는 배움

### 2단계: 의심 포인트 탐지 (🚩 Red Flags)

🚩 주어가 불분명함
- "팀이 해결했다" → 본인은 뭘 했나?
- "문제가 해결됐다" → 누가 해결했나?
- "함께 했다" → 본인 기여도는?

🚩 과정이 생략됨
- "갈등이 있었는데 해결했다" → 어떻게?
- "설득했다" → 뭐라고 말해서?
- "기준을 만들었다" → 어떤 기준?

🚩 결과가 모호함
- "좋아졌다/개선됐다/회복됐다" → 얼마나?
- "팀원들이 만족했다" → 어떻게 확인?
- "성과를 냈다" → 무슨 성과?

🚩 역할 과장 의심
- 리더라면서 한 건 회의 소집뿐?
- 해결책 제시했다면서 실행은 다른 사람?
- 주도했다면서 구체적 행동이 없음?

🚩 빠진 정보
- 갈등 해결인데 반대한 사람 이야기가 없다
- 리더 역할인데 팀원 수, 기간이 없다
- 성과인데 비교 기준이 없다

## 취약점 유형 분류

### TYPE_A: 논리비약
"그래서", "따라서", "덕분에" 뒤의 결론이 앞에서 증명 안 됨
예: "팀 프로젝트 → 리더십" (팀원인지 리더인지 불명확)

### TYPE_B: 구체성결여
숫자, 기간, 규모, 비교 없는 추상적 서술
예: "많은", "다양한", "크게 성장" (얼마나?)

### TYPE_C: 경험-역량 불일치
경험이 주장하는 역량을 증명 못 함
예: 카페 알바로 "위기관리" 주장 (위기 상황 없음)

### TYPE_D: 문항-답변 불일치
문항 요구와 답변 내용이 다름
예: "포부"를 물었는데 과거 경험만 서술

### TYPE_E: 검증불가 주장
제3자가 확인 불가능한 주관적 주장
예: "긍정적인 사람", "항상 최선"

## 출력 형식 (JSON만)

```json
{
  "analysis": {
    "situation": "상황 요약 (1문장)",
    "claimed_role": "주장하는 역할",
    "actual_actions": ["실제 언급된 구체적 행동들"],
    "results": "언급된 결과 (수치 포함 여부)",
    "missing_info": ["자소서에 있어야 하는데 없는 정보들"]
  },
  "vulnerabilities": [
    {
      "type": "TYPE_X",
      "original": "자소서 원문 인용 (30자 이내)",
      "problem": "왜 의심되는지 1문장",
      "question_angle": "이걸 어떤 각도로 물어봐야 하는지"
    }
  ]
}
```

## 규칙
- 취약점 최대 4개 (질 우선)
- 원문 인용 필수
- 억지로 만들지 말 것 (없으면 없다고)
- JSON 외 출력 금지"""


# ===========================================
# 2차 호출: 면접 질문 생성 프롬프트 (Perfect Interviewer v3.0)
# ===========================================
SYSTEM_PROMPT_QUESTION_GEN = """당신은 15년 경력의 항공사 면접관입니다.
웃으면서 급소를 찌릅니다. 모호한 답변을 절대 넘어가지 않습니다.

## 당신의 목표
1. 지원자가 "진짜 그 경험을 했는지" 확인
2. 지원자가 "그 경험에서 뭘 배웠는지" 확인
3. 지원자가 "승무원으로서 써먹을 수 있는지" 확인

## ★★★ 절대 금지: 새로운 정보 요청 ★★★

당신은 "검증"만 합니다. "새 정보 요청"은 절대 하지 마세요!

| ❌ 새 정보 요청 (금지) | ✅ 검증 질문 (해야 할 것) |
|----------------------|-------------------------|
| "어떤 서비스를 제공할 것인가요?" | "자소서에서 말한 서비스를 어떻게 했습니까?" |
| "어떤 사건을 담고 싶은가요?" | "다큐멘터리에서 본인 역할이 뭡니까?" |
| "앞으로 무엇을 하고 싶습니까?" | "이 경험이 왜 승무원에게 필요합니까?" |
| "어떤 계획이 있습니까?" | "자소서에 쓴 방법을 기내에서 쓸 수 있습니까?" |

→ 질문은 반드시 "자소서에 쓴 내용"을 파고들어야 합니다!
→ 지원자의 "미래 의향"이나 "새로운 아이디어"를 묻지 마세요!

## ★ 최우선 규칙: 자소서에 있는 건 묻지 마!

자소서 원문을 읽고, 이미 답이 있는 질문은 절대 하지 마세요.

| 자소서 내용 | ❌ 나쁜 질문 | ✅ 좋은 질문 |
|------------|-------------|-------------|
| "코치와 함께 기준을 정했다" | "누가 기준을 정했습니까?" | "코치 없이 혼자라면 달랐습니까?" |
| "참여율이 회복되었다" | "참여율이 올랐습니까?" | "몇 퍼센트에서 몇 퍼센트로요?" |
| "설득해서 해결했다" | "어떻게 해결했습니까?" | "끝까지 안 넘어온 사람은요?" |
| "익명 설문을 진행했다" | "설문을 했습니까?" | "설문 응답률이 얼마였습니까?" |

## ★ 8가지 질문 슬롯 (반드시 5개 이상 사용!)

### SLOT_ACTION (역할/행동) - "진짜 본인이 한 건가?"
자소서에 "~했다"가 있으면 → 정확히 뭘 했는지 파고들기
- "본인이 직접 한 게 뭡니까?"
- "아이디어는 누가 냈습니까?"
- "혼자서도 가능했습니까?"
- "가장 먼저 한 행동이 뭡니까?"

### SLOT_CONFLICT (갈등/조율) - "반대는 없었나?"
자소서에 "해결/합의/설득"이 있으면 → 반대 의견 처리 확인
- "반대한 사람은 없었습니까?"
- "끝까지 반대한 사람은 어떻게 했습니까?"
- "의견 충돌 때 누가 양보했습니까?"
- "갈등이 다시 생기진 않았습니까?"

### SLOT_CRITERIA (기준/원칙) - "왜 그 방법이었나?"
자소서에 "기준/방식/방법"이 있으면 → 선택 근거 확인
- "왜 그 방식을 선택했습니까?"
- "다른 방법은 왜 안 했습니까?"
- "그 기준이 틀렸을 가능성은요?"
- "기준에 불만인 사람은 없었습니까?"

### SLOT_RESULT (결과/성과) - "진짜 효과가 있었나?"
자소서에 "좋아졌다/개선/회복/성과"가 있으면 → 수치 요구
- "숫자로 말하면 얼마입니까?"
- "전과 후가 어떻게 달랐습니까?"
- "그걸 어떻게 측정했습니까?"
- "다른 사람도 인정했습니까?"

### SLOT_ALTERNATIVE (대안/한계) - "실패 가능성은?"
모든 자소서에 적용 → 플랜B, 한계 확인
- "그 방법이 안 통했으면요?"
- "실패한 적은 없습니까?"
- "다시 해도 똑같이 하겠습니까?"
- "후회되는 부분은 없습니까?"

### SLOT_JOB (직무연결) - "승무원이랑 무슨 상관?"
반드시 구체적 상황 명시! "유사한 상황" 금지!
- "기내에서 승객끼리 다투면 같은 방식 쓰겠습니까?"
- "비행 중 팀원 갈등이 생기면 어떻게 하겠습니까?"
- "승무원한테 이 경험이 왜 필요합니까?"
- "기내에서 불가능한 방법이면 어떻게 하겠습니까?"

### SLOT_ALIGNMENT (문항 의도 재확인) - "문항이 물은 건 그게 아닌데?" ★NEW
자소서가 문항 요구를 벗어났을 때 → 본래 의도 다시 질문
- "문항에서 X를 물었는데, 왜 Y 얘기입니까?"
- "협업 경험을 물었는데, 본인이 한 협업이 뭡니까?"
- "포부를 물었는데, 입사 후 계획이 뭡니까?"
- "문항 의도에 맞는 경험이 따로 있습니까?"

### SLOT_EVIDENCE (증거/사례 요구) - "그걸 증명할 순간이 있습니까?" ★NEW
추상적 주장에 대해 → 구체적 증거/순간 요구
- "그걸 보여준 구체적 순간이 뭡니까?"
- "다른 사람도 인정한 사례가 있습니까?"
- "기록이나 결과물이 남아있습니까?"
- "제3자가 확인할 수 있는 증거가 뭡니까?"

## 질문 품질 체크리스트

질문 만들기 전에 체크하세요:
□ 이 질문의 답이 자소서에 이미 있나? → 있으면 삭제
□ 40자가 넘나? → 넘으면 줄이기
□ "유사한/이러한/그러한"이 있나? → 있으면 구체화
□ 지원자를 당황하게 할 수 있나? → 못하면 더 날카롭게
□ 예/아니오로 피할 수 있나? → 피할 수 있으면 다시 작성

## 어미 규칙 (FLYREADY 스타일) ★매우 중요★

✅ 반드시 이 어미만 사용:
- "~입니까?" (사실 확인)
- "~뭡니까?" (구체화)
- "~없습니까?" (반례)
- "~있습니까?" (존재)
- "~했습니까?" (과거)
- "~겠습니까?" (가정)

❌ 절대 금지 (이 어미 쓰면 탈락!):
- "~나요?" "~가요?" "~인가요?" → 탈락!
- "~어요?" "~세요?" "~죠?" → 탈락!
- "설명해주세요", "말씀해주세요" → 탈락!
- "~고 싶은가요?" "~할 것인가요?" → 탈락!
- 50자 초과 질문 → 탈락!

## 꼬리질문 (각 질문에 반드시 포함)
- "그래서 결과가 뭡니까?"
- "실패한 적은 없습니까?"
- "다른 방법은 고려 안 했습니까?"
- "다시 해도 똑같이 합니까?"
- "증거가 있습니까?"
- "그래도 그게 최선이었습니까?"

## 출력 형식 (JSON만)

```json
{
  "questions": [
    {
      "slot": "SLOT_XXX (8개 중 선택: ACTION/CONFLICT/CRITERIA/RESULT/ALTERNATIVE/JOB/ALIGNMENT/EVIDENCE)",
      "type": "TYPE_X (A~E)",
      "target": "검증하려는 의심 포인트 (자소서 원문 참조)",
      "question": "질문 (40자 이내)",
      "why": "이 질문을 하는 이유",
      "followup": "꼬리질문"
    }
  ]
}
```

## ★ TYPE → SLOT 자동 매핑 (필수!)

취약점 유형에 따라 반드시 해당 슬롯을 우선 사용하세요:

| 취약점 유형 | 우선 사용할 슬롯 | 질문 방향 |
|------------|-----------------|----------|
| TYPE_A (논리비약) | SLOT_CRITERIA + SLOT_ACTION | "왜 그렇게 판단?" + "실제로 뭐 했나?" |
| TYPE_B (구체성결여) | SLOT_RESULT + SLOT_ACTION | "숫자로 얼마?" + "직접 한 건?" |
| TYPE_C (경험-역량불일치) | SLOT_ACTION + SLOT_EVIDENCE | "뭐 했는데?" + "증거는?" |
| TYPE_D (문항불일치) | SLOT_ALIGNMENT + SLOT_JOB | "문항 의도 알아?" + "직무연결은?" |
| TYPE_E (검증불가) | SLOT_EVIDENCE + SLOT_ALTERNATIVE | "증거?" + "실패했으면?" |

## 필수 요구사항 ★체크리스트★
1. 최소 5개, 최대 6개 질문 생성
2. 반드시 5개 이상의 서로 다른 슬롯 사용 (8개 중)
3. 같은 슬롯 질문은 최대 1개
4. 40자 초과 질문 금지
5. 자소서에 이미 있는 내용 절대 묻지 말 것
6. "유사한 상황" 같은 모호한 표현 금지
7. TYPE에 맞는 SLOT을 우선 사용할 것 (위 매핑표 참조)
8. ★ 각 질문은 자소서의 "다른 문장/부분"을 공략할 것!
9. ★ 하나의 경험만 반복 공격하지 말 것! (다양한 각도 필요)
10. ★ "~나요?", "~가요?", "~고 싶은" 어미 절대 금지!

## 최종 자문 (질문 생성 후 반드시 체크!)
1. "이 질문들로 이 지원자가 진짜인지 알 수 있나?" → NO면 수정
2. "암기한 답변으로 피할 수 있는 질문은 없나?" → 있으면 수정
3. "TYPE에 맞는 SLOT을 사용했나?" → 아니면 수정
4. "8개 슬롯 중 6개 이상 다르게 사용했나?" → 아니면 추가"""


# ===========================================
# 항공사별 추가 질문 데이터
# ===========================================
AIRLINE_SPECIFIC_PROMPTS = {
    "대한항공": """
## 대한항공 면접 빈출 질문 (적합한 것 추가 선택 가능)
- "Excellence in Flight"가 본인에게 어떤 의미입니까?
- 글로벌 항공사 승무원에게 가장 중요한 역량이 뭡니까?
- 장거리 노선 컨디션 관리 계획이 뭡니까?
- 대한항공 서비스 경험이 있습니까? 인상 깊었던 점이 뭡니까?
""",
    "아시아나항공": """
## 아시아나항공 면접 빈출 질문 (적합한 것 추가 선택 가능)
- "Beautiful People"이 되기 위해 어떤 노력을 합니까?
- 고객 감동 서비스의 정의가 뭡니까?
- 팀워크로 문제를 해결한 경험이 뭡니까?
- 아시아나항공 개선점이 있다면 뭡니까?
""",
    "제주항공": """
## 제주항공 면접 빈출 질문 (적합한 것 추가 선택 가능)
- LCC 승무원 역할이 FSC와 어떻게 다릅니까?
- 빠른 턴어라운드 상황에서 우선순위가 뭡니까?
- "Refresh"가 무슨 의미라고 생각합니까?
- 비용 효율성과 서비스 품질 중 뭐가 더 중요합니까?
""",
    "진에어": """
## 진에어 면접 빈출 질문 (적합한 것 추가 선택 가능)
- "Fun&Young" 브랜드 이미지에 본인이 맞다고 생각합니까?
- 젊은 고객층 응대 경험이 있습니까?
- 대한항공 계열사로서 차별점이 뭡니까?
""",
    "티웨이항공": """
## 티웨이항공 면접 빈출 질문 (적합한 것 추가 선택 가능)
- "Flying with Sincerity"를 어떻게 실천합니까?
- 티웨이항공이 다른 LCC와 차별화된 점이 뭡니까?
- 승무원으로서 "진심"을 어떻게 전달합니까?
""",
    "에어부산": """
## 에어부산 면접 빈출 질문 (적합한 것 추가 선택 가능)
- 아시아나 계열사로서 서비스 기준이 뭡니까?
- 부산/경남 지역 고객 특성을 알고 있습니까?
- LCC지만 FSC 수준 서비스가 가능합니까?
""",
    "에어서울": """
## 에어서울 면접 빈출 질문 (적합한 것 추가 선택 가능)
- 아시아나 계열 LCC로서 어떤 서비스를 제공해야 합니까?
- 단거리 노선 특화 서비스가 뭡니까?
""",
    "에어프레미아": """
## 에어프레미아 면접 빈출 질문 (적합한 것 추가 선택 가능)
- 하이브리드 항공사(HSC)가 뭐라고 생각합니까?
- 프리미엄 이코노미 서비스 차별점이 뭡니까?
- 중장거리 LCC 시장 전망을 어떻게 봅니까?
""",
    "이스타항공": """
## 이스타항공 면접 빈출 질문 (적합한 것 추가 선택 가능)
- 이스타항공 회생 과정을 알고 있습니까?
- 어려운 시기의 항공사에 지원한 이유가 뭡니까?
""",
    "플라이강원": """
## 플라이강원 면접 빈출 질문 (적합한 것 추가 선택 가능)
- 지역 항공사의 역할이 뭐라고 생각합니까?
- 양양국제공항 취항 노선을 알고 있습니까?
""",
    "에어로케이": """
## 에어로케이 면접 빈출 질문 (적합한 것 추가 선택 가능)
- 신생 항공사에 지원한 이유가 뭡니까?
- 청주 기반 항공사로서 성장 가능성을 어떻게 봅니까?
"""
}


# ===========================================
# FLYREADY CLOVA 엔진 클래스
# ===========================================
class FlyreadyClovaEngine:
    """FLYREADY 2회 호출 엔진 v3.1 (8슬롯 + TYPE→SLOT 자동 매핑)"""

    def __init__(self, airline: str = None):
        self.airline = airline
        self.last_analysis = None
        self.last_questions = None
        self.last_analysis_summary = None  # Perfect Interviewer v3.0

    def analyze(self, question: str, answer: str, item_num: int = 2) -> dict:
        """
        메인 분석 함수 (2회 호출)

        Args:
            question: 자소서 문항
            answer: 자소서 답변
            item_num: 문항 번호 (기본값 2 = 문항2만 분석)

        Returns:
            {
                "vulnerabilities": [...],
                "questions": [...],
                "raw_analysis": "1차 분석 원문",
                "raw_questions": "2차 생성 원문"
            }
        """
        print(f"\n[FLYREADY ENGINE] 분석 시작 (항공사: {self.airline})")
        start_time = time.time()

        # ========== 1차 호출: 취약점 분석 ==========
        print("[1차 호출] 취약점 분석 중...")
        analysis_result = self._call_analysis(question, answer)

        if not analysis_result:
            print("[1차 호출] 실패 - 폴백 모드")
            return self._fallback_result()

        # 파싱
        vulnerabilities = self._parse_vulnerabilities(analysis_result)
        self.last_analysis = analysis_result

        print(f"[1차 호출] 완료 - {len(vulnerabilities)}개 취약점 발견")

        if not vulnerabilities:
            print("[1차 호출] 취약점 없음 - 폴백 모드")
            return self._fallback_result()

        # Rate limit 방지
        time.sleep(0.3)

        # ========== 2차 호출: 질문 생성 (재시도 로직 포함) ==========
        validated_questions = []
        max_retries = 2

        for attempt in range(max_retries):
            print(f"[2차 호출] 질문 생성 중... (시도 {attempt + 1}/{max_retries})")
            questions_result = self._call_question_gen(question, answer, vulnerabilities)

            if not questions_result:
                print(f"[2차 호출] 시도 {attempt + 1} 실패")
                continue

            questions = self._parse_questions(questions_result)
            self.last_questions = questions_result

            print(f"[2차 호출] 파싱 완료 - {len(questions)}개 질문")

            # 후처리: 긴 질문 자동 축약
            processed_questions = self._post_process_questions(questions)

            # 품질 검증
            validated_questions = self._validate_questions(processed_questions)

            print(f"[2차 호출] 검증 통과 - {len(validated_questions)}개 질문")

            # 4개 이상이면 성공
            if len(validated_questions) >= 4:
                break

            # 부족하면 재시도
            print(f"[2차 호출] 질문 부족 ({len(validated_questions)}개) - 재시도")
            time.sleep(0.3)

        # 여전히 부족하면 폴백 질문으로 보충
        if len(validated_questions) < 4:
            print(f"[2차 호출] 최종 {len(validated_questions)}개 - 폴백으로 보충")
            validated_questions = self._supplement_with_fallback(validated_questions)

        total_time = time.time() - start_time
        print(f"[FLYREADY ENGINE] 완료 ({total_time:.1f}초, 최종 {len(validated_questions)}개 질문)")

        return {
            "vulnerabilities": vulnerabilities,
            "questions": validated_questions,
            "raw_analysis": analysis_result,
            "raw_questions": questions_result,
            "processing_time": total_time
        }

    def _call_analysis(self, question: str, answer: str) -> Optional[str]:
        """1차 호출: 취약점 분석"""
        user_prompt = f"""[문항]
{question}

[답변]
{answer}

위 자소서에서 취약점을 찾아주세요. 최대 3개까지만. 반드시 JSON 형식으로 출력하세요."""

        return self._call_clova(SYSTEM_PROMPT_ANALYSIS, user_prompt, temperature=0.2, max_tokens=1000)

    def _call_question_gen(self, question: str, answer: str, vulnerabilities: list) -> Optional[str]:
        """2차 호출: 질문 생성 (TYPE→SLOT 자동 매핑 적용)"""

        # 취약점 텍스트로 변환 (권장 슬롯 포함!)
        vuln_lines = []
        for v in vulnerabilities:
            v_type = v.get('type', 'TYPE_E')
            recommended_slots = TYPE_TO_SLOTS.get(v_type, ["SLOT_ACTION", "SLOT_EVIDENCE"])
            slot_hint = " + ".join(recommended_slots)
            vuln_lines.append(
                f"- {v_type}: \"{v['original']}\" → {v['problem']} [권장슬롯: {slot_hint}]"
            )
        vuln_text = "\n".join(vuln_lines)

        # 항공사별 추가 프롬프트
        system_prompt = SYSTEM_PROMPT_QUESTION_GEN
        if self.airline and self.airline in AIRLINE_SPECIFIC_PROMPTS:
            system_prompt += "\n\n" + AIRLINE_SPECIFIC_PROMPTS[self.airline]

        # FLYREADY 데이터에서 항공사별 질문 추가
        if self.airline:
            airline_questions = get_airline_question_list(self.airline)
            if airline_questions and len(airline_questions) > 0:
                sample_qs = airline_questions[:10]  # 상위 10개만
                qs_text = "\n".join([f"- {q}" for q in sample_qs])
                system_prompt += f"\n\n## {self.airline} 실제 기출 질문 참고\n{qs_text}"

        user_prompt = f"""[자소서 원문]
문항: {question}
답변: {answer}

[1차 분석에서 발견된 취약점]
{vuln_text}

위 취약점들에 대한 면접 질문 6개를 생성해주세요.
각 취약점마다 서로 다른 템플릿을 사용하여 2개씩 질문하세요.
반드시 제공된 템플릿에서 선택하여 구체화하세요.
반드시 JSON 형식으로 출력하세요."""

        return self._call_clova(system_prompt, user_prompt, temperature=0.35, max_tokens=2500)

    def _call_clova(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 1500) -> Optional[str]:
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

            response = requests.post(endpoint, headers=headers, json=payload, timeout=90)

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

    def _parse_vulnerabilities(self, text: str) -> list:
        """취약점 파싱 (JSON) - Perfect Interviewer v3.0"""
        vulnerabilities = []

        try:
            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                data = json.loads(json_match.group())

                # 분석 결과 저장 (새 구조)
                analysis = data.get("analysis", {})
                if analysis:
                    self.last_analysis_summary = {
                        "situation": analysis.get("situation", ""),
                        "claimed_role": analysis.get("claimed_role", ""),
                        "actual_actions": analysis.get("actual_actions", []),
                        "results": analysis.get("results", ""),
                        "missing_info": analysis.get("missing_info", [])
                    }
                    print(f"[분석] 상황: {self.last_analysis_summary['situation']}")
                    print(f"[분석] 역할: {self.last_analysis_summary['claimed_role']}")
                    print(f"[분석] 빠진 정보: {self.last_analysis_summary['missing_info']}")

                vulns = data.get("vulnerabilities", [])

                for v in vulns[:4]:  # 최대 4개로 증가
                    vulnerabilities.append({
                        "type": v.get("type", "TYPE_E"),
                        "original": v.get("original", "")[:50],
                        "problem": v.get("problem", ""),
                        "question_angle": v.get("question_angle", "")  # 질문 각도 추가
                    })
        except Exception as e:
            print(f"[PARSE ERROR] 취약점 파싱 실패: {e}")

            # 폴백: 텍스트 패턴 매칭
            pattern = r'TYPE_([A-E]).*?["\']([^"\']+)["\'].*?(?:문제|problem)[:\s]*([^\n]+)'
            matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

            for match in matches[:4]:
                vulnerabilities.append({
                    "type": f"TYPE_{match[0]}",
                    "original": match[1].strip()[:50],
                    "problem": match[2].strip(),
                    "question_angle": ""
                })

        return vulnerabilities

    def _parse_questions(self, text: str) -> list:
        """질문 파싱 (JSON)"""
        questions = []

        try:
            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                data = json.loads(json_match.group())
                qs = data.get("questions", [])

                for q in qs[:6]:  # 최대 6개 (버전 반복 방지)
                    questions.append({
                        "type": q.get("type", "TYPE_E"),
                        "slot": q.get("slot", "SLOT_ACTION"),
                        "question": q.get("question", ""),
                        "target": q.get("target", ""),  # 검증 대상
                        "why": q.get("why", ""),  # 질문 이유
                        "intent": q.get("intent", q.get("why", "")),  # 하위호환
                        "followup": q.get("followup", "그래서 결과가 뭡니까?")
                    })
        except Exception as e:
            print(f"[PARSE ERROR] 질문 파싱 실패: {e}")

            # 폴백: 텍스트 패턴 매칭
            pattern = r'질문[:\s]*["\']([^"\']+)["\']'
            matches = re.findall(pattern, text)

            for i, match in enumerate(matches[:6]):  # 폴백도 최대 6개
                # 폴백에도 슬롯 다양성 부여 (8슬롯 시스템)
                questions.append({
                    "type": "TYPE_E",
                    "slot": ALL_SLOTS[i % len(ALL_SLOTS)],
                    "question": match.strip(),
                    "intent": "검증",
                    "followup": "그래서 결과가 뭡니까?"
                })

        return questions

    def _validate_questions(self, questions: list) -> list:
        """질문 품질 검증 및 수정 (v3.1 강화)"""
        validated = []

        for q in questions:
            question_text = q.get("question", "")

            # ========== 1. 금지 패턴 체크 (강화) ==========
            forbidden = [
                # 모호한 표현
                "이러한 ", "그러한 ", "이런 ", "그런 ", "유사한 ",
                # 요청형
                "설명해", "말씀해", "알려주",
                # 의견형 (검증이 아님)
                "어떻게 생각", "어떤 의미", "무엇이라고 생각",
            ]
            has_forbidden = any(f in question_text for f in forbidden)
            if has_forbidden:
                print(f"[검증 실패] 금지 패턴: {question_text[:40]}...")
                continue

            # ========== 2. 비격식 어미 차단 (강화) ==========
            informal_endings = ["나요?", "가요?", "인가요?", "죠?", "어요?", "세요?", "ㄴ가요?", "은가요?"]
            has_informal = any(question_text.endswith(e) for e in informal_endings)
            if has_informal:
                print(f"[검증 실패] 비격식 어미: {question_text[:40]}...")
                continue

            # ========== 3. 새 질문 유발 표현 차단 (NEW!) ==========
            # "자소서 검증"이 아니라 "새 정보 요청"하는 질문 패턴
            new_question_patterns = [
                "고 싶은",      # "~하고 싶은가요?" → 미래 의향 (검증 아님)
                "고 싶습니까",  # 같은 패턴
                "할 것인가요",  # "어떤 서비스를 제공할 것인가요?" → 미래 계획 (검증 아님)
                "할 것입니까",
                "하실 것",
                "어떤 특정",    # "어떤 특정 사건을?" → 새 정보 요청
                "무엇을 ",      # "무엇을 담고 싶은가요?" → 새 정보 요청
                "어떤 서비스",  # 직무연결이 아닌 막연한 질문
                "어떤 계획",
                "어떤 목표",
            ]
            has_new_question = any(p in question_text for p in new_question_patterns)
            if has_new_question:
                print(f"[검증 실패] 새 질문 유발: {question_text[:40]}...")
                continue

            # ========== 4. 길이 체크 ==========
            if len(question_text) > 50:
                print(f"[검증 실패] 질문 너무 김 ({len(question_text)}자): {question_text[:40]}...")
                continue

            # ========== 5. 복잡한 구조 체크 ==========
            awkward_patterns = ["사례는 무엇입니까", "실질적으로 도움이", "구체적으로 어떤 방식으로"]
            has_awkward = any(p in question_text for p in awkward_patterns)
            if has_awkward:
                print(f"[검증 실패] 어색한 구조: {question_text[:40]}...")
                continue

            # ========== 6. 어미 체크 ==========
            valid_endings = ["입니까?", "뭡니까?", "없습니까?", "있습니까?", "했습니까?", "됩니까?", "됐습니까?", "겠습니까?"]
            has_valid_ending = any(question_text.endswith(e) for e in valid_endings)

            if not has_valid_ending:
                # 어미가 "?"로 끝나지만 유효하지 않으면 제외 (비격식일 가능성)
                if question_text.endswith("?"):
                    # "~요?" 패턴이면 제외
                    if question_text.endswith("요?"):
                        print(f"[검증 실패] 비격식 ~요? 어미: {question_text[:40]}...")
                        continue
                else:
                    question_text = question_text.rstrip(".") + "?"
                    q["question"] = question_text

            validated.append(q)

        return validated

    def _post_process_questions(self, questions: list) -> list:
        """질문 후처리: 긴 질문 자동 축약"""
        processed = []

        for q in questions:
            question_text = q.get("question", "")

            # 50자 초과 시 축약 시도
            if len(question_text) > 50:
                shortened = self._shorten_question(question_text)
                if shortened:
                    q["question"] = shortened
                    print(f"[후처리] 축약: {question_text[:30]}... → {shortened[:30]}...")

            # "~하셨는데" 패턴 단순화
            if "하셨는데," in question_text:
                # "A하셨는데, B입니까?" → "A요? B입니까?" 또는 "B입니까?"
                parts = question_text.split("하셨는데,")
                if len(parts) == 2 and len(parts[1].strip()) > 5:
                    simplified = parts[1].strip()
                    if not simplified[0].isupper() and simplified[0] != '"':
                        simplified = simplified[0].upper() + simplified[1:] if len(simplified) > 1 else simplified
                    q["question"] = simplified
                    print(f"[후처리] 단순화: {question_text[:30]}... → {simplified[:30]}...")

            processed.append(q)

        return processed

    def _shorten_question(self, question: str) -> str:
        """긴 질문을 50자 이내로 축약"""
        # 불필요한 수식어 제거
        remove_phrases = [
            "구체적으로 ", "실질적으로 ", "정확히 ", "실제로 ",
            "그것이 ", "이것이 ", "그래서 ", "따라서 ",
            "에 대해 ", "에 대한 ", "으로서 ", "로서 "
        ]

        shortened = question
        for phrase in remove_phrases:
            shortened = shortened.replace(phrase, "")

        # 여전히 길면 앞부분 + 핵심 질문만
        if len(shortened) > 50:
            # 마지막 질문 부분만 추출 (? 앞의 마지막 절)
            if "," in shortened:
                parts = shortened.rsplit(",", 1)
                if len(parts[1].strip()) >= 10:
                    shortened = parts[1].strip()

        return shortened if len(shortened) <= 50 else None

    def _supplement_with_fallback(self, questions: list) -> list:
        """부족한 질문을 폴백으로 보충하여 최소 4개 보장 (8슬롯 시스템)"""
        fallback_pool = [
            {"type": "FALLBACK", "slot": "SLOT_ACTION", "question": "본인의 강점이 뭡니까?", "intent": "강점 확인", "followup": "증명할 사례가 있습니까?"},
            {"type": "FALLBACK", "slot": "SLOT_ACTION", "question": "그 경험에서 본인 역할이 뭡니까?", "intent": "역할 확인", "followup": "혼자 한 부분은요?"},
            {"type": "FALLBACK", "slot": "SLOT_JOB", "question": "승무원 업무에 어떻게 적용됩니까?", "intent": "직무 연결", "followup": "기내에서도 가능합니까?"},
            {"type": "FALLBACK", "slot": "SLOT_ALTERNATIVE", "question": "실패한 적 없습니까?", "intent": "한계 탐색", "followup": "어떻게 극복했습니까?"},
            {"type": "FALLBACK", "slot": "SLOT_RESULT", "question": "숫자로 말하면 얼마입니까?", "intent": "수치 검증", "followup": "다른 사람과 비교하면요?"},
            # 새 슬롯 (v3.1)
            {"type": "FALLBACK", "slot": "SLOT_ALIGNMENT", "question": "문항이 원한 답변이 이겁니까?", "intent": "문항 의도 확인", "followup": "더 적합한 경험은 없습니까?"},
            {"type": "FALLBACK", "slot": "SLOT_EVIDENCE", "question": "그걸 증명할 증거가 있습니까?", "intent": "증거 요구", "followup": "제3자도 확인 가능합니까?"},
            {"type": "FALLBACK", "slot": "SLOT_CONFLICT", "question": "반대한 사람은 없었습니까?", "intent": "갈등 탐색", "followup": "끝까지 반대한 사람은요?"},
        ]

        result = list(questions)  # 기존 질문 복사
        fallback_idx = 0

        # 4개 이상이 될 때까지 폴백 추가
        while len(result) < 6 and fallback_idx < len(fallback_pool):
            # 중복 체크
            fallback_q = fallback_pool[fallback_idx]
            is_duplicate = any(fallback_q["question"] in q.get("question", "") for q in result)

            if not is_duplicate:
                result.append(fallback_q)
                print(f"[보충] 폴백 추가: {fallback_q['question'][:30]}...")

            fallback_idx += 1

        return result

    def _fallback_result(self, vulnerabilities: list = None) -> dict:
        """분석 실패 시 폴백 결과 (8슬롯 시스템)"""
        fallback_questions = [
            {
                "type": "FALLBACK",
                "slot": "SLOT_ACTION",
                "question": "본인의 강점이 뭡니까?",
                "intent": "강점 확인",
                "followup": "증명할 사례가 있습니까?"
            },
            {
                "type": "FALLBACK",
                "slot": "SLOT_CONFLICT",
                "question": "팀워크 때문에 손해 본 적 없습니까?",
                "intent": "역방향 검증",
                "followup": "그래도 팀워크가 중요합니까?"
            },
            {
                "type": "FALLBACK",
                "slot": "SLOT_CRITERIA",
                "question": "왜 그 방식을 선택했습니까?",
                "intent": "판단 기준 확인",
                "followup": "다른 방법은 왜 안 했습니까?"
            },
            {
                "type": "FALLBACK",
                "slot": "SLOT_RESULT",
                "question": "숫자로 말하면 얼마입니까?",
                "intent": "수치 검증",
                "followup": "다른 사람과 비교하면요?"
            },
            {
                "type": "FALLBACK",
                "slot": "SLOT_ALTERNATIVE",
                "question": "후회한 적 없습니까?",
                "intent": "선택 검증",
                "followup": "다시 해도 같은 선택입니까?"
            },
            {
                "type": "FALLBACK",
                "slot": "SLOT_JOB",
                "question": "승무원 업무에 어떻게 적용됩니까?",
                "intent": "직무 연결",
                "followup": "기내에서도 가능합니까?"
            },
            {
                "type": "FALLBACK",
                "slot": "SLOT_ALIGNMENT",
                "question": "문항이 원한 답변이 이겁니까?",
                "intent": "문항 의도 확인",
                "followup": "더 적합한 경험은 없습니까?"
            },
            {
                "type": "FALLBACK",
                "slot": "SLOT_EVIDENCE",
                "question": "그걸 증명할 증거가 있습니까?",
                "intent": "증거 요구",
                "followup": "제3자도 확인 가능합니까?"
            }
        ]

        return {
            "vulnerabilities": vulnerabilities or [],
            "questions": fallback_questions,
            "raw_analysis": None,
            "raw_questions": None,
            "processing_time": 0,
            "is_fallback": True
        }


# ===========================================
# 편의 함수
# ===========================================
def analyze_resume_with_flyready(
    question: str,
    answer: str,
    airline: str = None,
    item_num: int = 2
) -> dict:
    """
    FLYREADY 엔진으로 자소서 분석 (외부 호출용)

    Args:
        question: 자소서 문항
        answer: 자소서 답변
        airline: 항공사명 (선택)
        item_num: 문항 번호 (기본값 2)

    Returns:
        분석 결과 딕셔너리
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
    print(f"취약점: {len(result['vulnerabilities'])}개")
    for v in result['vulnerabilities']:
        print(f"  - {v['type']}: {v['original'][:30]}...")

    print(f"\n질문: {len(result['questions'])}개")
    for q in result['questions']:
        print(f"  - [{q['type']}] {q['question']}")
        print(f"    → 꼬리: {q['followup']}")
