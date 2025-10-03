"""
AI Trading Chatbot API with Voice Commands
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import asyncio
from datetime import datetime

from services.ai_trading_chatbot import ai_trading_chatbot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatbot", tags=["AI Trading Chatbot"])

class ChatMessage(BaseModel):
    message: str
    user_id: str
    voice_input: bool = False

class ChatResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    type: str
    timestamp: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(chat_message: ChatMessage):
    """
    Chat with AI Trading Bot - Natural Language Commands
    
    Examples:
    - "Scan NIFTY with 5 lakh capital using momentum strategy"
    - "Start auto trading BANKNIFTY with 2 lakh"
    - "Analyze RELIANCE for swing trading"
    - "Stop all trading"
    - "Get latest news for TCS"
    """
    
    try:
        logger.info(f"Processing chat message from {chat_message.user_id}: {chat_message.message}")
        
        # Process command through chatbot
        result = await ai_trading_chatbot.process_command(
            user_input=chat_message.message,
            user_id=chat_message.user_id
        )
        
        return ChatResponse(
            success=result.get('success', True),
            message=result.get('message', 'Command processed'),
            data=result,
            type=result.get('type', 'response'),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-command")
async def process_voice_command(audio_file: UploadFile = File(...), user_id: str = "default"):
    """
    Process voice commands for trading
    """
    
    try:
        # Read audio file
        audio_content = await audio_file.read()
        
        # Convert speech to text using Whisper
        text_command = await convert_speech_to_text(audio_content)
        
        if not text_command:
            return ChatResponse(
                success=False,
                message="Could not understand voice command. Please try again.",
                type="voice_error",
                timestamp=datetime.now().isoformat()
            )
        
        # Process the text command
        result = await ai_trading_chatbot.process_command(
            user_input=text_command,
            user_id=user_id
        )
        
        return ChatResponse(
            success=result.get('success', True),
            message=f"Voice command: '{text_command}' - {result.get('message', '')}",
            data={**result, 'voice_input': text_command},
            type=result.get('type', 'voice_response'),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Voice command processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active-sessions/{user_id}")
async def get_active_sessions(user_id: str):
    """Get active trading sessions for user"""
    
    try:
        user_sessions = []
        
        for session_id, session in ai_trading_chatbot.active_sessions.items():
            if user_id in session_id and session.active:
                user_sessions.append({
                    'session_id': session_id,
                    'symbol': session.symbol,
                    'strategy': session.strategy,
                    'capital': session.capital,
                    'entry_price': session.entry_price,
                    'current_pnl': session.current_pnl,
                    'trades_executed': session.trades_executed,
                    'start_time': session.start_time.isoformat(),
                    'stop_loss': session.stop_loss,
                    'take_profit': session.take_profit,
                    'trailing_stop': session.trailing_stop
                })
        
        return {
            'success': True,
            'active_sessions': user_sessions,
            'total_sessions': len(user_sessions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop-session/{session_id}")
async def stop_trading_session(session_id: str):
    """Stop specific trading session"""
    
    try:
        if session_id in ai_trading_chatbot.active_sessions:
            session = ai_trading_chatbot.active_sessions[session_id]
            session.active = False
            
            # Close position
            await ai_trading_chatbot._close_position(session)
            
            return {
                'success': True,
                'message': f"Trading session {session_id} stopped successfully",
                'final_pnl': session.current_pnl,
                'trades_executed': session.trades_executed
            }
        else:
            return {
                'success': False,
                'message': f"Session {session_id} not found or already stopped"
            }
            
    except Exception as e:
        logger.error(f"Failed to stop session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/command-examples")
async def get_command_examples():
    """Get examples of supported voice/text commands"""
    
    return {
        'success': True,
        'command_examples': {
            'trading_commands': [
                "Scan NIFTY with 5 lakh capital using momentum strategy",
                "Start auto trading BANKNIFTY with 2 lakh capital",
                "Stop trading RELIANCE",
                "Stop all trading sessions"
            ],
            'analysis_commands': [
                "Analyze NIFTY for swing trading",
                "Check sentiment for TCS",
                "Get latest news for HDFC Bank",
                "Analyze BANKNIFTY using mean reversion strategy"
            ],
            'market_commands': [
                "Scan NIFTY option chain",
                "Show portfolio status",
                "Check risk analysis for current positions",
                "Get market overview"
            ],
            'voice_commands': [
                "Hey InfinityAI, scan NIFTY with 1 lakh",
                "Start momentum trading on BANKNIFTY",
                "What's the sentiment for Reliance?",
                "Stop all my trades"
            ]
        },
        'supported_symbols': [
            'NIFTY', 'BANKNIFTY', 'SENSEX', 'RELIANCE', 'TCS', 'HDFC', 'ICICI',
            'INFY', 'WIPRO', 'HDFCBANK', 'KOTAKBANK', 'AXISBANK', 'SBIN',
            'BTC', 'ETH', 'BNB', 'ADA', 'DOT', 'MATIC'
        ],
        'supported_strategies': [
            'momentum', 'mean_reversion', 'sentiment', 'scalping', 'swing'
        ]
    }

@router.get("/chatbot-status")
async def get_chatbot_status():
    """Get chatbot system status"""
    
    try:
        active_sessions_count = len([s for s in ai_trading_chatbot.active_sessions.values() if s.active])
        
        return {
            'success': True,
            'status': 'operational',
            'features': {
                'voice_commands': ai_trading_chatbot.voice_enabled,
                'dual_engine_integration': True,
                'auto_trading': True,
                'risk_management': True,
                'real_time_monitoring': True
            },
            'statistics': {
                'active_sessions': active_sessions_count,
                'total_sessions': len(ai_trading_chatbot.active_sessions),
                'supported_commands': len(ai_trading_chatbot.command_patterns)
            },
            'capabilities': [
                'Natural language trading commands',
                'Voice command processing',
                'Automated trade execution',
                'Real-time position monitoring',
                'Risk management and stop-loss',
                'Market analysis and news',
                'Option chain scanning',
                'Portfolio management'
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get chatbot status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def convert_speech_to_text(audio_content: bytes) -> str:
    """Convert speech to text using Whisper"""
    
    try:
        # Mock implementation - integrate with Azure Speech Services or Whisper
        # For now, return a sample command for testing
        
        # In production, this would use:
        # - Azure Cognitive Services Speech-to-Text
        # - OpenAI Whisper API
        # - Local Whisper model
        
        return "scan nifty with 1 lakh capital"  # Mock response
        
    except Exception as e:
        logger.error(f"Speech to text conversion failed: {e}")
        return ""

# Background task to monitor trading sessions
@router.on_event("startup")
async def start_session_monitoring():
    """Start background monitoring of trading sessions"""
    
    asyncio.create_task(ai_trading_chatbot.monitor_active_sessions())