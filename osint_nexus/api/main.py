"""
FastAPI application entry point for OSINT Nexus API layer.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from osint_nexus.core.agent import OSINTAgent
from osint_nexus.core.intelligence import IntelligenceObject

app = FastAPI(title="OSINT Nexus API")


def _sanitize_for_log(value: str) -> str:
    """Remove ASCII control characters to prevent log injection."""
    return "".join(ch for ch in value if ch >= " " and ch != "\x7f")


class ScanRequest(BaseModel):
    username: str
    timeout: float = 15.0


@app.post("/scan", response_model=dict[str, object])
async def trigger_scan(request: ScanRequest) -> dict[str, object]:
    """Triggers an OSINT scan."""
    safe_username = _sanitize_for_log(request.username)
    agent = OSINTAgent(safe_username)

    results: list[IntelligenceObject] = []
    async for intel in agent.run_scan(safe_username, timeout=request.timeout):
        results.append(intel)

    # Use model_dump to serialize IntelligenceObject records
    serialized_results = [intel.model_dump() for intel in results]

    return {"username": safe_username, "results": serialized_results}
