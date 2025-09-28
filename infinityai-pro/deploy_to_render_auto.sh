#!/bin/bash
# InfinityAI.Pro Automated Render Deployment Script
# This script automates the complete deployment process to Render.com

set -e

echo "🚀 InfinityAI.Pro Automated Render Deployment"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get user confirmation
confirm() {
    local message=$1
    local default=${2:-n}
    local prompt

    if [ "$default" = "y" ]; then
        prompt="Y/n"
    else
        prompt="y/N"
    fi

    read -p "$message ($prompt): " -n 1 -r
    echo

    if [ "$default" = "y" ]; then
        [[ ! $REPLY =~ ^[Nn]$ ]]
    else
        [[ $REPLY =~ ^[Yy]$ ]]
    fi
}

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    print_error "Please run this script from the infinityai-pro directory"
    exit 1
fi

print_status "Checking prerequisites..."

# Check if required files exist
required_files=("backend/main.py" "backend/requirements.txt" "frontend/package.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

# Check for git
if ! command_exists git; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    print_warning "Git working directory is not clean."
    if confirm "Do you want to commit current changes?"; then
        print_status "Staging all changes..."
        git add .

        # Get commit message
        read -p "Enter commit message: " commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="🚀 Production deployment: Multi-cloud AI infrastructure"
        fi

        git commit -m "$commit_msg"
        print_success "Changes committed"
    else
        print_warning "Continuing with uncommitted changes..."
    fi
fi

# Check if remote exists
if ! git remote get-url origin >/dev/null 2>&1; then
    print_error "No git remote 'origin' found. Please set up your GitHub repository first."
    echo "Run: git remote add origin https://github.com/your-username/InfinityAI.Pro.git"
    exit 1
fi

print_success "Prerequisites check passed"

# Clean up any existing build artifacts
print_status "Cleaning build artifacts..."
rm -rf dist/ build/ *.egg-info/ __pycache__/ */__pycache__/

# Git operations
print_status "Preparing for deployment..."

if confirm "Push changes to GitHub?" y; then
    print_status "Pushing to GitHub..."
    git push origin main
    print_success "Code pushed to GitHub"

    # Get repository info
    REPO_URL=$(git remote get-url origin)
    REPO_NAME=$(basename "$REPO_URL" .git)

    print_success "Repository: $REPO_NAME"
else
    print_warning "Skipping GitHub push. Make sure your code is pushed manually."
fi

print_success "Deployment preparation complete!"
echo ""
echo "🎯 Next Steps:"
echo "1. Go to https://render.com"
echo "2. Click 'New' → 'Web Service'"
echo "3. Connect your GitHub repository: $REPO_NAME"
echo "4. Configure service:"
echo "   - Name: infinityai-pro-api"
echo "   - Runtime: Python 3"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: cd backend && python main.py"
echo "5. Set environment variables from RENDER_ENV_SETUP.md"
echo "6. Deploy!"
echo ""
echo "📖 See RENDER_ENV_SETUP.md for environment variables"
echo "🔍 Run 'python verify_deployment.py' after deployment"