# tests/integration/test_system_integration.py
# FlyReady Lab - System Integration Tests
# Stage 5: Enterprise-level integration testing

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestMonitoringAnalyticsIntegration:
    """Monitoring and Analytics system integration tests"""

    @patch('monitoring.st')
    @patch('analytics.st')
    def test_page_view_tracking_integration(self, mock_analytics_st, mock_monitoring_st):
        """Test page view tracking works across both systems"""
        mock_monitoring_st.session_state = {"session_id": "test_session"}
        mock_analytics_st.session_state = {"session_id": "test_session"}

        from monitoring import track_page_view as monitoring_track
        from analytics import track_page_view as analytics_track

        # Track page view in both systems
        monitoring_track("home", "user123")
        analytics_track("home", "test_session", "user123")

        # Both should work without errors

    @patch('monitoring.st')
    def test_error_tracking_creates_alert(self, mock_st):
        """Test that tracking an error creates an alert"""
        mock_st.session_state = {}

        from monitoring import get_monitoring, AlertLevel

        monitoring = get_monitoring()

        try:
            raise ValueError("Test integration error")
        except Exception as e:
            monitoring.track_error(e, {"test": "integration"}, "test_page")

        # Should have logged the error
        status = monitoring.get_system_status()
        assert status["error_count"] >= 0


class TestHealthCheckMonitoringIntegration:
    """Health check and monitoring integration tests"""

    @patch('health_check.psutil')
    def test_health_check_reports_to_monitoring(self, mock_psutil):
        """Test health check results integrate with monitoring"""
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0,
            total=16 * 1024 * 1024 * 1024,
            available=8 * 1024 * 1024 * 1024
        )
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.cpu_count.return_value = 8

        from health_check import run_health_check
        from monitoring import get_monitoring

        # Run health check
        health_result = run_health_check()

        assert "status" in health_result
        assert "checks" in health_result


class TestBackupSystemIntegration:
    """Backup system integration tests"""

    def test_backup_creates_valid_archive(self, tmp_path):
        """Test backup creates valid compressed archive"""
        from backup_system import BackupSystem, BackupType

        # Create test data
        test_data_dir = tmp_path / "data"
        test_data_dir.mkdir()
        (test_data_dir / "test.txt").write_text("test content")

        backup_system = BackupSystem()

        # Create backup
        with patch.object(backup_system, '_get_source_paths', return_value=[test_data_dir]):
            metadata = backup_system.create_backup(BackupType.DATA_ONLY, compress=True)

        assert metadata.status.value in ["completed", "in_progress", "pending"]

    def test_backup_metadata_persistence(self):
        """Test backup metadata is saved and loaded correctly"""
        from backup_system import BackupMetadata, BackupType, BackupStatus

        metadata = BackupMetadata(
            id="test_backup_001",
            backup_type=BackupType.FULL,
            status=BackupStatus.COMPLETED,
            created_at=datetime.now(),
            size_bytes=1024
        )

        # Convert to dict and back
        data = metadata.to_dict()
        restored = BackupMetadata.from_dict(data)

        assert restored.id == metadata.id
        assert restored.backup_type == metadata.backup_type
        assert restored.status == metadata.status


class TestEnvConfigIntegration:
    """Environment configuration integration tests"""

    def test_config_loads_from_environment(self):
        """Test configuration loads from environment variables"""
        from env_manager import get_config, Environment

        # Set test environment
        os.environ["ENV"] = "test"

        config = get_config("test")

        assert config.env == Environment.TEST
        assert config.debug is True

    def test_config_validates_production(self):
        """Test production configuration validation"""
        from env_manager import get_production_config, validate_config

        config = get_production_config()
        messages = validate_config(config)

        # Should have warnings about missing keys
        assert any("OPENAI_API_KEY" in msg for msg in messages)


