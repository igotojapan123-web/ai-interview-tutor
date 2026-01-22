# pages/14_항공사퀴즈.py
# 항공사 퀴즈 - 항공사별 10문제 심층 퀴즈

import streamlit as st
import random
from typing import List, Dict, Any

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth_utils import check_tester_password

st.set_page_config(page_title="항공사 퀴즈", page_icon="🎯", layout="wide")

# 깔끔한 네비게이션 적용
try:
    from nav_utils import render_sidebar
    render_sidebar(current_page="항공사퀴즈")
except ImportError:
    pass

st.markdown('<meta name="google" content="notranslate"><style>html{translate:no;}</style>', unsafe_allow_html=True)
st.markdown('<div translate="no" class="notranslate">', unsafe_allow_html=True)

# 비밀번호
check_tester_password()

# ========================================
# 항공사별 상세 퀴즈 데이터
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
        {"q": "아시아나항공 허브 공항이 아닌 것은?", "o": ["청주국제공항", "인천국제공항", "김포국제공항", ""], "a": "청주국제공항", "e": "아시아나항공 허브 공항은 인천국제공항과 김포국제공항입니다."},
        {"q": "아시아나항공의 경영 철학 핵심이 아닌 것은?", "o": ["가격 경쟁력", "최고 수준의 안전", "정성 어린 서비스", "윤리/환경/상생 경영"], "a": "가격 경쟁력", "e": "아시아나항공 경영 철학은 안전 최우선, 고객 만족, 지속 가능 성장, 사회적 책임입니다."},
        {"q": "아시아나항공 합병 상대 항공사는?", "o": ["대한항공", "진에어", "제주항공", "에어부산"], "a": "대한항공", "e": "2024년 12월 대한항공이 아시아나항공 지분 63.88%를 인수하며 합병이 완료되었습니다."},
        {"q": "아시아나항공이 속한 항공사 유형은?", "o": ["FSC (대형항공사)", "LCC (저비용항공사)", "HSC (하이브리드)", "지역항공사"], "a": "FSC (대형항공사)", "e": "아시아나항공은 FSC(Full Service Carrier) 대형항공사입니다."},
        {"q": "아시아나항공 자회사 LCC가 아닌 것은?", "o": ["진에어", "에어부산", "에어서울", ""], "a": "진에어", "e": "진에어는 대한항공 계열이고, 에어부산과 에어서울이 아시아나항공 자회사입니다."},
    ],
    "진에어": [
        {"q": "진에어의 슬로건은?", "o": ["Fly, better fly", "Fun, Young, Dynamic", "Smart Travel", "Joy Flight"], "a": "Fly, better fly", "e": "진에어 슬로건은 'Fly, better fly'입니다. (주의: 브랜드 문장 'Fun, Young, Dynamic'과 구분)"},
        {"q": "진에어 핵심가치 4가지(4 Core Values)에 포함되지 않는 것은?", "o": ["저비용", "SAFETY", "PRACTICALITY", "DELIGHT"], "a": "저비용", "e": "진에어 4 Core Values는 SAFETY, PRACTICALITY, CUSTOMER SERVICE, DELIGHT입니다."},
        {"q": "진에어 인재상 '5 JINISM'에 포함되지 않는 것은?", "o": ["JINIMUM", "JINIABLE", "JINIFUL", "JINIQUE"], "a": "JINIMUM", "e": "5 JINISM은 JINIABLE, JINIFUL, JINIVELY, JINISH, JINIQUE입니다."},
        {"q": "진에어의 지배기업(최대주주)은?", "o": ["대한항공", "한진칼", "아시아나항공", "제주항공"], "a": "대한항공", "e": "한진칼이 보유하던 진에어 지분 54.91%를 대한항공이 취득하여 지배기업이 되었습니다."},
        {"q": "진에어가 도입한 차세대 기종은?", "o": ["B737-8(MAX)", "A320neo", "B787", "A350"], "a": "B737-8(MAX)", "e": "진에어는 B737-8 기종을 도입하여 효율성과 항속거리를 개선했습니다."},
        {"q": "진에어가 운항 재개한 중대형기는?", "o": ["B777-200ER", "A330", "B787", "B747"], "a": "B777-200ER", "e": "진에어는 B777-200ER 운항을 재개하여 국제선에 투입했습니다."},
        {"q": "진에어가 강조하는 독자적 가치 키워드는?", "o": ["실용(Practicality)", "럭셔리", "고급화", "프리미엄"], "a": "실용(Practicality)", "e": "진에어는 LCC임에도 '실용(Practicality)'을 독립 가치로 강조합니다."},
        {"q": "통합 LCC 출범 예정 연도는?", "o": ["2027년", "2025년", "2026년", "2028년"], "a": "2027년", "e": "진에어를 중심으로 2027년 통합 LCC 출범이 예정되어 있습니다."},
        {"q": "진에어 영어 지원자격 TOEIC 기준은?", "o": ["550점 이상", "600점 이상", "700점 이상", "제한 없음"], "a": "550점 이상", "e": "진에어 영어 기준은 TOEIC 550점 / TOEIC Speaking IM1 / OPIc IM 이상입니다."},
        {"q": "진에어와 통합 예정인 LCC가 아닌 것은?", "o": ["제주항공", "에어부산", "에어서울", ""], "a": "제주항공", "e": "진에어, 에어부산, 에어서울 3사가 통합 LCC로 출범 예정입니다."},
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
        {"q": "제주항공 언어특기전형 대상 언어가 아닌 것은?", "o": ["베트남어", "일본어", "중국어", ""], "a": "베트남어", "e": "제주항공 언어특기전형은 일본어, 중국어 특기자를 대상으로 합니다."},
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
        {"q": "에어서울 우대 외국어가 아닌 것은?", "o": ["베트남어", "중국어", "일본어", ""], "a": "베트남어", "e": "에어서울은 아시아 노선 중심으로 중국어, 일본어 우수자를 우대합니다."},
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
        {"q": "에어로케이 영어 지원자격 기준은?", "o": ["TOEIC Speaking IM1 / OPIc IM1 이상", "TOEIC 600점 이상", "TOEIC 700점 이상", "제한 없음"], "a": "TOEIC Speaking IM1 / OPIc IM1 이상", "e": "에어로케이 영어 기준은 영어/중국어/일본어 TOEIC Speaking IM1 / OPIc IM1 이상입니다."},
        {"q": "에어로케이 슬로건은?", "o": ["새로운 하늘길", "청주의 날개", "하늘을 열다", "행복한 비행"], "a": "새로운 하늘길", "e": "에어로케이 슬로건은 '새로운 하늘길'입니다."},
        {"q": "에어로케이가 우대하는 거주 경력은?", "o": ["영어권/중국/일본 3년 이상 거주자", "유럽 거주자", "동남아 거주자", "미국 거주자"], "a": "영어권/중국/일본 3년 이상 거주자", "e": "에어로케이는 영어권/중국/일본 3년 이상 거주자를 우대합니다."},
        {"q": "에어로케이 항공사 유형은?", "o": ["LCC (저비용항공사)", "FSC (대형항공사)", "HSC (하이브리드)", "지역항공사"], "a": "LCC (저비용항공사)", "e": "에어로케이는 청주 거점 소형 LCC입니다."},
        {"q": "에어로케이 단일기종 운용의 장점이 아닌 것은?", "o": ["다양한 노선 확대", "조종사 훈련 단순화", "정비 비용 절감", "스케줄 운영 단순화"], "a": "다양한 노선 확대", "e": "단일기종의 장점은 훈련 단순화, 정비 비용 절감, 운영 단순화입니다."},
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
        {"q": "에어프레미아가 운영하지 않는 좌석 클래스는?", "o": ["비즈니스 클래스", "프리미엄 이코노미", "이코노미", ""], "a": "비즈니스 클래스", "e": "에어프레미아는 비즈니스 클래스를 운영하지 않습니다."},
        {"q": "에어프레미아 주요 주주로 참여한 기업은?", "o": ["타이어뱅크", "대한항공", "AK홀딩스", "한진칼"], "a": "타이어뱅크", "e": "에어프레미아는 타이어뱅크가 주요 주주로 참여한 독립 민간 자본 기반 항공사입니다."},
    ],
    "파라타항공": [
        {"q": "파라타항공의 전신(이전 이름)은?", "o": ["플라이강원", "에어강원", "강원에어", "스카이강원"], "a": "플라이강원", "e": "파라타항공은 플라이강원의 후신입니다."},
        {"q": "파라타항공을 인수한 기업은?", "o": ["위닉스(WINIX)", "삼성", "LG", "SK"], "a": "위닉스(WINIX)", "e": "생활가전 기업 위닉스가 2024년 8월 플라이강원을 인수했습니다."},
        {"q": "파라타항공 슬로건은?", "o": ["Fly new", "New Sky", "Fresh Air", "Clean Flight"], "a": "Fly new", "e": "파라타항공 슬로건은 'Fly new'입니다."},
        {"q": "파라타항공 브랜드 철학은?", "o": ["PARAdigm(패러다임)을 바꾸는 Trustworthy Airlines", "최고의 서비스", "안전 제일", "고객 감동"], "a": "PARAdigm(패러다임)을 바꾸는 Trustworthy Airlines", "e": "PARATA는 여행 경험의 패러다임을 바꾸는 신뢰할 수 있는 항공사를 의미합니다."},
        {"q": "파라타항공 거점 공항은?", "o": ["양양공항", "인천공항", "김포공항", "청주공항"], "a": "양양공항", "e": "파라타항공은 양양공항을 거점으로 합니다."},
        {"q": "파라타항공이 도입한 대형기는?", "o": ["A330-200", "B777", "B787", "A350"], "a": "A330-200", "e": "파라타항공은 A330-200(1호기)를 도입했습니다."},
        {"q": "파라타항공 채용 시 필수 제출 서류는?", "o": ["국민체력100 체력평가 결과서", "영어성적표", "자격증", "추천서"], "a": "국민체력100 체력평가 결과서", "e": "파라타항공은 국민체력100 체력평가 결과서 제출을 필수화했습니다."},
        {"q": "파라타항공 영어 지원자격 TOEIC 기준은?", "o": ["650점 이상", "550점 이상", "600점 이상", "700점 이상"], "a": "650점 이상", "e": "파라타항공 영어 기준은 TOEIC 650점 / TOEIC Speaking IM / OPIc IM 이상입니다."},
        {"q": "파라타항공 CI의 특징(A-Bird)은?", "o": ["PARATA 철자의 3개 A를 새로 형상화", "비행기 모양", "태극 문양", "강원도 산"], "a": "PARATA 철자의 3개 A를 새로 형상화", "e": "파라타항공 CI는 PARATA의 3개 A를 새(A-Bird)로 형상화한 심볼입니다."},
        {"q": "파라타항공 고객가치 키워드가 아닌 것은?", "o": ["고급스러움", "투명함", "쾌적함", "신뢰"], "a": "고급스러움", "e": "파라타항공 고객가치는 투명함, 쾌적함, 신뢰, 안정감입니다."},
        {"q": "파라타항공 슬로건은?", "o": ["새로운 하늘, 새로운 가치", "Fly new", "강원의 날개", "하늘을 열다"], "a": "새로운 하늘, 새로운 가치", "e": "파라타항공 슬로건은 '새로운 하늘, 새로운 가치'입니다."},
        {"q": "파라타항공의 항공사 운영 전략은?", "o": ["대형기+소형기 하이브리드", "단일기종 LCC", "대형기만 운용", "소형기만 운용"], "a": "대형기+소형기 하이브리드", "e": "파라타항공은 A330-200과 A320-200을 함께 운용하는 하이브리드 전략입니다."},
    ],
}

