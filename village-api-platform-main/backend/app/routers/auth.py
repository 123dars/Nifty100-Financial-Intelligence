from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.email import send_welcome_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

logger = get_logger("app.routers.auth")

BLOCKED_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "aol.com", "mail.com", "protonmail.com", "zoho.com",
}


async def _create_user(payload: UserCreate, db: AsyncSession) -> TokenResponse:
    existing = (
        await db.execute(select(User.id).where(User.email == payload.email.lower()))
    ).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        )

    # Block free email providers for B2B registration
    domain = payload.email.lower().split("@")[-1]
    if domain in BLOCKED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail="Please use your business email address",
        )

    user_count = (await db.execute(select(func.count(User.id)))).scalar_one()
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        business_name=payload.business_name,
        phone=payload.phone,
        gst_number=payload.gst_number,
        is_admin=user_count == 0,
        is_active=True,
        status="active" if user_count == 0 else "pending_approval",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    logger.info("New user signed up: %s (status=%s)", user.email, user.status)

    # Send welcome email asynchronously (fire-and-forget)
    try:
        await send_welcome_email(user.email, user.full_name)
    except Exception:
        logger.exception("Failed to send welcome email to %s", user.email)

    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await _create_user(payload, db)


# Alias endpoint matching AGENTS.md spec
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await _create_user(payload, db)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(
        select(User).where(User.email == payload.email.lower())
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    if user.status == "pending_approval":
        raise HTTPException(
            status_code=403,
            detail="Account pending approval. Check your email.",
        )

    if user.status == "rejected":
        reason = user.rejection_reason or "Contact support"
        raise HTTPException(
            status_code=403,
            detail=f"Account not approved: {reason}",
        )

    user.last_login_at = datetime.now(UTC)
    await db.commit()

    token = create_access_token(user.id, {"admin": user.is_admin})
    logger.info("User logged in: %s", user.email)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/admin-users", response_model=int)
async def count_admin_users(
    db: AsyncSession = Depends(get_db),
) -> int:
    """Small bootstrap helper: reports how many dashboard users exist.

    This lets the Next.js app decide whether to name the signup flow
    'Create your admin account'.
    """
    return (await db.execute(select(func.count(User.id)))).scalar_one()