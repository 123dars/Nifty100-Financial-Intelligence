from pydantic import BaseModel


class StateRef(BaseModel):
    id: int
    code: int
    name: str


class DistrictRef(BaseModel):
    id: int
    code: int
    name: str
    state_id: int


class SubDistrictRef(BaseModel):
    id: int
    code: int
    name: str
    district_id: int


class VillageRef(BaseModel):
    id: int
    code: int
    name: str
    sub_district_id: int


class SearchResponse(BaseModel):
    states: list[StateRef]
    districts: list[DistrictRef]
    sub_districts: list[SubDistrictRef]
    villages: list[VillageRef]