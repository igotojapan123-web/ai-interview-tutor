# pages/26_기내방송연습.py
# 기내방송 연습 - 스크립트 확장 + 쉐도잉 + TTS + 대시보드 + 속도코치

import streamlit as st
import os
import sys
import json
import re
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page

init_page(
    title="기내방송 연습",
    current_page="기내방송연습",
    wide_layout=True
)


# ========================================
# OpenAI API (캐시된 싱글톤)
# ========================================
@st.cache_resource
def get_openai_client():
    """OpenAI 클라이언트 싱글톤 (앱 재시작 전까지 재사용)"""
    try:
        from openai import OpenAI
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        return None

client = get_openai_client()
API_AVAILABLE = client is not None

# ========================================
# 데이터 관리
# ========================================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
PRACTICE_FILE = os.path.join(DATA_DIR, "announcement_practice.json")


@st.cache_data(ttl=60)
def load_practice():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(PRACTICE_FILE):
            with open(PRACTICE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def save_practice(data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PRACTICE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        load_practice.clear()  # 캐시 무효화
    except Exception:
        pass


def transcribe_audio(audio_bytes, language="ko"):
    if not API_AVAILABLE:
        return None
    try:
        temp_path = os.path.join(DATA_DIR, "temp_audio.wav")
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        with open(temp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
        os.remove(temp_path)
        return transcript.text
    except Exception as e:
        return f"오류: {str(e)}"


def analyze_announcement(original_script, user_transcript, language, ann_type):
    if not API_AVAILABLE:
        return None
    system_prompt = f"""당신은 10년 경력의 항공사 객실승무원 트레이너입니다.
기내방송 연습을 분석하고 피드백을 제공합니다.

방송 종류: {ann_type}
언어: {language}

평가 기준:
1. 정확성 (스크립트 일치도)
2. 발음 명확성 (음성인식 결과 기준)
3. 누락 여부 (빠뜨린 핵심 내용)
4. 자연스러움 (기내방송 느낌)

피드백 형식:
##  종합 점수: X/100점

##  잘한 점
- (구체적으로 2~3개)

##  개선할 점
- (구체적으로 2~3개)

##  핵심 누락 체크
- (놓친 내용이 있으면)

##  발음/톤 팁
- (구체적 조언 2개)
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"원본 스크립트:\n{original_script}\n\n사용자 낭독 (음성인식 결과):\n{user_transcript}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"분석 오류: {str(e)}"


def generate_tts(text, voice="nova"):
    if not API_AVAILABLE:
        return None
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        return response.content
    except Exception as e:
        return None


# ========================================
# 스크립트 데이터 (15개, 난이도별)
# ========================================
ANNOUNCEMENTS = {
    # === 초급 (기본 방송) ===
    "탑승 환영": {
        "level": "초급",
        "category": "기본",
        "target_time_kr": 35,
        "target_time_en": 30,
        "korean": """안녕하십니까, 고객 여러분.
대한항공 KE001편에 탑승해 주셔서 감사합니다.
본 항공편은 인천에서 뉴욕까지 운항하며,
예정 비행시간은 약 14시간입니다.

좌석 상단의 선반에 짐을 넣으실 때는
다른 승객분들을 배려하여 한 칸씩만 사용해 주시기 바랍니다.
잠시 후 안전에 관한 안내방송이 있겠습니다.
편안한 여행 되시기 바랍니다. 감사합니다.""",
        "english": """Good morning, ladies and gentlemen.
Welcome aboard Korean Air flight KE001,
with service from Incheon to New York.
Our flight time will be approximately 14 hours.

Please store your carry-on items in the overhead bin
or under the seat in front of you.
Shortly, we will be showing our safety demonstration.
Thank you for flying with us today.""",
        "tips": ["밝고 따뜻한 톤으로", "적절한 속도 (너무 빠르지 않게)", "숫자는 또박또박", "미소 띤 목소리"],
        "key_points": ["환영 인사", "편명/목적지", "비행시간", "짐 정리 안내"],
        "pronunciation_kr": {"탑승해": "탑-승-해 또박또박", "비행시간": "비-행-시-간 천천히"},
        "pronunciation_en": {"approximately": "uh-PROK-suh-muht-lee", "overhead": "OH-ver-hed"},
    },

    "안전 안내": {
        "level": "초급",
        "category": "안전",
        "target_time_kr": 40,
        "target_time_en": 35,
        "korean": """고객 여러분, 잠시 안전에 관한 안내 말씀 드리겠습니다.

좌석벨트는 비행 중 항상 착용해 주시고,
벨트 사인이 켜지면 좌석에 앉아 주시기 바랍니다.

비상구는 기내 앞쪽과 뒤쪽, 그리고 날개 위에 있으며,
좌석 앞 주머니에 있는 안전 카드를 참고해 주시기 바랍니다.

화장실 내 흡연은 법으로 금지되어 있습니다.
안전한 여행을 위해 협조해 주셔서 감사합니다.""",
        "english": """Ladies and gentlemen, may I have your attention please.

Please keep your seatbelt fastened at all times while seated.
When the seatbelt sign is on, please return to your seat.

Emergency exits are located at the front and rear of the cabin,
as well as over the wings.
Please take a moment to review the safety card
in the seat pocket in front of you.

Smoking is prohibited in the lavatories.
Thank you for your attention.""",
        "tips": ["명확하고 차분하게", "중요한 부분 강조", "적절한 포즈 (쉼)", "안전 관련은 진지하게"],
        "key_points": ["좌석벨트", "비상구 위치", "안전 카드", "흡연 금지"],
        "pronunciation_kr": {"비상구": "비-상-구 강조", "착용": "차-겅 (X) → 착-용 (O)"},
        "pronunciation_en": {"lavatories": "LAV-uh-tor-eez", "prohibited": "proh-HIB-ih-tid"},
    },

    "이륙 전": {
        "level": "초급",
        "category": "기본",
        "target_time_kr": 30,
        "target_time_en": 28,
        "korean": """고객 여러분, 곧 이륙하겠습니다.

좌석 테이블과 등받이를 원위치해 주시고,
좌석벨트를 착용해 주시기 바랍니다.
휴대전화를 포함한 모든 전자기기는
비행기 모드로 전환하거나 전원을 꺼 주시기 바랍니다.

창문 덮개는 열어 주시기 바랍니다.
협조해 주셔서 감사합니다.""",
        "english": """Ladies and gentlemen, we will be taking off shortly.

Please make sure your seat back is upright,
your tray table is stowed,
and your seatbelt is securely fastened.

All electronic devices, including mobile phones,
must be switched to airplane mode or turned off.

Please open your window shades.
Thank you for your cooperation.""",
        "tips": ["단호하지만 친절하게", "각 항목 끊어 읽기", "적절한 속도 유지"],
        "key_points": ["테이블/등받이", "좌석벨트", "전자기기", "창문 덮개"],
        "pronunciation_kr": {"원위치": "원-위-치 또박또박", "전환": "전-환"},
        "pronunciation_en": {"securely": "sih-KYOOR-lee", "cooperation": "koh-op-er-AY-shun"},
    },

    # === 중급 ===
    "식음료 서비스": {
        "level": "중급",
        "category": "서비스",
        "target_time_kr": 35,
        "target_time_en": 30,
        "korean": """고객 여러분, 잠시 후 식음료 서비스를 시작하겠습니다.

오늘 준비된 음료는 커피, 차, 주스, 그리고 생수가 있습니다.
식사로는 불고기 덮밥과 해산물 파스타를 준비했습니다.

서비스 중에는 좌석벨트를 착용한 상태로
좌석에 앉아 계시기 바랍니다.
서비스 카트가 지나갈 때 통로 쪽으로
몸이나 손을 내밀지 않도록 주의해 주십시오.

감사합니다.""",
        "english": """Ladies and gentlemen,
we will now begin our in-flight service.

Today we have coffee, tea, juice, and water available.
For your meal, we are serving Bulgogi rice bowl and Seafood pasta.

Please remain seated with your seatbelt fastened
during the service.
Please be careful not to extend your arms or legs
into the aisle as the cart passes.

Thank you.""",
        "tips": ["메뉴 설명은 천천히", "서비스 안내 시 미소", "감사 인사 진심으로"],
        "key_points": ["음료 종류", "기내식 메뉴", "안전 안내", "통로 주의"],
        "pronunciation_kr": {"해산물": "해-산-물 명확히", "내밀지": "내-밀-지"},
        "pronunciation_en": {"Bulgogi": "Bool-GO-gee", "aisle": "AYL (s 묵음)"},
    },

    "착륙 전": {
        "level": "중급",
        "category": "기본",
        "target_time_kr": 40,
        "target_time_en": 35,
        "korean": """고객 여러분, 곧 뉴욕 JFK 공항에 착륙하겠습니다.
현재 뉴욕의 기온은 섭씨 15도이며,
현지 시각은 오후 3시입니다.

좌석벨트를 착용하시고,
좌석 테이블과 등받이를 원위치해 주시기 바랍니다.
휴대전화와 전자기기는 비행기 모드를 유지해 주시고,
착륙 후 벨트 사인이 꺼질 때까지
좌석에 앉아 계시기 바랍니다.

대한항공을 이용해 주셔서 감사합니다.""",
        "english": """Ladies and gentlemen,
we will be landing at New York JFK Airport shortly.
The current temperature is 15 degrees Celsius,
and the local time is 3 PM.

Please fasten your seatbelt,
stow your tray table, and return your seat to the upright position.

Please keep your electronic devices in airplane mode.
For your safety, please remain seated
until the seatbelt sign has been turned off.

Thank you for flying with Korean Air.""",
        "tips": ["도착지 정보 정확히", "숫자 또박또박", "감사 인사 따뜻하게"],
        "key_points": ["도착지/기온/시간", "좌석벨트/테이블", "전자기기", "착석 유지"],
        "pronunciation_kr": {"섭씨": "섭-씨 명확히", "유지해": "유-지-해"},
        "pronunciation_en": {"Celsius": "SEL-see-us", "upright": "UP-ryt"},
    },

    "착륙 후": {
        "level": "초급",
        "category": "기본",
        "target_time_kr": 35,
        "target_time_en": 30,
        "korean": """고객 여러분, 뉴욕 JFK 공항에 도착했습니다.

좌석벨트 사인이 꺼질 때까지 좌석에 앉아 계시기 바랍니다.
선반을 여실 때는 짐이 떨어질 수 있으니 주의해 주시고,
내리실 때 휴대품을 다시 한 번 확인해 주시기 바랍니다.

오늘 대한항공을 이용해 주셔서 진심으로 감사드립니다.
즐거운 하루 되시기 바랍니다.
다음에도 대한항공을 이용해 주시기 바랍니다.
감사합니다.""",
        "english": """Ladies and gentlemen,
welcome to New York JFK Airport.

Please remain seated until the seatbelt sign has been turned off.
Please use caution when opening the overhead bins,
as items may have shifted during the flight.
Please make sure to take all your personal belongings with you.

Thank you for choosing Korean Air today.
We hope you have a pleasant day,
and we look forward to seeing you again soon.
Thank you.""",
        "tips": ["환영하는 느낌으로", "감사 인사 진심을 담아", "다음 이용 권유는 밝게"],
        "key_points": ["도착 환영", "안전 주의", "소지품 확인", "감사 인사"],
        "pronunciation_kr": {"진심으로": "진-심-으-로 강조", "휴대품": "휴-대-품"},
        "pronunciation_en": {"belongings": "bih-LONG-ingz", "pleasant": "PLEZ-uhnt"},
    },

    # === 중급 (추가) ===
    "난기류 안내": {
        "level": "중급",
        "category": "안전",
        "target_time_kr": 30,
        "target_time_en": 28,
        "korean": """고객 여러분, 기장입니다.
현재 기체가 약간의 흔들림이 있을 수 있습니다.

좌석벨트 착용 사인을 켜겠습니다.
화장실 이용 중이신 분은 빠르게 좌석으로 돌아가 주시고,
좌석벨트를 단단히 착용해 주시기 바랍니다.

머리 위 선반의 짐이 떨어질 수 있으니
선반을 열지 말아 주시기 바랍니다.
흔들림이 멈추면 다시 안내 드리겠습니다.
감사합니다.""",
        "english": """Ladies and gentlemen, this is your captain speaking.
We are experiencing some turbulence.

The seatbelt sign has been turned on.
If you are in the lavatory, please return to your seat immediately
and fasten your seatbelt securely.

Please do not open the overhead bins
as items may fall out.
We will let you know when it is safe to move about.
Thank you.""",
        "tips": ["차분하지만 단호하게", "긴급감 있되 패닉은 X", "천천히 명확하게"],
        "key_points": ["벨트 사인 ON", "좌석 복귀", "선반 열지 말 것", "추후 안내 예고"],
        "pronunciation_kr": {"흔들림": "흔-들-림 차분히", "단단히": "단-단-히 강조"},
        "pronunciation_en": {"turbulence": "TUR-byuh-lunts", "immediately": "ih-MEE-dee-uht-lee"},
    },

    "면세품 안내": {
        "level": "중급",
        "category": "서비스",
        "target_time_kr": 30,
        "target_time_en": 28,
        "korean": """고객 여러분, 잠시 후 기내 면세품 판매를 시작하겠습니다.

오늘 준비된 면세품은 향수, 화장품, 주류, 담배, 기념품 등이 있습니다.
좌석 앞 주머니에 있는 면세품 카탈로그를 참고해 주시기 바랍니다.

결제는 현금 및 신용카드 모두 가능하며,
한국 원화, 미국 달러, 유로가 가능합니다.

면세품 구매를 원하시는 분은
승무원에게 말씀해 주시기 바랍니다. 감사합니다.""",
        "english": """Ladies and gentlemen,
we will shortly begin our duty-free sales service.

We have a selection of perfumes, cosmetics,
liquor, cigarettes, and souvenirs available.
Please refer to the duty-free catalog
in the seat pocket in front of you.

We accept both cash and credit cards.
Korean Won, US Dollars, and Euros are accepted.

If you wish to make a purchase,
please let a crew member know. Thank you.""",
        "tips": ["밝고 활기찬 톤", "상품명 명확히", "결제 수단 천천히"],
        "key_points": ["면세품 종류", "카탈로그 안내", "결제 수단", "구매 방법"],
        "pronunciation_kr": {"면세품": "면-세-품", "카탈로그": "카-탈-로-그"},
        "pronunciation_en": {"duty-free": "DOO-tee free", "cosmetics": "koz-MET-iks"},
    },

    "환승 안내": {
        "level": "중급",
        "category": "기본",
        "target_time_kr": 35,
        "target_time_en": 30,
        "korean": """고객 여러분, 인천공항에서 환승하시는 분들께 안내 말씀 드립니다.

환승 절차는 다음과 같습니다.
기내에서 내리신 후 환승 표지판을 따라 이동해 주시고,
보안 검색을 받으신 후 해당 탑승구로 이동해 주시기 바랍니다.

환승 시간이 촉박하신 분은
내리실 때 승무원에게 말씀해 주시면
안내해 드리겠습니다.

환승 게이트 정보는 공항 모니터에서 확인하실 수 있습니다.
감사합니다.""",
        "english": """For passengers connecting to another flight at Incheon Airport,
please note the following transfer procedures.

After deplaning, please follow the transfer signs
and proceed through security screening
to your departure gate.

If you have a tight connection,
please inform a crew member as you deplane
and we will assist you.

Connecting gate information is available on airport monitors.
Thank you.""",
        "tips": ["환승객 주의 끌기", "절차 순서대로 명확히", "도움 제공 강조"],
        "key_points": ["환승 절차", "보안 검색", "촉박한 환승", "게이트 정보"],
        "pronunciation_kr": {"환승": "환-승 강조", "촉박": "촉-박"},
        "pronunciation_en": {"deplaning": "dee-PLAYN-ing", "connection": "kuh-NEK-shun"},
    },

    "기장 인사": {
        "level": "초급",
        "category": "기본",
        "target_time_kr": 30,
        "target_time_en": 28,
        "korean": """안녕하십니까, 고객 여러분.
본 항공편의 기장 홍길동입니다.

현재 비행 고도는 약 35,000피트이며,
순조롭게 비행하고 있습니다.
목적지 뉴욕까지 남은 비행시간은 약 10시간입니다.

현재 기상 상태는 양호하며,
도착 예정 시각은 현지 시간 오후 3시입니다.

편안한 비행 되시기를 바랍니다.
감사합니다.""",
        "english": """Good afternoon, ladies and gentlemen.
This is your captain, Hong Gil-dong, speaking.

We are currently cruising at an altitude of approximately 35,000 feet,
and the flight is progressing smoothly.
Our estimated remaining flight time to New York is about 10 hours.

Weather conditions are favorable,
and we expect to arrive at approximately 3 PM local time.

We hope you enjoy the rest of your flight.
Thank you.""",
        "tips": ["차분하고 안정된 목소리", "숫자 정보 또박또박", "자신감 있게"],
        "key_points": ["기장 소개", "비행 고도", "남은 시간", "기상/도착 예정"],
        "pronunciation_kr": {"35,000피트": "삼만오천피트", "순조롭게": "순-조-롭-게"},
        "pronunciation_en": {"altitude": "AL-tih-tood", "approximately": "uh-PROK-suh-muht-lee"},
    },

    # === 고급 (긴급/특수) ===
    "지연 안내": {
        "level": "고급",
        "category": "특수",
        "target_time_kr": 35,
        "target_time_en": 30,
        "korean": """고객 여러분, 불편을 끼쳐드려 대단히 죄송합니다.

현재 공항 혼잡으로 인해 출발이 약 30분 지연되고 있습니다.
안전을 위해 잠시만 기다려 주시기 바랍니다.

기내에서 편하게 대기해 주시고,
화장실 이용은 가능합니다.
추가 안내 사항이 있으면 다시 방송 드리겠습니다.

불편을 끼쳐드려 다시 한 번 사과드립니다.
양해해 주셔서 감사합니다.""",
        "english": """Ladies and gentlemen, we sincerely apologize for the inconvenience.

Due to airport congestion, our departure will be delayed
by approximately 30 minutes.
We ask for your patience as we wait for clearance.

Please feel free to remain comfortable in your seat.
Lavatory use is permitted during this time.
We will provide an update as soon as we have more information.

Once again, we apologize for the delay.
Thank you for your understanding.""",
        "tips": ["진심으로 사과하는 톤", "이유 명확히", "편의 제공 강조", "사과 반복"],
        "key_points": ["사과", "지연 사유", "지연 시간", "편의 안내", "재사과"],
        "pronunciation_kr": {"끼쳐드려": "끼-쳐-드-려 정중히", "양해": "양-해"},
        "pronunciation_en": {"inconvenience": "in-kun-VEEN-yunts", "congestion": "kun-JES-chun"},
    },

    "의료 도움 요청": {
        "level": "고급",
        "category": "안전",
        "target_time_kr": 25,
        "target_time_en": 22,
        "korean": """고객 여러분, 안내 말씀 드리겠습니다.

기내에 의사 또는 간호사 자격이 있으신 분께서
계시면 승무원에게 알려 주시기 바랍니다.
의료 도움이 필요한 상황입니다.

협조해 주셔서 감사합니다.""",
        "english": """Ladies and gentlemen, may I have your attention please.

If there is a doctor or nurse on board,
could you please identify yourself to a crew member.
We have a passenger who requires medical assistance.

Thank you for your cooperation.""",
        "tips": ["긴급하지만 침착하게", "패닉 유발 X", "간결하고 명확하게"],
        "key_points": ["의사/간호사 호출", "승무원 알림", "의료 상황"],
        "pronunciation_kr": {"의료": "의-료 명확히"},
        "pronunciation_en": {"identify": "eye-DEN-tih-fye", "assistance": "uh-SIS-tunts"},
    },

    "비상 착륙 안내": {
        "level": "고급",
        "category": "안전",
        "target_time_kr": 40,
        "target_time_en": 35,
        "korean": """고객 여러분, 기장입니다. 안전에 관한 중요한 안내입니다.

현재 기체 점검을 위해 가까운 공항에 비상 착륙을 실시합니다.
침착하게 승무원의 안내에 따라 주시기 바랍니다.

좌석벨트를 단단히 착용해 주시고,
안경, 볼펜 등 날카로운 물건은 주머니에서 빼 주십시오.
높은 굽의 구두는 벗어 주시기 바랍니다.

비상 착륙 자세를 안내 드리겠습니다.
허리를 숙이고 양손으로 뒷목을 감싸 주십시오.
승무원의 구령에 따라 주시기 바랍니다.

침착하게 행동해 주시면 안전하게 도착할 수 있습니다.
감사합니다.""",
        "english": """Ladies and gentlemen, this is your captain.
This is an important safety announcement.

We will be making an emergency landing
at the nearest airport for a precautionary inspection.
Please remain calm and follow the crew's instructions.

Please fasten your seatbelt securely.
Remove any sharp objects such as glasses or pens from your pockets.
Please remove high-heeled shoes.

I will now explain the brace position.
Please bend forward and place your hands behind your neck.
Follow the crew's commands.

Please remain calm. We will land safely.
Thank you.""",
        "tips": ["매우 차분하고 단호하게", "패닉 방지", "안심시키면서 지시", "속도 조절 중요"],
        "key_points": ["비상착륙 사유", "침착 유지", "벨트/날카로운 물건", "비상 착륙 자세", "안심"],
        "pronunciation_kr": {"비상": "비-상 강조", "침착하게": "침-착-하-게 차분히"},
        "pronunciation_en": {"precautionary": "prih-KAW-shun-air-ee", "emergency": "ih-MUR-juhn-see"},
    },

    "기내 소등 안내": {
        "level": "초급",
        "category": "서비스",
        "target_time_kr": 20,
        "target_time_en": 18,
        "korean": """고객 여러분, 잠시 후 기내 조명을 낮추겠습니다.

편안한 휴식을 위해 창문 덮개를 내려 주시기 바랍니다.
개인 독서등은 사용하실 수 있습니다.

도움이 필요하시면 좌석 위의 호출 버튼을 눌러 주십시오.
편안한 휴식 되시기 바랍니다.""",
        "english": """Ladies and gentlemen,
we will be dimming the cabin lights shortly.

For your comfort, please lower your window shades.
Individual reading lights are available for your use.

If you need any assistance,
please press the call button above your seat.
We hope you have a restful flight.""",
        "tips": ["부드럽고 조용한 톤", "속삭이듯 천천히", "편안함 전달"],
        "key_points": ["소등 예고", "창문 덮개", "독서등", "호출 버튼"],
        "pronunciation_kr": {"조명": "조-명", "독서등": "독-서-등"},
        "pronunciation_en": {"dimming": "DIM-ing", "assistance": "uh-SIS-tunts"},
    },

    "입국서류 안내": {
        "level": "중급",
        "category": "서비스",
        "target_time_kr": 30,
        "target_time_en": 25,
        "korean": """고객 여러분, 입국 서류에 대해 안내 말씀 드리겠습니다.

미국 입국 시 세관신고서 작성이 필요합니다.
승무원이 서류를 배부해 드리겠습니다.

가족 단위로 한 장만 작성하시면 되며,
여권 번호와 체류 주소를 미리 확인해 주시기 바랍니다.
작성하실 때 검정색 볼펜을 사용해 주십시오.

도움이 필요하시면 승무원에게 말씀해 주시기 바랍니다.
감사합니다.""",
        "english": """Ladies and gentlemen,
we would like to inform you about entry documents.

A customs declaration form is required for entry into the United States.
Our crew will be distributing the forms shortly.

Only one form per family is needed.
Please have your passport number and accommodation address ready.
Please use a black ink pen when filling out the form.

If you need any help, please ask a crew member.
Thank you.""",
        "tips": ["안내하듯 친절하게", "중요 사항 강조", "서류 관련 정보 정확히"],
        "key_points": ["세관신고서", "가족 1장", "여권번호/주소", "검정 볼펜"],
        "pronunciation_kr": {"세관신고서": "세-관-신-고-서", "배부": "배-부"},
        "pronunciation_en": {"declaration": "dek-luh-RAY-shun", "distributing": "dih-STRIB-yoo-ting"},
    },
}


# ========================================
# CSS
# ========================================
st.markdown("""
<style>
.script-box { background: #f8fafc; padding: 20px; border-radius: 12px; line-height: 2.0; white-space: pre-wrap; margin: 10px 0; }
.script-kr { border-left: 4px solid #3b82f6; }
.script-en { border-left: 4px solid #10b981; }
.level-badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; margin-right: 8px; }
.level-초급 { background: #dcfce7; color: #166534; }
.level-중급 { background: #fef3c7; color: #92400e; }
.level-고급 { background: #fee2e2; color: #991b1b; }
.shadow-sentence { padding: 12px 16px; margin: 6px 0; border-radius: 10px; border: 1px solid #e5e7eb; cursor: pointer; transition: all 0.2s; }
.shadow-active { background: #667eea15; border-color: #667eea; }
.shadow-done { background: #dcfce7; border-color: #22c55e; }
.pron-card { background: #fff7ed; border: 1px solid #fdba74; border-radius: 10px; padding: 12px; margin: 5px 0; }
.stat-box { background: white; border-radius: 12px; padding: 16px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
</style>
""", unsafe_allow_html=True)


# ========================================
# 메인
# ========================================
st.title("️ 기내방송 연습")
st.markdown("실제 기내방송 스크립트로 연습하고, AI 피드백으로 실력을 키우세요!")

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
 " 스크립트 학습",
 " 녹음 연습",
 " 쉐도잉/암기",
 " 모범 음성",
 " 연습 대시보드",
])


# ========================================
# 탭1: 스크립트 학습
# ========================================
with tab1:
    st.markdown("### 기내방송 스크립트")

    # 필터
    col1, col2 = st.columns(2)
    with col1:
        filter_level = st.selectbox("난이도", ["전체", "초급", "중급", "고급"], key="filter_level")
    with col2:
        filter_cat = st.selectbox("카테고리", ["전체", "기본", "안전", "서비스", "특수"], key="filter_cat")

    # 필터 적용
    filtered_scripts = {}
    for name, data in ANNOUNCEMENTS.items():
        if filter_level != "전체" and data["level"] != filter_level:
            continue
        if filter_cat != "전체" and data["category"] != filter_cat:
            continue
        filtered_scripts[name] = data

    st.caption(f"총 {len(filtered_scripts)}개 스크립트")
    st.markdown("---")

    # 스크립트 선택
    if filtered_scripts:
        selected = st.selectbox(
            "스크립트 선택",
            list(filtered_scripts.keys()),
            format_func=lambda x: f"[{ANNOUNCEMENTS[x]['level']}] {x}",
            key="script_select"
        )

        ann = ANNOUNCEMENTS[selected]

        # 난이도/카테고리 표시
        level_colors = {"초급": "#dcfce7", "중급": "#fef3c7", "고급": "#fee2e2"}
        st.markdown(f"""
        <span class="level-badge level-{ann['level']}">{ann['level']}</span>
        <span style="color: #666;">카테고리: {ann['category']} | 한국어 {ann['target_time_kr']}초 | 영어 {ann['target_time_en']}초</span>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # 스크립트 표시
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🇰🇷 한국어")
            st.markdown(f'<div class="script-box script-kr">{ann["korean"]}</div>', unsafe_allow_html=True)
        with col2:
            st.markdown("#### 🇺🇸 English")
            st.markdown(f'<div class="script-box script-en">{ann["english"]}</div>', unsafe_allow_html=True)

        # 핵심 포인트 + 팁 + 발음
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 핵심 포인트")
            for point in ann.get("key_points", []):
                st.markdown(f" {point}")

        with col2:
            st.markdown("#### 방송 팁")
            for tip in ann.get("tips", []):
                st.info(tip)

        with col3:
            st.markdown("#### ️ 발음 주의")
            for word, guide in ann.get("pronunciation_kr", {}).items():
                st.markdown(f'<div class="pron-card">🇰🇷 <strong>{word}</strong><br><small>{guide}</small></div>', unsafe_allow_html=True)
            for word, guide in ann.get("pronunciation_en", {}).items():
                st.markdown(f'<div class="pron-card">🇺🇸 <strong>{word}</strong><br><small>{guide}</small></div>', unsafe_allow_html=True)
    else:
        st.info("해당 조건의 스크립트가 없습니다.")


# ========================================
# 탭2: 녹음 연습
# ========================================
with tab2:
    st.markdown("### 녹음 연습 + AI 피드백")

    if not API_AVAILABLE:
        st.warning("️ OpenAI API가 설정되지 않아 음성 분석 기능을 사용할 수 없습니다. 자가 평가는 가능합니다.")

    # 세션 상태 초기화
    if "ann_recorded_audio" not in st.session_state:
        st.session_state.ann_recorded_audio = None
    if "ann_analysis_result" not in st.session_state:
        st.session_state.ann_analysis_result = None
    if "ann_transcript" not in st.session_state:
        st.session_state.ann_transcript = None

    # 방송/언어 선택
    col1, col2 = st.columns(2)
    with col1:
        practice_type = st.selectbox("연습할 방송", list(ANNOUNCEMENTS.keys()), key="rec_type")
    with col2:
        practice_lang = st.radio("언어", ["한국어", "English"], horizontal=True, key="rec_lang")

    ann = ANNOUNCEMENTS[practice_type]
    script_text = ann["korean"] if practice_lang == "한국어" else ann["english"]
    target_time = ann["target_time_kr"] if practice_lang == "한국어" else ann["target_time_en"]

    # 스크립트 보기 옵션
    show_script = st.checkbox("스크립트 보면서 연습", value=True, key="show_rec_script")
    if show_script:
        lang_class = "script-kr" if practice_lang == "한국어" else "script-en"
        st.markdown(f'<div class="script-box {lang_class}" style="font-size: 15px;">{script_text}</div>', unsafe_allow_html=True)

    st.markdown(f"⏱️ **목표 시간: {target_time}초** (너무 빠르거나 느리지 않게)")

    st.markdown("---")

    # 녹음
    st.markdown("#### 🎙️ 음성 녹음")
    audio_value = st.audio_input("녹음하기", key="audio_rec")

    # 새 녹음이 있으면 세션에 저장
    if audio_value:
        st.session_state.ann_recorded_audio = audio_value.getvalue()
        st.session_state.ann_analysis_result = None  # 새 녹음 시 이전 분석 결과 초기화
        st.session_state.ann_transcript = None

    # 녹음된 오디오가 있으면 재생 버튼 표시
    if st.session_state.ann_recorded_audio:
        st.markdown("#### 🔊 녹음된 음성 듣기")
        st.audio(st.session_state.ann_recorded_audio, format="audio/wav")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ 녹음 삭제", use_container_width=True, key="delete_rec"):
                st.session_state.ann_recorded_audio = None
                st.session_state.ann_analysis_result = None
                st.session_state.ann_transcript = None
                st.rerun()
        with col2:
            analyze_clicked = st.button("🤖 AI 분석 받기", type="primary", use_container_width=True, key="analyze_btn")

        if analyze_clicked:
            if API_AVAILABLE:
                with st.spinner("음성 분석 중... (Whisper → GPT-4o-mini)"):
                    audio_bytes = st.session_state.ann_recorded_audio
                    lang_code = "ko" if practice_lang == "한국어" else "en"
                    transcript = transcribe_audio(audio_bytes, lang_code)

                    if transcript and not transcript.startswith("오류") and len(transcript.strip()) > 0:
                        st.session_state.ann_transcript = transcript

                        # AI 분석
                        feedback = analyze_announcement(script_text, transcript, practice_lang, practice_type)

                        if feedback:
                            st.session_state.ann_analysis_result = feedback

                            # 점수 추출
                            score_match = re.search(r'(\d+)/100', feedback)
                            score = int(score_match.group(1)) if score_match else None

                            # 기록 저장
                            practices = load_practice()
                            practices.append({
                                "type": practice_type,
                                "language": practice_lang,
                                "transcript": transcript,
                                "feedback": feedback,
                                "score": score,
                                "date": datetime.now().isoformat()
                            })
                            save_practice(practices)
                            st.rerun()
                        else:
                            st.error("AI 분석에 실패했습니다. 잠시 후 다시 시도해주세요.")
                    else:
                        # 음성 인식 실패 시 더 친절한 안내
                        if transcript and transcript.startswith("오류"):
                            st.error(f"음성 인식 오류: {transcript}")
                        else:
                            st.error("음성 인식에 실패했습니다. 다음 사항을 확인해주세요:")
                            st.markdown("""
                            - 🎤 마이크가 제대로 작동하는지 확인하세요
                            - 🔊 충분히 큰 목소리로 녹음하세요
                            - ⏱️ 녹음 시간이 너무 짧지 않은지 확인하세요 (최소 3초 이상)
                            - 🔄 녹음을 삭제하고 다시 시도해보세요
                            """)
            else:
                st.error("OpenAI API 키가 필요합니다.")

    # 분석 결과 표시
    if st.session_state.ann_analysis_result:
        st.markdown("---")
        st.markdown("#### 📝 음성 인식 결과")
        st.info(st.session_state.ann_transcript)

        st.markdown("---")
        st.markdown("#### 💡 AI 피드백")
        st.markdown(st.session_state.ann_analysis_result)
        st.success("✅ 연습 기록이 저장되었습니다!")

    # 자가 평가
    st.markdown("---")
    st.markdown("#### ️ 자가 평가 (녹음 없이)")

    with st.form("self_eval_form"):
        col1, col2 = st.columns(2)
        with col1:
            eval_accuracy = st.slider("정확성 (스크립트 일치)", 1, 5, 3, key="eval_acc")
            eval_tone = st.slider("목소리 톤/밝기", 1, 5, 3, key="eval_tone")
            eval_speed = st.slider("속도 적절성", 1, 5, 3, key="eval_spd")
        with col2:
            eval_clarity = st.slider("발음 명확성", 1, 5, 3, key="eval_clr")
            eval_natural = st.slider("자연스러움", 1, 5, 3, key="eval_nat")
            eval_note = st.text_input("메모", key="eval_note", placeholder="느낀 점...")

        if st.form_submit_button("기록 저장", use_container_width=True):
            total_score = int((eval_accuracy + eval_tone + eval_speed + eval_clarity + eval_natural) / 5 * 20)
            practices = load_practice()
            practices.append({
                "type": practice_type,
                "language": practice_lang,
                "self_eval": True,
                "accuracy": eval_accuracy,
                "tone": eval_tone,
                "speed": eval_speed,
                "clarity": eval_clarity,
                "natural": eval_natural,
                "score": total_score,
                "note": eval_note,
                "date": datetime.now().isoformat()
            })
            save_practice(practices)
            st.success(f"기록 저장! (자가 평가 점수: {total_score}/100)")


# ========================================
# 탭3: 쉐도잉/암기 모드
# ========================================
with tab3:
    st.markdown("### 쉐도잉 & 암기 연습")

    col1, col2 = st.columns(2)
    with col1:
        shadow_type = st.selectbox("방송 선택", list(ANNOUNCEMENTS.keys()), key="shadow_type")
    with col2:
        shadow_lang = st.radio("언어", ["한국어", "English"], horizontal=True, key="shadow_lang")

    ann = ANNOUNCEMENTS[shadow_type]
    script = ann["korean"] if shadow_lang == "한국어" else ann["english"]
    sentences = [s.strip() for s in script.replace("\n\n", "\n").split("\n") if s.strip()]

    shadow_mode = st.radio("연습 모드", ["문장별 따라읽기", "빈칸 채우기", "전체 암기 테스트"], horizontal=True, key="shadow_mode")

    st.markdown("---")

    # --- 문장별 따라읽기 ---
    if shadow_mode == "문장별 따라읽기":
        st.markdown("#### 한 문장씩 따라 읽어보세요")
        st.caption("체크하면서 한 문장씩 연습하세요. 모두 체크하면 완료!")

        checked_count = 0
        for i, sentence in enumerate(sentences):
            checked = st.checkbox(sentence, key=f"shadow_chk_{shadow_type}_{shadow_lang}_{i}")
            if checked:
                checked_count += 1

        if sentences:
            progress = checked_count / len(sentences)
            st.progress(progress, text=f"진행률: {checked_count}/{len(sentences)} ({int(progress*100)}%)")

            if checked_count == len(sentences):
                st.success("모든 문장을 완료했습니다! 이제 스크립트 없이 도전해보세요!")
                st.balloons()

    # --- 빈칸 채우기 ---
    elif shadow_mode == "빈칸 채우기":
        st.markdown("#### ️ 핵심 단어를 채워보세요")
        st.caption("밑줄 부분에 알맞은 단어를 입력하세요.")

        # 핵심 키워드 추출 (key_points 기반)
        key_words = []
        for point in ann.get("key_points", []):
            # 스크립트에서 관련 단어 찾기
            for sentence in sentences:
                words = sentence.split()
                for word in words:
                    clean_word = re.sub(r'[^\w가-힣a-zA-Z]', '', word)
                    if len(clean_word) >= 2 and clean_word not in key_words:
                        if any(kp in sentence for kp in [point]):
                            key_words.append(clean_word)
                            break
                if len(key_words) >= 6:
                    break

        # 빈칸 문제 생성 (핵심 단어 기반)
        if not key_words:
            # 기본: 긴 단어들을 빈칸으로
            all_words = []
            for s in sentences:
                for w in s.split():
                    clean = re.sub(r'[^\w가-힣a-zA-Z]', '', w)
                    if len(clean) >= 3:
                        all_words.append(clean)
            key_words = list(dict.fromkeys(all_words))[:8]

        correct_count = 0
        total_blanks = min(len(key_words), 6)

        for i, word in enumerate(key_words[:total_blanks]):
            # 힌트: 첫 글자 + ___
            hint = word[0] + "_" * (len(word) - 1)
            user_answer = st.text_input(
                f"빈칸 {i+1}: {hint} ({len(word)}글자)",
                key=f"blank_{shadow_type}_{shadow_lang}_{i}",
                placeholder="정답 입력..."
            )
            if user_answer:
                if user_answer.strip().lower() == word.lower():
                    st.success(f" 정답! ({word})")
                    correct_count += 1
                else:
                    st.error(f" 오답 (정답: {word})")

        if total_blanks > 0:
            st.markdown("---")
            if correct_count == total_blanks and all(
                st.session_state.get(f"blank_{shadow_type}_{shadow_lang}_{i}", "") for i in range(total_blanks)
            ):
                st.success(f" 모두 정답! ({correct_count}/{total_blanks})")

    # --- 전체 암기 테스트 ---
    else:
        st.markdown("#### 스크립트를 보지 않고 전체 입력하세요")
        st.caption("기억나는 만큼 전체 스크립트를 작성해보세요.")

        user_script = st.text_area(
            "스크립트 입력",
            height=200,
            placeholder="방송 스크립트를 처음부터 끝까지 작성해보세요...",
            key=f"memory_test_{shadow_type}_{shadow_lang}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("정답 확인 & 비교", use_container_width=True, key="check_memory"):
                if user_script.strip():
                    st.markdown("---")

                    # 간단 비교
                    original_chars = set(script.replace(" ", "").replace("\n", ""))
                    user_chars = set(user_script.replace(" ", "").replace("\n", ""))
                    overlap = len(original_chars & user_chars) / max(len(original_chars), 1)

                    # 문장 매칭
                    user_sentences = [s.strip() for s in user_script.split("\n") if s.strip()]
                    matched = 0
                    for us in user_sentences:
                        for os_s in sentences:
                            if us.strip()[:10] in os_s:
                                matched += 1
                                break
                    sentence_match = matched / max(len(sentences), 1)

                    score = int((overlap * 0.4 + sentence_match * 0.6) * 100)

                    st.markdown(f"**암기 점수: {score}/100점** (문장 매칭 {int(sentence_match*100)}%)")

                    if score >= 80:
                        st.success("훌륭합니다! 거의 완벽하게 암기했어요!")
                    elif score >= 50:
                        st.info("절반 이상 기억하고 있어요! 조금 더 연습하면 완벽!")
                    else:
                        st.warning("아직 연습이 필요해요. 스크립트를 더 읽어보세요!")

        with col2:
            if st.button("정답 스크립트 보기", use_container_width=True, key="show_answer"):
                lang_class = "script-kr" if shadow_lang == "한국어" else "script-en"
                st.markdown(f'<div class="script-box {lang_class}">{script}</div>', unsafe_allow_html=True)


# ========================================
# 탭4: 모범 음성 (TTS)
# ========================================
with tab4:
    st.markdown("### 모범 음성 듣기")

    if not API_AVAILABLE:
        st.warning("️ OpenAI API가 필요합니다. API가 설정되면 모범 음성을 생성할 수 있습니다.")

    col1, col2 = st.columns(2)
    with col1:
        tts_type = st.selectbox("방송 선택", list(ANNOUNCEMENTS.keys()), key="tts_type")
    with col2:
        tts_lang = st.radio("언어", ["한국어", "English"], horizontal=True, key="tts_lang")

    ann = ANNOUNCEMENTS[tts_type]
    tts_script = ann["korean"] if tts_lang == "한국어" else ann["english"]

    # 음성 스타일 선택
    st.markdown("---")
    st.markdown("#### 음성 설정")

    # 음성 스타일 (세련된 한국어 이름)
    voice_options = {
        "서연 (여성, 따뜻한 톤)": "nova",
        "민지 (여성, 차분한 톤)": "alloy",
        "하늘 (여성, 밝은 톤)": "shimmer",
        "준혁 (남성, 중후한 톤)": "onyx",
    }

    col1, col2 = st.columns(2)
    with col1:
        voice_option = st.selectbox(
            "목소리 스타일",
            list(voice_options.keys()),
            key="voice_style"
        )
        voice_name = voice_options[voice_option]
    with col2:
        target_time = ann["target_time_kr"] if tts_lang == "한국어" else ann["target_time_en"]
        st.info(f"⏱️ 이 방송의 목표 시간: **{target_time}초**")

    # 스크립트 표시
    lang_class = "script-kr" if tts_lang == "한국어" else "script-en"
    st.markdown(f'<div class="script-box {lang_class}" style="font-size: 14px;">{tts_script}</div>', unsafe_allow_html=True)

    # TTS 생성
    st.markdown("---")
    if API_AVAILABLE:
        if st.button("모범 음성 생성", type="primary", use_container_width=True, key="gen_tts"):
            with st.spinner("음성 생성 중... (OpenAI TTS)"):
                audio_data = generate_tts(tts_script, voice_name)
                if audio_data:
                    st.session_state.tts_audio = audio_data
                    st.success("음성이 생성되었습니다! 아래에서 들어보세요.")
                else:
                    st.error("음성 생성에 실패했습니다.")

        if "tts_audio" in st.session_state:
            st.markdown("#### 모범 음성 재생")
            st.audio(st.session_state.tts_audio, format="audio/mp3")

            st.markdown("---")
            st.markdown("#### 비교 연습")
            st.info("위 모범 음성을 듣고, 아래에서 직접 녹음하여 비교해보세요!")

            compare_audio = st.audio_input("내 녹음", key="compare_rec")
            if compare_audio:
                st.markdown("**내 녹음:**")
                st.audio(compare_audio)
                st.caption("모범 음성과 비교하며 톤, 속도, 발음을 맞춰보세요!")
    else:
        st.info("API 키를 설정하면 모범 음성을 생성하고 비교할 수 있습니다.")

    # 발음 가이드
    st.markdown("---")
    st.markdown("#### ️ 발음 가이드")

    pron_data = ann.get("pronunciation_kr" if tts_lang == "한국어" else "pronunciation_en", {})
    if pron_data:
        for word, guide in pron_data.items():
            st.markdown(f'<div class="pron-card"> <strong>{word}</strong> → {guide}</div>', unsafe_allow_html=True)
    else:
        st.caption("이 스크립트에 대한 발음 가이드가 없습니다.")


# ========================================
# 탭5: 연습 대시보드
# ========================================
with tab5:
    st.markdown("### 연습 대시보드")

    practices = load_practice()

    if not practices:
        st.info("아직 연습 기록이 없습니다. '녹음 연습' 또는 '쉐도잉' 탭에서 연습을 시작해보세요!")
    else:
        # 상단 메트릭
        total_practices = len(practices)
        ai_practices = len([p for p in practices if p.get("transcript")])
        self_practices = len([p for p in practices if p.get("self_eval")])
        scores = [p.get("score") for p in practices if p.get("score")]
        avg_score = int(sum(scores) / len(scores)) if scores else 0
        latest_score = scores[-1] if scores else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(f"""<div class="stat-box"><div style="font-size: 24px;">️</div>
            <div style="font-size: 22px; font-weight: bold;">{total_practices}</div>
            <div style="font-size: 12px; color: #666;">총 연습</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="stat-box"><div style="font-size: 24px;"></div>
            <div style="font-size: 22px; font-weight: bold;">{ai_practices}</div>
            <div style="font-size: 12px; color: #666;">AI 분석</div></div>""", unsafe_allow_html=True)
        with col3:
            kr_count = len([p for p in practices if p.get("language") == "한국어"])
            st.markdown(f"""<div class="stat-box"><div style="font-size: 24px;">🇰🇷</div>
            <div style="font-size: 22px; font-weight: bold;">{kr_count}</div>
            <div style="font-size: 12px; color: #666;">한국어</div></div>""", unsafe_allow_html=True)
        with col4:
            en_count = len([p for p in practices if p.get("language") == "English"])
            st.markdown(f"""<div class="stat-box"><div style="font-size: 24px;">🇺🇸</div>
            <div style="font-size: 22px; font-weight: bold;">{en_count}</div>
            <div style="font-size: 12px; color: #666;">영어</div></div>""", unsafe_allow_html=True)
        with col5:
            st.markdown(f"""<div class="stat-box"><div style="font-size: 24px;"></div>
            <div style="font-size: 22px; font-weight: bold;">{avg_score}</div>
            <div style="font-size: 12px; color: #666;">평균 점수</div></div>""", unsafe_allow_html=True)

        st.markdown("---")

        # 점수 추이 그래프
        if len(scores) >= 2:
            st.markdown("#### 점수 추이")
            import pandas as pd
            score_data = []
            for p in practices:
                if p.get("score"):
                    score_data.append({
                        "날짜": p.get("date", "")[:10],
                        "점수": p["score"]
                    })
            if score_data:
                df = pd.DataFrame(score_data)
                st.line_chart(df.set_index("날짜"), height=200)

        # 스크립트별 연습 현황
        st.markdown("---")
        st.markdown("#### 스크립트별 연습 현황")

        script_stats = {}
        for p in practices:
            t = p.get("type", "기타")
            if t not in script_stats:
                script_stats[t] = {"count": 0, "scores": [], "last_date": ""}
            script_stats[t]["count"] += 1
            if p.get("score"):
                script_stats[t]["scores"].append(p["score"])
            if p.get("date", "") > script_stats[t]["last_date"]:
                script_stats[t]["last_date"] = p.get("date", "")

        # 미연습 스크립트 찾기
        practiced_types = set(script_stats.keys())
        all_types = set(ANNOUNCEMENTS.keys())
        unpracticed = all_types - practiced_types

        cols = st.columns(3)
        for i, (script_name, stats) in enumerate(sorted(script_stats.items(), key=lambda x: x[1]["count"], reverse=True)):
            with cols[i % 3]:
                avg = int(sum(stats["scores"]) / len(stats["scores"])) if stats["scores"] else 0
                score_color = "#22c55e" if avg >= 80 else "#f59e0b" if avg >= 60 else "#dc3545"
                st.markdown(f"""
                <div style="background: #f8f9fa; border-radius: 10px; padding: 12px; margin: 5px 0; border-left: 3px solid {score_color};">
                    <strong>{script_name}</strong><br>
                    <small>연습 {stats['count']}회 | 평균 {avg}점 | 최근 {stats['last_date'][:10]}</small>
                </div>
                """, unsafe_allow_html=True)

        # 추천
        st.markdown("---")
        st.markdown("#### 연습 추천")

        if unpracticed:
            st.warning(f"️ **아직 연습하지 않은 스크립트 ({len(unpracticed)}개):** {', '.join(unpracticed)}")

        # 가장 점수 낮은 스크립트
        weak_scripts = [(name, stats) for name, stats in script_stats.items() if stats["scores"]]
        weak_scripts.sort(key=lambda x: sum(x[1]["scores"]) / len(x[1]["scores"]))

        if weak_scripts:
            weakest = weak_scripts[0]
            weakest_avg = int(sum(weakest[1]["scores"]) / len(weakest[1]["scores"]))
            if weakest_avg < 80:
                st.info(f" **가장 약한 스크립트:** {weakest[0]} (평균 {weakest_avg}점) - 이것부터 연습하세요!")

        # 연습 비율 (한국어 vs 영어)
        if kr_count + en_count > 0:
            kr_ratio = kr_count / (kr_count + en_count)
            if kr_ratio > 0.7:
                st.caption(" 영어 방송 연습 비율이 낮습니다. 영어도 함께 연습해보세요!")
            elif kr_ratio < 0.3:
                st.caption(" 한국어 방송 연습 비율이 낮습니다. 한국어도 함께 연습해보세요!")

        # 최근 연습 기록
        st.markdown("---")
        with st.expander("최근 연습 기록 (최근 15건)"):
            for p in sorted(practices, key=lambda x: x.get("date", ""), reverse=True)[:15]:
                has_ai = bool(p.get("transcript"))
                score = p.get("score", "-")
                score_str = f"| {score}점" if score else ""
                label = "" if has_ai else "️"
                st.caption(f"{label} {p.get('date', '')[:10]} | {p.get('type', '')} ({p.get('language', '')}) {score_str}")
