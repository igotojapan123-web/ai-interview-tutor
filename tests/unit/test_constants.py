# tests/unit/test_constants.py
# FlyReady Lab - 상수 및 메시지 단위 테스트
# Stage 3: 대기업 수준 테스트

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestAppInfo:
    """앱 정보 테스트"""

    def test_app_name_exists(self):
        """APP_NAME 존재"""
        from constants import APP_NAME

        assert APP_NAME is not None
        assert len(APP_NAME) > 0
        assert "FlyReady" in APP_NAME

    def test_app_version_format(self):
        """APP_VERSION 형식"""
        from constants import APP_VERSION

        # 시맨틱 버전 형식 (X.Y.Z)
        parts = APP_VERSION.split(".")
        assert len(parts) >= 2

    def test_app_tagline_korean(self):
        """APP_TAGLINE 한국어"""
        from constants import APP_TAGLINE

        assert any('\uAC00' <= char <= '\uD7A3' for char in APP_TAGLINE)


class TestPageConfig:
    """페이지 설정 테스트"""

    def test_page_config_structure(self):
        """PAGE_CONFIG 구조"""
        from constants import PAGE_CONFIG

        assert "page_title" in PAGE_CONFIG
        assert "page_icon" in PAGE_CONFIG
        assert "layout" in PAGE_CONFIG

    def test_page_icon_airplane(self):
        """page_icon이 비행기 이모지"""
        from constants import PAGE_CONFIG

        assert PAGE_CONFIG["page_icon"] == "✈️"

    def test_pages_dict_structure(self):
        """PAGES 딕셔너리 구조"""
        from constants import PAGES

        assert len(PAGES) > 0

        for page_name, page_info in PAGES.items():
            assert "name" in page_info
            assert "icon" in page_info
            assert "desc" in page_info


class TestAirlineEnum:
    """항공사 Enum 테스트"""

    def test_airline_enum_exists(self):
        """Airline enum 존재"""
        from constants import Airline

        assert hasattr(Airline, 'KOREAN_AIR')
        assert hasattr(Airline, 'ASIANA')

    def test_airline_enum_values(self):
        """Airline 값이 한국어"""
        from constants import Airline

        assert Airline.KOREAN_AIR.value == "대한항공"
        assert Airline.ASIANA.value == "아시아나항공"


class TestAirlinesData:
    """항공사 데이터 테스트"""

    def test_airlines_dict_structure(self):
        """AIRLINES 딕셔너리 구조"""
        from constants import AIRLINES

        assert "대한항공" in AIRLINES
        assert "아시아나항공" in AIRLINES

        ke = AIRLINES["대한항공"]
        assert "code" in ke
        assert "english" in ke
        assert "hub" in ke
        assert "slogan" in ke
        assert "color" in ke

    def test_airline_codes(self):
        """항공사 코드"""
        from constants import AIRLINES

        assert AIRLINES["대한항공"]["code"] == "KE"
        assert AIRLINES["아시아나항공"]["code"] == "OZ"

    def test_airline_names_list(self):
        """AIRLINE_NAMES 리스트"""
        from constants import AIRLINE_NAMES

        assert isinstance(AIRLINE_NAMES, list)
        assert "대한항공" in AIRLINE_NAMES
        assert len(AIRLINE_NAMES) >= 5


class TestMessages:
    """메시지 상수 테스트"""

    def test_messages_class_exists(self):
        """Messages 클래스 존재"""
        from constants import Messages

        assert Messages is not None

    def test_loading_messages(self):
        """로딩 메시지"""
        from constants import Messages

        assert hasattr(Messages, 'LOADING_GENERAL')
        assert hasattr(Messages, 'LOADING_AI_ANALYSIS')
        assert hasattr(Messages, 'LOADING_VOICE')
        assert hasattr(Messages, 'LOADING_VIDEO')

        # 한국어 메시지
        assert any('\uAC00' <= c <= '\uD7A3' for c in Messages.LOADING_GENERAL)

    def test_success_messages(self):
        """성공 메시지"""
        from constants import Messages

        assert hasattr(Messages, 'SUCCESS_GENERAL')
        assert hasattr(Messages, 'SUCCESS_SAVE')
        assert "완료" in Messages.SUCCESS_GENERAL or "성공" in Messages.SUCCESS_GENERAL

    def test_error_messages(self):
        """에러 메시지"""
        from constants import Messages

        assert hasattr(Messages, 'ERROR_GENERAL')
        assert hasattr(Messages, 'ERROR_NETWORK')
        assert hasattr(Messages, 'ERROR_API')
        assert hasattr(Messages, 'ERROR_TIMEOUT')
        assert hasattr(Messages, 'ERROR_VALIDATION')

    def test_warning_messages(self):
        """경고 메시지"""
        from constants import Messages

        assert hasattr(Messages, 'WARNING_UNSAVED')
        assert hasattr(Messages, 'WARNING_CONFIRM')

    def test_placeholder_messages(self):
        """플레이스홀더 메시지"""
        from constants import Messages

        assert hasattr(Messages, 'PLACEHOLDER_TEXT')
        assert hasattr(Messages, 'PLACEHOLDER_SEARCH')


