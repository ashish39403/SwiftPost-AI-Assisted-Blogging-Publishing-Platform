import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

_BLOCKED_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "metadata.google.internal"}


def public_http_url(url, *, resolve=True):
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError({"url": "That image link is not allowed."})
    host = parsed.hostname.lower().rstrip(".")
    if host in _BLOCKED_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        raise ValidationError({"url": "That image link is not allowed."})
    if not resolve:
        return parsed.geturl()
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise ValidationError({"url": "That image link could not be reached."}) from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValidationError({"url": "That image link is not allowed."})
    return parsed.geturl()


def download_image(url):
    safe = public_http_url(url)
    try:
        response = httpx.get(
            safe,
            timeout=15.0,
            follow_redirects=False,
            headers={"User-Agent": "SwiftPost/1.0"},
        )
    except httpx.HTTPError as exc:
        raise ValidationError({"url": "That image could not be downloaded."}) from exc
    if response.status_code != 200:
        raise ValidationError({"url": "That image could not be downloaded."})
    content = response.content or b""
    if not content or len(content) > settings.MAX_IMAGE_BYTES:
        raise ValidationError({"url": "That image is empty or too large."})
    return SimpleUploadedFile("live-image", content, content_type="application/octet-stream")
