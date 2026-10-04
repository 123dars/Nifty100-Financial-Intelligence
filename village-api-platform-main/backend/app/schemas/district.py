from pydantic import BaseModel, ConfigDict


class DistrictBase(BaseModel):
    code: int
    name: str


class DistrictResponse(DistrictBase):
    id: int
    state_id: int
    model_config = ConfigDict(from_attributes=True)


class DistrictDetail(DistrictResponse):
    sub_district_count: int
