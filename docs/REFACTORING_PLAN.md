# FlyReady Lab 대형 파일 리팩토링 계획
## Stage 3: 코드 품질 개선

---

## 현황 분석

### 대형 파일 목록 (500줄 초과 기준)

| 파일 | 줄 수 | 상태 | 우선순위 |
|------|-------|------|----------|
| `pages/17_자소서기반질문.py` | 2,712 | 리팩토링 필요 | 높음 |
| `pages/8_면접꿀팁.py` | 2,561 | 리팩토링 필요 | 높음 |
| `config.py` | 2,407 | 리팩토링 필요 | 중간 |

---

## 1. `pages/17_자소서기반질문.py` 리팩토링 계획

### 현재 문제점
- 2,712줄의 단일 파일
- UI 로직, 비즈니스 로직, 데이터 처리가 혼재
- 테스트 어려움

### 제안 구조

```
essay_analysis/
├── __init__.py
├── analyzer.py          # 자소서 분석 로직
├── question_generator.py # 질문 생성 로직
├── ui_components.py     # UI 컴포넌트
├── prompts.py           # LLM 프롬프트 템플릿
└── validators.py        # 입력 검증
```

### 분리 대상
1. **analyzer.py** (~400줄)
   - `_srcai_analyze_text()`
   - `_classify_prompt_type_kor()`
   - `_extract_topic_keywords_short()`
   - `_pick_situation_snippet()`

2. **question_generator.py** (~500줄)
   - Q1 ~ Q5 질문 생성 함수들
   - 항공사별 질문 커스터마이징

3. **ui_components.py** (~300줄)
   - 결과 표시 UI
   - 진행 단계 UI

4. **prompts.py** (~200줄)
   - LLM 프롬프트 템플릿
   - Few-shot 예시

### 마이그레이션 단계
1. 새 모듈 생성
2. 함수 이동 (import 유지)
3. 기존 페이지에서 import 변경
4. 테스트 작성
5. 기존 함수 deprecated 처리

---

## 2. `pages/8_면접꿀팁.py` 리팩토링 계획

### 현재 문제점
- 2,561줄의 단일 파일
- 팁 데이터와 UI가 혼재
- 하드코딩된 콘텐츠

### 제안 구조

```
interview_tips/
├── __init__.py
├── data/
│   ├── tips.json        # 팁 데이터 (JSON)
│   ├── categories.json  # 카테고리 정의
│   └── airlines.json    # 항공사별 특화 팁
├── loader.py            # 데이터 로더
├── renderer.py          # UI 렌더링
└── search.py            # 검색/필터링
```

### 분리 대상
1. **data/*.json** (~1,500줄 → JSON)
   - 모든 팁 콘텐츠
   - 카테고리 메타데이터
   - 항공사별 팁

2. **loader.py** (~100줄)
   - JSON 로드
   - 캐싱
   - 필터링

3. **renderer.py** (~300줄)
   - 팁 카드 렌더링
   - 카테고리 네비게이션

### 마이그레이션 단계
1. 데이터 추출 → JSON 파일
2. 로더 모듈 생성
3. 렌더러 모듈 생성
4. 페이지 파일 슬림화
5. 검색 기능 추가

---

## 3. `config.py` 리팩토링 계획

### 현재 문제점
- 2,407줄의 단일 설정 파일
- 항공사 데이터, 질문 템플릿, 설정이 혼재
- 순환 import 위험

### 제안 구조

```
config/
├── __init__.py          # 통합 export
├── settings.py          # 앱 설정 (환경변수, 상수)
├── airlines/
│   ├── __init__.py
│   ├── data.py          # 항공사 기본 정보
│   ├── values.py        # 항공사별 인재상
│   └── questions.py     # 항공사별 질문 풀
├── interview/
│   ├── __init__.py
│   ├── templates.py     # 질문 템플릿
│   ├── prompts.py       # LLM 프롬프트
│   └── tips.py          # 면접 팁
└── ui/
    ├── __init__.py
    └── constants.py     # UI 상수
```

### 분리 대상
1. **settings.py** (~200줄)
   - `LLM_MODEL_NAME`, `LLM_API_URL`, `LLM_TIMEOUT_SEC`
   - 환경 변수 관련

2. **airlines/data.py** (~300줄)
   - `AIRLINES`, `AIRLINE_TYPE`
   - 항공사 기본 정보

3. **airlines/values.py** (~400줄)
   - `AIRLINE_VALUES`, `FSC_VALUE_DATA`, `LCC_VALUE_DATA`
   - 항공사별 인재상

4. **airlines/questions.py** (~600줄)
   - `Q1_POOL_*`, `Q5_POOL_*`
   - 질문 풀

5. **interview/templates.py** (~500줄)
   - `VALUE_Q_TEMPLATES_*`
   - `Q2_ATTACK_TEMPLATES` 등

### 마이그레이션 단계
1. config/ 패키지 생성
2. 설정별 모듈 분리
3. `__init__.py`에서 하위 호환 export
4. 점진적 import 변경
5. deprecated 경고 추가

---

## 실행 타임라인

### Phase 1: 준비 (즉시)
- [ ] 디렉토리 구조 생성
- [ ] 빈 모듈 파일 생성
- [ ] __init__.py에서 기존 import 유지

### Phase 2: config.py 분리 (우선순위 1)
- [ ] settings.py 분리
- [ ] airlines/ 패키지 분리
- [ ] interview/ 패키지 분리
- [ ] 테스트 추가

### Phase 3: 8_면접꿀팁.py 분리 (우선순위 2)
- [ ] 데이터 JSON 추출
- [ ] 로더/렌더러 분리
- [ ] 페이지 파일 슬림화

### Phase 4: 17_자소서기반질문.py 분리 (우선순위 3)
- [ ] 분석 로직 분리
- [ ] 질문 생성 분리
- [ ] UI 컴포넌트 분리

---

## 하위 호환성 전략

### 기존 import 유지

```python
# config/__init__.py
from config.settings import *
from config.airlines import *
from config.interview import *

# Deprecated warning
import warnings

def __getattr__(name):
    if name in _deprecated_names:
        warnings.warn(
            f"{name} is deprecated, import from config.{_deprecated_names[name]} instead",
            DeprecationWarning,
            stacklevel=2
        )
        return globals()[name]
    raise AttributeError(f"module 'config' has no attribute '{name}'")
```

### 점진적 마이그레이션

1. 새 모듈에서 함수 정의
2. 기존 파일에서 새 모듈 import 후 re-export
3. 사용처 점진적 변경
4. 충분한 시간 후 기존 export 제거

---

## 코드 품질 기준

### 리팩토링 후 목표
- 각 파일 500줄 이하
- 단일 책임 원칙 준수
- 테스트 커버리지 80% 이상
- 순환 import 없음
- Type hints 추가

### 검증 방법
```bash
# 줄 수 확인
wc -l config/*.py config/**/*.py

# Import 그래프 확인
pydeps config --max-bacon=2

# 순환 import 검사
pylint --disable=all --enable=cyclic-import .
```

---

## 위험 요소 및 대응

| 위험 | 대응 |
|------|------|
| 기존 페이지 import 깨짐 | `__init__.py`에서 하위 호환 export |
| 순환 import | 지연 import, TYPE_CHECKING |
| 테스트 실패 | 마이그레이션 전 테스트 작성 |
| 배포 중단 | 단계별 배포, 롤백 계획 |

---

## 완료 기준

- [ ] 모든 파일 500줄 이하
- [ ] 기존 기능 100% 동작
- [ ] 테스트 통과
- [ ] import 경고 없음
- [ ] 문서화 완료
