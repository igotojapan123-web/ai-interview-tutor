# data_cleanup.py
# 오래된 로그/세션/임시 파일 자동 정리 시스템

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import threading
import json

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
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
EXPORTS_DIR = BASE_DIR / "exports"

# 기본 보관 기간 (일)
DEFAULT_RETENTION = {
    "logs": 30,           # 로그 파일
    "temp": 1,            # 임시 파일
    "exports": 7,         # 내보내기 파일
    "errors": 90,         # 에러 로그
    "sessions": 7,        # 세션 데이터
    "backups": 30,        # 백업 파일
}

# 정리 대상 패턴
CLEANUP_PATTERNS = {
    "logs": ["*.log", "*.log.*"],
    "temp": ["*.tmp", "*.temp", "temp_*"],
    "exports": ["export_*.csv", "export_*.json"],
    "cache": ["*.cache", "__pycache__"],
}


# ============================================================
# 데이터 정리 클래스
# ============================================================

class DataCleanup:
    """데이터 정리 관리 클래스"""

    def __init__(self, retention_days: Dict[str, int] = None):
        self.retention = retention_days or DEFAULT_RETENTION
        self._cleanup_stats = {
            "last_cleanup": None,
            "files_deleted": 0,
            "bytes_freed": 0
        }

    def cleanup_old_logs(self, days: int = None) -> Dict[str, Any]:
        """
        오래된 로그 파일 정리

        Args:
            days: 보관 일수 (기본: retention 설정)

        Returns:
            정리 결과 통계
        """
        days = days or self.retention.get("logs", 30)
        cutoff = datetime.now() - timedelta(days=days)

        stats = {"deleted": 0, "bytes_freed": 0, "errors": []}

        if not LOGS_DIR.exists():
            return stats

        try:
            for pattern in CLEANUP_PATTERNS.get("logs", ["*.log"]):
                for log_file in LOGS_DIR.glob(pattern):
                    try:
                        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if mtime < cutoff:
                            size = log_file.stat().st_size
                            log_file.unlink()
                            stats["deleted"] += 1
                            stats["bytes_freed"] += size
                            logger.debug(f"삭제됨: {log_file.name}")
                    except Exception as e:
                        stats["errors"].append(str(e))

            logger.info(f"로그 정리 완료: {stats['deleted']}개 파일, {stats['bytes_freed']/1024:.1f}KB 확보")

        except Exception as e:
            logger.error(f"로그 정리 실패: {e}")
            stats["errors"].append(str(e))

        return stats

    def cleanup_temp_files(self, days: int = None) -> Dict[str, Any]:
        """임시 파일 정리"""
        days = days or self.retention.get("temp", 1)
        cutoff = datetime.now() - timedelta(days=days)

        stats = {"deleted": 0, "bytes_freed": 0, "errors": []}

        # temp 디렉토리
        if TEMP_DIR.exists():
            for item in TEMP_DIR.iterdir():
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < cutoff:
                        if item.is_file():
                            size = item.stat().st_size
                            item.unlink()
                        else:
                            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                            shutil.rmtree(item)
                        stats["deleted"] += 1
                        stats["bytes_freed"] += size
                except Exception as e:
                    stats["errors"].append(str(e))

        # __pycache__ 정리
        for cache_dir in BASE_DIR.rglob("__pycache__"):
            try:
                shutil.rmtree(cache_dir)
                stats["deleted"] += 1
                logger.debug(f"캐시 삭제: {cache_dir}")
            except:
                pass

        logger.info(f"임시 파일 정리 완료: {stats['deleted']}개")
        return stats

    def cleanup_old_exports(self, days: int = None) -> Dict[str, Any]:
        """오래된 내보내기 파일 정리"""
        days = days or self.retention.get("exports", 7)
        cutoff = datetime.now() - timedelta(days=days)

        stats = {"deleted": 0, "bytes_freed": 0, "errors": []}

        if not EXPORTS_DIR.exists():
            return stats

        for pattern in CLEANUP_PATTERNS.get("exports", []):
            for export_file in EXPORTS_DIR.glob(pattern):
                try:
                    mtime = datetime.fromtimestamp(export_file.stat().st_mtime)
                    if mtime < cutoff:
                        size = export_file.stat().st_size
                        export_file.unlink()
                        stats["deleted"] += 1
                        stats["bytes_freed"] += size
                except Exception as e:
                    stats["errors"].append(str(e))

        logger.info(f"내보내기 파일 정리 완료: {stats['deleted']}개")
        return stats

    def cleanup_error_logs(self, days: int = None) -> Dict[str, Any]:
        """오래된 에러 로그 정리"""
        days = days or self.retention.get("errors", 90)
        cutoff = datetime.now() - timedelta(days=days)

        stats = {"deleted": 0, "bytes_freed": 0}

        error_dir = DATA_DIR / "errors"
        if not error_dir.exists():
            return stats

        for error_file in error_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(error_file.stat().st_mtime)
                if mtime < cutoff:
                    size = error_file.stat().st_size
                    error_file.unlink()
                    stats["deleted"] += 1
                    stats["bytes_freed"] += size
            except:
                pass

        logger.info(f"에러 로그 정리 완료: {stats['deleted']}개")
        return stats

    def cleanup_old_sessions(self, days: int = None) -> Dict[str, Any]:
        """오래된 세션 데이터 정리"""
        days = days or self.retention.get("sessions", 7)
        cutoff = datetime.now() - timedelta(days=days)

        stats = {"deleted": 0, "cleaned_entries": 0}

        # 세션 관련 JSON 파일 정리
        session_files = [
            DATA_DIR / "room_messages.json",
            DATA_DIR / "rooms.json",
        ]

        for session_file in session_files:
            if session_file.exists():
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    original_count = len(data) if isinstance(data, list) else len(data.keys())

                    # 오래된 항목 필터링
                    if isinstance(data, list):
                        data = [item for item in data
                               if datetime.fromisoformat(item.get('timestamp', item.get('created_at', '2099-12-31'))[:19]) > cutoff]
                    elif isinstance(data, dict):
                        data = {k: v for k, v in data.items()
                               if datetime.fromisoformat(v.get('timestamp', v.get('created_at', '2099-12-31'))[:19]) > cutoff}

                    new_count = len(data) if isinstance(data, list) else len(data.keys())
                    cleaned = original_count - new_count

                    if cleaned > 0:
                        with open(session_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        stats["cleaned_entries"] += cleaned

                except Exception as e:
                    logger.error(f"세션 정리 실패 ({session_file}): {e}")

        logger.info(f"세션 데이터 정리 완료: {stats['cleaned_entries']}개 항목")
        return stats

    def run_full_cleanup(self) -> Dict[str, Any]:
        """전체 정리 실행"""
        logger.info("전체 데이터 정리 시작...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "logs": self.cleanup_old_logs(),
            "temp": self.cleanup_temp_files(),
            "exports": self.cleanup_old_exports(),
            "errors": self.cleanup_error_logs(),
            "sessions": self.cleanup_old_sessions()
        }

        # 총계 계산
        total_deleted = sum(r.get("deleted", 0) for r in results.values() if isinstance(r, dict))
        total_bytes = sum(r.get("bytes_freed", 0) for r in results.values() if isinstance(r, dict))

        results["summary"] = {
            "total_files_deleted": total_deleted,
            "total_bytes_freed": total_bytes,
            "total_mb_freed": total_bytes / (1024 * 1024)
        }

        self._cleanup_stats = {
            "last_cleanup": datetime.now().isoformat(),
            "files_deleted": total_deleted,
            "bytes_freed": total_bytes
        }

        logger.info(f"전체 정리 완료: {total_deleted}개 파일, {total_bytes/1024/1024:.2f}MB 확보")

        return results

    def get_storage_stats(self) -> Dict[str, Any]:
        """스토리지 사용량 통계"""
        stats = {}

        directories = {
            "data": DATA_DIR,
            "logs": LOGS_DIR,
            "exports": EXPORTS_DIR,
            "temp": TEMP_DIR
        }

        for name, path in directories.items():
            if path.exists():
                total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                file_count = len(list(path.rglob('*')))
                stats[name] = {
                    "size_bytes": total_size,
                    "size_mb": total_size / (1024 * 1024),
                    "file_count": file_count
                }
            else:
                stats[name] = {"size_bytes": 0, "size_mb": 0, "file_count": 0}

        stats["total_mb"] = sum(s.get("size_mb", 0) for s in stats.values())
        stats["last_cleanup"] = self._cleanup_stats.get("last_cleanup")

        return stats


# 전역 인스턴스
data_cleanup = DataCleanup()


# ============================================================
# 자동 정리 스케줄러
# ============================================================

_cleanup_running = False
_cleanup_thread = None


def start_auto_cleanup(cleanup_time: str = "04:00") -> None:
    """
    자동 정리 스케줄러 시작

    Args:
        cleanup_time: 정리 실행 시각 (HH:MM)
    """
    global _cleanup_running, _cleanup_thread

    if _cleanup_running:
        logger.warning("자동 정리가 이미 실행 중")
        return

    try:
        import schedule
    except ImportError:
        logger.warning("schedule 모듈 없음 - pip install schedule 필요")
        return

    def run_scheduler():
        global _cleanup_running
        import time

        _cleanup_running = True

        schedule.every().day.at(cleanup_time).do(data_cleanup.run_full_cleanup)

        logger.info(f"자동 정리 스케줄러 시작: 매일 {cleanup_time}")

        while _cleanup_running:
            schedule.run_pending()
            time.sleep(60)

    _cleanup_thread = threading.Thread(target=run_scheduler, daemon=True)
    _cleanup_thread.start()


def stop_auto_cleanup() -> None:
    """자동 정리 스케줄러 중지"""
    global _cleanup_running
    _cleanup_running = False
    logger.info("자동 정리 스케줄러 중지")


# ============================================================
# 간편 함수
# ============================================================

def cleanup_all() -> Dict[str, Any]:
    """전체 정리 실행"""
    return data_cleanup.run_full_cleanup()


def get_storage_stats() -> Dict[str, Any]:
    """스토리지 통계 조회"""
    return data_cleanup.get_storage_stats()


# ============================================================
# CLI 인터페이스
# ============================================================

if __name__ == "__main__":
    import sys

    print("=== Data Cleanup System ===")

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "all":
            results = cleanup_all()
            print(f"\n정리 완료:")
            print(f"  - 삭제된 파일: {results['summary']['total_files_deleted']}개")
            print(f"  - 확보된 공간: {results['summary']['total_mb_freed']:.2f}MB")

        elif command == "stats":
            stats = get_storage_stats()
            print(f"\n스토리지 사용량:")
            for name, info in stats.items():
                if isinstance(info, dict) and "size_mb" in info:
                    print(f"  - {name}: {info['size_mb']:.2f}MB ({info['file_count']}개 파일)")
            print(f"\n총 사용량: {stats.get('total_mb', 0):.2f}MB")

        elif command == "logs":
            result = data_cleanup.cleanup_old_logs()
            print(f"로그 정리: {result['deleted']}개 삭제")

        elif command == "temp":
            result = data_cleanup.cleanup_temp_files()
            print(f"임시 파일 정리: {result['deleted']}개 삭제")

        else:
            print(f"알 수 없는 명령: {command}")
    else:
        print("\n사용법:")
        print("  python data_cleanup.py all    - 전체 정리")
        print("  python data_cleanup.py stats  - 스토리지 통계")
        print("  python data_cleanup.py logs   - 로그만 정리")
        print("  python data_cleanup.py temp   - 임시파일만 정리")
