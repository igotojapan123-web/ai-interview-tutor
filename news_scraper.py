# news_scraper.py
# 항공사 뉴스 자동 수집 모듈 (Google News RSS + Naver News API)

import os
import json
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from html import unescape

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 캐시 설정
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE_FILE = os.path.join(DATA_DIR, "airline_news.json")
CACHE_TTL = 86400  # 24시간 (초)

# 항공사 검색 키워드 매핑
AIRLINE_SEARCH_KEYWORDS = {
    "대한항공": ["대한항공", "Korean Air", "KE"],
    "아시아나항공": ["아시아나항공", "아시아나", "Asiana"],
    "진에어": ["진에어", "Jin Air"],
    "제주항공": ["제주항공", "Jeju Air"],
    "티웨이항공": ["티웨이항공", "티웨이", "T'way"],
    "에어부산": ["에어부산", "Air Busan"],
    "에어서울": ["에어서울", "Air Seoul"],
    "이스타항공": ["이스타항공", "Eastar Jet"],
    "에어프레미아": ["에어프레미아", "Air Premia"],
    "에어로케이": ["에어로케이", "Aero K"],
    "파라타항공": ["파라타항공", "플라이강원", "Fly Gangwon"],
}


def _clean_html(text: str) -> str:
    """HTML 태그 및 엔티티 제거"""
    if not text:
        return ""
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # HTML 엔티티 디코딩
    text = unescape(text)
    # 불필요한 공백 정리
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _generate_news_id(title: str, source: str) -> str:
    """뉴스 고유 ID 생성"""
    content = f"{title}_{source}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def _parse_date(date_str: str) -> Optional[str]:
    """다양한 날짜 형식 파싱"""
    if not date_str:
        return None

    # RFC 2822 형식 (feedparser)
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime("%Y-%m-%d")
    except:
        pass

    # ISO 형식
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except:
        pass

    # 한국어 날짜 형식
    patterns = [
        (r'(\d{4})\.(\d{1,2})\.(\d{1,2})', '%Y-%m-%d'),
        (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
    ]
    for pattern, fmt in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
            except:
                pass

    return None


def _is_within_days(date_str: str, days: int) -> bool:
    """날짜가 지정된 일수 내인지 확인"""
    if not date_str:
        return True  # 날짜 없으면 포함

    try:
        news_date = datetime.strptime(date_str, "%Y-%m-%d")
        cutoff_date = datetime.now() - timedelta(days=days)
        return news_date >= cutoff_date
    except:
        return True


# ============================================
# Google News RSS
# ============================================
def fetch_google_news(airline: str, days: int = 90) -> List[Dict]:
    """Google News RSS에서 항공사 뉴스 수집"""
    if not FEEDPARSER_AVAILABLE:
        return []

    results = []
    keywords = AIRLINE_SEARCH_KEYWORDS.get(airline, [airline])

    for keyword in keywords[:2]:  # 상위 2개 키워드만
        # 검색 쿼리 생성
        query = f"{keyword} 채용 OR {keyword} 승무원 OR {keyword} 객실승무원"
        encoded_query = requests.utils.quote(query) if REQUESTS_AVAILABLE else query.replace(" ", "+")

        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries[:30]:  # 최대 30개
                pub_date = _parse_date(entry.get("published", ""))

                # 기간 필터링
                if not _is_within_days(pub_date, days):
                    continue

                title = _clean_html(entry.get("title", ""))
                summary = _clean_html(entry.get("summary", entry.get("description", "")))

                # 소스 추출 (Google News 형식: "제목 - 출처")
                source = "Google News"
                if " - " in title:
                    parts = title.rsplit(" - ", 1)
                    if len(parts) == 2:
                        title = parts[0]
                        source = parts[1]

                news_item = {
                    "id": _generate_news_id(title, source),
                    "title": title,
                    "summary": summary[:300] if summary else "",
                    "source": source,
                    "url": entry.get("link", ""),
                    "published_at": pub_date,
                    "airline": airline,
                    "provider": "google",
                }
                results.append(news_item)

        except Exception as e:
            print(f"[news_scraper] Google News 수집 실패 ({keyword}): {e}")
            continue

    return results


# ============================================
# Naver News API
# ============================================
def fetch_naver_news(airline: str, days: int = 90) -> List[Dict]:
    """Naver 뉴스 검색 API 사용"""
    if not REQUESTS_AVAILABLE:
        return []

    # API 키 확인
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        # API 키 없으면 빈 리스트 반환 (에러 아님)
        return []

    results = []
    keywords = AIRLINE_SEARCH_KEYWORDS.get(airline, [airline])

    # 다양한 쿼리로 검색 (채용/일반 뉴스 모두 수집)
    queries = [
        f"{keywords[0]}",  # 기본 검색
        f"{keywords[0]} 채용",  # 채용 관련
        f"{keywords[0]} 승무원",  # 승무원 관련
    ]

    for query in queries:

        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }
        params = {
            "query": query,
            "display": 100,
            "sort": "date",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                pub_date = _parse_date(item.get("pubDate", ""))

                # 기간 필터링
                if not _is_within_days(pub_date, days):
                    continue

                title = _clean_html(item.get("title", ""))
                description = _clean_html(item.get("description", ""))

                news_item = {
                    "id": _generate_news_id(title, "naver"),
                    "title": title,
                    "summary": description[:300] if description else "",
                    "source": "네이버 뉴스",
                    "url": item.get("link", ""),
                    "published_at": pub_date,
                    "airline": airline,
                    "provider": "naver",
                }
                results.append(news_item)

        except Exception as e:
            print(f"[news_scraper] Naver News 수집 실패 ({keyword}): {e}")
            continue

    return results


# ============================================
# 캐시 관리
# ============================================
def _load_cache() -> Dict:
    """캐시 파일 로드"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[news_scraper] 캐시 로드 실패: {e}")
    return {"news": {}, "last_update": {}}


def _save_cache(cache: Dict):
    """캐시 파일 저장"""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[news_scraper] 캐시 저장 실패: {e}")


def _is_cache_valid(cache: Dict, airline: str) -> bool:
    """캐시 유효성 확인"""
    last_update = cache.get("last_update", {}).get(airline)
    if not last_update:
        return False

    try:
        update_time = datetime.fromisoformat(last_update)
        return (datetime.now() - update_time).total_seconds() < CACHE_TTL
    except:
        return False


def _deduplicate_news(news_list: List[Dict]) -> List[Dict]:
    """중복 뉴스 제거"""
    seen_ids = set()
    unique_news = []

    for news in news_list:
        if news["id"] not in seen_ids:
            seen_ids.add(news["id"])
            unique_news.append(news)

    return unique_news


# ============================================
# 메인 함수
# ============================================
def get_airline_news(airline: str, days: int = 90, force_refresh: bool = False) -> List[Dict]:
    """
    항공사 뉴스 조회 (캐시 우선, 만료시 자동 갱신)

    Args:
        airline: 항공사명 (예: "대한항공")
        days: 최근 N일 이내 뉴스만 (기본 90일)
        force_refresh: 캐시 무시하고 새로 수집

    Returns:
        List[Dict]: 뉴스 목록
        [{
            "id": "abc123",
            "title": "뉴스 제목",
            "summary": "요약",
            "source": "출처",
            "url": "링크",
            "published_at": "2025-01-15",
            "airline": "대한항공",
            "provider": "google" or "naver"
        }, ...]
    """
    cache = _load_cache()

    # 캐시 유효하면 캐시에서 반환
    if not force_refresh and _is_cache_valid(cache, airline):
        cached_news = cache.get("news", {}).get(airline, [])
        # 기간 필터링 재적용
        return [n for n in cached_news if _is_within_days(n.get("published_at"), days)]

    # 새로 수집
    all_news = []

    # Google News
    google_news = fetch_google_news(airline, days)
    all_news.extend(google_news)

    # Naver News
    naver_news = fetch_naver_news(airline, days)
    all_news.extend(naver_news)

    # 중복 제거 및 정렬
    all_news = _deduplicate_news(all_news)
    all_news.sort(key=lambda x: x.get("published_at", "") or "", reverse=True)

    # 캐시 업데이트
    if "news" not in cache:
        cache["news"] = {}
    if "last_update" not in cache:
        cache["last_update"] = {}

    cache["news"][airline] = all_news
    cache["last_update"][airline] = datetime.now().isoformat()
    _save_cache(cache)

    return all_news


def get_news_summary(airline: str, max_items: int = 5) -> str:
    """
    뉴스 요약 텍스트 생성 (AI 프롬프트용)

    Args:
        airline: 항공사명
        max_items: 최대 뉴스 개수

    Returns:
        str: 뉴스 요약 텍스트
    """
    news = get_airline_news(airline, days=90)[:max_items]

    if not news:
        return "최근 뉴스 정보가 없습니다."

    lines = [f"## {airline} 최근 뉴스 (최근 3개월)"]
    for i, item in enumerate(news, 1):
        date = item.get("published_at", "날짜 미상")
        title = item.get("title", "제목 없음")
        lines.append(f"{i}. [{date}] {title}")

    return "\n".join(lines)


def refresh_all_airlines():
    """모든 항공사 뉴스 새로고침"""
    for airline in AIRLINE_SEARCH_KEYWORDS.keys():
        print(f"[news_scraper] {airline} 뉴스 수집 중...")
        get_airline_news(airline, force_refresh=True)
    print("[news_scraper] 전체 항공사 뉴스 수집 완료")


# ============================================
# 테스트용
# ============================================
if __name__ == "__main__":
    # 테스트 실행
    print("=== 뉴스 스크래퍼 테스트 ===")

    test_airline = "대한항공"
    print(f"\n{test_airline} 뉴스 수집 중...")

    news = get_airline_news(test_airline, days=90, force_refresh=True)
    print(f"수집된 뉴스: {len(news)}건")

    for item in news[:5]:
        print(f"  - [{item.get('published_at')}] {item.get('title')[:50]}...")

    print("\n--- 뉴스 요약 ---")
    print(get_news_summary(test_airline))
