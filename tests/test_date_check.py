import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from lib.date_check import check_license, get_real_utc_time, load_last_run, save_last_run

def test_load_save_last_run():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, ".run_info")
        dt = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)
        
        # Should return None when file doesn't exist
        assert load_last_run(file_path) is None
        
        # Save and load
        save_last_run(file_path, dt)
        loaded = load_last_run(file_path)
        assert loaded is not None
        assert loaded == dt

def test_check_license_valid():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, ".run_info")
        build_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
        
        # Mock internet check returning None to force fallback to current system date
        with patch("lib.date_check.get_real_utc_time", return_value=None):
            # Enforce current time is valid (build_date < now < build_date + 45 days)
            with patch("lib.date_check.datetime") as mock_datetime:
                mock_now = build_date + timedelta(days=10)
                mock_datetime.now.return_value = mock_now
                mock_datetime.fromisoformat = datetime.fromisoformat
                
                is_valid, msg = check_license(build_date, 45, file_path)
                assert is_valid is True
                assert "35 day(s) remaining" in msg

def test_check_license_expired():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, ".run_info")
        build_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
        
        with patch("lib.date_check.get_real_utc_time", return_value=None):
            with patch("lib.date_check.datetime") as mock_datetime:
                # Expired after 45 days (50 days delta)
                mock_now = build_date + timedelta(days=50)
                mock_datetime.now.return_value = mock_now
                mock_datetime.fromisoformat = datetime.fromisoformat
                
                is_valid, msg = check_license(build_date, 45, file_path)
                assert is_valid is False
                assert "expired" in msg

def test_check_license_before_build():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, ".run_info")
        build_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
        
        with patch("lib.date_check.get_real_utc_time", return_value=None):
            with patch("lib.date_check.datetime") as mock_datetime:
                # Before build date
                mock_now = build_date - timedelta(days=1)
                mock_datetime.now.return_value = mock_now
                mock_datetime.fromisoformat = datetime.fromisoformat
                
                is_valid, msg = check_license(build_date, 45, file_path)
                assert is_valid is False
                assert "before the software build date" in msg

def test_check_license_rollback():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, ".run_info")
        build_date = datetime(2026, 5, 1, tzinfo=timezone.utc)
        
        # Pre-seed last run info to a future date
        last_run_time = build_date + timedelta(days=20)
        save_last_run(file_path, last_run_time)
        
        with patch("lib.date_check.get_real_utc_time", return_value=None):
            with patch("lib.date_check.datetime") as mock_datetime:
                # Mock current time set earlier than last_run_time (e.g. build_date + 10 days)
                mock_now = build_date + timedelta(days=10)
                mock_datetime.now.return_value = mock_now
                mock_datetime.fromisoformat = datetime.fromisoformat
                
                is_valid, msg = check_license(build_date, 45, file_path)
                assert is_valid is False
                assert "clock rollback" in msg
