# crawlers/naver_news.py
# 네이버 뉴스 API 크롤러

import requests
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from html import unescape


class NaverNewsCrawler:
    """네이버 뉴스 검색 API를 사용한 크롤러"""

    BASE_URL = "https://openapi.naver.com/v1/search/news.json"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret
        }

    def search(self, query: str, display: int = 100, sort: str = "date") -> List[Dict]:
        """
        네이버 뉴스 검색

        Args:
            query: 검색 키워드
            display: 검색 결과 개수 (최대 100)
            sort: 정렬 방식 (date: 최신순, sim: 유사도순)

        Returns:
            뉴스 기사 리스트
        """
        params = {
            "query": query,
            "display": display,
            "sort": sort
        }

        try:
            response = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return self._process_items(data.get("items", []))

        except requests.RequestException as e:
            print(f"[ERROR] 네이버 뉴스 검색 실패 ({query}): {e}")
            return []

    def _process_items(self, items: List[Dict]) -> List[Dict]:
        """검색 결과 정제"""
        processed = []

        for item in items:
            # HTML 태그 제거 및 unescape
            title = self._clean_text(item.get("title", ""))
            description = self._clean_text(item.get("description", ""))

            # 날짜 파싱
            pub_date = self._parse_date(item.get("pubDate", ""))

            processed.append({
                "title": title,
                "description": description,
                "link": item.get("link", ""),
                "originallink": item.get("originallink", ""),
                "pub_date": pub_date,
                "source": self._extract_source(item.get("originallink", ""))
            })

        return processed

    def _clean_text(self, text: str) -> str:
        """HTML 태그 제거 및 텍스트 정제"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # HTML entities 변환
        text = unescape(text)
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _parse_date(self, date_str: str) -> Optional[str]:
        """날짜 문자열 파싱"""
        try:
            # RFC 822 형식: "Mon, 03 Feb 2026 10:30:00 +0900"
            dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return date_str

    def _extract_source(self, url: str) -> str:
        """URL에서 언론사 추출"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # 주요 언론사 매핑
            source_map = {
                "yna.co.kr": "연합뉴스",
                "news.sbs.co.kr": "SBS",
                "news.kbs.co.kr": "KBS",
                "imnews.imbc.com": "MBC",
                "www.chosun.com": "조선일보",
                "www.donga.com": "동아일보",
                "www.hani.co.kr": "한겨레",
                "www.khan.co.kr": "경향신문",
                "www.mk.co.kr": "매일경제",
                "www.hankyung.com": "한국경제",
                "www.sedaily.com": "서울경제",
                "www.fnnews.com": "파이낸셜뉴스",
                "www.newsis.com": "뉴시스",
                "www.ytn.co.kr": "YTN",
            }
            return source_map.get(domain, domain)
        except:
            return "출처 미상"

    def crawl_keywords(self, keywords: List[str], days_back: int = 1) -> List[Dict]:
        """
        여러 키워드로 뉴스 크롤링

        수집 범위: 전날 09:00 ~ 오늘 08:00 (직전 24시간)
        예: 2월 5일 오전 9시 발송 → 2월 4일 09:00 ~ 2월 5일 08:00

        Args:
            keywords: 검색 키워드 리스트
            days_back: 며칠 전 뉴스까지 수집할지

        Returns:
            중복 제거된 뉴스 리스트
        """
        all_articles = []
        seen_titles = set()

        # 수집 범위: 전날 09:00 ~ 오늘 08:00
        now = datetime.now()
        end_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(hours=24)

        # 현재 시각이 오전 8시 이전이면 하루 더 앞으로
        if now < end_time:
            pass  # 정상 (오늘 08:00 기준)
        else:
            # 오전 8시 이후 실행 → 오늘 09:00 ~ 내일 08:00은 아직 안 됨
            # 그대로 전날 09:00 ~ 오늘 08:00 사용
            pass

        print(f"  수집 범위: {start_time.strftime('%m/%d %H:%M')} ~ {end_time.strftime('%m/%d %H:%M')}")

        for keyword in keywords:
            print(f"  검색 중: {keyword}")
            articles = self.search(keyword)

            for article in articles:
                # 제목 기반 중복 체크
                title_key = article["title"][:30]
                if title_key in seen_titles:
                    continue

                # 시간 범위 필터
                if article["pub_date"]:
                    try:
                        pub_dt = datetime.strptime(article["pub_date"], "%Y-%m-%d %H:%M")
                        if start_time <= pub_dt <= end_time:
                            seen_titles.add(title_key)
                            article["keyword"] = keyword
                            all_articles.append(article)
                    except ValueError:
                        continue

        print(f"  총 {len(all_articles)}개 기사 수집")
        return all_articles


def test_crawler():
    """크롤러 테스트"""
    import os

    # 환경변수에서 API 키 로드 (테스트용)
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        print("[ERROR] NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 환경변수를 설정하세요.")
        return

    crawler = NaverNewsCrawler(client_id, client_secret)

    # 테스트 검색
    results = crawler.search("대한항공", display=5)

    print(f"\n검색 결과 ({len(results)}개):\n")
    for i, article in enumerate(results, 1):
        print(f"{i}. {article['title']}")
        print(f"   날짜: {article['pub_date']}")
        print(f"   출처: {article['source']}")
        print(f"   링크: {article['link']}")
        print()


if __name__ == "__main__":
    test_crawler()
