import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> FirecrawlApp:
    """Create a Firecrawl client."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY not set in environment")
    return FirecrawlApp(api_key=api_key)


def _strip_nav_boilerplate(markdown: str) -> str:
    """Remove navigation menus and repetitive link lists from markdown.

    Nav menus create huge blocks of markdown links that push actual content
    past the token limit. This strips them out while preserving page content.
    """
    lines = markdown.split("\n")
    cleaned = []
    consecutive_link_lines = 0

    for line in lines:
        stripped = line.strip()
        # Count consecutive lines that are just markdown links or empty
        if stripped.startswith("- [") or stripped.startswith("- **[") or (stripped == "" and consecutive_link_lines > 2):
            consecutive_link_lines += 1
            # Skip blocks of 5+ consecutive link lines (nav menus)
            if consecutive_link_lines >= 5:
                continue
        else:
            # If we skipped a nav block, don't retroactively add the first few links
            if consecutive_link_lines >= 5:
                cleaned = [l for l in cleaned if not (l.strip().startswith("- [") or l.strip().startswith("- **["))]
            consecutive_link_lines = 0
            cleaned.append(line)

    return "\n".join(cleaned)


def scrape_url(url: str) -> dict:
    """Scrape a single URL with Firecrawl and return markdown + metadata."""
    try:
        client = _get_client()
        result = client.scrape(url, only_main_content=False, formats=["markdown", "links"])
        markdown = getattr(result, "markdown", "") or ""
        links = getattr(result, "links", []) or []
        return {
            "markdown": _strip_nav_boilerplate(markdown),
            "links": links,
            "error": None,
        }
    except Exception as e:
        return {
            "markdown": "",
            "links": [],
            "error": str(e),
        }


def find_contact_page_url(links: list[str], base_url: str) -> str | None:
    """Find the most likely contact page URL from a list of links."""
    from urllib.parse import urlparse

    base_domain = urlparse(base_url).netloc

    # Priority tiers — check in order, return first match per tier
    tiers = [
        # Tier 1: Exact contact page patterns (highest confidence)
        ["contact-us", "contactus", "contact_us", "get-in-touch", "reach-us",
         "customer-support", "support", "inquiries", "connect"],
        # Tier 2: Generic contact (may match /contact-lens etc, so check after specific)
        ["contact"],
        # Tier 3: About pages (lower confidence, emails sometimes here)
        ["about-us", "aboutus", "about_us"],
        ["about"],
    ]

    for tier_keywords in tiers:
        for link in links:
            # Only same-domain links
            parsed = urlparse(link)
            if parsed.netloc and parsed.netloc != base_domain:
                continue

            # Get the last path segment to avoid matching "/about/" in "/about/bike-rental"
            path = parsed.path.rstrip("/").lower()
            last_segment = path.split("/")[-1] if path else ""

            for keyword in tier_keywords:
                if keyword in last_segment:
                    return link

    return None
