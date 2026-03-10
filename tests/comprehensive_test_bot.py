"""
FLYREADY 종합 테스트 봇 v2.0
- 오늘 수정된 모든 기능 테스트
- 어색함 감지 강화
- 오류 탐지 강화
- 코드 품질 검사

테스트 영역:
1. 구문/Import 오류 검사
2. 오늘 수정된 기능 테스트 (면접관 유형, STAR, 꼬리질문, 점수 로직 등)
3. 어색함 감지 (질문/피드백 품질)
4. 런타임 시뮬레이션
5. 데이터 흐름 검증
"""

import os
import sys
import json
import time
import datetime
import traceback
import re
from typing import Dict, List, Any, Tuple
from pathlib import Path

# Windows 콘솔 UTF-8 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ai_tutor 루트를 path에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import requests

# ═══════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════

API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-4o-mini"


class TestResult:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add(self, category: str, name: str, status: str, message: str = "", details: str = ""):
        self.tests.append({
            "category": category,
            "name": name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.datetime.now().isoformat()
        })
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1

        icon = {"PASS": "[OK]", "FAIL": "[XX]", "WARN": "[!!]"}.get(status, "[??]")
        print(f"  {icon} {name}")
        if message:
            print(f"         {message}")

    def summary(self) -> Dict:
        return {
            "total": len(self.tests),
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "pass_rate": f"{self.passed/len(self.tests)*100:.1f}%" if self.tests else "0%"
        }


results = TestResult()


# ═══════════════════════════════════════════
# 1. 구문 및 Import 오류 검사
# ═══════════════════════════════════════════

def test_syntax_errors():
    """모든 주요 Python 파일 구문 검사"""
    print("\n" + "="*60)
    print("  [1] 구문 및 Import 오류 검사")
    print("="*60)

    # 검사할 파일 목록
    critical_files = [
        ROOT / "pages" / "4_모의면접.py",
        ROOT / "interview_enhancer.py",
        ROOT / "airline_questions.py",
        ROOT / "content_enhancer.py",
        ROOT / "realism_enhancer.py",
        ROOT / "config.py",
        ROOT / "sidebar_common.py",
    ]

    # 모든 pages 폴더 파일도 검사
    pages_dir = ROOT / "pages"
    if pages_dir.exists():
        for f in pages_dir.glob("*.py"):
            if f not in critical_files:
                critical_files.append(f)

    for file_path in critical_files:
        if not file_path.exists():
            results.add("구문검사", file_path.name, "WARN", "파일 없음")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            compile(code, file_path.name, "exec")
            results.add("구문검사", file_path.name, "PASS")
        except SyntaxError as e:
            results.add("구문검사", file_path.name, "FAIL",
                       f"Line {e.lineno}: {e.msg}",
                       f"문제 코드: {e.text.strip() if e.text else '?'}")
        except Exception as e:
            results.add("구문검사", file_path.name, "FAIL", str(e))


def test_imports():
    """핵심 모듈 Import 테스트"""
    print("\n" + "="*60)
    print("  [2] 모듈 Import 검사")
    print("="*60)

    import_tests = [
        ("interview_enhancer", ["InterviewerType", "get_interviewer_character", "analyze_interview_answer", "FollowUpQuestionGenerator", "KeywordAnalyzer"]),
        ("airline_questions", ["get_airline_questions", "AIRLINE_VALUES", "COMMON_QUESTIONS"]),
        ("config", ["AIRLINES", "AIRLINE_TYPE"]),
    ]

    for module_name, items in import_tests:
        try:
            module = __import__(module_name)
            missing = [item for item in items if not hasattr(module, item)]
            if missing:
                results.add("Import", module_name, "WARN", f"누락: {', '.join(missing)}")
            else:
                results.add("Import", module_name, "PASS", f"{len(items)}개 항목 확인")
        except Exception as e:
            results.add("Import", module_name, "FAIL", str(e))


# ═══════════════════════════════════════════
# 2. 오늘 수정된 기능 테스트
# ═══════════════════════════════════════════

