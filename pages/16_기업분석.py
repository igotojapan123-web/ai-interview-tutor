# pages/16_기업분석.py
# 기업분석 PDF - 관리자 업로드 + 사용자 다운로드

import streamlit as st
import os
import json
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_tester_password, check_admin_password
from env_config import ADMIN_PASSWORD

st.set_page_config(page_title="기업분석 자료", page_icon="📑", layout="wide")

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="기업 분석")
except ImportError:
    pass

st.markdown('<meta name="google" content="notranslate"><style>html{translate:no;}</style>', unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# 비밀번호
check_tester_password()

# PDF 저장 경로
PDF_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pdf_files")
META_FILE = os.path.join(PDF_DIR, "metadata.json")

# 디렉토리 생성
if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)

# 항공사 목록
AIRLINES = [
    "대한항공", "아시아나항공", "진에어", "제주항공", "티웨이항공",
    "에어부산", "에어서울", "이스타항공", "에어로케이", "에어프레미아", "파라타항공"
]

# 메타데이터 관리
def load_metadata():
    if os.path.exists(META_FILE):
        with open(META_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_metadata(data):
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_pdf_info(airline):
    meta = load_metadata()
    return meta.get(airline, None)

def save_pdf(airline, file_bytes, filename, description=""):
    # 파일 저장
    safe_name = f"{airline}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(PDF_DIR, safe_name)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 메타데이터 저장
    meta = load_metadata()
    meta[airline] = {
        "filename": safe_name,
        "original_name": filename,
        "description": description,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
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

# CSS
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
}
.admin-panel {
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 12px;
    padding: 20px;
    margin: 20px 0;
}
.premium-badge {
    background: linear-gradient(135deg, #ffd700, #ffb700);
    color: #333;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ========================================
# 메인
# ========================================
st.title("📑 항공사 기업분석 자료")
st.markdown("각 항공사의 심층 기업분석 자료를 확인하세요!")

# 관리자 모드 체크
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# 사이드바에 관리자 로그인
with st.sidebar:
    st.markdown("---")
    st.markdown("### 🔐 관리자")

    if not st.session_state.is_admin:
        admin_pw = st.text_input("관리자 비밀번호", type="password", key="admin_pw")
        if st.button("관리자 로그인"):
            if admin_pw == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.success("관리자 모드 활성화!")
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다")
    else:
        st.success("✅ 관리자 모드")
        if st.button("로그아웃"):
            st.session_state.is_admin = False
            st.rerun()

# 탭
if st.session_state.is_admin:
    tab1, tab2 = st.tabs(["📥 자료 다운로드", "⚙️ 관리자 업로드"])
else:
    tab1, = st.tabs(["📥 자료 다운로드"])

# ========================================
# 탭1: 자료 다운로드
# ========================================
with tab1:
    st.markdown("### 📚 항공사별 기업분석 자료")
    st.info("💡 각 항공사의 심층 분석 자료 (10페이지 분량)를 다운로드할 수 있습니다.")

    # 필터
    filter_option = st.radio("필터", ["전체", "자료 있음", "자료 없음"], horizontal=True)

    meta = load_metadata()

    # 항공사 카드
    cols = st.columns(2)

    for i, airline in enumerate(AIRLINES):
        info = meta.get(airline)
        has_pdf = info is not None

        # 필터 적용
        if filter_option == "자료 있음" and not has_pdf:
            continue
        if filter_option == "자료 없음" and has_pdf:
            continue

        with cols[i % 2]:
            if has_pdf:
                st.markdown(f"""
                <div class="pdf-card pdf-available">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">✈️ {airline}</h4>
                        <span class="premium-badge">PDF 제공</span>
                    </div>
                    <p style="color: #666; margin: 10px 0;">{info.get('description', '기업분석 자료')}</p>
                    <small style="color: #999;">업로드: {info.get('uploaded_at', '-')} | {info.get('size', 0) // 1024}KB</small>
                </div>
                """, unsafe_allow_html=True)

                pdf_bytes = get_pdf_bytes(airline)
                if pdf_bytes:
                    st.download_button(
                        f"📥 {airline} 자료 다운로드",
                        data=pdf_bytes,
                        file_name=f"{airline}_기업분석.pdf",
                        mime="application/pdf",
                        key=f"download_{airline}",
                        use_container_width=True
                    )
            else:
                st.markdown(f"""
                <div class="pdf-card pdf-unavailable">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">✈️ {airline}</h4>
                        <span style="color: #dc3545; font-size: 12px;">준비중</span>
                    </div>
                    <p style="color: #999; margin: 10px 0;">자료 준비 중입니다.</p>
                </div>
                """, unsafe_allow_html=True)

    # 안내
    st.markdown("---")
    st.markdown("""
    #### 📋 기업분석 자료 내용
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
        st.markdown("### ⚙️ PDF 파일 관리")

        st.markdown("""
        <div class="admin-panel">
            <strong>⚠️ 관리자 전용</strong><br>
            각 항공사의 기업분석 PDF 파일을 업로드하거나 삭제할 수 있습니다.
        </div>
        """, unsafe_allow_html=True)

        # 업로드 섹션
        st.markdown("#### 📤 파일 업로드")

        col1, col2 = st.columns(2)

        with col1:
            selected_airline = st.selectbox("항공사 선택", AIRLINES, key="upload_airline")

        with col2:
            description = st.text_input("자료 설명", value="2026년 기업분석 자료", key="upload_desc")

        uploaded_file = st.file_uploader("PDF 파일 선택", type=["pdf"], key="pdf_upload")

        if uploaded_file:
            st.info(f"📄 선택된 파일: {uploaded_file.name} ({len(uploaded_file.getvalue()) // 1024}KB)")

            if st.button("📤 업로드", type="primary", use_container_width=True):
                if save_pdf(selected_airline, uploaded_file.getvalue(), uploaded_file.name, description):
                    st.success(f"✅ {selected_airline} 자료가 업로드되었습니다!")
                    st.rerun()
                else:
                    st.error("업로드 실패")

        st.markdown("---")

        # 현재 파일 목록
        st.markdown("#### 📋 업로드된 파일 목록")

        meta = load_metadata()

        if not meta:
            st.info("업로드된 파일이 없습니다.")
        else:
            for airline, info in meta.items():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"**✈️ {airline}**")
                    st.caption(f"{info.get('description', '-')} | {info.get('uploaded_at', '-')}")

                with col2:
                    st.caption(f"📄 {info.get('original_name', '-')}")
                    st.caption(f"💾 {info.get('size', 0) // 1024}KB")

                with col3:
                    if st.button("🗑️ 삭제", key=f"del_{airline}"):
                        if delete_pdf(airline):
                            st.success(f"{airline} 파일 삭제됨")
                            st.rerun()

                st.markdown("---")

st.markdown('</div>', unsafe_allow_html=True)
