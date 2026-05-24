from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LAMBDA_URL_ORIGINAL: str
    LAMBDA_URL_FINETUNED: str
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "furniture_items"

    class Config:
        env_file = ".env"


settings = Settings()
