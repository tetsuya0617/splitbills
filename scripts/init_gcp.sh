#!/bin/bash

set -e

echo "====================================="
echo "splitbills GCP Setup Script"
echo "====================================="

# Configuration
PROJECT_ID="splitbills"
SERVICE_NAME="splitbills"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="splitbills-sa"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Please install Google Cloud SDK first: https://cloud.google.com/sdk/install"
    exit 1
fi

# Step 1: Create project
echo ""
echo -e "${YELLOW}Step 1: Creating GCP project...${NC}"
if gcloud projects create ${PROJECT_ID} 2>/dev/null; then
    echo -e "${GREEN}✓ Project ${PROJECT_ID} created successfully${NC}"
else
    echo -e "${YELLOW}! Project ${PROJECT_ID} might already exist or ID is taken${NC}"
    echo "If the ID is taken, please update PROJECT_ID in this script and README"
    read -p "Continue with existing project? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set current project
gcloud config set project ${PROJECT_ID}
echo -e "${GREEN}✓ Set current project to ${PROJECT_ID}${NC}"

# Step 2: Link billing account
echo ""
echo -e "${YELLOW}Step 2: Checking billing account...${NC}"
BILLING_ACCOUNT=$(gcloud billing accounts list --format="value(name)" --limit=1 2>/dev/null)

if [ -z "$BILLING_ACCOUNT" ]; then
    echo -e "${RED}No billing account found. Please set up billing manually:${NC}"
    echo "1. Go to https://console.cloud.google.com/billing"
    echo "2. Create or select a billing account"
    echo "3. Link it to project ${PROJECT_ID}"
    read -p "Press Enter after setting up billing..."
else
    echo "Found billing account: ${BILLING_ACCOUNT}"
    gcloud billing projects link ${PROJECT_ID} --billing-account=${BILLING_ACCOUNT} 2>/dev/null || true
    echo -e "${GREEN}✓ Billing account linked${NC}"
fi

# Step 3: Enable required APIs
echo ""
echo -e "${YELLOW}Step 3: Enabling required APIs...${NC}"
gcloud services enable vision.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project=${PROJECT_ID}
echo -e "${GREEN}✓ APIs enabled${NC}"

# Step 4: Create service account
echo ""
echo -e "${YELLOW}Step 4: Creating service account...${NC}"
if gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
    --display-name="splitbills Service Account" \
    --project=${PROJECT_ID} 2>/dev/null; then
    echo -e "${GREEN}✓ Service account created${NC}"
else
    echo -e "${YELLOW}! Service account might already exist${NC}"
fi

# Get service account email
SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary roles
echo "Granting IAM roles..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudvision.user" \
    --condition=None \
    --quiet

echo -e "${GREEN}✓ IAM roles granted${NC}"

# Step 5: Check if .env exists
echo ""
echo -e "${YELLOW}Step 5: Checking environment configuration...${NC}"
if [ ! -f ../.env ]; then
    echo -e "${RED}! .env file not found${NC}"
    echo "Please create .env file from .env.example and add your LINE credentials"
    echo "cp .env.example .env"
    echo "Then edit .env with your LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN"
    exit 1
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi

# Step 6: Build and deploy to Cloud Run
echo ""
echo -e "${YELLOW}Step 6: Building and deploying to Cloud Run...${NC}"
echo "This will build the Docker image and deploy it to Cloud Run"
read -p "Continue with deployment? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ..
    
    # Build and deploy using Cloud Build
    echo "Building and deploying..."
    gcloud run deploy ${SERVICE_NAME} \
        --source . \
        --region ${REGION} \
        --platform managed \
        --allow-unauthenticated \
        --service-account ${SA_EMAIL} \
        --set-env-vars "$(grep -v '^#' .env | xargs | tr ' ' ',')" \
        --memory 512Mi \
        --max-instances 10 \
        --timeout 60 \
        --project ${PROJECT_ID}
    
    # Get the service URL
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --region ${REGION} \
        --format 'value(status.url)' \
        --project ${PROJECT_ID})
    
    echo ""
    echo -e "${GREEN}====================================="
    echo "Deployment Complete!"
    echo "====================================="
    echo ""
    echo "Cloud Run URL: ${SERVICE_URL}"
    echo "Webhook URL: ${SERVICE_URL}/callback"
    echo ""
    echo "Next steps:"
    echo "1. Copy the Webhook URL above"
    echo "2. Go to LINE Developers Console"
    echo "3. Set the Webhook URL in your channel settings"
    echo "4. Enable webhook and disable auto-reply"
    echo "5. Add the bot as friend and test!"
    echo "=====================================${NC}"
else
    echo "Deployment skipped. You can deploy manually later with:"
    echo "gcloud run deploy ${SERVICE_NAME} --source . --region ${REGION}"
fi