from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.sub_district import SubDistrict
from app.models.village import Village
from app.schemas.village import VillageResponse


router = APIRouter(
    prefix="",
    tags=["Villages"],
)


# ============================================================
# VILLAGES BY SUB-DISTRICT
# ============================================================

@router.get(
    "/sub-districts/{sub_district_id}/villages",
    response_model=list[VillageResponse],
)
async def list_villages_by_sub_district(
    sub_district_id: int,
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> list[Village]:

    # Check whether the sub-district exists
    sub_district = await db.get(SubDistrict, sub_district_id)

    if sub_district is None:
        raise HTTPException(
            status_code=404,
            detail="Sub-district not found",
        )

    # Base query
    stmt = select(Village).where(
        Village.sub_district_id == sub_district_id
    )

    # Partial village-name search
    if search and search.strip():
        stmt = stmt.where(
            Village.name.ilike(f"%{search.strip()}%")
        )

    # Sort villages alphabetically
    stmt = stmt.order_by(Village.name.asc())

    # Backend pagination
    stmt = stmt.offset(
        (page - 1) * page_size
    ).limit(page_size)

    result = await db.execute(stmt)

    return list(result.scalars().all())


# ============================================================
# GLOBAL VILLAGE SEARCH
# ============================================================

@router.get(
    "/villages",
    response_model=list[VillageResponse],
)
async def search_villages(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> list[Village]:

    # Base query
    stmt = select(Village)

    # Partial village-name search
    if search and search.strip():
        stmt = stmt.where(
            Village.name.ilike(f"%{search.strip()}%")
        )

    # Sort alphabetically
    stmt = stmt.order_by(Village.name.asc())

    # Backend pagination
    stmt = stmt.offset(
        (page - 1) * page_size
    ).limit(page_size)

    result = await db.execute(stmt)

    return list(result.scalars().all())