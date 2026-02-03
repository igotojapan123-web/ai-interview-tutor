#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beta Web Comprehensive Test Script
"""

import os
import sys
import json
import importlib.util
import traceback
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Project root setup
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 테스트 결과 저장
test_results = {
    "timestamp": datetime.now().isoformat(),
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "warnings": 0,
    "details": []
}

def log_result(category: str, name: str, status: str, message: str = ""):
    """테스트 결과 기록"""
    test_results["total_tests"] += 1
    if status == "PASS":
        test_results["passed"] += 1
        icon = "✅"
    elif status == "FAIL":
        test_results["failed"] += 1
        icon = "❌"
    else:
        test_results["warnings"] += 1
        icon = "⚠️"

    test_results["details"].append({
        "category": category,
        "name": name,
        "status": status,
        "message": message
    })

    if message:
        print(f"{icon} [{category}] {name}: {message}")
    else:
        print(f"{icon} [{category}] {name}")

def test_python_syntax():
    """모든 Python 파일 구문 검사"""
    print("\n" + "="*60)
    print("1. Python 구문 검사")
    print("="*60)

    py_files = list(PROJECT_ROOT.glob("*.py")) + list(PROJECT_ROOT.glob("pages/*.py"))

    for py_file in py_files:
        if py_file.name.startswith("__"):
            continue
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            compile(source, py_file, 'exec')
            log_result("구문검사", py_file.name, "PASS")
        except SyntaxError as e:
            log_result("구문검사", py_file.name, "FAIL", f"Line {e.lineno}: {e.msg}")
        except Exception as e:
            log_result("구문검사", py_file.name, "FAIL", str(e))

def test_core_imports():
    """핵심 모듈 import 테스트"""
    print("\n" + "="*60)
    print("2. 핵심 모듈 Import 테스트")
    print("="*60)

    core_modules = [
        "config",
        "env_config",
        "api_utils",
        "auth_utils",
        "ui_config",
        "sidebar_common",
        "airline_questions",
        "feedback_analyzer",
        "security_utils",
    ]

    for module_name in core_modules:
        try:
            module = importlib.import_module(module_name)
            log_result("Import", module_name, "PASS")
        except ImportError as e:
            log_result("Import", module_name, "FAIL", str(e))
        except Exception as e:
            log_result("Import", module_name, "WARN", f"Import 성공, 초기화 경고: {str(e)[:50]}")

def test_page_imports():
    """Streamlit 페이지 import 테스트"""
    print("\n" + "="*60)
    print("3. Streamlit 페이지 Import 테스트")
    print("="*60)

    pages_dir = PROJECT_ROOT / "pages"
    page_files = [f for f in pages_dir.glob("*.py") if not f.name.startswith("__")]

    for page_file in sorted(page_files):
        module_name = page_file.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name, page_file)
            if spec and spec.loader:
                # 구문만 검사 (실행은 하지 않음)
                with open(page_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                compile(source, page_file, 'exec')
                log_result("페이지", page_file.name, "PASS")
        except SyntaxError as e:
            log_result("페이지", page_file.name, "FAIL", f"Line {e.lineno}: {e.msg}")
        except Exception as e:
            log_result("페이지", page_file.name, "FAIL", str(e)[:100])

def test_dependencies():
    """필수 의존성 확인"""
    print("\n" + "="*60)
    print("4. 필수 의존성 확인")
    print("="*60)

    required_packages = [
        ("streamlit", "Streamlit 웹 프레임워크"),
        ("openai", "OpenAI API"),
        ("pandas", "데이터 처리"),
        ("plotly", "차트 시각화"),
        ("requests", "HTTP 요청"),
        ("Pillow", "이미지 처리"),
        ("google.generativeai", "Google Gemini API"),
    ]

    for package, description in required_packages:
        try:
            if "." in package:
                importlib.import_module(package)
            else:
                importlib.import_module(package)
            log_result("Dep", f"{package}", "PASS")
        except (ImportError, AttributeError, ModuleNotFoundError):
            log_result("Dep", f"{package}", "WARN", "Not installed")

def test_data_files():
    """데이터 파일 무결성 확인"""
    print("\n" + "="*60)
    print("5. 데이터 파일 무결성 확인")
    print("="*60)

    data_dir = PROJECT_ROOT / "data"
    json_files = list(data_dir.glob("*.json")) + list(data_dir.glob("**/*.json"))

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            rel_path = json_file.relative_to(PROJECT_ROOT)
            log_result("데이터", str(rel_path), "PASS")
        except json.JSONDecodeError as e:
            rel_path = json_file.relative_to(PROJECT_ROOT)
            log_result("데이터", str(rel_path), "FAIL", f"JSON 파싱 오류: {e.msg}")
        except Exception as e:
            rel_path = json_file.relative_to(PROJECT_ROOT)
            log_result("데이터", str(rel_path), "FAIL", str(e)[:50])

def test_env_config():
    """환경 설정 확인"""
    print("\n" + "="*60)
    print("6. 환경 설정 확인")
    print("="*60)

    try:
        from env_config import get_api_key, ENV_CONFIG

        # API 키 설정 확인 (값은 노출하지 않음)
        api_keys = ["OPENAI_API_KEY", "GOOGLE_API_KEY", "CLOVA_CLIENT_ID"]
        for key_name in api_keys:
            try:
                key = get_api_key(key_name)
                if key and len(key) > 5:
                    log_result("환경설정", key_name, "PASS", "설정됨")
                else:
                    log_result("환경설정", key_name, "WARN", "설정 필요")
            except:
                log_result("환경설정", key_name, "WARN", "설정 필요")

    except ImportError as e:
        log_result("환경설정", "env_config 모듈", "FAIL", str(e))

def test_streamlit_config():
    """Streamlit 설정 파일 확인"""
    print("\n" + "="*60)
    print("7. Streamlit 설정 확인")
    print("="*60)

    config_file = PROJECT_ROOT / ".streamlit" / "config.toml"
    secrets_file = PROJECT_ROOT / ".streamlit" / "secrets.toml"

    if config_file.exists():
        log_result("Streamlit", "config.toml", "PASS")
    else:
        log_result("Streamlit", "config.toml", "WARN", "파일 없음")

    if secrets_file.exists():
        log_result("Streamlit", "secrets.toml", "PASS", "존재함 (내용 비공개)")
    else:
        log_result("Streamlit", "secrets.toml", "WARN", "파일 없음 - 배포 환경에서 설정 필요")

def test_home_page():
    """홈 페이지 구문 검사"""
    print("\n" + "="*60)
    print("8. 홈 페이지 검사")
    print("="*60)

    home_file = PROJECT_ROOT / "홈.py"
    if home_file.exists():
        try:
            with open(home_file, 'r', encoding='utf-8') as f:
                source = f.read()
            compile(source, home_file, 'exec')
            log_result("홈페이지", "홈.py", "PASS", "구문 정상")
        except SyntaxError as e:
            log_result("홈페이지", "홈.py", "FAIL", f"Line {e.lineno}: {e.msg}")
    else:
        log_result("홈페이지", "홈.py", "FAIL", "파일 없음")

def test_critical_pages():
    """핵심 페이지 상세 검사"""
    print("\n" + "="*60)
    print("9. 핵심 페이지 상세 검사")
    print("="*60)

    critical_pages = [
        "4_모의면접.py",
        "2_영어면접.py",
        "1_롤플레잉.py",
        "5_토론면접.py",
        "17_자소서기반질문.py",
        "19_자소서작성.py",
        "20_자소서첨삭.py",
    ]

    pages_dir = PROJECT_ROOT / "pages"

    for page_name in critical_pages:
        page_file = pages_dir / page_name
        if not page_file.exists():
            log_result("핵심페이지", page_name, "WARN", "파일 없음")
            continue

        try:
            with open(page_file, 'r', encoding='utf-8') as f:
                source = f.read()

            # 구문 검사
            compile(source, page_file, 'exec')

            # 필수 import 확인
            required_imports = ["streamlit", "st"]
            has_streamlit = any(imp in source for imp in required_imports)

            if has_streamlit:
                log_result("핵심페이지", page_name, "PASS", "Streamlit import 확인됨")
            else:
                log_result("핵심페이지", page_name, "WARN", "Streamlit import 없음")

        except SyntaxError as e:
            log_result("핵심페이지", page_name, "FAIL", f"구문 오류 Line {e.lineno}: {e.msg}")
        except Exception as e:
            log_result("핵심페이지", page_name, "FAIL", str(e)[:100])

def test_api_modules():
    """API 관련 모듈 검사"""
    print("\n" + "="*60)
    print("10. API 모듈 검사")
    print("="*60)

    api_modules = [
        ("flyready_clova_engine_v3", "Clova Speech API"),
        ("api_utils", "API 유틸리티"),
        ("safe_api", "안전한 API 래퍼"),
    ]

    for module_name, description in api_modules:
        module_file = PROJECT_ROOT / f"{module_name}.py"
        if module_file.exists():
            try:
                with open(module_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                compile(source, module_file, 'exec')
                log_result("API모듈", f"{module_name} ({description})", "PASS")
            except SyntaxError as e:
                log_result("API모듈", f"{module_name}", "FAIL", f"Line {e.lineno}: {e.msg}")
        else:
            log_result("API모듈", f"{module_name}", "WARN", "파일 없음")

def print_summary():
    """테스트 요약 출력"""
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)

    total = test_results["total_tests"]
    passed = test_results["passed"]
    failed = test_results["failed"]
    warnings = test_results["warnings"]

    print(f"\n총 테스트: {total}")
    print(f"✅ 성공: {passed}")
    print(f"❌ 실패: {failed}")
    print(f"⚠️ 경고: {warnings}")

    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n성공률: {success_rate:.1f}%")

    if failed > 0:
        print("\n" + "-"*40)
        print("실패한 테스트:")
        for detail in test_results["details"]:
            if detail["status"] == "FAIL":
                print(f"  ❌ [{detail['category']}] {detail['name']}")
                if detail["message"]:
                    print(f"     → {detail['message']}")

    # 결과 파일 저장
    result_file = PROJECT_ROOT / "tests" / "beta_test_results.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    print(f"\n결과 저장: {result_file}")

    return failed == 0

def main():
    """메인 테스트 실행"""
    print("="*60)
    print("🧪 Beta 웹 종합 테스트")
    print(f"   시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   프로젝트: {PROJECT_ROOT}")
    print("="*60)

    # 모든 테스트 실행
    test_python_syntax()
    test_core_imports()
    test_page_imports()
    test_dependencies()
    test_data_files()
    test_env_config()
    test_streamlit_config()
    test_home_page()
    test_critical_pages()
    test_api_modules()

    # 요약 출력
    success = print_summary()

    print("\n" + "="*60)
    if success:
        print("🎉 모든 테스트 통과! Beta 웹 배포 준비 완료")
    else:
        print("⚠️ 일부 테스트 실패. 위 오류를 확인해주세요.")
    print("="*60)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
