from pydantic import BaseModel, ConfigDict


class VillageBase(BaseModel):
    code: int
    name: str


class VillageResponse(VillageBase):
    id: int
    sub_district_id: int
    model_config = ConfigDict(from_attributes=True)
