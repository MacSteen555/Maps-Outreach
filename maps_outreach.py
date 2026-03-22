import argparse
from urllib.parse import urljoin
from places_client import search_places
from scraper import scrape_url, find_contact_page_url
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
            print(" — no website, skipping")
            results.append({**biz, "emails": [], "contacts": []})
            continue

        # Pass 1: Scrape homepage
        print(f" — scraping homepage...", end="", flush=True)
        homepage = scrape_url(website)

        if homepage["error"]:
            print(f" failed ({homepage['error']})")
            results.append({**biz, "emails": [], "contacts": []})
            continue

        contact_info = extract_contact_info(homepage["markdown"])
        emails = contact_info.get("emails", [])
        contacts = contact_info.get("contacts", [])

        # Pass 2: If no emails, try the contact page
        if not emails:
            # Check both AI-suggested path and link-based detection
            contact_url = None
            ai_path = contact_info.get("contact_page_path")
            if ai_path:
                contact_url = urljoin(website, ai_path)
            else:
                contact_url = find_contact_page_url(homepage["links"], website)

            if contact_url:
                print(f" trying {contact_url}...", end="", flush=True)
                contact_page = scrape_url(contact_url)
                if not contact_page["error"]:
                    contact_info2 = extract_contact_info(contact_page["markdown"])
                    emails = contact_info2.get("emails", [])
                    contacts = contact_info2.get("contacts", []) or contacts

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
