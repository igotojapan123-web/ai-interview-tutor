# env_config.py
# 환경변수 로드 및 검증을 위한 공통 모듈

import os
import re
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Tuple, Dict

# 로거 설정
logger = logging.getLogger(__name__)

# .env 파일 로드 (프로젝트 루트에서)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    logger.warning(".env 파일이 없습니다. .env.example을 참고하여 생성하세요.")


def get_env(key: str, default: str = "", required: bool = False) -> str:
    """환경변수를 안전하게 가져옴

    Args:
        key: 환경변수 키
        default: 기본값
        required: 필수 여부

    Returns:
        환경변수 값

    Raises:
        ValueError: required=True인데 값이 없을 때
    """
    value = os.environ.get(key, default)
    if required and not value:
        error_msg = f"필수 환경변수 '{key}'가 설정되지 않았습니다. .env 파일을 확인하세요."
        logger.error(error_msg)
        raise ValueError(error_msg)
    return value


def check_env_exists(key: str) -> bool:
    """환경변수 존재 여부 확인"""
    return bool(os.environ.get(key))


def validate_api_key(key: str, key_type: str) -> Tuple[bool, str]:
    """API 키 형식 검증

    Args:
        key: API 키 값
        key_type: 키 종류 (openai, google, did, clova)

    Returns:
        (유효 여부, 메시지)
    """
    if not key:
        return False, "API 키가 비어있습니다."

    if key_type == "openai":
        # OpenAI 키는 sk-로 시작하고 충분한 길이
        if not key.startswith("sk-"):
            return False, "OpenAI API 키는 'sk-'로 시작해야 합니다."
        if len(key) < 40:
            return False, "OpenAI API 키 길이가 너무 짧습니다."
        # 플레이스홀더 체크
        if "your" in key.lower() or "here" in key.lower():
            return False, "실제 OpenAI API 키를 입력하세요."
        return True, "OK"

    elif key_type == "google":
        if len(key) < 20:
            return False, "Google API 키 길이가 너무 짧습니다."
        if "your" in key.lower() or "here" in key.lower():
            return False, "실제 Google API 키를 입력하세요."
        return True, "OK"

    elif key_type == "did":
        if len(key) < 10:
            return False, "D-ID API 키 길이가 너무 짧습니다."
        return True, "OK"

    elif key_type == "clova":
        if len(key) < 10:
            return False, "CLOVA API 키 길이가 너무 짧습니다."
        return True, "OK"

    return True, "OK"


def mask_api_key(key: str, visible_chars: int = 8) -> str:
    """API 키를 마스킹하여 로그에 안전하게 출력

    Args:
        key: 원본 API 키
        visible_chars: 앞뒤로 보여줄 문자 수

    Returns:
        마스킹된 키 (예: sk-proj...noA)
    """
    if not key or len(key) < visible_chars * 2:
        return "***"
    return f"{key[:visible_chars]}...{key[-visible_chars:]}"


# API Keys
OPENAI_API_KEY = get_env("OPENAI_API_KEY") or get_env("OPENAI_APIKEY")
DID_API_KEY = get_env("DID_API_KEY")
CLOVA_CLIENT_ID = get_env("CLOVA_CLIENT_ID")
CLOVA_CLIENT_SECRET = get_env("CLOVA_CLIENT_SECRET")
GOOGLE_TTS_API_KEY = get_env("GOOGLE_TTS_API_KEY") or get_env("GOOGLE_CLOUD_API_KEY") or get_env("GOOGLE_API_KEY")

# App Passwords - 환경변수 필수 (보안상 기본값 제거)
TESTER_PASSWORD = get_env("TESTER_PASSWORD")
ADMIN_PASSWORD = get_env("ADMIN_PASSWORD")

def check_passwords_configured() -> Tuple[bool, str]:
    """비밀번호 설정 상태 확인"""
    missing = []
    if not TESTER_PASSWORD:
        missing.append("TESTER_PASSWORD")
    if not ADMIN_PASSWORD:
        missing.append("ADMIN_PASSWORD")

    if missing:
        return False, f"비밀번호가 설정되지 않았습니다: {', '.join(missing)}. .env 파일에 추가하세요."
    return True, "비밀번호가 올바르게 설정되었습니다."


def check_openai_key() -> Tuple[bool, str]:
    """OpenAI API 키 상태 확인"""
    if not OPENAI_API_KEY:
        return False, "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가하세요."
    return validate_api_key(OPENAI_API_KEY, "openai")


def check_google_tts_key() -> Tuple[bool, str]:
    """Google TTS API 키 상태 확인"""
    if not GOOGLE_TTS_API_KEY:
        return False, "Google TTS API 키가 설정되지 않았습니다."
    return validate_api_key(GOOGLE_TTS_API_KEY, "google")


def check_all_keys() -> Dict[str, bool]:
    """모든 API 키 상태 확인"""
    return {
        "openai": bool(OPENAI_API_KEY) and validate_api_key(OPENAI_API_KEY, "openai")[0],
        "did": bool(DID_API_KEY) and validate_api_key(DID_API_KEY, "did")[0],
        "clova": bool(CLOVA_CLIENT_ID and CLOVA_CLIENT_SECRET),
        "google_tts": bool(GOOGLE_TTS_API_KEY) and validate_api_key(GOOGLE_TTS_API_KEY, "google")[0],
    }


def get_api_status_message() -> str:
    """API 상태 요약 메시지 반환"""
    status = check_all_keys()
    messages = []

    if status["openai"]:
        messages.append(f"OpenAI: {mask_api_key(OPENAI_API_KEY)}")
    else:
        messages.append("OpenAI: 미설정")

    if status["google_tts"]:
        messages.append(f"Google TTS: {mask_api_key(GOOGLE_TTS_API_KEY)}")
    else:
        messages.append("Google TTS: 미설정")

    if status["clova"]:
        messages.append("CLOVA: 설정됨")
    else:
        messages.append("CLOVA: 미설정")

    if status["did"]:
        messages.append("D-ID: 설정됨")
    else:
        messages.append("D-ID: 미설정")

    return " | ".join(messages)
