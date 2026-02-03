# 간단한 자소서 질문 생성 테스트 - 원본 응답 확인
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flyready_clova_engine import FlyreadyClovaEngine

# 테스트 자소서
TEST_Q = "팀에서 갈등 상황을 해결한 경험을 구체적으로 기술해 주세요."

TEST_A = """대학교 3학년 때 학과 축제 준비위원장으로 활동하면서 팀원 간 심각한 갈등을 해결한 경험이 있습니다.
당시 예산 배분 문제로 기획팀과 홍보팀이 대립했고, 양측 모두 자신들의 업무가 더 중요하다고 주장하며
한 달 동안 회의가 교착 상태에 빠졌습니다.

저는 먼저 양측의 이야기를 1:1로 경청했습니다. 기획팀은 무대 장비 비용이 예상보다 높아졌고,
홍보팀은 SNS 광고비가 효과적이라는 데이터를 제시했습니다. 양측 모두 타당한 이유가 있었습니다.

저는 객관적인 기준을 만들기로 했습니다. 지난 3년간 축제 데이터를 분석해서 관객 유입 경로와
만족도 조사 결과를 정리했습니다. 이를 바탕으로 홍보비 30%, 기획비 50%, 예비비 20%로
재배분안을 제시했고, 양측이 수용했습니다.

결과적으로 그해 축제는 역대 최다 관객 2,500명을 기록했고, 만족도 조사에서 4.5/5점을 받았습니다.
이 경험을 통해 갈등 상황에서는 감정보다 데이터에 기반한 객관적 중재가 효과적이라는 것을 배웠습니다."""

print("=" * 80)
print("FLYREADY CLOVA 엔진 - 자소서 기반 질문 생성 테스트")
print("=" * 80)

engine = FlyreadyClovaEngine(airline="대한항공")
result = engine.analyze(TEST_Q, TEST_A, item_num=2)

# 원본 응답 저장
raw_response = result.get("raw_response", "")
with open("clova_raw_response.txt", "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("CLOVA 원본 응답\n")
    f.write("=" * 80 + "\n\n")
    f.write(raw_response)

print("\n[원본 응답이 clova_raw_response.txt에 저장되었습니다]")

# 파싱 결과 출력
print("\n" + "=" * 80)
print("파싱 결과")
print("=" * 80)
print(f"등급: {result.get('grade')}")
print(f"취약점 점수: {result.get('vulnerability_score')}점")
print(f"핵심문장 수: {result.get('key_sentence_count')}개")

print("\n[취약점]")
for vuln in result.get("vulnerabilities", []):
    print(f"  - {vuln}")

print("\n[생성된 질문]")
questions = result.get("questions", {})
types = result.get("types", {})
slots = result.get("slots", {})
intents = result.get("intents", {})

for v in range(1, 7):
    vk = f"v{v}"
    q = questions.get(vk, "(없음)")
    t = types.get(vk, "")
    s = slots.get(vk, "")
    i = intents.get(vk, "")
    tone = "부드러움" if v % 2 == 0 else "날카로움"

    print(f"\n[v{v}] ({tone}) [{t}] [{s}]")
    print(f"  Q: {q}")
    if i:
        print(f"  의도: {i[:80]}...")

print(f"\n처리 시간: {result.get('processing_time', 0):.1f}초")
print("\n테스트 완료!")
