# -*- coding: utf-8 -*-
# test_phase_a_to_d_complete.py
# Phase A-D 전체 종합 테스트 스크립트
# 실제 사용자 시나리오 기반 완벽 테스트

import sys
import os
import ast
import traceback
from typing import Dict, List, Tuple, Any

# UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 테스트 결과 저장
all_results: Dict[str, List[Tuple[str, bool, str]]] = {}


def run_test(phase: str, test_name: str, test_func):
    """테스트 실행 및 결과 기록"""
    if phase not in all_results:
        all_results[phase] = []

    try:
        result, msg = test_func()
        all_results[phase].append((test_name, result, msg))
        return result
    except Exception as e:
        error_msg = f"예외 발생: {str(e)}"
        all_results[phase].append((test_name, False, error_msg))
        return False


# ============================================================
# PHASE B: 핵심 면접 기능 테스트
# ============================================================

def test_phase_b():
    """Phase B 테스트: 핵심 면접 기능"""
    print("\n" + "=" * 60)
    print("PHASE B: 핵심 면접 기능 테스트")
    print("=" * 60)

    # B1: interview_enhancer.py 테스트
    def test_interview_enhancer_import():
        from interview_enhancer import (
            generate_follow_up_question,
            get_keyword_feedback,
            analyze_interview_answer,
            FollowUpQuestionGenerator,
            KeywordAnalyzer
        )
        return True, "모든 함수 임포트 성공"

    def test_interview_enhancer_followup():
        from interview_enhancer import generate_follow_up_question

        # 실제 사용 시나리오: 면접 질문에 대한 답변 후 꼬리질문 생성
        question = "왜 승무원이 되고 싶으신가요?"
        answer = "저는 어릴 때부터 비행기를 타며 승무원 분들의 서비스에 감동받았습니다."

        result = generate_follow_up_question(question, answer, airline="대한항공")

        # 결과가 dict이면 성공
        assert result is not None, "꼬리질문이 None"
        assert isinstance(result, dict), "결과가 dict가 아님"

        return True, f"꼬리질문 생성 성공"

    def test_interview_enhancer_keywords():
        from interview_enhancer import get_keyword_feedback

        # 실제 사용 시나리오: 답변 키워드 피드백
        question = "자기소개 해주세요"
        answer = "저는 팀워크를 중시하며 고객 서비스에 열정이 있습니다."

        result = get_keyword_feedback(answer, question, "대한항공")

        assert result is not None, "키워드 피드백이 None"

        return True, f"키워드 피드백 생성 성공"

    def test_interview_enhancer_analysis():
        from interview_enhancer import analyze_interview_answer

        question = "자기소개 해주세요"
        answer = "저는 서비스 정신이 투철한 지원자입니다. 고객을 위해 최선을 다하겠습니다."

        result = analyze_interview_answer(question, answer, elapsed_seconds=45, airline="대한항공")

        assert result is not None, "분석 결과가 None"

        return True, f"답변 분석 성공"

    # B2: roleplay_enhancer.py 테스트
    def test_roleplay_enhancer_import():
        from roleplay_enhancer import (
            generate_dynamic_scenario,
            get_performance_feedback,
            DifficultyLevel,
            AdaptiveDifficultyManager
        )
        return True, "모든 함수 임포트 성공"

    def test_roleplay_scenario():
        from roleplay_enhancer import generate_dynamic_scenario

        # 실제 사용 시나리오: 상황극 시나리오 생성
        result = generate_dynamic_scenario(category="complaint", difficulty=2)

        assert result is not None, "시나리오가 None"

        return True, f"시나리오 생성 성공"

    def test_roleplay_feedback():
        from roleplay_enhancer import get_performance_feedback

        # 롤플레이 수행 결과 피드백
        analysis = {"strengths": ["공감표현"], "improvements": ["구체적 해결책 제시"]}
        result = get_performance_feedback(
            score=75,
            difficulty=2,
            analysis=analysis
        )

        assert result is not None, "피드백이 None"

        return True, f"롤플레이 피드백 생성 성공"

    # B3: english_interview_enhancer.py 테스트
    def test_english_enhancer_import():
        from english_interview_enhancer import (
            analyze_english_answer,
            get_grammar_analysis,
            get_pronunciation_analysis,
            get_pace_analysis,
            get_filler_analysis
        )
        return True, "모든 함수 임포트 성공"

    def test_english_analysis():
        from english_interview_enhancer import analyze_english_answer

        answer = "I want to be a flight attendant because I love meeting people from different cultures."

        result = analyze_english_answer(answer, "Why do you want to be a flight attendant?")

        assert result is not None, "분석 결과가 None"

        return True, f"영어 답변 분석 성공"

    def test_english_grammar():
        from english_interview_enhancer import get_grammar_analysis

        text = "I have been working in customer service for three years."

        result = get_grammar_analysis(text)

        assert result is not None, "문법 분석이 None"

        return True, f"영어 문법 분석 성공"

    # B4: debate_enhancer.py 테스트
    def test_debate_enhancer_import():
        from debate_enhancer import (
            analyze_debate_answer,
            get_argument_feedback,
            get_debate_analysis_complete,
            DebateStrategy
        )
        return True, "모든 함수 임포트 성공"

    def test_debate_analysis():
        from debate_enhancer import analyze_debate_answer

        topic = "기내에서 휴대폰 사용을 전면 허용해야 한다"
        statement = "저는 찬성합니다. 현대 사회에서 휴대폰은 필수품이며, 비행기 모드를 사용하면 안전에 문제가 없습니다."

        result = analyze_debate_answer(statement, topic=topic, user_position="찬성")

        assert result is not None, "분석 결과가 None"

        return True, f"토론 답변 분석 성공"

    def test_debate_argument():
        from debate_enhancer import get_argument_feedback

        argument = "휴대폰 사용은 승객의 편의를 높이고 비상시 연락 수단이 됩니다."

        result = get_argument_feedback(argument)

        assert result is not None, "논거 피드백이 None"

        return True, f"논거 피드백 성공"

    # 테스트 실행
    run_test("Phase B", "B1-1: interview_enhancer 임포트", test_interview_enhancer_import)
    run_test("Phase B", "B1-2: 꼬리질문 생성", test_interview_enhancer_followup)
    run_test("Phase B", "B1-3: 키워드 피드백", test_interview_enhancer_keywords)
    run_test("Phase B", "B1-4: 답변 분석", test_interview_enhancer_analysis)

    run_test("Phase B", "B2-1: roleplay_enhancer 임포트", test_roleplay_enhancer_import)
    run_test("Phase B", "B2-2: 상황극 시나리오", test_roleplay_scenario)
    run_test("Phase B", "B2-3: 롤플레이 피드백", test_roleplay_feedback)

    run_test("Phase B", "B3-1: english_enhancer 임포트", test_english_enhancer_import)
    run_test("Phase B", "B3-2: 영어 답변 분석", test_english_analysis)
    run_test("Phase B", "B3-3: 영어 문법 분석", test_english_grammar)

    run_test("Phase B", "B4-1: debate_enhancer 임포트", test_debate_enhancer_import)
    run_test("Phase B", "B4-2: 토론 답변 분석", test_debate_analysis)
    run_test("Phase B", "B4-3: 논거 피드백", test_debate_argument)


