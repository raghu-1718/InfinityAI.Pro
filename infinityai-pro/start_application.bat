@echo off
REM InfinityAI.Pro Application Startup Script
REM This script sets up and starts the complete application

echo ========================================
echo 🚀 InfinityAI.Pro Application Startup
echo ========================================

echo.
echo 📊 Checking prerequisites...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Node.js not found. Frontend development will be limited.
) else (
    echo ✅ Node.js found
)

echo ✅ Python found

echo.
echo 🔧 Setting up environment...

REM Navigate to backend directory
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo 📚 Installing Python dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist ".env" (
    echo 📝 Creating environment configuration...
    echo # InfinityAI.Pro Configuration > .env
    echo DHAN_CLIENT_ID=your_client_id_here >> .env
    echo DHAN_ACCESS_TOKEN=your_access_token_here >> .env
    echo TRADING_CAPITAL=1000000 >> .env
    echo RISK_PER_TRADE=0.02 >> .env
    echo MAX_POSITIONS=10 >> .env
    echo DAILY_LOSS_LIMIT=100000 >> .env
    echo DHAN_BASE_URL=https://api.dhan.co >> .env
    echo DEFAULT_SYMBOLS=NIFTY,BANKNIFTY,RELIANCE,TCS >> .env
    echo AI_CONFIDENCE_THRESHOLD=0.75 >> .env
    echo VOICE_TRADING_ENABLED=true >> .env
    echo.
    echo ⚠️ IMPORTANT: Please edit backend\.env and add your Dhan API credentials
    echo 📖 Get credentials from: https://web.dhan.co/developer/app
)

echo.
echo 🚀 Starting InfinityAI.Pro Backend Server...
echo.
echo 📍 Access Points:
echo    🌐 Web Application: http://localhost:8000
echo    📱 API Documentation: http://localhost:8000/docs
echo    🔍 Health Check: http://localhost:8000/health
echo    💬 Voice Trading: Ready for commands
echo.
echo 🎯 Voice Commands to try:
echo    "Start momentum trading on NIFTY with 2 lakh capital"
echo    "What is my current portfolio status?"
echo    "Stop all trading sessions"
echo.
echo 💡 Press Ctrl+C to stop the server
echo ========================================

REM Start the FastAPI server
python main.py

echo.
echo 👋 InfinityAI.Pro server stopped
pause