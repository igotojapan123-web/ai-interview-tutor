# db_migration.py
# 데이터베이스 마이그레이션 시스템 (JSON 기반)

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict

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
MIGRATIONS_DIR = DATA_DIR / "migrations"
MIGRATIONS_DIR.mkdir(parents=True, exist_ok=True)

MIGRATION_HISTORY_FILE = MIGRATIONS_DIR / "migration_history.json"


# ============================================================
# 데이터 클래스
# ============================================================

@dataclass
class Migration:
    """마이그레이션 정의"""
    version: str
    name: str
    description: str
    up_func: str  # 함수 이름
    down_func: str  # 롤백 함수 이름
    applied_at: str = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "applied_at": self.applied_at
        }


# ============================================================
# 마이그레이션 관리자
# ============================================================

class MigrationManager:
    """데이터베이스 마이그레이션 관리"""

    def __init__(self):
        self._migrations: Dict[str, Migration] = {}
        self._migration_funcs: Dict[str, Callable] = {}
        self._applied: List[str] = []
        self._load_history()

    def _load_history(self) -> None:
        """마이그레이션 히스토리 로드"""
        try:
            if MIGRATION_HISTORY_FILE.exists():
                with open(MIGRATION_HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._applied = data.get("applied", [])
        except Exception as e:
            logger.error(f"마이그레이션 히스토리 로드 실패: {e}")

    def _save_history(self) -> None:
        """마이그레이션 히스토리 저장"""
        try:
            with open(MIGRATION_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump({"applied": self._applied}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"마이그레이션 히스토리 저장 실패: {e}")

    def register(
        self,
        version: str,
        name: str,
        description: str = ""
    ) -> Callable:
        """마이그레이션 등록 데코레이터"""
        def decorator(func: Callable) -> Callable:
            self._migrations[version] = Migration(
                version=version,
                name=name,
                description=description,
                up_func=func.__name__,
                down_func=f"rollback_{func.__name__}"
            )
            self._migration_funcs[func.__name__] = func
            return func
        return decorator

    def register_rollback(self, version: str) -> Callable:
        """롤백 함수 등록 데코레이터"""
        def decorator(func: Callable) -> Callable:
            self._migration_funcs[f"rollback_{version}"] = func
            return func
        return decorator

    def migrate(self, target_version: str = None) -> List[str]:
        """마이그레이션 실행"""
        applied = []

        # 정렬된 마이그레이션 버전
        versions = sorted(self._migrations.keys())

        for version in versions:
            if version in self._applied:
                continue

            if target_version and version > target_version:
                break

            migration = self._migrations[version]
            func = self._migration_funcs.get(migration.up_func)

            if not func:
                logger.error(f"마이그레이션 함수 없음: {migration.up_func}")
                continue

            try:
                # 백업 생성
                self._create_backup(version)

                # 마이그레이션 실행
                logger.info(f"마이그레이션 실행: {version} - {migration.name}")
                func()

                # 히스토리 업데이트
                migration.applied_at = datetime.now().isoformat()
                self._applied.append(version)
                self._save_history()

                applied.append(version)
                logger.info(f"마이그레이션 완료: {version}")

            except Exception as e:
                logger.error(f"마이그레이션 실패: {version} - {e}")
                self._restore_backup(version)
                raise

        return applied

    def rollback(self, target_version: str) -> List[str]:
        """롤백 실행"""
        rolled_back = []

        # 역순으로 롤백
        versions = sorted(self._applied, reverse=True)

        for version in versions:
            if version <= target_version:
                break

            migration = self._migrations.get(version)
            if not migration:
                continue

            rollback_func = self._migration_funcs.get(f"rollback_{version}")

            if rollback_func:
                try:
                    logger.info(f"롤백 실행: {version}")
                    rollback_func()
                    self._applied.remove(version)
                    rolled_back.append(version)
                except Exception as e:
                    logger.error(f"롤백 실패: {version} - {e}")
                    raise

        self._save_history()
        return rolled_back

    def _create_backup(self, version: str) -> None:
        """데이터 백업"""
        backup_dir = MIGRATIONS_DIR / f"backup_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(exist_ok=True)

        # JSON 파일 백업
        for json_file in DATA_DIR.glob("*.json"):
            shutil.copy(json_file, backup_dir / json_file.name)

        logger.info(f"백업 생성: {backup_dir}")

    def _restore_backup(self, version: str) -> None:
        """백업 복원"""
        # 가장 최근 백업 찾기
        backups = list(MIGRATIONS_DIR.glob(f"backup_{version}_*"))
        if not backups:
            return

        latest_backup = max(backups, key=lambda p: p.stat().st_mtime)

        # 복원
        for json_file in latest_backup.glob("*.json"):
            shutil.copy(json_file, DATA_DIR / json_file.name)

        logger.info(f"백업 복원: {latest_backup}")

    def status(self) -> Dict[str, Any]:
        """마이그레이션 상태"""
        pending = [v for v in sorted(self._migrations.keys()) if v not in self._applied]

        return {
            "applied": self._applied,
            "pending": pending,
            "total": len(self._migrations)
        }


# 전역 인스턴스
migration_manager = MigrationManager()


# ============================================================
# 기본 마이그레이션 등록
# ============================================================

@migration_manager.register("001", "initial_schema", "초기 스키마 설정")
def migration_001():
    """초기 스키마"""
    # 필요한 디렉토리 생성
    dirs = ["analytics", "experiments", "jobs", "backups"]
    for d in dirs:
        (DATA_DIR / d).mkdir(exist_ok=True)


@migration_manager.register("002", "add_user_profiles", "사용자 프로필 필드 추가")
def migration_002():
    """사용자 프로필 필드 추가"""
    profiles_file = DATA_DIR / "analytics" / "user_profiles.json"
    if profiles_file.exists():
        with open(profiles_file, "r", encoding="utf-8") as f:
            profiles = json.load(f)

        # 새 필드 추가
        for user_id, profile in profiles.items():
            if "preferences" not in profile:
                profile["preferences"] = {}
            if "achievements" not in profile:
                profile["achievements"] = []

        with open(profiles_file, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)


@migration_manager.register("003", "add_experiment_metrics", "실험 메트릭 필드 추가")
def migration_003():
    """실험 메트릭 필드"""
    exp_file = DATA_DIR / "experiments" / "experiments.json"
    if exp_file.exists():
        with open(exp_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for exp in data.get("experiments", []):
            if "metrics" not in exp:
                exp["metrics"] = {}

        with open(exp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 간편 함수
# ============================================================

def migrate(target: str = None) -> List[str]:
    """마이그레이션 실행"""
    return migration_manager.migrate(target)


def rollback(target: str) -> List[str]:
    """롤백 실행"""
    return migration_manager.rollback(target)


def status() -> Dict[str, Any]:
    """상태 조회"""
    return migration_manager.status()


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys

    print("=== Database Migration ===")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "migrate":
            target = sys.argv[2] if len(sys.argv) > 2 else None
            applied = migrate(target)
            print(f"적용됨: {applied}")

        elif cmd == "rollback":
            if len(sys.argv) < 3:
                print("롤백 대상 버전 필요")
            else:
                rolled = rollback(sys.argv[2])
                print(f"롤백됨: {rolled}")

        elif cmd == "status":
            s = status()
            print(f"적용됨: {s['applied']}")
            print(f"대기중: {s['pending']}")

    else:
        print("사용법:")
        print("  python db_migration.py migrate [version]")
        print("  python db_migration.py rollback <version>")
        print("  python db_migration.py status")

    print("\nReady!")
