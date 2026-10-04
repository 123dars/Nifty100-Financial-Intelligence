from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.district import District
from app.models.state import State
from app.schemas.state import StateDetail, StateResponse

router = APIRouter(
    prefix="/states",
    tags=["States"],
)


async def _state_with_counts(db: AsyncSession, state_id: int) -> StateDetail:
    district_count_subq = (
        select(func.count(District.id))
        .where(District.state_id == State.id)
        .correlate(State)
        .scalar_subquery()
    )

    result = await db.execute(
        select(State, district_count_subq.label("district_count")).where(
            State.id == state_id
        )
    )
    row = result.first()

    if row is None:
        raise HTTPException(status_code=404, detail="State not found")

    state, district_count = row
    return StateDetail(
        id=state.id,
        code=state.code,
        name=state.name,
        district_count=district_count,
    )


@router.get("", response_model=list[StateResponse])
async def list_states(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> list[State]:
    stmt = select(State)
    if search:
        stmt = stmt.where(State.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(State.name).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{state_id}", response_model=StateDetail)
async def get_state(
    state_id: int,
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> StateDetail:
    return await _state_with_counts(db, state_id)
