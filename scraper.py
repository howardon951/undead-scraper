import json
import sys

import requests
from bs4 import BeautifulSoup


def scrape():
    with open("config.json") as f:
        cfg = json.load(f)

    url = cfg["url"]
    sel = cfg["selectors"]
    min_results = cfg.get("min_results", 1)

    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.select(sel["quote_container"])

    if len(containers) < min_results:
        raise ValueError(
            f"Expected >= {min_results} results using selector "
            f"'{sel['quote_container']}', found {len(containers)}. "
            f"Selectors may be broken. Check config.json."
        )

    results = []
    for item in containers:
        text_el = item.select_one(sel["quote_text"])
        author_el = item.select_one(sel["quote_author"])
        results.append({
            "text": text_el.get_text(strip=True) if text_el else "",
            "author": author_el.get_text(strip=True) if author_el else "",
        })

    print(f"SUCCESS: scraped {len(results)} quotes")
    for r in results[:3]:
        print(f"  - {r['author']}: {r['text'][:60]}...")
    return results


if __name__ == "__main__":
    try:
        scrape()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
