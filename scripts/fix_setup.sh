#!/bin/bash

set -e

echo "====================================="
echo "Fixing splitbills Setup"
echo "====================================="

# Use the project ID that was already created
PROJECT_ID="splitbills-cd1169bf"
SERVICE_NAME="splitbills"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="splitbills-sa"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}Using existing Project ID: ${PROJECT_ID}${NC}"
echo ""

# Set project
gcloud config set project ${PROJECT_ID}

# Service account email
SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant correct Vision API role (fix the error)
echo -e "${YELLOW}Granting correct IAM roles...${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/cloudfunctions.invoker" \
    --quiet 2>/dev/null || true

# Add Vision API user role at project level (without condition)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/serviceusage.serviceUsageConsumer" \
    --quiet

echo -e "${GREEN}✓ IAM roles granted${NC}"

# Check .env
echo ""
echo -e "${YELLOW}Checking environment configuration...${NC}"
if [ ! -f ../.env ]; then
    echo -e "${YELLOW}Creating .env from template...${NC}"
    cp ../.env.example ../.env
    echo ""
    echo -e "${RED}IMPORTANT: Edit the .env file with your LINE credentials${NC}"
    echo "You need to add:"
    echo "  - LINE_CHANNEL_SECRET"
    echo "  - LINE_CHANNEL_ACCESS_TOKEN"
    echo ""
    read -p "Press Enter after editing .env file..."
else
    echo -e "${GREEN}✓ .env file found${NC}"
    echo "Make sure your LINE credentials are set in .env"
    read -p "Press Enter to continue..."
fi

# Deploy
echo ""
echo -e "${YELLOW}Ready to deploy to Cloud Run${NC}"
echo -e "${GREEN}Project ID: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Service Account: ${SA_EMAIL}${NC}"
echo ""
read -p "Deploy now? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ..
    
    echo ""
    echo "Building and deploying to Cloud Run..."
    echo "This may take a few minutes..."
    
    gcloud run deploy ${SERVICE_NAME} \
        --source . \
        --region ${REGION} \
        --platform managed \
        --allow-unauthenticated \
        --service-account ${SA_EMAIL} \
        --set-env-vars "$(grep -v '^#' .env | grep -v '^$' | xargs | tr ' ' ',')" \
        --memory 512Mi \
        --max-instances 10 \
        --timeout 60 \
        --project ${PROJECT_ID}
    
    # Get service URL
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --region ${REGION} \
        --format 'value(status.url)' \
        --project ${PROJECT_ID})
    
    echo ""
    echo -e "${GREEN}====================================="
    echo "🎉 Deployment Complete!"
    echo "====================================="
    echo ""
    echo "Project ID: ${PROJECT_ID}"
    echo "Cloud Run URL: ${SERVICE_URL}"
    echo "Webhook URL: ${SERVICE_URL}/callback"
    echo ""
    echo "Next steps:"
    echo "1. Copy the Webhook URL: ${SERVICE_URL}/callback"
    echo "2. Go to LINE Developers Console"
    echo "3. Set the Webhook URL in your Messaging API settings"
    echo "4. Enable 'Use webhook' option"
    echo "5. Disable 'Auto-reply messages' option"
    echo "6. Add the bot as friend and send a receipt image!"
    echo "=====================================${NC}"
    
    # Save project info
    echo ${PROJECT_ID} > ../.project_id
    echo ${SERVICE_URL} > ../.service_url
    echo -e "${YELLOW}Project info saved to .project_id and .service_url files${NC}"
else
    echo ""
    echo "Deployment cancelled. You can run this script again later."
fi