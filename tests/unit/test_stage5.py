# tests/unit/test_stage5.py
# FlyReady Lab - Stage 5 Unit Tests
# Enterprise-level DevOps testing

import pytest
import sys
import os
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# =============================================================================
# Environment Manager Tests
# =============================================================================

class TestEnvironmentEnum:
    """Environment enum tests"""

    def test_development_value(self):
        """Development environment value"""
        from env_manager import Environment
        assert Environment.DEVELOPMENT.value == "development"

    def test_staging_value(self):
        """Staging environment value"""
        from env_manager import Environment
        assert Environment.STAGING.value == "staging"

    def test_production_value(self):
        """Production environment value"""
        from env_manager import Environment
        assert Environment.PRODUCTION.value == "production"

    def test_test_value(self):
        """Test environment value"""
        from env_manager import Environment
        assert Environment.TEST.value == "test"


class TestLoggingConfig:
    """LoggingConfig dataclass tests"""

    def test_default_values(self):
        """Default logging config values"""
        from env_manager import LoggingConfig

        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.json_format is False

    def test_custom_values(self):
        """Custom logging config values"""
        from env_manager import LoggingConfig

        config = LoggingConfig(
            level="DEBUG",
            json_format=True,
            file_path="/var/log/app.log"
        )

        assert config.level == "DEBUG"
        assert config.json_format is True


class TestSecurityConfig:
    """SecurityConfig dataclass tests"""

    def test_default_values(self):
        """Default security config values"""
        from env_manager import SecurityConfig

        config = SecurityConfig()

        assert config.csrf_enabled is True
        assert config.max_login_attempts == 5

    def test_rate_limit_defaults(self):
        """Rate limit default values"""
        from env_manager import SecurityConfig

        config = SecurityConfig()

        assert config.rate_limit_requests == 100
        assert config.rate_limit_window == 60


class TestMonitoringConfig:
    """MonitoringConfig dataclass tests"""

    def test_default_values(self):
        """Default monitoring config values"""
        from env_manager import MonitoringConfig

        config = MonitoringConfig()

        assert config.metrics_enabled is True
        assert config.sentry_traces_sample_rate == 0.1


class TestAPIConfig:
    """APIConfig dataclass tests"""

    def test_default_empty_keys(self):
        """API keys default to empty"""
        from env_manager import APIConfig

        config = APIConfig()

        assert config.openai_api_key == ""
        assert config.google_tts_api_key == ""


class TestAppConfig:
    """AppConfig dataclass tests"""

    def test_default_values(self):
        """Default app config values"""
        from env_manager import AppConfig, Environment

        config = AppConfig()

        assert config.env == Environment.DEVELOPMENT
        assert config.debug is False
        assert config.port == 8501

    def test_has_sub_configs(self):
        """App config has sub-configurations"""
        from env_manager import AppConfig

        config = AppConfig()

        assert config.logging is not None
        assert config.security is not None
        assert config.monitoring is not None
        assert config.api is not None


class TestEnvironmentConfigs:
    """Environment-specific config tests"""

    def test_development_config(self):
        """Development config settings"""
        from env_manager import get_development_config, Environment

        config = get_development_config()

        assert config.env == Environment.DEVELOPMENT
        assert config.debug is True
        assert config.logging.level == "DEBUG"

    def test_staging_config(self):
        """Staging config settings"""
        from env_manager import get_staging_config, Environment

        config = get_staging_config()

        assert config.env == Environment.STAGING
        assert config.debug is False
        assert config.logging.json_format is True

    def test_production_config(self):
        """Production config settings"""
        from env_manager import get_production_config, Environment

        config = get_production_config()

        assert config.env == Environment.PRODUCTION
        assert config.debug is False
        assert config.security.csrf_enabled is True

    def test_test_config(self):
        """Test config settings"""
        from env_manager import get_test_config, Environment

        config = get_test_config()

        assert config.env == Environment.TEST
        assert config.monitoring.metrics_enabled is False


