"""
FastAPI application entry point for OSINT Nexus API layer.
"""

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from osint_nexus.core.agent import OSINTAgent

app = FastAPI(title="OSINT Nexus API")


class ScanRequest(BaseModel):
    username: str
    timeout: float = 15.0


@app.post("/scan")
async def trigger_scan(request: ScanRequest) -> dict[str, Any]:
    """Triggers an OSINT scan."""
    agent = OSINTAgent(request.username)

    results = []
    async for intel in agent.run_scan(request.username, timeout=request.timeout):
        results.append(intel)

    return {"username": request.username, "results": results}
