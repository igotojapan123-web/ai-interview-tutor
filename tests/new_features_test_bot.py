"""
FLYREADY 신규 기능 테스트 봇
- 면접 제보 시스템 (40_면접제보.py)
- 면접 예측 시스템 (41_면접예측.py)
- 자소서+뉴스 연계 (42_자소서뉴스연계.py)

테스트 항목:
1. 코드 구문 검사
2. 모듈 import 검사
3. 함수 동작 테스트
4. 데이터 흐름 검증
5. 핵심 원칙 준수 확인 (AI 창작 금지, 출처 명시 등)
"""

import os
import sys
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ai_tutor 루트를 path에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ═══════════════════════════════════════════
# 테스트 결과 저장
# ═══════════════════════════════════════════

class TestResult:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add(self, name: str, status: str, message: str = "", details: str = ""):
        self.tests.append({
            "name": name,
            "status": status,
            "message": message,
            "details": details
        })
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1

    def summary(self):
        total = self.passed + self.failed + self.warnings
        return {
            "total": total,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "pass_rate": f"{self.passed/total*100:.1f}%" if total > 0 else "0%"
        }


results = TestResult()


def log_test(name: str, status: str, message: str = "", details: str = ""):
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}.get(status, "[????]")
    print(f"{icon} {name}")
    if message:
        print(f"       {message}")
    if details:
        for line in details.split("\n")[:3]:
            print(f"       | {line}")
    results.add(name, status, message, details)


# ═══════════════════════════════════════════
# 테스트 1: 구문 검사
# ═══════════════════════════════════════════

def test_syntax():
    print("\n" + "="*60)
    print("  [1/5] 구문 검사 (Syntax Check)")
    print("="*60)

    files = [
        ROOT / "interview_report_system.py",
        ROOT / "pages" / "40_면접제보.py",
        ROOT / "pages" / "41_면접예측.py",
        ROOT / "pages" / "42_자소서뉴스연계.py",
    ]

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()
            compile(code, file.name, "exec")
            log_test(f"구문: {file.name}", "PASS")
        except SyntaxError as e:
            log_test(f"구문: {file.name}", "FAIL", f"Line {e.lineno}: {e.msg}")
        except FileNotFoundError:
            log_test(f"구문: {file.name}", "FAIL", "파일 없음")


# ═══════════════════════════════════════════
# 테스트 2: Import 검사
# ═══════════════════════════════════════════

def test_imports():
    print("\n" + "="*60)
    print("  [2/5] Import 검사")
    print("="*60)

    # interview_report_system 모듈 import 테스트
    try:
        from interview_report_system import (
            submit_report,
            get_reward_display,
            get_airline_report_count,
            check_duplicate_submission,
            generate_user_hash,
            calculate_reward,
            get_question_stats,
            get_recent_new_questions,
            get_trending_questions,
        )
        log_test("Import: interview_report_system", "PASS", "9개 함수 모두 import 성공")
    except ImportError as e:
        log_test("Import: interview_report_system", "FAIL", str(e))

    # config 모듈 import 테스트
    try:
        from config import AIRLINES
        log_test("Import: config.AIRLINES", "PASS", f"{len(AIRLINES)}개 항공사")
    except ImportError as e:
        log_test("Import: config.AIRLINES", "FAIL", str(e))

    # sidebar_common 모듈 import 테스트
    try:
        from sidebar_common import init_page, end_page
        log_test("Import: sidebar_common", "PASS")
    except ImportError as e:
        log_test("Import: sidebar_common", "FAIL", str(e))


# ═══════════════════════════════════════════
# 테스트 3: 함수 동작 테스트
# ═══════════════════════════════════════════

