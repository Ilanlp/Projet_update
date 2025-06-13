from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Snowflake
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_USER: str
    SNOWFLAKE_PASSWORD: str
    SNOWFLAKE_DATABASE: str
    SNOWFLAKE_SCHEMA: Optional[str] = "PUBLIC"
    SNOWFLAKE_WAREHOUSE: Optional[str] = "COMPUTE_WH"
    SNOWFLAKE_ROLE: Optional[str] = None

    # API
    API_TITLE: str = "Snowflake FastAPI"
    API_DESCRIPTION: str = "API pour interroger Snowflake avec FastAPI"
    API_VERSION: str = "0.1.0"
    
    # Authentification
    AUTH_USERNAME: str = "admin"
    AUTH_PASSWORD: str = "password123"

    # MLflow
    MLFLOW_MODEL_URL: str = "http://mlflow-model:5001"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )


settings = Settings()