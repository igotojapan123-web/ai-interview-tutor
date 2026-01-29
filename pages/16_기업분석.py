# pages/16_기업분석.py
# 기업분석 PDF - 관리자 업로드 + 사용자 다운로드
# 핵심포인트 미리보기 + 열람기록 + 퀴즈연동 + NEW뱃지 + 다운로드카운터

import streamlit as st
import os
import json
from datetime import datetime, timedelta

from logging_config import get_logger
logger = get_logger(__name__)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page

init_page(
    title="기업분석 자료",
    current_page="기업분석",
    wide_layout=True
)



st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<style>
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    translate: no !important;
}
.notranslate, [translate="no"] {
    translate: no !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate" lang="ko">', unsafe_allow_html=True)

# PDF 저장 경로
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pdf_files")
META_FILE = os.path.join(PDF_DIR, "metadata.json")
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
READ_HISTORY_FILE = os.path.join(DATA_DIR, "pdf_read_history.json")

# 디렉토리 생성
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 항공사 목록
AIRLINES = [
    "대한항공", "아시아나항공", "진에어", "제주항공", "티웨이항공",
    "에어부산", "에어서울", "이스타항공", "에어로케이", "에어프레미아", "파라타항공"
]


# ========================================
# 메타데이터 및 기록 관리
# ========================================
def load_metadata():
    try:
        if os.path.exists(META_FILE):
            with open(META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"메타데이터 로드 실패: {e}")
    return {}


def save_metadata(data):
    try:
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug(f"메타데이터 저장 실패: {e}")


def load_read_history():
    try:
        if os.path.exists(READ_HISTORY_FILE):
            with open(READ_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"읽기 기록 로드 실패: {e}")
    return {"read": [], "downloads": {}}


def save_read_history(data):
    try:
        with open(READ_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug(f"읽기 기록 저장 실패: {e}")


def get_pdf_info(airline):
    meta = load_metadata()
    return meta.get(airline, None)


def save_pdf(airline, file_bytes, filename, description="", highlights=None):
    safe_name = f"{airline}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(PDF_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    meta = load_metadata()

    # 기존 파일이 있으면 삭제
    if airline in meta:
        old_path = os.path.join(PDF_DIR, meta[airline]["filename"])
        if os.path.exists(old_path):
            os.remove(old_path)

    meta[airline] = {
        "filename": safe_name,
        "original_name": filename,
        "description": description,
        "highlights": highlights or [],
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated_at": datetime.now().isoformat(),
        "size": len(file_bytes),
    }
    save_metadata(meta)
    return True


def delete_pdf(airline):
    meta = load_metadata()
    if airline in meta:
        file_path = os.path.join(PDF_DIR, meta[airline]["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
        del meta[airline]
        save_metadata(meta)
        return True
    return False


def get_pdf_bytes(airline):
    meta = load_metadata()
    if airline in meta:
        file_path = os.path.join(PDF_DIR, meta[airline]["filename"])
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
    return None


def record_download(airline):
    """다운로드 기록 저장"""
    history = load_read_history()
    # 열람 기록
    if airline not in history["read"]:
        history["read"].append(airline)
    # 다운로드 카운터
    if airline not in history["downloads"]:
        history["downloads"][airline] = 0
    history["downloads"][airline] += 1
    save_read_history(history)


def is_new_pdf(info):
    """7일 이내 업로드된 자료인지 확인"""
    try:
        updated = info.get("updated_at", info.get("uploaded_at", ""))
        if "T" in updated:
            upload_date = datetime.fromisoformat(updated)
        else:
            upload_date = datetime.strptime(updated, "%Y-%m-%d %H:%M")
        return (datetime.now() - upload_date).days <= 7
    except Exception as e:
        logger.debug(f"PDF 날짜 확인 실패: {e}")
        return False


# ========================================
# CSS
# ========================================
st.markdown("""
<style>
.pdf-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    margin: 12px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid #e0e0e0;
    transition: transform 0.2s, box-shadow 0.2s;
}
.pdf-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.12);
}
.pdf-available {
    border-left: 4px solid #28a745;
}
.pdf-unavailable {
    border-left: 4px solid #dc3545;
    opacity: 0.7;
}
.pdf-read {
    border-left: 4px solid #667eea;
}
.admin-panel {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
}
.badge-new {
    background: linear-gradient(135deg, #ff6b6b, #ee5a24);
    color: white;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: bold;
    animation: pulse 2s infinite;
}
.badge-updated {
    background: linear-gradient(135deg, #4facfe, #00f2fe);
    color: white;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: bold;
}
.badge-read {
    background: #e8e8e8;
    color: #666;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
}
.badge-pdf {
    background: linear-gradient(135deg, #ffd700, #ffb700);
    color: #333;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: bold;
}
.highlight-box {
    background: #f0f7ff;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 10px 0;
    border-left: 3px solid #4facfe;
    font-size: 13px;
}
.download-count {
    color: #999;
    font-size: 11px;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.7; }
    100% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# ========================================
# 메인
# ========================================
st.title("항공사 기업분석 자료")
st.markdown("각 항공사의 심층 기업분석 자료를 확인하세요!")

# 관리자 모드 (sidebar_common의 인증 사용)
st.session_state.is_admin = st.session_state.get("admin_authenticated", False)

# 탭
if st.session_state.is_admin:
    tab1, tab2 = st.tabs([" 자료 다운로드", "️ 관리자 업로드"])
else:
    tab1, = st.tabs([" 자료 다운로드"])

# ========================================
# 탭1: 자료 다운로드
# ========================================
with tab1:
    st.markdown("### 항공사별 기업분석 자료")
    st.info("각 항공사의 심층 분석 자료를 다운로드할 수 있습니다. 핵심 포인트를 미리 확인해보세요!")

    # 열람 현황 요약
    read_history = load_read_history()
    meta = load_metadata()
    available_count = len(meta)
    read_count = len([a for a in read_history["read"] if a in meta])

    if available_count > 0:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("등록된 자료", f"{available_count}개")
        with col2:
            st.metric("열람 완료", f"{read_count}개")
        with col3:
            unread = available_count - read_count
            st.metric("미열람", f"{unread}개", delta=f"-{unread}" if unread > 0 else None, delta_color="inverse")

    st.markdown("---")

    # 필터
    filter_option = st.radio("필터", ["전체", "자료 있음", "미열람", "열람 완료"], horizontal=True, key="pdf_filter")

    # 항공사 카드
    cols = st.columns(2)

    for i, airline in enumerate(AIRLINES):
        info = meta.get(airline)
        has_pdf = info is not None
        is_read = airline in read_history["read"]
        download_count = read_history["downloads"].get(airline, 0)

        # 필터 적용
        if filter_option == "자료 있음" and not has_pdf:
            continue
        if filter_option == "미열람" and (not has_pdf or is_read):
            continue
        if filter_option == "열람 완료" and not is_read:
            continue

        with cols[i % 2]:
            if has_pdf:
                # 상태 결정
                is_new = is_new_pdf(info)
                card_class = "pdf-read" if is_read else "pdf-available"

                # 뱃지 결정
                if is_new and not is_read:
                    badge = '<span class="badge-new"> NEW</span>'
                elif is_new and is_read:
                    badge = '<span class="badge-updated">Updated</span>'
                elif is_read:
                    badge = '<span class="badge-read"> 열람</span>'
                else:
                    badge = '<span class="badge-pdf">PDF</span>'

                # 다운로드 카운트
                dl_text = f' |  {download_count}회 다운로드' if download_count > 0 else ''

                st.markdown(f"""
                <div class="pdf-card {card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">️ {airline}</h4>
                        {badge}
                    </div>
                    <p style="color: #666; margin: 8px 0 4px 0; font-size: 14px;">{info.get('description', '기업분석 자료')}</p>
                    <small style="color: #999;">업로드: {info.get('uploaded_at', '-')} | {info.get('size', 0) // 1024}KB{dl_text}</small>
                </div>
                """, unsafe_allow_html=True)

                # 핵심 포인트 미리보기
                highlights = info.get("highlights", [])
                if highlights:
                    hl_html = "".join([f"<div>• {h}</div>" for h in highlights])
                    st.markdown(f'<div class="highlight-box"><strong> 핵심 포인트</strong>{hl_html}</div>', unsafe_allow_html=True)

                # 버튼 row
                btn_cols = st.columns([2, 1])
                with btn_cols[0]:
                    pdf_bytes = get_pdf_bytes(airline)
                    if pdf_bytes:
                        downloaded = st.download_button(
                            f" 다운로드",
                            data=pdf_bytes,
                            file_name=f"{airline}_기업분석.pdf",
                            mime="application/pdf",
                            key=f"download_{airline}",
                            use_container_width=True
                        )
                        if downloaded:
                            record_download(airline)
                with btn_cols[1]:
                    if st.button("퀴즈", key=f"quiz_{airline}", use_container_width=True):
                        st.session_state.quiz_type = "airline"
                        st.session_state.quiz_airline = None
                        st.switch_page("pages/14_항공사퀴즈.py")

                st.markdown("")  # spacing

            else:
                st.markdown(f"""
                <div class="pdf-card pdf-unavailable">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">️ {airline}</h4>
                        <span style="color: #dc3545; font-size: 12px;">준비중</span>
                    </div>
                    <p style="color: #999; margin: 10px 0; font-size: 14px;">자료 준비 중입니다.</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("")

    # 안내
    st.markdown("---")
    st.markdown("""
    ####  기업분석 자료 내용
    - 항공사 개요 및 역사
    - 경영 현황 및 재무 상태
    - 인재상 및 핵심가치
    - 채용 프로세스 상세
    - 면접 기출문제 및 팁
    - 합격자 인터뷰
    - 최신 이슈 및 전망
    """)

# ========================================
# 탭2: 관리자 업로드 (관리자만)
# ========================================
if st.session_state.is_admin:
    with tab2:
        st.markdown("### ️ PDF 파일 관리")

        st.markdown("""
        <div class="admin-panel">
            <strong>️ 관리자 전용</strong><br>
            각 항공사의 기업분석 PDF 파일을 업로드하거나 삭제할 수 있습니다.<br>
            <small> 핵심 포인트를 입력하면 사용자에게 미리보기로 표시됩니다.</small>
        </div>
        """, unsafe_allow_html=True)

        # 업로드 섹션
        st.markdown("#### 파일 업로드")

        col1, col2 = st.columns(2)

        with col1:
            selected_airline = st.selectbox("항공사 선택", AIRLINES, key="upload_airline")

        with col2:
            description = st.text_input("자료 설명", value="2026년 기업분석 자료", key="upload_desc")

        # 핵심 포인트 입력
        st.markdown("** 핵심 포인트 (최대 5개, 줄바꿈으로 구분)**")
        highlights_text = st.text_area(
            "핵심 포인트",
            placeholder="예시:\n미션: Excellence in Flight\n인재상: 도전, 혁신, 소통\n채용: 연 2회 공채\n특징: 국내 1위 FSC\n최신: 합병 완료",
            height=120,
            key="upload_highlights",
            label_visibility="collapsed"
        )

        uploaded_file = st.file_uploader("PDF 파일 선택", type=["pdf"], key="pdf_upload")

        if uploaded_file:
            st.info(f" 선택된 파일: {uploaded_file.name} ({len(uploaded_file.getvalue()) // 1024}KB)")

            if st.button("업로드", type="primary", use_container_width=True):
                # 핵심 포인트 파싱
                highlights = [h.strip() for h in highlights_text.strip().split("\n") if h.strip()][:5]

                if save_pdf(selected_airline, uploaded_file.getvalue(), uploaded_file.name, description, highlights):
                    st.success(f" {selected_airline} 자료가 업로드되었습니다!")
                    st.rerun()
                else:
                    st.error("업로드 실패")

        st.markdown("---")

        # 현재 파일 목록
        st.markdown("#### 업로드된 파일 목록")

        meta = load_metadata()
        read_history = load_read_history()

        if not meta:
            st.info("업로드된 파일이 없습니다.")
        else:
            for airline, info in meta.items():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    st.markdown(f"**️ {airline}**")
                    st.caption(f"{info.get('description', '-')} | {info.get('uploaded_at', '-')}")
                    highlights = info.get("highlights", [])
                    if highlights:
                        st.caption(f" 포인트: {len(highlights)}개")

                with col2:
                    st.caption(f" {info.get('original_name', '-')}")
                    st.caption(f" {info.get('size', 0) // 1024}KB")

                with col3:
                    dl_count = read_history["downloads"].get(airline, 0)
                    st.caption(f" {dl_count}회")
                    if is_new_pdf(info):
                        st.caption(" NEW")

                with col4:
                    if st.button("️", key=f"del_{airline}", help="삭제"):
                        if delete_pdf(airline):
                            st.success(f"{airline} 파일 삭제됨")
                            st.rerun()

                st.markdown("---")

        # 다운로드 통계
        if read_history["downloads"]:
            st.markdown("#### 다운로드 통계")
            sorted_downloads = sorted(read_history["downloads"].items(), key=lambda x: x[1], reverse=True)
            for airline, count in sorted_downloads:
                st.caption(f"️ {airline}: {count}회 다운로드")

st.markdown('</div>', unsafe_allow_html=True)
