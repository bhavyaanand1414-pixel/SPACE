from typing import List, Union, Optional
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Metadata
    APP_NAME: str = "SIH1518 Change Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False  # M-4 FIX: default is secure-off; set DEBUG=true in .env for development
    API_V1_STR: str = "/api/v1"
    # H-2 FIX: No default SECRET_KEY. pydantic-settings will raise ValidationError
    # on startup if SECRET_KEY is missing from the environment, preventing insecure
    # deployments with a well-known public signing key.
    SECRET_KEY: str

    # CORS Allowed Origins
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sih1518_gis"

    # Storage Paths & S3 / Cloudflare R2 Configuration
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    LOCAL_STORAGE_PATH: str = "./data/storage"
    REPORTS_STORAGE_PATH: str = "./reports"
    S3_ENDPOINT_URL: Optional[str] = None  # e.g., https://<account_id>.r2.cloudflarestorage.com
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: str = "sih1518-storage"
    S3_REGION_NAME: str = "auto"
    S3_CUSTOM_DOMAIN: Optional[str] = None  # e.g., storage.yourdomain.com

    # Machine Learning Device
    MODEL_DEVICE: str = "auto"
    MODEL_CHECKPOINT_DIR: str = "./ml/checkpoints"
    BASELINE_CONFIDENCE_THRESHOLD: float = 0.65

    # Redis URL
    REDIS_URL: str = "redis://localhost:6379/0"

    # Semantic Embedding Engine (PS 26227 §2.2.1 — fully offline)
    EMBEDDING_MODEL_NAME: str = "ViT-B-32"
    EMBEDDING_PRETRAINED: str = "laion2b_s34b_b79k"
    EMBEDDING_WEIGHTS_PATH: str = "./ml/checkpoints/clip"
    EMBEDDING_DIMENSION: int = 512

    # FAISS Vector Index (PS 26227 §2.2.6)
    FAISS_INDEX_PATH: str = "./data/faiss_index"
    FAISS_INDEX_TYPE: str = "IVFFlat"  # IVFFlat, HNSW, or Flat
    FAISS_NPROBE: int = 10

    # Tile Processing
    TILE_SIZE: int = 256
    TILE_OVERLAP: int = 32

    # Ingestion
    INGESTION_WATCH_DIR: Optional[str] = None
    SCENES_STORAGE_PATH: str = "./data/scenes"


settings = Settings()
