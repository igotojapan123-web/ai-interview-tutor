# english_interview_data.py
# 영어면접 질문 데이터

# 카테고리별 영어 면접 질문
ENGLISH_QUESTIONS = {
    "self_introduction": {
        "category": "자기소개",
        "category_en": "Self Introduction",
        "questions": [
            {
                "question": "Please introduce yourself briefly.",
                "korean_hint": "간단히 자기소개 해주세요.",
                "key_points": ["이름", "학력/경력", "지원동기", "강점"],
                "sample_answer": "Hello, my name is [Name]. I graduated from [University] with a degree in [Major]. I have [X] years of experience in customer service at [Company]. I am passionate about providing excellent service and I believe my communication skills and positive attitude make me a great fit for this cabin crew position.",
            },
            {
                "question": "Tell me about yourself in one minute.",
                "korean_hint": "1분 안에 자신에 대해 말씀해주세요.",
                "key_points": ["간결함", "핵심 강점", "지원동기"],
                "sample_answer": "I'm a dedicated service professional with a passion for helping others. I've worked in hospitality for three years, where I learned to handle diverse situations with patience and positivity. I'm excited about becoming a flight attendant because I love meeting people from different cultures and ensuring they have a comfortable journey.",
            },
            {
                "question": "What are your strengths and weaknesses?",
                "korean_hint": "당신의 강점과 약점은 무엇인가요?",
                "key_points": ["구체적 예시", "약점 극복 노력"],
                "sample_answer": "My greatest strength is my ability to stay calm under pressure. In my previous job, I often handled difficult customers while maintaining a positive attitude. As for weaknesses, I sometimes focus too much on details, but I've learned to balance perfectionism with efficiency by setting priorities.",
            },
        ],
    },
    "motivation": {
        "category": "지원동기",
        "category_en": "Motivation",
        "questions": [
            {
                "question": "Why do you want to be a flight attendant?",
                "korean_hint": "왜 승무원이 되고 싶나요?",
                "key_points": ["진정성", "직무 이해", "열정"],
                "sample_answer": "I want to be a flight attendant because I'm passionate about travel and customer service. I love the idea of ensuring passengers have a safe and comfortable journey while experiencing different cultures. The dynamic nature of this job and the opportunity to meet people from all over the world truly excites me.",
            },
            {
                "question": "Why did you choose our airline?",
                "korean_hint": "왜 저희 항공사를 선택했나요?",
                "key_points": ["항공사 연구", "가치 일치", "구체성"],
                "sample_answer": "I chose your airline because of your outstanding reputation for customer service and safety. I've researched your company values, and I truly resonate with your commitment to excellence. I've also heard wonderful things from passengers about their experiences, and I want to be part of a team that consistently delivers such high-quality service.",
            },
            {
                "question": "What do you know about our company?",
                "korean_hint": "저희 회사에 대해 무엇을 알고 계시나요?",
                "key_points": ["사전 조사", "구체적 정보", "관심 표현"],
                "sample_answer": "I know that your airline was established in [year] and has grown to become one of the leading carriers in Asia. You operate flights to over [X] destinations worldwide and are known for your award-winning service. I'm particularly impressed by your recent sustainability initiatives and your focus on passenger comfort.",
            },
        ],
    },
    "service": {
        "category": "서비스",
        "category_en": "Service",
        "questions": [
            {
                "question": "How would you handle an angry passenger?",
                "korean_hint": "화난 승객을 어떻게 응대하시겠습니까?",
                "key_points": ["공감", "경청", "해결책", "침착함"],
                "sample_answer": "First, I would listen carefully to understand their concerns and show empathy. I would apologize for any inconvenience and remain calm throughout. Then, I would try to find a solution within my authority or escalate to a senior crew member if needed. The key is to make the passenger feel heard and valued.",
            },
            {
                "question": "What does excellent customer service mean to you?",
                "korean_hint": "훌륭한 고객 서비스란 무엇이라고 생각하시나요?",
                "key_points": ["정의", "예시", "고객 중심"],
                "sample_answer": "Excellent customer service means anticipating passengers' needs before they ask and going above and beyond to ensure their comfort. It's about creating a positive experience through genuine care, attention to detail, and a warm, professional attitude. It also means handling problems efficiently while making passengers feel valued.",
            },
            {
                "question": "Describe a time when you provided excellent service.",
                "korean_hint": "훌륭한 서비스를 제공했던 경험을 말씀해주세요.",
                "key_points": ["STAR 기법", "구체적 상황", "결과"],
                "sample_answer": "At my previous job in a hotel, a guest's luggage was delayed. I noticed their frustration and immediately offered toiletries and arranged laundry service for their clothes. I also kept them updated on the luggage status and personally delivered it to their room when it arrived. The guest was so grateful that they wrote a complimentary letter to management.",
            },
        ],
    },
    "teamwork": {
        "category": "팀워크",
        "category_en": "Teamwork",
        "questions": [
            {
                "question": "How do you work in a team?",
                "korean_hint": "팀에서 어떻게 일하시나요?",
                "key_points": ["협력", "의사소통", "역할 인식"],
                "sample_answer": "I believe in open communication and mutual respect when working in a team. I always try to support my colleagues and share responsibilities fairly. I'm flexible and can adapt to different roles depending on what the team needs. I also believe in celebrating team successes and learning from challenges together.",
            },
            {
                "question": "Tell me about a conflict you had with a coworker.",
                "korean_hint": "동료와의 갈등 경험을 말씀해주세요.",
                "key_points": ["문제 해결", "소통", "결과"],
                "sample_answer": "Once, a colleague and I disagreed on how to handle a busy shift. Instead of arguing, I suggested we discuss it calmly after work. We listened to each other's perspectives and found a compromise that improved our workflow. This experience taught me the importance of open communication and staying professional even during disagreements.",
            },
            {
                "question": "What role do you usually take in a team?",
                "korean_hint": "팀에서 보통 어떤 역할을 맡으시나요?",
                "key_points": ["자기 인식", "유연성", "기여"],
                "sample_answer": "I'm naturally a supportive team member who ensures everyone is on the same page. However, I can also take the lead when necessary. I believe in adapting to what the team needs at any given moment. Whether it's coordinating tasks, motivating teammates, or simply helping out, I'm always ready to contribute.",
            },
        ],
    },
    "safety": {
        "category": "안전",
        "category_en": "Safety",
        "questions": [
            {
                "question": "What would you do in an emergency situation?",
                "korean_hint": "비상 상황에서 어떻게 하시겠습니까?",
                "key_points": ["침착함", "절차 준수", "승객 안전"],
                "sample_answer": "In an emergency, I would remain calm and follow the established safety procedures. My priority would be ensuring passenger safety by giving clear instructions and assisting those who need help. I would coordinate with other crew members and follow the captain's commands. Staying composed is essential to help passengers feel safe.",
            },
            {
                "question": "How important is safety to you?",
                "korean_hint": "안전이 당신에게 얼마나 중요한가요?",
                "key_points": ["최우선 순위", "구체적 행동"],
                "sample_answer": "Safety is my absolute top priority. As a flight attendant, I understand that passengers' lives depend on our vigilance and training. I would never compromise on safety procedures, even under pressure. I believe that maintaining high safety standards is not just a duty but a fundamental responsibility to everyone on board.",
            },
            {
                "question": "A passenger refuses to fasten their seatbelt. What do you do?",
                "korean_hint": "승객이 안전벨트 착용을 거부합니다. 어떻게 하시겠습니까?",
                "key_points": ["설득", "규정 설명", "단호함"],
                "sample_answer": "I would politely explain the safety regulations and why wearing a seatbelt is crucial for their protection. If they still refuse, I would calmly but firmly emphasize that it's a legal requirement and for their own safety. If necessary, I would involve a senior crew member or inform the captain, as safety rules cannot be compromised.",
            },
        ],
    },
    "situational": {
        "category": "상황질문",
        "category_en": "Situational",
        "questions": [
            {
                "question": "A passenger is afraid of flying. How would you help them?",
                "korean_hint": "비행을 무서워하는 승객을 어떻게 도와주시겠습니까?",
                "key_points": ["공감", "안심", "실질적 도움"],
                "sample_answer": "I would approach them with a warm smile and speak in a calm, reassuring voice. I'd let them know that feeling nervous is completely normal and that our crew is trained to ensure their safety. I might offer them a glass of water, suggest breathing exercises, and check on them regularly throughout the flight to make sure they're comfortable.",
            },
            {
                "question": "What would you do if you saw a colleague making a mistake?",
                "korean_hint": "동료가 실수하는 것을 본다면 어떻게 하시겠습니까?",
                "key_points": ["팀워크", "건설적 피드백", "안전"],
                "sample_answer": "If it's a safety-related issue, I would address it immediately but discreetly to avoid embarrassing them. For minor issues, I would wait for an appropriate moment and mention it privately in a supportive way. The goal is to help my colleague improve while maintaining a positive working relationship and ensuring passenger safety.",
            },
            {
                "question": "How do you handle stress and long working hours?",
                "korean_hint": "스트레스와 긴 근무 시간을 어떻게 관리하시나요?",
                "key_points": ["자기 관리", "긍정적 태도", "구체적 방법"],
                "sample_answer": "I manage stress by maintaining a healthy work-life balance. I exercise regularly, get enough sleep, and practice mindfulness. During long flights, I stay positive by focusing on the rewarding aspects of the job, like meeting interesting people. I also support my colleagues because teamwork makes challenging situations easier to handle.",
            },
            {
                "question": "Describe a difficult decision you had to make.",
                "korean_hint": "어려운 결정을 내려야 했던 경험을 말씀해주세요.",
                "key_points": ["상황 설명", "결정 과정", "결과"],
                "sample_answer": "In my previous job, I had to decide whether to report a colleague who was consistently late. It was difficult because we were friends. I chose to speak with them first privately. When the behavior continued, I reported it to our supervisor, prioritizing our team's performance. They understood, and our friendship remained intact after they improved.",
            },
        ],
    },
}

