"""Integration tests for health endpoint."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/v1/healthz")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]


@pytest.mark.asyncio
async def test_health_endpoint_details(client: AsyncClient):
    """Test health endpoint returns detailed status."""
    response = await client.get("/api/v1/healthz")
    
    data = response.json()
    # Should have status for each service
    assert isinstance(data["checks"]["database"], bool)
    assert isinstance(data["checks"]["redis"], bool)



