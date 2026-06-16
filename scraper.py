import json
import sys

import requests
from bs4 import BeautifulSoup


def scrape():
    with open("config.json") as f:
        cfg = json.load(f)

    url = cfg["url"]
    timeout = cfg.get("timeout", 15)
    sel = cfg["selectors"]
    min_results = cfg.get("min_results", 1)
    required_fields = cfg.get("required_fields", [])

    # HTTP request — distinct error prefix for skill routing
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.exceptions.ConnectTimeout:
        raise RuntimeError(
            f"TIMEOUT_ERROR: request timed out after {timeout}s connecting to {url}"
        )
    except requests.exceptions.ReadTimeout:
        raise RuntimeError(
            f"TIMEOUT_ERROR: request timed out after {timeout}s reading from {url}"
        )
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(f"TIMEOUT_ERROR: connection failed to {url} — {e}")

    if not resp.ok:
        raise RuntimeError(
            f"HTTP_ERROR: {resp.status_code} at {url}"
        )

    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.select(sel["quote_container"])

    if len(containers) < min_results:
        raise ValueError(
            f"CSS_SELECTOR_ERROR: selector '{sel['quote_container']}' matched "
            f"{len(containers)} elements, expected >= {min_results}. "
            f"Check selectors in config.json."
        )

    results = []
    for item in containers:
        text_el = item.select_one(sel["quote_text"])
        author_el = item.select_one(sel["quote_author"])
        results.append({
            "text": text_el.get_text(strip=True) if text_el else "",
            "author": author_el.get_text(strip=True) if author_el else "",
        })

    # Required fields validation — distinct error prefix
    for field in required_fields:
        missing = [r for r in results if not r.get(field)]
        if missing:
            raise ValueError(
                f"SCHEMA_ERROR: required field '{field}' is missing or empty "
                f"in {len(missing)}/{len(results)} results. "
                f"Available fields: {list(results[0].keys()) if results else []}"
            )

    # Write output for inspector
    field_names = list(results[0].keys()) if results else []
    output = {
        "result_count": len(results),
        "results": results,
        "field_stats": {
            field: {
                "fill_rate": round(sum(1 for r in results if r.get(field)) / len(results), 3),
                "empty_count": sum(1 for r in results if not r.get(field)),
            }
            for field in field_names
        },
    }
    with open("output.json", "w") as f:
        json.dump(output, f, indent=2)

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
