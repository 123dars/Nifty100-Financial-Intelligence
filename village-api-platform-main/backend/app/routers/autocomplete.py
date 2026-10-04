from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import verify_api_key
from app.models.api_key import ApiKey
from app.models.district import District
from app.models.state import State
from app.models.sub_district import SubDistrict
from app.models.village import Village
from app.schemas.autocomplete import (
    AutocompleteItem,
    AutocompleteResponse,
)

router = APIRouter(
    prefix="/autocomplete",
    tags=["Autocomplete"],
)

AUTOCOMPLETE_LIMIT = 25


@router.get(
    "",
    response_model=AutocompleteResponse,
)
async def autocomplete(
    q: str = Query(
        ...,
        min_length=2,
        description="Search village, code, sub-district, district, or state",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=AUTOCOMPLETE_LIMIT,
    ),
    db: AsyncSession = Depends(get_db),
    _: ApiKey = Depends(verify_api_key),
) -> AutocompleteResponse:

    search_text = q.strip()
    pattern = f"%{search_text}%"

    result = await db.execute(
        select(
            Village,
            SubDistrict,
            District,
            State,
        )
        .join(
            SubDistrict,
            Village.sub_district_id == SubDistrict.id,
        )
        .join(
            District,
            SubDistrict.district_id == District.id,
        )
        .join(
            State,
            District.state_id == State.id,
        )
        .where(
            or_(
                Village.name.ilike(pattern),

                cast(
                    Village.code,
                    String,
                ).ilike(pattern),

                SubDistrict.name.ilike(pattern),

                cast(
                    SubDistrict.code,
                    String,
                ).ilike(pattern),

                District.name.ilike(pattern),

                cast(
                    District.code,
                    String,
                ).ilike(pattern),

                State.name.ilike(pattern),

                cast(
                    State.code,
                    String,
                ).ilike(pattern),
            )
        )
        .order_by(
            Village.name.asc()
        )
        .limit(
            min(limit, AUTOCOMPLETE_LIMIT)
        )
    )

    rows = result.all()

    items: list[AutocompleteItem] = []

    for village, sub_district, district, state in rows:

        village_name = village.name or ""

        sub_district_name = (
            sub_district.name
            if sub_district
            else ""
        )

        district_name = (
            district.name
            if district
            else ""
        )

        state_name = (
            state.name
            if state
            else ""
        )

        village_code = (
            str(village.code)
            if village.code is not None
            else ""
        )

        full_address = ", ".join(
            filter(
                None,
                [
                    village_name,
                    sub_district_name,
                    district_name,
                    state_name,
                    "India",
                ],
            )
        )

        items.append(
            AutocompleteItem(
                value=f"village_{village_code}",
                label=village_name,
                fullAddress=full_address,
                hierarchy={
                    "village": village_name,
                    "subDistrict": sub_district_name,
                    "district": district_name,
                    "state": state_name,
                    "country": "India",
                },
            )
        )

    return AutocompleteResponse(
        count=len(items),
        data=items,
    )