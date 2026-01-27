# english_interview_report.py
# 영어면접 PDF 리포트 생성 및 약점 기반 추천

import os
import io
from datetime import datetime
from typing import Dict, List, Any, Optional

from fpdf import FPDF

# 영어면접 질문 데이터 import
try:
    from english_interview_data import ENGLISH_QUESTIONS, get_all_categories
except ImportError:
    ENGLISH_QUESTIONS = {}
    def get_all_categories():
        return []


# =====================
# 한글 폰트 설정
# =====================

FONT_PATHS = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/NanumGothic.ttf",
    "C:/Windows/Fonts/gulim.ttc",
]


def get_korean_font_path() -> Optional[str]:
    """사용 가능한 한글 폰트 경로 반환"""
    for path in FONT_PATHS:
        if os.path.exists(path):
            return path
    return None


# =====================
# 약점 기반 질문 추천
# =====================

WEAKNESS_QUESTION_MAP = {
    # 음성 분석 약점
    "tremor": {
        "description": "목소리 떨림",
        "recommended_categories": ["self_introduction"],
        "tip": "쉬운 자기소개부터 연습하며 자신감을 쌓으세요."
    },
    "ending_clarity": {
        "description": "말끝 흐림",
        "recommended_categories": ["service", "motivation"],
        "tip": "문장 끝까지 또렷하게 발음하는 연습을 하세요."
    },
    "pitch_variation": {
        "description": "억양 단조로움",
        "recommended_categories": ["situational", "service"],
        "tip": "감정을 담아 말하는 연습이 필요합니다."
    },
    "service_tone": {
        "description": "서비스 톤 부족",
        "recommended_categories": ["service", "motivation"],
        "tip": "밝고 친근한 톤으로 말하는 연습을 하세요."
    },
    "composure": {
        "description": "침착함 부족",
        "recommended_categories": ["self_introduction"],
        "tip": "심호흡 후 천천히 말하는 습관을 들이세요."
    },

    # 텍스트 분석 약점
    "speech_rate": {
        "description": "말 속도 문제",
        "recommended_categories": ["self_introduction", "motivation"],
        "tip": "적정 속도(120-150 WPM)로 말하는 연습을 하세요."
    },
    "filler_words": {
        "description": "추임새 과다 (um, uh 등)",
        "recommended_categories": ["teamwork", "service"],
        "tip": "'um', 'uh' 대신 잠시 멈추는 연습을 하세요."
    },
    "pauses": {
        "description": "휴지/끊김 많음",
        "recommended_categories": ["motivation", "service"],
        "tip": "답변을 미리 정리하고 말하는 연습을 하세요."
    },

    # 영어 실력 약점
    "grammar": {
        "description": "문법 오류 다수",
        "recommended_categories": ["self_introduction", "teamwork"],
        "tip": "기본 시제와 주어-동사 일치를 확인하세요."
    },
    "vocabulary": {
        "description": "어휘력 부족",
        "recommended_categories": ["service", "safety"],
        "tip": "항공 관련 어휘와 서비스 표현을 암기하세요."
    },
    "pronunciation": {
        "description": "발음 불명확",
        "recommended_categories": ["self_introduction"],
        "tip": "핵심 단어 발음을 정확히 연습하세요."
    },
}


