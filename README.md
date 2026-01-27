# FlyReady Lab - AI 승무원 면접 코칭 플랫폼

AI 기반 항공사 승무원 면접 준비 통합 솔루션

## 주요 기능

### 면접 연습
- **모의면접** - AI 면접관과 실전 모의면접
- **롤플레잉** - 기내 상황별 시뮬레이션
- **토론면접** - 그룹 토론 연습
- **영어면접** - 영어 질문 및 피드백

### 자소서 분석
- **자소서첨삭** - AI 기반 자소서 첨삭
- **자소서기반질문** - 자소서 내용 기반 예상 질문 생성
- **기업분석** - 항공사별 맞춤 분석

### 스킬 향상
- **표정연습** - 카메라 기반 표정 분석
- **기내방송연습** - 기내 안내방송 연습
- **면접꿀팁** - 합격자 노하우

### 학습 관리
- **진도관리** - 학습 진행 현황
- **성장그래프** - 실력 향상 추이
- **D-Day캘린더** - 채용 일정 관리

### 커뮤니티
- **합격자DB** - 합격 후기 및 기출질문
- **QnA게시판** - 질문/답변 커뮤니티
- **채용알림** - 항공사 채용 소식

## 설치 방법

### 1. 저장소 클론
```bash
git clone https://github.com/your-repo/flyready-lab.git
cd flyready-lab
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env.example`을 복사하여 `.env` 파일 생성:
```bash
cp .env.example .env
```

`.env` 파일에 API 키 설정:
```env
# 필수
OPENAI_API_KEY=sk-your-openai-api-key

# 선택 (추가 기능용)
GOOGLE_TTS_API_KEY=your-google-tts-key
DID_API_KEY=your-did-key
CLOVA_CLIENT_ID=your-clova-id
CLOVA_CLIENT_SECRET=your-clova-secret

# 앱 비밀번호 (필수)
TESTER_PASSWORD=your-tester-password
ADMIN_PASSWORD=your-admin-password
```

### 5. 실행
```bash
streamlit run 홈.py
```

브라우저에서 `http://localhost:8501` 접속

## API 키 발급 가이드

### OpenAI API (필수)
1. [OpenAI Platform](https://platform.openai.com/) 가입
2. API Keys 메뉴에서 새 키 생성
3. `.env`의 `OPENAI_API_KEY`에 입력

### Google Cloud TTS (선택)
1. [Google Cloud Console](https://console.cloud.google.com/) 프로젝트 생성
2. Cloud Text-to-Speech API 활성화
3. 사용자 인증 정보에서 API 키 생성
4. `.env`의 `GOOGLE_TTS_API_KEY`에 입력

### CLOVA API (선택)
1. [CLOVA Studio](https://clova.ai/studio) 가입
2. 서비스 앱 생성 후 키 발급
3. `.env`의 `CLOVA_CLIENT_ID`, `CLOVA_CLIENT_SECRET`에 입력

## 기술 스택

- **Frontend**: Streamlit
- **AI/ML**: OpenAI GPT-4, CLOVA HyperCLOVA X
- **TTS**: Google Cloud TTS, CLOVA Voice
- **분석**: Python, Pandas

## 프로젝트 구조

```
flyready-lab/
├── 홈.py                    # 메인 앱
├── pages/                   # 페이지 모듈
│   ├── 1_롤플레잉.py
│   ├── 2_영어면접.py
│   ├── 3_진도관리.py
│   ├── 4_모의면접.py
│   ├── 5_토론면접.py
│   └── ...
├── config.py                # 설정 및 상수
├── env_config.py            # 환경변수 관리
├── api_utils.py             # API 호출 유틸리티
├── llm_utils.py             # LLM 관련 유틸리티
├── voice_utils.py           # 음성 처리
├── video_utils.py           # 영상 처리
├── validation.py            # 입력 검증
├── logging_config.py        # 로깅 설정
├── requirements.txt         # 의존성 목록
├── .env.example             # 환경변수 템플릿
└── .gitignore               # Git 제외 파일
```

## 라이선스

본 프로젝트는 비공개 소프트웨어입니다. 무단 복제 및 배포를 금합니다.

## 문의

- Email: support@flyreadylab.com
- Website: https://flyreadylab.com
