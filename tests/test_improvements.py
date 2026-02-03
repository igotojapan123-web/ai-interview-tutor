# -*- coding: utf-8 -*-
"""
test_improvements.py
A~G 개선사항 전체 테스트 스크립트
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 테스트 결과 저장
all_results: Dict[str, List[Tuple[str, bool, str]]] = {}


def run_test(category: str, test_name: str, test_func):
    """테스트 실행"""
    if category not in all_results:
        all_results[category] = []

    try:
        result, msg = test_func()
        all_results[category].append((test_name, result, msg))
        return result
    except Exception as e:
        error_msg = f"예외: {str(e)}"
        all_results[category].append((test_name, False, error_msg))
        return False


# ============================================================
# A. 심리적/감정적 테스트
# ============================================================

def test_category_a():
    """A. 심리적/감정적 (-) 해결 테스트"""
    print("\n" + "=" * 60)
    print("A. 심리적/감정적 (-) 해결 테스트")
    print("=" * 60)

    # A1: 맞춤 학습 경로 테스트
    def test_learning_path():
        from user_experience_enhancer import generate_learning_path

        path = generate_learning_path(
            user_id="test_user",
            target_airline="대한항공",
            target_date=datetime.now() + timedelta(days=30),
            weak_areas=["english_interview"]
        )

        assert path is not None, "경로가 None"
        assert len(path.steps) > 0, "학습 단계가 없음"
        assert path.target_airline == "대한항공", "항공사 불일치"
        assert path.total_estimated_hours > 0, "예상 시간이 0"

        return True, f"학습 단계 {len(path.steps)}개, 예상 {path.total_estimated_hours:.1f}시간"

    def test_daily_plan():
        from user_experience_enhancer import generate_learning_path, LearningPathGenerator

        path = generate_learning_path("test_user", "대한항공")
        generator = LearningPathGenerator()
        daily = generator.get_daily_plan(path, available_minutes=60)

        assert isinstance(daily, list), "일일 계획이 list가 아님"

        return True, f"오늘 추천 {len(daily)}개 학습"

    # A2: 합격 예측 테스트
    def test_pass_prediction():
        from user_experience_enhancer import predict_pass_probability

        score_history = [
            {"date": datetime.now() - timedelta(days=10), "score": 65, "category": "interview"},
            {"date": datetime.now() - timedelta(days=8), "score": 68, "category": "interview"},
            {"date": datetime.now() - timedelta(days=6), "score": 70, "category": "interview"},
            {"date": datetime.now() - timedelta(days=4), "score": 72, "category": "interview"},
            {"date": datetime.now() - timedelta(days=2), "score": 75, "category": "interview"},
            {"date": datetime.now(), "score": 78, "category": "interview"},
        ]

        result = predict_pass_probability("대한항공", score_history, 1.5)

        assert result is not None, "예측 결과가 None"
        assert result.current_score > 0, "현재 점수가 0"
        assert result.target_score > 0, "목표 점수가 0"
        assert result.message, "메시지가 없음"

        return True, f"현재 {result.current_score}점, 목표 {result.target_score}점, 예상 {result.predicted_days}일"

    # A3: 동료 매칭 테스트
    def test_partner_matching():
        from user_experience_enhancer import find_study_partners

        partners = find_study_partners(
            user_airline="대한항공",
            user_level="intermediate",
            user_time="evening",
            limit=3
        )

        assert isinstance(partners, list), "파트너 목록이 list가 아님"

        return True, f"매칭된 파트너 {len(partners)}명"

    # A4: 게임화 시스템 테스트
    def test_gamification():
        from user_experience_enhancer import get_daily_missions, check_streak, get_leaderboard

        missions = get_daily_missions("test_user")
        assert len(missions) > 0, "미션이 없음"

        practice_dates = [
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now(),
        ]
        streak = check_streak(practice_dates)
        assert streak.current_streak >= 0, "스트릭이 음수"

        leaderboard = get_leaderboard(limit=5)
        assert len(leaderboard) > 0, "리더보드가 비어있음"

        return True, f"미션 {len(missions)}개, 스트릭 {streak.current_streak}일, 리더보드 {len(leaderboard)}명"

    # A5: 격려 메시지 테스트
    def test_encouragement():
        from user_experience_enhancer import get_encouragement, get_progress_celebration

        msg = get_encouragement(score=75, previous_score=70, streak=5)
        assert msg is not None, "메시지가 None"
        assert msg.message, "메시지 텍스트가 없음"
        assert msg.emoji, "이모지가 없음"

        celebration = get_progress_celebration("first_80")
        assert celebration, "축하 메시지가 없음"

        return True, f"격려: '{msg.message[:20]}...'"

    # 테스트 실행
    run_test("A. 심리적/감정적", "A1: 맞춤 학습 경로", test_learning_path)
    run_test("A. 심리적/감정적", "A1-2: 일일 학습 계획", test_daily_plan)
    run_test("A. 심리적/감정적", "A2: 합격 예측", test_pass_prediction)
    run_test("A. 심리적/감정적", "A3: 동료 매칭", test_partner_matching)
    run_test("A. 심리적/감정적", "A4: 게임화 시스템", test_gamification)
    run_test("A. 심리적/감정적", "A5: 격려 메시지", test_encouragement)


# ============================================================
# B. 기능적 테스트
# ============================================================

def test_category_b():
    """B. 기능적 (-) 해결 테스트"""
    print("\n" + "=" * 60)
    print("B. 기능적 (-) 해결 테스트")
    print("=" * 60)

    # B1: 다중 STT 검증
    def test_multi_stt():
        from functional_enhancer import validate_stt, STTResult

        primary = STTResult(
            text="대한 항공에 지원한 이유는 서비스 정신입니다",
            confidence=0.85,
            source="primary"
        )

        result = validate_stt(primary)

        assert result is not None, "결과가 None"
        assert result.final_text, "최종 텍스트가 없음"
        assert "대한항공" in result.final_text, "항공사 용어 보정 안됨"
        assert result.confidence > 0, "신뢰도가 0"

        return True, f"보정된 텍스트, 신뢰도 {result.confidence:.2f}"

    # B2: 진행 상황 추적
    def test_progress_tracking():
        from functional_enhancer import start_progress_tracking, update_progress, get_progress_message

        tasks = ["stt_processing", "llm_analysis", "feedback_generation"]
        start_progress_tracking(tasks)

        progress = update_progress(1, partial="부분결과")

        assert progress.current_step == 2, "단계가 틀림"
        assert progress.total_steps == 3, "총 단계가 틀림"

        msg = get_progress_message(progress)
        assert msg, "메시지가 없음"

        return True, f"진행: {progress.current_step}/{progress.total_steps}, {msg}"

    # B3: 실시간 코칭
    def test_realtime_coaching():
        from functional_enhancer import get_realtime_coaching

        # 말이 너무 빠른 경우
        coaching = get_realtime_coaching(speech_speed=200)

        if coaching:
            assert coaching.message, "코칭 메시지 없음"
            return True, f"코칭: {coaching.message}"
        else:
            return True, "코칭 간격 제한 (정상)"

    # B4: 발음 분석
    def test_pronunciation():
        from functional_enhancer import analyze_pronunciation

        audio_features = {
            "clarity": 65,
            "accuracy": 68,
            "rhythm": 70
        }

        result = analyze_pronunciation(audio_features, "ko")

        assert result is not None, "결과가 None"
        assert result.overall_score > 0, "점수가 0"
        assert len(result.improvements) > 0, "개선점이 없음"

        return True, f"발음 점수: {result.overall_score}, 개선점 {len(result.improvements)}개"

    # B5: 비언어 분석
    def test_nonverbal():
        from functional_enhancer import analyze_nonverbal_extended

        video_features = {
            "head_nods": 5,
            "hand_gesture_score": 70,
            "body_movement_score": 75,
            "eye_contact_ratio": 0.7
        }

        result = analyze_nonverbal_extended(video_features, duration=60.0)

        assert result is not None, "결과가 None"
        assert result.overall_score > 0, "점수가 0"
        assert len(result.feedback) > 0, "피드백이 없음"

        return True, f"비언어 점수: {result.overall_score}, 피드백 {len(result.feedback)}개"

    # B6: 세션 관리
    def test_session():
        from functional_enhancer import create_session, update_session, recover_session

        session_id = create_session("test_user", "모의면접", {"question": 1})

        assert session_id, "세션 ID가 없음"

        success = update_session(session_id, {"answer": "테스트 답변"})
        assert success, "세션 업데이트 실패"

        return True, f"세션 생성/업데이트 성공: {session_id[:8]}..."

    # 테스트 실행
    run_test("B. 기능적", "B1: 다중 STT 검증", test_multi_stt)
    run_test("B. 기능적", "B2: 진행 상황 추적", test_progress_tracking)
    run_test("B. 기능적", "B3: 실시간 코칭", test_realtime_coaching)
    run_test("B. 기능적", "B4: 발음 분석", test_pronunciation)
    run_test("B. 기능적", "B5: 비언어 분석", test_nonverbal)
    run_test("B. 기능적", "B6: 세션 관리", test_session)


# ============================================================
# C. 학습 경험 테스트
# ============================================================

def test_category_c():
    """C. 학습 경험 (-) 해결 테스트"""
    print("\n" + "=" * 60)
    print("C. 학습 경험 (-) 해결 테스트")
    print("=" * 60)

    # C1: 맞춤 학습 계획
    def test_personalized_plan():
        from learning_experience_enhancer import generate_personalized_plan

        plan = generate_personalized_plan(
            user_id="test_user",
            target_airline="대한항공",
            target_date=datetime.now() + timedelta(days=30),
            current_scores={"speech": 65, "content": 70, "attitude": 75}
        )

        assert plan is not None, "계획이 None"
        assert plan.total_weeks > 0, "주 수가 0"
        assert len(plan.weekly_plans) > 0, "주간 계획이 없음"
        assert len(plan.priority_skills) > 0, "우선순위 스킬이 없음"

        return True, f"{plan.total_weeks}주 계획, 우선순위: {plan.priority_skills[:2]}"

    # C2: 약점 감지
    def test_weakness_detection():
        from learning_experience_enhancer import detect_weaknesses, get_focus_recommendation

        skill_scores = {"speech": 60, "content": 75, "attitude": 85}

        weaknesses = detect_weaknesses(skill_scores, target_score=80)

        assert isinstance(weaknesses, list), "약점이 list가 아님"

        recommendation = get_focus_recommendation(skill_scores)
        assert recommendation.get("focus_skill"), "집중 스킬이 없음"

        return True, f"약점 {len(weaknesses)}개, 집중: {recommendation.get('focus_skill')}"

    # C3: 마일스톤
    def test_milestones():
        from learning_experience_enhancer import create_milestones, get_next_milestone

        milestones = create_milestones("test_user", datetime.now() + timedelta(days=60))

        assert len(milestones) > 0, "마일스톤이 없음"

        next_ms = get_next_milestone(milestones)
        assert next_ms is not None, "다음 마일스톤이 없음"

        return True, f"마일스톤 {len(milestones)}개, 다음: {next_ms.title}"

    # C4: 성장 예측
    def test_growth_prediction():
        from learning_experience_enhancer import predict_growth

        score_history = [
            {"score": 60, "date": datetime.now() - timedelta(days=14)},
            {"score": 63, "date": datetime.now() - timedelta(days=12)},
            {"score": 65, "date": datetime.now() - timedelta(days=10)},
            {"score": 68, "date": datetime.now() - timedelta(days=8)},
            {"score": 70, "date": datetime.now() - timedelta(days=6)},
            {"score": 72, "date": datetime.now() - timedelta(days=4)},
            {"score": 75, "date": datetime.now() - timedelta(days=2)},
            {"score": 77, "date": datetime.now()},
        ]

        prediction = predict_growth(score_history, target_score=85)

        assert prediction is not None, "예측이 None"
        assert prediction.days_to_target >= 0, "목표까지 일수가 음수"
        assert len(prediction.factors) > 0, "요인이 없음"

        return True, f"목표 도달 예상: {prediction.days_to_target}일, 일당 상승: {prediction.growth_rate}"

    # C5: 실패 분석
    def test_failure_analysis():
        from learning_experience_enhancer import analyze_failure, get_priority_improvement

        failures = analyze_failure(
            category="speech",
            score=55,
            details={"too_fast": 40, "monotone": 50}
        )

        assert isinstance(failures, list), "실패가 list가 아님"

        improvement = get_priority_improvement("speech", 55, {"too_fast": 40})
        if improvement:
            return True, f"분석 {len(failures)}개, 우선: {improvement.get('first_step', 'N/A')[:20]}..."
        return True, f"분석 {len(failures)}개"

    # 테스트 실행
    run_test("C. 학습 경험", "C1: 맞춤 학습 계획", test_personalized_plan)
    run_test("C. 학습 경험", "C2: 약점 감지", test_weakness_detection)
    run_test("C. 학습 경험", "C3: 마일스톤", test_milestones)
    run_test("C. 학습 경험", "C4: 성장 예측", test_growth_prediction)
    run_test("C. 학습 경험", "C5: 실패 분석", test_failure_analysis)


# ============================================================
# D. 현실성 테스트
# ============================================================

def test_category_d():
    """D. 현실성 (-) 해결 테스트"""
    print("\n" + "=" * 60)
    print("D. 현실성 (-) 해결 테스트")
    print("=" * 60)

    # D1: 다중 면접관
    def test_multi_interviewer():
        from realism_enhancer import create_multi_interviewer_session, get_next_interviewer_question

        session = create_multi_interviewer_session("대한항공", num_interviewers=3)

        assert session is not None, "세션이 None"
        assert len(session.interviewers) == 3, "면접관 수가 틀림"

        question = get_next_interviewer_question(session)
        assert question.get("question"), "질문이 없음"
        assert question.get("interviewer"), "면접관 이름이 없음"

        return True, f"면접관 {len(session.interviewers)}명, 질문: {question['question'][:20]}..."

    # D2: 압박 질문
    def test_pressure_question():
        from realism_enhancer import generate_pressure_question

        question = generate_pressure_question(pressure_type="weakness")

        assert question is not None, "질문이 None"
        assert question.question, "질문 텍스트가 없음"
        assert len(question.tips) > 0, "팁이 없음"

        return True, f"압박: {question.question[:30]}..."

    # D3: 돌발 상황
    def test_surprise_situation():
        from realism_enhancer import get_random_surprise

        surprise = get_random_surprise()

        assert surprise is not None, "돌발 상황이 None"
        assert surprise.title, "제목이 없음"
        assert surprise.description, "설명이 없음"
        assert len(surprise.scoring_criteria) > 0, "평가 기준이 없음"

        return True, f"돌발: {surprise.title}, 기준 {len(surprise.scoring_criteria)}개"

    # D4: 컨디션 시뮬레이션
    def test_condition():
        from realism_enhancer import get_condition_settings

        settings = get_condition_settings("tired")

        assert settings is not None, "설정이 None"
        assert settings.description, "설명이 없음"
        assert len(settings.tips) > 0, "팁이 없음"

        return True, f"컨디션: {settings.description[:20]}..."

    # D5: 환경 시뮬레이션
    def test_environment():
        from realism_enhancer import check_time_status, get_environment_preset

        env = get_environment_preset("strict")
        assert env.time_limit > 0, "시간 제한이 0"

        status = check_time_status(elapsed=50.0, preset_name="strict")
        assert "remaining" in status, "remaining이 없음"

        return True, f"환경: 제한 {env.time_limit}초, 남은 {status['remaining']:.0f}초"

    # 테스트 실행
    run_test("D. 현실성", "D1: 다중 면접관", test_multi_interviewer)
    run_test("D. 현실성", "D2: 압박 질문", test_pressure_question)
    run_test("D. 현실성", "D3: 돌발 상황", test_surprise_situation)
    run_test("D. 현실성", "D4: 컨디션 시뮬레이션", test_condition)
    run_test("D. 현실성", "D5: 환경 시뮬레이션", test_environment)


# ============================================================
# E. 접근성 테스트
# ============================================================

def test_category_e():
    """E. 접근성 (-) 해결 테스트"""
    print("\n" + "=" * 60)
    print("E. 접근성 (-) 해결 테스트")
    print("=" * 60)

    # E1: 모바일 최적화
    def test_mobile_responsive():
        from accessibility_enhancer import detect_device_type, get_mobile_css, get_responsive_settings

        device = detect_device_type(375)  # iPhone 크기
        assert device == "mobile", f"디바이스 감지 실패: {device}"

        css = get_mobile_css()
        assert "@media" in css, "반응형 CSS가 없음"
        assert "min-width: 768px" in css, "태블릿 미디어쿼리 없음"

        settings = get_responsive_settings(375)
        assert settings.touch_friendly == True, "터치 친화적 아님"

        return True, f"모바일 감지, CSS {len(css)}자, 터치 친화적"

    # E2: 알림 시스템
    def test_notification():
        from accessibility_enhancer import create_notification, schedule_study_reminder

        notif = create_notification("job_posting", {"airline": "대한항공"})

        assert notif is not None, "알림이 None"
        assert "대한항공" in notif.message, "항공사 이름이 없음"

        reminder = schedule_study_reminder("test_user", "19:00")
        assert reminder is not None, "리마인더가 None"

        return True, f"알림: {notif.title}, 리마인더 예약됨"

    # E3: 오프라인 캐시
    def test_cache():
        from accessibility_enhancer import cache_content, get_cached_content, get_cache_status

        success = cache_content("tip_001", "interview_tips", {"tip": "테스트 팁"})
        assert success, "캐시 실패"

        cached = get_cached_content("tip_001")
        assert cached is not None, "캐시 조회 실패"
        assert cached.get("tip") == "테스트 팁", "캐시 데이터 불일치"

        status = get_cache_status()
        assert status["cached_items"] >= 1, "캐시 항목 수가 0"

        return True, f"캐시 저장/조회 성공, 항목 {status['cached_items']}개"

    # E4: 음성 폴백
    def test_voice_fallback():
        from accessibility_enhancer import report_voice_error, get_input_mode_ui, reset_voice_mode

        reset_voice_mode()  # 초기화

        status = report_voice_error("마이크 권한 없음")
        assert status.voice_error_count >= 1, "에러 카운트 안 됨"

        ui = get_input_mode_ui()
        assert "current_mode" in ui, "현재 모드가 없음"

        return True, f"에러 카운트: {status.voice_error_count}, 모드: {ui['current_mode']}"

    # 테스트 실행
    run_test("E. 접근성", "E1: 모바일 최적화", test_mobile_responsive)
    run_test("E. 접근성", "E2: 알림 시스템", test_notification)
    run_test("E. 접근성", "E3: 오프라인 캐시", test_cache)
    run_test("E. 접근성", "E4: 음성 폴백", test_voice_fallback)


# ============================================================
# F. 콘텐츠 테스트
# ============================================================

def test_category_f():
    """F. 콘텐츠 (-) 해결 테스트"""
    print("\n" + "=" * 60)
    print("F. 콘텐츠 (-) 해결 테스트")
    print("=" * 60)

    # F1: 합격자 사례
    def test_passer_examples():
        from content_enhancer import get_passer_examples, compare_with_passer

        examples = get_passer_examples(airline="대한항공", limit=3)

        assert len(examples) > 0, "사례가 없음"
        assert examples[0].answer, "답변이 없음"

        comparison = compare_with_passer(
            "저는 서비스 정신이 강해서 승무원이 되고 싶습니다",
            "왜 승무원이 되고 싶으신가요?"
        )

        assert comparison is not None, "비교 결과가 None"
        assert len(comparison.improvement_tips) > 0, "개선팁이 없음"

        return True, f"사례 {len(examples)}개, 유사도 {comparison.similarity_score:.1f}%"

    # F2: 함정 질문
    def test_trap_questions():
        from content_enhancer import get_trap_questions, get_random_trap_question

        questions = get_trap_questions(airline="대한항공")

        assert len(questions) > 0, "함정 질문이 없음"
        assert questions[0].tips, "팁이 없음"

        random_q = get_random_trap_question("아시아나항공")
        assert random_q.question, "질문이 없음"

        return True, f"함정 질문 {len(questions)}개, 랜덤: {random_q.question[:20]}..."

    # F3: 비상상황 시뮬레이션
    def test_emergency():
        from content_enhancer import get_emergency_scenario, evaluate_emergency_response

        scenario = get_emergency_scenario(difficulty=3)

        assert scenario is not None, "시나리오가 None"
        assert scenario.situation, "상황 설명이 없음"
        assert len(scenario.correct_procedure) > 0, "절차가 없음"

        result = evaluate_emergency_response(
            scenario,
            ["상황 파악", "기장 보고"]
        )

        assert "score" in result, "점수가 없음"

        return True, f"시나리오: {scenario.title}, 평가 점수: {result['score']}"

    # F4: MBTI 맞춤 피드백
    def test_mbti():
        from content_enhancer import get_mbti_profile, get_mbti_feedback

        profile = get_mbti_profile("ENFJ")

        assert profile is not None, "프로필이 None"
        assert len(profile.strengths) > 0, "강점이 없음"
        assert len(profile.interview_tips) > 0, "팁이 없음"

        feedback = get_mbti_feedback("ENFJ", score=75, category="interview")

        assert feedback.get("specific_tips"), "맞춤 팁이 없음"

        return True, f"ENFJ 강점: {profile.strengths[0]}, 팁 {len(profile.interview_tips)}개"

    # 테스트 실행
    run_test("F. 콘텐츠", "F1: 합격자 사례", test_passer_examples)
    run_test("F. 콘텐츠", "F2: 함정 질문", test_trap_questions)
    run_test("F. 콘텐츠", "F3: 비상상황 시뮬레이션", test_emergency)
    run_test("F. 콘텐츠", "F4: MBTI 맞춤 피드백", test_mbti)


# ============================================================
# G. UI/UX 테스트
# ============================================================

def test_category_g():
    """G. UI/UX (-) 해결 테스트"""
    print("\n" + "=" * 60)
    print("G. UI/UX (-) 해결 테스트")
    print("=" * 60)

    # G1: 용어 표준화
    def test_term_standardize():
        from uiux_enhancer import get_standard_term, standardize_term, get_all_standard_terms

        # 표준 용어 조회
        retry = get_standard_term("btn_retry")
        assert retry == "다시 시도", f"용어 불일치: {retry}"

        # 비표준 → 표준 변환
        standardized = standardize_term("다시하기")
        assert standardized == "다시 시도", f"표준화 실패: {standardized}"

        # 전체 용어 조회
        all_terms = get_all_standard_terms()
        assert len(all_terms) > 0, "용어 사전이 비어있음"

        return True, f"용어 표준화 성공, 전체 {len(all_terms)}개 카테고리"

    # G2: 진행률 표시
    def test_progress_bar():
        from uiux_enhancer import init_progress, update_progress, get_progress_html

        state = init_progress("모의면접")

        assert state is not None, "상태가 None"
        assert state.total_steps > 0, "총 단계가 0"

        updated = update_progress("모의면접", step=1)
        assert updated.current_step == 2, f"단계 불일치: {updated.current_step}"

        html = get_progress_html(updated)
        assert html, "HTML이 없음"
        assert "%" in html, "퍼센트가 없음"

        return True, f"진행: {updated.fraction_text}, {updated.percent:.0f}%"

    # G3: 네비게이션
    def test_navigation():
        from uiux_enhancer import get_navigation_config, get_back_button_html, get_breadcrumb_html

        config = get_navigation_config("실전연습")

        assert config.show_back_button == True, "뒤로가기 버튼 없음"
        assert len(config.breadcrumb) > 1, "브레드크럼 없음"

        back_html = get_back_button_html("실전연습")
        assert "돌아가기" in back_html, "돌아가기 텍스트 없음"

        breadcrumb = get_breadcrumb_html("실전연습")
        assert ">" in breadcrumb, "브레드크럼 구분자 없음"

        return True, f"브레드크럼: {' > '.join(config.breadcrumb)}"

    # G4: 로딩 메시지
    def test_loading():
        from uiux_enhancer import get_loading_content, get_loading_html

        content = get_loading_content("면접")

        assert content.tip, "팁이 없음"
        assert content.encouragement, "격려가 없음"

        html = get_loading_html("면접", progress=50)
        assert "TIP" in html, "TIP 섹션 없음"
        assert "50%" in html, "진행률 없음"

        return True, f"팁: {content.tip[:30]}..."

    # 테스트 실행
    run_test("G. UI/UX", "G1: 용어 표준화", test_term_standardize)
    run_test("G. UI/UX", "G2: 진행률 표시", test_progress_bar)
    run_test("G. UI/UX", "G3: 네비게이션", test_navigation)
    run_test("G. UI/UX", "G4: 로딩 메시지", test_loading)


# ============================================================
# 결과 출력
# ============================================================

def print_results():
    """결과 출력"""
    print("\n")
    print("=" * 70)
    print("         A-G 개선사항 테스트 결과")
    print("=" * 70)

    total_passed = 0
    total_failed = 0

    for category, results in all_results.items():
        passed = sum(1 for _, p, _ in results if p)
        failed = len(results) - passed
        total_passed += passed
        total_failed += failed

        print(f"\n{'='*60}")
        print(f"  {category}: {passed}/{len(results)} 통과")
        print(f"{'='*60}")

        for name, success, msg in results:
            status = "PASS" if success else "FAIL"
            print(f"  [{status}] {name}")
            if msg:
                print(f"         -> {msg}")

    print("\n" + "=" * 70)
    total = total_passed + total_failed
    rate = (total_passed / total * 100) if total > 0 else 0
    print(f"  총 결과: {total_passed}/{total} 테스트 통과 ({rate:.1f}%)")
    print("=" * 70)

    return total_failed == 0


if __name__ == "__main__":
    print("A-G 개선사항 테스트 시작...")

    test_category_a()
    test_category_b()
    test_category_c()
    test_category_d()
    test_category_e()
    test_category_f()
    test_category_g()

    success = print_results()
    sys.exit(0 if success else 1)
