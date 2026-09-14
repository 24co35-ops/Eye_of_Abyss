"""MinIO / S3-compatible storage helper — Eye of Abyss.

Buckets: audio | spectrograms | graphs | pdfs

Override endpoint via MINIO_ENDPOINT env var (default: localhost:9000).
Compatible with Supabase Storage when STORAGE_BACKEND=supabase.
"""

from __future__ import annotations

import io
import os
from typing import Optional

import boto3
from botocore.client import Config

MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_REGION     = os.getenv("MINIO_REGION", "us-east-1")

BUCKETS = ["audio", "spectrograms", "graphs", "pdfs"]

_client: Optional["boto3.client"] = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name=MINIO_REGION,
            config=Config(signature_version="s3v4"),
        )
    return _client


def ensure_buckets() -> None:
    """Create buckets if they don't exist. Call once at service startup."""
    client = _get_client()
    existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
    for bucket in BUCKETS:
        if bucket not in existing:
            client.create_bucket(Bucket=bucket)


def upload_file(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload bytes to MinIO, return the storage key."""
    _get_client().put_object(
        Bucket=bucket,
        Key=key,
        Body=io.BytesIO(data),
        ContentType=content_type,
    )
    return f"{MINIO_ENDPOINT}/{bucket}/{key}"


def get_presigned_url(bucket: str, key: str, expires: int = 3600) -> str:
    """Return a presigned GET URL valid for `expires` seconds."""
    return _get_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def upload_from_path(bucket: str, key: str, path: str) -> str:
    with open(path, "rb") as f:
        return upload_file(bucket, key, f.read())
