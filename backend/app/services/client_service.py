"""Alibaba Cloud ModelRouter client creation service."""
from alibabacloud_aicontent20240611 import models as aicontent_models

from app.services.alicloud_client import get_alicloud_client


def create_cloud_client(name: str) -> dict:
    """
    Create a client on Alibaba Cloud ModelRouter.

    Returns a dict with:
        - id (int): Alibaba Cloud client ID
        - client_uuid (str): Alibaba Cloud client UUID
    """
    client = get_alicloud_client()
    req = aicontent_models.ModelRouterCreateClientRequest(name=name)
    resp = client.model_router_create_client(req)
    body = resp.body
    if not body or not body.success:
        raise Exception(body.err_message or "Failed to create Alibaba Cloud client")
    data = body.data
    return {
        "id": getattr(data, "id", None),
        "client_uuid": getattr(data, "client_uuid", None),
    }
