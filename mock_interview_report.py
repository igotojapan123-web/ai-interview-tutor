# mock_interview_report.py
# 모의면접 PDF 리포트 생성

import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from fpdf import FPDF

# 항공사 데이터 import
try:
    from airline_questions import AIRLINE_VALUES, get_airline_values
    AIRLINE_DATA_AVAILABLE = True
except ImportError:
    AIRLINE_DATA_AVAILABLE = False
    AIRLINE_VALUES = {}


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
# PDF 리포트 클래스
# =====================

class MockInterviewReportPDF(FPDF):
    """모의면접 리포트 PDF 클래스"""

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
        self.cell(0, 10, "FlyReady Lab - 모의면접 분석 리포트", align="C", new_x="LMARGIN", new_y="NEXT")
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

    def subsection_title(self, title: str):
        if self.korean_font_added:
            self.set_font("Korean", "B", 12)
        else:
            self.set_font("Helvetica", "B", 12)
        self.set_text_color(50, 80, 120)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text: str):
        if self.korean_font_added:
            self.set_font("Korean", "", 11)
        else:
            self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        # 현재 x를 왼쪽 마진으로 리셋하여 남은 너비 문제 방지
        self.set_x(self.l_margin)
        try:
            self.multi_cell(0, 7, text or "")
        except Exception:
            self.ln(7)
        self.ln(2)

    def small_text(self, text: str):
        if self.korean_font_added:
            self.set_font("Korean", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.set_x(self.l_margin)
        try:
            self.multi_cell(0, 5, text or "")
        except Exception:
            self.ln(5)

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

        # 라벨 (최대 12자로 자름)
        label_safe = label[:12] if len(label) > 12 else label
        self.set_text_color(50, 50, 50)
        self.cell(50, 8, label_safe, border=0)

        # 점수
        self.set_text_color(*color)
        self.cell(20, 8, f"{score}/{max_score}", border=0)

        # 피드백 (남은 너비 사용, 안전하게 처리)
        self.set_text_color(100, 100, 100)
        feedback_safe = (feedback or "")[:40]
        if feedback_safe:
            try:
                self.multi_cell(0, 8, feedback_safe)
            except Exception:
                self.ln(8)
        else:
            self.ln(8)

    def grade_display(self, grade: str, score: int):
        """큰 등급 표시"""
        if self.korean_font_added:
            self.set_font("Korean", "B", 36)
        else:
            self.set_font("Helvetica", "B", 36)

        grade_colors = {
            "S": (255, 215, 0),
            "A": (76, 175, 80),
            "B": (33, 150, 243),
            "C": (255, 152, 0),
            "D": (244, 67, 54)
        }
        color = grade_colors.get(grade, (100, 100, 100))
        self.set_text_color(*color)
        self.cell(0, 20, f"{grade}", align="C", new_x="LMARGIN", new_y="NEXT")

        if self.korean_font_added:
            self.set_font("Korean", "", 14)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, f"{score}/100점", align="C", new_x="LMARGIN", new_y="NEXT")


# =====================
# 리포트 생성 함수
# =====================

