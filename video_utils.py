# video_utils.py
# D-ID API 연동 및 영상 생성 유틸리티

import os
import time
import requests
import base64
from typing import Optional, Dict, Any

from logging_config import get_logger

logger = get_logger(__name__)

# D-ID API 설정
DID_API_URL = "https://api.d-id.com"
DID_API_KEY = os.environ.get("DID_API_KEY", "")

# 면접관 이미지 URL (기본 이미지 - 전문적인 여성 면접관)
DEFAULT_INTERVIEWER_IMAGES = {
    "female_professional": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400",
    "male_professional": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400",
    "female_friendly": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400",
    "male_friendly": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400",
}

# 승객 캐릭터 이미지 (롤플레잉용)
PASSENGER_IMAGES = {
    "angry": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=400",
    "worried": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=400",
    "elderly": "https://images.unsplash.com/photo-1581579438747-1dc8d17bbce4?w=400",
    "business": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=400",
    "family": "https://images.unsplash.com/photo-1491013516836-7db643ee125a?w=400",
}


def get_did_api_key() -> str:
    """D-ID API 키 가져오기"""
    return os.environ.get("DID_API_KEY", "") or os.environ.get("D_ID_API_KEY", "")


def check_did_api_available() -> bool:
    """D-ID API 사용 가능 여부 확인"""
    api_key = get_did_api_key()
    if not api_key:
        return False

    try:
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json",
        }
        r = requests.get(f"{DID_API_URL}/credits", headers=headers, timeout=10)
        return r.status_code == 200
    except Exception as e:
        logger.warning(f"D-ID API availability check failed: {e}")
        return False


