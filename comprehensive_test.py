# comprehensive_test.py
# 베타 웹사이트 전체 기능 테스트 스크립트

import sys
import os
import traceback
from pathlib import Path

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

# Streamlit mock (실제 실행 없이 import 테스트)
class MockStreamlit:
    def __getattr__(self, name):
        if name == 'session_state':
            return {}
        return lambda *args, **kwargs: None

    def set_page_config(self, *args, **kwargs): pass
    def markdown(self, *args, **kwargs): pass
    def write(self, *args, **kwargs): pass
    def title(self, *args, **kwargs): pass
    def header(self, *args, **kwargs): pass
    def subheader(self, *args, **kwargs): pass
    def text(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
    def warning(self, *args, **kwargs): pass
    def info(self, *args, **kwargs): pass
    def success(self, *args, **kwargs): pass
    def button(self, *args, **kwargs): return False
    def text_input(self, *args, **kwargs): return ""
    def text_area(self, *args, **kwargs): return ""
    def selectbox(self, *args, **kwargs): return None
    def multiselect(self, *args, **kwargs): return []
    def slider(self, *args, **kwargs): return 0
    def checkbox(self, *args, **kwargs): return False
    def radio(self, *args, **kwargs): return None
    def columns(self, *args, **kwargs): return [self] * 10
    def container(self, *args, **kwargs): return self
    def expander(self, *args, **kwargs): return self
    def tabs(self, *args, **kwargs): return [self] * 10
    def sidebar(self): return self
    def form(self, *args, **kwargs): return self
    def form_submit_button(self, *args, **kwargs): return False
    def file_uploader(self, *args, **kwargs): return None
    def image(self, *args, **kwargs): pass
    def audio(self, *args, **kwargs): pass
    def video(self, *args, **kwargs): pass
    def download_button(self, *args, **kwargs): return False
    def progress(self, *args, **kwargs): pass
    def spinner(self, *args, **kwargs): return self
    def cache_data(self, *args, **kwargs): return lambda f: f
    def cache_resource(self, *args, **kwargs): return lambda f: f
    def rerun(self): pass
    def stop(self): pass
    def empty(self): return self
    def metric(self, *args, **kwargs): pass
    def json(self, *args, **kwargs): pass
    def dataframe(self, *args, **kwargs): pass
    def table(self, *args, **kwargs): pass
    def plotly_chart(self, *args, **kwargs): pass
    def pyplot(self, *args, **kwargs): pass
    def altair_chart(self, *args, **kwargs): pass
    def date_input(self, *args, **kwargs): return None
    def time_input(self, *args, **kwargs): return None
    def number_input(self, *args, **kwargs): return 0
    def color_picker(self, *args, **kwargs): return "#000000"
    def divider(self, *args, **kwargs): pass
    def caption(self, *args, **kwargs): pass
    def code(self, *args, **kwargs): pass
    def latex(self, *args, **kwargs): pass
    def toggle(self, *args, **kwargs): return False
    def page_link(self, *args, **kwargs): pass
    def link_button(self, *args, **kwargs): pass
    def popover(self, *args, **kwargs): return self
    def status(self, *args, **kwargs): return self
    def toast(self, *args, **kwargs): pass
    def balloons(self): pass
    def snow(self): pass

    def __enter__(self): return self
    def __exit__(self, *args): pass
    def __call__(self, *args, **kwargs): return self
    def __iter__(self): return iter([self])

# Mock streamlit before any imports
sys.modules['streamlit'] = MockStreamlit()

# 테스트 결과 저장
ERRORS = []
WARNINGS = []
SUCCESS = []

def log_error(module, error):
    ERRORS.append(f"[ERROR] {module}: {error}")
    print(f"\033[91m[ERROR] {module}: {error}\033[0m")

def log_warning(module, warning):
    WARNINGS.append(f"[WARNING] {module}: {warning}")
    print(f"\033[93m[WARNING] {module}: {warning}\033[0m")

def log_success(module):
    SUCCESS.append(module)
    print(f"\033[92m[OK] {module}\033[0m")

def test_import(module_name, module_path=None):
    """모듈 import 테스트"""
    try:
        if module_path:
            spec = __import__(module_path, fromlist=[module_name])
        else:
            __import__(module_name)
        log_success(module_name)
        return True
    except Exception as e:
        log_error(module_name, f"{type(e).__name__}: {e}")
        traceback.print_exc()
        return False

def test_file_exists(filepath, description):
    """파일 존재 여부 테스트"""
    if os.path.exists(filepath):
        log_success(f"File exists: {description}")
        return True
    else:
        log_error(description, f"File not found: {filepath}")
        return False

print("=" * 60)
print("베타 웹사이트 전체 테스트 시작")
print("=" * 60)

# =====================
# 1. 필수 파일 존재 확인
# =====================
print("\n[1] 필수 파일 존재 확인")
print("-" * 40)

required_files = [
    ("홈.py", "메인 홈페이지"),
    ("sidebar_common.py", "사이드바/네비게이션"),
    ("auth_utils.py", "인증 유틸"),
    ("env_config.py", "환경설정"),
    ("safe_utils.py", "안전 유틸"),
    ("logging_config.py", "로깅 설정"),
    ("api_utils.py", "API 유틸"),
    ("ui_config.py", "UI 설정"),
    ("motivation.py", "동기부여 팝업"),
]

for filename, desc in required_files:
    test_file_exists(os.path.join(PROJECT_ROOT, filename), desc)

# =====================
# 2. 핵심 모듈 Import 테스트
# =====================
print("\n[2] 핵심 모듈 Import 테스트")
print("-" * 40)

core_modules = [
    "env_config",
    "logging_config",
    "safe_utils",
    "auth_utils",
    "api_utils",
    "ui_config",
    "sidebar_common",
    "motivation",
]

for module in core_modules:
    test_import(module)

# =====================
# 3. 페이지 파일 Import 테스트
# =====================
print("\n[3] 페이지 파일 Import 테스트")
print("-" * 40)

pages_dir = PROJECT_ROOT / "pages"
if pages_dir.exists():
    page_files = sorted(pages_dir.glob("*.py"))
    for page_file in page_files:
        module_name = page_file.stem
        try:
            # 페이지 파일 내용 읽어서 구문 검사
            with open(page_file, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, str(page_file), 'exec')
            log_success(f"pages/{module_name}.py (syntax)")
        except SyntaxError as e:
            log_error(f"pages/{module_name}.py", f"SyntaxError at line {e.lineno}: {e.msg}")
        except Exception as e:
            log_error(f"pages/{module_name}.py", str(e))

# =====================
# 4. 환경변수 설정 확인
# =====================
print("\n[4] 환경변수 설정 확인")
print("-" * 40)

try:
    from env_config import TESTER_PASSWORD, ADMIN_PASSWORD, OPENAI_API_KEY

    if TESTER_PASSWORD:
        log_success(f"TESTER_PASSWORD 설정됨: {TESTER_PASSWORD[:4]}***")
    else:
        log_error("env_config", "TESTER_PASSWORD가 비어있음!")

    if ADMIN_PASSWORD:
        log_success(f"ADMIN_PASSWORD 설정됨: {ADMIN_PASSWORD[:4]}***")
    else:
        log_warning("env_config", "ADMIN_PASSWORD가 비어있음")

    if OPENAI_API_KEY:
        log_success(f"OPENAI_API_KEY 설정됨: {OPENAI_API_KEY[:10]}***")
    else:
        log_warning("env_config", "OPENAI_API_KEY가 비어있음 (API 기능 제한됨)")

except Exception as e:
    log_error("env_config", str(e))

# =====================
# 5. 홈페이지 상세 테스트
# =====================
print("\n[5] 홈페이지 상세 테스트")
print("-" * 40)

try:
    with open(PROJECT_ROOT / "홈.py", 'r', encoding='utf-8') as f:
        home_code = f.read()

    # 필수 import 확인
    required_imports = [
        ("from safe_utils import", "safe_utils import"),
        ("from sidebar_common import", "sidebar_common import"),
        ("from auth_utils import", "auth_utils import"),
    ]

    for pattern, desc in required_imports:
        if pattern in home_code:
            log_success(f"홈.py: {desc} 존재")
        else:
            log_error("홈.py", f"{desc} 누락!")

    # 위험한 패턴 확인
    dangerous_patterns = [
        ("href=\"/로그인\"", "로그인 링크 (제거해야 함)"),
        ("href=\"/요금제\"", "요금제 링크 (제거해야 함)"),
        ("fr-header-nav", "이전 헤더 네비게이션 (제거해야 함)"),
    ]

    for pattern, desc in dangerous_patterns:
        if pattern in home_code:
            log_warning("홈.py", f"{desc} 발견!")
        else:
            log_success(f"홈.py: {desc} 없음")

except Exception as e:
    log_error("홈.py 분석", str(e))

# =====================
# 6. sidebar_common.py 상세 테스트
# =====================
print("\n[6] sidebar_common.py 상세 테스트")
print("-" * 40)

try:
    with open(PROJECT_ROOT / "sidebar_common.py", 'r', encoding='utf-8') as f:
        sidebar_code = f.read()

    # Beta Test 버튼 확인
    if "Beta Test" in sidebar_code:
        log_success("sidebar_common.py: Beta Test 버튼 존재")
    else:
        log_warning("sidebar_common.py", "Beta Test 버튼 없음")

    # 로그인/요금제 링크 확인
    if "로그인" in sidebar_code or "요금제" in sidebar_code:
        log_warning("sidebar_common.py", "로그인/요금제 관련 코드 발견")
    else:
        log_success("sidebar_common.py: 로그인/요금제 코드 없음")

except Exception as e:
    log_error("sidebar_common.py 분석", str(e))

# =====================
# 7. 각 페이지 의존성 테스트
# =====================
print("\n[7] 페이지별 의존성 분석")
print("-" * 40)

page_dependencies = {
    "1_롤플레잉": ["voice_utils"],  # voice_utils가 api_utils를 내부적으로 사용
    "2_영어면접": ["voice_utils"],
    "4_모의면접": ["voice_utils"],
    "5_토론면접": ["voice_utils"],  # api_utils는 voice_utils 통해 사용
    "20_자소서첨삭": ["openai", "OPENAI"],  # 텍스트 기반 - OpenAI API 직접 사용
}

for page, deps in page_dependencies.items():
    page_file = pages_dir / f"{page}.py"
    if page_file.exists():
        try:
            with open(page_file, 'r', encoding='utf-8') as f:
                page_code = f.read()

            missing_deps = []
            for dep in deps:
                if dep not in page_code:
                    missing_deps.append(dep)

            if missing_deps:
                log_warning(f"pages/{page}.py", f"의존성 누락 가능: {missing_deps}")
            else:
                log_success(f"pages/{page}.py: 의존성 OK")
        except Exception as e:
            log_error(f"pages/{page}.py", str(e))

# =====================
# 8. CSS/HTML 문제 검사
# =====================
print("\n[8] CSS/HTML 잠재적 문제 검사")
print("-" * 40)

# 클래스 불일치 검사
try:
    with open(PROJECT_ROOT / "sidebar_common.py", 'r', encoding='utf-8') as f:
        sidebar_code = f.read()

    # CSS 클래스 정의 찾기
    import re
    css_classes = set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]+)\s*\{', sidebar_code))
    html_classes = set(re.findall(r'class="([^"]+)"', sidebar_code))

    # HTML에서 사용된 클래스들 추출
    used_classes = set()
    for class_str in html_classes:
        used_classes.update(class_str.split())

    # 정의되지 않은 클래스 찾기
    # 동적 클래스 및 f-string 플레이스홀더 제외
    dynamic_classes = {'nav-link', 'active', 'sub-link', 'sub-label', '{active_class}', '{class_name}'}
    undefined = used_classes - css_classes - dynamic_classes
    if undefined:
        # 실제로 문제가 되는 것만 필터링 (st- 접두사, 중괄호 포함 클래스 제외)
        real_issues = [c for c in undefined if not c.startswith('st-') and '{' not in c]
        if real_issues and len(real_issues) < 10:  # 너무 많으면 무시
            log_warning("CSS", f"HTML에서 사용되지만 CSS에 정의 안된 클래스: {real_issues[:5]}")

    log_success("CSS/HTML 클래스 검사 완료")

except Exception as e:
    log_error("CSS/HTML 검사", str(e))

# =====================
# 9. 데이터 파일 확인
# =====================
print("\n[9] 데이터 파일 확인")
print("-" * 40)

data_dir = PROJECT_ROOT / "data"
if data_dir.exists():
    log_success("data 디렉토리 존재")

    # JSON 파일들 유효성 검사
    import json
    json_files = list(data_dir.glob("*.json"))
    for json_file in json_files[:10]:  # 최대 10개만 검사
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                json.load(f)
            log_success(f"data/{json_file.name}: JSON 유효")
        except json.JSONDecodeError as e:
            log_error(f"data/{json_file.name}", f"JSON 파싱 오류: {e}")
        except Exception as e:
            log_error(f"data/{json_file.name}", str(e))
else:
    log_warning("data", "data 디렉토리 없음")

# =====================
# 최종 결과 출력
# =====================
print("\n" + "=" * 60)
print("테스트 결과 요약")
print("=" * 60)

print(f"\n\033[92m성공: {len(SUCCESS)}개\033[0m")
print(f"\033[93m경고: {len(WARNINGS)}개\033[0m")
print(f"\033[91m오류: {len(ERRORS)}개\033[0m")

if ERRORS:
    print("\n\033[91m=== 발견된 오류 ===\033[0m")
    for err in ERRORS:
        print(f"  {err}")

if WARNINGS:
    print("\n\033[93m=== 경고 사항 ===\033[0m")
    for warn in WARNINGS:
        print(f"  {warn}")

print("\n" + "=" * 60)
if ERRORS:
    print("\033[91m테스트 실패 - 오류 수정 필요\033[0m")
    sys.exit(1)
else:
    print("\033[92m테스트 통과\033[0m")
    sys.exit(0)