def get_weakness_recommendations_english(
    voice_analysis: Dict[str, Any],
    text_evaluation: str = "",
    max_recommendations: int = 5
) -> List[Dict[str, Any]]:
    """
    약점 분석 기반 영어면접 질문 추천
    """
    weaknesses = []

    # 1. 음성 분석에서 약점 추출
    if voice_analysis:
        voice_detail = voice_analysis.get("voice_analysis", {})
        text_detail = voice_analysis.get("text_analysis", {})

        for key in ["tremor", "ending_clarity", "pitch_variation", "service_tone", "composure"]:
            if voice_detail.get(key, {}).get("score", 10) <= 6:
                weaknesses.append((key, voice_detail[key].get("score", 0)))

        for key in ["speech_rate", "filler_words", "pauses"]:
            if text_detail.get(key, {}).get("score", 10) <= 6:
                weaknesses.append((key, text_detail[key].get("score", 0)))

    # 2. 텍스트 평가에서 약점 추출
    if text_evaluation:
        eval_lower = text_evaluation.lower()
        if "grammar" in eval_lower or "문법" in eval_lower:
            weaknesses.append(("grammar", 4))
        if "vocabulary" in eval_lower or "어휘" in eval_lower:
            weaknesses.append(("vocabulary", 5))
        if "pronunciation" in eval_lower or "발음" in eval_lower:
            weaknesses.append(("pronunciation", 5))

    # 3. 점수 낮은 순 정렬
    weaknesses.sort(key=lambda x: x[1])

    # 4. 약점별 질문 추천
    recommendations = []
    used_questions = set()

    for weakness_key, score in weaknesses[:max_recommendations]:
        if weakness_key not in WEAKNESS_QUESTION_MAP:
            continue

        mapping = WEAKNESS_QUESTION_MAP[weakness_key]

        for cat_key in mapping["recommended_categories"]:
            if cat_key not in ENGLISH_QUESTIONS:
                continue

            cat_data = ENGLISH_QUESTIONS[cat_key]
            for q in cat_data.get("questions", []):
                q_text = q.get("question", "")
                if q_text in used_questions:
                    continue

                recommendations.append({
                    "weakness": mapping["description"],
                    "weakness_key": weakness_key,
                    "question": q_text,
                    "korean_hint": q.get("korean_hint", ""),
                    "category": cat_data.get("category", ""),
                    "category_en": cat_data.get("category_en", ""),
                    "tip": mapping["tip"],
                })
                used_questions.add(q_text)
                break

            if weakness_key in [r["weakness_key"] for r in recommendations]:
                break

    return recommendations


# =====================
# PDF 리포트 생성
# =====================

class EnglishInterviewReportPDF(FPDF):
    """영어면접 리포트 PDF 클래스"""

    def __init__(self):
        super().__init__()
        self.korean_font_added = False

        font_path = get_korean_font_path()
        if font_path:
            try:
                self.add_font("Korean", "", font_path, uni=True)
                self.add_font("Korean", "B", font_path, uni=True)
                self.korean_font_added = True
            except Exception as e:
                print(f"Font error: {e}")

    def header(self):
        if self.korean_font_added:
            self.set_font("Korean", "B", 16)
        else:
            self.set_font("Helvetica", "B", 16)

        self.set_text_color(30, 58, 95)
        self.cell(0, 10, "FlyReady Lab - English Interview Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        if self.korean_font_added:
            self.set_font("Korean", "", 8)
        else:
            self.set_font("Helvetica", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        if self.korean_font_added:
            self.set_font("Korean", "B", 14)
        else:
            self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 58, 95)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str):
        if self.korean_font_added:
            self.set_font("Korean", "", 11)
        else:
            self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        self.set_x(self.l_margin)
        try:
            self.multi_cell(0, 7, text or "")
        except Exception:
            self.ln(7)
        self.ln(2)

    def english_text(self, text: str):
        """영어 텍스트 (이탤릭)"""
        self.set_font("Helvetica", "I", 11)
        self.set_text_color(70, 70, 70)
        self.set_x(self.l_margin)
        try:
            self.multi_cell(0, 7, text or "")
        except Exception:
            self.ln(7)
        self.ln(2)

    def score_box(self, label: str, score: int, max_score: int = 10, feedback: str = ""):
        if self.korean_font_added:
            self.set_font("Korean", "", 10)
        else:
            self.set_font("Helvetica", "", 10)

        if score >= 8:
            color = (76, 175, 80)
        elif score >= 6:
            color = (255, 193, 7)
        else:
            color = (244, 67, 54)

        label_safe = label[:15] if len(label) > 15 else label
        self.set_text_color(50, 50, 50)
        self.cell(50, 8, label_safe, border=0)

        self.set_text_color(*color)
        self.cell(20, 8, f"{score}/{max_score}", border=0)

        self.set_text_color(100, 100, 100)
        feedback_safe = (feedback or "")[:40]
        if feedback_safe:
            try:
                self.multi_cell(0, 8, feedback_safe)
            except Exception:
                self.ln(8)
        else:
            self.ln(8)


