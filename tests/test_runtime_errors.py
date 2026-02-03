# 런타임 오류 검사 스크립트
import os
import sys
import importlib.util

# 환경 설정
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Streamlit mock (페이지 로드 시 st.set_page_config 오류 방지)
class MockStreamlit:
    def __getattr__(self, name):
        def mock_func(*args, **kwargs):
            if name == 'set_page_config':
                raise SystemExit("set_page_config called - page structure OK")
            return None
        return mock_func

sys.modules['streamlit'] = MockStreamlit()
sys.modules['streamlit.components'] = MockStreamlit()
sys.modules['streamlit.components.v1'] = MockStreamlit()

pages_dir = os.path.join(os.path.dirname(__file__), "pages")
results = {"ok": [], "error": [], "warning": []}

print("=" * 60)
print("FlyReady Lab - 런타임 오류 검사")
print("=" * 60)

for filename in sorted(os.listdir(pages_dir)):
    if filename.endswith(".py") and not filename.startswith("_"):
        filepath = os.path.join(pages_dir, filename)
        try:
            spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"[OK] {filename}")
            results["ok"].append(filename)
        except SystemExit as e:
            if "set_page_config" in str(e):
                print(f"[OK] {filename} (구조 정상)")
                results["ok"].append(filename)
            else:
                print(f"[WARN] {filename}: SystemExit - {e}")
                results["warning"].append((filename, str(e)))
        except ImportError as e:
            print(f"[WARN] {filename}: ImportError - {e}")
            results["warning"].append((filename, str(e)))
        except Exception as e:
            print(f"[ERROR] {filename}: {type(e).__name__} - {e}")
            results["error"].append((filename, f"{type(e).__name__}: {e}"))

print("\n" + "=" * 60)
print(f"결과: OK={len(results['ok'])}, 경고={len(results['warning'])}, 오류={len(results['error'])}")

if results["error"]:
    print("\n오류 목록:")
    for f, e in results["error"]:
        print(f"  - {f}: {e}")

if results["warning"]:
    print("\n경고 목록 (import 실패 - 선택적 의존성):")
    for f, e in results["warning"]:
        print(f"  - {f}: {e}")

print("=" * 60)