def test_today_modifications():
    """오늘 수정된 기능들 테스트"""
    print("\n" + "="*60)
    print("  [3] 오늘 수정된 기능 테스트")
    print("="*60)

    # 2-1. 면접관 유형 이름 변경 테스트
    print("\n  [면접관 유형]")
    try:
        from interview_enhancer import InterviewerType, get_interviewer_character, INTERVIEWER_CHARACTERS

        # 정석형, 분석형 확인
        neutral = get_interviewer_character("neutral")
        sharp = get_interviewer_character("sharp")

        if "정석형" in neutral.name or "정석" in str(INTERVIEWER_CHARACTERS.get(InterviewerType.NEUTRAL, {})):
            results.add("수정확인", "면접관 유형: 정석형", "PASS", f"이름: {neutral.name}")
        else:
            results.add("수정확인", "면접관 유형: 정석형", "FAIL", f"현재: {neutral.name}")

        if "분석형" in sharp.name or "분석" in str(INTERVIEWER_CHARACTERS.get(InterviewerType.SHARP, {})):
            results.add("수정확인", "면접관 유형: 분석형", "PASS", f"이름: {sharp.name}")
        else:
            results.add("수정확인", "면접관 유형: 분석형", "FAIL", f"현재: {sharp.name}")

    except Exception as e:
        results.add("수정확인", "면접관 유형", "FAIL", str(e))

    # 2-2. STAR 비중 질문별 적용 테스트
    print("\n  [STAR 비중]")
    try:
        from interview_enhancer import KeywordAnalyzer

        analyzer = KeywordAnalyzer()

        # 질문 유형별 STAR 가중치 확인
        if hasattr(analyzer, 'STAR_WEIGHTS_BY_TYPE'):
            weights = analyzer.STAR_WEIGHTS_BY_TYPE
            if "경험" in weights and "지원동기" in weights:
                exp_weights = weights["경험"]
                if exp_weights.get("action", 0) >= 40:  # 경험은 Action이 높아야 함
                    results.add("수정확인", "STAR 비중: 경험형", "PASS",
                               f"A={exp_weights.get('action')}%")
                else:
                    results.add("수정확인", "STAR 비중: 경험형", "FAIL",
                               f"Action 비중 낮음: {exp_weights.get('action')}%")
            else:
                results.add("수정확인", "STAR 비중: 유형별", "FAIL", "경험/지원동기 유형 없음")
        else:
            results.add("수정확인", "STAR 비중", "FAIL", "STAR_WEIGHTS_BY_TYPE 속성 없음")

        # _detect_question_type 메서드 확인
        if hasattr(analyzer, '_detect_question_type'):
            q_type = analyzer._detect_question_type("팀워크를 발휘한 경험을 말씀해주세요")
            if q_type in ["경험", "팀워크"]:
                results.add("수정확인", "STAR 질문유형 감지", "PASS", f"감지: {q_type}")
            else:
                results.add("수정확인", "STAR 질문유형 감지", "WARN", f"감지: {q_type}")
        else:
            results.add("수정확인", "STAR 질문유형 감지", "FAIL", "_detect_question_type 없음")

    except Exception as e:
        results.add("수정확인", "STAR 비중", "FAIL", str(e))

    # 2-3. 꼬리질문 강화 테스트
    print("\n  [꼬리질문]")
    try:
        from interview_enhancer import FollowUpQuestionGenerator, get_interviewer_character

        generator = FollowUpQuestionGenerator()

        # 다양한 질문 유형에 대한 꼬리질문 생성 테스트
        test_cases = [
            ("갈등을 해결한 경험이 있나요?", "팀원과 의견이 다를 때 대화로 해결했습니다."),
            ("지원동기를 말씀해주세요", "승무원이 되고 싶어서 지원했습니다."),
            ("팀워크 경험을 말씀해주세요", "팀에서 협력한 적이 있습니다."),
        ]

        for question, answer in test_cases:
            follow_up = generator._generate_fallback_follow_up(question, answer)
            if follow_up and "follow_up_question" in follow_up:
                fq = follow_up["follow_up_question"]
                # 질문이 관련성이 있는지 확인
                if len(fq) > 10 and "?" in fq or "요?" in fq or "까?" in fq:
                    results.add("수정확인", f"꼬리질문: {question[:15]}...", "PASS", fq[:40])
                else:
                    results.add("수정확인", f"꼬리질문: {question[:15]}...", "WARN", f"형식 이상: {fq[:40]}")
            else:
                results.add("수정확인", f"꼬리질문: {question[:15]}...", "FAIL", "생성 실패")

    except Exception as e:
        results.add("수정확인", "꼬리질문", "FAIL", str(e))

    # 2-4. 점수 로직 테스트 (패스 시 0점 반영)
    print("\n  [점수 로직]")
    try:
        # 모의면접 파일에서 패스 로직 확인
        mock_file = ROOT / "pages" / "4_모의면접.py"
        with open(mock_file, "r", encoding="utf-8") as f:
            code = f.read()

        # 패스 시 0점 + skipped 플래그 확인
        if '"skipped": True' in code and '"total_score": 0' in code:
            results.add("수정확인", "점수: 패스 시 0점+skipped", "PASS")
        else:
            results.add("수정확인", "점수: 패스 시 0점+skipped", "FAIL", "skipped 플래그 없음")

        # 평균 계산에서 0점 포함 확인 (기존: valid_scores = [s for s > 0] 제거)
        if "valid_scores = [s for s in keyword_scores if s > 0]" in code:
            results.add("수정확인", "점수: 0점 평균 제외", "FAIL", "0점이 평균에서 제외되고 있음")
        else:
            results.add("수정확인", "점수: 0점 평균 포함", "PASS", "패스도 평균에 반영")

    except Exception as e:
        results.add("수정확인", "점수 로직", "FAIL", str(e))

    # 2-5. 텍스트 모드 타이머 제거 확인
    print("\n  [타이머 제거]")
    try:
        mock_file = ROOT / "pages" / "4_모의면접.py"
        with open(mock_file, "r", encoding="utf-8") as f:
            code = f.read()

        # 텍스트 모드에서 타이머 HTML이 없어야 함
        # 음성 모드에는 있어도 됨
        text_mode_section = code[code.find("# 텍스트 입력 모드"):code.find("# 패스 버튼") if "# 패스 버튼" in code else -1]

        if "timer_html" in text_mode_section or '<div id="timer"' in text_mode_section:
            results.add("수정확인", "텍스트모드: 타이머 제거", "FAIL", "타이머 HTML 존재")
        else:
            results.add("수정확인", "텍스트모드: 타이머 제거", "PASS")

        if "답변 시작" in text_mode_section and 'st.button("답변 시작"' in text_mode_section:
            results.add("수정확인", "텍스트모드: 시작버튼 제거", "FAIL", "시작 버튼 존재")
        else:
            results.add("수정확인", "텍스트모드: 시작버튼 제거", "PASS")

    except Exception as e:
        results.add("수정확인", "타이머 제거", "FAIL", str(e))

    # 2-6. 질문 말투 자연스러움 확인
    print("\n  [질문 말투]")
    try:
        from airline_questions import AIRLINE_SPECIFIC_QUESTIONS, COMMON_QUESTIONS

        # "~것은?" 으로 끝나는 질문이 없어야 함 (자연스러운 말투로 수정됨)
        unnatural_endings = ["것은?", "점은?", "이유는?"]
        natural_endings = ["무엇인가요?", "있나요?", "입니까?", "습니까?"]

        unnatural_count = 0
        natural_count = 0

        # 일부 질문 샘플링
        sample_questions = []
        for airline, qs in AIRLINE_SPECIFIC_QUESTIONS.items():
            for cat, questions in qs.items():
                if isinstance(questions, list):
                    sample_questions.extend(questions[:3])

        for cat, questions in COMMON_QUESTIONS.items():
            if isinstance(questions, list):
                sample_questions.extend(questions[:3])

        for q in sample_questions[:50]:
            if any(q.endswith(end) for end in unnatural_endings):
                unnatural_count += 1
            if any(end in q for end in natural_endings):
                natural_count += 1

        if unnatural_count == 0:
            results.add("수정확인", "질문 말투: 자연스러움", "PASS", f"자연스러운 종결어 {natural_count}개")
        else:
            results.add("수정확인", "질문 말투: 자연스러움", "WARN", f"부자연스러운 종결어 {unnatural_count}개 발견")

    except Exception as e:
        results.add("수정확인", "질문 말투", "FAIL", str(e))

    # 2-7. 압박/트렌드/리얼 질문 추가 확인
    print("\n  [신규 질문]")
    try:
        from airline_questions import COMMON_QUESTIONS

        new_categories = ["pressure", "trend_2025", "real_interview"]
        for cat in new_categories:
            if cat in COMMON_QUESTIONS:
                count = len(COMMON_QUESTIONS[cat])
                results.add("수정확인", f"신규질문: {cat}", "PASS", f"{count}개 질문")
            else:
                results.add("수정확인", f"신규질문: {cat}", "FAIL", "카테고리 없음")

    except Exception as e:
        results.add("수정확인", "신규 질문", "FAIL", str(e))


