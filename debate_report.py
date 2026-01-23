# debate_report.py
# 토론면접 PDF 리포트 생성

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from fpdf import FPDF

# 토론 주제 카테고리 import
try:
    from debate_topics import DEBATE_CATEGORIES, get_category_info
    DEBATE_DATA_AVAILABLE = True
except ImportError:
    DEBATE_DATA_AVAILABLE = False
    DEBATE_CATEGORIES = {}


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

class DebateReportPDF(FPDF):
    """토론면접 리포트 PDF 클래스"""

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
        self.cell(0, 10, "FlyReady Lab - 토론면접 분석 리포트", align="C", new_x="LMARGIN", new_y="NEXT")
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
        # 특수문자 제거
        clean_text = self._clean_text(text)
        self.multi_cell(0, 6, clean_text)
        self.ln(2)

    def small_text(self, text: str):
        if self.korean_font_added:
            self.set_font("Korean", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        clean_text = self._clean_text(text)
        self.multi_cell(0, 5, clean_text)

    def _clean_text(self, text: str) -> str:
        """PDF에서 지원하지 않는 문자 제거"""
        # 이모지 제거
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub("", text)

        # 특수 기호 대체
        replacements = {
            "✅": "[OK]",
            "❌": "[X]",
            "⚠️": "[!]",
            "💡": "[TIP]",
            "🎯": "[TARGET]",
            "📊": "[CHART]",
            "📝": "[NOTE]",
            "🎤": "[MIC]",
            "👍": "[GOOD]",
            "👎": "[BAD]",
            "⚖️": "[BALANCE]",
            "✈️": "[PLANE]",
            "🛎️": "[SERVICE]",
            "🌍": "[WORLD]",
            "—": "-",
            "–": "-",
            "'": "'",
            "'": "'",
            """: '"',
            """: '"',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def draw_score_box(self, label: str, value: str, x: float, y: float, width: float = 45):
        """점수 박스 그리기"""
        self.set_xy(x, y)
        self.set_fill_color(240, 245, 250)
        self.set_draw_color(200, 210, 220)
        self.rect(x, y, width, 20, style="FD")

        if self.korean_font_added:
            self.set_font("Korean", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.set_xy(x, y + 2)
        self.cell(width, 5, label, align="C")

        if self.korean_font_added:
            self.set_font("Korean", "B", 12)
        else:
            self.set_font("Helvetica", "B", 12)
        self.set_text_color(30, 58, 95)
        self.set_xy(x, y + 9)
        self.cell(width, 8, value, align="C")

    def draw_grade_circle(self, grade: str, x: float, y: float, radius: float = 15):
        """등급 원 그리기"""
        grade_colors = {
            "S": (255, 215, 0),    # Gold
            "A": (76, 175, 80),    # Green
            "B": (33, 150, 243),   # Blue
            "C": (255, 152, 0),    # Orange
            "D": (244, 67, 54),    # Red
        }
        color = grade_colors.get(grade, (150, 150, 150))

        self.set_fill_color(*color)
        self.set_draw_color(*color)
        self.ellipse(x - radius, y - radius, radius * 2, radius * 2, style="F")

        self.set_text_color(255, 255, 255)
        if self.korean_font_added:
            self.set_font("Korean", "B", 20)
        else:
            self.set_font("Helvetica", "B", 20)
        self.set_xy(x - radius, y - 7)
        self.cell(radius * 2, 14, grade, align="C")


# =====================
# 리포트 생성 함수
# =====================

def generate_debate_report(
    topic: Dict[str, Any],
    position: str,
    history: List[Dict[str, Any]],
    voice_analyses: List[Dict[str, Any]] = None,
    combined_voice_analysis: Dict[str, Any] = None,
    evaluation_result: str = "",
    user_name: str = "지원자"
) -> bytes:
    """토론면접 PDF 리포트 생성

    Args:
        topic: 토론 주제 정보
        position: 지원자 입장 (찬성/반대/중립)
        history: 토론 히스토리
        voice_analyses: 발언별 음성 분석 결과
        combined_voice_analysis: 종합 음성 분석 결과
        evaluation_result: AI 평가 결과 텍스트
        user_name: 지원자 이름

    Returns:
        PDF 바이트 데이터
    """
    pdf = DebateReportPDF()
    pdf.add_page()

    # 1. 기본 정보
    pdf.section_title("1. 토론 기본 정보")

    now = datetime.now()
    topic_title = topic.get("topic", "토론 주제")
    category = topic.get("category", "")
    background = topic.get("background", "")

    # 카테고리 정보
    cat_info = get_category_info(category) if DEBATE_DATA_AVAILABLE else {}
    cat_name = cat_info.get("name", category) if cat_info else category

    # 기본 정보 박스
    y_pos = pdf.get_y()
    pdf.draw_score_box("날짜", now.strftime("%Y-%m-%d"), 10, y_pos)
    pdf.draw_score_box("카테고리", cat_name, 60, y_pos)
    pdf.draw_score_box("입장", position, 110, y_pos)

    user_statements = [h for h in history if h.get("is_user")]
    pdf.draw_score_box("발언 횟수", f"{len(user_statements)}회", 160, y_pos)

    pdf.set_y(y_pos + 28)

    # 토론 주제
    pdf.subsection_title("토론 주제")
    pdf.body_text(topic_title)

    if background:
        pdf.subsection_title("배경")
        pdf.body_text(background)

    # 찬반 논점
    pro_points = topic.get("pro_points", [])
    con_points = topic.get("con_points", [])

    if pro_points or con_points:
        pdf.subsection_title("논점 정리")
        if pro_points:
            pdf.small_text(f"[찬성] {', '.join(pro_points)}")
        if con_points:
            pdf.small_text(f"[반대] {', '.join(con_points)}")
        pdf.ln(3)

    # 2. 종합 점수
    pdf.add_page()
    pdf.section_title("2. 종합 점수")

    # 평가 결과에서 점수 추출
    total_score = 0
    grade = "N/A"

    if evaluation_result:
        # 점수 추출
        score_match = re.search(r'종합\s*점수[:\s]*(\d+)', evaluation_result)
        if score_match:
            total_score = int(score_match.group(1))

        # 등급 추출
        grade_match = re.search(r'등급[:\s]*\[?([SABCD])\]?', evaluation_result)
        if grade_match:
            grade = grade_match.group(1)
        elif total_score >= 90:
            grade = "S"
        elif total_score >= 80:
            grade = "A"
        elif total_score >= 70:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        else:
            grade = "D"

    # 등급 표시
    y_pos = pdf.get_y()
    pdf.draw_grade_circle(grade, 105, y_pos + 20, 18)
    pdf.set_y(y_pos + 45)

    pdf.body_text(f"종합 점수: {total_score}/100점")
    pdf.ln(5)

    # 3. 음성 분석 (있는 경우)
    if voice_analyses and combined_voice_analysis:
        pdf.section_title("3. 음성 전달력 분석")

        if "error" not in combined_voice_analysis:
            text_analysis = combined_voice_analysis.get("text_analysis", {})
            voice_quality = combined_voice_analysis.get("voice_quality", {})

            y_pos = pdf.get_y()
            pdf.draw_score_box(
                "말 속도",
                f"{text_analysis.get('words_per_minute', 0):.0f} WPM",
                10, y_pos
            )
            pdf.draw_score_box(
                "필러 단어",
                f"{text_analysis.get('filler_count', 0)}회",
                60, y_pos
            )
            pdf.draw_score_box(
                "발음 명확도",
                f"{voice_quality.get('pronunciation_clarity', 0)}%",
                110, y_pos
            )
            pdf.draw_score_box(
                "음성 점수",
                f"{combined_voice_analysis.get('overall_score', 0)}점",
                160, y_pos
            )

            pdf.set_y(y_pos + 28)

            # 개선 포인트
            improvements = combined_voice_analysis.get("priority_improvements", [])
            if improvements:
                pdf.subsection_title("우선 개선 포인트")
                for imp in improvements[:3]:
                    pdf.small_text(f"- {imp}")
                pdf.ln(3)

    # 4. 토론 내용
    pdf.add_page()
    pdf.section_title("4. 토론 내용")

    for i, h in enumerate(history):
        speaker = h.get("speaker", "")
        content = h.get("content", "")
        is_user = h.get("is_user", False)

        if is_user:
            pdf.subsection_title(f"[{position}] 나의 발언 {i // 2 + 1}")
        else:
            pos_label = {"pro": "찬성", "con": "반대", "neutral": "중립"}.get(h.get("position", ""), "")
            pdf.subsection_title(f"[{pos_label}] {speaker}")

        pdf.body_text(content)

        # 음성 분석 (사용자 발언인 경우)
        if is_user and voice_analyses:
            user_idx = sum(1 for hh in history[:i] if hh.get("is_user"))
            if user_idx < len(voice_analyses) and voice_analyses[user_idx]:
                va = voice_analyses[user_idx]
                ta = va.get("text_analysis", {})
                pdf.small_text(
                    f"[음성분석] 말속도: {ta.get('words_per_minute', 0):.0f} WPM, "
                    f"필러: {ta.get('filler_count', 0)}회, "
                    f"점수: {va.get('overall_score', 0)}점"
                )

        pdf.ln(2)

    # 5. AI 평가
    if evaluation_result:
        pdf.add_page()
        pdf.section_title("5. AI 종합 평가")

        # 마크다운 헤더 정리
        clean_eval = evaluation_result
        clean_eval = re.sub(r'^#{1,4}\s*', '', clean_eval, flags=re.MULTILINE)
        clean_eval = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_eval)

        # 줄 단위로 처리
        for line in clean_eval.split('\n'):
            line = line.strip()
            if not line:
                pdf.ln(2)
            elif line.startswith('---'):
                pdf.ln(3)
            elif any(line.startswith(prefix) for prefix in ['1.', '2.', '3.', '4.', '5.']):
                pdf.subsection_title(line)
            else:
                pdf.body_text(line)

    # 6. 토론 팁
    pdf.add_page()
    pdf.section_title("6. 토론면접 팁")

    tips = [
        "1. 상대방 발언을 끝까지 경청하세요. 중간에 끊지 않는 것이 기본입니다.",
        "2. 반박할 때는 '~라고 하셨는데'로 시작하면 경청했음을 보여줍니다.",
        "3. 근거 없는 주장보다 구체적 사례나 데이터를 활용하세요.",
        "4. 자신의 입장을 일관되게 유지하되, 상대 의견의 좋은 점은 인정하세요.",
        "5. 결론보다 과정이 중요합니다. 어떻게 토론에 참여했는지가 평가됩니다.",
        "6. 목소리 톤과 속도를 조절하세요. 너무 빠르거나 작으면 감점 요인입니다.",
        "7. 비언어적 표현(고개 끄덕임, 눈맞춤)도 중요한 평가 요소입니다.",
    ]

    for tip in tips:
        pdf.body_text(tip)

    # 마무리
    pdf.ln(10)
    pdf.set_text_color(128, 128, 128)
    if pdf.korean_font_added:
        pdf.set_font("Korean", "", 10)
    else:
        pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, f"Generated by FlyReady Lab - {now.strftime('%Y-%m-%d %H:%M')}", align="C")

    return bytes(pdf.output())


def get_debate_report_filename(topic: str) -> str:
    """PDF 파일명 생성"""
    now = datetime.now()
    # 특수문자 제거
    clean_topic = re.sub(r'[^\w\s가-힣]', '', topic)[:20]
    return f"토론면접_{clean_topic}_{now.strftime('%Y%m%d_%H%M')}.pdf"
