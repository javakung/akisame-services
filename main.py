from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
import httpx
from bs4 import BeautifulSoup
import ipaddress
import socket
from urllib.parse import urlparse

app = FastAPI(
    title="OG Tag Scraper API",
    description="A FastAPI service to extract Open Graph tags from any URL",
    version="1.0.0",
)

BLOCKED_SCHEMES = {"file", "ftp", "gopher", "data"}


def is_private_ip(hostname: str) -> bool:
    """Check if the hostname resolves to a private/internal IP address."""
    try:
        ip_addresses = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for addr_info in ip_addresses:
            ip_str = addr_info[4][0]
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        return False
    except (socket.gaierror, ValueError):
        return True


def validate_url_for_ssrf(url: str) -> None:
    """Validate URL to prevent SSRF attacks."""
    parsed = urlparse(url)

    if parsed.scheme.lower() in BLOCKED_SCHEMES:
        raise HTTPException(status_code=400, detail="URL scheme not allowed")

    if not parsed.hostname:
        raise HTTPException(status_code=400, detail="Invalid URL: no hostname")

    hostname_lower = parsed.hostname.lower()
    if hostname_lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise HTTPException(status_code=400, detail="Access to internal addresses is not allowed")

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        raise HTTPException(status_code=400, detail="Access to internal addresses is not allowed")

    if is_private_ip(parsed.hostname):
        raise HTTPException(status_code=400, detail="Access to internal addresses is not allowed")


class OGTagsResponse(BaseModel):
    url: str
    og_tags: dict[str, str]


@app.get("/og-tags", response_model=OGTagsResponse)
async def get_og_tags(url: HttpUrl = Query(..., description="The URL to fetch OG tags from")):
    """
    Fetch and return Open Graph tags from the specified URL.

    Open Graph tags are meta tags that provide structured information about
    a webpage, commonly used by social media platforms for link previews.
    """
    url_str = str(url)
    validate_url_for_ssrf(url_str)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                url_str,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; OGTagBot/1.0)"
                },
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to the URL timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch URL: HTTP {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch URL: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")
    og_tags: dict[str, str] = {}

    for meta in soup.find_all("meta"):
        property_attr = meta.get("property", "")
        if property_attr.startswith("og:"):
            og_name = property_attr[3:]
            content = meta.get("content", "")
            og_tags[og_name] = content

    return OGTagsResponse(url=str(url), og_tags=og_tags)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
