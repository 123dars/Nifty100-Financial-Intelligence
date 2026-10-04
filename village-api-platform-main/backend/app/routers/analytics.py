from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.district import District
from app.models.request_log import RequestLog
from app.models.state import State
from app.models.sub_district import SubDistrict
from app.models.user import User
from app.models.village import Village
from app.schemas.analytics import (
    ApiRequestTrendItem,
    ApiRequestTrendResponse,
    StateAnalyticsResponse,
    SummaryResponse,
    TopStateItem,
    TopStatesResponse,
)
from app.schemas.state import StateResponse


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("/summary", response_model=SummaryResponse)
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> SummaryResponse:

    # ----------------------------------------
    # LOCATION COUNTS
    # ----------------------------------------

    total_states = (
        await db.execute(
            select(func.count(State.id))
        )
    ).scalar_one()

    total_districts = (
        await db.execute(
            select(func.count(District.id))
        )
    ).scalar_one()

    total_sub_districts = (
        await db.execute(
            select(func.count(SubDistrict.id))
        )
    ).scalar_one()

    total_villages = (
        await db.execute(
            select(func.count(Village.id))
        )
    ).scalar_one()


    # ----------------------------------------
    # ACTIVE USERS
    # ----------------------------------------

    active_users = (
        await db.execute(
            select(func.count(User.id))
            .where(
                User.is_active.is_(True)
            )
        )
    ).scalar_one()


    # ----------------------------------------
    # API REQUESTS TODAY
    # ----------------------------------------

    now = datetime.now(timezone.utc)

    today_start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    api_requests = (
        await db.execute(
            select(func.count(RequestLog.id))
            .where(
                RequestLog.created_at >= today_start
            )
        )
    ).scalar_one()


    # ----------------------------------------
    # AVERAGE RESPONSE TIME
    # ----------------------------------------

    avg_response_result = await db.execute(
        select(
            func.avg(RequestLog.duration_ms)
        )
    )

    avg_response_time = (
        avg_response_result.scalar()
    )

    if avg_response_time is None:
        avg_response_time = 0.0


    # ----------------------------------------
    # STATE DISTRIBUTION
    # ----------------------------------------

    distribution_result = await db.execute(
        select(
            State.name.label("state_name"),
            State.code.label("state_code"),
            func.count(District.id).label(
                "district_count"
            ),
        )
        .outerjoin(
            District,
            District.state_id == State.id,
        )
        .group_by(
            State.id,
            State.name,
            State.code,
        )
        .order_by(State.name)
    )

    state_distribution = [
        {
            "state_name": row.state_name,
            "state_code": row.state_code,
            "district_count": row.district_count,
        }
        for row in distribution_result.all()
    ]


    # ----------------------------------------
    # RESPONSE
    # ----------------------------------------

    return SummaryResponse(
        total_states=total_states,
        total_districts=total_districts,
        total_sub_districts=total_sub_districts,
        total_villages=total_villages,
        active_users=active_users,
        api_requests=api_requests,
        avg_response_time=round(
            float(avg_response_time),
            2,
        ),
        state_distribution=state_distribution,
    )


@router.get(
    "/request-trend",
    response_model=ApiRequestTrendResponse,
)
async def request_trend(
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> ApiRequestTrendResponse:

    now = datetime.now(timezone.utc)

    start_date = (
        now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        - timedelta(days=6)
    )

    result = await db.execute(
        select(
            func.date(RequestLog.created_at).label("day"),
            func.count(RequestLog.id).label(
                "requests"
            ),
        )
        .where(
            RequestLog.created_at >= start_date
        )
        .group_by(
            func.date(RequestLog.created_at)
        )
        .order_by(
            func.date(RequestLog.created_at)
        )
    )

    request_counts = {
        str(row.day): row.requests
        for row in result.all()
    }

    trend = []

    for i in range(7):

        current_date = (
            start_date + timedelta(days=i)
        ).date()

        date_key = str(current_date)

        trend.append(
            ApiRequestTrendItem(
                day=current_date.strftime("%a"),
                requests=request_counts.get(
                    date_key,
                    0,
                ),
            )
        )

    return ApiRequestTrendResponse(
        data=trend
    )


@router.get(
    "/top-states",
    response_model=TopStatesResponse,
)
async def top_states(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> TopStatesResponse:

    district_count_subq = (
        select(
            func.count(District.id)
        )
        .where(
            District.state_id == State.id
        )
        .correlate(State)
        .scalar_subquery()
    )

    village_count_subq = (
        select(
            func.count(Village.id)
        )
        .join(
            SubDistrict,
            SubDistrict.id == Village.sub_district_id,
        )
        .join(
            District,
            District.id == SubDistrict.district_id,
        )
        .where(
            District.state_id == State.id
        )
        .correlate(State)
        .scalar_subquery()
    )

    result = await db.execute(
        select(
            State.name.label("state_name"),
            State.code.label("state_code"),
            village_count_subq.label(
                "village_count"
            ),
            district_count_subq.label(
                "district_count"
            ),
        )
        .order_by(
            village_count_subq.desc()
        )
        .limit(limit)
    )

    top_states = [
        TopStateItem(
            state_name=row.state_name,
            state_code=row.state_code,
            village_count=row.village_count,
            district_count=row.district_count,
        )
        for row in result.all()
    ]

    return TopStatesResponse(
        top_states=top_states
    )


@router.get(
    "/state/{state_id}",
    response_model=StateAnalyticsResponse,
)
async def state_analytics(
    state_id: int,
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> StateAnalyticsResponse:

    state = await db.get(
        State,
        state_id,
    )

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="State not found",
        )

    district_count = (
        await db.execute(
            select(
                func.count(District.id)
            ).where(
                District.state_id == state_id
            )
        )
    ).scalar_one()

    sub_district_count = (
        await db.execute(
            select(
                func.count(SubDistrict.id)
            )
            .join(
                District,
                District.id == SubDistrict.district_id,
            )
            .where(
                District.state_id == state_id
            )
        )
    ).scalar_one()

    village_count = (
        await db.execute(
            select(
                func.count(Village.id)
            )
            .join(
                SubDistrict,
                SubDistrict.id == Village.sub_district_id,
            )
            .join(
                District,
                District.id == SubDistrict.district_id,
            )
            .where(
                District.state_id == state_id
            )
        )
    ).scalar_one()

    districts_result = await db.execute(
        select(District)
        .where(
            District.state_id == state_id
        )
        .order_by(District.name)
    )

    districts = [
        {
            "id": district.id,
            "code": district.code,
            "name": district.name,
            "state_id": district.state_id,
        }
        for district in districts_result.scalars().all()
    ]

    return StateAnalyticsResponse(
        state=StateResponse(
            id=state.id,
            code=state.code,
            name=state.name,
        ),
        district_count=district_count,
        sub_district_count=sub_district_count,
        village_count=village_count,
        districts=districts,
    )