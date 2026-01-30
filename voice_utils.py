# voice_utils.py
# 음성 인식 (STT) 및 음성 평가 유틸리티
# 네이버 클로바 더빙 + OpenAI TTS 지원

from logging_config import get_logger

import os
import re
import json
import tempfile
import requests
from typing import Optional, Dict, Any, List, Tuple
from io import BytesIO

logger = get_logger(__name__)

# OpenAI API 설정
OPENAI_API_URL = "https://api.openai.com/v1"

# 네이버 클로바 보이스 API 설정
CLOVA_VOICE_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

# =====================
# 네이버 클로바 보이스 스피커 목록
# =====================
# 한국어 Premium 음성 (감정 지원)
CLOVA_SPEAKERS = {
    # 여성 음성
    "nara": {"name": "나라", "gender": "female", "age": "young", "emotion": True, "desc": "20대 여성, 차분함"},
    "nara_call": {"name": "나라(상담원)", "gender": "female", "age": "young", "emotion": False, "desc": "상담원 톤"},
    "nminsang": {"name": "민상", "gender": "female", "age": "young", "emotion": True, "desc": "20대 여성, 밝음"},
    "nyejin": {"name": "예진", "gender": "female", "age": "young", "emotion": True, "desc": "20대 여성, 활발함"},
    "mijin": {"name": "미진", "gender": "female", "age": "adult", "emotion": False, "desc": "성인 여성"},
    "jinho": {"name": "진호(여)", "gender": "female", "age": "adult", "emotion": False, "desc": "성인 여성"},
    "nsunhee": {"name": "선희", "gender": "female", "age": "middle", "emotion": True, "desc": "40-50대 여성"},
    "nsunkyung": {"name": "선경", "gender": "female", "age": "middle", "emotion": True, "desc": "40-50대 여성, 따뜻함"},
    "nyoungmi": {"name": "영미", "gender": "female", "age": "senior", "emotion": True, "desc": "60대 이상 여성"},

    # 남성 음성
    "njonghyun": {"name": "종현", "gender": "male", "age": "young", "emotion": True, "desc": "20대 남성"},
    "njoonyoung": {"name": "준영", "gender": "male", "age": "young", "emotion": True, "desc": "20대 남성, 밝음"},
    "nwontak": {"name": "원탁", "gender": "male", "age": "adult", "emotion": True, "desc": "30대 남성"},
    "nsangdo": {"name": "상도", "gender": "male", "age": "middle", "emotion": True, "desc": "40-50대 남성"},
    "nseungpyo": {"name": "승표", "gender": "male", "age": "middle", "emotion": True, "desc": "40-50대 남성, 권위"},
    "nkyungtae": {"name": "경태", "gender": "male", "age": "senior", "emotion": True, "desc": "60대 이상 남성"},

    # 아이/캐릭터 음성
    "ndain": {"name": "다인", "gender": "female", "age": "child", "emotion": True, "desc": "어린이 여아"},
    "nmeow": {"name": "야옹이", "gender": "female", "age": "child", "emotion": False, "desc": "귀여운 캐릭터"},
}

# 감정 코드
CLOVA_EMOTIONS = {
    "neutral": 0,   # 기본
    "happy": 1,     # 기쁨
    "sad": 2,       # 슬픔
    "angry": 3,     # 화남
}


def get_clova_api_keys() -> Tuple[str, str]:
    """네이버 클로바 API 키 가져오기"""
    client_id = os.environ.get("CLOVA_CLIENT_ID", "") or os.environ.get("NCP_CLIENT_ID", "")
    client_secret = os.environ.get("CLOVA_CLIENT_SECRET", "") or os.environ.get("NCP_CLIENT_SECRET", "")
    return client_id, client_secret


def is_clova_available() -> bool:
    """클로바 API 사용 가능 여부"""
    client_id, client_secret = get_clova_api_keys()
    return bool(client_id and client_secret)


def get_clova_speaker_for_persona(persona: str, escalation_level: int = 0) -> Tuple[str, str, int]:
    """
    페르소나에 맞는 클로바 스피커 선택

    Args:
        persona: 승객 페르소나 문자열
        escalation_level: 감정 레벨 (0: 평상시, 1: 짜증, 2: 화남)

    Returns:
        (speaker_id, speed, emotion_code) 튜플
    """
    # 감정 매핑
    emotion_map = {0: "neutral", 1: "neutral", 2: "angry"}
    emotion = emotion_map.get(escalation_level, "neutral")
    emotion_code = CLOVA_EMOTIONS.get(emotion, 0)

    # 속도 설정 (화날수록 빠르게)
    speed_map = {0: 0, 1: 1, 2: 2}  # -5 ~ 5 범위, 0이 기본
    speed = speed_map.get(escalation_level, 0)

    # 성별 판단
    is_female = any(kw in persona for kw in ['여성', '엄마', '할머니', '여자', '부인', '임산부', '아줌마'])
    is_male = any(kw in persona for kw in ['남성', '아빠', '할아버지', '남자', '사업가']) and not is_female

    # 나이대 판단
    if any(kw in persona for kw in ['60대', '70대', '어르신', '할머니', '할아버지', '노인']):
        age = "senior"
    elif any(kw in persona for kw in ['50대', '40대']):
        age = "middle"
    elif any(kw in persona for kw in ['30대', '직장인']):
        age = "adult"
    elif any(kw in persona for kw in ['20대', '대학생', '젊은']):
        age = "young"
    elif any(kw in persona for kw in ['어린이', '아동', '아이']):
        age = "child"
    else:
        age = "adult"

    # 스피커 선택
    if age == "child":
        speaker = "ndain"
    elif is_female:
        if age == "senior":
            speaker = "nyoungmi"  # 60대 이상 여성
        elif age == "middle":
            speaker = "nsunhee"  # 40-50대 여성
        elif age == "young":
            speaker = "nyejin"  # 20대 여성
        else:
            speaker = "nara"  # 기본 여성
    else:  # 남성 또는 기본
        if age == "senior":
            speaker = "nkyungtae"  # 60대 이상 남성
        elif age == "middle":
            speaker = "nsangdo"  # 40-50대 남성
        elif age == "young":
            speaker = "njonghyun"  # 20대 남성
        else:
            speaker = "nwontak"  # 30대 남성

    return (speaker, speed, emotion_code)


def generate_clova_tts(
    text: str,
    speaker: str = "nara",
    speed: int = 0,
    emotion: int = 0,
    volume: int = 0,
    pitch: int = 0,
) -> Optional[bytes]:
    """
    네이버 클로바 보이스 API로 TTS 생성

    Args:
        text: 변환할 텍스트 (최대 2000자)
        speaker: 스피커 ID
        speed: 속도 (-5 ~ 5, 기본 0)
        emotion: 감정 (0: 기본, 1: 슬픔, 2: 기쁨, 3: 화남)
        volume: 볼륨 (-5 ~ 5, 기본 0)
        pitch: 피치 (-5 ~ 5, 기본 0)

    Returns:
        MP3 오디오 바이트 또는 None
    """
    client_id, client_secret = get_clova_api_keys()
    if not client_id or not client_secret:
        return None

    # 텍스트 길이 제한 (2000자)
    if len(text) > 2000:
        text = text[:2000]

    headers = {
        "X-NCP-APIGW-API-KEY-ID": client_id,
        "X-NCP-APIGW-API-KEY": client_secret,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # 감정 지원 여부 확인
    speaker_info = CLOVA_SPEAKERS.get(speaker, {})
    supports_emotion = speaker_info.get("emotion", False)

    data = {
        "speaker": speaker,
        "text": text,
        "volume": str(volume),
        "speed": str(speed),
        "pitch": str(pitch),
        "format": "mp3",
    }

    # 감정 지원 스피커만 감정 파라미터 추가
    if supports_emotion and emotion > 0:
        data["emotion"] = str(emotion)
        data["emotion-strength"] = "2"  # 감정 강도 (1: 약함, 2: 보통, 3: 강함)

    try:
        r = requests.post(
            CLOVA_VOICE_URL,
            headers=headers,
            data=data,
            timeout=30
        )

        if r.status_code == 200:
            return r.content
        else:
            print(f"CLOVA TTS Error: {r.status_code} - {r.text}")
            return None

    except Exception as e:
        print(f"CLOVA TTS API Error: {e}")
        return None


# =====================
# 나이/성별별 TTS 음성 매핑 (OpenAI 백업용)
# =====================
# OpenAI TTS 음성:
# - alloy: 중성적, 젊은 느낌
# - echo: 남성, 중저음
# - fable: 표현력 좋음, 이야기체
# - onyx: 남성, 깊고 권위있는 느낌
# - nova: 여성, 따뜻하고 친근함
# - shimmer: 여성, 부드럽고 차분함

def get_voice_for_persona(persona: str, escalation_level: int = 0) -> Tuple[str, float]:
    """
    승객 페르소나에서 나이/성별을 파악하여 적합한 TTS 음성과 속도 반환
    감정 레벨에 따라 속도 조절 (화날수록 빨라짐)

    Args:
        persona: 승객 페르소나 문자열 (예: "50대 여성, 해외여행이 처음...")
        escalation_level: 감정 레벨 (0: 평상시, 1: 짜증, 2: 화남)

    Returns:
        (voice_id, speed) 튜플
    """
    # 감정에 따른 속도 배율
    emotion_speed_multiplier = {
        0: 1.0,    # 평상시: 보통 속도
        1: 1.08,   # 짜증: 약간 빠르게
        2: 1.15,   # 화남: 더 빠르게
    }
    speed_mult = emotion_speed_multiplier.get(escalation_level, 1.0)

    # 성별 판단
    is_female = any(keyword in persona for keyword in ['여성', '엄마', '아이 엄마', '할머니', '여자', '부인', '임산부', '아줌마'])
    is_male = any(keyword in persona for keyword in ['남성', '아빠', '할아버지', '남자', '사업가']) and not is_female

    # 나이대 판단
    age_group = "middle"  # 기본값: 중년

    if any(keyword in persona for keyword in ['20대', '이십대', '대학생', '젊은']):
        age_group = "young"
    elif any(keyword in persona for keyword in ['30대', '삼십대', '직장인']):
        age_group = "young_adult"
    elif any(keyword in persona for keyword in ['40대', '사십대']):
        age_group = "middle"
    elif any(keyword in persona for keyword in ['50대', '오십대']):
        age_group = "middle_aged"
    elif any(keyword in persona for keyword in ['60대', '육십대', '70대', '칠십대', '어르신', '할머니', '할아버지', '노인']):
        age_group = "elderly"

    # 특수 페르소나 체크
    if '어린이' in persona or '아동' in persona:
        return ("alloy", 1.1 * speed_mult)

    if '외국인' in persona:
        return ("fable", 1.0 * speed_mult)

    # 성별 + 나이 조합으로 음성 선택
    if is_female:
        if age_group in ["young", "young_adult"]:
            base_speed = 1.05
            voice = "nova"
        elif age_group == "middle":
            # 40대 아줌마: nova, 기본 빠름
            base_speed = 1.1 if escalation_level > 0 else 1.0
            voice = "nova"
        elif age_group == "middle_aged":
            # 50대 여성: shimmer
            base_speed = 1.0
            voice = "shimmer"
        else:  # elderly
            # 60-70대 여성: shimmer, 느리게
            base_speed = 0.92
            voice = "shimmer"
    else:
        # 남성 또는 성별 불명확
        if age_group in ["young", "young_adult"]:
            base_speed = 1.05
            voice = "echo"
        elif age_group == "middle":
            # 40대 남성/사업가: echo
            base_speed = 1.0
            voice = "echo"
        elif age_group == "middle_aged":
            # 50대 남성: onyx
            base_speed = 0.98
            voice = "onyx"
        else:  # elderly
            # 60-70대 남성: onyx, 느리게
            base_speed = 0.9
            voice = "onyx"

    final_speed = min(base_speed * speed_mult, 1.25)  # 최대 1.25배속
    return (voice, final_speed)


def get_openai_api_key() -> str:
    """OpenAI API 키 가져오기"""
    return (
        os.environ.get("OPENAI_API_KEY", "")
        or os.environ.get("OPENAI_APIKEY", "")
        or os.environ.get("OPENAI_KEY", "")
    )


def transcribe_audio(audio_bytes: bytes, language: str = "ko") -> Optional[Dict[str, Any]]:
    """
    OpenAI Whisper API로 음성을 텍스트로 변환

    Args:
        audio_bytes: 오디오 바이트 데이터
        language: 언어 코드 (ko, en)

    Returns:
        {
            "text": "인식된 텍스트",
            "duration": 10.5,  # 초 단위
            "words": [{"word": "안녕", "start": 0.0, "end": 0.5}, ...]
        }
    """
    api_key = get_openai_api_key()
    if not api_key:
        print("[Whisper] API 키 없음")
        return None

    # 최소 오디오 크기 체크 (1KB 미만은 유효하지 않음)
    if not audio_bytes or len(audio_bytes) < 1000:
        print(f"[Whisper] 오디오 데이터 부족: {len(audio_bytes) if audio_bytes else 0} bytes")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        with open(temp_path, "rb") as audio_file:
            files = {
                "file": ("audio.webm", audio_file, "audio/webm"),
            }
            data = {
                "model": "whisper-1",
                "language": language,
                "response_format": "verbose_json",
                "timestamp_granularities": ["word"],
            }

            r = requests.post(
                f"{OPENAI_API_URL}/audio/transcriptions",
                headers=headers,
                files=files,
                data=data,
                timeout=90  # 타임아웃 90초로 증가
            )
            r.raise_for_status()
            result = r.json()

            text = result.get("text", "").strip()
            duration = result.get("duration", 0)

            # 인식된 텍스트가 너무 짧으면 실패로 간주하지 않음 (빈 문자열만 제외)
            if not text:
                print("[Whisper] 인식된 텍스트 없음 (무음 또는 너무 짧은 녹음)")
                return None

            return {
                "text": text,
                "duration": duration,
                "words": result.get("words", []),
                "language": result.get("language", language),
            }

    except requests.exceptions.Timeout:
        print("[Whisper] API 타임아웃 (90초 초과)")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"[Whisper] HTTP 오류: {e.response.status_code if e.response else 'unknown'}")
        return None
    except Exception as e:
        print(f"[Whisper] API 오류: {e}")
        return None

    finally:
        # 임시 파일 삭제
        try:
            os.unlink(temp_path)
        except Exception as e:
            logger.debug(f"임시 파일 삭제 실패: {e}")


