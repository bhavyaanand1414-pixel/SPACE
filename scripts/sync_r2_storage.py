#!/usr/bin/env python3
"""
SIH1518 — Cloudflare R2 / AWS S3 Satellite Data & Reports Sync Utility.

Syncs local data/storage and reports/ folders with Cloudflare R2 bucket.
Usage:
    python scripts/sync_r2_storage.py --direction upload
    python scripts/sync_r2_storage.py --direction download
"""

import argparse
import os
import sys
from pathlib import Path

def get_r2_client():
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        print("[ERROR] boto3 is required. Install via: pip install boto3")
        sys.exit(1)

    endpoint_url = os.getenv("S3_ENDPOINT_URL")
    access_key = os.getenv("S3_ACCESS_KEY_ID")
    secret_key = os.getenv("S3_SECRET_ACCESS_KEY")
    bucket = os.getenv("S3_BUCKET_NAME", "sih1518-storage")

    if not endpoint_url or not access_key or not secret_key:
        print("[WARNING] S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, or S3_SECRET_ACCESS_KEY not set in environment.")
        print("Please check your .env file or Cloudflare R2 dashboard.")

    session = boto3.session.Session()
    client = session.client(
        service_name="s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url,
        region_name=os.getenv("S3_REGION_NAME", "auto"),
        config=Config(s3={"addressing_style": "path"}, signature_version="s3v4"),
    )
    return client, bucket

def sync_upload(local_dirs, client, bucket):
    print(f"[*] Uploading files to Cloudflare R2 / S3 bucket: {bucket}")
    total = 0
    for local_dir in local_dirs:
        path = Path(local_dir).resolve()
        if not path.exists():
            continue
        for file_path in path.glob("**/*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                rel_key = str(file_path.relative_to(path.parent))
                print(f"  -> Uploading: {rel_key} ({file_path.stat().st_size / 1024:.1f} KB)")
                try:
                    with open(file_path, "rb") as f:
                        client.upload_fileobj(f, bucket, rel_key)
                    total += 1
                except Exception as exc:
                    print(f"     [FAILED] {exc}")
    print(f"[SUCCESS] Uploaded {total} files to R2/S3 bucket {bucket}.")

def sync_download(target_dir, client, bucket):
    print(f"[*] Downloading files from Cloudflare R2 / S3 bucket: {bucket}")
    target_path = Path(target_dir).resolve()
    target_path.mkdir(parents=True, exist_ok=True)
    
    paginator = client.get_paginator("list_objects_v2")
    total = 0
    for page in paginator.paginate(Bucket=bucket):
        for item in page.get("Contents", []):
            key = item["Key"]
            dest = target_path / key
            dest.parent.mkdir(parents=True, exist_ok=True)
            print(f"  <- Downloading: {key} to {dest}")
            try:
                client.download_file(bucket, key, str(dest))
                total += 1
            except Exception as exc:
                print(f"     [FAILED] {exc}")
    print(f"[SUCCESS] Downloaded {total} files from R2/S3 bucket {bucket}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync SIH1518 satellite data with Cloudflare R2 / S3")
    parser.add_argument("--direction", choices=["upload", "download"], default="upload")
    args = parser.parse_args()

    client, bucket = get_r2_client()
    if args.direction == "upload":
        sync_upload(["./data/storage", "./reports"], client, bucket)
    else:
        sync_download("./data", client, bucket)
