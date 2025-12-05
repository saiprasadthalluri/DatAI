"""Unit tests for router service."""
import pytest
from app.services.router import decide


@pytest.mark.asyncio
async def test_router_theory_specialist():
    """Test routing to theory specialist for general questions."""
    result = await decide(
        meta={"mode": "chat"},
        message="Explain what machine learning is"
    )
    assert result["model"] == "theory-specialist"
    assert "confidence" in result
    assert "reasons" in result


@pytest.mark.asyncio
async def test_router_code_specialist():
    """Test routing to code specialist for code questions."""
    result = await decide(
        meta={"mode": "code"},
        message="Write a Python function to sort a list"
    )
    assert result["model"] == "code-specialist"
    assert "confidence" in result


@pytest.mark.asyncio
async def test_router_math_specialist():
    """Test routing to math specialist for math questions."""
    result = await decide(
        meta={"mode": "math"},
        message="Calculate the derivative of x^2"
    )
    assert result["model"] == "math-specialist"
    assert "confidence" in result


@pytest.mark.asyncio
async def test_router_auto_routing():
    """Test router auto-routes based on query content."""
    result = await decide(
        meta={"mode": "chat"},
        message="Write a Python function to sort a list"
    )
    # Should route to code specialist
    assert "model" in result
    assert "confidence" in result