# ═══════════════════════════════════════════
# 3. 어색함 감지 (AI 기반)
# ═══════════════════════════════════════════

def call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    if not API_KEY:
        return "[API KEY 없음]"
    try:
        r = requests.post(API_URL, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }, json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 2000
        }, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[API ERROR] {e}"


def test_awkwardness():
    """어색함 감지 테스트"""
    print("\n" + "="*60)
    print("  [4] 어색함 감지 (AI 분석)")
    print("="*60)

    if not API_KEY:
        results.add("어색함", "API 키 없음", "WARN", "AI 분석 스킵")
        return

    # 테스트용 시뮬레이션 데이터
    test_scenarios = [
        {
            "name": "짧은 답변 테스트",
            "question": "팀워크를 발휘한 경험을 말씀해주세요.",
            "answer": "네, 있습니다.",
            "expected_issue": "답변이 너무 짧음"
        },
        {
            "name": "추측성 답변 테스트",
            "question": "왜 대한항공에 지원하셨나요?",
            "answer": "글로벌 항공사라서 좋은 것 같습니다. 아마 제가 잘 맞을 것 같습니다. 대체로 좋은 회사라고 생각합니다.",
            "expected_issue": "추측성 표현 과다"
        },
        {
            "name": "구체성 부족 테스트",
            "question": "갈등 상황을 해결한 경험이 있나요?",
            "answer": "팀에서 갈등이 있었는데 대화로 해결했습니다. 서로 이해하게 되었습니다.",
            "expected_issue": "구체적 상황/행동/결과 부족"
        },
    ]

    system_prompt = """너는 항공사 면접 답변 품질 분석가다.
답변을 분석하고 어색하거나 문제가 있는 부분을 찾아라.

분석 항목:
1. 답변 길이 (너무 짧으면 지적)
2. 구체성 (STAR 구조 확인)
3. 추측성 표현 ("~것 같습니다", "아마" 등)
4. 결과/성과 언급 여부
5. 질문과의 관련성

JSON 형식으로 응답:
{
  "issues": ["발견된 문제점 1", "발견된 문제점 2"],
  "severity": "high/medium/low",
  "suggestion": "개선 제안"
}"""

    for scenario in test_scenarios:
        user_prompt = f"""질문: {scenario['question']}
답변: {scenario['answer']}

이 답변의 문제점을 분석하라."""

        response = call_llm(system_prompt, user_prompt)

        if "[API ERROR]" in response:
            results.add("어색함", scenario["name"], "WARN", "API 오류")
        else:
            try:
                # JSON 파싱 시도
                if "{" in response and "}" in response:
                    json_str = response[response.find("{"):response.rfind("}")+1]
                    analysis = json.loads(json_str)
                    issues = analysis.get("issues", [])
                    severity = analysis.get("severity", "unknown")

                    if issues:
                        results.add("어색함", scenario["name"], "PASS",
                                   f"발견: {len(issues)}개 문제, 심각도: {severity}",
                                   ", ".join(issues[:2]))
                    else:
                        results.add("어색함", scenario["name"], "WARN", "문제점 미발견")
                else:
                    results.add("어색함", scenario["name"], "WARN", f"응답: {response[:50]}")
            except json.JSONDecodeError:
                results.add("어색함", scenario["name"], "WARN", f"JSON 파싱 실패: {response[:50]}")


