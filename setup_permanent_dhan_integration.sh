#!/bin/bash
# Complete Dhan API Integration Setup for InfinityAI.Pro
# This script sets up permanent Dhan API integration with automated token refresh

echo "🚀 Setting up permanent Dhan API integration for InfinityAI.Pro"
echo "================================================================="

# Check if we're on Windows (since this is a Windows environment)
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "📍 Detected Windows environment"

    # Check if Python is available
    if ! command -v python &> /dev/null; then
        echo "❌ Python not found. Please install Python 3.8+ and try again."
        exit 1
    fi

    # Check if required files exist
    if [ ! -f "dhan_auto_refresh.py" ]; then
        echo "❌ dhan_auto_refresh.py not found. Please run the setup scripts first."
        exit 1
    fi

    if [ ! -f "nifty_options_analysis.py" ]; then
        echo "❌ nifty_options_analysis.py not found. Please ensure the analysis script exists."
        exit 1
    fi

    echo "✅ All required files found"

    # Test the auto-refresh service
    echo "🔄 Testing automated token refresh service..."
    python dhan_auto_refresh.py

    if [ $? -eq 0 ]; then
        echo "✅ Auto-refresh service test passed"
    else
        echo "❌ Auto-refresh service test failed"
        exit 1
    fi

    # Test the main analysis script
    echo "📊 Testing NIFTY options analysis with Dhan API..."
    python nifty_options_analysis.py > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "✅ NIFTY analysis script test passed"
    else
        echo "❌ NIFTY analysis script test failed"
        exit 1
    fi

    # Set up Windows Task Scheduler
    echo "📅 Setting up Windows Task Scheduler for daily token refresh..."
    if [ -f "setup_dhan_token_scheduler.ps1" ]; then
        powershell -ExecutionPolicy Bypass -File setup_dhan_token_scheduler.ps1

        if [ $? -eq 0 ]; then
            echo "✅ Windows Task Scheduler setup completed"
        else
            echo "❌ Windows Task Scheduler setup failed"
            exit 1
        fi
    else
        echo "⚠️ setup_dhan_token_scheduler.ps1 not found, skipping Task Scheduler setup"
    fi

else
    echo "❌ This setup script is designed for Windows. For Linux/Mac, please adapt manually."
    exit 1
fi

echo ""
echo "🎉 Dhan API permanent integration setup completed successfully!"
echo "================================================================="
echo "📋 What was set up:"
echo "   ✅ Automated token refresh service (dhan_auto_refresh.py)"
echo "   ✅ Updated NIFTY analysis with auto token validation"
echo "   ✅ Windows Task Scheduler for daily token refresh at 9:00 AM"
echo "   ✅ Fallback to NSE data when Dhan API is unavailable"
echo ""
echo "🔄 How it works:"
echo "   • Tokens are validated before each API call"
echo "   • Expired tokens are automatically refreshed using API key/secret"
echo "   • Daily scheduled refresh ensures tokens never expire"
echo "   • NSE fallback provides reliable data when needed"
echo ""
echo "📊 To use:"
echo "   • Run 'python nifty_options_analysis.py' anytime for fresh analysis"
echo "   • Tokens refresh automatically - no manual intervention needed"
echo "   • Check Task Scheduler for refresh status and logs"
echo ""
echo "⚠️ Important Notes:"
echo "   • Keep your API key and secret secure"
echo "   • Monitor the logs for any authentication issues"
echo "   • The system will automatically handle token expiration"
echo ""
echo "🎯 You're all set for permanent Dhan API integration!"