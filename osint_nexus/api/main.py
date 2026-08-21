"""
FastAPI application entry point for OSINT Nexus API layer.
"""

from typing import Annotated

from fastapi import Depends, FastAPI, Header
from pydantic import BaseModel

from osint_nexus.api.deps import get_db
from osint_nexus.core.agent import OSINTAgent
from osint_nexus.core.database import DatabaseManager
from osint_nexus.core.intelligence import IntelligenceObject

app = FastAPI(title="OSINT Nexus API")


def _sanitize_for_log(value: str) -> str:
    """Remove ASCII control characters to prevent log injection."""
    return "".join(ch for ch in value if ch >= " " and ch != "\x7f")


class ScanRequest(BaseModel):
    username: str
    timeout: float = 15.0


@app.post("/scan", response_model=dict[str, object])
async def trigger_scan(
    request: ScanRequest,
    db: DatabaseManager = Depends(get_db),
    ja3_hash: Annotated[str | None, Header(alias="X-JA3-Hash")] = None,
) -> dict[str, object]:
    """Triggers an OSINT scan."""
    safe_username = _sanitize_for_log(request.username)
    # Pass extracted JA3 hash to agent
    agent = OSINTAgent(safe_username, ja3_hash=ja3_hash)

    results: list[IntelligenceObject] = []
    async for intel in agent.run_scan(safe_username, timeout=request.timeout):
        results.append(intel)
        # Note: Using DB dependency as required by the new infrastructure
        await db.save_result(safe_username, intel.platform, True)

    # Use model_dump to serialize IntelligenceObject records
    serialized_results = [intel.model_dump() for intel in results]

    return {"username": safe_username, "results": serialized_results}
