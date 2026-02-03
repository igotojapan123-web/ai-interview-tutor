# user_experience_test.py
# 사용자 경험 시뮬레이션 테스트

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

print("=" * 70)
print("사용자 경험 시뮬레이션 테스트")
print("=" * 70)

ISSUES = []
GOOD = []

def check(condition, good_msg, bad_msg):
    if condition:
        GOOD.append(good_msg)
        print(f"\033[92m[OK] {good_msg}\033[0m")
    else:
        ISSUES.append(bad_msg)
        print(f"\033[91m[ISSUE] {bad_msg}\033[0m")

# =====================
# 1. 로그인 화면 테스트
# =====================
print("\n[1] 로그인 화면 (비밀번호 입력)")
print("-" * 50)

with open(PROJECT_ROOT / "auth_utils.py", 'r', encoding='utf-8') as f:
    auth_code = f.read()

check(
    'type="password"' in auth_code,
    "비밀번호 입력란이 password 타입으로 설정됨 (보안)",
    "비밀번호 입력란이 일반 텍스트로 노출될 수 있음"
)

check(
    "비밀번호를 입력하세요" in auth_code,
    "비밀번호 입력 안내 문구 있음",
    "비밀번호 입력 안내 문구 없음"
)

check(
    "비밀번호가 틀렸습니다" in auth_code,
    "잘못된 비밀번호 시 에러 메시지 표시",
    "잘못된 비밀번호 처리 없음"
)

# 비밀번호 기본값 확인
with open(PROJECT_ROOT / "env_config.py", 'r', encoding='utf-8') as f:
    env_code = f.read()

check(
    '"2026fly"' in env_code,
    "기본 비밀번호 2026fly 설정됨",
    "기본 비밀번호가 설정되지 않음!"
)

# =====================
# 2. 홈페이지 레이아웃
# =====================
print("\n[2] 홈페이지 레이아웃")
print("-" * 50)

with open(PROJECT_ROOT / "홈.py", 'r', encoding='utf-8') as f:
    home_code = f.read()

check(
    "from sidebar_common import render_sidebar" in home_code,
    "통일된 네비게이션 바 사용 (sidebar_common)",
    "네비게이션 바가 통일되지 않음"
)

check(
    'render_sidebar("home")' in home_code,
    "홈페이지에서 네비게이션 렌더링",
    "네비게이션이 렌더링되지 않을 수 있음"
)

check(
    'href="/로그인"' not in home_code and 'href="/요금제"' not in home_code,
    "로그인/요금제 링크 제거됨",
    "로그인/요금제 링크가 아직 있음!"
)

check(
    "AI와 함께하는 승무원 면접 준비" in home_code,
    "메인 히어로 타이틀 있음",
    "메인 히어로 타이틀 없음"
)

check(
    "무료로 시작하기" not in home_code or home_code.count("무료로 시작하기") == 0,
    "무료로 시작하기 버튼 제거됨",
    "무료로 시작하기 버튼이 아직 있음"
)

# =====================
# 3. 네비게이션 바
# =====================
print("\n[3] 네비게이션 바")
print("-" * 50)

with open(PROJECT_ROOT / "sidebar_common.py", 'r', encoding='utf-8') as f:
    sidebar_code = f.read()

check(
    "Beta Test" in sidebar_code,
    "Beta Test 뱃지 표시됨",
    "Beta Test 뱃지 없음"
)

check(
    sidebar_code.count("Beta Test") == 1,
    "Beta Test 뱃지가 하나만 있음",
    f"Beta Test 뱃지가 {sidebar_code.count('Beta Test')}개 있음 (중복!)"
)

check(
    "flyready-nav" in sidebar_code,
    "FlyReady 네비게이션 스타일 적용됨",
    "네비게이션 스타일 없음"
)

check(
    "면접연습" in sidebar_code and "준비도구" in sidebar_code and "학습정보" in sidebar_code,
    "메인 카테고리 (면접연습, 준비도구, 학습정보) 있음",
    "메인 카테고리 누락"
)

check(
    "로그인" not in sidebar_code and "요금제" not in sidebar_code,
    "네비게이션에 로그인/요금제 없음",
    "네비게이션에 로그인/요금제가 있음!"
)

# =====================
# 4. 주요 기능 페이지 접근성
# =====================
print("\n[4] 주요 기능 페이지")
print("-" * 50)

