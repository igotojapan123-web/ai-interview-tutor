# 모든 페이지 오류 체크
import os
import sys
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

pages_dir = os.path.join(os.path.dirname(__file__), "pages")
errors = []

print("=" * 60)
print("FlyReady Lab - 페이지 구문 오류 검사")
print("=" * 60)

for filename in sorted(os.listdir(pages_dir)):
    if filename.endswith(".py") and not filename.startswith("_"):
        filepath = os.path.join(pages_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, filepath, 'exec')
            print(f"[OK] {filename}")
        except SyntaxError as e:
            print(f"[ERROR] {filename}: 구문 오류 - {e}")
            errors.append((filename, str(e)))
        except Exception as e:
            print(f"[WARN] {filename}: {type(e).__name__} - {e}")

print("\n" + "=" * 60)
if errors:
    print(f"오류 발견: {len(errors)}개")
    for f, e in errors:
        print(f"  - {f}: {e}")
else:
    print("모든 페이지 구문 검사 통과!")
print("=" * 60)
