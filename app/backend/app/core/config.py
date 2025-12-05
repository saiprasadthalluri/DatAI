"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from .models_hidden import get_model_registry, get_inference_base_url, get_inference_api_key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    """Application settings loaded from environment variables."""
    
    # General
    env: str = "development"
    project_id: str = "your-gcp-project"
    region: str = "us-central1"
    frontend_origin: str = "http://localhost:5173,http://localhost:5174"
    
    # Auth
    firebase_project_id: str = "your-firebase-project"
    firebase_web_api_key: str = "placeholder"
    firebase_auth_emulator_host: Optional[str] = None
    
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "chatapp"
    postgres_user: str = "chatapp"
    postgres_password: str = "chatapp"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Model Configuration - Use friendly names only
    # Actual model IDs are hidden in models_hidden.py
    # These are just for backward compatibility - use models_hidden.py instead
    model_theory: str = "theory_model"  # Hidden - see models_hidden.py
    model_code: str = "code_model"  # Hidden - see models_hidden.py
    model_math: str = "math_model"  # Hidden - see models_hidden.py
    model_safety: str = "safety_model"  # Hidden - see models_hidden.py
    
    # Safety (PLACEHOLDERS)
    safety_api_url: str = "https://safety-placeholder/v1/check"
    safety_api_key: str = "PLACEHOLDER"
    
    # GCS (optional)
    gcs_bucket_raw: Optional[str] = None
    
    # Router
    router_strategy: str = "moe"  # "best" or "moe"
    
    # Rate limiting
    rate_limit_per_user: int = 60  # requests per minute
    rate_limit_per_ip: int = 10  # requests per minute
    
    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def model_registry(self) -> dict[str, str]:
        """Map friendly names to actual model IDs (from hidden config)."""
        hidden_registry = get_model_registry()
        return {
            "theory-specialist": hidden_registry["theory_model"],
            "code-specialist": hidden_registry["code_model"],
            "math-specialist": hidden_registry["math_model"],
            "safety-classifier": hidden_registry["safety_model"],
        }
    
    @property
    def inference_base_url(self) -> str:
        """Get inference base URL from hidden config."""
        return get_inference_base_url()
    
    @property
    def inference_api_key(self) -> str:
        """Get inference API key from hidden config."""
        return get_inference_api_key()
    


settings = Settings()