def test_functions():
    print("\n" + "="*60)
    print("  [3/5] 함수 동작 테스트")
    print("="*60)

    from interview_report_system import (
        calculate_reward,
        get_reward_display,
        generate_user_hash,
        check_duplicate_submission,
        get_airline_report_count,
        get_question_stats,
    )

    # 보상 계산 테스트
    print("\n  [보상 계산 테스트]")

    test_cases = [
        {
            "name": "8개 질문 + 꼬리질문 + 상세 → 14일",
            "input": {
                "questions": [{"question": f"Q{i}", "follow_up": "꼬리" if i == 0 else ""} for i in range(8)],
                "interview_mood": "보통",
                "duration_minutes": 15
            },
            "expected": "premium_14days"
        },
        {
            "name": "5개 질문 + 상세 → 7일",
            "input": {
                "questions": [{"question": f"Q{i}"} for i in range(5)],
                "interview_mood": "보통",
                "duration_minutes": 15
            },
            "expected": "premium_7days"
        },
        {
            "name": "3개 질문 → 3일",
            "input": {
                "questions": [{"question": f"Q{i}"} for i in range(3)],
                "interview_mood": None,
                "duration_minutes": None
            },
            "expected": "premium_3days"
        },
        {
            "name": "1개 질문 → 1일",
            "input": {
                "questions": [{"question": "Q1"}],
                "interview_mood": None,
                "duration_minutes": None
            },
            "expected": "premium_1day"
        },
        {
            "name": "0개 질문 → None",
            "input": {
                "questions": [],
                "interview_mood": None,
                "duration_minutes": None
            },
            "expected": None
        },
    ]

    for tc in test_cases:
        result = calculate_reward(tc["input"])
        if result == tc["expected"]:
            log_test(f"보상계산: {tc['name']}", "PASS", f"결과: {result}")
        else:
            log_test(f"보상계산: {tc['name']}", "FAIL", f"예상: {tc['expected']}, 실제: {result}")

    # 보상 표시 테스트
    print("\n  [보상 표시 테스트]")

    reward_codes = ["premium_14days", "premium_7days", "premium_3days", "premium_1day", "invalid"]
    for code in reward_codes:
        display = get_reward_display(code)
        if "label" in display and "days" in display:
            log_test(f"보상표시: {code}", "PASS", f"라벨: {display['label']}, 일수: {display['days']}")
        else:
            log_test(f"보상표시: {code}", "WARN", f"결과: {display}")

    # 사용자 해시 생성 테스트
    print("\n  [사용자 해시 테스트]")
    hash1 = generate_user_hash("session_12345")
    hash2 = generate_user_hash("session_12345")
    hash3 = generate_user_hash("session_67890")

    if hash1 == hash2:
        log_test("해시: 동일 세션 → 동일 해시", "PASS", f"해시: {hash1}")
    else:
        log_test("해시: 동일 세션 → 동일 해시", "FAIL", f"해시1: {hash1}, 해시2: {hash2}")

    if hash1 != hash3:
        log_test("해시: 다른 세션 → 다른 해시", "PASS")
    else:
        log_test("해시: 다른 세션 → 다른 해시", "FAIL", "해시가 동일함")

    # 항공사별 제보 수 조회 테스트
    print("\n  [항공사별 제보 수 테스트]")
    from config import AIRLINES
    for airline in AIRLINES[:3]:  # 처음 3개만 테스트
        count = get_airline_report_count(airline)
        log_test(f"제보수: {airline}", "PASS", f"{count}건")

    # 질문 통계 테스트
    print("\n  [질문 통계 테스트]")
    stats = get_question_stats("대한항공", days=30)
    if "sufficient_data" in stats:
        if stats["sufficient_data"]:
            log_test("통계: 대한항공", "PASS", f"충분 - {stats['total_reports']}건")
        else:
            log_test("통계: 대한항공", "WARN", f"부족 - {stats.get('needed', '?')}건 더 필요")
    else:
        log_test("통계: 대한항공", "FAIL", "결과 형식 오류")


# ═══════════════════════════════════════════
# 테스트 4: 데이터 흐름 검증
# ═══════════════════════════════════════════

def test_data_flow():
    print("\n" + "="*60)
    print("  [4/5] 데이터 흐름 검증")
    print("="*60)

    # 데이터 디렉토리 존재 확인
    data_dir = ROOT / "data" / "interview_reports"
    if data_dir.exists():
        log_test("디렉토리: data/interview_reports", "PASS")
    else:
        log_test("디렉토리: data/interview_reports", "WARN", "디렉토리 없음 (첫 제보 시 생성됨)")

    # 뉴스 데이터 파일 확인
    news_file = ROOT / "data" / "airline_news.json"
    if news_file.exists():
        try:
            with open(news_file, "r", encoding="utf-8") as f:
                news_data = json.load(f)

            if "news" in news_data:
                total_news = sum(len(v) for v in news_data["news"].values())
                airlines_with_news = list(news_data["news"].keys())
                log_test("뉴스 데이터: airline_news.json", "PASS",
                        f"총 {total_news}건, 항공사: {len(airlines_with_news)}개")
            else:
                log_test("뉴스 데이터: airline_news.json", "WARN", "news 키 없음")
        except json.JSONDecodeError as e:
            log_test("뉴스 데이터: airline_news.json", "FAIL", f"JSON 파싱 오류: {e}")
    else:
        log_test("뉴스 데이터: airline_news.json", "WARN", "파일 없음")

    # 제보 데이터 파일 확인
    reports_file = ROOT / "data" / "interview_reports" / "reports.json"
    if reports_file.exists():
        try:
            with open(reports_file, "r", encoding="utf-8") as f:
                reports = json.load(f)
            log_test("제보 데이터: reports.json", "PASS", f"{len(reports)}건 저장됨")
        except:
            log_test("제보 데이터: reports.json", "WARN", "파일 읽기 오류")
    else:
        log_test("제보 데이터: reports.json", "PASS", "아직 제보 없음 (정상)")