def analyze_voice_quality(
    transcription: Dict[str, Any],
    expected_duration_range: Tuple[int, int] = (60, 90),
) -> Dict[str, Any]:
    """
    음성 품질 분석

    Args:
        transcription: transcribe_audio 결과
        expected_duration_range: 적정 답변 시간 범위 (초)

    Returns:
        {
            "speech_rate": {"wpm": 150, "score": 8, "feedback": "적절한 속도"},
            "filler_words": {"count": 3, "list": ["음", "어"], "score": 7, "feedback": "..."},
            "pauses": {"count": 2, "long_pauses": 1, "score": 8, "feedback": "..."},
            "duration": {"seconds": 75, "score": 10, "feedback": "적절한 시간"},
            "clarity": {"score": 8, "feedback": "..."},
            "total_score": 82,
            "total_feedback": "..."
        }
    """
    text = transcription.get("text", "")
    duration = transcription.get("duration", 0)
    words = transcription.get("words", [])

    result = {
        "speech_rate": {},
        "filler_words": {},
        "pauses": {},
        "duration": {},
        "clarity": {},
        "total_score": 0,
        "total_feedback": "",
    }

    # 1. 말 속도 분석 (WPM - Words Per Minute)
    word_count = len(text.split())
    if duration > 0:
        wpm = int((word_count / duration) * 60)
    else:
        wpm = 0

    if 120 <= wpm <= 160:
        rate_score = 10
        rate_feedback = "적절한 말 속도입니다."
    elif 100 <= wpm < 120 or 160 < wpm <= 180:
        rate_score = 7
        rate_feedback = "약간 느리거나 빠릅니다." if wpm < 120 else "약간 빠릅니다."
    elif wpm < 100:
        rate_score = 4
        rate_feedback = "너무 느립니다. 자신감 있게 말해보세요."
    else:
        rate_score = 4
        rate_feedback = "너무 빠릅니다. 천천히 또박또박 말해보세요."

    result["speech_rate"] = {
        "wpm": wpm,
        "score": rate_score,
        "feedback": rate_feedback,
    }

    # 2. 필러 단어 분석
    filler_patterns = [
        r'\b음+\b', r'\b어+\b', r'\b그+\b', r'\b아+\b',
        r'\b그러니까\b', r'\b그래서\b', r'\b뭐랄까\b',
        r'\b약간\b', r'\b좀\b', r'\b진짜\b', r'\b막\b',
        r'\b이제\b', r'\b근데\b', r'\b그냥\b',
    ]

    filler_count = 0
    filler_list = []
    for pattern in filler_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            filler_count += len(matches)
            filler_list.extend(matches)

    # 1분당 필러 단어 수로 정규화
    if duration > 0:
        filler_per_min = (filler_count / duration) * 60
    else:
        filler_per_min = 0

    if filler_per_min <= 3:
        filler_score = 10
        filler_feedback = "불필요한 추임새가 거의 없습니다."
    elif filler_per_min <= 6:
        filler_score = 7
        filler_feedback = "추임새를 조금 줄이면 좋겠습니다."
    elif filler_per_min <= 10:
        filler_score = 4
        filler_feedback = "추임새가 많습니다. 의식적으로 줄여보세요."
    else:
        filler_score = 2
        filler_feedback = "추임새가 너무 많습니다. 침묵을 두려워하지 마세요."

    result["filler_words"] = {
        "count": filler_count,
        "list": list(set(filler_list))[:5],  # 상위 5개만
        "score": filler_score,
        "feedback": filler_feedback,
    }

    # 3. 묵음/휴지 분석
    if words:
        pauses = []
        long_pauses = 0
        for i in range(1, len(words)):
            prev_end = words[i-1].get("end", 0)
            curr_start = words[i].get("start", 0)
            gap = curr_start - prev_end
            if gap > 0.5:
                pauses.append(gap)
                if gap > 2.0:
                    long_pauses += 1

        pause_count = len(pauses)

        if pause_count <= 3 and long_pauses == 0:
            pause_score = 10
            pause_feedback = "자연스러운 흐름입니다."
        elif pause_count <= 5 and long_pauses <= 1:
            pause_score = 7
            pause_feedback = "전반적으로 괜찮지만 긴 침묵이 있었습니다."
        else:
            pause_score = 4
            pause_feedback = "답변이 자주 끊깁니다. 미리 정리해서 말해보세요."

        result["pauses"] = {
            "count": pause_count,
            "long_pauses": long_pauses,
            "score": pause_score,
            "feedback": pause_feedback,
        }
    else:
        result["pauses"] = {
            "count": 0,
            "long_pauses": 0,
            "score": 5,
            "feedback": "휴지 분석 데이터 없음",
        }

    # 4. 답변 시간 분석
    min_duration, max_duration = expected_duration_range
    if min_duration <= duration <= max_duration:
        duration_score = 10
        duration_feedback = f"적절한 답변 시간입니다. ({int(duration)}초)"
    elif duration < min_duration * 0.5:
        duration_score = 3
        duration_feedback = f"답변이 너무 짧습니다. ({int(duration)}초) 구체적인 예시를 추가하세요."
    elif duration < min_duration:
        duration_score = 6
        duration_feedback = f"조금 더 자세히 답변해도 좋습니다. ({int(duration)}초)"
    elif duration <= max_duration * 1.3:
        duration_score = 6
        duration_feedback = f"약간 깁니다. ({int(duration)}초) 핵심만 전달하세요."
    else:
        duration_score = 3
        duration_feedback = f"답변이 너무 깁니다. ({int(duration)}초) 간결하게 정리하세요."

    result["duration"] = {
        "seconds": int(duration),
        "score": duration_score,
        "feedback": duration_feedback,
    }

    # 5. 발음 명확성 (간접 측정 - 인식된 단어 수 기반)
    if words:
        recognized_ratio = len(words) / max(word_count, 1)
        if recognized_ratio >= 0.9:
            clarity_score = 10
            clarity_feedback = "발음이 명확합니다."
        elif recognized_ratio >= 0.7:
            clarity_score = 7
            clarity_feedback = "발음이 대체로 명확합니다."
        else:
            clarity_score = 4
            clarity_feedback = "발음을 더 또렷하게 해주세요."
    else:
        clarity_score = 7
        clarity_feedback = "발음 분석 데이터 없음"

    result["clarity"] = {
        "score": clarity_score,
        "feedback": clarity_feedback,
    }

    # 총점 계산 (가중 평균)
    weights = {
        "speech_rate": 0.2,
        "filler_words": 0.25,
        "pauses": 0.15,
        "duration": 0.2,
        "clarity": 0.2,
    }

    total_score = (
        result["speech_rate"]["score"] * weights["speech_rate"] +
        result["filler_words"]["score"] * weights["filler_words"] +
        result["pauses"]["score"] * weights["pauses"] +
        result["duration"]["score"] * weights["duration"] +
        result["clarity"]["score"] * weights["clarity"]
    ) * 10  # 100점 만점으로 환산

    result["total_score"] = int(total_score)

    # 총평
    if total_score >= 80:
        result["total_feedback"] = "음성 전달력이 우수합니다. 자신감 있게 면접에 임하세요!"
    elif total_score >= 60:
        result["total_feedback"] = "기본적인 전달력은 갖추었습니다. 아래 피드백을 참고해 개선해보세요."
    else:
        result["total_feedback"] = "음성 전달력 개선이 필요합니다. 꾸준한 연습이 필요합니다."

    return result


# =====================
# 음성 분석 점수 기준 (항공사 면접 특화)
# =====================

VOICE_SCORING = {
    "speech_rate": {
        "perfect": (120, 150),      # WPM - 완벽 범위
        "acceptable": (100, 170),   # WPM - 허용 범위
        "deduct_per_violation": 5   # 범위 벗어나면 -5점
    },
    "filler_words": {
        "perfect": 0,               # 필러 0개
        "acceptable": 3,            # 3개 이하
        "deduct_per_extra": 2       # 초과 1개당 -2점
    },
    "silence_gaps": {
        "max_allowed": 3,           # 2초 이상 침묵 최대 3회
        "deduct_per_extra": 3       # 초과 1회당 -3점
    },
    "response_time": {
        "perfect": (3, 10),         # 3~10초 (롤플레잉: 읽기+생각+응답)
        "acceptable": (2, 20),      # 2~20초 허용
        "deduct_if_outside": 5      # 범위 벗어나면 -5점
    },
    "pitch_variation": {
        "monotone_threshold": 20,   # Hz 변화량 20 이하면 단조로움
        "deduct_if_monotone": 5
    },
    "volume_stability": {
        "max_drop_percent": 30,     # 끝부분 음량 30% 이상 감소 시
        "deduct_if_drops": 5
    },
    "service_tone": {
        "greeting_pitch_rise": 10,  # 첫 인사 피치 상승 최소 %
        "ending_softness": True,    # 문장 끝 부드러움
    },
    "composure": {
        "speed_change_threshold": 30,  # 말 속도 30% 이상 급변 시
        "filler_spike_threshold": 3,   # 구간별 필러 3개 이상 급증 시
    }
}


# =====================
# 고급 음성 분석 (목소리 떨림, 말끝 흐림, 톤 변화 등)
# =====================

