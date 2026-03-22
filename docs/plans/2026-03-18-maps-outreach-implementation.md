# Maps Outreach Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python CLI that searches Google Maps for businesses, scrapes their websites for contact info using Claude AI, and outputs results to CSV.

**Architecture:** CLI → Google Places API (Text Search) → httpx website scraper → Claude Haiku extraction → CSV output. Each component is a separate module. No database, no async complexity — simple sequential processing.

**Tech Stack:** Python 3.10+, httpx, anthropic SDK, beautifulsoup4, python-dotenv, argparse (stdlib), csv (stdlib)

---

### Task 1: Project Setup & Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`

**Step 1: Create requirements.txt**

```
httpx>=0.27.0
anthropic>=0.43.0
python-dotenv>=1.0.0
beautifulsoup4>=4.12.0
```

**Step 2: Create .env.example**

```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Step 3: Create results directory**

Run: `mkdir results`
Add `results/` is already covered by .gitignore patterns, but add a `.gitkeep`:
Run: `touch results/.gitkeep`

**Step 4: Install dependencies**

Run: `pip install -r requirements.txt`

**Step 5: Commit**

```bash
git add requirements.txt .env.example results/.gitkeep
git commit -m "feat: add project dependencies and env template"
```

---

### Task 2: Google Places Client

**Files:**
- Create: `places_client.py`
- Test: `tests/test_places_client.py`

**Step 1: Write the failing test**

Create `tests/__init__.py` (empty) and `tests/test_places_client.py`:

```python
import os
from unittest.mock import patch, MagicMock
from places_client import search_places


def test_search_places_parses_response():
    """Test that search_places correctly parses the Google Places API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "places": [
            {
                "displayName": {"text": "Austin Dental"},
                "formattedAddress": "123 Main St, Austin, TX",
                "nationalPhoneNumber": "(512) 555-0100",
                "websiteUri": "https://austindental.com",
                "rating": 4.5,
                "primaryTypeDisplayName": {"text": "Dentist"},
                "googleMapsUri": "https://maps.google.com/?cid=123",
            }
        ]
    }

    with patch("places_client.httpx.post", return_value=mock_response):
        results = search_places("dentists near Austin TX", max_results=10)

    assert len(results) == 1
    assert results[0]["business_name"] == "Austin Dental"
    assert results[0]["address"] == "123 Main St, Austin, TX"
    assert results[0]["phone"] == "(512) 555-0100"
    assert results[0]["website"] == "https://austindental.com"
    assert results[0]["rating"] == 4.5
    assert results[0]["category"] == "Dentist"


def test_search_places_handles_missing_fields():
    """Test that missing optional fields default to empty strings."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "places": [
            {
                "displayName": {"text": "Some Place"},
                "formattedAddress": "456 Oak Ave",
            }
        ]
    }

    with patch("places_client.httpx.post", return_value=mock_response):
        results = search_places("cafes", max_results=5)

    assert results[0]["phone"] == ""
    assert results[0]["website"] == ""
    assert results[0]["rating"] == ""
    assert results[0]["category"] == ""
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_places_client.py -v`
Expected: FAIL with "cannot import name 'search_places'"

**Step 3: Write implementation**

Create `places_client.py`:

```python
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"


def search_places(query: str, max_results: int = 20) -> list[dict]:
    """Search Google Places API and return parsed business info."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not set in environment")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.websiteUri,"
            "places.rating,"
            "places.primaryTypeDisplayName,"
            "places.googleMapsUri"
        ),
    }

    body = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),
    }

    response = httpx.post(PLACES_API_URL, json=body, headers=headers)
    response.raise_for_status()
    data = response.json()

    results = []
    for place in data.get("places", []):
        results.append({
            "business_name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "phone": place.get("nationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "rating": place.get("rating", ""),
            "category": place.get("primaryTypeDisplayName", {}).get("text", ""),
            "google_maps_url": place.get("googleMapsUri", ""),
        })

    return results
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_places_client.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add places_client.py tests/__init__.py tests/test_places_client.py
git commit -m "feat: add Google Places API client with text search"
```

---

### Task 3: Website Scraper

**Files:**
- Create: `scraper.py`
- Test: `tests/test_scraper.py`

**Step 1: Write the failing test**

Create `tests/test_scraper.py`:

```python
from unittest.mock import patch, MagicMock
from scraper import fetch_website_content


def test_fetch_website_strips_scripts_and_styles():
    """Test that HTML is cleaned of script/style tags."""
    raw_html = """
    <html>
    <head><style>body { color: red; }</style></head>
    <body>
        <script>alert('hi')</script>
        <p>Contact us at info@test.com</p>
    </body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = raw_html

    with patch("scraper.httpx.get", return_value=mock_response):
        result = fetch_website_content("https://example.com")

    assert "alert" not in result["text"]
    assert "color: red" not in result["text"]
    assert "info@test.com" in result["text"]


