#!/bin/bash
# InfinityAI.Pro Complete Deployment Automation Script
# This script automates the entire deployment process from git to production

set -e

echo "🚀 InfinityAI.Pro Complete Deployment Automation"
echo "=============================================="

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

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
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
        [[ ! $REPLY =~ ^[Yy]$ ]]
    else
        [[ $REPLY =~ ^[Yy]$ ]]
    fi
}

# Step 1: Pre-deployment checks
step1_pre_deployment_checks() {
    print_header "Step 1: Pre-deployment Checks"

    # Check if we're in the right directory
    if [ ! -f "backend/main.py" ]; then
        print_error "Please run this script from the infinityai-pro directory"
        exit 1
    fi

    # Check required files
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

            read -p "Enter commit message: " commit_msg
            if [ -z "$commit_msg" ]; then
                commit_msg="🚀 Production deployment: Multi-cloud AI infrastructure"
            fi

            git commit -m "$commit_msg"
            print_success "Changes committed"
        fi
    fi

    # Check git remote
    if ! git remote get-url origin >/dev/null 2>&1; then
        print_error "No git remote 'origin' found."
        echo "Please set up your GitHub repository:"
        echo "git remote add origin https://github.com/your-username/InfinityAI.Pro.git"
        exit 1
    fi

    print_success "Pre-deployment checks passed"
}

# Step 2: Deploy to Render
step2_deploy_to_render() {
    print_header "Step 2: Deploy to Render"

    if confirm "Push code to GitHub?" y; then
        print_status "Pushing to GitHub..."
        git push origin main
        print_success "Code pushed to GitHub"

        # Get repository info
        REPO_URL=$(git remote get-url origin)
        REPO_NAME=$(basename "$REPO_URL" .git)

        print_success "Repository: $REPO_NAME"
    else
        print_warning "Skipping GitHub push"
        REPO_NAME="your-repo-name"
    fi

    echo ""
    echo "📋 MANUAL STEP REQUIRED:"
    echo "1. Go to https://render.com and sign in"
    echo "2. Click 'New' → 'Web Service'"
    echo "3. Connect your GitHub repository: $REPO_NAME"
    echo "4. Configure service:"
    echo "   - Name: infinityai-pro-api"
    echo "   - Runtime: Python 3"
    echo "   - Build Command: pip install -r requirements.txt"
    echo "   - Start Command: cd backend && python main.py"
    echo ""

    read -p "Enter your Render app URL (after deployment): " render_url
    if [ -n "$render_url" ]; then
        echo "RENDER_APP_URL=$render_url" > .render_url
        print_success "Render URL saved"
    fi
}

# Step 3: Setup environment variables
step3_setup_environment() {
    print_header "Step 3: Environment Variables Setup"

    if [ -f ".render_url" ]; then
        RENDER_URL=$(cat .render_url)
        print_status "Using Render URL: $RENDER_URL"
    else
        read -p "Enter your Render app URL: " RENDER_URL
    fi

    echo ""
    echo "🔧 Choose environment setup method:"
    echo "1. Interactive setup (recommended)"
    echo "2. Generate from existing .env file"
    echo "3. Show required variables list"
    echo ""

    read -p "Enter your choice (1-3): " choice

    case $choice in
        1)
            print_status "Starting interactive environment setup..."
            ./setup_env_vars.sh
            ;;
        2)
            if [ -f ".env" ]; then
                print_status "Generating from existing .env file..."
                ./setup_env_vars.sh
            else
                print_error "No .env file found. Run option 1 first."
                return 1
            fi
            ;;
        3)
            ./setup_env_vars.sh
            ;;
        *)
            print_error "Invalid choice"
            return 1
            ;;
    esac

    echo ""
    echo "📋 MANUAL STEP REQUIRED:"
    echo "1. Copy variables from render_env_vars.txt"
    echo "2. Go to Render dashboard → Your service → Environment"
    echo "3. Add each variable (one per line)"
    echo "4. Save and redeploy your service"
    echo ""

    confirm "Have you set up the environment variables in Render?" || return 1
}

# Step 4: Verify deployment
step4_verify_deployment() {
    print_header "Step 4: Deployment Verification"

    if [ -f ".render_url" ]; then
        RENDER_URL=$(cat .render_url)
        print_status "Using saved Render URL: $RENDER_URL"
    else
        read -p "Enter your Render app URL for verification: " RENDER_URL
    fi

    print_status "Running comprehensive verification..."

    # Run the verification script
    if [ -n "$RENDER_URL" ]; then
        echo "$RENDER_URL" | python3 verify_deployment.py
    else
        python3 verify_deployment.py
    fi

    if [ $? -eq 0 ]; then
        print_success "Deployment verification PASSED!"
        return 0
    else
        print_error "Deployment verification FAILED!"
        echo "Check the issues above and fix them, then run verification again."
        return 1
    fi
}

# Step 5: Post-deployment setup
step5_post_deployment() {
    print_header "Step 5: Post-deployment Setup"

    echo "🎯 Your InfinityAI.Pro is now deployed!"
    echo ""
    echo "📊 Monitoring & Maintenance:"
    echo "• Monitor costs in Azure/AWS consoles"
    echo "• Check trading performance regularly"
    echo "• Update AI models quarterly"
    echo "• Set up billing alerts"
    echo ""
    echo "🚨 Emergency Procedures:"
    echo "• Switch to PAPER_MODE=true for safe testing"
    echo "• Monitor drawdown limits"
    echo "• Have backup broker credentials ready"
    echo ""
    echo "📞 Support:"
    echo "• Check Render logs for errors"
    echo "• Run verification script if issues occur"
    echo "• Review environment variables if services fail"
    echo ""
    echo "🎉 HAPPY TRADING!"
}

# Main execution
main() {
    echo "This script will guide you through the complete deployment process."
    echo "Make sure you have:"
    echo "• GitHub repository set up"
    echo "• Render.com account"
    echo "• Azure/AWS API keys ready"
    echo "• Broker credentials (Dhan/CoinSwitch)"
    echo ""

    if ! confirm "Ready to start deployment?" y; then
        print_status "Deployment cancelled"
        exit 0
    fi

    # Execute steps
    step1_pre_deployment_checks
    step2_deploy_to_render
    step3_setup_environment

    if step4_verify_deployment; then
        step5_post_deployment
    else
        print_error "Deployment incomplete. Please fix issues and try again."
        exit 1
    fi
}

# Run main function
main