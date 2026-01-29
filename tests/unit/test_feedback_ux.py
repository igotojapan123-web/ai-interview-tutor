# tests/unit/test_feedback_ux.py
# FlyReady Lab - 사용자 피드백 UX 단위 테스트
# Stage 3: 대기업 수준 테스트

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestLoadingTypes:
    """로딩 유형 테스트"""

    def test_loading_type_enum_exists(self):
        """LoadingType enum 존재"""
        from feedback_ux import LoadingType

        assert hasattr(LoadingType, 'GENERAL')
        assert hasattr(LoadingType, 'AI_ANALYSIS')
        assert hasattr(LoadingType, 'VOICE')
        assert hasattr(LoadingType, 'VIDEO')
        assert hasattr(LoadingType, 'FILE')
        assert hasattr(LoadingType, 'NETWORK')
        assert hasattr(LoadingType, 'SAVE')

    def test_loading_messages_dict(self):
        """LOADING_MESSAGES 딕셔너리"""
        from feedback_ux import LOADING_MESSAGES, LoadingType

        # 모든 로딩 타입에 대해 메시지 존재
        for loading_type in LoadingType:
            assert loading_type in LOADING_MESSAGES

            messages = LOADING_MESSAGES[loading_type]
            assert "start" in messages
            assert "progress" in messages
            assert "finish" in messages

    def test_loading_messages_korean(self):
        """로딩 메시지가 한국어"""
        from feedback_ux import LOADING_MESSAGES

        for loading_type, messages in LOADING_MESSAGES.items():
            for stage, message in messages.items():
                # 한국어가 포함되어야 함
                assert any('\uAC00' <= char <= '\uD7A3' for char in message)

    def test_get_loading_message_function(self):
        """get_loading_message 함수"""
        from feedback_ux import get_loading_message, LoadingType

        message = get_loading_message(LoadingType.AI_ANALYSIS, "start")
        assert len(message) > 0

        # 기본 스테이지
        message_default = get_loading_message(LoadingType.GENERAL)
        assert len(message_default) > 0


class TestSpinnerComponents:
    """스피너 컴포넌트 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.spinner = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
            mock.markdown = MagicMock()
            yield mock

    def test_loading_spinner_function_exists(self):
        """loading_spinner 함수 존재"""
        from feedback_ux import loading_spinner

        assert callable(loading_spinner)

    def test_render_loading_overlay_function_exists(self):
        """render_loading_overlay 함수 존재"""
        from feedback_ux import render_loading_overlay

        assert callable(render_loading_overlay)


class TestSkeletonLoader:
    """스켈레톤 로더 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.markdown = MagicMock()
            yield mock

    def test_render_skeleton_function_exists(self):
        """render_skeleton 함수 존재"""
        from feedback_ux import render_skeleton

        assert callable(render_skeleton)

    def test_render_skeleton_default(self, mock_st):
        """기본 스켈레톤 렌더링"""
        from feedback_ux import render_skeleton

        render_skeleton()
        mock_st.markdown.assert_called()

    def test_render_skeleton_with_options(self, mock_st):
        """옵션이 있는 스켈레톤 렌더링"""
        from feedback_ux import render_skeleton

        render_skeleton(count=5, show_avatar=True, line_height=24)
        mock_st.markdown.assert_called()

    def test_render_card_skeleton_function_exists(self):
        """render_card_skeleton 함수 존재"""
        from feedback_ux import render_card_skeleton

        assert callable(render_card_skeleton)


class TestProgressIndicator:
    """진행률 표시 테스트"""

    def test_progress_state_dataclass(self):
        """ProgressState 데이터 클래스"""
        from feedback_ux import ProgressState

        state = ProgressState(current=50, total=100, message="처리 중")

        assert state.current == 50
        assert state.total == 100
        assert state.message == "처리 중"

    def test_progress_state_defaults(self):
        """ProgressState 기본값"""
        from feedback_ux import ProgressState

        state = ProgressState()

        assert state.current == 0
        assert state.total == 100

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.markdown = MagicMock()
            mock.progress = MagicMock(return_value=MagicMock())
            yield mock

    def test_render_progress_indicator_exists(self):
        """render_progress_indicator 함수 존재"""
        from feedback_ux import render_progress_indicator

        assert callable(render_progress_indicator)

    def test_create_progress_tracker_exists(self):
        """create_progress_tracker 함수 존재"""
        from feedback_ux import create_progress_tracker

        assert callable(create_progress_tracker)


