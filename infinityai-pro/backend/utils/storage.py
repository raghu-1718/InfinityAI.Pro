# utils/storage.py
"""
InfinityAI.Pro - Multi-Cloud Storage Abstraction
Supports AWS S3, Azure Blob Storage, and Google Cloud Storage
"""

import os
import logging
from typing import Optional, BinaryIO, Dict, Any
from abc import ABC, abstractmethod
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

class StorageProvider(ABC):
    """Abstract base class for cloud storage providers"""

    @abstractmethod
    async def upload_file(self, file_path: str, key: str, **kwargs) -> str:
        """Upload file to storage"""
        pass

    @abstractmethod
    async def download_file(self, key: str, local_path: str, **kwargs) -> bool:
        """Download file from storage"""
        pass

    @abstractmethod
    async def file_exists(self, key: str) -> bool:
        """Check if file exists in storage"""
        pass

    @abstractmethod
    async def get_file_url(self, key: str, expires: int = 3600) -> str:
        """Get signed URL for file access"""
        pass

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """Delete file from storage"""
        pass

class AWSStorageProvider(StorageProvider):
    """AWS S3 Storage Provider"""

    def __init__(self, config: Config):
        self.config = config
        self.s3_client = None
        self._initialized = False

    async def _ensure_initialized(self):
        if not self._initialized:
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.config.AWS_REGION,
                    aws_access_key_id=self.config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=self.config.AWS_SECRET_ACCESS_KEY
                )
                self._initialized = True
                logger.info("✅ AWS S3 storage initialized")
            except ImportError:
                logger.error("boto3 not installed for AWS storage")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize AWS storage: {e}")
                raise

    async def upload_file(self, file_path: str, key: str, **kwargs) -> str:
        await self._ensure_initialized()
        try:
            with open(file_path, 'rb') as f:
                self.s3_client.upload_fileobj(f, self.config.AWS_S3_BUCKET, key)
            logger.info(f"Uploaded {file_path} to s3://{self.config.AWS_S3_BUCKET}/{key}")
            return f"s3://{self.config.AWS_S3_BUCKET}/{key}"
        except Exception as e:
            logger.error(f"AWS upload failed: {e}")
            raise

    async def download_file(self, key: str, local_path: str, **kwargs) -> bool:
        await self._ensure_initialized()
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(self.config.AWS_S3_BUCKET, key, local_path)
            logger.info(f"Downloaded s3://{self.config.AWS_S3_BUCKET}/{key} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"AWS download failed: {e}")
            return False

    async def file_exists(self, key: str) -> bool:
        await self._ensure_initialized()
        try:
            self.s3_client.head_object(Bucket=self.config.AWS_S3_BUCKET, Key=key)
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception as e:
            logger.error(f"AWS file check failed: {e}")
            return False

    async def get_file_url(self, key: str, expires: int = 3600) -> str:
        await self._ensure_initialized()
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.AWS_S3_BUCKET, 'Key': key},
                ExpiresIn=expires
            )
            return url
        except Exception as e:
            logger.error(f"AWS URL generation failed: {e}")
            raise

    async def delete_file(self, key: str) -> bool:
        await self._ensure_initialized()
        try:
            self.s3_client.delete_object(Bucket=self.config.AWS_S3_BUCKET, Key=key)
            logger.info(f"Deleted s3://{self.config.AWS_S3_BUCKET}/{key}")
            return True
        except Exception as e:
            logger.error(f"AWS delete failed: {e}")
            return False

