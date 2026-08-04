"""
FastAPI application entry point for OSINT Nexus API layer.
"""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from osint_nexus.core.agent import OSINTAgent
from osint_nexus.core.intelligence import IntelligenceObject

app = FastAPI(title="OSINT Nexus API")


class ScanRequest(BaseModel):
    username: str
    timeout: float = 15.0


@app.post("/scan", response_model=dict[str, Any])
async def trigger_scan(request: ScanRequest) -> dict[str, Any]:
    """Triggers an OSINT scan."""
    agent = OSINTAgent(request.username)

    results: list[IntelligenceObject] = []
    async for intel in agent.run_scan(request.username, timeout=request.timeout):
        results.append(intel)

    # Use model_dump to serialize IntelligenceObject records
    serialized_results = [intel.model_dump() for intel in results]

    return {"username": request.username, "results": serialized_results}
