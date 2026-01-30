# tests/conftest.py
# pytest 공통 fixtures

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# 프로젝트 루트 경로 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 기본 Fixtures
# ============================================================

@pytest.fixture
def sample_user_id():
    """테스트용 사용자 ID"""
    return "test_user_12345"


@pytest.fixture
def sample_session_id():
    """테스트용 세션 ID"""
    return "test_session_abc123"


@pytest.fixture
def sample_airline():
    """테스트용 항공사"""
    return "korean_air"


@pytest.fixture
def sample_question():
    """테스트용 면접 질문"""
    return {
        "id": "q001",
        "text": "자기소개를 해주세요.",
        "category": "인성",
        "difficulty": "easy"
    }


@pytest.fixture
def sample_answer():
    """테스트용 답변"""
    return "안녕하세요. 저는 승무원을 꿈꾸는 김지원입니다."


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_openai_client():
    """OpenAI 클라이언트 모킹"""
    with patch('openai.OpenAI') as mock:
        client = MagicMock()
        mock.return_value = client
        
        # Chat completion 모킹
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(content="모의 응답입니다.")
            )]
        )
        
        yield client


@pytest.fixture
def mock_streamlit():
    """Streamlit 세션 모킹"""
    mock_session = MagicMock()
    mock_session.session_state = {}
    
    with patch.dict('sys.modules', {'streamlit': mock_session}):
        yield mock_session


@pytest.fixture
def temp_data_dir(tmp_path):
    """임시 데이터 디렉토리"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def temp_cache_dir(tmp_path):
    """임시 캐시 디렉토리"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


# ============================================================
# 테스트 유틸리티
# ============================================================

@pytest.fixture
def assert_json_structure():
    """JSON 구조 검증 헬퍼"""
    def _assert(data, required_keys):
        for key in required_keys:
            assert key in data, f"Missing key: {key}"
    return _assert


@pytest.fixture
def create_test_file(tmp_path):
    """테스트 파일 생성 헬퍼"""
    def _create(filename, content):
        file_path = tmp_path / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    return _create
