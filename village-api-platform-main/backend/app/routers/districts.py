from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.district import District
from app.models.state import State
from app.models.sub_district import SubDistrict
from app.schemas.district import DistrictDetail, DistrictResponse

router = APIRouter(
    prefix="",
    tags=["Districts"],
)


async def _district_with_counts(db: AsyncSession, district_id: int) -> DistrictDetail:
    sub_district_count_subq = (
        select(func.count(SubDistrict.id))
        .where(SubDistrict.district_id == District.id)
        .correlate(District)
        .scalar_subquery()
    )

    result = await db.execute(
        select(District, sub_district_count_subq.label("sub_district_count")).where(
            District.id == district_id
        )
    )
    row = result.first()

    if row is None:
        raise HTTPException(status_code=404, detail="District not found")

    district, sub_district_count = row
    return DistrictDetail(
        id=district.id,
        code=district.code,
        name=district.name,
        state_id=district.state_id,
        sub_district_count=sub_district_count,
    )


@router.get("/states/{state_id}/districts", response_model=list[DistrictResponse])
async def list_districts_by_state(
    state_id: int,
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> list[District]:
    state = await db.get(State, state_id)
    if state is None:
        raise HTTPException(status_code=404, detail="State not found")

    stmt = select(District).where(District.state_id == state_id)
    if search:
        stmt = stmt.where(District.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(District.name).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/districts/{district_id}", response_model=DistrictDetail)
async def get_district(
    district_id: int,
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> DistrictDetail:
    return await _district_with_counts(db, district_id)