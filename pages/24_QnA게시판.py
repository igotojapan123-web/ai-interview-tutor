# pages/24_QnA게시판.py
# 준비생 Q&A 게시판

import streamlit as st
import os
import json
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AIRLINES

from sidebar_common import render_sidebar

st.set_page_config(
    page_title="Q&A 게시판",
    page_icon="💬",
    layout="wide"
)
render_sidebar("QnA게시판")





# ----------------------------
# 데이터
# ----------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
QNA_FILE = os.path.join(DATA_DIR, "qna_board.json")


def load_qna():
    if os.path.exists(QNA_FILE):
        try:
            with open(QNA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def save_qna(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(QNA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 카테고리
CATEGORIES = {
    "전체": {"icon": "📋", "color": "#6b7280"},
    "서류/자소서": {"icon": "📝", "color": "#3b82f6"},
    "면접 준비": {"icon": "🎤", "color": "#8b5cf6"},
    "체력/수영": {"icon": "🏊", "color": "#10b981"},
    "이미지메이킹": {"icon": "👗", "color": "#ec4899"},
    "항공사 정보": {"icon": "✈️", "color": "#f59e0b"},
    "합격 후기": {"icon": "🏆", "color": "#eab308"},
    "기타": {"icon": "💭", "color": "#6b7280"},
}


# ----------------------------
# UI
# ----------------------------
st.title("💬 Q&A 게시판")
st.caption("승무원 준비생들의 질문과 답변 공간")

qna_data = load_qna()

# 탭 구성
tab1, tab2 = st.tabs(["📋 질문 보기", "✍️ 질문하기"])

# ========== 탭1: 질문 보기 ==========
with tab1:
    # 필터
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        filter_category = st.selectbox(
            "카테고리",
            list(CATEGORIES.keys()),
            format_func=lambda x: f"{CATEGORIES[x]['icon']} {x}"
        )

    with col2:
        search_keyword = st.text_input("검색", placeholder="키워드로 검색...")

    with col3:
        st.metric("총 질문", f"{len(qna_data)}개")

    st.markdown("---")

    # 필터링
    filtered = qna_data

    if filter_category != "전체":
        filtered = [q for q in filtered if q.get("category") == filter_category]

    if search_keyword:
        filtered = [q for q in filtered if
                    search_keyword.lower() in q.get("title", "").lower() or
                    search_keyword.lower() in q.get("content", "").lower()]

    # 최신순 정렬
    filtered = sorted(filtered, key=lambda x: x.get("created_at", ""), reverse=True)

    if not filtered:
        st.info("해당 조건의 질문이 없습니다.")
    else:
        for q in filtered:
            cat = CATEGORIES.get(q.get("category", "기타"), CATEGORIES["기타"])
            answer_count = len(q.get("answers", []))
            has_answer = answer_count > 0

            # 카드 스타일
            with st.expander(
                f"{cat['icon']} [{q.get('category', '')}] {q.get('title', '')} {'✅' if has_answer else '❓'} ({answer_count}개 답변)",
                expanded=False
            ):
                # 질문 정보
                st.caption(f"👤 {q.get('nickname', '익명')} | {q.get('created_at', '')[:10]}")

                st.markdown("---")
                st.markdown("**질문 내용:**")
                st.write(q.get("content", ""))

                if q.get("airline"):
                    st.caption(f"✈️ 관련 항공사: {q.get('airline')}")

                # 답변들
                answers = q.get("answers", [])
                if answers:
                    st.markdown("---")
                    st.markdown(f"**💬 답변 ({len(answers)}개)**")

                    for ans in answers:
                        st.markdown(f"""
                        <div style="background: #f8fafc; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #3b82f6;">
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">👤 {ans.get('nickname', '익명')} | {ans.get('created_at', '')[:10]}</div>
                            <div>{ans.get('content', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # 답변 달기
                st.markdown("---")
                with st.form(key=f"answer_form_{q.get('id')}"):
                    st.markdown("**답변 달기**")
                    ans_nickname = st.text_input("닉네임", placeholder="익명", key=f"ans_nick_{q.get('id')}")
                    ans_content = st.text_area("답변 내용", height=100, key=f"ans_content_{q.get('id')}")

                    if st.form_submit_button("답변 등록", use_container_width=True):
                        if ans_content.strip():
                            new_answer = {
                                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                                "nickname": ans_nickname.strip() if ans_nickname.strip() else "익명",
                                "content": ans_content.strip(),
                                "created_at": datetime.now().isoformat()
                            }

                            # 답변 추가
                            for item in qna_data:
                                if item.get("id") == q.get("id"):
                                    if "answers" not in item:
                                        item["answers"] = []
                                    item["answers"].append(new_answer)
                                    break

                            save_qna(qna_data)
                            st.success("답변이 등록되었습니다!")
                            st.rerun()
                        else:
                            st.error("답변 내용을 입력해주세요.")


# ========== 탭2: 질문하기 ==========
with tab2:
    st.subheader("✍️ 새 질문 작성")

    with st.form("new_question"):
        q_nickname = st.text_input("닉네임", placeholder="익명으로 할 경우 비워두세요")

        col1, col2 = st.columns(2)
        with col1:
            q_category = st.selectbox(
                "카테고리 *",
                [k for k in CATEGORIES.keys() if k != "전체"],
                format_func=lambda x: f"{CATEGORIES[x]['icon']} {x}"
            )
        with col2:
            q_airline = st.selectbox("관련 항공사 (선택)", ["없음"] + AIRLINES)

        q_title = st.text_input("제목 *", placeholder="질문 제목을 입력하세요")
        q_content = st.text_area("질문 내용 *", height=200, placeholder="궁금한 점을 자세히 작성해주세요")

        submitted = st.form_submit_button("질문 등록", type="primary", use_container_width=True)

        if submitted:
            if not q_title.strip():
                st.error("제목을 입력해주세요.")
            elif not q_content.strip():
                st.error("질문 내용을 입력해주세요.")
            elif len(q_content.strip()) < 10:
                st.error("질문 내용을 10자 이상 작성해주세요.")
            else:
                new_question = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "nickname": q_nickname.strip() if q_nickname.strip() else "익명",
                    "category": q_category,
                    "airline": q_airline if q_airline != "없음" else "",
                    "title": q_title.strip(),
                    "content": q_content.strip(),
                    "answers": [],
                    "created_at": datetime.now().isoformat()
                }

                qna_data.append(new_question)
                save_qna(qna_data)

                st.success("질문이 등록되었습니다!")
                st.balloons()
                st.rerun()

    st.markdown("---")

    st.info("""
    **게시판 이용 안내**
    - 서로 존중하는 마음으로 질문과 답변을 작성해주세요
    - 개인정보가 포함된 내용은 삼가주세요
    - 허위 정보 유포 시 삭제될 수 있습니다
    - 합격 후기는 '합격자 DB' 페이지를 이용해주세요
    """)
