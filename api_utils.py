# api_utils.py
# API 호출 및 응답 파싱을 위한 공통 유틸리티

import json
import requests
from typing import Optional, Dict, Any, List
import streamlit as st

from env_config import OPENAI_API_KEY, check_openai_key

# 타임아웃 설정
API_TIMEOUTS = {
    "openai_chat": 90,
    "openai_vision": 120,
    "openai_whisper": 60,
    "default": 60,
}


def get_api_key() -> Optional[str]:
    """OpenAI API 키를 안전하게 가져옴"""
    if not OPENAI_API_KEY:
        return None
    return OPENAI_API_KEY


def show_api_key_error():
    """API 키 오류 메시지 표시"""
    is_valid, message = check_openai_key()
    if not is_valid:
        st.error(f"API 키 오류: {message}")
        st.info("`.env` 파일에 `OPENAI_API_KEY=sk-...` 형식으로 API 키를 추가하세요.")
        return False
    return True


def safe_parse_openai_response(response: requests.Response) -> Optional[Dict[str, Any]]:
    """
    OpenAI API 응답을 안전하게 파싱

    Returns:
        성공 시: {"content": str, "raw": dict}
        실패 시: None (에러 메시지 표시됨)
    """
    try:
        # HTTP 상태 코드 확인
        if response.status_code != 200:
            error_msg = f"API 오류 (HTTP {response.status_code})"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg += f": {error_data['error'].get('message', '')}"
            except:
                pass
            st.error(error_msg)
            return None

        # JSON 파싱
        data = response.json()

        # choices 배열 확인
        choices = data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            st.error("API 응답에 choices가 없습니다. 잠시 후 다시 시도해주세요.")
            return None

        # 첫 번째 choice에서 message 추출
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            st.error("API 응답 형식이 올바르지 않습니다.")
            return None

        message = first_choice.get("message")
        if not isinstance(message, dict):
            st.error("API 응답에 message가 없습니다.")
            return None

        content = message.get("content", "")
        if not content:
            st.warning("API가 빈 응답을 반환했습니다.")
            return None

        return {
            "content": content,
            "raw": data
        }

    except json.JSONDecodeError as e:
        st.error(f"API 응답 JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        st.error(f"API 응답 처리 중 오류: {e}")
        return None


def safe_parse_json_content(content: str) -> Optional[Dict[str, Any]]:
    """
    API 응답 content에서 JSON을 안전하게 파싱

    Args:
        content: API 응답의 content 문자열

    Returns:
        성공 시: 파싱된 dict
        실패 시: None
    """
    if not content:
        return None

    try:
        # 마크다운 코드 블록 제거
        clean_content = content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        if clean_content.startswith("```"):
            clean_content = clean_content[3:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]

        return json.loads(clean_content.strip())

    except json.JSONDecodeError as e:
        st.error(f"JSON 파싱 실패: {e}")
        return None


def call_openai_chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    timeout: int = None,
    json_mode: bool = False
) -> Optional[Dict[str, Any]]:
    """
    OpenAI Chat API를 안전하게 호출

    Args:
        messages: 메시지 리스트 [{"role": "...", "content": "..."}]
        model: 사용할 모델
        timeout: 타임아웃 (초)
        json_mode: JSON 모드 사용 여부

    Returns:
        성공 시: {"content": str, "raw": dict}
        실패 시: None
    """
    api_key = get_api_key()
    if not api_key:
        show_api_key_error()
        return None

    if timeout is None:
        timeout = API_TIMEOUTS["openai_chat"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
    }

    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        return safe_parse_openai_response(response)

    except requests.Timeout:
        st.error(f"API 요청 시간 초과 ({timeout}초). 잠시 후 다시 시도해주세요.")
        return None
    except requests.ConnectionError:
        st.error("인터넷 연결을 확인해주세요.")
        return None
    except Exception as e:
        st.error(f"API 호출 오류: {e}")
        return None


def call_openai_vision(
    messages: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    timeout: int = None
) -> Optional[Dict[str, Any]]:
    """
    OpenAI Vision API를 안전하게 호출 (이미지 분석용)
    """
    if timeout is None:
        timeout = API_TIMEOUTS["openai_vision"]

    return call_openai_chat(messages, model, timeout)
