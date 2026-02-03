# -*- coding: utf-8 -*-
"""
enhancement_integrator.py
A-G 개선사항 통합 모듈

모든 페이지에서 import하여 사용할 수 있는 통합 인터페이스 제공
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# 모듈 경로 추가
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# 모듈 가용성 플래그
# ============================================================

MODULES_AVAILABLE = {
    "user_experience": False,  # A. 심리적/감정적
    "functional": False,       # B. 기능적
    "learning": False,         # C. 학습 경험
    "realism": False,          # D. 현실성
    "accessibility": False,    # E. 접근성
    "content": False,          # F. 콘텐츠
    "uiux": False,             # G. UI/UX
}


# ============================================================
# A. 심리적/감정적 모듈 Import
# ============================================================

try:
    from user_experience_enhancer import (
        generate_learning_path,
        predict_pass_probability,
        find_study_partners,
        get_daily_missions,
        check_streak,
        get_leaderboard,
        get_encouragement,
        get_progress_celebration,
        LearningPathGenerator,
        GamificationSystem,
    )
    MODULES_AVAILABLE["user_experience"] = True
except ImportError:
    pass


# ============================================================
# B. 기능적 모듈 Import
# ============================================================

try:
    from functional_enhancer import (
        validate_stt,
        start_progress_tracking,
        update_progress as update_func_progress,
        get_progress_message,
        get_realtime_coaching,
        analyze_pronunciation,
        analyze_nonverbal_extended,
        create_session,
        update_session,
        recover_session,
        STTResult,
        ProgressTracker,
        SessionManager,
    )
    MODULES_AVAILABLE["functional"] = True
except ImportError:
    pass


# ============================================================
# C. 학습 경험 모듈 Import
# ============================================================

try:
    from learning_experience_enhancer import (
        generate_personalized_plan,
        detect_weaknesses,
        get_focus_recommendation,
        create_milestones,
        get_next_milestone,
        predict_growth,
        analyze_failure,
        get_priority_improvement,
    )
    MODULES_AVAILABLE["learning"] = True
except ImportError:
    pass


# ============================================================
# D. 현실성 모듈 Import
# ============================================================

try:
    from realism_enhancer import (
        create_multi_interviewer_session,
        get_next_interviewer_question,
        generate_pressure_question,
        get_random_surprise,
        get_condition_settings,
        get_environment_preset,
        check_time_status,
    )
    MODULES_AVAILABLE["realism"] = True
except ImportError:
    pass


# ============================================================
# E. 접근성 모듈 Import
# ============================================================

try:
    from accessibility_enhancer import (
        detect_device_type,
        get_mobile_css,
        get_responsive_settings,
        create_notification,
        schedule_study_reminder,
        cache_content,
        get_cached_content,
        get_cache_status,
        report_voice_error,
        get_input_mode_ui,
        reset_voice_mode,
    )
    MODULES_AVAILABLE["accessibility"] = True
except ImportError:
    pass


# ============================================================
# F. 콘텐츠 모듈 Import
# ============================================================

try:
    from content_enhancer import (
        get_passer_examples,
        compare_with_passer,
        get_trap_questions,
        get_random_trap_question,
        get_emergency_scenario,
        evaluate_emergency_response,
        get_mbti_profile,
        get_mbti_feedback,
    )
    MODULES_AVAILABLE["content"] = True
except ImportError:
    pass


# ============================================================
# G. UI/UX 모듈 Import
# ============================================================

try:
    from uiux_enhancer import (
        get_standard_term,
        standardize_term,
        get_all_standard_terms,
        init_progress,
        update_progress as update_ui_progress,
        get_progress_html,
        get_navigation_config,
        get_back_button_html,
        get_breadcrumb_html,
        get_loading_content,
        get_loading_html,
    )
    MODULES_AVAILABLE["uiux"] = True
except ImportError:
    pass


# ============================================================
# 통합 헬퍼 클래스
# ============================================================

class EnhancementIntegrator:
    """개선사항 통합 관리자"""

    def __init__(self, user_id: str = "anonymous"):
        self.user_id = user_id
        self._session_id = None

    @property
    def available_modules(self) -> Dict[str, bool]:
        """사용 가능한 모듈 목록"""
        return MODULES_AVAILABLE.copy()

    def is_available(self, module_name: str) -> bool:
        """특정 모듈 사용 가능 여부"""
        return MODULES_AVAILABLE.get(module_name, False)

    # ---- A. 심리적/감정적 ----

    def get_user_dashboard_data(self, practice_dates: List[datetime] = None) -> Dict[str, Any]:
        """사용자 대시보드 데이터 (스트릭, 미션, 리더보드)"""
        data = {
            "streak": 0,
            "missions": [],
            "leaderboard": [],
            "encouragement": None
        }

        if not MODULES_AVAILABLE["user_experience"]:
            return data

        try:
            if practice_dates:
                streak_info = check_streak(practice_dates)
                data["streak"] = streak_info.current_streak

            data["missions"] = get_daily_missions(self.user_id)
            data["leaderboard"] = get_leaderboard(limit=5)
            data["encouragement"] = get_encouragement(score=70, streak=data["streak"])
        except Exception:
            pass

        return data

    def get_learning_path(self, airline: str, target_date: datetime = None, weak_areas: List[str] = None):
        """맞춤 학습 경로 생성"""
        if not MODULES_AVAILABLE["user_experience"]:
            return None

        try:
            return generate_learning_path(
                user_id=self.user_id,
                target_airline=airline,
                target_date=target_date or (datetime.now() + timedelta(days=30)),
                weak_areas=weak_areas or []
            )
        except Exception:
            return None

    def get_pass_prediction(self, airline: str, score_history: List[Dict]) -> Optional[Dict]:
        """합격 예측"""
        if not MODULES_AVAILABLE["user_experience"]:
            return None

        try:
            result = predict_pass_probability(airline, score_history, 1.0)
            return {
                "current_score": result.current_score,
                "target_score": result.target_score,
                "probability": result.probability,
                "predicted_days": result.predicted_days,
                "message": result.message
            }
        except Exception:
            return None

    # ---- B. 기능적 ----

    def start_session(self, page_type: str, initial_data: Dict = None) -> str:
        """세션 시작"""
        if not MODULES_AVAILABLE["functional"]:
            return ""

        try:
            self._session_id = create_session(self.user_id, page_type, initial_data or {})
            return self._session_id
        except Exception:
            return ""

    def update_current_session(self, data: Dict) -> bool:
        """현재 세션 업데이트"""
        if not MODULES_AVAILABLE["functional"] or not self._session_id:
            return False

        try:
            return update_session(self._session_id, data)
        except Exception:
            return False

    def get_realtime_feedback(self, speech_speed: float = None, volume: float = None,
                               silence_ratio: float = None) -> Optional[Dict]:
        """실시간 코칭 피드백"""
        if not MODULES_AVAILABLE["functional"]:
            return None

        try:
            coaching = get_realtime_coaching(
                speech_speed=speech_speed,
                volume=volume,
                silence_ratio=silence_ratio
            )
            if coaching:
                return {
                    "type": coaching.coaching_type,
                    "message": coaching.message,
                    "severity": coaching.severity
                }
        except Exception:
            pass

        return None

    def validate_speech_text(self, text: str, confidence: float = 0.8) -> Dict:
        """음성 인식 결과 검증"""
        if not MODULES_AVAILABLE["functional"]:
            return {"final_text": text, "confidence": confidence}

        try:
            stt_result = STTResult(text=text, confidence=confidence, source="primary")
            validated = validate_stt(stt_result)
            return {
                "final_text": validated.final_text,
                "confidence": validated.confidence,
                "corrections": validated.corrections
            }
        except Exception:
            return {"final_text": text, "confidence": confidence}

    # ---- C. 학습 경험 ----

    def get_personalized_learning_plan(self, airline: str, target_date: datetime,
                                        current_scores: Dict[str, float]) -> Optional[Dict]:
        """맞춤 학습 계획"""
        if not MODULES_AVAILABLE["learning"]:
            return None

        try:
            plan = generate_personalized_plan(
                user_id=self.user_id,
                target_airline=airline,
                target_date=target_date,
                current_scores=current_scores
            )
            return {
                "total_weeks": plan.total_weeks,
                "priority_skills": plan.priority_skills,
                "weekly_plans": [
                    {"week": w.week_number, "focus": w.focus_area, "goals": w.goals}
                    for w in plan.weekly_plans
                ]
            }
        except Exception:
            return None

    def analyze_weaknesses(self, skill_scores: Dict[str, float], target: int = 80) -> List[Dict]:
        """약점 분석"""
        if not MODULES_AVAILABLE["learning"]:
            return []

        try:
            weaknesses = detect_weaknesses(skill_scores, target)
            return [
                {"skill": w.skill_name, "current": w.current_score, "gap": w.gap}
                for w in weaknesses
            ]
        except Exception:
            return []

    def get_growth_prediction(self, score_history: List[Dict], target: int = 85) -> Optional[Dict]:
        """성장 예측"""
        if not MODULES_AVAILABLE["learning"]:
            return None

        try:
            prediction = predict_growth(score_history, target)
            return {
                "days_to_target": prediction.days_to_target,
                "growth_rate": prediction.growth_rate,
                "predicted_score": prediction.predicted_score,
                "confidence": prediction.confidence
            }
        except Exception:
            return None

    # ---- D. 현실성 ----

    def create_realistic_interview(self, airline: str, num_interviewers: int = 2) -> Optional[Dict]:
        """현실적 면접 세션 생성"""
        if not MODULES_AVAILABLE["realism"]:
            return None

        try:
            session = create_multi_interviewer_session(airline, num_interviewers)
            return {
                "session_id": session.session_id,
                "interviewers": [
                    {"name": i.name, "role": i.role, "style": i.style}
                    for i in session.interviewers
                ]
            }
        except Exception:
            return None

    def get_pressure_question(self, question_type: str = "random") -> Optional[Dict]:
        """압박 질문 생성"""
        if not MODULES_AVAILABLE["realism"]:
            return None

        try:
            q = generate_pressure_question(question_type)
            return {
                "question": q.question,
                "category": q.category,
                "tips": q.tips,
                "difficulty": q.difficulty
            }
        except Exception:
            return None

    def get_surprise_situation(self) -> Optional[Dict]:
        """돌발 상황 생성"""
        if not MODULES_AVAILABLE["realism"]:
            return None

        try:
            surprise = get_random_surprise()
            return {
                "title": surprise.title,
                "description": surprise.description,
                "expected_response": surprise.expected_response,
                "criteria": surprise.scoring_criteria
            }
        except Exception:
            return None

    # ---- E. 접근성 ----

    def get_responsive_css(self) -> str:
        """반응형 CSS"""
        if not MODULES_AVAILABLE["accessibility"]:
            return ""

        try:
            return get_mobile_css()
        except Exception:
            return ""

    def detect_device(self, screen_width: int) -> str:
        """디바이스 타입 감지"""
        if not MODULES_AVAILABLE["accessibility"]:
            if screen_width < 768:
                return "mobile"
            elif screen_width < 1024:
                return "tablet"
            return "desktop"

        try:
            return detect_device_type(screen_width)
        except Exception:
            return "desktop"

    def handle_voice_error(self, error_msg: str) -> Dict:
        """음성 에러 처리"""
        if not MODULES_AVAILABLE["accessibility"]:
            return {"show_text_input": True, "error_count": 1}

        try:
            status = report_voice_error(error_msg)
            return {
                "show_text_input": status.fallback_to_text,
                "error_count": status.voice_error_count,
                "mode": status.current_mode
            }
        except Exception:
            return {"show_text_input": True, "error_count": 1}

    # ---- F. 콘텐츠 ----

    def get_passer_comparison(self, user_answer: str, question: str) -> Optional[Dict]:
        """합격자 답변 비교"""
        if not MODULES_AVAILABLE["content"]:
            return None

        try:
            comparison = compare_with_passer(user_answer, question)
            return {
                "similarity": comparison.similarity_score,
                "missing_elements": comparison.missing_elements,
                "tips": comparison.improvement_tips
            }
        except Exception:
            return None

    def get_airline_trap_questions(self, airline: str) -> List[Dict]:
        """항공사별 함정 질문"""
        if not MODULES_AVAILABLE["content"]:
            return []

        try:
            questions = get_trap_questions(airline)
            return [
                {"question": q.question, "trap": q.trap_point, "tips": q.tips}
                for q in questions
            ]
        except Exception:
            return []

    def get_mbti_customized_feedback(self, mbti: str, score: float, category: str) -> Optional[Dict]:
        """MBTI 맞춤 피드백"""
        if not MODULES_AVAILABLE["content"]:
            return None

        try:
            profile = get_mbti_profile(mbti)
            feedback = get_mbti_feedback(mbti, score, category)
            return {
                "strengths": profile.strengths,
                "weaknesses": profile.weaknesses,
                "interview_tips": profile.interview_tips,
                "specific_tips": feedback.get("specific_tips", [])
            }
        except Exception:
            return None

    # ---- G. UI/UX ----

    def get_standardized_ui_text(self, term_id: str) -> str:
        """표준화된 UI 텍스트"""
        if not MODULES_AVAILABLE["uiux"]:
            return term_id

        try:
            return get_standard_term(term_id)
        except Exception:
            return term_id

    def get_page_progress(self, page_name: str, current_step: int = 0) -> Dict:
        """페이지 진행 상태"""
        if not MODULES_AVAILABLE["uiux"]:
            return {"html": "", "percent": 0}

        try:
            state = init_progress(page_name)
            if current_step > 0:
                state = update_ui_progress(page_name, current_step)
            html = get_progress_html(state)
            return {
                "html": html,
                "percent": state.percent,
                "step_name": state.step_name,
                "fraction": state.fraction_text
            }
        except Exception:
            return {"html": "", "percent": 0}

    def get_page_navigation(self, page_name: str) -> Dict:
        """페이지 네비게이션"""
        if not MODULES_AVAILABLE["uiux"]:
            return {"back_html": "", "breadcrumb_html": ""}

        try:
            return {
                "back_html": get_back_button_html(page_name),
                "breadcrumb_html": get_breadcrumb_html(page_name)
            }
        except Exception:
            return {"back_html": "", "breadcrumb_html": ""}

    def get_loading_screen(self, category: str = "general", progress: int = None) -> str:
        """로딩 화면 HTML"""
        if not MODULES_AVAILABLE["uiux"]:
            return "<div>로딩 중...</div>"

        try:
            return get_loading_html(category, progress)
        except Exception:
            return "<div>로딩 중...</div>"


# ============================================================
# Streamlit 통합 헬퍼 함수
# ============================================================

def get_enhanced_page_css() -> str:
    """향상된 페이지 CSS (모바일 포함)"""
    css = ""

    # 모바일 반응형 CSS
    if MODULES_AVAILABLE["accessibility"]:
        try:
            mobile_css = get_mobile_css()
            if mobile_css:
                css = f"<style>{mobile_css}</style>"
        except Exception:
            pass

    # 기본 반응형 폴백
    if not css:
        css = """
        <style>
        @media (max-width: 768px) {
            .main .block-container {
                padding: 1rem !important;
            }
            .stButton > button {
                width: 100%;
                min-height: 48px;
            }
        }
        </style>
        """

    return css


def show_encouragement_toast(score: int = 0, streak: int = 0, previous_score: int = 0) -> Optional[str]:
    """격려 메시지 토스트용 HTML"""
    if not MODULES_AVAILABLE["user_experience"]:
        return None

    try:
        msg = get_encouragement(score, previous_score, streak)
        if msg:
            return f"""
            <div class="encouragement-toast" style="
                position: fixed; bottom: 24px; right: 24px;
                background: linear-gradient(135deg, #10b981, #059669);
                color: white; padding: 16px 24px; border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                animation: slideIn 0.3s ease; z-index: 9999;
            ">
                <span style="font-size: 1.5rem; margin-right: 8px;">{msg.emoji}</span>
                <span style="font-weight: 600;">{msg.message}</span>
            </div>
            <style>
            @keyframes slideIn {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
            </style>
            """
    except Exception:
        pass

    return None


def get_streak_display_html(practice_dates: List[datetime]) -> str:
    """스트릭 표시 HTML"""
    if not MODULES_AVAILABLE["user_experience"]:
        return ""

    try:
        streak_info = check_streak(practice_dates)

        streak_color = "#10b981" if streak_info.current_streak >= 7 else (
            "#f59e0b" if streak_info.current_streak >= 3 else "#64748b"
        )

        return f"""
        <div style="
            display: inline-flex; align-items: center; gap: 8px;
            background: {streak_color}15; padding: 8px 16px;
            border-radius: 20px; border: 1px solid {streak_color}40;
        ">
            <span style="font-size: 1.2rem;">{'🔥' if streak_info.is_on_fire else '📅'}</span>
            <span style="font-weight: 700; color: {streak_color};">{streak_info.current_streak}일 연속</span>
        </div>
        """
    except Exception:
        return ""


def get_daily_missions_html(user_id: str = "anonymous") -> str:
    """일일 미션 HTML"""
    if not MODULES_AVAILABLE["user_experience"]:
        return ""

    try:
        missions = get_daily_missions(user_id)

        items_html = ""
        for m in missions[:3]:  # 최대 3개
            check = "✓" if m.is_completed else "○"
            color = "#10b981" if m.is_completed else "#64748b"
            items_html += f"""
            <div style="display: flex; align-items: center; gap: 12px;
                        padding: 12px; background: #f8fafc; border-radius: 8px; margin-bottom: 8px;">
                <span style="color: {color}; font-size: 1.2rem;">{check}</span>
                <div>
                    <div style="font-weight: 600; color: #334155;">{m.title}</div>
                    <div style="font-size: 0.8rem; color: #64748b;">+{m.reward_xp} XP</div>
                </div>
            </div>
            """

        return f"""
        <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
            <div style="font-weight: 700; color: #1e3a5f; margin-bottom: 16px;">오늘의 미션</div>
            {items_html}
        </div>
        """
    except Exception:
        return ""


# ============================================================
# 전역 인스턴스
# ============================================================

# 기본 통합 객체 (페이지에서 바로 사용 가능)
enhancer = EnhancementIntegrator()


def get_enhancer(user_id: str = "anonymous") -> EnhancementIntegrator:
    """사용자별 통합 객체 생성"""
    return EnhancementIntegrator(user_id)


# ============================================================
# 모듈 상태 체크 함수
# ============================================================

def check_all_modules() -> Dict[str, bool]:
    """모든 모듈 상태 확인"""
    return MODULES_AVAILABLE.copy()


def get_module_status_html() -> str:
    """모듈 상태 HTML (디버그용)"""
    status_html = "<div style='font-size: 0.8rem; color: #64748b;'>"

    module_names = {
        "user_experience": "A. 심리적",
        "functional": "B. 기능적",
        "learning": "C. 학습경험",
        "realism": "D. 현실성",
        "accessibility": "E. 접근성",
        "content": "F. 콘텐츠",
        "uiux": "G. UI/UX"
    }

    for key, name in module_names.items():
        available = MODULES_AVAILABLE[key]
        icon = "✓" if available else "✗"
        color = "#10b981" if available else "#ef4444"
        status_html += f"<span style='color: {color}; margin-right: 12px;'>{icon} {name}</span>"

    status_html += "</div>"
    return status_html
