"""MinIO / S3-compatible storage helper with security hardening, encryption, and virus scanning hooks."""

from __future__ import annotations

import io
import os
from typing import Optional

import boto3
from botocore.client import Config

try:
    from shared.runtime_config import is_production, validate_secret
except ImportError:
    from runtime_config import is_production, validate_secret

MINIO_ENDPOINT   = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = validate_secret("MINIO_ROOT_USER", os.getenv("MINIO_ROOT_USER"), min_length=4, required=is_production()) or os.getenv("MINIO_ROOT_USER", "eob_dev_minio_root")
MINIO_SECRET_KEY = validate_secret("MINIO_ROOT_PASSWORD", os.getenv("MINIO_ROOT_PASSWORD"), min_length=16, required=is_production()) or os.getenv("MINIO_ROOT_PASSWORD", "eob-dev-minio-root-pass-32-chars-long")
MINIO_REGION     = os.getenv("MINIO_REGION", "us-east-1")

BUCKETS = ["audio", "spectrograms", "graphs", "pdfs"]

_client: Optional["boto3.client"] = None

# Prohibited file extensions (potential executable/script attacks)
DANGEROUS_EXTENSIONS = {
    ".exe", ".dll", ".so", ".sh", ".bat", ".cmd", ".ps1", ".vbs",
    ".js", ".jsp", ".php", ".py", ".html", ".htm", ".svg", ".jar",
}


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
    """Create buckets, enforce private access policies, and configure encryption."""
    client = _get_client()
    existing = {b["Name"] for b in client.list_buckets().get("Buckets", [])}
    for bucket in BUCKETS:
        if bucket not in existing:
            client.create_bucket(Bucket=bucket)
            
        # Enforce public access block (no unauthorized reads)
        try:
            client.put_public_access_block(
                Bucket=bucket,
                PublicAccessBlockConfiguration={
                    "BlockPublicAcls": True,
                    "IgnorePublicAcls": True,
                    "BlockPublicPolicy": True,
                    "RestrictPublicBuckets": True,
                },
            )
        except Exception:
            pass
            
        # Enforce AES256 server-side encryption if supported by backend
        try:
            client.put_bucket_encryption(
                Bucket=bucket,
                ServerSideEncryptionConfiguration={
                    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
                },
            )
        except Exception:
            pass


def validate_file_content(data: bytes, filename: str) -> None:
    """Validate file extension and magic byte headers to prevent polyglot / format confusion attacks."""
    if not data:
        raise ValueError("Uploaded file is empty.")

    if len(data) > 100 * 1024 * 1024:
        raise ValueError("File exceeds maximum allowed size (100 MB).")

    ext = os.path.splitext(filename.lower())[1]
    if ext in DANGEROUS_EXTENSIONS:
        raise ValueError(f"File extension '{ext}' is prohibited.")

    header = data[:16]
    if ext == ".wav":
        if not (header.startswith(b"RIFF") and b"WAVE" in data[:12]):
            raise ValueError("Corrupted or invalid WAV file header.")
    elif ext in (".mp3",):
        if not (header.startswith(b"ID3") or header[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")):
            raise ValueError("Corrupted or invalid MP3 file header.")
    elif ext == ".flac":
        if not header.startswith(b"fLaC"):
            raise ValueError("Corrupted or invalid FLAC file header.")
    elif ext == ".pdf":
        if not header.startswith(b"%PDF-"):
            raise ValueError("Corrupted or invalid PDF file header.")
    elif ext == ".png":
        if not header.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Corrupted or invalid PNG file header.")


def scan_for_malware(data: bytes, filename: str) -> None:
    """Malware and virus scanning hook.
    
    # ponytail: checks for embedded executables and script injections in audio/pdf bytes.
    """
    if b"MZ\x90\x00" in data[:1024]:
        raise ValueError("Suspicious binary executable signature detected.")

    lower_slice = data[:4096].lower()
    if b"<script" in lower_slice or b"javascript:" in lower_slice or b"eval(" in lower_slice:
        raise ValueError("Prohibited executable script content detected in file payload.")

    clamav_host = os.getenv("CLAMAV_HOST")
    if clamav_host:
        try:
            import socket
            port = int(os.getenv("CLAMAV_PORT", "3310"))
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3.0)
                s.connect((clamav_host, port))
                s.sendall(b"zINSTREAM\0")
                size = len(data)
                s.sendall(size.to_bytes(4, byteorder="big") + data)
                s.sendall((0).to_bytes(4, byteorder="big"))
                res = s.recv(1024).decode("utf-8", errors="ignore")
                if "FOUND" in res:
                    raise ValueError(f"Malware detected by antivirus: {res.strip()}")
        except (ConnectionError, socket.timeout):
            pass


def upload_file(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload validated bytes to MinIO/S3, return presigned or endpoint storage key."""
    validate_file_content(data, key)
    scan_for_malware(data, key)
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
