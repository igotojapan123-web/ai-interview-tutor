# 자소서 기반 질문 생성 테스트
# 실제 자소서 예시를 넣어서 핵심문장 추출 및 질문 생성 테스트

import os
import sys

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flyready_clova_engine import FlyreadyClovaEngine, parse_essay_grade

# ============================================
# 테스트용 자소서 샘플 (실제 항공사 지원서 스타일)
# ============================================

TEST_QUESTION_1 = """
본인이 팀에서 갈등 상황을 해결한 경험을 구체적으로 기술해 주세요.
"""

TEST_ANSWER_1 = """
대학교 3학년 때 학과 축제 준비위원장으로 활동하면서 팀원 간 심각한 갈등을 해결한 경험이 있습니다.
당시 예산 배분 문제로 기획팀과 홍보팀이 대립했고, 양측 모두 자신들의 업무가 더 중요하다고 주장하며
한 달 동안 회의가 교착 상태에 빠졌습니다.

저는 먼저 양측의 이야기를 1:1로 경청했습니다. 기획팀은 무대 장비 비용이 예상보다 높아졌고,
홍보팀은 SNS 광고비가 효과적이라는 데이터를 제시했습니다. 양측 모두 타당한 이유가 있었습니다.

저는 객관적인 기준을 만들기로 했습니다. 지난 3년간 축제 데이터를 분석해서 관객 유입 경로와
만족도 조사 결과를 정리했습니다. 이를 바탕으로 홍보비 30%, 기획비 50%, 예비비 20%로
재배분안을 제시했고, 양측이 수용했습니다.

결과적으로 그해 축제는 역대 최다 관객 2,500명을 기록했고, 만족도 조사에서 4.5/5점을 받았습니다.
이 경험을 통해 갈등 상황에서는 감정보다 데이터에 기반한 객관적 중재가 효과적이라는 것을 배웠습니다.
"""

TEST_QUESTION_2 = """
지원 동기와 입사 후 포부를 작성해 주세요.
"""

TEST_ANSWER_2 = """
어릴 때부터 비행기를 탈 때마다 승무원 언니들의 따뜻한 미소와 세심한 배려에 감동받았습니다.
특히 초등학교 3학년 때 혼자 비행기를 탔을 때, 긴장한 저를 위해 조종실 구경을 시켜주시고
기장님 사인까지 받아주신 승무원분의 배려가 아직도 잊히지 않습니다.

대한항공을 지원한 이유는 '세계 최고 수준의 안전'과 '차별화된 프리미엄 서비스'를 동시에
추구한다는 점에서 제 가치관과 일치하기 때문입니다. 특히 스카이팀 창립 멤버로서
글로벌 네트워크를 갖추고 있어 다양한 문화권의 승객을 만날 수 있다는 점이 매력적입니다.

입사 후에는 먼저 안전 규정을 완벽히 숙지하고, 3년 내에 영어와 중국어 서비스가 가능한
글로벌 승무원이 되겠습니다. 또한 신입 시절 받은 도움을 기억하며 후배 양성에도 힘쓰고,
10년 후에는 사무장으로서 팀을 이끌어 대한항공의 서비스 품질 향상에 기여하고 싶습니다.
"""

TEST_QUESTION_3 = """
고객 서비스 경험 중 어려웠던 상황과 해결 과정을 기술해 주세요.
"""

TEST_ANSWER_3 = """
카페 아르바이트 중 외국인 손님과의 소통 문제를 해결한 경험이 있습니다.
일본인 관광객 두 분이 메뉴를 보며 한참 고민하셨는데, 영어로 설명을 드려도
잘 이해하지 못하시는 것 같았습니다.

저는 스마트폰 번역 앱을 활용해서 일본어로 메뉴 설명을 보여드렸고,
인기 메뉴 사진을 직접 보여드리며 추천해드렸습니다.
손님들이 음료를 받으시고 "오이시이!(맛있다)"라고 말씀하셨을 때 정말 뿌듯했습니다.

이후 자주 오시는 외국인 손님을 위해 영어, 일본어, 중국어 메뉴판을
제가 직접 제작해서 점장님께 제안드렸고, 실제로 도입되어 외국인 손님 응대 시간이
절반으로 줄었습니다. 이 경험으로 언어 장벽은 진심과 창의적 해결책으로 극복할 수 있다는 것을 배웠습니다.
"""


