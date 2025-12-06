#!/bin/bash
# ChatApp GCP Deployment Script
# Usage: ./deploy-gcp.sh [PROJECT_ID] [REGION]

set -e

PROJECT_ID=${1:-$(gcloud config get-value project 2>/dev/null)}
REGION=${2:-"us-central1"}

echo "🚀 ChatApp GCP Deployment Script"
echo "================================="
echo ""
echo "📋 Configuration:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: PROJECT_ID is required"
    echo "Usage: ./deploy-gcp.sh PROJECT_ID [REGION]"
    exit 1
fi

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Set project
echo "⚙️ Setting project..."
gcloud config set project $PROJECT_ID

# Enable APIs
echo "⚙️ Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    containerregistry.googleapis.com

# Check/Create secrets
echo "🔐 Setting up secrets..."
for secret in inference-api-key db-password; do
    if ! gcloud secrets describe $secret &>/dev/null; then
        echo "   Creating secret: $secret"
        read -sp "   Enter value for $secret: " value
        echo
        echo -n "$value" | gcloud secrets create $secret --data-file=-
    else
        echo "   Secret exists: $secret"
    fi
done

# Deploy Backend
echo ""
echo "📦 Building and deploying backend..."
cd app/backend

echo "   Building Docker image..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/chatapp-backend"

echo "   Deploying to Cloud Run..."
gcloud run deploy chatapp-backend \
    --image "gcr.io/$PROJECT_ID/chatapp-backend" \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "ENV=production,PROJECT_ID=$PROJECT_ID,REGION=$REGION" \
    --set-secrets "INFERENCE_API_KEY=inference-api-key:latest"

BACKEND_URL=$(gcloud run services describe chatapp-backend --region $REGION --format="value(status.url)")
echo "✅ Backend deployed: $BACKEND_URL"

cd ../..

# Build Frontend
echo ""
echo "📦 Building frontend..."
cd app/frontend

# Create production env
echo "VITE_API_URL=$BACKEND_URL/api/v1" > .env.production

# Install and build
echo "   Installing dependencies..."
npm install

echo "   Building for production..."
npm run build

# Create Dockerfile
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
    default_type application/octet-stream;
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

echo "   Deploying frontend to Cloud Run..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/chatapp-frontend" -f Dockerfile.prod

gcloud run deploy chatapp-frontend \
    --image "gcr.io/$PROJECT_ID/chatapp-frontend" \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080

FRONTEND_URL=$(gcloud run services describe chatapp-frontend --region $REGION --format="value(status.url)")
echo "✅ Frontend deployed: $FRONTEND_URL"

# Update backend CORS
echo ""
echo "⚙️ Updating backend CORS..."
gcloud run services update chatapp-backend \
    --region $REGION \
    --update-env-vars "FRONTEND_ORIGIN=$FRONTEND_URL"

cd ../..

echo ""
echo "========================================"
echo "🎉 Deployment Complete!"
echo "========================================"
echo ""
echo "📱 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL:  $BACKEND_URL"
echo "📚 API Docs:     $BACKEND_URL/docs"
echo ""
echo "⚠️  Next Steps:"
echo "   1. Set up Cloud SQL for production database"
echo "   2. Configure Firebase Authentication"
echo "   3. Set up custom domain (optional)"
echo ""

