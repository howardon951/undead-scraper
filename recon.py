"""
recon.py — read-only reconnaissance
Runs before the heal agent. Produces a structured snapshot of current
reality vs. config.json expectations. Never modifies anything.
"""
import json
import sys
import requests
from bs4 import BeautifulSoup


def recon() -> str:
    cfg = json.load(open("config.json"))
    url = cfg["url"]
    timeout = cfg.get("timeout", 15)
    sel = cfg["selectors"]
    required_fields = cfg.get("required_fields", [])
    min_results = cfg.get("min_results", 1)

    lines = []

    lines += [
        "=== RECON REPORT ===",
        "",
        "== config.json expects ==",
        f"  url: {url}",
        f"  required_fields: {required_fields}",
        f"  selectors: {json.dumps(sel)}",
        "",
    ]

    # Fetch page — use a generous timeout so recon always completes
    try:
        r = requests.get(url, timeout=60)
    except Exception as e:
        lines += [f"== HTTP == FAILED: {e}", ""]
        return "\n".join(lines)

    lines += [
        "== HTTP ==",
        f"  Status: {r.status_code} {'✓' if r.ok else '✗'}",
        f"  Final URL: {r.url}",
        "",
    ]

    if not r.ok:
        return "\n".join(lines)

    soup = BeautifulSoup(r.text, "html.parser")
    containers = soup.select(sel["quote_container"])

    lines += [
        f"== Container selector '{sel['quote_container']}' ==",
        f"  Found: {len(containers)} {'✓' if len(containers) >= min_results else '✗'}",
        "",
    ]

    if not containers:
        lines.append("No containers found — selector may be broken. HTML sample:")
        lines.append(r.text[1500:4000])
        return "\n".join(lines)

    item = containers[0]

    # Discover every element inside the first container
    lines.append("== First container — all child elements ==")
    for el in item.find_all(True):
        classes = ".".join(el.get("class", []))
        selector_hint = f".{classes}" if classes else el.name
        text = el.get_text(strip=True)[:60]
        lines.append(f"  {selector_hint:<30} → '{text}'")
    lines.append("")

    # Test each defined selector against live HTML
    lines.append("== Current selectors vs. live HTML ==")
    for name, selector in sel.items():
        if name == "quote_container":
            continue
        found = item.select_one(selector)
        if found:
            lines.append(f"  '{name}': '{selector}' → '{found.get_text(strip=True)[:50]}' ✓")
        else:
            lines.append(f"  '{name}': '{selector}' → NOT FOUND ✗")
    lines.append("")

    # Simulate exactly what scraper.py extracts (mirrors scraper logic)
    text_el = item.select_one(sel.get("quote_text", "__none__"))
    author_el = item.select_one(sel.get("quote_author", "__none__"))
    extracted = {
        "text": text_el.get_text(strip=True) if text_el else None,
        "author": author_el.get_text(strip=True) if author_el else None,
    }

    lines.append("== Required fields vs. extracted data ==")
    for field in required_fields:
        val = extracted.get(field)
        if val:
            lines.append(f"  '{field}': '{val[:50]}' ✓")
        elif field in extracted:
            lines.append(f"  '{field}': selector found but returned empty ✗")
        else:
            lines.append(f"  '{field}': not extracted by scraper (no selector) ✗")
    lines.append("")

    # Fill rates across all results
    lines.append("== Fill rates across all results ==")
    for name, selector in sel.items():
        if name == "quote_container":
            continue
        filled = sum(
            1 for c in containers
            if c.select_one(selector) and c.select_one(selector).get_text(strip=True)
        )
        rate = filled / len(containers)
        mark = "✓" if rate >= 0.8 else "✗"
        lines.append(f"  '{name}': {filled}/{len(containers)} = {rate:.0%} {mark}")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    report = recon()
    print(report)
    with open("recon_report.txt", "w") as f:
        f.write(report)
