from pydantic import BaseModel, ConfigDict


class StateBase(BaseModel):
    code: int
    name: str


class StateResponse(StateBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StateDetail(StateResponse):
    district_count: int
