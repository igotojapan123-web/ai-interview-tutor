"""
대한항공 면접 질문 데이터베이스
출처: 기출 문제 및 기출 패턴 기반
"""

QUESTIONS = [
    # ===== 인성/공통 질문 =====
    {
        "id": 1,
        "question": "간단하게 자기소개 해주세요.",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 2,
        "tip": "1분 내외로 핵심만. 대한항공과의 연결점 포함"
    },
    {
        "id": 2,
        "question": "대한항공에 왜 지원하셨나요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "대한항공만의 차별점(글로벌 네트워크, KE Way 등) 구체적으로 언급"
    },
    {
        "id": 3,
        "question": "대한항공의 'KE Way'에 대해 알고 계신가요? 본인과 어떻게 맞다고 생각하시나요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 4,
        "tip": "Beyond Excellence, Journey Together, Better Tomorrow 숙지 필수"
    },
    {
        "id": 4,
        "question": "본인의 강점과 약점을 말씀해주세요.",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "약점은 개선 노력과 함께 언급"
    },
    {
        "id": 5,
        "question": "'Beyond Excellence'를 실현하기 위해 어떤 노력을 하셨나요?",
        "category": "인재상",
        "round": "1차",
        "source": "기출패턴",
        "difficulty": 4,
        "tip": "최고를 향한 구체적인 노력 사례 필요"
    },
    {
        "id": 6,
        "question": "대한항공 승무원이 되고 싶은 이유를 구체적으로 말씀해주세요.",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "단순 동경이 아닌, 직무 이해 기반 답변"
    },
    {
        "id": 7,
        "question": "대한항공에 대해 알고 있는 것을 말씀해주세요.",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "기업 정보, 최근 뉴스, 노선 등 팩트 기반"
    },
    {
        "id": 8,
        "question": "본인을 한 단어로 표현한다면?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 2,
        "tip": "승무원 역량과 연결되는 키워드 + 근거"
    },
    {
        "id": 9,
        "question": "마지막으로 하고 싶은 말씀이 있으신가요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 2,
        "tip": "감사 인사 + 핵심 어필 포인트 요약"
    },
    {
        "id": 10,
        "question": "최근 대한항공 관련 뉴스 중 인상 깊었던 것은 무엇인가요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 4,
        "tip": "아시아나 합병, 노선 확장, 신기재 도입 등 최신 이슈"
    },
    {
        "id": 11,
        "question": "대한항공의 글로벌 네트워크에 대해 어떻게 생각하시나요?",
        "category": "인성",
        "round": "1차",
        "source": "기출패턴",
        "difficulty": 3,
        "tip": "스카이팀, 취항 도시 수, 허브 공항 등 숙지"
    },
    {
        "id": 12,
        "question": "승무원이라는 직업에 대해 어떤 각오를 갖고 계신가요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "체력, 서비스, 안전에 대한 책임감"
    },

    # ===== 인재상/가치관 질문 =====
    {
        "id": 13,
        "question": "대한항공 인재상 중 본인과 가장 맞는 것은?",
        "category": "인재상",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "진취성, 국제감각, 서비스정신, 성실, 팀워크 중 선택"
    },
    {
        "id": 14,
        "question": "'Journey Together'를 어떻게 실천하시겠습니까?",
        "category": "인재상",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 4,
        "tip": "팀워크와 동반 성장 경험 사례"
    },
    {
        "id": 15,
        "question": "'Better Tomorrow'를 위해 승무원으로서 어떤 기여를 하시겠습니까?",
        "category": "인재상",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 4,
        "tip": "지속가능성, 환경, 사회적 책임 관점"
    },
    {
        "id": 16,
        "question": "팀워크를 발휘한 가장 기억에 남는 경험은 무엇인가요?",
        "category": "인재상",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "STAR 기법으로 구체적 사례"
    },
    {
        "id": 17,
        "question": "국제적 감각을 키우기 위해 어떤 노력을 하셨나요?",
        "category": "인재상",
        "round": "1차",
        "source": "기출패턴",
        "difficulty": 3,
        "tip": "어학, 해외 경험, 다문화 이해 등"
    },
    {
        "id": 18,
        "question": "서비스 정신을 발휘한 경험을 말씀해주세요.",
        "category": "인재상",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "고객 만족을 위한 구체적 행동"
    },
    {
        "id": 19,
        "question": "성실함을 증명할 수 있는 경험이 있으신가요?",
        "category": "인재상",
        "round": "1차",
        "source": "기출패턴",
        "difficulty": 3,
        "tip": "꾸준함, 책임감, 완수한 경험"
    },
    {
        "id": 20,
        "question": "진취적으로 도전한 경험을 말씀해주세요.",
        "category": "인재상",
        "round": "1차",
        "source": "기출",
        "difficulty": 3,
        "tip": "새로운 시도, 어려움 극복 사례"
    },

    # ===== 서비스/상황 질문 =====
    {
        "id": 21,
        "question": "기내에서 승객이 불만을 표출하면 어떻게 대응하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "경청 → 공감 → 해결책 → 후속조치"
    },
    {
        "id": 22,
        "question": "퍼스트클래스 VIP 승객이 무리한 요청을 하면 어떻게 하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 5,
        "tip": "정중한 거절과 대안 제시"
    },
    {
        "id": 23,
        "question": "국제선 장거리 비행 중 컨디션 관리는 어떻게 하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 3,
        "tip": "체력 관리, 휴식, 수분 섭취 등"
    },
    {
        "id": 24,
        "question": "외국인 승객과의 의사소통 문제가 생기면 어떻게 해결하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "비언어적 소통, 동료 도움, 번역 도구"
    },
    {
        "id": 25,
        "question": "글로벌 항공사 대한항공의 이미지를 위해 어떤 서비스를 하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 4,
        "tip": "한국 문화 대표, 글로벌 스탠다드"
    },
    {
        "id": 26,
        "question": "동료 승무원이 실수했을 때 어떻게 대처하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "팀워크 유지, 문제 해결 우선"
    },
    {
        "id": 27,
        "question": "기내에서 승객 간 다툼이 발생하면 어떻게 하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 5,
        "tip": "중재, 분리, 안전 확보, 보고"
    },
    {
        "id": 28,
        "question": "비즈니스석 승객이 이코노미석으로 강제 이동해야 하는 상황에서 어떻게 안내하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 5,
        "tip": "진심어린 사과, 보상 안내, 대안 제시"
    },
    {
        "id": 29,
        "question": "기내 안전 수칙을 따르지 않는 승객이 있다면 어떻게 하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "안전이 최우선, 정중하지만 단호하게"
    },
    {
        "id": 30,
        "question": "승객이 기내식에 대해 강하게 불만을 제기하면 어떻게 하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "사과, 대안 제시, 향후 개선 약속"
    },
    {
        "id": 31,
        "question": "의료 응급상황이 발생하면 어떻게 대처하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 5,
        "tip": "절차 숙지: 의료진 호출, 기장 보고, 응급장비"
    },
    {
        "id": 32,
        "question": "기내에서 아이가 계속 울면 어떻게 대처하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출",
        "difficulty": 3,
        "tip": "보호자 배려, 주변 승객 양해 구하기"
    },
    {
        "id": 33,
        "question": "승객이 타 항공사의 서비스가 더 좋다고 비교하면 어떻게 응대하시겠습니까?",
        "category": "서비스",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 4,
        "tip": "경청, 대한항공 강점 자연스럽게 어필"
    },

    # ===== 인성 심화/2차 면접 =====
    {
        "id": 34,
        "question": "대한항공 승무원으로서 10년 후 어떤 모습이고 싶으신가요?",
        "category": "인성",
        "round": "2차",
        "source": "기출",
        "difficulty": 3,
        "tip": "성장 비전, 회사 기여 방향"
    },
    {
        "id": 35,
        "question": "글로벌 프리미엄 항공사 승무원에게 가장 중요한 자질은 무엇인가요?",
        "category": "인성",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 4,
        "tip": "FSC 승무원의 역할 이해"
    },
    {
        "id": 36,
        "question": "왜 LCC가 아닌 대한항공인가요?",
        "category": "인성",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "FSC vs LCC 서비스 차이 이해"
    },
    {
        "id": 37,
        "question": "스트레스 상황에서 프로페셔널함을 유지하는 방법은?",
        "category": "인성",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "감정 조절, 상황 분리 능력"
    },
    {
        "id": 38,
        "question": "본인이 생각하는 최고의 서비스란 무엇인가요?",
        "category": "인성",
        "round": "2차",
        "source": "기출",
        "difficulty": 3,
        "tip": "고객 관점에서 정의"
    },
    {
        "id": 39,
        "question": "체력 관리를 어떻게 하고 계신가요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 2,
        "tip": "구체적인 운동, 생활 습관"
    },
    {
        "id": 40,
        "question": "본인만의 스트레스 해소법은 무엇인가요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 2,
        "tip": "건강한 방법 제시"
    },
    {
        "id": 41,
        "question": "대한항공 승무원으로서 가장 중요하게 생각하는 가치는?",
        "category": "인성",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 4,
        "tip": "KE Way와 연결"
    },
    {
        "id": 42,
        "question": "존경하는 사람이 있다면 누구이고 왜인가요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 2,
        "tip": "승무원 역량과 연결"
    },
    {
        "id": 43,
        "question": "본인의 좌우명이 있다면 무엇인가요?",
        "category": "인성",
        "round": "1차",
        "source": "기출",
        "difficulty": 2,
        "tip": "삶의 태도와 연결"
    },

    # ===== 영어 면접 =====
    {
        "id": 44,
        "question": "Please introduce yourself briefly.",
        "category": "영어",
        "round": "영어",
        "source": "기출",
        "difficulty": 2,
        "tip": "1분 내외, 자연스럽게"
    },
    {
        "id": 45,
        "question": "Why do you want to work for Korean Air?",
        "category": "영어",
        "round": "영어",
        "source": "기출",
        "difficulty": 3,
        "tip": "대한항공 강점 + 본인 적합성"
    },
    {
        "id": 46,
        "question": "What are your strengths and weaknesses?",
        "category": "영어",
        "round": "영어",
        "source": "기출",
        "difficulty": 3,
        "tip": "서비스 관련 강점 강조"
    },
    {
        "id": 47,
        "question": "How would you handle a difficult passenger?",
        "category": "영어",
        "round": "영어",
        "source": "기출",
        "difficulty": 4,
        "tip": "구체적 대응 절차"
    },
    {
        "id": 48,
        "question": "Describe a time when you provided excellent customer service.",
        "category": "영어",
        "round": "영어",
        "source": "기출",
        "difficulty": 4,
        "tip": "STAR 기법 활용"
    },
    {
        "id": 49,
        "question": "What do you know about Korean Air?",
        "category": "영어",
        "round": "영어",
        "source": "기출",
        "difficulty": 3,
        "tip": "기업 정보 영어로 숙지"
    },
    {
        "id": 50,
        "question": "Where do you see yourself in 5 years?",
        "category": "영어",
        "round": "영어",
        "source": "기출",
        "difficulty": 3,
        "tip": "대한항공 내 성장 비전"
    },

    # ===== 심층 면접 =====
    {
        "id": 51,
        "question": "대한항공이 추구하는 '안전'은 단순 규정 준수와 무엇이 다르다고 생각합니까?",
        "category": "심층",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 5,
        "tip": "안전 문화, 예방적 사고"
    },
    {
        "id": 52,
        "question": "메가캐리어 체제에서 승무원에게 가장 중요해질 역량은 무엇이라고 보십니까?",
        "category": "심층",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 5,
        "tip": "통합 후 변화 이해"
    },
    {
        "id": 53,
        "question": "표준화된 서비스 환경에서 개인의 강점을 어떻게 발휘할 수 있습니까?",
        "category": "심층",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 5,
        "tip": "매뉴얼 + 개인 역량"
    },
    {
        "id": 54,
        "question": "글로벌 고객을 상대하며 문화 차이로 어려움을 겪었던 경험이 있습니까?",
        "category": "심층",
        "round": "2차",
        "source": "기출",
        "difficulty": 4,
        "tip": "다문화 이해, 유연한 대응"
    },
    {
        "id": 55,
        "question": "대한항공 승무원이 '대표 항공사'로서 가져야 할 태도는 무엇이라고 생각합니까?",
        "category": "심층",
        "round": "2차",
        "source": "기출패턴",
        "difficulty": 5,
        "tip": "국적기 대표성, 한국 이미지"
    },
]


def get_questions_by_category(category: str) -> list:
    """카테고리별 질문 반환"""
    return [q for q in QUESTIONS if q["category"] == category]


def get_questions_by_round(round_type: str) -> list:
    """면접 차수별 질문 반환"""
    return [q for q in QUESTIONS if q["round"] == round_type]


def get_random_questions(count: int = 5, category: str = None, round_type: str = None) -> list:
    """랜덤 질문 반환"""
    import random
    filtered = QUESTIONS.copy()
    if category:
        filtered = [q for q in filtered if q["category"] == category]
    if round_type:
        filtered = [q for q in filtered if q["round"] == round_type]
    return random.sample(filtered, min(count, len(filtered)))


# 카테고리 목록
CATEGORIES = ["인성", "인재상", "서비스", "영어", "심층"]

# 면접 차수
ROUNDS = ["1차", "2차", "영어"]
