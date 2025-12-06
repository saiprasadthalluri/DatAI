"""
Model configuration - loads from environment variables.
All model IDs and API endpoints are configured via environment.
"""
import os
from pathlib import Path
from typing import Dict

# Load .env file to get environment variables
from dotenv import load_dotenv

# Find and load the .env file from the backend directory
_backend_dir = Path(__file__).parent.parent.parent
_env_file = _backend_dir / ".env"
if _env_file.exists():
    load_dotenv(_env_file)

# Model IDs (loaded from environment)
_MATH_MODEL_ID = os.getenv("MODEL_MATH", "math-specialist")
_CODE_MODEL_ID = os.getenv("MODEL_CODE", "code-specialist")
_THEORY_MODEL_ID = os.getenv("MODEL_THEORY", "theory-specialist")
_SAFETY_MODEL_ID = os.getenv("MODEL_SAFETY", "safety-model")

# API configuration (loaded from environment)
_INFERENCE_BASE_URL = os.getenv("INFERENCE_BASE_URL", "")
_INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY", "")


def get_math_model_id() -> str:
    """Get the math model ID."""
    return _MATH_MODEL_ID


def get_code_model_id() -> str:
    """Get the code model ID."""
    return _CODE_MODEL_ID


def get_theory_model_id() -> str:
    """Get the theory model ID."""
    return _THEORY_MODEL_ID


def get_safety_model_id() -> str:
    """Get the safety model ID."""
    return _SAFETY_MODEL_ID


def get_inference_base_url() -> str:
    """Get the inference API base URL."""
    return _INFERENCE_BASE_URL


def get_inference_api_key() -> str:
    """Get the inference API key."""
    return _INFERENCE_API_KEY


def get_model_registry() -> Dict[str, str]:
    """
    Get model registry mapping friendly names to model IDs.
    """
    return {
        "math_model": _MATH_MODEL_ID,
        "code_model": _CODE_MODEL_ID,
        "theory_model": _THEORY_MODEL_ID,
        "safety_model": _SAFETY_MODEL_ID,
    }