# ═══════════════════════════════════════════
# 테스트 5: 핵심 원칙 준수 확인
# ═══════════════════════════════════════════

def test_core_principles():
    print("\n" + "="*60)
    print("  [5/5] 핵심 원칙 준수 확인")
    print("="*60)

    print("\n  [원칙: AI 창작 금지]")

    # 예측 페이지 코드 검사 - 데이터 부족 시 AI 생성 금지
    prediction_file = ROOT / "pages" / "41_면접예측.py"
    with open(prediction_file, "r", encoding="utf-8") as f:
        code = f.read()

    # 데이터 부족 처리 확인
    if "sufficient_data" in code and "데이터 부족" in code:
        log_test("원칙: 데이터 부족 시 AI 생성 금지", "PASS", "데이터 부족 처리 로직 있음")
    else:
        log_test("원칙: 데이터 부족 시 AI 생성 금지", "WARN", "데이터 부족 처리 확인 필요")

    # 출처 명시 확인 (N건 중 M건)
    if "건 중" in code or "total_reports" in code:
        log_test("원칙: 출처 명시 (N건 중 M건)", "PASS", "출처 표시 로직 있음")
    else:
        log_test("원칙: 출처 명시 (N건 중 M건)", "WARN", "출처 표시 확인 필요")

    print("\n  [원칙: 억지 매칭 금지]")

    # 뉴스 연계 페이지 코드 검사
    news_file = ROOT / "pages" / "42_자소서뉴스연계.py"
    with open(news_file, "r", encoding="utf-8") as f:
        code = f.read()

    # 매칭 실패 시 None 반환 확인
    if "return None" in code and "관련 뉴스 없음" in code:
        log_test("원칙: 매칭 실패 시 억지 매칭 금지", "PASS", "None 반환 로직 있음")
    else:
        log_test("원칙: 매칭 실패 시 억지 매칭 금지", "WARN", "억지 매칭 방지 확인 필요")

    # 최소 2개 키워드 매칭 확인
    if ">= 2" in code or "match_count >= 2" in code:
        log_test("원칙: 최소 2개 키워드 매칭", "PASS", "최소 2개 매칭 로직 있음")
    else:
        log_test("원칙: 최소 2개 키워드 매칭", "WARN", "매칭 기준 확인 필요")

    print("\n  [원칙: 중복 제보 방지]")

    # 제보 시스템 코드 검사
    report_file = ROOT / "interview_report_system.py"
    with open(report_file, "r", encoding="utf-8") as f:
        code = f.read()

    # 중복 확인 로직 존재
    if "check_duplicate_submission" in code and "24" in code:
        log_test("원칙: 24시간 내 중복 제보 방지", "PASS", "중복 확인 로직 있음")
    else:
        log_test("원칙: 24시간 내 중복 제보 방지", "WARN", "중복 방지 확인 필요")

    # 유사 질문 경고
    if "check_similar_questions" in code:
        log_test("원칙: 유사 질문 경고", "PASS", "유사도 체크 로직 있음")
    else:
        log_test("원칙: 유사 질문 경고", "WARN", "유사도 체크 확인 필요")


# ═══════════════════════════════════════════
# 메인 실행
# ═══════════════════════════════════════════

def run_all_tests():
    print("\n" + "#"*60)
    print("  FLYREADY 신규 기능 테스트 봇 v1.0")
    print("  대상: 면접제보, 면접예측, 자소서뉴스연계")
    print(f"  시작: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#"*60)

    # 테스트 실행
    test_syntax()
    test_imports()
    test_functions()
    test_data_flow()
    test_core_principles()

    # 최종 요약
    print("\n" + "#"*60)
    print("  최종 요약")
    print("#"*60)

    summary = results.summary()
    print(f"\n  총 테스트: {summary['total']}개")
    print(f"  통과: {summary['passed']}개")
    print(f"  실패: {summary['failed']}개")
    print(f"  경고: {summary['warnings']}개")
    print(f"  통과율: {summary['pass_rate']}")

    # 실패 항목 출력
    if summary['failed'] > 0:
        print("\n  [실패 항목]")
        for t in results.tests:
            if t["status"] == "FAIL":
                print(f"    - {t['name']}: {t['message']}")

    # 경고 항목 출력
    if summary['warnings'] > 0:
        print("\n  [경고 항목]")
        for t in results.tests:
            if t["status"] == "WARN":
                print(f"    - {t['name']}: {t['message']}")

    # 결과 저장
    output_path = ROOT / "tests" / f"new_features_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "tests": results.tests
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  리포트 저장: {output_path}")

    return summary


if __name__ == "__main__":
    run_all_tests()
