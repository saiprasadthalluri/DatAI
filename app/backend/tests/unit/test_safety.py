"""Unit tests for safety service."""
import pytest
from app.services.safety import check


@pytest.mark.asyncio
async def test_safety_check_allowed():
    """Test safety check for allowed content."""
    result = await check("Hello, this is a normal message")
    assert result["allowed"] is True
    assert "labels" in result
    assert "reference_code" in result


@pytest.mark.asyncio
async def test_safety_check_empty():
    """Test safety check for empty content."""
    result = await check("")
    assert result["allowed"] is False
    assert result["reference_code"] == "SAFETY_001"


@pytest.mark.asyncio
async def test_safety_check_whitespace_only():
    """Test safety check for whitespace-only content."""
    result = await check("   \n\t  ")
    assert result["allowed"] is False


@pytest.mark.asyncio
async def test_safety_check_long_message():
    """Test safety check handles long messages."""
    long_message = "Hello " * 1000
    result = await check(long_message)
    assert "allowed" in result



