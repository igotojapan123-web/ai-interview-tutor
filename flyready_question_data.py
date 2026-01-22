"""
FLYREADY 질문 데이터 통합 모듈
================================
5개 JSON 파일에서 질문 데이터를 로드하고 랜덤 선택 기능 제공

데이터 소스:
- 01_공통질문_100.json: 공통 면접 질문 100개 (10개 카테고리)
- 02_자소서_심층질문_생성_프롬프트.json: 자소서 분석 로직
- 03_꼬리질문_생성_프롬프트.json: FSC/LCC별 꼬리질문 패턴
- 04_항공사별_핵심질문_660.json: 항공사별 질문 660개 (11개 항공사)
- 05_돌발확장질문_100.json: 돌발/확장 질문 100개 (7개 카테고리)
"""

import json
import os
import random
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path


# ===========================================
# 데이터 파일 경로
# ===========================================
DATA_DIR = Path(r"C:\Users\ADMIN\Desktop")

DATA_FILES = {
    "common_100": DATA_DIR / "01_공통질문_100.json",
    "resume_prompt": DATA_DIR / "02_자소서_심층질문_생성_프롬프트.json",
    "followup_prompt": DATA_DIR / "03_꼬리질문_생성_프롬프트.json",
    "airline_660": DATA_DIR / "04_항공사별_핵심질문_660.json",
    "surprise_100": DATA_DIR / "05_돌발확장질문_100.json",
}


# ===========================================
# 캐시된 데이터 (싱글톤)
# ===========================================
_data_cache: Dict[str, Any] = {}


