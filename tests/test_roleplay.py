# test_roleplay.py - 롤플레잉 기능 테스트 (클로바 TTS 포함)

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("롤플레잉 기능 테스트")
print("=" * 50)

# 1. API 키 확인
openai_key = os.getenv('OPENAI_API_KEY', '')
clova_id = os.getenv('CLOVA_CLIENT_ID', '') or os.getenv('NCP_CLIENT_ID', '')
clova_secret = os.getenv('CLOVA_CLIENT_SECRET', '') or os.getenv('NCP_CLIENT_SECRET', '')

print(f"\n1. API Key 확인")
print(f"   OpenAI API Key: {'있음' if openai_key else '없음'}")
print(f"   CLOVA Client ID: {'있음' if clova_id else '없음'}")
print(f"   CLOVA Client Secret: {'있음' if clova_secret else '없음'}")

# 2. 클로바 사용 가능 여부
from voice_utils import is_clova_available, get_clova_speaker_for_persona, CLOVA_SPEAKERS

print(f"\n2. 클로바 TTS 사용 가능: {'예' if is_clova_available() else '아니오 (OpenAI 사용)'}")

# 3. 클로바 스피커 매핑 테스트
print("\n3. 클로바 스피커 매핑 테스트")
test_personas = [
    ('50대 여성, 해외여행이 처음', 0, '50대 여성 (평상시)'),
    ('50대 여성, 해외여행이 처음', 2, '50대 여성 (화남)'),
    ('60대 할머니', 0, '60대 할머니 (평상시)'),
    ('60대 할머니', 2, '60대 할머니 (화남)'),
    ('40대 아줌마', 1, '40대 아줌마 (짜증)'),
    ('40대 사업가 남성', 0, '40대 사업가 남성'),
    ('30대 직장인 여성', 0, '30대 직장인 여성'),
    ('20대 대학생', 0, '20대 대학생'),
]

for persona, level, desc in test_personas:
    speaker, speed, emotion = get_clova_speaker_for_persona(persona, level)
    speaker_info = CLOVA_SPEAKERS.get(speaker, {})
    print(f"   {desc}: speaker={speaker} ({speaker_info.get('name', '?')}), speed={speed}, emotion={emotion}")

# 4. TTS 생성 테스트
print("\n4. TTS 생성 테스트")
if is_clova_available():
    print("   클로바 TTS 테스트 중...")
    from voice_utils import generate_clova_tts

    test_text = "저기요, 창가 자리로 바꿔주실 수 있나요?"
    audio = generate_clova_tts(test_text, speaker="nsunhee", speed=0, emotion=0)

    if audio:
        print(f"   클로바 TTS 성공! (bytes={len(audio)})")
    else:
        print("   클로바 TTS 실패")
else:
    print("   클로바 API 키가 없어서 클로바 테스트 스킵")

if openai_key:
    print("   OpenAI TTS 테스트 중...")
    from voice_utils import generate_tts_audio

    test_text = "저기요, 창가 자리로 바꿔주실 수 있나요?"
    audio = generate_tts_audio(test_text, voice="shimmer", speed=1.0, use_clova=False)

    if audio:
        print(f"   OpenAI TTS 성공! (bytes={len(audio)})")
    else:
        print("   OpenAI TTS 실패")
else:
    print("   OpenAI API 키가 없어서 OpenAI TTS 테스트 스킵")

# 5. 통합 TTS 함수 테스트
print("\n5. 통합 TTS 함수 테스트 (generate_tts_for_passenger)")
if openai_key or is_clova_available():
    from voice_utils import generate_tts_for_passenger

    test_text = "아니 이게 뭐예요! 창가 자리 하나 못 바꿔줘요?"
    audio = generate_tts_for_passenger(
        text=test_text,
        persona="50대 여성, 해외여행이 처음",
        escalation_level=2  # 화남
    )

    if audio:
        print(f"   통합 TTS 성공! (bytes={len(audio)})")
        print(f"   사용된 TTS: {'클로바' if is_clova_available() else 'OpenAI'}")
    else:
        print("   통합 TTS 실패")
else:
    print("   API 키가 없어서 통합 TTS 테스트 스킵")

print("\n" + "=" * 50)
print("테스트 완료!")
print("=" * 50)

# 클로바 설정 안내
if not is_clova_available():
    print("\n[클로바 TTS 설정 방법]")
    print("1. 네이버 클라우드 플랫폼 가입: https://www.ncloud.com")
    print("2. AI Services > CLOVA Voice 신청")
    print("3. Application 등록 후 API Key 발급")
    print("4. 환경변수 설정:")
    print("   set CLOVA_CLIENT_ID=your_client_id")
    print("   set CLOVA_CLIENT_SECRET=your_client_secret")
