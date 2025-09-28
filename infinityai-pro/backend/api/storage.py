# api/storage.py
"""
Storage API endpoints for cloud storage operations
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, Optional
import os
import tempfile
from services.backup_service import backup_service

router = APIRouter()

@router.post("/upload/model")
async def upload_model(file: UploadFile = File(...), model_name: str = None):
    """Upload ML model to cloud storage"""
    if not model_name:
        model_name = file.filename

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        # Initialize storage service
        await cloud_storage_service.initialize()

        # Upload to cloud
        result = await cloud_storage_service.upload_model(temp_path, model_name)

        if result:
            return {
                "success": True,
                "url": result,
                "model_name": model_name
            }
        else:
            raise HTTPException(status_code=500, detail="Upload failed")

    finally:
        # Cleanup temp file
        os.unlink(temp_path)

@router.get("/download/model/{model_name}")
async def download_model(model_name: str):
    """Get download URL for ML model"""
    try:
        await cloud_storage_service.initialize()

        url = await cloud_storage_service.get_model_url(model_name)
        if url:
            return {"success": True, "url": url, "expires_in": 3600}
        else:
            raise HTTPException(status_code=404, detail="Model not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.post("/upload/trading-data")
async def upload_trading_data(file: UploadFile = File(...), symbol: str = None, data_type: str = "historical"):
    """Upload trading data to cloud storage"""
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        await cloud_storage_service.initialize()

        result = await cloud_storage_service.upload_trading_data(temp_path, symbol, data_type)

        if result:
            return {
                "success": True,
                "url": result,
                "symbol": symbol,
                "data_type": data_type
            }
        else:
            raise HTTPException(status_code=500, detail="Upload failed")

    finally:
        os.unlink(temp_path)

@router.post("/upload/chart")
async def upload_chart(file: UploadFile = File(...), symbol: str = None, analysis_id: str = None):
    """Upload chart analysis image to cloud storage"""
    if not symbol or not analysis_id:
        raise HTTPException(status_code=400, detail="Symbol and analysis_id are required")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    try:
        await cloud_storage_service.initialize()

        result = await cloud_storage_service.upload_chart_image(temp_path, symbol, analysis_id)

        if result:
            return {
                "success": True,
                "url": result,
                "symbol": symbol,
                "analysis_id": analysis_id
            }
        else:
            raise HTTPException(status_code=500, detail="Upload failed")

    finally:
        os.unlink(temp_path)

@router.post("/backup/database")
async def backup_database():
    """Backup ChromaDB database to cloud storage"""
    try:
        await cloud_storage_service.initialize()

        # Assume ChromaDB is in the default location
        db_path = "chroma_db/chroma.sqlite3"

        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail="Database file not found")

        result = await cloud_storage_service.backup_database(db_path)

        if result:
            return {"success": True, "backup_url": result}
        else:
            raise HTTPException(status_code=500, detail="Backup failed")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.post("/backup/models")
async def backup_models():
    """Backup all ML models to cloud storage"""
    try:
        await cloud_storage_service.initialize()

        models_dir = "models"
        uploaded_models = await cloud_storage_service.backup_models(models_dir)

        return {
            "success": True,
            "uploaded_models": uploaded_models,
            "count": len(uploaded_models)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Models backup failed: {str(e)}")

@router.get("/stats")
async def get_storage_stats():
    """Get cloud storage service statistics"""
    try:
        await cloud_storage_service.initialize()

        stats = cloud_storage_service.get_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.post("/cleanup")
async def cleanup_old_files(days_old: int = 30):
    """Clean up old files from cloud storage"""
    try:
        await cloud_storage_service.initialize()

        deleted_count = await cloud_storage_service.cleanup_old_files(days_old)

        return {
            "success": True,
            "deleted_files": deleted_count,
            "days_old": days_old
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.post("/backup/start-service")
async def start_backup_service():
    """Start the automated backup service"""
    try:
        await backup_service.start()
        return {"success": True, "message": "Backup service started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start backup service: {str(e)}")

@router.post("/backup/stop-service")
async def stop_backup_service():
    """Stop the automated backup service"""
    try:
        await backup_service.stop()
        return {"success": True, "message": "Backup service stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop backup service: {str(e)}")

@router.post("/backup/manual")
async def manual_backup(components: List[str] = None):
    """Perform manual backup"""
    try:
        result = await backup_service.manual_backup(components)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual backup failed: {str(e)}")

@router.get("/backup/stats")
async def get_backup_stats():
    """Get backup service statistics"""
    try:
        stats = backup_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backup stats: {str(e)}")