class TestButtonLabels:
    """버튼 레이블 테스트"""

    def test_button_labels_class_exists(self):
        """ButtonLabels 클래스 존재"""
        from constants import ButtonLabels

        assert ButtonLabels is not None

    def test_basic_buttons(self):
        """기본 버튼"""
        from constants import ButtonLabels

        assert hasattr(ButtonLabels, 'SUBMIT')
        assert hasattr(ButtonLabels, 'SAVE')
        assert hasattr(ButtonLabels, 'CANCEL')
        assert hasattr(ButtonLabels, 'CONFIRM')
        assert hasattr(ButtonLabels, 'DELETE')

    def test_navigation_buttons(self):
        """네비게이션 버튼"""
        from constants import ButtonLabels

        assert hasattr(ButtonLabels, 'NEXT')
        assert hasattr(ButtonLabels, 'PREV')
        assert hasattr(ButtonLabels, 'BACK')
        assert hasattr(ButtonLabels, 'HOME')

    def test_interview_buttons(self):
        """면접 관련 버튼"""
        from constants import ButtonLabels

        assert hasattr(ButtonLabels, 'START_INTERVIEW')
        assert hasattr(ButtonLabels, 'END_INTERVIEW')
        assert hasattr(ButtonLabels, 'NEXT_QUESTION')


class TestInterviewConfig:
    """면접 설정 테스트"""

    def test_interview_config_exists(self):
        """InterviewConfig 클래스 존재"""
        from constants import InterviewConfig

        assert InterviewConfig is not None

    def test_question_count_config(self):
        """질문 수 설정"""
        from constants import InterviewConfig

        assert hasattr(InterviewConfig, 'MIN_QUESTIONS')
        assert hasattr(InterviewConfig, 'DEFAULT_QUESTIONS')
        assert hasattr(InterviewConfig, 'MAX_QUESTIONS')

        assert InterviewConfig.MIN_QUESTIONS < InterviewConfig.DEFAULT_QUESTIONS
        assert InterviewConfig.DEFAULT_QUESTIONS < InterviewConfig.MAX_QUESTIONS

    def test_answer_time_config(self):
        """답변 시간 설정"""
        from constants import InterviewConfig

        assert hasattr(InterviewConfig, 'MIN_ANSWER_TIME')
        assert hasattr(InterviewConfig, 'DEFAULT_ANSWER_TIME')
        assert hasattr(InterviewConfig, 'MAX_ANSWER_TIME')

    def test_score_config(self):
        """점수 설정"""
        from constants import InterviewConfig

        assert hasattr(InterviewConfig, 'MIN_SCORE')
        assert hasattr(InterviewConfig, 'MAX_SCORE')
        assert hasattr(InterviewConfig, 'PASSING_SCORE')

        assert InterviewConfig.MIN_SCORE == 0
        assert InterviewConfig.MAX_SCORE == 100


class TestInterviewTypes:
    """면접 유형 테스트"""

    def test_interview_types_dict(self):
        """INTERVIEW_TYPES 딕셔너리"""
        from constants import INTERVIEW_TYPES

        assert "인성면접" in INTERVIEW_TYPES
        assert "직무면접" in INTERVIEW_TYPES
        assert "영어면접" in INTERVIEW_TYPES

        for name, info in INTERVIEW_TYPES.items():
            assert "description" in info
            assert "duration" in info
            assert "questions" in info

    def test_question_categories(self):
        """QUESTION_CATEGORIES 리스트"""
        from constants import QUESTION_CATEGORIES

        assert isinstance(QUESTION_CATEGORIES, list)
        assert "자기소개" in QUESTION_CATEGORIES
        assert "지원동기" in QUESTION_CATEGORIES
        assert len(QUESTION_CATEGORIES) >= 5


class TestEvaluationCriteria:
    """평가 기준 테스트"""

    def test_evaluation_criteria_exists(self):
        """EvaluationCriteria 클래스 존재"""
        from constants import EvaluationCriteria

        assert hasattr(EvaluationCriteria, 'CRITERIA')

    def test_criteria_structure(self):
        """평가 기준 구조"""
        from constants import EvaluationCriteria

        criteria = EvaluationCriteria.CRITERIA

        assert "내용" in criteria
        assert "표현" in criteria
        assert "태도" in criteria
        assert "구조" in criteria

        for name, info in criteria.items():
            assert "weight" in info
            assert "description" in info

    def test_criteria_weights_sum(self):
        """평가 기준 가중치 합계"""
        from constants import EvaluationCriteria

        total_weight = sum(
            c["weight"] for c in EvaluationCriteria.CRITERIA.values()
        )

        assert total_weight == 100