def test_fetch_website_finds_contact_links():
    """Test that contact/about page links are discovered."""
    raw_html = """
    <html><body>
        <a href="/contact">Contact Us</a>
        <a href="/about">About</a>
        <a href="/products">Products</a>
        <a href="/team">Our Team</a>
    </body></html>
    """
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = raw_html

    with patch("scraper.httpx.get", return_value=mock_response):
        result = fetch_website_content("https://example.com")

    assert "/contact" in result["contact_pages"]
    assert "/about" in result["contact_pages"]
    assert "/team" in result["contact_pages"]
    assert "/products" not in result["contact_pages"]


def test_fetch_website_handles_timeout():
    """Test that timeouts return empty result."""
    with patch("scraper.httpx.get", side_effect=Exception("Timeout")):
        result = fetch_website_content("https://example.com")

    assert result["text"] == ""
    assert result["contact_pages"] == []
    assert result["error"] is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scraper.py -v`
Expected: FAIL with "cannot import name 'fetch_website_content'"

**Step 3: Write implementation**

Create `scraper.py`:

```python
import re
import time
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

CONTACT_PATTERNS = re.compile(r"(contact|about|team|staff|people)", re.IGNORECASE)
TIMEOUT = 5.0
DELAY = 1.5


def _clean_html(html: str) -> str:
    """Strip scripts, styles, and extract readable text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _find_contact_pages(html: str, base_url: str) -> list[str]:
    """Find links to contact/about/team pages."""
    soup = BeautifulSoup(html, "html.parser")
    contact_pages = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True).lower()
        if CONTACT_PATTERNS.search(href) or CONTACT_PATTERNS.search(text):
            full_url = urljoin(base_url, href)
            # Only follow links on the same domain
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                contact_pages.append(href)
    return list(set(contact_pages))


def fetch_website_content(url: str) -> dict:
    """Fetch a website and return cleaned text + contact page links."""
    try:
        response = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        html = response.text
        cleaned_text = _clean_html(html)
        contact_pages = _find_contact_pages(html, url)
        return {
            "text": cleaned_text,
            "contact_pages": contact_pages,
            "error": None,
        }
    except Exception as e:
        return {
            "text": "",
            "contact_pages": [],
            "error": str(e),
        }


def fetch_all_pages(url: str) -> str:
    """Fetch homepage + all discovered contact pages, return combined text."""
    homepage = fetch_website_content(url)
    if homepage["error"]:
        return ""

    all_text = [f"=== HOMEPAGE ({url}) ===\n{homepage['text']}"]

    for page_path in homepage["contact_pages"][:3]:  # Limit to 3 sub-pages
        time.sleep(DELAY)
        full_url = urljoin(url, page_path)
        page = fetch_website_content(full_url)
        if not page["error"]:
            all_text.append(f"\n=== PAGE ({full_url}) ===\n{page['text']}")

    return "\n".join(all_text)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_scraper.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add scraper.py tests/test_scraper.py
git commit -m "feat: add website scraper with contact page discovery"
```

---

### Task 4: Claude AI Contact Extractor

**Files:**
- Create: `extractor.py`
- Test: `tests/test_extractor.py`

**Step 1: Write the failing test**

Create `tests/test_extractor.py`:

```python
import json
from unittest.mock import patch, MagicMock
from extractor import extract_contact_info


def test_extract_contact_info_parses_response():
    """Test that Claude's JSON response is correctly parsed."""
    mock_message = MagicMock()
    mock_message.content = [
        MagicMock(text=json.dumps({
            "emails": ["info@dentist.com", "admin@dentist.com"],
            "contacts": [
                {"name": "Dr. Smith", "role": "Owner", "email": "smith@dentist.com"}
            ]
        }))
    ]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("extractor.anthropic.Anthropic", return_value=mock_client):
        result = extract_contact_info("Some website text about dentistry")

    assert "info@dentist.com" in result["emails"]
    assert result["contacts"][0]["name"] == "Dr. Smith"


def test_extract_contact_info_handles_no_info():
    """Test graceful handling when no contact info is found."""
    mock_message = MagicMock()
    mock_message.content = [
        MagicMock(text=json.dumps({
            "emails": [],
            "contacts": []
        }))
    ]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("extractor.anthropic.Anthropic", return_value=mock_client):
        result = extract_contact_info("No contact info here")

    assert result["emails"] == []
    assert result["contacts"] == []


