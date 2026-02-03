# new_features/5_면접전체크리스트.py
# FlyReady Lab - 면접 전 체크리스트
# 면접 준비물, 복장, 마음가짐 등 종합 체크

import os
import sys
import json
from datetime import datetime, timedelta
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page
from logging_config import get_logger

logger = get_logger(__name__)

# =====================
# 데이터 경로
# =====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CHECKLIST_FILE = os.path.join(DATA_DIR, "interview_checklist.json")


def load_checklist_state():
    """체크리스트 상태 로드"""
    try:
        if os.path.exists(CHECKLIST_FILE):
            with open(CHECKLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"체크리스트 로드 실패: {e}")
    return {}


def save_checklist_state(data):
    """체크리스트 상태 저장"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CHECKLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"체크리스트 저장 실패: {e}")


# =====================
# 체크리스트 데이터
# =====================

CHECKLIST_CATEGORIES = {
    "documents": {
        "name": "서류 준비",
        "icon": "📄",
        "color": "#3b82f6",
        "items": [
            {"id": "resume", "name": "이력서 3부 출력", "required": True, "tip": "여분으로 준비하세요"},
            {"id": "cover_letter", "name": "자기소개서 3부 출력", "required": True, "tip": "면접 전 다시 읽어보세요"},
            {"id": "photo", "name": "여권사진 준비", "required": True, "tip": "최근 6개월 이내 촬영본"},
            {"id": "id_card", "name": "신분증", "required": True, "tip": "주민등록증 또는 여권"},
            {"id": "certificates", "name": "자격증 사본", "required": False, "tip": "어학성적, 자격증 등"},
            {"id": "portfolio", "name": "포트폴리오 (해당시)", "required": False, "tip": "경력자의 경우"},
        ]
    },
    "appearance": {
        "name": "복장 & 외모",
        "icon": "👔",
        "color": "#8b5cf6",
        "items": [
            {"id": "suit", "name": "정장 다림질", "required": True, "tip": "구김 없이 깔끔하게"},
            {"id": "shirt", "name": "블라우스/셔츠 준비", "required": True, "tip": "흰색 또는 밝은 색상"},
            {"id": "shoes", "name": "구두 광택", "required": True, "tip": "검정 또는 네이비 펌프스"},
            {"id": "stockings", "name": "스타킹 여분", "required": True, "tip": "살색 스타킹 2켤레 이상"},
            {"id": "hair", "name": "헤어 정돈", "required": True, "tip": "단정한 올림머리 또는 단발"},
            {"id": "nails", "name": "네일 정리", "required": True, "tip": "자연스러운 색상 또는 무광"},
            {"id": "makeup", "name": "메이크업 준비물", "required": True, "tip": "자연스럽고 밝은 메이크업"},
            {"id": "accessories", "name": "악세서리 최소화", "required": False, "tip": "귀걸이는 작은 것으로"},
            {"id": "scarf", "name": "스카프 (항공사별)", "required": False, "tip": "항공사 컬러 맞추기"},
        ]
    },
    "items": {
        "name": "소지품",
        "icon": "🎒",
        "color": "#10b981",
        "items": [
            {"id": "bag", "name": "서류 가방", "required": True, "tip": "A4 서류가 들어가는 크기"},
            {"id": "pen", "name": "필기구", "required": True, "tip": "검정 볼펜 2개 이상"},
            {"id": "mirror", "name": "손거울", "required": True, "tip": "대기 중 마지막 점검용"},
            {"id": "lipstick", "name": "립스틱/립밤", "required": True, "tip": "건조함 방지"},
            {"id": "tissue", "name": "휴지/손수건", "required": True, "tip": "땀이나 긴급 상황 대비"},
            {"id": "bandaid", "name": "반창고", "required": False, "tip": "구두 물집 대비"},
            {"id": "breath", "name": "구강청결제/민트", "required": False, "tip": "면접 직전 사용"},
            {"id": "water", "name": "생수", "required": False, "tip": "목 건조함 방지"},
        ]
    },
    "preparation": {
        "name": "사전 준비",
        "icon": "📚",
        "color": "#f59e0b",
        "items": [
            {"id": "company_research", "name": "항공사 정보 숙지", "required": True, "tip": "최신 뉴스, 핵심가치 확인"},
            {"id": "route", "name": "면접장 위치 확인", "required": True, "tip": "30분 일찍 도착 목표"},
            {"id": "transport", "name": "교통편 확인", "required": True, "tip": "대중교통/주차 정보"},
            {"id": "weather", "name": "날씨 확인", "required": True, "tip": "우산, 외투 준비"},
            {"id": "self_intro", "name": "자기소개 암기", "required": True, "tip": "30초, 1분 버전 준비"},
            {"id": "answers", "name": "예상 질문 답변 정리", "required": True, "tip": "핵심 키워드 중심"},
            {"id": "questions", "name": "면접관에게 할 질문", "required": False, "tip": "2-3개 준비"},
            {"id": "mock_interview", "name": "모의면접 연습", "required": True, "tip": "전날 최소 1회"},
        ]
    },
    "day_before": {
        "name": "전날 체크",
        "icon": "🌙",
        "color": "#6366f1",
        "items": [
            {"id": "sleep", "name": "충분한 수면", "required": True, "tip": "최소 7시간 이상"},
            {"id": "alarm", "name": "알람 설정", "required": True, "tip": "여러 개 설정"},
            {"id": "clothes_ready", "name": "복장 준비 완료", "required": True, "tip": "입어보고 확인"},
            {"id": "bag_pack", "name": "가방 미리 챙기기", "required": True, "tip": "서류, 소지품 확인"},
            {"id": "no_alcohol", "name": "음주 금지", "required": True, "tip": "컨디션 관리"},
            {"id": "light_meal", "name": "가벼운 저녁", "required": False, "tip": "소화 잘 되는 음식"},
        ]
    },
    "interview_day": {
        "name": "당일 체크",
        "icon": "☀️",
        "color": "#ef4444",
        "items": [
            {"id": "wake_up", "name": "기상 시간 준수", "required": True, "tip": "출발 2시간 전"},
            {"id": "shower", "name": "샤워 & 청결", "required": True, "tip": "향이 강한 제품 피하기"},
            {"id": "breakfast", "name": "아침 식사", "required": True, "tip": "가볍게, 냄새나는 음식 피하기"},
            {"id": "final_check", "name": "서류 최종 확인", "required": True, "tip": "출발 전 한번 더"},
            {"id": "phone_silent", "name": "휴대폰 무음/진동", "required": True, "tip": "면접장 도착 전"},
            {"id": "arrive_early", "name": "30분 일찍 도착", "required": True, "tip": "여유있게 마음 정리"},
            {"id": "restroom", "name": "화장실 다녀오기", "required": True, "tip": "면접 대기 전"},
            {"id": "deep_breath", "name": "심호흡 & 미소", "required": True, "tip": "긍정적 마인드셋"},
        ]
    },
}


# =====================
# UI
# =====================

def render_checklist():
    """면접 전 체크리스트 UI"""

    st.markdown("""
    <style>
    .checklist-header {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .category-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .category-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #e2e8f0;
    }
    .category-icon {
        font-size: 1.5rem;
    }
    .category-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    .category-progress {
        margin-left: auto;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .check-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        background: #f8fafc;
        transition: all 0.2s;
    }
    .check-item:hover {
        background: #f1f5f9;
    }
    .check-item.checked {
        background: #ecfdf5;
    }
    .check-item.required {
        border-left: 3px solid #ef4444;
    }
    .item-name {
        flex: 1;
        font-weight: 500;
        color: #334155;
    }
    .item-tip {
        font-size: 0.8rem;
        color: #64748b;
    }
    .required-badge {
        font-size: 0.7rem;
        background: #fee2e2;
        color: #ef4444;
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
    }
    .progress-summary {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .overall-progress {
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
    }
    .status-ready {
        color: #10b981;
    }
    .status-warning {
        color: #f59e0b;
    }
    .status-danger {
        color: #ef4444;
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더
    st.markdown("""
    <div class="checklist-header">
        <h2 style="margin:0 0 8px 0;">✅ 면접 전 체크리스트</h2>
        <p style="margin:0;opacity:0.9;">완벽한 준비로 자신감 있게 면접에 임하세요!</p>
    </div>
    """, unsafe_allow_html=True)

    # 면접 정보 입력
    col1, col2 = st.columns(2)
    with col1:
        interview_date = st.date_input(
            "면접 날짜",
            value=datetime.now().date() + timedelta(days=7),
            key="interview_date"
        )
    with col2:
        airline = st.selectbox(
            "지원 항공사",
            ["대한항공", "아시아나항공", "제주항공", "진에어", "티웨이항공", "에어부산", "에어서울", "기타"],
            key="checklist_airline"
        )

    # D-Day 계산
    days_left = (interview_date - datetime.now().date()).days
    if days_left > 0:
        st.info(f"📅 면접까지 **D-{days_left}** 남았습니다!")
    elif days_left == 0:
        st.warning("🔥 오늘이 면접 당일입니다! 화이팅!")
    else:
        st.error("면접일이 지났습니다. 새로운 면접 날짜를 입력해주세요.")

    st.markdown("---")

    # 체크리스트 상태 로드
    if "checklist_state" not in st.session_state:
        st.session_state.checklist_state = load_checklist_state()

    # 전체 진행률 계산
    total_items = 0
    checked_items = 0
    required_total = 0
    required_checked = 0

    for cat_key, cat_data in CHECKLIST_CATEGORIES.items():
        for item in cat_data["items"]:
            total_items += 1
            item_key = f"{cat_key}_{item['id']}"
            if st.session_state.checklist_state.get(item_key, False):
                checked_items += 1
            if item["required"]:
                required_total += 1
                if st.session_state.checklist_state.get(item_key, False):
                    required_checked += 1

    overall_pct = int((checked_items / total_items) * 100) if total_items > 0 else 0
    required_pct = int((required_checked / required_total) * 100) if required_total > 0 else 0

    # 진행률 표시
    if overall_pct >= 100:
        status_class = "status-ready"
        status_msg = "완벽히 준비되었습니다!"
    elif overall_pct >= 70:
        status_class = "status-warning"
        status_msg = "거의 다 됐어요!"
    else:
        status_class = "status-danger"
        status_msg = "더 준비가 필요해요!"

    st.markdown(f"""
    <div class="progress-summary">
        <div class="overall-progress {status_class}">{overall_pct}%</div>
        <div style="text-align:center;color:#64748b;margin-top:8px;">{status_msg}</div>
        <div style="margin-top:16px;">
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;">
                <span>전체 항목: {checked_items}/{total_items}</span>
                <span style="color:#ef4444;">필수 항목: {required_checked}/{required_total}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 카테고리별 체크리스트
    for cat_key, cat_data in CHECKLIST_CATEGORIES.items():
        # D-Day에 따라 특정 카테고리 강조
        highlight = False
        if days_left == 0 and cat_key == "interview_day":
            highlight = True
        elif days_left == 1 and cat_key == "day_before":
            highlight = True

        # 카테고리 진행률
        cat_total = len(cat_data["items"])
        cat_checked = sum(
            1 for item in cat_data["items"]
            if st.session_state.checklist_state.get(f"{cat_key}_{item['id']}", False)
        )
        cat_pct = int((cat_checked / cat_total) * 100) if cat_total > 0 else 0

        with st.expander(
            f"{cat_data['icon']} {cat_data['name']} ({cat_checked}/{cat_total})",
            expanded=highlight
        ):
            for item in cat_data["items"]:
                item_key = f"{cat_key}_{item['id']}"
                is_checked = st.session_state.checklist_state.get(item_key, False)

                col1, col2 = st.columns([4, 1])

                with col1:
                    # 체크박스
                    new_value = st.checkbox(
                        f"{'✅' if is_checked else '⬜'} {item['name']}",
                        value=is_checked,
                        key=f"check_{item_key}",
                        help=item.get("tip", "")
                    )

                    if new_value != is_checked:
                        st.session_state.checklist_state[item_key] = new_value
                        save_checklist_state(st.session_state.checklist_state)
                        st.rerun()

                with col2:
                    if item["required"]:
                        st.markdown("<span class='required-badge'>필수</span>", unsafe_allow_html=True)

                # 팁 표시
                if item.get("tip"):
                    st.caption(f"💡 {item['tip']}")

    # 체크리스트 초기화
    st.markdown("---")
    if st.button("체크리스트 초기화", type="secondary"):
        st.session_state.checklist_state = {}
        save_checklist_state({})
        st.success("체크리스트가 초기화되었습니다.")
        st.rerun()

    # 인쇄용 버전
    with st.expander("📄 인쇄용 체크리스트"):
        printable = "# 면접 전 체크리스트\n\n"
        printable += f"면접 날짜: {interview_date}\n"
        printable += f"지원 항공사: {airline}\n\n"

        for cat_key, cat_data in CHECKLIST_CATEGORIES.items():
            printable += f"\n## {cat_data['icon']} {cat_data['name']}\n"
            for item in cat_data["items"]:
                required = " (필수)" if item["required"] else ""
                printable += f"- [ ] {item['name']}{required}\n"
                if item.get("tip"):
                    printable += f"    💡 {item['tip']}\n"

        st.code(printable, language="markdown")
        st.download_button(
            "체크리스트 다운로드",
            printable,
            file_name=f"면접체크리스트_{interview_date}.md",
            mime="text/markdown"
        )


# 메인 실행
if __name__ == "__main__":
    render_checklist()
