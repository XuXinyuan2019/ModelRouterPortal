import os

from alibabacloud_aicontent20240611.client import Client
from alibabacloud_tea_openapi import models as open_api_models

from app.config import settings

_client: Client | None = None


def get_alicloud_client() -> Client:
    global _client
    if _client is None:
        config = open_api_models.Config(
            access_key_id=settings.ALIBABA_CLOUD_ACCESS_KEY_ID,
            access_key_secret=settings.ALIBABA_CLOUD_ACCESS_KEY_SECRET,
        )
        config.endpoint = settings.ALIBABA_ENDPOINT
        _client = Client(config)
    return _client
