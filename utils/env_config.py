# env_config.py
# 환경변수 로드 및 검증

import os
from pathlib import Path
from typing import Optional, Tuple
import streamlit as st

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # dotenv 없으면 Streamlit secrets 사용


def get_env(key: str, default: str = "") -> str:
    """환경변수 또는 Streamlit secrets에서 값 가져오기"""
    # 1. 환경변수 확인
    value = os.environ.get(key, "")
    if value:
        return value

    # 2. Streamlit secrets 확인
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass

    return default


def mask_api_key(key: str, visible_chars: int = 8) -> str:
    """API 키 마스킹"""
    if not key or len(key) < visible_chars * 2:
        return "***"
    return f"{key[:visible_chars]}...{key[-visible_chars:]}"


def validate_openai_key(key: str) -> Tuple[bool, str]:
    """OpenAI API 키 형식 검증"""
    if not key:
        return False, "API 키가 비어있습니다."
    if not key.startswith("sk-"):
        return False, "OpenAI API 키는 'sk-'로 시작해야 합니다."
    if len(key) < 40:
        return False, "API 키 길이가 너무 짧습니다."
    return True, "OK"


# API Keys (대소문자 모두 지원)
OPENAI_API_KEY = get_env("OPENAI_API_KEY") or get_env("OPENAI_APIKEY") or get_env("openai_api_key")


def check_openai_key() -> Tuple[bool, str]:
    """OpenAI API 키 상태 확인"""
    if not OPENAI_API_KEY:
        return False, "OpenAI API 키가 설정되지 않았습니다."
    return validate_openai_key(OPENAI_API_KEY)


def get_api_key() -> Optional[str]:
    """OpenAI API 키 반환"""
    return OPENAI_API_KEY if OPENAI_API_KEY else None
