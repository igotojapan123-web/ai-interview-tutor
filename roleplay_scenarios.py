# roleplay_scenarios.py
# 롤플레잉 시뮬레이션 시나리오 데이터

SCENARIO_CATEGORIES = [
    "좌석 관련",
    "기내 서비스",
    "안전/규정",
    "불만/컴플레인",
    "의료/응급",
    "특수 승객",
    "승객 간 갈등",
]

# 시나리오 데이터
# difficulty: 1~4 (별 개수)
# keywords: 평가 시 체크할 핵심 포인트
SCENARIOS = {
    # ========== 좌석 관련 ==========
    "seat_change_full": {
        "category": "좌석 관련",
        "title": "만석인데 좌석 변경 요청",
        "difficulty": 2,
        "situation": "장거리 비행 중, 만석 상황입니다. 중년 여성 승객이 창가 좌석을 원한다며 좌석 변경을 요청합니다.",
        "passenger_mood": "정중하지만 기대감이 큼",
        "passenger_persona": "50대 여성, 해외여행이 처음이라 창가에서 풍경을 보고 싶어함",
        "escalation_triggers": ["계속 거절만 할 경우", "대안 없이 안 된다고만 할 경우"],
        "ideal_response_keywords": ["공감", "대안 제시", "다른 승객 협조 요청 시도"],
        "evaluation_criteria": {
            "empathy": "승객의 기대감에 공감했는가",
            "alternative": "가능한 대안을 제시했는가",
            "manner": "정중하고 친절하게 응대했는가",
        },
    },
    "snoring_complaint": {
        "category": "좌석 관련",
        "title": "옆자리 승객 코골이 불만",
        "difficulty": 2,
        "situation": "야간 비행 중, 한 승객이 옆자리 승객의 심한 코골이로 잠을 못 자겠다며 불만을 제기합니다. 만석입니다.",
        "passenger_mood": "피곤하고 짜증난 상태",
        "passenger_persona": "30대 직장인, 내일 중요한 미팅이 있어서 꼭 자야 함",
        "escalation_triggers": ["아무 조치도 안 할 경우", "참으라고만 할 경우"],
        "ideal_response_keywords": ["양측 배려", "귀마개/안대 제공", "가능한 좌석 확인"],
        "evaluation_criteria": {
            "empathy": "승객의 불편함에 공감했는가",
            "solution": "실질적인 해결책을 제시했는가",
            "balance": "양측 승객 모두 배려했는가",
        },
    },
    "emergency_exit_english": {
        "category": "좌석 관련",
        "title": "비상구 좌석인데 영어 못함",
        "difficulty": 3,
        "situation": "비상구 좌석에 앉은 승객이 영어를 전혀 못합니다. 규정상 비상구 좌석은 영어 의사소통이 가능해야 합니다.",
        "passenger_mood": "왜 문제인지 이해 못함, 좌석 좋아서 기분 좋음",
        "passenger_persona": "60대 남성, 다리 불편해서 넓은 좌석 원함, 영어 전혀 못함",
        "escalation_triggers": ["무조건 이동하라고 할 경우", "이유 설명 없이 강요할 경우"],
        "ideal_response_keywords": ["규정 설명", "안전 이유 설명", "대체 좌석 제안", "정중한 요청"],
        "evaluation_criteria": {
            "regulation": "안전 규정을 명확히 설명했는가",
            "respect": "승객의 자존심을 배려했는가",
            "alternative": "대체 좌석을 제안했는가",
        },
    },
    "family_separated": {
        "category": "좌석 관련",
        "title": "가족인데 좌석이 떨어짐",
        "difficulty": 2,
        "situation": "어린 자녀(7살)와 함께 탑승한 엄마가 좌석이 떨어져 배정되었다며 도움을 요청합니다.",
        "passenger_mood": "걱정되고 불안함",
        "passenger_persona": "30대 엄마, 아이가 처음 비행기 타서 옆에 있어야 함",
        "escalation_triggers": ["방법이 없다고만 할 경우", "본인이 알아서 하라고 할 경우"],
        "ideal_response_keywords": ["다른 승객 협조 요청", "적극적 해결 시도", "안심시키기"],
        "evaluation_criteria": {
            "proactive": "적극적으로 해결하려 했는가",
            "empathy": "엄마의 불안감에 공감했는가",
            "effort": "다른 승객에게 협조를 구했는가",
        },
    },
    "upgrade_demand": {
        "category": "좌석 관련",
        "title": "비즈니스 업그레이드 요구",
        "difficulty": 3,
        "situation": "이코노미 승객이 '자주 이용하는 고객'이라며 비즈니스 클래스로 무료 업그레이드를 강력히 요구합니다.",
        "passenger_mood": "자신감 있고 당당함, 거절 시 불쾌해함",
        "passenger_persona": "40대 사업가, VIP 대우받는 것에 익숙함",
        "escalation_triggers": ["단호하게 거절만 할 경우", "무시하는 듯한 태도"],
        "ideal_response_keywords": ["정중한 거절", "마일리지 안내", "감사 표현", "대안 제시"],
        "evaluation_criteria": {
            "firmness": "원칙을 지키며 거절했는가",
            "politeness": "정중하게 응대했는가",
            "alternative": "가능한 대안을 제시했는가",
        },
    },

    # ========== 기내 서비스 ==========
    "special_meal_missing": {
        "category": "기내 서비스",
        "title": "특별식 예약했는데 없음",
        "difficulty": 3,
        "situation": "채식 특별식을 예약한 승객에게 해당 식사가 누락되었습니다. 승객은 종교적 이유로 일반식을 먹을 수 없습니다.",
        "passenger_mood": "당황하고 화남",
        "passenger_persona": "40대 인도인, 힌두교 신자로 소고기 절대 불가",
        "escalation_triggers": ["일반식이라도 드시라고 할 경우", "사과 없이 변명만 할 경우"],
        "ideal_response_keywords": ["진심 어린 사과", "대안 찾기", "과일/빵 등 제공", "보상 언급"],
        "evaluation_criteria": {
            "apology": "진심으로 사과했는가",
            "solution": "먹을 수 있는 대안을 찾았는가",
            "compensation": "적절한 보상을 언급했는가",
        },
    },
    "foreign_object_food": {
        "category": "기내 서비스",
        "title": "음식에 이물질 발견",
        "difficulty": 4,
        "situation": "승객이 기내식에서 머리카락을 발견했다며 화를 내고 있습니다.",
        "passenger_mood": "매우 화남, 역겨워함",
        "passenger_persona": "30대 여성, 위생에 민감함, SNS 활발히 함",
        "escalation_triggers": ["변명할 경우", "대수롭지 않게 여길 경우"],
        "ideal_response_keywords": ["즉시 사과", "음식 교체", "진정성", "보상 제안"],
        "evaluation_criteria": {
            "immediate_action": "즉시 음식을 치우고 사과했는가",
            "sincerity": "진정성 있는 태도를 보였는가",
            "compensation": "적절한 보상을 제안했는가",
        },
    },
    "drunk_more_alcohol": {
        "category": "기내 서비스",
        "title": "술 더 달라 (이미 취함)",
        "difficulty": 3,
        "situation": "이미 상당히 취한 승객이 술을 더 달라고 요청합니다. 말이 어눌하고 얼굴이 붉습니다.",
        "passenger_mood": "기분 좋게 취함, 거절 시 짜증",
        "passenger_persona": "50대 남성, 휴가 기분으로 기분 좋음",
        "escalation_triggers": ["무조건 안 된다고 할 경우", "취했다고 직접 말할 경우"],
        "ideal_response_keywords": ["안전 이유 설명", "부드러운 거절", "물/음료 대안", "자존심 배려"],
        "evaluation_criteria": {
            "safety": "안전을 이유로 거절했는가",
            "dignity": "승객의 자존심을 배려했는가",
            "alternative": "다른 음료를 권했는가",
        },
    },
    "duty_free_soldout": {
        "category": "기내 서비스",
        "title": "면세품 품절 불만",
        "difficulty": 2,
        "situation": "승객이 원하던 면세품이 품절되어 화를 내고 있습니다. 선물용으로 꼭 필요했다고 합니다.",
        "passenger_mood": "실망하고 짜증남",
        "passenger_persona": "40대 여성, 시어머니 선물로 꼭 필요했음",
        "escalation_triggers": ["품절이니 어쩔 수 없다고만 할 경우"],
        "ideal_response_keywords": ["공감", "대안 상품 추천", "도착지 면세점 안내"],
        "evaluation_criteria": {
            "empathy": "실망감에 공감했는가",
            "alternative": "대안을 제시했는가",
            "helpfulness": "도움이 되려는 태도를 보였는가",
        },
    },
    "blanket_shortage": {
        "category": "기내 서비스",
        "title": "담요/베개 부족",
        "difficulty": 1,
        "situation": "추위를 많이 타는 승객이 담요를 요청했는데 재고가 부족합니다.",
        "passenger_mood": "춥고 불편함",
        "passenger_persona": "60대 여성, 냉방에 약함",
        "escalation_triggers": ["없다고만 할 경우"],
        "ideal_response_keywords": ["대안 찾기", "다른 승객 반납 확인", "에어컨 조절 제안"],
        "evaluation_criteria": {
            "effort": "담요를 찾으려 노력했는가",
            "alternative": "대안을 제시했는가",
            "care": "승객을 배려하는 태도를 보였는가",
        },
    },

    # ========== 안전/규정 ==========
    "takeoff_restroom": {
        "category": "안전/규정",
        "title": "이륙 중 화장실 가겠다",
        "difficulty": 3,
        "situation": "이륙을 위해 활주로에 진입했는데 승객이 급하게 화장실을 가야 한다며 일어나려 합니다.",
        "passenger_mood": "급박함, 참기 힘들어함",
        "passenger_persona": "20대 남성, 배탈이 났는지 얼굴이 창백함",
        "escalation_triggers": ["무조건 안 된다고만 할 경우", "공감 없이 규정만 말할 경우"],
        "ideal_response_keywords": ["안전 규정 설명", "공감 표현", "이륙 후 바로 안내 약속", "최대한 빨리"],
        "evaluation_criteria": {
            "safety": "안전 규정을 명확히 설명했는가",
            "empathy": "승객의 급박함에 공감했는가",
            "promise": "이륙 후 즉시 안내를 약속했는가",
        },
    },
    "electronics_refuse": {
        "category": "안전/규정",
        "title": "전자기기 끄기 거부",
        "difficulty": 3,
        "situation": "이륙 준비 중 한 승객이 노트북을 끄지 않고 계속 업무를 보고 있습니다. 두 번 요청했지만 '중요한 일'이라며 거부합니다.",
        "passenger_mood": "바쁘고 짜증남",
        "passenger_persona": "30대 직장인, 급한 업무 마감 중",
        "escalation_triggers": ["계속 부드럽게만 요청할 경우", "포기하고 넘어갈 경우"],
        "ideal_response_keywords": ["단호한 태도", "법적 규정 언급", "착륙 후 시간 약속", "안전 강조"],
        "evaluation_criteria": {
            "firmness": "단호하게 요청했는가",
            "regulation": "규정/법적 근거를 설명했는가",
            "professionalism": "감정적이지 않고 전문적이었는가",
        },
    },
    "oversized_luggage": {
        "category": "안전/규정",
        "title": "큰 수하물 선반에 안 들어감",
        "difficulty": 2,
        "situation": "승객의 기내 수하물이 너무 커서 선반에 들어가지 않습니다. 승객은 위탁하기 싫어합니다.",
        "passenger_mood": "귀찮아함, 비용 걱정",
        "passenger_persona": "20대 여성, 소중한 물건이 들어있어서 위탁 꺼림",
        "escalation_triggers": ["무조건 위탁하라고 할 경우", "본인이 알아서 하라고 할 경우"],
        "ideal_response_keywords": ["다른 공간 확인", "소중품 분리 제안", "안전하게 위탁 보장"],
        "evaluation_criteria": {
            "solution": "대안을 찾으려 했는가",
            "understanding": "승객의 우려를 이해했는가",
            "reassurance": "위탁 시 안전을 보장했는가",
        },
    },
    "seatbelt_refuse": {
        "category": "안전/규정",
        "title": "안전벨트 착용 거부",
        "difficulty": 4,
        "situation": "난기류 예보로 안전벨트 착용 사인이 켜졌는데, 한 승객이 '불편하다'며 벨트 착용을 거부합니다.",
        "passenger_mood": "귀찮아함, 반항적",
        "passenger_persona": "40대 남성, 권위에 반항적 성향",
        "escalation_triggers": ["계속 부드럽게만 요청할 경우", "포기할 경우"],
        "ideal_response_keywords": ["안전 강조", "단호한 태도", "법적 결과 언급", "기장 보고"],
        "evaluation_criteria": {
            "firmness": "단호하게 요청했는가",
            "safety": "안전의 중요성을 강조했는가",
            "escalation": "필요시 상급자에게 보고 언급했는가",
        },
    },
    "mask_refuse": {
        "category": "안전/규정",
        "title": "마스크 착용 거부 (감염병 시)",
        "difficulty": 4,
        "situation": "감염병 유행 시기, 한 승객이 마스크 착용을 거부하며 '개인의 자유'라고 주장합니다.",
        "passenger_mood": "확신에 차 있음, 논쟁적",
        "passenger_persona": "50대 남성, 자신의 권리를 강하게 주장",
        "escalation_triggers": ["논쟁에 말려들 경우", "포기할 경우"],
        "ideal_response_keywords": ["다른 승객 안전", "항공사 규정", "단호하지만 정중함", "하기 불가 경고"],
        "evaluation_criteria": {
            "firmness": "원칙을 지켰는가",
            "calm": "침착하게 대응했는가",
            "other_passengers": "다른 승객의 안전을 언급했는가",
        },
    },

    # ========== 불만/컴플레인 ==========
    "delay_angry": {
        "category": "불만/컴플레인",
        "title": "3시간 지연에 화난 승객",
        "difficulty": 3,
        "situation": "항공기 정비로 3시간 지연되었습니다. 중요한 미팅에 늦게 된 승객이 화를 내며 보상을 요구합니다.",
        "passenger_mood": "매우 화남, 좌절감",
        "passenger_persona": "40대 사업가, 계약 미팅에 늦게 됨",
        "escalation_triggers": ["항공사 잘못이 아니라고 할 경우", "공감 없이 규정만 말할 경우"],
        "ideal_response_keywords": ["진심 어린 사과", "공감 표현", "정보 제공", "가능한 지원 안내"],
        "evaluation_criteria": {
            "empathy": "승객의 상황에 공감했는가",
            "apology": "진심으로 사과했는가",
            "information": "정확한 정보를 제공했는가",
        },
    },
    "luggage_damage": {
        "category": "불만/컴플레인",
        "title": "수하물 파손",
        "difficulty": 3,
        "situation": "수하물 수취대에서 가방이 파손된 것을 발견한 승객이 화를 내며 항의합니다.",
        "passenger_mood": "화남, 당황함",
        "passenger_persona": "30대 여성, 새로 산 고가 캐리어가 파손됨",
        "escalation_triggers": ["책임 회피할 경우", "절차만 안내하고 공감 없을 경우"],
        "ideal_response_keywords": ["사과", "공감", "신고 절차 안내", "신속한 처리 약속"],
        "evaluation_criteria": {
            "empathy": "승객의 속상함에 공감했는가",
            "procedure": "명확한 절차를 안내했는가",
            "support": "적극적으로 도우려 했는가",
        },
    },
    "slow_service": {
        "category": "불만/컴플레인",
        "title": "서비스가 너무 느리다",
        "difficulty": 2,
        "situation": "식사 서비스가 늦어져 한 승객이 '왜 이렇게 느리냐'며 짜증을 냅니다.",
        "passenger_mood": "배고프고 짜증남",
        "passenger_persona": "30대 직장인, 아침을 못 먹어서 매우 배고픔",
        "escalation_triggers": ["변명할 경우", "무시하는 태도"],
        "ideal_response_keywords": ["사과", "빠른 서비스 약속", "간식 제공 제안"],
        "evaluation_criteria": {
            "apology": "서비스 지연에 사과했는가",
            "quick_action": "빠른 조치를 취했는가",
            "care": "승객을 배려하는 태도를 보였는가",
        },
    },
    "vip_treatment": {
        "category": "불만/컴플레인",
        "title": "VIP인데 대우가 별로다",
        "difficulty": 3,
        "situation": "항공사 최상위 등급 회원이 '예전보다 서비스가 나빠졌다'며 불만을 표시합니다.",
        "passenger_mood": "실망함, 서운함",
        "passenger_persona": "50대 사업가, 연간 100회 이상 탑승하는 VIP",
        "escalation_triggers": ["가볍게 넘길 경우", "변명할 경우"],
        "ideal_response_keywords": ["감사 표현", "경청", "피드백 수용", "개선 약속", "특별 서비스 제공"],
        "evaluation_criteria": {
            "gratitude": "충성 고객에게 감사를 표했는가",
            "listening": "불만을 경청했는가",
            "action": "개선 또는 추가 서비스를 제안했는가",
        },
    },
    "sns_threat": {
        "category": "불만/컴플레인",
        "title": "SNS에 올리겠다 협박",
        "difficulty": 4,
        "situation": "사소한 서비스 불만으로 승객이 '이거 다 SNS에 올릴 거야'라며 협박조로 말합니다.",
        "passenger_mood": "화남, 과시적",
        "passenger_persona": "20대, 인플루언서라고 주장, 팔로워 많다고 함",
        "escalation_triggers": ["위협에 굴복할 경우", "맞서 싸울 경우"],
        "ideal_response_keywords": ["침착함 유지", "진심 어린 사과", "문제 해결 집중", "협박에 휘둘리지 않음"],
        "evaluation_criteria": {
            "calm": "침착하게 대응했는가",
            "focus": "문제 해결에 집중했는가",
            "professionalism": "협박에 휘둘리지 않았는가",
        },
    },

    # ========== 의료/응급 ==========
    "passenger_collapse": {
        "category": "의료/응급",
        "title": "승객이 갑자기 쓰러짐",
        "difficulty": 4,
        "situation": "비행 중 한 승객이 갑자기 의식을 잃고 쓰러졌습니다. 주변 승객들이 놀라고 있습니다.",
        "passenger_mood": "의식 없음 (주변 승객들 공포)",
        "passenger_persona": "70대 남성, 심장병 병력 있음 (동행인 정보)",
        "escalation_triggers": ["당황해서 우왕좌왕할 경우"],
        "ideal_response_keywords": ["침착한 대응", "의료진 호출", "AED 준비", "기장 보고", "주변 승객 안정"],
        "evaluation_criteria": {
            "calm": "침착하게 대응했는가",
            "procedure": "응급 절차를 따랐는가",
            "coordination": "팀과 협력했는가",
        },
    },
    "child_fever": {
        "category": "의료/응급",
        "title": "아이가 고열",
        "difficulty": 3,
        "situation": "3살 아이의 엄마가 아이가 갑자기 열이 많이 난다며 도움을 요청합니다.",
        "passenger_mood": "불안하고 걱정됨",
        "passenger_persona": "30대 엄마, 아이 첫 해외여행 중",
        "escalation_triggers": ["가볍게 여길 경우", "아무 조치도 안 할 경우"],
        "ideal_response_keywords": ["안심시키기", "해열제 제공", "의료진 확인", "체온 체크", "물 제공"],
        "evaluation_criteria": {
            "care": "아이와 엄마를 배려했는가",
            "action": "적절한 조치를 취했는가",
            "reassurance": "엄마를 안심시켰는가",
        },
    },
    "panic_attack": {
        "category": "의료/응급",
        "title": "공황장애 승객",
        "difficulty": 3,
        "situation": "한 승객이 갑자기 숨을 가쁘게 쉬며 '죽을 것 같다'고 호소합니다. 공황발작으로 보입니다.",
        "passenger_mood": "극도의 공포, 호흡 곤란",
        "passenger_persona": "20대 여성, 비행 공포증 있음",
        "escalation_triggers": ["무시하거나 가볍게 여길 경우"],
        "ideal_response_keywords": ["차분한 목소리", "함께 호흡", "안심시키기", "조용한 공간", "물 제공"],
        "evaluation_criteria": {
            "calm": "차분하게 대응했는가",
            "empathy": "승객의 공포에 공감했는가",
            "technique": "적절한 진정 기법을 사용했는가",
        },
    },
    "pregnant_pain": {
        "category": "의료/응급",
        "title": "임산부 복통 호소",
        "difficulty": 4,
        "situation": "임신 7개월 승객이 갑자기 복통을 호소하며 고통스러워합니다.",
        "passenger_mood": "공포, 고통",
        "passenger_persona": "30대 임산부, 남편과 함께 탑승",
        "escalation_triggers": ["당황해서 아무것도 못 할 경우"],
        "ideal_response_keywords": ["침착", "눕히기", "의료진 호출", "기장 보고", "비상착륙 고려", "남편 안심"],
        "evaluation_criteria": {
            "urgency": "상황의 긴급성을 인지했는가",
            "procedure": "적절한 응급 절차를 따랐는가",
            "communication": "기장에게 보고했는가",
        },
    },
    "elderly_breathing": {
        "category": "의료/응급",
        "title": "노인 승객 호흡 곤란",
        "difficulty": 4,
        "situation": "80대 노인 승객이 호흡이 힘들다며 가슴을 움켜쥐고 있습니다.",
        "passenger_mood": "고통스러움",
        "passenger_persona": "80대 남성, 혼자 탑승, 천식 병력",
        "escalation_triggers": ["늦게 대응할 경우"],
        "ideal_response_keywords": ["산소 공급", "의료진 호출", "침착", "기장 보고", "약 소지 확인"],
        "evaluation_criteria": {
            "speed": "신속하게 대응했는가",
            "procedure": "응급 절차를 따랐는가",
            "equipment": "필요한 장비를 준비했는가",
        },
    },

    # ========== 특수 승객 ==========
    "unaccompanied_minor_crying": {
        "category": "특수 승객",
        "title": "혼자 탄 어린이 울음",
        "difficulty": 2,
        "situation": "비동반 소아(10살)가 엄마가 보고 싶다며 울고 있습니다.",
        "passenger_mood": "외롭고 무서움",
        "passenger_persona": "10살 남자아이, 처음으로 혼자 비행",
        "escalation_triggers": ["무시할 경우", "어른처럼 대할 경우"],
        "ideal_response_keywords": ["눈높이 대화", "안심시키기", "간식/음료 제공", "관심 보여주기"],
        "evaluation_criteria": {
            "empathy": "아이의 감정에 공감했는가",
            "approach": "아이 눈높이에서 대화했는가",
            "care": "지속적으로 관심을 보였는가",
        },
    },
    "wheelchair_restroom": {
        "category": "특수 승객",
        "title": "휠체어 승객 화장실",
        "difficulty": 2,
        "situation": "휠체어 승객이 화장실을 이용하고 싶다며 도움을 요청합니다.",
        "passenger_mood": "불편하지만 참고 있음",
        "passenger_persona": "50대 남성, 하반신 마비",
        "escalation_triggers": ["민망하게 만들 경우", "도움 없이 혼자 하라고 할 경우"],
        "ideal_response_keywords": ["존중", "프라이버시 배려", "적극적 도움", "자연스럽게"],
        "evaluation_criteria": {
            "respect": "승객의 존엄성을 지켰는가",
            "help": "적극적으로 도왔는가",
            "privacy": "프라이버시를 배려했는가",
        },
    },
    "blind_passenger": {
        "category": "특수 승객",
        "title": "시각장애인 안내",
        "difficulty": 2,
        "situation": "시각장애인 승객이 좌석과 주변 환경에 대한 설명을 요청합니다.",
        "passenger_mood": "도움이 필요함",
        "passenger_persona": "40대 여성, 선천적 시각장애, 자주 혼자 여행",
        "escalation_triggers": ["대충 설명할 경우", "불편해할 경우"],
        "ideal_response_keywords": ["상세한 설명", "손 위치 안내", "서비스 타이밍 알림", "존중하는 태도"],
        "evaluation_criteria": {
            "detail": "충분히 상세하게 설명했는가",
            "respect": "존중하는 태도를 보였는가",
            "proactive": "필요한 것을 먼저 제안했는가",
        },
    },
    "first_flight_elderly": {
        "category": "특수 승객",
        "title": "처음 비행기 타는 노인",
        "difficulty": 1,
        "situation": "70대 노인 승객이 처음 비행기를 타서 모든 것이 낯설고 불안해합니다.",
        "passenger_mood": "불안하고 긴장됨",
        "passenger_persona": "70대 할머니, 손주 보러 혼자 여행",
        "escalation_triggers": ["귀찮아할 경우"],
        "ideal_response_keywords": ["친절한 안내", "안전벨트 도움", "안심시키기", "지속적 관심"],
        "evaluation_criteria": {
            "patience": "인내심을 보였는가",
            "kindness": "친절하게 안내했는가",
            "care": "지속적으로 신경 썼는가",
        },
    },
    "language_barrier": {
        "category": "특수 승객",
        "title": "외국인 언어 소통 불가",
        "difficulty": 3,
        "situation": "영어도 한국어도 못하는 외국인 승객이 무언가를 급하게 요청하지만 소통이 안 됩니다.",
        "passenger_mood": "답답함, 급함",
        "passenger_persona": "중년 아랍 여성, 아랍어만 가능",
        "escalation_triggers": ["포기할 경우", "짜증낼 경우"],
        "ideal_response_keywords": ["번역 앱 활용", "그림/제스처", "인내심", "다른 승객 도움 요청"],
        "evaluation_criteria": {
            "creativity": "창의적 소통 방법을 시도했는가",
            "patience": "인내심을 보였는가",
            "effort": "해결하려 노력했는가",
        },
    },

    # ========== 승객 간 갈등 ==========
    "reclining_conflict": {
        "category": "승객 간 갈등",
        "title": "리클라이닝 갈등",
        "difficulty": 3,
        "situation": "앞좌석 승객이 좌석을 젖혔는데 뒷좌석 승객이 공간이 없다며 항의합니다. 둘 다 화가 나 있습니다.",
        "passenger_mood": "양측 모두 화남",
        "passenger_persona": "앞: 장거리 피곤한 승객 / 뒤: 키 큰 남성",
        "escalation_triggers": ["한쪽 편만 들 경우"],
        "ideal_response_keywords": ["양측 공감", "중재", "절충안 제시", "식사시간 리클라이닝 규칙"],
        "evaluation_criteria": {
            "neutrality": "중립을 유지했는가",
            "mediation": "효과적으로 중재했는가",
            "solution": "양측이 수용할 수 있는 해결책을 제시했는가",
        },
    },
    "child_noise_complaint": {
        "category": "승객 간 갈등",
        "title": "아이 소음에 옆 승객 항의",
        "difficulty": 3,
        "situation": "3살 아이가 계속 울고 떼를 쓰자 옆 좌석 승객이 '통제 좀 하라'며 부모에게 화를 냅니다.",
        "passenger_mood": "양측 모두 스트레스",
        "passenger_persona": "부모: 지친 30대 부부 / 옆 승객: 피곤한 비즈니스맨",
        "escalation_triggers": ["한쪽 편만 들 경우", "무시할 경우"],
        "ideal_response_keywords": ["양측 공감", "부모 도움 제안", "좌석 이동 제안", "아이 달래기 도움"],
        "evaluation_criteria": {
            "empathy_both": "양측 모두에게 공감했는가",
            "help": "실질적 도움을 제안했는가",
            "calm": "상황을 진정시켰는가",
        },
    },
    "armrest_fight": {
        "category": "승객 간 갈등",
        "title": "팔걸이 싸움",
        "difficulty": 2,
        "situation": "가운데 좌석 승객과 창가 좌석 승객이 팔걸이 사용을 두고 신경전을 벌이고 있습니다.",
        "passenger_mood": "서로 짜증남",
        "passenger_persona": "양측 모두 중년 남성",
        "escalation_triggers": ["무시할 경우"],
        "ideal_response_keywords": ["유머 활용", "가운데 좌석 우선 관례 설명", "부드러운 중재"],
        "evaluation_criteria": {
            "diplomacy": "외교적으로 해결했는가",
            "humor": "분위기를 부드럽게 만들었는가",
            "resolution": "문제를 해결했는가",
        },
    },
    "drunk_harassment": {
        "category": "승객 간 갈등",
        "title": "음주 승객이 옆자리 괴롭힘",
        "difficulty": 4,
        "situation": "술에 취한 남성 승객이 옆자리 여성 승객에게 계속 말을 걸며 불편하게 합니다. 여성 승객이 도움을 요청합니다.",
        "passenger_mood": "남성: 취해서 기분 좋음 / 여성: 불안하고 불쾌함",
        "passenger_persona": "남성: 40대 취객 / 여성: 20대 혼자 여행",
        "escalation_triggers": ["가볍게 여길 경우", "조치를 안 할 경우"],
        "ideal_response_keywords": ["여성 승객 보호", "좌석 이동", "남성에게 단호한 경고", "기장 보고"],
        "evaluation_criteria": {
            "protection": "피해 승객을 보호했는가",
            "firmness": "가해자에게 단호했는가",
            "action": "실질적 조치를 취했는가",
        },
    },
    "couple_fight": {
        "category": "승객 간 갈등",
        "title": "커플 싸움",
        "difficulty": 3,
        "situation": "커플로 보이는 두 승객이 작은 목소리로 다투다가 점점 목소리가 커지고 있습니다. 주변 승객들이 불편해합니다.",
        "passenger_mood": "서로 화남, 감정적",
        "passenger_persona": "20대 커플",
        "escalation_triggers": ["공개적으로 개입할 경우", "무시할 경우"],
        "ideal_response_keywords": ["조용히 접근", "음료 제공 핑계", "분리 제안", "프라이버시 배려"],
        "evaluation_criteria": {
            "discretion": "조심스럽게 접근했는가",
            "tact": "상황을 악화시키지 않았는가",
            "resolution": "상황을 진정시켰는가",
        },
    },
}


def get_scenarios_by_category(category: str) -> list:
    """카테고리별 시나리오 리스트 반환"""
    return [
        {"id": k, **v}
        for k, v in SCENARIOS.items()
        if v["category"] == category
    ]


def get_all_scenarios() -> list:
    """전체 시나리오 리스트 반환"""
    return [{"id": k, **v} for k, v in SCENARIOS.items()]


def get_scenario_by_id(scenario_id: str) -> dict:
    """ID로 시나리오 조회"""
    if scenario_id in SCENARIOS:
        return {"id": scenario_id, **SCENARIOS[scenario_id]}
    return None