pages_to_check = [
    ("pages/1_롤플레잉.py", "롤플레잉"),
    ("pages/2_영어면접.py", "영어면접"),
    ("pages/4_모의면접.py", "모의면접"),
    ("pages/5_토론면접.py", "토론면접"),
    ("pages/20_자소서첨삭.py", "자소서첨삭"),
]

for page_path, page_name in pages_to_check:
    full_path = PROJECT_ROOT / page_path
    if full_path.exists():
        with open(full_path, 'r', encoding='utf-8') as f:
            page_code = f.read()

        # 페이지 제목 있는지
        has_title = "st.title" in page_code or "st.header" in page_code or "st.subheader" in page_code
        check(
            has_title,
            f"{page_name}: 페이지 제목 있음",
            f"{page_name}: 페이지 제목 없음"
        )

        # 에러 처리 있는지
        has_error_handling = "try:" in page_code and "except" in page_code
        check(
            has_error_handling,
            f"{page_name}: 에러 처리 있음",
            f"{page_name}: 에러 처리 없음 (충돌 가능)"
        )
    else:
        ISSUES.append(f"{page_name}: 페이지 파일 없음!")

# =====================
# 5. CSS/디자인 일관성
# =====================
print("\n[5] CSS/디자인 일관성")
print("-" * 50)

# 메인 색상 확인
check(
    "#2563EB" in sidebar_code or "#3b82f6" in sidebar_code,
    "메인 브랜드 색상 (파란색) 적용됨",
    "브랜드 색상 누락"
)

check(
    "#10b981" in sidebar_code,
    "Beta Test 뱃지 색상 (초록색) 적용됨",
    "Beta Test 뱃지 색상 없음"
)

# 반응형 디자인
check(
    "@media" in sidebar_code,
    "반응형 디자인 (모바일 대응) 있음",
    "반응형 디자인 없음"
)

# =====================
# 6. 성능 관련
# =====================
print("\n[6] 성능 최적화")
print("-" * 50)

check(
    "@st.cache_resource" in home_code or "@st.cache_data" in home_code,
    "홈페이지에 캐싱 적용됨",
    "홈페이지 캐싱 없음 (느릴 수 있음)"
)

# 로고 캐싱
check(
    "get_logo_base64" in home_code and "cache_resource" in home_code,
    "로고 이미지 캐싱됨",
    "로고 이미지 캐싱 안됨"
)

# =====================
# 7. 데이터 저장/불러오기
# =====================
print("\n[7] 데이터 저장/불러오기")
print("-" * 50)

data_dir = PROJECT_ROOT / "data"
check(
    data_dir.exists(),
    "data 디렉토리 존재",
    "data 디렉토리 없음"
)

if data_dir.exists():
    json_files = list(data_dir.glob("*.json"))
    check(
        len(json_files) > 0,
        f"데이터 파일 {len(json_files)}개 존재",
        "데이터 파일 없음"
    )

# =====================
# 8. 오류 메시지 사용자 친화성
# =====================
print("\n[8] 오류 메시지 사용자 친화성")
print("-" * 50)

# API 키 없을 때 안내
with open(PROJECT_ROOT / "api_utils.py", 'r', encoding='utf-8') as f:
    api_code = f.read()

check(
    "API 키" in api_code and ("추가하세요" in api_code or "설정" in api_code),
    "API 키 오류 시 친절한 안내 메시지",
    "API 키 오류 메시지 불친절할 수 있음"
)

# =====================
# 9. 접근성
# =====================
print("\n[9] 접근성")
print("-" * 50)

check(
    "page_title=" in home_code,
    "브라우저 탭 제목 설정됨",
    "브라우저 탭 제목 없음"
)

check(
    "page_icon=" in home_code,
    "파비콘 설정됨",
    "파비콘 없음"
)

# =====================
# 최종 결과
# =====================
print("\n" + "=" * 70)
print("사용자 경험 테스트 결과")
print("=" * 70)

print(f"\n\033[92m통과: {len(GOOD)}개\033[0m")
print(f"\033[91m문제: {len(ISSUES)}개\033[0m")

if ISSUES:
    print("\n\033[91m=== 발견된 문제 ===\033[0m")
    for issue in ISSUES:
        print(f"  - {issue}")
    print("\n이 문제들을 수정해야 합니다!")
    sys.exit(1)
else:
    print("\n\033[92m모든 사용자 경험 테스트 통과!\033[0m")
    print("사용자들이 만족할 수 있는 상태입니다.")
    sys.exit(0)
