from pydantic import BaseModel, ConfigDict


class SubDistrictBase(BaseModel):
    code: int
    name: str


class SubDistrictResponse(SubDistrictBase):
    id: int
    district_id: int
    model_config = ConfigDict(from_attributes=True)


class SubDistrictDetail(SubDistrictResponse):
    village_count: int
