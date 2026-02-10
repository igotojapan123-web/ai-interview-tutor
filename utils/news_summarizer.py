# analyzers/summarizer.py
# AI 뉴스 요약 및 면접질문 생성 (사실 기반 Only)
# 단일 뉴스 상세 버전 (데일리쿠키 스타일)
# v2.0 - 우선순위 및 필터링 규칙 적용

from openai import OpenAI
from typing import List, Dict, Optional, Tuple
import json
import re


class NewsSummarizer:
    """뉴스 요약 및 면접질문 생성 AI - 단일 뉴스 깊게 분석"""

    # ========== 제외 필터링 규칙 ==========

    # 무조건 제외 키워드 (모든 순위 공통)
    EXCLUDE_KEYWORDS = [
        # 부고/인사
        "별세", "부음", "부고", "조문", "영결식", "빈소", "발인", "장례", "유족",
        # 인사이동 단신
        "승진", "임명", "취임", "이임",
        # 정치/의회
        "의회", "국회", "의원", "지자체", "시의회", "도의회", "구의회", "시장", "도지사", "장관",
        "청문회", "국정감사", "탄핵", "대통령실",
        # 선행/기부/봉사
        "기부", "봉사", "후원", "나눔", "선행", "푸드트럭", "무료급식", "연탄", "김장", "헌혈", "장학금",
        # CSR/사회공헌
        "CSR", "사회공헌", "사회적 책임", "캠페인", "환경보호", "친환경 캠페인", "나무심기",
        # MOU/협약
        "MOU", "협약", "업무협약", "양해각서", "제휴 체결", "협력 체결", "파트너십 체결",
        # 수상/시상
        "수상", "시상", "대상 선정", "인증 획득", "표창", "감사패", "공로상",
        # 행사/이벤트
        "페스티벌", "축제", "행사 참여", "기념행사", "창립기념", "출범식", "개막식",
        # 광고성
        "프로모션", "이벤트 실시", "할인 행사", "특가", "세일", "경품",
        # 연예/스포츠
        "공항패션", "출국길", "입국길", "전지훈련", "스포츠팀", "연예인", "아이돌",
        # 과거 사고 회고
        "참사 추모", "기념식", "추모식", "희생자",
        # 학원/교육업체
        "학원", "아카데미", "교육원", "승무원학원", "취업학원", "어학원",
        # 홍보성 배출 기사
        "배출", "합격자 배출", "취업 성공",
        # 우주항공/ETF/투자
        "우주항공", "ETF", "수익률", "펀드",
    ]

    # 학원/교육업체 주체 키워드 (주체가 학원이면 제외)
    ACADEMY_SUBJECTS = [
        "학원", "아카데미", "교육원", "승무원학원", "취업학원", "어학원",
        "교육", "스쿨", "인재원", "연수원", "트레이닝센터",
    ]

    # 나쁜 "지원" 키워드 (복지/봉사/재난 관련 - 제외)
    BAD_SUPPORT_KEYWORDS = [
        "복지관 지원", "푸드트럭 지원", "봉사 지원", "무료급식 지원",
        "이재민 지원", "수해 지원", "재난 지원", "성금 지원", "장학금 지원",
        "물품 지원", "생필품 지원", "간식 지원", "도시락 지원",
        "취약계층 지원", "소외계층 지원", "독거노인 지원", "아동 지원",
    ]

    # 좋은 "지원" 키워드 (채용/노선/시스템 관련 - 포함)
    GOOD_SUPPORT_KEYWORDS = [
        "채용 지원", "입사 지원", "서류 지원", "노선 지원",
        "정부 지원", "운항 지원", "시스템 지원",
    ]

    # 제외 패턴 (정규표현식)
    EXCLUDE_PATTERNS = [
        r"\[부고\]",
        r"\[인사\]",
        r"\[공시\]",
        r"\[오늘의 공시\]",
        r"\[산업공시\]",
        r"주가.*상승",
        r"주가.*하락",
        r"시세.*등락",
        r"탑승.*후기",
        r"이용.*후기",
        # 정치/의회 패턴
        r"국회.*촉구",
        r"의원.*지적",
        r"야당.*비판",
        r"여당.*주장",
        # 과거 사고 회고 패턴
        r"\d+주기",
        r"사고.*추모",
        r"참사.*수습",
        # 정비사/조종사/사무직 채용
        r"정비사.*채용",
        r"조종사.*채용",
        r"파일럿.*채용",
        r"사무직.*채용",
        r"지상직.*채용",
        # 학원 홍보성 배출 기사
        r"\d+명\s*합격",
        r"\d+명\s*배출",
        r"합격자\s*\d+명",
        r"배출.*\d+명",
    ]

    # 항공사가 주체가 아닌 경우 제외할 주어 키워드
    NON_AIRLINE_SUBJECTS = [
        "의회", "국회", "의원", "정부", "장관", "차관", "청장",
        "시장", "도지사", "구청장", "지자체", "경찰", "검찰", "법원",
        "유족", "시민단체", "노동계", "야당", "여당", "대통령",
    ]

    # ========== 1~6순위 분류 키워드 ==========

    # 승무원 채용 관련 키워드 (포함)
    CABIN_CREW_KEYWORDS = [
        "객실승무원", "캐빈승무원", "승무원", "FA", "인턴승무원",
        "승무원 채용", "승무원 모집", "승무원 공채"
    ]

    # 비승무원 직종 키워드 (제외)
    NON_CABIN_CREW_KEYWORDS = [
        # 정비
        "정비사", "정비직", "정비 전문", "정비강사", "정비원",
        # 조종
        "조종사", "파일럿", "기장", "부기장", "운항승무원",
        # 사무/지상
        "사무직", "지상직", "공항직", "그라운드",
        # IT/개발
        "IT", "개발자", "엔지니어", "프로그래머", "데이터",
        # 기타
        "마케팅", "영업", "경영지원", "인사", "재무", "회계",
    ]

    PRIORITY_1_KEYWORDS = {
        "채용": ["채용", "공채", "모집"],  # 승무원 관련만 통과 (별도 체크)
        "서비스변경": ["기내식", "유니폼", "수하물", "라운지", "서비스 개편", "서비스 변경", "도입", "허용"],
        "기술혁신": ["AI", "인공지능", "챗봇", "디지털", "앱", "플랫폼", "시스템", "자동화", "로봇", "기술", "혁신", "업그레이드", "출시"],
        "노선": ["취항", "신규 노선", "증편", "감편", "운항 중단", "직항", "경유", "노선 확대"],
        "합병인수": ["합병", "인수", "통합", "지분", "매각", "M&A"],
        "실적": ["매출", "영업이익", "영업손실", "적자", "흑자", "실적", "분기", "연간"],
        "사건사고": ["결함", "사고", "비상착륙", "지연", "회항", "리콜", "점검", "긴급"],
        "정책규정": ["환불", "취소", "수수료", "마일리지 정책", "정책 변경", "규정"],
        "항공기도입": ["신기종", "도입", "인도", "A350", "B787", "B737", "A380", "A320"],
        "노조이슈": ["파업", "노조", "임금", "복지", "근무환경", "단체협약"]
    }

    PRIORITY_2_KEYWORDS = {
        "공항": ["인천공항", "김포공항", "제주공항", "이용객", "터미널", "확장", "개항"],
        "항공정책": ["국토부", "항공안전법", "규정", "법안", "정책", "제도"],
        "업계트렌드": ["LCC", "FSC", "저비용항공사", "업계 전망", "시장 분석", "시장 점유율"],
        "공항서비스": ["라운지", "면세점", "주차", "교통", "셔틀", "검색대"],
        "항공인프라": ["활주로", "슬롯", "관제", "항공유", "급유"]
    }

    PRIORITY_3_KEYWORDS = {
        "항공안전": ["보잉", "에어버스", "결함", "추락", "조사", "FAA", "NTSB"],
        "비자입국": ["무비자", "비자", "입국", "출국", "검역", "격리"],
        "기내트렌드": ["기내 와이파이", "좌석 트렌드", "프리미엄 이코노미", "비즈니스석"],
        "마일리지": ["마일리지", "적립", "제휴카드", "스카이패스", "아시아나클럽"],
        "항공기제조": ["보잉", "에어버스", "주문", "인도량"],
        "환경탄소": ["탄소중립", "친환경", "SAF", "지속가능"]
    }

    PRIORITY_4_KEYWORDS = {
        "항공권가격": ["항공권", "폭등", "폭락", "특가", "운임", "가격"],
        "여행수요": ["성수기", "비수기", "여행객", "출국자", "관광객"],
        "여행트렌드": ["인기 여행지", "트렌드", "핫플레이스"],
        "여행통계": ["출국자 수", "방문객 수", "통계"]
    }

    PRIORITY_5_KEYWORDS = {
        "유가": ["유가", "국제유가", "배럴", "WTI", "두바이유"],
        "환율": ["환율", "원달러", "엔화", "엔저", "엔고", "달러"],
        "유류할증료": ["유류할증료", "할증료", "인상", "인하"]
    }

    PRIORITY_6_KEYWORDS = {
        "금리": ["금리", "기준금리", "인상", "인하", "동결", "연준", "한은"],
        "경기": ["경기", "불황", "호황", "소비", "전망"],
        "글로벌": ["전쟁", "분쟁", "팬데믹", "자연재해"],
        "관광정책": ["관광", "K-관광", "방한"]
    }

    # 대상 항공사 목록
    AIRLINES_DOMESTIC = [
        "대한항공", "아시아나항공", "아시아나", "제주항공", "진에어", "티웨이항공", "티웨이",
        "에어부산", "에어서울", "에어프레미아", "이스타항공", "이스타", "에어로케이", "파라타항공"
    ]

    AIRLINES_INTERNATIONAL = [
        "델타항공", "유나이티드항공", "아메리칸항공", "에미레이트", "에미레이트항공",
        "싱가포르항공", "카타르항공", "ANA", "전일본공수", "JAL", "일본항공",
        "캐세이퍼시픽", "루프트한자", "에어프랑스", "브리티시항공", "콴타스",
        "중국동방항공", "중국남방항공", "에어차이나", "타이항공", "베트남항공",
        "라이언에어", "이지젯", "사우스웨스트"
    ]

    # ========== AI 프롬프트 ==========

    ABSOLUTE_RULES = """
## 절대 규칙 - 위반 시 응답 거부

### 1. 사실 기반 ONLY
- 제공된 뉴스 원문에 있는 정보만 사용
- 원문에 없는 내용 절대 추가 금지
- 출처 URL 필수 첨부

### 2. 창작 금지
- 추측, 예상, 가능성 언급 금지
- "~일 수 있습니다", "~로 보입니다" 사용 금지
- "~할 것으로 예상됩니다" 사용 금지
- 가상의 인터뷰, 사례, 통계 생성 금지

### 3. 할루시네이션 금지
- 날짜, 숫자, 이름, 통계는 원문 그대로만 인용
- 확실하지 않으면 해당 내용 생략
- 절대 지어내지 않음
- 모르면 "해당 정보 없음" 표시
"""

    DEEP_ANALYSIS_PROMPT = """너는 FLYREADY의 항공 뉴스 분석 AI야.
승무원 준비생에게 정확한 정보만 전달해야 해.

{rules}

## 5개 포인트 구성
1. 핵심 사실 (무엇이 일어났나)
2. 배경/원인 (왜 일어났나)
3. 상세 내용 (구체적 수치/내용)
4. 업계 영향/반응 (어떤 영향이 있나)
5. 전망/의미 (앞으로 어떻게 될까) - 원문에 있을 때만

## 작성 규칙
- 각 포인트는 원문에서 발췌한 내용만
- ~요, ~해요 체로 친근하게 작성
- 5번 포인트(전망)는 원문에 없으면 생략하고 4개만 작성
- 어려운 용어는 하단에 *표시로 설명 추가

## 금지 표현
- "~로 보입니다"
- "~일 것으로 예상됩니다"
- "~할 가능성이 있습니다"
""".format(rules=ABSOLUTE_RULES)

    QUESTION_SYSTEM_PROMPT = """너는 FLYREADY의 면접질문 생성 AI야.
뉴스 내용을 기반으로 날카롭고 깊이 있는 면접 질문을 생성해.

{rules}

## 질문 유형 3가지 (각 1개씩)

### 1. 업계/전략 관점 질문
- 항공사의 비즈니스 전략, 경쟁 구도, 업계 트렌드 관련
- 예시: "LCC가 프리미엄 좌석을 도입하면 FSC와의 차별점이 줄어드는데, LCC의 경쟁력은 어디서 나올까요?"

### 2. 승무원 관점 질문
- 객실승무원의 업무, 서비스 방식, 역할 변화와 연결
- 예시: "프리미엄 좌석 도입이 객실승무원의 서비스 방식에 어떤 변화를 가져올까요?"

### 3. 고객/서비스 관점 질문
- 고객 경험, 서비스 차별화, 고객 니즈 관련
- 예시: "프리미엄 이코노미 고객에게 어떤 차별화된 서비스를 제공해야 할까요?"

## 날카로운 질문 기준
❌ 단순 암기 질문 금지: "좌석 이름이 뭐예요?", "언제 도입했나요?"
✅ 생각이 필요한 질문: "왜?", "어떻게?", "영향은?", "당신이라면?"
✅ 승무원 업무와 연결된 질문

## 모범 답변 구조 (두괄식)
1. 결론: 핵심 답변 한 문장
2. 근거: 뉴스 내용 기반 2~3개 근거
3. 마무리: 승무원 관점에서의 다짐/의견

## 생성 규칙
- 뉴스 내용에서 직접 도출 가능한 질문과 답변만
- 답변은 뉴스 내용 기반 사실만 포함 (창작 금지)
- ~요, ~습니다 체로 자연스럽게
""".format(rules=ABSOLUTE_RULES)

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def summarize_articles(self, articles: List[Dict]) -> Dict:
        """
        뉴스 5개 선정 → 각 뉴스 3~4줄 브리핑 요약

        Returns:
            {"news": [{title, summary, source_url}, ...], "keywords": [...], "no_news": bool}
        """
        if not articles:
            return {"news": [], "keywords": [], "no_news": True}

        # 1. 제외 기사 필터링
        filtered_articles = self._filter_excluded(articles)
        print(f"[INFO] 제외 필터링: {len(articles)}개 → {len(filtered_articles)}개")

        if not filtered_articles:
            print("[WARN] 필터링 후 기사가 없습니다.")
            return {"news": [], "keywords": [], "no_news": True}

        # 2. 중복 뉴스 제거
        unique_articles = self._remove_duplicates(filtered_articles)
        print(f"[INFO] 중복 제거: {len(filtered_articles)}개 → {len(unique_articles)}개")

        # 3. 우선순위 분류
        categorized = self.categorize_articles(unique_articles)
        print(f"[INFO] 순위별 분류 완료")

        # 4. 뉴스 5개 선정 (순위별 배분)
        print(f"[INFO] 뉴스 5개 선정 시작...")
        top5 = self._select_top5_articles(categorized)

        if not top5:
            print("[WARN] 선정된 뉴스가 없습니다.")
            return {"news": [], "keywords": [], "no_news": True}

        print(f"[OK] {len(top5)}개 뉴스 선정 완료")
        for i, a in enumerate(top5, 1):
            print(f"  {i}. {a['title']}")

        # 5. 5개 뉴스 브리핑 요약 (AI)
        summaries = self._brief_summarize(top5)

        # 6. 키워드 추출
        keywords = self._extract_keywords(top5)

        return {
            "news": summaries,
            "keywords": keywords,
            "no_news": False
        }

    def _filter_excluded(self, articles: List[Dict]) -> List[Dict]:
        """제외 기사 필터링 (주체 확인 + 지원 문맥 판단 포함)"""
        filtered = []

        for article in articles:
            title = article["title"]
            text = title + " " + article.get("description", "")

            # 1. 제외 키워드 체크
            if any(kw in text for kw in self.EXCLUDE_KEYWORDS):
                continue

            # 2. 제외 패턴 체크
            skip = False
            for pattern in self.EXCLUDE_PATTERNS:
                if re.search(pattern, text):
                    skip = True
                    break

            if skip:
                continue

            # 3. "지원" 키워드 문맥 판단
            if "지원" in text:
                # 나쁜 지원 키워드가 있으면 제외
                if any(bad in text for bad in self.BAD_SUPPORT_KEYWORDS):
                    continue
                # 좋은 지원 키워드가 없고, 단순 "지원"만 있으면 추가 확인
                if not any(good in text for good in self.GOOD_SUPPORT_KEYWORDS):
                    # 복지/봉사/재난 관련 단어가 함께 있으면 제외
                    welfare_keywords = ["복지", "봉사", "재난", "이재민", "취약", "소외", "독거", "어르신"]
                    if any(wk in text for wk in welfare_keywords):
                        continue

            # 4. 학원/교육업체 주체 체크 (승무원 키워드 있어도 학원이면 제외)
            if self._is_academy_subject(title):
                continue

            # 5. 주체 확인 - 항공사가 주체인지 체크
            if not self._is_airline_subject(title, article.get("description", "")):
                continue

            filtered.append(article)

        return filtered

    def _is_academy_subject(self, title: str) -> bool:
        """
        기사의 주체가 학원/교육업체인지 확인

        예시:
        ❌ "ANC승무원학원, 58명 배출" → 주체가 학원 → 제외
        ✅ "대한항공, 승무원 채용 공고" → 주체가 항공사 → 포함
        """
        # 제목에서 주어 추출 (쉼표 기준 첫 부분)
        title_parts = re.split(r'[,]', title.strip())
        if not title_parts:
            return False

        subject_part = title_parts[0].strip()

        # 주어 위치에 학원/교육업체 키워드가 있으면 True (제외 대상)
        for academy in self.ACADEMY_SUBJECTS:
            if academy in subject_part:
                return True

        return False

    def _is_airline_subject(self, title: str, description: str) -> bool:
        """
        기사의 주체가 항공사/항공업계인지 확인

        판단 기준:
        1. 제목 시작 부분(주어 위치)에 항공사명이 있으면 OK
        2. 제목 시작 부분에 비항공사 주체가 있으면 제외
        3. 제목에 항공사명이 있어도 주어 위치가 아니면 추가 확인

        예시:
        ✅ "제주항공, 승무원 스니커즈 허용" → 주체가 제주항공
        ❌ "의회, 제주항공 참사 수습 지원" → 주체가 의회
        """
        # 제목에서 주어 추출 (쉼표, 마침표, 공백 기준 첫 부분)
        title_parts = re.split(r'[,\.\s]', title.strip())
        if not title_parts:
            return False

        # 첫 번째 의미있는 부분 (주어 위치)
        subject_part = ""
        for part in title_parts:
            part = part.strip()
            if len(part) >= 2:  # 의미있는 길이
                subject_part = part
                break

        if not subject_part:
            return False

        # 1. 주어 위치에 비항공사 주체가 있으면 제외
        for non_airline in self.NON_AIRLINE_SUBJECTS:
            if non_airline in subject_part:
                return False

        # 2. 주어 위치에 항공사명이 있으면 OK
        all_airlines = self.AIRLINES_DOMESTIC + self.AIRLINES_INTERNATIONAL
        for airline in all_airlines:
            if airline in subject_part:
                return True

        # 3. 주어 위치에 항공업계 관련 주체가 있으면 OK
        industry_subjects = [
            "인천공항", "김포공항", "제주공항", "공항공사",
            "국토부", "항공청", "보잉", "에어버스",
            "LCC", "FSC", "항공업계", "항공사",
        ]
        for subject in industry_subjects:
            if subject in subject_part:
                return True

        # 4. 제목 전체에 항공사명이 있고, 비항공사 주체가 없으면 OK
        has_airline = any(airline in title for airline in all_airlines)
        has_non_airline = any(non in title for non in self.NON_AIRLINE_SUBJECTS)

        if has_airline and not has_non_airline:
            return True

        # 5. 항공 관련 키워드가 있고 비항공사 주체가 없으면 OK
        aviation_keywords = ["항공", "비행", "승무원", "기내", "노선", "취항", "운항"]
        has_aviation = any(kw in title for kw in aviation_keywords)

        if has_aviation and not has_non_airline:
            return True

        # 그 외에는 제외
        return False

    def _is_cabin_crew_hiring(self, text: str) -> bool:
        """
        승무원 채용 기사인지 확인

        포함 조건:
        - 객실승무원, 캐빈승무원, 승무원, FA, 인턴승무원 관련 키워드

        제외 조건:
        - 정비사, 조종사, 사무직, IT, 마케팅 등 비승무원 직종
        """
        # 비승무원 직종 키워드가 있으면 제외
        for kw in self.NON_CABIN_CREW_KEYWORDS:
            if kw in text:
                return False

        # 승무원 관련 키워드가 있으면 포함
        for kw in self.CABIN_CREW_KEYWORDS:
            if kw in text:
                return True

        # 단순 "채용", "공채", "모집" 만 있고 승무원 키워드 없으면 제외
        return False

    def _remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """
        중복 뉴스 제거 (강화 버전)

        중복 판단 기준:
        1. 제목 단어 60% 이상 겹치면 → 중복
        2. 같은 항공사 + 같은 주제 → 중복
        3. 핵심 키워드 2개 이상 겹치면 → 중복 의심

        중복 발견 시 → 본문(description)이 더 긴 기사를 남김
        """
        # 먼저 본문 길이 기준 내림차순 정렬 (상세한 기사 우선)
        sorted_articles = sorted(
            articles,
            key=lambda a: len(a.get("description", "")),
            reverse=True
        )

        unique = []
        seen_titles = []
        seen_topics = set()  # (항공사, 주제) 튜플
        seen_keyword_sets = []  # 핵심 키워드 세트 리스트

        for article in sorted_articles:
            title = article["title"]
            text = title + " " + article.get("description", "")
            is_duplicate = False

            # 제목에서 핵심 단어 추출 (조사/기호 제거)
            title_clean = re.sub(r'[,.\[\]()\'\"…·\-]', ' ', title)
            title_words = set(w for w in title_clean.split() if len(w) >= 2)

            # 1. 제목 단어 60% 이상 겹치면 중복
            for seen in seen_titles:
                seen_clean = re.sub(r'[,.\[\]()\'\"…·\-]', ' ', seen)
                seen_words = set(w for w in seen_clean.split() if len(w) >= 2)
                if not title_words or not seen_words:
                    continue

                overlap = len(title_words & seen_words)
                min_len = min(len(title_words), len(seen_words))
                if min_len > 0 and overlap / min_len > 0.6:
                    is_duplicate = True
                    break

            if is_duplicate:
                continue

            # 2. 같은 항공사 + 같은 주제 → 중복
            airline = self._extract_airline(text)
            topic = self._extract_topic(text)

            if airline and topic:
                topic_key = (airline, topic)
                if topic_key in seen_topics:
                    continue
                seen_topics.add(topic_key)

            # 3. 핵심 키워드 2개 이상 겹치면 중복 의심
            # (항공사명 + 주제 키워드로 세트 구성)
            key_terms = set()
            if airline:
                key_terms.add(airline)
            if topic:
                key_terms.add(topic)
            # 제목에서 주요 명사 추출
            for w in title_words:
                if any(kw in w for kw in ["채용", "노선", "실적", "사고", "서비스", "합병",
                                           "파업", "AI", "챗봇", "터미널", "이전", "증편"]):
                    key_terms.add(w)

            if key_terms and len(key_terms) >= 2:
                for seen_keys in seen_keyword_sets:
                    common = key_terms & seen_keys
                    if len(common) >= 2:
                        is_duplicate = True
                        break

            if is_duplicate:
                continue

            seen_keyword_sets.append(key_terms)
            unique.append(article)
            seen_titles.append(title)

        return unique

    def _extract_airline(self, text: str) -> Optional[str]:
        """텍스트에서 항공사 추출"""
        all_airlines = self.AIRLINES_DOMESTIC + self.AIRLINES_INTERNATIONAL
        for airline in all_airlines:
            if airline in text:
                return airline
        return None

    def _extract_topic(self, text: str) -> Optional[str]:
        """텍스트에서 주제 추출"""
        all_keywords = {
            **self.PRIORITY_1_KEYWORDS,
            **self.PRIORITY_2_KEYWORDS,
            **self.PRIORITY_3_KEYWORDS
        }

        for topic, keywords in all_keywords.items():
            if any(kw in text for kw in keywords):
                return topic
        return None

    def categorize_articles(self, articles: List[Dict]) -> Dict[int, List[Dict]]:
        """
        기사 우선순위 분류 (1~6순위)

        Returns:
            {1: [1순위 기사들], 2: [2순위 기사들], ...}
        """
        categorized = {i: [] for i in range(1, 7)}

        for article in articles:
            text = article["title"] + " " + article.get("description", "")
            priority = self._get_priority(text)

            if priority:
                categorized[priority].append(article)

        return categorized

    def _get_priority(self, text: str) -> Optional[int]:
        """텍스트의 우선순위 반환 (1~6, 해당없으면 None)"""

        # 1순위 체크 (항공사 키워드 + 1순위 주제)
        has_airline = any(a in text for a in self.AIRLINES_DOMESTIC + self.AIRLINES_INTERNATIONAL)

        if has_airline:
            for category, keywords in self.PRIORITY_1_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    # 채용 카테고리는 승무원 관련만 통과
                    if category == "채용":
                        if not self._is_cabin_crew_hiring(text):
                            continue  # 승무원 채용 아니면 스킵
                    return 1

        # 2순위 체크
        for category, keywords in self.PRIORITY_2_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return 2

        # 3순위 체크
        for category, keywords in self.PRIORITY_3_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return 3

        # 4순위 체크
        for category, keywords in self.PRIORITY_4_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return 4

        # 5순위 체크
        for category, keywords in self.PRIORITY_5_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return 5

        # 6순위 체크 (항공/여행 연결 있어야 함)
        aviation_keywords = ["항공", "여행", "비행", "공항"]
        if any(kw in text for kw in aviation_keywords):
            for category, keywords in self.PRIORITY_6_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    return 6

        # 어떤 순위에도 해당 안 되면 None (제외)
        return None

    def _select_best_article(self, categorized: Dict[int, List[Dict]]) -> Optional[Dict]:
        """
        대표 뉴스 1개 선정 (순위별 필터링 후 선정)

        로직:
        1. 1순위 기사들 중 "좋은 기사 기준" 통과한 것만 후보로
        2. 후보 있으면 → 대표 뉴스 선정
        3. 후보 없으면 → 2순위로 내려감
        4. ... 6순위까지 반복
        5. 6순위에도 없으면 → None (뉴스 없음)
        """
        # 대표 뉴스 선정 우선순위 키워드 (같은 순위 내)
        selection_priority = [
            ["승무원 채용", "객실승무원", "캐빈승무원", "승무원 모집"],  # 승무원 채용 (최우선)
            ["서비스", "정책", "변경", "도입", "허용", "개편"],  # 서비스/정책
            ["AI", "인공지능", "디지털", "기술", "혁신", "챗봇"],  # 기술/혁신
            ["취항", "노선", "증편", "신규", "직항"],  # 노선
            ["실적", "매출", "영업이익", "흑자", "적자"],  # 실적
            ["사고", "결함", "비상", "안전"],  # 안전/사고
            ["트렌드", "업계", "전망", "시장"],  # 업계 트렌드
        ]

        # 1순위부터 순서대로 탐색
        for priority in range(1, 7):
            articles = categorized.get(priority, [])
            if not articles:
                continue

            # 순위별 좋은 기사 필터링
            good_articles = self._filter_good_articles(articles, priority)
            print(f"  {priority}순위: {len(articles)}개 → 필터 후 {len(good_articles)}개")

            if not good_articles:
                continue

            # 선정 우선순위에 따라 기사 선택
            for keywords in selection_priority:
                for article in good_articles:
                    text = article["title"] + " " + article.get("description", "")
                    if any(kw in text for kw in keywords):
                        return article

            # 선정 우선순위에 해당 없으면 첫 번째 기사
            return good_articles[0]

        return None

    def _filter_good_articles(self, articles: List[Dict], priority: int) -> List[Dict]:
        """순위별 좋은 기사 필터링"""
        good = []

        for article in articles:
            text = article["title"] + " " + article.get("description", "")

            # 공통 추가 제외 (순위별 세부 필터)
            if priority == 1:
                # 1순위: 정비사/조종사/사무직 채용 제외 (승무원만)
                if any(kw in text for kw in ["채용", "공채", "모집"]):
                    if not self._is_cabin_crew_hiring(text):
                        continue

            elif priority == 2:
                # 2순위: 단순 통계, 공항 내 행사/이벤트 제외
                if any(kw in text for kw in ["행사", "이벤트", "페스티벌"]):
                    continue

            elif priority == 3:
                # 3순위: 해외 소규모 사고 (국내 영향 없음) - 국내 항공사 언급 없으면 제외
                if any(kw in text for kw in ["사고", "결함", "추락"]):
                    all_airlines = self.AIRLINES_DOMESTIC + self.AIRLINES_INTERNATIONAL
                    if not any(airline in text for airline in all_airlines):
                        # 보잉/에어버스 관련은 포함
                        if not any(kw in text for kw in ["보잉", "에어버스", "FAA", "NTSB"]):
                            continue

            elif priority == 4:
                # 4순위: 단순 프로모션/광고, 여행 후기 제외
                if any(kw in text for kw in ["후기", "체험", "방문기"]):
                    continue

            elif priority == 5:
                # 5순위: 단순 시세만 있고 분석 없으면 제외
                analysis_keywords = ["영향", "전망", "분석", "항공", "여행"]
                if not any(kw in text for kw in analysis_keywords):
                    continue

            elif priority == 6:
                # 6순위: 항공/여행 연결 없으면 제외
                aviation_keywords = ["항공", "여행", "비행", "공항", "항공사"]
                if not any(kw in text for kw in aviation_keywords):
                    continue

            good.append(article)

        return good

    def _select_top5_articles(self, categorized: Dict[int, List[Dict]]) -> List[Dict]:
        """
        뉴스 5개 선정 (순위별 배분)

        배분 규칙:
        - 1순위 (항공사): 최대 3개
        - 2순위 (항공업계): 최대 2개
        - 3순위 (항공 이슈): 최대 1개
        - 4순위 (항공권/여행): 최대 1개
        - 5순위 (유가/환율): 최대 1개
        - 6순위 (경제/시사): 최대 1개

        부족하면 다음 순위에서 채움. 무조건 5개 채움.
        """
        max_per_priority = {1: 3, 2: 2, 3: 1, 4: 1, 5: 1, 6: 1}
        selected = []
        remaining_slots = 5

        # 1순위부터 순서대로 채움
        for priority in range(1, 7):
            if remaining_slots <= 0:
                break

            articles = categorized.get(priority, [])
            if not articles:
                continue

            # 순위별 좋은 기사 필터링
            good_articles = self._filter_good_articles(articles, priority)

            if not good_articles:
                continue

            # 이 순위에서 가져올 최대 개수
            max_count = min(max_per_priority.get(priority, 1), remaining_slots)
            take = good_articles[:max_count]

            selected.extend(take)
            remaining_slots -= len(take)

            print(f"  {priority}순위: {len(articles)}개 → 필터 후 {len(good_articles)}개 → {len(take)}개 선정")

        # 5개 미만이면 남은 순위에서 추가로 채움
        if remaining_slots > 0:
            for priority in range(1, 7):
                if remaining_slots <= 0:
                    break

                articles = categorized.get(priority, [])
                good_articles = self._filter_good_articles(articles, priority)

                for article in good_articles:
                    if article not in selected and remaining_slots > 0:
                        selected.append(article)
                        remaining_slots -= 1

        return selected[:5]

    def _brief_summarize(self, articles: List[Dict]) -> List[Dict]:
        """5개 뉴스 브리핑 요약 (AI)"""
        news_text = ""
        for i, article in enumerate(articles, 1):
            news_text += f"\n[뉴스 {i}]\n"
            news_text += f"제목: {article['title']}\n"
            news_text += f"내용: {article.get('description', '')}\n"
            news_text += f"출처: {article.get('source', '')}\n"
            news_text += f"URL: {article.get('link', '')}\n"

        prompt = f"""다음 뉴스 {len(articles)}개를 각각 브리핑 요약해줘.

{news_text}

## 뉴스당 요약 규칙 (4줄 필수)
1. 무슨 일? (핵심 사실) - 1줄
2. 왜? (원인/배경) - 1줄
3. 구체적으로? (상세 내용/수치) - 1줄
4. → 그래서? (업계 의미/영향) - 1줄 [필수!]

## 작성 규칙
- 원문에서 발췌한 내용만!
- ~요, ~해요 체로 친근하게
- 각 뉴스당 반드시 4줄 작성 (4번 화살표 줄 필수!)
- 4번(→)은 "승무원 준비생이 알아야 할 의미" 또는 "국내 항공업계에 미치는 영향"으로 작성
- 대충 요약 금지! 충분히 설명
- 뉴스당 약 150자 내외

## 해외 뉴스 처리 규칙
- 해외 항공사 뉴스는 반드시 4번(→)에서 국내 영향과 연결
- 예: 해외 LCC 구조조정 → "국내 LCC도 유사한 수익 구조를 활용 중이에요"
- 예: 보잉 결함 → "국내 항공사 보잉 기종 운항에도 영향을 줄 수 있어요"

## 출력 형식 (JSON)
{{
    "summaries": [
        {{
            "title": "뉴스 1 제목 (간결하게 정리)",
            "line1": "핵심 사실 1줄",
            "line2": "원인/배경 1줄",
            "line3": "상세 내용/수치 1줄",
            "line4": "→ 업계 의미/영향 1줄 (반드시 작성!)"
        }},
        ...
    ]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.DEEP_ANALYSIS_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            summaries = result.get("summaries", [])

            # 원본 URL 매칭
            news_list = []
            for i, s in enumerate(summaries):
                source_url = articles[i]["link"] if i < len(articles) else ""
                news_list.append({
                    "title": s.get("title", ""),
                    "line1": s.get("line1", ""),
                    "line2": s.get("line2", ""),
                    "line3": s.get("line3", ""),
                    "line4": s.get("line4", ""),
                    "source_url": source_url
                })

            return news_list

        except Exception as e:
            print(f"[ERROR] 브리핑 요약 실패: {e}")
            return []

    def _extract_keywords(self, articles: List[Dict]) -> List[str]:
        """뉴스 5개에서 핵심 키워드 3개 추출"""
        all_text = " ".join([
            a["title"] + " " + a.get("description", "")
            for a in articles
        ])

        prompt = f"""다음 뉴스들에서 오늘의 핵심 키워드 3개를 추출해줘.

