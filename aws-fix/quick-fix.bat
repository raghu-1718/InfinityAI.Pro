@echo off
echo 🚀 Quick AWS Fix - Restarting ECS Services
echo.

REM Restart Engine C service
echo Restarting Engine C service...
aws ecs update-service --cluster infinityai-pro-cluster --service engine-c-service --force-new-deployment --region us-east-1

REM Restart Engine D service  
echo Restarting Engine D service...
aws ecs update-service --cluster infinityai-pro-cluster --service engine-d-service --force-new-deployment --region us-east-1

REM Wait 30 seconds
echo Waiting 30 seconds for services to restart...
timeout /t 30 /nobreak

REM Test endpoints
echo Testing Engine C...
curl -s -o nul -w "Engine C Status: %%{http_code}" http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8002/health
echo.

echo Testing Engine D...
curl -s -o nul -w "Engine D Status: %%{http_code}" http://infinityai-pro-alb-1978325793.us-east-1.elb.amazonaws.com:8000/health
echo.

echo ✅ Quick fix completed!
pause