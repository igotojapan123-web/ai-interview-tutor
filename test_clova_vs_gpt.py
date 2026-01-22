"""
HyperCLOVA X vs GPT-4o-mini 한국어 자소서 분석 품질 비교 테스트
"""

import os
import time
from openai import OpenAI

# ===== API 설정 =====
CLOVA_API_KEY = "nv-b671e9692d064b1abd4fee4a5553887fdARS"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# CLOVA Studio 클라이언트
clova_client = OpenAI(
    api_key=CLOVA_API_KEY,
    base_url="https://clovastudio.stream.ntruss.com/v1/openai"
)

# OpenAI 클라이언트
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===== 테스트 자소서 =====
TEST_RESUME = """
문항: 동료 승무원들이 함께 근무하고 싶어하는 승무원이 되기 위해, 본인이 중요하게 생각하는 것은 무엇이며, 이를 위해 어떤 노력을 하고 있나요?

답변: 저는 팀워크가 제일 중요하다고 생각합니다. 축구라는 스포츠는 11명이서 합을 맞추어 진행되는 스포츠입니다. 저는 16살이라는 나이에 중국 칭다오로 홀로 유학을 가게되었습니다. 의지할 사람 없이 혼자 헤쳐나가야 한다는 부담감을 처음 느껴봤습니다. 하지만 같은 처지의 유학생 친구들과 서로 부족한 부분을 채워주며 혼자였으면 절대 극복하지 못할 것들을 공동체 속에 함께 있으니 극복할 수 있었던 것입니다. 저는 현재 세명대학교 항공서비스학과 축구 동아리 나르샤의 주장으로써 정말 잘하는 강팀을 만든다기 보다는 정말 축구를 잘 하지는 못하지만 좋아하는 인원도 같이 웃으면서 축구경기를 할 수 있는 환경을 조성하였습니다.
"""

# ===== 분석 프롬프트 =====
ANALYSIS_PROMPT = """
아래 자소서를 분석하고 날카로운 면접 질문 3개를 만들어주세요.

<자소서>
{resume}
</자소서>

## 요구사항
1. 지원자가 "헉" 할 만큼 날카로운 질문
2. 자소서 원문을 정확히 인용
3. "어떻게 ~했습니까?" 같은 약한 질문 금지
4. "~때문에 손해 본 적은?", "몇 승 몇 패?" 같은 검증 질문

## 출력 형식
각 질문마다:
- 인용: (자소서에서 인용한 문장)
- 질문: (날카로운 면접 질문)
- 꼬리질문: (예상 답변에 대한 추가 질문)
"""


def test_clova():
    """HyperCLOVA X 테스트"""
    print("\n" + "="*60)
    print("HyperCLOVA X 테스트")
    print("="*60)

    start = time.time()

    try:
        response = clova_client.chat.completions.create(
            model="HCX-003",  # 또는 HCX-DASH-001, HCX-005
            messages=[
                {"role": "system", "content": "당신은 베테랑 항공사 면접관입니다."},
                {"role": "user", "content": ANALYSIS_PROMPT.format(resume=TEST_RESUME)}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        elapsed = time.time() - start
        result = response.choices[0].message.content

        print(f"\n[소요시간] {elapsed:.1f}초")
        print(f"\n[결과]\n{result}")

        return {"success": True, "time": elapsed, "result": result}

    except Exception as e:
        elapsed = time.time() - start
        print(f"\n[에러] {type(e).__name__}: {e}")
        return {"success": False, "time": elapsed, "error": str(e)}


def test_gpt():
    """GPT-4o-mini 테스트"""
    print("\n" + "="*60)
    print("GPT-4o-mini 테스트")
    print("="*60)

    start = time.time()

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 베테랑 항공사 면접관입니다."},
                {"role": "user", "content": ANALYSIS_PROMPT.format(resume=TEST_RESUME)}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        elapsed = time.time() - start
        result = response.choices[0].message.content

        print(f"\n[소요시간] {elapsed:.1f}초")
        print(f"\n[결과]\n{result}")

        return {"success": True, "time": elapsed, "result": result}

    except Exception as e:
        elapsed = time.time() - start
        print(f"\n[에러] {type(e).__name__}: {e}")
        return {"success": False, "time": elapsed, "error": str(e)}


def main():
    print("\n" + "#"*60)
    print("# HyperCLOVA X vs GPT-4o-mini 한국어 품질 비교")
    print("#"*60)

    # 테스트 실행
    clova_result = test_clova()
    gpt_result = test_gpt()

    # 결과 비교
    print("\n" + "="*60)
    print("비교 결과")
    print("="*60)

    print(f"\n| 항목 | HyperCLOVA X | GPT-4o-mini |")
    print(f"|------|-------------|-------------|")
    print(f"| 성공 | {'O' if clova_result['success'] else 'X'} | {'O' if gpt_result['success'] else 'X'} |")
    print(f"| 속도 | {clova_result['time']:.1f}초 | {gpt_result['time']:.1f}초 |")

    # 파일로 저장
    with open("C:/Users/ADMIN/ai_tutor/clova_vs_gpt_result.txt", "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write("HyperCLOVA X vs GPT-4o-mini 비교 결과\n")
        f.write("="*60 + "\n\n")

        f.write("[HyperCLOVA X]\n")
        f.write(f"소요시간: {clova_result['time']:.1f}초\n")
        if clova_result['success']:
            f.write(f"결과:\n{clova_result['result']}\n")
        else:
            f.write(f"에러: {clova_result.get('error', 'Unknown')}\n")

        f.write("\n" + "-"*60 + "\n\n")

        f.write("[GPT-4o-mini]\n")
        f.write(f"소요시간: {gpt_result['time']:.1f}초\n")
        if gpt_result['success']:
            f.write(f"결과:\n{gpt_result['result']}\n")
        else:
            f.write(f"에러: {gpt_result.get('error', 'Unknown')}\n")

    print("\n결과가 clova_vs_gpt_result.txt에 저장되었습니다.")


if __name__ == "__main__":
    main()
