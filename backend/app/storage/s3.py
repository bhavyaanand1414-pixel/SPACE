"""
S3 & Cloudflare R2 Storage Backend for SIH1518 Platform.

Compatible with:
- Cloudflare R2 (S3-compatible API, zero egress fees)
- AWS S3 / MinIO / DigitalOcean Spaces
"""

import os
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional
from app.core.config import settings
from app.core.logging import logger
from app.storage.local import BaseStorageBackend


class S3StorageBackend(BaseStorageBackend):
    """
    S3 & Cloudflare R2 storage backend.
    Uses boto3 with S3-compatible endpoints for Cloudflare R2 or AWS S3.
    """

    def __init__(self):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "boto3 is required for S3/Cloudflare R2 storage. "
                "Install it via: pip install boto3"
            )

        self.bucket_name = settings.S3_BUCKET_NAME
        self.endpoint_url = settings.S3_ENDPOINT_URL or None
        self.region_name = settings.S3_REGION_NAME or "auto"
        self.custom_domain = settings.S3_CUSTOM_DOMAIN or None

        session = boto3.session.Session()
        self.client = session.client(
            service_name="s3",
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
        )
        logger.info(f"S3/R2 Storage backend initialized on bucket: {self.bucket_name} (endpoint: {self.endpoint_url})")

    def save(self, file_obj: BinaryIO, destination: str) -> str:
        """Upload file-like object to S3 / Cloudflare R2 bucket."""
        clean_key = Path(destination).name
        file_obj.seek(0)
        
        self.client.upload_fileobj(
            file_obj,
            self.bucket_name,
            clean_key,
        )
        logger.info(f"Uploaded {clean_key} to R2/S3 bucket {self.bucket_name}")
        return self.get_url(clean_key)

    def exists(self, path: str) -> bool:
        """Check if an object exists in S3 / R2."""
        clean_key = Path(path).name
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=clean_key)
            return True
        except Exception:
            return False

    def delete(self, path: str) -> bool:
        """Delete an object from S3 / R2."""
        clean_key = Path(path).name
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=clean_key)
            logger.info(f"Deleted {clean_key} from R2/S3 bucket {self.bucket_name}")
            return True
        except Exception as exc:
            logger.warning(f"Failed to delete {clean_key} from R2/S3: {exc}")
            return False

    def get_size(self, path: str) -> int:
        """Get object size in bytes from S3 / R2."""
        clean_key = Path(path).name
        response = self.client.head_object(Bucket=self.bucket_name, Key=clean_key)
        return int(response.get("ContentLength", 0))

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate public or presigned download URL."""
        if self.custom_domain:
            return f"https://{self.custom_domain}/{key}"
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
        except Exception:
            return f"s3://{self.bucket_name}/{key}"