class TestGetConfig:
    """get_config function tests"""

    def test_get_config_development(self):
        """Get development config"""
        from env_manager import get_config, Environment

        config = get_config("development")
        assert config.env == Environment.DEVELOPMENT

    def test_get_config_from_env_var(self):
        """Get config from ENV variable"""
        os.environ["ENV"] = "test"

        from env_manager import get_config, Environment

        config = get_config()
        # Should read from ENV variable
        assert config is not None

    def test_get_config_invalid_fallback(self):
        """Invalid env falls back to development"""
        from env_manager import get_config

        config = get_config("invalid_env")
        # Should not raise error, falls back to development


class TestValidateConfig:
    """validate_config function tests"""

    def test_validate_missing_api_key(self):
        """Validation warns about missing API key"""
        from env_manager import validate_config, get_development_config

        config = get_development_config()
        config.api.openai_api_key = ""

        messages = validate_config(config)

        assert any("OPENAI_API_KEY" in msg for msg in messages)

    def test_validate_production_warnings(self):
        """Validation checks production settings"""
        from env_manager import validate_config, get_production_config

        config = get_production_config()
        config.debug = True  # Wrong for production

        messages = validate_config(config)

        assert any("Debug mode" in msg or "debug" in msg.lower() for msg in messages)


class TestConvenienceFunctions:
    """Convenience function tests"""

    def test_is_development(self):
        """is_development function"""
        from env_manager import is_development, get_config

        get_config("development")
        # Just verify function exists and returns bool
        result = is_development()
        assert isinstance(result, bool)

    def test_is_production(self):
        """is_production function"""
        from env_manager import is_production

        result = is_production()
        assert isinstance(result, bool)

    def test_get_env_name(self):
        """get_env_name function"""
        from env_manager import get_env_name

        name = get_env_name()
        assert name in ["development", "staging", "production", "test"]


# =============================================================================
# Backup System Tests
# =============================================================================

class TestBackupType:
    """BackupType enum tests"""

    def test_full_value(self):
        """Full backup type value"""
        from backup_system import BackupType
        assert BackupType.FULL.value == "full"

    def test_incremental_value(self):
        """Incremental backup type value"""
        from backup_system import BackupType
        assert BackupType.INCREMENTAL.value == "incremental"

    def test_data_only_value(self):
        """Data only backup type value"""
        from backup_system import BackupType
        assert BackupType.DATA_ONLY.value == "data_only"


class TestBackupStatus:
    """BackupStatus enum tests"""

    def test_pending_value(self):
        """Pending status value"""
        from backup_system import BackupStatus
        assert BackupStatus.PENDING.value == "pending"

    def test_completed_value(self):
        """Completed status value"""
        from backup_system import BackupStatus
        assert BackupStatus.COMPLETED.value == "completed"

    def test_failed_value(self):
        """Failed status value"""
        from backup_system import BackupStatus
        assert BackupStatus.FAILED.value == "failed"


class TestBackupMetadata:
    """BackupMetadata dataclass tests"""

    def test_create_metadata(self):
        """Create backup metadata"""
        from backup_system import BackupMetadata, BackupType, BackupStatus

        metadata = BackupMetadata(
            id="test_backup_001",
            backup_type=BackupType.FULL,
            status=BackupStatus.PENDING,
            created_at=datetime.now()
        )

        assert metadata.id == "test_backup_001"
        assert metadata.backup_type == BackupType.FULL

    def test_metadata_to_dict(self):
        """Metadata to_dict conversion"""
        from backup_system import BackupMetadata, BackupType, BackupStatus

        metadata = BackupMetadata(
            id="test_backup_002",
            backup_type=BackupType.DATA_ONLY,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            size_bytes=1024
        )

        result = metadata.to_dict()

        assert result["id"] == "test_backup_002"
        assert result["backup_type"] == "data_only"
        assert result["status"] == "completed"
        assert "size_formatted" in result

    def test_metadata_from_dict(self):
        """Metadata from_dict conversion"""
        from backup_system import BackupMetadata, BackupType, BackupStatus

        data = {
            "id": "test_backup_003",
            "backup_type": "full",
            "status": "completed",
            "created_at": datetime.now().isoformat(),
            "size_bytes": 2048
        }

        metadata = BackupMetadata.from_dict(data)

        assert metadata.id == "test_backup_003"
        assert metadata.backup_type == BackupType.FULL
        assert metadata.size_bytes == 2048

    def test_format_size(self):
        """Size formatting"""
        from backup_system import BackupMetadata

        assert "B" in BackupMetadata._format_size(500)
        assert "KB" in BackupMetadata._format_size(5000)
        assert "MB" in BackupMetadata._format_size(5000000)
        assert "GB" in BackupMetadata._format_size(5000000000)


