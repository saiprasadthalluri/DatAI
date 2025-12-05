# ChatApp Backend

FastAPI backend for ChatGPT-like application.

## Setup

1. Install dependencies:
```bash
pip install -e ".[dev]"
```

2. Set up environment variables (copy from `.env.example`)

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start development server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest
```

## Linting

```bash
ruff check .
black .
mypy .
```

## Deployment

See `cloudbuild.yaml` for Cloud Build configuration.

Deploy to Cloud Run:
```bash
gcloud run deploy chatapp-backend --source .
```