def analyze_voice_with_gpt(transcription: Dict[str, Any]) -> Dict[str, Any]:
    """
    GPT 기반 음성 품질 분석 (librosa 없을 때 폴백)
    텍스트와 타이밍 정보만으로 음성 품질을 추정

    Args:
        transcription: transcribe_audio 결과

    Returns:
        고급 음성 분석 결과 딕셔너리
    """
    api_key = get_openai_api_key()
    if not api_key:
        return None

    text = transcription.get("text", "")
    duration = transcription.get("duration", 0)
    words = transcription.get("words", [])

    if not text or duration < 3:
        return None

    # 텍스트에서 추정 가능한 정보 수집
    word_count = len(text.split())
    wpm = int((word_count / max(duration, 1)) * 60) if duration > 0 else 0

    # 단어 타이밍으로 속도 변화 분석
    speed_changes = ""
    if words and len(words) > 5:
        # 전반/중반/후반 속도 비교
        segment_size = len(words) // 3
        segments = [words[:segment_size], words[segment_size:2*segment_size], words[2*segment_size:]]
        for i, seg in enumerate(segments):
            if len(seg) >= 2:
                seg_duration = (seg[-1].get("end", 0) - seg[0].get("start", 0))
                if seg_duration > 0:
                    seg_wpm = int((len(seg) / seg_duration) * 60)
                    speed_changes += f"구간{i+1}: {seg_wpm}WPM, "

    # 필러 단어 목록
    filler_patterns = ['음', '어', '그', '아', '그러니까', '뭐랄까', '약간', '좀', '진짜', '막', '이제', '근데', '그냥']
    found_fillers = [f for f in filler_patterns if f in text]

    system_prompt = """당신은 항공사 면접 음성 분석 전문가입니다. 객관적이고 공정하게 평가하세요.
주어진 텍스트와 말하기 데이터를 기반으로 음성 품질을 평가하세요.

JSON으로만 응답하세요:
{
    "tremor": {"score": 1-10, "level": "없음/약함/보통/심함", "feedback": "피드백"},
    "ending_clarity": {"score": 1-10, "issue": "없음/약간흐림/흐림", "feedback": "피드백"},
    "pitch_variation": {"score": 1-10, "type": "생동감있음/보통/단조로움", "feedback": "피드백"},
    "service_tone": {"score": 1-10, "feedback": "서비스 톤 피드백"},
    "composure": {"score": 1-10, "feedback": "침착함 피드백"}
}

공정한 점수 기준:
- 9-10점: 매우 우수 (프로 수준, 거의 완벽)
- 7-8점: 우수 (자연스럽고 잘함)
- 5-6점: 보통 (무난하지만 개선 여지 있음)
- 3-4점: 미흡 (명확한 문제가 있음)
- 1-2점: 매우 부족 (의미 없는 답변, 심각한 문제)

항목별 기준:
- tremor: 속도 일정하고 필러 적으면 8-9점. 필러 다수+속도 불안정하면 3-5점.
- ending_clarity: 문장이 명확히 끝나면 8-9점. 말끝이 흐리거나 미완성이면 4-5점.
- pitch_variation: 강조/억양 변화가 자연스러우면 8-9점. 완전히 단조로우면 4-5점.
- service_tone: 밝고 친근한 표현이 있으면 8-9점. 무미건조하면 5점. 불친절하면 3점.
- composure: 차분하고 안정적이면 8-9점. 불안정하고 버벅거리면 4-5점.

중요: 잘한 것은 확실히 높은 점수를 주세요. 터무니없는 답변(의미없는 입력, 너무 짧은 답변 등)만 낮은 점수를 주세요."""

    user_prompt = f"""분석 데이터:
- 전체 텍스트: {text[:500]}
- 총 소요시간: {duration:.1f}초
- 말 속도: {wpm} WPM
- 단어 수: {word_count}
- 구간별 속도: {speed_changes}
- 발견된 필러 단어: {', '.join(found_fillers)}
- 필러 빈도: 약 {len(found_fillers)}종류 사용

이 데이터를 기반으로 음성 품질을 평가해주세요."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    try:
        r = requests.post(
            f"{OPENAI_API_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )
        r.raise_for_status()
        result = r.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = json.loads(content)

        # 결과 정규화 (기본값을 5점으로 - 보통 수준)
        analysis = {
            "tremor": parsed.get("tremor", {"score": 5, "level": "보통", "feedback": "분석 데이터 부족"}),
            "ending_clarity": parsed.get("ending_clarity", {"score": 5, "issue": "보통", "feedback": "분석 데이터 부족"}),
            "pitch_variation": parsed.get("pitch_variation", {"score": 5, "type": "보통", "feedback": "분석 데이터 부족"}),
            "energy_consistency": {"score": 5, "feedback": "GPT 기반 분석"},
            "service_tone": parsed.get("service_tone", {"score": 5, "feedback": "분석 데이터 부족"}),
            "composure": parsed.get("composure", {"score": 5, "feedback": "분석 데이터 부족"}),
        }

        # 각 점수가 10을 초과하지 않도록 클램핑
        for key in ["tremor", "ending_clarity", "pitch_variation", "service_tone", "composure"]:
            if analysis[key].get("score", 5) > 10:
                analysis[key]["score"] = 10
            elif analysis[key].get("score", 5) < 1:
                analysis[key]["score"] = 1

        # confidence_score 계산
        scores = [
            analysis["tremor"].get("score", 5),
            analysis["ending_clarity"].get("score", 5),
            analysis["pitch_variation"].get("score", 5),
            analysis["service_tone"].get("score", 5),
            analysis["composure"].get("score", 5),
        ]
        avg_score = sum(scores) / len(scores)
        analysis["confidence_score"] = int(avg_score * 10)

        if analysis["confidence_score"] >= 85:
            analysis["confidence_feedback"] = "자신감 넘치는 음성입니다!"
        elif analysis["confidence_score"] >= 70:
            analysis["confidence_feedback"] = "괜찮은 수준입니다. 아래 피드백을 참고하세요."
        elif analysis["confidence_score"] >= 55:
            analysis["confidence_feedback"] = "자신감이 부족해 보일 수 있습니다."
        else:
            analysis["confidence_feedback"] = "긴장이 많이 느껴집니다. 연습이 필요합니다."

        return analysis

    except Exception as e:
        print(f"GPT voice analysis error: {e}")
        return None


def analyze_voice_advanced(audio_bytes: bytes, transcription: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    고급 음성 품질 분석 - 목소리 떨림, 말끝 흐림, 톤 변화 등
    librosa 가능 시 물리적 분석, 불가 시 GPT 기반 폴백

    Args:
        audio_bytes: 오디오 바이트 데이터
        transcription: transcribe_audio 결과 (GPT 폴백용)

    Returns:
        {
            "tremor": {"score": 8, "level": "약함", "feedback": "..."},
            "ending_clarity": {"score": 7, "issue": "말끝 흐림", "feedback": "..."},
            "pitch_variation": {"score": 8, "type": "적절함", "feedback": "..."},
            "energy_consistency": {"score": 7, "feedback": "..."},
            "confidence_score": 75,
            "confidence_feedback": "..."
        }
    """
    result = {
        "tremor": {"score": 5, "level": "보통", "feedback": "분석 대기"},
        "ending_clarity": {"score": 5, "issue": "보통", "feedback": "분석 대기"},
        "pitch_variation": {"score": 5, "type": "보통", "feedback": "분석 대기"},
        "energy_consistency": {"score": 5, "feedback": "분석 대기"},
        "service_tone": {"score": 5, "greeting_bright": False, "ending_soft": False, "feedback": "분석 대기"},
        "composure": {"score": 5, "speed_stable": True, "filler_stable": True, "feedback": "분석 대기"},
        "confidence_score": 50,
        "confidence_feedback": "기본 분석만 수행되었습니다.",
    }

    try:
        import numpy as np
        import io
        import wave
        import struct
    except ImportError:
        return result

    # librosa 사용 시도 (고급 분석)
    try:
        import librosa
        import librosa.display
        HAS_LIBROSA = True
    except ImportError:
        HAS_LIBROSA = False

    # scipy 폴백
    try:
        from scipy import signal
        from scipy.io import wavfile
        HAS_SCIPY = True
    except ImportError:
        HAS_SCIPY = False

    # 임시 파일로 저장
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        if HAS_LIBROSA:
            # librosa로 고급 분석
            y, sr = librosa.load(temp_path, sr=None)

            # 1. 목소리 떨림 분석 (Jitter - 피치 변동성)
            try:
                pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
                pitch_values = []
                for t in range(pitches.shape[1]):
                    index = magnitudes[:, t].argmax()
                    pitch = pitches[index, t]
                    if pitch > 0:
                        pitch_values.append(pitch)

                if len(pitch_values) > 10:
                    pitch_array = np.array(pitch_values)
                    # Jitter: 연속 피치 차이의 변동성
                    pitch_diff = np.abs(np.diff(pitch_array))
                    jitter = np.mean(pitch_diff) / (np.mean(pitch_array) + 1e-6) * 100

                    if jitter < 1.0:
                        tremor_score = 10
                        tremor_level = "없음"
                        tremor_feedback = "목소리가 매우 안정적입니다. 자신감이 느껴집니다."
                    elif jitter < 2.0:
                        tremor_score = 8
                        tremor_level = "약함"
                        tremor_feedback = "목소리가 대체로 안정적입니다."
                    elif jitter < 3.5:
                        tremor_score = 5
                        tremor_level = "보통"
                        tremor_feedback = "약간의 떨림이 감지됩니다. 긴장을 풀고 천천히 말해보세요."
                    else:
                        tremor_score = 3
                        tremor_level = "심함"
                        tremor_feedback = "목소리 떨림이 많습니다. 심호흡 후 차분하게 말해보세요."

                    result["tremor"] = {
                        "score": tremor_score,
                        "level": tremor_level,
                        "jitter_percent": round(jitter, 2),
                        "feedback": tremor_feedback,
                    }
            except Exception as e:
                print(f"Tremor analysis error: {e}")

            # 2. 말끝 흐림 분석 (문장 끝 에너지 하강)
            try:
                # RMS 에너지 계산
                rms = librosa.feature.rms(y=y)[0]

                if len(rms) > 20:
                    # 마지막 20% 구간의 에너지
                    last_portion = int(len(rms) * 0.2)
                    first_portion = int(len(rms) * 0.3)

                    avg_start_energy = np.mean(rms[:first_portion])
                    avg_end_energy = np.mean(rms[-last_portion:])

                    # 에너지 비율 (끝/시작)
                    energy_ratio = avg_end_energy / (avg_start_energy + 1e-6)

                    if energy_ratio >= 0.7:
                        ending_score = 10
                        ending_issue = "없음"
                        ending_feedback = "말끝까지 명확하게 전달합니다."
                    elif energy_ratio >= 0.5:
                        ending_score = 7
                        ending_issue = "약간 흐림"
                        ending_feedback = "말 끝이 약간 흐려집니다. 문장 끝까지 힘을 유지하세요."
                    elif energy_ratio >= 0.3:
                        ending_score = 4
                        ending_issue = "흐림"
                        ending_feedback = "말끝이 흐려져 자신감 없어 보일 수 있습니다. 끝까지 또렷하게!"
                    else:
                        ending_score = 2
                        ending_issue = "매우 흐림"
                        ending_feedback = "문장 끝이 거의 들리지 않습니다. 끝까지 확실하게 발음하세요."

                    result["ending_clarity"] = {
                        "score": ending_score,
                        "issue": ending_issue,
                        "energy_ratio": round(energy_ratio, 2),
                        "feedback": ending_feedback,
                    }
            except Exception as e:
                print(f"Ending clarity analysis error: {e}")

            # 3. 피치 변화 분석 (단조로움 vs 생동감)
            try:
                if len(pitch_values) > 10:
                    pitch_std = np.std(pitch_values)
                    pitch_mean = np.mean(pitch_values)
                    pitch_cv = (pitch_std / (pitch_mean + 1e-6)) * 100  # 변동계수

                    if 15 <= pitch_cv <= 35:
                        pitch_score = 10
                        pitch_type = "생동감 있음"
                        pitch_feedback = "적절한 억양 변화로 듣기 좋습니다."
                    elif 10 <= pitch_cv < 15 or 35 < pitch_cv <= 45:
                        pitch_score = 7
                        pitch_type = "보통"
                        pitch_feedback = "억양 변화가 조금 더 있으면 좋겠습니다." if pitch_cv < 15 else "억양이 조금 과합니다."
                    elif pitch_cv < 10:
                        pitch_score = 4
                        pitch_type = "단조로움"
                        pitch_feedback = "억양이 너무 단조롭습니다. 중요한 부분은 강조하세요."
                    else:
                        pitch_score = 4
                        pitch_type = "불안정"
                        pitch_feedback = "억양 변화가 너무 큽니다. 차분하게 말해보세요."

                    result["pitch_variation"] = {
                        "score": pitch_score,
                        "type": pitch_type,
                        "variation_percent": round(pitch_cv, 1),
                        "feedback": pitch_feedback,
                    }
            except Exception as e:
                print(f"Pitch variation analysis error: {e}")

            # 4. 에너지 일관성 (말 중간에 힘 빠짐)
            try:
                if len(rms) > 20:
                    # 구간별 에너지 변화
                    segment_size = len(rms) // 5
                    segments = [np.mean(rms[i*segment_size:(i+1)*segment_size]) for i in range(5)]

                    # 중간 구간들의 에너지가 일정한지
                    mid_segments = segments[1:4]
                    mid_std = np.std(mid_segments)
                    mid_mean = np.mean(mid_segments)
                    consistency = 1 - (mid_std / (mid_mean + 1e-6))

                    if consistency >= 0.85:
                        energy_score = 10
                        energy_feedback = "일정한 힘으로 말합니다."
                    elif consistency >= 0.7:
                        energy_score = 7
                        energy_feedback = "대체로 일정하지만 중간에 약간 힘이 빠지는 부분이 있습니다."
                    elif consistency >= 0.5:
                        energy_score = 5
                        energy_feedback = "말하는 중간에 힘이 빠집니다. 끝까지 집중해서 말하세요."
                    else:
                        energy_score = 3
                        energy_feedback = "에너지 변동이 큽니다. 호흡을 고르게 하고 말하세요."

                    result["energy_consistency"] = {
                        "score": energy_score,
                        "consistency": round(consistency, 2),
                        "feedback": energy_feedback,
                    }
            except Exception as e:
                print(f"Energy consistency analysis error: {e}")

            # 5. 서비스 톤 분석 (첫 인사 밝기, 문장 끝 부드러움)
            try:
                if len(pitch_values) > 20:
                    # 처음 20% 구간의 피치 (인사 부분)
                    first_portion = int(len(pitch_values) * 0.2)
                    mid_portion_start = int(len(pitch_values) * 0.3)
                    mid_portion_end = int(len(pitch_values) * 0.7)

                    first_pitch = np.mean(pitch_values[:first_portion])
                    mid_pitch = np.mean(pitch_values[mid_portion_start:mid_portion_end])

                    # 첫 인사가 밝은가? (피치가 평균보다 높으면 밝음)
                    pitch_rise_percent = ((first_pitch - mid_pitch) / (mid_pitch + 1e-6)) * 100
                    greeting_bright = pitch_rise_percent >= VOICE_SCORING["service_tone"]["greeting_pitch_rise"]

                    # 문장 끝 부드러움 (ending_clarity와 연계)
                    ending_soft = result["ending_clarity"].get("score", 0) >= 7

                    # 점수 계산
                    service_score = 5
                    if greeting_bright and ending_soft:
                        service_score = 10
                        service_feedback = "밝은 인사와 부드러운 마무리가 좋습니다!"
                    elif greeting_bright:
                        service_score = 8
                        service_feedback = "첫 인사가 밝습니다. 문장 끝도 부드럽게 마무리하면 더 좋습니다."
                    elif ending_soft:
                        service_score = 7
                        service_feedback = "마무리가 부드럽습니다. 첫 인사를 더 밝게 하면 좋겠습니다."
                    else:
                        service_score = 4
                        service_feedback = "인사를 더 밝게, 문장 끝을 부드럽게 마무리하세요."

                    result["service_tone"] = {
                        "score": service_score,
                        "greeting_bright": greeting_bright,
                        "ending_soft": ending_soft,
                        "pitch_rise_percent": round(pitch_rise_percent, 1),
                        "feedback": service_feedback,
                    }
            except Exception as e:
                print(f"Service tone analysis error: {e}")

            # 6. 침착함 분석 (말 속도 급변, 필러 급증)
            try:
                # 구간별 말 속도 분석 (피치 간격으로 대리 측정)
                if len(words_data := []) > 0 or len(pitch_values) > 30:
                    # 5구간으로 나눠서 피치 밀도(= 말 빠르기 proxy) 분석
                    segment_count = 5
                    segment_len = len(pitch_values) // segment_count

                    segment_densities = []
                    for i in range(segment_count):
                        start = i * segment_len
                        end = (i + 1) * segment_len
                        # 유효 피치 밀도
                        valid_count = sum(1 for p in pitch_values[start:end] if p > 0)
                        segment_densities.append(valid_count)

                    # 말 속도 급변 체크
                    if len(segment_densities) > 1:
                        density_changes = []
                        for i in range(1, len(segment_densities)):
                            if segment_densities[i-1] > 0:
                                change = abs(segment_densities[i] - segment_densities[i-1]) / segment_densities[i-1] * 100
                                density_changes.append(change)

                        max_change = max(density_changes) if density_changes else 0
                        speed_stable = max_change < VOICE_SCORING["composure"]["speed_change_threshold"]
                    else:
                        speed_stable = True
                        max_change = 0

                    # 필러 급증 체크는 텍스트 분석에서 수행 (여기선 기본값)
                    filler_stable = True

                    # 점수 계산
                    if speed_stable and filler_stable:
                        composure_score = 10
                        composure_feedback = "침착하게 일정한 속도로 말합니다."
                    elif speed_stable:
                        composure_score = 7
                        composure_feedback = "말 속도는 안정적이지만 추임새가 많습니다."
                    elif filler_stable:
                        composure_score = 6
                        composure_feedback = "말 속도가 급변합니다. 긴장 시 더 천천히 말하세요."
                    else:
                        composure_score = 4
                        composure_feedback = "긴장이 느껴집니다. 심호흡 후 천천히 또박또박 말하세요."

                    result["composure"] = {
                        "score": composure_score,
                        "speed_stable": speed_stable,
                        "filler_stable": filler_stable,
                        "max_speed_change": round(max_change, 1),
                        "feedback": composure_feedback,
                    }
            except Exception as e:
                print(f"Composure analysis error: {e}")

        elif HAS_SCIPY:
            # scipy로 기본 분석 (librosa 없을 때)
            try:
                result["tremor"]["feedback"] = "기본 분석 수행"
                result["ending_clarity"]["feedback"] = "기본 분석 수행"
                result["pitch_variation"]["feedback"] = "기본 분석 수행"
                result["energy_consistency"]["feedback"] = "기본 분석 수행"
            except Exception as e:
                print(f"Scipy analysis error: {e}")

        # GPT 폴백: librosa 분석 실패 시 (결과가 아직 기본값이면)
        librosa_worked = result["tremor"].get("level") not in ["보통", "분석불가"]
        if not librosa_worked and transcription:
            gpt_result = analyze_voice_with_gpt(transcription)
            if gpt_result:
                result.update(gpt_result)

        # 7. 자신감 종합 점수 (모든 항목 포함)
        scores = [
            result["tremor"].get("score", 5),
            result["ending_clarity"].get("score", 5),
            result["pitch_variation"].get("score", 5),
            result["energy_consistency"].get("score", 5),
            result["service_tone"].get("score", 5),
            result["composure"].get("score", 5),
        ]

        confidence_score = int(np.mean(scores) * 10)

        if confidence_score >= 85:
            confidence_feedback = "자신감 넘치는 음성입니다! 면접에서 좋은 인상을 줄 수 있습니다."
        elif confidence_score >= 70:
            confidence_feedback = "괜찮은 수준입니다. 아래 피드백을 참고해 개선하면 더 좋아집니다."
        elif confidence_score >= 55:
            confidence_feedback = "자신감이 부족해 보일 수 있습니다. 연습이 필요합니다."
        else:
            confidence_feedback = "긴장이 많이 느껴집니다. 충분한 연습과 심호흡으로 안정을 찾으세요."

        result["confidence_score"] = confidence_score
        result["confidence_feedback"] = confidence_feedback

    except Exception as e:
        print(f"Advanced voice analysis error: {e}")

    finally:
        # 임시 파일 삭제
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.debug(f"임시 파일 삭제 실패: {e}")

    return result