def test_extract_contact_info_handles_api_error():
    """Test graceful handling of API errors."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API Error")

    with patch("extractor.anthropic.Anthropic", return_value=mock_client):
        result = extract_contact_info("Some text")

    assert result["emails"] == []
    assert result["contacts"] == []
    assert result["error"] is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_extractor.py -v`
Expected: FAIL with "cannot import name 'extract_contact_info'"

**Step 3: Write implementation**

Create `extractor.py`:

```python
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

EXTRACTION_PROMPT = """Extract contact information from this website content. Return a JSON object with:
- "emails": list of all email addresses found
- "contacts": list of objects with "name", "role", and "email" for each person identified

If no contact information is found, return empty lists. Return ONLY valid JSON, no other text.

Website content:
{content}"""


def extract_contact_info(website_text: str) -> dict:
    """Use Claude to extract contact info from website text."""
    if not website_text.strip():
        return {"emails": [], "contacts": [], "error": None}

    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(
                        content=website_text[:10000]  # Limit input size
                    ),
                }
            ],
        )

        response_text = message.content[0].text
        data = json.loads(response_text)
        return {
            "emails": data.get("emails", []),
            "contacts": data.get("contacts", []),
            "error": None,
        }
    except Exception as e:
        return {
            "emails": [],
            "contacts": [],
            "error": str(e),
        }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_extractor.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add extractor.py tests/test_extractor.py
git commit -m "feat: add Claude AI contact info extractor"
```

---

### Task 5: CSV Writer

**Files:**
- Create: `csv_writer.py`
- Test: `tests/test_csv_writer.py`

**Step 1: Write the failing test**

Create `tests/test_csv_writer.py`:

```python
import csv
import os
import tempfile
from csv_writer import write_results


def test_write_results_creates_csv():
    """Test that CSV is created with correct headers and data."""
    results = [
        {
            "business_name": "Austin Dental",
            "address": "123 Main St",
            "phone": "(512) 555-0100",
            "website": "https://austindental.com",
            "rating": 4.5,
            "category": "Dentist",
            "google_maps_url": "https://maps.google.com/?cid=123",
            "emails": ["info@austindental.com"],
            "contacts": [{"name": "Dr. Smith", "role": "Owner", "email": "smith@austindental.com"}],
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = write_results(results, output_dir=tmpdir)
        assert os.path.exists(filepath)

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["business_name"] == "Austin Dental"
        assert "info@austindental.com" in rows[0]["emails"]
        assert "Dr. Smith" in rows[0]["contact_name"]


def test_write_results_handles_empty_contacts():
    """Test CSV output when no contact info was found."""
    results = [
        {
            "business_name": "Some Place",
            "address": "456 Oak Ave",
            "phone": "",
            "website": "",
            "rating": "",
            "category": "",
            "google_maps_url": "",
            "emails": [],
            "contacts": [],
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = write_results(results, output_dir=tmpdir)

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["emails"] == ""
        assert rows[0]["contact_name"] == ""
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_csv_writer.py -v`
Expected: FAIL with "cannot import name 'write_results'"

**Step 3: Write implementation**

Create `csv_writer.py`:

```python
import csv
import os
from datetime import datetime

HEADERS = [
    "business_name",
    "address",
    "phone",
    "website",
    "rating",
    "category",
    "emails",
    "contact_name",
    "contact_role",
    "google_maps_url",
]


def write_results(results: list[dict], output_dir: str = "results") -> str:
    """Write results to a timestamped CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{timestamp}_results.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()

        for result in results:
            emails = result.get("emails", [])
            contacts = result.get("contacts", [])

            writer.writerow({
                "business_name": result.get("business_name", ""),
                "address": result.get("address", ""),
                "phone": result.get("phone", ""),
                "website": result.get("website", ""),
                "rating": result.get("rating", ""),
                "category": result.get("category", ""),
                "emails": "; ".join(emails),
                "contact_name": "; ".join(c.get("name", "") for c in contacts),
                "contact_role": "; ".join(c.get("role", "") for c in contacts),
                "google_maps_url": result.get("google_maps_url", ""),
            })

    return filepath
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_csv_writer.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add csv_writer.py tests/test_csv_writer.py
git commit -m "feat: add CSV writer for outreach results"
```

---

### Task 6: CLI Entry Point — Wire It All Together

**Files:**
- Create: `maps_outreach.py`
- Test: `tests/test_maps_outreach.py`

**Step 1: Write the failing test**

Create `tests/test_maps_outreach.py`:

```python
from unittest.mock import patch, MagicMock
from maps_outreach import run_outreach


