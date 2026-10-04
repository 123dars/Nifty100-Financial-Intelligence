from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.district import District
from app.models.state import State
from app.models.sub_district import SubDistrict
from app.models.village import Village
from app.schemas.search import SearchResponse

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)

SEARCH_LIMIT = 20


@router.get("", response_model=SearchResponse)
async def global_search(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> SearchResponse:
    pattern = f"%{q}%"
    limit = min(page_size, SEARCH_LIMIT)
    offset = (page - 1) * limit

    states_result = await db.execute(
        select(State)
        .where(State.name.ilike(pattern))
        .order_by(State.name)
        .offset(offset)
        .limit(limit)
    )
    states = [
        {"id": s.id, "code": s.code, "name": s.name}
        for s in states_result.scalars().all()
    ]

    districts_result = await db.execute(
        select(District)
        .where(District.name.ilike(pattern))
        .order_by(District.name)
        .offset(offset)
        .limit(limit)
    )
    districts = [
        {"id": d.id, "code": d.code, "name": d.name, "state_id": d.state_id}
        for d in districts_result.scalars().all()
    ]

    sub_districts_result = await db.execute(
        select(SubDistrict)
        .where(SubDistrict.name.ilike(pattern))
        .order_by(SubDistrict.name)
        .offset(offset)
        .limit(limit)
    )
    sub_districts = [
        {
            "id": s.id,
            "code": s.code,
            "name": s.name,
            "district_id": s.district_id,
        }
        for s in sub_districts_result.scalars().all()
    ]

    villages_result = await db.execute(
        select(Village)
        .where(Village.name.ilike(pattern))
        .order_by(Village.name)
        .offset(offset)
        .limit(limit)
    )
    villages = [
        {
            "id": v.id,
            "code": v.code,
            "name": v.name,
            "sub_district_id": v.sub_district_id,
        }
        for v in villages_result.scalars().all()
    ]

    return SearchResponse(
        states=states,
        districts=districts,
        sub_districts=sub_districts,
        villages=villages,
    )
