# 🚀 GCP Deployment Guide - ChatApp

## Architecture on GCP

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Google Cloud Platform                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐  │
│   │  Cloud Run  │     │  Cloud Run  │     │   Firebase Hosting  │  │
│   │  (Backend)  │     │ (Frontend)  │ OR  │    (Frontend)       │  │
│   │   :8000     │     │   :5173     │     │                     │  │
│   └──────┬──────┘     └─────────────┘     └─────────────────────┘  │
│          │                                                          │
│          ├────────────────────┬────────────────────┐               │
│          ▼                    ▼                    ▼               │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐  │
│   │  Cloud SQL  │     │ Memorystore │     │   Secret Manager    │  │
│   │ (PostgreSQL)│     │   (Redis)   │     │    (API Keys)       │  │
│   └─────────────┘     └─────────────┘     └─────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed (for local testing)

---

## Step 1: Initial Setup

### 1.1 Set Project Variables

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="us-central1"

# Authenticate
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

---

## Step 2: Set Up Cloud SQL (PostgreSQL)

### 2.1 Create PostgreSQL Instance

```bash
# Create Cloud SQL instance
gcloud sql instances create chatapp-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION \
  --root-password=YOUR_SECURE_PASSWORD \
  --storage-size=10GB \
  --storage-type=SSD

# Create database
gcloud sql databases create chatapp --instance=chatapp-db

# Create user
gcloud sql users create chatapp \
  --instance=chatapp-db \
  --password=YOUR_DB_PASSWORD
```

### 2.2 Get Connection Info

```bash
# Get connection name
gcloud sql instances describe chatapp-db --format="value(connectionName)"
# Output: your-project:us-central1:chatapp-db
```

---

## Step 3: Set Up Cloud Memorystore (Redis)

```bash
# Create Redis instance
gcloud redis instances create chatapp-redis \
  --size=1 \
  --region=$REGION \
  --redis-version=redis_7_0 \
  --tier=basic

# Get Redis host IP
gcloud redis instances describe chatapp-redis \
  --region=$REGION \
  --format="value(host)"
```

---

## Step 4: Set Up Secret Manager

### 4.1 Create Secrets

```bash
# OpenRouter API Key
echo -n "sk-or-your-openrouter-key" | \
  gcloud secrets create openrouter-api-key --data-file=-

# Database Password
echo -n "YOUR_DB_PASSWORD" | \
  gcloud secrets create db-password --data-file=-

# Firebase (if using production Firebase)
echo -n "your-firebase-web-api-key" | \
  gcloud secrets create firebase-api-key --data-file=-
```

### 4.2 Grant Access to Cloud Run

```bash
# Get the compute service account
export SA_EMAIL="$(gcloud iam service-accounts list \
  --filter="displayName:Compute Engine default service account" \
  --format='value(email)')"

# Grant secret access
gcloud secrets add-iam-policy-binding openrouter-api-key \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Step 5: Deploy Backend to Cloud Run

### 5.1 Update Backend Dockerfile (if needed)

The existing Dockerfile should work. Verify it's at `app/backend/Dockerfile`.

### 5.2 Build and Deploy

```bash
cd app/backend

# Build and push to Artifact Registry
gcloud builds submit --tag gcr.io/$PROJECT_ID/chatapp-backend

# Deploy to Cloud Run
gcloud run deploy chatapp-backend \
  --image gcr.io/$PROJECT_ID/chatapp-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:$REGION:chatapp-db \
  --set-env-vars "ENV=production" \
  --set-env-vars "PROJECT_ID=$PROJECT_ID" \
  --set-env-vars "POSTGRES_HOST=/cloudsql/$PROJECT_ID:$REGION:chatapp-db" \
  --set-env-vars "POSTGRES_PORT=5432" \
  --set-env-vars "POSTGRES_DB=chatapp" \
  --set-env-vars "POSTGRES_USER=chatapp" \
  --set-env-vars "REDIS_URL=redis://REDIS_IP:6379/0" \
  --set-secrets "POSTGRES_PASSWORD=db-password:latest" \
  --set-secrets "INFERENCE_API_KEY=openrouter-api-key:latest" \
  --min-instances 0 \
  --max-instances 10 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60
```

### 5.3 Get Backend URL

```bash
gcloud run services describe chatapp-backend \
  --region $REGION \
  --format="value(status.url)"
# Output: https://chatapp-backend-xxxxx-uc.a.run.app
```

---

## Step 6: Deploy Frontend

### Option A: Deploy to Cloud Run

```bash
cd app/frontend

# Create production .env
echo "VITE_API_URL=https://chatapp-backend-xxxxx-uc.a.run.app/api/v1" > .env.production

# Build the app
npm run build

# Create a simple Dockerfile for static hosting
cat > Dockerfile.prod << 'EOF'
FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
EOF

