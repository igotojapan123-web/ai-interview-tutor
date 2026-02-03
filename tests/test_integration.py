# -*- coding: utf-8 -*-
"""
통합 테스트 - 새 프리미엄 분석이 제대로 작동하는지 확인
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from llm_utils import premium_analyze_resume, get_premium_q2_question, get_premium_q3_question

# 테스트 데이터
question = """동료 승무원들이 함께 근무하고 싶어하는 승무원이 되기 위해,
본인이 중요하게 생각하는 것은 무엇이며,
이를 위해 어떤 노력을 하고 있나요?"""

answer = """전반적인 인생에 걸쳐 사람들과 같이 더불어 살 수 밖에 없습니다. 그렇기에 팀워크가 제일 중요하다고 생각합니다.
저는 16살이라는 나이에 중국 칭다오로 홀로 유학을 가게되었습니다.
저는 현재 세명대학교 항공서비스학과 축구 동아리 나르샤의 주장으로써 정말 잘하는 강팀을 만든다기 보다는 정말 축구를 잘 하지는 못하지만 좋아하는 인원도 같이 웃으면서 축구경기를 할 수 있는 환경을 조성하였습니다."""

print("=" * 60)
print("[프리미엄 분석 테스트]")
print("=" * 60)

analysis = premium_analyze_resume(question, answer)

if analysis:
    print("\n[성공] 프리미엄 분석 완료!")

    # 스토리 분석
    story = analysis.get("story_analysis", {})
    print(f"\n핵심 메시지: {story.get('main_message', 'N/A')}")

    # 핵심 문장
    key_sentences = analysis.get("key_sentences", [])
    print(f"\n핵심 문장 {len(key_sentences)}개 추출됨")
    for i, ks in enumerate(key_sentences, 1):
        print(f"  [{i}] {ks.get('sentence', '')[:50]}...")

    # 면접 질문
    questions = analysis.get("interview_questions", [])
    print(f"\n면접 질문 {len(questions)}개 생성됨")

    # Q2, Q3 추출 테스트
    for version in [1, 2, 3]:
        q2 = get_premium_q2_question(analysis, version, is_soft=(version % 2 == 0))
        q3 = get_premium_q3_question(analysis, version, is_soft=(version % 2 == 0))
        print(f"\n[버전 {version}]")
        print(f"  Q2: {q2}")
        print(f"  Q3: {q3}")
else:
    print("\n[실패] 프리미엄 분석 실패 - API 키를 확인하세요")
