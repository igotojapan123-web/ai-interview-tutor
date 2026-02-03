# -*- coding: utf-8 -*-
"""
프리미엄 자소서 분석 - 면접관 시선으로 완벽 분석
"""

import os
import json
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PREMIUM_ANALYSIS_PROMPT = """당신은 10년차 항공사 면접관입니다. 수천 명의 지원자를 면접한 경험이 있습니다.
지원자의 자소서를 읽고, 실제 면접에서 검증하고 싶은 포인트를 분석하세요.

## 자소서 문항
{question}

## 지원자 답변
{answer}

---

## 분석 프레임워크

### STEP 1: 전체 스토리 파악
이 지원자가 이 답변을 통해 **진짜 전달하고 싶은 메시지**는 무엇인가?
- 표면적 메시지 vs 숨겨진 메시지
- 지원자가 자신을 어떻게 포지셔닝하고 있는가?

### STEP 2: 면접관으로서 눈에 띄는 점
**강점 (믿고 싶은 부분):**
- 구체적 경험이 있는가?
- 진정성이 느껴지는가?
- 승무원 직무와 연결되는가?

**의문점 (검증하고 싶은 부분):**
- 추상적이거나 미화된 표현은?
- 빠진 디테일은?
- "정말?" 하고 의심되는 부분은?

**약점 (파고들 구멍):**
- 논리적 비약은?
- 반례를 제시할 수 있는 부분은?
- 실제 상황에서 무너질 수 있는 주장은?

### STEP 3: 핵심 문장 3개 선정
면접관이 **반드시 파고들어야 할** 핵심 문장 3개를 선정하세요.

선정 기준:
1. **검증 가치가 높은 문장** - 이게 사실이면 큰 강점, 거짓이면 큰 문제
2. **추상적이어서 구체화가 필요한 문장** - "좋은 말"인데 실체가 불분명
3. **승무원 직무와 직결되는 문장** - 실제 업무 상황과 연결 가능

각 핵심 문장에 대해:
- 왜 이 문장을 선택했는지 (면접관 시선)
- 이 문장의 **함정** (지원자가 답변하기 어려운 포인트)
- 서브 포인트 3개 (이 문장과 연결된 다른 표현들)

### STEP 4: 실전 면접 질문 5개
실제 면접에서 사용할 **날카롭고 구체적인** 질문 5개를 만드세요.

질문 설계 원칙:
- **1번 질문**: 웜업 - 부드럽게 시작하되 핵심을 찌르는 질문
- **2번 질문**: 구체화 - "예를 들면?", "구체적으로?"
- **3번 질문**: 검증 - "정말 그랬나요?", "본인 역할은?"
- **4번 질문**: 압박 - 반례, 한계, 실패 경험
- **5번 질문**: 적용 - "승무원으로서 어떻게?"

질문 작성 규칙:
- 짧고 직접적 (1문장, 최대 2문장)
- "~에 대해 말씀해 주세요" 같은 열린 질문 금지
- 지원자가 **구체적 사실**로 답할 수밖에 없는 질문
- 준비된 답변이 아닌 **즉석 사고**를 요구하는 질문

---

## JSON 출력 형식
{{
  "story_analysis": {{
    "main_message": "지원자가 전달하려는 핵심 메시지 (1문장)",
    "positioning": "지원자가 자신을 어떻게 포지셔닝하는지 (1문장)",
    "strengths": ["강점1", "강점2"],
    "doubts": ["의문점1", "의문점2"],
    "weaknesses": ["약점/구멍1", "약점/구멍2"]
  }},
  "key_sentences": [
    {{
      "sentence": "핵심문장 원문 (자르지 말 것)",
      "type": "검증필요/구체화필요/직무연결",
      "interviewer_note": "면접관이 이 문장을 선택한 이유",
      "trap": "이 문장의 함정 (답변하기 어려운 포인트)",
      "sub_points": ["서브1", "서브2", "서브3"]
    }}
  ],
  "interview_questions": [
    {{
      "number": 1,
      "question": "면접 질문",
      "intent": "이 질문의 숨은 의도",
      "expected_trap": "지원자가 빠질 수 있는 함정"
    }}
  ],
  "overall_assessment": "이 답변에 대한 면접관의 총평 (2-3문장)"
}}
"""