def generate_mock_interview_report(
    airline: str,
    questions: List[str],
    answers: List[str],
    times: List[int],
    voice_analyses: List[Dict[str, Any]],
    content_analyses: List[Dict[str, Any]],
    combined_voice_analysis: Dict[str, Any] = None,
    evaluation_result: Dict[str, Any] = None,
    user_name: str = "지원자"
) -> bytes:
    """
    모의면접 결과 PDF 리포트 생성

    Args:
        airline: 지원 항공사
        questions: 질문 리스트
        answers: 답변 리스트
        times: 각 질문별 소요 시간
        voice_analyses: 각 질문별 음성 분석 결과
        content_analyses: 각 질문별 내용 분석 결과
        combined_voice_analysis: 종합 음성 분석 결과
        evaluation_result: AI 종합 평가 결과
        user_name: 사용자 이름

    Returns:
        PDF 바이트 데이터
    """
    pdf = MockInterviewReportPDF()
    pdf.add_page()

    # =====================
    # 1. 기본 정보
    # =====================
    pdf.section_title("1. 기본 정보")
    pdf.body_text(f"이름: {user_name}")
    pdf.body_text(f"지원 항공사: {airline}")
    pdf.body_text(f"면접 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}")
    pdf.body_text(f"총 질문 수: {len(questions)}개")

    total_time = sum(times)
    pdf.body_text(f"총 소요 시간: {total_time // 60}분 {total_time % 60}초")

    # 항공사 핵심가치 표시
    if AIRLINE_DATA_AVAILABLE and airline in AIRLINE_VALUES:
        values = AIRLINE_VALUES[airline]
        인재상 = values.get("인재상", [])
        if 인재상:
            pdf.small_text(f"[{airline} 인재상: {', '.join(인재상)}]")

    pdf.ln(5)

    # =====================
    # 2. 종합 점수
    # =====================
    pdf.section_title("2. 종합 점수")

    # 평균 점수 계산
    voice_scores = [v.get("total_score", 0) for v in voice_analyses if v.get("total_score", 0) > 0]
    content_scores = [c.get("total_score", 0) for c in content_analyses if c.get("total_score", 0) > 0]

    avg_voice = sum(voice_scores) // max(len(voice_scores), 1) if voice_scores else 0
    avg_content = sum(content_scores) // max(len(content_scores), 1) if content_scores else 0

    # 종합 음성 분석 결과 사용 (있으면)
    if combined_voice_analysis and "total_score" in combined_voice_analysis:
        total_score = combined_voice_analysis.get("total_score", 0)
        grade = combined_voice_analysis.get("grade", "N/A")
        summary = combined_voice_analysis.get("summary", "")

        pdf.grade_display(grade, total_score)
        if summary:
            pdf.small_text(summary)
        pdf.ln(3)
    else:
        # 평균으로 계산
        total_score = (avg_voice + avg_content) // 2 if (avg_voice or avg_content) else 0
        if total_score >= 90:
            grade = "S"
        elif total_score >= 80:
            grade = "A"
        elif total_score >= 70:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        else:
            grade = "D"

        pdf.grade_display(grade, total_score)
        pdf.ln(3)

    # 점수 상세
    pdf.body_text(f"음성 평균: {avg_voice}/100  |  내용 평균: {avg_content}/100")
    pdf.ln(5)

    # =====================
    # 3. 음성 분석 결과
    # =====================
    if combined_voice_analysis and "error" not in combined_voice_analysis:
        pdf.section_title("3. 음성 전달력 분석")

        # 텍스트 분석
        pdf.subsection_title("말하기 습관")
        text_analysis = combined_voice_analysis.get("text_analysis", {})

        for key, label in [
            ("speech_rate", "말 속도 (WPM)"),
            ("filler_words", "필러 단어"),
            ("pauses", "긴 휴지"),
            ("clarity", "발음 명확도")
        ]:
            item = text_analysis.get(key, {})
            pdf.score_box(label, item.get("score", 0), 10, item.get("feedback", ""))

        pdf.ln(3)

        # 음성 품질 분석
        pdf.subsection_title("음성 품질")
        voice_detail = combined_voice_analysis.get("voice_analysis", {})

        for key, label in [
            ("tremor", "목소리 안정성"),
            ("ending_clarity", "말끝 처리"),
            ("pitch_variation", "억양 변화"),
            ("service_tone", "서비스 톤"),
            ("composure", "침착함")
        ]:
            item = voice_detail.get(key, {})
            pdf.score_box(label, item.get("score", 0), 10, item.get("feedback", ""))

        # 응답 시간
        rt = combined_voice_analysis.get("response_time_analysis", {})
        if rt:
            pdf.ln(2)
            pdf.subsection_title("응답 시간")
            avg_time = rt.get("avg_time", 0)
            pdf.body_text(f"평균 응답 시간: {avg_time:.1f}초")
            pdf.score_box("응답 시간 점수", rt.get("score", 0), 10, rt.get("feedback", ""))

        # 우선 개선 포인트
        improvements = combined_voice_analysis.get("top_improvements", [])
        if improvements:
            pdf.ln(3)
            pdf.subsection_title("우선 개선 포인트")
            for i, imp in enumerate(improvements[:5], 1):
                pdf.body_text(f"{i}. {imp}")

        pdf.ln(5)

    # =====================
    # 4. 질문별 상세 분석
    # =====================
    pdf.add_page()
    pdf.section_title("4. 질문별 상세 분석")

    for i, (q, a, t) in enumerate(zip(questions, answers, times), 1):
        # 페이지 넘침 체크
        if pdf.get_y() > 240:
            pdf.add_page()

        pdf.subsection_title(f"Q{i}. {q[:60]}{'...' if len(q) > 60 else ''}")

        # 답변
        if a and a != "[답변 못함]":
            answer_short = a[:200] + "..." if len(a) > 200 else a
            pdf.small_text(f"답변: {answer_short}")
        else:
            pdf.small_text("답변: (패스)")

        pdf.small_text(f"소요 시간: {t}초")

        # 내용 분석
        content = content_analyses[i-1] if i-1 < len(content_analyses) else {}
        if content and content.get("total_score", 0) > 0:
            pdf.small_text(f"내용 점수: {content.get('total_score', 0)}/100")

            # STAR 체크
            star = content.get("star_check", {})
            if star:
                star_str = " | ".join([
                    f"S:{'O' if star.get('situation') else 'X'}",
                    f"T:{'O' if star.get('task') else 'X'}",
                    f"A:{'O' if star.get('action') else 'X'}",
                    f"R:{'O' if star.get('result') else 'X'}"
                ])
                pdf.small_text(f"STAR: {star_str}")

        # 음성 분석
        voice = voice_analyses[i-1] if i-1 < len(voice_analyses) else {}
        if voice and voice.get("total_score", 0) > 0:
            pdf.small_text(f"음성 점수: {voice.get('total_score', 0)}/100")

        pdf.ln(5)

    # =====================
    # 5. 항공사 인재상 부합도
    # =====================
    if AIRLINE_DATA_AVAILABLE and airline in AIRLINE_VALUES:
        pdf.add_page()
        pdf.section_title(f"5. {airline} 인재상 부합도")

        values = AIRLINE_VALUES[airline]
        인재상 = values.get("인재상", [])
        keywords = values.get("keywords", [])
        slogan = values.get("slogan", "")

        if slogan:
            pdf.body_text(f"슬로건: {slogan}")

        if 인재상:
            pdf.body_text(f"인재상: {', '.join(인재상)}")

        if keywords:
            pdf.body_text(f"핵심 키워드: {', '.join(keywords)}")

        pdf.ln(3)
        pdf.small_text("위 인재상을 기준으로 면접 답변을 점검해보세요.")
        pdf.small_text("각 인재상 항목과 관련된 경험, 역량을 구체적으로 어필했는지 확인하세요.")
        pdf.ln(5)

    # =====================
    # 6. AI 종합 평가
    # =====================
    if evaluation_result and "result" in evaluation_result:
        if pdf.get_y() > 200:
            pdf.add_page()

        pdf.section_title("6. AI 종합 평가")

        # 마크다운 정리
        eval_text = evaluation_result["result"]
        eval_text = eval_text.replace("**", "").replace("###", "").replace("##", "").replace("#", "")
        eval_text = eval_text.replace("|", " ").replace("---", "")

        # 길이 제한
        if len(eval_text) > 2000:
            eval_text = eval_text[:2000] + "\n\n(... 상세 내용은 앱에서 확인하세요)"

        pdf.body_text(eval_text)

    # =====================
    # 마무리
    # =====================
    pdf.add_page()
    pdf.section_title("면접 연습 팁")

    tips = [
        "1. 답변은 60-90초 내로 구조화하세요 (STAR 기법 활용)",
        "2. '음', '어' 같은 필러 단어를 줄이세요",
        "3. 말끝까지 또렷하게 발음하세요",
        "4. 밝은 첫인사와 부드러운 마무리를 연습하세요",
        "5. 지원 항공사의 인재상을 답변에 녹여내세요",
        f"6. {airline}의 핵심가치를 숙지하고 관련 경험을 준비하세요",
    ]

    for tip in tips:
        pdf.body_text(tip)

    pdf.ln(10)
    pdf.small_text("FlyReady Lab과 함께 꾸준히 연습하세요!")
    pdf.small_text(f"리포트 생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    return bytes(pdf.output())


def get_mock_interview_report_filename(airline: str) -> str:
    """리포트 파일명 생성"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    airline_safe = airline.replace(" ", "_")
    return f"FlyReady_MockInterview_{airline_safe}_{date_str}.pdf"