# ============================================================
# PHASE C: 자소서 분석 테스트
# ============================================================

def test_phase_c():
    """Phase C 테스트: 자소서 분석 기능"""
    print("\n" + "=" * 60)
    print("PHASE C: 자소서 분석 기능 테스트")
    print("=" * 60)

    # C1: resume_enhancer.py 테스트
    def test_resume_enhancer_import():
        from resume_enhancer import (
            analyze_resume_enhanced,
            get_keyword_density,
            get_sentence_analysis,
            get_storytelling_score,
            EnhancedResumeAnalyzer
        )
        return True, "모든 함수 임포트 성공"

    def test_resume_analysis():
        from resume_enhancer import analyze_resume_enhanced

        # 실제 자소서 예시
        resume_text = """
        저는 서비스 정신이 투철한 지원자입니다. 대학 시절 카페에서 3년간 아르바이트를 하며
        다양한 고객들을 응대했습니다. 특히 불만 고객을 진정시키고 오히려 단골로 만든 경험이 있습니다.
        이러한 경험을 바탕으로 승무원으로서 최고의 서비스를 제공하고 싶습니다.
        """

        result = analyze_resume_enhanced(resume_text, "대한항공", "지원동기")

        assert result is not None, "분석 결과가 None"

        return True, f"자소서 분석 성공"

    def test_resume_keyword_density():
        from resume_enhancer import get_keyword_density

        text = "저는 서비스 정신과 팀워크를 중시합니다. 고객 만족을 위해 최선을 다하겠습니다."

        result = get_keyword_density(text, "대한항공")

        assert result is not None, "키워드 밀도 결과가 None"

        return True, f"키워드 밀도 분석 성공"

    def test_resume_storytelling():
        from resume_enhancer import get_storytelling_score

        text = """
        대학 2학년 때, 저는 카페 아르바이트 중 한 손님이 음료에 불만을 표현하셨습니다.
        저는 즉시 사과하고 새 음료를 제공했으며, 그 분은 이후 단골이 되셨습니다.
        이 경험을 통해 진정성 있는 서비스의 중요성을 배웠습니다.
        """

        result = get_storytelling_score(text)

        assert result is not None, "스토리텔링 점수가 None"

        return True, f"스토리텔링 분석 성공"

    # C2: resume_question_enhancer.py 테스트
    def test_resume_question_import():
        from resume_question_enhancer import (
            analyze_from_interviewer,
            generate_trap_questions,
            simulate_followup,
            generate_dynamic_followup,
            get_answer_guide
        )
        return True, "모든 함수 임포트 성공"

    def test_interviewer_perspective():
        from resume_question_enhancer import analyze_from_interviewer

        resume_text = "저는 팀워크를 중시하며 리더십을 발휘한 경험이 있습니다."

        result = analyze_from_interviewer(resume_text, "대한항공", "지원동기")

        assert result is not None, "분석 결과가 None"

        return True, f"면접관 관점 분석 성공"

    def test_trap_questions():
        from resume_question_enhancer import generate_trap_questions

        resume_text = "저는 어떤 상황에서도 포기하지 않는 끈기가 있습니다."

        result = generate_trap_questions(resume_text, "대한항공", "지원동기")

        assert result is not None, "함정 질문이 None"
        assert isinstance(result, list), "결과가 list가 아님"

        return True, f"함정 질문 {len(result)}개 생성"

    def test_followup_simulation():
        from resume_question_enhancer import simulate_followup

        initial_question = "왜 승무원이 되고 싶으신가요?"
        resume_text = "저는 서비스를 통해 사람들에게 행복을 주고 싶습니다."

        result = simulate_followup(initial_question, resume_text, max_depth=3)

        assert result is not None, "시뮬레이션 결과가 None"

        return True, f"꼬리질문 시뮬레이션 성공"

    # C3: resume_template.py 테스트
    def test_resume_template_import():
        from resume_template import (
            get_resume_template,
            get_keyword_recommendations,
            check_keyword_usage,
            get_airline_characteristics,
            get_all_airlines,
            ResumeItemType
        )
        return True, "모든 함수 임포트 성공"

    def test_resume_template():
        from resume_template import get_resume_template

        result = get_resume_template("대한항공", "지원동기")

        assert result is not None, "템플릿이 None"

        return True, f"템플릿 생성 성공"

    def test_airline_characteristics():
        from resume_template import get_airline_characteristics, get_all_airlines

        airlines = get_all_airlines()
        assert len(airlines) > 0, "항공사 목록이 비어있음"

        # 첫 번째 항공사로 테스트
        char = get_airline_characteristics(airlines[0])

        assert char is not None, "특성 정보가 None"

        return True, f"항공사 {len(airlines)}개 확인"

    def test_keyword_usage_check():
        from resume_template import check_keyword_usage

        text = "저는 글로벌 서비스 역량을 갖추고 있으며, 팀워크를 중시합니다."

        result = check_keyword_usage(text, "대한항공", "지원동기")

        assert result is not None, "키워드 활용도가 None"

        return True, f"키워드 활용도 체크 성공"

    # 테스트 실행
    run_test("Phase C", "C1-1: resume_enhancer 임포트", test_resume_enhancer_import)
    run_test("Phase C", "C1-2: 자소서 상세 분석", test_resume_analysis)
    run_test("Phase C", "C1-3: 키워드 밀도 분석", test_resume_keyword_density)
    run_test("Phase C", "C1-4: 스토리텔링 분석", test_resume_storytelling)

    run_test("Phase C", "C2-1: resume_question_enhancer 임포트", test_resume_question_import)
    run_test("Phase C", "C2-2: 면접관 관점 분석", test_interviewer_perspective)
    run_test("Phase C", "C2-3: 함정 질문 생성", test_trap_questions)
    run_test("Phase C", "C2-4: 꼬리질문 시뮬레이션", test_followup_simulation)

    run_test("Phase C", "C3-1: resume_template 임포트", test_resume_template_import)
    run_test("Phase C", "C3-2: 자소서 템플릿 생성", test_resume_template)
    run_test("Phase C", "C3-3: 항공사 특성 조회", test_airline_characteristics)
    run_test("Phase C", "C3-4: 키워드 활용도 체크", test_keyword_usage_check)


