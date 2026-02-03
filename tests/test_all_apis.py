# 모든 외부 API/LLM 연동 테스트
# 실행: python test_all_apis.py

import os
import sys
import time
import json
import requests
import io

# 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

print("=" * 70)
print("FlyReady Lab - 외부 API 연동 테스트")
print("=" * 70)

results = {}

# ============================================
# 1. OpenAI GPT-4o-mini 테스트
# ============================================
print("\n[1/5] OpenAI GPT-4o-mini 테스트...")
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY 환경변수 없음")

    start = time.time()
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "안녕하세요. 테스트입니다. 한 문장으로 답해주세요."}],
            "max_tokens": 50,
            "temperature": 0.5
        },
        timeout=30
    )
    elapsed = time.time() - start

    if response.status_code == 200:
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {})
        print(f"  [OK] 성공 ({elapsed:.1f}초)")
        print(f"       응답: {answer[:50]}...")
        print(f"       토큰: 입력 {tokens.get('prompt_tokens', '?')}, 출력 {tokens.get('completion_tokens', '?')}")
        results["GPT-4o-mini"] = "[OK] 정상"
    else:
        print(f"  [FAIL] 실패: HTTP {response.status_code}")
        print(f"         {response.text[:100]}")
        results["GPT-4o-mini"] = f"[FAIL] HTTP {response.status_code}"
except Exception as e:
    print(f"  [FAIL] 오류: {e}")
    results["GPT-4o-mini"] = f"[FAIL] {type(e).__name__}"

# ============================================
# 2. OpenAI GPT-4o (Vision) 테스트
# ============================================
print("\n[2/5] OpenAI GPT-4o (Vision) 테스트...")
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY 환경변수 없음")

    start = time.time()
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "표정 분석 테스트입니다. '웃는 표정'을 분석한다면 어떻게 하겠습니까? 한 문장으로 답하세요."}],
            "max_tokens": 50,
            "temperature": 0.3
        },
        timeout=30
    )
    elapsed = time.time() - start

    if response.status_code == 200:
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        print(f"  [OK] 성공 ({elapsed:.1f}초)")
        print(f"       응답: {answer[:60]}...")
        results["GPT-4o (Vision)"] = "[OK] 정상"
    else:
        print(f"  [FAIL] 실패: HTTP {response.status_code}")
        results["GPT-4o (Vision)"] = f"[FAIL] HTTP {response.status_code}"
except Exception as e:
    print(f"  [FAIL] 오류: {e}")
    results["GPT-4o (Vision)"] = f"[FAIL] {type(e).__name__}"

# ============================================
# 3. OpenAI Whisper (STT) 테스트
# ============================================
print("\n[3/5] OpenAI Whisper (STT) 테스트...")
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY 환경변수 없음")

    print("  [INFO] Whisper는 오디오 파일 필요 - API 키 유효성만 확인")

    response = requests.get(
        "https://api.openai.com/v1/models/whisper-1",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10
    )

    if response.status_code == 200:
        print(f"  [OK] Whisper 모델 접근 가능")
        results["Whisper (STT)"] = "[OK] 정상"
    else:
        print(f"  [FAIL] 실패: HTTP {response.status_code}")
        results["Whisper (STT)"] = f"[FAIL] HTTP {response.status_code}"
except Exception as e:
    print(f"  [FAIL] 오류: {e}")
    results["Whisper (STT)"] = f"[FAIL] {type(e).__name__}"

# ============================================
# 4. CLOVA HCX-005 테스트
# ============================================
print("\n[4/5] CLOVA HCX-005 (HyperCLOVA X) 테스트...")
try:
    # flyready_clova_engine.py와 동일한 방식으로 키 로드
    CLOVA_API_KEY = os.getenv("CLOVA_API_KEY", "nv-f59b211212244304b064c131640a92a0UgPZ")
    CLOVA_REQUEST_ID = os.getenv("CLOVA_REQUEST_ID", "331785bac0c64228ac15f5616d9082d7")

    start = time.time()
    response = requests.post(
        "https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005",
        headers={
            "Authorization": f"Bearer {CLOVA_API_KEY}",
            "X-NCP-CLOVASTUDIO-REQUEST-ID": CLOVA_REQUEST_ID,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json"
        },
        json={
            "messages": [
                {"role": "system", "content": "당신은 테스트 봇입니다."},
                {"role": "user", "content": "안녕하세요. 테스트입니다. 한 문장으로 답해주세요."}
            ],
            "temperature": 0.3,
            "maxTokens": 50,
            "topP": 0.8,
            "topK": 0,
            "repeatPenalty": 1.2
        },
        timeout=30
    )
    elapsed = time.time() - start

    if response.status_code == 200:
        data = response.json()
        if "result" in data and "message" in data["result"]:
            answer = data["result"]["message"]["content"]
            print(f"  [OK] 성공 ({elapsed:.1f}초)")
            print(f"       응답: {answer[:60]}...")
            results["CLOVA HCX-005"] = "[OK] 정상"
        elif "message" in data:
            answer = data["message"].get("content", "")
            print(f"  [OK] 성공 ({elapsed:.1f}초)")
            print(f"       응답: {answer[:60]}...")
            results["CLOVA HCX-005"] = "[OK] 정상"
        else:
            print(f"  [WARN] 응답 형식 확인 필요: {str(data)[:100]}")
            results["CLOVA HCX-005"] = "[WARN] 응답 형식 확인"
    else:
        print(f"  [FAIL] 실패: HTTP {response.status_code}")
        print(f"         {response.text[:150]}")
        results["CLOVA HCX-005"] = f"[FAIL] HTTP {response.status_code}"
except Exception as e:
    print(f"  [FAIL] 오류: {e}")
    results["CLOVA HCX-005"] = f"[FAIL] {type(e).__name__}"

# ============================================
# 5. Google TTS 테스트
# ============================================
print("\n[5/5] Google TTS 테스트...")
try:
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if google_key and os.path.exists(str(google_key)):
        print(f"  [WARN] 서비스 계정 파일 존재")
        results["Google TTS"] = "[WARN] 서비스 계정 설정됨"
    elif google_key:
        print(f"  [WARN] API 키 설정됨")
        results["Google TTS"] = "[WARN] API 키 설정됨"
    else:
        try:
            from gtts import gTTS
            print(f"  [OK] gTTS 라이브러리 사용 가능 (무료)")
            results["Google TTS"] = "[OK] gTTS 사용 가능"
        except ImportError:
            print(f"  [WARN] Google TTS 키 미설정, gTTS도 없음")
            results["Google TTS"] = "[WARN] 미설정"
except Exception as e:
    print(f"  [FAIL] 오류: {e}")
    results["Google TTS"] = f"[FAIL] {type(e).__name__}"

# ============================================
# 결과 요약
# ============================================
print("\n" + "=" * 70)
print("테스트 결과 요약")
print("=" * 70)

for api, status in results.items():
    print(f"  {api:25s} : {status}")

success_count = sum(1 for s in results.values() if "[OK]" in s)
warning_count = sum(1 for s in results.values() if "[WARN]" in s)
error_count = sum(1 for s in results.values() if "[FAIL]" in s)

print("\n" + "-" * 70)
print(f"  [OK]: {success_count}개  |  [WARN]: {warning_count}개  |  [FAIL]: {error_count}개")
print("=" * 70)

if error_count == 0:
    print("\n>>> 모든 핵심 API가 정상 작동합니다!")
else:
    print("\n>>> 일부 API에 문제가 있습니다. 위 오류를 확인해주세요.")
