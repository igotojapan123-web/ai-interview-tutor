"""
deep_questions 생성 테스트 스크립트
LLM이 새 프롬프트에서 deep_questions를 제대로 생성하는지 확인
"""
import os
import json
import requests

# API 설정
api_key = os.getenv("OPENAI_API_KEY") or ""
if not api_key:
    print("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    exit(1)

# 테스트 자소서 (에어로케이 예시)
test_question = "동료 승무원들이 함께 근무하고 싶어하는 승무원이 되기 위해, 본인이 중요하게 생각하는 것은 무엇이며, 이를 위해 어떤 노력을 하고 있나요?"
test_answer = """저는 팀워크가 제일 중요하다고 생각합니다. 16살이라는 나이에 중국 칭다오로 홀로 유학을 떠났을 때, 혼자였으면 절대 극복하지 못할 것들을 공동체 속에 함께 있으니 극복할 수 있었습니다. 대학교에서 축구 동아리 활동을 하면서도 잘하는 강팀보다 못해도 함께 웃으면서 할 수 있는 환경을 조성하는 것이 더 좋은 결과를 가져온다는 것을 배웠습니다. 팀컬러라는 것이 존재하며, 좋은 팀컬러를 만들기 위해 항상 먼저 다가가고 소통하려고 노력하고 있습니다."""

# 단순화된 프롬프트 (deep_questions만 집중)
simple_prompt = f"""당신은 항공사 면접관입니다. 아래 자소서를 읽고 심층 면접 질문을 생성하세요.

## 자소서 문항
{test_question}

## 지원자 답변
{test_answer}

---

## 핵심문장 추출 및 질문 생성

답변에서 면접관이 파고들 핵심문장을 3개 찾고, 각각에 대해 심층 질문을 만드세요.

### 핵심문장 유형
1. 가치선언: "팀워크가 제일 중요하다고 생각합니다"
2. 경험제시: "16살에 중국으로 유학을 갔습니다"
3. 깨달음: "공동체 속에서 극복할 수 있었습니다"
4. 실천사례: "함께 웃는 환경을 조성했습니다"
5. 개념사용: "팀컬러라는 것이 존재합니다"

### 좋은 질문 예시
핵심문장: "팀워크가 제일 중요하다고 생각합니다"
좋은 질문: "팀워크가 제일 중요하다고 하셨는데, 팀워크가 안 되는 동료와 비행해야 한다면 어떻게 하시겠습니까?"

### 예상 답변 + 꼬리질문 예시
- 예상답변: "대화로 풀겠습니다" → 꼬리: "대화해도 안 바뀌면요?"
- 예상답변: "제가 먼저 맞추겠습니다" → 꼬리: "계속 맞추기만 하면 지치지 않습니까?"

---

## JSON 출력 (반드시 이 형식으로)
{{
  "deep_questions": [
    {{
      "source_sentence": "핵심문장 원문",
      "sentence_type": "가치선언/경험제시/깨달음/실천사례/개념사용",
      "question": "심층 면접 질문",
      "expected_answers": [
        {{"answer": "예상 답변 1", "followup": "꼬리질문 1"}},
        {{"answer": "예상 답변 2", "followup": "꼬리질문 2"}},
        {{"answer": "예상 답변 3", "followup": "꼬리질문 3"}}
      ]
    }}
  ]
}}
"""

print("=" * 60)
print("LLM deep_questions 생성 테스트")
print("=" * 60)
print(f"\n테스트 문항: {test_question[:50]}...")
print(f"테스트 답변: {test_answer[:50]}...")
print("\n" + "=" * 60)
print("LLM 호출 중...")
print("=" * 60)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}
payload = {
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "당신은 항공사 면접관입니다. JSON 형식으로만 응답하세요."},
        {"role": "user", "content": simple_prompt}
    ],
    "temperature": 0.7,
    "response_format": {"type": "json_object"},
}

try:
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )
    r.raise_for_status()
    resp = r.json()

    content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")

    print("\n" + "=" * 60)
    print("LLM 응답 (원본)")
    print("=" * 60)
    print(content)

    # JSON 파싱
    try:
        parsed = json.loads(content)
        print("\n" + "=" * 60)
        print("파싱된 JSON")
        print("=" * 60)
        print(json.dumps(parsed, ensure_ascii=False, indent=2))

        # deep_questions 확인
        deep_questions = parsed.get("deep_questions", [])
        print("\n" + "=" * 60)
        print(f"deep_questions 개수: {len(deep_questions)}")
        print("=" * 60)

        for i, dq in enumerate(deep_questions):
            print(f"\n[질문 {i+1}]")
            print(f"  핵심문장: {dq.get('source_sentence', 'N/A')}")
            print(f"  유형: {dq.get('sentence_type', 'N/A')}")
            print(f"  질문: {dq.get('question', 'N/A')}")
            print(f"  예상답변:")
            for ea in dq.get("expected_answers", []):
                print(f"    - {ea.get('answer', 'N/A')} → {ea.get('followup', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"\nJSON 파싱 실패: {e}")

except requests.exceptions.Timeout:
    print("\n타임아웃!")
except Exception as e:
    print(f"\n에러 발생: {e}")