def generate_english_interview_report(
    questions_answers: List[Dict[str, Any]],
    feedbacks: Dict[int, Dict[str, Any]],
    voice_analysis: Dict[str, Any] = None,
    mode: str = "practice",
    user_name: str = "Candidate"
) -> bytes:
    """
    영어면접 결과 PDF 리포트 생성

    Args:
        questions_answers: [{"question": ..., "answer": ..., "key_points": [...]}, ...]
        feedbacks: {idx: {"result": "..."}, ...}
        voice_analysis: 음성 분석 결과
        mode: "practice" or "mock"
        user_name: 사용자 이름

    Returns:
        PDF 바이트 데이터
    """
    pdf = EnglishInterviewReportPDF()
    pdf.add_page()

    # 1. 기본 정보
    pdf.section_title("Basic Information")
    pdf.body_text(f"Name: {user_name}")
    pdf.body_text(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    pdf.body_text(f"Mode: {'Mock Interview' if mode == 'mock' else 'Practice'}")
    pdf.body_text(f"Questions: {len(questions_answers)}")
    pdf.ln(5)

    # 2. 종합 점수 (음성 분석 있을 때)
    if voice_analysis:
        pdf.section_title("Overall Score")

        total_score = voice_analysis.get("total_score", 0)
        grade = voice_analysis.get("grade", "N/A")
        summary = voice_analysis.get("summary", "")

        if pdf.korean_font_added:
            pdf.set_font("Korean", "B", 24)
        else:
            pdf.set_font("Helvetica", "B", 24)

        grade_colors = {"S": (255, 215, 0), "A": (76, 175, 80), "B": (33, 150, 243), "C": (255, 152, 0), "D": (244, 67, 54)}
        color = grade_colors.get(grade, (100, 100, 100))
        pdf.set_text_color(*color)
        pdf.cell(0, 15, f"Grade {grade} ({total_score}/100)", align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(50, 50, 50)
        if pdf.korean_font_added:
            pdf.set_font("Korean", "", 11)
        pdf.multi_cell(0, 7, summary, align="C")
        pdf.ln(5)

    # 3. 음성 전달력 분석
    if voice_analysis:
        pdf.section_title("Voice Delivery Analysis")

        voice_detail = voice_analysis.get("voice_analysis", {})
        text_detail = voice_analysis.get("text_analysis", {})

        for key, label in [("tremor", "Voice Stability"), ("ending_clarity", "Ending Clarity"),
                           ("pitch_variation", "Pitch Variation"), ("service_tone", "Service Tone"),
                           ("composure", "Composure")]:
            item = voice_detail.get(key, {})
            pdf.score_box(label, item.get("score", 0), 10, item.get("feedback", ""))

        pdf.ln(3)

        for key, label in [("speech_rate", "Speech Rate"), ("filler_words", "Filler Words"),
                           ("pauses", "Pauses"), ("clarity", "Pronunciation")]:
            item = text_detail.get(key, {})
            pdf.score_box(label, item.get("score", 0), 10, item.get("feedback", ""))

        rt = voice_analysis.get("response_time_analysis", {})
        pdf.score_box("Response Time", rt.get("score", 0), 10, rt.get("feedback", ""))

        pdf.ln(5)

    # 4. 질문별 상세 평가
    pdf.add_page()
    pdf.section_title("Question Details")

    for idx, qa in enumerate(questions_answers):
        question = qa.get("question", "")
        answer = qa.get("answer", "")

        # 질문
        if pdf.korean_font_added:
            pdf.set_font("Korean", "B", 11)
        else:
            pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 58, 95)
        pdf.multi_cell(0, 7, f"Q{idx+1}: {question}")

        # 답변
        pdf.english_text(f"Your Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")

        # 피드백
        fb = feedbacks.get(idx, {})
        if "result" in fb:
            clean_fb = fb["result"].replace("**", "").replace("###", "").replace("##", "")
            if len(clean_fb) > 400:
                clean_fb = clean_fb[:400] + "..."
            pdf.body_text(clean_fb)

        pdf.ln(3)

        if pdf.get_y() > 250:
            pdf.add_page()

    # 5. 맞춤 추천
    recommendations = get_weakness_recommendations_english(voice_analysis, "", 3)

    if recommendations:
        pdf.add_page()
        pdf.section_title("Recommended Practice Questions")

        for i, rec in enumerate(recommendations, 1):
            pdf.body_text(f"{i}. [{rec['weakness']}] Improvement")
            pdf.english_text(f"   Q: {rec['question']}")
            pdf.body_text(f"   Category: {rec['category_en']}")
            pdf.body_text(f"   Tip: {rec['tip']}")
            pdf.ln(3)

    # 6. 개선 포인트
    if voice_analysis:
        improvements = voice_analysis.get("top_improvements", [])
        if improvements:
            pdf.section_title("Priority Improvements")
            for i, imp in enumerate(improvements, 1):
                pdf.body_text(f"{i}. {imp}")

    return bytes(pdf.output())


def get_english_report_filename() -> str:
    """리포트 파일명 생성"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    return f"FlyReady_EnglishInterview_{date_str}.pdf"
