from unittest.mock import MagicMock

from osint_nexus.core.orchestrator import OrchestratorDeps, ScanOrchestrator


def test_orchestrator_init():
    deps = MagicMock(spec=OrchestratorDeps)
    detection = MagicMock()
    orchestrator = ScanOrchestrator(deps, detection)
    assert orchestrator.max_concurrency == 5
    assert not orchestrator._abort_event.is_set()


def test_orchestrator_abort():
    deps = MagicMock(spec=OrchestratorDeps)
    detection = MagicMock()
    orchestrator = ScanOrchestrator(deps, detection)
    orchestrator.abort()
    assert orchestrator._abort_event.is_set()


def test_build_error_intel():
    deps = MagicMock(spec=OrchestratorDeps)
    detection = MagicMock()
    orchestrator = ScanOrchestrator(deps, detection)

    intel = orchestrator._build_error_intel("platform", "user", "error")
    assert intel.platform == "platform"
    assert intel.found is False
    assert intel.metadata["error"] == "error"
