from pydantic import BaseModel, Field

from app.schemas.api_key import ApiKeyResponse
from app.schemas.auth import UserResponse


class UsagePoint(BaseModel):
    bucket: str
    requests: int


class UsageOverview(BaseModel):
    total_requests: int
    total_errors: int
    error_rate: float
    avg_duration_ms: float
    requests_last_24h: int
    active_keys: int
    total_keys: int
    total_users: int
    hourly_requests: list[UsagePoint]
    daily_requests: list[UsagePoint]


class TopClientItem(BaseModel):
    key_id: int | None
    key_name: str | None
    requests: int
    error_rate: float


class AdminKeysResponse(BaseModel):
    count: int
    items: list[ApiKeyResponse]


class AdminUsersResponse(BaseModel):
    count: int
    items: list[UserResponse]


class LogItem(BaseModel):
    id: int
    api_key_name: str | None
    method: str
    path: str
    query_string: str | None
    status_code: int
    duration_ms: float
    ip_address: str | None
    user_agent: str | None
    is_anonymous: bool
    created_at: str


class AdminLogsResponse(BaseModel):
    count: int
    page: int
    page_size: int
    items: list[LogItem]


class SummaryStat(BaseModel):
    label: str
    value: int | float
    delta_percent: float | None = Field(default=None)


class AdminOverviewResponse(BaseModel):
    stats: list[SummaryStat]
    usage: UsageOverview
    recent_logs: list[LogItem]