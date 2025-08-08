#!/bin/bash

set -e

echo "====================================="
echo "splitbills GitHub Repository Setup"
echo "====================================="

# Configuration
REPO_NAME="splitbills"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}Warning: GitHub CLI (gh) is not installed${NC}"
    echo ""
    echo "To install gh CLI:"
    echo "  macOS: brew install gh"
    echo "  Linux: See https://github.com/cli/cli#installation"
    echo ""
    echo "Manual setup instructions:"
    echo "1. Create a new repository on GitHub: https://github.com/new"
    echo "2. Repository name: ${REPO_NAME}"
    echo "3. Set to Private"
    echo "4. Don't initialize with README"
    echo ""
    echo "Then run these commands:"
    echo "  cd .."
    echo "  git init"
    echo "  git add ."
    echo "  git commit -m 'Initial commit: splitbills LINE bot'"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/${REPO_NAME}.git"
    echo "  git push -u origin main"
    exit 0
fi

# Check if authenticated
echo -e "${YELLOW}Checking GitHub authentication...${NC}"
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Not authenticated with GitHub${NC}"
    echo "Please run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✓ GitHub CLI authenticated${NC}"

# Move to project root
cd ..

# Initialize git if not already
if [ ! -d .git ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    echo -e "${GREEN}✓ Git repository initialized${NC}"
else
    echo -e "${GREEN}✓ Git repository already initialized${NC}"
fi

# Create initial commit
echo -e "${YELLOW}Creating initial commit...${NC}"
git add .
git commit -m "Initial commit: splitbills receipt splitting LINE bot

Features:
- Receipt OCR using Google Cloud Vision API
- Automatic amount extraction from any currency
- Bill splitting calculation
- Modern Flex UI for LINE
- Free tier management with monthly limits
- Deployed on Google Cloud Run" 2>/dev/null || echo -e "${YELLOW}! Already committed${NC}"

# Create GitHub repository
echo ""
echo -e "${YELLOW}Creating GitHub repository...${NC}"
if gh repo create ${REPO_NAME} --private --source . --remote origin --push 2>/dev/null; then
    echo -e "${GREEN}✓ Repository created and pushed successfully${NC}"
    
    # Get repository URL
    REPO_URL=$(gh repo view --json url -q .url)
    
    echo ""
    echo -e "${GREEN}====================================="
    echo "GitHub Repository Setup Complete!"
    echo "====================================="
    echo ""
    echo "Repository URL: ${REPO_URL}"
    echo ""
    echo "Your code has been pushed to GitHub!"
    echo "=====================================${NC}"
else
    echo -e "${YELLOW}! Repository might already exist${NC}"
    
    # Check if remote exists
    if git remote get-url origin &> /dev/null; then
        echo "Remote 'origin' already configured"
        echo "Pushing latest changes..."
        git push -u origin main 2>/dev/null || git push origin main
        echo -e "${GREEN}✓ Code pushed to existing repository${NC}"
    else
        echo -e "${RED}Failed to create repository${NC}"
        echo "Please create manually on GitHub and run:"
        echo "  git remote add origin https://github.com/YOUR_USERNAME/${REPO_NAME}.git"
        echo "  git push -u origin main"
        exit 1
    fi
fi

# Add some useful GitHub configurations
echo ""
echo -e "${YELLOW}Setting up GitHub repository settings...${NC}"

# Create a basic GitHub Actions workflow for CI (optional)
mkdir -p .github/workflows
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Check code formatting
      run: |
        pip install black flake8
        black --check app/
        flake8 app/ --max-line-length=100
      continue-on-error: true
EOF

git add .github/
git commit -m "Add GitHub Actions CI workflow" 2>/dev/null && git push || echo -e "${YELLOW}! CI workflow already exists or no changes${NC}"

echo ""
echo -e "${GREEN}✓ GitHub repository fully configured${NC}"
echo ""
echo "Optional next steps:"
echo "1. Add collaborators: gh repo edit --add-collaborator USERNAME"
echo "2. Create issues: gh issue create --title 'Task title'"
echo "3. View in browser: gh repo view --web"