# 공통 퀴즈 (대한항공-아시아나 합병 관련)
MERGER_QUIZZES = [
    {"q": "대한항공-아시아나 합병 법적 완료 연도는?", "o": ["2024년", "2023년", "2025년", "2022년"], "a": "2024년", "e": "2024년 12월 12일 대한항공이 아시아나 지분 63.88%를 인수하며 법적 절차가 완료되었습니다."},
    {"q": "통합 항공사를 지칭하는 용어는?", "o": ["메가캐리어", "슈퍼캐리어", "울트라캐리어", "하이퍼캐리어"], "a": "메가캐리어", "e": "대한항공-아시아나 통합으로 '메가캐리어(초대형 항공사)'가 출현합니다."},
    {"q": "통합 LCC(진에어+에어부산+에어서울) 출범 예정 연도는?", "o": ["2027년", "2025년", "2026년", "2028년"], "a": "2027년", "e": "진에어를 중심으로 2027년 통합 LCC 출범이 예정되어 있습니다."},
    {"q": "합병으로 양도 조건이 된 사업부는?", "o": ["아시아나 화물 사업부 (Air Zeta로)", "아시아나 여객 사업부", "대한항공 화물 사업부", "대한항공 기내식 사업부"], "a": "아시아나 화물 사업부 (Air Zeta로)", "e": "규제 조건으로 아시아나 화물 사업부를 Air Zeta(구 에어인천)로 양도했습니다."},
    {"q": "합병 후 객실승무원에게 더 중요해지는 역량은?", "o": ["팀 기반 표준 수행 역량", "개인 서비스 감각", "화려한 이력", "외모"], "a": "팀 기반 표준 수행 역량", "e": "메가캐리어는 개인차보다 일관성을 중시하므로 표준 준수 능력이 중요합니다."},
]

