from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    rate_limit: int | None = Field(default=None, ge=1, le=1_000_000)
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    user_id: int | None = None
    is_active: bool
    rate_limit: int
    total_requests: int
    created_at: datetime
    last_used_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned once when a key is created; includes the never-again visible secret."""

    secret: str


class ApiKeyUpdate(BaseModel):
    is_active: bool | None = None
    rate_limit: int | None = Field(default=None, ge=1, le=1_000_000)
