from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    business_name: str | None = None
    phone: str | None = None
    gst_number: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    status: str = "active"
    plan: str = "free"
    business_name: str | None = None
    phone: str | None = None
    gst_number: str | None = None
    admin_notes: str | None = None
    created_at: datetime
    last_login_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    model_config = ConfigDict(from_attributes=True)


class UserApprove(BaseModel):
    plan: str = "free"
    admin_notes: str | None = None


class UserReject(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    admin_notes: str | None = None


class UserUpdate(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None
    plan: str | None = None
    status: str | None = None
    admin_notes: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse