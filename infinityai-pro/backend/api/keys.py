"""
API Key Management endpoints for InfinityAI.Pro
Provides secure management of API keys and service credentials
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
from services.security.azure_keyvault import vault_manager, config
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

class ApiKeyUpdate(BaseModel):
    service: str
    key: str
    value: str

class ApiKeyStatus(BaseModel):
    service: str
    has_key: bool
    is_valid: bool
    last_updated: Optional[str] = None

@router.get("/status", response_model=Dict[str, ApiKeyStatus])
async def get_api_key_status():
    """Get status of all API keys"""
    
    # Define required API keys
    required_keys = {
        "openai": "OPENAI_API_KEY",
        "alpha_vantage": "ALPHA_VANTAGE_API_KEY", 
        "pinecone": "PINECONE_API_KEY",
        "azure_openai": "AZURE_OPENAI_KEY",
        "azure_speech": "AZURE_SPEECH_KEY",
        "huggingface": "HUGGINGFACE_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "coinswitch": "COINSWITCH_API_KEY",
        "polygon": "POLYGON_API_KEY",
        "twelve_data": "TWELVE_DATA_API_KEY",
        "telegram": "TELEGRAM_BOT_TOKEN",
        "sentry": "SENTRY_DSN"
    }
    
    status_dict = {}
    
    for service_name, env_key in required_keys.items():
        try:
            # Get the key value
            key_value = config.get(env_key)
            
            # Check if key exists and is not a placeholder
            has_key = bool(key_value and key_value not in [
                "your_api_key_here", 
                "your_secret_here", 
                "your_token_here",
                ""
            ])
            
            # For some services, we can do basic validation
            is_valid = has_key
            if has_key:
                if service_name == "openai" and key_value:
                    is_valid = key_value.startswith("sk-")
                elif service_name == "pinecone" and key_value:
                    is_valid = len(key_value) > 20  # Basic length check
                elif service_name == "alpha_vantage" and key_value:
                    is_valid = len(key_value) >= 8  # Basic length check
            
            status_dict[service_name] = ApiKeyStatus(
                service=service_name,
                has_key=has_key,
                is_valid=is_valid,
                last_updated=datetime.utcnow().isoformat() if has_key else None
            )
            
        except Exception as e:
            logger.error(f"Error checking status for {service_name}: {e}")
            status_dict[service_name] = ApiKeyStatus(
                service=service_name,
                has_key=False,
                is_valid=False
            )
    
    return status_dict

@router.get("/missing")
async def get_missing_api_keys():
    """Get list of missing API keys"""
    
    status = await get_api_key_status()
    missing_keys = []
    
    for service_name, key_status in status.items():
        if not key_status.has_key:
            missing_keys.append({
                "service": service_name,
                "description": _get_service_description(service_name),
                "signup_url": _get_service_signup_url(service_name),
                "priority": _get_service_priority(service_name)
            })
    
    # Sort by priority (high priority first)
    missing_keys.sort(key=lambda x: x["priority"], reverse=True)
    
    return {
        "missing_count": len(missing_keys),
        "missing_keys": missing_keys,
        "recommendations": _get_setup_recommendations()
    }

def _get_service_description(service: str) -> str:
    """Get description for API service"""
    descriptions = {
        "openai": "OpenAI GPT models for advanced AI capabilities",
        "alpha_vantage": "Alpha Vantage for real-time and historical market data",
        "pinecone": "Pinecone vector database for AI embeddings storage",
        "azure_openai": "Azure OpenAI for enterprise AI services",
        "azure_speech": "Azure Speech Services for text-to-speech and speech-to-text",
        "huggingface": "Hugging Face for open-source AI models",
        "perplexity": "Perplexity AI for advanced reasoning capabilities",
        "coinswitch": "CoinSwitch for cryptocurrency trading",
        "polygon": "Polygon.io for financial market data",
        "twelve_data": "Twelve Data for comprehensive market data",
        "telegram": "Telegram Bot for notifications and alerts",
        "sentry": "Sentry for error monitoring and tracking"
    }
    return descriptions.get(service, f"API service: {service}")

def _get_service_signup_url(service: str) -> str:
    """Get signup URL for API service"""
    urls = {
        "openai": "https://platform.openai.com/signup",
        "alpha_vantage": "https://www.alphavantage.co/support/#api-key",
        "pinecone": "https://www.pinecone.io/",
        "azure_openai": "https://azure.microsoft.com/en-us/products/ai-services/openai-service",
        "azure_speech": "https://azure.microsoft.com/en-us/products/ai-services/speech-to-text",
        "huggingface": "https://huggingface.co/join",
        "perplexity": "https://www.perplexity.ai/",
        "coinswitch": "https://coinswitch.co/pro",
        "polygon": "https://polygon.io/",
        "twelve_data": "https://twelvedata.com/pricing",
        "telegram": "https://core.telegram.org/bots#creating-a-new-bot",
        "sentry": "https://sentry.io/"
    }
    return urls.get(service, "")

def _get_service_priority(service: str) -> int:
    """Get setup priority for service (1-10, 10=highest)"""
    priorities = {
        "alpha_vantage": 10,  # Critical for market data
        "openai": 9,         # Important for AI features
        "pinecone": 8,       # Important for vector storage
        "azure_openai": 7,   # Alternative to OpenAI
        "huggingface": 6,    # Open source models
        "coinswitch": 5,     # Crypto trading
        "polygon": 4,        # Alternative market data
        "twelve_data": 4,    # Alternative market data
        "azure_speech": 3,   # Speech features
        "perplexity": 3,     # Advanced AI
        "telegram": 2,       # Notifications
        "sentry": 2          # Monitoring
    }
    return priorities.get(service, 1)

def _get_setup_recommendations() -> List[str]:
    """Get setup recommendations"""
    return [
        "1. Start with Alpha Vantage API key for market data (free tier available)",
        "2. Get OpenAI API key for advanced AI features (pay-per-use)",
        "3. Set up Pinecone for vector storage (free starter plan)",
        "4. Consider Azure OpenAI as enterprise alternative",
        "5. Add Telegram bot for notifications (free)",
        "6. Set up Sentry for error monitoring (free tier available)"
    ]

@router.post("/update")
async def update_api_key(key_update: ApiKeyUpdate):
    """Update an API key (admin only)"""
    
    # TODO: Add proper authentication/authorization
    # For now, this is a placeholder that would store in Key Vault
    
    try:
        # Map service name to environment variable
        service_mapping = {
            "openai": "OPENAI_API_KEY",
            "alpha_vantage": "ALPHA_VANTAGE_API_KEY",
            "pinecone": "PINECONE_API_KEY",
            "azure_openai": "AZURE_OPENAI_KEY",
            "azure_speech": "AZURE_SPEECH_KEY",
            "huggingface": "HUGGINGFACE_API_KEY",
            "perplexity": "PERPLEXITY_API_KEY",
            "coinswitch": "COINSWITCH_API_KEY",
            "polygon": "POLYGON_API_KEY",
            "twelve_data": "TWELVE_DATA_API_KEY",
            "telegram": "TELEGRAM_BOT_TOKEN",
            "sentry": "SENTRY_DSN"
        }
        
        env_key = service_mapping.get(key_update.service)
        if not env_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown service: {key_update.service}"
            )
        
        # Store in Key Vault if available
        secret_name = env_key.lower().replace("_", "-")
        if vault_manager.is_available():
            success = vault_manager.set_secret(
                secret_name, 
                key_update.value,
                tags={
                    "service": key_update.service,
                    "updated_by": "api_endpoint",
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            
            if success:
                return {
                    "status": "success",
                    "message": f"API key for {key_update.service} updated successfully",
                    "storage": "azure_keyvault"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to store API key in Key Vault"
                )
        else:
            # Key Vault not available - return instructions for manual setup
            return {
                "status": "info",
                "message": f"Key Vault not configured. Please add {env_key}={key_update.value} to your environment variables",
                "env_key": env_key,
                "storage": "manual"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/test/{service}")
async def test_api_key(service: str):
    """Test an API key"""
    
    # Basic API key testing for some services
    test_results = {"service": service, "tested": False, "valid": False, "message": ""}
    
    try:
        if service == "alpha_vantage":
            api_key = config.get("ALPHA_VANTAGE_API_KEY")
            if api_key:
                # Test Alpha Vantage API
                import aiohttp
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=MSFT&apikey={api_key}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "Global Quote" in data:
                                test_results.update({
                                    "tested": True,
                                    "valid": True,
                                    "message": "API key is working correctly"
                                })
                            else:
                                test_results.update({
                                    "tested": True,
                                    "valid": False,
                                    "message": "API key may be invalid or rate limited"
                                })
                        else:
                            test_results.update({
                                "tested": True,
                                "valid": False,
                                "message": f"API returned status {response.status}"
                            })
            else:
                test_results["message"] = "No API key found"
        
        elif service == "openai":
            api_key = config.get("OPENAI_API_KEY")
            if api_key and api_key.startswith("sk-"):
                test_results.update({
                    "tested": False,
                    "valid": True,
                    "message": "API key format appears correct (actual test would require API call)"
                })
            else:
                test_results.update({
                    "tested": False,
                    "valid": False,
                    "message": "Invalid API key format or not found"
                })
        
        else:
            test_results["message"] = f"Testing not implemented for {service}"
            
    except Exception as e:
        test_results.update({
            "tested": True,
            "valid": False,
            "message": f"Test failed: {str(e)}"
        })
    
    return test_results