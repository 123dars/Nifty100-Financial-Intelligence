from pydantic import BaseModel

from app.schemas.district import DistrictResponse
from app.schemas.state import StateResponse


class StateDistributionItem(BaseModel):
    state_name: str
    state_code: int
    district_count: int


class SummaryResponse(BaseModel):
    total_states: int
    total_districts: int
    total_sub_districts: int
    total_villages: int
    active_users: int
    api_requests: int
    avg_response_time: float
    state_distribution: list[StateDistributionItem]


class TopStateItem(BaseModel):
    state_name: str
    state_code: int
    village_count: int
    district_count: int


class TopStatesResponse(BaseModel):
    top_states: list[TopStateItem]


class StateAnalyticsResponse(BaseModel):
    state: StateResponse
    district_count: int
    sub_district_count: int
    village_count: int
    districts: list[DistrictResponse]


class ApiRequestTrendItem(BaseModel):
    day: str
    requests: int


class ApiRequestTrendResponse(BaseModel):
    data: list[ApiRequestTrendItem]