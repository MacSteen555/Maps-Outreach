from unittest.mock import patch, MagicMock
from scraper import scrape_url, find_contact_page_url


def test_scrape_url_returns_markdown_and_links():
    """Test that Firecrawl response is correctly returned."""
    mock_document = MagicMock()
    mock_document.markdown = "# Welcome\nContact us at info@test.com"
    mock_document.links = ["https://example.com/contact", "https://example.com/about"]

    mock_client = MagicMock()
    mock_client.scrape.return_value = mock_document

    with patch("scraper.FirecrawlApp", return_value=mock_client), \
         patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key"}):
        result = scrape_url("https://example.com")

    assert "info@test.com" in result["markdown"]
    assert len(result["links"]) == 2
    assert result["error"] is None


def test_scrape_url_handles_error():
    """Test that errors are caught gracefully."""
    mock_client = MagicMock()
    mock_client.scrape.side_effect = Exception("Timeout")

    with patch("scraper.FirecrawlApp", return_value=mock_client), \
         patch.dict("os.environ", {"FIRECRAWL_API_KEY": "test-key"}):
        result = scrape_url("https://example.com")

    assert result["markdown"] == ""
    assert result["links"] == []
    assert result["error"] is not None


def test_find_contact_page_url_prefers_contact():
    """Test that /contact is preferred over /about."""
    links = [
        "https://example.com/about",
        "https://example.com/products",
        "https://example.com/contact-us",
    ]
    result = find_contact_page_url(links, "https://example.com")
    assert result == "https://example.com/contact-us"


def test_find_contact_page_url_falls_back_to_about():
    """Test fallback to about page when no contact page exists."""
    links = [
        "https://example.com/products",
        "https://example.com/about",
        "https://example.com/blog",
    ]
    result = find_contact_page_url(links, "https://example.com")
    assert result == "https://example.com/about"


def test_find_contact_page_url_returns_none():
    """Test None when no relevant pages found."""
    links = [
        "https://example.com/products",
        "https://example.com/blog",
    ]
    result = find_contact_page_url(links, "https://example.com")
    assert result is None