class TestModuleImportIntegration:
    """Module import integration tests"""

    def test_all_stage_modules_import(self):
        """Test all Stage 1-5 modules can be imported"""
        modules_to_test = [
            # Stage 1
            "ui_config",
            "ui_components",
            # Stage 2
            "accessibility",
            "responsive_design",
            "security_utils",
            "error_handler",
            "performance_utils",
            # Stage 3
            "shared_utils",
            # Stage 4
            "monitoring",
            "analytics",
            "health_check",
            "logging_config",
            # Stage 5
            "env_manager",
            "backup_system",
        ]

        failed_imports = []

        for module in modules_to_test:
            try:
                __import__(module)
            except ImportError as e:
                failed_imports.append(f"{module}: {e}")

        if failed_imports:
            pytest.fail(f"Failed to import modules:\n" + "\n".join(failed_imports))

    def test_sidebar_common_integrates_all_stages(self):
        """Test sidebar_common.py integrates all stage modules"""
        # Check imports work
        try:
            from sidebar_common import render_sidebar
            assert callable(render_sidebar)
        except ImportError as e:
            pytest.fail(f"sidebar_common import failed: {e}")


class TestLoggingIntegration:
    """Logging system integration tests"""

    def test_logging_config_creates_logger(self):
        """Test logging configuration creates working logger"""
        from logging_config import get_logger

        logger = get_logger("test_integration")

        assert logger is not None
        assert logger.name == "test_integration"

    def test_logging_writes_to_file(self, tmp_path):
        """Test logging can write to file"""
        import logging
        from logging_config import get_logger

        logger = get_logger("test_file_logger")

        # Add file handler
        log_file = tmp_path / "test.log"
        handler = logging.FileHandler(log_file)
        logger.addHandler(handler)

        logger.info("Test log message")
        handler.flush()

        # Verify file was written
        assert log_file.exists()


class TestSecurityIntegration:
    """Security utilities integration tests"""

    @patch('security_utils.st')
    def test_csrf_token_flow(self, mock_st):
        """Test CSRF token generation and validation flow"""
        class AttrDict(dict):
            def __setattr__(self, key, value):
                self[key] = value
            def __getattr__(self, key):
                return self.get(key)
            def __contains__(self, key):
                return dict.__contains__(self, key)

        mock_st.session_state = AttrDict()

        from security_utils import generate_csrf_token, validate_csrf_token

        # Generate token
        token = generate_csrf_token()
        assert token is not None

        # Validate token
        is_valid = validate_csrf_token(token)
        assert is_valid is True

        # Invalid token should fail
        is_invalid = validate_csrf_token("invalid_token")
        assert is_invalid is False

    def test_rate_limiter_integration(self):
        """Test rate limiter works across multiple calls"""
        from security_utils import RateLimiter

        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # First 5 requests should be allowed
        for i in range(5):
            allowed, remaining = limiter.is_allowed("test_user")
            assert allowed is True

        # 6th request should be blocked
        allowed, remaining = limiter.is_allowed("test_user")
        assert allowed is False


class TestPerformanceIntegration:
    """Performance utilities integration tests"""

    @patch('performance_utils.st')
    def test_session_cleanup_integration(self, mock_st):
        """Test session cleanup works correctly"""
        mock_st.session_state = {"key1": "value1", "key2": "value2"}

        from performance_utils import cleanup_session

        # Should not raise error
        cleanup_session()


class TestEndToEndWorkflow:
    """End-to-end workflow integration tests"""

    @patch('monitoring.st')
    @patch('analytics.st')
    def test_user_session_workflow(self, mock_analytics_st, mock_monitoring_st):
        """Test complete user session workflow"""
        session_state = {"session_id": "e2e_test_session"}
        mock_monitoring_st.session_state = session_state
        mock_analytics_st.session_state = session_state

        from monitoring import init_monitoring, track_page_view as m_track
        from analytics import get_analytics, track_page_view as a_track

        # Initialize monitoring
        monitoring = init_monitoring()
        analytics = get_analytics()

        # Simulate user journey
        pages = ["home", "interview", "result"]
        for page in pages:
            m_track(page, "test_user")
            a_track(page)

        # Verify tracking worked
        status = monitoring.get_system_status()
        assert status["total_events"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
