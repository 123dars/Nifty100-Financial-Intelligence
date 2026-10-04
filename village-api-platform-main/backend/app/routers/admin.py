from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security import generate_api_key, generate_api_secret, sign_key_secret
from app.database import get_db
from app.dependencies import require_admin
from app.models.api_key import ApiKey
from app.models.request_log import RequestLog
from app.models.state import State
from app.models.user import User
from app.models.user_state_access import UserStateAccess
from app.schemas.admin import (
    AdminKeysResponse,
    AdminLogsResponse,
    AdminOverviewResponse,
    AdminUsersResponse,
    LogItem,
    SummaryStat,
    TopClientItem,
    UsageOverview,
    UsagePoint,
)
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    ApiKeyUpdate,
)
from app.schemas.auth import (
    UserApprove,
    UserReject,
    UserResponse,
    UserUpdate,
)
from app.services.email import send_approval_email, send_rejection_email

router = APIRouter(prefix="/admin", tags=["Admin"])

logger = get_logger("app.routers.admin")


def _iso(dt: datetime) -> str:
    return dt.isoformat()


@router.get("/keys", response_model=AdminKeysResponse)
async def list_keys(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminKeysResponse:
    stmt = select(ApiKey)
    if search:
        stmt = stmt.where(ApiKey.name.ilike(f"%{search}%"))
    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = (
        stmt.order_by(ApiKey.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    keys = (await db.execute(stmt)).scalars().all()
    return AdminKeysResponse(
        count=total,
        items=[ApiKeyResponse.model_validate(k) for k in keys],
    )


@router.post(
    "/keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_key(
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ApiKeyCreatedResponse:
    key = generate_api_key()
    secret = generate_api_secret()
    api_key = ApiKey(
        key=key,
        secret_digest=sign_key_secret(key, secret),
        name=payload.name,
        is_active=True,
        rate_limit=payload.rate_limit or 1000,
        expires_at=payload.expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    logger.info("Admin created API key #%s", api_key.id)
    base = ApiKeyResponse.model_validate(api_key)
    return ApiKeyCreatedResponse(**base.model_dump(), secret=secret)


@router.post(
    "/keys/{key_id}/rotate",
    response_model=ApiKeyCreatedResponse,
)
async def rotate_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ApiKeyCreatedResponse:
    """Rotate an API key by deactivating the old key and issuing a new key/secret."""
    old_key = await db.get(ApiKey, key_id)
    if old_key is None:
        raise HTTPException(status_code=404, detail="API key not found")

    new_key = generate_api_key()
    new_secret = generate_api_secret()

    # Disable the compromised/retired credential first.
    old_key.is_active = False

    rotated_key = ApiKey(
        key=new_key,
        secret_digest=sign_key_secret(new_key, new_secret),
        name=old_key.name,
        user_id=old_key.user_id,
        is_active=True,
        rate_limit=old_key.rate_limit,
        expires_at=old_key.expires_at,
    )
    db.add(rotated_key)
    await db.commit()
    await db.refresh(rotated_key)

    logger.info(
        "Admin rotated API key #%s; new key #%s",
        old_key.id,
        rotated_key.id,
    )

    base = ApiKeyResponse.model_validate(rotated_key)
    return ApiKeyCreatedResponse(**base.model_dump(), secret=new_secret)


@router.get("/keys/{key_id}", response_model=ApiKeyResponse)
async def get_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ApiKeyResponse:
    key = await db.get(ApiKey, key_id)
    if key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return ApiKeyResponse.model_validate(key)


@router.patch("/keys/{key_id}", response_model=ApiKeyResponse)
async def update_key(
    key_id: int,
    payload: ApiKeyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ApiKeyResponse:
    key = await db.get(ApiKey, key_id)
    if key is None:
        raise HTTPException(status_code=404, detail="API key not found")

    if payload.is_active is not None:
        key.is_active = payload.is_active
    if payload.rate_limit is not None:
        key.rate_limit = payload.rate_limit
    await db.commit()
    await db.refresh(key)
    return ApiKeyResponse.model_validate(key)


@router.get("/users", response_model=AdminUsersResponse)
async def list_users(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    plan: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminUsersResponse:
    stmt = select(User)

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            User.email.ilike(search_pattern)
            | User.full_name.ilike(search_pattern)
            | User.business_name.ilike(search_pattern)
        )
    if status_filter:
        stmt = stmt.where(User.status == status_filter)
    if plan:
        stmt = stmt.where(User.plan == plan)

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()

    stmt = (
        stmt.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = (await db.execute(stmt)).scalars().all()

    return AdminUsersResponse(
        count=total,
        items=[UserResponse.model_validate(u) for u in users],
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.plan is not None:
        user.plan = payload.plan
    if payload.status is not None:
        user.status = payload.status
    if payload.admin_notes is not None:
        user.admin_notes = payload.admin_notes
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    logger.info("Admin deleted user #%s (%s)", user.id, user.email)


@router.post("/users/{user_id}/approve", response_model=UserResponse)
async def approve_user(
    user_id: int,
    payload: UserApprove | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.status == "active":
        raise HTTPException(status_code=400, detail="User is already active")

    user.status = "active"
    user.is_active = True
    user.approved_at = datetime.now(UTC)
    if payload:
        user.plan = payload.plan
        if payload.admin_notes:
            user.admin_notes = payload.admin_notes
    await db.commit()
    await db.refresh(user)

    logger.info("Admin approved user #%s (%s)", user.id, user.email)
    try:
        await send_approval_email(user.email, user.full_name)
    except Exception:
        logger.exception("Failed to send approval email to %s", user.email)

    return UserResponse.model_validate(user)


@router.post("/users/{user_id}/reject", response_model=UserResponse)
async def reject_user(
    user_id: int,
    payload: UserReject,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> UserResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.status = "rejected"
    user.is_active = False
    user.rejected_at = datetime.now(UTC)
    user.rejection_reason = payload.reason
    if payload.admin_notes:
        user.admin_notes = payload.admin_notes
    await db.commit()
    await db.refresh(user)

    logger.info("Admin rejected user #%s (%s)", user.id, user.email)
    try:
        await send_rejection_email(user.email, user.full_name, payload.reason)
    except Exception:
        logger.exception("Failed to send rejection email to %s", user.email)

    return UserResponse.model_validate(user)



# ── User API Key Management ──────────────────────────────────────


@router.get("/users/{user_id}/keys", response_model=list[ApiKeyResponse])
async def list_user_keys(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[ApiKeyResponse]:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user_id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [ApiKeyResponse.model_validate(key) for key in keys]


@router.post(
    "/users/{user_id}/keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user_key(
    user_id: int,
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> ApiKeyCreatedResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active or user.status != "active":
        raise HTTPException(status_code=400, detail="User account is not active")

    key = generate_api_key()
    secret = generate_api_secret()
    api_key = ApiKey(
        key=key,
        secret_digest=sign_key_secret(key, secret),
        name=payload.name,
        user_id=user_id,
        is_active=True,
        rate_limit=payload.rate_limit or 1000,
        expires_at=payload.expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info(
        "Admin created API key #%s (%s) for user #%s",
        api_key.id,
        api_key.name,
        user_id,
    )
    base = ApiKeyResponse.model_validate(api_key)
    return ApiKeyCreatedResponse(**base.model_dump(), secret=secret)


@router.get("/users/{user_id}/logs", response_model=AdminLogsResponse)
async def list_user_logs(
    user_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminLogsResponse:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    key_ids_result = await db.execute(
        select(ApiKey.id).where(ApiKey.user_id == user_id)
    )
    key_ids = list(key_ids_result.scalars().all())

    if not key_ids:
        return AdminLogsResponse(
            count=0,
            page=page,
            page_size=page_size,
            items=[],
        )

    base_stmt = select(RequestLog).where(RequestLog.api_key_id.in_(key_ids))
    total = (
        await db.execute(select(func.count()).select_from(base_stmt.subquery()))
    ).scalar_one()

    rows = (
        await db.execute(
            base_stmt
            .order_by(RequestLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    items = [
        LogItem(
            id=r.id,
            api_key_name=r.api_key_name,
            method=r.method,
            path=r.path,
            query_string=r.query_string,
            status_code=r.status_code,
            duration_ms=r.duration_ms,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            is_anonymous=r.is_anonymous,
            created_at=_iso(r.created_at),
        )
        for r in rows
    ]
    return AdminLogsResponse(
        count=total,
        page=page,
        page_size=page_size,
        items=items,
    )


# ── State Access Management ──────────────────────────────────────


@router.get("/users/{user_id}/state-access")
async def get_user_state_access(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    rows = (
        await db.execute(
            select(UserStateAccess).where(UserStateAccess.user_id == user_id)
        )
    ).scalars().all()

    state_ids = [r.state_id for r in rows]
    all_states = (await db.execute(select(State).order_by(State.name))).scalars().all()

    return {
        "user_id": user_id,
        "has_full_access": len(rows) == 0,
        "granted_state_ids": state_ids,
        "states": [
            {"id": s.id, "code": s.code, "name": s.name, "granted": s.id in state_ids}
            for s in all_states
        ],
    }


@router.post("/users/{user_id}/state-access")
async def grant_state_access(
    user_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    """Grant or revoke state access. Send { state_ids: [...], revoke: false }."""
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    state_ids: list[int] = payload.get("state_ids", [])
    revoke: bool = payload.get("revoke", False)

    if revoke:
        for sid in state_ids:
            existing = (
                await db.execute(
                    select(UserStateAccess).where(
                        UserStateAccess.user_id == user_id,
                        UserStateAccess.state_id == sid,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                await db.delete(existing)
    else:
        for sid in state_ids:
            existing = (
                await db.execute(
                    select(UserStateAccess).where(
                        UserStateAccess.user_id == user_id,
                        UserStateAccess.state_id == sid,
                    )
                )
            ).scalar_one_or_none()
            if not existing:
                db.add(UserStateAccess(user_id=user_id, state_id=sid))

    await db.commit()
    logger.info(
        "Admin %s state access for user #%s: states=%s",
        "revoked" if revoke else "granted",
        user_id,
        state_ids,
    )
    return {
        "success": True,
        "user_id": user_id,
        "state_ids": state_ids,
        "revoked": revoke,
    }


@router.get("/logs", response_model=AdminLogsResponse)
async def list_logs(
    api_key_id: int | None = Query(default=None),
    status_code: int | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminLogsResponse:
    conditions = []
    if api_key_id is not None:
        conditions.append(RequestLog.api_key_id == api_key_id)
    if status_code is not None:
        conditions.append(RequestLog.status_code == status_code)
    if from_date is not None:
        conditions.append(RequestLog.created_at >= from_date)
    if to_date is not None:
        conditions.append(RequestLog.created_at <= to_date)
    if search:
        conditions.append(
            RequestLog.path.ilike(f"%{search}%")
            | RequestLog.api_key_name.ilike(f"%{search}%")
        )

    stmt = select(RequestLog)
    if conditions:
        stmt = stmt.where(*conditions)

    total = (
        await db.execute(select(func.count()).select_from(stmt.subquery()))
    ).scalar_one()
    stmt = stmt.order_by(RequestLog.created_at.desc())
    rows = (
        await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    ).scalars().all()

    items = [
        LogItem(
            id=r.id,
            api_key_name=r.api_key_name,
            method=r.method,
            path=r.path,
            query_string=r.query_string,
            status_code=r.status_code,
            duration_ms=r.duration_ms,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            is_anonymous=r.is_anonymous,
            created_at=_iso(r.created_at),
        )
        for r in rows
    ]
    return AdminLogsResponse(
        count=total, page=page, page_size=page_size, items=items
    )


@router.get("/logs/top-clients", response_model=list[TopClientItem])
async def top_clients(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[TopClientItem]:
    row_count = func.count(RequestLog.id).label("requests")
    error_count = func.count(RequestLog.id).filter(
        RequestLog.status_code >= 400
    ).label("errors")

    stmt = (
        select(
            RequestLog.api_key_id,
            RequestLog.api_key_name,
            row_count,
            error_count,
        )
        .group_by(RequestLog.api_key_id, RequestLog.api_key_name)
        .order_by(row_count.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return [
        TopClientItem(
            key_id=row.api_key_id,
            key_name=row.api_key_name,
            requests=row.requests,
            error_rate=round((row.errors / row.requests) * 100, 2)
            if row.requests
            else 0.0,
        )
        for row in rows
    ]


@router.get("/usage", response_model=UsageOverview)
async def usage(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> UsageOverview:
    now = datetime.now(UTC)
    day_ago = now - timedelta(hours=24)

    total_requests = (await db.execute(select(func.count(RequestLog.id)))).scalar_one()
    error_requests = (
        await db.execute(
            select(func.count(RequestLog.id)).where(RequestLog.status_code >= 400)
        )
    ).scalar_one()
    avg_duration = (
        await db.execute(select(func.avg(RequestLog.duration_ms)))
    ).scalar_one()
    requests_24h = (
        await db.execute(
            select(func.count(RequestLog.id)).where(RequestLog.created_at >= day_ago)
        )
    ).scalar_one()
    active_keys = (
        await db.execute(
            select(func.count(ApiKey.id)).where(ApiKey.is_active.is_(True))
        )
    ).scalar_one()
    total_keys = (await db.execute(select(func.count(ApiKey.id)))).scalar_one()
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()

    hourly = await _series(db, "hour", day_ago)
    daily = await _series(db, "day", now - timedelta(days=30))

    return UsageOverview(
        total_requests=total_requests,
        total_errors=error_requests,
        error_rate=round((error_requests / total_requests) * 100, 2)
        if total_requests
        else 0.0,
        avg_duration_ms=round(avg_duration, 2) if avg_duration is not None else 0.0,
        requests_last_24h=requests_24h,
        active_keys=active_keys,
        total_keys=total_keys,
        total_users=total_users,
        hourly_requests=hourly,
        daily_requests=daily,
    )


async def _series(
    db: AsyncSession, granularity: str, since: datetime
) -> list[UsagePoint]:
    if granularity == "day":
        bucket_expr = func.date_trunc("day", RequestLog.created_at)
    else:
        bucket_expr = func.date_trunc("hour", RequestLog.created_at)

    stmt = (
        select(cast(bucket_expr, String).label("bucket"), func.count(RequestLog.id))
        .where(RequestLog.created_at >= since)
        .group_by(bucket_expr)
        .order_by(bucket_expr)
    )
    rows = (await db.execute(stmt)).all()
    return [UsagePoint(bucket=bucket, requests=count) for bucket, count in rows]


@router.get("/overview", response_model=AdminOverviewResponse)
async def overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminOverviewResponse:
    usage_data = await usage(db, _)
    total = usage_data.total_requests

    recent = (
        await db.execute(
            select(RequestLog).order_by(RequestLog.created_at.desc()).limit(8)
        )
    ).scalars().all()

    recent_logs = [
        LogItem(
            id=r.id,
            api_key_name=r.api_key_name,
            method=r.method,
            path=r.path,
            query_string=r.query_string,
            status_code=r.status_code,
            duration_ms=r.duration_ms,
            ip_address=r.ip_address,
            user_agent=r.user_agent,
            is_anonymous=r.is_anonymous,
            created_at=_iso(r.created_at),
        )
        for r in recent
    ]

    stats = [
        SummaryStat(label="Total Requests", value=total),
        SummaryStat(label="Requests (24h)", value=usage_data.requests_last_24h),
        SummaryStat(label="Error Rate (%)", value=usage_data.error_rate),
        SummaryStat(label="Avg Duration (ms)", value=usage_data.avg_duration_ms),
        SummaryStat(label="Active Keys", value=usage_data.active_keys),
        SummaryStat(label="Total Keys", value=usage_data.total_keys),
        SummaryStat(label="Dashboard Users", value=usage_data.total_users),
    ]

    return AdminOverviewResponse(
        stats=stats, usage=usage_data, recent_logs=recent_logs
    )