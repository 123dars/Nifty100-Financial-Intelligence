from pydantic import BaseModel


class AutocompleteItem(BaseModel):
    value: str
    label: str
    fullAddress: str
    hierarchy: dict


class AutocompleteResponse(BaseModel):
    success: bool = True
    count: int
    data: list[AutocompleteItem]