# 세션 초기화
for k, v in {"quiz_airline": None, "quiz_questions": [], "quiz_index": 0, "quiz_score": 0, "quiz_answered": False, "quiz_finished": False, "quiz_history": []}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ========================================
# 메인
# ========================================
st.title("🎯 항공사 퀴즈")
st.markdown("항공사를 선택하고 10문제를 풀어보세요!")

# 항공사 미선택 상태
if st.session_state.quiz_airline is None:
    st.markdown("### ✈️ 퀴즈 볼 항공사를 선택하세요")

    airlines = list(AIRLINE_QUIZZES.keys())

    # 항공사 버튼
    cols = st.columns(3)
    for i, airline in enumerate(airlines):
        with cols[i % 3]:
            if st.button(f"✈️ {airline}", key=f"select_{airline}", use_container_width=True):
                # 퀴즈 시작
                st.session_state.quiz_airline = airline
                questions = AIRLINE_QUIZZES[airline].copy()
                random.shuffle(questions)
                # 합병 관련 퀴즈 1개 추가 (대한항공, 아시아나, 진에어, 에어부산, 에어서울인 경우)
                if airline in ["대한항공", "아시아나항공", "진에어", "에어부산", "에어서울"]:
                    questions.append(random.choice(MERGER_QUIZZES))
                st.session_state.quiz_questions = questions[:10]
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_answered = False
                st.session_state.quiz_finished = False
                st.rerun()

    st.markdown("---")
    st.info("💡 각 항공사별 10문제가 출제됩니다. 핵심가치, 인재상, 채용조건, 최신이슈 등을 테스트합니다!")

