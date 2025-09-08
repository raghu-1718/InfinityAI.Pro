# Entry point for FastAPI application
from fastapi import FastAPI
from api.routes import webhook, user, health, chat

app = FastAPI(title="TradingAI Pro API")

app.include_router(webhook.router, prefix="/webhook")
app.include_router(user.router, prefix="/user")
app.include_router(health.router, prefix="/health")
app.include_router(chat.router, prefix="/chat")

if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, host="0.0.0.0", port=8000)
