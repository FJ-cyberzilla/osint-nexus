import os
from enum import Enum


class EngineType(Enum):
    PYQT6 = "pyqt6"
    PLAYWRIGHT = "playwright"


def detect_best_engine() -> EngineType:
    """Auto-detects the operational environment.

    Defaults to Playwright if running inside Termux, Android, or headless servers,
    otherwise uses PyQt6 for desktop environments.
    """
    is_termux = "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")
    is_android = "ANDROID_ROOT" in os.environ

    if is_termux or is_android:
        return EngineType.PLAYWRIGHT

    try:
        import PyQt6.QtWebEngineWidgets  # noqa: F401

        return EngineType.PYQT6
    except ImportError:
        return EngineType.PLAYWRIGHT