# ═══════════════════════════════════════════
# 4. 런타임 시뮬레이션
# ═══════════════════════════════════════════

def test_runtime_simulation():
    """핵심 함수 런타임 테스트"""
    print("\n" + "="*60)
    print("  [5] 런타임 시뮬레이션")
    print("="*60)

    # 5-1. 질문 생성 테스트
    print("\n  [질문 생성]")
    try:
        from airline_questions import get_airline_questions

        airlines = ["대한항공", "아시아나항공", "제주항공", "진에어"]
        for airline in airlines:
            questions = get_airline_questions(airline, count=6)
            if questions and len(questions) >= 4:
                results.add("런타임", f"질문생성: {airline}", "PASS", f"{len(questions)}개 생성")
            else:
                results.add("런타임", f"질문생성: {airline}", "FAIL", f"부족: {len(questions)}개")
    except Exception as e:
        results.add("런타임", "질문 생성", "FAIL", str(e))

    # 5-2. 키워드 분석 테스트
    print("\n  [키워드 분석]")
    try:
        from interview_enhancer import KeywordAnalyzer

        analyzer = KeywordAnalyzer()
        test_answer = "저는 대학교 동아리에서 팀장을 맡아 30명 규모의 행사를 기획했습니다. 팀원들과 협력하여 문제를 해결했고, 결과적으로 참석률이 40% 증가했습니다."
        test_question = "팀워크 경험을 말씀해주세요."

        result = analyzer.analyze_keywords(test_answer, test_question, "대한항공")

        if "star_structure" in result and "keyword_score" in result:
            star = result["star_structure"]
            score = result["keyword_score"]
            results.add("런타임", "키워드분석", "PASS",
                       f"점수: {score}, STAR: {star.get('complete_count', 0)}/4")
        else:
            results.add("런타임", "키워드분석", "FAIL", "결과 형식 오류")
    except Exception as e:
        results.add("런타임", "키워드 분석", "FAIL", str(e))

    # 5-3. 꼬리질문 생성 테스트
    print("\n  [꼬리질문 생성]")
    try:
        from interview_enhancer import FollowUpQuestionGenerator, get_interviewer_character

        generator = FollowUpQuestionGenerator()
        interviewer = get_interviewer_character("sharp")

        # should_ask_follow_up 테스트
        should_ask, reason = generator.should_ask_follow_up(
            answer="네.",
            answer_score=30,
            interviewer=interviewer
        )

        if should_ask:
            results.add("런타임", "꼬리질문 결정: 짧은답변", "PASS", f"사유: {reason}")
        else:
            results.add("런타임", "꼬리질문 결정: 짧은답변", "WARN", "꼬리질문 안 함")

    except Exception as e:
        results.add("런타임", "꼬리질문 생성", "FAIL", str(e))


