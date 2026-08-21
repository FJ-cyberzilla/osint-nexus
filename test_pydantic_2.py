from pydantic import BaseModel, Field

class TestModel(BaseModel):
    name: str = Field(...)