def analyze_premium(question: str, answer: str) -> dict:
    prompt = PREMIUM_ANALYSIS_PROMPT.format(question=question, answer=answer)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 10년차 항공사 면접관입니다. 날카롭고 전문적인 시선으로 분석하세요. JSON 형식으로만 응답하세요."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


def print_premium_analysis(result: dict, title: str):
    print("\n")
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)

    # 스토리 분석
    story = result.get("story_analysis", {})
    print("\n[STORY ANALYSIS - 면접관의 첫인상]")
    print("-" * 70)
    print(f"  핵심 메시지: {story.get('main_message', '')}")
    print(f"  포지셔닝: {story.get('positioning', '')}")

    print(f"\n  [+] 강점:")
    for s in story.get("strengths", []):
        print(f"      - {s}")

    print(f"\n  [?] 의문점 (검증 필요):")
    for d in story.get("doubts", []):
        print(f"      - {d}")

    print(f"\n  [-] 약점/구멍:")
    for w in story.get("weaknesses", []):
        print(f"      - {w}")

    # 핵심 문장
    print("\n")
    print("[KEY SENTENCES - 반드시 파고들 문장]")
    print("-" * 70)

    for i, ks in enumerate(result.get("key_sentences", []), 1):
        print(f"\n  [{i}] ({ks.get('type', '')})")
        print(f"  \"{ks.get('sentence', '')}\"")
        print(f"\n      면접관 메모: {ks.get('interviewer_note', '')}")
        print(f"      함정: {ks.get('trap', '')}")
        print(f"\n      서브 포인트:")
        for j, sub in enumerate(ks.get("sub_points", []), 1):
            print(f"        {j}. {sub}")

    # 면접 질문
    print("\n")
    print("[INTERVIEW QUESTIONS - 실전 질문]")
    print("-" * 70)

    for q in result.get("interview_questions", []):
        num = q.get("number", "")
        print(f"\n  Q{num}. \"{q.get('question', '')}\"")
        print(f"      [의도] {q.get('intent', '')}")
        print(f"      [함정] {q.get('expected_trap', '')}")

    # 총평
    print("\n")
    print("[OVERALL - 면접관 총평]")
    print("-" * 70)
    print(f"  {result.get('overall_assessment', '')}")
    print("\n")


