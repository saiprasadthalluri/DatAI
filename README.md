# DatAI - Data Science Domain Expert

A full-stack production-quality domain expert application, built with FastAPI backend and React frontend.

## Architecture

- **Backend**: FastAPI (Python 3.11) with async PostgreSQL, Redis, Firebase Auth
- **Frontend**: React + Vite + TypeScript with TailwindCSS and shadcn/ui
- **Database**: PostgreSQL (Cloud SQL in production)
- **Cache**: Redis (Cloud Memorystore in production)
- **Auth**: Firebase Authentication
- **Deployment**: Cloud Run (backend), Firebase Hosting or Cloud Run (frontend)
- **CI/CD**: GitHub Actions + Cloud Build

## Features

- ✅ User authentication (Firebase Auth with Google + email/password)
- ✅ Chat interface
- ✅ Conversation history and management
- ✅ Safety layer (Llama Guard)
- ✅ Router logic (routes to specialist models: theory, code, math)
- ✅ Rate limiting (Redis-based)
- ✅ Observability (OpenTelemetry, Prometheus metrics)
- ✅ Production-ready security (CORS, headers, JWT verification)

## Selected Models

We divided data science questions broadly into 3 categories i.e Theory, Code and Math. Tested more than 15 models for each category on benchmark datasets and selected one model for each category 

- **Theory**: Qwen2.5-7B-Instruct Model
- **Code**: Seedcoder-8B-Instruct Model
- **Math**: Qwen2.5-7B-math-Instruct Model

## Project Structure

```
/app
  /frontend          # React + Vite + TypeScript
  /backend           # FastAPI application
/infra               # Docker compose, Cloud Build configs
/.github/workflows   # CI/CD pipelines
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- PostgreSQL (or use Docker)
- Redis (or use Docker)

### Local Development

1. **Clone and setup environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

2. **Start infrastructure** (PostgreSQL, Redis):
```bash
docker-compose -f infra/docker-compose.dev.yml up -d postgres redis
```

3. **Backend setup**:
```bash
cd app/backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

4. **Frontend setup**:
```bash
cd app/frontend
npm install
npm run dev
```

5. **Access the application**:
- Frontend: https://chatapp-frontend-301170991982.us-central1.run.app 
- Backend API: https://chatapp-backend-301170991982.us-central1.run.app
- API Docs: https://chatapp-backend-301170991982.us-central1.run.app/docs

### Using Docker Compose (All Services)

```bash
docker-compose -f infra/docker-compose.dev.yml up
```

## Configuration

See `.env.example` for all environment variables. Key settings:

- **Firebase**: Set `FIREBASE_PROJECT_ID` and `FIREBASE_WEB_API_KEY`
- **Database**: Configure PostgreSQL connection
- **Safety API**: llamaguard API

## API Endpoints

### Auth
- `GET /api/v1/auth/me` - Get current user profile

### Conversations
- `GET /api/v1/conversations` - List conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation with messages
- `PATCH /api/v1/conversations/{id}` - Update conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation

### Chat
- `POST /api/v1/chat/send` - Send message and get response

### Health & Admin
- `GET /api/v1/healthz` - Health check
- `GET /api/v1/admin/metrics` - Prometheus metrics
- `GET /api/v1/admin/config` - Configuration (admin only)

## Configuration

Configure environment variables for:
- **LLM Inference**: Set `INFERENCE_BASE_URL` and `INFERENCE_API_KEY`
- **Safety**: Set `SAFETY_API_KEY` for content moderation

## Testing

### Backend
```bash
cd app/backend
pytest
```

### Frontend
```bash
cd app/frontend
npm test
npm run test:e2e  # Playwright E2E tests
```

## Deployment

### Backend to Google Cloud Run

1. **Build and push image**:
```bash
gcloud builds submit --config app/backend/cloudbuild.yaml
```

2. **Or deploy directly**:
```bash
gcloud run deploy chatapp-backend --source app/backend
```

### Frontend

Deploy Google Cloud Run (static site).

## Security

- Firebase JWT tokens verified on every request
- CORS locked to frontend origin
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- Rate limiting (per user and per IP)
- SQL injection protection (SQLAlchemy ORM)
- Input/output safety checks

## Observability

- **Logging**: Structured JSON logs (Cloud Logging in production)
- **Tracing**: OpenTelemetry → Cloud Trace
- **Metrics**: Prometheus endpoint at `/api/v1/admin/metrics`

## License

MIT




