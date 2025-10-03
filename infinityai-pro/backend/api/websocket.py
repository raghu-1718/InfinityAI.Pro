"""
WebSocket API for Real-time Communication
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json
import logging
import asyncio
from datetime import datetime

from services.websocket_manager import websocket_manager
from services.market_data_manager import market_data_manager
from services.advanced_ai_engine import advanced_ai_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    
    await websocket_manager.connect(websocket, user_id)
    logger.info(f"WebSocket connected for user: {user_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process message
            response = await process_websocket_message(data, user_id)
            
            # Send response back
            await websocket_manager.send_personal_message(response, user_id)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        websocket_manager.disconnect(user_id)

async def process_websocket_message(message: str, user_id: str) -> str:
    """Process incoming WebSocket messages"""
    
    try:
        data = json.loads(message)
        message_type = data.get('type', 'unknown')
        
        if message_type == 'analysis_request':
            return await handle_analysis_request(data, user_id)
        elif message_type == 'market_data_request':
            return await handle_market_data_request(data, user_id)
        elif message_type == 'trading_command':
            return await handle_trading_command(data, user_id)
        elif message_type == 'ping':
            return json.dumps({
                'type': 'pong',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return json.dumps({
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            })
            
    except Exception as e:
        logger.error(f"WebSocket message processing error: {e}")
        return json.dumps({
            'type': 'error',
            'message': str(e)
        })

async def handle_analysis_request(data: Dict[str, Any], user_id: str) -> str:
    """Handle analysis requests via WebSocket"""
    
    try:
        symbol = data.get('symbol', 'NIFTY')
        analysis_type = data.get('analysis_type', 'quick')
        
        # Run AI analysis
        result = await advanced_ai_engine.analyze_market_comprehensive(
            market_data=data.get('market_data', {}),
            analysis_type=analysis_type
        )
        
        return json.dumps({
            'type': 'analysis_result',
            'symbol': symbol,
            'data': result,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
        
    except Exception as e:
        return json.dumps({
            'type': 'analysis_error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

async def handle_market_data_request(data: Dict[str, Any], user_id: str) -> str:
    """Handle market data requests via WebSocket"""
    
    try:
        symbol = data.get('symbol', 'NIFTY')
        
        # Get real-time market data
        quote = await market_data_manager.get_real_time_quote(symbol)
        
        return json.dumps({
            'type': 'market_data',
            'symbol': symbol,
            'data': {
                'price': quote.get('price', 0),
                'change': quote.get('change', 0),
                'change_percent': quote.get('change_percent', 0),
                'volume': quote.get('volume', 0),
                'high': quote.get('high', 0),
                'low': quote.get('low', 0),
                'timestamp': datetime.now().isoformat()
            },
            'user_id': user_id
        })
        
    except Exception as e:
        return json.dumps({
            'type': 'market_data_error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

async def handle_trading_command(data: Dict[str, Any], user_id: str) -> str:
    """Handle trading commands via WebSocket"""
    
    try:
        command = data.get('command', '')
        symbol = data.get('symbol', 'NIFTY')
        
        # Process trading command
        result = {
            'command_processed': command,
            'symbol': symbol,
            'status': 'executed',
            'message': f'Trading command "{command}" processed for {symbol}'
        }
        
        return json.dumps({
            'type': 'trading_result',
            'data': result,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
        
    except Exception as e:
        return json.dumps({
            'type': 'trading_error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

# Background task to send periodic updates
async def send_periodic_updates():
    """Send periodic market updates to connected clients"""
    
    while True:
        try:
            # Get market data for major indices
            symbols = ['NIFTY', 'BANKNIFTY', 'SENSEX']
            
            for symbol in symbols:
                try:
                    quote = await market_data_manager.get_real_time_quote(symbol)
                    
                    update_message = json.dumps({
                        'type': 'market_update',
                        'symbol': symbol,
                        'data': quote,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Broadcast to all connected clients
                    await websocket_manager.broadcast(update_message)
                    
                except Exception as e:
                    logger.error(f"Failed to get quote for {symbol}: {e}")
            
            # Wait 30 seconds before next update
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Periodic update error: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Periodic updates will be started by the main application