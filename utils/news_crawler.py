"""
대한항공 뉴스 크롤링 모듈
네이버 뉴스 검색 기반
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os


class NewsCrawler:
    """대한항공 뉴스 크롤러"""

    SEARCH_URL = "https://search.naver.com/search.naver"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def __init__(self, cache_file: str = "data/news_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict = {}
        self._load_cache()

    def _load_cache(self):
        """캐시 로드"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
        except:
            self.cache = {}

    def _save_cache(self):
        """캐시 저장"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except:
            pass

    def search_news(
        self,
        keyword: str = "대한항공",
        days: int = 30,
        max_results: int = 10
    ) -> List[Dict]:
        """
        뉴스 검색

        Args:
            keyword: 검색 키워드
            days: 최근 N일 이내
            max_results: 최대 결과 수

        Returns:
            뉴스 목록 [{title, date, summary, url, source}]
        """
        # 캐시 확인 (1시간 유효)
        cache_key = f"{keyword}_{days}_{max_results}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            cached_time = datetime.fromisoformat(cached["timestamp"])
            if datetime.now() - cached_time < timedelta(hours=1):
                return cached["data"]

        try:
            news_list = self._crawl_naver_news(keyword, days, max_results)

            # 캐시 저장
            self.cache[cache_key] = {
                "timestamp": datetime.now().isoformat(),
                "data": news_list
            }
            self._save_cache()

            return news_list

        except Exception as e:
            print(f"뉴스 크롤링 오류: {e}")
            # 캐시된 데이터 반환 (있으면)
            if cache_key in self.cache:
                return self.cache[cache_key]["data"]
            return []

    def _crawl_naver_news(
        self,
        keyword: str,
        days: int,
        max_results: int
    ) -> List[Dict]:
        """네이버 뉴스 크롤링"""
        params = {
            "where": "news",
            "query": keyword,
            "sort": "1",  # 최신순
            "pd": "4" if days <= 7 else "3",  # 1주일 / 1개월
        }

        response = requests.get(
            self.SEARCH_URL,
            params=params,
            headers=self.HEADERS,
            timeout=10
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        news_items = soup.select("div.news_area")[:max_results]

        results = []
        for item in news_items:
            try:
                # 제목
                title_elem = item.select_one("a.news_tit")
                title = title_elem.get_text(strip=True) if title_elem else ""
                url = title_elem.get("href", "") if title_elem else ""

                # 요약
                summary_elem = item.select_one("div.news_dsc")
                summary = summary_elem.get_text(strip=True) if summary_elem else ""

                # 언론사
                source_elem = item.select_one("a.info.press")
                source = source_elem.get_text(strip=True) if source_elem else ""

                # 날짜
                date_elem = item.select_one("span.info")
                date_text = date_elem.get_text(strip=True) if date_elem else ""
                date = self._parse_date(date_text)

                if title:
                    results.append({
                        "title": title,
                        "date": date,
                        "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                        "url": url,
                        "source": source,
                        "relevance": self._calculate_relevance(title, summary)
                    })
            except Exception as e:
                continue

        return results

    def _parse_date(self, date_text: str) -> str:
        """날짜 파싱"""
        today = datetime.now()

        if "분 전" in date_text:
            return today.strftime("%Y-%m-%d")
        elif "시간 전" in date_text:
            return today.strftime("%Y-%m-%d")
        elif "일 전" in date_text:
            days = int(date_text.replace("일 전", "").strip())
            return (today - timedelta(days=days)).strftime("%Y-%m-%d")
        else:
            return date_text

    def _calculate_relevance(self, title: str, summary: str) -> str:
        """면접 관련도 태깅"""
        text = (title + " " + summary).lower()

        # 필수 숙지 키워드
        essential_keywords = ["합병", "인수", "실적", "사고", "안전", "파업", "채용"]
        for kw in essential_keywords:
            if kw in text:
                return "필수"

        # 알면 좋은 키워드
        good_keywords = ["노선", "취항", "서비스", "신규", "수상", "좌석"]
        for kw in good_keywords:
            if kw in text:
                return "알면좋음"

        return "참고용"


# 정적 뉴스 데이터 (크롤링 실패 시 폴백) - 2026년 채용 기준
FALLBACK_NEWS = [
    {
        "title": "대한항공-아시아나 통합 완료, 세계 11위 메가 캐리어로",
        "date": "2024-12",
        "summary": "2024.12.11 지분 63.88% 인수 완료. 2026.12 브랜드 완전 통합 예정. 면접에서 아시아나를 경쟁사로 언급 시 감점 가능",
        "url": "https://news.koreanair.com",
        "source": "대한항공 뉴스룸",
        "relevance": "필수"
    },
    {
        "title": "아시아나 인천공항 제2터미널 이전 완료",
        "date": "2026-01",
        "summary": "대한항공과 아시아나가 인천공항 제2터미널에서 통합 운영 시작",
        "url": "https://news.koreanair.com",
        "source": "대한항공 뉴스룸",
        "relevance": "필수"
    },
    {
        "title": "LCC 통합 추진: 진에어·에어서울·에어부산 → 진에어",
        "date": "2026-02",
        "summary": "2027년 초 LCC 3사 통합 예정. 그룹 전체 시너지 효과 기대",
        "url": "https://news.koreanair.com",
        "source": "대한항공 뉴스룸",
        "relevance": "알면좋음"
    },
    {
        "title": "대한항공, 친환경 SAF 도입 확대",
        "date": "2026-01",
        "summary": "지속가능 항공유(SAF) 사용 확대로 탄소중립 목표 추진. Better Tomorrow 가치와 연결",
        "url": "https://news.koreanair.com",
        "source": "대한항공 ESG",
        "relevance": "알면좋음"
    }
]


def get_korean_air_news(max_results: int = 10) -> List[Dict]:
    """대한항공 뉴스 가져오기 (외부 함수)"""
    try:
        crawler = NewsCrawler()
        news = crawler.search_news("대한항공", days=30, max_results=max_results)
        if news:
            return news
    except:
        pass

    # 폴백 데이터 반환
    return FALLBACK_NEWS
