# validation.py
# 입력 검증 및 보안 유틸리티

import re
import html
from typing import Optional, Tuple
from logging_config import get_logger

logger = get_logger(__name__)

# 최대 입력 길이 제한
MAX_TEXT_LENGTH = 10000  # 일반 텍스트
MAX_RESUME_LENGTH = 50000  # 자소서
MAX_QUESTION_LENGTH = 1000  # 질문


def sanitize_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    """텍스트 정제 및 길이 제한
    
    Args:
        text: 입력 텍스트
        max_length: 최대 길이
        
    Returns:
        정제된 텍스트
    """
    if not text:
        return ""
    
    # HTML 이스케이프
    cleaned = html.escape(text)
    
    # 연속 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # 길이 제한
    if len(cleaned) > max_length:
        logger.warning(f"텍스트 길이 초과: {len(cleaned)} > {max_length}")
        cleaned = cleaned[:max_length]
    
    return cleaned.strip()


def validate_text_input(
    text: str,
    min_length: int = 1,
    max_length: int = MAX_TEXT_LENGTH,
    field_name: str = "입력"
) -> Tuple[bool, str, str]:
    """텍스트 입력 유효성 검사
    
    Args:
        text: 검사할 텍스트
        min_length: 최소 길이
        max_length: 최대 길이
        field_name: 필드 이름 (에러 메시지용)
        
    Returns:
        (유효 여부, 정제된 텍스트, 에러 메시지)
    """
    if not text or not text.strip():
        return False, "", f"{field_name}을(를) 입력해주세요."
    
    cleaned = sanitize_text(text, max_length)
    
    if len(cleaned) < min_length:
        return False, cleaned, f"{field_name}이(가) 너무 짧습니다. (최소 {min_length}자)"
    
    if len(cleaned) > max_length:
        return False, cleaned, f"{field_name}이(가) 너무 깁니다. (최대 {max_length}자)"
    
    return True, cleaned, ""


def validate_resume(text: str) -> Tuple[bool, str, str]:
    """자소서 입력 검증"""
    return validate_text_input(
        text,
        min_length=50,
        max_length=MAX_RESUME_LENGTH,
        field_name="자소서"
    )


def validate_question(text: str) -> Tuple[bool, str, str]:
    """질문 입력 검증"""
    return validate_text_input(
        text,
        min_length=5,
        max_length=MAX_QUESTION_LENGTH,
        field_name="질문"
    )


def validate_answer(text: str) -> Tuple[bool, str, str]:
    """답변 입력 검증"""
    return validate_text_input(
        text,
        min_length=10,
        max_length=MAX_TEXT_LENGTH,
        field_name="답변"
    )


def is_safe_filename(filename: str) -> bool:
    """파일명 안전성 검사 (경로 탐색 공격 방지)"""
    if not filename:
        return False
    
    # 경로 구분자 포함 여부
    if '/' in filename or '\\' in filename:
        logger.warning(f"위험한 파일명 감지: {filename}")
        return False
    
    # 상위 디렉토리 참조
    if '..' in filename:
        logger.warning(f"경로 탐색 시도 감지: {filename}")
        return False
    
    # 허용된 문자만 포함
    if not re.match(r'^[\w\-. ]+$', filename):
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """파일명 정제"""
    if not filename:
        return "unnamed"
    
    # 경로 구분자 제거
    cleaned = filename.replace('/', '_').replace('\\', '_')
    
    # 상위 디렉토리 참조 제거
    cleaned = cleaned.replace('..', '_')
    
    # 특수문자 제거 (한글, 영문, 숫자, 일부 기호만 허용)
    cleaned = re.sub(r'[^\w\-. 가-힣]', '_', cleaned)
    
    return cleaned[:100] if cleaned else "unnamed"


def check_prompt_injection(text: str) -> Tuple[bool, str]:
    """프롬프트 인젝션 위험 검사
    
    Returns:
        (안전 여부, 경고 메시지)
    """
    if not text:
        return True, ""
    
    # 의심스러운 패턴
    suspicious_patterns = [
        r'ignore\s+(previous|above|all)\s+instructions',
        r'disregard\s+(previous|above|all)',
        r'forget\s+(everything|all|previous)',
        r'you\s+are\s+now\s+',
        r'act\s+as\s+if\s+you\s+are',
        r'pretend\s+to\s+be',
        r'system\s*:\s*',
        r'\[INST\]',
        r'\[/INST\]',
    ]
    
    text_lower = text.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, text_lower):
            logger.warning(f"프롬프트 인젝션 의심 패턴 감지: {pattern}")
            return False, "입력에 허용되지 않는 패턴이 포함되어 있습니다."
    
    return True, ""
