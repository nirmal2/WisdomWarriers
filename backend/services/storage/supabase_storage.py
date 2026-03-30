from __future__ import annotations

import io
import mimetypes
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

import logging

import boto3
from botocore.config import Config
from botocore.handlers import validate_bucket_name

from backend.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class UploadResult:
    path: str
    public_url: str


def _guess_extension(content_type: str | None, source_url: str) -> str:
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ext
    parsed = urlparse(source_url)
    last = parsed.path.rsplit("/", 1)[-1]
    if "." in last:
        return "." + last.rsplit(".", 1)[-1].lower()
    return ".jpg"


def _make_s3_client(settings):
    client = boto3.client(
        "s3",
        endpoint_url=settings.supabase_storage_s3_endpoint,
        aws_access_key_id=settings.supabase_storage_access_key_id,
        aws_secret_access_key=settings.supabase_storage_secret_access_key,
        region_name=settings.supabase_storage_region,
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )
    # Supabase bucket names can contain spaces which boto3's client-side
    # validator rejects; the actual S3-compatible endpoint accepts them fine.
    client.meta.events.unregister("before-parameter-build.s3", validate_bucket_name)
    return client


def _upload_image_to_supabase(source_url: str, bucket_name: str, object_key: str) -> UploadResult | None:
    settings = get_settings()
    if not settings.supabase_storage_access_key_id or not settings.supabase_storage_secret_access_key:
        return None
    if not settings.supabase_storage_s3_endpoint or not settings.supabase_url:
        return None

    download_req = Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(download_req, timeout=30) as resp:
        data = resp.read()
        content_type = resp.headers.get("Content-Type")

    mime_type = content_type or "application/octet-stream"

    s3 = _make_s3_client(settings)
    s3.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=io.BytesIO(data),
        ContentType=mime_type,
    )

    public_bucket_encoded = quote(bucket_name, safe="")
    public_key_encoded = quote(object_key, safe="/")
    public_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public"
        f"/{public_bucket_encoded}/{public_key_encoded}"
    )
    return UploadResult(path=object_key, public_url=public_url)


def upload_display_image_to_supabase(display_url: str, run_id: int, post_id: str) -> UploadResult | None:
    settings = get_settings()
    object_key = f"runs/{run_id}/{post_id}{_guess_extension(None, display_url)}"
    return _upload_image_to_supabase(display_url, settings.supabase_posts_display_bucket, object_key)


def upload_profile_image_to_supabase(profile_image_urls: str | Iterable[str], profile_id: str) -> UploadResult | None:
    settings = get_settings()
    candidates = [profile_image_urls] if isinstance(profile_image_urls, str) else list(profile_image_urls)

    for profile_image_url in dict.fromkeys(url for url in candidates if url):
        object_key = f"profiles/{profile_id}{_guess_extension(None, profile_image_url)}"
        try:
            return _upload_image_to_supabase(profile_image_url, settings.supabase_profile_picture_bucket, object_key)
        except Exception:
            logger.info("Profile image download failed for %s; trying next candidate if available", profile_image_url, exc_info=True)

    return None
