import pytest
from unittest.mock import AsyncMock, MagicMock
from osint_nexus.core.diff import DiffEngine
from osint_nexus.core.database import DatabaseManager
from typing import Any

@pytest.mark.asyncio
async def test_diff_engine() -> None:
    db_manager = MagicMock(spec=DatabaseManager)
    db_manager.query_results = AsyncMock(return_value=[
        {"platform": "twitter", "found": True, "bio": "old bio", "avatar_url": "old_url"},
        {"platform": "github", "found": True, "bio": "old bio", "avatar_url": "old_url"}
    ])
    
    engine = DiffEngine(db_manager)
    
    current_results: list[dict[str, Any]] = [
        {"platform": "twitter", "found": True, "bio": "new bio", "avatar_url": "old_url"},
        {"platform": "linkedin", "found": True, "bio": "new bio", "avatar_url": "new_url"}
    ]
    
    result = await engine.diff("test_user", current_results)
    
    assert "new_platforms" in result
    assert result["new_platforms"] == ["linkedin"]
    assert "removed_platforms" in result
    assert result["removed_platforms"] == ["github"]
    
    modified_content = result["modified_content"]
    assert len(modified_content) == 1
    assert modified_content[0]["platform"] == "twitter"
    assert modified_content[0]["field"] == "bio"
