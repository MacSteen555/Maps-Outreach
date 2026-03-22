import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

EXTRACTION_PROMPT = """Extract contact information from this website content. Return a JSON object with:
- "emails": list of all email addresses found (look for mailto: links, text like "email us at", and any email patterns)
- "contacts": list of objects with "name", "role", and "email" for each person identified
- "contact_page_path": if you see a link to a contact page (like "/contact", "/contact-us", "/get-in-touch") but no emails on this page, return that path. Otherwise return null.

If no contact information is found, return empty lists. Return ONLY valid JSON, no other text.

Website content:
{content}"""


def extract_contact_info(website_text: str) -> dict:
    """Use OpenAI to extract contact info from website text."""
    if not website_text.strip():
        return {"emails": [], "contacts": [], "contact_page_path": None, "error": None}

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(
                        content=website_text[:30000]
                    ),
                }
            ],
            max_tokens=1024,
        )

        response_text = response.choices[0].message.content
        data = json.loads(response_text)
        return {
            "emails": data.get("emails", []),
            "contacts": data.get("contacts", []),
            "contact_page_path": data.get("contact_page_path"),
            "error": None,
        }
    except Exception as e:
        return {
            "emails": [],
            "contacts": [],
            "contact_page_path": None,
            "error": str(e),
        }
