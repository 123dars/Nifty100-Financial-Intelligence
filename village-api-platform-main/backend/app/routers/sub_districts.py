from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.district import District
from app.models.sub_district import SubDistrict
from app.models.village import Village
from app.schemas.sub_district import SubDistrictDetail, SubDistrictResponse

router = APIRouter(
    prefix="",
    tags=["Sub-Districts"],
)


async def _sub_district_with_counts(
    db: AsyncSession, sub_district_id: int
) -> SubDistrictDetail:
    village_count_subq = (
        select(func.count(Village.id))
        .where(Village.sub_district_id == SubDistrict.id)
        .correlate(SubDistrict)
        .scalar_subquery()
    )

    result = await db.execute(
        select(SubDistrict, village_count_subq.label("village_count")).where(
            SubDistrict.id == sub_district_id
        )
    )
    row = result.first()

    if row is None:
        raise HTTPException(status_code=404, detail="Sub-district not found")

    sub_district, village_count = row
    return SubDistrictDetail(
        id=sub_district.id,
        code=sub_district.code,
        name=sub_district.name,
        district_id=sub_district.district_id,
        village_count=village_count,
    )


@router.get(
    "/districts/{district_id}/sub-districts", response_model=list[SubDistrictResponse]
)
async def list_sub_districts_by_district(
    district_id: int,
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> list[SubDistrict]:
    district = await db.get(District, district_id)
    if district is None:
        raise HTTPException(status_code=404, detail="District not found")

    stmt = select(SubDistrict).where(SubDistrict.district_id == district_id)
    if search:
        stmt = stmt.where(SubDistrict.name.ilike(f"%{search}%"))
    stmt = (
        stmt.order_by(SubDistrict.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/sub-districts/{sub_district_id}", response_model=SubDistrictDetail)
async def get_sub_district(
    sub_district_id: int,
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> SubDistrictDetail:
    return await _sub_district_with_counts(db, sub_district_id)