# 퀴즈 진행 중
elif not st.session_state.quiz_finished:
    airline = st.session_state.quiz_airline
    questions = st.session_state.quiz_questions
    idx = st.session_state.quiz_index

    # 진행 상황
    st.markdown(f"### ✈️ {airline} 퀴즈")
    progress = (idx + 1) / len(questions)
    st.progress(progress)
    st.caption(f"문제 {idx + 1} / {len(questions)} | 현재 점수: {st.session_state.quiz_score}점")

    # 현재 문제
    q = questions[idx]

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 20px; padding: 30px; margin: 20px 0;">
        <div style="font-size: 22px; font-weight: bold;">{q['q']}</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.quiz_answered:
        # 선택지
        options = q['o'].copy()
        random.shuffle(options)

        cols = st.columns(2)
        for i, opt in enumerate(options):
            with cols[i % 2]:
                if st.button(opt, key=f"opt_{idx}_{i}", use_container_width=True):
                    st.session_state.quiz_answered = True
                    if opt == q['a']:
                        st.session_state.quiz_score += 1
                        st.session_state.last_correct = True
                    else:
                        st.session_state.last_correct = False
                    st.session_state.last_answer = q['a']
                    st.session_state.last_explanation = q['e']
                    st.rerun()
    else:
        # 정답 확인
        if st.session_state.last_correct:
            st.success("🎉 정답입니다!")
        else:
            st.error(f"❌ 틀렸습니다. 정답: **{st.session_state.last_answer}**")

        st.info(f"💡 {st.session_state.last_explanation}")

        if st.button("➡️ 다음 문제", use_container_width=True):
            if idx + 1 < len(questions):
                st.session_state.quiz_index += 1
                st.session_state.quiz_answered = False
            else:
                st.session_state.quiz_finished = True
            st.rerun()

