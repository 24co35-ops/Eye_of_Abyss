"""Reject outbound URLs that can reach loopback, link-local, or cloud metadata."""

from __future__ import annotations

import ipaddress
import os
import socket
from urllib.parse import urlparse

_METADATA_HOSTS = {
    "metadata.google.internal",
    "metadata.goog",
    "instance-data",
}

_DEFAULT_MODULE_HOSTS = {
    "voiceguard",
    "shadowtrace",
    "chaineye",
    "case-engine",
    "localhost",
    "127.0.0.1",
}


class UnsafeUrlError(ValueError):
    pass


def _allowed_module_hosts() -> set[str]:
    raw = os.getenv("ALLOWED_MODULE_HOSTS", "")
    hosts = {h.strip().lower() for h in raw.split(",") if h.strip()}
    return hosts or set(_DEFAULT_MODULE_HOSTS)


def _allowed_webhook_domains() -> set[str]:
    raw = os.getenv("ALLOWED_WEBHOOK_DOMAINS", "").strip()
    if not raw:
        return set()
    return {d.strip().lower() for d in raw.split(",") if d.strip()}


def _resolved_ips(host: str, port: int) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Host could not be resolved: {host}") from exc
    ips = []
    for info in infos:
        try:
            ips.append(ipaddress.ip_address(info[4][0]))
        except ValueError as exc:
            raise UnsafeUrlError("Unparseable address") from exc
    if not ips:
        raise UnsafeUrlError(f"Host could not be resolved: {host}")
    return ips


def _reject_special(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if (
        ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        or str(ip) == "169.254.169.254"
    ):
        raise UnsafeUrlError("URL resolves to a blocked address")


def assert_public_http_url(url: str, *, https_only: bool = False) -> str:
    """Webhooks: public http(s) only. Production requires https."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrlError("Only absolute http(s) URLs are allowed")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials in the URL are not allowed")
    host = parsed.hostname.lower().rstrip(".")
    if host in _METADATA_HOSTS or host.endswith(".local") or host.endswith(".internal"):
        raise UnsafeUrlError("Internal hostnames are not allowed")
    allowed_domains = _allowed_webhook_domains()
    if allowed_domains and not any(host == d or host.endswith("." + d) for d in allowed_domains):
        raise UnsafeUrlError(f"Host '{host}' is not in the allowed webhook domains list")
    if https_only and parsed.scheme != "https":
        raise UnsafeUrlError("HTTPS is required")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    for ip in _resolved_ips(host, port):
        _reject_special(ip)
        if ip.is_private or ip.is_loopback:
            raise UnsafeUrlError("URL resolves to a non-public address")
    return url


def assert_module_endpoint(url: str) -> str:
    """Plugin base URLs. Private addresses are allowed only for known service hostnames."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrlError("Module endpoint must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("Credentials in the URL are not allowed")
    host = parsed.hostname.lower().rstrip(".")
    if host in _METADATA_HOSTS:
        raise UnsafeUrlError("Metadata endpoints are not allowed")
    if ".." in (parsed.path or ""):
        raise UnsafeUrlError("Invalid endpoint path")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    allow_private = host in _allowed_module_hosts()
    for ip in _resolved_ips(host, port):
        _reject_special(ip)
        if (ip.is_private or ip.is_loopback) and not allow_private:
            raise UnsafeUrlError("Module URL is not on the service allowlist")
    return parsed.geturl()


def assert_health_path(path: str) -> str:
    if not path.startswith("/") or path.startswith("//") or ".." in path:
        raise UnsafeUrlError("Health endpoint must be a relative path")
    if "://" in path:
        raise UnsafeUrlError("Health endpoint must be a relative path")
    return path
