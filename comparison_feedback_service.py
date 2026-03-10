"""
FLYREADY 비교 피드백 서비스
- 이전 세션 피드백 참고
- 발전/개선 피드백 생성
- GPT 프롬프트에 히스토리 컨텍스트 추가
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

# 환경 설정
try:
    from env_config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 히스토리 유틸리티
try:
    from interview_history_utils import (
        get_all_sessions,
        get_sessions_by_airline,
        get_question_history,
    )
    HISTORY_AVAILABLE = True
except ImportError:
    HISTORY_AVAILABLE = False


# ============================================================
# 이전 세션 피드백 조회
# ============================================================

def get_previous_feedback_context(
    airline: str,
    question_text: str = None,
    max_sessions: int = 3
) -> Dict[str, Any]:
    """
    이전 세션에서 피드백 컨텍스트 추출

    Args:
        airline: 항공사명
        question_text: 현재 질문 (유사 질문 매칭용)
        max_sessions: 참조할 최대 세션 수

    Returns:
        {
            "has_history": bool,
            "previous_weaknesses": ["약점1", "약점2"],
            "previous_strengths": ["강점1"],
            "improvement_trends": {"STAR기법": "improving"},
            "context_for_prompt": "프롬프트용 컨텍스트 문자열",
            "sessions_referenced": 3
        }
    """
    if not HISTORY_AVAILABLE:
        return _empty_context()

    try:
        # 같은 항공사 세션 조회
        sessions = get_sessions_by_airline(airline)
        if not sessions:
            # 전체 세션에서 조회
            sessions = get_all_sessions(limit=max_sessions * 2)

        if not sessions:
            return _empty_context()

        # 최근 세션만 (최대 3개)
        recent_sessions = sessions[:max_sessions]

        # 약점/강점 집계
        all_weaknesses = []
        all_strengths = []
        score_history = []

        for session in recent_sessions:
            questions = session.get("questions", [])
            scores = session.get("scores", {})

            if scores.get("total", 0) > 0:
                score_history.append(scores["total"])

            for q in questions:
                feedback = q.get("feedback", {})
                if isinstance(feedback, dict):
                    all_weaknesses.extend(feedback.get("improvements", []))
                    all_strengths.extend(feedback.get("strengths", []))
                elif isinstance(feedback, str) and feedback:
                    # 문자열 피드백에서 약점 추출
                    if "부족" in feedback or "개선" in feedback or "필요" in feedback:
                        all_weaknesses.append(feedback[:100])

        # 빈도 기반 주요 약점/강점 추출
        weakness_counts = defaultdict(int)
        strength_counts = defaultdict(int)

        for w in all_weaknesses:
            if w:
                # 핵심 키워드 추출
                key = _extract_feedback_key(w)
                if key:
                    weakness_counts[key] += 1

        for s in all_strengths:
            if s:
                key = _extract_feedback_key(s)
                if key:
                    strength_counts[key] += 1

        # 상위 약점/강점
        top_weaknesses = sorted(weakness_counts.items(), key=lambda x: -x[1])[:3]
        top_strengths = sorted(strength_counts.items(), key=lambda x: -x[1])[:2]

        # 개선 추이 분석
        improvement_trends = _analyze_improvement_trends(score_history)

        # 프롬프트용 컨텍스트 생성
        context_for_prompt = _build_prompt_context(
            top_weaknesses, top_strengths, improvement_trends, len(recent_sessions)
        )

        return {
            "has_history": True,
            "previous_weaknesses": [w[0] for w in top_weaknesses],
            "previous_strengths": [s[0] for s in top_strengths],
            "improvement_trends": improvement_trends,
            "context_for_prompt": context_for_prompt,
            "sessions_referenced": len(recent_sessions),
            "score_history": score_history,
        }

    except Exception as e:
        print(f"[comparison_feedback_service] get_previous_feedback_context error: {e}")
        return _empty_context()


def _extract_feedback_key(feedback_text: str) -> Optional[str]:
    """피드백 텍스트에서 핵심 키워드 추출"""
    keywords = [
        ("STAR", "STAR기법"),
        ("구체", "구체성"),
        ("Result", "결과 제시"),
        ("Action", "행동 설명"),
        ("Situation", "상황 설명"),
        ("Task", "과제 설명"),
        ("숫자", "수치 활용"),
        ("경험", "경험 활용"),
        ("논리", "논리성"),
        ("시간", "답변 시간"),
        ("속도", "말 속도"),
        ("발음", "발음"),
        ("자신감", "자신감"),
        ("표현", "표현력"),
        ("연결", "문장 연결"),
        ("두괄식", "두괄식 구조"),
    ]

    feedback_lower = feedback_text.lower()
    for keyword, label in keywords:
        if keyword.lower() in feedback_lower:
            return label

    return None


def _analyze_improvement_trends(score_history: List[int]) -> Dict[str, str]:
    """점수 히스토리에서 개선 추이 분석"""
    if len(score_history) < 2:
        return {"overall": "insufficient_data"}

    # 처음 절반 vs 나중 절반 비교
    mid = len(score_history) // 2
    first_half = score_history[:mid] if mid > 0 else score_history[:1]
    second_half = score_history[mid:] if mid > 0 else score_history[1:]

    first_avg = sum(first_half) / len(first_half) if first_half else 0
    second_avg = sum(second_half) / len(second_half) if second_half else 0

    diff = second_avg - first_avg

    if diff >= 5:
        trend = "improving"
    elif diff <= -5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "overall": trend,
        "first_avg": round(first_avg, 1),
        "second_avg": round(second_avg, 1),
        "change": round(diff, 1),
    }


def _build_prompt_context(
    weaknesses: List[tuple],
    strengths: List[tuple],
    trends: Dict,
    session_count: int
) -> str:
    """GPT 프롬프트용 컨텍스트 문자열 생성"""
    if not weaknesses and not strengths:
        return ""

    lines = [f"[이전 {session_count}회 세션 피드백 요약]"]

    if weaknesses:
        lines.append("- 반복된 약점:")
        for w, count in weaknesses:
            lines.append(f"  * {w} ({count}회 지적)")

    if strengths:
        lines.append("- 확인된 강점:")
        for s, count in strengths:
            lines.append(f"  * {s}")

    if trends.get("overall") == "improving":
        lines.append(f"- 점수 추이: 상승 중 (+{trends.get('change', 0)}점)")
    elif trends.get("overall") == "declining":
        lines.append(f"- 점수 추이: 하락 중 ({trends.get('change', 0)}점)")

    lines.append("")
    lines.append("위 히스토리를 참고하여:")
    lines.append("1. 이전에 지적한 부분이 개선되었으면 구체적으로 칭찬하세요")
    lines.append("2. 아직 개선되지 않은 부분은 다른 관점에서 새로운 조언을 제공하세요 (같은 말 반복 금지)")
    lines.append("3. 새로 발견된 약점이 있으면 추가 피드백을 제공하세요")

    return "\n".join(lines)


def _empty_context() -> Dict[str, Any]:
    """빈 컨텍스트"""
    return {
        "has_history": False,
        "previous_weaknesses": [],
        "previous_strengths": [],
        "improvement_trends": {},
        "context_for_prompt": "",
        "sessions_referenced": 0,
        "score_history": [],
    }


# ============================================================
# 비교 피드백 생성
# ============================================================

def generate_comparison_feedback(
    current_answer: str,
    current_score: int,
    previous_context: Dict[str, Any],
    question_text: str = ""
) -> Dict[str, Any]:
    """
    이전 세션과 비교한 피드백 생성

    Args:
        current_answer: 현재 답변
        current_score: 현재 점수
        previous_context: get_previous_feedback_context() 결과
        question_text: 질문 텍스트

    Returns:
        {
            "improved_areas": ["개선된 영역"],
            "still_needs_work": ["아직 보완 필요"],
            "new_findings": ["새로 발견된 점"],
            "encouragement": "격려 메시지",
            "score_comparison": {"previous_avg": 70, "current": 75, "change": +5}
        }
    """
    if not previous_context.get("has_history"):
        return {
            "improved_areas": [],
            "still_needs_work": [],
            "new_findings": [],
            "encouragement": "첫 면접 연습이시군요! 꾸준히 하시면 실력이 빠르게 늘어요.",
            "score_comparison": None,
        }

    # 점수 비교
    score_history = previous_context.get("score_history", [])
    prev_avg = sum(score_history) / len(score_history) if score_history else 0
    score_change = current_score - prev_avg

    # 개선 영역 분석 (현재 답변에서 이전 약점이 해결되었는지)
    improved_areas = []
    still_needs_work = []

    previous_weaknesses = previous_context.get("previous_weaknesses", [])
    answer_lower = current_answer.lower()

    for weakness in previous_weaknesses:
        # 약점 키워드 기반 체크 (간단 버전)
        if weakness == "구체성" and any(c.isdigit() for c in current_answer):
            improved_areas.append(f"'{weakness}' 개선됨 - 구체적인 수치가 포함되었어요!")
        elif weakness == "STAR기법" and len(current_answer) > 200:
            improved_areas.append(f"'{weakness}' 개선됨 - 답변이 더 체계적이에요!")
        else:
            still_needs_work.append(weakness)

    # 격려 메시지
    if score_change >= 5:
        encouragement = f"대단해요! 이전보다 {score_change:.0f}점 향상되었어요. 연습의 효과가 나타나고 있어요!"
    elif score_change >= 0:
        encouragement = "안정적인 점수를 유지하고 있어요. 약간의 개선으로 더 높은 점수를 받을 수 있어요!"
    else:
        encouragement = "점수가 조금 낮아졌지만 괜찮아요. 어려운 질문에 도전한 거예요. 복습하면 금방 올라요!"

    return {
        "improved_areas": improved_areas,
        "still_needs_work": still_needs_work,
        "new_findings": [],  # GPT에서 채울 수 있음
        "encouragement": encouragement,
        "score_comparison": {
            "previous_avg": round(prev_avg, 1),
            "current": current_score,
            "change": round(score_change, 1),
        },
    }


# ============================================================
# 피드백 UI 생성 (Streamlit용)
# ============================================================

def render_comparison_feedback_ui(comparison_result: Dict[str, Any]) -> str:
    """
    비교 피드백 UI HTML 생성

    Args:
        comparison_result: generate_comparison_feedback() 결과

    Returns:
        HTML 문자열 (st.markdown에서 사용)
    """
    if not comparison_result.get("score_comparison"):
        return ""

    score_comp = comparison_result["score_comparison"]
    change = score_comp.get("change", 0)

    # 점수 변화 색상
    if change >= 5:
        change_color = "#10b981"
        change_icon = "📈"
        change_text = f"+{change:.0f}점 향상"
    elif change >= 0:
        change_color = "#6b7280"
        change_icon = "➡️"
        change_text = "유지"
    else:
        change_color = "#f59e0b"
        change_icon = "📉"
        change_text = f"{change:.0f}점"

    html_parts = [f"""
    <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                border-radius: 12px; padding: 16px; margin: 12px 0;">
        <div style="font-weight: 700; color: #1e40af; margin-bottom: 8px;">
            {change_icon} 이전 세션 대비 성장 분석
        </div>
        <div style="display: flex; gap: 20px; align-items: center;">
            <div style="text-align: center;">
                <div style="font-size: 0.8rem; color: #666;">이전 평균</div>
                <div style="font-size: 1.5rem; font-weight: 700;">{score_comp['previous_avg']:.0f}점</div>
            </div>
            <div style="font-size: 2rem; color: {change_color};">→</div>
            <div style="text-align: center;">
                <div style="font-size: 0.8rem; color: #666;">이번 점수</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: {change_color};">{score_comp['current']}점</div>
            </div>
            <div style="background: {change_color}20; color: {change_color};
                        padding: 4px 12px; border-radius: 20px; font-weight: 600;">
                {change_text}
            </div>
        </div>
    </div>
    """]

    # 개선된 영역
    if comparison_result.get("improved_areas"):
        html_parts.append("""
        <div style="margin: 8px 0;">
            <div style="color: #10b981; font-weight: 600;">개선된 점</div>
        """)
        for area in comparison_result["improved_areas"]:
            html_parts.append(f"<div style='color: #065f46;'>✓ {area}</div>")
        html_parts.append("</div>")

    # 아직 보완 필요
    if comparison_result.get("still_needs_work"):
        html_parts.append("""
        <div style="margin: 8px 0;">
            <div style="color: #f59e0b; font-weight: 600;">계속 연습하면 좋을 점</div>
        """)
        for area in comparison_result["still_needs_work"]:
            html_parts.append(f"<div style='color: #92400e;'>→ {area}</div>")
        html_parts.append("</div>")

    # 격려 메시지
    encouragement = comparison_result.get("encouragement", "")
    if encouragement:
        html_parts.append(f"""
        <div style="margin-top: 12px; padding: 10px; background: #fef3c7;
                    border-radius: 8px; color: #92400e;">
            💪 {encouragement}
        </div>
        """)

    return "\n".join(html_parts)


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("비교 피드백 서비스 테스트")
    print("=" * 50)

    # 테스트: 이전 컨텍스트 조회
    context = get_previous_feedback_context("대한항공")
    print(f"\n1. 이전 피드백 컨텍스트:")
    print(f"   히스토리 있음: {context['has_history']}")
    print(f"   참조 세션 수: {context['sessions_referenced']}")
    print(f"   약점: {context['previous_weaknesses']}")

    # 테스트: 비교 피드백 생성
    comparison = generate_comparison_feedback(
        current_answer="저는 팀 프로젝트에서 리더로 활동하며 매출 20% 향상을 달성했습니다.",
        current_score=78,
        previous_context=context,
    )
    print(f"\n2. 비교 피드백:")
    print(f"   개선된 점: {comparison['improved_areas']}")
    print(f"   보완 필요: {comparison['still_needs_work']}")
    print(f"   격려: {comparison['encouragement']}")

    print("\n✅ 테스트 완료")
