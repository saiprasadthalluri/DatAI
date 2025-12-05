# ChatApp GCP Deployment Script (PowerShell)
# Usage: .\deploy-gcp.ps1

param(
    [string]$ProjectId = "",
    [string]$Region = "us-central1"
)

Write-Host "🚀 ChatApp GCP Deployment Script" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if gcloud is installed
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ gcloud CLI is not installed. Please install it first:" -ForegroundColor Red
    Write-Host "   https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Get project ID
if (-not $ProjectId) {
    $ProjectId = gcloud config get-value project 2>$null
    if (-not $ProjectId) {
        $ProjectId = Read-Host "Enter your GCP Project ID"
    }
}

Write-Host "`n📋 Configuration:" -ForegroundColor Green
Write-Host "   Project ID: $ProjectId"
Write-Host "   Region: $Region"

# Confirm
$confirm = Read-Host "`nContinue with deployment? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

# Set project
Write-Host "`n⚙️ Setting project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable APIs
Write-Host "`n⚙️ Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    sqladmin.googleapis.com `
    secretmanager.googleapis.com `
    containerregistry.googleapis.com

# Check if secrets exist, if not create them
Write-Host "`n🔐 Setting up secrets..." -ForegroundColor Yellow

$secrets = @("openrouter-api-key", "db-password")
foreach ($secret in $secrets) {
    $exists = gcloud secrets describe $secret 2>$null
    if (-not $exists) {
        Write-Host "   Creating secret: $secret" -ForegroundColor Gray
        $value = Read-Host "   Enter value for $secret" -AsSecureString
        $plainValue = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($value))
        $plainValue | gcloud secrets create $secret --data-file=-
    } else {
        Write-Host "   Secret exists: $secret" -ForegroundColor Gray
    }
}

# Deploy Backend
Write-Host "`n📦 Building and deploying backend..." -ForegroundColor Yellow
Set-Location -Path "app/backend"

# Build image
Write-Host "   Building Docker image..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/chatapp-backend"

# Deploy to Cloud Run
Write-Host "   Deploying to Cloud Run..." -ForegroundColor Gray
gcloud run deploy chatapp-backend `
    --image "gcr.io/$ProjectId/chatapp-backend" `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --memory 512Mi `
    --cpu 1 `
    --min-instances 0 `
    --max-instances 10 `
    --set-env-vars "ENV=production,PROJECT_ID=$ProjectId,REGION=$Region" `
    --set-secrets "INFERENCE_API_KEY=openrouter-api-key:latest"

# Get backend URL
$backendUrl = gcloud run services describe chatapp-backend --region $Region --format="value(status.url)"
Write-Host "`n✅ Backend deployed: $backendUrl" -ForegroundColor Green

# Go back to root
Set-Location -Path "../.."

# Build Frontend
Write-Host "`n📦 Building frontend..." -ForegroundColor Yellow
Set-Location -Path "app/frontend"

# Create production env
"VITE_API_URL=$backendUrl/api/v1" | Out-File -FilePath ".env.production" -Encoding UTF8

# Install and build
Write-Host "   Installing dependencies..." -ForegroundColor Gray
npm install

Write-Host "   Building for production..." -ForegroundColor Gray
npm run build

# Create Dockerfile for frontend
@"
FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
"@ | Out-File -FilePath "Dockerfile.prod" -Encoding UTF8

# Create nginx config
@"
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
            try_files `$uri `$uri/ /index.html;
        }
    }
}
"@ | Out-File -FilePath "nginx.conf" -Encoding UTF8

# Build and deploy frontend
Write-Host "   Deploying frontend to Cloud Run..." -ForegroundColor Gray
gcloud builds submit --tag "gcr.io/$ProjectId/chatapp-frontend" -f Dockerfile.prod

gcloud run deploy chatapp-frontend `
    --image "gcr.io/$ProjectId/chatapp-frontend" `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --port 8080

# Get frontend URL
$frontendUrl = gcloud run services describe chatapp-frontend --region $Region --format="value(status.url)"
Write-Host "`n✅ Frontend deployed: $frontendUrl" -ForegroundColor Green

# Update backend CORS
Write-Host "`n⚙️ Updating backend CORS..." -ForegroundColor Yellow
gcloud run services update chatapp-backend `
    --region $Region `
    --update-env-vars "FRONTEND_ORIGIN=$frontendUrl"

Set-Location -Path "../.."

Write-Host "`n" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Frontend URL: $frontendUrl" -ForegroundColor Cyan
Write-Host "🔧 Backend URL:  $backendUrl" -ForegroundColor Cyan
Write-Host "📚 API Docs:     $backendUrl/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Set up Cloud SQL for production database"
Write-Host "   2. Configure Firebase Authentication"
Write-Host "   3. Set up custom domain (optional)"
Write-Host ""

