from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import generate_api_secret, sign_key_secret
from app.core.security import generate_api_key as _make_key
from app.database import get_db
from app.dependencies import get_current_user
from app.models.api_key import ApiKey
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse

router = APIRouter(
    prefix="/keys",
    tags=["API Keys"],
)

logger = get_logger("app.routers.api_keys")


@router.post(
    "/generate",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_api_key(
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiKeyCreatedResponse:
    if not current_user.is_active or current_user.status != "active":
        raise HTTPException(status_code=403, detail="User account is not active")

    key = _make_key()
    secret = generate_api_secret()
    api_key = ApiKey(
        key=key,
        secret_digest=sign_key_secret(key, secret),
        name=payload.name,
        user_id=current_user.id,
        is_active=True,
        rate_limit=payload.rate_limit or 1000,
        expires_at=payload.expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(
        "Generated API key #%s (%s) for user #%s",
        api_key.id,
        api_key.name,
        current_user.id,
    )
    base = ApiKeyResponse.model_validate(api_key)
    return ApiKeyCreatedResponse(**base.model_dump(), secret=secret)


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApiKey]:
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc())
    )
    return list(result.scalars().all())
