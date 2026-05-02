"""Chat proxy endpoint — streams chat completions via Alibaba Cloud ModelRouter.

Uses the user's API Key for authentication (Bearer token) against the
OpenAI-compatible endpoint at model-router.edu-aliyun.com/v1.
"""

import json
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user, get_db, require_positive_balance
from app.models.activation import UserModelActivation
from app.models.user import User
from app.services import apikey_service, usage_service
from app.services.billing_service import calculate_cost

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


class ChatRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    stream: bool = True


def _is_model_activated(db: Session, user_id: int, model_id: str) -> bool:
    return (
        db.query(UserModelActivation)
        .filter(
            UserModelActivation.user_id == user_id,
            UserModelActivation.model_id == model_id,
            UserModelActivation.status == "active",
        )
        .first()
        is not None
    )


def _get_user_api_key(client_id: int) -> str:
    """Get an active API key value for the user's Alibaba Cloud client."""
    try:
        keys = apikey_service.list_api_keys(client_id)
        for key in keys:
            if key.get("status") == "active":
                key_id = key.get("id")
                if key_id is not None:
                    revealed = apikey_service.copy_api_key(key_id)
                    api_key = revealed.get("api_key")
                    if api_key:
                        return api_key
    except Exception as e:
        logger.warning("Failed to get API key for client %s: %s", client_id, e)
    return ""


# ModelRouter uses "qwen/" prefix for all models on the OpenAI-compatible endpoint
_UPSTREAM_MODEL_MAP: dict[str, str] = {
    "qwen3.6-plus": "qwen/qwen3.6-plus",
    "qwen3-max": "qwen/qwen3-max",
    "kimi-k2.6": "qwen/kimi-k2.6",
    "deepseek-v4-pro": "qwen/deepseek-v4-pro",
}

CHAT_URL = f"{settings.ALIBABA_CHAT_BASE_URL}/chat/completions"


@router.post("/completions")
def chat_completions(
    req: ChatRequest,
    current_user: User = Depends(require_positive_balance),
    db: Session = Depends(get_db),
):
    # Validate model is activated
    if not _is_model_activated(db, current_user.id, req.model):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="模型未开通 / Model not activated",
        )

    # Get user's API key
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未绑定阿里云客户端 / Alibaba Cloud client not bound",
        )

    api_key = _get_user_api_key(current_user.client_id)
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无可用 API Key，请先创建 / No API Key available, please create one",
        )

    # Map model name for upstream
    upstream_model = _UPSTREAM_MODEL_MAP.get(req.model, f"qwen/{req.model}")

    request_body: dict[str, Any] = {
        "model": upstream_model,
        "messages": req.messages,
        "stream": req.stream,
    }
    if req.stream:
        request_body["stream_options"] = {"include_usage": True}

    upstream_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if not req.stream:
        # Non-streaming
        try:
            resp = httpx.post(
                CHAT_URL,
                json=request_body,
                headers=upstream_headers,
                timeout=60.0,
            )
        except httpx.RequestError as e:
            logger.error("Chat upstream request error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="上游请求失败 / Upstream request failed",
            )

        if resp.status_code != 200:
            logger.error("Chat upstream returned %d: %s", resp.status_code, resp.text[:500])
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"上游错误 / Upstream error: {resp.text[:200]}",
            )

        data = resp.json()
        usage_info = data.get("usage", {})
        tokens_input = usage_info.get("prompt_tokens", 0)
        tokens_output = usage_info.get("completion_tokens", 0)
        if tokens_input or tokens_output:
            cost = calculate_cost(req.model, tokens_input, tokens_output)
            usage_service.record_usage(db, current_user.id, req.model, tokens_input, tokens_output, cost, request_type="chat")
            usage_service.deduct_balance(db, current_user, cost)
            usage_service.check_and_enforce_balance_limit(db, current_user)
        return data

    # Streaming
    def _stream_generator():
        total_content = ""
        tokens_input = 0
        tokens_output = 0
        try:
            with httpx.stream(
                "POST",
                CHAT_URL,
                json=request_body,
                headers=upstream_headers,
                timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
            ) as resp:
                if resp.status_code != 200:
                    error_text = ""
                    for chunk in resp.iter_bytes():
                        error_text += chunk.decode("utf-8", errors="replace")
                    yield f"data: {json.dumps({'error': f'HTTP {resp.status_code}: {error_text[:200]}'})}\n\n"
                    return

                for line in resp.iter_lines():
                    if not line.strip():
                        continue

                    # Forward SSE line as-is
                    yield f"{line}\n\n"

                    # Parse for token counting
                    trimmed = line.strip()
                    if not trimmed.startswith("data:"):
                        continue
                    payload = trimmed[5:].strip()
                    if payload == "[DONE]":
                        continue
                    try:
                        parsed = json.loads(payload)
                        usage_info = parsed.get("usage")
                        if isinstance(usage_info, dict):
                            tokens_input = usage_info.get("prompt_tokens", 0)
                            tokens_output = usage_info.get("completion_tokens", 0)
                        choices = parsed.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            if isinstance(delta, dict):
                                content = delta.get("content") or ""
                                reasoning = delta.get("reasoning_content") or ""
                                if content:
                                    total_content += content
                                if reasoning:
                                    total_content += reasoning
                    except (json.JSONDecodeError, TypeError, IndexError):
                        pass

        except httpx.RequestError as e:
            logger.error("Chat upstream stream error: %s", e)
            yield f"data: {json.dumps({'error': '上游连接失败 / Upstream connection failed'})}\n\n"
            return
        finally:
            if not tokens_output and total_content:
                tokens_output = max(1, len(total_content) // 2)
            if tokens_input or tokens_output:
                try:
                    cost = calculate_cost(req.model, tokens_input, tokens_output)
                    if cost > 0:
                        usage_service.record_usage(
                            db, current_user.id, req.model,
                            tokens_input, tokens_output, cost,
                            request_type="chat",
                        )
                        usage_service.deduct_balance(db, current_user, cost)
                        usage_service.check_and_enforce_balance_limit(db, current_user)
                except Exception as e:
                    logger.warning("Failed to record usage after chat: %s", e)

    return StreamingResponse(
        _stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
