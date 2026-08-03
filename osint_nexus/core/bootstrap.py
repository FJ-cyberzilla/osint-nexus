"""Centralized bootstrap logic for OSINT Nexus."""

from pathlib import Path

# Locate the project root (assumes bootstrap.py is inside osint_nexus/core/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Define standard storage paths
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"


# Guarantee directories exist at runtime before modules try to write to them
def initialize_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Exported absolute file paths
DATABASE_PATH = DATA_DIR / "osint_results.db"
LOG_FILE_PATH = LOGS_DIR / "osint.log"
