# Maps-Outreach

A CLI tool that searches Google Maps for businesses, scrapes their websites for contact info using AI, and outputs everything to a CSV.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and add your API keys:

```
GOOGLE_MAPS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

- **Google Maps API Key:** Get one from [Google Cloud Console](https://console.cloud.google.com/). Enable the **Places API (New)**.
- **OpenAI API Key:** Get one from [OpenAI Platform](https://platform.openai.com/).

## Usage

```bash
python maps_outreach.py "dentists near Austin, TX"
```

With a custom result limit (default is 20):

```bash
python maps_outreach.py "coffee shops in Brooklyn, NY" --max-results 10
```

## Output

Results are saved to `results/` as timestamped CSV files (e.g. `20260319_143022_results.csv`).

CSV columns:

| Column | Source |
|---|---|
| business_name | Google Maps |
| address | Google Maps |
| phone | Google Maps |
| website | Google Maps |
| rating | Google Maps |
| category | Google Maps |
| emails | Website scrape |
| contact_name | Website scrape |
| contact_role | Website scrape |
| google_maps_url | Google Maps |

## How It Works

1. Searches Google Places API for businesses matching your query
2. For each business with a website, fetches the homepage and any /contact, /about, /team pages
3. Sends the cleaned page text to GPT-4o-mini to extract emails and contact names
4. Writes all results to a CSV file
