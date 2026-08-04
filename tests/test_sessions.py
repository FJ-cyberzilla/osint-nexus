import json
import os
import pytest
from unittest.mock import patch, mock_open
from osint_nexus.core.sessions import SessionManager
from pathlib import Path
from typing import Any

def test_session_manager_init(tmp_path: Path) -> None:
    storage_path = tmp_path / "sessions.json"
    manager = SessionManager(storage_path=str(storage_path))
    assert manager.storage_path == str(storage_path)
    assert manager._sessions == {}

def test_load_sessions(tmp_path: Path) -> None:
    storage_path = tmp_path / "sessions.json"
    session_data: dict[str, Any] = {"test_platform": {"token": "abc"}}
    with open(storage_path, "w") as f:
        json.dump(session_data, f)
    
    manager = SessionManager(storage_path=str(storage_path))
    assert manager.get_session("test_platform") == {"token": "abc"}

def test_save_session(tmp_path: Path) -> None:
    storage_path = tmp_path / "sessions.json"
    manager = SessionManager(storage_path=str(storage_path))
    manager.save_session("new_platform", {"token": "xyz"})
    
    assert manager.get_session("new_platform") == {"token": "xyz"}
    
    with open(storage_path, "r") as f:
        data = json.load(f)
    assert data["new_platform"] == {"token": "xyz"}

def test_get_nonexistent_session(tmp_path: Path) -> None:
    storage_path = tmp_path / "sessions.json"
    manager = SessionManager(storage_path=str(storage_path))
    assert manager.get_session("unknown") is None

from osint_nexus.core.exceptions import DatabaseError

@patch("osint_nexus.core.sessions.logger")
def test_load_sessions_failure(mock_logger: Any, tmp_path: Path) -> None:
    storage_path = tmp_path / "sessions.json"
    with open(storage_path, "w") as f:
        f.write("invalid json")
    
    with pytest.raises(DatabaseError):
        SessionManager(storage_path=str(storage_path))
    
    mock_logger.error.assert_called()