class TestToastNotifications:
    """토스트 알림 테스트"""

    def test_toast_type_enum(self):
        """ToastType enum"""
        from feedback_ux import ToastType

        assert hasattr(ToastType, 'SUCCESS')
        assert hasattr(ToastType, 'ERROR')
        assert hasattr(ToastType, 'WARNING')
        assert hasattr(ToastType, 'INFO')

    def test_toast_styles_dict(self):
        """TOAST_STYLES 딕셔너리"""
        from feedback_ux import TOAST_STYLES, ToastType

        for toast_type in ToastType:
            assert toast_type in TOAST_STYLES

            style = TOAST_STYLES[toast_type]
            assert "bg" in style
            assert "border" in style
            assert "icon" in style

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.markdown = MagicMock()
            yield mock

    def test_show_toast_function_exists(self):
        """show_toast 함수 존재"""
        from feedback_ux import show_toast

        assert callable(show_toast)

    def test_toast_convenience_functions(self):
        """토스트 편의 함수들"""
        from feedback_ux import toast_success, toast_error, toast_warning, toast_info

        assert callable(toast_success)
        assert callable(toast_error)
        assert callable(toast_warning)
        assert callable(toast_info)


class TestRetryUI:
    """재시도 UI 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.session_state = {}
            mock.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
            mock.error = MagicMock()
            mock.button = MagicMock(return_value=False)
            mock.spinner = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
            mock.rerun = MagicMock()
            yield mock

    def test_render_retry_button_exists(self):
        """render_retry_button 함수 존재"""
        from feedback_ux import render_retry_button

        assert callable(render_retry_button)

    def test_with_retry_ui_exists(self):
        """with_retry_ui 함수 존재"""
        from feedback_ux import with_retry_ui

        assert callable(with_retry_ui)


class TestEmptyState:
    """빈 상태 화면 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.markdown = MagicMock()
            mock.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
            mock.button = MagicMock(return_value=False)
            yield mock

    def test_render_empty_state_exists(self):
        """render_empty_state 함수 존재"""
        from feedback_ux import render_empty_state

        assert callable(render_empty_state)

    def test_render_empty_state_basic(self, mock_st):
        """기본 빈 상태 렌더링"""
        from feedback_ux import render_empty_state

        render_empty_state(
            title="데이터 없음",
            description="아직 데이터가 없습니다."
        )

        mock_st.markdown.assert_called()


class TestCompletionScreen:
    """완료 화면 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.markdown = MagicMock()
            mock.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
            mock.button = MagicMock(return_value=False)
            yield mock

    def test_render_completion_screen_exists(self):
        """render_completion_screen 함수 존재"""
        from feedback_ux import render_completion_screen

        assert callable(render_completion_screen)

    def test_render_completion_screen_default(self, mock_st):
        """기본 완료 화면 렌더링"""
        from feedback_ux import render_completion_screen

        render_completion_screen()

        mock_st.markdown.assert_called()


class TestConfirmDialog:
    """확인 다이얼로그 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.session_state = {}
            mock.markdown = MagicMock()
            mock.container = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
            mock.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock()])
            mock.button = MagicMock(return_value=False)
            mock.rerun = MagicMock()
            yield mock

    def test_confirm_dialog_exists(self):
        """confirm_dialog 함수 존재"""
        from feedback_ux import confirm_dialog

        assert callable(confirm_dialog)


class TestStepIndicator:
    """단계 표시기 테스트"""

    @pytest.fixture
    def mock_st(self):
        """Streamlit 모킹"""
        with patch('feedback_ux.st') as mock:
            mock.markdown = MagicMock()
            yield mock

    def test_render_step_indicator_exists(self):
        """render_step_indicator 함수 존재"""
        from feedback_ux import render_step_indicator

        assert callable(render_step_indicator)

    def test_render_step_indicator_basic(self, mock_st):
        """기본 단계 표시기 렌더링"""
        from feedback_ux import render_step_indicator

        steps = ["설정", "입력", "확인", "완료"]
        render_step_indicator(steps, current_step=1)

        mock_st.markdown.assert_called()

    def test_render_step_indicator_with_completed(self, mock_st):
        """완료된 단계 포함 렌더링"""
        from feedback_ux import render_step_indicator

        steps = ["1단계", "2단계", "3단계"]
        render_step_indicator(steps, current_step=2, completed_steps=[0, 1])

        mock_st.markdown.assert_called()


class TestFeedbackUXIntegration:
    """피드백 UX 통합 테스트"""

    def test_all_main_functions_importable(self):
        """모든 주요 함수 import 가능"""
        from feedback_ux import (
            LoadingType,
            LOADING_MESSAGES,
            get_loading_message,
            loading_spinner,
            render_loading_overlay,
            render_skeleton,
            render_card_skeleton,
            ProgressState,
            render_progress_indicator,
            create_progress_tracker,
            ToastType,
            show_toast,
            toast_success,
            toast_error,
            toast_warning,
            toast_info,
            render_retry_button,
            with_retry_ui,
            render_empty_state,
            render_completion_screen,
            confirm_dialog,
            render_step_indicator,
        )

        # 모든 import 성공
        assert True

    def test_consistent_korean_messages(self):
        """한국어 메시지 일관성"""
        from feedback_ux import LOADING_MESSAGES, TOAST_STYLES

        # 모든 로딩 메시지가 한국어
        for loading_type, messages in LOADING_MESSAGES.items():
            for stage, message in messages.items():
                assert any('\uAC00' <= c <= '\uD7A3' for c in message), \
                    f"{loading_type}.{stage}: '{message}' is not Korean"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
