"""Cloud storage service"""
class CloudStorageService:
    async def upload(self, data, key):
        return {"uploaded": key, "status": "success"}

cloud_storage_service = CloudStorageService()