# Create nginx config
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}
http {
    include /etc/nginx/mime.types;
    server {
        listen 8080;
        root /usr/share/nginx/html;
        index index.html;
        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF

# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/chatapp-frontend -f Dockerfile.prod

gcloud run deploy chatapp-frontend \
  --image gcr.io/$PROJECT_ID/chatapp-frontend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080
```

### Option B: Deploy to Firebase Hosting (Recommended for Frontend)

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase Hosting
firebase init hosting
# Select your project
# Set public directory to: dist
# Configure as SPA: Yes

# Build the app
npm run build

# Deploy
firebase deploy --only hosting
```

---

## Step 7: Update CORS Configuration

After deployment, update the backend CORS to allow your frontend domain:

```bash
# Update Cloud Run with frontend URL
gcloud run services update chatapp-backend \
  --region $REGION \
  --set-env-vars "FRONTEND_ORIGIN=https://your-frontend-url.web.app"
```

---

## Step 8: Run Database Migrations

```bash
# Connect to Cloud SQL via proxy
gcloud sql connect chatapp-db --user=chatapp --database=chatapp

# Or run migrations from Cloud Run job
gcloud run jobs create migrate-db \
  --image gcr.io/$PROJECT_ID/chatapp-backend \
  --region $REGION \
  --add-cloudsql-instances $PROJECT_ID:$REGION:chatapp-db \
  --set-env-vars "POSTGRES_HOST=/cloudsql/$PROJECT_ID:$REGION:chatapp-db" \
  --set-secrets "POSTGRES_PASSWORD=db-password:latest" \
  --command "alembic" \
  --args "upgrade,head"

gcloud run jobs execute migrate-db --region $REGION
```

---

## Quick Deploy Script

Save this as `deploy.sh` in your project root:

```bash
#!/bin/bash
set -e

PROJECT_ID="your-project-id"
REGION="us-central1"

echo "🚀 Deploying ChatApp to GCP..."

# Deploy Backend
echo "📦 Building backend..."
cd app/backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/chatapp-backend

echo "🚀 Deploying backend to Cloud Run..."
gcloud run deploy chatapp-backend \
  --image gcr.io/$PROJECT_ID/chatapp-backend \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated

BACKEND_URL=$(gcloud run services describe chatapp-backend --region $REGION --format="value(status.url)")
echo "✅ Backend deployed: $BACKEND_URL"

# Deploy Frontend
echo "📦 Building frontend..."
cd ../frontend
echo "VITE_API_URL=$BACKEND_URL/api/v1" > .env.production
npm run build

echo "🚀 Deploying frontend..."
firebase deploy --only hosting

echo "✅ Deployment complete!"
```

---

## Cost Estimation (Monthly)

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| Cloud Run (Backend) | 0-2 vCPU, 512MB | $0-50 |
| Cloud Run (Frontend) | Minimal | $0-10 |
| Cloud SQL | db-f1-micro | ~$10 |
| Memorystore Redis | 1GB Basic | ~$35 |
| Secret Manager | 6 secrets | ~$0.06 |
| **Total** | | **~$50-100/month** |

*With free tier and minimal usage, costs can be much lower.*

---

## Environment Variables Summary

### Backend (Cloud Run)

| Variable | Value |
|----------|-------|
| ENV | production |
| POSTGRES_HOST | /cloudsql/PROJECT:REGION:chatapp-db |
| POSTGRES_PORT | 5432 |
| POSTGRES_DB | chatapp |
| POSTGRES_USER | chatapp |
| POSTGRES_PASSWORD | (from Secret Manager) |
| REDIS_URL | redis://REDIS_IP:6379/0 |
| INFERENCE_API_KEY | (from Secret Manager) |
| FRONTEND_ORIGIN | https://your-frontend.web.app |

### Frontend

| Variable | Value |
|----------|-------|
| VITE_API_URL | https://chatapp-backend-xxx.run.app/api/v1 |
| VITE_FIREBASE_API_KEY | your-firebase-key |
| VITE_FIREBASE_PROJECT_ID | your-project-id |

---

## Troubleshooting

### Backend won't start
```bash
# Check logs
gcloud run services logs read chatapp-backend --region $REGION
```

### Database connection issues
```bash
# Verify Cloud SQL proxy is working
gcloud sql instances describe chatapp-db
```

### Redis connection issues
```bash
# Check VPC connector is set up
gcloud compute networks vpc-access connectors list
```

---

## Next Steps After Deployment

1. ✅ Set up custom domain
2. ✅ Configure Firebase Authentication for production
3. ✅ Set up monitoring and alerts
4. ✅ Configure CI/CD with Cloud Build triggers
5. ✅ Set up backup policies for Cloud SQL