def test_run_outreach_end_to_end():
    """Test the full pipeline with mocked APIs."""
    mock_places = [
        {
            "business_name": "Test Biz",
            "address": "123 Main St",
            "phone": "555-0100",
            "website": "https://testbiz.com",
            "rating": 4.0,
            "category": "Dentist",
            "google_maps_url": "https://maps.google.com/?cid=1",
        }
    ]

    mock_contact = {
        "emails": ["info@testbiz.com"],
        "contacts": [{"name": "John", "role": "Manager", "email": "john@testbiz.com"}],
        "error": None,
    }

    with patch("maps_outreach.search_places", return_value=mock_places), \
         patch("maps_outreach.fetch_all_pages", return_value="some website text"), \
         patch("maps_outreach.extract_contact_info", return_value=mock_contact), \
         patch("maps_outreach.write_results", return_value="results/test.csv") as mock_write:

        result = run_outreach("dentists near Austin TX", max_results=10)

    assert result["total"] == 1
    assert result["with_email"] == 1
    mock_write.assert_called_once()
    written_data = mock_write.call_args[0][0]
    assert written_data[0]["emails"] == ["info@testbiz.com"]


def test_run_outreach_skips_no_website():
    """Test that businesses without websites are skipped for scraping."""
    mock_places = [
        {
            "business_name": "No Website Biz",
            "address": "456 Oak Ave",
            "phone": "555-0200",
            "website": "",
            "rating": 3.0,
            "category": "Cafe",
            "google_maps_url": "",
        }
    ]

    with patch("maps_outreach.search_places", return_value=mock_places), \
         patch("maps_outreach.fetch_all_pages") as mock_fetch, \
         patch("maps_outreach.extract_contact_info") as mock_extract, \
         patch("maps_outreach.write_results", return_value="results/test.csv"):

        result = run_outreach("cafes", max_results=5)

    mock_fetch.assert_not_called()
    mock_extract.assert_not_called()
    assert result["total"] == 1
    assert result["with_email"] == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_maps_outreach.py -v`
Expected: FAIL with "cannot import name 'run_outreach'"

**Step 3: Write implementation**

Create `maps_outreach.py`:

```python
import argparse
import sys
from places_client import search_places
from scraper import fetch_all_pages
from extractor import extract_contact_info
from csv_writer import write_results


def run_outreach(query: str, max_results: int = 20) -> dict:
    """Run the full outreach pipeline: search → scrape → extract → CSV."""
    print(f"\nSearching for: {query}")
    print(f"Max results: {max_results}\n")

    # Step 1: Search Google Places
    print("Searching Google Maps...")
    businesses = search_places(query, max_results=max_results)
    print(f"Found {len(businesses)} businesses\n")

    # Step 2 & 3: Scrape websites and extract contact info
    results = []
    with_email = 0

    for i, biz in enumerate(businesses, 1):
        name = biz["business_name"]
        website = biz["website"]
        print(f"[{i}/{len(businesses)}] {name}", end="")

        if not website:
            print(" — no website, skipping scrape")
            results.append({**biz, "emails": [], "contacts": []})
            continue

        print(f" — scraping {website}...", end="")
        website_text = fetch_all_pages(website)

        if not website_text:
            print(" failed to fetch")
            results.append({**biz, "emails": [], "contacts": []})
            continue

        contact_info = extract_contact_info(website_text)
        emails = contact_info.get("emails", [])
        contacts = contact_info.get("contacts", [])

        if emails:
            with_email += 1
            print(f" found {len(emails)} email(s)")
        else:
            print(" no emails found")

        results.append({**biz, "emails": emails, "contacts": contacts})

    # Step 4: Write CSV
    filepath = write_results(results)
    print(f"\nResults saved to: {filepath}")
    print(f"Total: {len(results)} | With email: {with_email} | No email: {len(results) - with_email}")

    return {"total": len(results), "with_email": with_email, "file": filepath}


def main():
    parser = argparse.ArgumentParser(
        description="Search Google Maps and find contact info for outreach"
    )
    parser.add_argument("query", help='Search query (e.g., "dentists near Austin, TX")')
    parser.add_argument(
        "--max-results", type=int, default=20, help="Maximum results (default: 20)"
    )

    args = parser.parse_args()
    run_outreach(args.query, max_results=args.max_results)


if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_maps_outreach.py -v`
Expected: PASS (2 tests)

**Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: All 10 tests PASS

**Step 6: Commit**

```bash
git add maps_outreach.py tests/test_maps_outreach.py
git commit -m "feat: add CLI entry point wiring full outreach pipeline"
```

---

### Task 7: Manual Integration Test

**Step 1: Set up .env**

Copy `.env.example` to `.env` and fill in real API keys.

**Step 2: Run a real search**

Run: `python maps_outreach.py "dentists near Austin, TX" --max-results 3`

Expected: The tool searches Google Maps, scrapes 1-3 websites, extracts contact info, and saves a CSV in `results/`.

**Step 3: Verify CSV output**

Open the generated CSV and confirm columns and data look correct.

**Step 4: Commit any final fixes if needed**

```bash
git commit -m "fix: adjustments from integration testing"
```