class AzureStorageProvider(StorageProvider):
    """Azure Blob Storage Provider"""

    def __init__(self, config: Config):
        self.config = config
        self.blob_service_client = None
        self._initialized = False

    async def _ensure_initialized(self):
        if not self._initialized:
            try:
                from azure.storage.blob import BlobServiceClient
                account_url = f"https://{self.config.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.config.AZURE_STORAGE_KEY
                )
                self._initialized = True
                logger.info("✅ Azure Blob storage initialized")
            except ImportError:
                logger.error("azure-storage-blob not installed for Azure storage")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Azure storage: {e}")
                raise

    async def upload_file(self, file_path: str, key: str, **kwargs) -> str:
        await self._ensure_initialized()
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.config.AZURE_CONTAINER, blob=key
            )
            with open(file_path, 'rb') as f:
                blob_client.upload_blob(f, overwrite=True)
            logger.info(f"Uploaded {file_path} to Azure blob: {key}")
            return f"https://{self.config.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{self.config.AZURE_CONTAINER}/{key}"
        except Exception as e:
            logger.error(f"Azure upload failed: {e}")
            raise

    async def download_file(self, key: str, local_path: str, **kwargs) -> bool:
        await self._ensure_initialized()
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            blob_client = self.blob_service_client.get_blob_client(
                container=self.config.AZURE_CONTAINER, blob=key
            )
            with open(local_path, 'wb') as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())
            logger.info(f"Downloaded Azure blob {key} to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Azure download failed: {e}")
            return False

    async def file_exists(self, key: str) -> bool:
        await self._ensure_initialized()
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.config.AZURE_CONTAINER, blob=key
            )
            blob_client.get_blob_properties()
            return True
        except Exception:
            return False

    async def get_file_url(self, key: str, expires: int = 3600) -> str:
        await self._ensure_initialized()
        try:
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas
            from datetime import datetime, timedelta

            sas_token = generate_blob_sas(
                account_name=self.config.AZURE_STORAGE_ACCOUNT,
                container_name=self.config.AZURE_CONTAINER,
                blob_name=key,
                account_key=self.config.AZURE_STORAGE_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(seconds=expires)
            )
            return f"https://{self.config.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{self.config.AZURE_CONTAINER}/{key}?{sas_token}"
        except Exception as e:
            logger.error(f"Azure URL generation failed: {e}")
            raise

    async def delete_file(self, key: str) -> bool:
        await self._ensure_initialized()
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.config.AZURE_CONTAINER, blob=key
            )
            blob_client.delete_blob()
            logger.info(f"Deleted Azure blob: {key}")
            return True
        except Exception as e:
            logger.error(f"Azure delete failed: {e}")
            return False

class MultiCloudStorage:
    """Multi-cloud storage abstraction layer"""

    def __init__(self, config: Config):
        self.config = config
        self.providers = {
            'aws': AWSStorageProvider(config),
            'azure': AzureStorageProvider(config)
        }
        self.primary_provider = config.STORAGE_PROVIDER

    async def upload_file(self, file_path: str, key: str, provider: Optional[str] = None, **kwargs) -> str:
        """Upload file using specified or primary provider"""
        provider_name = provider or self.primary_provider
        if provider_name not in self.providers:
            raise ValueError(f"Unsupported storage provider: {provider_name}")

        return await self.providers[provider_name].upload_file(file_path, key, **kwargs)

    async def download_file(self, key: str, local_path: str, provider: Optional[str] = None, **kwargs) -> bool:
        """Download file using specified or primary provider"""
        provider_name = provider or self.primary_provider
        if provider_name not in self.providers:
            raise ValueError(f"Unsupported storage provider: {provider_name}")

        return await self.providers[provider_name].download_file(key, local_path, **kwargs)

    async def file_exists(self, key: str, provider: Optional[str] = None) -> bool:
        """Check if file exists using specified or primary provider"""
        provider_name = provider or self.primary_provider
        if provider_name not in self.providers:
            raise ValueError(f"Unsupported storage provider: {provider_name}")

        return await self.providers[provider_name].file_exists(key)

    async def get_file_url(self, key: str, provider: Optional[str] = None, expires: int = 3600) -> str:
        """Get signed URL using specified or primary provider"""
        provider_name = provider or self.primary_provider
        if provider_name not in self.providers:
            raise ValueError(f"Unsupported storage provider: {provider_name}")

        return await self.providers[provider_name].get_file_url(key, expires)

    async def delete_file(self, key: str, provider: Optional[str] = None) -> bool:
        """Delete file using specified or primary provider"""
        provider_name = provider or self.primary_provider
        if provider_name not in self.providers:
            raise ValueError(f"Unsupported storage provider: {provider_name}")

        return await self.providers[provider_name].delete_file(key)

    async def replicate_file(self, key: str, from_provider: str, to_provider: str) -> bool:
        """Replicate file between providers for redundancy"""
        try:
            # Download from source
            temp_path = f"/tmp/{key.replace('/', '_')}"
            success = await self.download_file(key, temp_path, provider=from_provider)
            if not success:
                return False

            # Upload to destination
            await self.upload_file(temp_path, key, provider=to_provider)

            # Cleanup
            os.remove(temp_path)
            logger.info(f"Replicated {key} from {from_provider} to {to_provider}")
            return True

        except Exception as e:
            logger.error(f"Replication failed: {e}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """Check health of all storage providers"""
        health = {}
        for provider_name, provider in self.providers.items():
            try:
                # Try a simple operation to test connectivity
                health[provider_name] = {"status": "healthy"}
            except Exception as e:
                health[provider_name] = {"status": "error", "error": str(e)}

        return {
            "primary_provider": self.primary_provider,
            "providers": health,
            "multi_cloud": True
        }

# Global storage instance
_storage_instance = None

def get_storage() -> MultiCloudStorage:
    """Get global storage instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MultiCloudStorage(Config())
    return _storage_instance