# 퀴즈 완료
else:
    airline = st.session_state.quiz_airline
    score = st.session_state.quiz_score
    total = len(st.session_state.quiz_questions)
    percentage = int(score / total * 100)

    # 등급
    if percentage >= 90:
        grade, emoji, color = "S", "🏆", "#667eea"
    elif percentage >= 80:
        grade, emoji, color = "A", "🌟", "#28a745"
    elif percentage >= 70:
        grade, emoji, color = "B", "👍", "#17a2b8"
    elif percentage >= 60:
        grade, emoji, color = "C", "💪", "#ffc107"
    else:
        grade, emoji, color = "D", "📚", "#dc3545"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color}20, {color}10); border: 3px solid {color}; border-radius: 25px; padding: 40px; text-align: center; margin: 20px 0;">
        <div style="font-size: 60px;">{emoji}</div>
        <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">✈️ {airline} 퀴즈 완료!</div>
        <div style="font-size: 48px; font-weight: bold; color: {color};">{score} / {total}</div>
        <div style="font-size: 24px; color: #666;">{percentage}% | {grade}등급</div>
    </div>
    """, unsafe_allow_html=True)

    if percentage >= 80:
        st.success(f"🎉 {airline}에 대해 잘 알고 계시네요!")
    elif percentage >= 60:
        st.info(f"👍 조금만 더 공부하면 완벽해요!")
    else:
        st.warning(f"📚 {airline} 기업분석을 더 공부해보세요!")

    # 기록 저장
    st.session_state.quiz_history.append({"airline": airline, "score": score, "total": total})

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 같은 항공사 다시", use_container_width=True):
            questions = AIRLINE_QUIZZES[airline].copy()
            random.shuffle(questions)
            if airline in ["대한항공", "아시아나항공", "진에어", "에어부산", "에어서울"]:
                questions.append(random.choice(MERGER_QUIZZES))
            st.session_state.quiz_questions = questions[:10]
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_answered = False
            st.session_state.quiz_finished = False
            st.rerun()
    with col2:
        if st.button("✈️ 다른 항공사 선택", use_container_width=True):
            st.session_state.quiz_airline = None
            st.session_state.quiz_questions = []
            st.session_state.quiz_index = 0
            st.session_state.quiz_score = 0
            st.session_state.quiz_answered = False
            st.session_state.quiz_finished = False
            st.rerun()

# 기록 표시
if st.session_state.quiz_history:
    st.markdown("---")
    with st.expander(f"📊 퀴즈 기록 ({len(st.session_state.quiz_history)}회)"):
        for i, h in enumerate(reversed(st.session_state.quiz_history[-10:]), 1):
            pct = int(h['score'] / h['total'] * 100)
            st.markdown(f"**{i}.** {h['airline']} - {h['score']}/{h['total']} ({pct}%)")

st.markdown('</div>', unsafe_allow_html=True)
