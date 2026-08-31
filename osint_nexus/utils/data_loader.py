import json
from pathlib import Path

from pydantic import TypeAdapter

from osint_nexus.core.type_defs import JSONValue

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# TypeAdapter for JSONValue to handle type-safe parsing
json_adapter: TypeAdapter[JSONValue] = TypeAdapter(JSONValue)


def load_data(filename: str) -> JSONValue:
    """Load JSON data from the data directory in a type-safe manner."""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data: object = json.load(f)
        return json_adapter.validate_python(data)
