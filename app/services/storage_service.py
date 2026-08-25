from __future__ import annotations

import os
from contextlib import contextmanager
from typing import BinaryIO, Iterator

from app.core.config import settings


class LocalStorage:
    def __init__(self, root: str) -> None:
        self.root = root
        os.makedirs(root, exist_ok=True)

    def _path(self, key: str) -> str:
        return os.path.join(self.root, key)

    @contextmanager
    def open_write(self, key: str) -> Iterator[BinaryIO]:
        path = self._path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            yield f

    def put_bytes(self, key: str, data: bytes) -> None:
        with self.open_write(key) as f:
            f.write(data)

    def get_bytes(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)

    def exists(self, key: str) -> bool:
        return os.path.exists(self._path(key))


class R2Storage:
    def __init__(self) -> None:
        import boto3
        from botocore.config import Config

        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=Config(signature_version="s3v4"),
        )
        self.bucket = settings.r2_bucket

    @contextmanager
    def open_write(self, key: str) -> Iterator[BinaryIO]:
        import tempfile

        with tempfile.SpooledTemporaryFile(max_size=32 * 1024 * 1024) as buf:
            yield buf
            buf.seek(0)
            self.client.upload_fileobj(buf, self.bucket, key)

    def put_bytes(self, key: str, data: bytes) -> None:
        with self.open_write(key) as f:
            f.write(data)

    def get_bytes(self, key: str) -> bytes:
        import io

        buf = io.BytesIO()
        self.client.download_fileobj(self.bucket, key, buf)
        return buf.getvalue()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


def get_storage() -> LocalStorage | R2Storage:
    if settings.storage_backend == "r2":
        return R2Storage()
    return LocalStorage(settings.local_storage_root)
