import json
import os
import re
import subprocess
import sys

import anthropic
import requests


def get_html_sample(url: str) -> str:
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.text[:4000]


def call_claude(error_output: str, config_content: str, html_sample: str, url: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"""A Python scraper failed with the following error:

ERROR:
{error_output}

CURRENT config.json:
{config_content}

HTML from {url} (first 4000 chars):
{html_sample}

Analyze the HTML and find the correct CSS selectors for:
- quote_container: the element wrapping each individual quote block
- quote_text: the element containing the quote text
- quote_author: the element containing the author name

Return ONLY a valid JSON object, nothing else:
{{"quote_container": "...", "quote_text": "...", "quote_author": "..."}}"""
        }]
    )

    text = response.content[0].text.strip()
    match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"Claude did not return valid JSON.\nResponse: {text}")
    return json.loads(match.group())


def main():
    print("=== Step 1: Run scraper to capture error ===")
    result = subprocess.run(["python", "scraper.py"], capture_output=True, text=True)
    error_output = (result.stdout + result.stderr).strip()
    print(error_output)

    if result.returncode == 0:
        print("Scraper already passing — nothing to fix.")
        sys.exit(0)

    print("\n=== Step 2: Read current config ===")
    with open("config.json") as f:
        config_content = f.read()
    cfg = json.loads(config_content)
    print(f"Current selectors: {cfg['selectors']}")

    print(f"\n=== Step 3: Fetch live HTML from {cfg['url']} ===")
    html_sample = get_html_sample(cfg["url"])
    print(f"Fetched {len(html_sample)} chars")

    print("\n=== Step 4: Ask Claude for correct selectors ===")
    new_selectors = call_claude(error_output, config_content, html_sample, cfg["url"])
    print(f"Claude suggests: {new_selectors}")

    print("\n=== Step 5: Apply fix to config.json ===")
    cfg["selectors"] = new_selectors
    with open("config.json", "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print("config.json updated")

    print("\n=== Step 6: Verify fix ===")
    verify = subprocess.run(["python", "scraper.py"], capture_output=True, text=True)
    print(verify.stdout)
    if verify.returncode != 0:
        print(f"Verification failed:\n{verify.stderr}", file=sys.stderr)
        sys.exit(1)

    print("\n✓ Fix verified — ready to commit")


if __name__ == "__main__":
    main()
