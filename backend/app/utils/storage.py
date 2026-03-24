"""
File storage utilities supporting AWS S3 and local filesystem fallback.
Automatically chooses based on configuration.
"""
import os
import uuid
import shutil
from typing import Optional, BinaryIO
from pathlib import Path

from app.config import settings

# Local uploads directory (fallback when no cloud storage configured)
LOCAL_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


class LocalStorageService:
    """Local filesystem storage for development (no S3/Cloudinary needed)"""

    def __init__(self):
        LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        folder: str = "meetings",
        content_type: Optional[str] = None
    ) -> str:
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        folder_path = LOCAL_UPLOAD_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        dest = folder_path / unique_filename

        with open(dest, 'wb') as f:
            while chunk := file_obj.read(8192):
                f.write(chunk)

        return f"local://{folder}/{unique_filename}"

    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        return f"local://{key}"

    async def delete_file(self, key: str) -> bool:
        try:
            path = LOCAL_UPLOAD_DIR / key.replace("local://", "")
            if path.exists():
                path.unlink()
            return True
        except Exception:
            return False

    async def file_exists(self, key: str) -> bool:
        path = LOCAL_UPLOAD_DIR / key.replace("local://", "")
        return path.exists()

    async def download_file(self, key: str, local_path: str) -> str:
        src = LOCAL_UPLOAD_DIR / key.replace("local://", "")
        shutil.copy2(str(src), local_path)
        return local_path


class S3StorageService:
    """AWS S3 storage service"""

    def __init__(self):
        import boto3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_BUCKET_NAME

    async def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        folder: str = "meetings",
        content_type: Optional[str] = None
    ) -> str:
        from botocore.exceptions import ClientError

        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        key = f"{folder}/{unique_filename}"

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        try:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, key, ExtraArgs=extra_args)
            return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")

    async def get_file_url(self, key: str, expires_in: int = 3600) -> str:
        from botocore.exceptions import ClientError
        try:
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}")

    async def delete_file(self, key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            print(f"Failed to delete file {key}: {str(e)}")
            return False

    async def file_exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    async def download_file(self, key: str, local_path: str) -> str:
        self.s3_client.download_file(self.bucket_name, key, local_path)
        return local_path


# Lazy singleton
_storage_instance = None


def get_storage():
    """Get storage service instance (lazy initialization)"""
    global _storage_instance
    if _storage_instance is None:
        if settings.use_s3:
            _storage_instance = S3StorageService()
            import logging
            logging.getLogger(__name__).info("Storage: Using AWS S3")
        else:
            _storage_instance = LocalStorageService()
            import logging
            logging.getLogger(__name__).info("Storage: Using local filesystem (uploads/)")
    return _storage_instance


def reset_storage():
    """Reset storage singleton (useful for testing or config reload)"""
    global _storage_instance
    _storage_instance = None
