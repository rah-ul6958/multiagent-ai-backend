import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Backend is healthy"


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Multi-Agent AI" in data["message"]
    assert "version" in data


@pytest.mark.asyncio
async def test_docs_available(client):
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_redoc_available(client):
    response = await client.get("/redoc")
    assert response.status_code == 200