def analyze_voice_complete(
    audio_bytes: bytes,
    transcription: Dict[str, Any] = None,
    expected_duration_range: Tuple[int, int] = (10, 60),
    response_times: List[float] = None,
) -> Dict[str, Any]:
    """
    음성 종합 분석 (텍스트 분석 + 고급 음성 분석 + 응답 시간)

    Args:
        audio_bytes: 오디오 바이트 데이터
        transcription: transcribe_audio 결과 (없으면 자동 수행)
        expected_duration_range: 적정 답변 시간 범위 (초)
        response_times: 각 응답별 소요 시간 리스트 (초)

    Returns:
        {
            "text_analysis": {...},  # 기존 analyze_voice_quality 결과
            "voice_analysis": {...},  # 고급 음성 분석 결과
            "response_time_analysis": {...},  # 응답 시간 분석
            "total_score": 75,
            "grade": "B",
            "summary": "...",
            "top_improvements": ["...", "..."]
        }
    """
    # 1. 텍스트 분석 (STT 결과 기반)
    if transcription is None:
        transcription = transcribe_audio(audio_bytes, language="ko")

    if transcription:
        text_analysis = analyze_voice_quality(transcription, expected_duration_range)
    else:
        text_analysis = {
            "speech_rate": {"score": 5, "wpm": 0, "feedback": "음성 인식 실패 - 조용한 환경에서 다시 녹음해보세요"},
            "filler_words": {"score": 5, "count": 0, "list": [], "feedback": "녹음을 다시 시도해주세요"},
            "pauses": {"score": 5, "count": 0, "long_pauses": 0, "feedback": "녹음을 다시 시도해주세요"},
            "duration": {"score": 5, "seconds": 0, "feedback": "녹음 시간이 너무 짧거나 음성이 감지되지 않았습니다"},
            "clarity": {"score": 5, "feedback": "마이크 권한을 확인하고 다시 녹음해주세요"},
            "total_score": 50,
            "total_feedback": "음성 인식에 실패했습니다. 조용한 환경에서 마이크 가까이 말씀해주세요.",
        }

    # 2. 고급 음성 분석 (transcription 전달 → GPT 폴백용)
    voice_analysis = analyze_voice_advanced(audio_bytes, transcription=transcription)

    # 3. 응답 시간 분석
    response_time_analysis = {
        "score": 5,
        "avg_time": 0,
        "feedback": "응답 시간 데이터 없음",
    }

    if response_times and len(response_times) > 0:
        import numpy as np
        avg_time = np.mean(response_times)
        min_time, max_time = VOICE_SCORING["response_time"]["perfect"]
        acceptable_min, acceptable_max = VOICE_SCORING["response_time"]["acceptable"]

        if min_time <= avg_time <= max_time:
            rt_score = 10
            rt_feedback = f"적절한 응답 속도입니다. (평균 {avg_time:.1f}초)"
        elif acceptable_min <= avg_time <= acceptable_max:
            rt_score = 7
            if avg_time < min_time:
                rt_feedback = f"응답이 조금 빠릅니다. (평균 {avg_time:.1f}초) 잠시 생각 후 답하세요."
            else:
                rt_feedback = f"응답이 조금 느립니다. (평균 {avg_time:.1f}초) 더 빠르게 반응하세요."
        elif avg_time < acceptable_min:
            rt_score = 4
            rt_feedback = f"너무 즉답합니다. (평균 {avg_time:.1f}초) 경청 후 답변하세요."
        else:
            rt_score = 4
            rt_feedback = f"응답이 너무 느립니다. (평균 {avg_time:.1f}초) 질문에 빠르게 반응하세요."

        response_time_analysis = {
            "score": rt_score,
            "avg_time": round(avg_time, 1),
            "times": response_times,
            "feedback": rt_feedback,
        }

    # 4. 종합 점수 계산
    text_score = text_analysis.get("total_score", 50)
    voice_score = voice_analysis.get("confidence_score", 50)
    rt_score = response_time_analysis.get("score", 5)

    # 텍스트 내용 50%, 음성 품질 35%, 응답 시간 15% 가중치
    total_score = int(text_score * 0.50 + voice_score * 0.35 + rt_score * 10 * 0.15)

    # 등급
    if total_score >= 90:
        grade = "S"
    elif total_score >= 80:
        grade = "A"
    elif total_score >= 70:
        grade = "B"
    elif total_score >= 60:
        grade = "C"
    else:
        grade = "D"

    # 4. 개선 포인트 추출 (점수 낮은 순)
    improvement_items = []

    # 텍스트 분석 항목
    for key in ["speech_rate", "filler_words", "pauses", "clarity"]:
        if text_analysis.get(key, {}).get("score", 10) <= 6:
            improvement_items.append({
                "area": key,
                "score": text_analysis[key]["score"],
                "feedback": text_analysis[key].get("feedback", ""),
            })

    # 음성 분석 항목 (서비스 톤, 침착함 포함)
    for key in ["tremor", "ending_clarity", "pitch_variation", "energy_consistency", "service_tone", "composure"]:
        if voice_analysis.get(key, {}).get("score", 10) <= 6:
            improvement_items.append({
                "area": key,
                "score": voice_analysis[key]["score"],
                "feedback": voice_analysis[key].get("feedback", ""),
            })

    # 응답 시간 항목
    if response_time_analysis.get("score", 10) <= 6:
        improvement_items.append({
            "area": "response_time",
            "score": response_time_analysis["score"],
            "feedback": response_time_analysis.get("feedback", ""),
        })

    # 점수 낮은 순 정렬, 상위 3개
    improvement_items.sort(key=lambda x: x["score"])
    top_improvements = [item["feedback"] for item in improvement_items[:3] if item["feedback"]]

    # 6. 요약
    if total_score >= 80:
        summary = f"우수한 음성 전달력입니다! (등급: {grade})"
    elif total_score >= 65:
        summary = f"괜찮은 수준이지만 개선의 여지가 있습니다. (등급: {grade})"
    else:
        summary = f"음성 전달력 개선이 필요합니다. 아래 피드백을 참고하세요. (등급: {grade})"

    return {
        "text_analysis": text_analysis,
        "voice_analysis": voice_analysis,
        "response_time_analysis": response_time_analysis,
        "total_score": total_score,
        "grade": grade,
        "summary": summary,
        "top_improvements": top_improvements if top_improvements else ["현재 수준을 유지하세요!"],
    }


