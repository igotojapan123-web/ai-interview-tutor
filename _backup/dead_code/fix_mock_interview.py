#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 모의면접 페이지 웹캠 섹션 수정

import os

path = os.path.join(os.path.dirname(__file__), "pages", "4_모의면접.py")

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_section = '''        # Phase 2: 웹캠 분석 영역
        if st.session_state.mock_webcam_enabled and WEBCAM_AVAILABLE:
            webcam_col, feedback_col = st.columns([2, 1])

            with webcam_col:
                st.markdown("##### 📹 실시간 자세 분석")
                webcam_ctx = create_webcam_streamer(
                    key=f"mock_webcam_{current_idx}",
                    analysis_enabled=True
                )

                if webcam_ctx and webcam_ctx.get("is_playing"):
                    # 웹캠 점수 수집
                    processor = webcam_ctx.get("processor")
                    if processor:
                        avg_score = processor.get_average_score()
                        if avg_score > 0:
                            st.session_state.mock_webcam_scores.append(avg_score)

            with feedback_col:
                st.markdown("##### 실시간 피드백")
                feedback_placeholder = st.empty()

                if webcam_ctx and webcam_ctx.get("is_playing"):
                    processor = webcam_ctx.get("processor")
                    if processor:
                        feedback = processor.get_latest_feedback()
                        feedback_placeholder.markdown(
                            get_realtime_feedback_html(feedback),
                            unsafe_allow_html=True
                        )
                else:
                    feedback_placeholder.markdown(
                        get_webcam_placeholder_html(),
                        unsafe_allow_html=True
                    )'''

new_section = '''        # Phase 2: 웹캠 분석 영역 (단순화)
        if st.session_state.mock_webcam_enabled and WEBCAM_AVAILABLE:
            st.markdown("##### 📹 자세 분석 활성화")
            st.caption("답변하는 동안 자세를 분석합니다. 결과는 면접 완료 후 확인할 수 있습니다.")

            webcam_ctx = create_webcam_streamer(
                key=f"mock_webcam_{current_idx}",
                analysis_enabled=True
            )

            if webcam_ctx and webcam_ctx.get("is_playing"):
                processor = webcam_ctx.get("processor")
                if processor:
                    avg_score = processor.get_average_score()
                    if avg_score > 0:
                        st.session_state.mock_webcam_scores.append(avg_score)
                        # 간단한 상태 표시
                        if avg_score >= 70:
                            st.success(f"현재 자세 점수: {avg_score:.0f}/100 - 좋음")
                        elif avg_score >= 50:
                            st.warning(f"현재 자세 점수: {avg_score:.0f}/100 - 개선 필요")
                        else:
                            st.error(f"현재 자세 점수: {avg_score:.0f}/100 - 바른 자세 유지")
                    # 피드백 수집
                    feedback = processor.get_latest_feedback()
                    if feedback:
                        for fb in feedback:
                            st.session_state.mock_posture_feedback.append({
                                "type": fb.feedback_type.value,
                                "message": fb.message,
                                "priority": fb.priority.value
                            })
            else:
                st.info("웹캠을 시작하려면 START 버튼을 클릭하세요")'''

if old_section in content:
    content = content.replace(old_section, new_section)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("모의면접.py 웹캠 섹션 수정 완료")
else:
    print("수정할 섹션을 찾을 수 없습니다")
