from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LAMBDA_URL_ORIGINAL: str
    QDRANT_URL_ORIGINAL: str
    QDRANT_API_KEY_ORIGINAL: str
    QDRANT_COLLECTION_ORIGINAL: str = "furniture_items"

    LAMBDA_URL_FINETUNED: str
    QDRANT_URL_FINETUNED: str
    QDRANT_API_KEY_FINETUNED: str
    QDRANT_COLLECTION_FINETUNED: str = "furniture_items"

    class Config:
        env_file = ".env"


settings = Settings()