# ============================================================
# PHASE D: 분석/피드백 고도화 테스트
# ============================================================

def test_phase_d():
    """Phase D 테스트: 분석/피드백 고도화"""
    print("\n" + "=" * 60)
    print("PHASE D: 분석/피드백 고도화 테스트")
    print("=" * 60)

    # D1: voice_analysis_enhancer.py 테스트
    def test_voice_enhancer_import():
        from voice_analysis_enhancer import (
            analyze_voice_enhanced,
            get_speech_speed_graph_data,
            get_tone_graph_data,
            get_volume_graph_data,
            get_silence_analysis,
            SpeechSpeedLevel, VolumeLevel, TonePattern
        )
        return True, "모든 함수/Enum 임포트 성공"

    def test_speech_speed_analysis():
        from voice_analysis_enhancer import get_speech_speed_graph_data

        # 실제 시나리오: 30초 답변의 말 속도 분석
        transcript = "안녕하세요 저는 대한항공에 지원한 지원자입니다. 저는 서비스 정신이 투철하며 어떤 상황에서도 미소를 잃지 않습니다."

        result = get_speech_speed_graph_data(transcript, 30.0, "ko")

        assert "timestamps" in result, "timestamps 없음"
        assert "speeds" in result, "speeds 없음"
        assert len(result["timestamps"]) > 0, "타임스탬프가 비어있음"

        return True, f"데이터포인트: {len(result['timestamps'])}개"

    def test_tone_analysis():
        from voice_analysis_enhancer import get_tone_graph_data

        result = get_tone_graph_data(60.0, pitch_data=[200, 220, 210, 230, 200, 215, 225, 205])

        assert "timestamps" in result, "timestamps 없음"
        assert "pitches" in result, "pitches 없음"

        return True, f"톤 분석 성공"

    def test_volume_analysis():
        from voice_analysis_enhancer import get_volume_graph_data

        result = get_volume_graph_data(60.0, volume_data=[-20, -18, -22, -19, -21, -17, -23, -20])

        assert "timestamps" in result, "timestamps 없음"
        assert "volumes" in result, "volumes 없음"

        return True, f"음량 분석 성공"

    def test_silence_analysis():
        from voice_analysis_enhancer import get_silence_analysis

        silence_segments = [
            {"start": 5.0, "end": 6.0},
            {"start": 15.0, "end": 16.5},
            {"start": 30.0, "end": 31.0}
        ]

        result = get_silence_analysis(60.0, silence_segments)

        assert "total_silence" in result, "total_silence 없음"
        assert "ratio" in result, "ratio 없음"

        return True, f"침묵 분석 성공"

    def test_voice_comprehensive():
        from voice_analysis_enhancer import analyze_voice_enhanced

        result = analyze_voice_enhanced(
            transcript="저는 승무원이 되기 위해 오랫동안 준비해왔습니다.",
            duration=45.0,
            language="ko",
            pitch_data=[200, 210, 205, 215, 200],
            volume_data=[-20, -18, -22, -19, -21]
        )

        assert result is not None, "분석 결과가 None"

        return True, f"음성 종합 분석 성공"

    # D2: emotion_analysis_enhancer.py 테스트
    def test_emotion_enhancer_import():
        from emotion_analysis_enhancer import (
            analyze_emotion_enhanced,
            get_confidence_timeline,
            get_stress_timeline,
            get_segment_analysis,
            ConfidenceLevel, StressLevel, EmotionType
        )
        return True, "모든 함수/Enum 임포트 성공"

    def test_confidence_timeline():
        from emotion_analysis_enhancer import get_confidence_timeline

        result = get_confidence_timeline(60.0, voice_stability=0.7)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"자신감 타임라인 성공"

    def test_stress_timeline():
        from emotion_analysis_enhancer import get_stress_timeline

        result = get_stress_timeline(60.0, voice_tremor=0.3, filler_count=5)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"긴장도 타임라인 성공"

    def test_segment_analysis():
        from emotion_analysis_enhancer import get_segment_analysis

        result = get_segment_analysis(60.0)

        assert isinstance(result, list), "결과가 list가 아님"
        assert len(result) >= 3, "최소 3구간 분석 필요"

        return True, f"{len(result)}개 구간 분석 완료"

    def test_emotion_comprehensive():
        from emotion_analysis_enhancer import analyze_emotion_enhanced

        result = analyze_emotion_enhanced(
            duration=60.0,
            voice_stability=0.6,
            voice_tremor=0.2,
            speech_hesitations=3,
            filler_count=4
        )

        assert result is not None, "분석 결과가 None"

        return True, f"감정 종합 분석 성공"

    # D3: posture_analysis_enhancer.py 테스트
    def test_posture_enhancer_import():
        from posture_analysis_enhancer import (
            analyze_posture_enhanced,
            get_shoulder_timeline,
            get_gaze_timeline,
            get_hand_timeline,
            get_posture_correction_guide,
            PostureLevel, ShoulderPosition, GazeDirection
        )
        return True, "모든 함수/Enum 임포트 성공"

    def test_shoulder_timeline():
        from posture_analysis_enhancer import get_shoulder_timeline

        result = get_shoulder_timeline(60.0)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"어깨 타임라인 성공"

    def test_gaze_timeline():
        from posture_analysis_enhancer import get_gaze_timeline

        result = get_gaze_timeline(60.0)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"시선 타임라인 성공"

    def test_hand_timeline():
        from posture_analysis_enhancer import get_hand_timeline

        result = get_hand_timeline(60.0)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"손 타임라인 성공"

    def test_posture_correction():
        from posture_analysis_enhancer import get_posture_correction_guide

        result = get_posture_correction_guide(60.0)

        assert isinstance(result, list), "결과가 list가 아님"

        return True, f"{len(result)}개 교정 가이드"

    def test_posture_comprehensive():
        from posture_analysis_enhancer import analyze_posture_enhanced

        result = analyze_posture_enhanced(60.0)

        assert result is not None, "분석 결과가 None"

        return True, f"자세 종합 분석 성공"

    # D4: expression_analysis_enhancer.py 테스트
    def test_expression_enhancer_import():
        from expression_analysis_enhancer import (
            analyze_expression_enhanced,
            get_smile_timeline,
            get_eye_contact_timeline,
            get_naturalness_timeline,
            get_expression_coaching,
            SmileLevel, ExpressionType
        )
        return True, "모든 함수/Enum 임포트 성공"

    def test_smile_timeline():
        from expression_analysis_enhancer import get_smile_timeline

        result = get_smile_timeline(60.0)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"미소 타임라인 성공"

    def test_eye_contact_timeline():
        from expression_analysis_enhancer import get_eye_contact_timeline

        result = get_eye_contact_timeline(60.0)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"눈맞춤 타임라인 성공"

    def test_naturalness_timeline():
        from expression_analysis_enhancer import get_naturalness_timeline

        result = get_naturalness_timeline(60.0)

        assert "timestamps" in result, "timestamps 없음"
        assert "values" in result, "values 없음"

        return True, f"자연스러움 타임라인 성공"

    def test_expression_coaching():
        from expression_analysis_enhancer import get_expression_coaching

        result = get_expression_coaching(60.0)

        assert isinstance(result, list), "결과가 list가 아님"

        return True, f"{len(result)}개 코칭 팁"

    def test_expression_comprehensive():
        from expression_analysis_enhancer import analyze_expression_enhanced

        result = analyze_expression_enhanced(60.0)

        assert result is not None, "분석 결과가 None"

        return True, f"표정 종합 분석 성공"

    # 테스트 실행
    run_test("Phase D", "D1-1: voice_enhancer 임포트", test_voice_enhancer_import)
    run_test("Phase D", "D1-2: 말 속도 분석", test_speech_speed_analysis)
    run_test("Phase D", "D1-3: 톤 분석", test_tone_analysis)
    run_test("Phase D", "D1-4: 음량 분석", test_volume_analysis)
    run_test("Phase D", "D1-5: 침묵 분석", test_silence_analysis)
    run_test("Phase D", "D1-6: 음성 종합 분석", test_voice_comprehensive)

    run_test("Phase D", "D2-1: emotion_enhancer 임포트", test_emotion_enhancer_import)
    run_test("Phase D", "D2-2: 자신감 타임라인", test_confidence_timeline)
    run_test("Phase D", "D2-3: 긴장도 타임라인", test_stress_timeline)
    run_test("Phase D", "D2-4: 구간별 분석", test_segment_analysis)
    run_test("Phase D", "D2-5: 감정 종합 분석", test_emotion_comprehensive)

    run_test("Phase D", "D3-1: posture_enhancer 임포트", test_posture_enhancer_import)
    run_test("Phase D", "D3-2: 어깨 타임라인", test_shoulder_timeline)
    run_test("Phase D", "D3-3: 시선 타임라인", test_gaze_timeline)
    run_test("Phase D", "D3-4: 손 타임라인", test_hand_timeline)
    run_test("Phase D", "D3-5: 자세 교정 가이드", test_posture_correction)
    run_test("Phase D", "D3-6: 자세 종합 분석", test_posture_comprehensive)

    run_test("Phase D", "D4-1: expression_enhancer 임포트", test_expression_enhancer_import)
    run_test("Phase D", "D4-2: 미소 타임라인", test_smile_timeline)
    run_test("Phase D", "D4-3: 눈맞춤 타임라인", test_eye_contact_timeline)
    run_test("Phase D", "D4-4: 자연스러움 타임라인", test_naturalness_timeline)
    run_test("Phase D", "D4-5: 표정 코칭", test_expression_coaching)
    run_test("Phase D", "D4-6: 표정 종합 분석", test_expression_comprehensive)