def create_talking_video(
    text: str,
    image_url: str = None,
    voice_id: str = "ko-KR-SunHiNeural",  # 한국어 여성 음성
    emotion: str = "neutral",
) -> Optional[Dict[str, Any]]:
    """
    D-ID API로 말하는 영상 생성

    Args:
        text: 말할 텍스트
        image_url: 얼굴 이미지 URL
        voice_id: Microsoft Azure TTS 음성 ID
        emotion: 표정 (neutral, happy, serious)

    Returns:
        {"video_url": str, "id": str} 또는 None
    """
    api_key = get_did_api_key()
    if not api_key:
        return None

    if not image_url:
        image_url = DEFAULT_INTERVIEWER_IMAGES["female_professional"]

    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
    }

    # 영상 생성 요청
    payload = {
        "source_url": image_url,
        "script": {
            "type": "text",
            "input": text,
            "provider": {
                "type": "microsoft",
                "voice_id": voice_id,
            },
        },
        "config": {
            "fluent": True,
            "pad_audio": 0.5,
        },
    }

    try:
        # 영상 생성 시작
        r = requests.post(
            f"{DID_API_URL}/talks",
            headers=headers,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        result = r.json()

        talk_id = result.get("id")
        if not talk_id:
            return None

        # 영상 생성 완료 대기 (최대 60초)
        for _ in range(30):
            time.sleep(2)
            status_r = requests.get(
                f"{DID_API_URL}/talks/{talk_id}",
                headers=headers,
                timeout=10
            )
            status_r.raise_for_status()
            status = status_r.json()

            if status.get("status") == "done":
                return {
                    "video_url": status.get("result_url"),
                    "id": talk_id,
                }
            elif status.get("status") == "error":
                return None

        return None

    except Exception as e:
        print(f"D-ID API Error: {e}")
        return None


def create_interviewer_video(
    question: str,
    interviewer_type: str = "female_professional",
    airline_type: str = "FSC",
) -> Optional[Dict[str, Any]]:
    """
    면접관 영상 생성

    Args:
        question: 면접 질문
        interviewer_type: 면접관 유형
        airline_type: 항공사 유형 (FSC/LCC)

    Returns:
        {"video_url": str, "id": str} 또는 None
    """
    image_url = DEFAULT_INTERVIEWER_IMAGES.get(
        interviewer_type,
        DEFAULT_INTERVIEWER_IMAGES["female_professional"]
    )

    # FSC는 차분한 톤, LCC는 밝은 톤
    if airline_type == "FSC":
        voice_id = "ko-KR-SunHiNeural"  # 차분한 여성
    else:
        voice_id = "ko-KR-InJoonNeural"  # 밝은 남성

    return create_talking_video(
        text=question,
        image_url=image_url,
        voice_id=voice_id,
    )


def create_passenger_video(
    dialogue: str,
    passenger_type: str = "business",
    emotion: str = "neutral",
) -> Optional[Dict[str, Any]]:
    """
    승객 캐릭터 영상 생성 (롤플레잉용)

    Args:
        dialogue: 승객 대사
        passenger_type: 승객 유형 (angry, worried, elderly, business, family)
        emotion: 표정

    Returns:
        {"video_url": str, "id": str} 또는 None
    """
    image_url = PASSENGER_IMAGES.get(
        passenger_type,
        PASSENGER_IMAGES["business"]
    )

    # 승객 유형별 음성
    voice_map = {
        "angry": "ko-KR-InJoonNeural",
        "worried": "ko-KR-SunHiNeural",
        "elderly": "ko-KR-BongJinNeural",
        "business": "ko-KR-InJoonNeural",
        "family": "ko-KR-SunHiNeural",
    }
    voice_id = voice_map.get(passenger_type, "ko-KR-SunHiNeural")

    return create_talking_video(
        text=dialogue,
        image_url=image_url,
        voice_id=voice_id,
        emotion=emotion,
    )


def get_video_html(video_url: str, width: int = 400, autoplay: bool = True) -> str:
    """
    영상 재생용 HTML 생성

    Args:
        video_url: 영상 URL
        width: 영상 너비
        autoplay: 자동 재생 여부

    Returns:
        HTML 문자열
    """
    autoplay_attr = "autoplay" if autoplay else ""
    return f"""
    <div style="display: flex; justify-content: center; margin: 20px 0;">
        <video width="{width}" {autoplay_attr} controls style="border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <source src="{video_url}" type="video/mp4">
            브라우저가 영상을 지원하지 않습니다.
        </video>
    </div>
    """


def get_fallback_avatar_html(
    text: str,
    avatar_type: str = "interviewer",
    is_speaking: bool = False,
) -> str:
    """
    D-ID API 사용 불가시 대체 아바타 HTML (CSS 애니메이션)

    Args:
        text: 표시할 텍스트
        avatar_type: 아바타 유형
        is_speaking: 말하는 중 여부

    Returns:
        HTML 문자열
    """
    # 아바타 이모지
    avatars = {
        "interviewer": "👩‍💼",
        "passenger_angry": "😠",
        "passenger_worried": "😟",
        "passenger_elderly": "👴",
        "passenger_business": "👨‍💼",
        "passenger_family": "👨‍👩‍👧",
    }
    avatar = avatars.get(avatar_type, "👤")

    # speaking 애니메이션용 CSS 클래스
    style_block = ""
    avatar_class = ""
    if is_speaking:
        style_block = """
        <style>
        @keyframes avatar-pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .avatar-speaking {
            animation: avatar-pulse 0.5s infinite;
        }
        </style>
        """
        avatar_class = "avatar-speaking"

    return f"""
    {style_block}
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 30px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    ">
        <div class="{avatar_class}" style="
            font-size: 80px;
            margin-bottom: 15px;
        ">{avatar}</div>
        <div style="
            background: white;
            padding: 15px 25px;
            border-radius: 15px;
            max-width: 80%;
            font-size: 16px;
            color: #333;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        ">
            <p style="margin: 0;">{text}</p>
        </div>
    </div>
    """


def get_enhanced_fallback_avatar_html(
    text: str,
    character_type: str = "interviewer",
    emotion_state: str = "neutral"
) -> str:
    """
    고급 폴백 아바타 HTML (CSS 애니메이션 강화)
    Phase 1 - 감정 표현이 가능한 향상된 아바타

    Args:
        text: 표시할 텍스트 (질문)
        character_type: 캐릭터 유형 (interviewer, passenger_*)
        emotion_state: 감정 상태 (neutral, friendly, serious, encouraging, thinking)

    Returns:
        HTML 문자열
    """
    # 감정별 이모지 매핑
    emotion_emojis = {
        "neutral": "👩‍💼",
        "friendly": "😊",
        "serious": "😐",
        "encouraging": "👍",
        "thinking": "🤔",
        "listening": "👂",
        "nodding": "🙂",
    }

    # 캐릭터 타입별 기본 이모지
    character_emojis = {
        "interviewer": "👩‍💼",
        "passenger_angry": "😠",
        "passenger_worried": "😟",
        "passenger_elderly": "👴",
        "passenger_business": "👨‍💼",
        "passenger_family": "👨‍👩‍👧",
    }

    # 감정 상태가 있으면 감정 이모지, 없으면 캐릭터 이모지
    if emotion_state in emotion_emojis:
        avatar = emotion_emojis[emotion_state]
    else:
        avatar = character_emojis.get(character_type, "👤")

    # 감정별 그라데이션 색상
    emotion_gradients = {
        "neutral": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "friendly": "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)",
        "serious": "linear-gradient(135deg, #434343 0%, #000000 100%)",
        "encouraging": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "thinking": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "listening": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
        "nodding": "linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)",
    }

    gradient = emotion_gradients.get(emotion_state, emotion_gradients["neutral"])

    return f'''
    <div class="enhanced-avatar-container" style="
        text-align: center;
        padding: 2rem;
        background: {gradient};
        border-radius: 20px;
        margin: 1rem 0;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    ">
        <style>
            @keyframes avatar-breathe {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
            }}
            @keyframes avatar-speak {{
                0%, 100% {{ transform: scale(1) rotate(0deg); }}
                25% {{ transform: scale(1.02) rotate(-1deg); }}
                50% {{ transform: scale(1.05) rotate(0deg); }}
                75% {{ transform: scale(1.02) rotate(1deg); }}
            }}
            @keyframes bubble-fade-in {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes glow {{
                0%, 100% {{ box-shadow: 0 4px 20px rgba(255,255,255,0.2); }}
                50% {{ box-shadow: 0 4px 30px rgba(255,255,255,0.4); }}
            }}
            .avatar-wrapper {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 120px;
                height: 120px;
                background: white;
                border-radius: 50%;
                font-size: 60px;
                margin-bottom: 1rem;
                animation: avatar-speak 2s ease-in-out infinite;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            }}
            .speech-bubble {{
                background: white;
                padding: 1.5rem 2rem;
                border-radius: 15px;
                margin-top: 1rem;
                position: relative;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                animation: bubble-fade-in 0.5s ease-out, glow 3s ease-in-out infinite;
                max-width: 90%;
                margin-left: auto;
                margin-right: auto;
            }}
            .speech-bubble::before {{
                content: '';
                position: absolute;
                top: -10px;
                left: 50%;
                transform: translateX(-50%);
                border-left: 10px solid transparent;
                border-right: 10px solid transparent;
                border-bottom: 10px solid white;
            }}
            .question-text {{
                color: #333;
                font-size: 1.1rem;
                line-height: 1.6;
                margin: 0;
                word-break: keep-all;
            }}
            .interviewer-label {{
                color: white;
                font-size: 0.85rem;
                margin-bottom: 0.5rem;
                opacity: 0.9;
            }}
        </style>
        <div class="interviewer-label">면접관</div>
        <div class="avatar-wrapper">{avatar}</div>
        <div class="speech-bubble">
            <p class="question-text">{text}</p>
        </div>
    </div>
    '''
