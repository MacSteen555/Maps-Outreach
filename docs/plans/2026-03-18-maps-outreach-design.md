# Maps Outreach Platform — Design Doc

## Overview

A Python CLI tool for personal lead generation. Searches Google Maps for businesses in a given area/niche, scrapes their websites for contact info using AI, and outputs everything to a CSV.

## Usage

```bash
python maps_outreach.py "dentists near Austin, TX" --max-results 20
```

## Architecture

```
CLI Input (query, max results)
    │
    ▼
Google Places API (Text Search)
    │ Returns: name, address, phone, website, rating, category
    ▼
Website Scraper (httpx)
    │ Fetches homepage + /contact, /about, /team pages
    ▼
Claude API — Haiku (extract structured contact info from HTML)
    │ Returns: emails, contact names, roles
    ▼
CSV Writer
    │ Outputs: results/{timestamp}_results.csv
    ▼
Done — prints summary
```

## Project Structure

```
maps_outreach.py      # CLI entry point (argparse)
places_client.py      # Google Places API wrapper
scraper.py            # Website fetcher (httpx)
extractor.py          # Claude API contact extraction
csv_writer.py         # CSV output
.env                  # API keys (gitignored)
requirements.txt
```

## CSV Output Columns

business_name, address, phone, website, rating, category, email(s), contact_name, contact_role, source_page

## Key Decisions

### Website Scraping
- Fetch homepage, then follow links to /contact, /about, /team pages
- Strip scripts/styles from HTML before sending to Claude (reduce tokens)
- 5 second timeout per request
- 1-2 second delay between fetches to avoid blocks

### AI Extraction
- Use Claude Haiku for cost efficiency — simple structured extraction task
- Send cleaned HTML, ask for JSON response with emails, names, roles
- If no contact info found, business still appears in CSV with Google data only

### Error Handling
- Businesses with no website are skipped but logged
- Timeout/error sites are skipped but logged
- Claude extraction failures gracefully degrade to Google-only data

### Configuration
- API keys stored in .env file (python-dotenv)
- No database — CSV is sufficient for 10-20 result batches

## Dependencies

- httpx — async HTTP client for website fetching
- anthropic — Claude API SDK
- python-dotenv — environment variable management
- beautifulsoup4 — HTML parsing and cleaning
- argparse — CLI argument parsing (stdlib)
