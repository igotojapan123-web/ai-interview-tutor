# english_interview_data.py
# 영어면접 질문 데이터 (확장판)

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
            {
                "question": "How would your friends describe you?",
                "korean_hint": "친구들은 당신을 어떻게 묘사할까요?",
                "key_points": ["성격", "대인관계", "객관성"],
                "sample_answer": "My friends would describe me as reliable and approachable. They often say I'm the person they turn to when they need advice because I listen carefully and offer thoughtful suggestions. I'm also known for being optimistic and bringing positive energy to any group.",
            },
            {
                "question": "What makes you unique compared to other candidates?",
                "korean_hint": "다른 지원자와 비교해 당신만의 특별한 점은?",
                "key_points": ["차별점", "구체적 경험", "자신감"],
                "sample_answer": "What sets me apart is my multicultural background. Having lived in three different countries, I can communicate in multiple languages and understand diverse cultural perspectives. This enables me to connect with passengers from all backgrounds and anticipate their needs effectively.",
            },
            {
                "question": "Describe yourself in three words.",
                "korean_hint": "세 단어로 자신을 표현해주세요.",
                "key_points": ["핵심 특성", "간결함", "직무 연관성"],
                "sample_answer": "I would describe myself as adaptable, empathetic, and proactive. Adaptable because I thrive in changing environments. Empathetic because I genuinely care about others' well-being. Proactive because I believe in anticipating problems before they arise.",
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
            {
                "question": "Where do you see yourself in 5 years?",
                "korean_hint": "5년 후 자신의 모습은?",
                "key_points": ["성장 의지", "현실적 목표", "회사 기여"],
                "sample_answer": "In five years, I see myself as a senior cabin crew member, possibly training new recruits. I want to continuously improve my skills and take on more responsibilities. My goal is to become someone who contributes significantly to the team's success while maintaining excellent service standards.",
            },
            {
                "question": "What motivates you to work hard?",
                "korean_hint": "열심히 일하게 하는 동기는?",
                "key_points": ["내적 동기", "구체적 예시", "열정"],
                "sample_answer": "What motivates me most is seeing the positive impact of my work on others. When I help a passenger feel comfortable or resolve their concern, the gratitude in their eyes is incredibly rewarding. I'm also motivated by personal growth and the opportunity to learn something new every day.",
            },
            {
                "question": "What are your career goals?",
                "korean_hint": "커리어 목표는 무엇인가요?",
                "key_points": ["장기 목표", "단계별 계획", "직무 연관성"],
                "sample_answer": "My short-term goal is to become an excellent cabin crew member who provides exceptional service. In the long term, I aspire to advance to a purser position and eventually contribute to training programs. I want to build a lasting career in aviation while continuously developing my leadership skills.",
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
            {
                "question": "How would you handle a passenger who complains about the food?",
                "korean_hint": "기내식에 불만을 제기하는 승객은 어떻게 응대하시겠습니까?",
                "key_points": ["공감", "대안 제시", "사과"],
                "sample_answer": "I would sincerely apologize for the inconvenience and listen to their specific concerns. Then, I would check what alternative options we have available, such as a different meal or snacks. I would also assure them that their feedback is valuable and will be reported to help us improve our service.",
            },
            {
                "question": "What would you do if you couldn't fulfill a passenger's request?",
                "korean_hint": "승객의 요청을 들어줄 수 없을 때 어떻게 하시겠습니까?",
                "key_points": ["정중한 거절", "대안 제시", "공감"],
                "sample_answer": "I would explain the situation politely and express genuine regret that I cannot fulfill their request. Then, I would offer alternative solutions that might meet their needs. For example, if they wanted an unavailable seat, I could offer extra amenities or check if the seat becomes available later. The key is to show that I truly want to help.",
            },
            {
                "question": "How do you personalize service for different passengers?",
                "korean_hint": "다양한 승객에게 맞춤 서비스를 어떻게 제공하시겠습니까?",
                "key_points": ["관찰력", "문화 이해", "유연성"],
                "sample_answer": "I believe in observing passengers' needs and preferences carefully. For families with children, I might offer games or extra attention. For business travelers, I'd ensure quick, efficient service without unnecessary interruptions. For elderly passengers, I'd be extra patient and offer assistance proactively. Understanding cultural differences is also crucial.",
            },
            {
                "question": "How would you handle a language barrier with a passenger?",
                "korean_hint": "승객과 언어 장벽이 있을 때 어떻게 하시겠습니까?",
                "key_points": ["비언어적 소통", "인내심", "창의적 해결"],
                "sample_answer": "I would use simple words, gestures, and visual aids to communicate. I'd speak slowly and clearly while maintaining a warm smile to help them feel comfortable. If available, I'd use translation apps or seek help from multilingual colleagues. The important thing is to remain patient and show that I genuinely want to help them.",
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
            {
                "question": "How would you support a colleague who is struggling?",
                "korean_hint": "어려움을 겪는 동료를 어떻게 도와주시겠습니까?",
                "key_points": ["공감", "실질적 도움", "배려"],
                "sample_answer": "First, I would approach them privately and ask if they're okay. I'd offer to help with their tasks or share some of my workload. If they're facing personal difficulties, I'd listen without judgment and encourage them to take care of themselves. Supporting each other is essential for maintaining a positive team environment.",
            },
            {
                "question": "Describe a successful team project you were part of.",
                "korean_hint": "성공적인 팀 프로젝트 경험을 말씀해주세요.",
                "key_points": ["역할", "협력", "결과"],
                "sample_answer": "In my previous job, our team organized a charity event in just two weeks. I coordinated the volunteer schedule and communicated with vendors. Despite tight deadlines, we worked together efficiently, supporting each other when needed. The event was a great success, raising more funds than expected. This showed me the power of teamwork.",
            },
            {
                "question": "How do you handle different opinions in a team?",
                "korean_hint": "팀에서 의견 차이를 어떻게 다루시나요?",
                "key_points": ["경청", "존중", "합의 도출"],
                "sample_answer": "I welcome different opinions because they often lead to better solutions. I listen carefully to all perspectives without judgment, then try to find common ground. If we can't agree, I suggest we test both approaches on a small scale or consult a supervisor. The key is respecting everyone's input while working toward our shared goal.",
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
            {
                "question": "How would you handle a passenger who smokes in the lavatory?",
                "korean_hint": "화장실에서 흡연하는 승객은 어떻게 하시겠습니까?",
                "key_points": ["규정 설명", "단호함", "보고"],
                "sample_answer": "I would immediately but calmly approach the passenger and explain that smoking on aircraft is strictly prohibited by law and poses a serious safety risk. I would confiscate any smoking materials and inform the senior crew member. This is a serious violation, and I would document the incident according to company procedures.",
            },
            {
                "question": "What would you do if you noticed something suspicious on board?",
                "korean_hint": "기내에서 수상한 것을 발견하면 어떻게 하시겠습니까?",
                "key_points": ["관찰", "보고", "침착함"],
                "sample_answer": "I would remain calm and not alert others to avoid panic. I would discreetly observe the situation to gather more information and then immediately report to the senior crew member or captain using our established communication protocols. Safety is paramount, and any suspicious activity must be reported immediately.",
            },
            {
                "question": "How do you stay updated on safety procedures?",
                "korean_hint": "안전 절차에 대해 어떻게 최신 정보를 유지하시나요?",
                "key_points": ["학습 의지", "지속적 교육"],
                "sample_answer": "I believe continuous learning is essential for safety. I regularly review safety manuals, attend all mandatory training sessions, and practice emergency procedures. I also stay updated on any industry changes and incidents to learn from them. Safety knowledge should always be fresh in mind because emergencies don't wait.",
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
            {
                "question": "What would you do if two passengers were arguing?",
                "korean_hint": "두 승객이 다투고 있다면 어떻게 하시겠습니까?",
                "key_points": ["중재", "침착함", "해결책"],
                "sample_answer": "I would approach them calmly and politely ask them to lower their voices to avoid disturbing other passengers. I'd listen to both sides briefly and try to understand the issue. If possible, I might offer to relocate one of them to an available seat. If the situation escalates, I would involve the senior crew member for assistance.",
            },
            {
                "question": "How would you handle a medical emergency on board?",
                "korean_hint": "기내에서 의료 응급상황이 발생하면 어떻게 하시겠습니까?",
                "key_points": ["침착함", "절차 준수", "협력"],
                "sample_answer": "I would remain calm and immediately assess the situation. I'd call for medical assistance among passengers while another crew member gets the first aid kit. I would follow our emergency medical protocols and communicate with the captain about the situation. If needed, we would coordinate for a possible diversion. Staying composed helps reassure other passengers.",
            },
            {
                "question": "A passenger's behavior is making others uncomfortable. What do you do?",
                "korean_hint": "한 승객의 행동이 다른 승객들을 불편하게 합니다. 어떻게 하시겠습니까?",
                "key_points": ["관찰", "정중한 접근", "해결책"],
                "sample_answer": "I would approach the passenger politely and address the issue discreetly without embarrassing them. I'd explain how their behavior might be affecting others and ask for their cooperation. If the behavior continues, I would consider relocating affected passengers if possible and inform the senior crew member for further action.",
            },
            {
                "question": "What would you do if you made a mistake during service?",
                "korean_hint": "서비스 중 실수를 했다면 어떻게 하시겠습니까?",
                "key_points": ["책임감", "즉시 대응", "재발 방지"],
                "sample_answer": "I would immediately apologize to the affected passenger and take responsibility for my mistake. I'd do my best to correct the situation, whether it's getting the right item or cleaning up a spill. I would thank them for their understanding and perhaps offer a small gesture of goodwill. After the flight, I'd reflect on how to prevent similar mistakes.",
            },
        ],
    },
    "personality": {
        "category": "인성",
        "category_en": "Personality",
        "questions": [
            {
                "question": "Tell me about a time you faced failure.",
                "korean_hint": "실패를 경험했던 때를 말씀해주세요.",
                "key_points": ["성찰", "교훈", "성장"],
                "sample_answer": "Early in my career, I failed to meet a project deadline because I took on too much work without asking for help. I learned the importance of time management and teamwork. Now, I set realistic goals, prioritize tasks, and communicate openly with my team when I need support. That failure taught me valuable lessons I still apply today.",
            },
            {
                "question": "How do you handle criticism?",
                "korean_hint": "비판을 어떻게 받아들이시나요?",
                "key_points": ["수용성", "개선 의지", "전문성"],
                "sample_answer": "I view criticism as an opportunity to grow. When I receive feedback, I listen carefully without being defensive and try to understand the perspective. I ask clarifying questions if needed and take concrete steps to improve. I believe that constructive criticism helps me become better at what I do.",
            },
            {
                "question": "What do you do when you disagree with a rule or policy?",
                "korean_hint": "규칙이나 정책에 동의하지 않을 때 어떻게 하시나요?",
                "key_points": ["존중", "적절한 채널", "전문성"],
                "sample_answer": "While I always follow company rules and policies, if I disagree with something, I would express my concerns through proper channels. I'd speak with my supervisor respectfully, present my perspective with reasons, and suggest alternatives. Ultimately, I understand that policies exist for good reasons, and I respect the final decision.",
            },
            {
                "question": "What was your biggest achievement?",
                "korean_hint": "가장 큰 성취는 무엇인가요?",
                "key_points": ["구체적 성과", "과정", "자부심"],
                "sample_answer": "My biggest achievement was leading a customer satisfaction improvement project at my previous company. I analyzed feedback, identified key areas for improvement, and implemented new service protocols. Within six months, our satisfaction scores increased by 15%. I'm proud of this because it showed how dedication and teamwork can create real results.",
            },
            {
                "question": "How do you stay motivated when work gets repetitive?",
                "korean_hint": "반복적인 업무에서 어떻게 동기를 유지하시나요?",
                "key_points": ["태도", "창의성", "목표 설정"],
                "sample_answer": "I find ways to make each day unique by setting small personal goals, like learning a passenger's name or trying a new approach to service. I remind myself that every flight is someone's special journey - maybe their first flight or a trip to see family. This perspective keeps me engaged and helps me provide genuine service.",
            },
            {
                "question": "What do you value most in a workplace?",
                "korean_hint": "직장에서 가장 중요하게 생각하는 것은?",
                "key_points": ["가치관", "팀워크", "성장"],
                "sample_answer": "I value a supportive team environment where everyone respects each other and works toward common goals. I appreciate opportunities for growth and feedback that helps me improve. A workplace that values both professionalism and genuine care for employees' well-being is where I thrive and give my best.",
            },
        ],
    },
}

# 난이도별 추가 질문 (고급)
ADVANCED_QUESTIONS = [
    {
        "question": "If a passenger makes an unreasonable demand, how would you respond?",
        "korean_hint": "승객이 무리한 요구를 한다면 어떻게 대응하시겠습니까?",
        "key_points": ["공감", "한계 설명", "대안 제시"],
        "category": "Advanced",
    },
    {
        "question": "How would you handle a medical emergency on board?",
        "korean_hint": "기내에서 의료 응급상황이 발생하면 어떻게 하시겠습니까?",
        "key_points": ["침착함", "절차", "협력"],
        "category": "Advanced",
    },
    {
        "question": "What would you do if you disagreed with your senior crew member?",
        "korean_hint": "선임 승무원과 의견이 다르다면 어떻게 하시겠습니까?",
        "key_points": ["존중", "소통", "협력"],
        "category": "Advanced",
    },
    {
        "question": "How do you prioritize tasks during a busy flight?",
        "korean_hint": "바쁜 비행 중 업무의 우선순위를 어떻게 정하시나요?",
        "key_points": ["안전 우선", "효율성", "팀워크"],
        "category": "Advanced",
    },
    {
        "question": "Describe a time when you had to adapt to a sudden change.",
        "korean_hint": "갑작스러운 변화에 적응해야 했던 경험을 말씀해주세요.",
        "key_points": ["유연성", "문제 해결", "결과"],
        "category": "Advanced",
    },
    {
        "question": "How would you handle a VIP passenger with high expectations?",
        "korean_hint": "높은 기대를 가진 VIP 승객은 어떻게 응대하시겠습니까?",
        "key_points": ["전문성", "세심함", "개인화 서비스"],
        "category": "Advanced",
    },
    {
        "question": "What would you do if you witnessed discrimination among passengers?",
        "korean_hint": "승객 간 차별 행위를 목격하면 어떻게 하시겠습니까?",
        "key_points": ["중재", "존중", "정책 준수"],
        "category": "Advanced",
    },
    {
        "question": "How do you maintain high service standards during delays?",
        "korean_hint": "지연 상황에서 어떻게 높은 서비스 수준을 유지하시겠습니까?",
        "key_points": ["소통", "공감", "프로페셔널"],
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
    "발음이 불확실한 단어는 미리 연습하고, 비슷한 쉬운 단어로 대체하세요.",
    "질문을 못 들었으면 당당하게 'Could you repeat that, please?'라고 요청하세요.",
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


def get_questions_count() -> int:
    """전체 질문 개수 반환"""
    total = 0
    for cat_data in ENGLISH_QUESTIONS.values():
        total += len(cat_data.get("questions", []))
    total += len(ADVANCED_QUESTIONS)
    return total


def get_questions_fresh(category: str = None, count: int = 3) -> list:
    """
    영어면접 질문 선택 (중복 방지 적용)
    - 이전에 나온 질문을 제외하고 새 질문만 선택
    - 모든 질문이 소진되면 자동으로 리셋

    Args:
        category: 카테고리 키 (None이면 전체에서 랜덤)
        count: 선택할 질문 수

    Returns:
        질문 리스트 (이전에 안 나온 것 우선)
    """
    import random
    
    # 카테고리별 또는 전체 질문 가져오기
    if category and category in ENGLISH_QUESTIONS:
        all_questions = ENGLISH_QUESTIONS[category]["questions"]
        sub_key = category
    else:
        all_questions = []
        for cat_data in ENGLISH_QUESTIONS.values():
            for q in cat_data["questions"]:
                all_questions.append({**q, "category": cat_data["category"]})
        sub_key = "all"
    
    if not all_questions:
        return []
    
    try:
        from question_history import get_fresh_english_questions
        return get_fresh_english_questions(all_questions, sub_key, count)
    except ImportError:
        # question_history 모듈 없으면 기존 방식 사용
        return random.sample(all_questions, min(count, len(all_questions)))
