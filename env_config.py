# env_config.py
# 환경변수 로드 및 검증을 위한 공통 모듈

import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    # .env 파일이 없으면 .env.example 경로 안내
    pass

def get_env(key: str, default: str = "", required: bool = False) -> str:
    """환경변수를 안전하게 가져옴"""
    value = os.environ.get(key, default)
    if required and not value:
        raise ValueError(f"필수 환경변수 '{key}'가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return value

def check_env_exists(key: str) -> bool:
    """환경변수 존재 여부 확인"""
    return bool(os.environ.get(key))

# API Keys
OPENAI_API_KEY = get_env("OPENAI_API_KEY") or get_env("OPENAI_APIKEY")
DID_API_KEY = get_env("DID_API_KEY")
CLOVA_CLIENT_ID = get_env("CLOVA_CLIENT_ID")
CLOVA_CLIENT_SECRET = get_env("CLOVA_CLIENT_SECRET")
GOOGLE_TTS_API_KEY = get_env("GOOGLE_TTS_API_KEY") or get_env("GOOGLE_CLOUD_API_KEY") or get_env("GOOGLE_API_KEY")

# App Passwords
TESTER_PASSWORD = get_env("TESTER_PASSWORD", "crew2024")
ADMIN_PASSWORD = get_env("ADMIN_PASSWORD", "admin2026")

def check_openai_key() -> tuple[bool, str]:
    """OpenAI API 키 상태 확인"""
    if not OPENAI_API_KEY:
        return False, "OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가하세요."
    if not OPENAI_API_KEY.startswith("sk-"):
        return False, "OpenAI API 키 형식이 올바르지 않습니다. 'sk-'로 시작해야 합니다."
    return True, "OK"

def check_all_keys() -> dict:
    """모든 API 키 상태 확인"""
    return {
        "openai": bool(OPENAI_API_KEY),
        "did": bool(DID_API_KEY),
        "clova": bool(CLOVA_CLIENT_ID and CLOVA_CLIENT_SECRET),
        "google_tts": bool(GOOGLE_TTS_API_KEY),
    }