def test_flyready_engine():
    """FLYREADY 엔진 테스트"""
    print("=" * 70)
    print("FLYREADY CLOVA 엔진 v4.0 - 자소서 기반 질문 생성 테스트")
    print("=" * 70)

    test_cases = [
        ("대한항공", TEST_QUESTION_1, TEST_ANSWER_1, "갈등 해결 경험"),
        ("대한항공", TEST_QUESTION_2, TEST_ANSWER_2, "지원 동기/포부"),
        ("제주항공", TEST_QUESTION_3, TEST_ANSWER_3, "고객 서비스 경험"),
    ]

    for airline, question, answer, desc in test_cases:
        print(f"\n{'='*70}")
        print(f"[테스트] {desc} | 항공사: {airline}")
        print(f"{'='*70}")
        print(f"\n[문항] {question.strip()[:100]}...")
        print(f"\n[답변 일부] {answer.strip()[:200]}...")

        try:
            engine = FlyreadyClovaEngine(airline=airline)
            result = engine.analyze(question, answer, item_num=2)

            print(f"\n{'─'*50}")
            print(f"[분석 결과]")
            print(f"{'─'*50}")

            # 등급 정보
            grade = result.get("grade", "UNKNOWN")
            vuln_score = result.get("vulnerability_score", 0)
            key_count = result.get("key_sentence_count", 0)

            print(f"  - 등급: {grade}")
            print(f"  - 취약점 점수: {vuln_score}점")
            print(f"  - 핵심문장 수: {key_count}개")

            # 취약점 목록
            vulnerabilities = result.get("vulnerabilities", [])
            if vulnerabilities:
                print(f"\n[추출된 취약점]")
                for i, vuln in enumerate(vulnerabilities[:5], 1):
                    print(f"  {i}. {vuln}")

            # 생성된 질문 (6개 버전)
            questions = result.get("questions", {})
            types = result.get("types", {})
            slots = result.get("slots", {})
            intents = result.get("intents", {})

            print(f"\n[생성된 질문 (6개 버전)]")
            for v in range(1, 7):
                v_key = f"v{v}"
                q = questions.get(v_key, "(없음)")
                q_type = types.get(v_key, "")
                q_slot = slots.get(v_key, "")
                intent = intents.get(v_key, "")

                tone = "부드러움" if v % 2 == 0 else "날카로움"

                print(f"\n  [v{v}] ({tone}) [{q_type}] [{q_slot}]")
                print(f"      Q: {q}")
                if intent:
                    print(f"      의도: {intent[:50]}...")

            # 처리 시간
            proc_time = result.get("processing_time", 0)
            print(f"\n[처리 시간] {proc_time:.2f}초")

        except Exception as e:
            print(f"\n[오류] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*70}")
    print("테스트 완료")
    print(f"{'='*70}")


def test_parse_essay_grade():
    """파싱 함수 단독 테스트"""
    print("\n" + "="*70)
    print("parse_essay_grade 함수 테스트")
    print("="*70)

    # 예시 CLOVA 응답 (실제 응답 형태 시뮬레이션)
    sample_response = """
## 1. 핵심문장(4문장)
1. "저는 먼저 양측의 이야기를 1:1로 경청했습니다."
2. "객관적인 기준을 만들기로 했습니다."
3. "지난 3년간 축제 데이터를 분석해서 관객 유입 경로와 만족도 조사 결과를 정리했습니다."
4. "결과적으로 그해 축제는 역대 최다 관객 2,500명을 기록했습니다."

## 2. 슬롯별 취약점
- SLOT_CONFLICT: 갈등 상황의 심각성이 구체적으로 드러나지 않음 (2점)
- SLOT_ACTION: 1:1 경청이 구체적으로 어떻게 이루어졌는지 불명확 (2점)
- SLOT_CRITERIA: 데이터 분석 방법이 모호함 (3점)
- SLOT_RESULT: 숫자는 있으나 본인 기여도가 불분명 (2점)

## 3. 총점: 9점

## 4. 등급: MEDIUM

## 5. 6버전 질문

### v1 (자소서 기반, 날카로움)
슬롯: SLOT_ACTION
질문: 1:1로 경청했다고 했는데, 구체적으로 각 팀과 얼마나 만났고 뭘 들었어요?
의도: 경청 행동의 구체성 검증

### v2 (자소서 기반, 부드러움)
슬롯: SLOT_CRITERIA
질문: 3년간 데이터를 분석했다고 했는데, 어떤 기준으로 예산 비율을 정했어요?
의도: 의사결정 기준 확인

### v3 (자소서 기반, 날카로움)
슬롯: SLOT_RESULT
질문: 2,500명이 왔다고 했는데, 그게 본인 덕분이라는 근거가 뭐예요?
의도: 성과 귀속 검증

### v4 (자소서 기반, 부드러움)
슬롯: SLOT_CONFLICT
질문: 한 달간 교착 상태였다고 했는데, 그동안 팀 분위기는 어땠어요?
의도: 갈등 상황 심층 이해

### v5 (직무 연결, 날카로움)
슬롯: SLOT_JOB
질문: 기내에서 승객 두 분이 좌석 문제로 싸우면 어떻게 중재할 거예요?
의도: 승무원 직무 적용력 검증

### v6 (직무 연결, 부드러움)
슬롯: SLOT_JOB
질문: 이 경험이 승무원으로서 팀 갈등 상황에서 어떻게 도움이 될 것 같아요?
의도: 직무 연결성 확인
"""

    result = parse_essay_grade(sample_response)

    print(f"\n[파싱 결과]")
    print(f"  - 등급: {result.get('grade')}")
    print(f"  - 취약점 점수: {result.get('vulnerability_score')}")
    print(f"  - 핵심문장 수: {result.get('key_sentence_count')}")

    print(f"\n[취약점]")
    for vuln in result.get("vulnerabilities", []):
        print(f"  - {vuln}")

    print(f"\n[생성된 질문]")
    for v in range(1, 7):
        v_key = f"v{v}"
        q = result.get("questions", {}).get(v_key, "(없음)")
        print(f"  v{v}: {q[:60]}..." if len(q) > 60 else f"  v{v}: {q}")


if __name__ == "__main__":
    # 파싱 테스트 먼저 실행
    test_parse_essay_grade()

    print("\n" + "="*70)
    print("CLOVA API 호출 테스트를 진행하시겠습니까? (API 비용 발생)")
    print("="*70)

    # API 테스트 실행
    test_flyready_engine()
