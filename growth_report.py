# growth_report.py
# 성장 리포트 PDF 생성

import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from fpdf import FPDF


# =====================
# 한글 폰트 설정
# =====================

FONT_PATHS = [
    "C:/Windows/Fonts/malgun.ttf",
    "C:/Windows/Fonts/NanumGothic.ttf",
    "C:/Windows/Fonts/gulim.ttc",
]


def get_korean_font_path() -> Optional[str]:
    for path in FONT_PATHS:
        if os.path.exists(path):
            return path
    return None


# =====================
# PDF 리포트 클래스
# =====================

class GrowthReportPDF(FPDF):
    """성장 리포트 PDF 클래스"""

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
            self.set_font("Korean", "B", 18)
        else:
            self.set_font("Helvetica", "B", 18)

        self.set_text_color(102, 126, 234)
        self.cell(0, 12, "FlyReady Lab - 성장 리포트", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

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
        self.set_text_color(102, 126, 234)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_title(self, title: str):
        if self.korean_font_added:
            self.set_font("Korean", "B", 12)
        else:
            self.set_font("Helvetica", "B", 12)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text: str):
        if self.korean_font_added:
            self.set_font("Korean", "", 11)
        else:
            self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        clean_text = self._clean_text(text)
        self.multi_cell(0, 6, clean_text)
        self.ln(2)

    def small_text(self, text: str):
        if self.korean_font_added:
            self.set_font("Korean", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        clean_text = self._clean_text(text)
        self.multi_cell(0, 5, clean_text)

    def _clean_text(self, text: str) -> str:
        """PDF에서 지원하지 않는 문자 제거"""
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

        replacements = {
            "✅": "[OK]", "❌": "[X]", "⚠️": "[!]", "💡": "[TIP]",
            "🎯": "[TARGET]", "📊": "[CHART]", "📈": "[UP]", "📉": "[DOWN]",
            "🔥": "*", "💪": "[STRONG]", "📚": "[STUDY]",
            "🟢": "[G]", "🟡": "[Y]", "🔴": "[R]",
            "🎭": "[RP]", "🌍": "[EN]", "🎤": "[MI]", "💬": "[DB]",
            "—": "-", "–": "-", "'": "'", "'": "'", """: '"', """: '"',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        return text

    def draw_stat_box(self, label: str, value: str, x: float, y: float, width: float = 45, color: tuple = (102, 126, 234)):
        """통계 박스 그리기"""
        self.set_xy(x, y)

        # 배경
        self.set_fill_color(color[0], color[1], color[2])
        self.set_draw_color(color[0], color[1], color[2])
        self.rect(x, y, width, 25, style="F")

        # 값
        self.set_text_color(255, 255, 255)
        if self.korean_font_added:
            self.set_font("Korean", "B", 16)
        else:
            self.set_font("Helvetica", "B", 16)
        self.set_xy(x, y + 3)
        self.cell(width, 10, value, align="C")

        # 라벨
        if self.korean_font_added:
            self.set_font("Korean", "", 9)
        else:
            self.set_font("Helvetica", "", 9)
        self.set_xy(x, y + 14)
        self.cell(width, 8, label, align="C")

    def draw_progress_bar(self, value: float, max_value: float = 100, x: float = 10, y: float = None, width: float = 190, height: float = 8, color: tuple = (102, 126, 234)):
        """프로그레스 바 그리기"""
        if y is None:
            y = self.get_y()

        # 배경
        self.set_fill_color(230, 230, 230)
        self.rect(x, y, width, height, style="F")

        # 진행
        fill_width = (value / max_value) * width if max_value > 0 else 0
        self.set_fill_color(*color)
        self.rect(x, y, fill_width, height, style="F")

        self.set_y(y + height + 3)


# =====================
# 리포트 생성 함수
# =====================

def generate_growth_report(
    all_scores: List[Dict[str, Any]],
    skill_scores: Dict[str, float] = None,
    weekly_comp: Dict[str, Any] = None,
    insights: List[Dict[str, Any]] = None,
    streak: int = 0,
    user_name: str = "지원자"
) -> bytes:
    """성장 리포트 PDF 생성"""

    pdf = GrowthReportPDF()
    pdf.add_page()

    now = datetime.now()

    # 1. 요약 정보
    pdf.section_title("1. 학습 현황 요약")

    # 통계 계산
    total_count = len(all_scores)
    recent_scores = [s["score"] for s in all_scores[-20:] if s.get("score", 0) > 0]
    avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 0

    this_week = weekly_comp.get("this_week", {}).get("count", 0) if weekly_comp else 0
    last_week = weekly_comp.get("last_week", {}).get("count", 0) if weekly_comp else 0

    # 통계 박스
    y_pos = pdf.get_y()
    pdf.draw_stat_box("총 연습", f"{total_count}회", 10, y_pos, 45, (102, 126, 234))
    pdf.draw_stat_box("이번 주", f"{this_week}회", 60, y_pos, 45, (17, 153, 142))
    pdf.draw_stat_box("연속 학습", f"{streak}일", 110, y_pos, 45, (245, 87, 108))
    pdf.draw_stat_box("평균 점수", f"{avg_score:.0f}점", 160, y_pos, 45, (79, 172, 254))

    pdf.set_y(y_pos + 35)

    # 리포트 기간
    if all_scores:
        first_date = all_scores[0].get("date", "")
        last_date = all_scores[-1].get("date", "")
        pdf.small_text(f"기간: {first_date} ~ {last_date} | 생성일: {now.strftime('%Y-%m-%d %H:%M')}")

    pdf.ln(5)

    # 2. 성장 분석
    pdf.section_title("2. 성장 분석")

    scored_records = [s for s in all_scores if s.get("score", 0) > 0]

    if len(scored_records) >= 6:
        first_half = scored_records[:len(scored_records)//2]
        second_half = scored_records[len(scored_records)//2:]

        first_avg = sum(s["score"] for s in first_half) / len(first_half)
        second_avg = sum(s["score"] for s in second_half) / len(second_half)
        growth = second_avg - first_avg

        pdf.body_text(f"처음 평균: {first_avg:.0f}점 -> 최근 평균: {second_avg:.0f}점")

        if growth > 0:
            pdf.body_text(f"[UP] 성장: +{growth:.0f}점 상승!")
        elif growth < 0:
            pdf.body_text(f"[DOWN] 변화: {growth:.0f}점 (복습 권장)")
        else:
            pdf.body_text("변화 없음")

        # 성장 메시지
        if growth >= 10:
            pdf.body_text("대단합니다! 크게 성장하고 있어요!")
        elif growth >= 5:
            pdf.body_text("꾸준히 성장하고 있습니다. 좋은 흐름이에요!")
        elif growth >= 0:
            pdf.body_text("꾸준히 연습하면 점수가 오를 거예요!")
        else:
            pdf.body_text("복습이 필요해 보여요. 기초부터 다시 점검해보세요.")

    else:
        pdf.body_text("6회 이상 연습하면 성장 분석이 제공됩니다.")

    pdf.ln(3)

    # 3. 스킬 분석
    if skill_scores:
        pdf.section_title("3. 내가 잘하는 것 / 더 연습할 것")

        sorted_skills = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)

        for skill, score in sorted_skills:
            if score >= 85:
                status = "[G] 아주 잘해요!"
            elif score >= 70:
                status = "[Y] 괜찮아요"
            else:
                status = "[R] 더 연습해요"

            pdf.body_text(f"{skill}: {score:.0f}점 {status}")

        # 강점/약점
        if sorted_skills:
            strongest = sorted_skills[0]
            weakest = sorted_skills[-1]
            pdf.ln(2)
            pdf.subsection_title("한눈에 보기")
            pdf.body_text(f"[STRONG] 가장 잘하는 것: {strongest[0]} ({strongest[1]:.0f}점)")
            if weakest[1] < 70:
                pdf.body_text(f"[STUDY] 더 연습하면 좋을 것: {weakest[0]} ({weakest[1]:.0f}점)")

    # 4. 유형별 현황
    pdf.add_page()
    pdf.section_title("4. 유형별 현황")

    type_stats = defaultdict(lambda: {"count": 0, "scores": []})
    for s in all_scores:
        t = s.get("type", "기타")
        type_stats[t]["count"] += 1
        if s.get("score", 0) > 0:
            type_stats[t]["scores"].append(s["score"])

    for type_name, data in type_stats.items():
        count = data["count"]
        scores = data["scores"]
        avg = sum(scores) / len(scores) if scores else 0

        pdf.body_text(f"{type_name}: {count}회 연습, 평균 {avg:.0f}점")

    # 5. AI 인사이트
    if insights:
        pdf.section_title("5. 오늘의 조언")

        for insight in insights[:5]:
            title = insight.get("title", "")
            message = insight.get("message", "")
            insight_type = insight.get("type", "info")

            if insight_type == "positive":
                prefix = "[OK]"
            elif insight_type == "warning":
                prefix = "[!]"
            else:
                prefix = "[TIP]"

            pdf.subsection_title(f"{prefix} {title}")
            pdf.body_text(message)

    # 6. 최근 기록
    pdf.add_page()
    pdf.section_title("6. 최근 연습 기록 (최근 20개)")

    recent = list(reversed(all_scores[-20:]))

    # 테이블 헤더
    if pdf.korean_font_added:
        pdf.set_font("Korean", "B", 10)
    else:
        pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 8, "날짜", border=1, fill=True, align="C")
    pdf.cell(35, 8, "유형", border=1, fill=True, align="C")
    pdf.cell(25, 8, "점수", border=1, fill=True, align="C")
    pdf.cell(100, 8, "상세", border=1, fill=True, align="C")
    pdf.ln()

    # 테이블 내용
    if pdf.korean_font_added:
        pdf.set_font("Korean", "", 9)
    else:
        pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(50, 50, 50)

    for record in recent:
        date = record.get("date", "-")
        type_name = record.get("type", "-")
        score = record.get("score", 0)
        detail = record.get("detail", "-")[:40]

        pdf.cell(30, 7, date, border=1, align="C")
        pdf.cell(35, 7, type_name, border=1, align="C")
        pdf.cell(25, 7, f"{score}점" if score > 0 else "-", border=1, align="C")
        pdf.cell(100, 7, pdf._clean_text(detail), border=1, align="L")
        pdf.ln()

    # 7. 학습 팁
    pdf.add_page()
    pdf.section_title("7. 합격을 위한 꿀팁")

    tips = [
        "1. 하루에 딱 1번만 연습해도 충분해요. 꾸준함이 실력을 만들어요!",
        "2. 점수가 낮은 항목부터 공략하세요. 거기서 점수가 제일 많이 올라요.",
        "3. 롤플레잉, 영어, 모의면접, 토론 - 다 한번씩은 해보세요. 실제 면접은 뭐가 나올지 몰라요.",
        "4. 녹음해서 들어보세요. 내 목소리가 어떻게 들리는지 알면 금방 고쳐져요.",
        "5. AI 피드백을 꼭 읽어보세요. 거기 정답이 다 있어요!",
        "6. 면접 전날? 새로운 거 하지 말고, 잘하는 거 복습하세요. 자신감이 중요해요.",
        "7. 여기까지 읽은 당신은 이미 합격에 한 발 다가섰어요. 화이팅!",
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


def get_growth_report_filename() -> str:
    """PDF 파일명 생성"""
    now = datetime.now()
    return f"성장리포트_{now.strftime('%Y%m%d_%H%M')}.pdf"