if __name__ == "__main__":
    # 문항 1
    question1 = """동료 승무원들이 함께 근무하고 싶어하는 승무원이 되기 위해,
본인이 중요하게 생각하는 것은 무엇이며,
이를 위해 어떤 노력을 하고 있나요?"""

    answer1 = """전반적인 인생에 걸쳐 사람들과 같이 더불어 살 수 밖에 없습니다. 그렇기에 팀워크가 제일 중요하다고 생각합니다.
저는 16살이라는 나이에 중국 칭다오로 홀로 유학을 가게되었습니다.
타국에 홀로 떨어져서 기숙사 생활을 하니 말이 통하지 않는 무서움, 의지할 사람 없이 혼자 헤쳐나가야 한다는 부담감을 처음 느껴봤습니다.
하지만 기숙사에는 저와 같이 가족들과 떨어져서 홀로 유학을 온 사람들이 있었고 이 몇몇 사람들과 저는 함께 중국어 공부를 통해서 중국 생활에 적응하려고 노력했고, 중국어 공부를 비롯해 학교에서 배우는 경제학 수업이나 ACT 수업 등등 서로 부족한 부분을 채워주며 학교 생활도 같이 적응하려고 노력했습니다.
그렇기에 서로 더 의지하며 타지 생활의 외로움을 달랬습니다. 저는 실제로 홀로 중국에 유학을 갔을 때 향수병이 무엇인지 느껴봤고, 극복해본 결과 혼자였으면 절대 극복하지 못할 것들을 공동체 속에 함께 있으니 극복할 수 있었던 경험이 있습니다. 저의 이러한 경험들이 저에게 하여금 사람들과 공동체 속에서 어울릴 때의 가치와 공동체 의식의 중요성 그리고 더불어 살아가는 것이 무엇인지를 깨닫게 해주었습니다.
그래서 저는 많은 운동중에서도 축구라는 스포츠를 제일 선호합니다. 축구라는 스포츠는 11명이서 합을 맞추어 진행되는 스포츠입니다. 11명 중 한명만 정말 특출나게 잘한다고 하더라도 모든 경기에서 승리할 수는 없습니다,
그렇기에 축구에는 팀컬러 라는것이 존재하며 각 팀마다 팀컬러가 다릅니다. 저는 현재 세명대학교 항공서비스학과 축구 동아리 나르샤의 주장으로써 정말 잘하는 강팀을 만든다기 보다는 정말 축구를 잘 하지는 못하지만 좋아하는 인원도 같이 웃으면서 축구경기를 할 수 있는 환경을 조성하였습니다."""

    # 문항 2
    question2 = """자신의 인생을 한 편의 영화로 제작한다면,
어떤 장르와 제목으로 표현하고 싶으며 그 이유는 무엇인가요?"""

    answer2 = """저는 제 안생을 영화로 만든다면, 그 장르는 다큐멘터리일 것입니다,
왜냐하면 지금까지의 제 삶은 화려하거나 극적인 반전이 있는 영화나 드라마라기보다는, 작은 선택과 경험들이 차곡차곡 쌓이며 지금의 저를 만들어온 현실적인 여정의 기록이기 때문입니다. 다큐멘터리같은 제 삶은 한 장면 한 장면이 의미 있는 선택과 성장의 연속이었고, 그것이 저로 하여금 지금 현재의 나를 만들어주었기 때문입니다.
제 영화제목은 《初航：梦想的起点》 (첫 비행: 꿈의 시작점)입니다.
제 인생에서 가장 큰 전환점은 중학생 때의 홀로 떠난 중국 유학 경험이였습니다. 그 당시 혼자 비행기에 올라 낯선 나라로 향하는 비행기에 몸을 실었던 순간, 설렘과 동시에 막연한 두려움도 함께 느꼈습니다. 하지만 매번 비행기를 탈 때마다 승무원 분들의 따뜻한 미소와 승객분들을 향한 섬세한 배려는 저에게 큰 안정감을 주었고, 어느 순간부터 그들의 모습이 제 눈에 하나의 '이상적인 직업'으로 보이기 시작했습니다.
그 이후로 저에게 있어서 비행은 단순한 이동 수단이 아니라, 새로운 환경에 도전하고 성장해가는 여정을 상징하는 경험이 되었습니다. 그 여정 속에서 다양한 문화와 언어를 경험하고, 동시에 넓은 시야와 열린 마음을 가지게 되었습니다. 그리고 자연스럽게 저도 저를 반겨주었던 그 승무원분 처럼 '나도 언젠가 누군가의 첫 여정을 따뜻하게 맞이하는 사람이 되고 싶다'는 꿈을 품게 되었습니다.
이 영화는 저의 성장과 변화, 그리고 꿈을 향한 노력의 과정을 진솔하게 담은 하나의 다큐멘터리 입니다. 그리고 지금 저는 그 다음 장면, 바로 하늘 위에서 고객의 안전과 편안함을 책임지는 승무원으로서의 새로운 장을 준비하고 있습니다. 이 다큐멘터리가 계속될 수 있도록 , 저는 앞으로도 끊임없이 배우고 도전하며, 누군가의 여행에 따뜻한 기억을 남겨줄 수 있는 그런 승무원이 되고싶습니다."""

    print("\n")
    print("#" * 70)
    print("#  PREMIUM RESUME ANALYSIS - 면접관 시선 완벽 분석")
    print("#" * 70)

    result1 = analyze_premium(question1, answer1)
    print_premium_analysis(result1, "문항 1: 함께 근무하고 싶은 승무원")

    result2 = analyze_premium(question2, answer2)
    print_premium_analysis(result2, "문항 2: 인생을 영화로 표현한다면")
