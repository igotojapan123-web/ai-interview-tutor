# data_export.py
# 사용자 데이터 내보내기 시스템 (CSV/PDF)

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO, StringIO

try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ============================================================
# 설정
# ============================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CSV 내보내기
# ============================================================

def export_to_csv(
    data: List[Dict[str, Any]],
    filename: str = None,
    columns: List[str] = None
) -> Optional[Path]:
    """
    데이터를 CSV 파일로 내보내기

    Args:
        data: 내보낼 데이터 (딕셔너리 리스트)
        filename: 파일 이름 (없으면 자동 생성)
        columns: 포함할 컬럼 (없으면 전체)

    Returns:
        저장된 파일 경로
    """
    if not data:
        logger.warning("내보낼 데이터가 없습니다")
        return None

    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.csv"

        filepath = EXPORT_DIR / filename

        # 컬럼 결정
        if columns:
            fieldnames = columns
        else:
            fieldnames = list(data[0].keys())

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"CSV 내보내기 완료: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"CSV 내보내기 실패: {e}")
        return None


def export_to_csv_bytes(
    data: List[Dict[str, Any]],
    columns: List[str] = None
) -> Optional[bytes]:
    """
    데이터를 CSV 바이트로 내보내기 (다운로드용)

    Args:
        data: 내보낼 데이터
        columns: 포함할 컬럼

    Returns:
        CSV 바이트 데이터
    """
    if not data:
        return None

    try:
        output = StringIO()

        if columns:
            fieldnames = columns
        else:
            fieldnames = list(data[0].keys())

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

        return output.getvalue().encode('utf-8-sig')

    except Exception as e:
        logger.error(f"CSV 바이트 내보내기 실패: {e}")
        return None


# ============================================================
# JSON 내보내기
# ============================================================

def export_to_json(
    data: Any,
    filename: str = None,
    pretty: bool = True
) -> Optional[Path]:
    """
    데이터를 JSON 파일로 내보내기

    Args:
        data: 내보낼 데이터
        filename: 파일 이름
        pretty: 들여쓰기 적용 여부

    Returns:
        저장된 파일 경로
    """
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.json"

        filepath = EXPORT_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            else:
                json.dump(data, f, ensure_ascii=False, default=str)

        logger.info(f"JSON 내보내기 완료: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"JSON 내보내기 실패: {e}")
        return None


def export_to_json_bytes(data: Any, pretty: bool = True) -> Optional[bytes]:
    """데이터를 JSON 바이트로 내보내기"""
    try:
        if pretty:
            return json.dumps(data, ensure_ascii=False, indent=2, default=str).encode('utf-8')
        else:
            return json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
    except Exception as e:
        logger.error(f"JSON 바이트 내보내기 실패: {e}")
        return None


# ============================================================
# 연습 기록 내보내기
# ============================================================

def export_practice_history(
    user_id: str = None,
    practice_type: str = None,
    start_date: datetime = None,
    end_date: datetime = None,
    format: str = "csv"
) -> Optional[bytes]:
    """
    연습 기록 내보내기

    Args:
        user_id: 사용자 ID (없으면 전체)
        practice_type: 연습 유형 (mock_interview, debate, roleplay 등)
        start_date: 시작 날짜
        end_date: 종료 날짜
        format: 출력 형식 (csv, json)

    Returns:
        내보내기 데이터 (바이트)
    """
    try:
        # 점수 데이터 로드
        score_file = DATA_DIR / "practice_scores.json"
        if not score_file.exists():
            logger.warning("연습 기록 파일이 없습니다")
            return None

        with open(score_file, 'r', encoding='utf-8') as f:
            all_scores = json.load(f)

        # 필터링
        filtered = all_scores

        if user_id:
            filtered = [s for s in filtered if s.get('user_id') == user_id]

        if practice_type:
            filtered = [s for s in filtered if s.get('practice_type') == practice_type]

        if start_date:
            filtered = [s for s in filtered
                       if datetime.fromisoformat(s.get('timestamp', '2000-01-01')) >= start_date]

        if end_date:
            filtered = [s for s in filtered
                       if datetime.fromisoformat(s.get('timestamp', '2099-12-31')) <= end_date]

        # 내보내기
        if format == "csv":
            columns = ['timestamp', 'practice_type', 'score', 'airline', 'feedback']
            return export_to_csv_bytes(filtered, columns)
        else:
            return export_to_json_bytes(filtered)

    except Exception as e:
        logger.error(f"연습 기록 내보내기 실패: {e}")
        return None


def export_user_summary(user_id: str) -> Optional[Dict[str, Any]]:
    """
    사용자 요약 데이터 내보내기

    Args:
        user_id: 사용자 ID

    Returns:
        요약 데이터 딕셔너리
    """
    try:
        summary = {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "practice_count": 0,
            "average_score": 0,
            "practice_types": {},
            "recent_practices": [],
            "score_trend": []
        }

        # 점수 데이터 로드
        score_file = DATA_DIR / "practice_scores.json"
        if score_file.exists():
            with open(score_file, 'r', encoding='utf-8') as f:
                all_scores = json.load(f)

            user_scores = [s for s in all_scores if s.get('user_id') == user_id]

            if user_scores:
                summary["practice_count"] = len(user_scores)

                scores = [s.get('score', 0) for s in user_scores if s.get('score')]
                if scores:
                    summary["average_score"] = sum(scores) / len(scores)

                # 연습 유형별 카운트
                for score in user_scores:
                    ptype = score.get('practice_type', 'unknown')
                    summary["practice_types"][ptype] = summary["practice_types"].get(ptype, 0) + 1

                # 최근 연습 (5개)
                sorted_scores = sorted(user_scores, key=lambda x: x.get('timestamp', ''), reverse=True)
                summary["recent_practices"] = sorted_scores[:5]

                # 점수 추이 (최근 10개)
                for s in sorted_scores[:10]:
                    summary["score_trend"].append({
                        "date": s.get('timestamp', '')[:10],
                        "score": s.get('score', 0),
                        "type": s.get('practice_type', '')
                    })

        return summary

    except Exception as e:
        logger.error(f"사용자 요약 내보내기 실패: {e}")
        return None


# ============================================================
# Streamlit 다운로드 헬퍼
# ============================================================

def get_download_button_data(
    data: Any,
    filename: str,
    format: str = "csv"
) -> tuple:
    """
    Streamlit 다운로드 버튼용 데이터 준비

    Args:
        data: 내보낼 데이터
        filename: 파일 이름
        format: 형식 (csv, json)

    Returns:
        (바이트 데이터, MIME 타입, 파일 이름)
    """
    if format == "csv":
        if isinstance(data, list):
            bytes_data = export_to_csv_bytes(data)
        else:
            bytes_data = export_to_csv_bytes([data])
        mime = "text/csv"
        if not filename.endswith('.csv'):
            filename += '.csv'
    else:
        bytes_data = export_to_json_bytes(data)
        mime = "application/json"
        if not filename.endswith('.json'):
            filename += '.json'

    return bytes_data, mime, filename


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=== Data Export System ===")
    print(f"Export directory: {EXPORT_DIR}")
    print("\nFunctions available:")
    print("  - export_to_csv(data, filename)")
    print("  - export_to_json(data, filename)")
    print("  - export_practice_history(user_id, format)")
    print("  - export_user_summary(user_id)")
    print("  - get_download_button_data(data, filename, format)")
    print("\nReady!")
