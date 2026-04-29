from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.apikey import ApiKeyCreateResponse, ApiKeyListItem
from app.services import apikey_service

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])

MOCK_CLIENT_ID = 10001  # mock client_id for users without real Alibaba Cloud client


def _get_client_id(user: User) -> int:
    return user.client_id if user.client_id else MOCK_CLIENT_ID + user.id


@router.get("/", response_model=list[ApiKeyListItem])
def list_keys(current_user: User = Depends(get_current_user)):
    client_id = _get_client_id(current_user)
    return apikey_service.list_api_keys(client_id)


@router.post("/", response_model=ApiKeyCreateResponse)
def create_key(current_user: User = Depends(get_current_user)):
    client_id = _get_client_id(current_user)
    result = apikey_service.create_api_key(client_id)
    return ApiKeyCreateResponse(
        id=result["id"],
        api_key=result["api_key"],
        status=result["status"],
        created_at=result["created_at"],
    )


@router.delete("/{key_id}")
def delete_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
):
    client_id = _get_client_id(current_user)
    try:
        apikey_service.delete_api_key(key_id, client_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "API Key deleted"}
