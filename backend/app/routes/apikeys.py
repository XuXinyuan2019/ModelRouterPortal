from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.apikey import ApiKeyCreateResponse, ApiKeyListItem
from app.services import apikey_service

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


def _get_client_id(user: User) -> int:
    if not user.client_id:
        raise HTTPException(
            status_code=403,
            detail="User has no Alibaba Cloud client binding. Please contact admin.",
        )
    return user.client_id


@router.get("/", response_model=list[ApiKeyListItem])
def list_keys(current_user: User = Depends(get_current_user)):
    client_id = _get_client_id(current_user)
    return apikey_service.list_api_keys(client_id)


@router.post("/", response_model=ApiKeyCreateResponse)
def create_key(current_user: User = Depends(get_current_user)):
    client_id = _get_client_id(current_user)
    try:
        result = apikey_service.create_api_key(client_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiKeyCreateResponse(
        id=result["id"],
        api_key=result["api_key"],
        status=result["status"],
        created_at=result["created_at"],
    )


@router.post("/{key_id}/copy")
def copy_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
):
    client_id = _get_client_id(current_user)
    try:
        result = apikey_service.copy_api_key(key_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "id": result["id"],
        "api_key": result["api_key"],
        "api_key_preview": result["api_key_preview"],
        "status": result["status"],
        "created_at": result["created_at"],
    }


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
