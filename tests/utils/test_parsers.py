from pydantic import BaseModel, ConfigDict

from osint_nexus.utils.parsers import SafeParser


class SampleModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    age: int


def test_safe_parser_str() -> None:
    data: dict[str, str | int | float | bool | None] = {"name": "Test", "age": 30, "extra": "ignored"}
    parser = SafeParser(data)
    assert parser.get_str("name") == "Test"
    assert parser.get_str("missing", "default") == "default"


def test_safe_parser_int() -> None:
    data: dict[str, str | int | float | bool | None] = {"age": 30}
    parser = SafeParser(data)
    assert parser.get_int("age") == 30
    assert parser.get_int("missing", 0) == 0


def test_safe_parser_as_model() -> None:
    data: dict[str, str | int | float | bool | None] = {"name": "Test", "age": 30, "extra": "ignored"}
    parser = SafeParser(data)
    # Cast to ensure mypy knows the type returned
    model = parser.as_model(SampleModel)
    assert model.name == "Test"
    assert model.age == 30
