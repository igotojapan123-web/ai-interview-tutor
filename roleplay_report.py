# roleplay_report.py
# 롤플레잉 PDF 리포트 생성 및 약점 기반 시나리오 추천

import os
import io
from datetime import datetime
from typing import Dict, List, Any, Optional

from fpdf import FPDF

# 시나리오 데이터 import
try:
    from roleplay_scenarios import SCENARIOS, get_all_scenarios
except ImportError:
    SCENARIOS = {}
    def get_all_scenarios():
        return []


# =====================
# 한글 폰트 설정
# =====================

# Windows 기본 한글 폰트 경로
FONT_PATHS = [
    "C:/Windows/Fonts/malgun.ttf",      # 맑은 고딕
    "C:/Windows/Fonts/NanumGothic.ttf", # 나눔고딕
    "C:/Windows/Fonts/gulim.ttc",       # 굴림
]


def get_korean_font_path() -> Optional[str]:
    """사용 가능한 한글 폰트 경로 반환"""
    for path in FONT_PATHS:
        if os.path.exists(path):
            return path
    return None


# =====================
# 약점 기반 시나리오 추천
# =====================

# 약점과 시나리오 매핑
WEAKNESS_SCENARIO_MAP = {
    # 음성 분석 약점
    "tremor": {
        "description": "목소리 떨림",
        "recommended_categories": ["좌석 관련"],  # 쉬운 상황부터
        "recommended_difficulty": [1, 2],
        "tip": "쉬운 시나리오부터 연습하며 자신감을 쌓으세요."
    },
    "ending_clarity": {
        "description": "말끝 흐림",
        "recommended_categories": ["기내 서비스"],
        "recommended_difficulty": [1, 2],
        "tip": "문장 끝까지 또렷하게 말하는 연습을 하세요."
    },
    "pitch_variation": {
        "description": "억양 단조로움",
        "recommended_categories": ["특수 승객"],
        "recommended_difficulty": [1, 2],
        "tip": "감정을 담아 말하는 연습이 필요합니다."
    },
    "service_tone": {
        "description": "서비스 톤 부족",
        "recommended_categories": ["좌석 관련", "기내 서비스"],
        "recommended_difficulty": [1, 2],
        "tip": "밝은 인사와 부드러운 마무리를 연습하세요."
    },
    "composure": {
        "description": "침착함 부족",
        "recommended_categories": ["좌석 관련"],
        "recommended_difficulty": [1],
        "tip": "심호흡 후 천천히 말하는 습관을 들이세요."
    },

    # 텍스트 분석 약점
    "speech_rate": {
        "description": "말 속도 문제",
        "recommended_categories": ["기내 서비스"],
        "recommended_difficulty": [1, 2],
        "tip": "적정 속도(120-150 WPM)로 말하는 연습을 하세요."
    },
    "filler_words": {
        "description": "추임새 과다",
        "recommended_categories": ["좌석 관련"],
        "recommended_difficulty": [1, 2],
        "tip": "'음', '어' 대신 잠시 멈추는 연습을 하세요."
    },
    "pauses": {
        "description": "휴지/끊김 많음",
        "recommended_categories": ["기내 서비스"],
        "recommended_difficulty": [1, 2],
        "tip": "답변을 미리 정리하고 말하는 연습을 하세요."
    },

    # 내용 분석 약점
    "empathy": {
        "description": "공감 표현 부족",
        "recommended_categories": ["불만/컴플레인", "특수 승객"],
        "recommended_difficulty": [2, 3],
        "tip": "승객의 감정을 먼저 인정하는 표현을 사용하세요."
    },
    "solution": {
        "description": "해결책 제시 부족",
        "recommended_categories": ["불만/컴플레인", "승객 간 갈등"],
        "recommended_difficulty": [2, 3],
        "tip": "구체적인 대안을 제시하는 연습을 하세요."
    },
    "professionalism": {
        "description": "전문성 부족",
        "recommended_categories": ["안전/규정", "의료/응급"],
        "recommended_difficulty": [3, 4],
        "tip": "항공사 규정과 절차를 숙지하세요."
    },
}


