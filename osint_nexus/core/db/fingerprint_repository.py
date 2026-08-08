import json
from pathlib import Path


class FingerprintRepository:
    """Manages loading and querying fingerprint signatures from disk."""

    def __init__(self, data_path: Path = Path("data/fingerprints.json")):
        self.data_path = data_path
        self.data: dict[str, dict[str, str]] = {}
        self._load_data()

    def _load_data(self) -> None:
        if self.data_path.exists():
            with open(self.data_path) as f:
                self.data = json.load(f)
        else:
            # Fallback for initial implementation or missing file
            self.data = {
                "ja3": {
                    "72a589da586844d7f0818ce684948eea": "Chrome 120 on Windows 10",
                    "a0e9f5d64349fb13191bc787f6efad1f": "curl 7.68 on Ubuntu 20.04",
                    "e7b6b5f5f5f5f5f5f5f5f5f5f5f5f5": "Python requests (urllib3)",
                }
            }

    def get_signature(self, category: str, signature: str) -> str | None:
        return self.data.get(category, {}).get(signature)
