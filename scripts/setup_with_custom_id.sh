#!/bin/bash

set -e

echo "====================================="
echo "splitbills GCP Setup with Custom ID"
echo "====================================="

# Generate unique project ID
RANDOM_SUFFIX=$(openssl rand -hex 4)
PROJECT_ID="splitbills-${RANDOM_SUFFIX}"
SERVICE_NAME="splitbills"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="splitbills-sa"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}Using Project ID: ${PROJECT_ID}${NC}"
echo ""

# Create project with new ID
echo -e "${YELLOW}Creating GCP project with ID: ${PROJECT_ID}...${NC}"
gcloud projects create ${PROJECT_ID}
gcloud config set project ${PROJECT_ID}
echo -e "${GREEN}✓ Project ${PROJECT_ID} created successfully${NC}"

# Link billing account
echo ""
echo -e "${YELLOW}Checking billing account...${NC}"
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

# Enable APIs
echo ""
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable vision.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project=${PROJECT_ID}
echo -e "${GREEN}✓ APIs enabled${NC}"

# Create service account
echo ""
echo -e "${YELLOW}Creating service account...${NC}"
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
    --display-name="splitbills Service Account" \
    --project=${PROJECT_ID}
echo -e "${GREEN}✓ Service account created${NC}"

SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant roles
echo "Granting IAM roles..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudvision.user" \
    --condition=None \
    --quiet
echo -e "${GREEN}✓ IAM roles granted${NC}"

# Check .env
echo ""
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f ../.env ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp ../.env.example ../.env
    echo -e "${RED}! Please edit .env file with your LINE credentials${NC}"
    echo "Add your LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN"
    read -p "Press Enter after editing .env..."
else
    echo -e "${GREEN}✓ .env file found${NC}"
fi

# Deploy
echo ""
echo -e "${YELLOW}Ready to deploy to Cloud Run${NC}"
echo -e "${GREEN}Project ID: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Service Account: ${SA_EMAIL}${NC}"
read -p "Deploy now? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ..
    
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
    
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --region ${REGION} \
        --format 'value(status.url)' \
        --project ${PROJECT_ID})
    
    echo ""
    echo -e "${GREEN}====================================="
    echo "Deployment Complete!"
    echo "====================================="
    echo ""
    echo "Project ID: ${PROJECT_ID}"
    echo "Cloud Run URL: ${SERVICE_URL}"
    echo "Webhook URL: ${SERVICE_URL}/callback"
    echo ""
    echo "IMPORTANT: Save this Project ID for future use!"
    echo ""
    echo "Next steps:"
    echo "1. Copy the Webhook URL above"
    echo "2. Go to LINE Developers Console"
    echo "3. Set the Webhook URL in your channel settings"
    echo "4. Enable webhook and disable auto-reply"
    echo "5. Add the bot as friend and test!"
    echo "=====================================${NC}"
    
    # Save project ID for reference
    echo ${PROJECT_ID} > ../.project_id
    echo -e "${YELLOW}Project ID saved to .project_id file${NC}"
fi