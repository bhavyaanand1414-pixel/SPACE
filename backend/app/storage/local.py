"""
Storage service abstraction layer.

Provides a unified interface for storing and retrieving files,
supporting local filesystem and future S3-compatible backends.
"""

import os
import hashlib
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
from app.core.config import settings
from app.core.logging import logger


class BaseStorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save(self, file_obj: BinaryIO, destination: str) -> str:
        """Save a file and return the absolute storage path."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if a file exists at the given path."""
        ...

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete a file. Returns True if deleted, False if not found."""
        ...

    @abstractmethod
    def get_size(self, path: str) -> int:
        """Return file size in bytes."""
        ...


class LocalStorageBackend(BaseStorageBackend):
    """Local filesystem storage backend."""

    def __init__(self, root_path: Optional[str] = None):
        self.root = Path(root_path or settings.LOCAL_STORAGE_PATH).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorageBackend initialized at: {self.root}")

    def _resolve_safe_path(self, destination: str) -> Path:
        """Resolve destination path and prevent directory traversal attacks."""
        # Normalize and strip leading separators / parent refs
        clean = Path(destination).name  # Only keep the filename
        full_path = (self.root / clean).resolve()
        # Ensure the resolved path is still within root
        if not str(full_path).startswith(str(self.root)):
            raise ValueError(f"Path traversal detected: {destination}")
        return full_path

    def save(self, file_obj: BinaryIO, destination: str) -> str:
        """Save file from file-like object to local filesystem."""
        target_path = self._resolve_safe_path(destination)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as out_file:
            shutil.copyfileobj(file_obj, out_file)

        logger.info(f"File stored locally: {target_path} ({target_path.stat().st_size} bytes)")
        return str(target_path)

    def exists(self, path: str) -> bool:
        target = self._resolve_safe_path(path)
        return target.is_file()

    def delete(self, path: str) -> bool:
        target = self._resolve_safe_path(path)
        if target.is_file():
            target.unlink()
            logger.info(f"File deleted: {target}")
            return True
        return False

    def get_size(self, path: str) -> int:
        target = self._resolve_safe_path(path)
        return target.stat().st_size


def compute_sha256(file_obj: BinaryIO, chunk_size: int = 8192) -> str:
    """Compute SHA-256 hash of a file-like object, then reset seek position."""
    sha256 = hashlib.sha256()
    file_obj.seek(0)
    while True:
        chunk = file_obj.read(chunk_size)
        if not chunk:
            break
        sha256.update(chunk)
    file_obj.seek(0)
    return sha256.hexdigest()


def get_storage_backend() -> BaseStorageBackend:
    """Factory: return the configured storage backend."""
    if settings.STORAGE_TYPE == "local":
        return LocalStorageBackend()
    elif settings.STORAGE_TYPE in ("s3", "r2"):
        from app.storage.s3 import S3StorageBackend
        return S3StorageBackend()
    raise ValueError(f"Unsupported storage type: {settings.STORAGE_TYPE}")