class TestScoreGrades:
    """점수 등급 테스트"""

    def test_score_grades_dict(self):
        """SCORE_GRADES 딕셔너리"""
        from constants import SCORE_GRADES

        assert "S" in SCORE_GRADES
        assert "A" in SCORE_GRADES
        assert "B" in SCORE_GRADES
        assert "C" in SCORE_GRADES
        assert "D" in SCORE_GRADES
        assert "F" in SCORE_GRADES

        for grade, info in SCORE_GRADES.items():
            assert "min" in info
            assert "label" in info
            assert "color" in info

    def test_get_score_grade_function(self):
        """get_score_grade 함수"""
        from constants import get_score_grade

        result_s = get_score_grade(95)
        assert result_s["grade"] == "S"

        result_a = get_score_grade(85)
        assert result_a["grade"] == "A"

        result_f = get_score_grade(30)
        assert result_f["grade"] == "F"


class TestLimits:
    """제한 설정 테스트"""

    def test_limits_class_exists(self):
        """Limits 클래스 존재"""
        from constants import Limits

        assert Limits is not None

    def test_file_upload_limits(self):
        """파일 업로드 제한"""
        from constants import Limits

        assert hasattr(Limits, 'MAX_FILE_SIZE_MB')
        assert hasattr(Limits, 'MAX_IMAGE_SIZE_MB')
        assert hasattr(Limits, 'MAX_VIDEO_SIZE_MB')

        assert Limits.MAX_FILE_SIZE_MB > 0

    def test_allowed_file_types(self):
        """허용 파일 유형"""
        from constants import Limits

        assert hasattr(Limits, 'ALLOWED_IMAGE_TYPES')
        assert hasattr(Limits, 'ALLOWED_VIDEO_TYPES')
        assert hasattr(Limits, 'ALLOWED_AUDIO_TYPES')

        assert "jpg" in Limits.ALLOWED_IMAGE_TYPES or "jpeg" in Limits.ALLOWED_IMAGE_TYPES
        assert "mp4" in Limits.ALLOWED_VIDEO_TYPES
        assert "mp3" in Limits.ALLOWED_AUDIO_TYPES

    def test_api_limits(self):
        """API 제한"""
        from constants import Limits

        assert hasattr(Limits, 'MAX_API_RETRIES')
        assert hasattr(Limits, 'API_TIMEOUT_SECONDS')
        assert hasattr(Limits, 'RATE_LIMIT_PER_MINUTE')

    def test_text_limits(self):
        """텍스트 제한"""
        from constants import Limits

        assert hasattr(Limits, 'MAX_INPUT_LENGTH')
        assert hasattr(Limits, 'MAX_PROMPT_LENGTH')


class TestColors:
    """색상 팔레트 테스트"""

    def test_colors_dict_exists(self):
        """COLORS 딕셔너리 존재"""
        from constants import COLORS

        assert COLORS is not None
        assert isinstance(COLORS, dict)

    def test_brand_colors(self):
        """브랜드 색상"""
        from constants import COLORS

        assert "primary" in COLORS
        assert "secondary" in COLORS
        assert "accent" in COLORS

    def test_status_colors(self):
        """상태 색상"""
        from constants import COLORS

        assert "success" in COLORS
        assert "warning" in COLORS
        assert "error" in COLORS
        assert "info" in COLORS

    def test_text_colors(self):
        """텍스트 색상"""
        from constants import COLORS

        assert "text_primary" in COLORS
        assert "text_secondary" in COLORS

    def test_color_format(self):
        """색상 형식 (HEX)"""
        from constants import COLORS

        for color_name, color_value in COLORS.items():
            assert color_value.startswith("#")
            assert len(color_value) == 7  # #RRGGBB


class TestKeyboardShortcuts:
    """키보드 단축키 테스트"""

    def test_keyboard_shortcuts_exists(self):
        """KEYBOARD_SHORTCUTS 존재"""
        from constants import KEYBOARD_SHORTCUTS

        assert KEYBOARD_SHORTCUTS is not None

    def test_common_shortcuts(self):
        """일반 단축키"""
        from constants import KEYBOARD_SHORTCUTS

        assert "save" in KEYBOARD_SHORTCUTS
        assert "submit" in KEYBOARD_SHORTCUTS


class TestRegexPatterns:
    """정규식 패턴 테스트"""

    def test_regex_patterns_exists(self):
        """REGEX_PATTERNS 존재"""
        from constants import REGEX_PATTERNS

        assert REGEX_PATTERNS is not None

    def test_email_pattern(self):
        """이메일 패턴"""
        from constants import REGEX_PATTERNS
        import re

        pattern = REGEX_PATTERNS["email"]
        assert re.match(pattern, "test@example.com")
        assert not re.match(pattern, "not-an-email")

    def test_url_pattern(self):
        """URL 패턴"""
        from constants import REGEX_PATTERNS
        import re

        pattern = REGEX_PATTERNS["url"]
        assert re.match(pattern, "https://www.example.com", re.IGNORECASE)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
