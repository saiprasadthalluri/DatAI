"""
Hidden model configuration - DO NOT EXPOSE ACTUAL MODEL NAMES/APIS.
This file contains the actual model IDs and API endpoints.
All other code should reference models as: math_model, code_model, theory_model
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

# Actual model IDs (loaded from environment or defaults)
_MATH_MODEL_ID = os.getenv("MODEL_MATH", "google/gemma-3-12b-it")
_CODE_MODEL_ID = os.getenv("MODEL_CODE", "qwen/qwen-2.5-coder-32b-instruct")
_THEORY_MODEL_ID = os.getenv("MODEL_THEORY", "qwen/qwen-2.5-72b-instruct")
_SAFETY_MODEL_ID = os.getenv("MODEL_SAFETY", "meta-llama/llama-guard-3-8b")

# Actual API configuration (loaded from environment)
_INFERENCE_BASE_URL = os.getenv("INFERENCE_BASE_URL", "https://openrouter.ai/api/v1")
_INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY", "PLACEHOLDER")


def get_math_model_id() -> str:
    """Get the actual math model ID."""
    return _MATH_MODEL_ID


def get_code_model_id() -> str:
    """Get the actual code model ID."""
    return _CODE_MODEL_ID


def get_theory_model_id() -> str:
    """Get the actual theory model ID."""
    return _THEORY_MODEL_ID


def get_safety_model_id() -> str:
    """Get the actual safety model ID."""
    return _SAFETY_MODEL_ID


def get_inference_base_url() -> str:
    """Get the actual inference API base URL."""
    return _INFERENCE_BASE_URL


def get_inference_api_key() -> str:
    """Get the actual inference API key."""
    return _INFERENCE_API_KEY


def get_model_registry() -> Dict[str, str]:
    """
    Get model registry mapping friendly names to actual model IDs.
    Friendly names: math_model, code_model, theory_model, safety_model
    """
    return {
        "math_model": _MATH_MODEL_ID,
        "code_model": _CODE_MODEL_ID,
        "theory_model": _THEORY_MODEL_ID,
        "safety_model": _SAFETY_MODEL_ID,
    }

