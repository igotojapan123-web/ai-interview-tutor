# tests/conftest.py
# FlyReady Lab - 대기업 수준 테스트 설정
# Stage 3: pytest fixtures 및 공통 설정

import pytest
import sys
import os
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import MagicMock, patch
from datetime import datetime

# 프로젝트 루트를 path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Streamlit Mock (테스트 환경에서 Streamlit 사용)
# =============================================================================

class MockSessionState(dict):
    """Streamlit session_state 모킹"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._callbacks = {}

    def __setattr__(self, key, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __getattr__(self, key):
        if key.startswith('_'):
            return super().__getattribute__(key)
        return self.get(key)

    def __delattr__(self, key):
        if key in self:
            del self[key]


@pytest.fixture
def mock_streamlit():
    """Streamlit 모듈 모킹"""
    mock_st = MagicMock()
    mock_st.session_state = MockSessionState()
    mock_st.secrets = {}
    mock_st.cache_data = lambda **kwargs: lambda f: f
    mock_st.cache_resource = lambda **kwargs: lambda f: f

    # UI 컴포넌트 모킹
    mock_st.markdown = MagicMock()
    mock_st.write = MagicMock()
    mock_st.error = MagicMock()
    mock_st.warning = MagicMock()
    mock_st.info = MagicMock()
    mock_st.success = MagicMock()
    mock_st.spinner = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    mock_st.progress = MagicMock()
    mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock()])
    mock_st.container = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    mock_st.rerun = MagicMock()

    with patch.dict('sys.modules', {'streamlit': mock_st}):
        yield mock_st


@pytest.fixture
def session_state():
    """깨끗한 session_state 제공"""
    return MockSessionState()


# =============================================================================
# 샘플 데이터 Fixtures
# =============================================================================

@pytest.fixture
def sample_user_input() -> Dict[str, str]:
    """샘플 사용자 입력"""
    return {
        "text": "안녕하세요, 저는 대한항공 객실승무원에 지원하는 홍길동입니다.",
        "email": "test@example.com",
        "url": "https://www.koreanair.com",
        "phone": "010-1234-5678",
    }


@pytest.fixture
def sample_airline_data() -> Dict[str, Any]:
    """샘플 항공사 데이터"""
    return {
        "name": "대한항공",
        "code": "KE",
        "english": "Korean Air",
        "hub": "인천국제공항",
        "slogan": "Excellence in Flight",
        "values": ["안전", "서비스", "혁신", "글로벌"],
    }


@pytest.fixture
def sample_interview_data() -> Dict[str, Any]:
    """샘플 면접 데이터"""
    return {
        "question": "간단하게 자기소개 해주세요.",
        "answer": "안녕하세요, 저는 대한항공 객실승무원에 지원한 홍길동입니다. "
                  "저는 서비스 정신과 글로벌 역량을 갖추고 있으며, "
                  "팀워크를 중시하는 성격입니다.",
        "category": "자기소개",
        "score": 85,
        "feedback": "명확하고 자신감 있는 답변입니다.",
    }


@pytest.fixture
def sample_essay() -> str:
    """샘플 자기소개서"""
    return """
    저는 대한항공 객실승무원에 지원하게 된 홍길동입니다.

    어린 시절부터 하늘을 나는 꿈을 꿔왔고, 서비스업에서 5년간
    다양한 고객들을 만나며 소통 능력을 키워왔습니다.

    특히 글로벌 환경에서 일하고 싶은 열망이 있어,
    영어와 중국어를 꾸준히 공부하고 있습니다.

    대한항공의 'Excellence in Flight' 슬로건처럼,
    최고의 서비스를 제공하는 승무원이 되겠습니다.
    """


@pytest.fixture
def sample_html_content() -> Dict[str, str]:
    """XSS 테스트용 HTML 콘텐츠"""
    return {
        "safe": "안녕하세요",
        "script": "<script>alert('xss')</script>",
        "img_onerror": '<img src="x" onerror="alert(1)">',
        "event_handler": '<div onclick="alert(1)">클릭</div>',
        "javascript_url": '<a href="javascript:alert(1)">링크</a>',
    }


# =============================================================================
# 성능 측정 Fixtures
# =============================================================================

@pytest.fixture
def timer():
    """실행 시간 측정 fixture"""
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = 0

        def start(self):
            self.start_time = datetime.now()
            return self

        def stop(self):
            self.end_time = datetime.now()
            self.elapsed = (self.end_time - self.start_time).total_seconds()
            return self.elapsed

        def __enter__(self):
            self.start()
            return self

        def __exit__(self, *args):
            self.stop()

    return Timer()


# =============================================================================
# 파일 시스템 Fixtures
# =============================================================================

@pytest.fixture
def temp_json_file(tmp_path) -> Path:
    """임시 JSON 파일"""
    import json

    file_path = tmp_path / "test_data.json"
    test_data = {"key": "value", "items": [1, 2, 3]}

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False)

    return file_path


@pytest.fixture
def temp_dir(tmp_path) -> Path:
    """임시 디렉토리"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    return test_dir


# =============================================================================
# API Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_openai_response():
    """OpenAI API 응답 모킹"""
    def _make_response(content: str = "AI 응답입니다."):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = content
        return mock_response

    return _make_response


@pytest.fixture
def mock_api_key():
    """테스트용 API 키"""
    return "sk-test-" + "a" * 48


# =============================================================================
# 에러 테스트 Fixtures
# =============================================================================

@pytest.fixture
def error_scenarios():
    """에러 시나리오 모음"""
    return {
        "network": {
            "type": "NetworkError",
            "message": "네트워크 연결 실패",
            "code": "NET_ERR_001",
        },
        "api": {
            "type": "APIError",
            "message": "API 호출 실패",
            "code": "API_ERR_001",
        },
        "validation": {
            "type": "ValidationError",
            "message": "입력값 검증 실패",
            "code": "VAL_ERR_001",
        },
        "timeout": {
            "type": "TimeoutError",
            "message": "요청 시간 초과",
            "code": "TMO_ERR_001",
        },
        "auth": {
            "type": "AuthenticationError",
            "message": "인증 실패",
            "code": "AUTH_ERR_001",
        },
    }


# =============================================================================
# 마커 등록
# =============================================================================

def pytest_configure(config):
    """pytest 마커 등록"""
    config.addinivalue_line("markers", "unit: 단위 테스트")
    config.addinivalue_line("markers", "integration: 통합 테스트")
    config.addinivalue_line("markers", "slow: 느린 테스트")
    config.addinivalue_line("markers", "api: API 호출 테스트")
    config.addinivalue_line("markers", "ui: UI 테스트")


# =============================================================================
# 테스트 리포트 훅 (선택적)
# =============================================================================

# pytest-html이 설치된 경우에만 훅 등록
try:
    import pytest_html

    def pytest_html_report_title(report):
        """HTML 리포트 제목"""
        report.title = "FlyReady Lab 테스트 리포트"
except ImportError:
    pass


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """터미널 요약 커스터마이징"""
    terminalreporter.write_sep("=", "FlyReady Lab 테스트 완료")

    passed = len(terminalreporter.stats.get('passed', []))
    failed = len(terminalreporter.stats.get('failed', []))
    skipped = len(terminalreporter.stats.get('skipped', []))

    terminalreporter.write_line(f"통과: {passed}, 실패: {failed}, 건너뜀: {skipped}")