def get_weakness_recommendations(
    voice_analysis: Dict[str, Any],
    text_evaluation: str = "",
    max_recommendations: int = 5
) -> List[Dict[str, Any]]:
    """
    약점 분석 기반 시나리오 추천

    Args:
        voice_analysis: analyze_voice_complete 결과
        text_evaluation: 텍스트 평가 결과 문자열
        max_recommendations: 최대 추천 개수

    Returns:
        [
            {
                "weakness": "말끝 흐림",
                "scenario_id": "seat_change_full",
                "scenario_title": "만석인데 좌석 변경 요청",
                "difficulty": 2,
                "tip": "..."
            },
            ...
        ]
    """
    weaknesses = []

    # 1. 음성 분석에서 약점 추출
    if voice_analysis:
        voice_detail = voice_analysis.get("voice_analysis", {})
        text_detail = voice_analysis.get("text_analysis", {})

        # 점수 6점 이하인 항목 추출
        for key in ["tremor", "ending_clarity", "pitch_variation", "service_tone", "composure"]:
            if voice_detail.get(key, {}).get("score", 10) <= 6:
                weaknesses.append((key, voice_detail[key].get("score", 0)))

        for key in ["speech_rate", "filler_words", "pauses"]:
            if text_detail.get(key, {}).get("score", 10) <= 6:
                weaknesses.append((key, text_detail[key].get("score", 0)))

    # 2. 텍스트 평가에서 약점 추출 (간단한 키워드 매칭)
    if text_evaluation:
        eval_lower = text_evaluation.lower()
        if "공감" in eval_lower and ("부족" in eval_lower or "개선" in eval_lower):
            weaknesses.append(("empathy", 5))
        if "해결" in eval_lower and ("부족" in eval_lower or "개선" in eval_lower):
            weaknesses.append(("solution", 5))
        if "전문" in eval_lower and ("부족" in eval_lower or "개선" in eval_lower):
            weaknesses.append(("professionalism", 5))

    # 3. 점수 낮은 순으로 정렬
    weaknesses.sort(key=lambda x: x[1])

    # 4. 약점별로 시나리오 추천
    recommendations = []
    used_scenarios = set()
    all_scenarios = get_all_scenarios()

    for weakness_key, score in weaknesses[:max_recommendations]:
        if weakness_key not in WEAKNESS_SCENARIO_MAP:
            continue

        mapping = WEAKNESS_SCENARIO_MAP[weakness_key]

        # 매칭되는 시나리오 찾기
        for scenario in all_scenarios:
            if scenario["id"] in used_scenarios:
                continue

            category_match = scenario.get("category") in mapping["recommended_categories"]
            difficulty_match = scenario.get("difficulty", 1) in mapping["recommended_difficulty"]

            if category_match and difficulty_match:
                recommendations.append({
                    "weakness": mapping["description"],
                    "weakness_key": weakness_key,
                    "scenario_id": scenario["id"],
                    "scenario_title": scenario["title"],
                    "category": scenario.get("category", ""),
                    "difficulty": scenario.get("difficulty", 1),
                    "tip": mapping["tip"],
                })
                used_scenarios.add(scenario["id"])
                break

    return recommendations


# =====================
# PDF 리포트 생성
# =====================

class RoleplayReportPDF(FPDF):
    """롤플레잉 리포트 PDF 클래스"""

    def __init__(self):
        super().__init__()
        self.korean_font_added = False

        # 한글 폰트 추가
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

        self.set_text_color(30, 58, 95)  # 진한 파랑
        self.cell(0, 10, "FlyReady Lab - 롤플레잉 분석 리포트", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        if self.korean_font_added:
            self.set_font("Korean", "", 8)
        else:
            self.set_font("Helvetica", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"페이지 {self.page_no()}", align="C")

    def section_title(self, title: str):
        """섹션 제목"""
        if self.korean_font_added:
            self.set_font("Korean", "B", 14)
        else:
            self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 58, 95)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text: str):
        """본문 텍스트"""
        if self.korean_font_added:
            self.set_font("Korean", "", 11)
        else:
            self.set_font("Helvetica", "", 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, text)
        self.ln(2)

    def score_box(self, label: str, score: int, max_score: int = 10, feedback: str = ""):
        """점수 박스"""
        if self.korean_font_added:
            self.set_font("Korean", "", 10)
        else:
            self.set_font("Helvetica", "", 10)

        # 점수에 따른 색상
        if score >= 8:
            color = (76, 175, 80)  # 초록
        elif score >= 6:
            color = (255, 193, 7)  # 노랑
        else:
            color = (244, 67, 54)  # 빨강

        self.set_text_color(50, 50, 50)
        self.cell(60, 8, label, border=0)

        self.set_text_color(*color)
        self.cell(30, 8, f"{score}/{max_score}", border=0)

        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 8, feedback[:50] + "..." if len(feedback) > 50 else feedback)