# 난이도별 추가 질문
ADVANCED_QUESTIONS = [
    {
        "question": "If a passenger makes an unreasonable demand, how would you respond?",
        "korean_hint": "승객이 무리한 요구를 한다면 어떻게 대응하시겠습니까?",
        "category": "Advanced",
    },
    {
        "question": "How would you handle a medical emergency on board?",
        "korean_hint": "기내에서 의료 응급상황이 발생하면 어떻게 하시겠습니까?",
        "category": "Advanced",
    },
    {
        "question": "What would you do if you disagreed with your senior crew member?",
        "korean_hint": "선임 승무원과 의견이 다르다면 어떻게 하시겠습니까?",
        "category": "Advanced",
    },
    {
        "question": "How do you stay updated with safety procedures?",
        "korean_hint": "안전 절차에 대해 어떻게 최신 정보를 유지하시나요?",
        "category": "Advanced",
    },
    {
        "question": "Describe a time when you had to adapt to a sudden change.",
        "korean_hint": "갑작스러운 변화에 적응해야 했던 경험을 말씀해주세요.",
        "category": "Advanced",
    },
]

# 면접 팁 (한국어)
ENGLISH_INTERVIEW_TIPS = [
    "또박또박 적당한 속도로 말하세요 - 너무 빨리 말하지 마세요.",
    "STAR 기법을 활용하세요: 상황(Situation), 과제(Task), 행동(Action), 결과(Result)",
    "미소를 짓고 아이컨택을 유지하세요 (화상 면접에서도 카메라를 보세요).",
    "자주 나오는 질문을 연습하되, 대본을 통째로 외우지는 마세요.",
    "해당 항공사에 대한 열정과 진심어린 관심을 보여주세요.",
    "답변은 간결하게 - 질문당 1~2분을 목표로 하세요.",
    "답변 전 잠깐 생각을 정리하는 시간을 가져도 괜찮습니다.",
    "긍정적인 표현을 사용하고, 문제보다는 해결책에 초점을 맞추세요.",
    "문법 실수를 두려워하지 마세요 - 자신감 있게 말하는 것이 더 중요합니다.",
    "I think, I believe, In my opinion 같은 표현으로 문장을 시작하면 자연스럽습니다.",
]


def get_questions_by_category(category_key: str) -> list:
    """카테고리별 질문 반환"""
    if category_key in ENGLISH_QUESTIONS:
        return ENGLISH_QUESTIONS[category_key]["questions"]
    return []


def get_all_categories() -> list:
    """전체 카테고리 리스트 반환"""
    return [
        {"key": k, "name": v["category"], "name_en": v["category_en"]}
        for k, v in ENGLISH_QUESTIONS.items()
    ]


def get_random_questions(count: int = 5) -> list:
    """랜덤 질문 선택"""
    import random
    all_questions = []
    for cat_data in ENGLISH_QUESTIONS.values():
        for q in cat_data["questions"]:
            all_questions.append({**q, "category": cat_data["category"]})
    return random.sample(all_questions, min(count, len(all_questions)))
