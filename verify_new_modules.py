"""
신규 모듈 임포트 검증 스크립트
"""
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("FLYREADY 신규 모듈 검증")
print("=" * 50)

errors = []

# 1. tutorial_component
print("\n1. tutorial_component 검증...")
try:
    from tutorial_component import (
        render_tutorial_if_needed,
        is_tutorial_completed,
        show_tutorial_button,
        show_tutorial,
        mark_tutorial_completed,
        reset_tutorial,
    )
    print("   [OK] tutorial_component 임포트 성공")
except Exception as e:
    print(f"   [FAIL] {e}")
    errors.append(("tutorial_component", str(e)))

# 2. comparison_feedback_service
print("\n2. comparison_feedback_service 검증...")
try:
    from comparison_feedback_service import (
        get_previous_feedback_context,
        generate_comparison_feedback,
        render_comparison_feedback_ui,
    )
    print("   [OK] comparison_feedback_service 임포트 성공")
except Exception as e:
    print(f"   [FAIL] {e}")
    errors.append(("comparison_feedback_service", str(e)))

# 3. interview_history_utils
print("\n3. interview_history_utils 검증...")
try:
    from interview_history_utils import (
        save_interview_session,
        get_all_sessions,
        get_sessions_by_airline,
        get_weak_questions,
        delete_session,
    )
    print("   [OK] interview_history_utils 임포트 성공")
except Exception as e:
    print(f"   [FAIL] {e}")
    errors.append(("interview_history_utils", str(e)))

# 4. interview_review_service
print("\n4. interview_review_service 검증...")
try:
    from interview_review_service import (
        get_weekly_recommendation,
        get_improvement_trend,
        get_category_analysis,
        get_practice_again_list,
    )
    print("   [OK] interview_review_service 임포트 성공")
except Exception as e:
    print(f"   [FAIL] {e}")
    errors.append(("interview_review_service", str(e)))

# 5. error_components
print("\n5. error_components 검증...")
try:
    from error_components import (
        show_server_error,
        show_timeout_error,
        show_limit_exceeded,
        show_input_error,
    )
    print("   [OK] error_components 임포트 성공")
except Exception as e:
    print(f"   [FAIL] {e}")
    errors.append(("error_components", str(e)))

# 6. 페이지 파일 구문 검사
print("\n6. 주요 페이지 파일 구문 검증...")
pages_to_check = [
    "pages/0_시작하기.py",
    "pages/4_모의면접.py",
    "pages/6_성장그래프.py",
    "pages/17_자소서기반질문.py",
    "pages/25_면접히스토리.py",
]

for page in pages_to_check:
    filepath = os.path.join(os.path.dirname(__file__), page)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                code = f.read()
            compile(code, filepath, "exec")
            print(f"   [OK] {page}")
        except SyntaxError as e:
            print(f"   [FAIL] {page}: Line {e.lineno} - {e.msg}")
            errors.append((page, f"Line {e.lineno}: {e.msg}"))
    else:
        print(f"   [SKIP] {page} 파일 없음")

# 결과 요약
print("\n" + "=" * 50)
if errors:
    print(f"검증 완료: {len(errors)}개 오류 발견")
    for module, error in errors:
        print(f"  - {module}: {error}")
else:
    print("검증 완료: 모든 모듈 정상!")
print("=" * 50)

sys.exit(0 if not errors else 1)
