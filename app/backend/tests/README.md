# Backend Testing Guide

## Quick Start

### 1. Create Test Database
```bash
# Using Docker Compose
docker-compose -f ../../infra/docker-compose.dev.yml up -d postgres

# Create test database
psql -h localhost -U chatapp -d postgres -c "CREATE DATABASE chatapp_test;"
```

### 2. Run Tests
```bash
# Install dependencies (already done)
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_router.py -v

# Run tests in watch mode
pytest-watch
```

### 3. Test Structure
```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── unit/                # Unit tests (isolated)
│   ├── test_router.py
│   └── test_safety.py
├── integration/         # Integration tests (with DB)
│   ├── test_chat.py
│   └── test_conversations.py
└── fixtures/            # Test data
    └── sample_data.py
```

### 4. Writing Tests

#### Example Unit Test
```python
# tests/unit/test_router.py
import pytest
from app.services.router import decide

@pytest.mark.asyncio
async def test_router_decides_best_model():
    result = await decide({"mode": "chat"}, "Hello")
    assert result["strategy"] == "best"
```

#### Example Integration Test
```python
# tests/integration/test_chat.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_chat_endpoint(client: AsyncClient):
    response = await client.post(
        "/api/v1/chat/send",
        json={"message": "Hello", "meta": {"mode": "chat"}},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
```

### 5. Environment Variables for Testing
Create `tests/.env.test`:
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=chatapp_test
POSTGRES_USER=chatapp
POSTGRES_PASSWORD=chatapp
REDIS_URL=redis://localhost:6379/1
ENV=test
```

### 6. Mock External Services
```python
# Use pytest fixtures to mock LLM client
@pytest.fixture
def mock_llm_client(monkeypatch):
    async def mock_chat(*args, **kwargs):
        return {"response": "Mocked response"}
    mock_client = AsyncMock()
    mock_client.chat_completion = mock_chat
    monkeypatch.setattr("app.services.llm_client.get_llm_client", lambda: mock_client)
```

### 7. CI/CD Integration
Tests run automatically in GitHub Actions (see `.github/workflows/ci.yml`)