def generate_roleplay_report(
    scenario: Dict[str, Any],
    messages: List[Dict[str, Any]],
    text_evaluation: str,
    voice_analysis: Dict[str, Any] = None,
    user_name: str = "사용자"
) -> bytes:
    """
    롤플레잉 결과 PDF 리포트 생성

    Args:
        scenario: 시나리오 정보
        messages: 대화 내용
        text_evaluation: 텍스트 평가 결과
        voice_analysis: 음성 분석 결과
        user_name: 사용자 이름

    Returns:
        PDF 바이트 데이터
    """
    pdf = RoleplayReportPDF()
    pdf.add_page()

    # 1. 기본 정보
    pdf.section_title("📋 기본 정보")
    pdf.body_text(f"이름: {user_name}")
    pdf.body_text(f"날짜: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}")
    pdf.body_text(f"시나리오: {scenario.get('title', 'N/A')}")
    pdf.body_text(f"카테고리: {scenario.get('category', 'N/A')}")
    pdf.body_text(f"난이도: {'⭐' * scenario.get('difficulty', 1)}")
    pdf.ln(5)

    # 2. 종합 점수
    pdf.section_title("📊 종합 점수")

    if voice_analysis:
        total_score = voice_analysis.get("total_score", 0)
        grade = voice_analysis.get("grade", "N/A")
        summary = voice_analysis.get("summary", "")

        if pdf.korean_font_added:
            pdf.set_font("Korean", "B", 24)
        else:
            pdf.set_font("Helvetica", "B", 24)

        # 등급별 색상
        grade_colors = {"S": (255, 215, 0), "A": (76, 175, 80), "B": (33, 150, 243), "C": (255, 152, 0), "D": (244, 67, 54)}
        color = grade_colors.get(grade, (100, 100, 100))
        pdf.set_text_color(*color)
        pdf.cell(0, 15, f"{grade} ({total_score}점)", align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(50, 50, 50)
        if pdf.korean_font_added:
            pdf.set_font("Korean", "", 11)
        pdf.multi_cell(0, 7, summary, align="C")
        pdf.ln(5)

    # 3. 음성 분석 상세
    if voice_analysis:
        pdf.section_title("🎙️ 음성 전달력 분석")

        voice_detail = voice_analysis.get("voice_analysis", {})
        text_detail = voice_analysis.get("text_analysis", {})

        # 음성 품질
        for key, label in [("tremor", "목소리 안정성"), ("ending_clarity", "말끝 명확성"),
                           ("pitch_variation", "억양 변화"), ("service_tone", "서비스 톤"),
                           ("composure", "침착함")]:
            item = voice_detail.get(key, {})
            pdf.score_box(label, item.get("score", 0), 10, item.get("feedback", ""))

        pdf.ln(3)

        # 말하기 습관
        for key, label in [("speech_rate", "말 속도"), ("filler_words", "추임새"),
                           ("pauses", "휴지/끊김"), ("clarity", "발음 명확성")]:
            item = text_detail.get(key, {})
            pdf.score_box(label, item.get("score", 0), 10, item.get("feedback", ""))

        # 응답 시간
        rt = voice_analysis.get("response_time_analysis", {})
        pdf.score_box("응답 시간", rt.get("score", 0), 10, rt.get("feedback", ""))

        pdf.ln(5)

    # 4. 대응 내용 평가
    pdf.section_title("💬 대응 내용 평가")

    # 평가 텍스트 정리 (마크다운 제거)
    clean_eval = text_evaluation.replace("**", "").replace("###", "").replace("##", "").replace("#", "")
    clean_eval = clean_eval.replace("|", " ").replace("-", "")

    # 긴 텍스트는 잘라서 표시
    if len(clean_eval) > 1500:
        clean_eval = clean_eval[:1500] + "\n\n(... 상세 내용은 앱에서 확인하세요)"

    pdf.body_text(clean_eval)
    pdf.ln(5)

    # 5. 맞춤 추천
    recommendations = get_weakness_recommendations(voice_analysis, text_evaluation, 3)

    if recommendations:
        pdf.add_page()
        pdf.section_title("🎯 맞춤 추천 시나리오")

        for i, rec in enumerate(recommendations, 1):
            pdf.body_text(f"{i}. [{rec['weakness']}] 개선 추천")
            pdf.body_text(f"   시나리오: {rec['scenario_title']}")
            pdf.body_text(f"   카테고리: {rec['category']} | 난이도: {'⭐' * rec['difficulty']}")
            pdf.body_text(f"   💡 {rec['tip']}")
            pdf.ln(3)

    # 6. 우선 개선 포인트
    if voice_analysis:
        improvements = voice_analysis.get("top_improvements", [])
        if improvements:
            pdf.section_title("🔧 우선 개선 포인트")
            for i, imp in enumerate(improvements, 1):
                pdf.body_text(f"{i}. {imp}")

    # PDF 바이트 반환
    return bytes(pdf.output())


def get_report_filename(scenario_title: str = "") -> str:
    """리포트 파일명 생성"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    safe_title = scenario_title.replace(" ", "_")[:20] if scenario_title else "roleplay"
    return f"FlyReady_롤플레잉리포트_{safe_title}_{date_str}.pdf"