# ═══════════════════════════════════════════
# 5. 데이터 흐름 검증
# ═══════════════════════════════════════════

def test_data_flow():
    """데이터 파일 및 설정 검증"""
    print("\n" + "="*60)
    print("  [6] 데이터 흐름 검증")
    print("="*60)

    # 필수 데이터 파일 확인
    required_files = [
        ROOT / "config.py",
        ROOT / ".env",
    ]

    for f in required_files:
        if f.exists():
            results.add("데이터", f.name, "PASS")
        else:
            results.add("데이터", f.name, "FAIL", "파일 없음")

    # 항공사 설정 확인
    try:
        from config import AIRLINES, AIRLINE_TYPE, AIRLINE_VALUES

        if len(AIRLINES) >= 10:
            results.add("데이터", "항공사 목록", "PASS", f"{len(AIRLINES)}개")
        else:
            results.add("데이터", "항공사 목록", "WARN", f"{len(AIRLINES)}개 (부족)")

    except Exception as e:
        results.add("데이터", "항공사 설정", "FAIL", str(e))


# ═══════════════════════════════════════════
# 메인 실행
# ═══════════════════════════════════════════

def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "#"*60)
    print("  FLYREADY 종합 테스트 봇 v2.0")
    print(f"  시작: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("#"*60)

    start_time = time.time()

    # 테스트 실행
    test_syntax_errors()
    test_imports()
    test_today_modifications()
    test_awkwardness()
    test_runtime_simulation()
    test_data_flow()

    elapsed = time.time() - start_time

    # 최종 요약
    print("\n" + "#"*60)
    print("  최종 요약")
    print("#"*60)

    summary = results.summary()
    print(f"\n  총 테스트: {summary['total']}개")
    print(f"  [OK] 통과: {summary['passed']}개")
    print(f"  [XX] 실패: {summary['failed']}개")
    print(f"  [!!] 경고: {summary['warnings']}개")
    print(f"  통과율: {summary['pass_rate']}")
    print(f"  소요시간: {elapsed:.1f}초")

    # 실패 항목 출력
    if summary['failed'] > 0:
        print("\n  [실패 항목]")
        for t in results.tests:
            if t["status"] == "FAIL":
                print(f"    [XX] [{t['category']}] {t['name']}")
                if t["message"]:
                    print(f"         -> {t['message']}")

    # 경고 항목 출력
    if summary['warnings'] > 0:
        print("\n  [경고 항목]")
        for t in results.tests:
            if t["status"] == "WARN":
                print(f"    [!!] [{t['category']}] {t['name']}: {t['message']}")

    # 결과 저장
    output_path = ROOT / "tests" / f"comprehensive_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "elapsed_seconds": elapsed,
            "tests": results.tests
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  리포트 저장: {output_path}")

    return summary


if __name__ == "__main__":
    run_all_tests()
