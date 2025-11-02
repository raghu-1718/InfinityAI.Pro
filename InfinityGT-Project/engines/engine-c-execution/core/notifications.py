"""
Lightweight notifications for Engine C (Telegram only for now).

This mirrors the idea from Auto_AI_Bot but keeps it minimal and dependency-free
by using requests directly. Configure the following environment variables:
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID

Usage:
  from core.notifications import notify_telegram
  notify_telegram("Trade executed: BUY RELIANCE x10 @ 2450")
"""
from __future__ import annotations

import os
import requests
from typing import Optional


def notify_telegram(message: str, chat_id: Optional[str] = None, token: Optional[str] = None) -> bool:
    token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=8)
        return resp.status_code == 200
    except Exception:
        return False
