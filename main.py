from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
import httpx
from bs4 import BeautifulSoup

app = FastAPI(
    title="OG Tag Scraper API",
    description="A FastAPI service to extract Open Graph tags from any URL",
    version="1.0.0",
)


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
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                str(url),
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
