from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class Storage:
    def save(self, key, content, content_type):
        raise NotImplementedError

    def delete(self, key):
        raise NotImplementedError

    def url(self, key):
        raise NotImplementedError


class LocalStorage(Storage):
    """Writes bytes under MEDIA_ROOT. The key is server-generated."""

    def save(self, key, content, content_type):
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def delete(self, key):
        path = self._path(key)
        if path.exists():
            path.unlink()

    def url(self, key):
        return f"{settings.MEDIA_URL}{key}"

    def _path(self, key):
        root = Path(settings.MEDIA_ROOT).resolve()
        path = (root / key).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Storage key escapes the media root.")
        return path


class S3Storage(Storage):
    def __init__(self, client, bucket, public_base_url):
        self.client = client
        self.bucket = bucket
        self.public_base_url = public_base_url.rstrip("/")

    def save(self, key, content, content_type):
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def url(self, key):
        return f"{self.public_base_url}/{key}"


def get_storage():
    if settings.MEDIA_STORAGE == "s3":
        return _s3_storage()
    return LocalStorage()


def _s3_storage():
    if not settings.AWS_S3_BUCKET or not settings.AWS_S3_PUBLIC_BASE_URL:
        raise ImproperlyConfigured("S3 media storage requires AWS_S3_BUCKET and AWS_S3_PUBLIC_BASE_URL.")
    import boto3

    client = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION or None,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
    )
    return S3Storage(client, settings.AWS_S3_BUCKET, settings.AWS_S3_PUBLIC_BASE_URL)
