# e2e_test_bot.py
# FlyReady Lab E2E 테스트 봇 v2.0 (고도화)
# 사용법: python e2e_test_bot.py [--full] [--quick]
# --full: 모든 페이지 + 모든 요소 상호작용 테스트
# --quick: 핵심 페이지만 빠르게 체크

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Windows 콘솔 UTF-8 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright가 설치되지 않았습니다.")
    print("설치: pip install playwright && playwright install chromium")
    exit(1)


class FlyReadyTestBot:
    """FlyReady Lab E2E 테스트 봇 v2.0"""

    def __init__(self, base_url: str = "http://localhost:8501", full_mode: bool = False):
        self.base_url = base_url
        self.full_mode = full_mode
        self.results = []
        self.interaction_results = []
        self.screenshots_dir = Path("test_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

        # 테스트할 페이지 목록 (우선순위별)
        self.pages_to_test = [
            # A등급: 핵심 페이지 (상호작용 테스트 필수)
            {"name": "홈", "path": "/", "checks": ["FlyReady"], "priority": "A", "interactions": ["sidebar"]},
            {"name": "모의면접", "path": "/모의면접", "checks": ["면접"], "priority": "A", "interactions": ["selectbox", "radio", "button"]},
            {"name": "롤플레잉", "path": "/롤플레잉", "checks": [], "priority": "A", "interactions": ["selectbox", "button"]},
            {"name": "영어면접", "path": "/영어면접", "checks": [], "priority": "A", "interactions": ["selectbox", "button"]},

            # B등급: 주요 페이지
            {"name": "시작하기", "path": "/시작하기", "checks": [], "priority": "B", "interactions": ["button"]},
            {"name": "토론면접", "path": "/토론면접", "checks": [], "priority": "B", "interactions": ["selectbox"]},
            {"name": "진도관리", "path": "/진도관리", "checks": [], "priority": "B", "interactions": []},
            {"name": "성장그래프", "path": "/성장그래프", "checks": [], "priority": "B", "interactions": []},
            {"name": "합격자DB", "path": "/합격자DB", "checks": [], "priority": "B", "interactions": ["selectbox"]},
            {"name": "면접꿀팁", "path": "/면접꿀팁", "checks": [], "priority": "B", "interactions": ["expander"]},
            {"name": "채용알림", "path": "/채용알림", "checks": [], "priority": "B", "interactions": []},
            {"name": "항공사가이드", "path": "/항공사가이드", "checks": [], "priority": "B", "interactions": ["selectbox", "tab"]},
            {"name": "표정연습", "path": "/표정연습", "checks": [], "priority": "B", "interactions": ["button"]},
            {"name": "항공사퀴즈", "path": "/항공사퀴즈", "checks": [], "priority": "B", "interactions": ["radio", "button"]},

            # C등급: 보조 페이지
            {"name": "기업분석", "path": "/기업분석", "checks": [], "priority": "C", "interactions": ["selectbox"]},
            {"name": "자소서작성", "path": "/자소서작성", "checks": [], "priority": "C", "interactions": ["text_area", "button"]},
            {"name": "자소서첨삭", "path": "/자소서첨삭", "checks": [], "priority": "C", "interactions": ["text_area"]},
            {"name": "자소서기반질문", "path": "/자소서기반질문", "checks": [], "priority": "C", "interactions": []},
            {"name": "기내방송연습", "path": "/기내방송연습", "checks": [], "priority": "C", "interactions": ["selectbox"]},
            {"name": "D-Day캘린더", "path": "/D-Day캘린더", "checks": [], "priority": "C", "interactions": []},
            {"name": "요금제", "path": "/요금제", "checks": ["FREE", "STANDARD", "PREMIUM"], "priority": "C", "interactions": []},
            {"name": "그룹면접", "path": "/그룹면접", "checks": [], "priority": "C", "interactions": []},
        ]

        # 오늘 수정된 항목 체크리스트 (2025-02-06)
        self.today_checks = {
            "모의면접": [
                {"type": "text", "value": "정석형", "desc": "면접관 유형 라벨 변경"},
                {"type": "text", "value": "분석형", "desc": "면접관 유형 라벨 변경"},
                {"type": "no_text", "value": "남은 시간", "desc": "텍스트 모드 타이머 제거"},
            ]
        }

    async def run_all_tests(self, quick_mode: bool = False):
        """모든 테스트 실행"""
        mode_text = "빠른 검증" if quick_mode else ("전체 상호작용" if self.full_mode else "기본")
        print("=" * 60)
        print(f"FlyReady Lab E2E 테스트 v2.0 [{mode_text} 모드]")
        print(f"대상: {self.base_url}")
        print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # quick 모드: A등급만
        if quick_mode:
            pages = [p for p in self.pages_to_test if p.get("priority") == "A"]
        else:
            pages = self.pages_to_test

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                locale="ko-KR"
            )

            # 콘솔 에러 수집
            page = await context.new_page()
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            # 사이드바 탐색 먼저
            print("\n[STEP 1] 사이드바 탐색 테스트")
            sidebar_result = await self.test_sidebar_navigation(page)
            self.results.append(sidebar_result)

            # 각 페이지 테스트
            print(f"\n[STEP 2] 페이지별 테스트 ({len(pages)}개)")
            for page_info in pages:
                result = await self.test_page(page, page_info, console_errors)
                self.results.append(result)

                # full 모드: 상호작용 테스트
                if self.full_mode and page_info.get("interactions"):
                    interaction_result = await self.test_page_interactions(page, page_info)
                    self.interaction_results.append(interaction_result)

                console_errors.clear()

            # 오늘 수정사항 체크
            print(f"\n[STEP 3] 오늘 수정사항 확인")
            today_result = await self.test_today_modifications(page)
            self.results.append(today_result)

            await browser.close()

        self.generate_report()

    async def test_sidebar_navigation(self, page) -> dict:
        """사이드바 모든 메뉴 클릭 테스트"""
        result = {
            "name": "사이드바 탐색",
            "path": "/",
            "status": "unknown",
            "errors": [],
            "warnings": [],
            "details": []
        }

        try:
            await page.goto(f"{self.base_url}/", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            # 사이드바 메뉴 찾기
            sidebar = await page.query_selector('[data-testid="stSidebar"]')
            if not sidebar:
                result["warnings"].append("사이드바를 찾을 수 없음")
                result["status"] = "warn"
                return result

            # 모든 링크/버튼 찾기
            links = await sidebar.query_selector_all('a, [role="button"]')
            result["details"].append(f"사이드바 요소: {len(links)}개")

            clicked = 0
            for link in links[:15]:  # 최대 15개만
                try:
                    text = await link.inner_text()
                    if text and len(text) < 30:
                        await link.click()
                        await page.wait_for_timeout(1000)
                        clicked += 1
                except:
                    pass

            result["details"].append(f"클릭 성공: {clicked}개")
            result["status"] = "pass" if clicked > 5 else "warn"

            print(f"  [OK] 사이드바: {clicked}개 메뉴 탐색 완료")

        except Exception as e:
            result["errors"].append(f"사이드바 테스트 오류: {str(e)[:100]}")
            result["status"] = "fail"
            print(f"  [XX] 사이드바: {str(e)[:50]}")

        return result

    async def test_page_interactions(self, page, page_info: dict) -> dict:
        """페이지 내 모든 상호작용 요소 테스트"""
        name = page_info["name"]
        interactions = page_info.get("interactions", [])

        result = {
            "name": f"{name} 상호작용",
            "interactions_tested": [],
            "errors": [],
            "status": "unknown"
        }

        try:
            # selectbox 테스트
            if "selectbox" in interactions:
                selects = await page.query_selector_all('[data-testid="stSelectbox"]')
                for i, select in enumerate(selects[:3]):  # 최대 3개
                    try:
                        await select.click()
                        await page.wait_for_timeout(500)
                        # 첫 번째 옵션 선택
                        options = await page.query_selector_all('[role="option"]')
                        if options:
                            await options[0].click()
                            await page.wait_for_timeout(500)
                            result["interactions_tested"].append(f"selectbox_{i+1}")
                    except:
                        pass

            # radio 버튼 테스트
            if "radio" in interactions:
                radios = await page.query_selector_all('[role="radio"]')
                for i, radio in enumerate(radios[:4]):  # 최대 4개
                    try:
                        await radio.click()
                        await page.wait_for_timeout(300)
                        result["interactions_tested"].append(f"radio_{i+1}")
                    except:
                        pass

            # button 테스트 (submit 버튼 제외)
            if "button" in interactions:
                buttons = await page.query_selector_all('button:not([type="submit"])')
                for i, btn in enumerate(buttons[:5]):  # 최대 5개
                    try:
                        text = await btn.inner_text()
                        if "시작" in text or "선택" in text:  # 안전한 버튼만
                            await btn.click()
                            await page.wait_for_timeout(500)
                            result["interactions_tested"].append(f"button: {text[:10]}")
                    except:
                        pass

            # expander 테스트
            if "expander" in interactions:
                expanders = await page.query_selector_all('[data-testid="stExpander"]')
                for i, exp in enumerate(expanders[:3]):
                    try:
                        await exp.click()
                        await page.wait_for_timeout(300)
                        result["interactions_tested"].append(f"expander_{i+1}")
                    except:
                        pass

            # tab 테스트
            if "tab" in interactions:
                tabs = await page.query_selector_all('[role="tab"]')
                for i, tab in enumerate(tabs[:4]):
                    try:
                        await tab.click()
                        await page.wait_for_timeout(300)
                        result["interactions_tested"].append(f"tab_{i+1}")
                    except:
                        pass

            result["status"] = "pass" if result["interactions_tested"] else "warn"
            print(f"    상호작용: {len(result['interactions_tested'])}개 테스트")

        except Exception as e:
            result["errors"].append(str(e)[:100])
            result["status"] = "fail"

        return result

    async def test_today_modifications(self, page) -> dict:
        """오늘 수정된 기능 확인"""
        result = {
            "name": "오늘 수정사항 확인",
            "checks": [],
            "errors": [],
            "status": "unknown"
        }

        try:
            # 모의면접 페이지 테스트
            await page.goto(f"{self.base_url}/모의면접", wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)

            content = await page.content()

            # 면접관 유형 라벨 확인
            if "정석형" in content:
                result["checks"].append({"item": "정석형 라벨", "status": "pass"})
            else:
                result["checks"].append({"item": "정석형 라벨", "status": "fail"})

            if "분석형" in content:
                result["checks"].append({"item": "분석형 라벨", "status": "pass"})
            else:
                result["checks"].append({"item": "분석형 라벨", "status": "fail"})

            # 텍스트 모드 진입 시 타이머 없음 확인
            # 항공사 선택
            selects = await page.query_selector_all('[data-testid="stSelectbox"]')
            if selects:
                await selects[0].click()
                await page.wait_for_timeout(500)
                options = await page.query_selector_all('[role="option"]')
                if options:
                    await options[0].click()
                    await page.wait_for_timeout(500)

            # 텍스트 모드 선택
            radios = await page.query_selector_all('[role="radio"]')
            for radio in radios:
                text = await radio.inner_text()
                if "텍스트" in text:
                    await radio.click()
                    await page.wait_for_timeout(500)
                    break

            # 시작 버튼 클릭
            buttons = await page.query_selector_all('button')
            for btn in buttons:
                text = await btn.inner_text()
                if "시작" in text:
                    await btn.click()
                    await page.wait_for_timeout(2000)
                    break

            # 타이머 텍스트 확인
            content_after = await page.content()
            if "남은 시간" not in content_after:
                result["checks"].append({"item": "타이머 제거 (텍스트)", "status": "pass"})
            else:
                result["checks"].append({"item": "타이머 제거 (텍스트)", "status": "fail"})

            # 결과 판정
            passed = sum(1 for c in result["checks"] if c["status"] == "pass")
            total = len(result["checks"])
            result["status"] = "pass" if passed == total else ("warn" if passed > 0 else "fail")

            print(f"  오늘 수정사항: {passed}/{total} 통과")
            for c in result["checks"]:
                icon = "[OK]" if c["status"] == "pass" else "[XX]"
                print(f"    {icon} {c['item']}")

        except Exception as e:
            result["errors"].append(str(e)[:100])
            result["status"] = "fail"
            print(f"  [XX] 오늘 수정사항 확인 실패: {str(e)[:50]}")

        return result

    async def test_page(self, page, page_info: dict, console_errors: list) -> dict:
        """개별 페이지 테스트 (고도화)"""
        name = page_info["name"]
        path = page_info["path"]
        checks = page_info.get("checks", [])
        priority = page_info.get("priority", "C")

        result = {
            "name": name,
            "path": path,
            "priority": priority,
            "status": "unknown",
            "load_time": 0,
            "errors": [],
            "warnings": [],
            "elements_found": {},
            "screenshot": None
        }

        print(f"\n[{priority}] {name} ({path})")

        try:
            start_time = datetime.now()

            # 페이지 로드
            response = await page.goto(
                f"{self.base_url}{path}",
                wait_until="networkidle",
                timeout=30000
            )

            load_time = (datetime.now() - start_time).total_seconds()
            result["load_time"] = round(load_time, 2)

            # HTTP 상태 확인
            if response and response.status >= 400:
                result["errors"].append(f"HTTP 에러: {response.status}")
                result["status"] = "fail"

            # Streamlit 로드 대기
            await page.wait_for_timeout(2000)

            # 페이지 요소 카운트 (실제 사람처럼 확인)
            try:
                buttons = await page.query_selector_all('button')
                selects = await page.query_selector_all('[data-testid="stSelectbox"]')
                radios = await page.query_selector_all('[role="radio"]')
                text_areas = await page.query_selector_all('textarea')
                expanders = await page.query_selector_all('[data-testid="stExpander"]')
                tabs = await page.query_selector_all('[role="tab"]')

                result["elements_found"] = {
                    "buttons": len(buttons),
                    "selectbox": len(selects),
                    "radio": len(radios),
                    "textarea": len(text_areas),
                    "expander": len(expanders),
                    "tabs": len(tabs),
                }
            except:
                pass

            # 텍스트 체크
            content = await page.content()
            for check_text in checks:
                if check_text not in content:
                    result["warnings"].append(f"'{check_text}' 텍스트 없음")

            # 콘솔 에러 확인
            if console_errors:
                for err in console_errors:
                    if "error" in err.lower() or "exception" in err.lower():
                        result["errors"].append(f"JS 에러: {err[:100]}")

            # Streamlit 에러 메시지 확인
            try:
                error_elements = await page.query_selector_all(".stException, .stError")
                for elem in error_elements:
                    text = await elem.inner_text()
                    result["errors"].append(f"Streamlit 에러: {text[:100]}")
            except:
                pass

            # 빈 페이지 체크
            try:
                body = await page.query_selector('body')
                body_text = await body.inner_text() if body else ""
                if len(body_text.strip()) < 50:
                    result["warnings"].append("페이지 콘텐츠가 거의 없음")
            except:
                pass

            # 스크린샷 저장
            screenshot_path = self.screenshots_dir / f"{name}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            result["screenshot"] = str(screenshot_path)

            # 최종 상태 결정
            if result["errors"]:
                result["status"] = "fail"
            elif result["warnings"]:
                result["status"] = "warn"
            else:
                result["status"] = "pass"

            status_icon = {"pass": "[OK]", "warn": "[!!]", "fail": "[XX]"}.get(result["status"], "[??]")
            elem_summary = f"btn:{result['elements_found'].get('buttons',0)}, sel:{result['elements_found'].get('selectbox',0)}, rad:{result['elements_found'].get('radio',0)}"
            print(f"  {status_icon} {result['status'].upper()} ({load_time}s) [{elem_summary}]")

        except PlaywrightTimeout:
            result["status"] = "fail"
            result["errors"].append("페이지 로드 타임아웃 (30초)")
            print(f"  [XX] TIMEOUT")

        except Exception as e:
            result["status"] = "fail"
            result["errors"].append(f"예외 발생: {str(e)}")
            print(f"  [XX] ERROR: {str(e)[:50]}")

        return result

    def generate_report(self):
        """테스트 결과 리포트 생성"""
        print("\n" + "=" * 60)
        print("테스트 결과 요약")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.get("status") == "pass")
        warned = sum(1 for r in self.results if r.get("status") == "warn")
        failed = sum(1 for r in self.results if r.get("status") == "fail")
        total = len(self.results)

        print(f"\n총 {total}개 항목 테스트")
        print(f"  [OK] 성공: {passed}")
        print(f"  [!!] 경고: {warned}")
        print(f"  [XX] 실패: {failed}")

        # 상호작용 테스트 결과
        if self.interaction_results:
            total_interactions = sum(len(r.get("interactions_tested", [])) for r in self.interaction_results)
            print(f"\n상호작용 테스트: {total_interactions}개 요소")

        # 실패/경고 상세
        if failed > 0 or warned > 0:
            print("\n문제 발견된 항목:")
            for r in self.results:
                if r.get("status") in ["fail", "warn"]:
                    path = r.get("path", "")
                    priority = r.get("priority", "")
                    print(f"\n  [{r['status'].upper()}] {r['name']} {f'({path})' if path else ''} {f'[{priority}]' if priority else ''}")
                    for err in r.get("errors", []):
                        print(f"    - 에러: {err}")
                    for warn in r.get("warnings", []):
                        print(f"    - 경고: {warn}")

        # 오늘 수정사항 체크 결과
        for r in self.results:
            if r.get("name") == "오늘 수정사항 확인" and "checks" in r:
                print("\n오늘 수정사항 (2025-02-06):")
                for c in r["checks"]:
                    icon = "[OK]" if c["status"] == "pass" else "[XX]"
                    print(f"  {icon} {c['item']}")

        # JSON 리포트 저장
        report_path = self.screenshots_dir / f"e2e_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "mode": "full" if self.full_mode else "basic",
            "summary": {
                "total": total,
                "passed": passed,
                "warned": warned,
                "failed": failed
            },
            "results": self.results,
            "interactions": self.interaction_results
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n리포트 저장: {report_path}")
        print(f"스크린샷 폴더: {self.screenshots_dir}")
        print("=" * 60)

        return failed == 0


async def main():
    parser = argparse.ArgumentParser(description="FlyReady E2E 테스트 봇 v2.0")
    parser.add_argument("--full", action="store_true", help="모든 페이지 + 모든 요소 상호작용 테스트")
    parser.add_argument("--quick", action="store_true", help="A등급 핵심 페이지만 빠르게")
    parser.add_argument("--url", type=str, default="http://localhost:8501", help="테스트 대상 URL")
    args = parser.parse_args()

    print(f"\n{'#'*60}")
    print(f"  FlyReady E2E 테스트 봇 v2.0")
    print(f"  사이드바 전체 탐색 + 모든 요소 테스트")
    print(f"{'#'*60}")

    bot = FlyReadyTestBot(args.url, full_mode=args.full)
    await bot.run_all_tests(quick_mode=args.quick)


if __name__ == "__main__":
    asyncio.run(main())
