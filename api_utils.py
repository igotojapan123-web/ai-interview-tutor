# api_utils.py
# API 호출 및 응답 파싱을 위한 공통 유틸리티

import json
import time
import requests
from typing import Optional, Dict, Any, List
import streamlit as st

from env_config import OPENAI_API_KEY, check_openai_key, mask_api_key
from logging_config import get_logger, APIError

# 로거 설정
logger = get_logger(__name__)

# 타임아웃 설정
API_TIMEOUTS = {
    "openai_chat": 90,
    "openai_vision": 120,
    "openai_whisper": 60,
    "default": 60,
}

# 재시도 설정
MAX_RETRIES = 3
RETRY_DELAY = 2  # 초


def get_api_key() -> Optional[str]:
    """OpenAI API 키를 안전하게 가져옴"""
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API 키가 설정되지 않음")
        return None
    return OPENAI_API_KEY


def show_api_key_error():
    """API 키 오류 메시지 표시"""
    is_valid, message = check_openai_key()
    if not is_valid:
        logger.error(f"API 키 검증 실패: {message}")
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
                    error_detail = error_data['error'].get('message', '')
                    error_msg += f": {error_detail}"
                    logger.error(f"OpenAI API 에러: {response.status_code} - {error_detail}")
            except json.JSONDecodeError:
                logger.error(f"OpenAI API 에러: {response.status_code} - 응답 파싱 실패")
            st.error(error_msg)
            return None

        # JSON 파싱
        data = response.json()

        # choices 배열 확인
        choices = data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            logger.error("API 응답에 choices가 없음")
            st.error("API 응답에 choices가 없습니다. 잠시 후 다시 시도해주세요.")
            return None

        # 첫 번째 choice에서 message 추출
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            logger.error("API 응답 형식이 올바르지 않음: choice가 dict가 아님")
            st.error("API 응답 형식이 올바르지 않습니다.")
            return None

        message = first_choice.get("message")
        if not isinstance(message, dict):
            logger.error("API 응답에 message가 없음")
            st.error("API 응답에 message가 없습니다.")
            return None

        content = message.get("content", "")
        if not content:
            logger.warning("API가 빈 응답을 반환함")
            st.warning("API가 빈 응답을 반환했습니다.")
            return None

        # 토큰 사용량 로깅
        usage = data.get("usage", {})
        if usage:
            logger.info(f"토큰 사용: prompt={usage.get('prompt_tokens', 0)}, completion={usage.get('completion_tokens', 0)}, total={usage.get('total_tokens', 0)}")

        return {
            "content": content,
            "raw": data
        }

    except json.JSONDecodeError as e:
        logger.error(f"API 응답 JSON 파싱 실패: {e}")
        st.error(f"API 응답 JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        logger.exception(f"API 응답 처리 중 예외 발생: {e}")
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
        logger.warning("빈 content로 JSON 파싱 시도")
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
        logger.error(f"JSON 파싱 실패: {e}, content 길이: {len(content)}")
        st.error(f"JSON 파싱 실패: {e}")
        return None


def call_openai_chat(
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    timeout: int = None,
    json_mode: bool = False,
    max_retries: int = MAX_RETRIES
) -> Optional[Dict[str, Any]]:
    """
    OpenAI Chat API를 안전하게 호출 (재시도 로직 포함)

    Args:
        messages: 메시지 리스트 [{"role": "...", "content": "..."}]
        model: 사용할 모델
        timeout: 타임아웃 (초)
        json_mode: JSON 모드 사용 여부
        max_retries: 최대 재시도 횟수

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

    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"OpenAI API 호출 시도 {attempt + 1}/{max_retries}, 모델: {model}")

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout
            )

            result = safe_parse_openai_response(response)
            if result:
                logger.info(f"OpenAI API 호출 성공 (시도 {attempt + 1})")
                return result

            # 응답 파싱 실패 시 재시도 여부 결정
            if response.status_code in [429, 500, 502, 503, 504]:
                # Rate limit 또는 서버 오류는 재시도
                logger.warning(f"재시도 가능한 오류 (HTTP {response.status_code}), {RETRY_DELAY}초 후 재시도...")
                time.sleep(RETRY_DELAY * (attempt + 1))  # 지수 백오프
                continue
            else:
                # 다른 오류는 재시도 안 함
                return None

        except requests.Timeout as e:
            last_error = e
            logger.warning(f"API 요청 시간 초과 (시도 {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            st.error(f"API 요청 시간 초과 ({timeout}초). 잠시 후 다시 시도해주세요.")
            return None

        except requests.ConnectionError as e:
            last_error = e
            logger.error(f"연결 오류: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            st.error("인터넷 연결을 확인해주세요.")
            return None

        except Exception as e:
            last_error = e
            logger.exception(f"API 호출 중 예외 발생: {e}")
            st.error(f"API 호출 오류: {e}")
            return None

    logger.error(f"최대 재시도 횟수 초과, 마지막 오류: {last_error}")
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

    logger.info(f"Vision API 호출, 모델: {model}")
    return call_openai_chat(messages, model, timeout)


def validate_messages(messages: List[Dict[str, str]]) -> bool:
    """
    메시지 리스트 유효성 검사

    Args:
        messages: 검사할 메시지 리스트

    Returns:
        유효 여부
    """
    if not messages or not isinstance(messages, list):
        logger.error("메시지 리스트가 비어있거나 리스트가 아님")
        return False

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            logger.error(f"메시지 {i}가 dict가 아님")
            return False
        if "role" not in msg or "content" not in msg:
            logger.error(f"메시지 {i}에 role 또는 content가 없음")
            return False
        if msg["role"] not in ["system", "user", "assistant"]:
            logger.error(f"메시지 {i}의 role이 유효하지 않음: {msg['role']}")
            return False

    return True


def estimate_tokens(text: str) -> int:
    """
    텍스트의 대략적인 토큰 수 추정 (정확하지 않음)

    Args:
        text: 추정할 텍스트

    Returns:
        추정 토큰 수
    """
    # 한국어는 대략 1.5자당 1토큰, 영어는 4자당 1토큰
    # 단순화를 위해 3자당 1토큰으로 추정
    return len(text) // 3 + 1
