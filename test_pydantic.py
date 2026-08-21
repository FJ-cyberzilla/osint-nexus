from pydantic import BaseModel, ConfigDict

class TestModel(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