def generate_tts_audio(
    text: str,
    voice: str = "nova",  # alloy, echo, fable, onyx, nova, shimmer
    speed: float = 1.0,
    use_clova: bool = False,  # 비용 절감을 위해 OpenAI TTS 기본 사용 (나중에 업그레이드 예정)
    persona: str = "",  # 페르소나 (클로바용)
    escalation_level: int = 0,  # 감정 레벨 (클로바용)
) -> Optional[bytes]:
    """
    TTS로 텍스트를 음성으로 변환
    - 기본: OpenAI TTS 사용 (비용 효율적)
    - use_clova=True 시 클로바 사용 (더 자연스러운 한국어, 추가 비용)

    Args:
        text: 변환할 텍스트
        voice: OpenAI 음성 종류 (클로바 미사용시)
        speed: OpenAI 속도 (0.25 ~ 4.0)
        use_clova: 클로바 우선 사용 여부
        persona: 승객 페르소나 (클로바용)
        escalation_level: 감정 레벨 (클로바용)

    Returns:
        MP3 오디오 바이트 데이터
    """
    # 1. 클로바 시도
    if use_clova and is_clova_available():
        if persona:
            speaker, clova_speed, emotion = get_clova_speaker_for_persona(persona, escalation_level)
        else:
            # 페르소나 없으면 기본 설정
            speaker = "nara"
            clova_speed = 0
            emotion = CLOVA_EMOTIONS.get("angry", 0) if escalation_level >= 2 else 0

        audio = generate_clova_tts(
            text=text,
            speaker=speaker,
            speed=clova_speed,
            emotion=emotion,
        )
        if audio:
            return audio
        print("CLOVA TTS 실패, OpenAI로 폴백...")

    # 2. OpenAI TTS 폴백
    api_key = get_openai_api_key()
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "tts-1-hd",
        "input": text,
        "voice": voice,
        "speed": speed,
    }

    try:
        r = requests.post(
            f"{OPENAI_API_URL}/audio/speech",
            headers=headers,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        return r.content

    except Exception as e:
        print(f"OpenAI TTS API Error: {e}")
        return None


def generate_tts_for_passenger(
    text: str,
    persona: str,
    escalation_level: int = 0,
) -> Optional[bytes]:
    """
    승객 대사용 TTS 생성 (페르소나/감정 자동 매핑)

    Args:
        text: 승객 대사
        persona: 승객 페르소나
        escalation_level: 감정 레벨 (0: 평상시, 1: 짜증, 2: 화남)

    Returns:
        MP3 오디오 바이트 데이터
    """
    # OpenAI TTS 기본 사용 (비용 효율적)
    voice, speed = get_voice_for_persona(persona, escalation_level)
    return generate_tts_audio(
        text=text,
        voice=voice,
        speed=speed,
        use_clova=False,
    )


def get_loud_audio_component(audio_bytes: bytes, autoplay: bool = True, gain: float = 10.0):
    """
    볼륨 증폭된 오디오 플레이어 (Streamlit components.html 사용)

    Args:
        audio_bytes: MP3 오디오 바이트
        autoplay: 자동 재생 여부
        gain: 볼륨 증폭 배율 (10.0 = 10배)
    """
    import base64
    import streamlit.components.v1 as components

    audio_b64 = base64.b64encode(audio_bytes).decode()

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <body>
    <button id="playBtn" style="padding: 10px 20px; font-size: 16px; cursor: pointer; background: #4CAF50; color: white; border: none; border-radius: 5px;">
        🔊 재생 (볼륨 증폭)
    </button>
    <script>
    var audioCtx = null;
    var isPlaying = false;

    document.getElementById('playBtn').addEventListener('click', async function() {{
        if (isPlaying) return;
        isPlaying = true;
        this.textContent = '🔊 재생 중...';
        this.style.background = '#888';

        try {{
            if (!audioCtx) {{
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }}
            if (audioCtx.state === 'suspended') {{
                await audioCtx.resume();
            }}

            var base64 = "{audio_b64}";
            var binaryString = atob(base64);
            var len = binaryString.length;
            var bytes = new Uint8Array(len);
            for (var i = 0; i < len; i++) {{
                bytes[i] = binaryString.charCodeAt(i);
            }}

            var audioBuffer = await audioCtx.decodeAudioData(bytes.buffer);
            var source = audioCtx.createBufferSource();
            source.buffer = audioBuffer;

            var gainNode = audioCtx.createGain();
            gainNode.gain.value = {gain};

            source.connect(gainNode);
            gainNode.connect(audioCtx.destination);

            source.onended = function() {{
                isPlaying = false;
                document.getElementById('playBtn').textContent = '🔊 재생 (볼륨 증폭)';
                document.getElementById('playBtn').style.background = '#4CAF50';
            }};

            source.start(0);
        }} catch(e) {{
            console.error('Audio error:', e);
            isPlaying = false;
            this.textContent = '🔊 재생 (볼륨 증폭)';
            this.style.background = '#4CAF50';
        }}
    }});

    {"document.getElementById('playBtn').click();" if autoplay else ""}
    </script>
    </body>
    </html>
    """

    components.html(html_code, height=60)


def get_audio_player_html(audio_bytes: bytes, autoplay: bool = False, volume_boost: float = 2.0) -> str:
    """
    오디오 재생용 HTML 생성 (기본 플레이어)

    Args:
        audio_bytes: MP3 오디오 바이트
        autoplay: 자동 재생 여부
        volume_boost: 사용하지 않음

    Returns:
        HTML 문자열
    """
    import base64

    audio_b64 = base64.b64encode(audio_bytes).decode()
    autoplay_attr = "autoplay" if autoplay else ""

    return f"""<audio {autoplay_attr} controls style="width: 100%;"><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>"""


def evaluate_answer_content(
    question: str,
    answer_text: str,
    airline: str = "",
    airline_type: str = "LCC",
) -> Dict[str, Any]:
    """
    답변 내용 평가 (GPT-4o-mini)

    Args:
        question: 면접 질문
        answer_text: 답변 텍스트
        airline: 항공사명
        airline_type: FSC/LCC

    Returns:
        {
            "content_score": 35,  # /40
            "structure_score": 25,  # /30
            "delivery_score": 12,  # /15
            "relevance_score": 13,  # /15
            "total_score": 85,
            "star_check": {...},
            "strengths": [...],
            "improvements": [...],
            "sample_answer": "..."
        }
    """
    api_key = get_openai_api_key()
    if not api_key:
        return {"error": "API 키 없음"}

    system_prompt = f"""당신은 엄격한 항공사 면접관입니다.
지원 항공사: {airline} ({airline_type})

답변을 객관적으로 평가하세요. 후한 점수를 주지 마세요.

JSON 형식으로만 응답하세요:
{{
    "content_score": 0-40,
    "content_feedback": "내용 피드백",
    "structure_score": 0-30,
    "structure_feedback": "구조 피드백",
    "delivery_score": 0-15,
    "delivery_feedback": "전달력 피드백",
    "relevance_score": 0-15,
    "relevance_feedback": "질문 관련성 피드백",
    "star_check": {{
        "situation": true/false,
        "task": true/false,
        "action": true/false,
        "result": true/false
    }},
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2", "개선점3"],
    "sample_answer": "모범 답변 예시 (3-4문장)"
}}

점수 기준:
- content (40점): 구체적 경험, 숫자/사례, 진정성
- structure (30점): 두괄식, STAR 구조, 논리 흐름
- delivery (15점): 자신감 있는 표현, "것 같습니다" 과다 사용 감점
- relevance (15점): 질문 의도 파악, 핵심 답변"""

    user_prompt = f"""질문: {question}

답변: {answer_text}

위 답변을 평가해주세요."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    try:
        r = requests.post(
            f"{OPENAI_API_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        r.raise_for_status()
        result = r.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        parsed = json.loads(content)

        # 총점 계산
        total = (
            parsed.get("content_score", 0) +
            parsed.get("structure_score", 0) +
            parsed.get("delivery_score", 0) +
            parsed.get("relevance_score", 0)
        )
        parsed["total_score"] = total

        return parsed

    except Exception as e:
        return {"error": str(e)}


# =====================================================
# Google Cloud TTS 연동 (Neural2 - 고품질 한국어)
# =====================================================

# Google Cloud TTS API 설정
GOOGLE_TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

# Google Cloud TTS 한국어 음성 목록 (Neural2 = 최고 품질)
GOOGLE_TTS_VOICES = {
    # Neural2 (최고 품질) - 추천
    "ko-KR-Neural2-A": {"name": "여성 A (Neural2)", "gender": "female", "quality": "neural2", "desc": "자연스러운 여성 음성"},
    "ko-KR-Neural2-B": {"name": "여성 B (Neural2)", "gender": "female", "quality": "neural2", "desc": "부드러운 여성 음성"},
    "ko-KR-Neural2-C": {"name": "남성 A (Neural2)", "gender": "male", "quality": "neural2", "desc": "자연스러운 남성 음성"},

    # Wavenet (고품질)
    "ko-KR-Wavenet-A": {"name": "여성 A (Wavenet)", "gender": "female", "quality": "wavenet", "desc": "여성 음성"},
    "ko-KR-Wavenet-B": {"name": "여성 B (Wavenet)", "gender": "female", "quality": "wavenet", "desc": "여성 음성"},
    "ko-KR-Wavenet-C": {"name": "남성 A (Wavenet)", "gender": "male", "quality": "wavenet", "desc": "남성 음성"},
    "ko-KR-Wavenet-D": {"name": "남성 B (Wavenet)", "gender": "male", "quality": "wavenet", "desc": "남성 음성"},

    # Standard (무료 할당량 많음)
    "ko-KR-Standard-A": {"name": "여성 (Standard)", "gender": "female", "quality": "standard", "desc": "기본 여성 음성"},
    "ko-KR-Standard-B": {"name": "여성 (Standard)", "gender": "female", "quality": "standard", "desc": "기본 여성 음성"},
    "ko-KR-Standard-C": {"name": "남성 (Standard)", "gender": "male", "quality": "standard", "desc": "기본 남성 음성"},
    "ko-KR-Standard-D": {"name": "남성 (Standard)", "gender": "male", "quality": "standard", "desc": "기본 남성 음성"},
}


def get_google_api_key() -> str:
    """Google Cloud API 키 가져오기"""
    return (
        os.environ.get("GOOGLE_TTS_API_KEY", "")
        or os.environ.get("GOOGLE_CLOUD_API_KEY", "")
        or os.environ.get("GOOGLE_API_KEY", "")
    )


def is_google_tts_available() -> bool:
    """Google Cloud TTS 사용 가능 여부"""
    return bool(get_google_api_key())


def get_google_voice_for_persona(persona: str, escalation_level: int = 0) -> Tuple[str, float, float]:
    """
    페르소나에 맞는 Google TTS 음성 선택

    Args:
        persona: 승객 페르소나
        escalation_level: 감정 레벨 (0: 평상시, 1: 짜증, 2: 화남)

    Returns:
        (voice_name, speaking_rate, pitch) 튜플
    """
    # 성별 판단
    is_female = any(kw in persona for kw in ['여성', '엄마', '할머니', '여자', '부인', '임산부', '아줌마'])

    # 기본 음성 선택 (Neural2 = 최고 품질)
    if is_female:
        voice = "ko-KR-Neural2-A"
    else:
        voice = "ko-KR-Neural2-C"

    # 감정에 따른 속도/피치 조절
    if escalation_level == 0:
        speaking_rate = 1.0
        pitch = 0.0
    elif escalation_level == 1:
        speaking_rate = 1.1  # 약간 빠르게
        pitch = 1.0  # 약간 높게
    else:  # 화남
        speaking_rate = 1.2  # 더 빠르게
        pitch = 2.0  # 더 높게

    return (voice, speaking_rate, pitch)


def generate_google_tts(
    text: str,
    voice_name: str = "ko-KR-Neural2-A",
    speaking_rate: float = 1.0,
    pitch: float = 0.0,
    volume_gain_db: float = 0.0,
) -> Optional[bytes]:
    """
    Google Cloud TTS API로 음성 생성

    Args:
        text: 변환할 텍스트
        voice_name: 음성 이름 (ko-KR-Neural2-A 등)
        speaking_rate: 말하기 속도 (0.25 ~ 4.0, 기본 1.0)
        pitch: 피치 (-20.0 ~ 20.0, 기본 0.0)
        volume_gain_db: 볼륨 (-96.0 ~ 16.0, 기본 0.0)

    Returns:
        MP3 오디오 바이트 또는 None
    """
    api_key = get_google_api_key()
    if not api_key:
        print("[Google TTS] API 키 없음")
        return None

    # 텍스트 길이 제한 (5000바이트)
    if len(text.encode('utf-8')) > 5000:
        text = text[:1500]  # 대략적인 제한

    # API 요청 URL (API 키 방식)
    url = f"{GOOGLE_TTS_URL}?key={api_key}"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }

    payload = {
        "input": {
            "text": text
        },
        "voice": {
            "languageCode": "ko-KR",
            "name": voice_name,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": speaking_rate,
            "pitch": pitch,
            "volumeGainDb": volume_gain_db,
        }
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)

        if r.status_code == 200:
            result = r.json()
            audio_content = result.get("audioContent", "")
            if audio_content:
                import base64
                audio_bytes = base64.b64decode(audio_content)
                print(f"[Google TTS] 성공 - {voice_name}, {len(audio_bytes)} bytes")
                return audio_bytes
            else:
                print("[Google TTS] 오디오 컨텐츠 없음")
                return None
        else:
            print(f"[Google TTS] 오류: {r.status_code} - {r.text[:200]}")
            return None

    except Exception as e:
        print(f"[Google TTS] 예외: {e}")
        return None


def generate_tts_for_passenger_v2(
    text: str,
    persona: str,
    escalation_level: int = 0,
    tts_provider: str = "openai",  # "openai" 기본 (비용 효율적), "auto", "google", "clova" 선택 가능
) -> Optional[bytes]:
    """
    승객 대사용 TTS 생성 (v2 - 다중 TTS 지원, 기본: OpenAI)

    Args:
        text: 승객 대사
        persona: 승객 페르소나
        escalation_level: 감정 레벨 (0: 평상시, 1: 짜증, 2: 화남)
        tts_provider: TTS 제공자 선택

    Returns:
        MP3 오디오 바이트 데이터
    """
    # 1. Google TTS 시도 (auto 또는 google 선택 시)
    if tts_provider in ["auto", "google"] and is_google_tts_available():
        voice, rate, pitch = get_google_voice_for_persona(persona, escalation_level)
        audio = generate_google_tts(
            text=text,
            voice_name=voice,
            speaking_rate=rate,
            pitch=pitch,
        )
        if audio:
            return audio
        if tts_provider == "google":
            print("[TTS] Google TTS 실패")
            return None

    # 2. CLOVA 시도 (auto 또는 clova 선택 시)
    if tts_provider in ["auto", "clova"] and is_clova_available():
        speaker, speed, emotion = get_clova_speaker_for_persona(persona, escalation_level)
        audio = generate_clova_tts(
            text=text,
            speaker=speaker,
            speed=speed,
            emotion=emotion,
        )
        if audio:
            return audio
        if tts_provider == "clova":
            print("[TTS] CLOVA TTS 실패")
            return None

    # 3. OpenAI 폴백
    voice, speed = get_voice_for_persona(persona, escalation_level)
    return generate_tts_audio(
        text=text,
        voice=voice,
        speed=speed,
        use_clova=False,
    )


# =====================================================
# Edge TTS 연동 (Microsoft Edge 브라우저 TTS - 무료/무제한)
# =====================================================

# Edge TTS 한국어 음성 목록
EDGE_TTS_VOICES = {
    # 여성 음성
    "ko-KR-SunHiNeural": {"name": "선희", "gender": "female", "age": "adult", "desc": "밝고 친근한 여성 음성"},
    "ko-KR-YuJinNeural": {"name": "유진", "gender": "female", "age": "young", "desc": "젊고 활기찬 여성 음성"},

    # 남성 음성
    "ko-KR-InJoonNeural": {"name": "인준", "gender": "male", "age": "adult", "desc": "차분한 남성 음성"},
    "ko-KR-HyunsuNeural": {"name": "현수", "gender": "male", "age": "adult", "desc": "신뢰감 있는 남성 음성"},
    "ko-KR-GookMinNeural": {"name": "국민", "gender": "male", "age": "adult", "desc": "표준 남성 음성"},
}


def is_edge_tts_available() -> bool:
    """Edge TTS 사용 가능 여부 (항상 True - API 키 불필요)"""
    try:
        import edge_tts
        return True
    except ImportError:
        return False


def get_edge_voice_for_persona(persona: str, escalation_level: int = 0) -> Tuple[str, str, str]:
    """
    페르소나에 맞는 Edge TTS 음성 선택

    Args:
        persona: 승객 페르소나
        escalation_level: 감정 레벨 (0: 평상시, 1: 짜증, 2: 화남)

    Returns:
        (voice_name, rate, pitch) 튜플 (rate/pitch는 문자열: "+10%", "-5Hz" 등)
    """
    # 성별 판단
    is_female = any(kw in persona for kw in ['여성', '엄마', '할머니', '여자', '부인', '임산부', '아줌마'])
    is_male = any(kw in persona for kw in ['남성', '아빠', '할아버지', '남자', '사업가']) and not is_female

    # 나이대 판단
    if any(kw in persona for kw in ['20대', '대학생', '젊은']):
        age = "young"
    else:
        age = "adult"

    # 음성 선택
    if is_female:
        if age == "young":
            voice = "ko-KR-YuJinNeural"  # 젊은 여성
        else:
            voice = "ko-KR-SunHiNeural"  # 성인 여성
    else:
        voice = "ko-KR-InJoonNeural"  # 남성

    # 감정에 따른 속도/피치 조절
    if escalation_level == 0:
        rate = "+0%"
        pitch = "+0Hz"
    elif escalation_level == 1:
        rate = "+10%"  # 약간 빠르게
        pitch = "+5Hz"  # 약간 높게
    else:  # 화남
        rate = "+20%"  # 더 빠르게
        pitch = "+10Hz"  # 더 높게

    return (voice, rate, pitch)


def generate_edge_tts(
    text: str,
    voice: str = "ko-KR-SunHiNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> Optional[bytes]:
    """
    Edge TTS로 음성 생성 (무료/무제한)

    Args:
        text: 변환할 텍스트
        voice: 음성 이름
        rate: 말하기 속도 (예: "+10%", "-5%")
        pitch: 피치 (예: "+5Hz", "-10Hz")

    Returns:
        MP3 오디오 바이트 또는 None
    """
    try:
        import edge_tts
        import asyncio

        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data

        # 이벤트 루프 처리 (Streamlit 환경 고려)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # 이미 이벤트 루프가 실행 중인 경우 (Streamlit)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _generate())
                audio_bytes = future.result(timeout=30)
        else:
            # 새 이벤트 루프 생성
            audio_bytes = asyncio.run(_generate())

        if audio_bytes:
            print(f"[Edge TTS] 성공 - {voice}, {len(audio_bytes)} bytes")
            return audio_bytes
        else:
            print("[Edge TTS] 오디오 데이터 없음")
            return None

    except ImportError:
        print("[Edge TTS] edge-tts 패키지가 설치되지 않았습니다. pip install edge-tts")
        return None
    except Exception as e:
        print(f"[Edge TTS] 예외: {e}")
        return None


def generate_tts_for_passenger_v3(
    text: str,
    persona: str,
    escalation_level: int = 0,
    tts_provider: str = "openai",  # "openai" 기본 (비용 효율적), "edge"(무료), "clova", "auto" 선택 가능
) -> Optional[bytes]:
    """
    승객 대사용 TTS 생성 (v3 - 다중 TTS 지원, 기본: OpenAI)

    Args:
        text: 승객 대사
        persona: 승객 페르소나
        escalation_level: 감정 레벨 (0: 평상시, 1: 짜증, 2: 화남)
        tts_provider: TTS 제공자 선택 (기본: edge)

    Returns:
        MP3 오디오 바이트 데이터
    """
    # 1. Edge TTS 시도 (무료, 우선 사용)
    if tts_provider in ["auto", "edge"] and is_edge_tts_available():
        voice, rate, pitch = get_edge_voice_for_persona(persona, escalation_level)
        audio = generate_edge_tts(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
        if audio:
            return audio
        if tts_provider == "edge":
            print("[TTS] Edge TTS 실패")
            # 폴백 없이 None 반환하지 않고 다음으로 진행

    # 2. CLOVA 시도
    if tts_provider in ["auto", "clova"] and is_clova_available():
        speaker, speed, emotion = get_clova_speaker_for_persona(persona, escalation_level)
        audio = generate_clova_tts(
            text=text,
            speaker=speaker,
            speed=speed,
            emotion=emotion,
        )
        if audio:
            return audio
        if tts_provider == "clova":
            print("[TTS] CLOVA TTS 실패")
            return None

    # 3. OpenAI 폴백
    voice, speed = get_voice_for_persona(persona, escalation_level)
    return generate_tts_audio(
        text=text,
        voice=voice,
        speed=speed,
        use_clova=False,
    )


# =====================================================
# 감정 분석 래퍼 함수 (Phase 1 - 감정 분석 통합)
# =====================================================

# 감정 한국어 설명 매핑
EMOTION_KOREAN_MAP = {
    "neutral": ("중립", "차분하고 안정적인 상태입니다."),
    "happy": ("행복", "긍정적이고 밝은 감정이 느껴집니다."),
    "sad": ("슬픔", "다소 우울하거나 침체된 느낌입니다."),
    "angry": ("화남", "불만이나 짜증이 느껴집니다."),
    "fearful": ("두려움", "불안하거나 걱정되는 상태입니다."),
    "surprised": ("놀람", "예상치 못한 반응을 보이고 있습니다."),
    "disgusted": ("혐오", "불쾌하거나 거부감을 느끼고 있습니다."),
    "confident": ("자신감", "확신에 차 있고 당당합니다."),
    "nervous": ("긴장", "긴장하거나 불안해 보입니다."),
    "excited": ("흥분", "들뜨고 열정적인 상태입니다."),
    "confused": ("혼란", "무엇인가에 대해 확신이 없어 보입니다."),
    "focused": ("집중", "집중하며 진지하게 임하고 있습니다."),
    "stressed": ("스트레스", "압박감을 느끼고 있습니다."),
    "calm": ("차분함", "침착하고 여유로운 상태입니다."),
    "enthusiastic": ("열정", "열의와 관심이 넘칩니다."),
}


def extract_voice_features_for_emotion(audio_bytes: bytes) -> Dict[str, Any]:
    """
    감정 분석을 위한 음성 특성 추출

    Args:
        audio_bytes: 오디오 바이트 데이터

    Returns:
        EmotionDetector가 사용하는 형식의 특성 딕셔너리
    """
    features = {
        "pitch_mean": 150,
        "pitch_std": 30,
        "pitch_range": 100,
        "energy_mean": 0.5,
        "energy_std": 0.1,
        "speech_rate": 150,
        "pause_ratio": 0.2,
        "jitter": 0.02,
        "shimmer": 0.03,
        "spectral_centroid": 2000,
    }

    try:
        import numpy as np
        import librosa
        import tempfile

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            # librosa로 로드
            y, sr = librosa.load(temp_path, sr=None)

            if len(y) == 0:
                return features

            # 피치 추출
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)

            if len(pitch_values) > 0:
                pitch_array = np.array(pitch_values)
                features["pitch_mean"] = float(np.mean(pitch_array))
                features["pitch_std"] = float(np.std(pitch_array))
                features["pitch_range"] = float(np.max(pitch_array) - np.min(pitch_array))

                # Jitter 계산
                if len(pitch_values) > 1:
                    pitch_diff = np.abs(np.diff(pitch_array))
                    features["jitter"] = float(np.mean(pitch_diff) / (np.mean(pitch_array) + 1e-6))

            # RMS 에너지 계산
            rms = librosa.feature.rms(y=y)[0]
            if len(rms) > 0:
                features["energy_mean"] = float(np.mean(rms))
                features["energy_std"] = float(np.std(rms))

                # Shimmer 계산 (에너지 변동성)
                if len(rms) > 1:
                    rms_diff = np.abs(np.diff(rms))
                    features["shimmer"] = float(np.mean(rms_diff) / (np.mean(rms) + 1e-6))

            # Spectral centroid
            spec_cent = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            if len(spec_cent) > 0:
                features["spectral_centroid"] = float(np.mean(spec_cent))

            # 음성 구간 감지로 휴지 비율 추정
            intervals = librosa.effects.split(y, top_db=30)
            if len(intervals) > 0:
                voiced_frames = sum(end - start for start, end in intervals)
                total_frames = len(y)
                features["pause_ratio"] = 1.0 - (voiced_frames / total_frames) if total_frames > 0 else 0.2

        finally:
            # 임시 파일 삭제
            import os
            try:
                os.unlink(temp_path)
            except:
                pass

    except ImportError:
        logger.warning("librosa가 설치되지 않아 기본 특성값을 사용합니다.")
    except Exception as e:
        logger.warning(f"음성 특성 추출 실패: {e}")

    return features


def get_default_emotion_result() -> Dict[str, Any]:
    """감정 분석 실패 시 기본값 반환"""
    return {
        "confidence_score": 5.0,
        "stress_level": 5.0,
        "engagement_level": 5.0,
        "emotion_stability": 5.0,
        "primary_emotion": "neutral",
        "emotion_description": "분석 결과를 가져올 수 없습니다.",
        "suggestions": ["다시 한번 녹음해 보세요."],
        "valence": 0.0,
        "arousal": 0.5,
    }


def analyze_interview_emotion(
    audio_bytes: bytes,
    transcribed_text: str = "",
    question_context: str = "",
) -> Dict[str, Any]:
    """
    면접 답변의 감정을 종합 분석

    Args:
        audio_bytes: 오디오 바이트 데이터
        transcribed_text: 인식된 텍스트
        question_context: 질문 맥락

    Returns:
        {
            "confidence_score": 0-10,
            "stress_level": 0-10,
            "engagement_level": 0-10,
            "emotion_stability": 0-10,
            "primary_emotion": str,
            "emotion_description": str,
            "suggestions": List[str],
            "valence": float (-1 to 1),
            "arousal": float (0 to 1),
        }
    """
    try:
        # 음성 특성 추출
        voice_features = extract_voice_features_for_emotion(audio_bytes)

        # 간단한 감정 분석 로직 (EmotionDetector의 핵심 로직 적용)
        scores = {}

        # 피치 분석
        pitch_std = voice_features.get("pitch_std", 30)
        if pitch_std > 50:
            scores["excited"] = 0.3
            scores["nervous"] = 0.2
        elif pitch_std < 20:
            scores["calm"] = 0.3
            scores["neutral"] = 0.2

        # 에너지 분석
        energy_mean = voice_features.get("energy_mean", 0.5)
        if energy_mean > 0.7:
            scores["excited"] = scores.get("excited", 0.0) + 0.2
            scores["confident"] = scores.get("confident", 0.0) + 0.2
        elif energy_mean < 0.3:
            scores["sad"] = scores.get("sad", 0.0) + 0.2
            scores["nervous"] = scores.get("nervous", 0.0) + 0.15

        # Jitter 분석 (목소리 떨림)
        jitter = voice_features.get("jitter", 0.02)
        shimmer = voice_features.get("shimmer", 0.03)
        if jitter > 0.05 or shimmer > 0.1:
            scores["stressed"] = scores.get("stressed", 0.0) + 0.3
            scores["nervous"] = scores.get("nervous", 0.0) + 0.2

        # 휴지 비율 분석
        pause_ratio = voice_features.get("pause_ratio", 0.2)
        if pause_ratio > 0.4:
            scores["nervous"] = scores.get("nervous", 0.0) + 0.2
            scores["confused"] = scores.get("confused", 0.0) + 0.15

        # 텍스트 기반 분석
        if transcribed_text:
            text_lower = transcribed_text.lower()
            word_count = len(transcribed_text.split())

            # 자신감 키워드
            confident_keywords = ["확실히", "분명히", "반드시", "certainly", "definitely", "absolutely"]
            nervous_keywords = ["음", "어", "그", "그러니까", "um", "uh", "maybe", "perhaps"]

            conf_count = sum(1 for kw in confident_keywords if kw in text_lower)
            nerv_count = sum(1 for kw in nervous_keywords if kw in text_lower)

            if conf_count > 0:
                scores["confident"] = scores.get("confident", 0.0) + conf_count * 0.1
            if nerv_count > 0:
                scores["nervous"] = scores.get("nervous", 0.0) + nerv_count * 0.05

            # 응답 길이 분석
            if word_count > 50:
                scores["confident"] = scores.get("confident", 0.0) + 0.15
            elif word_count < 10:
                scores["nervous"] = scores.get("nervous", 0.0) + 0.1

        # 기본값
        if not scores:
            scores["neutral"] = 0.5

        # 정규화
        total = sum(scores.values())
        if total > 0:
            scores = {e: s / total for e, s in scores.items()}

        # 주요 감정 결정
        primary_emotion = max(scores.items(), key=lambda x: x[1])[0]
        primary_confidence = scores[primary_emotion]

        # 면접 메트릭 계산
        stress_level = (
            scores.get("stressed", 0) * 10 +
            scores.get("nervous", 0) * 8 +
            scores.get("fearful", 0) * 7
        )
        stress_level = min(10, stress_level * 3)  # 스케일링

        confidence_level = (
            scores.get("confident", 0) * 10 +
            scores.get("calm", 0) * 7 +
            scores.get("enthusiastic", 0) * 6
        )
        confidence_level = min(10, confidence_level * 3)

        engagement_level = (
            scores.get("excited", 0) * 10 +
            scores.get("enthusiastic", 0) * 10 +
            scores.get("focused", 0) * 8 +
            scores.get("happy", 0) * 6
        )
        engagement_level = min(10, engagement_level * 3)

        # 안정성 (떨림이 적을수록 높음)
        emotion_stability = 10.0 - min(10.0, jitter * 100)

        # 감정 설명 가져오기
        emotion_info = EMOTION_KOREAN_MAP.get(primary_emotion, ("알 수 없음", "분석 중입니다."))
        emotion_description = emotion_info[1]

        # 제안 생성
        suggestions = []
        if stress_level > 6:
            suggestions.append("심호흡을 하고 천천히 말해보세요.")
        if confidence_level < 4:
            suggestions.append("답변 시 '~것 같습니다' 대신 '~입니다'로 확신 있게 말해보세요.")
        if engagement_level < 4:
            suggestions.append("질문에 대한 열정과 관심을 표현해 보세요.")
        if emotion_stability < 5:
            suggestions.append("목소리 떨림이 감지됩니다. 긴장을 풀고 자연스럽게 말해보세요.")

        if not suggestions:
            suggestions.append("전반적으로 좋은 감정 상태입니다. 이 상태를 유지하세요!")

        # VAD 값 계산 (Valence, Arousal)
        valence = (
            scores.get("happy", 0) * 0.8 +
            scores.get("confident", 0) * 0.6 +
            scores.get("enthusiastic", 0) * 0.8 -
            scores.get("sad", 0) * 0.6 -
            scores.get("angry", 0) * 0.5 -
            scores.get("fearful", 0) * 0.7 -
            scores.get("stressed", 0) * 0.4
        )
        valence = max(-1, min(1, valence * 2))

        arousal = (
            scores.get("excited", 0) * 0.8 +
            scores.get("angry", 0) * 0.8 +
            scores.get("nervous", 0) * 0.6 +
            scores.get("stressed", 0) * 0.7 -
            scores.get("calm", 0) * 0.2
        )
        arousal = max(0, min(1, arousal * 2 + 0.3))

        return {
            "confidence_score": round(confidence_level, 1),
            "stress_level": round(stress_level, 1),
            "engagement_level": round(engagement_level, 1),
            "emotion_stability": round(emotion_stability, 1),
            "primary_emotion": primary_emotion,
            "emotion_description": emotion_description,
            "suggestions": suggestions[:3],  # 최대 3개
            "valence": round(valence, 2),
            "arousal": round(arousal, 2),
            "emotion_scores": {k: round(v, 3) for k, v in scores.items()},
        }

    except Exception as e:
        logger.warning(f"감정 분석 실패: {e}")
        return get_default_emotion_result()


# =====================================================
# 고도화된 음성 분석 (Phase 1 강화)
# =====================================================

# 필러 단어 목록 (한국어 + 영어)
FILLER_WORDS_KO = [
    "음", "어", "그", "저", "뭐", "이제", "그래서", "그러니까",
    "아", "에", "으음", "저기", "그게", "뭐랄까", "어떻게",
    "사실", "약간", "좀", "진짜", "막", "뭔가", "그냥",
]
FILLER_WORDS_EN = [
    "um", "uh", "er", "ah", "like", "you know", "so", "well",
    "basically", "actually", "literally", "I mean", "kind of",
]

# 자신감 키워드
CONFIDENT_KEYWORDS = [
    "확실히", "분명히", "반드시", "당연히", "물론", "절대",
    "저는", "제가", "직접", "명확하게", "구체적으로",
    "certainly", "definitely", "absolutely", "clearly",
]

# 불확실성 키워드
UNCERTAIN_KEYWORDS = [
    "아마", "어쩌면", "혹시", "글쎄", "모르겠", "같아요",
    "것 같", "듯해요", "인 듯", "일수도", "maybe", "perhaps",
    "probably", "might", "could be", "I think", "I guess",
]


def analyze_voice_advanced(
    audio_bytes: bytes,
    transcribed_text: str = "",
    question_context: str = "",
    audio_duration: float = 0.0,
) -> Dict[str, Any]:
    """
    고도화된 음성 분석 (면접용)

    Returns:
        {
            # 기본 감정 분석
            "emotion": {...},

            # 말 속도 분석
            "speech_rate": {
                "wpm": float,  # 분당 단어 수
                "syllables_per_sec": float,  # 초당 음절 수
                "rating": str,  # "느림", "적절", "빠름"
                "feedback": str,
            },

            # 필러 단어 분석
            "filler_analysis": {
                "total_count": int,
                "filler_ratio": float,  # 전체 단어 대비 비율
                "details": [{"word": str, "count": int}],
                "rating": str,
                "feedback": str,
            },

            # 침묵/휴지 분석
            "pause_analysis": {
                "total_pauses": int,  # 총 휴지 횟수
                "long_pauses": int,  # 3초 이상 침묵
                "avg_pause_duration": float,
                "pause_ratio": float,  # 전체 대비 침묵 비율
                "rating": str,
                "feedback": str,
            },

            # 에너지/톤 분석
            "energy_analysis": {
                "start_energy": float,  # 시작 구간 에너지
                "mid_energy": float,  # 중간 구간 에너지
                "end_energy": float,  # 종료 구간 에너지
                "energy_trend": str,  # "상승", "유지", "하락"
                "pitch_variation": float,  # 피치 변화량
                "monotone_score": float,  # 단조로움 점수 (0-10, 낮을수록 좋음)
                "feedback": str,
            },

            # 발음 명확도
            "pronunciation": {
                "clarity_score": float,  # 0-100
                "feedback": str,
            },

            # 답변 구조 분석
            "structure_analysis": {
                "has_intro": bool,
                "has_body": bool,
                "has_conclusion": bool,
                "star_score": float,  # STAR 구조 점수
                "feedback": str,
            },

            # 종합 점수 및 피드백
            "overall": {
                "voice_score": float,  # 종합 음성 점수 (0-100)
                "strengths": List[str],
                "improvements": List[str],
                "detailed_feedback": str,
            },
        }
    """
    result = {
        "emotion": {},
        "speech_rate": {},
        "filler_analysis": {},
        "pause_analysis": {},
        "energy_analysis": {},
        "pronunciation": {},
        "structure_analysis": {},
        "overall": {},
    }

    try:
        # 기본 음성 특성 추출
        voice_features = extract_voice_features_for_emotion(audio_bytes)

        # 오디오 duration 계산 (없으면 추정)
        if audio_duration <= 0:
            audio_duration = voice_features.get("duration", 60.0)

        # 1. 기존 감정 분석
        emotion_result = analyze_interview_emotion(audio_bytes, transcribed_text, question_context)
        result["emotion"] = emotion_result

        # 2. 말 속도 분석
        result["speech_rate"] = _analyze_speech_rate(transcribed_text, audio_duration)

        # 3. 필러 단어 분석
        result["filler_analysis"] = _analyze_filler_words(transcribed_text)

        # 4. 침묵/휴지 분석
        result["pause_analysis"] = _analyze_pauses(voice_features, audio_duration)

        # 5. 에너지/톤 분석
        result["energy_analysis"] = _analyze_energy_pattern(voice_features, audio_bytes)

        # 6. 발음 명확도 (STT 신뢰도 기반)
        result["pronunciation"] = _analyze_pronunciation(transcribed_text, voice_features)

        # 7. 답변 구조 분석
        result["structure_analysis"] = _analyze_answer_structure(transcribed_text)

        # 8. 종합 점수 계산
        result["overall"] = _calculate_overall_score(result)

    except Exception as e:
        logger.warning(f"고도화 음성 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        # 기본값 반환
        result["overall"] = {
            "voice_score": 50.0,
            "strengths": [],
            "improvements": ["분석 중 오류가 발생했습니다."],
            "detailed_feedback": "음성 분석을 완료할 수 없습니다.",
        }

    return result


def _analyze_speech_rate(text: str, duration: float) -> Dict[str, Any]:
    """말 속도 분석"""
    if not text or duration <= 0:
        return {
            "wpm": 0,
            "syllables_per_sec": 0,
            "rating": "분석불가",
            "feedback": "텍스트 또는 오디오 정보가 부족합니다.",
        }

    words = text.split()
    word_count = len(words)

    # 한글 음절 수 계산
    syllable_count = sum(1 for char in text if '가' <= char <= '힣')
    syllable_count += len(re.findall(r'[a-zA-Z]+', text))  # 영어 단어도 대략 카운트

    minutes = duration / 60.0
    wpm = word_count / minutes if minutes > 0 else 0
    sps = syllable_count / duration if duration > 0 else 0

    # 면접 적정 말 속도: 분당 120-150 단어 (한국어 기준 초당 3-4 음절)
    if wpm < 80 or sps < 2.5:
        rating = "느림"
        feedback = "말 속도가 다소 느립니다. 자연스러운 속도로 말해보세요."
    elif wpm > 180 or sps > 5.0:
        rating = "빠름"
        feedback = "말 속도가 빠릅니다. 면접관이 이해하기 어려울 수 있으니 천천히 말해보세요."
    else:
        rating = "적절"
        feedback = "말 속도가 적절합니다. 이 페이스를 유지하세요."

    return {
        "wpm": round(wpm, 1),
        "syllables_per_sec": round(sps, 2),
        "rating": rating,
        "feedback": feedback,
    }


def _analyze_filler_words(text: str) -> Dict[str, Any]:
    """필러 단어 분석"""
    if not text:
        return {
            "total_count": 0,
            "filler_ratio": 0,
            "details": [],
            "rating": "분석불가",
            "feedback": "텍스트가 없습니다.",
        }

    text_lower = text.lower()
    words = text.split()
    total_words = len(words)

    filler_counts = {}

    # 한국어 필러
    for filler in FILLER_WORDS_KO:
        count = text_lower.count(filler)
        if count > 0:
            filler_counts[filler] = count

    # 영어 필러
    for filler in FILLER_WORDS_EN:
        count = text_lower.count(filler)
        if count > 0:
            filler_counts[filler] = count

    total_fillers = sum(filler_counts.values())
    filler_ratio = total_fillers / total_words if total_words > 0 else 0

    # 상세 목록 (빈도순 정렬)
    details = [{"word": k, "count": v} for k, v in sorted(filler_counts.items(), key=lambda x: -x[1])]

    # 평가
    if filler_ratio < 0.03:
        rating = "우수"
        feedback = "필러 단어 사용이 적절합니다. 명확하게 말하고 있습니다."
    elif filler_ratio < 0.08:
        rating = "양호"
        feedback = f"필러 단어가 {total_fillers}회 감지되었습니다. 조금만 줄이면 더 좋습니다."
    else:
        rating = "개선필요"
        top_fillers = ", ".join([d["word"] for d in details[:3]])
        feedback = f"필러 단어가 많습니다({total_fillers}회). 특히 '{top_fillers}'를 줄여보세요."

    return {
        "total_count": total_fillers,
        "filler_ratio": round(filler_ratio, 3),
        "details": details[:5],  # 상위 5개
        "rating": rating,
        "feedback": feedback,
    }


def _analyze_pauses(voice_features: Dict, duration: float) -> Dict[str, Any]:
    """침묵/휴지 분석"""
    pause_ratio = voice_features.get("pause_ratio", 0.2)

    # 휴지 횟수 추정 (에너지 기반)
    total_pauses = int(pause_ratio * duration / 2)  # 대략적 추정
    long_pauses = max(0, int(total_pauses * 0.2))  # 긴 침묵 비율
    avg_pause = 0.8 if pause_ratio > 0.3 else 0.5

    if pause_ratio < 0.15:
        rating = "적음"
        feedback = "휴지가 너무 적습니다. 적절한 쉼으로 강조점을 만들어보세요."
    elif pause_ratio < 0.35:
        rating = "적절"
        feedback = "휴지 사용이 적절합니다. 자연스러운 리듬감이 있습니다."
    else:
        rating = "많음"
        if long_pauses > 2:
            feedback = f"긴 침묵이 {long_pauses}회 감지되었습니다. 준비된 답변으로 자신감 있게 말해보세요."
        else:
            feedback = "휴지가 다소 많습니다. 생각을 정리한 후 말하되, 너무 오래 멈추지 마세요."

    return {
        "total_pauses": total_pauses,
        "long_pauses": long_pauses,
        "avg_pause_duration": round(avg_pause, 2),
        "pause_ratio": round(pause_ratio, 3),
        "rating": rating,
        "feedback": feedback,
    }


def _analyze_energy_pattern(voice_features: Dict, audio_bytes: bytes) -> Dict[str, Any]:
    """에너지/톤 변화 분석"""
    try:
        import numpy as np
        import io
        import wave

        # 피치와 에너지 정보
        pitch_std = voice_features.get("pitch_std", 30)
        energy_mean = voice_features.get("energy_mean", 0.5)

        # 간단한 에너지 분석 (librosa 있으면 더 정교하게)
        try:
            import librosa

            # 오디오 로드
            audio_io = io.BytesIO(audio_bytes)
            y, sr = librosa.load(audio_io, sr=16000)

            # 3구간으로 나누기
            segment_len = len(y) // 3
            if segment_len > 0:
                start_energy = float(np.mean(np.abs(y[:segment_len])))
                mid_energy = float(np.mean(np.abs(y[segment_len:2*segment_len])))
                end_energy = float(np.mean(np.abs(y[2*segment_len:])))
            else:
                start_energy = mid_energy = end_energy = energy_mean

        except:
            # librosa 없으면 추정값
            start_energy = energy_mean * 1.1
            mid_energy = energy_mean
            end_energy = energy_mean * 0.9

        # 정규화
        max_e = max(start_energy, mid_energy, end_energy, 0.001)
        start_energy = start_energy / max_e
        mid_energy = mid_energy / max_e
        end_energy = end_energy / max_e

        # 에너지 트렌드 판단
        if end_energy > start_energy * 1.1:
            energy_trend = "상승"
            trend_feedback = "답변 마무리에 에너지가 높아져 좋은 인상을 줍니다."
        elif end_energy < start_energy * 0.8:
            energy_trend = "하락"
            trend_feedback = "답변이 끝날수록 에너지가 떨어집니다. 마무리까지 힘을 유지하세요."
        else:
            energy_trend = "유지"
            trend_feedback = "답변 전반에 걸쳐 일정한 에너지를 유지하고 있습니다."

        # 피치 변화량 (단조로움 점수)
        if pitch_std < 15:
            monotone_score = 8.0
            pitch_feedback = "목소리가 단조롭습니다. 강조점에서 톤을 높이거나 낮춰보세요."
        elif pitch_std < 30:
            monotone_score = 5.0
            pitch_feedback = "적절한 톤 변화가 있습니다."
        else:
            monotone_score = 2.0
            pitch_feedback = "다양한 톤으로 말하고 있어 생동감이 있습니다."

        feedback = f"{trend_feedback} {pitch_feedback}"

        # 에너지 점수 계산 (트렌드 + 단조로움 기반)
        trend_score = 80 if energy_trend == "상승" else (70 if energy_trend == "유지" else 50)
        monotone_penalty = monotone_score * 3  # 단조로움 점수가 높을수록 감점
        energy_score = max(0, min(100, trend_score - monotone_penalty + 30))

        return {
            "start_energy": round(start_energy, 2),
            "mid_energy": round(mid_energy, 2),
            "end_energy": round(end_energy, 2),
            "energy_trend": energy_trend,
            "pitch_variation": round(pitch_std, 1),
            "monotone_score": monotone_score,
            "energy_score": round(energy_score, 1),
            "feedback": feedback,
        }

    except Exception as e:
        logger.warning(f"에너지 분석 오류: {e}")
        return {
            "start_energy": 0.5,
            "mid_energy": 0.5,
            "end_energy": 0.5,
            "energy_trend": "유지",
            "pitch_variation": 30,
            "monotone_score": 5.0,
            "energy_score": 70.0,
            "feedback": "에너지 패턴 분석 중 오류가 발생했습니다.",
        }


def _analyze_pronunciation(text: str, voice_features: Dict) -> Dict[str, Any]:
    """발음 명확도 분석"""
    if not text:
        return {
            "clarity_score": 50.0,
            "feedback": "텍스트가 인식되지 않았습니다.",
        }

    # 단어 수 기반 추정 (STT 인식 품질)
    word_count = len(text.split())

    # 짧은 문장이면 명확도 추정 어려움
    if word_count < 5:
        return {
            "clarity_score": 60.0,
            "feedback": "답변이 너무 짧아 발음 분석이 어렵습니다.",
        }

    # jitter/shimmer 기반 명확도 추정
    jitter = voice_features.get("jitter", 0.02)
    shimmer = voice_features.get("shimmer", 0.03)

    # 떨림이 적을수록 명확
    clarity = 100 - (jitter * 500 + shimmer * 200)
    clarity = max(30, min(100, clarity))

    if clarity >= 80:
        feedback = "발음이 명확하고 또렷합니다."
    elif clarity >= 60:
        feedback = "발음이 대체로 좋습니다. 일부 단어를 더 또렷하게 발음하면 좋겠습니다."
    else:
        feedback = "발음이 불명확한 부분이 있습니다. 입을 더 크게 벌리고 천천히 말해보세요."

    return {
        "clarity_score": round(clarity, 1),
        "feedback": feedback,
    }


def _analyze_answer_structure(text: str) -> Dict[str, Any]:
    """답변 구조 분석 (STAR 기법)"""
    if not text or len(text) < 50:
        return {
            "has_intro": False,
            "has_body": False,
            "has_conclusion": False,
            "star_score": 0,
            "feedback": "답변이 너무 짧아 구조 분석이 어렵습니다.",
        }

    text_lower = text.lower()

    # 도입부 패턴
    intro_patterns = ["저는", "제가", "먼저", "처음에", "~때", "경험", "있습니다", "있었습니다"]
    has_intro = any(p in text_lower for p in intro_patterns)

    # 본론 패턴 (구체적 행동/상황)
    body_patterns = ["그래서", "따라서", "이때", "그 결과", "했습니다", "했고", "진행", "수행", "해결"]
    has_body = any(p in text_lower for p in body_patterns)

    # 결론 패턴
    conclusion_patterns = ["결과적으로", "이를 통해", "배웠", "느꼈", "생각합니다", "것 같습니다", "앞으로", "계획"]
    has_conclusion = any(p in text_lower for p in conclusion_patterns)

    # STAR 점수 계산
    star_elements = {
        "situation": any(w in text_lower for w in ["상황", "때", "당시", "situation"]),
        "task": any(w in text_lower for w in ["과제", "목표", "해야", "task", "역할"]),
        "action": any(w in text_lower for w in ["했", "진행", "수행", "해결", "action", "노력"]),
        "result": any(w in text_lower for w in ["결과", "성과", "달성", "배웠", "result", "이를 통해"]),
    }

    star_score = sum(star_elements.values()) * 25  # 각 요소 25점

    # 피드백 생성
    if star_score >= 75:
        feedback = "STAR 구조가 잘 갖춰진 답변입니다. 구체적인 사례와 결과가 명확합니다."
    elif star_score >= 50:
        missing = [k for k, v in star_elements.items() if not v]
        feedback = f"답변 구조가 좋습니다. {', '.join(missing)} 요소를 보강하면 더 좋겠습니다."
    else:
        feedback = "STAR 기법을 활용해보세요: 상황(S) → 과제(T) → 행동(A) → 결과(R) 순으로 구성하세요."

    return {
        "has_intro": has_intro,
        "has_body": has_body,
        "has_conclusion": has_conclusion,
        "star_score": star_score,
        "star_elements": star_elements,
        "feedback": feedback,
    }


def _calculate_overall_score(result: Dict) -> Dict[str, Any]:
    """종합 점수 및 피드백 계산"""
    scores = []
    strengths = []
    improvements = []

    # 감정 분석 점수
    emotion = result.get("emotion", {})
    confidence = emotion.get("confidence_score", 5)
    stress = emotion.get("stress_level", 5)
    engagement = emotion.get("engagement_level", 5)
    stability = emotion.get("emotion_stability", 5)

    emotion_score = (confidence * 10 + (10 - stress) * 10 + engagement * 5 + stability * 5) / 3
    scores.append(("감정", emotion_score))

    if confidence >= 7:
        strengths.append("자신감 있는 목소리")
    elif confidence < 4:
        improvements.append("답변 시 더 확신 있게 말하기")

    if stress > 7:
        improvements.append("긴장을 풀고 편안하게 말하기")

    # 말 속도 점수
    speech = result.get("speech_rate", {})
    if speech.get("rating") == "적절":
        scores.append(("말속도", 90))
        strengths.append("적절한 말 속도")
    elif speech.get("rating") == "빠름":
        scores.append(("말속도", 60))
        improvements.append("말 속도 줄이기")
    elif speech.get("rating") == "느림":
        scores.append(("말속도", 65))
        improvements.append("말 속도 높이기")
    else:
        scores.append(("말속도", 70))

    # 필러 단어 점수
    filler = result.get("filler_analysis", {})
    if filler.get("rating") == "우수":
        scores.append(("필러", 95))
        strengths.append("명확한 화법")
    elif filler.get("rating") == "양호":
        scores.append(("필러", 75))
    else:
        filler_count = filler.get("total_count", 0)
        scores.append(("필러", max(40, 80 - filler_count * 3)))
        if filler_count > 5:
            improvements.append(f"필러 단어 줄이기 ({filler_count}회 감지)")

    # 휴지 분석 점수
    pause = result.get("pause_analysis", {})
    if pause.get("rating") == "적절":
        scores.append(("휴지", 85))
        strengths.append("자연스러운 리듬")
    elif pause.get("rating") == "많음":
        scores.append(("휴지", 60))
        improvements.append("긴 침묵 줄이기")
    else:
        scores.append(("휴지", 70))

    # 에너지 분석 점수
    energy = result.get("energy_analysis", {})
    monotone = energy.get("monotone_score", 5)
    if monotone <= 3:
        scores.append(("톤변화", 90))
        strengths.append("생동감 있는 톤")
    elif monotone >= 7:
        scores.append(("톤변화", 55))
        improvements.append("톤에 변화 주기")
    else:
        scores.append(("톤변화", 75))

    if energy.get("energy_trend") == "하락":
        improvements.append("마무리까지 에너지 유지하기")

    # 발음 명확도
    pron = result.get("pronunciation", {})
    clarity = pron.get("clarity_score", 70)
    scores.append(("발음", clarity))
    if clarity >= 80:
        strengths.append("또렷한 발음")
    elif clarity < 60:
        improvements.append("발음 명확하게 하기")

    # 답변 구조 점수
    structure = result.get("structure_analysis", {})
    star = structure.get("star_score", 50)
    scores.append(("구조", star))
    if star >= 75:
        strengths.append("체계적인 답변 구조")
    elif star < 50:
        improvements.append("STAR 기법 활용하기")

    # 종합 점수 계산 (가중 평균)
    weights = {"감정": 2.0, "말속도": 1.5, "필러": 1.5, "휴지": 1.0, "톤변화": 1.5, "발음": 1.5, "구조": 2.0}
    total_weight = sum(weights.get(name, 1.0) for name, _ in scores)
    weighted_sum = sum(score * weights.get(name, 1.0) for name, score in scores)
    overall_score = weighted_sum / total_weight if total_weight > 0 else 50

    # 상세 피드백 생성
    if overall_score >= 85:
        grade = "우수"
        detailed = "전반적으로 훌륭한 음성 전달력입니다. 자신감 있고 명확한 화법이 인상적입니다."
    elif overall_score >= 70:
        grade = "양호"
        detailed = "좋은 음성 전달력입니다. 일부 개선점을 보완하면 더욱 좋아질 것입니다."
    elif overall_score >= 55:
        grade = "보통"
        detailed = "기본적인 전달력은 있으나 개선이 필요합니다. 연습을 통해 충분히 향상될 수 있습니다."
    else:
        grade = "개선필요"
        detailed = "음성 전달력 향상이 필요합니다. 아래 개선점을 참고하여 연습해보세요."

    return {
        "voice_score": round(overall_score, 1),
        "grade": grade,
        "score_breakdown": {name: round(score, 1) for name, score in scores},
        "strengths": strengths[:3] if strengths else ["분석 완료"],
        "improvements": improvements[:4] if improvements else ["현재 상태 유지"],
        "detailed_feedback": detailed,
    }


# =====================================================
# TTS 테스트 함수
# =====================================================
def test_edge_tts():
    """Edge TTS 테스트"""
    test_text = "안녕하세요, 저는 마이크로소프트 Edge TTS입니다. 자연스러운 한국어 음성을 무료로 들려드립니다."

    print("=== Edge TTS 테스트 ===")
    print(f"Edge TTS 사용 가능: {is_edge_tts_available()}")

    if not is_edge_tts_available():
        print("edge-tts 패키지를 설치하세요: pip install edge-tts")
        return

    # 각 음성 테스트
    for voice_id, voice_info in EDGE_TTS_VOICES.items():
        print(f"\n테스트 음성: {voice_info['name']} ({voice_id})")
        audio = generate_edge_tts(test_text, voice=voice_id)
        if audio:
            filename = f"test_{voice_id}.mp3"
            with open(filename, "wb") as f:
                f.write(audio)
            print(f"저장 완료: {filename} ({len(audio)} bytes)")
        else:
            print("실패")


def test_google_tts():
    """Google TTS 테스트"""
    test_text = "안녕하세요, 저는 구글 클라우드 TTS입니다. 자연스러운 한국어 음성을 들려드립니다."

    print("=== Google TTS 테스트 ===")
    print(f"API 키 설정: {is_google_tts_available()}")

    if not is_google_tts_available():
        print("Google API 키가 설정되지 않았습니다.")
        print("환경변수 GOOGLE_TTS_API_KEY를 설정하세요.")
        return

    # Neural2 테스트
    for voice in ["ko-KR-Neural2-A", "ko-KR-Neural2-C"]:
        print(f"\n테스트 음성: {voice}")
        audio = generate_google_tts(test_text, voice_name=voice)
        if audio:
            filename = f"test_{voice}.mp3"
            with open(filename, "wb") as f:
                f.write(audio)
            print(f"저장 완료: {filename}")
        else:
            print("실패")


if __name__ == "__main__":
    test_edge_tts()
