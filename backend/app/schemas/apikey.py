from pydantic import BaseModel


class ApiKeyCreateResponse(BaseModel):
    id: int | None
    api_key: str
    status: str
    created_at: str


class ApiKeyListItem(BaseModel):
    id: int | None
    api_key_preview: str
    status: str
    created_at: str | None
