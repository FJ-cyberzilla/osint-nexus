import os
from typing import Literal

EngineType = Literal["pyqt6", "playwright"]


def detect_best_engine() -> EngineType:
    """Auto-detects the operational environment.

    Defaults to Playwright if running inside Termux, Android, or headless servers,
    otherwise uses PyQt6 for desktop environments.
    """
    is_termux = "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")
    is_android = "ANDROID_ROOT" in os.environ

    if is_termux or is_android:
        return "playwright"

    try:
        import PyQt6.QtWebEngineWidgets  # noqa: F401

        return "pyqt6"
    except ImportError:
        return "playwright"