{all_text}

## 규칙
- 구체적이고 임팩트 있는 키워드 (일반적 단어 금지!)
- "항공사", "항공", "LCC" 같은 뻔한 단어 금지
- 뉴스 내용을 특정할 수 있는 구체적 키워드
- 항공사명+이슈 조합 형태 권장
- 3~6글자

## 좋은 예시
- #에어서울지연 #아시아나적자 #AI화물특수
- #제주항공스니커즈 #대한항공챗봇 #인천공항확장
- #보잉결함 #유가급등 #엔저여행

## 나쁜 예시 (금지)
- #항공사 #LCC #항공업계 #뉴스 #여행

## 출력 형식 (JSON)
{{
    "keywords": ["키워드1", "키워드2", "키워드3"]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "핵심 키워드를 추출하는 AI야."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("keywords", [])

        except Exception as e:
            print(f"[ERROR] 키워드 추출 실패: {e}")
            return []

    def _deep_analyze(self, article: Dict) -> Dict:
        """5개 포인트로 깊게 분석"""
        prompt = f"""다음 뉴스를 5개 포인트로 깊게 분석해줘.

[뉴스 정보]
제목: {article['title']}
내용: {article.get('description', '')}
날짜: {article.get('pub_date', '')}
출처: {article.get('source', '')}

## 5개 포인트 구성
1. 핵심 사실 (무엇이 일어났나)
2. 배경/원인 (왜 일어났나)
3. 상세 내용 (구체적 수치/내용)
4. 업계 영향/반응 (어떤 영향이 있나)
5. 전망/의미 (원문에 있을 때만, 없으면 생략)

## 요청사항
- 각 포인트는 원문에서 발췌한 내용만!
- 각 포인트는 1~2문장, ~요/~해요 체로 친근하게
- 원문에 없는 내용은 절대 추가 금지
- 5번 포인트는 원문에 전망이 없으면 생략 (4개만 작성)
- 어려운 용어가 있으면 term_explanation에 설명 추가

## 출력 형식 (JSON)
{{
    "points": [
        "1번 포인트 내용 (~요 체)",
        "2번 포인트 내용 (~요 체)",
        "3번 포인트 내용 (~요 체)",
        "4번 포인트 내용 (~요 체)",
        "5번 포인트 내용 (원문에 있을 때만)"
    ],
    "term_explanation": "용어: 설명 (없으면 빈 문자열)"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.DEEP_ANALYSIS_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"[ERROR] 분석 생성 실패: {e}")
            return {"points": [], "term_explanation": ""}

    def _generate_questions(self, article: Dict) -> List[Dict]:
        """면접 질문 + 모범답변 생성"""
        prompt = f"""다음 뉴스 기사를 기반으로 날카로운 면접 질문 3개와 모범답변을 생성해줘.

[뉴스 정보]
제목: {article['title']}
내용: {article.get('description', '')}

## 질문 유형 (각 1개씩, 총 3개)

### 1번 질문: 업계/전략 관점
- 항공사 비즈니스 전략, 경쟁 구도, 업계 트렌드 분석
- "왜 이런 결정을 했을까?", "경쟁사 대비 어떤 의미?"

### 2번 질문: 승무원 관점
- 객실승무원 업무/역할 변화와 연결
- "승무원 서비스 방식에 어떤 변화?", "승무원으로서 어떻게 대응?"

### 3번 질문: 고객/서비스 관점
- 고객 경험, 서비스 차별화
- "고객에게 어떤 가치?", "어떤 서비스를 제공해야?"

## 질문 작성 규칙
❌ 금지: "~가 뭔가요?", "언제 ~했나요?" (단순 암기)
✅ 권장: "왜 ~했을까요?", "어떤 영향이?", "당신이라면?" (생각 필요)

## 모범답변 구조
1. [결론] 핵심 답변 1문장
2. [근거] 뉴스 기반 근거 2~3개
3. [마무리] 승무원 관점 다짐/의견 1문장

## 출력 형식 (JSON)
{{
    "questions": [
        {{
            "type": "업계/전략",
            "question": "질문 내용",
            "answer": "모범답변 (결론-근거-마무리 구조)"
        }},
        {{
            "type": "승무원",
            "question": "질문 내용",
            "answer": "모범답변"
        }},
        {{
            "type": "고객/서비스",
            "question": "질문 내용",
            "answer": "모범답변"
        }}
    ]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.QUESTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("questions", [])

        except Exception as e:
            print(f"[ERROR] 질문 생성 실패: {e}")
            return []


def test_summarizer():
    """요약기 테스트"""
    import os

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY 환경변수를 설정하세요.")
        return

    summarizer = NewsSummarizer(api_key)

    # 테스트 기사
    test_articles = [
        {
            "title": "제주항공, 승무원 운동화 착용 허용",
            "description": "제주항공이 객실승무원의 운동화 착용을 허용한다고 밝혔다. 기존에는 검정색 구두만 착용 가능했으나, 이번 달부터 브랜드 로고가 없는 흰색 또는 검정색 운동화도 선택할 수 있다. 제주항공 관계자는 승무원들의 건강과 편의를 위한 조치라고 설명했다.",
            "link": "https://example.com/news1",
            "source": "연합뉴스",
            "pub_date": "2026-02-03"
        },
        {
            "title": "[부고] OOO씨 별세",
            "description": "부고 기사입니다.",
            "link": "https://example.com/news2",
            "source": "연합뉴스",
            "pub_date": "2026-02-03"
        },
        {
            "title": "대한항공 주가 3% 상승",
            "description": "단순 주가 기사입니다.",
            "link": "https://example.com/news3",
            "source": "연합뉴스",
            "pub_date": "2026-02-03"
        }
    ]

    result = summarizer.summarize_articles(test_articles)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_summarizer()
