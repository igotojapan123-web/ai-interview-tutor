# backup_system.py
# FlyReady Lab - Enterprise Backup & Recovery System
# Stage 5: Samsung-level data protection

import os
import json
import shutil
import gzip
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# Constants
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
BACKUP_DIR = PROJECT_ROOT / "backups"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure backup directory exists
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Backup Types
# =============================================================================

class BackupType(Enum):
    """Backup types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DATA_ONLY = "data_only"
    LOGS_ONLY = "logs_only"
    CONFIG_ONLY = "config_only"


class BackupStatus(Enum):
    """Backup status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


# =============================================================================
# Backup Metadata
# =============================================================================

@dataclass
class BackupMetadata:
    """Backup metadata"""
    id: str
    backup_type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    size_bytes: int = 0
    file_count: int = 0
    checksum: str = ""
    source_paths: List[str] = field(default_factory=list)
    backup_path: str = ""
    error_message: str = ""
    compression: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "backup_type": self.backup_type.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "size_bytes": self.size_bytes,
            "size_formatted": self._format_size(self.size_bytes),
            "file_count": self.file_count,
            "checksum": self.checksum,
            "source_paths": self.source_paths,
            "backup_path": self.backup_path,
            "error_message": self.error_message,
            "compression": self.compression
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        return cls(
            id=data["id"],
            backup_type=BackupType(data["backup_type"]),
            status=BackupStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            size_bytes=data.get("size_bytes", 0),
            file_count=data.get("file_count", 0),
            checksum=data.get("checksum", ""),
            source_paths=data.get("source_paths", []),
            backup_path=data.get("backup_path", ""),
            error_message=data.get("error_message", ""),
            compression=data.get("compression", True)
        )


# =============================================================================
# Backup System
# =============================================================================