def _load_json(filepath: Path) -> Optional[Dict]:
    """JSON 파일 로드"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] JSON 로드 실패: {filepath} - {e}")
        return None


def load_all_data() -> Dict[str, Any]:
    """모든 데이터 파일 로드 (캐시)"""
    global _data_cache

    if _data_cache:
        return _data_cache

    for key, filepath in DATA_FILES.items():
        data = _load_json(filepath)
        if data:
            _data_cache[key] = data
            print(f"[DATA] {key} 로드 완료")

    return _data_cache


# ===========================================
# 01. 공통질문 100개
# ===========================================

def get_common_questions() -> List[Dict]:
    """공통질문 100개 전체 반환"""
    data = load_all_data()
    common = data.get("common_100", {})
    return common.get("questions", [])


def get_common_categories() -> List[str]:
    """공통질문 카테고리 목록"""
    data = load_all_data()
    common = data.get("common_100", {})
    return common.get("categories", [])


def get_common_by_category(category: str) -> List[Dict]:
    """특정 카테고리의 공통질문 반환"""
    questions = get_common_questions()
    return [q for q in questions if q.get("category") == category]


def get_random_common_questions(count: int = 5, category: Optional[str] = None) -> List[Dict]:
    """랜덤 공통질문 선택"""
    if category:
        pool = get_common_by_category(category)
    else:
        pool = get_common_questions()

    if not pool:
        return []

    return random.sample(pool, min(count, len(pool)))


# ===========================================
# 04. 항공사별 핵심질문 660개
# ===========================================

AIRLINE_MAP = {
    "대한항공": "대한항공",
    "아시아나항공": "아시아나항공",
    "아시아나": "아시아나항공",
    "제주항공": "제주항공",
    "진에어": "진에어",
    "티웨이항공": "티웨이항공",
    "티웨이": "티웨이항공",
    "이스타항공": "이스타항공",
    "이스타": "이스타항공",
    "에어부산": "에어부산",
    "에어서울": "에어서울",
    "에어로케이": "에어로케이",
    "에어프레미아": "에어프레미아",
    "파라타항공": "파라타항공",
    "파라타": "파라타항공",
}

FSC_AIRLINES = ["대한항공", "아시아나항공"]
LCC_AIRLINES = ["제주항공", "진에어", "티웨이항공", "이스타항공", "에어부산", "에어서울", "에어로케이", "파라타항공"]
HSC_AIRLINES = ["에어프레미아"]


def _normalize_airline(airline: str) -> str:
    """항공사 이름 정규화"""
    return AIRLINE_MAP.get(airline, airline)


def get_airline_questions(airline: str) -> Dict:
    """특정 항공사의 질문 데이터 반환"""
    data = load_all_data()
    airline_data = data.get("airline_660", {})
    airlines = airline_data.get("airlines", {})

    normalized = _normalize_airline(airline)
    return airlines.get(normalized, {})


def get_airline_question_list(airline: str) -> List[str]:
    """특정 항공사의 질문 리스트 반환 (카테고리별 통합)"""
    airline_info = get_airline_questions(airline)
    categories = airline_info.get("categories", {})

    questions = []
    for cat_name, cat_questions in categories.items():
        if isinstance(cat_questions, list):
            questions.extend(cat_questions)

    return questions


def get_random_airline_questions(airline: str, count: int = 5) -> List[str]:
    """특정 항공사에서 랜덤 질문 선택"""
    questions = get_airline_question_list(airline)
    if not questions:
        return []
    return random.sample(questions, min(count, len(questions)))


def get_airline_type(airline: str) -> str:
    """항공사 유형 반환 (FSC/LCC/HSC)"""
    normalized = _normalize_airline(airline)
    if normalized in FSC_AIRLINES:
        return "FSC"
    elif normalized in HSC_AIRLINES:
        return "HSC"
    else:
        return "LCC"


# ===========================================
# 05. 돌발/확장 질문 100개
# ===========================================

def get_surprise_questions() -> Dict[str, List[str]]:
    """돌발질문 카테고리별 반환"""
    data = load_all_data()
    surprise = data.get("surprise_100", {})
    categories = surprise.get("categories", {})

    result = {}
    for cat_name, cat_data in categories.items():
        if isinstance(cat_data, dict):
            result[cat_name] = cat_data.get("questions", [])
        elif isinstance(cat_data, list):
            result[cat_name] = cat_data

    return result


def get_surprise_categories() -> List[str]:
    """돌발질문 카테고리 목록"""
    return list(get_surprise_questions().keys())


def get_all_surprise_questions() -> List[str]:
    """모든 돌발질문 리스트"""
    categories = get_surprise_questions()
    all_questions = []
    for questions in categories.values():
        all_questions.extend(questions)
    return all_questions


def get_random_surprise_questions(count: int = 3, category: Optional[str] = None) -> List[str]:
    """랜덤 돌발질문 선택"""
    if category:
        categories = get_surprise_questions()
        pool = categories.get(category, [])
    else:
        pool = get_all_surprise_questions()

    if not pool:
        return []

    return random.sample(pool, min(count, len(pool)))


def get_surprise_by_difficulty(difficulty: str) -> List[str]:
    """난이도별 돌발질문 반환 (easy/medium/hard)"""
    data = load_all_data()
    surprise = data.get("surprise_100", {})
    usage = surprise.get("usage_guide", {})
    difficulty_map = usage.get("difficulty_control", {})

    category_names = difficulty_map.get(difficulty, "").split(", ")
    categories = get_surprise_questions()

    questions = []
    for cat_name in category_names:
        cat_name = cat_name.strip()
        if cat_name in categories:
            questions.extend(categories[cat_name])

    return questions


# ===========================================
# 03. 꼬리질문 패턴
# ===========================================

def get_followup_patterns(airline_type: str = "LCC") -> List[str]:
    """FSC/LCC별 꼬리질문 패턴"""
    data = load_all_data()
    followup = data.get("followup_prompt", {})

    if airline_type.upper() == "FSC":
        patterns = followup.get("fsc_specific_follow_ups", {})
    else:
        patterns = followup.get("lcc_specific_follow_ups", {})

    return patterns.get("patterns", [])


def get_random_followup(airline_type: str = "LCC", count: int = 3) -> List[str]:
    """랜덤 꼬리질문 패턴 선택"""
    patterns = get_followup_patterns(airline_type)
    if not patterns:
        return []
    return random.sample(patterns, min(count, len(patterns)))


def get_vulnerability_signals() -> List[Dict]:
    """취약점 신호 목록"""
    data = load_all_data()
    followup = data.get("followup_prompt", {})
    framework = followup.get("answer_analysis_framework", {})
    step2 = framework.get("step2_빈틈_탐지", {})
    return step2.get("vulnerability_signals", [])


# ===========================================
# 02. 자소서 심층질문 로직
# ===========================================

def get_resume_analysis_framework() -> Dict:
    """자소서 분석 프레임워크"""
    data = load_all_data()
    resume = data.get("resume_prompt", {})
    return resume.get("analysis_framework", {})


def get_vulnerability_types() -> List[Dict]:
    """취약점 유형 목록"""
    framework = get_resume_analysis_framework()
    step2 = framework.get("step2_취약점_분석", {})
    return step2.get("vulnerability_types", [])


def get_question_levels() -> List[Dict]:
    """질문 레벨 (사실확인/깊이검증/연결적용)"""
    framework = get_resume_analysis_framework()
    step3 = framework.get("step3_질문_생성", {})
    return step3.get("question_levels", [])


def get_airline_focus(airline: str) -> Dict:
    """항공사별 인재상 포커스"""
    data = load_all_data()
    resume = data.get("resume_prompt", {})
    focus = resume.get("airline_specific_focus", {})
    normalized = _normalize_airline(airline)
    return focus.get(normalized, {})


# ===========================================
# 통합 질문 생성 함수
# ===========================================

def get_mixed_questions(
    airline: str,
    count: int = 10,
    include_common: bool = True,
    include_airline: bool = True,
    include_surprise: bool = True,
    common_ratio: float = 0.3,
    airline_ratio: float = 0.5,
    surprise_ratio: float = 0.2,
) -> List[Dict[str, str]]:
    """
    다양한 소스에서 질문을 혼합하여 반환

    Returns:
        List[Dict]: [{"question": "...", "source": "common|airline|surprise", "category": "..."}]
    """
    result = []

    # 비율 계산
    if include_common:
        common_count = max(1, int(count * common_ratio))
    else:
        common_count = 0

    if include_airline:
        airline_count = max(1, int(count * airline_ratio))
    else:
        airline_count = 0

    if include_surprise:
        surprise_count = max(1, int(count * surprise_ratio))
    else:
        surprise_count = 0

    # 총 개수 조정
    total = common_count + airline_count + surprise_count
    if total > count:
        # 비율 조정
        factor = count / total
        common_count = int(common_count * factor)
        airline_count = int(airline_count * factor)
        surprise_count = count - common_count - airline_count

    # 공통질문
    if common_count > 0:
        common_qs = get_random_common_questions(common_count)
        for q in common_qs:
            result.append({
                "question": q.get("question", ""),
                "source": "common",
                "category": q.get("category", ""),
                "difficulty": q.get("difficulty", "중"),
            })

    # 항공사별 질문
    if airline_count > 0:
        airline_qs = get_random_airline_questions(airline, airline_count)
        for q in airline_qs:
            result.append({
                "question": q,
                "source": "airline",
                "category": airline,
                "difficulty": "중",
            })

    # 돌발질문
    if surprise_count > 0:
        surprise_qs = get_random_surprise_questions(surprise_count)
        for q in surprise_qs:
            result.append({
                "question": q,
                "source": "surprise",
                "category": "돌발",
                "difficulty": "상",
            })

    # 섞기
    random.shuffle(result)

    return result


def get_interview_question_set(
    airline: str,
    round_type: str = "1차",  # 1차, 2차, 최종
    version: int = 1,
) -> List[Dict[str, str]]:
    """
    면접 라운드별 질문 세트 생성

    Args:
        airline: 항공사 이름
        round_type: 면접 라운드 (1차/2차/최종)
        version: 버전 번호 (다른 질문 세트 생성)
    """
    # 시드 설정 (같은 버전은 같은 질문)
    seed = hash(f"{airline}_{round_type}_{version}") % (2**32)
    random.seed(seed)

    airline_type = get_airline_type(airline)

    if round_type == "1차":
        # 1차: 공통 + 지원동기 위주
        result = get_mixed_questions(
            airline=airline,
            count=8,
            common_ratio=0.5,
            airline_ratio=0.4,
            surprise_ratio=0.1,
        )
    elif round_type == "2차":
        # 2차: 심층 + 상황대처
        result = get_mixed_questions(
            airline=airline,
            count=10,
            common_ratio=0.3,
            airline_ratio=0.5,
            surprise_ratio=0.2,
        )
    else:  # 최종
        # 최종: 압박 + 돌발 위주
        result = get_mixed_questions(
            airline=airline,
            count=12,
            common_ratio=0.2,
            airline_ratio=0.4,
            surprise_ratio=0.4,
        )

    # 시드 리셋
    random.seed()

    return result


# ===========================================
# 데이터 통계
# ===========================================

def get_data_stats() -> Dict[str, Any]:
    """데이터 통계 반환"""
    common = get_common_questions()
    surprise = get_all_surprise_questions()

    airline_counts = {}
    for airline in AIRLINE_MAP.values():
        questions = get_airline_question_list(airline)
        if questions:
            airline_counts[airline] = len(questions)

    return {
        "common_count": len(common),
        "common_categories": len(get_common_categories()),
        "surprise_count": len(surprise),
        "surprise_categories": len(get_surprise_categories()),
        "airline_questions": airline_counts,
        "total_airline_questions": sum(airline_counts.values()),
        "total_questions": len(common) + len(surprise) + sum(airline_counts.values()),
    }


# ===========================================
# 초기화 및 테스트
# ===========================================

if __name__ == "__main__":
    # 데이터 로드 테스트
    print("=" * 60)
    print("FLYREADY 질문 데이터 로드 테스트")
    print("=" * 60)

    load_all_data()

    stats = get_data_stats()
    print(f"\n[통계]")
    print(f"  - 공통질문: {stats['common_count']}개 ({stats['common_categories']}개 카테고리)")
    print(f"  - 돌발질문: {stats['surprise_count']}개 ({stats['surprise_categories']}개 카테고리)")
    print(f"  - 항공사별 질문: {stats['total_airline_questions']}개")
    print(f"  - 총 질문: {stats['total_questions']}개")

    print("\n[항공사별 질문 수]")
    for airline, count in stats['airline_questions'].items():
        print(f"  - {airline}: {count}개")

    # 혼합 질문 테스트
    print("\n[혼합 질문 테스트 - 제주항공]")
    mixed = get_mixed_questions("제주항공", count=5)
    for i, q in enumerate(mixed, 1):
        print(f"  {i}. [{q['source']}] {q['question'][:50]}...")

    # 면접 세트 테스트
    print("\n[면접 질문 세트 테스트 - 대한항공 1차]")
    interview_set = get_interview_question_set("대한항공", "1차", version=1)
    for i, q in enumerate(interview_set, 1):
        print(f"  {i}. [{q['source']}] {q['question'][:50]}...")

    # 꼬리질문 테스트
    print("\n[FSC 꼬리질문 패턴 샘플]")
    followups = get_random_followup("FSC", 3)
    for f in followups:
        print(f"  - {f}")

    print("\n[LCC 꼬리질문 패턴 샘플]")
    followups = get_random_followup("LCC", 3)
    for f in followups:
        print(f"  - {f}")