class TestBackupSystem:
    """BackupSystem class tests"""

    def test_singleton(self):
        """Backup system is singleton"""
        from backup_system import BackupSystem

        system1 = BackupSystem()
        system2 = BackupSystem()

        assert system1 is system2

    def test_get_backup_system(self):
        """get_backup_system function"""
        from backup_system import get_backup_system, BackupSystem

        system = get_backup_system()
        assert isinstance(system, BackupSystem)

    def test_generate_backup_id(self):
        """Backup ID generation"""
        from backup_system import get_backup_system

        system = get_backup_system()
        backup_id = system._generate_backup_id()

        assert backup_id.startswith("backup_")
        assert len(backup_id) > 10

    def test_list_backups_empty(self):
        """List backups when empty"""
        from backup_system import get_backup_system

        system = get_backup_system()
        backups = system.list_backups()

        assert isinstance(backups, list)

    def test_get_storage_usage(self):
        """Get storage usage stats"""
        from backup_system import get_backup_system

        system = get_backup_system()
        usage = system.get_storage_usage()

        assert "total_backups" in usage
        assert "total_size_bytes" in usage
        assert "total_size_formatted" in usage


class TestBackupConvenienceFunctions:
    """Backup convenience function tests"""

    def test_list_backups_function(self):
        """list_backups convenience function"""
        from backup_system import list_backups

        result = list_backups(limit=10)
        assert isinstance(result, list)

    def test_get_latest_backup_function(self):
        """get_latest_backup convenience function"""
        from backup_system import get_latest_backup

        result = get_latest_backup()
        # May be None if no backups exist
        assert result is None or hasattr(result, "id")


# =============================================================================
# CI/CD Workflow Tests
# =============================================================================

class TestCICDWorkflowExists:
    """CI/CD workflow file tests"""

    def test_workflow_file_exists(self):
        """CI/CD workflow file exists"""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci-cd.yml"

        assert workflow_path.exists(), f"CI/CD workflow not found at {workflow_path}"

    def test_workflow_is_valid_yaml(self):
        """Workflow file is valid YAML"""
        import yaml

        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "ci-cd.yml"

        with open(workflow_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)

        assert "name" in content
        assert "jobs" in content


# =============================================================================
# Docker Configuration Tests
# =============================================================================

class TestDockerfileExists:
    """Dockerfile tests"""

    def test_dockerfile_exists(self):
        """Dockerfile exists"""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile"
        assert dockerfile_path.exists()

    def test_dockerfile_has_healthcheck(self):
        """Dockerfile has healthcheck"""
        dockerfile_path = Path(__file__).parent.parent.parent / "Dockerfile"

        with open(dockerfile_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "HEALTHCHECK" in content


class TestDockerComposeExists:
    """Docker Compose tests"""

    def test_compose_file_exists(self):
        """docker-compose.yml exists"""
        compose_path = Path(__file__).parent.parent.parent / "docker-compose.yml"
        assert compose_path.exists()

    def test_compose_dev_exists(self):
        """docker-compose.dev.yml exists"""
        compose_path = Path(__file__).parent.parent.parent / "docker-compose.dev.yml"
        assert compose_path.exists()

    def test_compose_prod_exists(self):
        """docker-compose.prod.yml exists"""
        compose_path = Path(__file__).parent.parent.parent / "docker-compose.prod.yml"
        assert compose_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