class BackupSystem:
    """Enterprise backup and recovery system"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._backup_history: List[BackupMetadata] = []
        self._metadata_file = BACKUP_DIR / "backup_metadata.json"
        self._backup_in_progress = False
        self._callbacks: List[Callable[[BackupMetadata], None]] = []

        # Load existing metadata
        self._load_metadata()

        logger.info("BackupSystem initialized")

    def _load_metadata(self):
        """Load backup metadata from file"""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._backup_history = [BackupMetadata.from_dict(b) for b in data]
        except Exception as e:
            logger.error(f"Failed to load backup metadata: {e}")
            self._backup_history = []

    def _save_metadata(self):
        """Save backup metadata to file"""
        try:
            with open(self._metadata_file, "w", encoding="utf-8") as f:
                json.dump([b.to_dict() for b in self._backup_history], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")

    def _generate_backup_id(self) -> str:
        """Generate unique backup ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{timestamp}"

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def add_callback(self, callback: Callable[[BackupMetadata], None]):
        """Add callback for backup completion"""
        self._callbacks.append(callback)

    # -------------------------------------------------------------------------
    # Backup Operations
    # -------------------------------------------------------------------------

    def create_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        compress: bool = True,
        async_mode: bool = False
    ) -> BackupMetadata:
        """
        Create a new backup.

        Args:
            backup_type: Type of backup to create
            compress: Whether to compress the backup
            async_mode: Run backup in background thread

        Returns:
            BackupMetadata for the created backup
        """
        if self._backup_in_progress:
            raise RuntimeError("Backup already in progress")

        backup_id = self._generate_backup_id()
        metadata = BackupMetadata(
            id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            created_at=datetime.now(),
            compression=compress
        )

        self._backup_history.append(metadata)

        if async_mode:
            thread = threading.Thread(
                target=self._execute_backup,
                args=(metadata,),
                daemon=True
            )
            thread.start()
            return metadata
        else:
            return self._execute_backup(metadata)

    def _execute_backup(self, metadata: BackupMetadata) -> BackupMetadata:
        """Execute the backup operation"""
        self._backup_in_progress = True
        metadata.status = BackupStatus.IN_PROGRESS

        try:
            # Determine source paths based on backup type
            source_paths = self._get_source_paths(metadata.backup_type)
            metadata.source_paths = [str(p) for p in source_paths]

            # Create backup directory
            backup_name = f"{metadata.id}_{metadata.backup_type.value}"
            backup_path = BACKUP_DIR / backup_name

            if metadata.compression:
                backup_path = backup_path.with_suffix(".tar.gz")
                self._create_compressed_backup(source_paths, backup_path)
            else:
                backup_path.mkdir(parents=True, exist_ok=True)
                self._create_uncompressed_backup(source_paths, backup_path)

            # Update metadata
            metadata.backup_path = str(backup_path)
            metadata.size_bytes = self._get_path_size(backup_path)
            metadata.file_count = self._count_files(source_paths)
            metadata.checksum = self._calculate_checksum(backup_path) if backup_path.is_file() else ""
            metadata.status = BackupStatus.COMPLETED
            metadata.completed_at = datetime.now()

            logger.info(f"Backup completed: {metadata.id} ({metadata.size_bytes} bytes)")

        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            logger.error(f"Backup failed: {metadata.id} - {e}")

        finally:
            self._backup_in_progress = False
            self._save_metadata()

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(metadata)
                except Exception as e:
                    logger.error(f"Callback error: {e}")

        return metadata

    def _get_source_paths(self, backup_type: BackupType) -> List[Path]:
        """Get source paths for backup type"""
        paths = []

        if backup_type == BackupType.FULL:
            paths = [DATA_DIR, LOGS_DIR]
            # Add config files
            for config_file in ["env_config.py", "config.py", ".env"]:
                config_path = PROJECT_ROOT / config_file
                if config_path.exists():
                    paths.append(config_path)

        elif backup_type == BackupType.DATA_ONLY:
            paths = [DATA_DIR]

        elif backup_type == BackupType.LOGS_ONLY:
            paths = [LOGS_DIR]

        elif backup_type == BackupType.CONFIG_ONLY:
            for config_file in ["env_config.py", "config.py", ".env", "constants.py"]:
                config_path = PROJECT_ROOT / config_file
                if config_path.exists():
                    paths.append(config_path)

        return [p for p in paths if p.exists()]

    def _create_compressed_backup(self, source_paths: List[Path], dest_path: Path):
        """Create compressed tar.gz backup"""
        import tarfile

        with tarfile.open(dest_path, "w:gz") as tar:
            for path in source_paths:
                arcname = path.name
                tar.add(path, arcname=arcname)

    def _create_uncompressed_backup(self, source_paths: List[Path], dest_path: Path):
        """Create uncompressed backup"""
        for path in source_paths:
            dest = dest_path / path.name
            if path.is_dir():
                shutil.copytree(path, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(path, dest)

    def _get_path_size(self, path: Path) -> int:
        """Get total size of path"""
        if path.is_file():
            return path.stat().st_size

        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
        return total

    def _count_files(self, paths: List[Path]) -> int:
        """Count total files in paths"""
        count = 0
        for path in paths:
            if path.is_file():
                count += 1
            elif path.is_dir():
                count += len(list(path.rglob("*")))
        return count

    # -------------------------------------------------------------------------
    # Recovery Operations
    # -------------------------------------------------------------------------

    def restore_backup(self, backup_id: str, target_path: Path = None) -> bool:
        """
        Restore from a backup.

        Args:
            backup_id: ID of the backup to restore
            target_path: Target path for restoration (default: original locations)

        Returns:
            True if restoration was successful
        """
        metadata = self.get_backup(backup_id)
        if not metadata:
            logger.error(f"Backup not found: {backup_id}")
            return False

        if metadata.status != BackupStatus.COMPLETED:
            logger.error(f"Cannot restore incomplete backup: {backup_id}")
            return False

        backup_path = Path(metadata.backup_path)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        try:
            if target_path is None:
                target_path = PROJECT_ROOT

            if metadata.compression:
                self._restore_compressed_backup(backup_path, target_path)
            else:
                self._restore_uncompressed_backup(backup_path, target_path)

            logger.info(f"Backup restored: {backup_id} to {target_path}")
            return True

        except Exception as e:
            logger.error(f"Restore failed: {backup_id} - {e}")
            return False

    def _restore_compressed_backup(self, backup_path: Path, target_path: Path):
        """Restore from compressed backup"""
        import tarfile

        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(path=target_path)

    def _restore_uncompressed_backup(self, backup_path: Path, target_path: Path):
        """Restore from uncompressed backup"""
        for item in backup_path.iterdir():
            dest = target_path / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity.

        Args:
            backup_id: ID of the backup to verify

        Returns:
            True if backup is valid
        """
        metadata = self.get_backup(backup_id)
        if not metadata:
            return False

        backup_path = Path(metadata.backup_path)
        if not backup_path.exists():
            return False

        # Verify checksum
        if metadata.checksum and backup_path.is_file():
            current_checksum = self._calculate_checksum(backup_path)
            if current_checksum != metadata.checksum:
                logger.error(f"Checksum mismatch for backup: {backup_id}")
                return False

        # Verify size
        current_size = self._get_path_size(backup_path)
        if current_size != metadata.size_bytes:
            logger.warning(f"Size mismatch for backup: {backup_id}")

        metadata.status = BackupStatus.VERIFIED
        self._save_metadata()

        logger.info(f"Backup verified: {backup_id}")
        return True

    # -------------------------------------------------------------------------
    # Query Operations
    # -------------------------------------------------------------------------

    def get_backup(self, backup_id: str) -> Optional[BackupMetadata]:
        """Get backup by ID"""
        for backup in self._backup_history:
            if backup.id == backup_id:
                return backup
        return None

    def list_backups(
        self,
        backup_type: BackupType = None,
        status: BackupStatus = None,
        limit: int = 20
    ) -> List[BackupMetadata]:
        """
        List backups with optional filtering.

        Args:
            backup_type: Filter by backup type
            status: Filter by status
            limit: Maximum number of backups to return

        Returns:
            List of BackupMetadata
        """
        backups = self._backup_history.copy()

        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]

        if status:
            backups = [b for b in backups if b.status == status]

        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.created_at, reverse=True)

        return backups[:limit]

    def get_latest_backup(self, backup_type: BackupType = None) -> Optional[BackupMetadata]:
        """Get the most recent successful backup"""
        backups = self.list_backups(backup_type=backup_type, status=BackupStatus.COMPLETED, limit=1)
        return backups[0] if backups else None

    # -------------------------------------------------------------------------
    # Cleanup Operations
    # -------------------------------------------------------------------------

    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10) -> int:
        """
        Remove old backups.

        Args:
            keep_days: Keep backups newer than this many days
            keep_count: Always keep at least this many backups

        Returns:
            Number of backups deleted
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0

        # Sort by date (oldest first)
        backups = sorted(self._backup_history, key=lambda b: b.created_at)

        # Keep at least keep_count backups
        if len(backups) <= keep_count:
            return 0

        for backup in backups[:-keep_count]:
            if backup.created_at < cutoff_date:
                if self._delete_backup(backup):
                    deleted_count += 1

        return deleted_count

    def _delete_backup(self, metadata: BackupMetadata) -> bool:
        """Delete a backup"""
        try:
            backup_path = Path(metadata.backup_path)
            if backup_path.exists():
                if backup_path.is_file():
                    backup_path.unlink()
                else:
                    shutil.rmtree(backup_path)

            self._backup_history.remove(metadata)
            self._save_metadata()

            logger.info(f"Deleted backup: {metadata.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete backup: {metadata.id} - {e}")
            return False

    def get_storage_usage(self) -> Dict[str, Any]:
        """Get backup storage usage statistics"""
        total_size = 0
        completed_count = 0
        failed_count = 0

        for backup in self._backup_history:
            total_size += backup.size_bytes
            if backup.status == BackupStatus.COMPLETED:
                completed_count += 1
            elif backup.status == BackupStatus.FAILED:
                failed_count += 1

        return {
            "total_backups": len(self._backup_history),
            "completed_count": completed_count,
            "failed_count": failed_count,
            "total_size_bytes": total_size,
            "total_size_formatted": BackupMetadata._format_size(total_size),
            "backup_directory": str(BACKUP_DIR)
        }


# =============================================================================
# Global Instance
# =============================================================================

_backup_system = BackupSystem()


def get_backup_system() -> BackupSystem:
    """Get backup system instance"""
    return _backup_system


# =============================================================================
# Convenience Functions
# =============================================================================

def create_backup(backup_type: BackupType = BackupType.FULL, compress: bool = True) -> BackupMetadata:
    """Create a new backup"""
    return _backup_system.create_backup(backup_type, compress)


def restore_backup(backup_id: str, target_path: Path = None) -> bool:
    """Restore from backup"""
    return _backup_system.restore_backup(backup_id, target_path)


def list_backups(limit: int = 20) -> List[BackupMetadata]:
    """List recent backups"""
    return _backup_system.list_backups(limit=limit)


def get_latest_backup() -> Optional[BackupMetadata]:
    """Get most recent successful backup"""
    return _backup_system.get_latest_backup()


def cleanup_backups(keep_days: int = 30) -> int:
    """Clean up old backups"""
    return _backup_system.cleanup_old_backups(keep_days)
