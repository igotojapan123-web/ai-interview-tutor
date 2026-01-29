# pages/14_항공사퀴즈.py
# 항공 퀴즈 통합 - 항공사별 퀴즈 + 항공 상식 퀴즈
# 항공사 10개 기업분석 퀴즈 + 항공 일반상식 5개 카테고리

import streamlit as st
import os
import sys
import json
import random
from datetime import datetime
from typing import List, Dict

from logging_config import get_logger
logger = get_logger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sidebar_common import init_page, end_page

init_page(
    title="항공 퀴즈",
    current_page="항공사퀴즈",
    wide_layout=True
)


st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<style>
html, body, .stApp, .main, [data-testid="stAppViewContainer"] {
    translate: no !important;
}
.notranslate, [translate="no"] {
    translate: no !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate" lang="ko">', unsafe_allow_html=True)

# 누적 기록 파일
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
QUIZ_HISTORY_FILE = os.path.join(DATA_DIR, "quiz_history.json")


def load_quiz_history() -> List[Dict]:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(QUIZ_HISTORY_FILE):
            with open(QUIZ_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.debug(f"퀴즈 기록 로드 실패: {e}")
    return []


def save_quiz_history(history: List[Dict]):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(QUIZ_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.debug(f"퀴즈 기록 저장 실패: {e}")


# ========================================
# 항공사별 퀴즈 데이터
# ========================================
AIRLINE_QUIZZES = {
    "대한항공": [
        {"q": "대한항공의 공식 미션은?", "o": ["Connecting for a better world", "Excellence in Flight", "Fly High, Fly Safe", "Beyond the Sky"], "a": "Connecting for a better world", "e": "대한항공의 공식 미션은 'Connecting for a better world' - 더 나은 세상으로 사람과 문화를 연결한다는 의미입니다."},
        {"q": "대한항공의 공식 비전은?", "o": ["To be the world's most loved airline", "Global No.1 Airline", "Asia's Best Carrier", "Excellence in Service"], "a": "To be the world's most loved airline", "e": "대한항공의 비전은 'To be the world's most loved airline' - 전 세계에서 가장 사랑받는 항공사가 되겠다는 목표입니다."},
        {"q": "대한항공이 2025년 발표한 핵심가치 체계의 이름은?", "o": ["KE Way", "Korean Spirit", "Sky Value", "Air Excellence"], "a": "KE Way", "e": "대한항공은 2025년 'KE Way'라는 핵심 가치 체계를 공식 발표했습니다."},
        {"q": "대한항공 핵심가치 3가지에 포함되지 않는 것은?", "o": ["Speed First", "Beyond Excellence", "Journey Together", "Better Tomorrow"], "a": "Speed First", "e": "대한항공 핵심가치는 Beyond Excellence, Journey Together, Better Tomorrow입니다."},
        {"q": "대한항공 1차 면접의 특징은?", "o": ["Standing(서서) 진행", "앉아서 진행", "개인면접", "토론면접"], "a": "Standing(서서) 진행", "e": "대한항공 1차 면접은 7~8인 1조, 면접관 2명, 20분간 Standing으로 진행됩니다."},
        {"q": "대한항공 영어 지원자격 기준 TOEIC 점수는?", "o": ["550점 이상", "600점 이상", "700점 이상", "500점 이상"], "a": "550점 이상", "e": "대한항공 영어 기준은 TOEIC 550점 / TOEIC Speaking IM / OPIc IM 이상입니다."},
        {"q": "대한항공 채용 시 필수인 수영 테스트 기준은?", "o": ["25m 완영", "50m 완영", "수영 테스트 없음", "100m 완영"], "a": "25m 완영", "e": "대한항공은 건강검진 단계에서 25m 완영 테스트를 필수로 실시합니다."},
        {"q": "대한항공 설립 연도는?", "o": ["1962년", "1969년", "1988년", "1975년"], "a": "1962년", "e": "대한항공은 1962년에 설립되었습니다."},
        {"q": "대한항공 인재상 핵심 요소가 아닌 것은?", "o": ["개인주의", "진취적 성향", "국제적 감각", "서비스 정신"], "a": "개인주의", "e": "대한항공 인재상 핵심 요소는 진취성, 국제감각, 서비스정신, 성실, 팀워크입니다."},
        {"q": "대한항공 객실승무원 핵심역량이 아닌 것은?", "o": ["마케팅 능력", "안전 중심 능력", "고객 서비스 품질", "글로벌 마인드"], "a": "마케팅 능력", "e": "객실승무원 핵심역량은 안전 대응, 고객 서비스, 커뮤니케이션, 글로벌 역량입니다."},
        {"q": "대한항공이 속한 항공사 유형은?", "o": ["FSC (대형항공사)", "LCC (저비용항공사)", "HSC (하이브리드)", "UCC (초저비용)"], "a": "FSC (대형항공사)", "e": "대한항공은 FSC(Full Service Carrier) 대형항공사입니다."},
        {"q": "대한항공 본사 소재지는?", "o": ["서울특별시", "인천광역시", "부산광역시", "제주도"], "a": "서울특별시", "e": "대한항공 본사는 서울특별시에 위치해 있습니다."},
    ],
    "아시아나항공": [
        {"q": "아시아나항공의 슬로건은?", "o": ["아름다운 사람들", "Excellence in Flight", "Fly Better", "Beautiful Journey"], "a": "아름다운 사람들", "e": "아시아나항공의 슬로건은 '아름다운 사람들'입니다."},
        {"q": "아시아나항공의 ESG 미션은?", "o": ["Better flight, Better tomorrow", "Green Sky", "Eco Flight", "Sustainable Air"], "a": "Better flight, Better tomorrow", "e": "아시아나항공 ESG 미션은 'Better flight, Better tomorrow'입니다."},
        {"q": "아시아나항공 설립 연도는?", "o": ["1988년", "1962년", "1995년", "1978년"], "a": "1988년", "e": "아시아나항공은 1988년 2월 17일에 설립되었습니다."},
        {"q": "아시아나항공이 가입한 글로벌 항공 동맹은?", "o": ["Star Alliance", "SkyTeam", "Oneworld", "없음"], "a": "Star Alliance", "e": "아시아나항공은 Star Alliance 회원사입니다."},
        {"q": "아시아나항공 인턴 근무 후 정규직 전환까지 기간은?", "o": ["24개월", "12개월", "6개월", "36개월"], "a": "24개월", "e": "아시아나항공은 인턴 24개월 근무 후 심사를 거쳐 정규직 전환됩니다."},
        {"q": "아시아나항공의 핵심 운영 축이 아닌 것은?", "o": ["저가 전략", "안전", "최고 서비스", "ESG 경영"], "a": "저가 전략", "e": "아시아나항공 핵심 운영 축은 안전, 최고 서비스, 지속가능성/ESG, 사회적 책임입니다."},
        {"q": "아시아나항공 TOEIC 지원자격 기준은?", "o": ["550점 이상", "600점 이상", "700점 이상", "자격 제한 없음"], "a": "550점 이상", "e": "아시아나항공 영어 기준은 TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상입니다."},
        {"q": "아시아나항공 허브 공항이 아닌 것은?", "o": ["청주국제공항", "인천국제공항", "김포국제공항", "제주국제공항"], "a": "청주국제공항", "e": "아시아나항공 허브 공항은 인천국제공항과 김포국제공항입니다."},
        {"q": "아시아나항공의 경영 철학 핵심이 아닌 것은?", "o": ["가격 경쟁력", "최고 수준의 안전", "정성 어린 서비스", "윤리/환경/상생 경영"], "a": "가격 경쟁력", "e": "아시아나항공 경영 철학은 안전 최우선, 고객 만족, 지속 가능 성장, 사회적 책임입니다."},
        {"q": "아시아나항공 합병 상대 항공사는?", "o": ["대한항공", "진에어", "제주항공", "에어부산"], "a": "대한항공", "e": "2024년 12월 대한항공이 아시아나항공 지분 63.88%를 인수하며 합병이 완료되었습니다."},
        {"q": "아시아나항공이 속한 항공사 유형은?", "o": ["FSC (대형항공사)", "LCC (저비용항공사)", "HSC (하이브리드)", "지역항공사"], "a": "FSC (대형항공사)", "e": "아시아나항공은 FSC(Full Service Carrier) 대형항공사입니다."},
        {"q": "아시아나항공 자회사 LCC가 아닌 것은?", "o": ["진에어", "에어부산", "에어서울", "에어프레미아"], "a": "진에어", "e": "진에어는 대한항공 계열이고, 에어부산과 에어서울이 아시아나항공 자회사입니다."},
    ],
    "진에어": [
        {"q": "진에어의 슬로건은?", "o": ["Fly, better fly", "Fun, Young, Dynamic", "Smart Travel", "Joy Flight"], "a": "Fly, better fly", "e": "진에어 슬로건은 'Fly, better fly'입니다."},
        {"q": "진에어 핵심가치 4가지(4 Core Values)에 포함되지 않는 것은?", "o": ["저비용", "SAFETY", "PRACTICALITY", "DELIGHT"], "a": "저비용", "e": "진에어 4 Core Values는 SAFETY, PRACTICALITY, CUSTOMER SERVICE, DELIGHT입니다."},
        {"q": "진에어 인재상 '5 JINISM'에 포함되지 않는 것은?", "o": ["JINIMUM", "JINIABLE", "JINIFUL", "JINIQUE"], "a": "JINIMUM", "e": "5 JINISM은 JINIABLE, JINIFUL, JINIVELY, JINISH, JINIQUE입니다."},
        {"q": "진에어의 지배기업(최대주주)은?", "o": ["대한항공", "한진칼", "아시아나항공", "제주항공"], "a": "대한항공", "e": "한진칼이 보유하던 진에어 지분 54.91%를 대한항공이 취득하여 지배기업이 되었습니다."},
        {"q": "진에어가 도입한 차세대 기종은?", "o": ["B737-8(MAX)", "A320neo", "B787", "A350"], "a": "B737-8(MAX)", "e": "진에어는 B737-8 기종을 도입하여 효율성과 항속거리를 개선했습니다."},
        {"q": "진에어가 운항 재개한 중대형기는?", "o": ["B777-200ER", "A330", "B787", "B747"], "a": "B777-200ER", "e": "진에어는 B777-200ER 운항을 재개하여 국제선에 투입했습니다."},
        {"q": "진에어가 강조하는 독자적 가치 키워드는?", "o": ["실용(Practicality)", "럭셔리", "고급화", "프리미엄"], "a": "실용(Practicality)", "e": "진에어는 LCC임에도 '실용(Practicality)'을 독립 가치로 강조합니다."},
        {"q": "통합 LCC 출범 예정 연도는?", "o": ["2027년", "2025년", "2026년", "2028년"], "a": "2027년", "e": "진에어를 중심으로 2027년 통합 LCC 출범이 예정되어 있습니다."},
        {"q": "진에어 영어 지원자격 TOEIC 기준은?", "o": ["550점 이상", "600점 이상", "700점 이상", "제한 없음"], "a": "550점 이상", "e": "진에어 영어 기준은 TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상입니다."},
        {"q": "진에어와 통합 예정인 LCC가 아닌 것은?", "o": ["제주항공", "에어부산", "에어서울", "에어로케이"], "a": "제주항공", "e": "진에어, 에어부산, 에어서울 3사가 통합 LCC로 출범 예정입니다."},
        {"q": "진에어 인재상 JINISH의 의미는?", "o": ["팀워크와 협업 지향", "최고의 안전", "긍정적 에너지", "열린 사고"], "a": "팀워크와 협업 지향", "e": "JINISH는 팀워크와 협업을 지향하는 JINI를 의미합니다."},
        {"q": "진에어가 속한 항공사 유형은?", "o": ["LCC (저비용항공사)", "FSC (대형항공사)", "HSC (하이브리드)", "지역항공사"], "a": "LCC (저비용항공사)", "e": "진에어는 대한항공 계열 LCC(저비용항공사)입니다."},
    ],
    "제주항공": [
        {"q": "제주항공의 미션은?", "o": ["더 넓은 하늘을 향한 도전으로 더 많은 사람들과 행복한 여행의 경험을 나눈다", "최고의 안전, 최고의 서비스", "하늘 위의 행복", "대한민국 대표 항공사"], "a": "더 넓은 하늘을 향한 도전으로 더 많은 사람들과 행복한 여행의 경험을 나눈다", "e": "제주항공 미션은 '더 넓은 하늘을 향한 도전으로 더 많은 사람들과 행복한 여행의 경험을 나눈다'입니다."},
        {"q": "제주항공 핵심가치 5가지에 포함되지 않는 것은?", "o": ["혁신", "안전", "저비용", "팀워크"], "a": "혁신", "e": "제주항공 핵심가치는 안전, 저비용, 신뢰, 팀워크, 도전입니다."},
        {"q": "제주항공 브랜드 태그라인은?", "o": ["NEW STANDARD", "Fly Better", "Joy Flight", "Happy Travel"], "a": "NEW STANDARD", "e": "제주항공 브랜드 태그라인은 'NEW STANDARD'입니다."},
        {"q": "제주항공 인재상 '7C'에 포함되지 않는 것은?", "o": ["Courageous", "Confident", "Competent", "Customer oriented"], "a": "Courageous", "e": "7C는 Confident, Competent, Connected, Cooperative, Consistent, Creative, Customer oriented입니다."},
        {"q": "제주항공 영어 지원자격 TOEIC 기준은?", "o": ["600점 이상", "550점 이상", "700점 이상", "제한 없음"], "a": "600점 이상", "e": "제주항공 영어 기준은 TOEIC 600점 / TOEIC Speaking IM1 / OPIc IM1 이상입니다."},
        {"q": "제주항공의 학력 지원자격은?", "o": ["학력 제한 없음", "전문대졸 이상", "대졸 이상", "고졸 이상"], "a": "학력 제한 없음", "e": "제주항공은 학력 제한 없는 열린 채용을 실시합니다."},
        {"q": "제주항공이 LCC 최초로 도입한 것은?", "o": ["화물 전용기", "프리미엄 이코노미", "비즈니스석", "퍼스트클래스"], "a": "화물 전용기", "e": "제주항공은 LCC 최초로 B737-800F 화물 전용기를 도입했습니다."},
        {"q": "제주항공 차세대 기종은?", "o": ["B737-8", "A320neo", "B787", "A350"], "a": "B737-8", "e": "제주항공은 B737-8 도입으로 운용비용 14% 절감, 항속거리 8시간까지 확대를 계획합니다."},
        {"q": "제주항공 본점 소재지는?", "o": ["제주도", "서울", "인천", "부산"], "a": "제주도", "e": "제주항공은 제주도에 본점을 두고 있습니다."},
        {"q": "제주항공 최대주주는?", "o": ["AK홀딩스", "대한항공", "아시아나", "한진칼"], "a": "AK홀딩스", "e": "제주항공 최대주주는 AK홀딩스입니다."},
        {"q": "제주항공 언어특기전형 대상 언어가 아닌 것은?", "o": ["베트남어", "일본어", "중국어", "영어"], "a": "베트남어", "e": "제주항공 언어특기전형은 일본어, 중국어 특기자를 대상으로 합니다."},
        {"q": "제주항공이 스스로 포지셔닝하는 것은?", "o": ["대한민국 No.1 LCC", "아시아 최고 LCC", "글로벌 LCC", "프리미엄 LCC"], "a": "대한민국 No.1 LCC", "e": "제주항공은 스스로를 '대한민국 No.1 LCC'로 포지셔닝합니다."},
    ],
    "티웨이항공": [
        {"q": "티웨이항공의 미션은?", "o": ["첫째도 안전, 둘째도 안전!", "최고의 서비스", "즐거운 여행", "함께하는 하늘길"], "a": "첫째도 안전, 둘째도 안전!", "e": "티웨이항공 미션은 '첫째도 안전, 둘째도 안전!'입니다."},
        {"q": "티웨이항공 핵심가치 '5S'에 포함되지 않는 것은?", "o": ["Speed", "Safety", "Smart", "Sustainability"], "a": "Speed", "e": "5S는 Safety, Smart, Satisfaction, Sharing, Sustainability입니다."},
        {"q": "티웨이항공이 스스로 지향하는 포지션은?", "o": ["Leading LCC", "Premium LCC", "Hybrid LCC", "Budget Airline"], "a": "Leading LCC", "e": "티웨이항공은 비전에서 'Leading LCC'를 포함합니다."},
        {"q": "티웨이항공 인재상 4문장에 포함되지 않는 것은?", "o": ["체력이 뛰어난 사람", "도전의 가치를 아는 사람", "창의적 인재", "국제적 유머감각"], "a": "체력이 뛰어난 사람", "e": "인재상은 도전, 창의, 소통, 국제적 유머감각입니다."},
        {"q": "티웨이항공이 변경 추진 중인 새 브랜드명은?", "o": ["Trinity Airways", "T-Air", "New T'way", "Sky T"], "a": "Trinity Airways", "e": "티웨이항공은 Trinity Airways(트리니티 항공)로 브랜드 변경을 추진 중입니다."},
        {"q": "티웨이항공의 새 최대주주는?", "o": ["소노인터내셔널", "대한항공", "AK홀딩스", "한진칼"], "a": "소노인터내셔널", "e": "티웨이항공은 최대주주가 소노인터내셔널로 변경되었습니다."},
        {"q": "티웨이항공이 확대하고 있는 노선 지역은?", "o": ["유럽", "북미", "호주", "남미"], "a": "유럽", "e": "티웨이항공은 바르셀로나, 로마, 파리 등 유럽 노선을 확대하고 있습니다."},
        {"q": "티웨이항공 IOSA 인증 유지 시작 연도는?", "o": ["2014년", "2010년", "2018년", "2020년"], "a": "2014년", "e": "티웨이항공은 2014년부터 IATA 안전평가(IOSA) 인증을 유지하고 있습니다."},
        {"q": "티웨이항공 인턴 기간은?", "o": ["1년", "2년", "6개월", "즉시 정규직"], "a": "1년", "e": "티웨이항공은 인턴 1년 후 정규직 전환됩니다."},
        {"q": "티웨이항공 영어 지원자격 TOEIC 기준은?", "o": ["600점 이상", "550점 이상", "700점 이상", "650점 이상"], "a": "600점 이상", "e": "티웨이항공 영어 기준은 TOEIC 600점 / TOEIC Speaking IM / OPIc IM 이상입니다."},
        {"q": "티웨이항공 슬로건은?", "o": ["즐거운 여행의 시작", "하늘 위의 행복", "안전한 비행", "함께하는 여행"], "a": "즐거운 여행의 시작", "e": "티웨이항공 슬로건은 '즐거운 여행의 시작'입니다."},
        {"q": "티웨이항공 비윤리/부패행위 신고 이메일은?", "o": ["audit@twayair.com", "ethics@twayair.com", "report@twayair.com", "help@twayair.com"], "a": "audit@twayair.com", "e": "티웨이항공 윤리경영 신고 이메일은 audit@twayair.com입니다."},
    ],
    "에어부산": [
        {"q": "에어부산의 서비스 모토는?", "o": ["여행의 지혜, FLY SMART", "부산의 자부심", "Smart Flight", "Happy Journey"], "a": "여행의 지혜, FLY SMART", "e": "에어부산 서비스 모토는 '여행의 지혜, FLY SMART'입니다."},
        {"q": "에어부산 ESG 슬로건은?", "o": ["FLY TO ZERO", "Green Flight", "Eco Air", "Zero Carbon"], "a": "FLY TO ZERO", "e": "에어부산 ESG 슬로건은 'FLY TO ZERO'입니다."},
        {"q": "에어부산 2025년 경영 핵심가치 3가지에 포함되지 않는 것은?", "o": ["고객만족", "안전운항", "산업안전", "정보보안"], "a": "고객만족", "e": "2025년 핵심가치는 안전운항, 산업안전, 정보보안입니다."},
        {"q": "에어부산의 모회사는?", "o": ["아시아나항공", "대한항공", "제주항공", "독립 항공사"], "a": "아시아나항공", "e": "에어부산은 전통적으로 아시아나항공 계열입니다."},
        {"q": "에어부산 1차 면접 형식은?", "o": ["그룹 토론", "개인 면접", "PT 발표", "영어 면접"], "a": "그룹 토론", "e": "에어부산 1차 면접은 그룹 토론 형식으로 진행됩니다."},
        {"q": "에어부산 거점 공항은?", "o": ["김해공항", "인천공항", "김포공항", "청주공항"], "a": "김해공항", "e": "에어부산은 김해공항(부산)을 거점으로 합니다."},
        {"q": "에어부산 고객 가치 3요소에 포함되지 않는 것은?", "o": ["빠른 속도", "완벽한 안전", "편리한 서비스", "실용적인 가격"], "a": "빠른 속도", "e": "에어부산 고객 가치는 안전, 편리한 서비스, 실용적인 가격입니다."},
        {"q": "에어부산 ESG 미션은?", "o": ["ESG 경영을 통한 지속 가능한 환경과 사회적 가치 창조", "친환경 비행", "탄소 중립", "그린 항공"], "a": "ESG 경영을 통한 지속 가능한 환경과 사회적 가치 창조", "e": "에어부산 ESG 미션은 'ESG 경영을 통한 지속 가능한 환경과 사회적 가치 창조'입니다."},
        {"q": "에어부산이 우대하는 지역 거주자는?", "o": ["부산/경남 거주자", "서울 거주자", "인천 거주자", "제주 거주자"], "a": "부산/경남 거주자", "e": "에어부산은 부산 거점 항공사로 부산/경남 거주자를 우대합니다."},
        {"q": "에어부산과 통합 예정인 LCC는?", "o": ["진에어, 에어서울", "제주항공", "티웨이항공", "이스타항공"], "a": "진에어, 에어서울", "e": "에어부산은 진에어, 에어서울과 함께 통합 LCC로 편입 예정입니다."},
        {"q": "에어부산 슬로건은?", "o": ["부산의 자부심", "하늘 위의 부산", "부산을 날다", "부산 스카이"], "a": "부산의 자부심", "e": "에어부산 슬로건은 '부산의 자부심'입니다."},
        {"q": "에어부산이 운영하는 안전관리시스템은?", "o": ["SMS", "SOS", "SAM", "SSM"], "a": "SMS", "e": "에어부산은 항공안전관리시스템(SMS)을 운영합니다."},
    ],
    "에어서울": [
        {"q": "에어서울의 슬로건은?", "o": ["It's mint time", "Premium LCC", "Seoul in the Sky", "Fly Seoul"], "a": "It's mint time", "e": "에어서울 슬로건은 'It's mint time'입니다."},
        {"q": "에어서울 브랜드 컬러 'MINT'가 나타내는 가치가 아닌 것은?", "o": ["Luxury", "Open", "Refresh", "Pleasant"], "a": "Luxury", "e": "MINT 서비스 가치는 Open, Refresh, Relax, Pleasant입니다."},
        {"q": "에어서울의 비즈니스 철학은?", "o": ["The best and safest airline, giving the gift of happiness to its customers", "Premium Service", "Budget Travel", "Luxury in the Sky"], "a": "The best and safest airline, giving the gift of happiness to its customers", "e": "에어서울 비즈니스 철학은 '최고의 안전과 행복을 선사하는 항공사'입니다."},
        {"q": "에어서울 조직문화 3가지 축에 포함되지 않는 것은?", "o": ["효율성의 문화", "소통/배려/조화의 문화", "새로운 도전의 문화", "창의성의 문화"], "a": "효율성의 문화", "e": "조직문화는 소통/배려/조화, 새로운 도전, 창의성입니다."},
        {"q": "에어서울 창립일은?", "o": ["2015년 4월 7일", "2010년 1월 1일", "2018년 6월 15일", "2012년 3월 20일"], "a": "2015년 4월 7일", "e": "에어서울은 2015년 4월 7일에 창립되었습니다."},
        {"q": "에어서울 2024년 3월 기준 항공기 보유수는?", "o": ["6대", "10대", "15대", "3대"], "a": "6대", "e": "에어서울은 2024년 3월 기준 항공기 6대를 보유하고 있습니다."},
        {"q": "에어서울의 모회사는?", "o": ["아시아나항공", "대한항공", "제주항공", "독립 항공사"], "a": "아시아나항공", "e": "에어서울은 아시아나항공 자회사입니다."},
        {"q": "에어서울 인턴 기간은?", "o": ["2년", "1년", "6개월", "즉시 정규직"], "a": "2년", "e": "에어서울은 인턴 2년 근무 후 심사를 거쳐 정규직 전환됩니다."},
        {"q": "에어서울 서비스 지향점 3가지에 포함되지 않는 것은?", "o": ["The fastest flight", "The highest safety", "The happiest services", "A company you can trust"], "a": "The fastest flight", "e": "서비스 지향점은 최고 안전, 행복한 서비스, 신뢰입니다."},
        {"q": "에어서울 영어 지원자격 TOEIC 기준은?", "o": ["550점 이상", "600점 이상", "700점 이상", "제한 없음"], "a": "550점 이상", "e": "에어서울 영어 기준은 TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM1 이상입니다."},
        {"q": "에어서울 2025년 1월 취임한 대표이사는?", "o": ["김중호", "김민수", "이정호", "박준영"], "a": "김중호", "e": "2025년 1월 16일 김중호 대표이사가 취임했습니다."},
        {"q": "에어서울 우대 외국어가 아닌 것은?", "o": ["베트남어", "중국어", "일본어", "영어"], "a": "베트남어", "e": "에어서울은 아시아 노선 중심으로 중국어, 일본어 우수자를 우대합니다."},
    ],
    "이스타항공": [
        {"q": "이스타항공의 비전/미션은?", "o": ["항공여행의 대중화를 선도하고 사회공익에 기여하는 글로벌 국민항공사", "최고의 서비스", "안전 제일", "하늘 위의 행복"], "a": "항공여행의 대중화를 선도하고 사회공익에 기여하는 글로벌 국민항공사", "e": "이스타항공 비전은 '항공여행의 대중화를 선도하고 사회공익에 기여하는 글로벌 국민항공사'입니다."},
        {"q": "이스타항공 슬로건은?", "o": ["기분 좋은 만남, 국민항공사 이스타항공", "새로운 도약", "행복한 비행", "하늘의 별"], "a": "기분 좋은 만남, 국민항공사 이스타항공", "e": "이스타항공 슬로건은 '기분 좋은 만남, 국민항공사 이스타항공'입니다."},
        {"q": "이스타항공 체력시험 항목이 아닌 것은?", "o": ["윗몸일으키기", "오래달리기", "높이뛰기", "목소리 데시벨"], "a": "윗몸일으키기", "e": "이스타항공 체력시험은 오래달리기, 높이뛰기, 목소리 데시벨입니다."},
        {"q": "이스타항공 기업회생절차 종결 연도는?", "o": ["2022년", "2020년", "2023년", "2021년"], "a": "2022년", "e": "이스타항공은 2022년 3월 기업회생절차가 종결되었습니다."},
        {"q": "이스타항공 운항 재개 연도는?", "o": ["2023년", "2022년", "2024년", "2021년"], "a": "2023년", "e": "이스타항공은 2023년 2월 AOC 재취득, 3월 국내선 운항을 재개했습니다."},
        {"q": "이스타항공 현재 대주주는?", "o": ["VIG파트너스", "대한항공", "AK홀딩스", "한진칼"], "a": "VIG파트너스", "e": "2023년 1월 VIG파트너스가 이스타항공 지분 100%를 취득했습니다."},
        {"q": "이스타항공 설립 연도는?", "o": ["2007년", "2005년", "2010년", "2003년"], "a": "2007년", "e": "이스타항공은 2007년 10월 23일에 설립되었습니다."},
        {"q": "이스타항공 영어 지원자격 TOEIC 기준은?", "o": ["670점 이상", "550점 이상", "600점 이상", "700점 이상"], "a": "670점 이상", "e": "이스타항공 영어 기준은 TOEIC 670점 / TOEIC Speaking IM3 / OPIc IM2 이상으로 타 LCC보다 높습니다."},
        {"q": "이스타항공이 2024년 신설한 조직은?", "o": ["준법경영팀", "마케팅팀", "고객서비스팀", "안전관리팀"], "a": "준법경영팀", "e": "이스타항공은 2024년 2월 준법경영팀을 신설했습니다."},
        {"q": "이스타항공이 운영하는 안전관리시스템은?", "o": ["ESMS (통합안전관리시스템)", "SMS", "QMS", "TMS"], "a": "ESMS (통합안전관리시스템)", "e": "이스타항공은 ESMS(통합안전관리시스템)를 운영합니다."},
        {"q": "이스타항공 허브공항은?", "o": ["김포국제공항", "인천국제공항", "청주국제공항", "제주국제공항"], "a": "김포국제공항", "e": "이스타항공 주요 허브공항은 김포국제공항입니다."},
        {"q": "이스타항공이 우대하는 전공자는?", "o": ["간호학 전공자", "항공학 전공자", "경영학 전공자", "외국어 전공자"], "a": "간호학 전공자", "e": "이스타항공은 응급 구조 역할의 중요성으로 간호학 전공자를 우대합니다."},
    ],
    "에어로케이": [
        {"q": "에어로케이의 거점 공항은?", "o": ["청주국제공항", "인천국제공항", "김포국제공항", "김해국제공항"], "a": "청주국제공항", "e": "에어로케이는 청주국제공항을 거점으로 합니다."},
        {"q": "에어로케이가 운용하는 기종은?", "o": ["A320 단일기종", "B737", "A330", "B787"], "a": "A320 단일기종", "e": "에어로케이는 A320 단일기종을 운용합니다."},
        {"q": "에어로케이 운항 개시 연도는?", "o": ["2021년", "2019년", "2020년", "2022년"], "a": "2021년", "e": "에어로케이는 2021년 4월 운항을 개시했습니다."},
        {"q": "에어로케이 채용의 특징이 아닌 것은?", "o": ["경력자만 채용", "학력 제한 없음", "나이 제한 없음", "외모 규정 없음"], "a": "경력자만 채용", "e": "에어로케이는 학력, 나이, 외모 제한 없는 열린 채용을 실시합니다."},
        {"q": "에어로케이 1차 면접 형식은?", "o": ["토론과 실무면접 병행", "개인 면접", "PT 발표", "영상 면접"], "a": "토론과 실무면접 병행", "e": "에어로케이 1차 면접은 토론과 실무면접을 병행합니다."},
        {"q": "에어로케이가 우대하는 자격은?", "o": ["안전분야 관련 자격", "마케팅 자격증", "회계 자격증", "IT 자격증"], "a": "안전분야 관련 자격", "e": "에어로케이는 안전분야 관련 자격 보유자를 우대합니다."},
        {"q": "에어로케이 설립 연도는?", "o": ["2016년", "2018년", "2020년", "2014년"], "a": "2016년", "e": "에어로케이는 2016년에 설립되었습니다."},
        {"q": "에어로케이 영어 지원자격 기준은?", "o": ["TOEIC Speaking IM1 / OPIc IM1 이상", "TOEIC 600점 이상", "TOEIC 700점 이상", "제한 없음"], "a": "TOEIC Speaking IM1 / OPIc IM1 이상", "e": "에어로케이 영어 기준은 TOEIC Speaking IM1 / OPIc IM1 이상입니다."},
        {"q": "에어로케이가 우대하는 거주 경력은?", "o": ["영어권/중국/일본 3년 이상 거주자", "유럽 거주자", "동남아 거주자", "미국 거주자"], "a": "영어권/중국/일본 3년 이상 거주자", "e": "에어로케이는 영어권/중국/일본 3년 이상 거주자를 우대합니다."},
        {"q": "에어로케이 항공사 유형은?", "o": ["LCC (저비용항공사)", "FSC (대형항공사)", "HSC (하이브리드)", "지역항공사"], "a": "LCC (저비용항공사)", "e": "에어로케이는 청주 거점 소형 LCC입니다."},
        {"q": "에어로케이 단일기종 운용의 장점이 아닌 것은?", "o": ["다양한 노선 확대", "조종사 훈련 단순화", "정비 비용 절감", "스케줄 운영 단순화"], "a": "다양한 노선 확대", "e": "단일기종의 장점은 훈련 단순화, 정비 비용 절감, 운영 단순화입니다."},
        {"q": "에어로케이 슬로건은?", "o": ["새로운 하늘길", "청주의 날개", "하늘을 열다", "행복한 비행"], "a": "새로운 하늘길", "e": "에어로케이 슬로건은 '새로운 하늘길'입니다."},
    ],
    "에어프레미아": [
        {"q": "에어프레미아의 항공사 유형은?", "o": ["HSC (하이브리드)", "LCC (저비용)", "FSC (대형)", "UCC (초저비용)"], "a": "HSC (하이브리드)", "e": "에어프레미아는 스스로를 HSC(Hybrid Service Carrier)로 규정합니다."},
        {"q": "에어프레미아가 운용하는 기종은?", "o": ["B787-9 Dreamliner", "B737", "A320", "A330"], "a": "B787-9 Dreamliner", "e": "에어프레미아는 B787-9 Dreamliner 단일기종을 운용합니다."},
        {"q": "에어프레미아 슬로건은?", "o": ["New Way to Fly", "Premium Flight", "Hybrid Excellence", "Sky Premium"], "a": "New Way to Fly", "e": "에어프레미아 슬로건은 'New Way to Fly'입니다."},
        {"q": "에어프레미아 좌석 구성은?", "o": ["프리미엄 이코노미 + 이코노미 2클래스", "비즈니스 + 이코노미", "퍼스트 + 비즈니스 + 이코노미", "이코노미만"], "a": "프리미엄 이코노미 + 이코노미 2클래스", "e": "에어프레미아는 프리미엄 이코노미와 이코노미 2클래스로 운영합니다."},
        {"q": "에어프레미아 체력측정 항목이 아닌 것은?", "o": ["오래달리기", "악력", "윗몸일으키기", "버피테스트"], "a": "오래달리기", "e": "에어프레미아 체력측정은 악력, 윗몸일으키기, 버피테스트, 유연성, 암리치입니다."},
        {"q": "에어프레미아 운항 개시 연도는?", "o": ["2021년", "2019년", "2020년", "2022년"], "a": "2021년", "e": "에어프레미아는 2021년 8월 운항을 개시했습니다."},
        {"q": "에어프레미아 주요 노선 특징은?", "o": ["중장거리 특화", "단거리 다빈도", "국내선 중심", "화물 전용"], "a": "중장거리 특화", "e": "에어프레미아는 미주, 아시아 중장거리 노선에 특화되어 있습니다."},
        {"q": "에어프레미아 영어 지원자격 TOEIC 기준은?", "o": ["600점 이상", "550점 이상", "700점 이상", "650점 이상"], "a": "600점 이상", "e": "에어프레미아 영어 기준은 TOEIC 600점 / TOEIC Speaking IM / OPIc IM 이상입니다."},
        {"q": "에어프레미아 설립 연도는?", "o": ["2017년", "2015년", "2019년", "2020년"], "a": "2017년", "e": "에어프레미아는 2017년에 설립되었습니다."},
        {"q": "에어프레미아 허브공항은?", "o": ["인천국제공항", "김포국제공항", "청주국제공항", "김해국제공항"], "a": "인천국제공항", "e": "에어프레미아 허브공항은 인천국제공항입니다."},
        {"q": "에어프레미아가 운영하지 않는 좌석 클래스는?", "o": ["비즈니스 클래스", "프리미엄 이코노미", "이코노미", "일반석"], "a": "비즈니스 클래스", "e": "에어프레미아는 비즈니스 클래스를 운영하지 않습니다."},
        {"q": "에어프레미아 주요 주주로 참여한 기업은?", "o": ["타이어뱅크", "대한항공", "AK홀딩스", "한진칼"], "a": "타이어뱅크", "e": "에어프레미아는 타이어뱅크가 주요 주주로 참여한 독립 민간 자본 기반 항공사입니다."},
    ],
    "파라타항공": [
        {"q": "파라타항공의 전신(이전 이름)은?", "o": ["플라이강원", "에어강원", "강원에어", "스카이강원"], "a": "플라이강원", "e": "파라타항공은 플라이강원의 후신입니다."},
        {"q": "파라타항공을 인수한 기업은?", "o": ["위닉스(WINIX)", "삼성", "LG", "SK"], "a": "위닉스(WINIX)", "e": "생활가전 기업 위닉스가 2024년 8월 플라이강원을 인수했습니다."},
        {"q": "파라타항공 슬로건은?", "o": ["Fly new", "New Sky", "Fresh Air", "Clean Flight"], "a": "Fly new", "e": "파라타항공 슬로건은 'Fly new'입니다."},
        {"q": "파라타항공 브랜드 철학은?", "o": ["PARAdigm을 바꾸는 Trustworthy Airlines", "최고의 서비스", "안전 제일", "고객 감동"], "a": "PARAdigm을 바꾸는 Trustworthy Airlines", "e": "PARATA는 여행 경험의 패러다임을 바꾸는 신뢰할 수 있는 항공사를 의미합니다."},
        {"q": "파라타항공 거점 공항은?", "o": ["양양공항", "인천공항", "김포공항", "청주공항"], "a": "양양공항", "e": "파라타항공은 양양공항을 거점으로 합니다."},
        {"q": "파라타항공이 도입한 대형기는?", "o": ["A330-200", "B777", "B787", "A350"], "a": "A330-200", "e": "파라타항공은 A330-200(1호기)를 도입했습니다."},
        {"q": "파라타항공 채용 시 필수 제출 서류는?", "o": ["국민체력100 체력평가 결과서", "영어성적표", "자격증", "추천서"], "a": "국민체력100 체력평가 결과서", "e": "파라타항공은 국민체력100 체력평가 결과서 제출을 필수화했습니다."},
        {"q": "파라타항공 영어 지원자격 TOEIC 기준은?", "o": ["650점 이상", "550점 이상", "600점 이상", "700점 이상"], "a": "650점 이상", "e": "파라타항공 영어 기준은 TOEIC 650점 / TOEIC Speaking IM / OPIc IM 이상입니다."},
        {"q": "파라타항공 CI의 특징(A-Bird)은?", "o": ["PARATA 철자의 3개 A를 새로 형상화", "비행기 모양", "태극 문양", "강원도 산"], "a": "PARATA 철자의 3개 A를 새로 형상화", "e": "파라타항공 CI는 PARATA의 3개 A를 새(A-Bird)로 형상화한 심볼입니다."},
        {"q": "파라타항공 고객가치 키워드가 아닌 것은?", "o": ["고급스러움", "투명함", "쾌적함", "신뢰"], "a": "고급스러움", "e": "파라타항공 고객가치는 투명함, 쾌적함, 신뢰, 안정감입니다."},
        {"q": "파라타항공의 항공사 운영 전략은?", "o": ["대형기+소형기 하이브리드", "단일기종 LCC", "대형기만 운용", "소형기만 운용"], "a": "대형기+소형기 하이브리드", "e": "파라타항공은 A330-200과 A320-200을 함께 운용하는 하이브리드 전략입니다."},
        {"q": "파라타항공 인재상의 핵심은?", "o": ["안전의식과 서비스 마인드", "외모와 체력", "학벌과 경력", "영어 능력"], "a": "안전의식과 서비스 마인드", "e": "파라타항공은 안전의식과 서비스 마인드를 갖춘 인재를 선호합니다."},
    ],
}

# 합병 관련 공통 퀴즈
MERGER_QUIZZES = [
    {"q": "대한항공-아시아나 합병 법적 완료 연도는?", "o": ["2024년", "2023년", "2025년", "2022년"], "a": "2024년", "e": "2024년 12월 12일 대한항공이 아시아나 지분 63.88%를 인수하며 법적 절차가 완료되었습니다."},
    {"q": "통합 항공사를 지칭하는 용어는?", "o": ["메가캐리어", "슈퍼캐리어", "울트라캐리어", "하이퍼캐리어"], "a": "메가캐리어", "e": "대한항공-아시아나 통합으로 '메가캐리어(초대형 항공사)'가 출현합니다."},
    {"q": "통합 LCC(진에어+에어부산+에어서울) 출범 예정 연도는?", "o": ["2027년", "2025년", "2026년", "2028년"], "a": "2027년", "e": "진에어를 중심으로 2027년 통합 LCC 출범이 예정되어 있습니다."},
    {"q": "합병으로 양도 조건이 된 사업부는?", "o": ["아시아나 화물 사업부 (Air Zeta로)", "아시아나 여객 사업부", "대한항공 화물 사업부", "대한항공 기내식 사업부"], "a": "아시아나 화물 사업부 (Air Zeta로)", "e": "규제 조건으로 아시아나 화물 사업부를 Air Zeta(구 에어인천)로 양도했습니다."},
    {"q": "합병 후 객실승무원에게 더 중요해지는 역량은?", "o": ["팀 기반 표준 수행 역량", "개인 서비스 감각", "화려한 이력", "외모"], "a": "팀 기반 표준 수행 역량", "e": "메가캐리어는 개인차보다 일관성을 중시하므로 표준 준수 능력이 중요합니다."},
]


# ========================================
# 항공 상식 퀴즈 데이터 (확장)
# ========================================
KNOWLEDGE_QUIZZES = {
    "항공 기초": [
        {"q": "항공기의 날개 끝에 있는 작은 수직 날개를 무엇이라고 할까요?", "o": ["윙렛(Winglet)", "플랩(Flap)", "스포일러(Spoiler)", "에일러론(Aileron)"], "a": "윙렛(Winglet)", "e": "윙렛은 연료 효율을 높이고 항력을 줄이기 위해 날개 끝에 부착된 작은 수직 날개입니다."},
        {"q": "비행기가 이륙할 때 속도를 나타내는 V1은 무엇을 의미할까요?", "o": ["이륙 결심 속도", "최대 이륙 속도", "순항 속도", "착륙 속도"], "a": "이륙 결심 속도", "e": "V1은 이륙 결심 속도로, 이 속도를 넘으면 이륙을 중단할 수 없습니다."},
        {"q": "국제선 항공기에서 사용하는 표준 언어는?", "o": ["영어", "프랑스어", "스페인어", "중국어"], "a": "영어", "e": "ICAO에 의해 영어가 국제 항공 표준 언어로 지정되어 있습니다."},
        {"q": "항공기 동체의 압력을 유지하는 것을 무엇이라고 할까요?", "o": ["여압(Pressurization)", "가압(Compression)", "감압(Decompression)", "기압(Barometry)"], "a": "여압(Pressurization)", "e": "여압은 고고도에서 승객이 편안하게 호흡할 수 있도록 객실 압력을 유지하는 것입니다."},
        {"q": "항공기 블랙박스의 실제 색상은?", "o": ["주황색", "검정색", "빨간색", "노란색"], "a": "주황색", "e": "블랙박스는 사고 현장에서 쉽게 발견할 수 있도록 밝은 주황색으로 되어 있습니다."},
        {"q": "항공기 순항 고도는 보통 몇 피트인가요?", "o": ["35,000피트", "10,000피트", "50,000피트", "5,000피트"], "a": "35,000피트", "e": "여객기의 순항 고도는 보통 30,000~40,000피트(약 10~12km)입니다."},
        {"q": "항공기가 착륙 시 역추력을 사용하는 이유는?", "o": ["감속을 위해", "방향 전환을 위해", "이륙 준비를 위해", "연료 절약을 위해"], "a": "감속을 위해", "e": "역추력(Reverse Thrust)은 엔진의 추력 방향을 바꿔 착륙 시 감속을 돕습니다."},
        {"q": "항공기 날개의 플랩(Flap)의 주요 역할은?", "o": ["양력 증가", "속도 증가", "방향 전환", "고도 유지"], "a": "양력 증가", "e": "플랩은 이착륙 시 날개 면적을 늘려 저속에서도 충분한 양력을 확보합니다."},
        {"q": "제트기류(Jet Stream)의 평균 속도는?", "o": ["시속 150~300km", "시속 50~100km", "시속 500~700km", "시속 30~50km"], "a": "시속 150~300km", "e": "제트기류는 대류권 상부(약 10km)에서 부는 강한 바람으로 평균 시속 150~300km입니다."},
        {"q": "ICAO는 무엇의 약자인가요?", "o": ["국제민간항공기구", "국제항공조종사협회", "국제항공안전기구", "국제공항협의회"], "a": "국제민간항공기구", "e": "ICAO는 International Civil Aviation Organization(국제민간항공기구)의 약자입니다."},
    ],
    "객실 서비스": [
        {"q": "비상구 좌석에 앉을 수 없는 승객은?", "o": ["15세 미만 승객", "비즈니스맨", "외국인", "첫 비행 승객"], "a": "15세 미만 승객", "e": "비상구 좌석은 비상시 문을 열 수 있어야 하므로, 어린이, 노약자, 임산부 등은 앉을 수 없습니다."},
        {"q": "기내식이 지상에서 먹을 때보다 맛없게 느껴지는 이유는?", "o": ["낮은 습도와 기압", "음식 온도", "좌석 불편함", "조명"], "a": "낮은 습도와 기압", "e": "기내의 낮은 습도와 기압으로 인해 미각과 후각이 둔해져 음식 맛이 다르게 느껴집니다."},
        {"q": "객실승무원이 이착륙 시 앉는 좌석을 무엇이라고 할까요?", "o": ["점프시트(Jump Seat)", "크루시트(Crew Seat)", "서비스시트(Service Seat)", "에어시트(Air Seat)"], "a": "점프시트(Jump Seat)", "e": "점프시트는 승무원 전용 접이식 좌석입니다."},
        {"q": "기내에서 승객이 쓰러졌을 때 찾는 의료 장비는?", "o": ["AED", "CPR기", "EMS", "ICU"], "a": "AED", "e": "AED(자동제세동기)는 심정지 환자에게 전기 충격을 주는 응급 의료 장비입니다."},
        {"q": "기내 산소마스크가 공급하는 산소의 지속 시간은 약?", "o": ["12~15분", "1~2분", "30분~1시간", "5분"], "a": "12~15분", "e": "기내 산소마스크는 화학반응으로 약 12~15분간 산소를 공급합니다."},
        {"q": "기내에서 금지되는 전자기기 사용 시점은?", "o": ["이착륙 시", "순항 시", "기내식 서비스 중", "영화 상영 중"], "a": "이착륙 시", "e": "이착륙 시에는 항공기 통신장비 간섭 방지를 위해 전자기기 사용이 제한됩니다."},
        {"q": "갤리(Galley)란 무엇인가요?", "o": ["기내 주방", "조종실", "화물칸", "승무원 휴게실"], "a": "기내 주방", "e": "갤리는 기내에서 음식을 준비하고 보관하는 주방 공간입니다."},
        {"q": "기내 좌석 등급 중 가장 높은 등급은?", "o": ["퍼스트 클래스", "비즈니스 클래스", "프리미엄 이코노미", "이코노미 플러스"], "a": "퍼스트 클래스", "e": "좌석 등급은 퍼스트 > 비즈니스 > 프리미엄 이코노미 > 이코노미 순입니다."},
        {"q": "Pax는 항공업계에서 무엇을 의미하나요?", "o": ["승객(Passenger)", "수하물(Package)", "파일럿(Pilot)", "활주로(Path)"], "a": "승객(Passenger)", "e": "Pax는 라틴어에서 유래한 항공업계 용어로 승객을 의미합니다."},
        {"q": "데드헤딩(Deadheading)이란?", "o": ["승무원이 비번으로 탑승", "항공기 회항", "빈 좌석 운항", "야간 비행"], "a": "승무원이 비번으로 탑승", "e": "데드헤딩은 승무원이 근무지 이동을 위해 승객으로 탑승하는 것입니다."},
    ],
    "공항/항로": [
        {"q": "인천국제공항의 IATA 코드는?", "o": ["ICN", "INC", "SEL", "GMP"], "a": "ICN", "e": "인천국제공항의 IATA 코드는 ICN입니다. 김포공항은 GMP입니다."},
        {"q": "세계에서 가장 붐비는 공항(2023년 기준)은?", "o": ["하츠필드-잭슨 애틀랜타", "두바이", "히스로", "인천"], "a": "하츠필드-잭슨 애틀랜타", "e": "미국 애틀랜타 공항이 승객 수 기준 세계 1위입니다."},
        {"q": "면세점에서 'Duty Free'의 Duty는 무엇을 의미할까요?", "o": ["관세", "의무", "근무", "세금"], "a": "관세", "e": "Duty는 관세를 의미하며, Duty Free는 관세가 없다는 뜻입니다."},
        {"q": "CIQ는 무엇의 약자일까요?", "o": ["세관/출입국/검역", "체크인/입국/대기", "수하물/입국/조회", "출국/입국/대기"], "a": "세관/출입국/검역", "e": "CIQ는 Customs(세관), Immigration(출입국), Quarantine(검역)의 약자입니다."},
        {"q": "IATA와 ICAO 공항 코드의 차이는?", "o": ["3글자 vs 4글자", "숫자 vs 문자", "국내 vs 국제", "같은 것"], "a": "3글자 vs 4글자", "e": "IATA 코드는 3글자(ICN), ICAO 코드는 4글자(RKSI)입니다."},
        {"q": "에이프런(Apron)이란?", "o": ["항공기 주기장", "활주로", "유도로", "터미널"], "a": "항공기 주기장", "e": "에이프런은 항공기가 승객 탑승, 화물 적재, 급유 등을 하는 주기장입니다."},
        {"q": "허브 앤 스포크(Hub and Spoke) 시스템이란?", "o": ["거점 공항 중심 노선 구조", "직항 노선 체계", "저비용 운항 방식", "화물 전용 시스템"], "a": "거점 공항 중심 노선 구조", "e": "허브 공항을 중심으로 바퀴살처럼 노선을 연결하는 운항 시스템입니다."},
        {"q": "코드쉐어(Code Share)란?", "o": ["항공사 간 좌석 공동 판매", "공항 코드 공유", "항공기 공동 운용", "마일리지 통합"], "a": "항공사 간 좌석 공동 판매", "e": "코드쉐어는 한 항공사의 항공편에 다른 항공사 편명을 부여해 공동 판매하는 것입니다."},
        {"q": "김포공항의 IATA 코드는?", "o": ["GMP", "KPO", "SEL", "KIM"], "a": "GMP", "e": "김포국제공항의 IATA 코드는 GMP입니다."},
        {"q": "PBB(탑승교)의 정식 명칭은?", "o": ["Passenger Boarding Bridge", "Passenger Bus Bridge", "Plane Boarding Bridge", "Pre-Boarding Bridge"], "a": "Passenger Boarding Bridge", "e": "PBB는 터미널과 항공기를 연결하는 탑승교(보딩 브릿지)입니다."},
    ],
    "안전/비상": [
        {"q": "항공기 비상탈출 슬라이드가 펼쳐지는 데 걸리는 시간은?", "o": ["약 6초", "약 30초", "약 1분", "약 3분"], "a": "약 6초", "e": "비상 슬라이드는 약 6초 만에 완전히 펼쳐지도록 설계되어 있습니다."},
        {"q": "산소마스크가 내려왔을 때 먼저 해야 하는 것은?", "o": ["본인 먼저 착용", "아이 먼저 착용", "안전벨트 확인", "짐 챙기기"], "a": "본인 먼저 착용", "e": "본인이 먼저 착용해야 의식을 잃지 않고 옆 사람을 도울 수 있습니다."},
        {"q": "비상착수 시 구명조끼는 언제 부풀려야 할까요?", "o": ["항공기 밖으로 나간 후", "착석 즉시", "착수 직전", "산소마스크 착용 후"], "a": "항공기 밖으로 나간 후", "e": "기내에서 부풀리면 이동이 어려우므로, 반드시 항공기 밖으로 나간 후 부풀려야 합니다."},
        {"q": "Brace Position(충격 방지 자세)에서 머리를 어디에 두어야 할까요?", "o": ["앞좌석 등받이", "무릎 위", "창문 쪽", "통로 쪽"], "a": "앞좌석 등받이", "e": "앞좌석 등받이에 머리를 대고 손으로 머리를 감싸 보호합니다."},
        {"q": "90초 규정이란?", "o": ["전 승객 90초 내 탈출 가능해야 인증", "90초 내 이륙해야 함", "90초간 산소 공급", "90초 내 착륙 허가"], "a": "전 승객 90초 내 탈출 가능해야 인증", "e": "항공기는 출구 절반만 사용해도 90초 내에 전원 탈출이 가능해야 형식 인증을 받습니다."},
        {"q": "EGPWS란 무엇인가요?", "o": ["지상 접근 경고 시스템", "엔진 고장 경보", "전자 기어 시스템", "비상 발전기"], "a": "지상 접근 경고 시스템", "e": "EGPWS(Enhanced Ground Proximity Warning System)는 지형과의 충돌을 경고하는 시스템입니다."},
        {"q": "항공기 비상구 도어의 모드 설정에서 'Armed' 상태란?", "o": ["슬라이드 자동 전개 상태", "문 잠금 상태", "문 열림 상태", "수동 모드"], "a": "슬라이드 자동 전개 상태", "e": "Armed 상태에서 문을 열면 비상 슬라이드가 자동으로 펼쳐집니다."},
        {"q": "TCAS란 무엇인가요?", "o": ["공중 충돌 방지 시스템", "객실 온도 조절", "통신 주파수 조절", "착륙 유도 장치"], "a": "공중 충돌 방지 시스템", "e": "TCAS(Traffic Collision Avoidance System)는 다른 항공기와의 충돌을 방지하는 시스템입니다."},
        {"q": "기내 화재 시 가장 위험한 것은?", "o": ["유독 가스(연기)", "열기", "불꽃", "폭발"], "a": "유독 가스(연기)", "e": "기내 화재 시 가장 큰 위험은 유독 가스로 인한 질식입니다."},
        {"q": "ELT란 무엇인가요?", "o": ["비상 위치 송신기", "비상 착륙 장치", "전자 잠금 장치", "엔진 제한 장치"], "a": "비상 위치 송신기", "e": "ELT(Emergency Locator Transmitter)는 사고 시 자동으로 위치 신호를 송신하는 장치입니다."},
    ],
    "항공 용어": [
        {"q": "ETD는 무엇의 약자인가요?", "o": ["예정 출발 시간", "예정 도착 시간", "비상 탈출문", "전자 티켓"], "a": "예정 출발 시간", "e": "ETD는 Estimated Time of Departure(예정 출발 시간)입니다."},
        {"q": "터뷸런스(Turbulence)란?", "o": ["대기 불안정으로 인한 기체 흔들림", "엔진 고장", "활주로 결함", "통신 장애"], "a": "대기 불안정으로 인한 기체 흔들림", "e": "터뷸런스는 기류 변화로 항공기가 흔들리는 현상입니다."},
        {"q": "레이오버(Layover)란?", "o": ["승무원의 외박 체류", "비행기 지연", "수하물 분실", "좌석 업그레이드"], "a": "승무원의 외박 체류", "e": "레이오버는 승무원이 목적지에서 다음 비행까지 체류하는 것입니다."},
        {"q": "노쇼(No-Show)란?", "o": ["예약 후 미탑승", "좌석 없음", "결항", "지연 도착"], "a": "예약 후 미탑승", "e": "노쇼는 예약한 승객이 탑승하지 않는 것을 말합니다."},
        {"q": "딜레이(Delay)와 캔슬(Cancel)의 차이는?", "o": ["지연 vs 결항", "출발 vs 도착", "국내 vs 국제", "같은 의미"], "a": "지연 vs 결항", "e": "딜레이는 출발 시간 지연, 캔슬은 항공편 자체가 취소되는 것입니다."},
        {"q": "오버부킹(Overbooking)이란?", "o": ["좌석 수 이상 예약 접수", "수하물 초과", "연료 과다 적재", "승객 초과 탑승"], "a": "좌석 수 이상 예약 접수", "e": "노쇼를 대비해 좌석 수보다 많은 예약을 받는 관행입니다."},
        {"q": "UM(Unaccompanied Minor)이란?", "o": ["비동반 소아 승객", "업그레이드 마일리지", "긴급 의료", "미확인 수하물"], "a": "비동반 소아 승객", "e": "UM은 보호자 없이 혼자 탑승하는 어린이 승객 서비스입니다."},
        {"q": "기내 방송에서 'Cabin Crew, doors to manual'의 의미는?", "o": ["슬라이드 해제(착륙 후)", "문 닫기", "비상 대기", "이륙 준비"], "a": "슬라이드 해제(착륙 후)", "e": "착륙 후 도어를 수동 모드로 전환하라는 의미입니다. (Armed 해제)"},
        {"q": "ATIS란?", "o": ["공항 자동 기상 정보", "항공 교통 정보", "자동 티켓 시스템", "공항 보안 시스템"], "a": "공항 자동 기상 정보", "e": "ATIS(Automatic Terminal Information Service)는 공항의 기상/활주로 정보를 자동 방송합니다."},
        {"q": "Red-eye Flight(적목 비행)란?", "o": ["야간 비행편", "위험 비행", "최단 비행", "장거리 비행"], "a": "야간 비행편", "e": "밤에 출발해 새벽에 도착하는 비행편으로, 피로로 눈이 빨개진다는 의미입니다."},
    ],
}


# ========================================
# 세션 초기화
# ========================================
DEFAULT_QUIZ_STATE = {
    "quiz_type": None,          # "airline" or "knowledge"
    "quiz_airline": None,
    "quiz_category": None,
    "quiz_questions": [],
    "quiz_index": 0,
    "quiz_score": 0,
    "quiz_answered": False,
    "quiz_finished": False,
    "last_correct": False,
    "last_answer": "",
    "last_explanation": "",
    "quiz_shuffled_options": [],
    "quiz_shuffled_for_idx": -1,
}
for k, v in DEFAULT_QUIZ_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

if "quiz_persistent_history" not in st.session_state:
    st.session_state.quiz_persistent_history = load_quiz_history()


# ========================================
# 메인 UI
# ========================================
st.title("️ 항공 퀴즈")
st.markdown("항공사 기업분석부터 항공 상식까지, 면접에 필요한 모든 지식을 퀴즈로!")

st.markdown("---")

# ========================================
# 퀴즈 타입 미선택 상태
# ========================================
if st.session_state.quiz_type is None:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px; padding: 30px; text-align: center; min-height: 200px;">
            <div style="font-size: 48px;"></div>
            <div style="font-size: 22px; font-weight: bold; margin: 10px 0;">항공사별 퀴즈</div>
            <div style="font-size: 14px; opacity: 0.8;">11개 항공사 기업분석<br>미션/비전/인재상/채용조건</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("항공사별 퀴즈 시작", use_container_width=True, key="start_airline"):
            st.session_state.quiz_type = "airline"
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f093fb, #f5576c); color: white; border-radius: 20px; padding: 30px; text-align: center; min-height: 200px;">
            <div style="font-size: 48px;"></div>
            <div style="font-size: 22px; font-weight: bold; margin: 10px 0;">항공 상식 퀴즈</div>
            <div style="font-size: 14px; opacity: 0.8;">5개 카테고리 50문제<br>기초/서비스/공항/안전/용어</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("항공 상식 퀴즈 시작", use_container_width=True, key="start_knowledge"):
            st.session_state.quiz_type = "knowledge"
            st.rerun()

    # 전체 랜덤
    st.markdown("---")
    if st.button("전체 랜덤 퀴즈 (항공사 + 상식 혼합 10문제)", type="primary", use_container_width=True):
        all_q = []
        for qs in AIRLINE_QUIZZES.values():
            all_q.extend(qs)
        for qs in KNOWLEDGE_QUIZZES.values():
            all_q.extend(qs)
        st.session_state.quiz_type = "mixed"
        st.session_state.quiz_category = "전체 랜덤"
        st.session_state.quiz_questions = random.sample(all_q, min(10, len(all_q)))
        st.session_state.quiz_index = 0
        st.session_state.quiz_score = 0
        st.session_state.quiz_answered = False
        st.session_state.quiz_shuffled_for_idx = -1
        st.session_state.quiz_finished = False
        st.rerun()

# ========================================
# 항공사 선택 화면
# ========================================
elif st.session_state.quiz_type == "airline" and st.session_state.quiz_airline is None:
    st.markdown("### 퀴즈 볼 항공사를 선택하세요")
    airlines = list(AIRLINE_QUIZZES.keys())
    cols = st.columns(3)
    for i, airline in enumerate(airlines):
        with cols[i % 3]:
            q_count = len(AIRLINE_QUIZZES[airline])
            if st.button(f"️ {airline} ({q_count}문제)", key=f"sel_{airline}", use_container_width=True):
                st.session_state.quiz_airline = airline
                questions = AIRLINE_QUIZZES[airline].copy()
                random.shuffle(questions)
                if airline in ["대한항공", "아시아나항공", "진에어", "에어부산", "에어서울"]:
                    questions.append(random.choice(MERGER_QUIZZES))
                st.session_state.quiz_questions = questions[:10]
                st.session_state.quiz_category = airline
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_answered = False
                st.session_state.quiz_shuffled_for_idx = -1
                st.session_state.quiz_finished = False
                st.rerun()

    st.markdown("---")
    if st.button("⬅️ 돌아가기"):
        st.session_state.quiz_type = None
        st.rerun()

# ========================================
# 상식 카테고리 선택 화면
# ========================================
elif st.session_state.quiz_type == "knowledge" and st.session_state.quiz_category is None:
    st.markdown("### 카테고리를 선택하세요")
    categories = list(KNOWLEDGE_QUIZZES.keys())
    cols = st.columns(3)
    for i, cat in enumerate(categories):
        with cols[i % 3]:
            q_count = len(KNOWLEDGE_QUIZZES[cat])
            if st.button(f" {cat} ({q_count}문제)", key=f"cat_{cat}", use_container_width=True):
                st.session_state.quiz_category = cat
                questions = KNOWLEDGE_QUIZZES[cat].copy()
                random.shuffle(questions)
                st.session_state.quiz_questions = questions[:10]
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_answered = False
                st.session_state.quiz_shuffled_for_idx = -1
                st.session_state.quiz_finished = False
                st.rerun()

    st.markdown("---")
    if st.button("전체 상식 랜덤 (10문제)", type="primary", use_container_width=True):
        all_knowledge = []
        for qs in KNOWLEDGE_QUIZZES.values():
            all_knowledge.extend(qs)
        st.session_state.quiz_category = "상식 랜덤"
        st.session_state.quiz_questions = random.sample(all_knowledge, min(10, len(all_knowledge)))
        st.session_state.quiz_index = 0
        st.session_state.quiz_score = 0
        st.session_state.quiz_answered = False
        st.session_state.quiz_shuffled_for_idx = -1
        st.session_state.quiz_finished = False
        st.rerun()

    if st.button("⬅️ 돌아가기"):
        st.session_state.quiz_type = None
        st.rerun()

# ========================================
# 퀴즈 진행 중
# ========================================
elif not st.session_state.quiz_finished:
    questions = st.session_state.quiz_questions
    idx = st.session_state.quiz_index
    category = st.session_state.quiz_category or ""

    st.markdown(f"### ️ {category} 퀴즈")
    progress = (idx + 1) / len(questions)
    st.progress(progress)
    st.caption(f"문제 {idx + 1} / {len(questions)} | 현재 점수: {st.session_state.quiz_score}점")

    q = questions[idx]
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px; padding: 30px; margin: 20px 0;">
        <div style="font-size: 22px; font-weight: bold;">{q['q']}</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.quiz_answered:
        if st.session_state.quiz_shuffled_for_idx != idx:
            options = q['o'].copy()
            random.shuffle(options)
            st.session_state.quiz_shuffled_options = options
            st.session_state.quiz_shuffled_for_idx = idx
        options = st.session_state.quiz_shuffled_options
        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"opt_{idx}_{i}", use_container_width=True):
                    st.session_state.quiz_answered = True
                    st.session_state.last_correct = (opt == q['a'])
                    if st.session_state.last_correct:
                        st.session_state.quiz_score += 1
                    st.session_state.last_answer = q['a']
                    st.session_state.last_explanation = q['e']
                    st.rerun()
    else:
        if st.session_state.last_correct:
            st.success("정답입니다!")
        else:
            st.error(f" 틀렸습니다. 정답: **{st.session_state.last_answer}**")
        st.info(f" {st.session_state.last_explanation}")

        if st.button("️ 다음 문제", use_container_width=True):
            if idx + 1 < len(questions):
                st.session_state.quiz_index += 1
                st.session_state.quiz_answered = False
            else:
                st.session_state.quiz_finished = True
            st.rerun()

# ========================================
# 퀴즈 완료
# ========================================
else:
    category = st.session_state.quiz_category or ""
    score = st.session_state.quiz_score
    total = len(st.session_state.quiz_questions)
    percentage = int(score / total * 100)

    if percentage >= 90:
        grade, emoji, color = "S", "", "#667eea"
    elif percentage >= 80:
        grade, emoji, color = "A", "", "#28a745"
    elif percentage >= 70:
        grade, emoji, color = "B", "", "#17a2b8"
    elif percentage >= 60:
        grade, emoji, color = "C", "", "#ffc107"
    else:
        grade, emoji, color = "D", "", "#dc3545"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}20, {color}10); border: 3px solid {color}; border-radius: 25px; padding: 40px; text-align: center; margin: 20px 0;">
        <div style="font-size: 60px;">{emoji}</div>
        <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">️ {category} 퀴즈 완료!</div>
        <div style="font-size: 48px; font-weight: bold; color: {color};">{score} / {total}</div>
        <div style="font-size: 24px; color: #666;">{percentage}% | {grade}등급</div>
    </div>
    """, unsafe_allow_html=True)

    if percentage >= 80:
        st.success(f" {category}에 대해 잘 알고 계시네요!")
    elif percentage >= 60:
        st.info("조금만 더 공부하면 완벽해요!")
    else:
        st.warning("복습이 필요합니다. 다시 도전해보세요!")

    # 기록 저장
    record = {
        "category": category,
        "type": st.session_state.quiz_type,
        "score": score,
        "total": total,
        "percentage": percentage,
        "grade": grade,
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.quiz_persistent_history.append(record)
    save_quiz_history(st.session_state.quiz_persistent_history)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("같은 퀴즈 다시", use_container_width=True):
            if st.session_state.quiz_type == "airline" and st.session_state.quiz_airline:
                questions = AIRLINE_QUIZZES[st.session_state.quiz_airline].copy()
                random.shuffle(questions)
                if st.session_state.quiz_airline in ["대한항공", "아시아나항공", "진에어", "에어부산", "에어서울"]:
                    questions.append(random.choice(MERGER_QUIZZES))
                st.session_state.quiz_questions = questions[:10]
            elif st.session_state.quiz_type == "knowledge" and st.session_state.quiz_category in KNOWLEDGE_QUIZZES:
                questions = KNOWLEDGE_QUIZZES[st.session_state.quiz_category].copy()
                random.shuffle(questions)
                st.session_state.quiz_questions = questions[:10]
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_answered = False
            st.session_state.quiz_shuffled_for_idx = -1
            st.session_state.quiz_finished = False
            st.rerun()
    with col2:
        if st.button("️ 다른 퀴즈 선택", use_container_width=True):
            st.session_state.quiz_airline = None
            st.session_state.quiz_category = None
            st.session_state.quiz_questions = []
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_answered = False
            st.session_state.quiz_shuffled_for_idx = -1
            st.session_state.quiz_finished = False
            st.rerun()
    with col3:
        if st.button("처음으로", use_container_width=True):
            for k, v in DEFAULT_QUIZ_STATE.items():
                st.session_state[k] = v
            st.rerun()

# ========================================
# 하단: 누적 기록
# ========================================
st.markdown("---")

history = st.session_state.quiz_persistent_history
if history:
    st.markdown("### 나의 퀴즈 기록")

    scores = [h["percentage"] for h in history]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 도전", f"{len(history)}회")
    with col2:
        st.metric("평균 정답률", f"{sum(scores)/len(scores):.0f}%")
    with col3:
        st.metric("최고 정답률", f"{max(scores)}%")
    with col4:
        airline_count = len(set(h["category"] for h in history if h.get("type") == "airline"))
        st.metric("도전한 항공사", f"{airline_count}개")

    with st.expander("최근 기록"):
        for h in reversed(history[-15:]):
            ts = h.get("timestamp", "")[:10]
            type_icon = "" if h.get("type") == "airline" else ""
            st.caption(f"{ts} | {type_icon} {h['category']} | {h['score']}/{h['total']} ({h['percentage']}%) | {h['grade']}등급")

st.markdown('</div>', unsafe_allow_html=True)
