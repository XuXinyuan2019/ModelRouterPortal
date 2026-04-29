from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    ALIBABA_CLOUD_ACCESS_KEY_ID: str = ""
    ALIBABA_CLOUD_ACCESS_KEY_SECRET: str = ""
    ALIBABA_ENDPOINT: str = "aicontent.cn-beijing.aliyuncs.com"

    SECRET_KEY: str = "change-me-to-a-random-secret-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    DATABASE_URL: str = "sqlite:///./model_router_portal.db"
    FRONTEND_URL: str = "http://localhost:5173"
    MOCK_MODE: bool = True  # 开发环境使用 mock 数据，无需真实 AccessKey


settings = Settings()