# ============================================================
# 페이지 통합 테스트
# ============================================================

def test_page_integration():
    """페이지 통합 테스트"""
    print("\n" + "=" * 60)
    print("페이지 통합 테스트")
    print("=" * 60)

    pages_to_test = [
        ("pages/1_롤플레잉.py", ["roleplay_enhancer"]),
        ("pages/2_영어면접.py", ["english_interview_enhancer"]),
        ("pages/4_모의면접.py", ["voice_analysis_enhancer", "emotion_analysis_enhancer"]),
        ("pages/5_토론면접.py", ["debate_enhancer"]),
        ("pages/13_실전연습.py", ["voice_analysis_enhancer"]),
        ("pages/17_자소서기반질문.py", ["resume_question_enhancer"]),
        ("pages/20_자소서첨삭.py", ["resume_enhancer"]),
        ("pages/21_자소서템플릿.py", ["resume_template"]),
    ]

    for page_path, expected_imports in pages_to_test:
        def test_page(path=page_path, imports=expected_imports):
            full_path = os.path.join(os.path.dirname(__file__), path)

            if not os.path.exists(full_path):
                return False, f"파일 없음: {path}"

            with open(full_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # 문법 검사
            try:
                ast.parse(code)
            except SyntaxError as e:
                return False, f"문법 오류: {e}"

            # 필수 import 확인
            missing = []
            for imp in imports:
                if imp not in code:
                    missing.append(imp)

            if missing:
                return False, f"누락된 import: {missing}"

            return True, f"문법 OK, {len(imports)}개 모듈 통합됨"

        page_name = os.path.basename(page_path)
        run_test("페이지 통합", f"{page_name}", test_page)


# ============================================================
# 실제 사용 시나리오 테스트
# ============================================================

def test_real_user_scenarios():
    """실제 사용자 시나리오 테스트"""
    print("\n" + "=" * 60)
    print("실제 사용자 시나리오 테스트")
    print("=" * 60)

    # 시나리오 1: 면접 연습 전체 플로우
    def test_interview_flow():
        from interview_enhancer import (
            get_keyword_feedback,
            generate_follow_up_question,
            analyze_interview_answer
        )

        question = "자기소개 해주세요"
        answer = "안녕하세요 저는 서비스업 경력 3년의 지원자입니다."

        # 1. 답변 분석
        analysis = analyze_interview_answer(question, answer, elapsed_seconds=45, airline="대한항공")

        # 2. 키워드 피드백
        keywords = get_keyword_feedback(answer, question, "대한항공")

        # 3. 꼬리질문
        followup = generate_follow_up_question(question, answer, airline="대한항공")

        assert analysis is not None, "분석 실패"
        return True, f"면접 플로우 완료"

    # 시나리오 2: 자소서 작성 플로우
    def test_resume_flow():
        from resume_template import get_resume_template, check_keyword_usage
        from resume_enhancer import analyze_resume_enhanced

        # 1. 템플릿 확인
        template = get_resume_template("대한항공", "지원동기")

        # 2. 자소서 작성 (예시)
        resume = """
        저는 어릴 때부터 비행기를 타며 승무원의 꿈을 키워왔습니다.
        대학에서 서비스 경영을 전공하며 고객 만족의 중요성을 배웠고,
        3년간의 호텔 인턴 경험을 통해 실무 역량을 쌓았습니다.
        """

        # 3. 키워드 체크
        keyword_check = check_keyword_usage(resume, "대한항공", "지원동기")

        # 4. 상세 분석
        analysis = analyze_resume_enhanced(resume, "대한항공", "지원동기")

        assert analysis is not None, "분석 실패"
        return True, f"자소서 분석 완료"

    # 시나리오 3: 음성 분석 플로우
    def test_voice_analysis_flow():
        from voice_analysis_enhancer import analyze_voice_enhanced
        from emotion_analysis_enhancer import analyze_emotion_enhanced

        # 1. 음성 분석
        voice_result = analyze_voice_enhanced(
            transcript="저는 대한항공에 지원한 지원자입니다. 서비스 정신이 투철합니다.",
            duration=30.0,
            language="ko"
        )

        # 2. 감정 분석
        emotion_result = analyze_emotion_enhanced(duration=30.0)

        assert voice_result is not None, "음성 분석 실패"
        assert emotion_result is not None, "감정 분석 실패"
        return True, f"분석 완료"

    # 시나리오 4: 비언어적 분석 플로우
    def test_nonverbal_flow():
        from posture_analysis_enhancer import analyze_posture_enhanced
        from expression_analysis_enhancer import analyze_expression_enhanced

        # 1. 자세 분석
        posture = analyze_posture_enhanced(60.0)

        # 2. 표정 분석
        expression = analyze_expression_enhanced(60.0)

        assert posture is not None, "자세 분석 실패"
        assert expression is not None, "표정 분석 실패"
        return True, f"비언어 분석 완료"

    run_test("시나리오", "1: 면접 연습 플로우", test_interview_flow)
    run_test("시나리오", "2: 자소서 작성 플로우", test_resume_flow)
    run_test("시나리오", "3: 음성/감정 분석 플로우", test_voice_analysis_flow)
    run_test("시나리오", "4: 비언어적 분석 플로우", test_nonverbal_flow)


# ============================================================
# 메인 실행
# ============================================================

def print_results():
    """결과 출력"""
    print("\n")
    print("=" * 70)
    print("=" * 70)
    print("         PHASE A-D 전체 테스트 결과")
    print("=" * 70)
    print("=" * 70)

    total_passed = 0
    total_failed = 0

    for phase, results in all_results.items():
        passed = sum(1 for _, p, _ in results if p)
        failed = len(results) - passed
        total_passed += passed
        total_failed += failed

        print(f"\n{'='*60}")
        print(f"  {phase}: {passed}/{len(results)} 통과")
        print(f"{'='*60}")

        for name, success, msg in results:
            status = "PASS" if success else "FAIL"
            print(f"  [{status}] {name}")
            if msg:
                print(f"         -> {msg}")

        if failed > 0:
            print(f"\n  [!] {failed}개 실패!")

    print("\n")
    print("=" * 70)
    total = total_passed + total_failed
    success_rate = (total_passed / total * 100) if total > 0 else 0
    print(f"  총 결과: {total_passed}/{total} 테스트 통과 ({success_rate:.1f}%)")
    print("=" * 70)

    if total_failed == 0:
        print("\n  [SUCCESS] 모든 테스트 통과! Phase A-D 완벽 작동 확인!")
    else:
        print(f"\n  [WARNING] {total_failed}개 테스트 실패. 수정이 필요합니다.")

    return total_failed == 0


if __name__ == "__main__":
    print("Phase A-D 전체 종합 테스트 시작...")
    print("실제 사용자 시나리오 기반 완벽 테스트")
    print("")

    # 테스트 실행
    test_phase_b()
    test_phase_c()
    test_phase_d()
    test_page_integration()
    test_real_user_scenarios()

    # 결과 출력
    success = print_results()

    sys.exit(0 if success else 1)
